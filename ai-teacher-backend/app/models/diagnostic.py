"""Diagnostic-related domain models for pre-class assessment."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class DiagnosticStatus(str, Enum):
    """Diagnostic session status."""

    PENDING = "pending"  # 诊断未开始
    IN_PROGRESS = "in_progress"  # 诊断进行中
    COMPLETED = "completed"  # 诊断已完成


class DiagnosticConclusion(str, Enum):
    """Diagnostic conclusion types.

    Based on the diagnostic result, determines the learning path.
    """

    FULL_MASTERY = "full_mastery"  # 完全掌握 - 可跳过该知识点
    PARTIAL_MASTERY = "partial_mastery"  # 部分掌握 - 需要快速复习
    NEED_REVIEW = "need_review"  # 需要复习 - 正常学习流程
    FULL_LEARNING = "full_learning"  # 完全学习 - 从头开始学习


class QuestionCategory(str, Enum):
    """Diagnostic question category."""

    PREREQUISITE = "prerequisite"  # 前置知识检测题
    TARGET = "target"  # 目标知识基础检测题


class DiagnosticQuestionType(str, Enum):
    """Types of diagnostic questions."""

    POINT_CLICK = "point_click"  # 点击坐标题（在坐标系中点击）
    INPUT = "input"  # 输入题（文本/数字输入）
    CHOICE = "choice"  # 选择题（单选/多选）


@dataclass
class DiagnosticQuestion:
    """Diagnostic question model.

    Represents a question used in pre-class diagnosis.
    Supports multiple question types including interactive ones.
    """

    id: str
    session_id: str
    kp_id: str  # 关联的知识点ID
    category: QuestionCategory  # 问题类别
    question_type: DiagnosticQuestionType  # 题型
    content: str  # 题目内容/描述
    correct_answer: Any  # 正确答案（格式取决于题型）
    options: Optional[list[str]] = None  # 选择题选项
    image_url: Optional[str] = None  # 题目配图（如坐标系图）
    coordinate_range: Optional[dict[str, Any]] = None  # 坐标题的范围设置
    explanation: Optional[str] = None  # 答案解析
    order: int = 0  # 题目顺序
    created_at: datetime = field(default_factory=datetime.now)

    def check_answer(self, student_answer: Any) -> bool:
        """Check if the student's answer is correct.

        Args:
            student_answer: The student's answer (format depends on question_type).

        Returns:
            True if correct, False otherwise.
        """
        if self.question_type == DiagnosticQuestionType.POINT_CLICK:
            # 对于坐标点击题，检查点击位置是否在正确范围内
            return self._check_coordinate_answer(student_answer)
        elif self.question_type == DiagnosticQuestionType.INPUT:
            # 对于输入题，比较字符串/数值
            return self._check_input_answer(student_answer)
        elif self.question_type == DiagnosticQuestionType.CHOICE:
            # 对于选择题，比较选项
            return self._check_choice_answer(student_answer)
        return False

    def _check_coordinate_answer(self, student_answer: Any) -> bool:
        """Check coordinate answer with tolerance.

        Args:
            student_answer: Dict with 'x' and 'y' coordinates.

        Returns:
            True if within tolerance.
        """
        if not isinstance(student_answer, dict):
            return False

        if not isinstance(self.correct_answer, dict):
            return False

        # 获取容差（默认0.5个单位）
        tolerance = self.coordinate_range.get("tolerance", 0.5) if self.coordinate_range else 0.5

        try:
            x = float(student_answer.get("x", 0))
            y = float(student_answer.get("y", 0))
            correct_x = float(self.correct_answer.get("x", 0))
            correct_y = float(self.correct_answer.get("y", 0))

            return abs(x - correct_x) <= tolerance and abs(y - correct_y) <= tolerance
        except (ValueError, TypeError):
            return False

    def _check_input_answer(self, student_answer: Any) -> bool:
        """Check input answer with normalization.

        Args:
            student_answer: String or number input.

        Returns:
            True if matches.
        """
        # 标准化答案比较
        student_str = str(student_answer).strip().lower()
        correct_str = str(self.correct_answer).strip().lower()

        # 直接匹配
        if student_str == correct_str:
            return True

        # 尝试数值比较（处理分数、小数等）
        try:
            # 处理分数形式如 "1/2"
            if "/" in student_str:
                parts = student_str.split("/")
                student_num = float(parts[0]) / float(parts[1])
            else:
                student_num = float(student_str)

            if "/" in correct_str:
                parts = correct_str.split("/")
                correct_num = float(parts[0]) / float(parts[1])
            else:
                correct_num = float(correct_str)

            return abs(student_num - correct_num) < 0.001
        except (ValueError, TypeError, ZeroDivisionError):
            return False

    def _check_choice_answer(self, student_answer: Any) -> bool:
        """Check choice answer.

        Args:
            student_answer: Selected option(s).

        Returns:
            True if correct.
        """
        # 标准化选项格式
        student_choice = str(student_answer).strip().upper()
        correct_choice = str(self.correct_answer).strip().upper()

        return student_choice == correct_choice

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "kp_id": self.kp_id,
            "category": self.category.value,
            "question_type": self.question_type.value,
            "content": self.content,
            "options": self.options,
            "image_url": self.image_url,
            "coordinate_range": self.coordinate_range,
            "order": self.order,
        }


@dataclass
class DiagnosticAnswer:
    """Record of a student's answer to a diagnostic question."""

    id: int
    session_id: str
    question_id: str
    student_answer: Any
    is_correct: bool
    response_time: Optional[int] = None  # seconds
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "question_id": self.question_id,
            "student_answer": self.student_answer,
            "is_correct": self.is_correct,
            "response_time": self.response_time,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class PrerequisiteCheckResult:
    """Result of prerequisite knowledge check.

    Represents the mastery status of a single prerequisite knowledge point.
    """

    kp_id: str
    kp_name: str
    is_mastered: bool
    questions_total: int
    questions_correct: int
    confidence: float  # 0.0 - 1.0，置信度

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "kp_id": self.kp_id,
            "kp_name": self.kp_name,
            "is_mastered": self.is_mastered,
            "questions_total": self.questions_total,
            "questions_correct": self.questions_correct,
            "confidence": self.confidence,
        }


