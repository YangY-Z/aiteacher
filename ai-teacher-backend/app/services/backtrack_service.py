"""Backtrack service for learning path remediation."""

from typing import Any, Optional

from app.models.learning import LearningRecord
from app.repositories.learning_repository import learning_record_repository
from app.repositories.course_repository import knowledge_point_repository, knowledge_point_dependency_repository
from app.services.llm_service import llm_service
from app.prompts.backtrack_prompt import BACKTRACK_DECISION_PROMPT


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

        # Otherwise, continue with remediation
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
