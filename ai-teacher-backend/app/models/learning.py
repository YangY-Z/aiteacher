"""Learning-related domain models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class LearningStatus(str, Enum):
    """Learning record status."""

    PENDING = "pending"
    LEARNING = "learning"
    MASTERED = "mastered"
    SKIPPED = "skipped"
    BACKTRACK = "backtrack"


class SessionStatus(str, Enum):
    """Learning session status."""

    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class SessionResult(str, Enum):
    """Learning session result."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class RoundStatus(str, Enum):
    """学习轮次状态"""
    IN_PROGRESS = "in_progress"    # 进行中
    COMPLETED = "completed"        # 已完成（通过评估）
    FAILED = "failed"              # 已完成（未通过评估）
    ABANDONED = "abandoned"        # 中途退出


@dataclass
class AssessmentResult:
    """评估结果"""
    score: float
    correct_count: int
    total_count: int
    passed: bool
    error_types: list[str] = field(default_factory=list)
    wrong_questions: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "correct_count": self.correct_count,
            "total_count": self.total_count,
            "passed": self.passed,
            "error_types": self.error_types,
            "wrong_questions": self.wrong_questions,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AssessmentResult":
        return cls(
            score=data.get("score", 0.0),
            correct_count=data.get("correct_count", 0),
            total_count=data.get("total_count", 0),
            passed=data.get("passed", False),
            error_types=data.get("error_types", []),
            wrong_questions=data.get("wrong_questions", []),
        )


@dataclass
class RoundSummary:
    """轮次总结（AI生成）"""
    result: str  # passed, failed, abandoned
    score: float
    main_issues: list[str]  # 主要问题
    error_types: list[str]  # 错误类型
    mastery_level: str  # 掌握程度：入门/理解/掌握/精通
    key_insights: str  # 关键收获
    teaching_phases_completed: int  # 完成了几个教学阶段
    total_phases: int  # 总共几个阶段
    generated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "result": self.result,
            "score": self.score,
            "main_issues": self.main_issues,
            "error_types": self.error_types,
            "mastery_level": self.mastery_level,
            "key_insights": self.key_insights,
            "teaching_phases_completed": self.teaching_phases_completed,
            "total_phases": self.total_phases,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RoundSummary":
        return cls(
            result=data.get("result", ""),
            score=data.get("score", 0.0),
            main_issues=data.get("main_issues", []),
            error_types=data.get("error_types", []),
            mastery_level=data.get("mastery_level", "入门"),
            key_insights=data.get("key_insights", ""),
            teaching_phases_completed=data.get("teaching_phases_completed", 0),
            total_phases=data.get("total_phases", 4),
            generated_at=datetime.fromisoformat(data["generated_at"]) if data.get("generated_at") else datetime.now(),
        )

    def to_prompt_str(self, round_number: int) -> str:
        """转换为 Prompt 中使用的字符串"""
        status = "通过" if self.result == "passed" else ("未通过" if self.result == "failed" else "未完成")
        return f"- 第{round_number}轮：{status}({self.score}分)，掌握程度：{self.mastery_level}，主要问题：{', '.join(self.main_issues) if self.main_issues else '无'}"


