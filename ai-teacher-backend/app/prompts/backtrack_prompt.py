"""Backtrack decision prompt."""

BACKTRACK_DECISION_PROMPT = """【回溯决策任务】

学生当前正在学习"{current_kp_name}"，但表现不佳，请分析原因并决定是否需要回溯。

【当前知识点信息】
- 名称：{current_kp_name}
- 编号：{current_kp_id}
- 类型：{current_kp_type}
- 描述：{current_kp_description}

【学生表现】
- 错误类型：{error_type}
- 学生回答：{student_response}
- 错误次数：{error_count}

【前置知识点列表】
{dependencies_list}

【学生在各前置知识点的历史表现】
{dependency_performance}

【决策要求】
1. 分析学生的错误，判断根本原因
2. 检查是否与某个前置知识点掌握不牢有关
3. 决定是否需要回溯，以及回溯到哪个知识点

【输出格式】
请以JSON格式输出你的决策：
{
  "decision": "continue|backtrack",
  "reason": "决策理由",
  "error_root_cause": "错误根本原因分析",
  "backtrack_target": {
    "knowledge_point_id": "KXX",
    "knowledge_point_name": "知识点名称"
  },
  "teaching_adjustment": "针对当前情况的讲解调整建议"
}"""
