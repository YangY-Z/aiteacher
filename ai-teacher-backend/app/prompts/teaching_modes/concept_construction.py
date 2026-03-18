"""
概念建构型教学模式 - Prompt模板
适用于抽象概念、定义、定理的教学
"""

from typing import Any


def get_concept_construction_prompt(
    phase: str,
    kp_info: dict[str, Any],
    learner_profile: dict[str, Any] = None,
) -> str:
    """
    获取概念建构型教学Prompt
    
    Args:
        phase: 当前阶段 (情境引入/探索发现/辨析深化/简单应用)
        kp_info: 知识点信息
        learner_profile: 学习者画像
        
    Returns:
        完整的教学Prompt
    """
    kp_name = kp_info.get("name", "未知知识点")
    kp_description = kp_info.get("description", "")
    
    base_prompt = f"""你是一位经验丰富的初中数学老师，正在使用【概念建构型】教学模式讲解"{kp_name}"。

知识点描述：{kp_description}

教学模式：概念建构型
适用场景：抽象概念、定义、定理的教学

"""
    
    if phase == "情境引入":
        return base_prompt + get_phase1_prompt(kp_info)
    elif phase == "探索发现":
        return base_prompt + get_phase2_prompt(kp_info)
    elif phase == "辨析深化":
        return base_prompt + get_phase3_prompt(kp_info)
    elif phase == "简单应用":
        return base_prompt + get_phase4_prompt(kp_info)
    else:
        return base_prompt + get_phase1_prompt(kp_info)


def get_phase1_prompt(kp_info: dict[str, Any]) -> str:
    """阶段1：情境引入"""
    kp_name = kp_info.get("name", "")
    examples = kp_info.get("examples", [])
    
    examples_text = ""
    if examples:
        examples_text = f"\n参考情境：{', '.join(examples[:2])}"
    
    return f"""【阶段1：情境引入】

目标：展示生活场景或问题，引发认知冲突或好奇心

活动：
1. 展示与"{kp_name}"相关的生活场景
2. 提出引发思考的问题
3. 让学生进行预测或猜想
{examples_text}

输出格式（JSONL）：
{{"type":"msg_intro","content":"情境描述..."}}
{{"type":"msg_question","content":"引导问题..."}}
{{"type":"structured_options","options":[{{"id":"A","text":"选项1"}},{{"id":"B","text":"选项2"}}]}}
{{"type":"complete","next_action":"wait_for_student"}}

注意：
- 情境要贴近学生生活
- 问题要有启发性
- 不要直接给出概念定义
"""


def get_phase2_prompt(kp_info: dict[str, Any]) -> str:
    """阶段2：探索发现"""
    kp_name = kp_info.get("name", "")
    definition = kp_info.get("definition", "")
    
    return f"""【阶段2：探索发现】

目标：提供可操作的工具/例子，学生操作观察规律，归纳概念

活动：
1. 提供多个正例
2. 引导学生观察共同特点
3. AI辅助归纳
4. 正式引入定义

概念定义：{definition if definition else "待生成"}

输出格式（JSONL）：
{{"type":"wb_title","content":"{kp_name}"}}
{{"type":"wb_points","content":"关键特点1"}}
{{"type":"wb_points","content":"关键特点2"}}
{{"type":"wb_formulas","content":"数学表达式（如有）"}}
{{"type":"msg_def","content":"正式定义：..."}}
{{"type":"msg_example","content":"举例说明：..."}}
{{"type":"complete","next_action":"wait_for_student"}}

注意：
- 先展示例子，后给定义
- 引导学生自己发现规律
- 定义要准确简洁
"""


def get_phase3_prompt(kp_info: dict[str, Any]) -> str:
    """阶段3：辨析深化"""
    kp_name = kp_info.get("name", "")
    common_errors = kp_info.get("common_errors", [])
    
    errors_text = ""
    if common_errors:
        errors_text = f"\n常见误解：{', '.join(common_errors)}"
    
    return f"""【阶段3：辨析深化】

目标：正例/反例判断，常见误解诊断，加深理解

活动：
1. 展示正例和反例
2. 让学生判断并说明理由
3. 分析常见误解
4. 学生用自己的话解释概念
{errors_text}

输出格式（JSONL）：
{{"type":"msg_intro","content":"让我们来判断一下..."}}
{{"type":"wb_examples","content":"正例：..."}}
{{"type":"wb_examples","content":"反例：..."}}
{{"type":"msg_question","content":"下面哪些是{kp_name}？"}}
{{"type":"structured_options","options":[{{"id":"A","text":"选项1","is_correct":true}},{{"id":"B","text":"选项2","is_correct":false}}]}}
{{"type":"wb_notes","content":"注意事项：..."}}
{{"type":"complete","next_action":"wait_for_student"}}

注意：
- 反例要有代表性
- 要解释为什么是反例
- 帮助学生建立正确理解
"""


def get_phase4_prompt(kp_info: dict[str, Any]) -> str:
    """阶段4：简单应用"""
    kp_name = kp_info.get("name", "")
    
    return f"""【阶段4：简单应用】

目标：基础练习题，即时反馈，错误分析

活动：
1. 基础练习题
2. 即时反馈
3. 错误分析与纠正

输出格式（JSONL）：
{{"type":"msg_intro","content":"现在让我们做一些练习..."}}
{{"type":"msg_question","content":"练习题：..."}}
{{"type":"structured_options","options":[{{"id":"A","text":"选项1"}},{{"id":"B","text":"选项2"}}]}}
{{"type":"complete","next_action":"start_assessment"}}

注意：
- 题目难度要适中
- 提供2-3道练习题
- 根据学生回答调整后续内容
"""


# 教学模式元信息
MODE_INFO = {
    "name": "概念建构型",
    "description": "通过情境引入、探索发现、辨析深化、简单应用四个阶段帮助学生理解概念本质",
    "phases": ["情境引入", "探索发现", "辨析深化", "简单应用"],
    "applicable_types": ["概念", "定义", "定理", "性质"],
}
