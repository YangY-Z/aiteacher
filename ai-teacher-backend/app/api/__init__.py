"""API routes module."""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.students import router as students_router
from app.api.courses import router as courses_router
from app.api.learning import router as learning_router
from app.api.diagnostic import router as diagnostic_router
from app.api.retention import router as retention_router
from app.api.chat import router as chat_router
from app.api.admin import router as admin_router
from app.api.chapters import router as chapters_router
from app.api.knowledge_points import router as kp_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(students_router, prefix="/students", tags=["学生"])
api_router.include_router(courses_router, prefix="/courses", tags=["课程"])
api_router.include_router(learning_router, prefix="/learning", tags=["学习"])
api_router.include_router(diagnostic_router, prefix="/diagnostic", tags=["诊断"])
api_router.include_router(retention_router, tags=["课后保持"])
api_router.include_router(chat_router, prefix="/chat", tags=["对话推荐"])
api_router.include_router(admin_router, tags=["管理员"])
api_router.include_router(chapters_router, tags=["章节管理"])
api_router.include_router(kp_router, tags=["知识点管理"])
