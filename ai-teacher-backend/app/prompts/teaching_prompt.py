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


def get_phase_output_guide(phase: int, phase_config: Optional[TeachingPhase], total_phases: int = 4) -> str:
    """获取当前阶段的输出指引"""
    if not phase_config:
        return f"执行第{phase}阶段的教学内容"

    phase_name = phase_config.name
    activities = phase_config.activities
    activities_text = " → ".join(activities)

    guides = {
        1: f"""
【阶段{phase}：{phase_name}】输出要求：
- 本阶段活动：{activities_text}
- 输出内容：情境引入、展示问题、激发兴趣
- 结尾：提出引导性问题，让学生思考或预测
""",
        2: f"""
【阶段{phase}：{phase_name}】输出要求：
- 本阶段活动：{activities_text}
- 输出内容：详细讲解、示例演示、学生操作
- 结尾：确认学生是否理解，或提出练习问题
""",
        3: f"""
【阶段{phase}：{phase_name}】输出要求：
- 本阶段活动：{activities_text}
- 输出内容：辨析练习、深化理解、错误诊断
- 结尾：让学生用自己的话解释或举例子
""",
        4: f"""
【阶段{phase}：{phase_name}】输出要求：
- 本阶段活动：{activities_text}
- 输出内容：综合练习、巩固应用、总结归纳
- 结尾：提问检查整体理解程度
""",
    }

    return guides.get(phase, f"执行{phase_name}的内容")


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

【返回格式 - 边讲边写模式 + HTML增强】
请严格按照以下JSONL格式输出，每行一个独立的JSON对象：

{{"type":"segment","message":"教学内容...","whiteboard":{{"title":"标题"}}}}
{{"type":"segment","message":"教学内容...","whiteboard":{{"points":["要点1","要点2"]}}}}
{{"type":"segment","message":"需要配图说明的内容","whiteboard":{{}},"need_image":{{"concept":"精确描述你想要画什么样的图片，不要产出模糊的描述，例如：y=2x+1的图片，要展示截距/斜率等重要信息","animation_type":"auto","output_format":"image"}}}}
{{"type":"segment","message":"需要动画演示的内容","whiteboard":{{}},"need_image":{{"concept":"精确描述你想要画什么样的动画，不要产出模糊的描述，例如：希望展示函数变换的过程，对y=2x+1的图像先左右再上下平移3个单位","animation_type":"auto","output_format":"video"}}}}
{{"type":"segment","message":"提问内容...","whiteboard":{{}},"is_question":true}}
{{"type":"complete","next_action":"wait_for_student"}}

【HTML增强输出（强烈推荐使用）】
这是本系统的核心特色。对于每个教学segment，强烈推荐同时输出whiteboard_html字段，
用语义HTML实现丰富、美观的视觉呈现。

**设计风格：Dark Academia · 编辑式排版**
- 教育性、庄重、有质感的视觉风格
- 字体层次丰富：标题用衬线（h1-h4），正文用无衬线，公式用等宽字体
- 色彩以深黑底 + 冷调石板蓝绿（sage/slate）为主色系，避免刺眼的亮色
- 每个组件都有精心设计的边角装饰和过渡动画

**核心原则：**只写结构HTML（div/span/class），不写内联style，不写JS**。

【可用视觉组件速查表】
系统内置20+种CSS组件，LLM只需添加对应class名即可使用：

1. 知识卡片网格 — 展示多个相关概念/公式/示例
   card-grid > knowledge-card (concept|formula|example|warning|tip)
   > card-icon(emoji) + card-title + card-body + card-tag

2. 对比面板 — 两个概念的并排对比
   comparison > compare-a + compare-b
   > compare-title + compare-item(> compare-label + compare-value-a/b)

3. 进度条 — 展示掌握程度/进度
   progress-container > progress-label + progress-bar > progress-fill (low|medium|high|full)

4. 时间线 — 展示步骤/过程/历史
   timeline > tl-item (active|done) > tl-title + tl-desc

