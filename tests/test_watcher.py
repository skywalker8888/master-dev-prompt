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
        # Pass a non-existent validator to isolate script-call behaviour
        process_transcript(txt, outputs_dir, script, validator=tmp_path / "no_validator.py")
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert str(script) in args
        assert str(txt) in args


def test_process_transcript_validates_output(tmp_path):
    from watcher import process_transcript
    txt = tmp_path / "meeting.txt"
    txt.write_text("transcript content")
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    script = tmp_path / "run_master_dev.sh"
    validator = tmp_path / "validate_output.py"
    validator.write_text("# stub")

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="{}", stderr="")
        process_transcript(txt, outputs_dir, script, validator=validator)
        assert mock_run.call_count == 2
        val_args = mock_run.call_args_list[1][0][0]
        assert str(validator) in val_args


def test_process_transcript_saves_invalid_on_schema_error(tmp_path):
    from watcher import process_transcript
    txt = tmp_path / "meeting.txt"
    txt.write_text("transcript content")
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    script = tmp_path / "run_master_dev.sh"
    validator = tmp_path / "validate_output.py"
    validator.write_text("# stub")

    def side_effect(cmd, **kwargs):
        if str(validator) in cmd:
            return MagicMock(returncode=1, stdout="", stderr="INVALID: missing key")
        return MagicMock(returncode=0, stdout="{}", stderr="")

    with patch("subprocess.run", side_effect=side_effect):
        process_transcript(txt, outputs_dir, script, validator=validator)
        assert not (outputs_dir / "meeting.json").exists()
        assert (outputs_dir / "meeting.invalid.json").exists()
