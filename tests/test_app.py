from app import _get_anthropic_model


def test_get_anthropic_model_defaults_to_supported_sonnet(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)

    assert _get_anthropic_model() == "claude-sonnet-5"


def test_get_anthropic_model_allows_env_override(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-haiku-4.5")

    assert _get_anthropic_model() == "claude-haiku-4.5"
