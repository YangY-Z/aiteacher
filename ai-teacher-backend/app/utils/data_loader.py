"""Data loader utility for importing course and assessment data."""

import json
from typing import Any
from pathlib import Path

from app.models.course import (
    Chapter,
    Course,
    CourseStatus,
    Edition,
    KnowledgePoint,
    KnowledgePointType,
    KnowledgePointDependency,
    MasteryCriteria,
    Subject,
    TeachingConfig,
)
from app.models.assessment import (
    AssessmentQuestion,
    QuestionType,
    Difficulty,
)
from app.repositories.course_repository import (
    course_repository,
    knowledge_point_repository,
    knowledge_point_dependency_repository,
)
from app.repositories.memory_db import db
from app.repositories.assessment_repository import assessment_question_repository


def _build_mastery_criteria(kp_type: KnowledgePointType) -> MasteryCriteria:
    if kp_type == KnowledgePointType.CONCEPT:
        return MasteryCriteria(
            type="concept_check",
            method="选择题",
            question_count=2,
            pass_threshold=1,
        )
    if kp_type == KnowledgePointType.FORMULA:
        return MasteryCriteria(
            type="formula_check",
            method="填空题",
            question_count=3,
            pass_threshold=2,
        )
    return MasteryCriteria(
        type="skill_check",
        method="计算题",
        question_count=2,
        pass_threshold=1,
    )


def _build_teaching_config() -> TeachingConfig:
    return TeachingConfig(
        use_examples=True,
        ask_questions=True,
        question_positions=["讲解结束"],
    )


def _upsert_chapter_knowledge_points(
    course_id: str,
    chapter_id: str,
    knowledge_points_data: list[dict[str, Any]],
) -> None:
    for i, kp_data in enumerate(knowledge_points_data):
        kp_type = KnowledgePointType(kp_data["type"])
        kp = KnowledgePoint(
            id=kp_data["id"],
            course_id=course_id,
            name=kp_data["name"],
            type=kp_type,
            description=kp_data["description"],
            level=kp_data["level"],
            sort_order=i,
            mastery_criteria=_build_mastery_criteria(kp_type),
            teaching_config=_build_teaching_config(),
            key_points=kp_data.get("key_points") or [kp_data["description"]],
            chapter_id=chapter_id,
        )
        knowledge_point_repository.update(kp)

        db._kp_dependencies = [
            dep for dep in db._kp_dependencies if dep.kp_id != kp_data["id"]
        ]
        for dep_id in kp_data.get("dependencies", []):
            knowledge_point_dependency_repository.add_dependency(kp_data["id"], dep_id)


