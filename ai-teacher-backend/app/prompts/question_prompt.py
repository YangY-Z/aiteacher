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

【教学进度】
- 当前阶段：第 {current_phase}/{total_phases} 阶段
- 阶段说明：
  * 第1阶段：情境引入，激发兴趣
  * 第2阶段：详细讲解，示例演示
  * 第3阶段：辨析练习，深化理解
  * 第4阶段：综合应用，总结归纳

【对话历史】
{conversation_history}

【学生的回答】
{student_message}

【判断标准】
1. 学生是否正确理解了概念？
2. 回答是否完整？是否遗漏关键点？
3. 是否存在误解需要纠正？

【返回格式】请严格按照以下JSONL格式输出，每行一个独立的JSON对象：

{{"type":"msg_feedback","content":"对学生的回答进行评价和反馈（指出正确/错误，解释原因）"}}
{{"type":"msg_encourage","content":"鼓励语（可选，学生表现好时输出）"}}
{{"type":"msg_supplement","content":"补充说明或提出新的引导问题（如果学生回答不完整或有误解时输出）"}}
{{"type":"wb_formulas","content":"需要强调的公式（LaTeX格式）"}}
{{"type":"complete","next_action":"wait_for_student 或 next_phase 或 start_assessment 或 next_knowledge_point"}}

【输出规则】
1. 必须包含 msg_feedback
2. 学生表现好时输出 msg_encourage
3. 学生有误解时输出 msg_supplement 和 wb_formulas
4. 最后必须输出 complete
5. 【关键】如果 next_action 是 "wait_for_student"，必须在 msg_feedback 或 msg_supplement 的最后提出一个明确的引导问题，让学生知道接下来该回答什么

【next_action 决策规则】

【重要】根据当前阶段和回答质量，智能选择 next_action：

1. 返回 "next_phase" 当（阶段推进）：
   - 学生正确理解了当前阶段的核心内容
   - 学生能够回答当前阶段的关键问题
   - 当前阶段不是最后一个阶段（current_phase < total_phases）
   
2. 返回 "start_assessment" 当（进入评估）：
   - 当前是最后一个阶段（current_phase == total_phases）
   - 且学生已经掌握了核心概念和基本应用方法
   - 学生能够正确回答多个关键问题
   - 学生表现出对知识的熟练掌握

3. 返回 "next_knowledge_point" 当（跳过评估）：
   - 当前知识点是概念类（概念理解为主，不需要计算练习）
   - 学生回答正确理解了核心概念
   - 学生回答基本正确，只是表述不够完整

4. 返回 "wait_for_student" 当（继续引导）：
   - 学生回答有明显错误，需要纠正
   - 学生提出问题需要回答
   - 学生只是简单回应（如"好的"、"明白了"），但没有展示真正的理解
   - 需要进一步提问检查理解程度
   - 学生表示"忘记了"、"不会"，需要更详细的讲解
   - 学生回答不完整或不够深入
   【重要】返回 wait_for_student 时，必须在输出中提出新的问题

【决策优先级】
- 如果学生理解了 → 优先推进阶段（next_phase）
- 如果是最后阶段且掌握了 → 开始评估（start_assessment）
- 如果不理解 → 继续引导（wait_for_student）

不要急于出题，要确保学生真正理解后再进入下一阶段或评估

【知识点类型判断】
- 概念类：定义、性质、定理等 → 可跳过评估（next_knowledge_point）
- 公式类：公式推导、公式应用 → 需要评估（start_assessment）
- 技能类：计算方法、解题技巧 → 需要评估（start_assessment）

【示例 - 错误示范】
学生回答不完整时：
{{"type":"msg_feedback","content":"你的回答不够完整。斜率是表示直线倾斜程度的数值。"}}
{{"type":"complete","next_action":"wait_for_student"}}
❌ 错误：没有提出新问题，学生不知道下一步该做什么

【示例 - 正确示范】
学生回答不完整时：
{{"type":"msg_feedback","content":"你的回答不够完整。斜率是表示直线倾斜程度的数值。"}}
{{"type":"msg_supplement","content":"那么问题来了：如果一个一次函数的图像从左往右是上升的，它的k值应该是正数还是负数？为什么？"}}
{{"type":"complete","next_action":"wait_for_student"}}
✅ 正确：提出了明确的引导问题

【场景示例 - 何时推进阶段】

❌ 错误：学生说"我忘记怎么算了" → 老师讲解后 → next_phase
学生还没掌握，应该继续引导（wait_for_student）

❌ 错误：学生说"好的明白了" → 老师直接 next_phase
这只是简单回应，应该进一步检查是否真正理解

✅ 正确：学生正确回答关键问题 → next_phase
当前阶段学生理解了，推进到下一阶段

✅ 正确：最后阶段，学生多次正确回答关键问题 → start_assessment
确认学生理解后进入评估

请开始输出："""
