"""Backtrack service for learning path remediation."""

import logging
from typing import Any, Optional

from app.models.learning import LearningRecord
from app.repositories.learning_repository import learning_record_repository
from app.repositories.course_repository import knowledge_point_repository, knowledge_point_dependency_repository
from app.services.llm_service import llm_service
from app.services.learner_profile_service import learner_profile_service
from app.prompts.backtrack_prompt import BACKTRACK_DECISION_PROMPT

logger = logging.getLogger(__name__)


class BacktrackService:
    """Service for backtrack decision and remediation."""

    def analyze_and_decide(
        self,
        student_id: int,
        current_kp_id: str,
        error_type: str,
        student_response: str,
        error_count: int = 1,
    ) -> dict[str, Any]:
        """Analyze student errors and decide on backtrack.

        Args:
            student_id: Student ID.
            current_kp_id: Current knowledge point ID.
            error_type: Type of error made.
            student_response: Student's incorrect response.
            error_count: Number of errors made.

        Returns:
            Decision with backtrack target if needed.
        """
        # Get current knowledge point info
        current_kp = knowledge_point_repository.get_by_id(current_kp_id)
        if not current_kp:
            return {
                "decision": "continue",
                "reason": "知识点不存在",
            }

        # Get prerequisites
        prereq_ids = knowledge_point_dependency_repository.get_dependencies(current_kp_id)

        if not prereq_ids:
            # No prerequisites, continue with current topic
            return {
                "decision": "continue",
                "reason": "当前知识点没有前置依赖，建议重新讲解",
                "teaching_adjustment": "使用不同的讲解方式，增加练习",
            }

        # ========== 集成学习者画像服务 ==========
        # 获取薄弱知识点列表（按掌握度排序）
        try:
            weak_kps = learner_profile_service.get_weak_knowledge_points(
                student_id=student_id,
                course_id=current_kp.course_id,
                threshold=0.6,
            )
            
            # 筛选出当前知识点的前置依赖中的薄弱点
            weak_prereqs = [
                wkp for wkp in weak_kps
                if wkp["kp_id"] in prereq_ids
            ]
            
            logger.info(f"薄弱前置知识点: {len(weak_prereqs)}个")
            
            if weak_prereqs:
                # 选择最薄弱的前置知识点
                weakest = weak_prereqs[0]  # 已经按掌握度排序
                
                return {
                    "decision": "backtrack",
                    "reason": f"学生对前置知识点「{weakest['kp_name']}」掌握不牢（掌握度{weakest['mastery']:.0%}）",
                    "error_root_cause": self._analyze_error_root_with_patterns(
                        error_type, weakest["kp_name"], weakest.get("error_patterns", [])
                    ),
                    "backtrack_target": {
                        "knowledge_point_id": weakest["kp_id"],
                        "knowledge_point_name": weakest["kp_name"],
                    },
                    "teaching_adjustment": f"重点讲解「{weakest['kp_name']}」的核心概念，强调与「{current_kp.name}」的联系",
                }
                
        except Exception as e:
            logger.warning(f"获取薄弱知识点失败，使用默认逻辑: {e}")
            # 降级：使用原有逻辑
            return self._fallback_analyze(
                student_id, current_kp_id, current_kp, prereq_ids, error_type
            )

        # Otherwise, continue with remediation
        return {
            "decision": "continue",
            "reason": "前置知识点掌握程度尚可，建议针对当前知识点进行针对性讲解",
            "teaching_adjustment": f"针对「{error_type}」类型的错误进行重点讲解",
        }
    
    def _fallback_analyze(
        self,
        student_id: int,
        current_kp_id: str,
        current_kp,
        prereq_ids: list[str],
        error_type: str,
    ) -> dict[str, Any]:
        """降级分析逻辑（当学习者画像服务不可用时）

        Args:
            student_id: 学生ID
            current_kp_id: 当前知识点ID
            current_kp: 当前知识点对象
            prereq_ids: 前置知识点ID列表
            error_type: 错误类型

        Returns:
            回溯决策
        """
        # Get student performance on prerequisites
        prereq_performance = []
        for prereq_id in prereq_ids:
            record = learning_record_repository.get_by_student_and_kp(
                student_id, prereq_id
            )
            prereq_kp = knowledge_point_repository.get_by_id(prereq_id)

            performance = {
                "kp_id": prereq_id,
                "kp_name": prereq_kp.name if prereq_kp else prereq_id,
                "status": record.status.value if record else "未学习",
                "attempt_count": record.attempt_count if record else 0,
                "last_score": record.attempts[-1].score if record and record.attempts else 0,
            }
            prereq_performance.append(performance)

        # Find the weakest prerequisite
        weakest = None
        lowest_score = 1.0

        for perf in prereq_performance:
            if perf["status"] == "未学习":
                weakest = perf
                break
            if perf["attempt_count"] >= 2 and perf["last_score"] < lowest_score:
                lowest_score = perf["last_score"]
                weakest = perf

        # If found weak prerequisite, backtrack
        if weakest and (weakest["status"] == "未学习" or lowest_score < 0.7):
            return {
                "decision": "backtrack",
                "reason": f"学生对前置知识点「{weakest['kp_name']}」掌握不牢",
                "error_root_cause": self._analyze_error_root(error_type, weakest["kp_name"]),
                "backtrack_target": {
                    "knowledge_point_id": weakest["kp_id"],
                    "knowledge_point_name": weakest["kp_name"],
                },
                "teaching_adjustment": f"重点讲解{weakest['kp_name']}的核心概念，强调与{current_kp.name}的联系",
            }

        return {
            "decision": "continue",
            "reason": "前置知识点掌握程度尚可，建议针对当前知识点进行针对性讲解",
            "teaching_adjustment": f"针对「{error_type}」类型的错误进行重点讲解",
        }

    def _analyze_error_root(self, error_type: str, prereq_name: str) -> str:
        """Analyze the root cause of an error.

        Args:
            error_type: Type of error.
            prereq_name: Name of the weak prerequisite.

        Returns:
            Root cause analysis string.
        """
        error_mapping = {
            "概念混淆": f"学生对{prereq_name}的概念理解不够清晰，导致无法正确应用",
            "计算错误": "学生在计算过程中存在粗心或方法错误",
            "公式记忆": f"学生对相关公式记忆不牢固，特别是{prereq_name}相关的公式",
            "理解不深": f"学生对{prereq_name}的理解停留在表面，未能深入理解其内涵",
        }

        return error_mapping.get(error_type, f"学生对{prereq_name}的掌握存在不足")
    
    def _analyze_error_root_with_patterns(
        self,
        error_type: str,
        prereq_name: str,
        error_patterns: list[dict],
    ) -> str:
        """结合错误模式分析根本原因

        Args:
            error_type: 错误类型
            prereq_name: 薄弱知识点名称
            error_patterns: 错误模式列表

        Returns:
            根本原因分析
        """
        base_cause = self._analyze_error_root(error_type, prereq_name)
        
        if not error_patterns:
            return base_cause
        
        # 添加具体错误模式信息
        pattern_desc = []
        for pattern in error_patterns[:2]:  # 最多取2个
            pattern_type = pattern.get("type", "")
            frequency = pattern.get("frequency", 0)
            
            pattern_names = {
                "concept_misunderstanding": "概念理解错误",
                "calculation_error": "计算错误",
                "procedure_error": "步骤错误",
                "careless_error": "粗心大意",
                "incomplete_answer": "答题不完整",
                "prerequisite_gap": "前置知识缺失",
            }
            
            name = pattern_names.get(pattern_type, pattern_type)
            pattern_desc.append(f"{name}({frequency}次)")
        
        if pattern_desc:
            return f"{base_cause}。常见错误模式：{', '.join(pattern_desc)}"
        
        return base_cause

    def generate_remedial_content(
        self,
        backtrack_kp_id: str,
        current_kp_name: str,
        error_analysis: str,
        student_name: str = "同学",
    ) -> dict[str, Any]:
        """Generate remedial teaching content for backtrack.

        Args:
            backtrack_kp_id: Knowledge point to backtrack to.
            current_kp_name: Name of the current (failed) knowledge point.
            error_analysis: Analysis of the error.
            student_name: Student name for personalization.

        Returns:
            Remedial teaching content.
        """
        kp = knowledge_point_repository.get_by_id(backtrack_kp_id)
        if not kp:
            return {
                "response_type": "讲解",
                "content": {"introduction": "让我们来复习一下相关的知识点。"},
                "whiteboard": {"formulas": [], "diagrams": []},
                "next_action": "wait_for_student",
            }

        return {
            "response_type": "讲解",
            "content": {
                "introduction": f"{student_name}，我发现你在学习「{current_kp_name}」时遇到了一些困难。让我们回顾一下相关的知识点「{kp.name}」，这会帮助你更好地理解。",
                "definition": kp.description or f"这是关于「{kp.name}」的核心内容。",
                "example": "让我们通过一个例子来加深理解...",
                "summary": f"记住「{kp.name}」的核心要点，这对理解「{current_kp_name}」非常重要。",
            },
            "whiteboard": {
                "formulas": [],
                "diagrams": ["坐标系"] if "图象" in kp.name or "函数" in kp.name else [],
            },
            "next_action": "wait_for_student",
        }


# Global service instance
backtrack_service = BacktrackService()
