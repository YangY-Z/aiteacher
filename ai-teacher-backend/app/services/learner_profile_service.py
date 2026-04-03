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
    
    def get_weak_knowledge_points(
        self,
        student_id: int,
        course_id: str,
        threshold: float = 0.6,
    ) -> list[dict]:
        """识别薄弱知识点

        Args:
            student_id: 学生ID
            course_id: 课程ID
            threshold: 掌握度阈值，低于此值视为薄弱

        Returns:
            薄弱知识点列表，包含：
            - kp_id: 知识点ID
            - kp_name: 知识点名称
            - mastery: 当前掌握度
            - error_count: 错误次数
            - error_patterns: 主要错误模式
        """
        from app.repositories.learning_repository import learning_record_repository
        from app.repositories.course_repository import knowledge_point_repository
        
        weak_kps = []
        
        # 获取学生学习记录
        learning_records = learning_record_repository.get_by_student_and_course(
            student_id, course_id
        )
        
        # 获取学习者画像（用于获取错误模式）
        profile = learner_profile_repository.get_by_student_and_course(
            student_id, course_id
        )
        
        for record in learning_records:
            # 计算掌握度
            mastery = self._calculate_kp_mastery(record)
            
            if mastery < threshold:
                kp = knowledge_point_repository.get_by_id(record.kp_id)
                
                # 获取该知识点的错误模式
                error_patterns = []
                if profile:
                    for ep in profile.metrics.error_patterns:
                        # 检查错误示例中是否包含该知识点
                        for example in ep.examples:
                            if kp and kp.name in example:
                                error_patterns.append({
                                    "type": ep.pattern_type.value,
                                    "frequency": ep.frequency,
                                })
                                break
                
                weak_kps.append({
                    "kp_id": record.kp_id,
                    "kp_name": kp.name if kp else record.kp_id,
                    "mastery": mastery,
                    "error_count": sum(
                        1 for a in record.attempts if a.result == "failed"
                    ),
                    "status": record.status.value,
                    "error_patterns": error_patterns,
                })
        
        # 按掌握度排序（最薄弱的在前）
        weak_kps.sort(key=lambda x: x["mastery"])
        
        return weak_kps
    
    def _calculate_kp_mastery(self, record) -> float:
        """计算知识点掌握度

        Args:
            record: 学习记录

        Returns:
            掌握度 (0.0 - 1.0)
        """
        if record.status.value == "mastered":
            return 1.0
        
        if not record.attempts:
            return 0.0
        
        # 基于尝试次数和通过率计算
        total_attempts = len(record.attempts)
        passed_attempts = sum(1 for a in record.attempts if a.result == "passed")
        
        # 考虑最近的表现（最近一次尝试权重更高）
        if record.attempts:
            last_result = record.attempts[-1].result
            last_score = record.attempts[-1].score if hasattr(record.attempts[-1], 'score') else 0.5
            
            # 综合计算：通过率占60%，最近得分占40%
            pass_rate = passed_attempts / total_attempts
            mastery = pass_rate * 0.6 + last_score * 0.4
        else:
            mastery = 0.0
        
        return min(1.0, max(0.0, mastery))
    
    def get_teaching_strategy_for_kp(
        self,
        student_id: int,
        course_id: str,
        kp_id: str,
        kp_type: Optional[str] = None,
    ) -> dict:
        """获取针对特定知识点的教学策略

        综合考虑学习者类型和知识点类型，返回完整的教学策略配置。

        Args:
            student_id: 学生ID
            course_id: 课程ID
            kp_id: 知识点ID
            kp_type: 知识点类型（概念/公式/技能）

        Returns:
            教学策略配置字典
        """
        # 1. 获取学习者分类
        learner_type, reason, metrics = self.classify_learner(
            student_id, course_id, kp_id
        )
        
        # 2. 获取基础教学策略
        strategy = self.get_teaching_strategy(learner_type, kp_type)
        
        # 3. 获取主要错误模式
        dominant_error = None
        if metrics.error_patterns:
            # 按频率排序，取最高的
            sorted_patterns = sorted(
                metrics.error_patterns,
                key=lambda x: x.frequency,
                reverse=True
            )
            dominant_error = sorted_patterns[0].pattern_type.value
        
        # 4. 生成教学要求
        teaching_requirements = self._generate_teaching_requirements(
            learner_type, metrics, dominant_error
        )
        
        return {
            "learner_type": learner_type.value,
            "learner_type_description": LearnerType.get_description(learner_type),
            "classification_reason": reason,
            "metrics": {
                "prerequisite_mastery": metrics.prerequisite_mastery,
                "current_kp_mastery": metrics.current_kp_mastery,
                "learning_velocity": metrics.learning_velocity,
                "average_score": metrics.average_score,
            },
            "strategy": {
                "primary_strategy": strategy.primary_strategy,
                "secondary_strategies": strategy.secondary_strategies,
                "example_count": strategy.example_count,
                "practice_count": strategy.practice_count,
                "hint_level": strategy.hint_level,
                "pacing": strategy.pacing,
                "focus_areas": strategy.focus_areas,
                "scaffolding": strategy.scaffolding,
            },
            "dominant_error_pattern": dominant_error,
            "teaching_requirements": teaching_requirements,
        }
    
    def _generate_teaching_requirements(
        self,
        learner_type: LearnerType,
        metrics: LearnerMetrics,
        dominant_error: Optional[str],
    ) -> list[str]:
        """根据学习者画像生成教学要求

        Args:
            learner_type: 学习者类型
            metrics: 学习指标
            dominant_error: 主要错误模式

        Returns:
            教学要求列表
        """
        requirements = []
        
        # 根据学习者类型
        if learner_type == LearnerType.NOVICE:
            requirements.append("从基础概念开始讲解，使用通俗易懂的语言")
            requirements.append("每个知识点配合2-3个简单示例")
            requirements.append("讲解过程中多提问确认理解")
            requirements.append("放慢教学节奏，确保每一步都清晰")
            
        elif learner_type == LearnerType.INTERMEDIATE:
            requirements.append("可以直接讲解核心内容")
            requirements.append("引导学生发现规律和结论")
            requirements.append("使用启发式提问")
            
        elif learner_type == LearnerType.REVIEWER:
            requirements.append("重点复习关键概念")
            requirements.append("使用不同于之前的讲解方式")
            requirements.append("增加辨析练习")
            
        elif learner_type == LearnerType.ADVANCED:
            requirements.append("简洁总结核心要点")
            requirements.append("增加拓展应用和综合题")
            requirements.append("鼓励学生举一反三")
        
        # 根据错误模式
        if dominant_error:
            error_requirements = {
                "concept_misunderstanding": "注意概念辨析，强调易混淆点",
                "calculation_error": "计算步骤要详细展示，提醒检查",
                "procedure_error": "分步演示，提供步骤清单",
                "prerequisite_gap": "先复习相关前置知识",
                "careless_error": "提醒细心，增加检查环节",
                "incomplete_answer": "强调答题完整性，提供模板",
            }
            if dominant_error in error_requirements:
                requirements.append(error_requirements[dominant_error])
        
        # 根据学习速度
        if metrics.learning_velocity < 0.5:
            requirements.append("学习节奏稍慢，多给一些时间理解")
        elif metrics.learning_velocity > 0.8:
            requirements.append("学习速度较快，可以适当增加内容")
        
        return requirements
    
    def record_error_from_assessment(
        self,
        student_id: int,
        course_id: str,
        kp_id: str,
        question_type: str,
        is_correct: bool,
        student_answer: Optional[str] = None,
    ) -> None:
        """根据评估结果自动识别并记录错误模式

        Args:
            student_id: 学生ID
            course_id: 课程ID
            kp_id: 知识点ID
            question_type: 题目类型
            is_correct: 是否正确
            student_answer: 学生答案（用于分析）
        """
        if is_correct:
            return
        
        # 根据题目类型和知识点推断错误模式
        error_type = self._infer_error_pattern(question_type, kp_id, student_answer)
        
        if error_type:
            self.add_error_pattern(
                student_id,
                course_id,
                error_type,
                student_answer,
            )
    
    def _infer_error_pattern(
        self,
        question_type: str,
        kp_id: str,
        student_answer: Optional[str],
    ) -> Optional[ErrorPatternType]:
        """推断错误模式类型

        Args:
            question_type: 题目类型
            kp_id: 知识点ID
            student_answer: 学生答案

        Returns:
            推断的错误模式类型
        """
        from app.repositories.course_repository import knowledge_point_repository
        
        kp = knowledge_point_repository.get_by_id(kp_id)
        kp_name = kp.name if kp else ""
        
        # 基于知识点类型推断
        if kp and kp.type == "概念":
            return ErrorPatternType.CONCEPT_MISUNDERSTANDING
        elif kp and kp.type == "公式":
            # 公式类可能是记忆问题或计算问题
            if student_answer and any(c.isdigit() for c in student_answer):
                return ErrorPatternType.CALCULATION_ERROR
            return ErrorPatternType.CONCEPT_MISUNDERSTANDING
        elif kp and kp.type == "技能":
            # 技能类通常是步骤问题
            if "步骤" in kp_name or "画" in kp_name or "求" in kp_name:
                return ErrorPatternType.PROCEDURE_ERROR
            return ErrorPatternType.CALCULATION_ERROR
        
        # 基于题目类型推断
        if question_type == "选择题":
            return ErrorPatternType.CONCEPT_MISUNDERSTANDING
        elif question_type == "填空题":
            return ErrorPatternType.CALCULATION_ERROR
        elif question_type == "计算题":
            return ErrorPatternType.CALCULATION_ERROR
        elif question_type == "作图题":
            return ErrorPatternType.PROCEDURE_ERROR
        
        return ErrorPatternType.CONCEPT_MISUNDERSTANDING
    
    def record_learning_activity(
        self,
        student_id: int,
        course_id: str,
        kp_id: str,
        score: float,
        passed: bool,
    ) -> None:
        """记录学习活动，用于更新学习指标

        Args:
            student_id: 学生ID
            course_id: 课程ID
            kp_id: 知识点ID
            score: 本次得分 (0.0 - 1.0)
            passed: 是否通过
        """
        profile = self.get_or_create_profile(student_id, course_id)
        
        # 更新学习统计
        if not hasattr(profile.metrics, 'total_sessions'):
            profile.metrics.total_sessions = 0
        profile.metrics.total_sessions += 1
        
        if not hasattr(profile.metrics, 'total_score_sum'):
            profile.metrics.total_score_sum = 0.0
        profile.metrics.total_score_sum += score
        
        if passed:
            if not hasattr(profile.metrics, 'passed_sessions'):
                profile.metrics.passed_sessions = 0
            profile.metrics.passed_sessions += 1
        
        # 更新平均分
        if profile.metrics.total_sessions > 0:
            profile.metrics.average_score = (
                profile.metrics.total_score_sum / profile.metrics.total_sessions
            )
        
        # 更新最后活动时间
        profile.last_activity_at = datetime.now()
        
        # 保存更新
        learner_profile_repository.update(profile)


# Global service instance
learner_profile_service = LearnerProfileService()
