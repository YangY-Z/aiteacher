#!/usr/bin/env python3
"""Migrate chapter grade and subject references to foreign keys.

This script updates Chapter entities to use grade_id and subject_id
instead of the deprecated grade and subject fields.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "ai-teacher-backend"))

from app.repositories.chapter_repository import chapter_repository
from app.repositories.grade_repository import grade_repository
from app.repositories.subject_repository import subject_repository


def migrate_chapter_references():
    """Migrate chapter references from string to foreign keys."""
    print("=" * 60)
    print("章节数据迁移：将grade和subject字段映射到外键引用")
    print("=" * 60)

    # Build grade mapping: grade name -> grade ID
    grades = grade_repository.get_all()
    grade_mapping = {grade.name: grade.id for grade in grades}
    print(f"\n年级映射关系：")
    for name, id in grade_mapping.items():
        print(f"  {name} -> {id}")

    # Build subject mapping: subject name -> subject ID
    subjects = subject_repository.get_all()
    subject_mapping = {subject.name: subject.id for subject in subjects}
    print(f"\n科目映射关系：")
    for name, id in subject_mapping.items():
        print(f"  {name} -> {id}")

    # Migrate chapters
    print(f"\n开始迁移章节数据...")
    updated_count = chapter_repository.migrate_grade_subject_references(
        grade_mapping, subject_mapping
    )

    print(f"\n✅ 迁移完成！更新了 {updated_count} 个引用")

    # Verify migration
    print(f"\n验证迁移结果：")
    chapters = chapter_repository.get_all()
    migrated_count = 0
    for chapter in chapters:
        if chapter.grade_id and chapter.subject_id:
            migrated_count += 1
            print(
                f"  ✓ {chapter.name}: "
                f"grade_id={chapter.grade_id}, subject_id={chapter.subject_id}"
            )

    print(f"\n总计：{len(chapters)} 个章节，{migrated_count} 个已迁移")


if __name__ == "__main__":
    migrate_chapter_references()
