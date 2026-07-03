"""
Hermes Tier 2 - Scheduled Dispatcher

Polls the Hermes Notion database every 5 minutes and moves the cheapest
pending task to "Running".

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
    pending = client.query_tasks("Pending", limit=1)

    if not pending:
        log("No pending tasks found")
        return

    task = task_details(pending[0])
    log(f"Found task: '{task['name']}' (Cost: {task['cost']})")

    client.update_status(task["id"], "Running")
    log(f"Task '{task['name']}' moved to Running")


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
