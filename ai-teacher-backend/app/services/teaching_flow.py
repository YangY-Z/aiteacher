"""Teaching flow coordinator for the layered Agent architecture."""

import json
import logging
import re
from typing import Any, AsyncGenerator, Optional

from app.models.tool import TeachingEvent, StudentContext
from app.models.learning import LearningSession
from app.services.tools.registry import ToolRegistry, tool_registry as global_tool_registry
from app.services.student_context_loader import student_context_loader
from app.services.tool_selection_engine import (
    tool_selection_engine,
    TeachingContext,
)
from app.services.tool_strategies import (
    ToolProcessStrategySelector,
    build_default_strategy_selector,
)
from app.services.course_service import course_service
from app.services.llm_service import llm_service
from app.prompts.system_prompt import TEACHING_SYSTEM_PROMPT
from app.repositories.course_repository import knowledge_point_repository
from app.repositories.learning_repository import learning_session_repository

logger = logging.getLogger(__name__)


class TeachingFlow:
    """Teaching flow coordinator for the layered Agent architecture.

    This class coordinates the entire teaching process:
    1. Load student context (profile, history, summary)
    2. Load teaching configuration (KP info, teaching mode, phase)
    3. Prepare tool contexts (based on rules)
    4. Generate teaching prompt (with tool contexts)
    5. Stream LLM response (with tool decision-making)
    6. Process tool results (using strategy pattern)

    Key Design Decisions:
    - Not called "Agent" to avoid over-design
    - Rule-based tool selection instead of AI decision
    - LLM decides whether to use tools (not external engine)
    - Strategy pattern for tool result processing

    Example:
        >>> flow = TeachingFlow()
        >>> async for event in flow.execute_teaching_phase(session, "张三"):
        ...     print(event)
    """

    def __init__(self, tool_registry: Optional[ToolRegistry] = None):
        """Initialize the teaching flow.

        Args:
            tool_registry: Tool registry instance (uses global if not provided)
        """
        self.tool_registry = tool_registry if tool_registry is not None else global_tool_registry
        self.student_context_loader = student_context_loader
        self.course_service = course_service
        self.llm_service = llm_service

        # Initialize strategy selector
        self.strategy_selector = build_default_strategy_selector()

        logger.info("TeachingFlow initialized")

    async def execute_teaching_phase(
        self,
        session: LearningSession,
        student_name: str,
        trace_id: Optional[str] = None,
        use_tools: bool = True,
        student_message: str = "",
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Execute teaching phase - 6-step process with multi-phase support.

        This is the main entry point for teaching flow.
        Supports automatic phase advancement: LLM decides via next_action field.

        Steps:
        1. Load student context (profile, history, summary)
        2. Load teaching configuration (KP info, teaching mode, phase)
        3. Prepare tool contexts (based on rules)
        4. Generate teaching prompt (with tool contexts)
        5. Stream LLM response (with tool decision-making)
        6. Process tool results (using strategy pattern)
        7. If LLM outputs next_action="next_phase", advance phase and repeat 4-6

        Args:
            session: Learning session
            student_name: Student name for personalization
            trace_id: Optional trace ID for logging
            use_tools: Whether to use tool enhancement
            student_message: Student's latest message for context

        Yields:
            SSE event dictionaries with event type and data
        """
        trace_id = trace_id or session.id
        logger.info(f"[{trace_id}] === TeachingFlow: 开始执行教学阶段 ===")
        logger.info(f"[{trace_id}] use_tools={use_tools}")

        if not session.kp_id:
            logger.error(f"[{trace_id}] 会话没有当前知识点")
            yield {
                "event": "error",
                "data": json.dumps({"error": "会话没有当前知识点"}, ensure_ascii=False)
            }
            return

        # ========== Step 1: Load student context ==========
        logger.info(f"[{trace_id}] === 步骤1: 加载学生上下文 ===")
        student_context = await self.student_context_loader.load(
            student_id=session.student_id,
            course_id=session.course_id,
        )
        logger.info(
            f"[{trace_id}] 学生上下文加载完成: "
            f"total_learned={student_context.summary['total_learned']}, "
            f"average_score={student_context.summary['average_score']:.2%}"
        )

        # ========== Step 2: Load teaching configuration ==========
        logger.info(f"[{trace_id}] === 步骤2: 加载教学配置 ===")
        kp_info = self.course_service.get_knowledge_point_info(session.kp_id)
        kp_entity = knowledge_point_repository.get_by_id(session.kp_id)

        # Get teaching mode (already bound to KP type)
        from app.prompts.teaching_prompt import get_teaching_mode_for_kp
        teaching_mode = get_teaching_mode_for_kp(kp_info["type"])

        # Get total phases from mode config
        from app.models.teaching_mode import TEACHING_MODE_CONFIGS
        mode_config = TEACHING_MODE_CONFIGS.get(teaching_mode)
        total_phases = len(mode_config.phases) if mode_config else 4

        logger.info(
            f"[{trace_id}] 教学配置: "
            f"kp_name={kp_info['name']}, "
            f"kp_type={kp_info['type']}, "
            f"teaching_mode={teaching_mode}, "
            f"current_phase={session.current_phase}, "
            f"total_phases={total_phases}"
        )

        # ========== Step 3: Prepare tool contexts ==========
        logger.info(f"[{trace_id}] === 步骤3: 准备工具上下文 ===")

        # Prepare tool contexts based on use_tools flag
        tool_contexts = {}

        if use_tools:
            # Determine student ability
            profile = student_context.profile
            attempt_count = 0
            if profile and session.kp_id in profile.completed_kp_ids:
                attempt_count = 1  # Simplified
            student_ability = tool_selection_engine.determine_student_ability(attempt_count)

            # Build teaching context
            teaching_context = TeachingContext(
                current_phase=session.current_phase,
                kp_type=kp_info["type"],
                student_ability=student_ability,
                teaching_mode=str(teaching_mode),
            )

            # Get all registered tools
            all_tools = self.tool_registry.get_all_registered_tools()
            logger.info(f"[{trace_id}] 已注册工具: {all_tools}")

            # Prepare tool contexts for all tools
            tool_contexts = await self.tool_registry.prepare_tool_contexts(
                all_tools,
                session.kp_id,
            )
            logger.info(f"[{trace_id}] 工具上下文准备完成: {list(tool_contexts.keys())}")
        else:
            logger.info(f"[{trace_id}] 工具增强已禁用,跳过工具上下文准备")

        # 加载对话历史（只需一次）
        conversation_history = session.get_conversation_history(max_turns=20)
        history_summary_str = session.get_history_summary_str()

        # 多阶段循环：LLM 通过 next_action 决定是否推进到下一阶段
        student_message_for_prompt = student_message
        first_phase = True

        while session.current_phase <= total_phases:
            current_phase = session.current_phase
            if not first_phase:
                logger.info(f"[{trace_id}] === 进入下一阶段: 第{current_phase}/{total_phases}阶段 ===")
                student_message_for_prompt = ""
                conversation_history = []
            first_phase = False

            # ========== Step 4: Generate teaching prompt ==========
            logger.info(f"[{trace_id}] === 步骤4: 生成教学Prompt ===")
            logger.info(f"[{trace_id}] 当前会话消息数: {len(conversation_history)}")
            if history_summary_str:
                logger.info(f"[{trace_id}] 历史学习总结:\n{history_summary_str}")

            prompt = self._build_teaching_prompt(
                kp_info=kp_info,
                kp_entity=kp_entity,
                current_phase=current_phase,
                teaching_mode=teaching_mode,
                student_context=student_context,
                student_name=student_name,
                tool_contexts=tool_contexts,
                session_messages=conversation_history,
                student_message=student_message_for_prompt,
                history_summary=history_summary_str,
                learning_round=session.learning_round,
                has_student_response=bool(student_message_for_prompt),
                total_phases=total_phases,
            )
            logger.info(f"[{trace_id}] Prompt生成完成, 长度={len(prompt)}字符")

            # ========== Step 5: Stream LLM response ==========
            logger.info(f"[{trace_id}] === 步骤5: 流式调用LLM ===")

            buffer = ""
            event_count = 0
            last_next_action = "wait_for_student"

            try:
                async for line in self._stream_lines(
                    self.llm_service.stream_chat(TEACHING_SYSTEM_PROMPT, prompt, trace_id=trace_id)
                ):
                    result = await self._parse_line(line, tool_contexts, trace_id)
                    if result is None:
                        continue
                    event_type, event_data, sse_dict = result
                    event_count += 1
                    if event_type == "complete":
                        last_next_action = event_data.get("next_action", "wait_for_student")
                    yield sse_dict
            except Exception as e:
                logger.error(f"[{trace_id}] LLM调用失败: {e}", exc_info=True)
                yield {
                    "event": "error",
                    "data": json.dumps({"error": f"LLM调用失败: {str(e)}"}, ensure_ascii=False)
                }
                break

            if event_count == 0:
                logger.error(f"[{trace_id}] LLM返回空响应")
                yield {
                    "event": "error",
                    "data": json.dumps({"error": "LLM返回空响应，请检查LLM服务配置"}, ensure_ascii=False)
                }
                break

            # ========== Step 7: Handle phase advancement ==========
            if last_next_action == "next_phase":
                new_phase = session.advance_phase()
                learning_session_repository.update(session)
                logger.info(f"[{trace_id}] 推进到第{new_phase}阶段")
                yield {
                    "event": "phase_advance",
                    "data": json.dumps({
                        "current_phase": new_phase,
                        "total_phases": total_phases,
                        "next_action": "teaching",
                    }, ensure_ascii=False)
                }
                # Loop continues to teach next phase
            elif last_next_action == "start_assessment":
                logger.info(f"[{trace_id}] 所有阶段完成,开始评估")
                yield {
                    "event": "complete",
                    "data": json.dumps({
                        "next_action": "start_assessment",
                        "message": "所有阶段学习完成，开始评估",
                    }, ensure_ascii=False)
                }
                break
            else:
                # wait_for_student: end the stream, wait for student response
                logger.info(f"[{trace_id}] 等待学生回复")
                break

        logger.info(f"[{trace_id}] === 教学阶段执行完成 ===")

    def _build_teaching_prompt(
        self,
        kp_info: dict[str, Any],
        kp_entity: Any,
        current_phase: int,
        teaching_mode: Any,
        student_context: StudentContext,
        student_name: str,
        tool_contexts: dict[str, Any],
        session_messages: Optional[list[dict[str, str]]] = None,
        student_message: str = "",
        history_summary: str = "",
        learning_round: int = 1,
        has_student_response: bool = False,
        total_phases: int = 4,
    ) -> str:
        """Build teaching prompt with tool contexts and phase advancement support.

        This method constructs a comprehensive prompt including:
        - Knowledge point information
        - Student context (profile, history, summary)
        - Current phase and teaching mode
        - Available tools and usage instructions
        - Student response evaluation (when has_student_response)
        - Output format constraints

        Args:
            kp_info: Knowledge point information dict
            kp_entity: Knowledge point entity
            current_phase: Current teaching phase
            teaching_mode: Teaching mode
            student_context: Student context
            student_name: Student name
            tool_contexts: Dictionary of tool contexts
            has_student_response: Whether this is a follow-up with student answer
            total_phases: Total number of phases

        Returns:
            Formatted prompt string
        """
        from app.prompts.teaching_prompt import generate_teaching_prompt

        # Get key points
        key_points = ", ".join(kp_entity.key_points) if kp_entity and kp_entity.key_points else ""

        # Build base prompt
        prompt = generate_teaching_prompt(
            knowledge_point_name=kp_info["name"],
            knowledge_point_id=kp_info["id"],
            knowledge_point_type=kp_info["type"],
            description=kp_info.get("description", ""),
            key_points=key_points,
            dependencies=", ".join(kp_info.get("dependency_names", [])) if kp_info.get("dependency_names") else "无",
            student_name=student_name,
            attempt_count=student_context.summary.get("total_learned", 0),
            attempt_info="",
            teaching_requirements="",
            learner_type="intermediate",
            current_phase=current_phase,
            learning_round=learning_round,
            history_summary=history_summary,
        )

        # Add tool contexts
        if tool_contexts:
            prompt += "\n\n【可用教学资源】\n"
            for tool_name, context in tool_contexts.items():
                prompt += f"\n{context.to_prompt_str()}\n"

        # Add conversation history for multi-round context
        if session_messages:
            prompt += "\n\n【本轮对话历史】\n"
            for msg in session_messages:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "assistant":
                    prompt += f"老师：{content}\n"
                elif role == "user":
                    prompt += f"学生：{content}\n"
                else:
                    prompt += f"{role}：{content}\n"

        # Add latest student message
        if student_message:
            prompt += f"\n【学生最新提问】\n{student_message}\n"

        # Add phase advancement evaluation when there's a student response
        if has_student_response:
            prompt += f"""
【学生回答评估】
学生的上一条消息是对你之前教学问题的回答。请评估学生的理解程度，并选择后续行动：

next_action 选项：
  - "wait_for_student": 学生没有完全理解，继续当前阶段教学
  - "next_phase": 学生已理解，进入下一阶段教学
  - "start_assessment": 所有阶段已完成，开始评估

评估规则：
1. 如果学生理解正确、回答准确 → 当前阶段教学成功
   a. 如果 current_phase < total_phases → next_action = "next_phase"
   b. 如果 current_phase == total_phases（当前是最后一个阶段）→ next_action = "start_assessment"
2. 如果学生理解有误、回答不完整或需要更多帮助 → next_action = "wait_for_student"，继续当前阶段
3. 不要随意推进阶段，确保学生真正理解后再推进

【输出格式】
每行输出一个JSON对象：

{{"type":"segment","message":"点评/反馈或继续教学的内容..."}}
{{"type":"segment","message":"提问内容...","is_question":true}}
{{"type":"complete","next_action":"next_phase"}}

注意：next_action 根据评估规则决定，可选 "wait_for_student"、"next_phase" 或 "start_assessment"
"""
        else:
            # Initial teaching: next_action should follow the base prompt's phase output guide
            prompt += """
【返回格式】
请严格按照以下JSONL格式输出,每行一个独立的JSON对象:

{"type":"segment","message":"教学内容...","image_id":"IMG_001"}
{"type":"segment","message":"教学内容...","video_id":"VID_002"}
{"type":"segment","message":"提问内容...","is_question":true}
{"type":"complete","next_action":"wait_for_student"}

【重要规则】
1. 每个 segment 最多只能引用一个资源(图片/视频/演示)
2. 如果需要多个资源,请分成多个 segment 输出
3. 必须包含提问环节
4. next_action 设为 "wait_for_student"（系统会根据LLM响应自动决定是否推进）

请开始输出:
"""

        return prompt

    async def _process_tool_references(
        self,
        event: TeachingEvent,
        tool_contexts: dict[str, Any],
        trace_id: str,
    ) -> TeachingEvent:
        """Process tool references in the event using strategy pattern.

        This method:
        1. Delegates to strategy selector
        2. Lets the appropriate strategy handle the event
        3. Returns processed event

        Args:
            event: Teaching event to process
            tool_contexts: Available tool contexts
            trace_id: Trace ID for logging

        Returns:
            Processed teaching event
        """
        processed_event = await self.strategy_selector.select_and_process(
            event,
            self.tool_registry,
            self.llm_service,
        )

        return processed_event

    async def _stream_lines(self, stream) -> AsyncGenerator[str, None]:
        """Split streaming chunks into individual lines, flushing trailing content."""
        buffer = ""
        for chunk in stream:
            buffer += chunk
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if line.strip():
                    yield line.strip()
        if buffer.strip():
            yield buffer.strip()

    async def _parse_line(
        self,
        line: str,
        tool_contexts: dict[str, Any],
        trace_id: str,
    ):
        """Parse a single JSON line from LLM stream and process tool references.

        Returns (event_type, event_data, sse_dict) or None if line should be skipped.
        """
        line = line.strip()
        print(line)
        if not line or line.startswith("```"):
            return None
        try:
            line_fixed = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', line)
            event_data = json.loads(line_fixed)
            event_type = event_data.get("type", "")

            event = TeachingEvent(
                event_type=event_type,
                message=line_fixed,
                next_action=event_data.get("next_action", ""),
            )
            processed_event = await self._process_tool_references(event, tool_contexts, trace_id)
            sse_dict = self._event_to_sse(processed_event, event_data)
            return event_type, event_data, sse_dict
        except json.JSONDecodeError as e:
            logger.warning(f"[{trace_id}] JSON解析失败: {line[:50]}... 错误: {e}")
            return None

    def _event_to_sse(
        self,
        event: TeachingEvent,
        original_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Convert teaching event to SSE format.

        Args:
            event: Processed teaching event
            original_data: Original JSON data from LLM

        Returns:
            SSE event dictionary
        """
        response_data = {
            "message": original_data.get("message", ""),
        }

        # Add resource attachments
        if event.image:
            response_data["image"] = event.image
        if event.video:
            response_data["video"] = event.video
        if event.interactive:
            response_data["interactive"] = event.interactive
        if event.question:
            response_data["question"] = event.question

        return {
            "event": event.event_type,
            "data": json.dumps(response_data, ensure_ascii=False),
        }


# Global instance
teaching_flow = TeachingFlow()
