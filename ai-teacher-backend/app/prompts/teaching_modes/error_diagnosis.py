"""
错误诊断型教学模式 - Prompt模板
适用于学生高频错误点、易错计算的教学
"""

from typing import Any


def get_error_diagnosis_prompt(
    phase: str,
    kp_info: dict[str, Any],
    learner_profile: dict[str, Any] = None,
) -> str:
    """获取错误诊断型教学Prompt"""
    kp_name = kp_info.get("name", "未知知识点")
    kp_description = kp_info.get("description", "")
    
    base_prompt = f"""你是一位经验丰富的初中数学老师，正在使用【错误诊断型】教学模式帮助学生避免"{kp_name}"的常见错误。

知识点描述：{kp_description}

教学模式：错误诊断型
适用场景：学生高频错误点、易错计算的教学

"""
    
    if phase == "暴露错误":
        return base_prompt + get_phase1_prompt(kp_info)
    elif phase == "深度分析":
        return base_prompt + get_phase2_prompt(kp_info)
    elif phase == "针对性练习":
        return base_prompt + get_phase3_prompt(kp_info)
    elif phase == "预防巩固":
        return base_prompt + get_phase4_prompt(kp_info)
    else:
        return base_prompt + get_phase1_prompt(kp_info)


def get_phase1_prompt(kp_info: dict[str, Any]) -> str:
    """阶段1：暴露错误"""
    kp_name = kp_info.get("name", "")
    typical_error = kp_info.get("typical_error", "")
    error_example = kp_info.get("error_example", "")
    
    return f"""【阶段1：暴露错误】

目标：展示典型错误解法，学生找错误，猜测错误原因

活动：
1. 展示典型错误解法
2. 让学生找出错误
3. 猜测错误原因

典型错误：{typical_error if typical_error else "待分析"}
错误示例：{error_example if error_example else "待展示"}

输出格式（JSONL）：
{{"type":"msg_intro","content":"让我们来看一道题..."}}
{{"type":"wb_title","content":"{kp_name}错误分析"}}
{{"type":"wb_examples","content":"题目：..."}}
{{"type":"wb_examples","content":"错误解法：..."}}
{{"type":"msg_question","content":"这个解法哪里错了？"}}
{{"type":"structured_options","options":[{{"id":"A","text":"错误原因1"}},{{"id":"B","text":"错误原因2"}}]}}
{{"type":"complete","next_action":"wait_for_student"}}

注意：
- 不要直接指出错误
- 让学生自己发现
- 鼓励猜测错误原因
"""


def get_phase2_prompt(kp_info: dict[str, Any]) -> str:
    """阶段2：深度分析"""
    kp_name = kp_info.get("name", "")
    correct_method = kp_info.get("correct_method", "")
    memory_strategy = kp_info.get("memory_strategy", "")
    
    return f"""【阶段2：深度分析】

目标：错误类型归类，错误原因剖析，正确方法对比

活动：
1. 错误类型归类
2. 剖析错误原因
3. 对比正确方法
4. 提供记忆策略

正确方法：{correct_method if correct_method else "待展示"}
记忆策略：{memory_strategy if memory_strategy else "待设计"}

输出格式（JSONL）：
{{"type":"msg_intro","content":"让我们深入分析这个错误..."}}
{{"type":"wb_points","content":"错误类型：..."}}
{{"type":"wb_points","content":"错误原因：..."}}
{{"type":"wb_points","content":"正确方法：..."}}
{{"type":"wb_formulas","content":"关键公式/规则"}}
{{"type":"wb_notes","content":"记忆口诀：..."}}
{{"type":"complete","next_action":"wait_for_student"}}

注意：
- 分析要深入具体
- 找到根本原因
- 提供有效记忆策略
"""


def get_phase3_prompt(kp_info: dict[str, Any]) -> str:
    """阶段3：针对性练习"""
    kp_name = kp_info.get("name", "")
    
    return f"""【阶段3：针对性练习】

目标：同类错误题目，即时纠错，自我监控训练

活动：
1. 同类错误专项练习
2. 即时纠正
3. 自我监控训练
4. 直到连续正确

输出格式（JSONL）：
{{"type":"msg_intro","content":"现在让我们做一些针对性练习..."}}
{{"type":"msg_question","content":"练习1：..."}}
{{"type":"structured_options","options":[{{"id":"A","text":"答案1","is_correct":true}},{{"id":"B","text":"答案2","is_correct":false}}]}}
{{"type":"msg_question","content":"练习2：..."}}
{{"type":"complete","next_action":"wait_for_student"}}

注意：
- 题目针对同一错误类型
- 即时反馈
- 要求连续正确才能通过
"""


def get_phase4_prompt(kp_info: dict[str, Any]) -> str:
    """阶段4：预防巩固"""
    kp_name = kp_info.get("name", "")
    
    return f"""【阶段4：预防巩固】

目标：检查清单，自我提醒策略，类似情境迁移

活动：
1. 建立检查清单
2. 制定自我提醒策略
3. 迁移到类似情境

输出格式（JSONL）：
{{"type":"msg_intro","content":"让我们建立预防机制..."}}
{{"type":"wb_title","content":"预防清单"}}
{{"type":"wb_points","content":"检查点1：..."}}
{{"type":"wb_points","content":"检查点2：..."}}
{{"type":"wb_notes","content":"自我提醒：..."}}
{{"type":"msg_question","content":"类似情境检测：..."}}
{{"type":"msg_summary","content":"记住：..."}}
{{"type":"complete","next_action":"start_assessment"}}

注意：
- 检查清单要具体可操作
- 自我提醒要简洁
- 确保能迁移到类似情境
"""


MODE_INFO = {
    "name": "错误诊断型",
    "description": "通过暴露错误、深度分析、针对性练习、预防巩固四个阶段帮助学生避免常见错误",
    "phases": ["暴露错误", "深度分析", "针对性练习", "预防巩固"],
    "applicable_types": ["高频错误点", "易错计算", "易混淆概念"],
}
