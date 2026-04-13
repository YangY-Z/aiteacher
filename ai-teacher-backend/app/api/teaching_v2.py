"""Teaching API v2 with layered Agent architecture."""

import json
import logging
import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from app.core.security import get_current_student_id
from app.core.init_tools import initialize_system
from app.schemas.common import APIResponse
from app.repositories.learning_repository import learning_session_repository
from app.services.student_service import student_service
from app.services.teaching_flow import teaching_flow

router = APIRouter()
logger = logging.getLogger(__name__)

# System initialization flag
_system_initialized = False


def ensure_system_initialized():
    """Ensure the layered Agent system is initialized."""
    global _system_initialized
    if not _system_initialized:
        initialize_system()
        _system_initialized = True
        logger.info("Layered Agent system initialized for v2 API")


@router.post("/session/{session_id}/teach-v2")
async def teach_with_layered_agent(
    session_id: str,
    student_id: Annotated[int, Depends(get_current_student_id)],
    use_tools: bool = True,  # 是否使用工具增强
) -> EventSourceResponse:
    """Teaching endpoint using layered Agent architecture.
    
    This endpoint integrates:
    - Student context loading (历史信息、学习速度、困难领域)
    - Tool selection based on rules (规则映射选择工具)
    - Tool context preparation (准备工具上下文给LLM)
    - LLM streaming with tool references (LLM自决策使用工具)
    - Tool result processing (工具结果处理和输出)
    
    Args:
        session_id: Session ID.
        student_id: Authenticated student ID.
        use_tools: Whether to use tool enhancement.
        
    Returns:
        SSE stream with teaching content enriched with tools.
    """
    # Ensure system is initialized
    ensure_system_initialized()
    
    trace_id = f"teach-v2-{uuid.uuid4().hex[:12]}"
    logger.info(f"[{trace_id}] ========== V2教学流开始 ==========")
    logger.info(f"[{trace_id}] session_id={session_id}, student_id={student_id}, use_tools={use_tools}")
    
    # Get session
    session = learning_session_repository.get_by_id(session_id)
    if not session:
        logger.error(f"[{trace_id}] 会话不存在: {session_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )
    
    if session.student_id != student_id:
        logger.warning(f"[{trace_id}] 权限校验失败")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此会话",
        )
    
    # Get student
    student = student_service.get_by_id(student_id)
    if not student:
        logger.error(f"[{trace_id}] 学生不存在: {student_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学生不存在",
        )
    
    logger.info(f"[{trace_id}] 学生: {student.name}, 知识点: {session.kp_id}")
    
    async def event_generator():
        event_count = 0
        try:
            # Execute teaching flow
            async for sse_event in teaching_flow.execute_teaching_phase(
                session=session,
                student_name=student.name,
                trace_id=trace_id,
                use_tools=use_tools,
            ):
                event_count += 1
                
                # sse_event is already in SSE format {"event": ..., "data": ...}
                yield sse_event
            
            logger.info(f"[{trace_id}] ========== V2教学流完成, 共{event_count}个事件 ==========")
        
        except Exception as e:
            logger.error(f"[{trace_id}] V2教学流失败: {e}", exc_info=True)
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}, ensure_ascii=False),
            }
    
    return EventSourceResponse(event_generator())


@router.get("/session/{session_id}/tools/available")
async def get_available_tools(
    session_id: str,
    student_id: Annotated[int, Depends(get_current_student_id)],
) -> APIResponse[dict]:
    """Get available tools for current teaching context.
    
    This endpoint shows which tools would be selected for the current
    teaching phase and knowledge point type.
    
    Args:
        session_id: Session ID.
        student_id: Authenticated student ID.
        
    Returns:
        API response with available tools and their contexts.
    """
    # Ensure system is initialized
    ensure_system_initialized()
    
    # Get session
    session = learning_session_repository.get_by_id(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )
    
    if session.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此会话",
        )
    
    # Get tools based on context
    from app.services.tool_selection_engine import tool_selection_engine, TeachingContext
    from app.services.tools.registry import tool_registry
    
    # Determine teaching context
    current_phase = session.current_phase or 1
    kp = None
    if session.kp_id:
        from app.repositories.course_repository import knowledge_point_repository
        kp = knowledge_point_repository.get_by_id(session.kp_id)
    
    kp_type = kp.type if kp else "概念"
    
    # Select tools
    context = TeachingContext(
        current_phase=current_phase,
        kp_type=kp_type,
    )
    selected_tools = tool_selection_engine.select_tools(context)
    
    # Get tool contexts
    tool_contexts = {}
    if selected_tools and session.kp_id:
        tool_contexts = await tool_registry.prepare_tool_contexts(
            selected_tools,
            session.kp_id
        )
    
    # Build response
    tools_info = []
    for tool_name in selected_tools:
        metadata = tool_registry.get_tool_metadata(tool_name)
        context = tool_contexts.get(tool_name)
        
        tool_info = {
            "name": tool_name,
            "metadata": metadata,
            "context": {
                "description": context.description if context else "",
                "available_resources": len(context.available_resources) if context else 0,
            } if context else None,
        }
        tools_info.append(tool_info)
    
    return APIResponse(
        success=True,
        data={
            "teaching_context": {
                "phase": current_phase,
                "kp_type": kp_type,
                "kp_id": session.kp_id,
            },
            "selected_tools": selected_tools,
            "tools_info": tools_info,
        },
    )


@router.get("/images/{image_id}")
async def get_image_resource(
    image_id: str,
    student_id: Annotated[int, Depends(get_current_student_id)],
) -> APIResponse[dict]:
    """Get a specific image resource by ID.
    
    This endpoint retrieves image metadata and URL from the image library.
    
    Args:
        image_id: Image ID.
        student_id: Authenticated student ID.
        
    Returns:
        API response with image metadata.
    """
    # Ensure system is initialized
    ensure_system_initialized()
    
    from app.repositories.resource_repository import teaching_image_repository
    
    # Get image
    image = teaching_image_repository.get_by_id(image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图片不存在",
        )
    
    # Increment usage count
    teaching_image_repository.increment_usage(image_id)
    
    return APIResponse(
        success=True,
        data=image.to_dict(),
    )


@router.post("/images/generate")
async def generate_image(
    request: dict,
    student_id: Annotated[int, Depends(get_current_student_id)],
) -> APIResponse[dict]:
    """Generate a new image using template or AI.
    
    This endpoint generates an image based on concept and type.
    
    Args:
        request: Generation request with concept and type.
        student_id: Authenticated student ID.
        
    Returns:
        API response with generated image metadata.
    """
    # Ensure system is initialized
    ensure_system_initialized()
    
    from app.models.tool import ToolRequest
    from app.services.tools.image_tool import ImageTool
    
    # Extract parameters
    concept = request.get("concept", "")
    image_type = request.get("type", "infographic")
    knowledge_point_id = request.get("knowledge_point_id", "")
    
    if not concept:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少concept参数",
        )
    
    # Create image tool
    image_tool = ImageTool()
    
    # Generate image
    tool_request = ToolRequest(
        action="generate_image",
        params={
            "concept": concept,
            "type": image_type,
            "knowledge_point_id": knowledge_point_id,
        }
    )
    
    result = await image_tool.execute(tool_request)
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"图片生成失败: {result.error}",
        )
    
    return APIResponse(
        success=True,
        data=result.resource,
        message="图片生成成功",
    )
