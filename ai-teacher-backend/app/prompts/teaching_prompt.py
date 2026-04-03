"""
教学模式Prompt生成器 - V2 整合6种教学模式
支持：概念建构型、程序技能型、可视化理解型、对比辨析型、问题探究型、错误诊断型
"""

from typing import Any, Optional
from app.models.teaching_mode import (
    TeachingModeType,
    TeachingPhase,
    TEACHING_MODE_CONFIGS,
)


# ============= 教学模式 -> 知识点类型 映射 =============
KP_TYPE_TO_MODE = {
    "概念": TeachingModeType.CONCEPT_CONSTRUCTION,
    "concept": TeachingModeType.CONCEPT_CONSTRUCTION,
    "公式": TeachingModeType.CONCEPT_CONSTRUCTION,  # 公式也可以用概念建构型
    "formula": TeachingModeType.CONCEPT_CONSTRUCTION,
    "技能": TeachingModeType.PROCEDURAL_SKILL,
    "skill": TeachingModeType.PROCEDURAL_SKILL,
}


def get_teaching_mode_for_kp(kp_type: str) -> TeachingModeType:
    """根据知识点类型获取教学模式"""
    return KP_TYPE_TO_MODE.get(kp_type, TeachingModeType.CONCEPT_CONSTRUCTION)


def get_mode_prompt_section(mode_type: TeachingModeType) -> str:
    """获取教学模式说明部分"""
    mode_config = TEACHING_MODE_CONFIGS.get(mode_type)
    if not mode_config:
        return ""
    
    phases_desc = "\n".join([
        f"   阶段{p.order}：{p.name}（{p.duration_minutes[0]}-{p.duration_minutes[1]}分钟）- {p.description}"
        for p in mode_config.phases
    ])
    
    return f"""【教学模式：{mode_config.name}】
{mode_config.description}

教学阶段：
{phases_desc}

评估标准：
{chr(10).join(['- ' + c for c in mode_config.assessment_criteria])}
"""


def get_phase_prompt_section(phase: TeachingPhase) -> str:
    """获取教学阶段说明部分"""
    activities = " → ".join(phase.activities)
    return f"""【当前阶段：{phase.name}】
阶段目标：{phase.description}
阶段活动：{activities}
交互类型：{phase.interaction_type.value}
"""


def get_phase_output_guide(phase: int, phase_config: Optional[TeachingPhase], total_phases: int) -> str:
    """获取当前阶段的输出指引"""
    if not phase_config:
        return f"执行第{phase}阶段的教学内容"
    
    phase_name = phase_config.name
    activities = phase_config.activities
    activities_text = " → ".join(activities)
    
    # 根据阶段序号和总阶段数决定 next_action
    next_action = "next_phase" if phase < total_phases else "start_assessment"
    
    guides = {
        1: f"""
【阶段{phase}：{phase_name}】输出要求：
- 本阶段活动：{activities_text}
- 输出内容：情境引入、展示问题、激发兴趣
- 结尾：提出引导性问题，让学生思考或预测
- next_action: "{next_action}"
""",
        2: f"""
【阶段{phase}：{phase_name}】输出要求：
- 本阶段活动：{activities_text}
- 输出内容：详细讲解、示例演示、学生操作
- 结尾：确认学生是否理解，或提出练习问题
- next_action: "{next_action}"
""",
        3: f"""
【阶段{phase}：{phase_name}】输出要求：
- 本阶段活动：{activities_text}
- 输出内容：辨析练习、深化理解、错误诊断
- 结尾：让学生用自己的话解释或举例子
- next_action: "{next_action}"
""",
        4: f"""
【阶段{phase}：{phase_name}】输出要求：
- 本阶段活动：{activities_text}
- 输出内容：综合练习、巩固应用、总结归纳
- 结尾：提问检查整体理解程度
- next_action: "{next_action}"
""",
    }
    
    return guides.get(phase, f"执行{phase_name}的内容，完成后设置 next_action: \"{next_action}\"")


