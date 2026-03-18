"""Learner profile Pydantic schemas for API interfaces."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# ==================== Learner Type Schemas ====================


class LearnerTypeInfo(BaseModel):
    """Schema for learner type information."""

    type: str = Field(..., description="学习者类型")
    description: str = Field(..., description="类型描述")


class LearnerTypeListResponse(BaseModel):
    """Schema for list of all learner types."""

    types: list[LearnerTypeInfo] = Field(..., description="学习者类型列表")


# ==================== Metrics Schemas ====================


class ErrorPatternSchema(BaseModel):
    """Schema for error pattern."""

    pattern_type: str = Field(..., description="错误模式类型")
    frequency: int = Field(..., description="出现频率")
    last_occurrence: datetime = Field(..., description="最近出现时间")
    examples: list[str] = Field(default_factory=list, description="示例")


class LearnerMetricsSchema(BaseModel):
    """Schema for learner metrics."""

    prerequisite_mastery: float = Field(
        ..., ge=0.0, le=1.0, description="前置知识掌握度"
    )
    current_kp_mastery: float = Field(
        ..., ge=0.0, le=1.0, description="当前知识点掌握度"
    )
    learning_velocity: float = Field(
        default=0.5, ge=0.0, le=1.0, description="学习速度"
    )
    error_patterns: list[ErrorPatternSchema] = Field(
        default_factory=list, description="错误模式列表"
    )
    total_learning_time: int = Field(default=0, description="总学习时间(秒)")
    total_sessions: int = Field(default=0, description="总会话数")
    average_score: float = Field(default=0.0, ge=0.0, le=1.0, description="平均得分")
    questions_answered: int = Field(default=0, description="已答题数")
    questions_correct: int = Field(default=0, description="正确题数")

    @classmethod
    def from_domain(cls, metrics: Any) -> "LearnerMetricsSchema":
        """Create schema from domain model."""
        return cls(
            prerequisite_mastery=metrics.prerequisite_mastery,
            current_kp_mastery=metrics.current_kp_mastery,
            learning_velocity=metrics.learning_velocity,
            error_patterns=[
                ErrorPatternSchema(
                    pattern_type=ep.pattern_type.value,
                    frequency=ep.frequency,
                    last_occurrence=ep.last_occurrence,
                    examples=ep.examples,
                )
                for ep in metrics.error_patterns
            ],
            total_learning_time=metrics.total_learning_time,
            total_sessions=metrics.total_sessions,
            average_score=metrics.average_score,
            questions_answered=metrics.questions_answered,
            questions_correct=metrics.questions_correct,
        )


class LearnerMetricsUpdate(BaseModel):
    """Schema for updating learner metrics."""

    prerequisite_mastery: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="前置知识掌握度"
    )
    current_kp_mastery: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="当前知识点掌握度"
    )
    learning_velocity: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="学习速度"
    )
    score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="新得分(用于更新平均分)"
    )


# ==================== Teaching Strategy Schemas ====================


class TeachingStrategySchema(BaseModel):
    """Schema for teaching strategy."""

    learner_type: str = Field(..., description="学习者类型")
    primary_strategy: str = Field(..., description="主要教学策略")
    secondary_strategies: list[str] = Field(
        default_factory=list, description="辅助策略"
    )
    example_count: int = Field(default=2, description="示例数量")
    practice_count: int = Field(default=3, description="练习数量")
    hint_level: int = Field(default=2, ge=1, le=3, description="提示级别")
    pacing: str = Field(default="normal", description="教学节奏")
    focus_areas: list[str] = Field(default_factory=list, description="重点领域")
    scaffolding: bool = Field(default=True, description="是否需要脚手架支持")

    @classmethod
    def from_domain(cls, strategy: Any) -> "TeachingStrategySchema":
        """Create schema from domain model."""
        return cls(
            learner_type=strategy.learner_type.value,
            primary_strategy=strategy.primary_strategy,
            secondary_strategies=strategy.secondary_strategies,
            example_count=strategy.example_count,
            practice_count=strategy.practice_count,
            hint_level=strategy.hint_level,
            pacing=strategy.pacing,
            focus_areas=strategy.focus_areas,
            scaffolding=strategy.scaffolding,
        )


# ==================== Learning Preference Schemas ====================


class LearningPreferenceSchema(BaseModel):
    """Schema for learning preferences."""

    preferred_style: str = Field(default="visual", description="偏好学习风格")
    preferred_pace: str = Field(default="normal", description="偏好学习节奏")
    preferred_feedback_frequency: str = Field(
        default="high", description="偏好反馈频率"
    )
    prefers_hints: bool = Field(default=True, description="是否偏好提示")
    prefers_examples: bool = Field(default=True, description="是否偏好示例")
    prefers_step_by_step: bool = Field(default=True, description="是否偏好分步讲解")

    @classmethod
    def from_domain(cls, preferences: Any) -> "LearningPreferenceSchema":
        """Create schema from domain model."""
        return cls(
            preferred_style=preferences.preferred_style.value,
            preferred_pace=preferences.preferred_pace,
            preferred_feedback_frequency=preferences.preferred_feedback_frequency,
            prefers_hints=preferences.prefers_hints,
            prefers_examples=preferences.prefers_examples,
            prefers_step_by_step=preferences.prefers_step_by_step,
        )


class LearningPreferenceUpdate(BaseModel):
    """Schema for updating learning preferences."""

    preferred_style: Optional[str] = Field(None, description="偏好学习风格")
    preferred_pace: Optional[str] = Field(None, description="偏好学习节奏")
    preferred_feedback_frequency: Optional[str] = Field(
        None, description="偏好反馈频率"
    )
    prefers_hints: Optional[bool] = Field(None, description="是否偏好提示")
    prefers_examples: Optional[bool] = Field(None, description="是否偏好示例")
    prefers_step_by_step: Optional[bool] = Field(None, description="是否偏好分步讲解")

    @field_validator("preferred_style")
    @classmethod
    def validate_style(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_styles = ["visual", "auditory", "kinesthetic", "reading"]
            if v not in valid_styles:
                raise ValueError(f"学习风格必须是: {', '.join(valid_styles)}")
        return v

    @field_validator("preferred_pace")
    @classmethod
    def validate_pace(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_paces = ["slow", "normal", "fast"]
            if v not in valid_paces:
                raise ValueError(f"学习节奏必须是: {', '.join(valid_paces)}")
        return v


# ==================== Learner Profile Schemas ====================


class LearnerProfileResponse(BaseModel):
    """Schema for learner profile response."""

    id: int
    student_id: int
    course_id: str
    learner_type: str
    learner_type_description: str
    metrics: LearnerMetricsSchema
    preferences: LearningPreferenceSchema
    current_strategy: Optional[TeachingStrategySchema] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_domain(cls, profile: Any) -> "LearnerProfileResponse":
        """Create response from domain model."""
        from app.models.learner_profile import LearnerType

        return cls(
            id=profile.id,
            student_id=profile.student_id,
            course_id=profile.course_id,
            learner_type=profile.learner_type.value,
            learner_type_description=LearnerType.get_description(profile.learner_type),
            metrics=LearnerMetricsSchema.from_domain(profile.metrics),
            preferences=LearningPreferenceSchema.from_domain(profile.preferences),
            current_strategy=TeachingStrategySchema.from_domain(profile.current_strategy)
            if profile.current_strategy
            else None,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )


class LearnerProfileCreate(BaseModel):
    """Schema for creating a learner profile."""

    student_id: int = Field(..., description="学生ID")
    course_id: str = Field(..., description="课程ID")
    prerequisite_mastery: float = Field(
        default=0.0, ge=0.0, le=1.0, description="前置知识掌握度"
    )


class LearnerClassifyRequest(BaseModel):
    """Schema for learner classification request."""

    student_id: int = Field(..., description="学生ID")
    course_id: str = Field(..., description="课程ID")
    kp_id: str = Field(..., description="知识点ID")


class LearnerClassifyResponse(BaseModel):
    """Schema for learner classification response."""

    learner_type: str = Field(..., description="识别出的学习者类型")
    learner_type_description: str = Field(..., description="类型描述")
    metrics: LearnerMetricsSchema = Field(..., description="学习者指标")
    teaching_strategy: TeachingStrategySchema = Field(..., description="推荐教学策略")
    classification_reason: str = Field(..., description="分类原因")


class TypeHistoryEntry(BaseModel):
    """Schema for a single type history entry."""

    from_type: str
    to_type: str
    reason: str
    timestamp: datetime


class LearnerTypeHistoryResponse(BaseModel):
    """Schema for learner type history response."""

    student_id: int
    course_id: str
    history: list[TypeHistoryEntry]


# ==================== Error Pattern Schemas ====================


class AddErrorPatternRequest(BaseModel):
    """Schema for adding an error pattern."""

    student_id: int = Field(..., description="学生ID")
    course_id: str = Field(..., description="课程ID")
    pattern_type: str = Field(..., description="错误模式类型")
    example: Optional[str] = Field(None, description="错误示例")

    @field_validator("pattern_type")
    @classmethod
    def validate_pattern_type(cls, v: str) -> str:
        valid_types = [
            "concept_misunderstanding",
            "calculation_error",
            "procedure_error",
            "careless_error",
            "incomplete_answer",
            "prerequisite_gap",
        ]
        if v not in valid_types:
            raise ValueError(f"错误模式类型必须是: {', '.join(valid_types)}")
        return v


class ErrorPatternSummary(BaseModel):
    """Schema for error pattern summary."""

    pattern_type: str
    frequency: int
    last_occurrence: datetime
    examples: list[str]


class ErrorPatternAnalysisResponse(BaseModel):
    """Schema for error pattern analysis response."""

    student_id: int
    course_id: str
    total_errors: int
    patterns: list[ErrorPatternSummary]
    dominant_pattern: Optional[str] = None
    recommendations: list[str] = Field(default_factory=list)
