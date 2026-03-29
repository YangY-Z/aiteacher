"""专项提升 Agent 主类。"""

import json
import logging
from typing import Any, Optional, Callable
from datetime import datetime

from app.agents.tools.improvement_tools import ImprovementTools
from app.agents.prompts.improvement_agent_prompt import (
    IMPROVEMENT_AGENT_SYSTEM_PROMPT,
    IMPROVEMENT_AGENT_USER_PROMPT_TEMPLATE,
)
from app.models.improvement import ImprovementSession, ImprovementSessionStatus
from app.services.llm_service import LLMService
from app.services.improvement_service import ImprovementService
from app.services.course_service import CourseService

logger = logging.getLogger(__name__)


class ToolDefinition:
    """工具定义。"""

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: dict,
        handler: Callable,
    ):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.handler = handler

    def to_dict(self) -> dict:
        """转换为字典格式（用于 LLM）。"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


class ImprovementAgent:
    """专项提升 Agent - 自主决策学生诊断、方案生成、教学讲解、评估流程。"""

    def __init__(
        self,
        improvement_service: ImprovementService,
        course_service: CourseService,
        llm_service: LLMService,
    ):
        self.improvement_service = improvement_service
        self.course_service = course_service
        self.llm_service = llm_service
        self.tools = ImprovementTools(
            improvement_service=improvement_service,
            course_service=course_service,
            llm_service=llm_service,
        )
        self.tool_map = self._build_tool_map()
        self.tool_definitions = self._build_tool_definitions()

    def _build_tool_map(self) -> dict[str, Callable]:
        """构建工具名称到处理函数的映射。"""
        return {
            "diagnose_student": self._handle_diagnose_student,
            "clarify_student": self._handle_clarify_student,
            "generate_learning_plan": self._handle_generate_learning_plan,
            "teach_knowledge_point": self._handle_teach_knowledge_point,
            "evaluate_quiz": self._handle_evaluate_quiz,
        }

    def _build_tool_definitions(self) -> list[ToolDefinition]:
        """构建工具定义列表。"""
        return [
            ToolDefinition(
                name="diagnose_student",
                description="诊断学生薄弱知识点",
                input_schema={
                    "type": "object",
                    "properties": {
                        "score": {"type": "number", "description": "学生成绩"},
                        "total_score": {"type": "number", "description": "总分"},
                        "error_description": {"type": "string", "description": "错误描述"},
                        "available_time": {"type": "integer", "description": "可用时间（分钟）"},
                        "difficulty": {"type": "string", "description": "难度等级"},
                        "foundation": {"type": "string", "description": "基础水平"},
                    },
                    "required": ["score", "total_score", "available_time", "difficulty", "foundation"],
                },
                handler=self._handle_diagnose_student,
            ),
            ToolDefinition(
                name="clarify_student",
                description="澄清学生知识缺口，生成澄清问题",
                input_schema={
                    "type": "object",
                    "properties": {
                        "candidate_kp_ids": {"type": "array", "items": {"type": "string"}, "description": "候选知识点列表"},
                        "clarification_round": {"type": "integer", "description": "澄清轮数"},
                        "student_answer": {"type": "string", "description": "学生上一轮回答"},
                    },
                    "required": ["candidate_kp_ids", "clarification_round"],
                },
                handler=self._handle_clarify_student,
            ),
            ToolDefinition(
                name="generate_learning_plan",
                description="生成分步学习方案",
                input_schema={
                    "type": "object",
                    "properties": {
                        "target_kp_id": {"type": "string", "description": "目标知识点ID"},
                        "available_time": {"type": "integer", "description": "可用时间（分钟）"},
                        "difficulty": {"type": "string", "description": "难度等级"},
                        "foundation": {"type": "string", "description": "基础水平"},
                    },
                    "required": ["target_kp_id", "available_time", "difficulty", "foundation"],
                },
                handler=self._handle_generate_learning_plan,
            ),
            ToolDefinition(
                name="teach_knowledge_point",
                description="生成教学讲解内容",
                input_schema={
                    "type": "object",
                    "properties": {
                        "knowledge_point_id": {"type": "string", "description": "知识点ID"},
                        "goal": {"type": "string", "description": "学习目标"},
                        "attempt_count": {"type": "integer", "description": "尝试次数", "default": 1},
                    },
                    "required": ["knowledge_point_id", "goal"],
                },
                handler=self._handle_teach_knowledge_point,
            ),
            ToolDefinition(
                name="evaluate_quiz",
                description="评估小测答题结果",
                input_schema={
                    "type": "object",
                    "properties": {
                        "knowledge_point_id": {"type": "string", "description": "知识点ID"},
                        "answers": {"type": "array", "items": {"type": "object"}, "description": "学生答案"},
                    },
                    "required": ["knowledge_point_id", "answers"],
                },
                handler=self._handle_evaluate_quiz,
            ),
        ]

    def _handle_diagnose_student(self, input_data: dict) -> dict:
        """处理诊断工具调用。"""
        from app.agents.tools.improvement_tools import DiagnoseStudentInput

        result = self.tools.diagnose_student(DiagnoseStudentInput(**input_data))
        return result.model_dump()

    def _handle_clarify_student(self, input_data: dict) -> dict:
        """处理澄清工具调用。"""
        from app.agents.tools.improvement_tools import ClarifyStudentInput

        result = self.tools.clarify_student(ClarifyStudentInput(**input_data))
        return result.model_dump()

    def _handle_generate_learning_plan(self, input_data: dict) -> dict:
        """处理方案生成工具调用。"""
        from app.agents.tools.improvement_tools import GenerateLearningPlanInput

        result = self.tools.generate_learning_plan(GenerateLearningPlanInput(**input_data))
        return result.model_dump()

    def _handle_teach_knowledge_point(self, input_data: dict) -> dict:
        """处理教学工具调用。"""
        from app.agents.tools.improvement_tools import TeachKnowledgePointInput

        result = self.tools.teach_knowledge_point(TeachKnowledgePointInput(**input_data))
        return result.model_dump()

    def _handle_evaluate_quiz(self, input_data: dict) -> dict:
        """处理评估工具调用。"""
        from app.agents.tools.improvement_tools import EvaluateQuizInput

        result = self.tools.evaluate_quiz(EvaluateQuizInput(**input_data))
        return result.model_dump()

    def run(
        self,
        session_id: str,
        student_id: str,
        course_id: str,
        score: float,
        total_score: float,
        error_description: Optional[str] = None,
        available_time: int = 30,
        difficulty: str = "normal",
        foundation: str = "average",
        max_turns: int = 20,
    ) -> ImprovementSession:
        """运行 Agent 流程（tool_use 循环）。

        Args:
            session_id: 会话 ID
            student_id: 学生 ID
            course_id: 课程 ID
            score: 学生成绩
            total_score: 总分
            error_description: 错误描述
            available_time: 可用时间（分钟）
            difficulty: 难度等级
            foundation: 基础水平
            max_turns: 最大轮数

        Returns:
            更新后的会话对象
        """
        session = self.improvement_service.get_session(session_id)

        # 构建初始用户提示
        user_prompt = IMPROVEMENT_AGENT_USER_PROMPT_TEMPLATE.format(
            score=score,
            total_score=total_score,
            error_description=error_description or "未提供",
            available_time=available_time,
            difficulty=difficulty,
            foundation=foundation,
        )

        # 初始化消息历史
        messages = [
            {"role": "user", "content": user_prompt}
        ]

        try:
            # tool_use 循环
            for turn in range(max_turns):
                logger.info(f"Agent 循环 {turn + 1}/{max_turns}")

                # 调用 LLM，请求工具调用
                response = self.llm_service.chat_with_history(
                    system_prompt=IMPROVEMENT_AGENT_SYSTEM_PROMPT,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2000,
                )

                # 解析 LLM 响应
                try:
                    response_data = json.loads(response)
                except json.JSONDecodeError:
                    logger.warning(f"LLM 响应不是有效 JSON：{response[:200]}")
                    response_data = {"action": "end", "reason": "LLM 响应格式错误"}

                action = response_data.get("action", "end")

                # 如果 LLM 决定结束
                if action == "end":
                    reason = response_data.get("reason", "Agent 决定结束")
                    logger.info(f"Agent 结束：{reason}")
                    session.status = ImprovementSessionStatus.COMPLETED
                    session.updated_at = datetime.now()
                    self.improvement_service.improvement_repo.update_session(session)
                    break

                # 如果 LLM 请求调用工具
                if action == "call_tool":
                    tool_name = response_data.get("tool_name")
                    tool_input = response_data.get("tool_input", {})

                    if tool_name not in self.tool_map:
                        logger.warning(f"未知工具：{tool_name}")
                        messages.append({"role": "assistant", "content": response})
                        messages.append({
                            "role": "user",
                            "content": f"错误：工具 '{tool_name}' 不存在"
                        })
                        continue

                    # 执行工具
                    try:
                        tool_result = self.tool_map[tool_name](tool_input)
                        logger.info(f"工具执行成功：{tool_name}")

                        # 更新会话状态（根据工具类型）
                        self._update_session_from_tool(session, tool_name, tool_result)

                    except Exception as e:
                        logger.error(f"工具执行失败：{tool_name}, 错误：{e}")
                        tool_result = {"error": str(e)}

                    # 将工具结果反馈给 LLM
                    messages.append({"role": "assistant", "content": response})
                    messages.append({
                        "role": "user",
                        "content": f"工具 '{tool_name}' 执行结果：{json.dumps(tool_result, ensure_ascii=False)}"
                    })

                else:
                    # LLM 返回其他响应
                    logger.info(f"Agent 返回响应：{action}")
                    messages.append({"role": "assistant", "content": response})
                    break

            session.updated_at = datetime.now()
            self.improvement_service.improvement_repo.update_session(session)
            logger.info(f"Agent 流程完成：session_id={session_id}")

        except Exception as e:
            logger.error(f"Agent 流程失败：{e}", exc_info=True)
            session.status = ImprovementSessionStatus.FAILED
            session.updated_at = datetime.now()
            self.improvement_service.improvement_repo.update_session(session)
            raise

        return session

    def _update_session_from_tool(self, session: ImprovementSession, tool_name: str, tool_result: dict) -> None:
        """根据工具执行结果更新会话状态。"""
        from app.models.improvement import DiagnosisResult, ImprovementPlan, ImprovementPlanStep
        import uuid

        if tool_name == "diagnose_student":
            session.diagnosis = DiagnosisResult(
                target_knowledge_point_id=tool_result.get("target_kp_id"),
                confidence=tool_result.get("confidence", 0.5),
                reason=tool_result.get("reason", ""),
                prerequisite_gaps=tool_result.get("prerequisite_gaps", []),
            )
            session.status = ImprovementSessionStatus.DIAGNOSED

        elif tool_name == "generate_learning_plan":
            steps_data = tool_result.get("steps", [])
            session.plan = ImprovementPlan(
                plan_id=str(uuid.uuid4()),
                target_kp_id=tool_result.get("target_kp_id", session.diagnosis.target_knowledge_point_id if session.diagnosis else "K1"),
                steps=[
                    ImprovementPlanStep(
                        step_order=step.get("step_order"),
                        knowledge_point_id=step.get("knowledge_point_id"),
                        goal=step.get("goal"),
                        estimated_minutes=step.get("estimated_minutes", 10),
                    )
                    for step in steps_data
                ],
                total_estimated_minutes=tool_result.get("total_estimated_minutes", 30),
            )
            session.status = ImprovementSessionStatus.PLANNING

        elif tool_name == "evaluate_quiz":
            if tool_result.get("passed"):
                session.status = ImprovementSessionStatus.COMPLETED
            else:
                session.status = ImprovementSessionStatus.QUIZ

