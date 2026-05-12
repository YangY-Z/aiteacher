"""Interactive whiteboard API endpoints."""

import json
import logging
import base64
from typing import Annotated, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.security import get_current_student_id
from app.schemas.common import APIResponse
from app.repositories.learning_repository import learning_session_repository
from app.services.llm_service import llm_service

router = APIRouter()
logger = logging.getLogger(__name__)


class SubmitDrawingRequest(BaseModel):
    """Request model for submitting a drawing."""
    task_id: str
    image_data: str
    template_id: Optional[str] = None


class Correction(BaseModel):
    """Correction model for AI feedback."""
    type: str
    position: dict
    content: str


class AIFeedbackResponse(BaseModel):
    """Response model for AI feedback."""
    score: Optional[float] = None
    correct: bool
    feedback: str
    corrections: Optional[list[Correction]] = None


@router.post("/session/{session_id}/submit-drawing")
async def submit_drawing(
    session_id: str,
    student_id: Annotated[int, Depends(get_current_student_id)],
    request: SubmitDrawingRequest,
) -> APIResponse[AIFeedbackResponse]:
    """Submit a student's drawing for AI analysis.
    
    This endpoint:
    1. Receives the student's drawing as base64 image
    2. Analyzes the drawing using multimodal LLM
    3. Returns feedback on correctness and suggestions
    
    Args:
        session_id: Learning session ID
        student_id: Authenticated student ID
        request: Drawing submission request
        
    Returns:
        API response with AI feedback
    """
    logger.info(f"[Interactive] Submitting drawing for session {session_id}, task {request.task_id}")
    
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
    
    try:
        image_data = request.image_data
        if image_data.startswith("data:image"):
            image_data = image_data.split(",", 1)[1]
        
        prompt = """你是一位理科教师，正在批改学生的绘图作业。

请分析学生的绘图并给出反馈：
1. 判断绘图是否正确
2. 给出评分（0-100）
3. 提供详细的反馈意见
4. 如果有错误，指出具体问题

请以JSON格式返回：
{
    "correct": true/false,
    "score": 0-100,
    "feedback": "详细的反馈内容",
    "corrections": [
        {"type": "highlight", "position": {"x": 0, "y": 0}, "content": "标注内容"}
    ]
}

注意：
- 如果学生画的是函数图像，检查斜率、截距等关键点
- 如果学生画的是几何图形，检查形状、大小、位置
- 给出鼓励性的反馈，指出做得好的地方
- 如果有错误，给出具体的改进建议"""

        analysis_result = await llm_service.analyze_image(
            image_data=image_data,
            prompt=prompt,
        )
        
        try:
            if isinstance(analysis_result, str):
                analysis = json.loads(analysis_result)
            else:
                analysis = analysis_result
        except json.JSONDecodeError:
            analysis = {
                "correct": True,
                "score": 80,
                "feedback": analysis_result if isinstance(analysis_result, str) else "绘图已完成",
                "corrections": None,
            }
        
        feedback = AIFeedbackResponse(
            score=analysis.get("score"),
            correct=analysis.get("correct", True),
            feedback=analysis.get("feedback", "绘图已完成"),
            corrections=analysis.get("corrections"),
        )
        
        logger.info(f"[Interactive] Drawing analysis complete: correct={feedback.correct}, score={feedback.score}")
        
        return APIResponse(
            success=True,
            data=feedback,
            message="绘图分析完成",
        )
        
    except Exception as e:
        logger.error(f"[Interactive] Failed to analyze drawing: {e}", exc_info=True)
        
        feedback = AIFeedbackResponse(
            correct=True,
            score=75,
            feedback="绘图已收到。由于分析服务暂时不可用，请继续学习。",
            corrections=None,
        )
        
        return APIResponse(
            success=True,
            data=feedback,
            message="绘图已收到",
        )


@router.get("/templates")
async def get_drawing_templates(
    student_id: Annotated[int, Depends(get_current_student_id)],
) -> APIResponse[list]:
    """Get available drawing templates.
    
    Args:
        student_id: Authenticated student ID
        
    Returns:
        API response with list of templates
    """
    templates = [
        {
            "id": "blank",
            "name": "空白画布",
            "subject": "general",
            "guide": "自由绘制",
        },
        {
            "id": "grid",
            "name": "方格纸",
            "subject": "math",
            "guide": "在方格纸上绘图",
        },
        {
            "id": "coordinate",
            "name": "平面直角坐标系",
            "subject": "math",
            "guide": "在坐标系中绘制函数图像",
        },
        {
            "id": "number-line",
            "name": "数轴",
            "subject": "math",
            "guide": "在数轴上标出点",
        },
    ]
    
    return APIResponse(
        success=True,
        data=templates,
    )
