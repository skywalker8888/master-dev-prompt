from pathlib import Path
from typing import Optional

from zos.memory.loader import load_project_by_id, load_project_by_name
from zos.memory.models import ProjectMemory

DEFAULT_PROJECTS_DIR = Path(__file__).parent / "data"


class ProjectMemoryService:
    def __init__(self, projects_dir: Optional[Path] = None):
        self.projects_dir = projects_dir or DEFAULT_PROJECTS_DIR

    def get_by_id(self, project_id: str) -> Optional[ProjectMemory]:
        return load_project_by_id(project_id, self.projects_dir)

    def get_by_name(self, project_name: str) -> Optional[ProjectMemory]:
        return load_project_by_name(project_name, self.projects_dir)

    def get(self, identifier: str) -> Optional[ProjectMemory]:
        result = self.get_by_id(identifier)
        if result is None:
            result = self.get_by_name(identifier)
        return result
