import asyncio
import json
from types import SimpleNamespace

import app


class _FakeStream:
    def __init__(self, chunks):
        self.text_stream = chunks

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_process_transcript_uses_supported_default_model(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)

    captured = {}

    class FakeClient:
        def __init__(self, api_key):
            assert api_key == "test-key"
            self.messages = self

        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                content=[SimpleNamespace(text=json.dumps({"status": "ok"}))]
            )

    monkeypatch.setattr(app.anthropic, "Anthropic", FakeClient)

    response = app.process_transcript(app.ProcessRequest(transcript="hello"), None)

    assert response.result == {"status": "ok"}
    assert captured["model"] == "claude-sonnet-5"


def test_process_transcript_stream_honors_model_override(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-sonnet-5-20260701")

    captured = {}

    class FakeClient:
        def __init__(self, api_key):
            assert api_key == "test-key"
            self.messages = self

        def stream(self, **kwargs):
            captured.update(kwargs)
            return _FakeStream([json.dumps({"status": "ok"})])

    monkeypatch.setattr(app.anthropic, "Anthropic", FakeClient)

    response = app.process_transcript_stream(app.ProcessRequest(transcript="hello"), None)
    events = asyncio.run(_collect_events(response.body_iterator))

    assert captured["model"] == "claude-sonnet-5-20260701"
    assert any('"done": true' in event for event in events)


async def _collect_events(body_iterator):
    return [event async for event in body_iterator]
