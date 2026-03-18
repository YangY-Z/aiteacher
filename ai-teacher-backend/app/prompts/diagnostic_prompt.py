"""Diagnostic prompts for pre-class assessment."""

DIAGNOSTIC_QUESTION_PROMPT = """【诊断题目生成任务】
请为知识点"{kp_name}"生成{question_count}道诊断题。

【知识点信息】
- 编号：{kp_id}
- 类型：{kp_type}
- 描述：{description}
- 题目类别：{category_text}

【题型要求】
请生成以下题型的题目：
1. 选择题（choice）：提供4个选项，正确答案为选项字母（A/B/C/D）
2. 输入题（input）：学生需要输入数值或文本答案
3. 点击题（point_click）：学生需要在坐标系中点击特定位置

【题目设计原则】
1. 前置知识检测题（prerequisite）：
   - 检查学生是否已掌握本知识点的前置知识
   - 题目应该简洁直接，能快速判断掌握程度
   - 避免综合性强的题目

2. 目标知识检测题（target）：
   - 检查学生对本知识点的初步了解程度
   - 题目应是基础知识点的直接应用
   - 难度为基础或中等

【返回格式】请严格按照以下JSON格式输出（不要添加```标记）：
{{
  "questions": [
    {{
      "question_type": "choice",
      "content": "题目内容",
      "options": ["选项A内容", "选项B内容", "选项C内容", "选项D内容"],
      "correct_answer": "A",
      "explanation": "答案解析"
    }},
    {{
      "question_type": "input",
      "content": "题目内容，用____表示空缺",
      "correct_answer": "答案",
      "explanation": "答案解析"
    }},
    {{
      "question_type": "point_click",
      "content": "在坐标系中点击点(2, 3)的位置",
      "correct_answer": {{"x": 2, "y": 3}},
      "coordinate_range": {{"x_min": -5, "x_max": 5, "y_min": -5, "y_max": 5, "tolerance": 0.5}},
      "explanation": "答案解析"
    }}
  ]
}}

请开始生成："""

DIAGNOSTIC_RESULT_PROMPT = """【诊断结果分析任务】
请分析学生的诊断答题情况，给出诊断结论和学习建议。

【目标知识点】
- 名称：{target_kp_name}
- 类型：{target_kp_type}

【答题情况】
前置知识检测结果：
{prerequisite_results_text}

目标知识检测结果：
- 总题数：{target_total}
- 正确数：{target_correct}
- 正确率：{target_rate:.1%}

总体情况：
- 总题数：{total_questions}
- 正确数：{total_correct}
- 正确率：{overall_rate:.1%}

【诊断结论说明】
1. full_mastery（完全掌握）：前置知识全掌握 + 目标题全对，可跳过该知识点
2. partial_mastery（部分掌握）：前置知识全掌握 + 目标题部分对，需要快速复习
3. need_review（需要复习）：前置知识部分掌握，需要正常学习流程
4. full_learning（完全学习）：前置知识大部分未掌握，需要从头开始学习

【返回格式】请严格按照以下JSON格式输出（不要添加```标记）：
{{
  "conclusion": "full_mastery/partial_mastery/need_review/full_learning",
  "recommended_teaching_mode": "direct_teaching/guided_inquiry/practice_oriented/visual_analog/step_by_step/remedial",
  "summary": "一句话总结诊断结论和学习建议（30-50字）"
}}

请开始分析："""


def get_diagnostic_question_prompt(
    kp_id: str,
    kp_name: str,
    kp_type: str,
    description: str,
    question_count: int = 2,
    category: str = "target",
) -> str:
    """Generate the prompt for diagnostic question generation.

    Args:
        kp_id: Knowledge point ID.
        kp_name: Knowledge point name.
        kp_type: Knowledge point type (概念/公式/技能).
        description: Knowledge point description.
        question_count: Number of questions to generate.
        category: Question category (prerequisite/target).

    Returns:
        Formatted prompt string.
    """
    category_text = "前置知识检测题" if category == "prerequisite" else "目标知识基础检测题"

    return DIAGNOSTIC_QUESTION_PROMPT.format(
        kp_id=kp_id,
        kp_name=kp_name,
        kp_type=kp_type,
        description=description or "无详细描述",
        question_count=question_count,
        category_text=category_text,
    )


def get_diagnostic_result_prompt(
    target_kp_name: str,
    target_kp_type: str,
    prerequisite_results: list[dict],
    target_total: int,
    target_correct: int,
    total_questions: int,
    total_correct: int,
) -> str:
    """Generate the prompt for diagnostic result analysis.

    Args:
        target_kp_name: Target knowledge point name.
        target_kp_type: Target knowledge point type.
        prerequisite_results: List of prerequisite check results.
        target_total: Total target questions.
        target_correct: Correct target questions.
        total_questions: Total questions.
        total_correct: Total correct answers.

    Returns:
        Formatted prompt string.
    """
    # Format prerequisite results
    prereq_lines = []
    for result in prerequisite_results:
        status = "✓ 已掌握" if result.get("is_mastered") else "✗ 未掌握"
        prereq_lines.append(
            f"- {result.get('kp_name', '未知知识点')}: {status} "
            f"({result.get('questions_correct', 0)}/{result.get('questions_total', 0)})"
        )
    prerequisite_results_text = "\n".join(prereq_lines) if prereq_lines else "无前置知识要求"

    target_rate = target_correct / target_total if target_total > 0 else 0
    overall_rate = total_correct / total_questions if total_questions > 0 else 0

    return DIAGNOSTIC_RESULT_PROMPT.format(
        target_kp_name=target_kp_name,
        target_kp_type=target_kp_type,
        prerequisite_results_text=prerequisite_results_text,
        target_total=target_total,
        target_correct=target_correct,
        target_rate=target_rate,
        total_questions=total_questions,
        total_correct=total_correct,
        overall_rate=overall_rate,
    )


# 教学模式推荐规则
TEACHING_MODE_RECOMMENDATIONS = {
    "full_mastery": None,  # 跳过，不需要教学模式
    "partial_mastery": "direct_teaching",  # 直接教学法（快速复习）
    "need_review": "guided_inquiry",  # 引导探究法
    "full_learning": "step_by_step",  # 分步教学法
}

CONCLUSION_DESCRIPTIONS = {
    "full_mastery": "已完全掌握该知识点及其前置知识，可以直接进入下一知识点学习。",
    "partial_mastery": "前置知识已掌握，对目标知识有初步了解，建议进行快速复习巩固。",
    "need_review": "部分前置知识未掌握，建议按正常流程系统学习。",
    "full_learning": "前置知识基础较弱，建议从基础知识开始系统学习。",
}
