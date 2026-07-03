"""
Hermes Tier 2 - Scheduled Dispatcher

Polls the Hermes Notion database every 5 minutes and moves the cheapest
pending task to "running".

Setup:
    pip install -r requirements.txt
    cp .env.example .env   # fill in NOTION_TOKEN and DATABASE_ID

Run:
    python3 dispatcher_tier2.py
"""

import time

from dotenv import load_dotenv

from notion_client import NotionClient, log, require_env, task_details

POLL_INTERVAL_SECONDS = 300


def dispatch_next_task(client: NotionClient) -> None:
    log("Checking for pending tasks...")
    # The live database has no Cost property to sort by server-side, so fetch
    # a page of pending tasks and pick the cheapest one client-side.
    pending = [task_details(raw) for raw in client.query_tasks("pending")]

    if not pending:
        log("No pending tasks found")
        return

    task = min(pending, key=lambda t: t["cost"])
    log(f"Found task: '{task['name']}' (Type: {task['type']}, Cost: {task['cost']})")

    client.update_status(task["id"], "running")
    log(f"Task '{task['name']}' moved to running")


def main() -> None:
    load_dotenv()
    env = require_env("NOTION_TOKEN", "DATABASE_ID")
    client = NotionClient(env["NOTION_TOKEN"], env["DATABASE_ID"])

    log("Hermes Tier 2 dispatcher started")
    log(f"Monitoring database: {env['DATABASE_ID']}")
    log("Press Ctrl+C to stop")

    try:
        while True:
            try:
                dispatch_next_task(client)
            except Exception as exc:
                log(f"Dispatcher error: {exc}")
            log(f"Sleeping for {POLL_INTERVAL_SECONDS // 60} minutes...")
            time.sleep(POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        log("Hermes Tier 2 dispatcher stopped")


if __name__ == "__main__":
    main()
