"""
教学模式Prompt模板
支持6种教学模式：概念建构型、程序技能型、可视化理解型、对比辨析型、问题探究型、错误诊断型
"""

from typing import Any, Callable

from app.models.teaching_mode import TeachingModeType

from .concept_construction import (
    get_concept_construction_prompt,
    MODE_INFO as CONCEPT_INFO,
)
from .procedural_skill import (
    get_procedural_skill_prompt,
    MODE_INFO as PROCEDURAL_INFO,
)
from .visual_understanding import (
    get_visual_understanding_prompt,
    MODE_INFO as VISUAL_INFO,
)
from .contrast_analysis import (
    get_contrast_analysis_prompt,
    MODE_INFO as CONTRAST_INFO,
)
from .problem_inquiry import (
    get_problem_inquiry_prompt,
    MODE_INFO as INQUIRY_INFO,
)
from .error_diagnosis import (
    get_error_diagnosis_prompt,
    MODE_INFO as ERROR_INFO,
)


# 教学模式Prompt生成函数映射
TEACHING_MODE_PROMPTS: dict[TeachingModeType, Callable] = {
    TeachingModeType.CONCEPT_CONSTRUCTION: get_concept_construction_prompt,
    TeachingModeType.PROCEDURAL_SKILL: get_procedural_skill_prompt,
    TeachingModeType.VISUAL_UNDERSTANDING: get_visual_understanding_prompt,
    TeachingModeType.CONTRAST_ANALYSIS: get_contrast_analysis_prompt,
    TeachingModeType.PROBLEM_INQUIRY: get_problem_inquiry_prompt,
    TeachingModeType.ERROR_DIAGNOSIS: get_error_diagnosis_prompt,
}

# 教学模式信息映射
TEACHING_MODE_INFO: dict[TeachingModeType, dict] = {
    TeachingModeType.CONCEPT_CONSTRUCTION: CONCEPT_INFO,
    TeachingModeType.PROCEDURAL_SKILL: PROCEDURAL_INFO,
    TeachingModeType.VISUAL_UNDERSTANDING: VISUAL_INFO,
    TeachingModeType.CONTRAST_ANALYSIS: CONTRAST_INFO,
    TeachingModeType.PROBLEM_INQUIRY: INQUIRY_INFO,
    TeachingModeType.ERROR_DIAGNOSIS: ERROR_INFO,
}


def get_teaching_prompt(
    mode_type: TeachingModeType,
    phase: str,
    kp_info: dict[str, Any],
    learner_profile: dict[str, Any] = None,
) -> str:
    """
    获取教学模式Prompt
    
    Args:
        mode_type: 教学模式类型
        phase: 当前阶段名称
        kp_info: 知识点信息
        learner_profile: 学习者画像
        
    Returns:
        教学Prompt字符串
    """
    prompt_func = TEACHING_MODE_PROMPTS.get(mode_type)
    if not prompt_func:
        raise ValueError(f"未知的教学模式类型: {mode_type}")
    
    return prompt_func(phase, kp_info, learner_profile)


def get_mode_phases(mode_type: TeachingModeType) -> list[str]:
    """获取教学模式的阶段列表"""
    info = TEACHING_MODE_INFO.get(mode_type)
    if not info:
        return []
    return info.get("phases", [])


def get_mode_name(mode_type: TeachingModeType) -> str:
    """获取教学模式名称"""
    info = TEACHING_MODE_INFO.get(mode_type)
    if not info:
        return "未知教学模式"
    return info.get("name", "未知教学模式")


__all__ = [
    "get_teaching_prompt",
    "get_mode_phases",
    "get_mode_name",
    "TEACHING_MODE_PROMPTS",
    "TEACHING_MODE_INFO",
    "TeachingModeType",
]
