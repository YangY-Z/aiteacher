"""FastAPI main application entry point."""

import json
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.utils.data_loader import load_assessment_data

# 配置日志
def setup_logging():
    """配置应用日志"""
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # 设置根日志级别
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),  # 输出到控制台
        ]
    )
    
    # 设置第三方库日志级别（减少噪音）
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    # 设置应用日志级别
    logging.getLogger("app").setLevel(logging.DEBUG if settings.debug else logging.INFO)

# 初始化日志
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    logger.info("=" * 50)
    logger.info("AI虚拟教师系统启动中...")
    logger.info(f"环境: {settings.environment}")
    logger.info(f"LLM Provider: {settings.llm_provider}")
    logger.info(f"Debug模式: {settings.debug}")
    logger.info("=" * 50)
    
    # Note: Course data is already initialized in memory_db.__post_init__
    # Only load assessment questions here

    # Load assessment questions
    assessment_path = Path(settings.data_dir) / "评估题库_一次函数.json"
    if assessment_path.exists():
        try:
            with open(assessment_path, "r", encoding="utf-8") as f:
                assessment_data = json.load(f)
            load_assessment_data(assessment_data)
            logger.info(f"评估题库加载成功: {assessment_path}")
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"加载评估题库失败: {e}")

    yield

    # Shutdown: Clean up resources if needed
    logger.info("AI虚拟教师系统关闭...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(
        title="AI虚拟教师系统",
        description="AI Virtual Teacher System API - K12智能教学平台",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router, prefix="/api/v1")

    # Mount generated media files (Manim animations, images)
    generated_media_dir = Path("./generated_media")
    generated_media_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/media", StaticFiles(directory=str(generated_media_dir)), name="generated_media")

    # Global exception handler
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        """Handle application-specific exceptions."""
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": exc.message,
                "error_code": exc.error_code,
                "details": exc.details,
            },
        )

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "environment": settings.environment}

    return app


# Create the application instance
app = create_app()
