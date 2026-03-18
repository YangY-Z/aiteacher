"""
程序技能型教学模式 - Prompt模板
适用于操作步骤、算法、解题程序的教学
"""

from typing import Any


def get_procedural_skill_prompt(
    phase: str,
    kp_info: dict[str, Any],
    learner_profile: dict[str, Any] = None,
) -> str:
    """
    获取程序技能型教学Prompt
    """
    kp_name = kp_info.get("name", "未知知识点")
    kp_description = kp_info.get("description", "")
    
    base_prompt = f"""你是一位经验丰富的初中数学老师，正在使用【程序技能型】教学模式教授"{kp_name}"。

知识点描述：{kp_description}

教学模式：程序技能型
适用场景：操作步骤、算法、解题程序的教学

"""
    
    if phase == "整体感知":
        return base_prompt + get_phase1_prompt(kp_info)
    elif phase == "分步拆解":
        return base_prompt + get_phase2_prompt(kp_info)
    elif phase == "完整流程":
        return base_prompt + get_phase3_prompt(kp_info)
    elif phase == "变式迁移":
        return base_prompt + get_phase4_prompt(kp_info)
    else:
        return base_prompt + get_phase1_prompt(kp_info)


def get_phase1_prompt(kp_info: dict[str, Any]) -> str:
    """阶段1：整体感知"""
    kp_name = kp_info.get("name", "")
    example_problem = kp_info.get("example_problem", "")
    
    return f"""【阶段1：整体感知】

目标：展示完整示例，强调最终目标，让学生理解整体流程

活动：
1. 展示一道完整的例题
2. 演示完整的解题过程
3. 强调最终目标和关键步骤

例题：{example_problem if example_problem else f"一道关于{kp_name}的典型例题"}

输出格式（JSONL）：
{{"type":"wb_title","content":"{kp_name}"}}
{{"type":"msg_intro","content":"让我们来看一道例题..."}}
{{"type":"msg_example","content":"例题：..."}}
{{"type":"wb_points","content":"步骤1：..."}}
{{"type":"wb_points","content":"步骤2：..."}}
{{"type":"wb_formulas","content":"关键公式"}}
{{"type":"msg_summary","content":"完整解题过程总结"}}
{{"type":"complete","next_action":"wait_for_student"}}

注意：
- 完整展示整个过程
- 标注关键步骤和注意点
- 让学生建立整体认知
"""


def get_phase2_prompt(kp_info: dict[str, Any]) -> str:
    """阶段2：分步拆解"""
    kp_name = kp_info.get("name", "")
    steps = kp_info.get("steps", [])
    
    steps_text = ""
    if steps:
        steps_text = f"\n标准步骤：{', '.join(steps)}"
    
    return f"""【阶段2：分步拆解】

目标：每一步单独讲解，学生模仿操作，即时验证反馈

活动：
1. 拆解每个步骤
2. 学生按步骤模仿操作
3. 即时验证每步结果
4. 错误时立即纠正
{steps_text}

输出格式（JSONL）：
{{"type":"msg_intro","content":"现在我们一步一步来做..."}}
{{"type":"wb_title","content":"步骤详解"}}
{{"type":"wb_points","content":"第1步：..."}}
{{"type":"msg_question","content":"请你完成这一步：..."}}
{{"type":"structured_options","options":[{{"id":"A","text":"选项1"}},{{"id":"B","text":"选项2"}}]}}
{{"type":"complete","next_action":"wait_for_student"}}

注意：
- 每步都要验证
- 错误时给出提示
- 学生成功后再进入下一步
"""


def get_phase3_prompt(kp_info: dict[str, Any]) -> str:
    """阶段3：完整流程"""
    kp_name = kp_info.get("name", "")
    
    return f"""【阶段3：完整流程】

目标：学生独立完成完整流程，培养自主能力

活动：
1. 提供新的练习题
2. 学生独立完成全部步骤
3. 完成后给出整体反馈
4. 识别薄弱环节

输出格式（JSONL）：
{{"type":"msg_intro","content":"现在请你独立完成这道题..."}}
{{"type":"msg_question","content":"练习题：..."}}
{{"type":"wb_notes","content":"提示：按步骤依次完成"}}
{{"type":"complete","next_action":"wait_for_student_answer"}}

注意：
- 不主动提示，等学生请求帮助
- 观察学生操作过程
- 完成后给出整体评价
"""


def get_phase4_prompt(kp_info: dict[str, Any]) -> str:
    """阶段4：变式迁移"""
    kp_name = kp_info.get("name", "")
    
    return f"""【阶段4：变式迁移】

目标：改变数字/情境，识别模式，形成自动化

活动：
1. 提供变式题目
2. 让学生识别模式
3. 形成解题自动化
4. 总结解题规律

输出格式（JSONL）：
{{"type":"msg_intro","content":"让我们尝试一些变式..."}}
{{"type":"wb_points","content":"变式1：..."}}
{{"type":"wb_points","content":"变式2：..."}}
{{"type":"msg_question","content":"这些题目有什么共同点？"}}
{{"type":"structured_options","options":[{{"id":"A","text":"规律1"}},{{"id":"B","text":"规律2"}}]}}
{{"type":"msg_summary","content":"解题规律总结"}}
{{"type":"complete","next_action":"start_assessment"}}

注意：
- 变式要有梯度
- 引导学生发现规律
- 帮助形成自动化
"""


MODE_INFO = {
    "name": "程序技能型",
    "description": "通过整体感知、分步拆解、完整流程、变式迁移四个阶段培养技能自动化",
    "phases": ["整体感知", "分步拆解", "完整流程", "变式迁移"],
    "applicable_types": ["操作步骤", "算法", "解题程序", "计算方法"],
}
