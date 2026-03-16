"""Assessment-related domain models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class QuestionType(str, Enum):
    """Question types for assessment."""

    MULTIPLE_CHOICE = "选择题"
    FILL_IN_BLANK = "填空题"
    TRUE_FALSE = "判断题"
    CALCULATION = "计算题"
    DRAWING = "作图题"


class Difficulty(str, Enum):
    """Question difficulty levels."""

    BASIC = "基础"
    MEDIUM = "中等"
    HARD = "困难"


@dataclass
class AssessmentQuestion:
    """Assessment question domain model.

    Represents a question used to assess knowledge point mastery.
    """

    id: str
    kp_id: str
    type: QuestionType
    content: str
    correct_answer: Any  # Can be string or list for fill-in-blank
    explanation: Optional[str] = None
    options: Optional[list[str]] = None  # For multiple choice
    difficulty: Difficulty = Difficulty.BASIC
    created_at: datetime = field(default_factory=datetime.now)

    def check_answer(self, student_answer: Any) -> bool:
        """Check if the student's answer is correct.

        Args:
            student_answer: The student's answer.

        Returns:
            True if correct, False otherwise.
        """
        if self.type == QuestionType.FILL_IN_BLANK:
            # For fill-in-blank, compare each blank
            if isinstance(self.correct_answer, list) and isinstance(
                student_answer, list
            ):
                if len(self.correct_answer) != len(student_answer):
                    return False
                return all(
                    str(ca).strip().lower() == str(sa).strip().lower()
                    for ca, sa in zip(self.correct_answer, student_answer)
                )
            return str(self.correct_answer).strip().lower() == str(student_answer).strip().lower()

        if self.type == QuestionType.TRUE_FALSE:
            # For true/false, accept various formats
            correct = str(self.correct_answer).strip().lower()
            answer = str(student_answer).strip().lower()
            # Normalize true/false values
            true_values = {"正确", "true", "是", "对", "t", "yes"}
            false_values = {"错误", "false", "否", "错", "f", "no"}
            if correct in true_values:
                return answer in true_values
            if correct in false_values:
                return answer in false_values
            return correct == answer

        # For multiple choice, compare the selected option
        return str(student_answer).strip().upper() == str(self.correct_answer).strip().upper()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "kp_id": self.kp_id,
            "type": self.type.value,
            "content": self.content,
            "options": self.options,
            "correct_answer": self.correct_answer,
            "explanation": self.explanation,
            "difficulty": self.difficulty.value,
        }


@dataclass
class StudentAnswer:
    """Record of a student's answer to an assessment question.

    Tracks the student's response and correctness.
    """

    id: int
    session_id: str
    student_id: int
    question_id: str
    kp_id: str
    student_answer: Any
    is_correct: bool
    response_time: Optional[int] = None  # seconds
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "student_id": self.student_id,
            "question_id": self.question_id,
            "kp_id": self.kp_id,
            "student_answer": self.student_answer,
            "is_correct": self.is_correct,
            "response_time": self.response_time,
            "created_at": self.created_at.isoformat(),
        }
