"""Admin API routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import create_access_token, require_admin
from app.models.student import Student, UserRole
from app.schemas.admin import AdminLogin, AdminResponse, AdminToken
from app.schemas.common import APIResponse
from app.repositories.memory_db import db

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/login", response_model=APIResponse[AdminToken])
async def admin_login(login_data: AdminLogin) -> APIResponse[AdminToken]:
    """Admin login endpoint.

    Args:
        login_data: Admin login credentials.

    Returns:
        API response with access token.

    Raises:
        HTTPException: If credentials are invalid or user is not admin.
    """
    # Find admin by phone
    admin = None
    for student in db._students.values():
        if student.phone == login_data.phone:
            admin = student
            break

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="管理员账号不存在",
        )

    # Verify role
    if admin.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="非管理员账号",
        )

    # Verify password
    from app.core.security import verify_password
    
    if not verify_password(login_data.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="密码错误",
        )

    # Create access token
    access_token = create_access_token(data={"sub": admin.id})

    # Update last login
    admin.update_last_login()

    return APIResponse(
        success=True,
        data=AdminToken(
            access_token=access_token,
            admin_id=admin.id,
            admin_name=admin.name,
            role=admin.role,
        ),
        message="登录成功",
    )


@router.get("/profile", response_model=APIResponse[AdminResponse])
async def get_admin_profile(
    current_admin: Student = Depends(require_admin),
) -> APIResponse[AdminResponse]:
    """Get current admin profile.

    Args:
        current_admin: Current authenticated admin user.

    Returns:
        API response with admin profile.
    """
    return APIResponse(
        success=True,
        data=AdminResponse.from_domain(current_admin),
    )


@router.get("/dashboard")
async def admin_dashboard(
    current_admin: Student = Depends(require_admin),
) -> dict:
    """Get admin dashboard statistics.

    Args:
        current_admin: Current authenticated admin user.

    Returns:
        Dashboard statistics.
    """
    # Calculate statistics
    total_students = len([s for s in db._students.values() if s.role == UserRole.STUDENT])
    total_courses = len(db._courses)
    total_chapters = len(db._chapters)
    total_knowledge_points = len(db._knowledge_points)

    return {
        "total_students": total_students,
        "total_courses": total_courses,
        "total_chapters": total_chapters,
        "total_knowledge_points": total_knowledge_points,
    }
