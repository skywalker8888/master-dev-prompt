import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dispatcher_tier2 import dispatch_next_task  # noqa: E402


def _task(task_id="page1", name="Write blog post", cost=1):
    return {
        "id": task_id,
        "properties": {
            "Task Name": {"title": [{"plain_text": name}]},
            "Cost": {"formula": {"number": cost}},
            "Pipeline": {"select": {"name": "Automation"}},
        },
    }


def test_dispatch_next_task_starts_cheapest_pending_task():
    client = MagicMock()
    client.query_tasks.return_value = [_task()]

    dispatch_next_task(client)

    client.query_tasks.assert_called_once_with("Pending", limit=1)
    client.update_status.assert_called_once_with("page1", "Running")


def test_dispatch_next_task_does_nothing_when_queue_is_empty():
    client = MagicMock()
    client.query_tasks.return_value = []

    dispatch_next_task(client)

    client.update_status.assert_not_called()
