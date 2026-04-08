#!/usr/bin/env python3
"""Initialize grade-subject associations.

This script creates initial associations between grades and subjects.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "ai-teacher-backend"))

from app.repositories.grade_repository import grade_repository
from app.repositories.subject_repository import subject_repository


def init_grade_subject_associations():
    """Initialize grade-subject associations."""
    print("Initializing grade-subject associations...")

    # Define initial associations
    associations = [
        # 初一科目
        ("G_C1", "S_MATH", 1),
        ("G_C1", "S_CHINESE", 2),
        ("G_C1", "S_ENGLISH", 3),
        # 初二科目
        ("G_C2", "S_MATH", 1),
        ("G_C2", "S_CHINESE", 2),
        ("G_C2", "S_ENGLISH", 3),
        ("G_C2", "S_PHYSICS", 4),
        # 初三科目
        ("G_C3", "S_MATH", 1),
        ("G_C3", "S_CHINESE", 2),
        ("G_C3", "S_ENGLISH", 3),
        ("G_C3", "S_PHYSICS", 4),
        ("G_C3", "S_CHEMISTRY", 5),
        # 高一科目
        ("G_S1", "S_MATH", 1),
        ("G_S1", "S_CHINESE", 2),
        ("G_S1", "S_ENGLISH", 3),
        ("G_S1", "S_PHYSICS", 4),
        ("G_S1", "S_CHEMISTRY", 5),
        # 高二科目
        ("G_S2", "S_MATH", 1),
        ("G_S2", "S_CHINESE", 2),
        ("G_S2", "S_ENGLISH", 3),
        ("G_S2", "S_PHYSICS", 4),
        ("G_S2", "S_CHEMISTRY", 5),
        # 高三科目
        ("G_S3", "S_MATH", 1),
        ("G_S3", "S_CHINESE", 2),
        ("G_S3", "S_ENGLISH", 3),
        ("G_S3", "S_PHYSICS", 4),
        ("G_S3", "S_CHEMISTRY", 5),
    ]

    created_count = 0
    skipped_count = 0

    for grade_id, subject_id, sort_order in associations:
        try:
            # Check if already exists
            grade = grade_repository.get_by_id(grade_id)
            if not grade:
                print(f"  ⚠️  Grade {grade_id} not found, skipping...")
                skipped_count += 1
                continue

            # Check if subject already added
            if any(s.subject_id == subject_id for s in grade.subjects):
                print(f"  ℹ️  Subject {subject_id} already in grade {grade_id}, skipping...")
                skipped_count += 1
                continue

            # Add association
            grade_repository.add_subject_to_grade(grade_id, subject_id, sort_order)
            print(f"  ✓  Added {subject_id} to {grade_id} (order: {sort_order})")
            created_count += 1

        except Exception as e:
            print(f"  ✗  Failed to add {subject_id} to {grade_id}: {e}")
            skipped_count += 1

    print(f"\n完成！创建 {created_count} 个关联，跳过 {skipped_count} 个。")


if __name__ == "__main__":
    init_grade_subject_associations()
