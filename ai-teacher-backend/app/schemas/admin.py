"""Admin API schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.student import UserRole


class AdminLogin(BaseModel):
    """Admin login request."""

    phone: str = Field(..., description="Admin phone number")
    password: str = Field(..., description="Admin password")


class AdminResponse(BaseModel):
    """Admin user response."""

    id: int
    name: str
    phone: Optional[str] = None
    role: UserRole = UserRole.ADMIN
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_domain(cls, student) -> "AdminResponse":
        """Create from domain model."""
        return cls(
            id=student.id,
            name=student.name,
            phone=student.phone,
            role=student.role,
            created_at=student.created_at,
        )


class AdminToken(BaseModel):
    """Admin authentication token response."""

    access_token: str
    token_type: str = "bearer"
    admin_id: int
    admin_name: str
    role: UserRole = UserRole.ADMIN
