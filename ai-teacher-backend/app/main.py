"""FastAPI main application entry point."""

import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import api_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.utils.data_loader import load_course_data, load_assessment_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup: Load initial data
    load_course_data()

    # Load assessment questions
    assessment_path = Path(settings.data_dir) / "评估题库_一次函数.json"
    if assessment_path.exists():
        try:
            with open(assessment_path, "r", encoding="utf-8") as f:
                assessment_data = json.load(f)
            load_assessment_data(assessment_data)
        except (json.JSONDecodeError, Exception) as e:
            print(f"Warning: Failed to load assessment data: {e}")

    yield

    # Shutdown: Clean up resources if needed
    pass


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

    # Catch all other exceptions
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other exceptions."""
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": str(exc),
                "error_code": "INTERNAL_ERROR",
                "details": {"type": type(exc).__name__},
            },
        )

    # General exception handler for debugging
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other exceptions."""
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": str(exc),
                "error_type": type(exc).__name__,
                "traceback": traceback.format_exc(),
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
