"""Thin wrapper around the Notion API calls shared by the Tier 2 and Tier 3 dispatchers."""

import os
from datetime import datetime

import requests

NOTION_VERSION = "2022-06-28"


class NotionClient:
    def __init__(self, token: str, database_id: str):
        self.database_id = database_id
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        }

    def query_tasks(self, status: str, limit: int | None = None) -> list[dict]:
        url = f"https://api.notion.com/v1/databases/{self.database_id}/query"
        payload = {
            "filter": {"property": "Status", "select": {"equals": status}},
            "sorts": [{"property": "Cost", "direction": "ascending"}],
        }
        if limit:
            payload["page_size"] = limit

        response = requests.post(url, headers=self.headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json().get("results", [])

    def update_status(self, page_id: str, new_status: str) -> None:
        url = f"https://api.notion.com/v1/pages/{page_id}"
        payload = {"properties": {"Status": {"select": {"name": new_status}}}}
        response = requests.patch(url, headers=self.headers, json=payload, timeout=30)
        response.raise_for_status()


def task_details(task: dict) -> dict:
    properties = task.get("properties", {})

    name = "Unnamed Task"
    title = properties.get("Task Name", {}).get("title") or []
    if title:
        name = title[0].get("plain_text", name)

    cost = None
    formula = properties.get("Cost", {}).get("formula")
    if formula:
        cost = formula.get("number")

    pipeline = None
    select = properties.get("Pipeline", {}).get("select")
    if select:
        pipeline = select.get("name")

    return {"id": task["id"], "name": name, "cost": cost, "pipeline": pipeline}


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def require_env(*names: str) -> dict:
    values = {name: os.getenv(name) for name in names}
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise SystemExit(f"Missing required environment variable(s): {', '.join(missing)}")
    return values
