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
from app.schemas.learner_profile import (
    LearnerTypeInfo,
    LearnerTypeListResponse,
    ErrorPatternSchema,
    LearnerMetricsSchema,
    LearnerMetricsUpdate,
    TeachingStrategySchema,
    LearningPreferenceSchema,
    LearningPreferenceUpdate,
    LearnerProfileResponse,
    LearnerProfileCreate,
    LearnerClassifyRequest,
    LearnerClassifyResponse,
    TypeHistoryEntry,
    LearnerTypeHistoryResponse,
    AddErrorPatternRequest,
    ErrorPatternSummary,
    ErrorPatternAnalysisResponse,
)

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
    # Learner profile schemas
    "LearnerTypeInfo",
    "LearnerTypeListResponse",
    "ErrorPatternSchema",
    "LearnerMetricsSchema",
    "LearnerMetricsUpdate",
    "TeachingStrategySchema",
    "LearningPreferenceSchema",
    "LearningPreferenceUpdate",
    "LearnerProfileResponse",
    "LearnerProfileCreate",
    "LearnerClassifyRequest",
    "LearnerClassifyResponse",
    "TypeHistoryEntry",
    "LearnerTypeHistoryResponse",
    "AddErrorPatternRequest",
    "ErrorPatternSummary",
    "ErrorPatternAnalysisResponse",
]