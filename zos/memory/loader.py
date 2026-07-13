import json
from pathlib import Path
from typing import Optional

from zos.memory.models import ProjectMemory


class ProjectMemoryError(Exception):
    pass


def load_project_by_id(
    project_id: str, projects_dir: Path
) -> Optional[ProjectMemory]:
    path = projects_dir / f"{project_id}.json"
    if not path.exists():
        return None
    return _parse(path)


def load_project_by_name(
    project_name: str, projects_dir: Path
) -> Optional[ProjectMemory]:
    if not projects_dir.exists():
        return None
    for path in projects_dir.glob("*.json"):
        try:
            raw = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            raise ProjectMemoryError(
                f"Malformed JSON in {path.name}: {e}"
            ) from e
        if raw.get("project_name", "").casefold() == project_name.casefold():
            return _build(raw, path)
    return None


def _parse(path: Path) -> ProjectMemory:
    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise ProjectMemoryError(
            f"Malformed JSON in {path.name}: {e}"
        ) from e
    return _build(raw, path)


def _build(raw: dict, path: Path) -> ProjectMemory:
    project_id = raw.get("project_id", "").strip()
    project_name = raw.get("project_name", "").strip()

    if not project_id:
        raise ProjectMemoryError(
            f"Missing required field 'project_id' in {path.name}"
        )
    if not project_name:
        raise ProjectMemoryError(
            f"Missing required field 'project_name' in {path.name}"
        )

    return ProjectMemory(
        project_id=project_id,
        project_name=project_name,
        current_phase=raw.get("current_phase", ""),
        objectives=raw.get("objectives", []),
        architecture=raw.get("architecture", ""),
        tasks=raw.get("tasks", []),
        decisions=raw.get("decisions", []),
        blockers=raw.get("blockers", []),
        progress=raw.get("progress", ""),
        assigned_specialists=raw.get("assigned_specialists", []),
        history=raw.get("history", []),
        lessons_learned=raw.get("lessons_learned", []),
        last_updated=raw.get("last_updated"),
    )
