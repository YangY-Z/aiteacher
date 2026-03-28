"""专项提升模块领域模型。"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class ImprovementSessionStatus(str, Enum):
    """专项提升会话状态。"""

    UPLOADING = "uploading"
    ANALYZING = "analyzing"
    CLARIFYING = "clarifying"
    DIAGNOSED = "diagnosed"
    PLANNING = "planning"
    LEARNING = "learning"
    QUIZ = "quiz"
    COMPLETED = "completed"


class DifficultyLevel(str, Enum):
    """期望难度。"""

    BASIC = "basic"
    NORMAL = "normal"
    CHALLENGE = "challenge"


class FoundationLevel(str, Enum):
    """自评基础。"""

    WEAK = "weak"
    AVERAGE = "average"
    GOOD = "good"


@dataclass
class ScoreInput:
    """成绩输入。"""

    exam_name: str
    score: float
    total_score: float
    error_description: Optional[str] = None
    available_time: int = 30
    difficulty: DifficultyLevel = DifficultyLevel.NORMAL
    foundation: FoundationLevel = FoundationLevel.AVERAGE
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "exam_name": self.exam_name,
            "score": self.score,
            "total_score": self.total_score,
            "error_description": self.error_description,
            "available_time": self.available_time,
            "difficulty": self.difficulty.value,
            "foundation": self.foundation.value,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScoreInput":
        return cls(
            exam_name=data["exam_name"],
            score=data["score"],
            total_score=data["total_score"],
            error_description=data.get("error_description"),
            available_time=data.get("available_time", 30),
            difficulty=DifficultyLevel(data.get("difficulty", DifficultyLevel.NORMAL.value)),
            foundation=FoundationLevel(data.get("foundation", FoundationLevel.AVERAGE.value)),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
        )


@dataclass
class ClarificationRound:
    """澄清轮次。"""

    round_number: int
    system_question: str
    student_answer: Optional[str] = None
    candidate_kp_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    answered_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "round_number": self.round_number,
            "system_question": self.system_question,
            "student_answer": self.student_answer,
            "candidate_kp_ids": self.candidate_kp_ids,
            "created_at": self.created_at.isoformat(),
            "answered_at": self.answered_at.isoformat() if self.answered_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClarificationRound":
        return cls(
            round_number=data["round_number"],
            system_question=data["system_question"],
            student_answer=data.get("student_answer"),
            candidate_kp_ids=data.get("candidate_kp_ids", []),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            answered_at=datetime.fromisoformat(data["answered_at"]) if data.get("answered_at") else None,
        )


@dataclass
class DiagnosisResult:
    """诊断结果。"""

    target_knowledge_point_id: str
    confidence: float
    reason: str
    prerequisite_gaps: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_knowledge_point_id": self.target_knowledge_point_id,
            "confidence": self.confidence,
            "reason": self.reason,
            "prerequisite_gaps": self.prerequisite_gaps,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DiagnosisResult":
        return cls(
            target_knowledge_point_id=data["target_knowledge_point_id"],
            confidence=data["confidence"],
            reason=data["reason"],
            prerequisite_gaps=data.get("prerequisite_gaps", []),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
        )


@dataclass
class ImprovementPlanStep:
    """学习方案步骤。"""

    step_order: int
    knowledge_point_id: str
    goal: str
    estimated_minutes: int
    is_completed: bool = False
    completed_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_order": self.step_order,
            "knowledge_point_id": self.knowledge_point_id,
            "goal": self.goal,
            "estimated_minutes": self.estimated_minutes,
            "is_completed": self.is_completed,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImprovementPlanStep":
        return cls(
            step_order=data["step_order"],
            knowledge_point_id=data["knowledge_point_id"],
            goal=data["goal"],
            estimated_minutes=data["estimated_minutes"],
            is_completed=data.get("is_completed", False),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
        )


@dataclass
class ImprovementPlan:
    """专项提升学习方案。"""

    plan_id: str
    target_kp_id: str
    steps: list[ImprovementPlanStep] = field(default_factory=list)
    total_estimated_minutes: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "target_kp_id": self.target_kp_id,
            "steps": [step.to_dict() for step in self.steps],
            "total_estimated_minutes": self.total_estimated_minutes,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImprovementPlan":
        return cls(
            plan_id=data["plan_id"],
            target_kp_id=data["target_kp_id"],
            steps=[ImprovementPlanStep.from_dict(step) for step in data.get("steps", [])],
            total_estimated_minutes=data.get("total_estimated_minutes", 0),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
        )


@dataclass
class ImprovementQuizResult:
    """专项提升小测结果。"""

    quiz_id: str
    questions: list[dict[str, Any]] = field(default_factory=list)
    answers: list[dict[str, Any]] = field(default_factory=list)
    score: float = 0.0
    passed: bool = False
    feedback: str = ""
    submitted_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "quiz_id": self.quiz_id,
            "questions": self.questions,
            "answers": self.answers,
            "score": self.score,
            "passed": self.passed,
            "feedback": self.feedback,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImprovementQuizResult":
        return cls(
            quiz_id=data["quiz_id"],
            questions=data.get("questions", []),
            answers=data.get("answers", []),
            score=data.get("score", 0.0),
            passed=data.get("passed", False),
            feedback=data.get("feedback", ""),
            submitted_at=datetime.fromisoformat(data["submitted_at"]) if data.get("submitted_at") else None,
        )


@dataclass
class ImprovementSession:
    """专项提升会话。"""

    session_id: str
    student_id: str
    course_id: str
    status: ImprovementSessionStatus
    max_clarification_rounds: int = 5
    score_input: Optional[ScoreInput] = None
    clarification_rounds: list[ClarificationRound] = field(default_factory=list)
    diagnosis: Optional[DiagnosisResult] = None
    plan: Optional[ImprovementPlan] = None
    current_step_order: int = 0
    quiz_result: Optional[ImprovementQuizResult] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "student_id": self.student_id,
            "course_id": self.course_id,
            "status": self.status.value,
            "max_clarification_rounds": self.max_clarification_rounds,
            "score_input": self.score_input.to_dict() if self.score_input else None,
            "clarification_rounds": [round_item.to_dict() for round_item in self.clarification_rounds],
            "diagnosis": self.diagnosis.to_dict() if self.diagnosis else None,
            "plan": self.plan.to_dict() if self.plan else None,
            "current_step_order": self.current_step_order,
            "quiz_result": self.quiz_result.to_dict() if self.quiz_result else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImprovementSession":
        return cls(
            session_id=data["session_id"],
            student_id=data["student_id"],
            course_id=data["course_id"],
            status=ImprovementSessionStatus(data["status"]),
            max_clarification_rounds=data.get("max_clarification_rounds", 5),
            score_input=ScoreInput.from_dict(data["score_input"]) if data.get("score_input") else None,
            clarification_rounds=[
                ClarificationRound.from_dict(item)
                for item in data.get("clarification_rounds", [])
            ],
            diagnosis=DiagnosisResult.from_dict(data["diagnosis"]) if data.get("diagnosis") else None,
            plan=ImprovementPlan.from_dict(data["plan"]) if data.get("plan") else None,
            current_step_order=data.get("current_step_order", 0),
            quiz_result=ImprovementQuizResult.from_dict(data["quiz_result"]) if data.get("quiz_result") else None,
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
        )
