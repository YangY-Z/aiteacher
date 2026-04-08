"""Knowledge point API schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.course import KnowledgePointType, MasteryCriteria, TeachingConfig


class MasteryCriteriaSchema(BaseModel):
    """Mastery criteria schema."""

    type: str = Field(..., description="检查类型")
    method: str = Field(..., description="评估方式")
    question_count: int = Field(..., ge=1, le=10, description="题目数量")
    pass_threshold: int = Field(..., ge=1, description="通过阈值")

    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        valid_types = ['concept_check', 'formula_check', 'skill_check']
        if v not in valid_types:
            raise ValueError(f'类型必须是: {", ".join(valid_types)}')
        return v

    @field_validator('method')
    @classmethod
    def validate_method(cls, v: str) -> str:
        valid_methods = ['选择题', '填空题', '判断题', '计算题']
        if v not in valid_methods:
            raise ValueError(f'方式必须是: {", ".join(valid_methods)}')
        return v

    def to_domain(self) -> MasteryCriteria:
        """Convert to domain model."""
        return MasteryCriteria(
            type=self.type,
            method=self.method,
            question_count=self.question_count,
            pass_threshold=self.pass_threshold,
        )

    @classmethod
    def from_domain(cls, mc: MasteryCriteria) -> "MasteryCriteriaSchema":
        """Create from domain model."""
        return cls(
            type=mc.type,
            method=mc.method,
            question_count=mc.question_count,
            pass_threshold=mc.pass_threshold,
        )


class TeachingConfigSchema(BaseModel):
    """Teaching config schema."""

    use_examples: bool = Field(default=True, description="是否使用示例")
    ask_questions: bool = Field(default=True, description="是否提问")
    question_positions: list[str] = Field(default_factory=list, description="提问位置")

    def to_domain(self) -> TeachingConfig:
        """Convert to domain model."""
        return TeachingConfig(
            use_examples=self.use_examples,
            ask_questions=self.ask_questions,
            question_positions=self.question_positions,
        )

    @classmethod
    def from_domain(cls, tc: TeachingConfig) -> "TeachingConfigSchema":
        """Create from domain model."""
        return cls(
            use_examples=tc.use_examples,
            ask_questions=tc.ask_questions,
            question_positions=tc.question_positions,
        )


class KnowledgePointCreate(BaseModel):
    """Knowledge point creation request."""

    id: str = Field(..., min_length=1, max_length=20, description="知识点ID，如 K1, K2")
    name: str = Field(..., min_length=1, max_length=100, description="知识点名称")
    type: KnowledgePointType = Field(..., description="类型：概念/公式/技能")
    description: Optional[str] = Field(None, description="知识点描述")
    level: int = Field(..., ge=0, le=6, description="层级（0-6）")
    sort_order: int = Field(default=0, description="同层级内排序")
    key_points: list[str] = Field(default_factory=list, description="核心要点")
    mastery_criteria: Optional[MasteryCriteriaSchema] = None
    teaching_config: Optional[TeachingConfigSchema] = None
    content_template: Optional[str] = Field(None, description="教学内容模板")
    dependencies: list[str] = Field(default_factory=list, description="前置依赖知识点ID列表")

    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not v.startswith('K'):
            raise ValueError('知识点ID必须以 K 开头')
        return v


class KnowledgePointUpdate(BaseModel):
    """Knowledge point update request."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[KnowledgePointType] = None
    description: Optional[str] = None
    level: Optional[int] = Field(None, ge=0, le=6)
    sort_order: Optional[int] = None
    key_points: Optional[list[str]] = None
    mastery_criteria: Optional[MasteryCriteriaSchema] = None
    teaching_config: Optional[TeachingConfigSchema] = None
    content_template: Optional[str] = None
    dependencies: Optional[list[str]] = None


class KnowledgePointResponse(BaseModel):
    """Knowledge point response."""

    id: str
    chapter_id: Optional[str] = None
    course_id: str  # Deprecated, kept for compatibility
    name: str
    type: KnowledgePointType
    description: Optional[str] = None
    level: int
    sort_order: int
    key_points: list[str]
    mastery_criteria: Optional[MasteryCriteriaSchema] = None
    teaching_config: Optional[TeachingConfigSchema] = None
    content_template: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_domain(cls, kp) -> "KnowledgePointResponse":
        """Create from domain model."""
        return cls(
            id=kp.id,
            chapter_id=kp.chapter_id,
            course_id=kp.course_id,
            name=kp.name,
            type=kp.type,
            description=kp.description,
            level=kp.level,
            sort_order=kp.sort_order,
            key_points=kp.key_points,
            mastery_criteria=MasteryCriteriaSchema.from_domain(kp.mastery_criteria) if kp.mastery_criteria else None,
            teaching_config=TeachingConfigSchema.from_domain(kp.teaching_config) if kp.teaching_config else None,
            content_template=kp.content_template,
            created_at=kp.created_at,
            updated_at=kp.updated_at,
        )


class KnowledgePointListResponse(BaseModel):
    """Knowledge point list response."""

    knowledge_points: list[KnowledgePointResponse]
    total: int
    chapter_id: Optional[str] = None
    level: Optional[int] = None


class DependencyCreate(BaseModel):
    """Dependency creation request."""

    depends_on_kp_id: str = Field(..., description="依赖的知识点ID")


class DependencyResponse(BaseModel):
    """Dependency response."""

    id: int
    kp_id: str
    depends_on_kp_id: str
    dependency_type: str

    class Config:
        from_attributes = True
