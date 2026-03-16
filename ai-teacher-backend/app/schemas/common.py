"""Common Pydantic schemas for API responses."""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Schema for pagination metadata."""

    page: int = 1
    page_size: int = 20
    total: int
    total_pages: int


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""

    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    meta: Optional[PaginationMeta] = None

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Schema for error response."""

    success: bool = False
    error_code: str
    message: str
    details: Optional[dict[str, Any]] = None


class HealthCheckResponse(BaseModel):
    """Schema for health check response."""

    status: str = "ok"
    version: str
    environment: str