5. 标签系统
   tag (blue|green|yellow|red|purple|cyan)

6. 公式聚光灯 — 突出显示核心公式
   formula-spotlight > formula-label + formula-main + formula-note

7. 记忆口诀 — 助记技巧
   mnemonic > mne-title + mne-text + mne-rhyme

8. 流程图（水平）
   flow-diagram > flow-step(> flow-label + flow-desc) + flow-arrow(→) ...

9. 垂直流程图
   vflow > vflow-step(> vflow-num + vflow-body(> vflow-title + vflow-desc))

10. 迷你测验 — 选择题预览
    quiz-box > quiz-q + quiz-opt (correct|wrong)

11. 要点洞察框
    key-insight > ki-icon(emoji) + ki-body(> ki-title + ki-text)

12. 数字统计数据面板
    stat-row > stat-item(> stat-value + stat-label)

13. 示例框
    example-box > ex-title + ex-body + ex-solution

14. 错误诊断框
    error-box > err-title + err-body + err-fix

15. 基础：table / callout (info|warn|tip|error) / definition (term+meaning)
    step-list (step-item > step-number + step-body(step-title+step-desc))
    highlight / blockquote / details+summary / pre+code / h1-h4

【组件使用示例 — 直接copy到whiteboard_html字段中】：

-- 示例1：知识卡片网格（展示3个关键点）--
<div class="card-grid">
  <div class="knowledge-card concept">
    <div class="card-icon">🔑</div>
    <div class="card-title">斜率 k</div>
    <div class="card-body">决定直线的倾斜方向和程度，k>0递增，k<0递减</div>
    <span class="card-tag">核心概念</span>
  </div>
  <div class="knowledge-card formula">
    <div class="card-icon">📐</div>
    <div class="card-title">截距 b</div>
    <div class="card-body">直线与y轴的交点$(0,b)$，决定直线的上下位置</div>
    <span class="card-tag">重要参数</span>
  </div>
  <div class="knowledge-card tip">
    <div class="card-icon">💡</div>
    <div class="card-title">平移规律</div>
    <div class="card-body">上+下-，左+右-（注意平移方向对解析式的反直觉影响）</div>
    <span class="card-tag">记忆技巧</span>
  </div>
</div>

-- 示例2：对比面板（辨析两个概念）--
<div class="comparison">
  <div class="compare-a">
    <div class="compare-title">一次函数 $y=kx+b$</div>
    <div class="compare-item"><span class="compare-label">图像</span><span class="compare-value-a">一条直线</span></div>
    <div class="compare-item"><span class="compare-label">变化率</span><span class="compare-value-a">恒定（k）</span></div>
    <div class="compare-item"><span class="compare-label">定义域</span><span class="compare-value-a">全体实数</span></div>
  </div>
  <div class="compare-b">
    <div class="compare-title">二次函数 $y=ax^2$</div>
    <div class="compare-item"><span class="compare-label">图像</span><span class="compare-value-b">抛物线</span></div>
    <div class="compare-item"><span class="compare-label">变化率</span><span class="compare-value-b">变化（2ax）</span></div>
    <div class="compare-item"><span class="compare-label">定义域</span><span class="compare-value-b">全体实数</span></div>
  </div>
</div>

-- 示例3：公式聚光灯 + 记忆口诀--
<div class="formula-spotlight">
  <div class="formula-label">核心公式</div>
  <div class="formula-main">$$y = kx + b \quad (k \neq 0)$$</div>
  <div class="formula-note">k 决定倾斜方向与程度，b 决定与 y 轴的交点</div>
</div>
<div class="mnemonic">
  <div class="mne-title">🎯 记忆口诀</div>
  <div class="mne-text">"k定倾斜b定起，正增负减记心里"</div>
  <div class="mne-rhyme">k > 0 时向右上倾斜 ↗，k < 0 时向右下倾斜 ↘</div>
</div>

-- 示例4：垂直流程图+进度条（展示掌握路径）--
<div class="progress-container">
  <div class="progress-label"><span>当前掌握进度</span><span>70%</span></div>
  <div class="progress-bar"><div class="progress-fill medium" style="width:70%">中级</div></div>