def get_mode_specific_requirements(mode_type: TeachingModeType) -> str:
    """获取教学模式的特殊要求"""
    requirements = {
        TeachingModeType.CONCEPT_CONSTRUCTION: """
概念建构型教学模式要点：
- 从具体到抽象：先展示实例，再归纳概念
- 强调本质特征：指出概念的核心要素
- 正反例对比：帮助学生辨析概念
- 检查理解：让学生用自己的话解释
""",
        TeachingModeType.PROCEDURAL_SKILL: """
程序技能型教学模式要点：
- 分步骤讲解：将操作分解为具体步骤
- 每步验证：每个步骤后让学生确认
- 强调要点：指出每步的注意事项和常见错误
- 练习巩固：让学生模仿操作
""",
        TeachingModeType.VISUAL_UNDERSTANDING: """
可视化理解型教学模式要点：
- 动态展示：描述图形的变化过程
- 观察猜想：引导学生从直观发现规律
- 形式化表达：将直观理解转化为数学语言
- 应用拓展：计算应用和逆向问题
""",
        TeachingModeType.CONTRAST_ANALYSIS: """
对比辨析型教学模式要点：
- 并置呈现：同时展示两个相关概念
- 对比分析：找出相同点和不同点
- 决策练习：让学生判断用哪个概念
- 整合总结：生成对比表格或记忆口诀
""",
        TeachingModeType.PROBLEM_INQUIRY: """
问题探究型教学模式要点：
- 问题情境：提出有趣或真实的问题
- 方案设计：讨论可能的方法和策略
- 执行探究：实施计划并记录数据
- 反思总结：分享结果和方法比较
""",
        TeachingModeType.ERROR_DIAGNOSIS: """
错误诊断型教学模式要点：
- 暴露错误：展示典型错误解法
- 深度分析：分析错误原因和类型
- 针对性练习：同类错误的纠正练习
- 预防巩固：建立检查清单
""",
    }
    return requirements.get(mode_type, "")


