"""
Hermes Tier 3 - Real-time Dispatcher

Combines a background polling loop with a Notion webhook endpoint so pending
tasks are picked up immediately, subject to a parallel-task cap.

Setup:
    pip install -r requirements.txt
    cp .env.example .env   # fill in NOTION_TOKEN, DATABASE_ID, WEBHOOK_PORT, MAX_PARALLEL_TASKS

Run:
    python dispatcher_tier3.py
"""

import os
import threading
import time
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, jsonify, request

from notion_client import NotionClient, log, require_env, task_details

POLL_INTERVAL_SECONDS = 30

app = Flask(__name__)
client: NotionClient | None = None
max_parallel_tasks = 3


def running_task_count() -> int:
    return len(client.query_tasks("Running"))


def dispatch_tasks() -> int:
    available_slots = max_parallel_tasks - running_task_count()
    if available_slots <= 0:
        log(f"Max parallel tasks reached ({max_parallel_tasks})")
        return 0

    pending = client.query_tasks("Pending", limit=available_slots)
    if not pending:
        return 0

    dispatched = 0
    for raw_task in pending:
        task = task_details(raw_task)
        log(f"Dispatching '{task['name']}' (Cost: {task['cost']}, Pipeline: {task['pipeline']})")
        client.update_status(task["id"], "Running")
        log(f"Started '{task['name']}'")
        dispatched += 1

    return dispatched


@app.route("/webhook", methods=["POST"])
def webhook_handler():
    log(f"Webhook received: {request.json}")
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
    global client, max_parallel_tasks

    load_dotenv()
    env = require_env("NOTION_TOKEN", "DATABASE_ID")
    client = NotionClient(env["NOTION_TOKEN"], env["DATABASE_ID"])
    max_parallel_tasks = int(os.getenv("MAX_PARALLEL_TASKS", "3"))
    webhook_port = int(os.getenv("WEBHOOK_PORT", "5000"))

    log("Hermes Tier 3 dispatcher started")
    log(f"Database: {env['DATABASE_ID']}, max parallel tasks: {max_parallel_tasks}")

    threading.Thread(target=continuous_dispatcher, daemon=True).start()

    log(f"Starting webhook server on port {webhook_port}")
    app.run(host="0.0.0.0", port=webhook_port)


if __name__ == "__main__":
    main()