</div>
<div class="vflow">
  <div class="vflow-step">
    <div class="vflow-num">1</div>
    <div class="vflow-body"><div class="vflow-title">认识一次函数</div><div class="vflow-desc">理解 $y=kx+b$ 的形式和参数含义</div></div>
  </div>
  <div class="vflow-step">
    <div class="vflow-num">2</div>
    <div class="vflow-body"><div class="vflow-title">图像与性质</div><div class="vflow-desc">掌握k和b对图像的影响规律 ✓</div></div>
  </div>
  <div class="vflow-step">
    <div class="vflow-num">3</div>
    <div class="vflow-body"><div class="vflow-title">平移变换</div><div class="vflow-desc">理解平移对解析式的改写规则 ✓</div></div>
  </div>
</div>

-- 示例5：错误诊断+正解--
<div class="error-box">
  <div class="err-title">常见错误</div>
  <div class="err-body">认为"直线向上平移3个单位"就是 $y=kx+b+3$，但忽略了平移对自变量x的影响。</div>
  <div class="err-fix">向左平移m个单位应替换 x→(x+m)，即 $y=k(x+m)+b$；向右平移则替换 x→(x-m)</div>
</div>

-- 示例6：统计面板+时间线--
<div class="stat-row">
  <div class="stat-item"><div class="stat-value">3</div><div class="stat-label">核心概念</div></div>
  <div class="stat-item"><div class="stat-value">2</div><div class="stat-label">变换规则</div></div>
  <div class="stat-item"><div class="stat-value">85%</div><div class="stat-label">典型正确率</div></div>
</div>

-- 示例7：要点洞察+标签--
<div class="key-insight">
  <div class="ki-icon">🎯</div>
  <div class="ki-body">
    <div class="ki-title">核心洞见</div>
    <div class="ki-text">一次函数的"变"与"不变"：平移改变的是截距 <span class="tag blue">b</span>，斜率的绝对值 <span class="tag green">|k|</span> 始终不变！</div>
  </div>
</div>

-- 示例8：选择题预览--
<div class="quiz-box">
  <div class="quiz-q">直线 $y=2x+3$ 向下平移2个单位后，解析式是？</div>
  <div class="quiz-opt wrong">$y=2x+1$</div>
  <div class="quiz-opt correct">$y=2x+1$ ✓</div>
  <div class="quiz-opt">$y=2x+5$</div>
  <div class="quiz-opt">$y=2(x-2)+3$</div>
</div>

-- 示例9：交互选择题（点击选项看反馈）--
<div class="interactive-quiz">
  <div class="quiz-question">直线 $y=3x-2$ 向右平移4个单位后的解析式是？</div>
  <div class="quiz-option" data-correct>$y=3(x-4)-2$</div>
  <div class="quiz-option">$y=3(x+4)-2$</div>
  <div class="quiz-option">$y=3x+2$</div>
</div>

-- 示例10：点击揭示答案 --
<div class="interactive-reveal">
  <div class="reveal-question">将 $y=-2x+5$ 先向左平移3个单位，再向下平移1个单位</div>
  <div class="reveal-hint">💡 先处理左右平移（对x操作），再处理上下平移（对常数操作）</div>
  <div class="reveal-answer"><div class="reveal-answer-content">$y = -2(x+3) + 5 - 1 = -2x - 6 + 4 = -2x - 2$</div></div>
</div>

-- 示例11：逐步揭示解题步骤 --
<div class="interactive-steps">
  <div class="step-header">📋 解题步骤（点击每步可展开下一步）</div>
  <div class="step" data-step="1">第一步：判断平移方向 → 左移3，下移1</div>
  <div class="step" data-step="2" data-hidden>第二步：左移对x操作 → x变成(x+3)</div>
  <div class="step" data-step="3" data-hidden>第三步：下移对b操作 → b变成5-1=4</div>
  <div class="step" data-step="4" data-hidden>第四步：代入化简 → y = -2(x+3) + 4 = -2x - 2</div>