def generate_teaching_prompt(
    knowledge_point_name: str,
    knowledge_point_id: str,
    knowledge_point_type: str,
    description: str,
    key_points: str,
    dependencies: str,
    student_name: str,
    attempt_count: int,
    attempt_info: str,
    teaching_requirements: str,
    learner_type: str = "intermediate",
    current_phase: int = 1,
    learning_round: int = 1,
    history_summary: str = "",
) -> str:
    """
    生成完整的教学Prompt
    
    根据知识点类型自动选择教学模式，并生成对应的教学内容。
    重点：只输出当前阶段的教学内容，等待学生互动后再进入下一阶段。
    
    Args:
        learning_round: 当前学习轮次。第1轮=首次学习，第2轮=重新学习（之前未通过评估），以此类推。
        history_summary: 历史学习总结（用于回顾之前的学习情况）。
    """
    # 根据知识点类型选择教学模式
    mode_type = get_teaching_mode_for_kp(knowledge_point_type)
    mode_config = TEACHING_MODE_CONFIGS.get(mode_type)
    
    # 获取教学模式说明
    mode_section = get_mode_prompt_section(mode_type)
    
    # 获取教学策略
    if mode_config:
        strategy = mode_config.learner_type_strategies.get(
            learner_type, 
            "标准教学流程"
        )
    else:
        strategy = "标准教学流程"
    
    # 获取当前阶段
    current_phase_config = None
    total_phases = 4
    if mode_config:
        total_phases = len(mode_config.phases)
        for p in mode_config.phases:
            if p.order == current_phase:
                current_phase_config = p
                break
    
    phase_section = ""
    if current_phase_config:
        phase_section = get_phase_prompt_section(current_phase_config)
    
    # 获取常见错误
    common_errors = ""
    if mode_config and mode_config.common_errors:
        common_errors = f"""
常见错误：
{chr(10).join(['- ' + e for e in mode_config.common_errors])}
"""

    # 根据阶段生成不同的输出指引
    phase_output_guide = get_phase_output_guide(current_phase, current_phase_config, total_phases)
    
    # 根据阶段序号和总阶段数决定 next_action
    next_action = "next_phase" if current_phase < total_phases else "start_assessment"
    
    # 准备历史学习记录部分
    history_section = ""
    if history_summary:
        history_section = f"""【历史学习记录】
{history_summary}
"""
    
    # 准备学习轮次描述
    round_desc = "（首次学习）" if learning_round == 1 else "（重新学习，之前评估未通过，需要针对性复习）"

    return f"""【教学任务】
请为学生讲解知识点：{knowledge_point_name}

【知识点信息】
- 编号：{knowledge_point_id}
- 类型：{knowledge_point_type}
- 描述：{description}
- 核心要点：{key_points}
- 前置知识：{dependencies}

【学生情况】
- 学生姓名：{student_name}
- 学习者类型：{learner_type}
- 历史学习次数：第{attempt_count}次
- 当前学习轮次：第{learning_round}轮{round_desc}
{attempt_info}
{history_section}
{mode_section}

【当前教学进度】
正在执行第 {current_phase}/{total_phases} 阶段

{phase_section}

【教学策略】
{strategy}
{common_errors}

【教学要求】
{teaching_requirements}

【重要规则 - 分阶段教学】
1. 你现在只执行第{current_phase}阶段的教学内容
2. 【关键】每个阶段必须包含一个提问，让学生回答
3. 有提问时，next_action 必须设为 "wait_for_student"，等待学生回答
4. 学生回答后，系统会自动进入下一阶段
5. 不要一次性输出所有阶段的内容

{phase_output_guide}

【返回格式 - 边讲边写模式】
请严格按照以下JSONL格式输出，每行一个独立的JSON对象：

{{"type":"segment","message":"教学内容...","whiteboard":{{"title":"标题"}}}}
{{"type":"segment","message":"教学内容...","whiteboard":{{"points":["要点1","要点2"]}}}}
{{"type":"segment","message":"提问内容...","whiteboard":{{}},"is_question":true}}
{{"type":"complete","next_action":"wait_for_student"}}

【输出规则】
1. 必须使用"边讲边写"模式：每句话搭配相应的白板内容
2. whiteboard字段可以包含：title, points, formulas, examples, notes
3. 每个segment只包含当前段话相关的白板内容，不要重复之前的内容
4. 公式使用纯LaTeX格式，例如：y = kx + b
5. 【必须】每个阶段结尾要有提问，next_action 设为 "wait_for_student"
6. 每行必须是合法的JSON

{get_mode_specific_requirements(mode_type)}

请开始输出第{current_phase}阶段的内容："""


def get_teaching_requirements(
    kp_type: str,
    attempt_count: int,
    last_error_type: str = "",
    learner_type: str = "intermediate",
) -> str:
    """Generate teaching requirements based on context.

    Args:
        kp_type: Knowledge point type (概念/公式/技能).
        attempt_count: Number of learning attempts.
        last_error_type: Error type from last attempt.
        learner_type: Learner type (novice/intermediate/reviewer/advanced).

    Returns:
        Formatted teaching requirements string.
    """
    requirements = []
    
    # 根据教学模式类型添加基础要求
    mode_type = get_teaching_mode_for_kp(kp_type)
    
    if mode_type == TeachingModeType.CONCEPT_CONSTRUCTION:
        requirements.append("从具体实例出发，引导学生归纳概念")
        requirements.append("提供正例和反例，帮助学生辨析")
        if kp_type == "公式":
            requirements.append("解释公式中各符号的含义和取值范围")
            requirements.append("演示公式的代入计算")
    elif mode_type == TeachingModeType.PROCEDURAL_SKILL:
        requirements.append("将操作分解为清晰的步骤")
        requirements.append("每步提供即时反馈")
        requirements.append("强调关键步骤和易错点")
    
    # 根据学习者类型调整
    learner_strategies = {
        "novice": ["这是学生首次学习，请详细讲解", "提供更多示例", "分步引导"],
        "intermediate": ["使用引导发现的方法", "让学生自主归纳"],
        "reviewer": ["重点回顾关键概念", "辨析练习"],
        "advanced": ["应用拓展", "举一反三", "让学生教别人"],
    }
    
    if learner_type in learner_strategies:
        requirements.extend(learner_strategies[learner_type])
    
    # 根据尝试次数调整
    if attempt_count >= 2:
        requirements.append(f"学生已学习{attempt_count}次，请用更简洁的方式总结要点")
        if last_error_type:
            requirements.append(f"学生上次在「{last_error_type}」方面有困难，请重点讲解")
    
    return "\n".join([f"{i + 1}. {r}" for i, r in enumerate(requirements)])


