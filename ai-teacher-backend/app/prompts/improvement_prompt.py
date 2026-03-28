"""专项提升模块 prompt 模板。"""

IMPROVEMENT_DIAGNOSIS_PROMPT = """【专项提升诊断任务】
你是一名初中数学专项提升老师，当前只处理“一次函数”单元知识点。

【学生输入】
- 试卷/作业：{exam_name}
- 得分：{score}/{total_score}
- 错题描述/老师评语：{error_description}
- 可投入时间：{available_time} 分钟
- 期望难度：{difficulty}
- 自评基础：{foundation}

【历史掌握情况】
- 已掌握知识点：{mastered_kps}
- 未掌握候选知识点：{candidate_kps}

【候选知识点详细信息】
{candidate_details}

【要求】
1. 判断最可能的薄弱知识点
2. 如果信息不足，提出一个最关键的澄清问题
3. 必须只从 candidate_kps 中选择 target_knowledge_point_id
4. 输出严格 JSON，不要加 markdown 代码块

输出格式：
{{
  "need_clarification": true,
  "clarification_question": "你更容易错在图象判断还是解析式求解？",
  "target_knowledge_point_id": null,
  "confidence": 0.0,
  "reason": "信息不足，需要继续追问",
  "prerequisite_gaps": []
}}
或
{{
  "need_clarification": false,
  "clarification_question": "",
  "target_knowledge_point_id": "K15",
  "confidence": 0.82,
  "reason": "学生错误集中在一次函数基本定义与解析式理解",
  "prerequisite_gaps": ["K12", "K10"]
}}
"""

IMPROVEMENT_CLARIFICATION_PROMPT = """【专项提升追问后诊断任务】
你是一名初中数学专项提升老师。

【已有诊断背景】
- 试卷/作业：{exam_name}
- 得分：{score}/{total_score}
- 错题描述/老师评语：{error_description}
- 候选知识点：{candidate_kps}
- 当前追问：{current_question}
- 学生回答：{student_answer}

【候选知识点详细信息】
{candidate_details}

【要求】
1. 根据学生回答判断最可能的薄弱知识点
2. 如果仍无法判断，可以继续追问一个更具体的问题
3. target_knowledge_point_id 只能从 candidate_kps 中选择
4. 输出严格 JSON，不要加 markdown 代码块

输出格式：
{{
  "need_clarification": false,
  "clarification_question": "",
  "target_knowledge_point_id": "K18",
  "confidence": 0.79,
  "reason": "学生明确提到不会根据图象判断函数特征",
  "prerequisite_gaps": ["K15"]
}}
或
{{
  "need_clarification": true,
  "clarification_question": "如果给你图象，你更不确定斜率还是截距？",
  "target_knowledge_point_id": null,
  "confidence": 0.0,
  "reason": "仍需区分图象理解中的具体薄弱点",
  "prerequisite_gaps": []
}}
"""

IMPROVEMENT_PLAN_PROMPT = """【专项提升学习方案生成任务】
你是一名初中数学专项提升老师。

【目标知识点】
- 编号：{target_kp_id}
- 名称：{target_kp_name}
- 描述：{target_kp_description}
- 前置知识点：{prerequisite_names}

【学生情况】
- 可投入时间：{available_time} 分钟
- 期望难度：{difficulty}
- 自评基础：{foundation}
- 诊断原因：{reason}

【要求】
1. 生成 3-5 步学习方案
2. 每一步都要有 knowledge_point_id、goal、estimated_minutes
3. total_estimated_minutes 尽量接近 available_time，但不要超过太多
4. 可在第一步加入前置知识补缺
5. 最后一步应指向小测前准备
6. 输出严格 JSON，不要加 markdown 代码块

输出格式：
{{
  "steps": [
    {{"knowledge_point_id": "K12", "goal": "复习正比例函数与一次函数关系", "estimated_minutes": 10}},
    {{"knowledge_point_id": "K15", "goal": "理解一次函数定义与解析式结构", "estimated_minutes": 15}},
    {{"knowledge_point_id": "K15", "goal": "完成针对练习并整理易错点", "estimated_minutes": 15}}
  ],
  "total_estimated_minutes": 40
}}
"""
