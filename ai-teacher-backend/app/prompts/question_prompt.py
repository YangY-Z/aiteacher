"""Question and answer prompts."""

QUESTION_PROMPT = """【提问任务】
请在知识点讲解过程中向学生提问，检查理解程度。

【当前知识点】
- 名称：{knowledge_point_name}
- 类型：{knowledge_point_type}
- 核心要点：{key_points}

【提问位置】
{question_position}（讲解中段/讲解结束）

【提问目的】
{question_purpose}

【提问类型选择】
根据知识点类型选择合适的提问方式：

1. 概念类
   - 让学生用自己的话解释概念
   - 判断题：给出陈述让学生判断对错
   - 辨析题：区分易混淆的概念

2. 公式类
   - 选择题：识别公式的正确形式
   - 填空题：填写公式中的关键部分
   - 计算题：代入数值计算

3. 技能类
   - 让学生动手操作
   - 找错题：指出步骤中的错误
   - 完成题：完成部分步骤"""

STUDENT_ANSWER_PROMPT = """【学生回答处理任务】

【学生回答】
{student_answer}

【问题信息】
- 正确答案：{correct_answer}
- 问题类型：{question_type}

【处理要求】
1. 判断学生回答是否正确
2. 如果错误，分析错误原因
3. 给出针对性的反馈
4. 决定下一步行动"""

# 处理学生自由回答的 prompt
CHAT_RESPONSE_PROMPT = """【任务】
你是一位正在辅导学生的数学老师。学生刚刚回答了你的提问，请根据学生的回答给出合适的反馈。

【当前知识点】
- 名称：{knowledge_point_name}
- 类型：{knowledge_point_type}（概念/公式/技能）
- 核心要点：{key_points}
- 前置知识：{dependencies}

【学生的回答】
{student_message}

【判断标准】
1. 学生是否正确理解了概念？
2. 回答是否完整？是否遗漏关键点？
3. 是否存在误解需要纠正？

【返回格式】请严格按照以下JSONL格式输出，每行一个独立的JSON对象：

{{"type":"msg_feedback","content":"对学生的回答进行评价和反馈（指出正确/错误，解释原因）"}}
{{"type":"msg_encourage","content":"鼓励语（可选，学生表现好时输出）"}}
{{"type":"msg_supplement","content":"补充说明（如果学生回答不完整或有误解时输出）"}}
{{"type":"wb_formulas","content":"需要强调的公式（LaTeX格式）"}}
{{"type":"complete","next_action":"wait_for_student 或 start_assessment 或 next_knowledge_point"}}

【输出规则】
1. 必须包含 msg_feedback
2. 学生表现好时输出 msg_encourage
3. 学生有误解时输出 msg_supplement 和 wb_formulas
4. 最后必须输出 complete

【next_action 决策规则】

1. 返回 "next_knowledge_point" 当（最高优先级）：
   - 当前知识点是概念类（概念理解为主，不需要计算练习）
   - 学生回答正确理解了核心概念
   - 学生回答基本正确，只是表述不够完整

2. 返回 "start_assessment" 当：
   - 当前知识点是公式类或技能类（需要通过练习验证掌握程度）
   - 学生理解了概念，但需要通过题目验证应用能力

3. 返回 "wait_for_student" 当：
   - 学生回答有明显错误，需要纠正
   - 学生提出问题需要回答

【知识点类型判断】
- 概念类：定义、性质、定理等 → next_knowledge_point
- 公式类：公式推导、公式应用 → start_assessment
- 技能类：计算方法、解题技巧 → start_assessment

请开始输出："""
