"""专项提升服务层。"""

import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from app.models.improvement import (
    ClarificationRound,
    DiagnosisResult,
    ImprovementPlan,
    ImprovementPlanStep,
    ImprovementQuizResult,
    ImprovementSession,
    ImprovementSessionStatus,
    ScoreInput,
)
from app.prompts.improvement_prompt import (
    IMPROVEMENT_CLARIFICATION_PROMPT,
    IMPROVEMENT_DIAGNOSIS_PROMPT,
    IMPROVEMENT_PLAN_PROMPT,
)
from app.prompts.system_prompt import SYSTEM_PROMPT
from app.prompts.teaching_prompt import TEACHING_PROMPT, get_teaching_requirements
from app.repositories.assessment_repository import assessment_question_repository
from app.repositories.course_repository import knowledge_point_repository
from app.repositories.improvement_repository import ImprovementRepository, improvement_repository
from app.repositories.learning_repository import student_profile_repository
from app.services.course_service import CourseService, course_service
from app.services.llm_service import LLMService, llm_service

logger = logging.getLogger(__name__)


class ImprovementService:
    """专项提升业务逻辑服务。"""

    def __init__(
        self,
        improvement_repo: ImprovementRepository,
        course_service: CourseService,
        llm_service: LLMService,
    ) -> None:
        self.improvement_repo = improvement_repo
        self.course_service = course_service
        self.llm_service = llm_service

    def start_session(
        self,
        student_id: str,
        course_id: str,
        score_input: ScoreInput,
        max_clarification_rounds: int = 5,
    ) -> ImprovementSession:
        session = ImprovementSession(
            session_id=str(uuid.uuid4()),
            student_id=student_id,
            course_id=course_id,
            status=ImprovementSessionStatus.ANALYZING,
            max_clarification_rounds=max_clarification_rounds,
            score_input=score_input,
        )

        diagnosis, clarification = self._initial_diagnose(int(student_id), course_id, score_input)
        if diagnosis is not None:
            session.diagnosis = diagnosis
            session.status = ImprovementSessionStatus.DIAGNOSED
        elif clarification is not None:
            session.clarification_rounds.append(clarification)
            session.status = ImprovementSessionStatus.CLARIFYING

        self.improvement_repo.create_session(session)
        return session

    def get_session(self, session_id: str) -> ImprovementSession:
        session = self.improvement_repo.get_session(session_id)
        if not session:
            raise ValueError("专项提升会话不存在")
        return session

    def submit_clarification_answer(self, session_id: str, answer: str) -> ImprovementSession:
        session = self.get_session(session_id)
        if not session.clarification_rounds:
            raise ValueError("当前没有待回答的澄清问题")

        current_round = session.clarification_rounds[-1]
        current_round.student_answer = answer
        current_round.answered_at = datetime.now()
        session.updated_at = datetime.now()

        diagnosis, next_question = self._diagnose_from_answer(session, answer)
        if diagnosis is not None:
            session.diagnosis = diagnosis
            session.status = ImprovementSessionStatus.DIAGNOSED
        elif len(session.clarification_rounds) >= session.max_clarification_rounds:
            fallback_kp_id = current_round.candidate_kp_ids[0] if current_round.candidate_kp_ids else self._get_default_kp_id(session.course_id)
            session.diagnosis = DiagnosisResult(
                target_knowledge_point_id=fallback_kp_id,
                confidence=0.55,
                reason="基于已有成绩与澄清信息，先从最可能的薄弱知识点开始专项提升。",
                prerequisite_gaps=self.course_service.get_knowledge_point_dependencies(fallback_kp_id),
            )
            session.status = ImprovementSessionStatus.DIAGNOSED
        else:
            next_round = self._build_next_clarification(session, next_question)
            session.clarification_rounds.append(next_round)
            session.status = ImprovementSessionStatus.CLARIFYING

        self.improvement_repo.update_session(session)
        return session

    def generate_plan(self, session_id: str) -> ImprovementSession:
        session = self.get_session(session_id)
        if not session.diagnosis or not session.score_input:
            raise ValueError("尚未完成诊断，无法生成方案")

        llm_plan = self._generate_plan_with_llm(session)
        if llm_plan is not None:
            session.plan = llm_plan
        else:
            session.plan = self._generate_plan_by_rules(session)

        session.current_step_order = 1 if session.plan.steps else 0
        session.status = ImprovementSessionStatus.LEARNING
        session.updated_at = datetime.now()
        self.improvement_repo.update_session(session)
        return session

    def start_plan_step(self, session_id: str, step_order: int) -> dict[str, Any]:
        session = self.get_session(session_id)
        if not session.plan:
            raise ValueError("学习方案不存在")

        step = next((item for item in session.plan.steps if item.step_order == step_order), None)
        if not step:
            raise ValueError("学习步骤不存在")

        kp_info = self.course_service.get_knowledge_point_info(step.knowledge_point_id)
        kp = knowledge_point_repository.get_by_id(step.knowledge_point_id)
        prompt = TEACHING_PROMPT.format(
            knowledge_point_name=kp_info["name"],
            knowledge_point_id=kp_info["id"],
            knowledge_point_type=kp_info["type"],
            description=kp_info["description"] or step.goal,
            key_points=", ".join(kp.key_points) if kp and kp.key_points else (kp_info["description"] or step.goal),
            dependencies=", ".join(kp_info["dependency_names"]) if kp_info["dependency_names"] else "无",
            student_name="同学",
            attempt_count=1,
            attempt_info="",
            teaching_requirements=get_teaching_requirements(kp_info["type"], 1, ""),
        )

        try:
            teaching_content = self.llm_service.chat_json(SYSTEM_PROMPT, prompt)
        except Exception as exc:
            logger.warning(f"Improvement step teaching LLM failed: {exc}")
            teaching_content = {
                "response_type": "讲解",
                "content": {
                    "title": f"开始学习：{kp_info['name']}",
                    "introduction": kp_info.get("description") or step.goal,
                    "definition": step.goal,
                    "example": f"请结合 {kp_info['name']} 的典型题目进行练习。",
                    "question": "你能先用自己的话说说这个知识点的关键点吗？",
                    "summary": f"先掌握 {kp_info['name']} 的核心概念，再进入下一步。",
                },
                "whiteboard": {"formulas": [], "diagrams": []},
                "next_action": "wait_for_student",
            }

        session.current_step_order = step.step_order
        session.status = ImprovementSessionStatus.LEARNING
        session.updated_at = datetime.now()
        self.improvement_repo.update_session(session)

        return {
            "step_order": step.step_order,
            "goal": step.goal,
            "knowledge_point": kp_info,
            "content": teaching_content.get("content", {}),
            "whiteboard": teaching_content.get("whiteboard", {"formulas": [], "diagrams": []}),
            "response_type": teaching_content.get("response_type", "讲解"),
            "next_action": teaching_content.get("next_action", "wait_for_student"),
        }

    def complete_plan_step(self, session_id: str, step_order: int) -> ImprovementSession:
        session = self.get_session(session_id)
        if not session.plan:
            raise ValueError("学习方案不存在")

        step = next((item for item in session.plan.steps if item.step_order == step_order), None)
        if not step:
            raise ValueError("学习步骤不存在")

        step.is_completed = True
        step.completed_at = datetime.now()
        remaining = [item for item in session.plan.steps if not item.is_completed]
        if remaining:
            session.current_step_order = remaining[0].step_order
            session.status = ImprovementSessionStatus.LEARNING
        else:
            session.current_step_order = 0
            session.status = ImprovementSessionStatus.QUIZ
        session.updated_at = datetime.now()
        self.improvement_repo.update_session(session)
        return session

    def get_quiz(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        if not session.diagnosis:
            raise ValueError("尚未完成诊断")

        kp_id = session.diagnosis.target_knowledge_point_id
        questions = assessment_question_repository.get_by_kp(kp_id)[:4]
        if not questions:
            raise ValueError("当前知识点暂无题目")

        quiz_id = session.quiz_result.quiz_id if session.quiz_result else str(uuid.uuid4())
        session.quiz_result = ImprovementQuizResult(
            quiz_id=quiz_id,
            questions=[question.to_dict() for question in questions],
        )
        session.updated_at = datetime.now()
        self.improvement_repo.update_session(session)

        return {
            "quiz_id": quiz_id,
            "target_kp_id": kp_id,
            "questions": [
                {
                    "id": question.id,
                    "type": question.type.value,
                    "content": question.content,
                    "options": question.options,
                    "difficulty": question.difficulty.value,
                }
                for question in questions
            ],
        }

    def submit_quiz(self, session_id: str, answers: list[dict[str, Any]]) -> ImprovementQuizResult:
        session = self.get_session(session_id)
        if not session.quiz_result:
            raise ValueError("请先获取小测题目")

        correct_count = 0
        total_questions = len(answers)
        for answer in answers:
            question_id = answer.get("question_id")
            student_answer = answer.get("answer")
            question = assessment_question_repository.get_by_id(question_id)
            if question and question.check_answer(student_answer):
                correct_count += 1

        score = correct_count / total_questions if total_questions else 0.0
        passed = score >= 0.6
        session.quiz_result.answers = answers
        session.quiz_result.score = score
        session.quiz_result.passed = passed
        session.quiz_result.feedback = "已达到本次专项提升目标。" if passed else "建议复习当前目标知识点后再次测试。"
        session.quiz_result.submitted_at = datetime.now()
        session.status = ImprovementSessionStatus.COMPLETED
        session.completed_at = datetime.now()
        session.updated_at = datetime.now()
        self.improvement_repo.update_session(session)
        return session.quiz_result

    def _initial_diagnose(
        self,
        student_id: int,
        course_id: str,
        score_input: ScoreInput,
    ) -> tuple[Optional[DiagnosisResult], Optional[ClarificationRound]]:
        all_kps = self.course_service.get_course_knowledge_points(course_id)
        profile = student_profile_repository.get_by_student_and_course(student_id, course_id)
        weak_candidates = [kp.id for kp in all_kps if not profile or kp.id not in profile.mastered_kp_ids]
        weak_candidates = weak_candidates[:5] if weak_candidates else [all_kps[0].id]

        llm_result = self._call_diagnosis_llm(course_id, score_input, weak_candidates, profile.mastered_kp_ids if profile else [])
        if llm_result:
            need_clarification = bool(llm_result.get("need_clarification"))
            target_kp_id = llm_result.get("target_knowledge_point_id")
            if not need_clarification and target_kp_id in weak_candidates:
                return (
                    DiagnosisResult(
                        target_knowledge_point_id=target_kp_id,
                        confidence=float(llm_result.get("confidence", 0.75)),
                        reason=str(llm_result.get("reason", "已定位目标知识点。")),
                        prerequisite_gaps=llm_result.get("prerequisite_gaps", []),
                    ),
                    None,
                )
            question = str(llm_result.get("clarification_question", "你这次主要是在哪一类题目上丢分更多？"))
            return None, ClarificationRound(round_number=1, system_question=question, candidate_kp_ids=weak_candidates)

        score_ratio = score_input.score / score_input.total_score if score_input.total_score else 0
        if score_ratio <= 0.6 and score_input.error_description:
            target = weak_candidates[0]
            return (
                DiagnosisResult(
                    target_knowledge_point_id=target,
                    confidence=0.72,
                    reason="结合当前分数偏低、错题描述和历史掌握情况，先聚焦最可能的薄弱知识点。",
                    prerequisite_gaps=self.course_service.get_knowledge_point_dependencies(target),
                ),
                None,
            )

        return None, ClarificationRound(
            round_number=1,
            system_question="你这次主要是在哪一类题目上丢分更多？是概念理解、图象判断，还是解析式求解？",
            candidate_kp_ids=weak_candidates,
        )

    def _diagnose_from_answer(
        self,
        session: ImprovementSession,
        answer: str,
    ) -> tuple[Optional[DiagnosisResult], Optional[str]]:
        candidate_ids = session.clarification_rounds[-1].candidate_kp_ids
        if not candidate_ids:
            return None, None

        llm_result = self._call_clarification_llm(session, answer, candidate_ids)
        if llm_result:
            need_clarification = bool(llm_result.get("need_clarification"))
            target_kp_id = llm_result.get("target_knowledge_point_id")
            if not need_clarification and target_kp_id in candidate_ids:
                return (
                    DiagnosisResult(
                        target_knowledge_point_id=target_kp_id,
                        confidence=float(llm_result.get("confidence", 0.78)),
                        reason=str(llm_result.get("reason", "根据澄清回答定位到目标知识点。")),
                        prerequisite_gaps=llm_result.get("prerequisite_gaps", []),
                    ),
                    None,
                )
            return None, str(llm_result.get("clarification_question", "请再具体说说你最容易卡住的地方。"))

        lowered = answer.lower()
        target = candidate_ids[0]
        if "图" in answer or "象" in answer:
            target = next((kp_id for kp_id in candidate_ids if kp_id in {"K13", "K17", "K18", "K22", "K23", "K24", "K26"}), candidate_ids[0])
        elif "解析" in answer or "求式" in answer or "方程" in answer:
            target = next((kp_id for kp_id in candidate_ids if kp_id in {"K10", "K27", "K28", "K29", "K31", "K32"}), candidate_ids[0])
        elif "概念" in answer or "定义" in answer or "不会" in lowered:
            target = next((kp_id for kp_id in candidate_ids if kp_id in {"K6", "K12", "K15", "K20", "K21"}), candidate_ids[0])
        else:
            return None, None

        return (
            DiagnosisResult(
                target_knowledge_point_id=target,
                confidence=0.78,
                reason="根据你的澄清回答，问题集中在这一类题型对应的核心知识点上。",
                prerequisite_gaps=self.course_service.get_knowledge_point_dependencies(target),
            ),
            None,
        )

    def _generate_plan_with_llm(self, session: ImprovementSession) -> Optional[ImprovementPlan]:
        assert session.diagnosis is not None
        assert session.score_input is not None

        target_info = self.course_service.get_knowledge_point_info(session.diagnosis.target_knowledge_point_id)
        prompt = IMPROVEMENT_PLAN_PROMPT.format(
            target_kp_id=target_info["id"],
            target_kp_name=target_info["name"],
            target_kp_description=target_info["description"],
            prerequisite_names=", ".join(target_info["dependency_names"]) or "无",
            available_time=session.score_input.available_time,
            difficulty=session.score_input.difficulty.value,
            foundation=session.score_input.foundation.value,
            reason=session.diagnosis.reason,
        )

        try:
            result = self.llm_service.chat_json(prompt, "请输出学习方案 JSON")
            steps_data = result.get("steps", [])
            if not steps_data:
                return None
            steps: list[ImprovementPlanStep] = []
            for index, step_data in enumerate(steps_data, start=1):
                kp_id = str(step_data.get("knowledge_point_id") or session.diagnosis.target_knowledge_point_id)
                steps.append(
                    ImprovementPlanStep(
                        step_order=index,
                        knowledge_point_id=kp_id,
                        goal=str(step_data.get("goal", "完成本步学习任务")),
                        estimated_minutes=int(step_data.get("estimated_minutes", 10)),
                    )
                )
            return ImprovementPlan(
                plan_id=str(uuid.uuid4()),
                target_kp_id=session.diagnosis.target_knowledge_point_id,
                steps=steps,
                total_estimated_minutes=int(result.get("total_estimated_minutes", sum(step.estimated_minutes for step in steps))),
            )
        except Exception as exc:
            logger.warning(f"Improvement plan LLM failed: {exc}")
            return None

    def _generate_plan_by_rules(self, session: ImprovementSession) -> ImprovementPlan:
        assert session.diagnosis is not None
        assert session.score_input is not None

        target_kp_id = session.diagnosis.target_knowledge_point_id
        prerequisite_ids = session.diagnosis.prerequisite_gaps[:1]
        steps: list[ImprovementPlanStep] = []
        available_time = session.score_input.available_time

        step_index = 1
        if prerequisite_ids and available_time >= 40:
            prereq_id = prerequisite_ids[0]
            prereq_info = self.course_service.get_knowledge_point_info(prereq_id)
            steps.append(
                ImprovementPlanStep(
                    step_order=step_index,
                    knowledge_point_id=prereq_id,
                    goal=f"先补齐前置知识：{prereq_info['name']}",
                    estimated_minutes=min(15, max(10, available_time // 4)),
                )
            )
            step_index += 1

        target_info = self.course_service.get_knowledge_point_info(target_kp_id)
        explain_minutes = min(20, max(10, available_time // 3))
        practice_minutes = min(20, max(10, available_time // 3))
        quiz_minutes = min(15, max(8, available_time - explain_minutes - practice_minutes - sum(s.estimated_minutes for s in steps)))

        steps.append(ImprovementPlanStep(step_order=step_index, knowledge_point_id=target_kp_id, goal=f"理解核心概念与关键方法：{target_info['name']}", estimated_minutes=explain_minutes))
        step_index += 1
        steps.append(ImprovementPlanStep(step_order=step_index, knowledge_point_id=target_kp_id, goal=f"围绕 {target_info['name']} 做针对练习与纠错", estimated_minutes=practice_minutes))
        step_index += 1
        steps.append(ImprovementPlanStep(step_order=step_index, knowledge_point_id=target_kp_id, goal="完成本次专项提升小测并验证掌握程度", estimated_minutes=quiz_minutes))

        return ImprovementPlan(
            plan_id=str(uuid.uuid4()),
            target_kp_id=target_kp_id,
            steps=steps,
            total_estimated_minutes=sum(step.estimated_minutes for step in steps),
        )

    def _call_diagnosis_llm(
        self,
        course_id: str,
        score_input: ScoreInput,
        candidate_kps: list[str],
        mastered_kps: list[str],
    ) -> Optional[dict[str, Any]]:
        candidate_details = self._format_kp_details(candidate_kps)
        prompt = IMPROVEMENT_DIAGNOSIS_PROMPT.format(
            exam_name=score_input.exam_name,
            score=score_input.score,
            total_score=score_input.total_score,
            error_description=score_input.error_description or "无",
            available_time=score_input.available_time,
            difficulty=score_input.difficulty.value,
            foundation=score_input.foundation.value,
            mastered_kps=", ".join(mastered_kps) or "无",
            candidate_kps=", ".join(candidate_kps),
            candidate_details=candidate_details,
        )
        try:
            return self.llm_service.chat_json(prompt, "请输出诊断 JSON")
        except Exception as exc:
            logger.warning(f"Improvement diagnosis LLM failed: {exc}")
            return None

    def _call_clarification_llm(
        self,
        session: ImprovementSession,
        answer: str,
        candidate_kps: list[str],
    ) -> Optional[dict[str, Any]]:
        score_input = session.score_input
        if score_input is None:
            return None
        prompt = IMPROVEMENT_CLARIFICATION_PROMPT.format(
            exam_name=score_input.exam_name,
            score=score_input.score,
            total_score=score_input.total_score,
            error_description=score_input.error_description or "无",
            candidate_kps=", ".join(candidate_kps),
            current_question=session.clarification_rounds[-1].system_question,
            student_answer=answer,
            candidate_details=self._format_kp_details(candidate_kps),
        )
        try:
            return self.llm_service.chat_json(prompt, "请输出追问后诊断 JSON")
        except Exception as exc:
            logger.warning(f"Improvement clarification LLM failed: {exc}")
            return None

    def _build_next_clarification(self, session: ImprovementSession, llm_question: Optional[str]) -> ClarificationRound:
        candidate_ids = session.clarification_rounds[-1].candidate_kp_ids
        next_round_number = len(session.clarification_rounds) + 1
        questions = [
            "你更容易错在看不懂题意，还是知道题意但不会下笔？",
            "如果给你一条直线图象，你最不确定的是斜率、截距，还是象限位置？",
            "你做题时更容易卡在公式记忆，还是计算转换？",
        ]
        system_question = llm_question or questions[min(next_round_number - 2, len(questions) - 1)]
        return ClarificationRound(
            round_number=next_round_number,
            system_question=system_question,
            candidate_kp_ids=candidate_ids,
        )

    def _format_kp_details(self, kp_ids: list[str]) -> str:
        details = []
        for kp_id in kp_ids:
            info = self.course_service.get_knowledge_point_info(kp_id)
            details.append(
                f"- {info['id']} {info['name']}：{info['description']}；前置知识：{', '.join(info['dependency_names']) or '无'}"
            )
        return "\n".join(details)

    def _get_default_kp_id(self, course_id: str) -> str:
        return self.course_service.get_course_knowledge_points(course_id)[0].id


improvement_service = ImprovementService(
    improvement_repo=improvement_repository,
    course_service=course_service,
    llm_service=llm_service,
)
