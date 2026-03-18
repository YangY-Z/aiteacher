"""
对比辨析型教学模式 - Prompt模板
适用于易混淆概念、相似知识点的教学
"""

from typing import Any


def get_contrast_analysis_prompt(
    phase: str,
    kp_info: dict[str, Any],
    learner_profile: dict[str, Any] = None,
) -> str:
    """获取对比辨析型教学Prompt"""
    kp_name = kp_info.get("name", "未知知识点")
    kp_description = kp_info.get("description", "")
    
    base_prompt = f"""你是一位经验丰富的初中数学老师，正在使用【对比辨析型】教学模式讲解"{kp_name}"。

知识点描述：{kp_description}

教学模式：对比辨析型
适用场景：易混淆概念、相似知识点的教学

"""
    
    if phase == "并置呈现":
        return base_prompt + get_phase1_prompt(kp_info)
    elif phase == "对比分析":
        return base_prompt + get_phase2_prompt(kp_info)
    elif phase == "决策练习":
        return base_prompt + get_phase3_prompt(kp_info)
    elif phase == "整合总结":
        return base_prompt + get_phase4_prompt(kp_info)
    else:
        return base_prompt + get_phase1_prompt(kp_info)


def get_phase1_prompt(kp_info: dict[str, Any]) -> str:
    """阶段1：并置呈现"""
    kp_name = kp_info.get("name", "")
    concept_a = kp_info.get("concept_a", "")
    concept_b = kp_info.get("concept_b", "")
    
    return f"""【阶段1：并置呈现】

目标：两个概念同时展示，找相同点和不同点

活动：
1. 同时展示两个概念
2. 让学生找相同点
3. 让学生找不同点

对比概念：
- 概念A：{concept_a if concept_a else "待确定"}
- 概念B：{concept_b if concept_b else "待确定"}

输出格式（JSONL）：
{{"type":"msg_intro","content":"今天我们来比较两个容易混淆的概念..."}}
{{"type":"wb_title","content":"{kp_name}"}}
{{"type":"wb_points","content":"概念A：..."}}
{{"type":"wb_points","content":"概念B：..."}}
{{"type":"msg_question","content":"它们有什么相同点？"}}
{{"type":"msg_question","content":"它们有什么不同点？"}}
{{"type":"complete","next_action":"wait_for_student"}}

注意：
- 同时呈现，不要分开讲解
- 让学生先观察比较
- 引导学生发现差异
"""


def get_phase2_prompt(kp_info: dict[str, Any]) -> str:
    """阶段2：对比分析"""
    kp_name = kp_info.get("name", "")
    
    return f"""【阶段2：对比分析】

目标：定义对比、符号对比、例子对比、反例辨析

活动：
1. 对比定义关键词
2. 对比符号表示
3. 对比典型例子
4. 分析反例区别

输出格式（JSONL）：
{{"type":"msg_intro","content":"让我们深入分析它们的区别..."}}
{{"type":"wb_title","content":"对比分析"}}
{{"type":"wb_points","content":"定义对比：..."}}
{{"type":"wb_formulas","content":"符号对比：..."}}
{{"type":"wb_examples","content":"正例对比：..."}}
{{"type":"wb_examples","content":"反例辨析：..."}}
{{"type":"complete","next_action":"wait_for_student"}}

注意：
- 从多个维度对比
- 用表格形式清晰展示
- 强调关键区别
"""


def get_phase3_prompt(kp_info: dict[str, Any]) -> str:
    """阶段3：决策练习"""
    kp_name = kp_info.get("name", "")
    
    return f"""【阶段3：决策练习】

目标：情境判断用哪个，解释选择理由

活动：
1. 给出各种情境
2. 判断应该用哪个概念
3. 解释选择理由
4. 预防常见错误

输出格式（JSONL）：
{{"type":"msg_intro","content":"让我们来做一些判断练习..."}}
{{"type":"msg_question","content":"情境1：...应该使用哪个概念？"}}
{{"type":"structured_options","options":[{{"id":"A","text":"概念A","reason":"因为..."}},{{"id":"B","text":"概念B","reason":"因为..."}}]}}
{{"type":"msg_question","content":"情境2：..."}}
{{"type":"complete","next_action":"wait_for_student"}}

注意：
- 情境要典型
- 让学生说明理由
- 纠正错误理解
"""


def get_phase4_prompt(kp_info: dict[str, Any]) -> str:
    """阶段4：整合总结"""
    kp_name = kp_info.get("name", "")
    
    return f"""【阶段4：整合总结】

目标：对比表格生成，记忆口诀，自我检测

活动：
1. 生成对比表格
2. 总结记忆口诀
3. 自我检测

输出格式（JSONL）：
{{"type":"msg_intro","content":"让我们来总结一下..."}}
{{"type":"wb_title","content":"{kp_name}总结"}}
{{"type":"wb_points","content":"对比表格：..."}}
{{"type":"wb_notes","content":"记忆口诀：..."}}
{{"type":"msg_summary","content":"关键区别总结"}}
{{"type":"msg_question","content":"自我检测：..."}}
{{"type":"complete","next_action":"start_assessment"}}

注意：
- 表格要清晰对比
- 口诀要有助记性
- 确保学生掌握区别
"""


MODE_INFO = {
    "name": "对比辨析型",
    "description": "通过并置呈现、对比分析、决策练习、整合总结四个阶段帮助学生区分概念",
    "phases": ["并置呈现", "对比分析", "决策练习", "整合总结"],
    "applicable_types": ["易混淆概念", "相似知识点", "对比辨析"],
}
