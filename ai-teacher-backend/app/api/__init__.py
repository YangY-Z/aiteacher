"""API routes module."""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.students import router as students_router
from app.api.courses import router as courses_router
from app.api.learning import router as learning_router
from app.api.diagnostic import router as diagnostic_router
from app.api.retention import router as retention_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(students_router, prefix="/students", tags=["学生"])
api_router.include_router(courses_router, prefix="/courses", tags=["课程"])
api_router.include_router(learning_router, prefix="/learning", tags=["学习"])
api_router.include_router(diagnostic_router, prefix="/diagnostic", tags=["诊断"])
api_router.include_router(retention_router, tags=["课后保持"])