@dataclass
class LearningRound:
    """单个学习轮次"""
    round_number: int
    start_time: datetime
    end_time: Optional[datetime] = None
    status: RoundStatus = RoundStatus.IN_PROGRESS

    # 该轮对话内容（完整保留）
    messages: list[dict[str, str]] = field(default_factory=list)

    # 教学进度
    teaching_mode: Optional[str] = None
    current_phase: int = 1
    total_phases: int = 4
    phases_completed: list[int] = field(default_factory=list)

    # 评估结果（如果已评估）
    assessment_result: Optional[AssessmentResult] = None

    # 总结（完成后生成）
    summary: Optional[RoundSummary] = None

    def add_message(self, role: str, content: str) -> None:
        """添加消息到对话历史"""
        normalized_role = role
        if role == "ai":
            normalized_role = "assistant"
        elif role == "student":
            normalized_role = "user"
        self.messages.append({"role": normalized_role, "content": content})

    def get_conversation_history(self, max_turns: int = 10) -> list[dict[str, str]]:
        """获取对话历史"""
        max_messages = max_turns * 2
        if len(self.messages) <= max_messages:
            return self.messages.copy()
        return self.messages[-max_messages:]

    def complete(self, passed: bool, assessment_result: Optional[AssessmentResult] = None) -> None:
        """完成该轮次"""
        self.end_time = datetime.now()
        self.status = RoundStatus.COMPLETED if passed else RoundStatus.FAILED
        if assessment_result:
            self.assessment_result = assessment_result

    def abandon(self) -> None:
        """标记为中途退出"""
        self.end_time = datetime.now()
        self.status = RoundStatus.ABANDONED

    def to_dict(self) -> dict[str, Any]:
        return {
            "round_number": self.round_number,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status.value if isinstance(self.status, RoundStatus) else self.status,
            "messages": self.messages,
            "teaching_mode": self.teaching_mode,
            "current_phase": self.current_phase,
            "total_phases": self.total_phases,
            "phases_completed": self.phases_completed,
            "assessment_result": self.assessment_result.to_dict() if self.assessment_result else None,
            "summary": self.summary.to_dict() if self.summary else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LearningRound":
        return cls(
            round_number=data.get("round_number", 1),
            start_time=datetime.fromisoformat(data["start_time"]) if data.get("start_time") else datetime.now(),
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            status=RoundStatus(data.get("status", "in_progress")),
            messages=data.get("messages", []),
            teaching_mode=data.get("teaching_mode"),
            current_phase=data.get("current_phase", 1),
            total_phases=data.get("total_phases", 4),
            phases_completed=data.get("phases_completed", []),
            assessment_result=AssessmentResult.from_dict(data["assessment_result"]) if data.get("assessment_result") else None,
            summary=RoundSummary.from_dict(data["summary"]) if data.get("summary") else None,
        )


@dataclass
class AttemptRecord:
    """Record of a single learning attempt.

    Represents one attempt at learning/mastering a knowledge point.
    """

    attempt_id: int
    start_time: datetime
    result: str  # passed, failed
    end_time: Optional[datetime] = None
    error_type: Optional[str] = None
    backtrack_to: Optional[str] = None
    score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "attempt_id": self.attempt_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "result": self.result,
            "error_type": self.error_type,
            "backtrack_to": self.backtrack_to,
            "score": self.score,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AttemptRecord":
        """Create from dictionary."""
        return cls(
            attempt_id=data["attempt_id"],
            start_time=datetime.fromisoformat(data["start_time"])
            if isinstance(data.get("start_time"), str)
            else data.get("start_time", datetime.now()),
            end_time=datetime.fromisoformat(data["end_time"])
            if data.get("end_time") and isinstance(data["end_time"], str)
            else data.get("end_time"),
            result=data["result"],
            error_type=data.get("error_type"),
            backtrack_to=data.get("backtrack_to"),
            score=data.get("score", 0.0),
        )


@dataclass
class SkipInfo:
    """Information about a skipped knowledge point."""

    skip_time: datetime
    reason: Optional[str] = None
    later_reviewed: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "skip_time": self.skip_time.isoformat(),
            "reason": self.reason,
            "later_reviewed": self.later_reviewed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SkipInfo":
        """Create from dictionary."""
        return cls(
            skip_time=datetime.fromisoformat(data["skip_time"])
            if isinstance(data["skip_time"], str)
            else data["skip_time"],
            reason=data.get("reason"),
            later_reviewed=data.get("later_reviewed", False),
        )


@dataclass
class ReviewInfo:
    """Information about knowledge point reviews."""

    review_count: int = 0
    reviews: list[dict[str, Any]] = field(default_factory=list)

    def add_review(self, trigger_type: str) -> None:
        """Add a new review record."""
        self.review_count += 1
        self.reviews.append(
            {
                "request_time": datetime.now().isoformat(),
                "trigger_type": trigger_type,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "review_count": self.review_count,
            "reviews": self.reviews,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReviewInfo":
        """Create from dictionary."""
        return cls(
            review_count=data.get("review_count", 0),
            reviews=data.get("reviews", []),
        )


@dataclass
class LearningRecord:
    """Learning record for a knowledge point.

    Tracks a student's learning progress for a specific knowledge point.
    """

    id: int
    student_id: int
    kp_id: str
    status: LearningStatus = LearningStatus.PENDING
    attempt_count: int = 0
    attempts: list[AttemptRecord] = field(default_factory=list)
    mastery_time: Optional[datetime] = None
    total_time: int = 0  # seconds
    skip_info: Optional[SkipInfo] = None
    review_info: Optional[ReviewInfo] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_attempt(self, result: str, error_type: Optional[str] = None) -> AttemptRecord:
        """Add a new learning attempt.

        Args:
            result: Result of the attempt (passed/failed).
            error_type: Type of error if failed.

        Returns:
            The created attempt record.
        """
        self.attempt_count += 1
        attempt = AttemptRecord(
            attempt_id=self.attempt_count,
            start_time=datetime.now(),
            result=result,
            error_type=error_type,
        )
        self.attempts.append(attempt)
        self.updated_at = datetime.now()
        return attempt

    def complete_attempt(
        self,
        attempt: AttemptRecord,
        end_time: datetime,
        score: float = 0.0,
        backtrack_to: Optional[str] = None,
    ) -> None:
        """Complete an ongoing attempt.

        Args:
            attempt: The attempt to complete.
            end_time: End time of the attempt.
            score: Score achieved.
            backtrack_to: Knowledge point to backtrack to if needed.
        """
        attempt.end_time = end_time
        attempt.score = score
        attempt.backtrack_to = backtrack_to
        self.updated_at = datetime.now()

    def mark_mastered(self) -> None:
        """Mark this knowledge point as mastered."""
        self.status = LearningStatus.MASTERED
        self.mastery_time = datetime.now()
        self.updated_at = datetime.now()

    def mark_skipped(self, reason: Optional[str] = None) -> None:
        """Mark this knowledge point as skipped."""
        self.status = LearningStatus.SKIPPED
        self.skip_info = SkipInfo(skip_time=datetime.now(), reason=reason)
        self.updated_at = datetime.now()

    def get_last_attempt(self) -> Optional[AttemptRecord]:
        """Get the most recent attempt."""
        if self.attempts:
            return self.attempts[-1]
        return None

    def get_last_error_type(self) -> Optional[str]:
        """Get the error type from the last failed attempt."""
        for attempt in reversed(self.attempts):
            if attempt.result == "failed" and attempt.error_type:
                return attempt.error_type
        return None


@dataclass
class StudentProfile:
    """Student learning profile for a course.

    Tracks overall progress and statistics for a student in a course.
    """

    id: int
    student_id: int
    course_id: str
    current_kp_id: Optional[str] = None
    completed_kp_ids: list[str] = field(default_factory=list)
    mastered_kp_ids: list[str] = field(default_factory=list)
    skipped_kp_ids: list[str] = field(default_factory=list)
    mastery_rate: float = 0.0
    total_time: int = 0  # seconds
    session_count: int = 0
    last_session_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update_progress(
        self,
        total_kp_count: int,
    ) -> None:
        """Update mastery rate based on mastered knowledge points.

        Args:
            total_kp_count: Total number of knowledge points in the course.
        """
        if total_kp_count > 0:
            self.mastery_rate = len(self.mastered_kp_ids) / total_kp_count
        self.updated_at = datetime.now()

    def add_mastered_kp(self, kp_id: str, total_kp_count: int) -> None:
        """Add a mastered knowledge point.

        Args:
            kp_id: Knowledge point ID that was mastered.
            total_kp_count: Total number of knowledge points.
        """
        if kp_id not in self.mastered_kp_ids:
            self.mastered_kp_ids.append(kp_id)
        if kp_id in self.completed_kp_ids:
            self.completed_kp_ids.remove(kp_id)
        self.update_progress(total_kp_count)

    def set_current_kp(self, kp_id: str) -> None:
        """Set the current knowledge point being studied."""
        self.current_kp_id = kp_id
        if kp_id not in self.completed_kp_ids and kp_id not in self.mastered_kp_ids:
            self.completed_kp_ids.append(kp_id)
        self.updated_at = datetime.now()


@dataclass
class LearningSession:
    """Learning session domain model.

    Represents a single learning session with the AI teacher.
    Supports multiple learning rounds with full history preservation.
    """

    id: str
    student_id: int
    course_id: str
    kp_id: Optional[str] = None
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    
    # 所有学习轮次（完整保留历史）
    rounds: list[LearningRound] = field(default_factory=list)
    
    # 当前轮次索引
    current_round_index: int = 0
    
    # === 以下属性为兼容现有代码，代理到当前轮次 ===
    
    @property
    def current_round(self) -> LearningRound:
        """获取当前轮次"""
        if not self.rounds:
            self._ensure_round()
        return self.rounds[self.current_round_index]
    
    def _ensure_round(self) -> None:
        """确保至少有一个轮次"""
        if not self.rounds:
            self.rounds.append(LearningRound(
                round_number=1,
                start_time=datetime.now(),
            ))
            self.current_round_index = 0
    
    @property
    def learning_round(self) -> int:
        """当前是第几轮学习"""
        return self.current_round.round_number
    
    @property
    def messages(self) -> list[dict[str, str]]:
        """当前轮次的对话历史（兼容属性）"""
        return self.current_round.messages
    
    @property
    def teaching_mode(self) -> Optional[str]:
        """当前轮次的教学模式"""
        return self.current_round.teaching_mode
    
    @teaching_mode.setter
    def teaching_mode(self, value: str) -> None:
        self.current_round.teaching_mode = value
    
    @property
    def current_phase(self) -> int:
        """当前教学阶段"""
        return self.current_round.current_phase
    
    @current_phase.setter
    def current_phase(self, value: int) -> None:
        self.current_round.current_phase = value
    
    @property
    def total_phases(self) -> int:
        """总教学阶段数"""
        return self.current_round.total_phases
    
    @total_phases.setter
    def total_phases(self, value: int) -> None:
        self.current_round.total_phases = value
    
    @property
    def phase_status(self) -> str:
        """阶段状态"""
        return "in_progress" if self.current_round.status == RoundStatus.IN_PROGRESS else "completed"
    
    @phase_status.setter
    def phase_status(self, value: str) -> None:
        pass  # 兼容，实际状态由 RoundStatus 控制
    
    @property
    def start_time(self) -> datetime:
        """当前轮次开始时间"""
        return self.current_round.start_time
    
    @property
    def end_time(self) -> Optional[datetime]:
        """当前轮次结束时间"""
        return self.current_round.end_time
    
    @property
    def result(self) -> Optional[SessionResult]:
        """当前轮次结果"""
        if self.current_round.status == RoundStatus.COMPLETED:
            return SessionResult.PASSED
        elif self.current_round.status == RoundStatus.FAILED:
            return SessionResult.FAILED
        return None
    
    @property
    def summary(self) -> Optional[dict[str, Any]]:
        """当前轮次总结"""
        return self.current_round.summary.to_dict() if self.current_round.summary else None
    
    @property
    def duration(self) -> Optional[int]:
        """当前轮次持续时间（秒）"""
        if self.current_round.end_time:
            return int((self.current_round.end_time - self.current_round.start_time).total_seconds())
        return None

    def start_new_round(self) -> LearningRound:
        """开始新一轮学习
        
        如果上一轮未完成，会先标记为放弃。
        """
        # 如果有未完成的轮次，标记为放弃
        if self.rounds and self.current_round.status == RoundStatus.IN_PROGRESS:
            self.current_round.abandon()
        
        # 创建新轮次
        new_round = LearningRound(
            round_number=len(self.rounds) + 1,
            start_time=datetime.now(),
        )
        self.rounds.append(new_round)
        self.current_round_index = len(self.rounds) - 1
        return new_round

    def get_history_summaries(self, max_rounds: int = 3, min_time_gap_hours: float = 1.0) -> list[RoundSummary]:
        """获取最近N轮的总结（用于Prompt）
        
        Args:
            max_rounds: 最多返回几轮总结
            min_time_gap_hours: 最小时间间隔（小时），距离现在小于此值的轮次不返回
        
        Returns:
            符合条件的轮次总结列表
        """
        summaries = []
        now = datetime.now()
        
        for r in reversed(self.rounds[:-1]):  # 排除当前轮
            if r.summary:
                # 检查时间间隔：只有距离现在足够久才包含回顾
                if r.summary.generated_at:
                    time_gap = now - r.summary.generated_at
                    time_gap_hours = time_gap.total_seconds() / 3600
                    
                    # 如果时间间隔小于阈值，跳过（刚学完不需要回顾）
                    if time_gap_hours < min_time_gap_hours:
                        continue
                
                summaries.append(r.summary)
            if len(summaries) >= max_rounds:
                break
        return list(reversed(summaries))

    def get_history_summary_str(self) -> str:
        """获取历史总结的字符串（用于Prompt）"""
        summaries = self.get_history_summaries()
        if not summaries:
            return ""
        lines = []
        for i, s in enumerate(summaries):
            round_num = len(self.rounds) - len(summaries) + i
            lines.append(s.to_prompt_str(round_num))
        return "\n".join(lines)

    def add_message(self, role: str, content: str) -> None:
        """添加消息到当前轮次对话历史"""
        self.current_round.add_message(role, content)

    def get_conversation_history(self, max_turns: int = 10) -> list[dict[str, str]]:
        """获取当前轮次对话历史"""
        return self.current_round.get_conversation_history(max_turns)

    def complete(self, result: SessionResult, summary: Optional[dict[str, Any]] = None) -> None:
        """完成当前轮次"""
        passed = result == SessionResult.PASSED
        self.current_round.complete(passed)

    def abandon(self) -> None:
        """放弃当前会话"""
        self.current_round.abandon()
        self.status = SessionStatus.ABANDONED

    def advance_phase(self) -> int:
        """推进到下一个教学阶段"""
        self.current_round.current_phase += 1
        self.current_phase = self.current_round.current_phase
        return self.current_round.current_phase

    def complete_phase(self) -> None:
        """标记当前阶段完成"""
        self.current_round.phases_completed.append(self.current_round.current_phase)

    def set_teaching_mode(self, mode: str) -> None:
        """设置教学模式"""
        self.current_round.teaching_mode = mode
        self.current_round.current_phase = 1

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "student_id": self.student_id,
            "course_id": self.course_id,
            "kp_id": self.kp_id,
            "status": self.status.value if isinstance(self.status, SessionStatus) else self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "rounds": [r.to_dict() for r in self.rounds],
            "current_round_index": self.current_round_index,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LearningSession":
        """Create from dictionary."""
        session = cls(
            id=data["id"],
            student_id=data["student_id"],
            course_id=data["course_id"],
            kp_id=data.get("kp_id"),
            status=SessionStatus(data.get("status", "active")),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            rounds=[],  # 先创建空列表
            current_round_index=data.get("current_round_index", 0),
        )
        
        # 解析轮次
        rounds_data = data.get("rounds", [])
        for r_data in rounds_data:
            session.rounds.append(LearningRound.from_dict(r_data))
        
        # 兼容旧数据格式（没有 rounds 字段）
        if not session.rounds and "messages" in data:
            # 从旧格式迁移
            old_round = LearningRound(
                round_number=data.get("learning_round", 1),
                start_time=datetime.fromisoformat(data["start_time"]) if data.get("start_time") else datetime.now(),
                end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
                messages=data.get("messages", []),
                teaching_mode=data.get("teaching_mode"),
                current_phase=data.get("current_phase", 1),
            )
            session.rounds.append(old_round)
        
        return session
