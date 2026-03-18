"""Domain models module."""

from app.models.student import Student
from app.models.course import Course, KnowledgePoint, KnowledgePointDependency
from app.models.learning import (
    StudentProfile,
    LearningRecord,
    LearningSession,
    AttemptRecord,
    SkipInfo,
    ReviewInfo,
)
from app.models.assessment import AssessmentQuestion, StudentAnswer
from app.models.diagnostic import (
    DiagnosticSession,
    DiagnosticQuestion,
    DiagnosticAnswer,
    DiagnosticResult,
    DiagnosticStatus,
    DiagnosticConclusion,
    QuestionCategory,
    DiagnosticQuestionType,
    PrerequisiteCheckResult,
)
from app.models.teaching_mode import (
    TeachingModeType,
    KnowledgeType,
    InteractionType,
    AIInterventionLevel,
    TeachingPhase,
    StructuredOption,
    InteractionTemplate,
    TeachingModeConfig,
    KnowledgePointTeachingConfig,
    TEACHING_MODE_CONFIGS,
)
from app.models.learner_profile import (
    LearnerType,
    LearnerMetrics,
    LearnerProfile,
    TeachingStrategy,
    LearningPreference,
    ErrorPattern,
)
from app.models.retention import (
    ErrorType,
    ReviewStatus,
    RetentionSchedule,
    MicroPractice,
    WrongAnswerRecord,
    WrongAnswerBook,
)
from app.models.adaptive_remedy import (
    RemedialStrategy,
    RemedyStatus,
    ErrorAnalysis,
    RemedialContent,
    AdaptiveRemedyPlan,
)

__all__ = [
    "Student",
    "Course",
    "KnowledgePoint",
    "KnowledgePointDependency",
    "StudentProfile",
    "LearningRecord",
    "LearningSession",
    "AttemptRecord",
    "SkipInfo",
    "ReviewInfo",
    "AssessmentQuestion",
    "StudentAnswer",
    "DiagnosticSession",
    "DiagnosticQuestion",
    "DiagnosticAnswer",
    "DiagnosticResult",
    "DiagnosticStatus",
    "DiagnosticConclusion",
    "QuestionCategory",
    "DiagnosticQuestionType",
    "PrerequisiteCheckResult",
    # 教学模式
    "TeachingModeType",
    "KnowledgeType",
    "InteractionType",
    "AIInterventionLevel",
    "TeachingPhase",
    "StructuredOption",
    "InteractionTemplate",
    "TeachingModeConfig",
    "KnowledgePointTeachingConfig",
    "TEACHING_MODE_CONFIGS",
    # 学习者画像
    "LearnerType",
    "LearnerMetrics",
    "LearnerProfile",
    "TeachingStrategy",
    "LearningPreference",
    "ErrorPattern",
    # 课后保持
    "ErrorType",
    "ReviewStatus",
    "RetentionSchedule",
    "MicroPractice",
    "WrongAnswerRecord",
    "WrongAnswerBook",
    # 自适应补救
    "RemedialStrategy",
    "RemedyStatus",
    "ErrorAnalysis",
    "RemedialContent",
    "AdaptiveRemedyPlan",
]
