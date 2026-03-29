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
        from app.repositories.course_repository import knowledge_point_repository

        kp_info = self.course_service.get_knowledge_point_info(input_data.knowledge_point_id)
        kp = knowledge_point_repository.get_by_id(input_data.knowledge_point_id)

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

    # 可扩展工具（已实现）

    def analyze_error_pattern(self, student_id: str, error_history: list[dict]) -> dict:
        """分析错误模式，识别学生的常见错误类型。"""
        if not error_history:
            return {
                "error_root_cause": "无错误历史",
                "suggested_kp_ids": [],
                "error_types": [],
            }

        # 统计错误类型
        error_types = {}
        for error in error_history:
            error_type = error.get("type", "unknown")
            error_types[error_type] = error_types.get(error_type, 0) + 1

        # 找出最常见的错误类型
        most_common_error = max(error_types.items(), key=lambda x: x[1])[0] if error_types else "unknown"

        # 根据错误类型推荐补救知识点
        error_to_kp_map = {
            "calculation": ["K1", "K2"],  # 计算错误 → 基础知识点
            "concept": ["K3", "K4"],      # 概念错误 → 概念知识点
            "application": ["K5", "K6"],  # 应用错误 → 应用知识点
        }

        suggested_kp_ids = error_to_kp_map.get(most_common_error, ["K1"])

        return {
            "error_root_cause": f"主要错误类型：{most_common_error}（出现 {error_types.get(most_common_error, 0)} 次）",
            "suggested_kp_ids": suggested_kp_ids,
            "error_types": error_types,
        }

    def query_knowledge_graph(self, kp_id: str, query_type: str) -> dict:
        """查询知识图谱，获取知识点的前置、后续、相关知识点。"""
        kp_info = self.course_service.get_knowledge_point_info(kp_id)

        if query_type == "prerequisites":
            # 获取前置知识点
            related_kp_ids = kp_info.get("dependency_names", [])
        elif query_type == "successors":
            # 获取后续知识点（通过反向查询）
            all_kps = self.course_service.get_course_knowledge_points("MATH_JUNIOR_01")
            related_kp_ids = [
                kp["id"] for kp in all_kps
                if kp_id in kp.get("dependencies", [])
            ]
        elif query_type == "related":
            # 获取相关知识点（同一类别）
            kp_type = kp_info.get("type", "")
            all_kps = self.course_service.get_course_knowledge_points("MATH_JUNIOR_01")
            related_kp_ids = [
                kp["id"] for kp in all_kps
                if kp["type"] == kp_type and kp["id"] != kp_id
            ]
        else:
            related_kp_ids = []

        return {
            "query_type": query_type,
            "target_kp_id": kp_id,
            "related_kp_ids": related_kp_ids,
            "dependencies": kp_info.get("dependencies", []),
        }

    def fetch_similar_questions(self, kp_id: str, difficulty: str, question_type: str = "选择题") -> dict:
        """获取相似题目，用于练习和巩固。"""
        from app.repositories.assessment_repository import assessment_question_repository

        # 获取该知识点的所有题目
        all_questions = assessment_question_repository.get_by_kp(kp_id)

        if not all_questions:
            return {
                "questions": [],
                "count": 0,
                "message": f"知识点 {kp_id} 暂无题目",
            }

        # 按难度和题型筛选
        filtered_questions = [
            q for q in all_questions
            if q.difficulty == difficulty and q.type == question_type
        ]

        # 如果筛选结果为空，返回所有题目
        if not filtered_questions:
            filtered_questions = all_questions[:3]

        return {
            "questions": [
                {
                    "id": q.id,
                    "content": q.content,
                    "type": q.type,
                    "difficulty": q.difficulty,
                    "options": q.options if hasattr(q, "options") else [],
                }
                for q in filtered_questions[:5]  # 最多返回 5 道题
            ],
            "count": len(filtered_questions),
            "total_available": len(all_questions),
        }

    def record_learning_progress(self, student_id: str, kp_id: str, mastery: float) -> dict:
        """记录学生的学习进度和掌握度。"""
        from app.repositories.learning_repository import student_profile_repository

        try:
            # 获取学生档案
            profile = student_profile_repository.get_by_student_and_course(
                int(student_id),
                "MATH_JUNIOR_01",
            )

            if not profile:
                return {
                    "success": False,
                    "message": f"学生 {student_id} 的档案不存在",
                }

            # 更新掌握度
            if mastery >= 0.8:
                # 标记为已掌握
                if kp_id not in profile.mastered_kp_ids:
                    profile.mastered_kp_ids.append(kp_id)
                if kp_id in profile.completed_kp_ids:
                    profile.completed_kp_ids.remove(kp_id)
            elif mastery >= 0.6:
                # 标记为已完成
                if kp_id not in profile.completed_kp_ids:
                    profile.completed_kp_ids.append(kp_id)
            else:
                # 标记为需要复习
                pass

            # 更新掌握率
            total_kps = len(profile.mastered_kp_ids) + len(profile.completed_kp_ids)
            profile.mastery_rate = len(profile.mastered_kp_ids) / total_kps if total_kps > 0 else 0.0

            # 保存更新
            student_profile_repository.update(profile)

            return {
                "success": True,
                "message": f"学生 {student_id} 的知识点 {kp_id} 掌握度已更新为 {mastery:.2%}",
                "mastery": mastery,
                "mastery_rate": profile.mastery_rate,
            }

        except Exception as e:
            logger.error(f"记录学习进度失败：{e}")
            return {
                "success": False,
                "message": f"记录失败：{str(e)}",
            }

