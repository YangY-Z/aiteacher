"""Teaching prompts for knowledge point explanation."""

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

【返回格式】（请严格按照此JSON格式返回，不要添加任何其他文字）
{{
    "response_type": "讲解",
    "content": {{
        "introduction": "引入（20-30字）：联系已学知识或生活实例",
        "definition": "定义/公式（40-60字）：清晰给出核心内容",
        "example": "示例（30-50字）：举例说明",
        "question": "提问（15-25字）：检查学生理解的问题",
        "summary": "总结（20-30字）：归纳要点"
    }},
    "whiteboard": {{
        "title": "{knowledge_point_name}",
        "key_points": ["要点1", "要点2", "要点3"],
        "formulas": ["公式1（LaTeX格式）", "公式2（LaTeX格式）"],
        "examples": ["示例说明"],
        "notes": ["注意事项或易错点"]
    }},
    "next_action": "wait_for_student"
}}

【白板内容说明】
whiteboard字段是展示在黑板上的内容，会累积展示，请认真填写：
- title: 知识点标题
- key_points: 核心要点列表（2-4条，每条10-20字）
- formulas: 公式列表，每条公式使用纯LaTeX格式（不要加$符号），例如：
  - "y = kx + b" （一次函数）
  - "C = 2\\pi r" （圆周长）
  - "x = \\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}" （求根公式）
- examples: 典型示例（1-2个），如需包含公式，用 $公式$ 格式
- notes: 注意事项或易错点（1-2条）

【重要说明】
1. question 字段必须填写，用于引导学生互动
2. next_action 固定返回 "wait_for_student"，等待学生回复后再决定下一步
3. 学生回复后，系统会智能判断是否可以开始测试

请直接返回JSON，不要包含```json```标记"""

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


def get_teaching_requirements(
    kp_type: str,
    attempt_count: int,
    last_error_type: str = "",
) -> str:
    """Generate teaching requirements based on context.

    Args:
        kp_type: Knowledge point type (概念/公式/技能).
        attempt_count: Number of learning attempts.
        last_error_type: Error type from last attempt.

    Returns:
        Formatted teaching requirements string.
    """
    requirements = []

    # Base requirements by type
    if kp_type == "概念":
        requirements.append("讲清概念的定义和内涵")
        requirements.append("用生活实例帮助学生理解")
    elif kp_type == "公式":
        requirements.append("说明公式中各符号的含义")
        requirements.append("强调公式的适用条件")
        requirements.append("演示公式的使用方法")
    else:  # 技能
        requirements.append("分步骤讲解操作方法")
        requirements.append("边讲边演示")

    # Adjust based on attempt count
    if attempt_count == 1:
        requirements.append("这是学生首次学习，请详细讲解")
    elif attempt_count == 2:
        if last_error_type:
            requirements.append(f"学生上次在{last_error_type}方面有困难，请重点讲解")
        requirements.append("使用与上次不同的讲解方式")
    else:
        requirements.append("学生多次学习仍有困难，请用最简洁的方式总结要点")
        requirements.append("增加练习题帮助学生建立信心")

    return "\n".join([f"{i + 1}. {r}" for i, r in enumerate(requirements)])