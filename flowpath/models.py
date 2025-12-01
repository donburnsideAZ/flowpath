"""Data models for FlowPath application."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import uuid


@dataclass
class Step:
    """A single step in a workflow path."""
    instructions: str
    screenshot_path: Optional[str] = None
    step_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "instructions": self.instructions,
            "screenshot_path": self.screenshot_path,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Step":
        return cls(
            step_id=data.get("step_id", str(uuid.uuid4())),
            instructions=data.get("instructions", ""),
            screenshot_path=data.get("screenshot_path"),
            created_at=data.get("created_at", datetime.now().isoformat()),
        )


@dataclass
class Path:
    """A workflow path containing multiple steps."""
    title: str
    category: str = ""
    tags: list = field(default_factory=list)
    description: str = ""
    steps: list = field(default_factory=list)  # List of Step objects
    path_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    is_creator: bool = True

    def to_dict(self) -> dict:
        return {
            "path_id": self.path_id,
            "title": self.title,
            "category": self.category,
            "tags": self.tags,
            "description": self.description,
            "steps": [step.to_dict() for step in self.steps],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_creator": self.is_creator,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Path":
        steps = [Step.from_dict(s) for s in data.get("steps", [])]
        return cls(
            path_id=data.get("path_id", str(uuid.uuid4())),
            title=data.get("title", ""),
            category=data.get("category", ""),
            tags=data.get("tags", []),
            description=data.get("description", ""),
            steps=steps,
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            is_creator=data.get("is_creator", True),
        )

    def add_step(self, step: Step):
        """Add a step to the path."""
        self.steps.append(step)
        self.updated_at = datetime.now().isoformat()

    def get_tags_string(self) -> str:
        """Return tags as comma-separated string."""
        return ", ".join(self.tags)

    def set_tags_from_string(self, tags_str: str):
        """Set tags from comma-separated string."""
        self.tags = [t.strip() for t in tags_str.split(",") if t.strip()]
