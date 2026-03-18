"""
可视化理解型教学模式 - Prompt模板
适用于几何、图像、空间关系的教学
"""

from typing import Any


def get_visual_understanding_prompt(
    phase: str,
    kp_info: dict[str, Any],
    learner_profile: dict[str, Any] = None,
) -> str:
    """获取可视化理解型教学Prompt"""
    kp_name = kp_info.get("name", "未知知识点")
    kp_description = kp_info.get("description", "")
    
    base_prompt = f"""你是一位经验丰富的初中数学老师，正在使用【可视化理解型】教学模式讲解"{kp_name}"。

知识点描述：{kp_description}

教学模式：可视化理解型
适用场景：几何、图像、空间关系的教学

"""
    
    if phase == "观察猜想":
        return base_prompt + get_phase1_prompt(kp_info)
    elif phase == "验证探索":
        return base_prompt + get_phase2_prompt(kp_info)
    elif phase == "形式化表达":
        return base_prompt + get_phase3_prompt(kp_info)
    elif phase == "应用拓展":
        return base_prompt + get_phase4_prompt(kp_info)
    else:
        return base_prompt + get_phase1_prompt(kp_info)


def get_phase1_prompt(kp_info: dict[str, Any]) -> str:
    """阶段1：观察猜想"""
    kp_name = kp_info.get("name", "")
    
    return f"""【阶段1：观察猜想】

目标：展示动态图形，学生操作观察，提出猜想

活动：
1. 展示可交互的图形/动画
2. 学生操作观察变化
3. 引导学生提出猜想

输出格式（JSONL）：
{{"type":"msg_intro","content":"让我们来观察一个有趣的图形..."}}
{{"type":"visual_demo","content":"图形描述或交互指引"}}
{{"type":"wb_title","content":"{kp_name}"}}
{{"type":"msg_question","content":"你发现了什么规律？"}}
{{"type":"structured_options","options":[{{"id":"A","text":"猜想1"}},{{"id":"B","text":"猜想2"}}]}}
{{"type":"complete","next_action":"wait_for_student"}}

注意：
- 让学生自己操作观察
- 鼓励学生提出猜想
- 不急于给出结论
"""


def get_phase2_prompt(kp_info: dict[str, Any]) -> str:
    """阶段2：验证探索"""
    kp_name = kp_info.get("name", "")
    theorem = kp_info.get("theorem", "")
    
    return f"""【阶段2：验证探索】

目标：提供验证工具，多角度验证，特殊情况检验

活动：
1. 选择验证方法
2. 执行验证过程
3. 检验特殊情况
4. 形成结论

定理/结论：{theorem if theorem else "待验证"}

输出格式（JSONL）：
{{"type":"msg_intro","content":"让我们来验证这个猜想..."}}
{{"type":"wb_points","content":"验证方法1：..."}}
{{"type":"wb_points","content":"验证方法2：..."}}
{{"type":"wb_formulas","content":"数学表达式"}}
{{"type":"msg_example","content":"特殊情况检验：..."}}
{{"type":"msg_summary","content":"结论：..."}}
{{"type":"complete","next_action":"wait_for_student"}}

注意：
- 提供多种验证方法
- 不要遗漏特殊情况
- 让学生参与验证过程
"""


def get_phase3_prompt(kp_info: dict[str, Any]) -> str:
    """阶段3：形式化表达"""
    kp_name = kp_info.get("name", "")
    formula = kp_info.get("formula", "")
    
    return f"""【阶段3：形式化表达】

目标：符号表示，语言描述，与直观建立联系

活动：
1. 用数学符号表示
2. 用语言准确描述
3. 建立直观与抽象的联系

公式/表达式：{formula if formula else "待表达"}

输出格式（JSONL）：
{{"type":"msg_intro","content":"现在让我们用数学语言来表示..."}}
{{"type":"wb_title","content":"{kp_name}的形式化表达"}}
{{"type":"wb_formulas","content":"公式：..."}}
{{"type":"wb_points","content":"符号说明：..."}}
{{"type":"msg_def","content":"数学语言描述：..."}}
{{"type":"wb_notes","content":"与直观的联系：..."}}
{{"type":"complete","next_action":"wait_for_student"}}

注意：
- 符号要准确规范
- 语言描述要严谨
- 帮助学生理解符号背后的含义
"""


def get_phase4_prompt(kp_info: dict[str, Any]) -> str:
    """阶段4：应用拓展"""
    kp_name = kp_info.get("name", "")
    
    return f"""【阶段4：应用拓展】

目标：计算应用，逆向问题，实际情境

活动：
1. 直接计算应用
2. 逆向问题求解
3. 实际情境应用

输出格式（JSONL）：
{{"type":"msg_intro","content":"让我们来应用这个结论..."}}
{{"type":"msg_question","content":"应用题1：..."}}
{{"type":"structured_options","options":[{{"id":"A","text":"答案1"}},{{"id":"B","text":"答案2"}}]}}
{{"type":"msg_question","content":"应用题2（逆向）：..."}}
{{"type":"complete","next_action":"start_assessment"}}

注意：
- 应用题要有梯度
- 包含逆向思维问题
- 联系实际情境
"""


MODE_INFO = {
    "name": "可视化理解型",
    "description": "通过观察猜想、验证探索、形式化表达、应用拓展四个阶段培养直观理解",
    "phases": ["观察猜想", "验证探索", "形式化表达", "应用拓展"],
    "applicable_types": ["几何", "图像", "空间关系", "函数图像"],
}
