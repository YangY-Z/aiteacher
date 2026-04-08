"""Student domain model."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class StudentStatus(str, Enum):
    """Student account status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    BANNED = "banned"


class UserRole(str, Enum):
    """User role types."""

    STUDENT = "student"
    ADMIN = "admin"


class Grade(str, Enum):
    """Student grade levels."""

    GRADE_7 = "初一"
    GRADE_8 = "初二"
    GRADE_9 = "初三"
    GRADE_10 = "高一"
    GRADE_11 = "高二"
    GRADE_12 = "高三"


@dataclass
class Student:
    """Student domain model.

    Represents a student user in the system.
    """

    id: int
    name: str
    grade: Grade
    password_hash: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    status: StudentStatus = StudentStatus.ACTIVE
    role: UserRole = UserRole.STUDENT
    last_login_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update_last_login(self) -> None:
        """Update last login timestamp to now."""
        self.last_login_at = datetime.now()
        self.updated_at = datetime.now()

    def is_active(self) -> bool:
        """Check if student account is active."""
        return self.status == StudentStatus.ACTIVE

    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == UserRole.ADMIN
