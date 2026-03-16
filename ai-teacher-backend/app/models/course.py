"""Course and knowledge point domain models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class Subject(str, Enum):
    """Subject types."""

    MATH = "数学"
    CHINESE = "语文"
    ENGLISH = "英语"
    PHYSICS = "物理"
    CHEMISTRY = "化学"


class KnowledgePointType(str, Enum):
    """Knowledge point types."""

    CONCEPT = "概念"
    FORMULA = "公式"
    SKILL = "技能"


class CourseStatus(str, Enum):
    """Course status."""

    ACTIVE = "active"
    DRAFT = "draft"
    ARCHIVED = "archived"


class DependencyType(str, Enum):
    """Knowledge point dependency types."""

    PREREQUISITE = "prerequisite"
    RELATED = "related"


@dataclass
class MasteryCriteria:
    """Mastery criteria for a knowledge point.

    Defines how mastery is evaluated for a knowledge point.
    """

    type: str  # concept_check, formula_check, skill_check
    method: str  # 选择题, 填空题, 判断题, 计算题
    question_count: int
    pass_threshold: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "method": self.method,
            "question_count": self.question_count,
            "pass_threshold": self.pass_threshold,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MasteryCriteria":
        """Create from dictionary."""
        return cls(
            type=data["type"],
            method=data["method"],
            question_count=data["question_count"],
            pass_threshold=data["pass_threshold"],
        )


@dataclass
class TeachingConfig:
    """Teaching configuration for a knowledge point.

    Defines how a knowledge point should be taught.
    """

    use_examples: bool = True
    ask_questions: bool = True
    question_positions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "use_examples": self.use_examples,
            "ask_questions": self.ask_questions,
            "question_positions": self.question_positions,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TeachingConfig":
        """Create from dictionary."""
        return cls(
            use_examples=data.get("use_examples", True),
            ask_questions=data.get("ask_questions", True),
            question_positions=data.get("question_positions", []),
        )


@dataclass
class Course:
    """Course domain model.

    Represents a course containing multiple knowledge points.
    """

    id: str
    name: str
    grade: str
    subject: Subject
    description: Optional[str] = None
    total_knowledge_points: int = 0
    estimated_hours: Optional[float] = None
    status: CourseStatus = CourseStatus.ACTIVE
    sort_order: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class KnowledgePoint:
    """Knowledge point domain model.

    Represents a single knowledge point within a course.
    """

    id: str
    course_id: str
    name: str
    type: KnowledgePointType
    description: Optional[str] = None
    level: int = 0
    sort_order: int = 0
    key_points: list[str] = field(default_factory=list)
    mastery_criteria: Optional[MasteryCriteria] = None
    teaching_config: Optional[TeachingConfig] = None
    content_template: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def get_pass_threshold(self) -> int:
        """Get the pass threshold for mastery."""
        if self.mastery_criteria:
            return self.mastery_criteria.pass_threshold
        return 1  # Default threshold

    def get_question_count(self) -> int:
        """Get the question count for assessment."""
        if self.mastery_criteria:
            return self.mastery_criteria.question_count
        return 2  # Default count


@dataclass
class KnowledgePointDependency:
    """Knowledge point dependency relationship.

    Represents a prerequisite relationship between knowledge points.
    """

    id: int
    kp_id: str
    depends_on_kp_id: str
    dependency_type: DependencyType = DependencyType.PREREQUISITE
    created_at: datetime = field(default_factory=datetime.now)
