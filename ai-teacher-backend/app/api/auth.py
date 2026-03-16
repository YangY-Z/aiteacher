"""Authentication API routes."""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.core.security import create_access_token
from app.schemas.student import StudentCreate, StudentLogin, StudentResponse, Token
from app.schemas.common import APIResponse
from app.services.student_service import student_service

router = APIRouter()


@router.post("/register", response_model=APIResponse[StudentResponse])
async def register(student_data: StudentCreate) -> APIResponse[StudentResponse]:
    """Register a new student.

    Args:
        student_data: Student registration data.

    Returns:
        API response with created student.
    """
    student = student_service.register(
        name=student_data.name,
        grade=student_data.grade,
        phone=student_data.phone,
        password=student_data.password,
    )

    return APIResponse(
        success=True,
        data=StudentResponse.from_domain(student),
        message="注册成功",
    )


@router.post("/login", response_model=APIResponse[Token])
async def login(login_data: StudentLogin) -> APIResponse[Token]:
    """Login with phone and password.

    Args:
        login_data: Login credentials.

    Returns:
        API response with access token.
    """
    result = student_service.login(
        phone=login_data.phone,
        password=login_data.password,
    )

    return APIResponse(
        success=True,
        data=Token(
            access_token=result["access_token"],
            token_type=result["token_type"],
            student_id=result["student_id"],
            student_name=result["student_name"],
        ),
        message="登录成功",
    )


@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> dict:
    """OAuth2 compatible token endpoint.

    Args:
        form_data: OAuth2 form data.

    Returns:
        Access token.
    """
    result = student_service.login(
        phone=form_data.username,
        password=form_data.password,
    )

    return {
        "access_token": result["access_token"],
        "token_type": result["token_type"],
    }
