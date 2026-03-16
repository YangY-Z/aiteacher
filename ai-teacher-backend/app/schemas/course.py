"""Course-related Pydantic schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class MasteryCriteriaSchema(BaseModel):
    """Schema for mastery criteria."""

    type: str
    method: str
    question_count: int
    pass_threshold: int


class TeachingConfigSchema(BaseModel):
    """Schema for teaching configuration."""

    use_examples: bool = True
    ask_questions: bool = True
    question_positions: list[str] = Field(default_factory=list)


class KnowledgePointResponse(BaseModel):
    """Schema for knowledge point response."""

    id: str
    course_id: str
    name: str
    type: str
    description: Optional[str] = None
    level: int
    sort_order: int = 0
    key_points: list[str] = Field(default_factory=list)
    mastery_criteria: Optional[MasteryCriteriaSchema] = None
    teaching_config: Optional[TeachingConfigSchema] = None
    dependencies: list[str] = Field(default_factory=list)
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_domain(cls, kp: Any, dependencies: list[str] = None) -> "KnowledgePointResponse":
        """Create from domain model.

        Args:
            kp: KnowledgePoint domain model.
            dependencies: List of dependency KP IDs.

        Returns:
            KnowledgePointResponse instance.
        """
        mastery_criteria = None
        if kp.mastery_criteria:
            mastery_criteria = MasteryCriteriaSchema(
                type=kp.mastery_criteria.type,
                method=kp.mastery_criteria.method,
                question_count=kp.mastery_criteria.question_count,
                pass_threshold=kp.mastery_criteria.pass_threshold,
            )

        teaching_config = None
        if kp.teaching_config:
            teaching_config = TeachingConfigSchema(
                use_examples=kp.teaching_config.use_examples,
                ask_questions=kp.teaching_config.ask_questions,
                question_positions=kp.teaching_config.question_positions,
            )

        return cls(
            id=kp.id,
            course_id=kp.course_id,
            name=kp.name,
            type=kp.type.value if hasattr(kp.type, "value") else str(kp.type),
            description=kp.description,
            level=kp.level,
            sort_order=kp.sort_order,
            key_points=kp.key_points or [],
            mastery_criteria=mastery_criteria,
            teaching_config=teaching_config,
            dependencies=dependencies or [],
            created_at=kp.created_at,
        )


class DependencyResponse(BaseModel):
    """Schema for knowledge point dependency."""

    kp_id: str
    depends_on_kp_id: str
    dependency_type: str


class CourseResponse(BaseModel):
    """Schema for course response."""

    id: str
    name: str
    grade: str
    subject: str
    description: Optional[str] = None
    total_knowledge_points: int
    estimated_hours: Optional[float] = None
    status: str
    knowledge_points: list[KnowledgePointResponse] = Field(default_factory=list)
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_domain(cls, course: Any, knowledge_points: list[Any] = None, dependencies_map: dict[str, list[str]] = None) -> "CourseResponse":
        """Create from domain model.

        Args:
            course: Course domain model.
            knowledge_points: List of KnowledgePoint domain models.
            dependencies_map: Map of kp_id to list of dependency kp_ids.

        Returns:
            CourseResponse instance.
        """
        kp_responses = []
        if knowledge_points:
            for kp in knowledge_points:
                deps = dependencies_map.get(kp.id, []) if dependencies_map else []
                kp_responses.append(KnowledgePointResponse.from_domain(kp, deps))

        return cls(
            id=course.id,
            name=course.name,
            grade=course.grade,
            subject=course.subject.value if hasattr(course.subject, "value") else str(course.subject),
            description=course.description,
            total_knowledge_points=course.total_knowledge_points,
            estimated_hours=course.estimated_hours,
            status=course.status.value if hasattr(course.status, "value") else str(course.status),
            knowledge_points=kp_responses,
            created_at=course.created_at,
        )


class CourseListResponse(BaseModel):
    """Schema for course list item."""

    id: str
    name: str
    grade: str
    subject: str
    total_knowledge_points: int
    mastery_rate: Optional[float] = None  # For the current student
    status: str


class WhiteboardContent(BaseModel):
    """Schema for whiteboard content."""

    formulas: list[str] = Field(default_factory=list)
    diagrams: list[str] = Field(default_factory=list)


class TeachingContent(BaseModel):
    """Schema for teaching content in a response."""

    introduction: Optional[str] = None
    definition: Optional[str] = None
    example: Optional[str] = None
    question: Optional[str] = None
    summary: Optional[str] = None


class KnowledgePointDetail(BaseModel):
    """Schema for detailed knowledge point info."""

    id: str
    name: str
    type: str
    description: Optional[str] = None
    level: int
    dependencies: list[str] = Field(default_factory=list)
    dependency_names: list[str] = Field(default_factory=list)
    mastery_criteria: Optional[dict[str, Any]] = None
    teaching_config: Optional[dict[str, Any]] = None

    class Config:
        from_attributes = True
