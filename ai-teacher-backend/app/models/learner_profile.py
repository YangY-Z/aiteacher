"""Learner profile domain models.

This module defines learner types, metrics, and profiles for
adaptive learning personalization.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class LearnerType(str, Enum):
    """Learner type classification based on knowledge mastery.

    NOVICE: First-time learner with weak prerequisite knowledge
    INTERMEDIATE: Has prerequisite knowledge, but hasn't learned current topic
    REVIEWER: Has learned the topic before, but hasn't mastered it
    ADVANCED: Already mastered, needs reinforcement or extension
    """

    NOVICE = "novice"  # 新手：第一次学，前置知识薄弱
    INTERMEDIATE = "intermediate"  # 有基础者：前置知识OK，未学过当前知识点
    REVIEWER = "reviewer"  # 复习者：学过但未掌握
    ADVANCED = "advanced"  # 熟练者：已掌握，需强化

    @classmethod
    def get_description(cls, learner_type: "LearnerType") -> str:
        """Get Chinese description for learner type."""
        descriptions = {
            cls.NOVICE: "新手学习者：第一次学习此知识，前置知识薄弱",
            cls.INTERMEDIATE: "有基础者：前置知识充足，但未学习过当前知识点",
            cls.REVIEWER: "复习者：曾经学过此知识点，但遗忘或未掌握",
            cls.ADVANCED: "熟练者：已掌握该知识点，需要强化或拓展",
        }
        return descriptions.get(learner_type, "未知类型")


class LearningStyle(str, Enum):
    """Learning style preferences."""

    VISUAL = "visual"  # 视觉型：偏好图表、图示
    AUDITORY = "auditory"  # 听觉型：偏好讲解、讨论
    KINESTHETIC = "kinesthetic"  # 动觉型：偏好动手实践
    READING = "reading"  # 阅读型：偏好文字材料


class ErrorPatternType(str, Enum):
    """Common error pattern types."""

    CONCEPT_MISUNDERSTANDING = "concept_misunderstanding"  # 概念理解错误
    CALCULATION_ERROR = "calculation_error"  # 计算错误
    PROCEDURE_ERROR = "procedure_error"  # 步骤/程序错误
    CARELESS_ERROR = "careless_error"  # 粗心大意
    INCOMPLETE_ANSWER = "incomplete_answer"  # 答题不完整
    PREREQUISITE_GAP = "prerequisite_gap"  # 前置知识缺失


@dataclass
class ErrorPattern:
    """Error pattern analysis for a student.

    Tracks common mistakes and their frequencies.
    """

    pattern_type: ErrorPatternType
    frequency: int = 1
    last_occurrence: datetime = field(default_factory=datetime.now)
    examples: list[str] = field(default_factory=list)

    def add_occurrence(self, example: Optional[str] = None) -> None:
        """Add a new occurrence of this error pattern."""
        self.frequency += 1
        self.last_occurrence = datetime.now()
        if example:
            self.examples.append(example)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "pattern_type": self.pattern_type.value,
            "frequency": self.frequency,
            "last_occurrence": self.last_occurrence.isoformat(),
            "examples": self.examples,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ErrorPattern":
        """Create from dictionary."""
        return cls(
            pattern_type=ErrorPatternType(data["pattern_type"]),
            frequency=data.get("frequency", 1),
            last_occurrence=datetime.fromisoformat(data["last_occurrence"])
            if isinstance(data.get("last_occurrence"), str)
            else data.get("last_occurrence", datetime.now()),
            examples=data.get("examples", []),
        )


@dataclass
class LearnerMetrics:
    """Learning metrics for learner classification.

    Contains quantitative measures used to determine learner type.
    """

    prerequisite_mastery: float = 0.0  # 前置知识掌握度 (0.0 - 1.0)
    current_kp_mastery: float = 0.0  # 当前知识点掌握度 (0.0 - 1.0)
    learning_velocity: float = 0.5  # 学习速度 (0.0 - 1.0, 相对平均水平)
    error_patterns: list[ErrorPattern] = field(default_factory=list)
    total_learning_time: int = 0  # seconds
    total_sessions: int = 0
    average_score: float = 0.0
    questions_answered: int = 0
    questions_correct: int = 0

    def update_score(self, score: float) -> None:
        """Update average score with new score."""
        if self.questions_answered == 0:
            self.average_score = score
        else:
            # Exponential moving average
            alpha = 0.3
            self.average_score = alpha * score + (1 - alpha) * self.average_score
        self.questions_answered += 1
        if score >= 0.6:  # 60% is passing threshold
            self.questions_correct += 1

    def add_error_pattern(
        self,
        pattern_type: ErrorPatternType,
        example: Optional[str] = None,
    ) -> None:
        """Add or update an error pattern."""
        for pattern in self.error_patterns:
            if pattern.pattern_type == pattern_type:
                pattern.add_occurrence(example)
                return
        # Create new pattern
        new_pattern = ErrorPattern(
            pattern_type=pattern_type,
            examples=[example] if example else [],
        )
        self.error_patterns.append(new_pattern)

    def get_accuracy_rate(self) -> float:
        """Calculate accuracy rate."""
        if self.questions_answered == 0:
            return 0.0
        return self.questions_correct / self.questions_answered

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "prerequisite_mastery": self.prerequisite_mastery,
            "current_kp_mastery": self.current_kp_mastery,
            "learning_velocity": self.learning_velocity,
            "error_patterns": [ep.to_dict() for ep in self.error_patterns],
            "total_learning_time": self.total_learning_time,
            "total_sessions": self.total_sessions,
            "average_score": self.average_score,
            "questions_answered": self.questions_answered,
            "questions_correct": self.questions_correct,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LearnerMetrics":
        """Create from dictionary."""
        return cls(
            prerequisite_mastery=data.get("prerequisite_mastery", 0.0),
            current_kp_mastery=data.get("current_kp_mastery", 0.0),
            learning_velocity=data.get("learning_velocity", 0.5),
            error_patterns=[
                ErrorPattern.from_dict(ep) for ep in data.get("error_patterns", [])
            ],
            total_learning_time=data.get("total_learning_time", 0),
            total_sessions=data.get("total_sessions", 0),
            average_score=data.get("average_score", 0.0),
            questions_answered=data.get("questions_answered", 0),
            questions_correct=data.get("questions_correct", 0),
        )


@dataclass
class TeachingStrategy:
    """Teaching strategy recommendations for a learner type.

    Contains specific strategies and parameters for teaching.
    """

    learner_type: LearnerType
    primary_strategy: str  # 主要教学策略
    secondary_strategies: list[str] = field(default_factory=list)  # 辅助策略
    example_count: int = 2  # 示例数量
    practice_count: int = 3  # 练习数量
    hint_level: int = 2  # 提示级别 (1-3, 3最高)
    pacing: str = "normal"  # 教学节奏 (slow, normal, fast)
    focus_areas: list[str] = field(default_factory=list)  # 重点领域
    scaffolding: bool = True  # 是否需要脚手架支持

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "learner_type": self.learner_type.value,
            "primary_strategy": self.primary_strategy,
            "secondary_strategies": self.secondary_strategies,
            "example_count": self.example_count,
            "practice_count": self.practice_count,
            "hint_level": self.hint_level,
            "pacing": self.pacing,
            "focus_areas": self.focus_areas,
            "scaffolding": self.scaffolding,
        }


@dataclass
class LearningPreference:
    """Student learning preferences.

    Tracks preferred learning styles and settings.
    """

    preferred_style: LearningStyle = LearningStyle.VISUAL
    preferred_pace: str = "normal"  # slow, normal, fast
    preferred_feedback_frequency: str = "high"  # low, medium, high
    prefers_hints: bool = True
    prefers_examples: bool = True
    prefers_step_by_step: bool = True
    custom_settings: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "preferred_style": self.preferred_style.value,
            "preferred_pace": self.preferred_pace,
            "preferred_feedback_frequency": self.preferred_feedback_frequency,
            "prefers_hints": self.prefers_hints,
            "prefers_examples": self.prefers_examples,
            "prefers_step_by_step": self.prefers_step_by_step,
            "custom_settings": self.custom_settings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LearningPreference":
        """Create from dictionary."""
        return cls(
            preferred_style=LearningStyle(data.get("preferred_style", "visual")),
            preferred_pace=data.get("preferred_pace", "normal"),
            preferred_feedback_frequency=data.get("preferred_feedback_frequency", "high"),
            prefers_hints=data.get("prefers_hints", True),
            prefers_examples=data.get("prefers_examples", True),
            prefers_step_by_step=data.get("prefers_step_by_step", True),
            custom_settings=data.get("custom_settings", {}),
        )


@dataclass
class LearnerProfile:
    """Comprehensive learner profile for a student.

    Contains learner type, metrics, preferences, and learning history.
    """

    id: int
    student_id: int
    course_id: str
    learner_type: LearnerType = LearnerType.NOVICE
    metrics: LearnerMetrics = field(default_factory=LearnerMetrics)
    preferences: LearningPreference = field(default_factory=LearningPreference)
    current_strategy: Optional[TeachingStrategy] = None
    type_history: list[dict[str, Any]] = field(default_factory=list)  # 学习者类型变更历史
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update_learner_type(self, new_type: LearnerType, reason: str = "") -> None:
        """Update learner type with history tracking."""
        if new_type != self.learner_type:
            # Record history
            self.type_history.append({
                "from_type": self.learner_type.value,
                "to_type": new_type.value,
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
            })
            self.learner_type = new_type
            self.updated_at = datetime.now()

    def update_metrics(self, metrics_update: dict[str, Any]) -> None:
        """Update specific metrics."""
        for key, value in metrics_update.items():
            if hasattr(self.metrics, key):
                setattr(self.metrics, key, value)
        self.updated_at = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "student_id": self.student_id,
            "course_id": self.course_id,
            "learner_type": self.learner_type.value,
            "metrics": self.metrics.to_dict(),
            "preferences": self.preferences.to_dict(),
            "current_strategy": self.current_strategy.to_dict()
            if self.current_strategy else None,
            "type_history": self.type_history,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LearnerProfile":
        """Create from dictionary."""
        profile = cls(
            id=data["id"],
            student_id=data["student_id"],
            course_id=data["course_id"],
            learner_type=LearnerType(data.get("learner_type", "novice")),
            metrics=LearnerMetrics.from_dict(data.get("metrics", {})),
            preferences=LearningPreference.from_dict(data.get("preferences", {})),
            type_history=data.get("type_history", []),
            created_at=datetime.fromisoformat(data["created_at"])
            if isinstance(data.get("created_at"), str)
            else data.get("created_at", datetime.now()),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if isinstance(data.get("updated_at"), str)
            else data.get("updated_at", datetime.now()),
        )
        if data.get("current_strategy"):
            profile.current_strategy = TeachingStrategy(
                learner_type=LearnerType(data["current_strategy"]["learner_type"]),
                primary_strategy=data["current_strategy"]["primary_strategy"],
                secondary_strategies=data["current_strategy"].get("secondary_strategies", []),
                example_count=data["current_strategy"].get("example_count", 2),
                practice_count=data["current_strategy"].get("practice_count", 3),
                hint_level=data["current_strategy"].get("hint_level", 2),
                pacing=data["current_strategy"].get("pacing", "normal"),
                focus_areas=data["current_strategy"].get("focus_areas", []),
                scaffolding=data["current_strategy"].get("scaffolding", True),
            )
        return profile


# Predefined teaching strategies for each learner type
DEFAULT_TEACHING_STRATEGIES: dict[LearnerType, TeachingStrategy] = {
    LearnerType.NOVICE: TeachingStrategy(
        learner_type=LearnerType.NOVICE,
        primary_strategy="基础讲解+逐步引导",
        secondary_strategies=["前置知识补救", "多示例演示", "分步练习"],
        example_count=3,
        practice_count=4,
        hint_level=3,
        pacing="slow",
        focus_areas=["基础概念理解", "前置知识补充"],
        scaffolding=True,
    ),
    LearnerType.INTERMEDIATE: TeachingStrategy(
        learner_type=LearnerType.INTERMEDIATE,
        primary_strategy="知识讲解+引导发现",
        secondary_strategies=["对比教学", "问题引导"],
        example_count=2,
        practice_count=3,
        hint_level=2,
        pacing="normal",
        focus_areas=["知识关联", "理解深化"],
        scaffolding=True,
    ),
    LearnerType.REVIEWER: TeachingStrategy(
        learner_type=LearnerType.REVIEWER,
        primary_strategy="快速复习+针对强化",
        secondary_strategies=["错题回顾", "变式练习"],
        example_count=1,
        practice_count=4,
        hint_level=1,
        pacing="fast",
        focus_areas=["薄弱环节", "记忆强化"],
        scaffolding=False,
    ),
    LearnerType.ADVANCED: TeachingStrategy(
        learner_type=LearnerType.ADVANCED,
        primary_strategy="拓展深化+应用实践",
        secondary_strategies=["高阶问题", "综合应用"],
        example_count=1,
        practice_count=2,
        hint_level=1,
        pacing="fast",
        focus_areas=["深度理解", "灵活应用", "知识迁移"],
        scaffolding=False,
    ),
}
