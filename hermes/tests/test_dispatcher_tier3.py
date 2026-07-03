import hashlib
import hmac
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import dispatcher_tier3 as tier3  # noqa: E402


@pytest.fixture(autouse=True)
def reset_globals():
    tier3.client = None
    tier3.max_parallel_tasks = 3
    tier3.webhook_secret = None
    tier3.notion_webhook_secret = None
    yield


def _task(task_id="page1", name="Write blog post", task_type="automation"):
    return {
        "id": task_id,
        "properties": {
            "Task Name": {"title": [{"plain_text": name}]},
            "Type": {"select": {"name": task_type}},
        },
    }


def test_dispatch_tasks_skips_when_at_capacity():
    tier3.client = MagicMock()
    tier3.client.query_tasks.return_value = [_task(), _task(), _task()]  # 3 running == cap
    tier3.max_parallel_tasks = 3

    dispatched = tier3.dispatch_tasks()

    assert dispatched == 0
    tier3.client.update_status.assert_not_called()


def test_dispatch_tasks_starts_cheapest_pending_tasks_up_to_available_slots():
    tier3.client = MagicMock()
    tier3.max_parallel_tasks = 3
    tier3.client.get_status.return_value = "pending"
    tier3.client.query_tasks.return_value = [_task("running1")]  # 1 running, 2 slots available
    tier3.client.query_all_tasks.return_value = [
        _task("expensive", "Write article", task_type="content"),  # cost 7
        _task("cheap1", "Sync data", task_type="automation"),  # cost 1
        _task("cheap2", "Look something up", task_type="research"),  # cost 3
    ]

    dispatched = tier3.dispatch_tasks()

    assert dispatched == 2
    tier3.client.query_all_tasks.assert_called_once_with("pending")
    started_ids = {call.args[0] for call in tier3.client.update_status.call_args_list}
    assert started_ids == {"cheap1", "cheap2"}


def test_dispatch_tasks_picks_cheapest_pending_task_beyond_first_page():
    """query_all_tasks must be used (not query_tasks) so a cheaper task
    beyond the first 100-row Notion page still wins."""
    tier3.client = MagicMock()
    tier3.max_parallel_tasks = 1
    tier3.client.get_status.return_value = "pending"
    tier3.client.query_tasks.return_value = []  # 0 running, 1 slot available
    tier3.client.query_all_tasks.return_value = [
        _task("page-1-task", "Older, pricier task", task_type="content"),  # cost 7
        _task("page-2-task", "Newer, cheaper task", task_type="automation"),  # cost 1
    ]

    dispatched = tier3.dispatch_tasks()

    assert dispatched == 1
    tier3.client.update_status.assert_called_once_with("page-2-task", "running")


def test_dispatch_tasks_skips_task_whose_status_changed_before_dispatch():
    tier3.client = MagicMock()
    tier3.max_parallel_tasks = 2
    tier3.client.query_tasks.return_value = []  # 0 running, 2 slots available
    tier3.client.query_all_tasks.return_value = [_task("stale", "Already handled")]
    # Someone completed/cancelled it in Notion between the query and now.
    tier3.client.get_status.return_value = "completed"

    dispatched = tier3.dispatch_tasks()

    assert dispatched == 0
    tier3.client.update_status.assert_not_called()


def test_verify_notion_signature_accepts_matching_hmac():
    body = b'{"event":"task.updated"}'
    secret = "shhh"
    signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    assert tier3.verify_notion_signature(body, signature, secret) is True


def test_verify_notion_signature_rejects_wrong_signature():
    body = b'{"event":"task.updated"}'
    assert tier3.verify_notion_signature(body, "sha256=deadbeef", "shhh") is False


def test_verify_notion_signature_rejects_missing_header():
    assert tier3.verify_notion_signature(b"{}", None, "shhh") is False


def test_verify_notion_signature_rejects_non_ascii_header_without_crashing():
    # hmac.compare_digest() raises TypeError on non-ASCII str input; an
    # attacker-controlled header must be rejected, not crash the process.
    assert tier3.verify_notion_signature(b"{}", "sha256=ééé", "shhh") is False


def test_webhook_rejects_non_ascii_shared_secret_header_without_crashing():
    tier3.webhook_secret = "expected-secret"
    with tier3.app.test_client() as test_client:
        response = test_client.post(
            "/webhook",
            json={"event": "x"},
            headers={"X-Webhook-Secret": "ééé"},
        )

    assert response.status_code == 401


def test_webhook_accepts_notion_verification_handshake():
    tier3.notion_webhook_secret = "some-secret"
    with tier3.app.test_client() as test_client:
        response = test_client.post("/webhook", json={"verification_token": "abc123"})

    assert response.status_code == 200
    assert response.get_json()["status"] == "verified"


def test_webhook_rejects_invalid_notion_signature():
    tier3.notion_webhook_secret = "some-secret"
    with tier3.app.test_client() as test_client:
        response = test_client.post(
            "/webhook",
            json={"event": "task.updated"},
            headers={"X-Notion-Signature": "sha256=wrong"},
        )

    assert response.status_code == 401


def test_webhook_accepts_valid_notion_signature(monkeypatch):
    tier3.notion_webhook_secret = "some-secret"
    monkeypatch.setattr(tier3.threading, "Thread", lambda target, daemon: MagicMock(start=lambda: None))

    body = b'{"event":"task.updated"}'
    signature = "sha256=" + hmac.new(b"some-secret", body, hashlib.sha256).hexdigest()

    with tier3.app.test_client() as test_client:
        response = test_client.post(
            "/webhook",
            data=body,
            content_type="application/json",
            headers={"X-Notion-Signature": signature},
        )

    assert response.status_code == 202


def test_webhook_rejects_missing_shared_secret(monkeypatch):
    tier3.webhook_secret = "expected-secret"
    with tier3.app.test_client() as test_client:
        response = test_client.post("/webhook", json={"event": "x"})

    assert response.status_code == 401


def test_webhook_accepts_matching_shared_secret(monkeypatch):
    tier3.webhook_secret = "expected-secret"
    monkeypatch.setattr(tier3.threading, "Thread", lambda target, daemon: MagicMock(start=lambda: None))

    with tier3.app.test_client() as test_client:
        response = test_client.post(
            "/webhook",
            json={"event": "x"},
            headers={"X-Webhook-Secret": "expected-secret"},
        )

    assert response.status_code == 202
