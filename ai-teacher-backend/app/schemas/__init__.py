"""Pydantic schemas module."""

from app.schemas.student import (
    StudentCreate,
    StudentLogin,
    StudentResponse,
    Token,
    TokenPayload,
)
from app.schemas.course import (
    CourseResponse,
    KnowledgePointResponse,
    DependencyResponse,
)
from app.schemas.learning import (
    StartSessionRequest,
    SessionResponse,
    ProgressResponse,
    ChatRequest,
    ChatResponse,
    AssessmentRequest,
    AssessmentResponse,
    SkipRequest,
)
from app.schemas.common import APIResponse, PaginationMeta

__all__ = [
    # Student schemas
    "StudentCreate",
    "StudentLogin",
    "StudentResponse",
    "Token",
    "TokenPayload",
    # Course schemas
    "CourseResponse",
    "KnowledgePointResponse",
    "DependencyResponse",
    # Learning schemas
    "StartSessionRequest",
    "SessionResponse",
    "ProgressResponse",
    "ChatRequest",
    "ChatResponse",
    "AssessmentRequest",
    "AssessmentResponse",
    "SkipRequest",
    # Common schemas
    "APIResponse",
    "PaginationMeta",
]