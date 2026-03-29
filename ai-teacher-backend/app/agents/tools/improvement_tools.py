"""专项提升 Agent 工具定义。"""

import json
import logging
from typing import Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DiagnoseStudentInput(BaseModel):
    """诊断学生输入。"""
    score: float = Field(..., description="学生成绩")
    total_score: float = Field(..., description="总分")
    error_description: Optional[str] = Field(None, description="错误描述")
    available_time: int = Field(..., description="可用时间（分钟）")
    difficulty: str = Field(..., description="难度等级")
    foundation: str = Field(..., description="基础水平")


class DiagnoseStudentOutput(BaseModel):
    """诊断输出。"""
    target_kp_id: str
    confidence: float
    reason: str
    prerequisite_gaps: list[str]


class ClarifyStudentInput(BaseModel):
    """澄清学生输入。"""
    candidate_kp_ids: list[str] = Field(..., description="候选知识点列表")
    clarification_round: int = Field(..., description="澄清轮数")
    student_answer: Optional[str] = Field(None, description="学生上一轮回答")


class ClarifyStudentOutput(BaseModel):
    """澄清输出。"""
    question: Optional[str] = Field(None, description="下一个澄清问题")
    target_kp_id: Optional[str] = Field(None, description="诊断结果知识点ID")
    confidence: Optional[float] = Field(None, description="诊断置信度")
    reason: Optional[str] = Field(None, description="诊断原因")


class GenerateLearningPlanInput(BaseModel):
    """生成学习方案输入。"""
    target_kp_id: str = Field(..., description="目标知识点ID")
    available_time: int = Field(..., description="可用时间（分钟）")
    difficulty: str = Field(..., description="难度等级")
    foundation: str = Field(..., description="基础水平")


class PlanStep(BaseModel):
    """学习方案步骤。"""
    step_order: int
    knowledge_point_id: str
    goal: str
    estimated_minutes: int


class GenerateLearningPlanOutput(BaseModel):
    """生成学习方案输出。"""
    steps: list[PlanStep]
    total_estimated_minutes: int


class TeachKnowledgePointInput(BaseModel):
    """教学输入。"""
    knowledge_point_id: str = Field(..., description="知识点ID")
    goal: str = Field(..., description="学习目标")
    attempt_count: int = Field(default=1, description="尝试次数")


class TeachKnowledgePointOutput(BaseModel):
    """教学输出。"""
    response_type: str
    content: dict[str, Any]
    whiteboard: dict[str, Any]
    next_action: str


class EvaluateQuizInput(BaseModel):
    """评估小测输入。"""
    knowledge_point_id: str = Field(..., description="知识点ID")
    answers: list[dict[str, Any]] = Field(..., description="学生答案")


class EvaluateQuizOutput(BaseModel):
    """评估小测输出。"""
    score: float
    passed: bool
    feedback: str


