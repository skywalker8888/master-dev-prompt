import json

from fastapi.testclient import TestClient

import app as app_module


def test_health_reports_mock_when_api_key_missing(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("MOCK_OUTPUT", raising=False)
    client = TestClient(app_module.app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["prompt_loaded"] is True
    assert body["mock"] is True


def test_health_reports_live_when_api_key_set(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.delenv("MOCK_OUTPUT", raising=False)
    client = TestClient(app_module.app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["mock"] is False


def test_process_returns_sample_json_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("MOCK_OUTPUT", raising=False)
    client = TestClient(app_module.app)
    response = client.post("/process", json={"transcript": "hello from vercel"})
    assert response.status_code == 200
    result = response.json()["result"]
    assert "design_doc" in result
    assert "actions" in result
    assert "agent_task_report" in result


def test_process_mock_flag_wins_over_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("MOCK_OUTPUT", "1")
    client = TestClient(app_module.app)
    response = client.post("/process", json={"transcript": "hello"})
    assert response.status_code == 200
    assert "design_doc" in response.json()["result"]


def test_process_stream_emits_mock_result(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    client = TestClient(app_module.app)
    response = client.post("/process/stream", json={"transcript": "stream me"})
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    done = None
    for line in response.text.splitlines():
        if not line.startswith("data: "):
            continue
        payload = json.loads(line[6:])
        if payload.get("done"):
            done = payload
    assert done is not None
    assert done["mock"] is True
    assert "design_doc" in done["result"]
