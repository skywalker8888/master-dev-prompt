def test_get_anthropic_model_uses_default_when_env_missing(monkeypatch):
    from app import DEFAULT_ANTHROPIC_MODEL, _get_anthropic_model

    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    assert _get_anthropic_model() == DEFAULT_ANTHROPIC_MODEL


def test_get_anthropic_model_uses_env_override(monkeypatch):
    from app import _get_anthropic_model

    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-sonnet-5")
    assert _get_anthropic_model() == "claude-sonnet-5"