# 保留旧的常量以兼容
TEACHING_PROMPT = """【教学任务】
请为学生讲解知识点：{knowledge_point_name}

【知识点信息】
- 编号：{knowledge_point_id}
- 类型：{knowledge_point_type}（概念/公式/技能）
- 描述：{description}
- 核心要点：{key_points}
- 前置知识：{dependencies}

【学生情况】
- 学生姓名：{student_name}
- 学习次数：第{attempt_count}次
{attempt_info}

【教学要求】
{teaching_requirements}

【返回格式 - 边讲边写模式】
请严格按照以下JSONL格式输出，实现"边说边展示"的效果。每行一个独立的JSON对象：

{{"type":"segment","message":"引入内容（20-30字，联系已学知识或生活实例）","whiteboard":{{"title":"知识点标题"}}}}

{{"type":"segment","message":"定义/概念解释（40-60字）","whiteboard":{{"points":["核心要点1","核心要点2"]}}}}

{{"type":"segment","message":"公式或关键内容说明（30-50字）","whiteboard":{{"formulas":["公式（LaTeX格式）"]}}}}

{{"type":"segment","message":"示例讲解（40-60字，结合公式演示）","whiteboard":{{"examples":["示例1","示例2"]}}}}

{{"type":"segment","message":"总结归纳（20-30字）","whiteboard":{{"notes":["注意事项"]}}}}

{{"type":"segment","message":"提问（15-25字，检查学生理解）","whiteboard":{{}},"is_question":true}}

{{"type":"complete","next_action":"wait_for_student"}}

【输出规则】
1. 必须使用"边讲边写"模式：每句话搭配相应的白板内容
2. whiteboard字段可以包含：title, points, formulas, examples, notes
3. points/formulas/examples/notes 都是数组格式，可以添加多个
4. 每个segment只包含当前段话相关的白板内容，不要重复之前的内容
5. 公式使用纯LaTeX格式，不要加$符号，例如：y = kx + b
6. 必须包含提问环节
7. next_action 固定为 "wait_for_student"
8. 每行必须是合法的JSON，不要有多余逗号或换行

请开始输出："""

CONCEPT_TEACHING_PROMPT = """【概念讲解专项要求】

讲解概念类知识点时，请遵循以下原则：

1. 从具体到抽象
   - 先给出生活实例或已学知识的联系
   - 再抽象出数学概念

2. 强调本质特征
   - 指出概念的核心要素
   - 区分易混淆的概念

3. 正反例对比
   - 给出符合概念的例子
   - 给出不符合概念的例子
   - 引导学生辨别

4. 检查理解
   - 让学生用自己的话复述概念
   - 或让学生举一个例子"""

FORMULA_TEACHING_PROMPT = """【公式讲解专项要求】

讲解公式类知识点时，请遵循以下原则：

1. 公式的来源（可选）
   - 简要说明公式的推导过程
   - 或直接给出公式

2. 符号含义
   - 逐个解释公式中各符号的含义
   - 说明各符号的取值范围

3. 适用条件
   - 明确公式的适用范围
   - 指出特殊情况

4. 使用示例
   - 演示如何代入计算
   - 至少给出1-2个例子

5. 记忆技巧
   - 提供记忆公式的方法
   - 或指出易错点"""