</div>

-- 示例12：翻转卡片 --
<div class="interactive-flip">
  <div class="flip-inner">
    <div class="flip-front">
      <div class="flip-icon">❓</div>
      <div class="flip-label">点击翻转</div>
      <div class="flip-text">一次函数平移的口诀是？</div>
    </div>
    <div class="flip-back">
      <div class="flip-icon">💡</div>
      <div class="flip-label">答案</div>
      <div class="flip-text">上加下减，左加右减（对x操作）</div>
    </div>
  </div>
</div>

-- 示例13：选项卡 --
<div class="interactive-tabs">
  <div class="tab-bar">
    <span class="tab-trigger active" data-tab="concept">📖 概念</span>
    <span class="tab-trigger" data-tab="rule">📐 规律</span>
    <span class="tab-trigger" data-tab="example">📝 示例</span>
  </div>
  <div class="tab-panel active" data-tab="concept">平移是指函数图像在坐标系中沿某个方向移动，不改变图像的形状和倾斜程度。</div>
  <div class="tab-panel" data-tab="rule" data-hidden>上移+b、下移-b、左移对x加、右移对x减。平移不改变斜率k。</div>
  <div class="tab-panel" data-tab="example" data-hidden>$y=2x+1$ 右移2 → $y=2(x-2)+1=2x-3$</div>
</div>

【交互组件使用说明】
以上示例（9-13）中的组件是真正的交互式组件，学生可以在白板上点击操作：
- interactive-quiz：点击选项 → 自动判断对错，显示反馈文字 ✓/✗
- interactive-reveal：点击方块 → 平滑展开显示隐藏答案，再点击收回
- interactive-steps：点击每一步 → 展开下一步，逐步引导思考
- interactive-flip：点击卡片 → 3D翻转显示背面答案
- interactive-tabs：点击标签 → 切换不同面板内容
推荐在"提问"或"练习"环节使用这些交互组件来增强学生的参与感。

-- 示例14：杂志式不对称网格 --
<div class="magazine-grid">
  <div class="mg-lead">
    <div class="mg-label">核心概念</div>
    <div class="mg-title">平移的本质：坐标变换</div>
    <div class="mg-body">平移不是改变函数本身，而是改变自变量 x 或因变量 y 的"参照系"。就像在地图上移动一个点，点本身没变，但它的坐标变了。</div>
  </div>
  <div class="mg-secondary">
    <div class="mg-subtitle">上下平移</div>
    <div class="mg-subbody">对 y 操作：$y = kx + (b \pm n)$，直线上下滑动，斜率不变</div>
  </div>
  <div class="mg-secondary">
    <div class="mg-subtitle">左右平移</div>
    <div class="mg-subbody">对 x 操作：$y = k(x \mp m) + b$，注意方向与直觉相反</div>
  </div>
</div>

-- 示例15：拉引文（大号排版元素）--
<div class="pull-quote">
  <span class="pq-mark">"</span>
  <div class="pq-text">平移不改变直线的「倾斜程度」——斜率 k 是平移变换下的不变量</div>
  <div class="pq-attribution">一次函数核心规律</div>
</div>

-- 示例16：斜角卡片 --
<div class="slant-box">
  <div class="s-title">💡 记忆技巧</div>
  <div class="s-body">"左加右减"是针对 x 的变换——向左平移 x 要加上移动量，因为新位置在原位置的左边，需要加到原来的 x 上才能到达相同 y。</div>
</div>

-- 示例17：重叠统计 --
<div class="overlap-stats">
  <div class="os-item"><div class="os-value">4</div><div class="os-label">平移方向</div></div>
  <div class="os-item"><div class="os-value">2</div><div class="os-label">操作对象</div></div>
  <div class="os-item"><div class="os-value">1</div><div class="os-label">不变量(k)</div></div>
</div>

