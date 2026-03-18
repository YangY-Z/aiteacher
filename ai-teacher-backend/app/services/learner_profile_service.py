"""Learner profile service for learner type classification and teaching strategies.

This module provides services for:
- Classifying learner types based on knowledge mastery
- Generating teaching strategies based on learner type
- Managing learner profiles and metrics
"""

from datetime import datetime
from typing import Optional

from app.core.exceptions import EntityNotFoundError
from app.models.learner_profile import (
    DEFAULT_TEACHING_STRATEGIES,
    ErrorPatternType,
    LearnerMetrics,
    LearnerProfile,
    LearnerType,
    LearningPreference,
    TeachingStrategy,
)
from app.repositories.course_repository import course_repository
from app.repositories.learner_profile_repository import learner_profile_repository
from app.repositories.learning_repository import (
    LearningRecordRepository,
    StudentProfileRepository,
)
from app.repositories.memory_db import db


class LearnerProfileService:
    """Service for learner profile management and classification."""

    # Thresholds for learner type classification
    PREREQUISITE_WEAK_THRESHOLD = 0.6  # 前置知识薄弱阈值
    CURRENT_MASTERY_THRESHOLD = 0.7  # 当前知识点掌握阈值
    LEARNED_THRESHOLD = 1  # 学过当前知识点的尝试次数阈值

    def __init__(self) -> None:
        """Initialize the service with repositories."""
        self._learning_record_repo = LearningRecordRepository()
        self._student_profile_repo = StudentProfileRepository()

    def get_or_create_profile(
        self,
        student_id: int,
        course_id: str,
        prerequisite_mastery: float = 0.0,
    ) -> LearnerProfile:
        """Get existing profile or create a new one.

        Args:
            student_id: Student ID.
            course_id: Course ID.
            prerequisite_mastery: Initial prerequisite mastery level.

        Returns:
            The learner profile.
        """
        profile = learner_profile_repository.get_by_student_and_course(
            student_id, course_id
        )

        if not profile:
            # Create new profile
            metrics = LearnerMetrics(prerequisite_mastery=prerequisite_mastery)
            profile = LearnerProfile(
                id=0,
                student_id=student_id,
                course_id=course_id,
                metrics=metrics,
            )
            profile = learner_profile_repository.create(profile)

        return profile

    def classify_learner(
        self,
        student_id: int,
        course_id: str,
        kp_id: str,
    ) -> tuple[LearnerType, str, LearnerMetrics]:
        """Classify learner type based on learning history and mastery.

        Args:
            student_id: Student ID.
            course_id: Course ID.
            kp_id: Current knowledge point ID.

        Returns:
            Tuple of (learner_type, classification_reason, metrics).
        """
        # Get or create profile
        profile = self.get_or_create_profile(student_id, course_id)

        # Calculate metrics
        metrics = self._calculate_metrics(student_id, course_id, kp_id)

        # Get knowledge point dependencies
        prerequisite_kp_ids = self._get_prerequisites(kp_id)

        # Check if student has learned the current knowledge point
        learned_current = self._has_learned_kp(student_id, kp_id)

        # Check prerequisite mastery
        prerequisite_mastery = self._calculate_prerequisite_mastery(
            student_id, prerequisite_kp_ids
        )

        # Update metrics
        metrics.prerequisite_mastery = prerequisite_mastery

        # Classify based on rules
        learner_type, reason = self._apply_classification_rules(
            first_time=not learned_current,
            prerequisite_mastery=prerequisite_mastery,
            learned_current=learned_current,
            current_mastery=metrics.current_kp_mastery,
        )

        # Update profile
        profile.update_learner_type(learner_type, reason)
        profile.metrics = metrics
        learner_profile_repository.update(profile)

        return learner_type, reason, metrics

    def _apply_classification_rules(
        self,
        first_time: bool,
        prerequisite_mastery: float,
        learned_current: bool,
        current_mastery: float,
    ) -> tuple[LearnerType, str]:
        """Apply classification rules to determine learner type.

        Classification rules:
        - NOVICE: First time learning, weak prerequisite knowledge
        - INTERMEDIATE: Has prerequisite knowledge, but hasn't learned current topic
        - REVIEWER: Has learned the topic before, but hasn't mastered it
        - ADVANCED: Already mastered, needs reinforcement

        Args:
            first_time: Whether this is first time learning this KP.
            prerequisite_mastery: Prerequisite knowledge mastery level.
            learned_current: Whether student has learned current KP.
            current_mastery: Current KP mastery level.

        Returns:
            Tuple of (learner_type, reason).
        """
        # 新手：第一次学这个知识，前置知识薄弱
        if first_time and prerequisite_mastery < self.PREREQUISITE_WEAK_THRESHOLD:
            return (
                LearnerType.NOVICE,
                f"新手学习者：首次学习该知识点，前置知识掌握度为{prerequisite_mastery:.1%}（低于{self.PREREQUISITE_WEAK_THRESHOLD:.0%}阈值）",
            )

        # 有基础者：学过相关内容，但未掌握本知识点
        if (
            prerequisite_mastery >= self.PREREQUISITE_WEAK_THRESHOLD
            and not learned_current
        ):
            return (
                LearnerType.INTERMEDIATE,
                f"有基础者：前置知识掌握度为{prerequisite_mastery:.1%}（达到阈值），但未学习过当前知识点",
            )

        # 复习者：学过本知识点，但遗忘或未掌握
        if learned_current and current_mastery < self.CURRENT_MASTERY_THRESHOLD:
            return (
                LearnerType.REVIEWER,
                f"复习者：曾学习过该知识点，当前掌握度为{current_mastery:.1%}（低于{self.CURRENT_MASTERY_THRESHOLD:.0%}阈值）",
            )

        # 熟练者：已掌握，需要强化或拓展
        if current_mastery >= self.CURRENT_MASTERY_THRESHOLD:
            return (
                LearnerType.ADVANCED,
                f"熟练者：已掌握该知识点，掌握度为{current_mastery:.1%}（达到{self.CURRENT_MASTERY_THRESHOLD:.0%}阈值），建议进行强化训练",
            )

        # Default to NOVICE if no other conditions match
        return (LearnerType.NOVICE, "默认分类为新手学习者")

    def get_teaching_strategy(
        self,
        learner_type: LearnerType,
        kp_type: Optional[str] = None,
    ) -> TeachingStrategy:
        """Get teaching strategy based on learner type.

        Args:
            learner_type: The learner type.
            kp_type: Optional knowledge point type for customization.

        Returns:
            The recommended teaching strategy.
        """
        # Get default strategy for learner type
        strategy = DEFAULT_TEACHING_STRATEGIES.get(learner_type)

        if not strategy:
            # Fallback to INTERMEDIATE strategy
            strategy = DEFAULT_TEACHING_STRATEGIES[LearnerType.INTERMEDIATE]

        # Customize based on knowledge point type if provided
        if kp_type:
            strategy = self._customize_strategy_for_kp_type(strategy, kp_type)

        return strategy

    def _customize_strategy_for_kp_type(
        self,
        strategy: TeachingStrategy,
        kp_type: str,
    ) -> TeachingStrategy:
        """Customize teaching strategy based on knowledge point type.

        Args:
            strategy: Base teaching strategy.
            kp_type: Knowledge point type (concept, formula, skill).

        Returns:
            Customized teaching strategy.
        """
        # Create a copy to avoid modifying the default
        customized = TeachingStrategy(
            learner_type=strategy.learner_type,
            primary_strategy=strategy.primary_strategy,
            secondary_strategies=strategy.secondary_strategies.copy(),
            example_count=strategy.example_count,
            practice_count=strategy.practice_count,
            hint_level=strategy.hint_level,
            pacing=strategy.pacing,
            focus_areas=strategy.focus_areas.copy(),
            scaffolding=strategy.scaffolding,
        )

        # Adjust based on knowledge point type
        if kp_type == "concept":
            customized.focus_areas.extend(["概念理解", "实例辨析"])
            customized.example_count += 1
        elif kp_type == "formula":
            customized.focus_areas.extend(["公式推导", "条件记忆"])
            customized.practice_count += 1
        elif kp_type == "skill":
            customized.focus_areas.extend(["步骤规范", "练习强化"])
            customized.practice_count += 2

        return customized

    def update_metrics(
        self,
        student_id: int,
        course_id: str,
        metrics_update: dict,
    ) -> LearnerMetrics:
        """Update learner metrics for a student.

        Args:
            student_id: Student ID.
            course_id: Course ID.
            metrics_update: Dictionary of metrics to update.

        Returns:
            Updated metrics.
        """
        profile = self.get_or_create_profile(student_id, course_id)

        # Update specific metrics
        if "score" in metrics_update:
            profile.metrics.update_score(metrics_update["score"])

        if "learning_time" in metrics_update:
            profile.metrics.total_learning_time += metrics_update["learning_time"]

        if "session_completed" in metrics_update:
            profile.metrics.total_sessions += 1

        # Update other metrics
        for key, value in metrics_update.items():
            if key not in ["score", "learning_time", "session_completed"]:
                if hasattr(profile.metrics, key):
                    setattr(profile.metrics, key, value)

        learner_profile_repository.update(profile)

        return profile.metrics

    def add_error_pattern(
        self,
        student_id: int,
        course_id: str,
        pattern_type: ErrorPatternType,
        example: Optional[str] = None,
    ) -> None:
        """Add an error pattern to learner metrics.

        Args:
            student_id: Student ID.
            course_id: Course ID.
            pattern_type: Type of error pattern.
            example: Optional example of the error.
        """
        profile = self.get_or_create_profile(student_id, course_id)
        profile.metrics.add_error_pattern(pattern_type, example)
        learner_profile_repository.update(profile)

    def get_profile(self, student_id: int, course_id: str) -> LearnerProfile:
        """Get learner profile for a student in a course.

        Args:
            student_id: Student ID.
            course_id: Course ID.

        Returns:
            The learner profile.

        Raises:
            EntityNotFoundError: If profile not found.
        """
        profile = learner_profile_repository.get_by_student_and_course(
            student_id, course_id
        )
        if not profile:
            raise EntityNotFoundError("学习者画像", f"{student_id}/{course_id}")
        return profile

    def get_learner_type_history(
        self,
        student_id: int,
        course_id: str,
    ) -> list[dict]:
        """Get history of learner type changes.

        Args:
            student_id: Student ID.
            course_id: Course ID.

        Returns:
            List of type change records.
        """
        profile = self.get_or_create_profile(student_id, course_id)
        return profile.type_history

    def update_preferences(
        self,
        student_id: int,
        course_id: str,
        preferences_update: dict,
    ) -> LearningPreference:
        """Update learning preferences.

        Args:
            student_id: Student ID.
            course_id: Course ID.
            preferences_update: Dictionary of preferences to update.

        Returns:
            Updated preferences.
        """
        profile = self.get_or_create_profile(student_id, course_id)

        for key, value in preferences_update.items():
            if hasattr(profile.preferences, key):
                setattr(profile.preferences, key, value)

        learner_profile_repository.update(profile)
        return profile.preferences

    def _calculate_metrics(
        self,
        student_id: int,
        course_id: str,
        kp_id: str,
    ) -> LearnerMetrics:
        """Calculate learner metrics.

        Args:
            student_id: Student ID.
            course_id: Course ID.
            kp_id: Current knowledge point ID.

        Returns:
            Calculated metrics.
        """
        # Get student profile for the course
        student_profile = self._student_profile_repo.get_by_student_and_course(
            student_id, course_id
        )

        # Get learning records for the current KP
        learning_records = self._get_learning_records_for_kp(student_id, kp_id)

        # Calculate metrics
        metrics = LearnerMetrics()

        if student_profile:
            metrics.total_sessions = student_profile.session_count
            metrics.total_learning_time = student_profile.total_time

        if learning_records:
            # Calculate current KP mastery
            total_attempts = sum(lr.attempt_count for lr in learning_records)
            passed_attempts = sum(
                1
                for lr in learning_records
                for attempt in lr.attempts
                if attempt.result == "passed"
            )

            if total_attempts > 0:
                metrics.current_kp_mastery = passed_attempts / (
                    total_attempts * 2
                )  # Normalize

            # Calculate average score from recent attempts
            recent_scores = []
            for lr in learning_records:
                for attempt in lr.attempts:
                    if attempt.score > 0:
                        recent_scores.append(attempt.score)

            if recent_scores:
                metrics.average_score = sum(recent_scores) / len(recent_scores)
                metrics.questions_answered = len(recent_scores)
                metrics.questions_correct = sum(1 for s in recent_scores if s >= 0.6)

            # Calculate learning velocity (relative to average)
            # This is a simplified calculation
            metrics.learning_velocity = min(1.0, metrics.average_score * 1.2)

        return metrics

    def _get_prerequisites(self, kp_id: str) -> list[str]:
        """Get prerequisite knowledge point IDs.

        Args:
            kp_id: Knowledge point ID.

        Returns:
            List of prerequisite knowledge point IDs.
        """
        prerequisites = []
        for dep in db._kp_dependencies:
            if dep.kp_id == kp_id:
                prerequisites.append(dep.depends_on_kp_id)
        return prerequisites

    def _has_learned_kp(self, student_id: int, kp_id: str) -> bool:
        """Check if student has learned a knowledge point.

        Args:
            student_id: Student ID.
            kp_id: Knowledge point ID.

        Returns:
            True if student has at least one learning record for the KP.
        """
        for record in db._learning_records.values():
            if record.student_id == student_id and record.kp_id == kp_id:
                return record.attempt_count >= self.LEARNED_THRESHOLD
        return False

    def _calculate_prerequisite_mastery(
        self,
        student_id: int,
        prerequisite_kp_ids: list[str],
    ) -> float:
        """Calculate mastery level of prerequisite knowledge points.

        Args:
            student_id: Student ID.
            prerequisite_kp_ids: List of prerequisite KP IDs.

        Returns:
            Average mastery level of prerequisites.
        """
        if not prerequisite_kp_ids:
            return 1.0  # No prerequisites, assume full mastery

        mastery_levels = []
        for kp_id in prerequisite_kp_ids:
            # Check if mastered
            for record in db._learning_records.values():
                if record.student_id == student_id and record.kp_id == kp_id:
                    if record.status.value == "mastered":
                        mastery_levels.append(1.0)
                    elif record.attempt_count > 0:
                        # Partial mastery based on attempts
                        passed = sum(
                            1 for a in record.attempts if a.result == "passed"
                        )
                        mastery_levels.append(passed / max(record.attempt_count, 1))
                    break
            else:
                # No record found, assume not mastered
                mastery_levels.append(0.0)

        return sum(mastery_levels) / len(mastery_levels) if mastery_levels else 0.0

    def _get_learning_records_for_kp(
        self,
        student_id: int,
        kp_id: str,
    ) -> list:
        """Get all learning records for a specific knowledge point.

        Args:
            student_id: Student ID.
            kp_id: Knowledge point ID.

        Returns:
            List of learning records.
        """
        records = []
        for record in db._learning_records.values():
            if record.student_id == student_id and record.kp_id == kp_id:
                records.append(record)
        return records

    def get_all_learner_types(self) -> list[dict]:
        """Get all available learner types with descriptions.

        Returns:
            List of learner type information.
        """
        return [
            {
                "type": lt.value,
                "description": LearnerType.get_description(lt),
            }
            for lt in LearnerType
        ]


# Global service instance
learner_profile_service = LearnerProfileService()
