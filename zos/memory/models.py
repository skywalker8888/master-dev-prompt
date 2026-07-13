from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ProjectMemory:
    project_id: str
    project_name: str
    current_phase: str = ""
    objectives: List[str] = field(default_factory=list)
    architecture: str = ""
    tasks: List[str] = field(default_factory=list)
    decisions: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    progress: str = ""
    assigned_specialists: List[str] = field(default_factory=list)
    history: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    last_updated: Optional[str] = None