def load_course_data(data_dir: str = "/Users/zhaoyang/iFlow/aiteacher") -> None:
    """Load course and knowledge point data from JSON files.

    Args:
        data_dir: Directory containing the JSON data files.
    """
    target_course_id = "COURSE_RENJIAO_7_MATH"
    target_chapter_id = "CH_7MATH_LINEAR_FUNCTION"
    legacy_course_id = "MATH_JUNIOR_01"
    textbook_level_descriptions = {
        0: "基础概念层",
        1: "核心性质层",
        2: "运算方法层",
        3: "综合应用层",
    }
    level_descriptions = {
        0: "基础概念层",
        1: "核心概念层",
        2: "函数基础层",
        3: "正比例与一次函数层",
        4: "图象与性质层",
        5: "变换层",
        6: "综合应用层",
    }

    course = course_repository.get_by_id(target_course_id)
    if not course:
        course = Course(
            id=target_course_id,
            name="初一数学（人教版）",
            grade="初一",
            edition=Edition.RENJIAO,
            subject=Subject.MATH,
            description="人教版初一数学全册",
            total_knowledge_points=0,
            estimated_hours=35.0,
            status=CourseStatus.ACTIVE,
        )
        course_repository.create(course)

    textbook_chapters = [
        {
            "id": "CH_7MATH_01",
            "name": "有理数",
            "description": "正数和负数、有理数、数轴、相反数、绝对值及有理数运算",
            "sort_order": 0,
            "estimated_hours": 10.0,
            "prerequisites": [],
            "knowledge_points": [
                {"id": "KP_7MATH_01_01", "name": "正数和负数", "type": "概念", "description": "用正数、负数表示具有相反意义的量", "level": 0, "dependencies": []},
                {"id": "KP_7MATH_01_02", "name": "有理数分类", "type": "概念", "description": "按整数、分数以及正负性对有理数进行分类", "level": 0, "dependencies": ["KP_7MATH_01_01"]},
                {"id": "KP_7MATH_01_03", "name": "数轴", "type": "概念", "description": "理解原点、正方向、单位长度并在数轴上表示有理数", "level": 1, "dependencies": ["KP_7MATH_01_01"]},
                {"id": "KP_7MATH_01_04", "name": "相反数", "type": "概念", "description": "理解只有符号不同的两个数互为相反数", "level": 1, "dependencies": ["KP_7MATH_01_03"]},
                {"id": "KP_7MATH_01_05", "name": "绝对值", "type": "概念", "description": "从数轴距离理解绝对值并比较有理数大小", "level": 1, "dependencies": ["KP_7MATH_01_03"]},
                {"id": "KP_7MATH_01_06", "name": "有理数加减法", "type": "技能", "description": "掌握有理数加法法则、减法转化为加法及混合运算", "level": 2, "dependencies": ["KP_7MATH_01_04", "KP_7MATH_01_05"]},
                {"id": "KP_7MATH_01_07", "name": "有理数乘除法", "type": "技能", "description": "掌握有理数乘除法符号法则、倒数和乘除混合运算", "level": 2, "dependencies": ["KP_7MATH_01_06"]},
                {"id": "KP_7MATH_01_08", "name": "有理数乘方", "type": "概念", "description": "理解乘方、底数、指数、幂及负数乘方的符号规律", "level": 2, "dependencies": ["KP_7MATH_01_07"]},
                {"id": "KP_7MATH_01_09", "name": "科学记数法", "type": "技能", "description": "用a×10^n表示较大的数并理解近似数精确度", "level": 3, "dependencies": ["KP_7MATH_01_08"]},
                {"id": "KP_7MATH_01_10", "name": "有理数混合运算", "type": "技能", "description": "按运算顺序完成含乘方、括号的有理数综合计算", "level": 3, "dependencies": ["KP_7MATH_01_06", "KP_7MATH_01_07", "KP_7MATH_01_08"]},
            ],
        },
        {
            "id": "CH_7MATH_02",
            "name": "整式的加减",
            "description": "代数式、单项式、多项式、同类项、合并同类项与去括号",
            "sort_order": 1,
            "estimated_hours": 8.0,
            "prerequisites": ["CH_7MATH_01"],
            "knowledge_points": [
                {"id": "KP_7MATH_02_01", "name": "用字母表示数", "type": "概念", "description": "用字母表示数量关系和运算规律", "level": 0, "dependencies": ["KP_7MATH_01_10"]},
                {"id": "KP_7MATH_02_02", "name": "代数式", "type": "概念", "description": "理解代数式及代数式的值", "level": 0, "dependencies": ["KP_7MATH_02_01"]},
                {"id": "KP_7MATH_02_03", "name": "单项式", "type": "概念", "description": "认识单项式、系数和次数", "level": 1, "dependencies": ["KP_7MATH_02_02"]},
                {"id": "KP_7MATH_02_04", "name": "多项式", "type": "概念", "description": "认识多项式、项、常数项、次数和整式", "level": 1, "dependencies": ["KP_7MATH_02_03"]},
                {"id": "KP_7MATH_02_05", "name": "同类项", "type": "概念", "description": "识别所含字母相同且相同字母指数也相同的项", "level": 1, "dependencies": ["KP_7MATH_02_03"]},
                {"id": "KP_7MATH_02_06", "name": "合并同类项", "type": "技能", "description": "利用合并同类项法则化简整式", "level": 2, "dependencies": ["KP_7MATH_02_05"]},
                {"id": "KP_7MATH_02_07", "name": "去括号", "type": "技能", "description": "根据括号前符号正确去括号并处理各项符号", "level": 2, "dependencies": ["KP_7MATH_02_06"]},
                {"id": "KP_7MATH_02_08", "name": "整式加减", "type": "技能", "description": "通过去括号、合并同类项完成整式加减运算", "level": 3, "dependencies": ["KP_7MATH_02_06", "KP_7MATH_02_07"]},
                {"id": "KP_7MATH_02_09", "name": "整式化简求值", "type": "技能", "description": "先化简整式再代入数值求值", "level": 3, "dependencies": ["KP_7MATH_02_02", "KP_7MATH_02_08"]},
            ],
        },
        {
            "id": "CH_7MATH_03",
            "name": "一元一次方程",
            "description": "方程、等式性质、一元一次方程解法及实际问题",
            "sort_order": 2,
            "estimated_hours": 10.0,
            "prerequisites": ["CH_7MATH_02"],
            "knowledge_points": [
                {"id": "KP_7MATH_03_01", "name": "方程与方程的解", "type": "概念", "description": "理解含未知数的等式和使方程成立的未知数的值", "level": 0, "dependencies": ["KP_7MATH_02_02"]},
                {"id": "KP_7MATH_03_02", "name": "一元一次方程", "type": "概念", "description": "识别只含一个未知数且未知数次数为1的整式方程", "level": 0, "dependencies": ["KP_7MATH_03_01"]},
                {"id": "KP_7MATH_03_03", "name": "等式性质", "type": "公式", "description": "理解等式两边同加减、同乘除非零数仍相等", "level": 1, "dependencies": ["KP_7MATH_03_01"]},
                {"id": "KP_7MATH_03_04", "name": "移项", "type": "技能", "description": "把方程中的项改变符号后从一边移到另一边", "level": 1, "dependencies": ["KP_7MATH_03_03"]},
                {"id": "KP_7MATH_03_05", "name": "合并与系数化为1", "type": "技能", "description": "通过合并同类项和系数化为1解简单方程", "level": 2, "dependencies": ["KP_7MATH_03_04", "KP_7MATH_02_06"]},
                {"id": "KP_7MATH_03_06", "name": "去括号解方程", "type": "技能", "description": "先去括号再移项、合并、系数化为1", "level": 2, "dependencies": ["KP_7MATH_03_05", "KP_7MATH_02_07"]},
                {"id": "KP_7MATH_03_07", "name": "去分母解方程", "type": "技能", "description": "通过方程两边同乘最小公倍数化去分母", "level": 2, "dependencies": ["KP_7MATH_03_03", "KP_7MATH_03_06"]},
                {"id": "KP_7MATH_03_08", "name": "列方程解应用题", "type": "技能", "description": "找等量关系、设未知数、列方程并检验实际意义", "level": 3, "dependencies": ["KP_7MATH_03_07"]},
                {"id": "KP_7MATH_03_09", "name": "行程工程问题", "type": "技能", "description": "用一元一次方程解决行程、工程等数量关系问题", "level": 3, "dependencies": ["KP_7MATH_03_08"]},
                {"id": "KP_7MATH_03_10", "name": "销售盈亏问题", "type": "技能", "description": "用售价、进价、利润、折扣等关系建立方程", "level": 3, "dependencies": ["KP_7MATH_03_08"]},
            ],
        },
        {
            "id": "CH_7MATH_04",
            "name": "几何图形初步",
            "description": "立体图形、直线射线线段、角及几何图形的初步认识",
            "sort_order": 3,
            "estimated_hours": 8.0,
            "prerequisites": ["CH_7MATH_03"],
            "knowledge_points": [
                {"id": "KP_7MATH_04_01", "name": "立体图形与平面图形", "type": "概念", "description": "区分常见立体图形和平面图形，认识点、线、面、体", "level": 0, "dependencies": []},
                {"id": "KP_7MATH_04_02", "name": "展开图与三视图", "type": "技能", "description": "从不同方向观察立体图形并认识简单展开图", "level": 1, "dependencies": ["KP_7MATH_04_01"]},
                {"id": "KP_7MATH_04_03", "name": "直线射线线段", "type": "概念", "description": "理解直线、射线、线段的表示方法和基本性质", "level": 1, "dependencies": ["KP_7MATH_04_01"]},
                {"id": "KP_7MATH_04_04", "name": "线段比较与和差", "type": "技能", "description": "比较线段长短，计算线段的和、差、中点相关长度", "level": 2, "dependencies": ["KP_7MATH_04_03"]},
                {"id": "KP_7MATH_04_05", "name": "角的概念与表示", "type": "概念", "description": "认识角、角的顶点和边，并用不同方式表示角", "level": 1, "dependencies": ["KP_7MATH_04_03"]},
                {"id": "KP_7MATH_04_06", "name": "度分秒换算", "type": "技能", "description": "进行角度单位度、分、秒之间的换算和计算", "level": 2, "dependencies": ["KP_7MATH_04_05", "KP_7MATH_01_10"]},
                {"id": "KP_7MATH_04_07", "name": "角的比较与运算", "type": "技能", "description": "比较角的大小，计算角的和、差、倍、分", "level": 2, "dependencies": ["KP_7MATH_04_05", "KP_7MATH_04_06"]},
                {"id": "KP_7MATH_04_08", "name": "余角和补角", "type": "概念", "description": "理解余角、补角及同角或等角的余补角性质", "level": 3, "dependencies": ["KP_7MATH_04_07"]},
            ],
        },
        {
            "id": "CH_7MATH_05",
            "name": "相交线与平行线",
            "description": "相交线、垂线、平行线性质与判定、平移",
            "sort_order": 4,
            "estimated_hours": 10.0,
            "prerequisites": ["CH_7MATH_04"],
            "knowledge_points": [
                {"id": "KP_7MATH_05_01", "name": "相交线与对顶角", "type": "概念", "description": "认识邻补角、对顶角并掌握对顶角相等", "level": 0, "dependencies": ["KP_7MATH_04_08"]},
                {"id": "KP_7MATH_05_02", "name": "垂线", "type": "概念", "description": "理解垂直、垂线段及点到直线距离", "level": 1, "dependencies": ["KP_7MATH_05_01"]},
                {"id": "KP_7MATH_05_03", "name": "同位角内错角同旁内角", "type": "概念", "description": "在三线八角图形中识别同位角、内错角、同旁内角", "level": 1, "dependencies": ["KP_7MATH_05_01"]},
                {"id": "KP_7MATH_05_04", "name": "平行线判定", "type": "公式", "description": "利用同位角相等、内错角相等、同旁内角互补判定平行", "level": 2, "dependencies": ["KP_7MATH_05_03"]},
                {"id": "KP_7MATH_05_05", "name": "平行线性质", "type": "公式", "description": "由两直线平行推出相应角相等或互补", "level": 2, "dependencies": ["KP_7MATH_05_04"]},
                {"id": "KP_7MATH_05_06", "name": "命题定理证明初步", "type": "概念", "description": "认识命题、题设、结论，并进行简单推理说明", "level": 3, "dependencies": ["KP_7MATH_05_05"]},
                {"id": "KP_7MATH_05_07", "name": "平移", "type": "技能", "description": "理解平移的方向、距离和对应点连线关系", "level": 3, "dependencies": ["KP_7MATH_05_02"]},
            ],
        },
        {
            "id": "CH_7MATH_06",
            "name": "实数",
            "description": "平方根、立方根、无理数、实数及数轴",
            "sort_order": 5,
            "estimated_hours": 8.0,
            "prerequisites": ["CH_7MATH_01"],
            "knowledge_points": [
                {"id": "KP_7MATH_06_01", "name": "算术平方根", "type": "概念", "description": "理解非负数的算术平方根及根号表示", "level": 0, "dependencies": ["KP_7MATH_01_08"]},
                {"id": "KP_7MATH_06_02", "name": "平方根", "type": "概念", "description": "理解平方根、开平方和正负平方根关系", "level": 1, "dependencies": ["KP_7MATH_06_01"]},
                {"id": "KP_7MATH_06_03", "name": "立方根", "type": "概念", "description": "理解立方根、开立方及正负数立方根规律", "level": 1, "dependencies": ["KP_7MATH_01_08"]},
                {"id": "KP_7MATH_06_04", "name": "无理数", "type": "概念", "description": "认识无限不循环小数和常见无理数", "level": 1, "dependencies": ["KP_7MATH_06_01"]},
                {"id": "KP_7MATH_06_05", "name": "实数分类", "type": "概念", "description": "理解有理数、无理数组成实数并进行分类", "level": 2, "dependencies": ["KP_7MATH_01_02", "KP_7MATH_06_04"]},
                {"id": "KP_7MATH_06_06", "name": "实数与数轴", "type": "概念", "description": "理解实数与数轴上的点一一对应的思想", "level": 2, "dependencies": ["KP_7MATH_01_03", "KP_7MATH_06_05"]},
                {"id": "KP_7MATH_06_07", "name": "实数大小比较", "type": "技能", "description": "比较含根号实数的大小并进行估算", "level": 3, "dependencies": ["KP_7MATH_06_01", "KP_7MATH_06_06"]},
                {"id": "KP_7MATH_06_08", "name": "实数运算", "type": "技能", "description": "在有理数运算法则基础上进行简单实数运算", "level": 3, "dependencies": ["KP_7MATH_01_10", "KP_7MATH_06_05"]},
            ],
        },
        {
            "id": "CH_7MATH_07",
            "name": "平面直角坐标系",
            "description": "有序数对、平面直角坐标系、点的坐标与坐标平移",
            "sort_order": 6,
            "estimated_hours": 8.0,
            "prerequisites": ["CH_7MATH_05", "CH_7MATH_06"],
            "knowledge_points": [
                {"id": "KP_7MATH_07_01", "name": "有序数对", "type": "概念", "description": "用有序数对确定平面内位置", "level": 0, "dependencies": ["KP_7MATH_01_02"]},
                {"id": "KP_7MATH_07_02", "name": "平面直角坐标系", "type": "概念", "description": "认识坐标轴、原点、象限并建立坐标系", "level": 0, "dependencies": ["KP_7MATH_07_01"]},
                {"id": "KP_7MATH_07_03", "name": "点的坐标", "type": "技能", "description": "根据点写坐标，根据坐标描点", "level": 1, "dependencies": ["KP_7MATH_07_02"]},
                {"id": "KP_7MATH_07_04", "name": "象限内点坐标特征", "type": "概念", "description": "掌握各象限及坐标轴上点的坐标符号特征", "level": 1, "dependencies": ["KP_7MATH_07_03"]},
                {"id": "KP_7MATH_07_05", "name": "坐标表示地理位置", "type": "技能", "description": "选择合适坐标系描述实际位置", "level": 2, "dependencies": ["KP_7MATH_07_03"]},
                {"id": "KP_7MATH_07_06", "name": "点的平移与坐标变化", "type": "技能", "description": "理解左右、上下平移时坐标的变化规律", "level": 2, "dependencies": ["KP_7MATH_05_07", "KP_7MATH_07_03"]},
                {"id": "KP_7MATH_07_07", "name": "图形平移的坐标表示", "type": "技能", "description": "通过顶点坐标变化表示图形平移", "level": 3, "dependencies": ["KP_7MATH_07_06"]},
            ],
        },
        {
            "id": "CH_7MATH_08",
            "name": "二元一次方程组",
            "description": "二元一次方程、方程组、代入消元、加减消元和实际问题",
            "sort_order": 7,
            "estimated_hours": 10.0,
            "prerequisites": ["CH_7MATH_03"],
            "knowledge_points": [
                {"id": "KP_7MATH_08_01", "name": "二元一次方程", "type": "概念", "description": "识别含两个未知数且未知数次数均为1的方程", "level": 0, "dependencies": ["KP_7MATH_03_02"]},
                {"id": "KP_7MATH_08_02", "name": "二元一次方程组", "type": "概念", "description": "理解由两个二元一次方程组成的方程组及其解", "level": 0, "dependencies": ["KP_7MATH_08_01"]},
                {"id": "KP_7MATH_08_03", "name": "代入消元法", "type": "技能", "description": "通过表示一个未知数并代入另一方程求解方程组", "level": 1, "dependencies": ["KP_7MATH_08_02", "KP_7MATH_03_07"]},
                {"id": "KP_7MATH_08_04", "name": "加减消元法", "type": "技能", "description": "通过方程同加同减消去一个未知数求解方程组", "level": 1, "dependencies": ["KP_7MATH_08_02", "KP_7MATH_03_07"]},
                {"id": "KP_7MATH_08_05", "name": "选择合适消元方法", "type": "技能", "description": "根据方程组结构选择代入或加减消元", "level": 2, "dependencies": ["KP_7MATH_08_03", "KP_7MATH_08_04"]},
                {"id": "KP_7MATH_08_06", "name": "方程组实际问题", "type": "技能", "description": "设两个未知数，列二元一次方程组解决实际问题", "level": 3, "dependencies": ["KP_7MATH_08_05"]},
                {"id": "KP_7MATH_08_07", "name": "三元一次方程组初步", "type": "技能", "description": "用逐步消元思想解简单三元一次方程组", "level": 3, "dependencies": ["KP_7MATH_08_05"]},
            ],
        },
        {
            "id": "CH_7MATH_09",
            "name": "不等式与不等式组",
            "description": "不等式、一元一次不等式、一元一次不等式组及应用",
            "sort_order": 8,
            "estimated_hours": 9.0,
            "prerequisites": ["CH_7MATH_03"],
            "knowledge_points": [
                {"id": "KP_7MATH_09_01", "name": "不等式", "type": "概念", "description": "理解用不等号表示大小关系的式子", "level": 0, "dependencies": ["KP_7MATH_01_05"]},
                {"id": "KP_7MATH_09_02", "name": "不等式的解集", "type": "概念", "description": "理解不等式的解和解集并在数轴上表示", "level": 0, "dependencies": ["KP_7MATH_09_01", "KP_7MATH_01_03"]},
                {"id": "KP_7MATH_09_03", "name": "不等式性质", "type": "公式", "description": "掌握不等式两边同加减、同乘除时方向变化规律", "level": 1, "dependencies": ["KP_7MATH_09_02"]},
                {"id": "KP_7MATH_09_04", "name": "一元一次不等式", "type": "概念", "description": "识别只含一个未知数且未知数次数为1的不等式", "level": 1, "dependencies": ["KP_7MATH_09_03", "KP_7MATH_03_02"]},
                {"id": "KP_7MATH_09_05", "name": "解一元一次不等式", "type": "技能", "description": "按去分母、去括号、移项、合并、系数化为1求解", "level": 2, "dependencies": ["KP_7MATH_09_03", "KP_7MATH_03_07"]},
                {"id": "KP_7MATH_09_06", "name": "一元一次不等式组", "type": "概念", "description": "理解几个一元一次不等式公共解组成不等式组解集", "level": 2, "dependencies": ["KP_7MATH_09_05"]},
                {"id": "KP_7MATH_09_07", "name": "解不等式组", "type": "技能", "description": "分别求解各不等式并在数轴上确定公共部分", "level": 3, "dependencies": ["KP_7MATH_09_06"]},
                {"id": "KP_7MATH_09_08", "name": "不等式应用", "type": "技能", "description": "根据实际限制条件列不等式或不等式组求方案范围", "level": 3, "dependencies": ["KP_7MATH_09_07"]},
            ],
        },
        {
            "id": "CH_7MATH_10",
            "name": "数据的收集、整理与描述",
            "description": "统计调查、抽样调查、频数分布及统计图表",
            "sort_order": 9,
            "estimated_hours": 7.0,
            "prerequisites": ["CH_7MATH_01"],
            "knowledge_points": [
                {"id": "KP_7MATH_10_01", "name": "全面调查与抽样调查", "type": "概念", "description": "区分全面调查和抽样调查的适用情形", "level": 0, "dependencies": []},
                {"id": "KP_7MATH_10_02", "name": "总体个体样本样本容量", "type": "概念", "description": "理解统计调查中的总体、个体、样本和样本容量", "level": 0, "dependencies": ["KP_7MATH_10_01"]},
                {"id": "KP_7MATH_10_03", "name": "数据收集与整理", "type": "技能", "description": "设计调查问题，记录、分类并整理数据", "level": 1, "dependencies": ["KP_7MATH_10_02"]},
                {"id": "KP_7MATH_10_04", "name": "条形图扇形图折线图", "type": "技能", "description": "根据数据选择并绘制常见统计图", "level": 1, "dependencies": ["KP_7MATH_10_03"]},
                {"id": "KP_7MATH_10_05", "name": "频数与频率", "type": "概念", "description": "理解频数、频率及两者关系", "level": 2, "dependencies": ["KP_7MATH_10_03"]},
                {"id": "KP_7MATH_10_06", "name": "频数分布表", "type": "技能", "description": "分组整理数据并制作频数分布表", "level": 2, "dependencies": ["KP_7MATH_10_05"]},
                {"id": "KP_7MATH_10_07", "name": "频数分布直方图", "type": "技能", "description": "用频数分布直方图描述数据分布", "level": 3, "dependencies": ["KP_7MATH_10_06"]},
                {"id": "KP_7MATH_10_08", "name": "统计图表解读", "type": "技能", "description": "从统计图表中读取信息并作出合理判断", "level": 3, "dependencies": ["KP_7MATH_10_04", "KP_7MATH_10_07"]},
            ],
        },
    ]

    for chapter_data in textbook_chapters:
        db._chapters[chapter_data["id"]] = Chapter(
            id=chapter_data["id"],
            name=chapter_data["name"],
            grade="初一",
            edition=Edition.RENJIAO,
            subject=Subject.MATH,
            course_id=target_course_id,
            prerequisite_chapter_ids=chapter_data["prerequisites"],
            description=chapter_data["description"],
            sort_order=chapter_data["sort_order"],
            total_knowledge_points=len(chapter_data["knowledge_points"]),
            estimated_hours=chapter_data["estimated_hours"],
            level_descriptions=textbook_level_descriptions,
            status=CourseStatus.ACTIVE,
        )
        _upsert_chapter_knowledge_points(
            target_course_id,
            chapter_data["id"],
            chapter_data["knowledge_points"],
        )

    # The original "一次函数" seed used to be a standalone course. Keep its
    # content, but normalize it into the textbook course -> chapter hierarchy.
    db._courses.pop(legacy_course_id, None)
    db._chapters[target_chapter_id] = Chapter(
        id=target_chapter_id,
        name="一次函数",
        grade="初一",
        edition=Edition.RENJIAO,
        subject=Subject.MATH,
        course_id=target_course_id,
        prerequisite_chapter_ids=["CH_7MATH_07", "CH_7MATH_08"],
        description="函数专题扩展，保留原课程设计内容，衔接平面直角坐标系与方程组",
        sort_order=100,
        total_knowledge_points=32,
        estimated_hours=12.0,
        level_descriptions=level_descriptions,
        status=CourseStatus.ACTIVE,
    )

    # Define all knowledge points from the spec
    knowledge_points_data = [
        # Level 0
        {"id": "K1", "name": "坐标系", "type": "概念", "description": "平面直角坐标系的建立，x轴、y轴、原点", "level": 0, "dependencies": []},
        {"id": "K2", "name": "点的坐标", "type": "技能", "description": "用有序数对(x,y)表示平面上点的位置", "level": 1, "dependencies": ["K1"]},
        {"id": "K3", "name": "象限", "type": "概念", "description": "坐标平面被两轴分成四个象限及其特征", "level": 0, "dependencies": ["K1"]},
        {"id": "K4", "name": "变量", "type": "概念", "description": "可以取不同数值的量", "level": 0, "dependencies": []},
        {"id": "K5", "name": "常量", "type": "概念", "description": "数值固定不变的量", "level": 0, "dependencies": []},
        
        # Level 1-2
        {"id": "K6", "name": "函数定义", "type": "概念", "description": "设x和y是两个变量，若x每取一个值，y都有唯一确定的值与之对应", "level": 1, "dependencies": ["K4", "K5"]},
        {"id": "K7", "name": "自变量与因变量", "type": "概念", "description": "主动变化的量为自变量，随之变化的量为因变量", "level": 2, "dependencies": ["K6"]},
        {"id": "K8", "name": "函数的定义域", "type": "概念", "description": "自变量x允许取值的范围", "level": 2, "dependencies": ["K6"]},
        {"id": "K9", "name": "函数值", "type": "技能", "description": "当x取某值时，y对应的值", "level": 2, "dependencies": ["K6"]},
        {"id": "K10", "name": "函数解析式", "type": "概念", "description": "用数学式子表示函数关系", "level": 2, "dependencies": ["K6"]},
        {"id": "K11", "name": "函数的三种表示法", "type": "技能", "description": "解析式法、列表法、图象法", "level": 2, "dependencies": ["K10"]},
        
        # Level 3
        {"id": "K12", "name": "正比例函数定义", "type": "概念", "description": "y=kx(k≠0)形式的函数", "level": 3, "dependencies": ["K6", "K10"]},
        {"id": "K13", "name": "正比例函数图象", "type": "技能", "description": "正比例函数图象是过原点的直线", "level": 3, "dependencies": ["K11", "K12"]},
        {"id": "K14", "name": "正比例函数性质", "type": "公式", "description": "k>0过一三象限且递增；k<0过二四象限且递减", "level": 3, "dependencies": ["K12", "K3"]},
        {"id": "K15", "name": "一次函数定义", "type": "概念", "description": "y=kx+b(k≠0)形式的函数", "level": 3, "dependencies": ["K12", "K10"]},
        {"id": "K16", "name": "一次函数与正比例函数关系", "type": "概念", "description": "当b=0时，一次函数退化为正比例函数", "level": 3, "dependencies": ["K15"]},
        
        # Level 4
        {"id": "K17", "name": "描点法画函数图象", "type": "技能", "description": "列表、描点、连线的作图方法", "level": 4, "dependencies": ["K11", "K2"]},
        {"id": "K18", "name": "一次函数图象特征", "type": "技能", "description": "一次函数图象是一条直线", "level": 4, "dependencies": ["K15"]},
        {"id": "K19", "name": "两点确定直线", "type": "技能", "description": "画一次函数图象只需描出两点连线", "level": 4, "dependencies": ["K17"]},
        {"id": "K20", "name": "截距概念", "type": "概念", "description": "直线与y轴交点的纵坐标，即b的值", "level": 4, "dependencies": ["K15"]},
        {"id": "K21", "name": "斜率概念", "type": "概念", "description": "直线倾斜程度的度量，即k的值", "level": 4, "dependencies": ["K15"]},
        {"id": "K22", "name": "k对图象方向的影响", "type": "公式", "description": "k>0从左向右上升；k<0从左向右下降", "level": 4, "dependencies": ["K18", "K21"]},
        {"id": "K23", "name": "b对图象位置的影响", "type": "公式", "description": "b>0与y轴交于正半轴；b<0交于负半轴", "level": 4, "dependencies": ["K20"]},
        {"id": "K24", "name": "一次函数增减性", "type": "公式", "description": "k>0时y随x增大而增大；k<0时y随x增大而减小", "level": 4, "dependencies": ["K21", "K18"]},
        
        # Level 5
        {"id": "K25", "name": "平移变换", "type": "技能", "description": "上下平移改变b值，左右平移改变x", "level": 5, "dependencies": ["K18", "K20"]},
        
        # Level 6
        {"id": "K26", "name": "k与b的综合判断", "type": "技能", "description": "根据k、b符号判断图象经过的象限", "level": 6, "dependencies": ["K22", "K23", "K3"]},
        {"id": "K27", "name": "待定系数法", "type": "技能", "description": "设出函数解析式，代入条件求k、b", "level": 6, "dependencies": ["K15", "K9"]},
        {"id": "K28", "name": "由图象求解析式", "type": "技能", "description": "从图象上读取点坐标，用待定系数法求解析式", "level": 6, "dependencies": ["K27", "K19"]},
        {"id": "K29", "name": "求交点坐标", "type": "技能", "description": "联立两一次函数解析式求解方程组", "level": 6, "dependencies": ["K27"]},
        {"id": "K30", "name": "实际问题建模", "type": "技能", "description": "将实际问题转化为一次函数求解", "level": 6, "dependencies": ["K15", "K28"]},
        {"id": "K31", "name": "一次函数与方程的关系", "type": "概念", "description": "求ax+b=0的解等价于求y=ax+b与x轴交点横坐标", "level": 6, "dependencies": ["K18"]},
        {"id": "K32", "name": "一次函数与不等式的关系", "type": "概念", "description": "图象在x轴上方/下方对应的x范围即为不等式解集", "level": 6, "dependencies": ["K18"]},
    ]

    _upsert_chapter_knowledge_points(target_course_id, target_chapter_id, knowledge_points_data)

    course.total_knowledge_points = sum(
        1
        for kp in db._knowledge_points.values()
        if kp.course_id == target_course_id
    )
    course.estimated_hours = sum(
        chapter.estimated_hours or 0
        for chapter in db._chapters.values()
        if chapter.course_id == target_course_id
    )
    course_repository.update(course)


def load_assessment_data(data: dict[str, Any]) -> None:
    """Load assessment questions from JSON data.

    Args:
        data: Assessment bank JSON data.
    """
    # The JSON has "assessment_bank" at the root level
    assessment_bank = data.get("assessment_bank", [])
    
    for kp_data in assessment_bank:
        kp_id = kp_data.get("knowledge_point_id")

        for q_data in kp_data.get("questions", []):
            question_type = QuestionType(q_data["type"])
            difficulty = Difficulty(q_data.get("difficulty", "基础"))

            question = AssessmentQuestion(
                id=q_data["id"],
                kp_id=kp_id,
                type=question_type,
                content=q_data["content"],
                options=q_data.get("options"),
                correct_answer=q_data["correct_answer"],
                explanation=q_data.get("explanation", ""),
                difficulty=difficulty,
            )
            assessment_question_repository.create(question)
