"""Chat API routes for conversation-based knowledge point recommendation."""

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.security import get_current_student_id
from app.schemas.common import APIResponse
from app.services.chat_service import chat_service

router = APIRouter()


class ChatRecommendRequest(BaseModel):
    """Request schema for chat recommendation."""

    message: str = Field(..., description="学生说的话", min_length=1, max_length=1000)
    session_id: Optional[str] = Field(None, description="对话会话ID，用于继续多轮对话")
    student_id: Optional[int] = Field(None, description="学生ID（可选，用于未登录场景）")


class ChatRecommendData(BaseModel):
    """Response data schema for chat recommendation."""

    reply: str = Field(..., description="AI的回复")
    is_ready: bool = Field(..., description="是否已收集足够信息可以推荐知识点")
    recommended_kp: Optional[str] = Field(None, description="推荐的知识点ID")
    recommended_kp_name: Optional[str] = Field(None, description="推荐的知识点名称")
    session_id: str = Field(..., description="会话ID，用于继续对话")


@router.post("/recommend", response_model=APIResponse[ChatRecommendData])
async def chat_recommend(
    request: ChatRecommendRequest,
    student_id: int = Depends(get_current_student_id),
) -> APIResponse[ChatRecommendData]:
    """Process student message and recommend knowledge point.

    这个接口用于对话分析推荐知识点：
    - 学生与AI对话，AI分析学生的薄弱点
    - 当收集到足够信息后，推荐合适的知识点开始学习

    Args:
        request: Chat request with message and optional session_id.
        student_id: Authenticated student ID.

    Returns:
        API response with AI reply and optional knowledge point recommendation.
    """
    result = chat_service.process_message(
        message=request.message,
        student_id=student_id,
        session_id=request.session_id,
    )

    return APIResponse(
        success=True,
        data=ChatRecommendData(
            reply=result["reply"],
            is_ready=result["is_ready"],
            recommended_kp=result.get("recommended_kp"),
            recommended_kp_name=result.get("recommended_kp_name"),
            session_id=result["session_id"],
        ),
    )


class ChatSessionInfo(BaseModel):
    """Chat session info schema."""

    session_id: str
    message_count: int
    created_at: str
    recommended_kp_id: Optional[str] = None


@router.get("/session/{session_id}", response_model=APIResponse[ChatSessionInfo])
async def get_chat_session(
    session_id: str,
    student_id: int = Depends(get_current_student_id),
) -> APIResponse[ChatSessionInfo]:
    """Get chat session info.

    Args:
        session_id: Session ID.
        student_id: Authenticated student ID.

    Returns:
        API response with session info.
    """
    session = chat_service.get_session(session_id)
    
    if not session:
        return APIResponse(
            success=False,
            message="会话不存在",
        )
    
    if session.student_id != student_id:
        return APIResponse(
            success=False,
            message="无权访问此会话",
        )

    return APIResponse(
        success=True,
        data=ChatSessionInfo(
            session_id=session.id,
            message_count=len(session.messages),
            created_at=session.created_at.isoformat(),
            recommended_kp_id=session.recommended_kp_id,
        ),
    )
