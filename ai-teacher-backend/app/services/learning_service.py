"""Learning service for learning session management."""

import json
from typing import Any, Optional
import uuid

from app.core.exceptions import EntityNotFoundError, LearningSessionError
from app.models.learning import (
    LearningRecord,
    LearningSession,
    LearningStatus,
    SessionStatus,
    SessionResult,
    StudentProfile,
    AttemptRecord,
)
from app.models.assessment import AssessmentQuestion, StudentAnswer
from app.repositories.learning_repository import (
    learning_record_repository,
    learning_session_repository,
    student_profile_repository,
)
from app.repositories.assessment_repository import (
    assessment_question_repository,
    student_answer_repository,
)
from app.repositories.course_repository import knowledge_point_repository
from app.services.llm_service import llm_service
from app.services.course_service import course_service
from app.prompts.system_prompt import SYSTEM_PROMPT
from app.prompts.teaching_prompt import (
    TEACHING_PROMPT,
    get_teaching_requirements,
)


class LearningService:
    """Service for learning session management."""

    def start_session(
        self,
        student_id: int,
        course_id: str,
        kp_id: Optional[str] = None,
    ) -> LearningSession:
        """Start a new learning session.

        Args:
            student_id: Student ID.
            course_id: Course ID.
            kp_id: Optional specific knowledge point to start with.

        Returns:
            Created learning session.
        """
        # Check for existing active session
        existing = learning_session_repository.get_active_by_student(
            student_id, course_id
        )
        if existing:
            # Update session's kp_id to current progress if not specified
            if not kp_id:
                profile = student_profile_repository.get_by_student_and_course(
                    student_id, course_id
                )
                if profile and profile.current_kp_id:
                    existing.kp_id = profile.current_kp_id
                    learning_session_repository.update(existing)
            return existing

        # Get or create student profile
        profile = student_profile_repository.get_by_student_and_course(
            student_id, course_id
        )
        if not profile:
            profile = StudentProfile(
                id=0,
                student_id=student_id,
                course_id=course_id,
            )
            profile = student_profile_repository.create(profile)

        # Determine starting knowledge point
        if not kp_id:
            if profile.current_kp_id:
                kp_id = profile.current_kp_id
            else:
                first_kp = course_service.get_first_knowledge_point(course_id)
                kp_id = first_kp.id

        # Create session
        session = LearningSession(
            id=f"SESSION_{uuid.uuid4().hex[:8].upper()}",
            student_id=student_id,
            course_id=course_id,
            kp_id=kp_id,
        )

        return learning_session_repository.create(session)

    def get_session(self, session_id: str) -> LearningSession:
        """Get a learning session by ID.

        Args:
            session_id: Session ID.

        Returns:
            Learning session.

        Raises:
            EntityNotFoundError: If session not found.
        """
        session = learning_session_repository.get_by_id(session_id)
        if not session:
            raise EntityNotFoundError("学习会话", session_id)
        return session

    def get_or_create_record(
        self,
        student_id: int,
        kp_id: str,
    ) -> LearningRecord:
        """Get or create a learning record for a knowledge point.

        Args:
            student_id: Student ID.
            kp_id: Knowledge point ID.

        Returns:
            Learning record.
        """
        record = learning_record_repository.get_by_student_and_kp(student_id, kp_id)
        if not record:
            record = LearningRecord(
                id=0,
                student_id=student_id,
                kp_id=kp_id,
                status=LearningStatus.PENDING,
            )
            record = learning_record_repository.create(record)

        # Update status to learning
        if record.status == LearningStatus.PENDING:
            record.status = LearningStatus.LEARNING
            learning_record_repository.update(record)

        return record

    def generate_teaching_content(
        self,
        session: LearningSession,
        student_name: str,
    ) -> dict[str, Any]:
        """Generate teaching content for the current knowledge point.

        Args:
            session: Learning session.
            student_name: Student name for personalization.

        Returns:
            Teaching content response.
        """
        if not session.kp_id:
            raise LearningSessionError("会话没有当前知识点")

        # Get knowledge point info
        kp_info = course_service.get_knowledge_point_info(session.kp_id)
        record = self.get_or_create_record(session.student_id, session.kp_id)

        # Build attempt info
        attempt_info = ""
        if record.attempt_count > 0:
            last_error = record.get_last_error_type()
            attempt_info = f"- 上次学习时间：{record.updated_at}\n- 上次评估结果：{'通过' if record.attempts[-1].result == 'passed' else '未通过'}\n- 主要错误类型：{last_error or '无'}"

        # Get teaching requirements
        teaching_requirements = get_teaching_requirements(
            kp_info["type"],
            record.attempt_count + 1,
            record.get_last_error_type() or "",
        )

        # Build prompt
        prompt = TEACHING_PROMPT.format(
            knowledge_point_name=kp_info["name"],
            knowledge_point_id=kp_info["id"],
            knowledge_point_type=kp_info["type"],
            description=kp_info["description"] or "",
            key_points=", ".join(knowledge_point_repository.get_by_id(kp_info["id"]).key_points) if knowledge_point_repository.get_by_id(kp_info["id"]) else "",
            dependencies=", ".join(kp_info["dependency_names"]) if kp_info["dependency_names"] else "无",
            student_name=student_name,
            attempt_count=record.attempt_count + 1,
            attempt_info=attempt_info,
            teaching_requirements=teaching_requirements,
        )

        # Call LLM
        response = llm_service.chat_json(SYSTEM_PROMPT, prompt)

        return response

    def process_student_message(
        self,
        session: LearningSession,
        message: str,
    ) -> dict[str, Any]:
        """Process a student message and generate a response.

        Args:
            session: Learning session.
            message: Student message.

        Returns:
            AI response.
        """
        # 快捷意图检测（不需要 LLM）
        if "跳过" in message or "已经会了" in message:
            return {
                "response_type": "确认",
                "content": {
                    "feedback": "好的，我理解你觉得这个知识点已经掌握了。让我们来做一道测试题确认一下。",
                },
                "whiteboard": {"formulas": [], "diagrams": []},
                "next_action": "start_assessment",
            }

        if "开始测试" in message or "开始评估" in message:
            return {
                "response_type": "引导",
                "content": {
                    "feedback": "好的，让我们开始测试！",
                },
                "whiteboard": {"formulas": [], "diagrams": []},
                "next_action": "start_assessment",
            }

        # 使用 LLM 处理学生的回答
        if not session.kp_id:
            return {
                "response_type": "反馈",
                "content": {
                    "feedback": "请先开始一个学习会话。",
                },
                "whiteboard": {"formulas": [], "diagrams": []},
                "next_action": "wait_for_student",
            }

        # 获取知识点信息
        kp_info = course_service.get_knowledge_point_info(session.kp_id)
        kp = knowledge_point_repository.get_by_id(session.kp_id)
        
        # 构建 prompt
        from app.prompts.question_prompt import CHAT_RESPONSE_PROMPT
        
        prompt = CHAT_RESPONSE_PROMPT.format(
            knowledge_point_name=kp_info["name"],
            knowledge_point_type=kp_info["type"],
            key_points=", ".join(kp.key_points) if kp and kp.key_points else kp_info["description"],
            dependencies=", ".join(kp_info["dependency_names"]) if kp_info["dependency_names"] else "无",
            student_message=message,
        )
        
        # 调用 LLM
        try:
            response = llm_service.chat_json(SYSTEM_PROMPT, prompt)
            
            # 确保 response 包含必要字段
            if "next_action" not in response:
                response["next_action"] = "wait_for_student"
            if "whiteboard" not in response:
                response["whiteboard"] = {"formulas": [], "diagrams": []}
            if "response_type" not in response:
                response["response_type"] = "反馈"
                
            return response
        except Exception as e:
            # LLM 调用失败时的降级处理
            logger.warning(f"LLM processing failed: {e}")
            return {
                "response_type": "反馈",
                "content": {
                    "feedback": "好的，我收到了你的回答。还有其他问题吗？或者输入'开始测试'检验学习效果。",
                },
                "whiteboard": {"formulas": [], "diagrams": []},
                "next_action": "wait_for_student",
            }

    def get_assessment_questions(
        self,
        kp_id: str,
        count: int = 2,
    ) -> list[AssessmentQuestion]:
        """Get assessment questions for a knowledge point.

        Args:
            kp_id: Knowledge point ID.
            count: Number of questions to return.

        Returns:
            List of assessment questions.
        """
        questions = assessment_question_repository.get_by_kp(kp_id)
        return questions[:count]

    def submit_assessment(
        self,
        session: LearningSession,
        answers: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Submit assessment answers and calculate results.

        Args:
            session: Learning session.
            answers: List of answer dicts with question_id and answer.

        Returns:
            Assessment result.
        """
        if not session.kp_id:
            raise LearningSessionError("会话没有当前知识点")

        kp = knowledge_point_repository.get_by_id(session.kp_id)
        if not kp:
            raise EntityNotFoundError("知识点", session.kp_id)

        pass_threshold = kp.get_pass_threshold()
        correct_count = 0

        # Check each answer
        for answer_data in answers:
            question_id = answer_data.get("question_id")
            student_answer = answer_data.get("answer")

            question = assessment_question_repository.get_by_id(question_id)
            if not question:
                continue

            is_correct = question.check_answer(student_answer)
            if is_correct:
                correct_count += 1

            # Save answer
            student_answer_repository.create(
                {
                    "session_id": session.id,
                    "student_id": session.student_id,
                    "question_id": question_id,
                    "kp_id": session.kp_id,
                    "student_answer": student_answer,
                    "is_correct": is_correct,
                }
            )

        # Calculate result
        passed = correct_count >= pass_threshold
        score = correct_count / len(answers) if answers else 0

        # Update learning record
        record = learning_record_repository.get_by_student_and_kp(
            session.student_id, session.kp_id
        )
        if record:
            attempt = record.add_attempt("passed" if passed else "failed")
            record.complete_attempt(
                attempt,
                record.updated_at,
                score,
            )

            if passed:
                record.mark_mastered()
            else:
                # Set error type for failed attempts
                record.attempts[-1].error_type = self._analyze_error_type(answers)

            learning_record_repository.update(record)

        # Update student profile
        profile = student_profile_repository.get_by_student_and_course(
            session.student_id, session.course_id
        )
        if profile:
            total_kps = len(course_service.get_course_knowledge_points(session.course_id))
            if passed:
                profile.add_mastered_kp(session.kp_id, total_kps)

            # Get next knowledge point
            next_kp = course_service.get_next_knowledge_point(
                session.course_id,
                session.kp_id,
                profile.completed_kp_ids + profile.mastered_kp_ids,
            )
            if next_kp:
                profile.set_current_kp(next_kp.id)
            else:
                profile.current_kp_id = None

            student_profile_repository.update(profile)

        # Determine if backtrack is required
        backtrack_required = False
        if not passed and record is not None:
            backtrack_required = record.attempt_count >= 2

        return {
            "result": "passed" if passed else "failed",
            "score": score,
            "correct_count": correct_count,
            "total_questions": len(answers),
            "passed": passed,
            "next_kp_id": profile.current_kp_id if profile else None,
            "next_kp_name": knowledge_point_repository.get_by_id(profile.current_kp_id).name if profile and profile.current_kp_id else None,
            "backtrack_required": backtrack_required,
        }

    def _analyze_error_type(self, answers: list[dict[str, Any]]) -> str:
        """Analyze the type of error based on answers.

        Args:
            answers: List of answer dicts.

        Returns:
            Error type string.
        """
        # Simple error type analysis
        return "概念混淆"

    def skip_knowledge_point(
        self,
        session: LearningSession,
        reason: Optional[str] = None,
    ) -> dict[str, Any]:
        """Skip the current knowledge point.

        Args:
            session: Learning session.
            reason: Optional reason for skipping.

        Returns:
            Result with next knowledge point info.
        """
        if not session.kp_id:
            raise LearningSessionError("会话没有当前知识点")

        # Update learning record
        record = learning_record_repository.get_by_student_and_kp(
            session.student_id, session.kp_id
        )
        if record:
            record.mark_skipped(reason)
            learning_record_repository.update(record)

        # Update student profile
        profile = student_profile_repository.get_by_student_and_course(
            session.student_id, session.course_id
        )
        if profile:
            if session.kp_id not in profile.skipped_kp_ids:
                profile.skipped_kp_ids.append(session.kp_id)

            # Get next knowledge point
            next_kp = course_service.get_next_knowledge_point(
                session.course_id,
                session.kp_id,
                profile.completed_kp_ids + profile.mastered_kp_ids + profile.skipped_kp_ids,
            )
            if next_kp:
                profile.set_current_kp(next_kp.id)
            else:
                profile.current_kp_id = None

            student_profile_repository.update(profile)

        return {
            "skipped_kp_id": session.kp_id,
            "next_kp_id": profile.current_kp_id if profile else None,
            "next_kp_name": knowledge_point_repository.get_by_id(profile.current_kp_id).name if profile and profile.current_kp_id else None,
        }

    def complete_knowledge_point(
        self,
        session: LearningSession,
    ) -> dict[str, Any]:
        """Mark current knowledge point as mastered (for concept-type KPs without assessment).

        Args:
            session: Learning session.

        Returns:
            Result with next knowledge point info.
        """
        if not session.kp_id:
            raise LearningSessionError("会话没有当前知识点")

        # Update learning record
        record = learning_record_repository.get_by_student_and_kp(
            session.student_id, session.kp_id
        )
        if record:
            record.mark_mastered()
            learning_record_repository.update(record)

        # Update student profile
        profile = student_profile_repository.get_by_student_and_course(
            session.student_id, session.course_id
        )
        if profile:
            total_kps = len(course_service.get_course_knowledge_points(session.course_id))
            profile.add_mastered_kp(session.kp_id, total_kps)

            # Get next knowledge point
            next_kp = course_service.get_next_knowledge_point(
                session.course_id,
                session.kp_id,
                profile.completed_kp_ids + profile.mastered_kp_ids,
            )
            if next_kp:
                profile.set_current_kp(next_kp.id)
            else:
                profile.current_kp_id = None

            student_profile_repository.update(profile)

        return {
            "completed_kp_id": session.kp_id,
            "next_kp_id": profile.current_kp_id if profile else None,
            "next_kp_name": knowledge_point_repository.get_by_id(profile.current_kp_id).name if profile and profile.current_kp_id else None,
        }

    def get_progress(self, student_id: int, course_id: str) -> dict[str, Any]:
        """Get learning progress for a student in a course.

        Args:
            student_id: Student ID.
            course_id: Course ID.

        Returns:
            Progress information.
        """
        profile = student_profile_repository.get_by_student_and_course(
            student_id, course_id
        )
        course = course_service.get_course(course_id)
        all_kps = course_service.get_course_knowledge_points(course_id)

        current_kp = None
        if profile and profile.current_kp_id:
            current_kp = knowledge_point_repository.get_by_id(profile.current_kp_id)

        return {
            "student_id": student_id,
            "course_id": course_id,
            "current_kp_id": profile.current_kp_id if profile else None,
            "current_kp_name": current_kp.name if current_kp else None,
            "completed_count": len(profile.completed_kp_ids) if profile else 0,
            "mastered_count": len(profile.mastered_kp_ids) if profile else 0,
            "skipped_count": len(profile.skipped_kp_ids) if profile else 0,
            "total_count": len(all_kps),
            "mastery_rate": profile.mastery_rate if profile else 0,
            "total_time": profile.total_time if profile else 0,
            "session_count": profile.session_count if profile else 0,
            "last_session_at": profile.last_session_at if profile else None,
        }


# Global service instance
learning_service = LearningService()
