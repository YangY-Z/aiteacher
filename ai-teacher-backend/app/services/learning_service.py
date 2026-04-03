"""Learning service for learning session management."""

import json
import logging
import re
from datetime import datetime
from typing import Any, Optional, AsyncGenerator
import uuid

logger = logging.getLogger(__name__)

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
    generate_teaching_prompt,
    get_teaching_mode_for_kp,
)
from app.services.teaching_mode_service import teaching_mode_service
from app.prompts.question_prompt import CHAT_RESPONSE_PROMPT


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

        # Get teaching mode for this knowledge point
        kp = knowledge_point_repository.get_by_id(kp_id)
        kp_type = kp.type if kp else "概念"
        teaching_mode = get_teaching_mode_for_kp(kp_type)

        # Create session with first round
        from app.models.learning import LearningRound
        first_round = LearningRound(
            round_number=1,
            start_time=datetime.now(),
            teaching_mode=teaching_mode.value if hasattr(teaching_mode, 'value') else teaching_mode,
        )
        
        session = LearningSession(
            id=f"SESSION_{uuid.uuid4().hex[:8].upper()}",
            student_id=student_id,
            course_id=course_id,
            kp_id=kp_id,
            rounds=[first_round],
            current_round_index=0,
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
        next_kp_id = None
        next_kp_name = None
        
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
                next_kp_id = next_kp.id
                next_kp_name = next_kp.name
            else:
                profile.current_kp_id = None

            student_profile_repository.update(profile)

        # Update session's kp_id to the next knowledge point (only if passed)
        if passed and next_kp_id:
            session.kp_id = next_kp_id
            learning_session_repository.update(session)

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
            "next_kp_id": next_kp_id,
            "next_kp_name": next_kp_name,
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
        next_kp_id = None
        next_kp_name = None
        
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
                next_kp_id = next_kp.id
                next_kp_name = next_kp.name
            else:
                profile.current_kp_id = None

            student_profile_repository.update(profile)

        # Update session's kp_id to the next knowledge point
        if next_kp_id:
            session.kp_id = next_kp_id
            learning_session_repository.update(session)

        return {
            "skipped_kp_id": profile.skipped_kp_ids[-1] if profile and profile.skipped_kp_ids else None,
            "next_kp_id": next_kp_id,
            "next_kp_name": next_kp_name,
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
        next_kp_id = None
        next_kp_name = None
        
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
                next_kp_id = next_kp.id
                next_kp_name = next_kp.name
            else:
                profile.current_kp_id = None

            student_profile_repository.update(profile)

        # Update session's kp_id to the next knowledge point
        if next_kp_id:
            session.kp_id = next_kp_id
            learning_session_repository.update(session)

        return {
            "completed_kp_id": session.kp_id if not next_kp_id else profile.mastered_kp_ids[-1] if profile else None,
            "next_kp_id": next_kp_id,
            "next_kp_name": next_kp_name,
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

    async def stream_teaching_content(
        self,
        session: LearningSession,
        student_name: str,
        trace_id: str = "",
        learning_round: int = 1,
        history_summary: str = "",
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream teaching content for the current knowledge point using JSONL format.

        Args:
            session: Learning session.
            student_name: Student name for personalization.
            trace_id: 链路追踪ID.
            learning_round: 当前学习轮次（第几次学习该知识点）。
            history_summary: 历史学习总结（用于回顾）。

        Yields:
            SSE events with incremental content.
        """
        if not session.kp_id:
            logger.error(f"[{trace_id}] 会话没有当前知识点")
            yield {"event": "error", "data": json.dumps({"error": "会话没有当前知识点"}, ensure_ascii=False)}
            return

        logger.info(f"[{trace_id}] === 步骤1: 获取知识点信息 ===")
        # Get knowledge point info
        kp_info = course_service.get_knowledge_point_info(session.kp_id)
        record = self.get_or_create_record(session.student_id, session.kp_id)
        logger.info(f"[{trace_id}] 知识点: name={kp_info.get('name')}, type={kp_info.get('type')}, attempt_count={record.attempt_count}, learning_round={learning_round}")

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

        # Determine learner type based on attempt count and history
        learner_type = "intermediate"  # default
        if record.attempt_count == 0:
            learner_type = "novice"
        elif record.attempt_count >= 3:
            learner_type = "reviewer"
        elif record.attempt_count == 1 and record.attempts and record.attempts[0].result == "passed":
            learner_type = "advanced"

        # Get teaching mode from session or determine from knowledge point type
        if session.teaching_mode:
            from app.models.teaching_mode import TeachingModeType
            teaching_mode = TeachingModeType(session.teaching_mode)
        else:
            teaching_mode = get_teaching_mode_for_kp(kp_info["type"])

        # Get current phase from session
        current_phase = session.current_phase if session.current_phase else 1

        # Build prompt using teaching mode and current phase
        prompt = generate_teaching_prompt(
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
            learner_type=learner_type,
            current_phase=current_phase,
            learning_round=learning_round,
            history_summary=history_summary,
        )

        logger.info(f"[{trace_id}] === 步骤3: 生成教学Prompt完成, 长度={len(prompt)}字符 ===")

        # Stream LLM response and parse JSONL
        buffer = ""
        event_count = 0
        
        logger.info(f"[{trace_id}] === 步骤4: 开始流式调用LLM ===")
        for chunk in llm_service.stream_chat(SYSTEM_PROMPT, prompt, trace_id=trace_id):
            buffer += chunk
            
            # Try to parse complete JSON lines
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                
                if not line:
                    continue
                
                # Try to parse as JSON
                try:
                    # Skip markdown code blocks
                    if line.startswith("```"):
                        continue
                    
                    # 修复反斜杠转义问题：将单反斜杠转为双反斜杠（但不是已经双转义的）
                    # 例如：\frac -> \\frac, \pi -> \\pi
                    line_fixed = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', line)
                    
                    data = json.loads(line_fixed)
                    event_type = data.get("type", "")
                    event_count += 1
                    
                    if event_type == "segment":
                        # 边讲边写模式：同时发送消息和白板内容
                        message_content = data.get("message", "")
                        whiteboard = data.get("whiteboard", {})
                        
                        # 先发送白板内容（如果有）
                        if whiteboard:
                            # 发送segment事件（前端可以同时处理消息和白板）
                            yield {"event": "segment", "data": json.dumps({
                                "message": message_content,
                                "whiteboard": whiteboard
                            }, ensure_ascii=False)}
                        else:
                            # 只有消息，没有白板内容
                            yield {"event": "segment", "data": json.dumps({
                                "message": message_content,
                                "whiteboard": {}
                            }, ensure_ascii=False)}
                    
                    elif event_type == "wb_title":
                        # 白板标题（兼容旧格式）
                        yield {"event": "wb_title", "data": json.dumps({"content": data.get("content", "")}, ensure_ascii=False)}
                    
                    elif event_type == "wb_points":
                        # 白板要点（增量，兼容旧格式）
                        yield {"event": "wb_points", "data": json.dumps({"content": data.get("content", "")}, ensure_ascii=False)}
                    
                    elif event_type == "wb_formulas":
                        # 白板公式（增量，兼容旧格式）
                        yield {"event": "wb_formulas", "data": json.dumps({"content": data.get("content", "")}, ensure_ascii=False)}
                    
                    elif event_type == "wb_examples":
                        # 白板示例（增量，兼容旧格式）
                        yield {"event": "wb_examples", "data": json.dumps({"content": data.get("content", "")}, ensure_ascii=False)}
                    
                    elif event_type == "wb_notes":
                        # 白板注意事项（增量，兼容旧格式）
                        yield {"event": "wb_notes", "data": json.dumps({"content": data.get("content", "")}, ensure_ascii=False)}
                    
                    elif event_type == "msg_intro":
                        # 引入消息（兼容旧格式）
                        yield {"event": "msg_intro", "data": json.dumps({"content": data.get("content", "")}, ensure_ascii=False)}
                    
                    elif event_type == "msg_def":
                        # 定义消息（兼容旧格式）
                        yield {"event": "msg_def", "data": json.dumps({"content": data.get("content", "")}, ensure_ascii=False)}
                    
                    elif event_type == "msg_example":
                        # 示例消息（兼容旧格式）
                        yield {"event": "msg_example", "data": json.dumps({"content": data.get("content", "")}, ensure_ascii=False)}
                    
                    elif event_type == "msg_summary":
                        # 总结消息（兼容旧格式）
                        yield {"event": "msg_summary", "data": json.dumps({"content": data.get("content", "")}, ensure_ascii=False)}
                    
                    elif event_type == "msg_question":
                        # 提问消息（兼容旧格式）
                        yield {"event": "msg_question", "data": json.dumps({"content": data.get("content", "")}, ensure_ascii=False)}
                    
                    elif event_type == "complete":
                        # 完成事件
                        logger.info(f"[{trace_id}] 收到complete事件: next_action={data.get('next_action')}")
                        yield {"event": "complete", "data": json.dumps({"next_action": data.get("next_action", "wait_for_student")}, ensure_ascii=False)}
                
                except json.JSONDecodeError:
                    # Skip invalid JSON lines
                    continue
        
        logger.info(f"[{trace_id}] === 步骤5: LLM流式处理完成, 共生成{event_count}个事件 ===")
        
        # Process any remaining content in buffer
        if buffer.strip():
            try:
                # Skip markdown code blocks
                clean_buffer = buffer.strip()
                if not clean_buffer.startswith("```"):
                    data = json.loads(clean_buffer)
                    event_type = data.get("type", "")
                    
                    if event_type == "complete":
                        event_count += 1
                        logger.info(f"[{trace_id}] 最终complete事件: next_action={data.get('next_action')}")
                        yield {"event": "complete", "data": json.dumps({"next_action": data.get("next_action", "wait_for_student")}, ensure_ascii=False)}
            except json.JSONDecodeError:
                pass
        
        logger.info(f"[{trace_id}] === 教学流式响应结束, 总计{event_count}个事件 ===")

    async def stream_chat_response(
        self,
        session: LearningSession,
        message: str,
        trace_id: str = "",
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream chat response for student message using JSONL format.

        Args:
            session: Learning session.
            message: Student message.
            trace_id: 链路追踪ID.

        Yields:
            SSE events with incremental response.
        """
        logger.info(f"[{trace_id}] === 处理学生消息 ===")
        logger.info(f"[{trace_id}] 学生消息: {message[:50]}...")
        logger.info(f"[{trace_id}] 当前对话历史: {len(session.messages)}条")
        
        # 快捷意图检测
        if "跳过" in message or "已经会了" in message or "开始测试" in message:
            yield {"event": "complete", "data": json.dumps({"next_action": "start_assessment"}, ensure_ascii=False)}
            return

        # Get knowledge point info
        if not session.kp_id:
            yield {"event": "error", "data": json.dumps({"error": "会话没有当前知识点"}, ensure_ascii=False)}
            return

        # 保存学生消息到对话历史
        session.add_message("student", message)
        
        kp_info = course_service.get_knowledge_point_info(session.kp_id)

        # Build prompt
        prompt = CHAT_RESPONSE_PROMPT.format(
            knowledge_point_name=kp_info["name"],
            knowledge_point_type=kp_info["type"],
            key_points=", ".join(knowledge_point_repository.get_by_id(kp_info["id"]).key_points) if knowledge_point_repository.get_by_id(kp_info["id"]) else "",
            dependencies=", ".join(kp_info["dependency_names"]) if kp_info["dependency_names"] else "无",
            student_message=message,
        )

        # 获取对话历史（最近10轮）
        conversation_history = session.get_conversation_history(max_turns=10)
        logger.info(f"[{trace_id}] 传递对话历史: {len(conversation_history)}条消息")
        
        # Stream LLM response and parse JSONL
        buffer = ""
        has_feedback = False
        ai_response_content = ""  # 收集AI完整回复
        
        for chunk in llm_service.stream_chat(SYSTEM_PROMPT, prompt, trace_id=trace_id):
            buffer += chunk
            ai_response_content += chunk
            
            # Try to parse complete JSON lines
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                
                if not line:
                    continue
                
                try:
                    # Skip markdown code blocks
                    if line.startswith("```"):
                        continue
                    
                    # 修复反斜杠转义问题
                    line_fixed = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', line)
                    
                    data = json.loads(line_fixed)
                    event_type = data.get("type", "")
                    
                    if event_type == "msg_feedback":
                        has_feedback = True
                        yield {"event": "msg_feedback", "data": json.dumps({"content": data.get("content", "")}, ensure_ascii=False)}
                    elif event_type == "msg_encourage":
                        yield {"event": "msg_encourage", "data": json.dumps({"content": data.get("content", "")}, ensure_ascii=False)}
                    elif event_type == "msg_supplement":
                        yield {"event": "msg_supplement", "data": json.dumps({"content": data.get("content", "")}, ensure_ascii=False)}
                    elif event_type == "wb_formulas":
                        yield {"event": "wb_formulas", "data": json.dumps({"content": data.get("content", "")}, ensure_ascii=False)}
                    elif event_type == "complete":
                        yield {"event": "complete", "data": json.dumps({"next_action": data.get("next_action", "wait_for_student")}, ensure_ascii=False)}
                
                except json.JSONDecodeError:
                    continue
        
        # Process any remaining content
        if buffer.strip():
            try:
                clean_buffer = buffer.strip()
                if not clean_buffer.startswith("```"):
                    data = json.loads(clean_buffer)
                    if data.get("type") == "complete":
                        yield {"event": "complete", "data": json.dumps({"next_action": data.get("next_action", "wait_for_student")}, ensure_ascii=False)}
            except json.JSONDecodeError:
                pass
        
        # 学生回答后，自动推进到下一阶段
        if has_feedback:
            # 获取教学模式配置
            from app.models.teaching_mode import TeachingModeType, TEACHING_MODE_CONFIGS
            
            total_phases = 4
            if session.teaching_mode:
                try:
                    mode_type = TeachingModeType(session.teaching_mode)
                    mode_config = TEACHING_MODE_CONFIGS.get(mode_type)
                    if mode_config:
                        total_phases = len(mode_config.phases)
                except ValueError:
                    pass
            
            # 推进阶段
            current_phase = session.current_phase or 1
            if current_phase < total_phases:
                # 还有下一阶段
                session.advance_phase()
                learning_session_repository.update(session)
                yield {"event": "phase_advance", "data": json.dumps({
                    "current_phase": session.current_phase,
                    "total_phases": total_phases,
                    "next_action": "next_phase"
                }, ensure_ascii=False)}
            else:
                # 已是最后阶段，进入评估
                yield {"event": "phase_advance", "data": json.dumps({
                    "current_phase": current_phase,
                    "total_phases": total_phases,
                    "next_action": "start_assessment"
                }, ensure_ascii=False)}
        
        # 保存AI回复到对话历史（提取主要内容）
        if has_feedback and ai_response_content:
            # 尝试从JSONL中提取msg_feedback内容
            try:
                for line in ai_response_content.split('\n'):
                    if line.strip() and not line.startswith('```'):
                        try:
                            data = json.loads(line)
                            if data.get("type") == "msg_feedback":
                                session.add_message("ai", data.get("content", ""))
                                break
                        except:
                            pass
            except:
                pass
            
            # 更新session（保存对话历史）
            learning_session_repository.update(session)
            logger.info(f"[{trace_id}] 对话历史已保存, 当前共{len(session.messages)}条消息")

    async def stream_unified_response(
        self,
        session: LearningSession,
        student_name: str,
        message: str = "",
        trace_id: str = "",
        start_new_round: bool = False,
        is_first_input: bool = False,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Unified streaming response method.
        
        Determines whether to use teaching mode or chat mode:
        - is_first_input=True: Teaching mode, student input is ignored (not saved)
        - is_first_input=False and has message: Chat mode, saves both student and AI messages
        - start_new_round=True: Start a new learning round with history summary

        Args:
            session: Learning session.
            student_name: Student name for personalization.
            message: Student message (optional for first round).
            trace_id: Trace ID for logging.
            start_new_round: Whether to start a new learning round.
            is_first_input: Whether this is the first input after welcome message.

        Yields:
            SSE events with teaching content or chat response.
        """
        from app.models.learning import RoundStatus
        
        # 如果需要开始新轮次
        if start_new_round:
            self.prepare_new_round(session, trace_id)
        
        # 判断当前模式：
        # is_first_input=True → 教学模式（首次输入只是确认开始）
        # 否则 → 检查当前轮次是否有消息，有则对话模式
        current_round_messages = session.current_round.messages if session.current_round else []
        is_teaching_mode = is_first_input or (len(current_round_messages) == 0 and not message)
        learning_round = session.learning_round
        
        # 获取历史总结（用于提示模型）
        history_summary_str = session.get_history_summary_str()
        
        logger.info(f"[{trace_id}] === 统一流式响应 ===")
        logger.info(f"[{trace_id}] is_teaching_mode={is_teaching_mode}, learning_round={learning_round}, current_round_messages={len(current_round_messages)}, message={'有' if message else '无'}")
        
        if is_teaching_mode:
            # 教学模式：第一轮或新学习轮次
            # 学生的输入只作为触发信号，不保存到对话历史
            logger.info(f"[{trace_id}] 进入教学模式（第{learning_round}轮学习）")
            
            ai_content_parts = []
            async for event in self.stream_teaching_content(
                session, 
                student_name, 
                trace_id,
                learning_round=learning_round,
                history_summary=history_summary_str,
            ):
                # 收集 AI 输出
                if event.get("event") in ["segment", "msg_intro", "msg_def", "msg_example", "msg_summary", "msg_question"]:
                    try:
                        data = json.loads(event.get("data", "{}"))
                        content = data.get("message") or data.get("content", "")
                        if content:
                            ai_content_parts.append(content)
                    except:
                        pass
                yield event
            
            # 保存 AI 输出到对话历史
            if ai_content_parts:
                ai_content = "\n".join(ai_content_parts)
                session.add_message("ai", ai_content)
                learning_session_repository.update(session)
                logger.info(f"[{trace_id}] 教学内容已保存到对话历史")
        else:
            # 对话模式：同一轮学习内的师生互动
            logger.info(f"[{trace_id}] 进入对话模式（第{learning_round}轮学习内的对话）")
            async for event in self.stream_chat_response(session, message, trace_id):
                yield event

    def generate_round_summary(
        self,
        round_data: "LearningRound",
        trace_id: str = "",
    ) -> "RoundSummary":
        """生成轮次总结
        
        Args:
            round_data: 学习轮次数据
            trace_id: 链路追踪ID
            
        Returns:
            轮次总结
        """
        from app.models.learning import RoundSummary, RoundStatus
        
        # 如果是评估完成的，使用评估结果
        if round_data.assessment_result:
            ar = round_data.assessment_result
            return RoundSummary(
                result="passed" if ar.passed else "failed",
                score=ar.score,
                main_issues=ar.error_types[:3] if ar.error_types else ["需要加强练习"],
                error_types=ar.error_types,
                mastery_level="掌握" if ar.passed and ar.score >= 80 else ("理解" if ar.passed else "入门"),
                key_insights=f"正确率{int(ar.correct_count/ar.total_count*100)}%",
                teaching_phases_completed=round_data.current_phase,
                total_phases=round_data.total_phases,
            )
        
        # 如果是中途退出的，基于对话内容生成
        messages_text = "\n".join([f"{m['role']}: {m['content'][:100]}" for m in round_data.messages[-10:]])
        
        # 简单估算（实际可以调用LLM生成更详细的总结）
        phases_done = round_data.current_phase
        total = round_data.total_phases
        progress = phases_done / total if total > 0 else 0
        
        return RoundSummary(
            result="abandoned",
            score=0.0,
            main_issues=["学习中途中断"],
            error_types=[],
            mastery_level="入门" if progress < 0.5 else "理解",
            key_insights=f"完成{phases_done}/{total}阶段",
            teaching_phases_completed=phases_done,
            total_phases=total,
        )

    def ensure_previous_round_summary(self, session: "LearningSession", trace_id: str = "") -> None:
        """确保上一轮有总结（懒加载）
        
        如果上一轮没有总结，则生成一个。
        """
        from app.models.learning import RoundStatus
        
        if len(session.rounds) < 2:
            return  # 没有上一轮
        
        previous_round = session.rounds[-2]  # 倒数第二轮
        if previous_round.summary is None and previous_round.status != RoundStatus.IN_PROGRESS:
            logger.info(f"[{trace_id}] 为第{previous_round.round_number}轮生成懒加载总结")
            previous_round.summary = self.generate_round_summary(previous_round, trace_id)
            learning_session_repository.update(session)

    def prepare_new_round(self, session: "LearningSession", trace_id: str = "") -> "LearningRound":
        """准备新一轮学习
        
        1. 确保上一轮有总结
        2. 开始新一轮
        
        Returns:
            新的学习轮次
        """
        # 先为上一轮生成总结（如果需要）
        self.ensure_previous_round_summary(session, trace_id)
        
        # 开始新一轮
        new_round = session.start_new_round()
        learning_session_repository.update(session)
        
        logger.info(f"[{trace_id}] 开始第{new_round.round_number}轮学习")
        return new_round


# Global service instance
learning_service = LearningService()