-- 示例18：斜线分割对比 --
<div class="diagonal-compare">
  <div class="dc-side">
    <div class="dc-title">平移前 $y=2x+1$</div>
    <div class="dc-item"><span class="dc-label">斜率</span><span class="dc-val">k=2</span></div>
    <div class="dc-item"><span class="dc-label">y截距</span><span class="dc-val">b=1</span></div>
  </div>
  <div class="dc-side">
    <div class="dc-title">右移2后</div>
    <div class="dc-item"><span class="dc-label">斜率</span><span class="dc-val">k=2（不变）</span></div>
    <div class="dc-item"><span class="dc-label">新解析式</span><span class="dc-val">$y=2x-3$</span></div>
  </div>
</div>

-- 示例19：知识阶梯（台阶式布局）--
<div class="knowledge-steps">
  <div class="ks-step"><div class="ks-num">1</div><div class="ks-body"><div class="ks-title">判断方向</div><div class="ks-desc">上/下？左/右？</div></div></div>
  <div class="ks-step"><div class="ks-num">2</div><div class="ks-body"><div class="ks-title">确定操作对象</div><div class="ks-desc">上下→b，左右→x</div></div></div>
  <div class="ks-step"><div class="ks-num">3</div><div class="ks-body"><div class="ks-title">代入变换公式</div><div class="ks-desc">上加下减 / 左加右减</div></div></div>
  <div class="ks-step"><div class="ks-num">4</div><div class="ks-body"><div class="ks-title">化简验证</div><div class="ks-desc">检查斜率k不变</div></div></div>
</div>

【新布局组件速查】
以上示例（14-19）展示了全新的非矩形、非对称的排版模式：
- magazine-grid：左大右小的杂志式不对称网格，适合"主概念+辅助要点"
- pull-quote：大号引文排版，适合核心规律的强调展示
- slant-box：clip-path 斜角卡片，hover 时还原为矩形
- overlap-stats：元素重叠的统计面板，有 Z 轴层次感
- diagonal-compare：斜线分割的对比面板，比垂直分割更有动感
- knowledge-steps：台阶式布局，每级递增左缩进，适合递进式内容

【组件组合技巧】
- 可以将多个组件自由组合：card-grid + callout + table + formula-spotlight
- 同一segment的HTML应围绕同一知识点组织
- 为每段教学内容选择最适合的视觉呈现方式，而不是全部用段落

【依然需要保留 message 字段】message仍提供纯文本版本，可作为辅助朗读文本。

【输出规则】
1. 必须使用"边讲边写"模式：每句话搭配相应的白板内容
2. whiteboard字段可以包含：title, points, formulas, examples, notes；也可用 whiteboard_html 字段输出语义HTML版本
3. 每个segment只包含当前段话相关的白板内容，不要重复之前的内容
4. 公式使用纯LaTeX格式，例如：y = kx + b
5. 【必须】每个阶段结尾要有提问，next_action 设为 "wait_for_student"
6. 每行必须是合法的JSON
7. 当教学内容涉及函数图像、几何图形、数学证明等需要可视化展示的内容时，请使用need_image字段请求生成图片或视频
8. need_image字段说明：
   - concept（必填）：描述需要展示的概念，要具体明确（如"一次函数y=2x+1的图像"）
   - animation_type：固定填"auto"，系统会自动选择最佳展示方式
   - output_format："image"为静态图片，"video"为动画视频
   - concept内容要清晰完整，系统会用它来生成对应的可视化内容

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
2. whiteboard字段可以包含：title, points, formulas, examples, notes；也可用 whiteboard_html 字段输出语义HTML版本
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
2. whiteboard字段可以包含：title, points, formulas, examples, notes；也可用 whiteboard_html 字段输出语义HTML版本
3. 每个segment只包含当前段话相关的白板内容，不要重复之前的内容
4. 公式使用纯LaTeX格式，例如：y = kx + b
5. 【必须】每个阶段结尾要有提问，next_action 设为 "wait_for_student"
6. 每行必须是合法的JSON

{mode_requirements}

请开始输出第{current_phase}阶段的内容："""