SKILL_TEACHING_PROMPT = """【技能讲解专项要求】

讲解技能类知识点时，请遵循以下原则：

1. 分步骤讲解
   - 将技能分解为具体步骤
   - 每步用简洁的语言说明

2. 边讲边演示
   - 配合白板展示
   - 关键步骤标注说明

3. 强调要点
   - 指出每步的注意事项
   - 提示常见错误

4. 练习巩固
   - 讲解后立即让学生尝试
   - 从简单到复杂"""


def generate_personalized_teaching_prompt(
    knowledge_point_name: str,
    knowledge_point_id: str,
    knowledge_point_type: str,
    description: str,
    key_points: str,
    dependencies: str,
    student_name: str,
    # 学习者画像数据
    learner_type: str = "intermediate",
    learner_type_description: str = "有基础者：前置知识充足，但未学习过当前知识点",
    prerequisite_mastery: float = 0.0,
    current_kp_mastery: float = 0.0,
    learning_velocity: float = 0.5,
    average_score: float = 0.0,
    dominant_error_pattern: Optional[str] = None,
    teaching_requirements: Optional[list[str]] = None,
    # 教学策略数据
    primary_strategy: str = "知识讲解+引导发现",
    example_count: int = 2,
    practice_count: int = 3,
    hint_level: int = 2,
    pacing: str = "normal",
    focus_areas: Optional[list[str]] = None,
    # 其他参数
    attempt_count: int = 1,
    attempt_info: str = "",
    current_phase: int = 1,
) -> str:
    """
    生成个性化教学Prompt（集成学习者画像数据）
    
    Args:
        knowledge_point_name: 知识点名称
        knowledge_point_id: 知识点ID
        knowledge_point_type: 知识点类型
        description: 描述
        key_points: 核心要点
        dependencies: 前置知识
        student_name: 学生姓名
        learner_type: 学习者类型 (novice/intermediate/reviewer/advanced)
        learner_type_description: 学习者类型描述
        prerequisite_mastery: 前置知识掌握度 (0.0-1.0)
        current_kp_mastery: 当前知识点掌握度 (0.0-1.0)
        learning_velocity: 学习速度 (0.0-1.0)
        average_score: 平均得分 (0.0-1.0)
        dominant_error_pattern: 主要错误模式
        teaching_requirements: 教学要求列表
        primary_strategy: 主要教学策略
        example_count: 示例数量
        practice_count: 练习数量
        hint_level: 提示级别 (1-3)
        pacing: 教学节奏 (slow/normal/fast)
        focus_areas: 重点领域
        attempt_count: 学习次数
        attempt_info: 尝试信息
        current_phase: 当前阶段
        
    Returns:
        生成的教学Prompt
    """
    # 根据知识点类型选择教学模式
    mode_type = get_teaching_mode_for_kp(knowledge_point_type)
    mode_config = TEACHING_MODE_CONFIGS.get(mode_type)
    
    # 获取教学模式说明
    mode_section = get_mode_prompt_section(mode_type)
    
    # 获取当前阶段配置
    current_phase_config = None
    total_phases = 4
    if mode_config:
        total_phases = len(mode_config.phases)
        for p in mode_config.phases:
            if p.order == current_phase:
                current_phase_config = p
                break
    
    phase_section = ""
    if current_phase_config:
        phase_section = get_phase_prompt_section(current_phase_config)
    
    # 格式化教学要求
    if teaching_requirements:
        requirements_text = "\n".join([f"- {r}" for r in teaching_requirements])
    else:
        requirements_text = "按照标准教学流程进行"
    
    # 格式化重点领域
    if focus_areas:
        focus_text = "、".join(focus_areas)
    else:
        focus_text = "理解核心概念"
    
    # 学习速度描述
    velocity_text = "正常"
    if learning_velocity < 0.5:
        velocity_text = "较慢"
    elif learning_velocity > 0.8:
        velocity_text = "较快"
    
    # 节奏描述
    pacing_text = {
        "slow": "慢节奏，给学生充分时间理解",
        "normal": "正常节奏",
        "fast": "快节奏，高效讲解",
    }.get(pacing, "正常节奏")
    
    # 提示级别描述
    hint_text = {
        1: "少量提示，鼓励学生自主思考",
        2: "适度提示，在关键点给予引导",
        3: "详细提示，充分支持和帮助",
    }.get(hint_level, "适度提示")
    
    # 错误模式描述
    error_pattern_text = ""
    if dominant_error_pattern:
        error_descriptions = {
            "concept_misunderstanding": "概念理解错误",
            "calculation_error": "计算错误",
            "procedure_error": "步骤/程序错误",
            "careless_error": "粗心大意",
            "incomplete_answer": "答题不完整",
            "prerequisite_gap": "前置知识缺失",
        }
        error_pattern_text = error_descriptions.get(
            dominant_error_pattern, dominant_error_pattern
        )
    
    # 阶段输出指引
    phase_output_guide = get_phase_output_guide(current_phase, current_phase_config, total_phases)
    
    # 模式特殊要求
    mode_requirements = get_mode_specific_requirements(mode_type)
    
    return f"""【教学任务】
请为学生讲解知识点：{knowledge_point_name}

【知识点信息】
- 编号：{knowledge_point_id}
- 类型：{knowledge_point_type}
- 描述：{description}
- 核心要点：{key_points}
- 前置知识：{dependencies}

【学生画像】
- 学生姓名：{student_name}
- 学习者类型：{learner_type}
- 类型描述：{learner_type_description}
- 前置知识掌握度：{prerequisite_mastery:.0%}
- 当前知识点掌握度：{current_kp_mastery:.0%}
- 学习速度：{velocity_text}
- 平均得分：{average_score:.0%}
- 主要错误模式：{error_pattern_text or '无'}
- 学习次数：第{attempt_count}次
{attempt_info}

{mode_section}

【当前教学进度】
正在执行第 {current_phase}/{total_phases} 阶段

{phase_section}

【个性化教学策略】
- 主要策略：{primary_strategy}
- 示例数量：{example_count}个
- 练习数量：{practice_count}道
- 提示级别：{hint_text}
- 教学节奏：{pacing_text}
- 重点领域：{focus_text}

【教学要求】
{requirements_text}

【重要规则 - 分阶段教学】
1. 你现在只执行第{current_phase}阶段的教学内容
2. 【关键】每个阶段必须包含一个提问，让学生回答
3. 有提问时，next_action 必须设为 "wait_for_student"，等待学生回答
4. 学生回答后，系统会自动进入下一阶段
5. 不要一次性输出所有阶段的内容

{phase_output_guide}

【返回格式 - 边讲边写模式】
请严格按照以下JSONL格式输出，每行一个独立的JSON对象：

{{"type":"segment","message":"教学内容...","whiteboard":{{"title":"标题"}}}}
{{"type":"segment","message":"教学内容...","whiteboard":{{"points":["要点1","要点2"]}}}}
{{"type":"segment","message":"提问内容...","whiteboard":{{}},"is_question":true}}
{{"type":"complete","next_action":"wait_for_student"}}

【输出规则】
1. 必须使用"边讲边写"模式：每句话搭配相应的白板内容
2. whiteboard字段可以包含：title, points, formulas, examples, notes
3. 每个segment只包含当前段话相关的白板内容，不要重复之前的内容
4. 公式使用纯LaTeX格式，例如：y = kx + b
5. 【必须】每个阶段结尾要有提问，next_action 设为 "wait_for_student"
6. 每行必须是合法的JSON

{mode_requirements}

请开始输出第{current_phase}阶段的内容："""
