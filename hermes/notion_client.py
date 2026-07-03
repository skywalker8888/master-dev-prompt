"""Thin wrapper around the Notion API calls shared by the Tier 2 and Tier 3 dispatchers."""

import os
from datetime import datetime

import requests

NOTION_VERSION = "2022-06-28"
MAX_PAGE_SIZE = 100

# The live Hermes Tasks database has no Cost formula property, so cost-by-type
# is computed here in code instead of read from Notion. Keys match the live
# database's "Type" select options.
TYPE_COST = {
    "automation": 1,
    "research": 3,
    "report": 5,
    "content": 7,
}
DEFAULT_COST = 10


class NotionClient:
    def __init__(self, token: str, database_id: str):
        self.database_id = database_id
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        }

    def query_tasks(self, status: str, limit: int | None = None) -> list[dict]:
        """Fetch one page of tasks in the given status, sorted by Created At ascending (FIFO).

        The live database has no Cost property to sort by server-side, so
        callers that need cheapest-first ordering must sort the returned
        results client-side using `task_cost`/`task_details`. Only returns
        the first Notion page (at most `MAX_PAGE_SIZE` results) - callers
        that need an exact count above that should page through
        `next_cursor` themselves. `limit=0` returns an empty list rather than
        an unbounded query.
        """
        if limit is not None and limit <= 0:
            return []

        url = f"https://api.notion.com/v1/databases/{self.database_id}/query"
        payload = {
            "filter": {"property": "Status", "select": {"equals": status}},
            "sorts": [{"property": "Created At", "direction": "ascending"}],
        }
        if limit is not None:
            payload["page_size"] = min(limit, MAX_PAGE_SIZE)

        response = requests.post(url, headers=self.headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json().get("results", [])

    def query_all_tasks(self, status: str) -> list[dict]:
        """Fetch every task in the given status, paging through `next_cursor`.

        Use this (not `query_tasks`) when the caller needs a globally correct
        answer over the whole status - e.g. picking the cheapest pending task
        - since `query_tasks` only returns a single Notion page.
        """
        url = f"https://api.notion.com/v1/databases/{self.database_id}/query"
        base_payload = {
            "filter": {"property": "Status", "select": {"equals": status}},
            "sorts": [{"property": "Created At", "direction": "ascending"}],
            "page_size": MAX_PAGE_SIZE,
        }

        results: list[dict] = []
        cursor: str | None = None
        while True:
            payload = dict(base_payload)
            if cursor:
                payload["start_cursor"] = cursor

            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            results.extend(data.get("results", []))
            if not data.get("has_more"):
                return results
            cursor = data.get("next_cursor")

    def update_status(self, page_id: str, new_status: str) -> None:
        url = f"https://api.notion.com/v1/pages/{page_id}"
        payload = {"properties": {"Status": {"select": {"name": new_status}}}}
        response = requests.patch(url, headers=self.headers, json=payload, timeout=30)
        response.raise_for_status()


def task_cost(task_type: str | None) -> int:
    if not task_type:
        return DEFAULT_COST
    return TYPE_COST.get(task_type.lower(), DEFAULT_COST)


def task_details(task: dict) -> dict:
    properties = task.get("properties", {})

    name = "Unnamed Task"
    title = properties.get("Task Name", {}).get("title") or []
    if title:
        name = title[0].get("plain_text", name)

    task_type = None
    select = properties.get("Type", {}).get("select")
    if select:
        task_type = select.get("name")

    return {"id": task["id"], "name": name, "type": task_type, "cost": task_cost(task_type)}


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def require_env(*names: str) -> dict:
    values = {name: os.getenv(name) for name in names}
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise SystemExit(f"Missing required environment variable(s): {', '.join(missing)}")
    return values
