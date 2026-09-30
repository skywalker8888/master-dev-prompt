"""
Hermes Tier 3 - Real-time Dispatcher

Combines a background polling loop with a Notion webhook endpoint so pending
tasks are picked up immediately, subject to a parallel-task cap.

Setup:
    pip install -r requirements.txt
    cp .env.example .env   # fill in NOTION_TOKEN, DATABASE_ID, WEBHOOK_PORT, MAX_PARALLEL_TASKS

Run:
    python3 dispatcher_tier3.py

/webhook accepts two kinds of callers:
  - A generic trigger (curl, an internal script, Zapier, ...) authenticated
    with a shared secret in the X-Webhook-Secret header (WEBHOOK_SECRET).
  - A real Notion webhook subscription: Notion first POSTs a one-time
    {"verification_token": ...} handshake, then signs every subsequent event
    body with an X-Notion-Signature header, verified here using
    NOTION_WEBHOOK_SECRET as the HMAC key (see
    https://developers.notion.com/reference/webhooks).
"""

import hashlib
import hmac
import os
import threading
import time
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, jsonify, request

from notion_client import MAX_PAGE_SIZE, NotionClient, log, require_env, task_details

POLL_INTERVAL_SECONDS = 30

app = Flask(__name__)
client: NotionClient | None = None
max_parallel_tasks = 3
webhook_secret: str | None = None
notion_webhook_secret: str | None = None

# Where the one-time Notion verification_token is written so an operator can
# retrieve it and paste it into NOTION_WEBHOOK_SECRET. Written with 0600
# permissions rather than logged, since the same value later doubles as the
# X-Notion-Signature HMAC key - anyone with log access could otherwise forge
# signed webhook requests.
VERIFICATION_TOKEN_PATH = os.getenv("VERIFICATION_TOKEN_PATH", ".notion_verification_token")

# Serializes dispatch_tasks so the webhook thread and the background poll
# loop can't both read a stale running-task count and jointly exceed
# max_parallel_tasks.
#
# This lock is process-local only. It does not coordinate across multiple
# Tier 3 processes, or between Tier 2 and Tier 3 running against the same
# database - two dispatchers can still both read the same running count and
# both pass the pending-status check before either writes "running". Run
# exactly one dispatcher process (one Tier 2 *or* one Tier 3, never both,
# never more than one of either) per Notion database until this has a real
# cross-process claim mechanism.
dispatch_lock = threading.Lock()


def running_task_count(limit: int | None = None) -> int:
    # query_tasks only returns a single Notion page (<= MAX_PAGE_SIZE), so
    # this undercounts whenever limit exceeds that - main() enforces
    # max_parallel_tasks <= MAX_PAGE_SIZE so limit never does here.
    return len(client.query_tasks("running", limit=limit))


def verify_notion_signature(raw_body: bytes, signature_header: str | None, secret: str) -> bool:
    if not signature_header:
        return False
    expected = "sha256=" + hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    # Compare as bytes, not str: hmac.compare_digest() raises TypeError on
    # non-ASCII str input, and an attacker-controlled header could contain
    # arbitrary bytes - that would 500 instead of cleanly rejecting with 401.
    return hmac.compare_digest(expected.encode(), signature_header.encode())


def dispatch_tasks() -> int:
    with dispatch_lock:
        # Bounding the query at max_parallel_tasks is enough to decide
        # whether the cap is reached, without needing to page through every
        # Running task (query_tasks only returns one Notion page).
        available_slots = max_parallel_tasks - running_task_count(limit=max_parallel_tasks)
        if available_slots <= 0:
            log(f"Max parallel tasks reached ({max_parallel_tasks})")
            return 0

        # The live database has no Cost property to sort by server-side, so
        # fetch every pending task and pick the cheapest ones client-side.
        pending = [task_details(raw) for raw in client.query_all_tasks("pending")]
        if not pending:
            return 0

        pending.sort(key=lambda t: t["cost"])

        dispatched = 0
        for task in pending:
            if dispatched == available_slots:
                break

            # Re-check status: someone may have edited this task in Notion
            # between the query above and now.
            if client.get_status(task["id"]) != "pending":
                log(f"Skipped '{task['name']}': status changed before dispatch")
                continue

            log(f"Dispatching '{task['name']}' (Type: {task['type']}, Cost: {task['cost']})")
            client.update_status(task["id"], "running")
            log(f"Started '{task['name']}'")
            dispatched += 1

        return dispatched


