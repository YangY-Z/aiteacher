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

from app.models.student import Student, StudentStatus, Grade, UserRole

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
    Edition,
    Chapter,
)
from app.models.learning import (
    StudentProfile,
    LearningRecord,
    LearningSession,
    LearningStatus,
    SessionStatus,
)
from app.models.assessment import AssessmentQuestion, Difficulty, QuestionType
from app.models.learner_profile import LearnerProfile
from app.models.diagnostic import (
    DiagnosticSession,
    DiagnosticQuestion,
    DiagnosticAnswer,
)


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

    # Chapter storage
    _chapters: dict[str, Chapter] = field(default_factory=dict)

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

    # Learner profiles (for adaptive learning)
    _learner_profiles: dict[int, LearnerProfile] = field(default_factory=dict)
    _learner_profile_id_counter: int = 0

    # Diagnostic sessions
    _diagnostic_sessions: dict[str, DiagnosticSession] = field(default_factory=dict)

    # Diagnostic questions
    _diagnostic_questions: dict[str, DiagnosticQuestion] = field(default_factory=dict)

    # Diagnostic answers
    _diagnostic_answers: dict[int, DiagnosticAnswer] = field(default_factory=dict)
    _diagnostic_answer_id_counter: int = 0

    def __post_init__(self) -> None:
        """Initialize with seed data and load persisted data."""
        self._initialize_seed_data()
        self._load_students_from_file()
        self.load_learner_profiles_from_file()
        self.load_learning_sessions_from_file()
        self.load_media_resources_from_file()

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
                    edition=Edition(student_dict.get("edition", "人教版")),
                    password_hash=student_dict["password_hash"],
                    phone=student_dict.get("phone"),
                    avatar_url=student_dict.get("avatar_url"),
                    status=StudentStatus(student_dict.get("status", "active")),
                    role=UserRole(student_dict.get("role", "student")),
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
                    "edition": student.edition.value if hasattr(student.edition, 'value') else str(student.edition),
                    "password_hash": student.password_hash,
                    "phone": student.phone,
                    "avatar_url": student.avatar_url,
                    "status": student.status.value,
                    "role": student.role.value,
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
        
        # Create default admin account
        self._create_default_admin()
    
    def _create_default_admin(self) -> None:
        """Create default admin account if not exists."""
        from app.core.security import hash_password
        
        # Check if admin already exists
        admin_exists = any(
            student.role == UserRole.ADMIN
            for student in self._students.values()
        )
        
        if not admin_exists:
            admin = Student(
                id=999,
                name="系统管理员",
                phone="admin",
                grade=Grade.GRADE_7,
                edition=Edition.RENJIAO,
                password_hash=hash_password("admin@2026"),
                role=UserRole.ADMIN,
                status=StudentStatus.ACTIVE,
            )
            self._students[admin.id] = admin
            logger.info("Created default admin account (phone: admin, password: admin@2026)")

    def _init_linear_function_course(self) -> None:
        """Initialize seed data with correct Course → Chapter hierarchy."""
        self._init_course_renjiao_8_math()
        self._init_course_renjiao_8_chinese()
        self._init_course_renjiao_7_math()

    def _init_course_renjiao_8_math(self) -> None:
        """初二数学（人教版）—— 包含一次函数、二次根式、勾股定理、平行四边形、数据的分析"""
        course = Course(
            id="COURSE_RENJIAO_8_MATH",
            name="初二数学（人教版）",
            grade="初二",
            edition=Edition.RENJIAO,
            subject=Subject.MATH,
            description="人教版初二数学全册",
            total_knowledge_points=50,
            estimated_hours=40.0,
            status=CourseStatus.ACTIVE,
        )
        self._courses[course.id] = course

        ch1 = Chapter(
            id="CH_8MATH_01", name="一次函数", grade="初二", edition=Edition.RENJIAO,
            subject=Subject.MATH, course_id=course.id,
            prerequisite_chapter_ids=[],
            description="变量、函数定义、正比例函数、一次函数图象与性质、待定系数法、综合应用",
            sort_order=0, total_knowledge_points=32, estimated_hours=12.0,
            status=CourseStatus.ACTIVE,
            level_descriptions={0: "基础概念层", 1: "核心概念层", 2: "函数基础层",
                3: "正比例与一次函数层", 4: "图象与性质层", 5: "变换层", 6: "综合应用层"},
        )
        ch2 = Chapter(
            id="CH_8MATH_02", name="二次根式", grade="初二", edition=Edition.RENJIAO,
            subject=Subject.MATH, course_id=course.id,
            prerequisite_chapter_ids=["CH_8MATH_01"],
            description="二次根式概念、性质、化简与运算",
            sort_order=1, total_knowledge_points=8, estimated_hours=8.0,
            status=CourseStatus.ACTIVE,
        )
        ch3 = Chapter(
            id="CH_8MATH_03", name="勾股定理", grade="初二", edition=Edition.RENJIAO,
            subject=Subject.MATH, course_id=course.id,
            prerequisite_chapter_ids=["CH_8MATH_02"],
            description="定理理解、逆定理、直角三角形判定与实际应用",
            sort_order=2, total_knowledge_points=6, estimated_hours=8.0,
            status=CourseStatus.ACTIVE,
        )
        ch4 = Chapter(
            id="CH_8MATH_04", name="平行四边形", grade="初二", edition=Edition.RENJIAO,
            subject=Subject.MATH, course_id=course.id,
            prerequisite_chapter_ids=["CH_8MATH_01"],
            description="性质、判定、特殊平行四边形与证明应用",
            sort_order=3, total_knowledge_points=8, estimated_hours=10.0,
            status=CourseStatus.ACTIVE,
        )
        ch5 = Chapter(
            id="CH_8MATH_05", name="数据的分析", grade="初二", edition=Edition.RENJIAO,
            subject=Subject.MATH, course_id=course.id,
            prerequisite_chapter_ids=["CH_8MATH_01"],
            description="平均数、中位数、众数、方差与数据决策",
            sort_order=4, total_knowledge_points=4, estimated_hours=6.0,
            status=CourseStatus.ACTIVE,
        )
        for ch in [ch1, ch2, ch3, ch4, ch5]:
            self._chapters[ch.id] = ch

        # KP data for 一次函数 (32 KPs)
        kp_data_ch1 = [
            ("K1", "坐标系", KnowledgePointType.CONCEPT, "平面直角坐标系的建立，x轴、y轴、原点", 0),
            ("K2", "点的坐标", KnowledgePointType.SKILL, "用有序数对(x,y)表示平面上点的位置", 0),
            ("K3", "象限", KnowledgePointType.CONCEPT, "坐标平面被两轴分成四个象限及其特征", 0),
            ("K4", "变量", KnowledgePointType.CONCEPT, "可以取不同数值的量", 0),
            ("K5", "常量", KnowledgePointType.CONCEPT, "数值固定不变的量", 0),
            ("K6", "函数定义", KnowledgePointType.CONCEPT, "设x和y是两个变量，若x每取一个值，y都有唯一确定的值与之对应", 1),
            ("K7", "自变量与因变量", KnowledgePointType.CONCEPT, "主动变化的量为自变量，随之变化的量为因变量", 1),
            ("K8", "函数的定义域", KnowledgePointType.CONCEPT, "自变量x允许取值的范围", 1),
            ("K9", "函数值", KnowledgePointType.SKILL, "当x取某值时，y对应的值", 1),
            ("K10", "函数解析式", KnowledgePointType.CONCEPT, "用数学式子表示函数关系", 1),
            ("K11", "函数的三种表示法", KnowledgePointType.SKILL, "解析式法、列表法、图象法", 1),
            ("K12", "正比例函数定义", KnowledgePointType.CONCEPT, "y=kx(k≠0)形式的函数", 2),
            ("K13", "正比例函数图象", KnowledgePointType.SKILL, "正比例函数图象是过原点的直线", 2),
            ("K14", "正比例函数性质", KnowledgePointType.FORMULA, "k>0过一三象限且递增；k<0过二四象限且递减", 2),
            ("K15", "一次函数定义", KnowledgePointType.CONCEPT, "y=kx+b(k≠0)形式的函数", 2),
            ("K16", "一次函数与正比例函数关系", KnowledgePointType.CONCEPT, "当b=0时，一次函数退化为正比例函数", 2),
            ("K17", "描点法画函数图象", KnowledgePointType.SKILL, "列表、描点、连线的作图方法", 3),
            ("K18", "一次函数图象特征", KnowledgePointType.SKILL, "一次函数图象是一条直线", 3),
            ("K19", "两点确定直线", KnowledgePointType.SKILL, "画一次函数图象只需描出两点连线", 3),
            ("K20", "截距概念", KnowledgePointType.CONCEPT, "直线与y轴交点的纵坐标，即b的值", 3),
            ("K21", "斜率概念", KnowledgePointType.CONCEPT, "直线倾斜程度的度量，即k的值", 3),
            ("K22", "k对图象方向的影响", KnowledgePointType.FORMULA, "k>0从左向右上升；k<0从左向右下降", 3),
            ("K23", "b对图象位置的影响", KnowledgePointType.FORMULA, "b>0与y轴交于正半轴；b<0交于负半轴", 3),
            ("K24", "一次函数增减性", KnowledgePointType.FORMULA, "k>0时y随x增大而增大；k<0时y随x增大而减小", 3),
            ("K25", "平移变换", KnowledgePointType.SKILL, "上下平移改变b值，左右平移改变x", 4),
            ("K26", "k与b的综合判断", KnowledgePointType.SKILL, "根据k、b符号判断图象经过的象限", 4),
            ("K27", "待定系数法", KnowledgePointType.SKILL, "设出函数解析式，代入条件求k、b", 5),
            ("K28", "由图象求解析式", KnowledgePointType.SKILL, "从图象上读取点坐标，用待定系数法求解析式", 5),
            ("K29", "求交点坐标", KnowledgePointType.SKILL, "联立两一次函数解析式求解方程组", 5),
            ("K30", "实际问题建模", KnowledgePointType.SKILL, "将实际问题转化为一次函数求解", 5),
            ("K31", "一次函数与方程的关系", KnowledgePointType.CONCEPT, "求ax+b=0的解等价于求y=ax+b与x轴交点横坐标", 5),
            ("K32", "一次函数与不等式的关系", KnowledgePointType.CONCEPT, "图象在x轴上方/下方对应的x范围即为不等式解集", 5),
        ]
        for kp_id, name, kp_type, desc, level in kp_data_ch1:
            self._knowledge_points[kp_id] = KnowledgePoint(
                id=kp_id, course_id=course.id, chapter_id=ch1.id,
                name=name, type=kp_type, description=desc, level=level,
                sort_order=level * 10 + int(kp_id[1:]),
                mastery_criteria=self._get_mastery_criteria(kp_type),
                teaching_config=self._get_teaching_config(kp_type),
            )

        # KP dependencies for 一次函数 (same as before)
        deps_ch1 = [
            ("K2","K1"),("K3","K1"),("K6","K4"),("K6","K5"),("K7","K6"),("K8","K6"),
            ("K9","K6"),("K10","K6"),("K11","K10"),("K12","K6"),("K12","K10"),
            ("K13","K11"),("K13","K12"),("K14","K12"),("K14","K3"),("K15","K12"),
            ("K15","K10"),("K16","K15"),("K17","K11"),("K17","K2"),("K18","K15"),
            ("K19","K17"),("K20","K15"),("K21","K15"),("K22","K18"),("K22","K21"),
            ("K23","K20"),("K24","K21"),("K24","K18"),("K26","K22"),("K26","K23"),
            ("K26","K3"),("K25","K18"),("K25","K20"),("K27","K15"),("K27","K9"),
            ("K28","K27"),("K28","K19"),("K29","K27"),("K30","K15"),("K30","K28"),
            ("K31","K18"),("K32","K18"),
        ]
        for kp_id, dep_id in deps_ch1:
            self._kp_dependencies.append(KnowledgePointDependency(
                id=self._kp_dependency_id_counter, kp_id=kp_id,
                depends_on_kp_id=dep_id, dependency_type=DependencyType.PREREQUISITE,
            ))
            self._kp_dependency_id_counter += 1

    def _init_course_renjiao_8_chinese(self) -> None:
        """初二语文（人教版）"""
        course = Course(
            id="COURSE_RENJIAO_8_CHINESE",
            name="初二语文（人教版）",
            grade="初二",
            edition=Edition.RENJIAO,
            subject=Subject.CHINESE,
            description="人教版初二语文全册",
            total_knowledge_points=12,
            estimated_hours=30.0,
            status=CourseStatus.ACTIVE,
        )
        self._courses[course.id] = course

        chapters = [
            Chapter(id="CH_8CHI_01", name="现代文阅读", grade="初二", edition=Edition.RENJIAO,
                subject=Subject.CHINESE, course_id=course.id,
                prerequisite_chapter_ids=[], sort_order=0,
                description="记叙文、说明文阅读方法", status=CourseStatus.ACTIVE),
            Chapter(id="CH_8CHI_02", name="文言文阅读", grade="初二", edition=Edition.RENJIAO,
                subject=Subject.CHINESE, course_id=course.id,
                prerequisite_chapter_ids=[], sort_order=1,
                description="常见文言实词、虚词、句式", status=CourseStatus.ACTIVE),
            Chapter(id="CH_8CHI_03", name="作文写作", grade="初二", edition=Edition.RENJIAO,
                subject=Subject.CHINESE, course_id=course.id,
                prerequisite_chapter_ids=["CH_8CHI_01", "CH_8CHI_02"], sort_order=2,
                description="记叙文写作方法与技巧", status=CourseStatus.ACTIVE),
        ]
        for ch in chapters:
            self._chapters[ch.id] = ch

    def _init_course_renjiao_7_math(self) -> None:
        """初一数学（人教版）"""
        course = Course(
            id="COURSE_RENJIAO_7_MATH",
            name="初一数学（人教版）",
            grade="初一",
            edition=Edition.RENJIAO,
            subject=Subject.MATH,
            description="人教版初一数学全册",
            total_knowledge_points=20,
            estimated_hours=35.0,
            status=CourseStatus.ACTIVE,
        )
        self._courses[course.id] = course

        chapters = [
            Chapter(id="CH_7MATH_01", name="有理数", grade="初一", edition=Edition.RENJIAO,
                subject=Subject.MATH, course_id=course.id,
                prerequisite_chapter_ids=[], sort_order=0,
                description="正负数、数轴、相反数、绝对值、有理数运算", status=CourseStatus.ACTIVE),
            Chapter(id="CH_7MATH_02", name="整式的加减", grade="初一", edition=Edition.RENJIAO,
                subject=Subject.MATH, course_id=course.id,
                prerequisite_chapter_ids=["CH_7MATH_01"], sort_order=1,
                description="单项式、多项式、合并同类项", status=CourseStatus.ACTIVE),
            Chapter(id="CH_7MATH_03", name="一元一次方程", grade="初一", edition=Edition.RENJIAO,
                subject=Subject.MATH, course_id=course.id,
                prerequisite_chapter_ids=["CH_7MATH_02"], sort_order=2,
                description="方程概念、解法、实际应用", status=CourseStatus.ACTIVE),
        ]
        for ch in chapters:
            self._chapters[ch.id] = ch

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
    def get_student(self, student_id: int) -> Optional[Student]:
        """Get a student by ID.

        Args:
            student_id: Student ID.

        Returns:
            Student object or None if not found.
        """
        return self._students.get(student_id)

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

    # Learner profile operations
    def get_next_learner_profile_id(self) -> int:
        """Get the next learner profile ID."""
        self._learner_profile_id_counter += 1
        return self._learner_profile_id_counter

    # Diagnostic answer operations
    def get_next_diagnostic_answer_id(self) -> int:
        """Get the next diagnostic answer ID."""
        self._diagnostic_answer_id_counter += 1
        return self._diagnostic_answer_id_counter

    def save_learner_profile_data(self) -> None:
        """Save learner profiles to file."""
        file_path = self._get_data_file_path()

        try:
            # Load existing data first
            existing_data = {}
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)

            # Update learner profiles section
            learner_profiles_data = []
            for profile in self._learner_profiles.values():
                learner_profiles_data.append(profile.to_dict())

            existing_data["learner_profiles"] = learner_profiles_data
            existing_data["next_learner_profile_id"] = self._learner_profile_id_counter
            existing_data["learner_profiles_updated_at"] = datetime.now().isoformat()

            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)

            logger.debug(f"Saved {len(learner_profiles_data)} learner profiles to {file_path}")

        except Exception as e:
            logger.error(f"Failed to save learner profiles: {e}")

    def load_learner_profiles_from_file(self) -> None:
        """Load learner profiles from JSON file."""
        file_path = self._get_data_file_path()

        if not file_path.exists():
            logger.debug(f"Learner profile data file not found: {file_path}")
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            learner_profiles_data = data.get("learner_profiles", [])
            for profile_dict in learner_profiles_data:
                profile = LearnerProfile.from_dict(profile_dict)
                self._learner_profiles[profile.id] = profile

            # Restore ID counter
            self._learner_profile_id_counter = data.get(
                "next_learner_profile_id", len(self._learner_profiles)
            )

            logger.info(f"Loaded {len(self._learner_profiles)} learner profiles from {file_path}")

        except Exception as e:
            logger.error(f"Failed to load learner profiles: {e}")

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

    # Learning Session persistence
    def _get_session_data_file_path(self) -> Path:
        """Get the path to the learning sessions data file."""
        project_root = Path(__file__).parent.parent.parent
        return project_root / "data" / "learning_sessions.json"

    def save_learning_sessions_to_file(self) -> None:
        """Save learning sessions to JSON file."""
        file_path = self._get_session_data_file_path()
        
        try:
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            sessions_data = []
            for session in self._learning_sessions.values():
                sessions_data.append(session.to_dict())
            
            data = {
                "sessions": sessions_data,
                "updated_at": datetime.now().isoformat(),
            }
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"Saved {len(sessions_data)} learning sessions to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save learning sessions to file: {e}")

    def load_learning_sessions_from_file(self) -> None:
        """Load learning sessions from JSON file."""
        file_path = self._get_session_data_file_path()
        
        if not file_path.exists():
            logger.debug(f"Learning sessions file not found: {file_path}")
            return
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    logger.debug(f"Learning sessions file is empty: {file_path}")
                    return
                data = json.loads(content)
            
            sessions_data = data.get("sessions", [])
            for session_dict in sessions_data:
                session = LearningSession.from_dict(session_dict)
                self._learning_sessions[session.id] = session
            
            logger.info(f"Loaded {len(sessions_data)} learning sessions from {file_path}")
            
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in learning sessions file: {e}")
        except Exception as e:
            logger.error(f"Failed to load learning sessions from file: {e}")

    def _get_media_data_file_path(self) -> Path:
        """Get the path to the media resources data file."""
        project_root = Path(__file__).parent.parent.parent
        return project_root / "data" / "media_resources.json"

    def save_media_resources_to_file(self) -> None:
        """Save media resources (images + videos) to JSON file."""
        file_path = self._get_media_data_file_path()
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "images": [],
                "videos": [],
            }

            # Save teaching images
            if hasattr(self, "_teaching_images"):
                for img in self._teaching_images.values():
                    data["images"].append(img.to_dict())

            # Save teaching videos
            if hasattr(self, "_teaching_videos"):
                for vid in self._teaching_videos.values():
                    data["videos"].append(vid.to_dict())

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            total = len(data["images"]) + len(data["videos"])
            logger.info(f"Saved {total} media resources to {file_path}")

        except Exception as e:
            logger.error(f"Failed to save media resources: {e}")

    def load_media_resources_from_file(self) -> None:
        """Load media resources from JSON file."""
        file_path = self._get_media_data_file_path()
        if not file_path.exists():
            logger.debug(f"Media resources file not found: {file_path}")
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if not content:
                return
            data = json.loads(content)

            # Initialize storage if needed
            if not hasattr(self, "_teaching_images"):
                self._teaching_images = {}
            if not hasattr(self, "_teaching_videos"):
                self._teaching_videos = {}

            # Load images
            from app.models.resource import TeachingImage, ImageType, ImageStatus
            for img_dict in data.get("images", []):
                try:
                    img = TeachingImage(
                        id=img_dict["id"],
                        knowledge_point_id=img_dict["knowledge_point_id"],
                        title=img_dict["title"],
                        description=img_dict["description"],
                        image_type=ImageType(img_dict["image_type"]),
                        file_path=img_dict["file_path"],
                        thumbnail_path=img_dict.get("thumbnail_path"),
                        tags=img_dict.get("tags", []),
                        metadata=img_dict.get("metadata", {}),
                        usage_count=img_dict.get("usage_count", 0),
                        rating=img_dict.get("rating", 0.0),
                        status=ImageStatus(img_dict.get("status", "ready")),
                    )
                    self._teaching_images[img.id] = img
                except (KeyError, ValueError) as e:
                    logger.warning(f"Skipping invalid image record: {e}")

            # Load videos
            from app.models.resource import TeachingVideo
            for vid_dict in data.get("videos", []):
                try:
                    vid = TeachingVideo(
                        id=vid_dict["id"],
                        knowledge_point_id=vid_dict["knowledge_point_id"],
                        title=vid_dict["title"],
                        description=vid_dict["description"],
                        video_url=vid_dict["video_url"],
                        duration=vid_dict.get("duration", 0),
                        thumbnail_url=vid_dict.get("thumbnail_url"),
                        tags=vid_dict.get("tags", []),
                        metadata=vid_dict.get("metadata", {}),
                        usage_count=vid_dict.get("usage_count", 0),
                        rating=vid_dict.get("rating", 0.0),
                    )
                    self._teaching_videos[vid.id] = vid
                except (KeyError, ValueError) as e:
                    logger.warning(f"Skipping invalid video record: {e}")

            total = len(data.get("images", [])) + len(data.get("videos", []))
            logger.info(f"Loaded {total} media resources from {file_path}")

        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in media resources file: {e}")
        except Exception as e:
            logger.error(f"Failed to load media resources from file: {e}")


# Global database instance
db = InMemoryDatabase()