@dataclass
class DiagnosticResult:
    """Final diagnostic result.

    Contains comprehensive diagnostic analysis and recommendations.
    """

    session_id: str
    target_kp_id: str
    target_kp_name: str
    conclusion: DiagnosticConclusion
    prerequisite_results: list[PrerequisiteCheckResult] = field(default_factory=list)
    target_questions_total: int = 0
    target_questions_correct: int = 0
    total_questions: int = 0
    total_correct: int = 0
    correct_rate: float = 0.0
    recommended_starting_point: Optional[str] = None  # 推荐的学习起点kp_id
    recommended_teaching_mode: Optional[str] = None  # 推荐的教学模式
    summary: Optional[str] = None  # 诊断总结
    created_at: datetime = field(default_factory=datetime.now)

    def calculate_conclusion(self) -> DiagnosticConclusion:
        """Calculate and return the diagnostic conclusion.

        Returns:
            Diagnostic conclusion based on results.
        """
        # 计算前置知识掌握率
        prereq_mastered_count = sum(
            1 for r in self.prerequisite_results if r.is_mastered
        )
        prereq_total = len(self.prerequisite_results)
        prereq_rate = prereq_mastered_count / prereq_total if prereq_total > 0 else 1.0

        # 计算目标知识检测正确率
        target_rate = (
            self.target_questions_correct / self.target_questions_total
            if self.target_questions_total > 0
            else 0.0
        )

        # 计算总体正确率
        overall_rate = self.total_correct / self.total_questions if self.total_questions > 0 else 0.0

        # 根据结果判断结论
        # 完全掌握：前置知识全掌握 + 目标题全对
        if prereq_rate >= 1.0 and target_rate >= 1.0:
            self.conclusion = DiagnosticConclusion.FULL_MASTERY
        # 部分掌握：前置知识全掌握 + 目标题部分对
        elif prereq_rate >= 1.0 and target_rate >= 0.5:
            self.conclusion = DiagnosticConclusion.PARTIAL_MASTERY
        # 需要复习：前置知识部分掌握
        elif prereq_rate >= 0.5:
            self.conclusion = DiagnosticConclusion.NEED_REVIEW
        # 完全学习：前置知识大部分未掌握
        else:
            self.conclusion = DiagnosticConclusion.FULL_LEARNING

        # 设置推荐学习起点
        if self.conclusion == DiagnosticConclusion.FULL_MASTERY:
            # 完全掌握，可以跳过
            self.recommended_starting_point = None  # 表示可以跳过
        elif self.conclusion == DiagnosticConclusion.PARTIAL_MASTERY:
            # 部分掌握，从当前知识点开始快速复习
            self.recommended_starting_point = self.target_kp_id
        elif self.conclusion == DiagnosticConclusion.NEED_REVIEW:
            # 需要复习，找到第一个未掌握的前置知识
            for prereq in self.prerequisite_results:
                if not prereq.is_mastered:
                    self.recommended_starting_point = prereq.kp_id
                    break
        else:
            # 完全学习，从第一个未掌握的前置知识开始
            for prereq in self.prerequisite_results:
                if not prereq.is_mastered:
                    self.recommended_starting_point = prereq.kp_id
                    break
            if not self.recommended_starting_point:
                self.recommended_starting_point = self.target_kp_id

        return self.conclusion

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "target_kp_id": self.target_kp_id,
            "target_kp_name": self.target_kp_name,
            "conclusion": self.conclusion.value,
            "prerequisite_results": [r.to_dict() for r in self.prerequisite_results],
            "target_questions_total": self.target_questions_total,
            "target_questions_correct": self.target_questions_correct,
            "total_questions": self.total_questions,
            "total_correct": self.total_correct,
            "correct_rate": self.correct_rate,
            "recommended_starting_point": self.recommended_starting_point,
            "recommended_teaching_mode": self.recommended_teaching_mode,
            "summary": self.summary,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class DiagnosticSession:
    """Diagnostic session domain model.

    Represents a complete pre-class diagnostic session.
    """

    id: str
    student_id: int
    course_id: str
    target_kp_id: str  # 目标知识点ID
    status: DiagnosticStatus = DiagnosticStatus.PENDING
    questions: list[DiagnosticQuestion] = field(default_factory=list)
    answers: list[DiagnosticAnswer] = field(default_factory=list)
    result: Optional[DiagnosticResult] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[int] = None  # seconds
    created_at: datetime = field(default_factory=datetime.now)

    def start(self) -> None:
        """Start the diagnostic session."""
        self.status = DiagnosticStatus.IN_PROGRESS
        self.start_time = datetime.now()

    def complete(self) -> None:
        """Complete the diagnostic session."""
        self.status = DiagnosticStatus.COMPLETED
        self.end_time = datetime.now()
        if self.start_time:
            self.duration = int((self.end_time - self.start_time).total_seconds())

    def get_current_question(self) -> Optional[DiagnosticQuestion]:
        """Get the current question to answer.

        Returns:
            The first unanswered question, or None if all answered.
        """
        answered_ids = {a.question_id for a in self.answers}
        for question in sorted(self.questions, key=lambda q: q.order):
            if question.id not in answered_ids:
                return question
        return None

    def get_progress(self) -> dict[str, int]:
        """Get the current progress.

        Returns:
            Dict with total and answered counts.
        """
        total = len(self.questions)
        answered = len(self.answers)
        return {
            "total": total,
            "answered": answered,
            "remaining": total - answered,
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "student_id": self.student_id,
            "course_id": self.course_id,
            "target_kp_id": self.target_kp_id,
            "status": self.status.value,
            "questions": [q.to_dict() for q in self.questions],
            "progress": self.get_progress(),
            "result": self.result.to_dict() if self.result else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "created_at": self.created_at.isoformat(),
        }
