"""In-memory database implementation for MVP.

This module provides an in-memory database that simulates
PostgreSQL, MongoDB, and Redis for development and testing.
Supports file-based persistence for student data.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from app.models.student import Student, StudentStatus, Grade

logger = logging.getLogger(__name__)
from app.models.course import (
    Course,
    KnowledgePoint,
    KnowledgePointDependency,
    CourseStatus,
    KnowledgePointType,
    Subject,
    MasteryCriteria,
    TeachingConfig,
    DependencyType,
)
from app.models.learning import (
    StudentProfile,
    LearningRecord,
    LearningSession,
    LearningStatus,
    SessionStatus,
)
from app.models.assessment import AssessmentQuestion, Difficulty, QuestionType


@dataclass
class InMemoryDatabase:
    """In-memory database for development and testing.

    Simulates the behavior of PostgreSQL, MongoDB, and Redis.
    Supports file-based persistence for student data.
    """

    # Data file path for persistence
    _data_file: str = field(default="data/students.json", repr=False)

    # Student storage
    _students: dict[int, Student] = field(default_factory=dict)
    _student_id_counter: int = 0

    # Course storage
    _courses: dict[str, Course] = field(default_factory=dict)

    # Knowledge point storage
    _knowledge_points: dict[str, KnowledgePoint] = field(default_factory=dict)

    # Knowledge point dependencies
    _kp_dependencies: list[KnowledgePointDependency] = field(default_factory=list)
    _kp_dependency_id_counter: int = 0

    # Learning records
    _learning_records: dict[int, LearningRecord] = field(default_factory=dict)
    _learning_record_id_counter: int = 0

    # Student profiles
    _student_profiles: dict[int, StudentProfile] = field(default_factory=dict)
    _student_profile_id_counter: int = 0

    # Learning sessions
    _learning_sessions: dict[str, LearningSession] = field(default_factory=dict)

    # Assessment questions
    _assessment_questions: dict[str, AssessmentQuestion] = field(default_factory=dict)

    # Student answers
    _student_answers: dict[int, Any] = field(default_factory=dict)
    _student_answer_id_counter: int = 0

    # Session logs (simulating MongoDB)
    _session_logs: list[dict[str, Any]] = field(default_factory=list)

    # Cache (simulating Redis)
    _cache: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize with seed data and load persisted data."""
        self._initialize_seed_data()
        self._load_students_from_file()

    def _get_data_file_path(self) -> Path:
        """Get the absolute path to the data file.

        Returns:
            Path to the data file.
        """
        # Use project root directory
        project_root = Path(__file__).parent.parent.parent
        return project_root / self._data_file

    def _load_students_from_file(self) -> None:
        """Load students and profiles from JSON file if it exists."""
        file_path = self._get_data_file_path()

        if not file_path.exists():
            logger.debug(f"Student data file not found: {file_path}")
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            students_data = data.get("students", [])
            for student_dict in students_data:
                student = Student(
                    id=student_dict["id"],
                    name=student_dict["name"],
                    grade=Grade(student_dict["grade"]),
                    password_hash=student_dict["password_hash"],
                    phone=student_dict.get("phone"),
                    avatar_url=student_dict.get("avatar_url"),
                    status=StudentStatus(student_dict.get("status", "active")),
                    last_login_at=self._parse_datetime(student_dict.get("last_login_at")),
                    created_at=self._parse_datetime(student_dict.get("created_at")),
                    updated_at=self._parse_datetime(student_dict.get("updated_at")),
                )
                self._students[student.id] = student

            # Restore ID counter
            self._student_id_counter = data.get("next_id", len(self._students))

            # Load student profiles
            profiles_data = data.get("profiles", [])
            for profile_dict in profiles_data:
                profile = StudentProfile(
                    id=profile_dict["id"],
                    student_id=profile_dict["student_id"],
                    course_id=profile_dict["course_id"],
                    current_kp_id=profile_dict.get("current_kp_id"),
                    completed_kp_ids=profile_dict.get("completed_kp_ids", []),
                    mastered_kp_ids=profile_dict.get("mastered_kp_ids", []),
                    skipped_kp_ids=profile_dict.get("skipped_kp_ids", []),
                    mastery_rate=profile_dict.get("mastery_rate", 0.0),
                    total_time=profile_dict.get("total_time", 0),
                    session_count=profile_dict.get("session_count", 0),
                    last_session_at=self._parse_datetime(profile_dict.get("last_session_at")),
                    created_at=self._parse_datetime(profile_dict.get("created_at")),
                    updated_at=self._parse_datetime(profile_dict.get("updated_at")),
                )
                self._student_profiles[profile.id] = profile
            
            # Restore profile ID counter
            self._student_profile_id_counter = data.get("next_profile_id", len(self._student_profiles))

            logger.info(f"Loaded {len(self._students)} students and {len(self._student_profiles)} profiles from {file_path}")

        except Exception as e:
            logger.error(f"Failed to load students from file: {e}")

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string.

        Args:
            dt_str: ISO format datetime string.

        Returns:
            datetime object or None.
        """
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str)
        except ValueError:
            return None

    def _save_students_to_file(self) -> None:
        """Save students and profiles to JSON file."""
        file_path = self._get_data_file_path()

        try:
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            students_data = []
            for student in self._students.values():
                students_data.append({
                    "id": student.id,
                    "name": student.name,
                    "grade": student.grade.value,
                    "password_hash": student.password_hash,
                    "phone": student.phone,
                    "avatar_url": student.avatar_url,
                    "status": student.status.value,
                    "last_login_at": student.last_login_at.isoformat() if student.last_login_at else None,
                    "created_at": student.created_at.isoformat() if student.created_at else None,
                    "updated_at": student.updated_at.isoformat() if student.updated_at else None,
                })

            # Save profiles
            profiles_data = []
            for profile in self._student_profiles.values():
                profiles_data.append({
                    "id": profile.id,
                    "student_id": profile.student_id,
                    "course_id": profile.course_id,
                    "current_kp_id": profile.current_kp_id,
                    "completed_kp_ids": profile.completed_kp_ids,
                    "mastered_kp_ids": profile.mastered_kp_ids,
                    "skipped_kp_ids": profile.skipped_kp_ids,
                    "mastery_rate": profile.mastery_rate,
                    "total_time": profile.total_time,
                    "session_count": profile.session_count,
                    "last_session_at": profile.last_session_at.isoformat() if profile.last_session_at else None,
                    "created_at": profile.created_at.isoformat() if profile.created_at else None,
                    "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
                })

            data = {
                "students": students_data,
                "next_id": self._student_id_counter,
                "profiles": profiles_data,
                "next_profile_id": self._student_profile_id_counter,
                "updated_at": datetime.now().isoformat(),
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug(f"Saved {len(students_data)} students and {len(profiles_data)} profiles to {file_path}")

        except Exception as e:
            logger.error(f"Failed to save students to file: {e}")

    def save_student_data(self) -> None:
        """Public method to trigger student data save."""
        self._save_students_to_file()

    def _initialize_seed_data(self) -> None:
        """Initialize the database with seed data."""
        # Initialize the "一次函数" course with 32 knowledge points
        self._init_linear_function_course()

    def _init_linear_function_course(self) -> None:
        """Initialize the linear function course with knowledge points."""
        # Create course
        course = Course(
            id="MATH_JUNIOR_01",
            name="一次函数",
            grade="初一",
            subject=Subject.MATH,
            description="初一数学一次函数单元，包含32个知识点",
            total_knowledge_points=32,
            estimated_hours=12.0,
            status=CourseStatus.ACTIVE,
        )
        self._courses[course.id] = course

        # Define all knowledge points
        kp_data = [
            # Level 0: 基础概念层
            ("K1", "坐标系", KnowledgePointType.CONCEPT, "平面直角坐标系的建立，x轴、y轴、原点", 0),
            ("K2", "点的坐标", KnowledgePointType.SKILL, "用有序数对(x,y)表示平面上点的位置", 1),
            ("K3", "象限", KnowledgePointType.CONCEPT, "坐标平面被两轴分成四个象限及其特征", 0),
            ("K4", "变量", KnowledgePointType.CONCEPT, "可以取不同数值的量", 0),
            ("K5", "常量", KnowledgePointType.CONCEPT, "数值固定不变的量", 0),
            # Level 1: 函数基础层
            ("K6", "函数定义", KnowledgePointType.CONCEPT, "设x和y是两个变量，若x每取一个值，y都有唯一确定的值与之对应", 1),
            ("K7", "自变量与因变量", KnowledgePointType.CONCEPT, "主动变化的量为自变量，随之变化的量为因变量", 2),
            ("K8", "函数的定义域", KnowledgePointType.CONCEPT, "自变量x允许取值的范围", 2),
            ("K9", "函数值", KnowledgePointType.SKILL, "当x取某值时，y对应的值", 2),
            ("K10", "函数解析式", KnowledgePointType.CONCEPT, "用数学式子表示函数关系", 2),
            ("K11", "函数的三种表示法", KnowledgePointType.SKILL, "解析式法、列表法、图象法", 2),
            # Level 2: 正比例函数层
            ("K12", "正比例函数定义", KnowledgePointType.CONCEPT, "y=kx(k≠0)形式的函数", 3),
            ("K13", "正比例函数图象", KnowledgePointType.SKILL, "正比例函数图象是过原点的直线", 3),
            ("K14", "正比例函数性质", KnowledgePointType.FORMULA, "k>0过一三象限且递增；k<0过二四象限且递减", 3),
            ("K15", "一次函数定义", KnowledgePointType.CONCEPT, "y=kx+b(k≠0)形式的函数", 3),
            ("K16", "一次函数与正比例函数关系", KnowledgePointType.CONCEPT, "当b=0时，一次函数退化为正比例函数", 3),
            # Level 3: 图象与性质层
            ("K17", "描点法画函数图象", KnowledgePointType.SKILL, "列表、描点、连线的作图方法", 4),
            ("K18", "一次函数图象特征", KnowledgePointType.SKILL, "一次函数图象是一条直线", 4),
            ("K19", "两点确定直线", KnowledgePointType.SKILL, "画一次函数图象只需描出两点连线", 4),
            ("K20", "截距概念", KnowledgePointType.CONCEPT, "直线与y轴交点的纵坐标，即b的值", 4),
            ("K21", "斜率概念", KnowledgePointType.CONCEPT, "直线倾斜程度的度量，即k的值", 4),
            ("K22", "k对图象方向的影响", KnowledgePointType.FORMULA, "k>0从左向右上升；k<0从左向右下降", 4),
            ("K23", "b对图象位置的影响", KnowledgePointType.FORMULA, "b>0与y轴交于正半轴；b<0交于负半轴", 4),
            ("K24", "一次函数增减性", KnowledgePointType.FORMULA, "k>0时y随x增大而增大；k<0时y随x增大而减小", 4),
            # Level 4: 综合判断层
            ("K25", "平移变换", KnowledgePointType.SKILL, "上下平移改变b值，左右平移改变x", 5),
            ("K26", "k与b的综合判断", KnowledgePointType.SKILL, "根据k、b符号判断图象经过的象限", 5),
            # Level 5: 应用层
            ("K27", "待定系数法", KnowledgePointType.SKILL, "设出函数解析式，代入条件求k、b", 6),
            ("K28", "由图象求解析式", KnowledgePointType.SKILL, "从图象上读取点坐标，用待定系数法求解析式", 6),
            ("K29", "求交点坐标", KnowledgePointType.SKILL, "联立两一次函数解析式求解方程组", 6),
            ("K30", "实际问题建模", KnowledgePointType.SKILL, "将实际问题转化为一次函数求解", 6),
            ("K31", "一次函数与方程的关系", KnowledgePointType.CONCEPT, "求ax+b=0的解等价于求y=ax+b与x轴交点横坐标", 6),
            ("K32", "一次函数与不等式的关系", KnowledgePointType.CONCEPT, "图象在x轴上方/下方对应的x范围即为不等式解集", 6),
        ]

        # Create knowledge points
        for kp_id, name, kp_type, description, level in kp_data:
            mastery_criteria = self._get_mastery_criteria(kp_type)
            teaching_config = self._get_teaching_config(kp_type)

            kp = KnowledgePoint(
                id=kp_id,
                course_id=course.id,
                name=name,
                type=kp_type,
                description=description,
                level=level,
                sort_order=level * 10 + int(kp_id[1:]),
                mastery_criteria=mastery_criteria,
                teaching_config=teaching_config,
            )
            self._knowledge_points[kp_id] = kp

        # Define dependencies (from the spec)
        dependencies = [
            # K1 -> K2, K3
            ("K2", "K1"),
            ("K3", "K1"),
            # K4, K5 -> K6
            ("K6", "K4"),
            ("K6", "K5"),
            # K6 -> K7, K8, K9, K10
            ("K7", "K6"),
            ("K8", "K6"),
            ("K9", "K6"),
            ("K10", "K6"),
            # K10 -> K11
            ("K11", "K10"),
            # K6, K10 -> K12
            ("K12", "K6"),
            ("K12", "K10"),
            # K11, K12 -> K13
            ("K13", "K11"),
            ("K13", "K12"),
            # K12, K3 -> K14
            ("K14", "K12"),
            ("K14", "K3"),
            # K12, K10 -> K15
            ("K15", "K12"),
            ("K15", "K10"),
            # K15 -> K16
            ("K16", "K15"),
            # K11, K2 -> K17
            ("K17", "K11"),
            ("K17", "K2"),
            # K15 -> K18
            ("K18", "K15"),
            # K17 -> K19
            ("K19", "K17"),
            # K15 -> K20, K21
            ("K20", "K15"),
            ("K21", "K15"),
            # K18, K21 -> K22
            ("K22", "K18"),
            ("K22", "K21"),
            # K20 -> K23
            ("K23", "K20"),
            # K21, K18 -> K24
            ("K24", "K21"),
            ("K24", "K18"),
            # K22, K23, K3 -> K26
            ("K26", "K22"),
            ("K26", "K23"),
            ("K26", "K3"),
            # K18, K20 -> K25
            ("K25", "K18"),
            ("K25", "K20"),
            # K15, K9 -> K27
            ("K27", "K15"),
            ("K27", "K9"),
            # K27, K19 -> K28
            ("K28", "K27"),
            ("K28", "K19"),
            # K27 -> K29
            ("K29", "K27"),
            # K15, K28 -> K30
            ("K30", "K15"),
            ("K30", "K28"),
            # K18 -> K31, K32
            ("K31", "K18"),
            ("K32", "K18"),
        ]

        for kp_id, depends_on_kp_id in dependencies:
            dep = KnowledgePointDependency(
                id=self._kp_dependency_id_counter,
                kp_id=kp_id,
                depends_on_kp_id=depends_on_kp_id,
                dependency_type=DependencyType.PREREQUISITE,
            )
            self._kp_dependencies.append(dep)
            self._kp_dependency_id_counter += 1

    def _get_mastery_criteria(self, kp_type: KnowledgePointType) -> MasteryCriteria:
        """Get mastery criteria based on knowledge point type."""
        if kp_type == KnowledgePointType.CONCEPT:
            return MasteryCriteria(
                type="concept_check",
                method="选择题",
                question_count=2,
                pass_threshold=1,
            )
        elif kp_type == KnowledgePointType.FORMULA:
            return MasteryCriteria(
                type="formula_check",
                method="填空题",
                question_count=3,
                pass_threshold=2,
            )
        else:  # SKILL
            return MasteryCriteria(
                type="skill_check",
                method="计算题",
                question_count=2,
                pass_threshold=1,
            )

    def _get_teaching_config(self, kp_type: KnowledgePointType) -> TeachingConfig:
        """Get teaching configuration based on knowledge point type."""
        return TeachingConfig(
            use_examples=True,
            ask_questions=True,
            question_positions=["讲解中段", "讲解结束"],
        )

    # Student operations
    def get_next_student_id(self) -> int:
        """Get the next student ID."""
        self._student_id_counter += 1
        return self._student_id_counter

    # Learning record operations
    def get_next_learning_record_id(self) -> int:
        """Get the next learning record ID."""
        self._learning_record_id_counter += 1
        return self._learning_record_id_counter

    # Student profile operations
    def get_next_student_profile_id(self) -> int:
        """Get the next student profile ID."""
        self._student_profile_id_counter += 1
        return self._student_profile_id_counter

    # Student answer operations
    def get_next_student_answer_id(self) -> int:
        """Get the next student answer ID."""
        self._student_answer_id_counter += 1
        return self._student_answer_id_counter

    # Cache operations (Redis simulation)
    def cache_get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        return self._cache.get(key)

    def cache_set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time to live in seconds (ignored in memory implementation).
        """
        self._cache[key] = value

    def cache_delete(self, key: str) -> bool:
        """Delete a value from cache."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    # Session log operations (MongoDB simulation)
    def add_session_log(self, log: dict[str, Any]) -> None:
        """Add a session log entry."""
        self._session_logs.append(log)

    def get_session_logs(
        self,
        session_id: Optional[str] = None,
        student_id: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Get session logs with optional filtering."""
        logs = self._session_logs
        if session_id:
            logs = [l for l in logs if l.get("session_id") == session_id]
        if student_id:
            logs = [l for l in logs if l.get("student_id") == student_id]
        return logs


# Global database instance
db = InMemoryDatabase()
