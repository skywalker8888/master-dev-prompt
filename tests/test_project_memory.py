import json
import pytest
from zos.memory.state import ProjectMemoryService
from zos.memory.loader import ProjectMemoryError


VALID = {
    "project_id": "founder-os",
    "project_name": "Founder Operating System",
    "current_phase": "Execution",
    "objectives": ["Build minimum loop"],
    "tasks": ["WP001-T001"],
    "decisions": ["Capability-based routing"],
}


def make_project(tmp_path, data: dict) -> ProjectMemoryService:
    project_id = data.get("project_id", "test-project")
    (tmp_path / f"{project_id}.json").write_text(json.dumps(data))
    return ProjectMemoryService(projects_dir=tmp_path)


def test_load_by_id(tmp_path):
    svc = make_project(tmp_path, VALID)
    project = svc.get_by_id("founder-os")
    assert project is not None
    assert project.project_id == "founder-os"


def test_load_by_name(tmp_path):
    svc = make_project(tmp_path, VALID)
    project = svc.get_by_name("Founder Operating System")
    assert project is not None
    assert project.project_name == "Founder Operating System"


def test_id_first_resolution(tmp_path):
    svc = make_project(tmp_path, VALID)
    project = svc.get("founder-os")
    assert project is not None
    assert project.project_id == "founder-os"


def test_name_resolution(tmp_path):
    svc = make_project(tmp_path, VALID)
    project = svc.get("Founder Operating System")
    assert project is not None


def test_missing_id_returns_none(tmp_path):
    svc = make_project(tmp_path, VALID)
    assert svc.get_by_id("does-not-exist") is None


def test_missing_name_returns_none(tmp_path):
    svc = make_project(tmp_path, VALID)
    assert svc.get_by_name("Ghost Project") is None


def test_optional_fields_empty_when_absent(tmp_path):
    minimal = {"project_id": "min", "project_name": "Minimal"}
    svc = make_project(tmp_path, minimal)
    project = svc.get("min")
    assert project.blockers == []
    assert project.history == []
    assert project.lessons_learned == []
    assert project.last_updated is None


def test_known_fields_preserved(tmp_path):
    svc = make_project(tmp_path, VALID)
    project = svc.get("founder-os")
    assert "WP001-T001" in project.tasks
    assert project.current_phase == "Execution"


def test_malformed_json_raises_error(tmp_path):
    (tmp_path / "bad.json").write_text("{ this is not json }")
    svc = ProjectMemoryService(projects_dir=tmp_path)
    with pytest.raises(ProjectMemoryError, match="Malformed JSON"):
        svc.get_by_id("bad")


def test_missing_project_id_raises_error(tmp_path):
    data = {"project_name": "No ID Project"}
    (tmp_path / "no-id.json").write_text(json.dumps(data))
    svc = ProjectMemoryService(projects_dir=tmp_path)
    with pytest.raises(ProjectMemoryError, match="project_id"):
        svc.get_by_id("no-id")


def test_missing_project_name_raises_error(tmp_path):
    data = {"project_id": "no-name"}
    (tmp_path / "no-name.json").write_text(json.dumps(data))
    svc = ProjectMemoryService(projects_dir=tmp_path)
    with pytest.raises(ProjectMemoryError, match="project_name"):
        svc.get_by_id("no-name")
