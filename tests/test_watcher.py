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


def test_should_process_accepts_uppercase_txt_extension(tmp_path):
    from watcher import should_process
    txt = tmp_path / "MEETING.TXT"
    txt.write_text("hello")
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    assert should_process(txt, outputs_dir) is True


def test_process_transcript_creates_outputs_dir(tmp_path):
    from watcher import process_transcript
    txt = tmp_path / "meeting.txt"
    txt.write_text("transcript content")
    outputs_dir = tmp_path / "outputs"
    script = tmp_path / "run_master_dev.sh"
    script.write_text("#!/bin/bash\necho '{}'\n")
    script.chmod(0o755)

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="{}", stderr="")
        process_transcript(txt, outputs_dir, script)
        assert outputs_dir.exists()
        mock_run.assert_called_once()


def test_main_processes_existing_transcripts_on_startup(tmp_path, monkeypatch):
    import sys

    import watcher

    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    existing = transcripts_dir / "meeting.txt"
    existing.write_text("hello")
    outputs_dir = tmp_path / "outputs"

    fake_observer = MagicMock()
    monkeypatch.setattr(watcher, "Observer", lambda: fake_observer)
    process_mock = MagicMock()
    monkeypatch.setattr(watcher, "process_transcript", process_mock)
    monkeypatch.setattr(watcher.time, "sleep", lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    monkeypatch.setattr(sys, "argv", ["watcher.py", "--transcripts", str(transcripts_dir), "--outputs", str(outputs_dir)])

    watcher.main()

    process_mock.assert_called_once_with(existing, outputs_dir)
    fake_observer.start.assert_called_once()
    fake_observer.stop.assert_called_once()
    fake_observer.join.assert_called_once()


def test_get_output_path(tmp_path):
    from watcher import get_output_path
    txt = tmp_path / "my-meeting.txt"
    outputs_dir = tmp_path / "outputs"
    result = get_output_path(txt, outputs_dir)
    assert result == outputs_dir / "my-meeting.json"


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
