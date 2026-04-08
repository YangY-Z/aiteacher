"""Grade and related domain models for DDD design."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class GradeLevel(str, Enum):
    """Grade level enumeration.

    Represents different educational stages.
    """

    PRIMARY = "primary"  # 小学
    MIDDLE = "middle"  # 初中
    HIGH = "high"  # 高中


class Status(str, Enum):
    """Status enumeration for entities.

    Represents the lifecycle status of an entity.
    """

    ACTIVE = "active"  # 启用
    INACTIVE = "inactive"  # 停用
    DRAFT = "draft"  # 草稿
    ARCHIVED = "archived"  # 归档


@dataclass
class GradeSubject:
    """Grade-Subject association entity.

    Represents the relationship between a grade and a subject.
    Belongs to the Grade aggregate.

    Attributes:
        id: Unique identifier for the association.
        grade_id: ID of the grade.
        subject_id: ID of the subject.
        sort_order: Display order of the subject within this grade.
        status: Status of the subject within this grade.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    id: str
    grade_id: str
    subject_id: str
    sort_order: int = 0
    status: Status = Status.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary.

        Returns:
            Dictionary representation of the association.
        """
        return {
            "id": self.id,
            "grade_id": self.grade_id,
            "subject_id": self.subject_id,
            "sort_order": self.sort_order,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GradeSubject":
        """Create from dictionary.

        Args:
            data: Dictionary containing association data.

        Returns:
            GradeSubject instance.
        """
        return cls(
            id=data["id"],
            grade_id=data["grade_id"],
            subject_id=data["subject_id"],
            sort_order=data.get("sort_order", 0),
            status=Status(data.get("status", "active")),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


@dataclass
class Grade:
    """Grade aggregate root.

    Represents an educational grade level (e.g., "初一", "高一").

    Attributes:
        id: Unique identifier (format: G_{code}, e.g., G_C1, G_S1).
        name: Display name (e.g., "初一", "高一").
        code: Short code (e.g., "C1", "S1").
        level: Educational level (primary, middle, high).
        subjects: List of subjects associated with this grade.
        sort_order: Display order.
        description: Optional description.
        status: Status of the grade.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    id: str
    name: str
    code: str
    level: GradeLevel
    subjects: list[GradeSubject] = field(default_factory=list)
    sort_order: int = 0
    description: Optional[str] = None
    status: Status = Status.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_subject(self, subject_id: str, sort_order: int = 0) -> GradeSubject:
        """Add a subject to this grade.

        Args:
            subject_id: ID of the subject to add.
            sort_order: Display order of the subject.

        Returns:
            The created GradeSubject association.
        """
        association_id = f"GS_{self.id}_{subject_id}"
        association = GradeSubject(
            id=association_id,
            grade_id=self.id,
            subject_id=subject_id,
            sort_order=sort_order,
        )
        self.subjects.append(association)
        self.updated_at = datetime.now()
        return association

    def remove_subject(self, subject_id: str) -> bool:
        """Remove a subject from this grade.

        Args:
            subject_id: ID of the subject to remove.

        Returns:
            True if removed, False if not found.
        """
        for i, subject in enumerate(self.subjects):
            if subject.subject_id == subject_id:
                self.subjects.pop(i)
                self.updated_at = datetime.now()
                return True
        return False

    def to_dict(self) -> dict:
        """Convert to dictionary.

        Returns:
            Dictionary representation of the grade.
        """
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "level": self.level.value,
            "subjects": [s.to_dict() for s in self.subjects],
            "sort_order": self.sort_order,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Grade":
        """Create from dictionary.

        Args:
            data: Dictionary containing grade data.

        Returns:
            Grade instance.
        """
        subjects = [GradeSubject.from_dict(s) for s in data.get("subjects", [])]
        return cls(
            id=data["id"],
            name=data["name"],
            code=data["code"],
            level=GradeLevel(data["level"]),
            subjects=subjects,
            sort_order=data.get("sort_order", 0),
            description=data.get("description"),
            status=Status(data.get("status", "active")),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )
