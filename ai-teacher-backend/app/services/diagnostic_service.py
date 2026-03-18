"""Diagnostic service for pre-class assessment."""

import logging
from typing import Any, Optional

from app.core.exceptions import EntityNotFoundError, DiagnosticError
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
from app.models.course import KnowledgePoint, KnowledgePointType
from app.repositories.diagnostic_repository import (
    diagnostic_session_repository,
    diagnostic_question_repository,
    diagnostic_answer_repository,
)
from app.repositories.course_repository import (
    knowledge_point_repository,
    knowledge_point_dependency_repository,
)
from app.services.llm_service import llm_service
from app.prompts.diagnostic_prompt import (
    get_diagnostic_question_prompt,
    get_diagnostic_result_prompt,
    TEACHING_MODE_RECOMMENDATIONS,
    CONCLUSION_DESCRIPTIONS,
)
from app.prompts.system_prompt import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class DiagnosticService:
    """Service for pre-class diagnostic assessment.

    Handles the complete diagnostic workflow:
    1. Create diagnostic session with questions
    2. Process student answers
    3. Complete diagnosis and generate results
    """

    def create_diagnostic_session(
        self,
        student_id: int,
        course_id: str,
        target_kp_id: str,
    ) -> DiagnosticSession:
        """Create a new diagnostic session with generated questions.

        Args:
            student_id: Student ID.
            course_id: Course ID.
            target_kp_id: Target knowledge point ID to diagnose.

        Returns:
            Created diagnostic session with questions.

        Raises:
            EntityNotFoundError: If target knowledge point not found.
            DiagnosticError: If question generation fails.
        """
        # Check if target knowledge point exists
        target_kp = knowledge_point_repository.get_by_id(target_kp_id)
        if not target_kp:
            raise EntityNotFoundError("知识点", target_kp_id)

        # Check for existing active session
        existing = diagnostic_session_repository.get_active_by_student(student_id, course_id)
        if existing:
            return existing

        # Create new session
        session = DiagnosticSession(
            id="",
            student_id=student_id,
            course_id=course_id,
            target_kp_id=target_kp_id,
            status=DiagnosticStatus.PENDING,
        )
        session = diagnostic_session_repository.create(session)

        try:
            # Generate diagnostic questions
            questions = self._generate_diagnostic_questions(session.id, target_kp)
            session.questions = questions

            # Update session
            diagnostic_session_repository.update(session)

            return session
        except Exception as e:
            # Clean up session on failure
            diagnostic_session_repository.delete(session.id)
            raise DiagnosticError(f"诊断题生成失败: {e}", {"error": str(e)})

    def _generate_diagnostic_questions(
        self,
        session_id: str,
        target_kp: KnowledgePoint,
    ) -> list[DiagnosticQuestion]:
        """Generate diagnostic questions for a target knowledge point.

        Generates:
        - 1-2 questions for each prerequisite knowledge point
        - 2-3 questions for target knowledge point (basic level)

        Args:
            session_id: Diagnostic session ID.
            target_kp: Target knowledge point.

        Returns:
            List of diagnostic questions.
        """
        questions = []
        order = 0

        # Get prerequisite knowledge points
        prereq_ids = knowledge_point_dependency_repository.get_dependencies(target_kp.id)

        # Generate prerequisite questions
        for prereq_id in prereq_ids:
            prereq_kp = knowledge_point_repository.get_by_id(prereq_id)
            if prereq_kp:
                prereq_questions = self._generate_questions_for_kp(
                    session_id=session_id,
                    kp=prereq_kp,
                    category=QuestionCategory.PREREQUISITE,
                    count=1,  # 1 question per prerequisite
                    start_order=order,
                )
                questions.extend(prereq_questions)
                order += len(prereq_questions)

        # Generate target knowledge questions (basic level)
        target_questions = self._generate_questions_for_kp(
            session_id=session_id,
            kp=target_kp,
            category=QuestionCategory.TARGET,
            count=min(3, 5 - len(questions)),  # Max 5 total questions
            start_order=order,
        )
        questions.extend(target_questions)

        return questions

    def _generate_questions_for_kp(
        self,
        session_id: str,
        kp: KnowledgePoint,
        category: QuestionCategory,
        count: int,
        start_order: int,
    ) -> list[DiagnosticQuestion]:
        """Generate diagnostic questions for a specific knowledge point.

        Uses LLM to generate appropriate questions based on KP type.

        Args:
            session_id: Diagnostic session ID.
            kp: Knowledge point.
            category: Question category (prerequisite/target).
            count: Number of questions to generate.
            start_order: Starting order number.

        Returns:
            List of generated diagnostic questions.
        """
        prompt = get_diagnostic_question_prompt(
            kp_id=kp.id,
            kp_name=kp.name,
            kp_type=kp.type.value,
            description=kp.description or "",
            question_count=count,
            category=category.value,
        )

        try:
            response = llm_service.chat_json(SYSTEM_PROMPT, prompt)
            raw_questions = response.get("questions", [])

            questions = []
            for i, q_data in enumerate(raw_questions[:count]):
                question = self._parse_llm_question(
                    session_id=session_id,
                    kp_id=kp.id,
                    category=category,
                    q_data=q_data,
                    order=start_order + i,
                )
                if question:
                    questions.append(question)

            # If LLM failed to generate enough questions, create fallback
            if len(questions) < count:
                fallback = self._create_fallback_questions(
                    session_id=session_id,
                    kp=kp,
                    category=category,
                    count=count - len(questions),
                    start_order=start_order + len(questions),
                )
                questions.extend(fallback)

            return questions
        except Exception as e:
            logger.warning(f"LLM question generation failed: {e}, using fallback")
            return self._create_fallback_questions(
                session_id=session_id,
                kp=kp,
                category=category,
                count=count,
                start_order=start_order,
            )

    def _parse_llm_question(
        self,
        session_id: str,
        kp_id: str,
        category: QuestionCategory,
        q_data: dict[str, Any],
        order: int,
    ) -> Optional[DiagnosticQuestion]:
        """Parse a question from LLM response.

        Args:
            session_id: Diagnostic session ID.
            kp_id: Knowledge point ID.
            category: Question category.
            q_data: Question data from LLM.
            order: Question order.

        Returns:
            DiagnosticQuestion if valid, None otherwise.
        """
        try:
            question_type_str = q_data.get("question_type", "choice")
            question_type = DiagnosticQuestionType(question_type_str)

            return DiagnosticQuestion(
                id="",
                session_id=session_id,
                kp_id=kp_id,
                category=category,
                question_type=question_type,
                content=q_data.get("content", ""),
                correct_answer=q_data.get("correct_answer"),
                options=q_data.get("options"),
                coordinate_range=q_data.get("coordinate_range"),
                explanation=q_data.get("explanation"),
                order=order,
            )
        except (ValueError, KeyError) as e:
            logger.warning(f"Failed to parse LLM question: {e}")
            return None

    def _create_fallback_questions(
        self,
        session_id: str,
        kp: KnowledgePoint,
        category: QuestionCategory,
        count: int,
        start_order: int,
    ) -> list[DiagnosticQuestion]:
        """Create fallback questions when LLM generation fails.

        Creates simple choice questions based on knowledge point info.

        Args:
            session_id: Diagnostic session ID.
            kp: Knowledge point.
            category: Question category.
            count: Number of questions to create.
            start_order: Starting order number.

        Returns:
            List of fallback diagnostic questions.
        """
        questions = []

        # Create simple understanding questions based on KP type
        if kp.type == KnowledgePointType.CONCEPT:
            content = f"以下哪个是对「{kp.name}」的正确描述？"
            options = [
                kp.description or f"{kp.name}的基本概念",
                f"与{kp.name}无关的概念A",
                f"与{kp.name}无关的概念B",
                f"与{kp.name}无关的概念C",
            ]
            correct = "A"
        elif kp.type == KnowledgePointType.FORMULA:
            content = f"关于「{kp.name}」，以下说法正确的是："
            options = [
                f"该公式可以解决相关问题",
                "该公式没有任何应用场景",
                "该公式总是错误的",
                "该公式只适用于特殊情况",
            ]
            correct = "A"
        else:  # SKILL
            content = f"关于「{kp.name}」技能，以下说法正确的是："
            options = [
                "需要按照步骤操作",
                "可以随意操作",
                "不需要练习",
                "一次性就能掌握",
            ]
            correct = "A"

        for i in range(count):
            question = DiagnosticQuestion(
                id="",
                session_id=session_id,
                kp_id=kp.id,
                category=category,
                question_type=DiagnosticQuestionType.CHOICE,
                content=content,
                correct_answer=correct,
                options=options,
                explanation=f"这是关于{kp.name}的基础检测题。",
                order=start_order + i,
            )
            questions.append(question)

        return questions

    def process_answer(
        self,
        session_id: str,
        question_id: str,
        student_answer: Any,
        response_time: Optional[int] = None,
    ) -> dict[str, Any]:
        """Process a student's answer to a diagnostic question.

        Args:
            session_id: Diagnostic session ID.
            question_id: Question ID.
            student_answer: Student's answer.
            response_time: Time taken to answer in seconds.

        Returns:
            Dict with answer result and next question info.

        Raises:
            EntityNotFoundError: If session or question not found.
            DiagnosticError: If session is not in progress.
        """
        # Get session
        session = diagnostic_session_repository.get_by_id(session_id)
        if not session:
            raise EntityNotFoundError("诊断会话", session_id)

        # Start session if pending
        if session.status == DiagnosticStatus.PENDING:
            session.start()
            diagnostic_session_repository.update(session)

        # Check session status
        if session.status == DiagnosticStatus.COMPLETED:
            raise DiagnosticError("诊断会话已完成", {"session_id": session_id})

        # Get question
        question = next((q for q in session.questions if q.id == question_id), None)
        if not question:
            raise EntityNotFoundError("诊断题目", question_id)

        # Check if already answered
        existing_answer = diagnostic_answer_repository.get_by_question(question_id)
        if existing_answer:
            raise DiagnosticError("该题目已作答", {"question_id": question_id})

        # Check answer
        is_correct = question.check_answer(student_answer)

        # Save answer
        answer = DiagnosticAnswer(
            id=0,
            session_id=session_id,
            question_id=question_id,
            student_answer=student_answer,
            is_correct=is_correct,
            response_time=response_time,
        )
        diagnostic_answer_repository.create(answer)
        session.answers.append(answer)

        # Get next question
        next_question = session.get_current_question()

        # Check if session is complete
        session_completed = next_question is None

        return {
            "is_correct": is_correct,
            "explanation": question.explanation,
            "progress": session.get_progress(),
            "next_question": next_question,
            "session_completed": session_completed,
        }

    def complete_diagnosis(self, session_id: str) -> DiagnosticResult:
        """Complete the diagnostic session and generate results.

        Args:
            session_id: Diagnostic session ID.

        Returns:
            DiagnosticResult with analysis and recommendations.

        Raises:
            EntityNotFoundError: If session not found.
            DiagnosticError: If session has no answers.
        """
        # Get session
        session = diagnostic_session_repository.get_by_id(session_id)
        if not session:
            raise EntityNotFoundError("诊断会话", session_id)

        # Check if session has answers
        if not session.answers:
            raise DiagnosticError("诊断会话没有答题记录", {"session_id": session_id})

        # Get target knowledge point
        target_kp = knowledge_point_repository.get_by_id(session.target_kp_id)
        if not target_kp:
            raise EntityNotFoundError("知识点", session.target_kp_id)

        # Calculate prerequisite results
        prerequisite_results = self._calculate_prerequisite_results(session)

        # Calculate target question results
        target_questions = [q for q in session.questions if q.category == QuestionCategory.TARGET]
        target_answers = [
            a for a in session.answers
            if any(q.id == a.question_id for q in target_questions)
        ]
        target_correct = sum(1 for a in target_answers if a.is_correct)

        # Calculate total results
        total_correct = sum(1 for a in session.answers if a.is_correct)

        # Create result
        result = DiagnosticResult(
            session_id=session_id,
            target_kp_id=session.target_kp_id,
            target_kp_name=target_kp.name,
            conclusion=DiagnosticConclusion.NEED_REVIEW,  # Will be calculated
            prerequisite_results=prerequisite_results,
            target_questions_total=len(target_questions),
            target_questions_correct=target_correct,
            total_questions=len(session.questions),
            total_correct=total_correct,
            correct_rate=total_correct / len(session.questions) if session.questions else 0,
        )

        # Calculate conclusion
        result.calculate_conclusion()

        # Set recommended teaching mode
        result.recommended_teaching_mode = TEACHING_MODE_RECOMMENDATIONS.get(
            result.conclusion.value, "direct_teaching"
        )

        # Generate summary
        result.summary = self._generate_result_summary(session, result, target_kp)

        # Update session
        session.result = result
        session.complete()
        diagnostic_session_repository.update(session)

        return result

    def _calculate_prerequisite_results(
        self,
        session: DiagnosticSession,
    ) -> list[PrerequisiteCheckResult]:
        """Calculate prerequisite knowledge check results.

        Args:
            session: Diagnostic session.

        Returns:
            List of prerequisite check results.
        """
        results = []

        # Group questions and answers by KP
        prereq_questions = [
            q for q in session.questions
            if q.category == QuestionCategory.PREREQUISITE
        ]

        # Group by kp_id
        kp_questions: dict[str, list[DiagnosticQuestion]] = {}
        for q in prereq_questions:
            if q.kp_id not in kp_questions:
                kp_questions[q.kp_id] = []
            kp_questions[q.kp_id].append(q)

        # Calculate results for each KP
        for kp_id, questions in kp_questions.items():
            kp = knowledge_point_repository.get_by_id(kp_id)
            if not kp:
                continue

            kp_answers = [
                a for a in session.answers
                if a.question_id in [q.id for q in questions]
            ]
            correct = sum(1 for a in kp_answers if a.is_correct)

            # Determine mastery (at least 50% correct)
            is_mastered = correct >= len(questions) / 2

            # Calculate confidence based on correct rate
            confidence = correct / len(questions) if questions else 0

            results.append(PrerequisiteCheckResult(
                kp_id=kp_id,
                kp_name=kp.name,
                is_mastered=is_mastered,
                questions_total=len(questions),
                questions_correct=correct,
                confidence=confidence,
            ))

        return results

    def _generate_result_summary(
        self,
        session: DiagnosticSession,
        result: DiagnosticResult,
        target_kp: KnowledgePoint,
    ) -> str:
        """Generate a summary of the diagnostic result.

        Args:
            session: Diagnostic session.
            result: Diagnostic result.
            target_kp: Target knowledge point.

        Returns:
            Summary string.
        """
        try:
            prompt = get_diagnostic_result_prompt(
                target_kp_name=target_kp.name,
                target_kp_type=target_kp.type.value,
                prerequisite_results=[r.to_dict() for r in result.prerequisite_results],
                target_total=result.target_questions_total,
                target_correct=result.target_questions_correct,
                total_questions=result.total_questions,
                total_correct=result.total_correct,
            )

            response = llm_service.chat_json(SYSTEM_PROMPT, prompt)
            return response.get("summary", CONCLUSION_DESCRIPTIONS.get(result.conclusion.value, ""))
        except Exception as e:
            logger.warning(f"LLM summary generation failed: {e}")
            return CONCLUSION_DESCRIPTIONS.get(result.conclusion.value, "")

    def get_session(self, session_id: str) -> DiagnosticSession:
        """Get a diagnostic session by ID.

        Args:
            session_id: Session ID.

        Returns:
            Diagnostic session.

        Raises:
            EntityNotFoundError: If session not found.
        """
        session = diagnostic_session_repository.get_by_id(session_id)
        if not session:
            raise EntityNotFoundError("诊断会话", session_id)
        return session

    def get_current_question(self, session_id: str) -> Optional[DiagnosticQuestion]:
        """Get the current question for a session.

        Args:
            session_id: Session ID.

        Returns:
            Current question or None if all answered.
        """
        session = self.get_session(session_id)
        return session.get_current_question()

    def get_progress(self, session_id: str) -> dict[str, int]:
        """Get the progress of a diagnostic session.

        Args:
            session_id: Session ID.

        Returns:
            Dict with progress info.
        """
        session = self.get_session(session_id)
        return session.get_progress()

    def get_result(self, session_id: str) -> DiagnosticResult:
        """Get the result of a completed diagnostic session.

        Args:
            session_id: Session ID.

        Returns:
            Diagnostic result.

        Raises:
            EntityNotFoundError: If session not found.
            DiagnosticError: If session is not completed.
        """
        session = self.get_session(session_id)

        if session.status != DiagnosticStatus.COMPLETED:
            raise DiagnosticError(
                "诊断会话尚未完成",
                {"session_id": session_id, "status": session.status.value}
            )

        if not session.result:
            raise DiagnosticError(
                "诊断会话没有结果",
                {"session_id": session_id}
            )

        return session.result


# Global service instance
diagnostic_service = DiagnosticService()
