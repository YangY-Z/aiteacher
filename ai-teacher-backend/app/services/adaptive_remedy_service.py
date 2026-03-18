"""
自适应补救服务
"""

from datetime import datetime
from typing import Optional

from app.models.adaptive_remedy import (
    ErrorAnalysis,
    RemedialContent,
    AdaptiveRemedyPlan,
    RemedyStatus,
    RemedialStrategy,
    ERROR_STRATEGY_MAPPING,
    SEVERITY_THRESHOLDS,
)
from app.models.retention import ErrorType


class AdaptiveRemedyService:
    """自适应补救服务"""

    def __init__(self, repository, llm_service=None):
        self.repository = repository
        self.llm_service = llm_service

    def analyze_error(
        self,
        student_id: int,
        kp_id: str,
        wrong_answers: list[dict],
        attempt_count: int,
    ) -> ErrorAnalysis:
        """
        分析错误类型
        
        Args:
            student_id: 学生ID
            kp_id: 知识点ID
            wrong_answers: 错误答案列表
            attempt_count: 尝试次数
            
        Returns:
            错误分析结果
        """
        # 基于规则分析错误类型
        error_type = self._classify_error_type(wrong_answers, attempt_count)
        
        # 确定严重程度
        severity = self._determine_severity(attempt_count)
        
        # 确定补救策略
        strategy = ERROR_STRATEGY_MAPPING.get(error_type, RemedialStrategy.CONCEPT_REVIEW)
        
        # 分析相关知识缺口
        knowledge_gaps = self._identify_knowledge_gaps(student_id, kp_id, wrong_answers)
        
        return ErrorAnalysis(
            error_type=error_type,
            error_description=self._generate_error_description(error_type, wrong_answers),
            related_knowledge_gaps=knowledge_gaps,
            severity=severity,
            remedial_strategy=strategy,
        )

    def create_remedy_plan(
        self,
        student_id: int,
        current_kp_id: str,
        current_kp_name: str,
        error_analysis: ErrorAnalysis,
    ) -> AdaptiveRemedyPlan:
        """
        创建补救计划
        
        Args:
            student_id: 学生ID
            current_kp_id: 当前知识点ID
            current_kp_name: 当前知识点名称
            error_analysis: 错误分析结果
            
        Returns:
            补救计划
        """
        # 根据错误类型生成补救路径
        remedy_path = self._generate_remedy_path(error_analysis, current_kp_id, current_kp_name)
        
        plan = AdaptiveRemedyPlan(
            id=0,
            student_id=student_id,
            current_kp_id=current_kp_id,
            current_kp_name=current_kp_name,
            error_analysis=error_analysis,
            remedy_path=remedy_path,
            status=RemedyStatus.PENDING,
        )
        
        return self.repository.save_remedy_plan(plan)

    def get_remedy_plan(self, plan_id: int) -> Optional[AdaptiveRemedyPlan]:
        """获取补救计划"""
        return self.repository.get_remedy_plan(plan_id)

    def get_active_remedy_plan(self, student_id: int, kp_id: str) -> Optional[AdaptiveRemedyPlan]:
        """获取当前活跃的补救计划"""
        return self.repository.get_active_remedy_plan(student_id, kp_id)

    def advance_remedy_step(self, plan_id: int) -> AdaptiveRemedyPlan:
        """进入补救计划的下一步"""
        plan = self.get_remedy_plan(plan_id)
        if not plan:
            raise ValueError(f"未找到补救计划: {plan_id}")
        
        if plan.advance_step():
            plan.status = RemedyStatus.IN_PROGRESS
        else:
            plan.status = RemedyStatus.COMPLETED
            plan.completed_at = datetime.now()
        
        return self.repository.save_remedy_plan(plan)

    def complete_remedy(self, plan_id: int, success: bool = True) -> AdaptiveRemedyPlan:
        """完成补救"""
        plan = self.get_remedy_plan(plan_id)
        if not plan:
            raise ValueError(f"未找到补救计划: {plan_id}")
        
        plan.status = RemedyStatus.COMPLETED if success else RemedyStatus.FAILED
        plan.completed_at = datetime.now()
        
        return self.repository.save_remedy_plan(plan)

    # ============= 私有方法 =============
    
    def _classify_error_type(self, wrong_answers: list[dict], attempt_count: int) -> ErrorType:
        """分类错误类型"""
        if not wrong_answers:
            return ErrorType.CARELESS
        
        # 检查是否是计算错误
        for answer in wrong_answers:
            if self._is_calculation_error(answer):
                return ErrorType.CALCULATION
        
        # 检查是否是程序错误
        for answer in wrong_answers:
            if self._is_procedure_error(answer):
                return ErrorType.PROCEDURE_ERROR
        
        # 多次尝试失败可能是知识缺口
        if attempt_count >= 3:
            return ErrorType.KNOWLEDGE_GAP
        
        # 默认为概念误解
        return ErrorType.CONCEPT_MISUNDERSTANDING

    def _is_calculation_error(self, answer: dict) -> bool:
        """判断是否是计算错误"""
        # 检查答案是否接近正确答案（数值接近）
        # 这里简化处理
        return answer.get("is_calculation_error", False)

    def _is_procedure_error(self, answer: dict) -> bool:
        """判断是否是程序错误"""
        return answer.get("is_procedure_error", False)

    def _determine_severity(self, attempt_count: int) -> str:
        """确定严重程度"""
        if attempt_count >= SEVERITY_THRESHOLDS["severe"]:
            return "severe"
        elif attempt_count >= SEVERITY_THRESHOLDS["moderate"]:
            return "moderate"
        else:
            return "minor"

    def _identify_knowledge_gaps(
        self, 
        student_id: int, 
        kp_id: str, 
        wrong_answers: list[dict]
    ) -> list[str]:
        """识别知识缺口"""
        # TODO: 基于知识图谱分析前置知识掌握情况
        # 这里返回模拟数据
        gaps = []
        for answer in wrong_answers:
            if answer.get("missing_prerequisite"):
                gaps.append(answer["missing_prerequisite"])
        return gaps

    def _generate_error_description(self, error_type: ErrorType, wrong_answers: list[dict]) -> str:
        """生成错误描述"""
        descriptions = {
            ErrorType.CALCULATION: "计算过程中出现错误，需要检查计算步骤",
            ErrorType.CONCEPT_MISUNDERSTANDING: "对概念理解有误，需要重新理解概念",
            ErrorType.KNOWLEDGE_GAP: "缺少必要的前置知识，需要补充基础",
            ErrorType.CARELESS: "粗心导致的错误，需要提高注意力",
            ErrorType.PROCEDURE_ERROR: "解题步骤有误，需要重新学习正确流程",
        }
        return descriptions.get(error_type, "未知错误类型")

    def _generate_remedy_path(
        self,
        error_analysis: ErrorAnalysis,
        current_kp_id: str,
        current_kp_name: str,
    ) -> list[RemedialContent]:
        """生成补救路径"""
        path = []
        
        strategy = error_analysis.remedial_strategy
        
        if strategy == RemedialStrategy.CALCULATION_TIP:
            # 计算错误：提供检查提示
            path.append(RemedialContent(
                target_kp_id=current_kp_id,
                target_kp_name=current_kp_name,
                error_analysis=error_analysis,
                review_content="让我们检查一下计算过程...",
                examples=["检查符号", "检查运算顺序", "检查代入值"],
                practice_questions=[{"type": "calculation_check"}],
                estimated_time=3,
            ))
        
        elif strategy == RemedialStrategy.PREREQUISITE_FILL:
            # 知识缺口：补习前置知识
            for gap_kp in error_analysis.related_knowledge_gaps:
                path.append(RemedialContent(
                    target_kp_id=gap_kp,
                    target_kp_name=f"前置知识: {gap_kp}",
                    error_analysis=error_analysis,
                    review_content=f"让我们先复习一下 {gap_kp}...",
                    examples=[],
                    practice_questions=[],
                    estimated_time=5,
                ))
            # 最后回到当前知识点
            path.append(RemedialContent(
                target_kp_id=current_kp_id,
                target_kp_name=current_kp_name,
                error_analysis=error_analysis,
                review_content="现在回到原问题...",
                examples=[],
                practice_questions=[{"type": "original"}],
                estimated_time=5,
            ))
        
        elif strategy == RemedialStrategy.CONCEPT_REVIEW:
            # 概念复习
            path.append(RemedialContent(
                target_kp_id=current_kp_id,
                target_kp_name=current_kp_name,
                error_analysis=error_analysis,
                review_content="让我们重新理解这个概念...",
                examples=["概念要点1", "概念要点2"],
                practice_questions=[{"type": "concept_check"}],
                estimated_time=5,
            ))
        
        elif strategy == RemedialStrategy.PROCEDURE_PRACTICE:
            # 程序强化
            path.append(RemedialContent(
                target_kp_id=current_kp_id,
                target_kp_name=current_kp_name,
                error_analysis=error_analysis,
                review_content="让我们分步骤练习...",
                examples=["步骤1", "步骤2", "步骤3"],
                practice_questions=[{"type": "step_practice"}],
                estimated_time=8,
            ))
        
        elif strategy == RemedialStrategy.ERROR_PREVENTION:
            # 错误预防
            path.append(RemedialContent(
                target_kp_id=current_kp_id,
                target_kp_name=current_kp_name,
                error_analysis=error_analysis,
                review_content="让我们看看常见的错误陷阱...",
                examples=["易错点1", "易错点2"],
                practice_questions=[{"type": "error_prevention"}],
                estimated_time=3,
            ))
        
        return path