@app.route("/webhook", methods=["POST"])
def webhook_handler():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"status": "bad_request"}), 400

    # Notion's one-time subscription verification handshake: no signature is
    # sent with this request. Never log the token itself - it's the same
    # value used as the NOTION_WEBHOOK_SECRET HMAC key, so logging it would
    # let anyone with log access forge X-Notion-Signature. Instead write it
    # to a 0600 local file the operator can read once and then delete.
    if "verification_token" in payload:
        try:
            fd = os.open(VERIFICATION_TOKEN_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w") as f:
                f.write(str(payload["verification_token"]))
            log(
                f"Notion webhook verification handshake received - token written to "
                f"{VERIFICATION_TOKEN_PATH} (mode 600). Copy it into NOTION_WEBHOOK_SECRET, "
                "then delete the file."
            )
        except OSError as exc:
            log(f"Notion webhook verification handshake received, but couldn't write the token to disk: {exc}")
        return jsonify({"status": "verified"}), 200

    if notion_webhook_secret:
        signature = request.headers.get("X-Notion-Signature")
        if not verify_notion_signature(request.get_data(), signature, notion_webhook_secret):
            log("Webhook rejected: invalid or missing X-Notion-Signature")
            return jsonify({"status": "unauthorized"}), 401
    elif webhook_secret:
        provided = request.headers.get("X-Webhook-Secret", "")
        # Compare as bytes - see verify_notion_signature for why.
        if not hmac.compare_digest(provided.encode(), webhook_secret.encode()):
            log("Webhook rejected: invalid or missing X-Webhook-Secret")
            return jsonify({"status": "unauthorized"}), 401

    log(f"Webhook received: {payload}")
    threading.Thread(target=dispatch_tasks, daemon=True).start()
    return jsonify({"status": "accepted"}), 202


@app.route("/status", methods=["GET"])
def status():
    return jsonify(
        {
            "status": "running",
            "running_tasks": running_task_count(),
            "max_parallel": max_parallel_tasks,
            "timestamp": datetime.now().isoformat(),
        }
    )


def continuous_dispatcher() -> None:
    log("Background dispatcher started")
    while True:
        try:
            dispatched = dispatch_tasks()
            if dispatched:
                log(f"Dispatched {dispatched} task(s)")
            time.sleep(POLL_INTERVAL_SECONDS)
        except Exception as exc:
            log(f"Dispatcher error: {exc}")
            time.sleep(POLL_INTERVAL_SECONDS * 2)


def main() -> None:
    global client, max_parallel_tasks, webhook_secret, notion_webhook_secret

    load_dotenv()
    env = require_env("NOTION_TOKEN", "DATABASE_ID")
    client = NotionClient(env["NOTION_TOKEN"], env["DATABASE_ID"])
    max_parallel_tasks = int(os.getenv("MAX_PARALLEL_TASKS", "3"))
    webhook_port = int(os.getenv("WEBHOOK_PORT", "5000"))
    webhook_secret = os.getenv("WEBHOOK_SECRET")
    notion_webhook_secret = os.getenv("NOTION_WEBHOOK_SECRET")

    if max_parallel_tasks > MAX_PAGE_SIZE:
        raise RuntimeError(
            f"MAX_PARALLEL_TASKS ({max_parallel_tasks}) exceeds {MAX_PAGE_SIZE} - "
            "running_task_count() only pages through a single Notion page and would "
            "undercount above that, letting the parallel-task cap be exceeded"
        )

    if not webhook_secret and not notion_webhook_secret:
        raise RuntimeError(
            "WEBHOOK_SECRET or NOTION_WEBHOOK_SECRET must be set - refusing to start "
            "an unauthenticated /webhook that can trigger dispatches for anyone who can reach it"
        )

    log("Hermes Tier 3 dispatcher started")
    log(f"Database: {env['DATABASE_ID']}, max parallel tasks: {max_parallel_tasks}")

    threading.Thread(target=continuous_dispatcher, daemon=True).start()

    log(f"Starting webhook server on port {webhook_port}")
    app.run(host="0.0.0.0", port=webhook_port)


if __name__ == "__main__":
    main()
