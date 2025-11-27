"""Data models for FlowPath application."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Step:
    """Represents a single step in a path."""
    id: Optional[int] = None
    path_id: Optional[int] = None
    step_number: int = 1
    screenshot_path: Optional[str] = None
    instructions: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return {
            "step_number": self.step_number,
            "screenshot_path": self.screenshot_path,
            "instructions": self.instructions
        }

    @classmethod
    def from_dict(cls, data: dict, path_id: Optional[int] = None) -> "Step":
        """Create Step from dictionary (JSON import)."""
        return cls(
            path_id=path_id,
            step_number=data.get("step_number", 1),
            screenshot_path=data.get("screenshot_path"),
            instructions=data.get("instructions", "")
        )


@dataclass
class Path:
    """Represents a documentation path."""
    id: Optional[int] = None
    title: str = ""
    category: str = ""
    tags: str = ""  # Comma-separated tags
    description: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    steps: list[Step] = field(default_factory=list)

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def get_tags_list(self) -> list[str]:
        """Return tags as a list."""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(",") if tag.strip()]

    def set_tags_from_list(self, tags: list[str]):
        """Set tags from a list."""
        self.tags = ", ".join(tags)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return {
            "title": self.title,
            "category": self.category,
            "tags": self.get_tags_list(),
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "steps": [step.to_dict() for step in self.steps]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Path":
        """Create Path from dictionary (JSON import)."""
        path = cls(
            title=data.get("title", ""),
            category=data.get("category", ""),
            description=data.get("description", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        )

        # Handle tags - could be list or string
        tags = data.get("tags", [])
        if isinstance(tags, list):
            path.set_tags_from_list(tags)
        else:
            path.tags = tags

        # Load steps
        for step_data in data.get("steps", []):
            path.steps.append(Step.from_dict(step_data))

        return path