class ImprovementTools:
    """专项提升工具集。"""

    def __init__(self, improvement_service, course_service, llm_service):
        self.improvement_service = improvement_service
        self.course_service = course_service
        self.llm_service = llm_service

    def diagnose_student(self, input_data: DiagnoseStudentInput) -> DiagnoseStudentOutput:
        """诊断学生薄弱知识点。"""
        from app.models.improvement import ScoreInput, DifficultyLevel, FoundationLevel

        score_input = ScoreInput(
            exam_name="诊断考试",
            score=input_data.score,
            total_score=input_data.total_score,
            error_description=input_data.error_description,
            available_time=input_data.available_time,
            difficulty=DifficultyLevel(input_data.difficulty),
            foundation=FoundationLevel(input_data.foundation),
        )

        diagnosis, _ = self.improvement_service._initial_diagnose(
            student_id=0,  # 临时学生ID
            course_id="MATH_JUNIOR_01",
            score_input=score_input,
        )

        if diagnosis:
            return DiagnoseStudentOutput(
                target_kp_id=diagnosis.target_knowledge_point_id,
                confidence=diagnosis.confidence,
                reason=diagnosis.reason,
                prerequisite_gaps=diagnosis.prerequisite_gaps or [],
            )

        # 诊断失败，返回默认值
        return DiagnoseStudentOutput(
            target_kp_id="K1",
            confidence=0.5,
            reason="诊断失败，使用默认知识点",
            prerequisite_gaps=[],
        )

    def clarify_student(self, input_data: ClarifyStudentInput) -> ClarifyStudentOutput:
        """澄清学生知识缺口。"""
        # 调用 LLM 生成澄清问题
        try:
            question = self.improvement_service._call_clarification_llm(
                candidate_kp_ids=input_data.candidate_kp_ids,
                student_answer=input_data.student_answer,
            )
            return ClarifyStudentOutput(question=question)
        except Exception as e:
            logger.warning(f"Clarification LLM failed: {e}")
            # 返回默认澄清问题
            return ClarifyStudentOutput(
                question="你能具体描述一下遇到的困难吗？"
            )

    def generate_learning_plan(self, input_data: GenerateLearningPlanInput) -> GenerateLearningPlanOutput:
        """生成学习方案。"""
        from app.models.improvement import ImprovementSession, ScoreInput, DifficultyLevel, FoundationLevel, DiagnosisResult

        # 构造临时会话
        session = ImprovementSession(
            session_id="temp",
            student_id="0",
            course_id="MATH_JUNIOR_01",
            status="DIAGNOSED",
            max_clarification_rounds=5,
            score_input=ScoreInput(
                exam_name="诊断考试",
                score=60.0,
                total_score=100.0,
                available_time=input_data.available_time,
                difficulty=DifficultyLevel(input_data.difficulty),
                foundation=FoundationLevel(input_data.foundation),
            ),
        )
        session.diagnosis = DiagnosisResult(
            target_knowledge_point_id=input_data.target_kp_id,
            confidence=0.8,
            reason="Agent 诊断",
        )

        plan = self.improvement_service._generate_plan_with_llm(session)
        if not plan:
            plan = self.improvement_service._generate_plan_by_rules(session)

        return GenerateLearningPlanOutput(
            steps=[
                PlanStep(
                    step_order=step.step_order,
                    knowledge_point_id=step.knowledge_point_id,
                    goal=step.goal,
                    estimated_minutes=step.estimated_minutes,
                )
                for step in plan.steps
            ],
            total_estimated_minutes=plan.total_estimated_minutes,
        )

    def teach_knowledge_point(self, input_data: TeachKnowledgePointInput) -> TeachKnowledgePointOutput:
        """生成教学内容。"""
        from app.prompts.teaching_prompt import TEACHING_PROMPT, get_teaching_requirements
        from app.prompts.system_prompt import SYSTEM_PROMPT

        kp_info = self.course_service.get_knowledge_point_info(input_data.knowledge_point_id)
        kp = self.course_service.knowledge_point_repository.get_by_id(input_data.knowledge_point_id)

        prompt = TEACHING_PROMPT.format(
            knowledge_point_name=kp_info["name"],
            knowledge_point_id=kp_info["id"],
            knowledge_point_type=kp_info["type"],
            description=kp_info["description"] or input_data.goal,
            key_points=", ".join(kp.key_points) if kp and kp.key_points else kp_info["description"],
            dependencies=", ".join(kp_info["dependency_names"]) if kp_info["dependency_names"] else "无",
            student_name="同学",
            attempt_count=input_data.attempt_count,
            attempt_info="",
            teaching_requirements=get_teaching_requirements(kp_info["type"], input_data.attempt_count, ""),
        )

        try:
            content = self.llm_service.chat_json(SYSTEM_PROMPT, prompt)
        except Exception as e:
            logger.warning(f"Teaching LLM failed: {e}")
            content = {
                "response_type": "讲解",
                "content": {
                    "title": f"开始学习：{kp_info['name']}",
                    "introduction": kp_info.get("description") or input_data.goal,
                },
                "whiteboard": {"formulas": [], "diagrams": []},
                "next_action": "wait_for_student",
            }

        return TeachKnowledgePointOutput(
            response_type=content.get("response_type", "讲解"),
            content=content.get("content", {}),
            whiteboard=content.get("whiteboard", {"formulas": [], "diagrams": []}),
            next_action=content.get("next_action", "wait_for_student"),
        )

    def evaluate_quiz(self, input_data: EvaluateQuizInput) -> EvaluateQuizOutput:
        """评估小测答题。"""
        from app.repositories.assessment_repository import assessment_question_repository

        correct_count = 0
        total_questions = len(input_data.answers)

        for answer in input_data.answers:
            question_id = answer.get("question_id")
            student_answer = answer.get("answer")
            question = assessment_question_repository.get_by_id(question_id)
            if question and question.check_answer(student_answer):
                correct_count += 1

        score = correct_count / total_questions if total_questions else 0.0
        passed = score >= 0.6

        return EvaluateQuizOutput(
            score=score,
            passed=passed,
            feedback="已达到本次专项提升目标。" if passed else "建议复习当前目标知识点后再次测试。",
        )

    # 可扩展工具（暂不实现）

    def analyze_error_pattern(self, student_id: str, error_history: list[dict]) -> dict:
        """分析错误模式。TODO: 实现"""
        return {
            "error_root_cause": "待实现",
            "suggested_kp_ids": [],
        }

    def query_knowledge_graph(self, kp_id: str, query_type: str) -> dict:
        """查询知识图谱。TODO: 实现"""
        return {
            "related_kp_ids": [],
            "dependencies": [],
        }

    def fetch_similar_questions(self, kp_id: str, difficulty: str, question_type: str) -> dict:
        """获取相似题目。TODO: 实现"""
        return {
            "questions": [],
        }

    def record_learning_progress(self, student_id: str, kp_id: str, mastery: float) -> dict:
        """记录学习进度。TODO: 实现"""
        return {
            "success": True,
            "message": "进度记录待实现",
        }
