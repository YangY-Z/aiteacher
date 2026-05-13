"""HTML Agent View API — 基于 HTML 的 AI Agent 可浏览接口。

此模块提供 HTML 格式的端点，使得：
- AI Agent 可以通过 HTTP 直接"浏览"课程结构
- 所有页面都是语义化 HTML，LLM 可直接解析
- 学生看到的和 Agent 看到的是同一界面
"""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse

from app.core.security import get_current_student_id
from app.services.html_lesson_engine import (
    build_curriculum_html,
    build_lesson_html,
    build_agent_instructions_html,
)
from app.services.course_service import course_service
from app.repositories.course_repository import (
    course_repository,
    knowledge_point_repository,
)
from app.repositories.learning_repository import learning_session_repository
from app.repositories.learner_profile_repository import learner_profile_repository

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/curriculum/html", response_class=HTMLResponse)
async def get_curriculum_html(
    course_id: str = Query(default="MATH_JUNIOR_01", description="课程 ID"),
    student_id: Annotated[int, Depends(get_current_student_id)] = None,
    completed: Optional[str] = Query(default=None, description="已完成的知识点 ID，逗号分隔"),
):
    """
    返回整个课程地图作为 HTML 页面。
    这是 AI Agent 也能"浏览"的课程目录。

    HTML 语义约定：
    - .kp-card.completed — 已完成的知识点
    - .kp-card.active — 正在学习的知识点
    - .kp-card.pending — 未开始的知识点
    - data-kp-id — 知识点唯一标识
    - data-level — 知识点层级
    - meta[name="agent-interface"] — 标记此页面为 Agent 可解析
    """
    # 检查课程是否存在
    course = course_repository.get_by_id(course_id)
    if not course:
        raise HTTPException(status_code=404, detail=f"课程 {course_id} 不存在")

    # 解析已完成的知识点
    completed_ids: list[str] = []
    if completed:
        completed_ids = [c.strip() for c in completed.split(",") if c.strip()]

    # 如果提供了 student_id，从学习档案中加载完成状态
    if student_id and not completed:
        profile = learner_profile_repository.get_by_student_course(student_id, course_id)
        if profile:
            completed_ids = list(profile.completed_kp_ids)

    # 获取活跃知识点（当前正在学习的会话）
    active_kp_id: Optional[str] = None
    if student_id:
        active_session = learning_session_repository.get_active_session(student_id, course_id)
        if active_session:
            active_kp_id = active_session.kp_id

    html = build_curriculum_html(
        course_id=course_id,
        completed_kp_ids=completed_ids,
        active_kp_id=active_kp_id,
    )
    return HTMLResponse(content=html, status_code=200)


@router.get("/teaching-v2/session/{session_id}/html", response_class=HTMLResponse)
async def get_session_html(
    session_id: str,
    student_id: Annotated[int, Depends(get_current_student_id)] = None,
):
    """
    返回当前教学会话的 HTML 视图。
    包含知识点详情和白板内容，AI Agent 可直接解析教学状态。
    """
    session = learning_session_repository.get_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 权限校验
    if student_id and session.student_id != student_id:
        raise HTTPException(status_code=403, detail="无权访问此会话")

    # 取最后一条白板数据（如果有）
    whiteboard_data = {}
    history = session.get_conversation_history(max_turns=5)
    for msg in reversed(history):
        if msg.get("role") == "assistant":
            whiteboard_data = {
                "title": "当前教学内容",
                "key_points": [],
                "formulas": [],
                "examples": [],
                "notes": [],
                "content": msg.get("content", "")[:500],
            }
            break

    html = build_lesson_html(
        kp_id=session.kp_id,
        student_name=f"学生 {session.student_id}",
        phase=session.current_phase or 1,
        total_phases=4,
        whiteboard_data=whiteboard_data,
    )
    return HTMLResponse(content=html, status_code=200)


@router.get("/agent/instructions", response_class=HTMLResponse)
async def get_agent_instructions():
    """
    返回 AI Agent 交互指引页。
    说明本系统的 HTML 接口约定，供 Agent 解析。
    """
    html = build_agent_instructions_html()
    return HTMLResponse(content=html, status_code=200)
