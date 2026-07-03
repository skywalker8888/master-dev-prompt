import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from notion_client import NotionClient, require_env, task_cost, task_details  # noqa: E402


def _client():
    return NotionClient("secret_token", "db123")


def _mock_response(results):
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"results": results}
    return response


def test_query_tasks_sends_status_filter_and_sort():
    client = _client()
    with patch("notion_client.requests.post", return_value=_mock_response([])) as mock_post:
        client.query_tasks("pending")

        url, kwargs = mock_post.call_args
        payload = kwargs["json"]
        assert url[0] == "https://api.notion.com/v1/databases/db123/query"
        assert payload["filter"] == {"property": "Status", "select": {"equals": "pending"}}
        assert payload["sorts"] == [{"property": "Created At", "direction": "ascending"}]
        assert "page_size" not in payload


def test_query_tasks_limit_zero_returns_empty_without_request():
    client = _client()
    with patch("notion_client.requests.post") as mock_post:
        result = client.query_tasks("pending", limit=0)

        assert result == []
        mock_post.assert_not_called()


def test_query_tasks_limit_is_capped_at_max_page_size():
    client = _client()
    with patch("notion_client.requests.post", return_value=_mock_response([])) as mock_post:
        client.query_tasks("pending", limit=500)

        payload = mock_post.call_args.kwargs["json"]
        assert payload["page_size"] == 100


def test_query_tasks_returns_results():
    client = _client()
    tasks = [{"id": "abc"}]
    with patch("notion_client.requests.post", return_value=_mock_response(tasks)):
        assert client.query_tasks("pending", limit=1) == tasks


def test_update_status_patches_correct_page():
    client = _client()
    response = MagicMock()
    response.raise_for_status.return_value = None
    with patch("notion_client.requests.patch", return_value=response) as mock_patch:
        client.update_status("page123", "running")

        url, kwargs = mock_patch.call_args
        assert url[0] == "https://api.notion.com/v1/pages/page123"
        assert kwargs["json"] == {"properties": {"Status": {"select": {"name": "running"}}}}


def test_task_cost_maps_known_types_case_insensitively():
    assert task_cost("automation") == 1
    assert task_cost("Research") == 3
    assert task_cost("report") == 5
    assert task_cost("CONTENT") == 7


def test_task_cost_defaults_for_unknown_or_missing_type():
    assert task_cost("something-else") == 10
    assert task_cost(None) == 10


def test_task_details_extracts_name_type_and_computed_cost():
    task = {
        "id": "abc",
        "properties": {
            "Task Name": {"title": [{"plain_text": "Write blog post"}]},
            "Type": {"select": {"name": "automation"}},
        },
    }
    details = task_details(task)
    assert details == {"id": "abc", "name": "Write blog post", "type": "automation", "cost": 1}


def test_task_details_handles_missing_properties():
    task = {"id": "abc", "properties": {}}
    details = task_details(task)
    assert details == {"id": "abc", "name": "Unnamed Task", "type": None, "cost": 10}


def test_require_env_returns_values_when_all_present(monkeypatch):
    monkeypatch.setenv("FOO", "bar")
    assert require_env("FOO") == {"FOO": "bar"}


def test_require_env_raises_when_missing(monkeypatch):
    monkeypatch.delenv("MISSING_VAR", raising=False)
    with pytest.raises(SystemExit):
        require_env("MISSING_VAR")
