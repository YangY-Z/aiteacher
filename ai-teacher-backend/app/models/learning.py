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
    """

    id: str
    student_id: int
    course_id: str
    kp_id: Optional[str] = None
    status: SessionStatus = SessionStatus.ACTIVE
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration: Optional[int] = None  # seconds
    result: Optional[SessionResult] = None
    summary: Optional[dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)

    def complete(
        self,
        result: SessionResult,
        summary: Optional[dict[str, Any]] = None,
    ) -> None:
        """Complete the learning session.

        Args:
            result: Result of the session.
            summary: Optional session summary.
        """
        self.status = SessionStatus.COMPLETED
        self.end_time = datetime.now()
        self.duration = int((self.end_time - self.start_time).total_seconds())
        self.result = result
        self.summary = summary

    def abandon(self) -> None:
        """Mark the session as abandoned."""
        self.status = SessionStatus.ABANDONED
        self.end_time = datetime.now()
        self.duration = int((self.end_time - self.start_time).total_seconds())
