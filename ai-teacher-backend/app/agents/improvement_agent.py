"""专项提升 Agent 主类。"""

import json
import logging
from typing import Any, Optional
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
    ) -> ImprovementSession:
        """运行 Agent 流程。

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

        Returns:
            更新后的会话对象
        """
        session = self.improvement_service.get_session(session_id)

        # 构建 Agent 提示
        user_prompt = IMPROVEMENT_AGENT_USER_PROMPT_TEMPLATE.format(
            score=score,
            total_score=total_score,
            error_description=error_description or "未提供",
            available_time=available_time,
            difficulty=difficulty,
            foundation=foundation,
        )

        # 调用 LLM 进行 Agent 推理
        messages = [
            {"role": "user", "content": user_prompt}
        ]

        # 简化版本：直接执行工具调用序列
        # 完整版本应该使用 tool_use 让 LLM 自主选择工具
        try:
            # 1. 诊断
            from app.agents.tools.improvement_tools import DiagnoseStudentInput
            diagnosis_result = self.tools.diagnose_student(
                DiagnoseStudentInput(
                    score=score,
                    total_score=total_score,
                    error_description=error_description,
                    available_time=available_time,
                    difficulty=difficulty,
                    foundation=foundation,
                )
            )

            # 更新会话诊断结果
            from app.models.improvement import DiagnosisResult
            session.diagnosis = DiagnosisResult(
                target_knowledge_point_id=diagnosis_result.target_kp_id,
                confidence=diagnosis_result.confidence,
                reason=diagnosis_result.reason,
                prerequisite_gaps=diagnosis_result.prerequisite_gaps,
            )
            session.status = ImprovementSessionStatus.DIAGNOSED
            session.updated_at = datetime.now()
            self.improvement_service.improvement_repo.update_session(session)

            # 2. 生成方案
            from app.agents.tools.improvement_tools import GenerateLearningPlanInput
            plan_result = self.tools.generate_learning_plan(
                GenerateLearningPlanInput(
                    target_kp_id=diagnosis_result.target_kp_id,
                    available_time=available_time,
                    difficulty=difficulty,
                    foundation=foundation,
                )
            )

            # 更新会话方案
            from app.models.improvement import ImprovementPlan, ImprovementPlanStep
            import uuid
            session.plan = ImprovementPlan(
                plan_id=str(uuid.uuid4()),
                target_kp_id=diagnosis_result.target_kp_id,
                steps=[
                    ImprovementPlanStep(
                        step_order=step.step_order,
                        knowledge_point_id=step.knowledge_point_id,
                        goal=step.goal,
                        estimated_minutes=step.estimated_minutes,
                    )
                    for step in plan_result.steps
                ],
                total_estimated_minutes=plan_result.total_estimated_minutes,
            )
            session.status = ImprovementSessionStatus.PLANNING
            session.updated_at = datetime.now()
            self.improvement_service.improvement_repo.update_session(session)

            logger.info(f"Agent 流程完成：session_id={session_id}, diagnosis={diagnosis_result.target_kp_id}, plan_steps={len(plan_result.steps)}")

        except Exception as e:
            logger.error(f"Agent 流程失败：{e}", exc_info=True)
            session.status = ImprovementSessionStatus.FAILED
            session.updated_at = datetime.now()
            self.improvement_service.improvement_repo.update_session(session)
            raise

        return session
