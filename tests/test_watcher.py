import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest


def test_should_process_returns_true_for_new_txt(tmp_path):
    from watcher import should_process
    txt = tmp_path / "meeting.txt"
    txt.write_text("hello")
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    assert should_process(txt, outputs_dir) is True


def test_should_process_returns_false_if_json_exists(tmp_path):
    from watcher import should_process
    txt = tmp_path / "meeting.txt"
    txt.write_text("hello")
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    (outputs_dir / "meeting.json").write_text("{}")
    assert should_process(txt, outputs_dir) is False


def test_should_process_returns_false_for_non_txt(tmp_path):
    from watcher import should_process
    f = tmp_path / "meeting.md"
    f.write_text("hello")
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    assert should_process(f, outputs_dir) is False


def test_get_output_path(tmp_path):
    from watcher import get_output_path
    txt = tmp_path / "my-meeting.txt"
    outputs_dir = tmp_path / "outputs"
    result = get_output_path(txt, outputs_dir)
    assert result == outputs_dir / "my-meeting.json"


def test_resolve_io_dirs_defaults(tmp_path, monkeypatch):
    from watcher import resolve_io_dirs
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("MASTER_DEV_TRANSCRIPTS_DIR", raising=False)
    monkeypatch.delenv("MASTER_DEV_OUTPUTS_DIR", raising=False)
    monkeypatch.delenv("OBSIDIAN_VAULT_PATH", raising=False)
    monkeypatch.delenv("OBSIDIAN_TRANSCRIPTS_SUBDIR", raising=False)
    monkeypatch.delenv("OBSIDIAN_OUTPUTS_SUBDIR", raising=False)

    transcripts_dir, outputs_dir = resolve_io_dirs()

    assert transcripts_dir == (tmp_path / "transcripts").resolve()
    assert outputs_dir == (tmp_path / "outputs").resolve()


def test_resolve_io_dirs_prefers_explicit_args(tmp_path, monkeypatch):
    from watcher import resolve_io_dirs
    monkeypatch.setenv("MASTER_DEV_TRANSCRIPTS_DIR", str(tmp_path / "env-transcripts"))
    monkeypatch.setenv("MASTER_DEV_OUTPUTS_DIR", str(tmp_path / "env-outputs"))

    transcripts_dir, outputs_dir = resolve_io_dirs("./cli-transcripts", "./cli-outputs")

    assert transcripts_dir == Path("./cli-transcripts").resolve()
    assert outputs_dir == Path("./cli-outputs").resolve()


def test_resolve_io_dirs_uses_master_dev_env_over_vault(tmp_path, monkeypatch):
    from watcher import resolve_io_dirs
    monkeypatch.setenv("MASTER_DEV_TRANSCRIPTS_DIR", str(tmp_path / "env-transcripts"))
    monkeypatch.setenv("MASTER_DEV_OUTPUTS_DIR", str(tmp_path / "env-outputs"))
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path / "vault"))

    transcripts_dir, outputs_dir = resolve_io_dirs()

    assert transcripts_dir == (tmp_path / "env-transcripts").resolve()
    assert outputs_dir == (tmp_path / "env-outputs").resolve()


def test_resolve_io_dirs_uses_obsidian_vault_subdirs(tmp_path, monkeypatch):
    from watcher import resolve_io_dirs
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path / "vault"))
    monkeypatch.setenv("OBSIDIAN_TRANSCRIPTS_SUBDIR", "Meetings/Inbox")
    monkeypatch.setenv("OBSIDIAN_OUTPUTS_SUBDIR", "Meetings/Structured")

    transcripts_dir, outputs_dir = resolve_io_dirs()

    assert transcripts_dir == (tmp_path / "vault" / "Meetings" / "Inbox").resolve()
    assert outputs_dir == (tmp_path / "vault" / "Meetings" / "Structured").resolve()


def test_process_transcript_calls_script(tmp_path):
    from watcher import process_transcript
    txt = tmp_path / "meeting.txt"
    txt.write_text("transcript content")
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    script = tmp_path / "run_master_dev.sh"
    script.write_text("#!/bin/bash\necho '{}'")
    script.chmod(0o755)

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="{}", stderr="")
        process_transcript(txt, outputs_dir, script)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert str(script) in args
        assert str(txt) in args
