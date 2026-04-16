"""Teaching flow coordinator for the layered Agent architecture."""

import json
import logging
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
from app.prompts.system_prompt import SYSTEM_PROMPT
from app.repositories.course_repository import knowledge_point_repository

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
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Execute teaching phase - 6-step process.
        
        This is the main entry point for teaching flow.
        
        Steps:
        1. Load student context (profile, history, summary)
        2. Load teaching configuration (KP info, teaching mode, phase)
        3. Prepare tool contexts (based on rules)
        4. Generate teaching prompt (with tool contexts)
        5. Stream LLM response (with tool decision-making)
        6. Process tool results (using strategy pattern)
        
        Args:
            session: Learning session
            student_name: Student name for personalization
            trace_id: Optional trace ID for logging
            use_tools: Whether to use tool enhancement
            
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
        
        # Get current phase
        current_phase = session.current_phase if session.current_phase else 1
        
        logger.info(
            f"[{trace_id}] 教学配置: "
            f"kp_name={kp_info['name']}, "
            f"kp_type={kp_info['type']}, "
            f"teaching_mode={teaching_mode}, "
            f"current_phase={current_phase}"
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
                current_phase=current_phase,
                kp_type=kp_info["type"],
                student_ability=student_ability,
                teaching_mode=str(teaching_mode),
            )
            
            # Get all registered tools
            all_tools = self.tool_registry.get_all_registered_tools()
            logger.info(f"[{trace_id}] 已注册工具: {all_tools}")
            
            # Prepare tool contexts for all tools
            # Key Design: Load ALL tool contexts, let LLM decide which to use
            tool_contexts = await self.tool_registry.prepare_tool_contexts(
                all_tools,
                session.kp_id,
            )
            logger.info(f"[{trace_id}] 工具上下文准备完成: {list(tool_contexts.keys())}")
        else:
            logger.info(f"[{trace_id}] 工具增强已禁用,跳过工具上下文准备")
        
        # ========== Step 4: Generate teaching prompt ==========
        logger.info(f"[{trace_id}] === 步骤4: 生成教学Prompt ===")
        prompt = self._build_teaching_prompt(
            kp_info=kp_info,
            kp_entity=kp_entity,
            current_phase=current_phase,
            teaching_mode=teaching_mode,
            student_context=student_context,
            student_name=student_name,
            tool_contexts=tool_contexts,
        )
        logger.info(f"[{trace_id}] Prompt生成完成, 长度={len(prompt)}字符")
        
        # ========== Step 5: Stream LLM response ==========
        logger.info(f"[{trace_id}] === 步骤5: 流式调用LLM ===")
        
        # Use buffer to accumulate stream data
        buffer = ""
        event_count = 0

        try:
            for chunk in self.llm_service.stream_chat(SYSTEM_PROMPT, prompt, trace_id=trace_id):
                buffer += chunk
                
                # Try to parse complete JSON lines
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    
                    if not line:
                        continue
                    
                    # Try to parse as JSON
                    try:
                        # Skip markdown code blocks
                        if line.startswith("```"):
                            continue
                        
                        # Fix backslash escaping issue
                        import re
                        line_fixed = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', line)
                        
                        event_data = json.loads(line_fixed)
                        event_type = event_data.get("type", "")
                        event_count += 1
                        
                        # Build teaching event
                        event = TeachingEvent(
                            event_type=event_type,
                            message=line_fixed,
                            next_action=event_data.get("next_action", ""),
                        )
                        
                        # ========== Step 6: Process tool results ==========
                        processed_event = await self._process_tool_references(
                            event, tool_contexts, trace_id
                        )
                        
                        # Yield processed event
                        yield self._event_to_sse(processed_event, event_data)
                        
                    except json.JSONDecodeError as e:
                        # Skip invalid JSON
                        logger.warning(f"[{trace_id}] JSON解析失败: {line[:50]}... 错误: {e}")
                        continue

            # Check if no events were yielded
            if event_count == 0:
                logger.error(f"[{trace_id}] LLM返回空响应")
                yield {
                    "event": "error",
                    "data": json.dumps({"error": "LLM返回空响应，请检查LLM服务配置"}, ensure_ascii=False)
                }

        except Exception as e:
            logger.error(f"[{trace_id}] LLM调用失败: {e}", exc_info=True)
            yield {
                "event": "error",
                "data": json.dumps({"error": f"LLM调用失败: {str(e)}"}, ensure_ascii=False)
            }

        logger.info(f"[{trace_id}] === 教学阶段执行完成, 共{event_count}个事件 ===")
    
    def _build_teaching_prompt(
        self,
        kp_info: dict[str, Any],
        kp_entity: Any,
        current_phase: int,
        teaching_mode: Any,
        student_context: StudentContext,
        student_name: str,
        tool_contexts: dict[str, Any],
    ) -> str:
        """Build teaching prompt with tool contexts.
        
        This method constructs a comprehensive prompt including:
        - Knowledge point information
        - Student context (profile, history, summary)
        - Current phase and teaching mode
        - Available tools and usage instructions
        - Output format constraints
        
        Args:
            kp_info: Knowledge point information dict
            kp_entity: Knowledge point entity
            current_phase: Current teaching phase
            teaching_mode: Teaching mode
            student_context: Student context
            student_name: Student name
            tool_contexts: Dictionary of tool contexts
            
        Returns:
            Formatted prompt string
        """
        # Base prompt (existing logic)
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
            learning_round=1,
            history_summary="",
        )
        
        # Add tool contexts
        if tool_contexts:
            prompt += "\n\n【可用教学资源】\n"
            for tool_name, context in tool_contexts.items():
                prompt += f"\n{context.to_prompt_str()}\n"
        
        # Add output format constraints
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
4. next_action 设为 "wait_for_student"

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
        # Use strategy selector to process the event
        processed_event = await self.strategy_selector.select_and_process(
            event,
            self.tool_registry,
            self.llm_service,
        )
        
        return processed_event
    
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
        # Build response data
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
