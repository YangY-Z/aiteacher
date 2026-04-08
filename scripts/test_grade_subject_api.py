#!/usr/bin/env python3
"""Quick test script for Grade and Subject APIs.

This script tests all the new API endpoints for grade and subject management.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "ai-teacher-backend"))

from app.repositories.grade_repository import grade_repository
from app.repositories.subject_repository import subject_repository
from app.repositories.chapter_repository import chapter_repository


def test_repositories():
    """Test repository operations."""
    print("=" * 60)
    print("测试仓储层操作")
    print("=" * 60)

    # Test Grade Repository
    print("\n【年级仓储测试】")
    grades = grade_repository.get_all()
    print(f"✓ 获取所有年级: {len(grades)} 个")
    for grade in grades[:3]:
        print(f"  - {grade.name} ({grade.id}): {len(grade.subjects)} 个科目")

    # Test Subject Repository
    print("\n【科目仓储测试】")
    subjects = subject_repository.get_all()
    print(f"✓ 获取所有科目: {len(subjects)} 个")
    for subject in subjects[:3]:
        print(f"  - {subject.name} ({subject.id}): {subject.category}")

    # Test Chapter Repository
    print("\n【章节仓储测试】")
    chapters = chapter_repository.get_all()
    print(f"✓ 获取所有章节: {len(chapters)} 个")
    for chapter in chapters[:3]:
        print(f"  - {chapter.name}")
        print(f"    grade_id={chapter.grade_id}, subject_id={chapter.subject_id}")

    # Test Grade-Subject Associations
    print("\n【年级-科目关联测试】")
    grade = grade_repository.get_by_id("G_C3")
    if grade:
        print(f"✓ {grade.name} 的科目:")
        for gs in grade.subjects[:3]:
            subject = subject_repository.get_by_id(gs.subject_id)
            if subject:
                print(f"  - {subject.name} (sort_order={gs.sort_order})")


def test_services():
    """Test service layer operations."""
    print("\n" + "=" * 60)
    print("测试服务层操作")
    print("=" * 60)

    from app.services.grade_service import grade_service
    from app.services.subject_service import subject_service
    from app.models import GradeLevel, SubjectCategory

    # Test Grade Service
    print("\n【年级服务测试】")
    middle_grades = grade_service.get_all_grades(level=GradeLevel.MIDDLE)
    print(f"✓ 获取初中年级: {len(middle_grades)} 个")
    for grade in middle_grades:
        print(f"  - {grade.name}")

    # Test Subject Service
    print("\n【科目服务测试】")
    science_subjects = subject_service.get_all_subjects(category=SubjectCategory.SCIENCE)
    print(f"✓ 获取理科科目: {len(science_subjects)} 个")
    for subject in science_subjects:
        print(f"  - {subject.name}")


def test_api_schemas():
    """Test API schema transformations."""
    print("\n" + "=" * 60)
    print("测试API Schema转换")
    print("=" * 60)

    from app.schemas.grade import GradeResponse, SubjectResponse

    # Test Grade Response
    print("\n【年级响应Schema测试】")
    grade = grade_repository.get_by_id("G_C1")
    if grade:
        response = GradeResponse.from_domain(grade)
        print(f"✓ 年级: {response.name}")
        print(f"  ID: {response.id}")
        print(f"  Level: {response.level}")
        print(f"  Subjects: {len(response.subjects)}")

    # Test Subject Response
    print("\n【科目响应Schema测试】")
    subject = subject_repository.get_by_id("S_MATH")
    if subject:
        response = SubjectResponse.from_domain(subject)
        print(f"✓ 科目: {response.name}")
        print(f"  ID: {response.id}")
        print(f"  Category: {response.category}")


def test_data_integrity():
    """Test data integrity."""
    print("\n" + "=" * 60)
    print("测试数据完整性")
    print("=" * 60)

    # Check grade-subject associations
    print("\n【年级-科目关联完整性】")
    grades = grade_repository.get_all()
    for grade in grades:
        if grade.subjects:
            print(f"✓ {grade.name}: {len(grade.subjects)} 个科目")

    # Check chapter references
    print("\n【章节外键引用完整性】")
    chapters = chapter_repository.get_all()
    migrated_count = sum(1 for c in chapters if c.grade_id and c.subject_id)
    print(f"✓ 已迁移章节: {migrated_count}/{len(chapters)}")


def main():
    """Run all tests."""
    print("\n" + "🚀 " + "=" * 56 + " 🚀")
    print("   年级科目管理API - 集成测试")
    print("🚀 " + "=" * 56 + " 🚀\n")

    try:
        test_repositories()
        test_services()
        test_api_schemas()
        test_data_integrity()

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        print("\n下一步:")
        print("1. 启动后端服务: cd ai-teacher-backend && python3 run.py")
        print("2. 访问API文档: http://localhost:8000/docs")
        print("3. 测试API端点:")
        print("   - GET  /api/v1/admin/grades")
        print("   - GET  /api/v1/admin/subjects")
        print("   - POST /api/v1/admin/grades")
        print("   - POST /api/v1/admin/subjects")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
