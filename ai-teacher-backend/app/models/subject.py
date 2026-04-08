"""Subject domain model for DDD design."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from app.models.grade import Status


class SubjectCategory(str, Enum):
    """Subject category enumeration.

    Represents different categories of subjects.
    """

    SCIENCE = "science"  # 理科
    ARTS = "arts"  # 文科
    LANGUAGE = "language"  # 语言
    COMPREHENSIVE = "comprehensive"  # 综合


@dataclass
class Subject:
    """Subject aggregate root.

    Represents an academic subject (e.g., "数学", "语文").

    Attributes:
        id: Unique identifier (format: S_{code}, e.g., S_MATH, S_CHINESE).
        name: Display name (e.g., "数学", "语文").
        code: Short code (e.g., "MATH", "CHINESE").
        category: Subject category.
        icon: Optional icon URL or identifier.
        color: Optional theme color.
        sort_order: Display order.
        description: Optional description.
        status: Status of the subject.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    id: str
    name: str
    code: str
    category: SubjectCategory
    icon: Optional[str] = None
    color: Optional[str] = None
    sort_order: int = 0
    description: Optional[str] = None
    status: Status = Status.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary.

        Returns:
            Dictionary representation of the subject.
        """
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "category": self.category.value,
            "icon": self.icon,
            "color": self.color,
            "sort_order": self.sort_order,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Subject":
        """Create from dictionary.

        Args:
            data: Dictionary containing subject data.

        Returns:
            Subject instance.
        """
        return cls(
            id=data["id"],
            name=data["name"],
            code=data["code"],
            category=SubjectCategory(data["category"]),
            icon=data.get("icon"),
            color=data.get("color"),
            sort_order=data.get("sort_order", 0),
            description=data.get("description"),
            status=Status(data.get("status", "active")),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )
