"""Knowledge point management API routes."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import require_admin
from app.models.course import KnowledgePoint, KnowledgePointType, DependencyType, KnowledgePointDependency
from app.models.student import Student
from app.repositories.memory_db import db
from app.schemas.knowledge_point import (
    KnowledgePointCreate,
    KnowledgePointUpdate,
    KnowledgePointResponse,
    KnowledgePointListResponse,
    DependencyCreate,
    DependencyResponse,
)
from app.schemas.common import APIResponse

router = APIRouter(prefix="/admin", tags=["知识点管理"])


@router.get("/chapters/{chapter_id}/knowledge-points", response_model=APIResponse[KnowledgePointListResponse])
async def list_knowledge_points(
    chapter_id: str,
    level: Optional[int] = Query(None, ge=0, le=6, description="层级筛选"),
    type: Optional[KnowledgePointType] = Query(None, description="类型筛选"),
    current_admin: Student = Depends(require_admin),
) -> APIResponse[KnowledgePointListResponse]:
    """List knowledge points for a chapter.

    Args:
        chapter_id: Chapter ID.
        level: Filter by level.
        type: Filter by type.
        current_admin: Current admin user.

    Returns:
        List of knowledge points.

    Raises:
        HTTPException: If chapter not found.
    """
    # Check chapter exists
    if chapter_id not in db._chapters:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="章节不存在",
        )
    
    # Get knowledge points for this chapter
    knowledge_points = [
        kp for kp in db._knowledge_points.values()
        if kp.chapter_id == chapter_id
    ]
    
    # Apply filters
    if level is not None:
        knowledge_points = [kp for kp in knowledge_points if kp.level == level]
    if type:
        knowledge_points = [kp for kp in knowledge_points if kp.type == type]
    
    # Sort by level and sort_order
    knowledge_points.sort(key=lambda kp: (kp.level, kp.sort_order))
    
    return APIResponse(
        success=True,
        data=KnowledgePointListResponse(
            knowledge_points=[KnowledgePointResponse.from_domain(kp) for kp in knowledge_points],
            total=len(knowledge_points),
            chapter_id=chapter_id,
            level=level,
        ),
    )


@router.post("/chapters/{chapter_id}/knowledge-points", response_model=APIResponse[KnowledgePointResponse], status_code=status.HTTP_201_CREATED)
async def create_knowledge_point(
    chapter_id: str,
    kp_data: KnowledgePointCreate,
    current_admin: Student = Depends(require_admin),
) -> APIResponse[KnowledgePointResponse]:
    """Create a new knowledge point.

    Args:
        chapter_id: Chapter ID.
        kp_data: Knowledge point creation data.
        current_admin: Current admin user.

    Returns:
        Created knowledge point.

    Raises:
        HTTPException: If chapter not found or KP ID already exists.
    """
    # Check chapter exists
    if chapter_id not in db._chapters:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="章节不存在",
        )
    
    # Check KP ID not used
    if kp_data.id in db._knowledge_points:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"知识点ID {kp_data.id} 已存在",
        )
    
    # Validate dependencies
    for dep_id in kp_data.dependencies:
        if dep_id not in db._knowledge_points:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"依赖的知识点 {dep_id} 不存在",
            )
    
    # Create knowledge point
    kp = KnowledgePoint(
        id=kp_data.id,
        course_id=chapter_id,  # Use chapter_id for compatibility
        chapter_id=chapter_id,
        name=kp_data.name,
        type=kp_data.type,
        description=kp_data.description,
        level=kp_data.level,
        sort_order=kp_data.sort_order,
        key_points=kp_data.key_points,
        mastery_criteria=kp_data.mastery_criteria.to_domain() if kp_data.mastery_criteria else None,
        teaching_config=kp_data.teaching_config.to_domain() if kp_data.teaching_config else None,
        content_template=kp_data.content_template,
    )
    
    db._knowledge_points[kp.id] = kp
    
    # Create dependencies
    for dep_id in kp_data.dependencies:
        dep = KnowledgePointDependency(
            id=db._kp_dependency_id_counter,
            kp_id=kp.id,
            depends_on_kp_id=dep_id,
            dependency_type=DependencyType.PREREQUISITE,
        )
        db._kp_dependencies.append(dep)
        db._kp_dependency_id_counter += 1
    
    # Update chapter knowledge point count
    chapter = db._chapters[chapter_id]
    chapter.total_knowledge_points = sum(
        1 for kp in db._knowledge_points.values()
        if kp.chapter_id == chapter_id
    )
    
    return APIResponse(
        success=True,
        data=KnowledgePointResponse.from_domain(kp),
        message="知识点创建成功",
    )


@router.get("/knowledge-points/{kp_id}", response_model=APIResponse[KnowledgePointResponse])
async def get_knowledge_point(
    kp_id: str,
    current_admin: Student = Depends(require_admin),
) -> APIResponse[KnowledgePointResponse]:
    """Get knowledge point by ID.

    Args:
        kp_id: Knowledge point ID.
        current_admin: Current admin user.

    Returns:
        Knowledge point details.

    Raises:
        HTTPException: If knowledge point not found.
    """
    kp = db._knowledge_points.get(kp_id)
    if not kp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识点不存在",
        )
    
    return APIResponse(
        success=True,
        data=KnowledgePointResponse.from_domain(kp),
    )


@router.put("/knowledge-points/{kp_id}", response_model=APIResponse[KnowledgePointResponse])
async def update_knowledge_point(
    kp_id: str,
    kp_data: KnowledgePointUpdate,
    current_admin: Student = Depends(require_admin),
) -> APIResponse[KnowledgePointResponse]:
    """Update knowledge point.

    Args:
        kp_id: Knowledge point ID.
        kp_data: Knowledge point update data.
        current_admin: Current admin user.

    Returns:
        Updated knowledge point.

    Raises:
        HTTPException: If knowledge point not found.
    """
    kp = db._knowledge_points.get(kp_id)
    if not kp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识点不存在",
        )
    
    # Update fields
    update_data = kp_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == 'mastery_criteria' and value:
            value = value.to_domain()
        elif field == 'teaching_config' and value:
            value = value.to_domain()
        setattr(kp, field, value)
    
    # Update timestamp
    from datetime import datetime
    kp.updated_at = datetime.now()
    
    return APIResponse(
        success=True,
        data=KnowledgePointResponse.from_domain(kp),
        message="知识点更新成功",
    )


@router.delete("/knowledge-points/{kp_id}")
async def delete_knowledge_point(
    kp_id: str,
    current_admin: Student = Depends(require_admin),
) -> APIResponse[None]:
    """Delete knowledge point.

    Args:
        kp_id: Knowledge point ID.
        current_admin: Current admin user.

    Returns:
        Success message.

    Raises:
        HTTPException: If knowledge point not found.
    """
    kp = db._knowledge_points.get(kp_id)
    if not kp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识点不存在",
        )
    
    # Check if other KPs depend on this one
    dependents = [dep for dep in db._kp_dependencies if dep.depends_on_kp_id == kp_id]
    if dependents:
        dependent_ids = [dep.kp_id for dep in dependents]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"知识点 {kp_id} 被以下知识点依赖: {', '.join(dependent_ids)}",
        )
    
    # Delete dependencies
    db._kp_dependencies = [
        dep for dep in db._kp_dependencies
        if dep.kp_id != kp_id
    ]
    
    # Delete knowledge point
    del db._knowledge_points[kp_id]
    
    # Update chapter count
    if kp.chapter_id:
        chapter = db._chapters.get(kp.chapter_id)
        if chapter:
            chapter.total_knowledge_points = sum(
                1 for kp in db._knowledge_points.values()
                if kp.chapter_id == kp.chapter_id
            )
    
    return APIResponse(
        success=True,
        message="知识点删除成功",
    )


@router.post("/knowledge-points/{kp_id}/dependencies", response_model=APIResponse[DependencyResponse], status_code=status.HTTP_201_CREATED)
async def add_dependency(
    kp_id: str,
    dep_data: DependencyCreate,
    current_admin: Student = Depends(require_admin),
) -> APIResponse[DependencyResponse]:
    """Add dependency to knowledge point.

    Args:
        kp_id: Knowledge point ID.
        dep_data: Dependency data.
        current_admin: Current admin user.

    Returns:
        Created dependency.

    Raises:
        HTTPException: If KP not found or circular dependency detected.
    """
    # Check both KPs exist
    if kp_id not in db._knowledge_points:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"知识点 {kp_id} 不存在",
        )
    
    if dep_data.depends_on_kp_id not in db._knowledge_points:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"依赖的知识点 {dep_data.depends_on_kp_id} 不存在",
        )
    
    # Check not already exists
    for dep in db._kp_dependencies:
        if dep.kp_id == kp_id and dep.depends_on_kp_id == dep_data.depends_on_kp_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="依赖关系已存在",
            )
    
    # Check for circular dependency (simple check)
    if kp_id == dep_data.depends_on_kp_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能依赖自身",
        )
    
    # Create dependency
    dep = KnowledgePointDependency(
        id=db._kp_dependency_id_counter,
        kp_id=kp_id,
        depends_on_kp_id=dep_data.depends_on_kp_id,
        dependency_type=DependencyType.PREREQUISITE,
    )
    db._kp_dependencies.append(dep)
    db._kp_dependency_id_counter += 1
    
    return APIResponse(
        success=True,
        data=DependencyResponse(
            id=dep.id,
            kp_id=dep.kp_id,
            depends_on_kp_id=dep.depends_on_kp_id,
            dependency_type=dep.dependency_type.value,
        ),
        message="依赖关系添加成功",
    )


@router.delete("/knowledge-points/{kp_id}/dependencies/{dep_id}")
async def remove_dependency(
    kp_id: str,
    dep_id: int,
    current_admin: Student = Depends(require_admin),
) -> APIResponse[None]:
    """Remove dependency from knowledge point.

    Args:
        kp_id: Knowledge point ID.
        dep_id: Dependency ID.
        current_admin: Current admin user.

    Returns:
        Success message.

    Raises:
        HTTPException: If dependency not found.
    """
    # Find and remove dependency
    for i, dep in enumerate(db._kp_dependencies):
        if dep.id == dep_id and dep.kp_id == kp_id:
            db._kp_dependencies.pop(i)
            return APIResponse(
                success=True,
                message="依赖关系删除成功",
            )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="依赖关系不存在",
    )
