import hashlib
import hmac
import stat
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import dispatcher_tier3 as tier3  # noqa: E402


@pytest.fixture(autouse=True)
def reset_globals(tmp_path):
    tier3.client = None
    tier3.max_parallel_tasks = 3
    tier3.webhook_secret = None
    tier3.notion_webhook_secret = None
    # Redirect the verification-token file out of the repo working directory
    # so tests don't leave (or race on) a real dotfile on disk.
    tier3.VERIFICATION_TOKEN_PATH = str(tmp_path / "notion_verification_token")
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


def test_dispatch_tasks_fills_slot_from_remaining_pending_after_skip():
    tier3.client = MagicMock()
    tier3.max_parallel_tasks = 2
    tier3.client.query_tasks.return_value = []  # 0 running, 2 slots available
    tier3.client.query_all_tasks.return_value = [
        _task("stale", "Already handled", task_type="automation"),  # cheapest, but stale
        _task("cheap2", "Backup task", task_type="research"),
        _task("cheap3", "Another backup", task_type="content"),
    ]
    # The cheapest task's status changed before dispatch; the two behind it
    # are still pending and should backfill the freed slot.
    tier3.client.get_status.side_effect = ["completed", "pending", "pending"]

    dispatched = tier3.dispatch_tasks()

    assert dispatched == 2
    started_ids = {call.args[0] for call in tier3.client.update_status.call_args_list}
    assert started_ids == {"cheap2", "cheap3"}


def test_main_raises_without_any_webhook_secret(monkeypatch):
    monkeypatch.setattr(tier3, "load_dotenv", lambda: None)
    monkeypatch.setattr(tier3, "require_env", lambda *names: {"NOTION_TOKEN": "x", "DATABASE_ID": "y"})
    monkeypatch.setattr(tier3, "NotionClient", MagicMock())
    monkeypatch.delenv("WEBHOOK_SECRET", raising=False)
    monkeypatch.delenv("NOTION_WEBHOOK_SECRET", raising=False)
    monkeypatch.delenv("MAX_PARALLEL_TASKS", raising=False)

    with pytest.raises(RuntimeError):
        tier3.main()


def test_main_raises_when_max_parallel_tasks_exceeds_page_size(monkeypatch):
    monkeypatch.setattr(tier3, "load_dotenv", lambda: None)
    monkeypatch.setattr(tier3, "require_env", lambda *names: {"NOTION_TOKEN": "x", "DATABASE_ID": "y"})
    monkeypatch.setattr(tier3, "NotionClient", MagicMock())
    monkeypatch.setenv("WEBHOOK_SECRET", "expected-secret")
    monkeypatch.setenv("MAX_PARALLEL_TASKS", str(tier3.MAX_PAGE_SIZE + 1))

    with pytest.raises(RuntimeError, match="MAX_PARALLEL_TASKS"):
        tier3.main()


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


def test_webhook_verification_handshake_does_not_log_token(capsys):
    # The verification token doubles as the NOTION_WEBHOOK_SECRET HMAC key,
    # so it must never end up in logs - anyone reading them could forge
    # X-Notion-Signature.
    tier3.notion_webhook_secret = "some-secret"
    with tier3.app.test_client() as test_client:
        test_client.post("/webhook", json={"verification_token": "abc123"})

    assert "abc123" not in capsys.readouterr().out


def test_webhook_verification_handshake_writes_token_to_restricted_file():
    tier3.notion_webhook_secret = "some-secret"
    with tier3.app.test_client() as test_client:
        test_client.post("/webhook", json={"verification_token": "abc123"})

    path = Path(tier3.VERIFICATION_TOKEN_PATH)
    assert path.read_text() == "abc123"
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_webhook_rejects_non_dict_json_payload():
    with tier3.app.test_client() as test_client:
        response = test_client.post("/webhook", data="1", content_type="application/json")

    assert response.status_code == 400


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
