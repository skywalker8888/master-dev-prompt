#!/usr/bin/env python3
"""
watcher.py — Autopilot file watcher for Master Developer Prompt Kit.

Watches transcripts/ for new .txt files and automatically runs
run_master_dev.sh, writing output to outputs/.

Usage:
    python3 watcher.py
    python3 watcher.py --transcripts ./transcripts --outputs ./outputs
"""

import argparse
import logging
import subprocess
import sys
import time
from pathlib import Path

from watchdog.events import FileCreatedEvent, FileSystemEventHandler
from watchdog.observers import Observer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

_SCRIPT = Path(__file__).parent / "run_master_dev.sh"
_VALIDATOR = Path(__file__).parent / "validate_output.py"


def should_process(txt_path: Path, outputs_dir: Path) -> bool:
    """Return True if txt_path is a .txt without a corresponding .json output."""
    if txt_path.suffix != ".txt":
        return False
    output = get_output_path(txt_path, outputs_dir)
    return not output.exists()


def get_output_path(txt_path: Path, outputs_dir: Path) -> Path:
    """Return the expected .json output path for a given .txt transcript."""
    return outputs_dir / (txt_path.stem + ".json")


def process_transcript(
    txt_path: Path,
    outputs_dir: Path,
    script: Path = _SCRIPT,
    validator: Path = _VALIDATOR,
) -> None:
    """Run run_master_dev.sh on txt_path, saving output to outputs_dir.

    Validates the JSON schema after generation; invalid outputs are saved as
    .invalid.json (matching batch_run_master_dev.sh behaviour).
    """
    output_json = get_output_path(txt_path, outputs_dir)
    output_tmp = outputs_dir / (txt_path.stem + ".tmp.json")
    output_invalid = outputs_dir / (txt_path.stem + ".invalid.json")
    log_file = outputs_dir / (txt_path.stem + ".log")

    log.info("Processing: %s → %s", txt_path.name, output_json.name)

    result = subprocess.run(
        [str(script), str(txt_path)],
        capture_output=True,
        text=True,
    )

    log_file.write_text(result.stderr)

    if result.returncode != 0:
        log.error("Failed: %s (exit %d). See %s", txt_path.name, result.returncode, log_file)
        return

    output_tmp.write_text(result.stdout)

    if validator.exists():
        val_result = subprocess.run(
            ["python3", str(validator), str(output_tmp)],
            capture_output=True,
            text=True,
        )
        if val_result.returncode != 0:
            output_tmp.rename(output_invalid)
            log.error("Invalid schema: %s → %s", txt_path.name, output_invalid.name)
            return

    output_tmp.rename(output_json)
    log.info("Done: %s", output_json)


class TranscriptHandler(FileSystemEventHandler):
    def __init__(self, outputs_dir: Path, script: Path = _SCRIPT):
        self.outputs_dir = outputs_dir
        self.script = script

    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return
        txt = Path(event.src_path)
        if should_process(txt, self.outputs_dir):
            process_transcript(txt, self.outputs_dir, self.script)


def main() -> None:
    parser = argparse.ArgumentParser(description="Autopilot watcher for transcript processing")
    parser.add_argument("--transcripts", default="transcripts", help="Directory to watch")
    parser.add_argument("--outputs", default="outputs", help="Directory for output JSON files")
    args = parser.parse_args()

    transcripts_dir = Path(args.transcripts).resolve()
    outputs_dir = Path(args.outputs).resolve()

    if not transcripts_dir.exists():
        log.error("Transcripts directory not found: %s", transcripts_dir)
        sys.exit(1)

    outputs_dir.mkdir(parents=True, exist_ok=True)

    log.info("Watching %s for new transcripts...", transcripts_dir)
    log.info("Outputs will be written to %s", outputs_dir)

    handler = TranscriptHandler(outputs_dir=outputs_dir)
    observer = Observer()
    observer.schedule(handler, str(transcripts_dir), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Stopping watcher.")
        observer.stop()

    observer.join()


if __name__ == "__main__":
    main()
