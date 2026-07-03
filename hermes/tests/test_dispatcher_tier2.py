import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import dispatcher_tier2 as tier2  # noqa: E402
from dispatcher_tier2 import dispatch_next_task  # noqa: E402


def _task(task_id="page1", name="Write blog post", task_type="automation"):
    return {
        "id": task_id,
        "properties": {
            "Task Name": {"title": [{"plain_text": name}]},
            "Type": {"select": {"name": task_type}},
        },
    }


def test_dispatch_next_task_starts_only_pending_task():
    client = MagicMock()
    client.query_all_tasks.return_value = [_task()]

    dispatch_next_task(client)

    client.query_all_tasks.assert_called_once_with("pending")
    client.update_status.assert_called_once_with("page1", "running")


def test_dispatch_next_task_picks_cheapest_of_several_pending_tasks():
    client = MagicMock()
    # content (cost 7) is queried before automation (cost 1); the cheaper one
    # must still win since there's no server-side Cost sort to rely on.
    client.query_all_tasks.return_value = [
        _task("expensive", "Write article", task_type="content"),
        _task("cheap", "Sync data", task_type="automation"),
    ]

    dispatch_next_task(client)

    client.update_status.assert_called_once_with("cheap", "running")


def test_dispatch_next_task_does_nothing_when_queue_is_empty():
    client = MagicMock()
    client.query_all_tasks.return_value = []

    dispatch_next_task(client)

    client.update_status.assert_not_called()


def test_main_loop_survives_dispatch_errors(monkeypatch):
    monkeypatch.setenv("NOTION_TOKEN", "secret")
    monkeypatch.setenv("DATABASE_ID", "db123")

    calls = {"count": 0}

    def flaky_dispatch(client):
        calls["count"] += 1
        raise RuntimeError("transient Notion API error")

    def sleep_then_stop(seconds):
        raise KeyboardInterrupt

    with patch("dispatcher_tier2.NotionClient", return_value=MagicMock()), \
         patch("dispatcher_tier2.dispatch_next_task", side_effect=flaky_dispatch), \
         patch("dispatcher_tier2.time.sleep", side_effect=sleep_then_stop):
        tier2.main()  # must not raise despite dispatch_next_task failing

    assert calls["count"] == 1
