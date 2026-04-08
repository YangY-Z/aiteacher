# 课程数据结构 DDD 设计方案

## 一、领域分析

### 1.1 核心概念
- **年级（Grade）**：教育阶段的基本单位，如"初一"、"初二"等
- **科目（Subject）**：学科分类，如"数学"、"语文"、"英语"等
- **章节（Chapter）**：课程内容的基本单元，如"一次函数"、"二次方程"等

### 1.2 业务规则
1. 年级和科目是相对稳定的配置数据
2. 章节属于具体的年级和科目
3. 一个年级可以有多个科目
4. 一个科目可以被多个年级使用
5. 章节包含知识点、教材版本等详细信息

### 1.3 聚合边界识别
根据DDD原则，识别出以下聚合：

```
Grade (聚合根)
  └─ 年级基本信息
  └─ GradeSubject (关联实体) - 该年级下的科目配置

Subject (聚合根)
  └─ 科目基本信息

Chapter (聚合根)
  ├─ 知识点（KnowledgePoint）- 实体
  └─ 章节依赖关系 - 值对象
```

**说明：**
- GradeSubject 作为 Grade 聚合内的实体，记录年级与科目的关联关系
- 这样设计便于管理"某个年级下有哪些科目"这一业务概念
- 科目仍保持独立性，可以被多个年级使用

## 二、领域模型设计

### 2.1 年级聚合（Grade Aggregate）

**聚合根：Grade**

```python
@dataclass
class Grade:
    """年级聚合根"""
    id: str                    # 格式: G_{年级代码}，如 G_C1, G_C2, G_S1
    name: str                  # 年级名称，如"初一"、"高一"
    code: str                  # 年级代码，如"C1", "C2", "S1"
    level: GradeLevel          # 学段：primary(小学), middle(初中), high(高中)
    subjects: List[GradeSubject]  # 该年级下的科目列表（聚合内实体）
    sort_order: int            # 排序序号
    description: Optional[str] # 描述
    status: Status             # 状态：active, inactive
    created_at: datetime
    updated_at: datetime
```

**枚举：GradeLevel**

```python
class GradeLevel(str, Enum):
    """年级学段枚举"""
    PRIMARY = "primary"    # 小学
    MIDDLE = "middle"      # 初中
    HIGH = "high"          # 高中
```

**实体：GradeSubject**

```python
@dataclass
class GradeSubject:
    """年级-科目关联实体（属于Grade聚合）"""
    grade_id: str              # 年级ID
    subject_id: str            # 科目ID（引用Subject聚合根）
    sort_order: int            # 该年级下科目的排序
    status: Status             # 该年级下科目的状态：active, inactive
    created_at: datetime
    updated_at: datetime
```

### 2.2 科目聚合（Subject Aggregate）

**聚合根：Subject**

```python
@dataclass
class Subject:
    """科目聚合根"""
    id: str                    # 格式: S_{科目代码}，如 S_MATH, S_CHINESE
    name: str                  # 科目名称，如"数学"、"语文"
    code: str                  # 科目代码，如"MATH", "CHINESE", "ENGLISH"
    category: SubjectCategory  # 科目类别
    icon: Optional[str]        # 图标URL或标识
    color: Optional[str]       # 主题色
    sort_order: int            # 排序序号
    description: Optional[str] # 描述
    status: Status             # 状态
    created_at: datetime
    updated_at: datetime
```

**枚举：SubjectCategory**

```python
class SubjectCategory(str, Enum):
    """科目类别枚举"""
    SCIENCE = "science"            # 理科
    ARTS = "arts"                  # 文科
    LANGUAGE = "language"          # 语言
    COMPREHENSIVE = "comprehensive" # 综合
```

### 2.3 章节聚合（Chapter Aggregate）

**聚合根：Chapter**

```python
@dataclass
class Chapter:
    """章节聚合根"""
    id: str                           # 格式: CH_{GRADE_ID}_{SUBJECT_ID}_{NUM}
    name: str                         # 章节名称
    grade_id: str                     # 年级ID（引用）
    subject_id: str                   # 科目ID（引用）
    edition: Edition                  # 教材版本
    description: Optional[str]        # 描述
    sort_order: int                   # 排序序号
    total_knowledge_points: int       # 知识点总数
    estimated_hours: Optional[float]  # 预估学时
    level_descriptions: Dict[int, str] # 各级别描述
    status: Status                    # 状态
    created_at: datetime
    updated_at: datetime
```

**实体：KnowledgePoint**

```python
@dataclass
class KnowledgePoint:
    """知识点实体"""
    id: str
    chapter_id: str                   # 所属章节ID
    name: str
    type: KnowledgePointType          # 类型：概念、公式、技能
    level: int                        # 难度等级：0-5
    description: Optional[str]
    sort_order: int
    key_points: List[str]             # 关键点列表
    mastery_criteria: Optional[MasteryCriteria]
    teaching_config: Optional[TeachingConfig]
    content_template: Optional[str]
    created_at: datetime
    updated_at: datetime
```

**枚举：Edition**

```python
class Edition(str, Enum):
    """教材版本枚举"""
    RENJIAO = "人教版"
    BEISHIDA = "北师大版"
    SUJIAO = "苏教版"
    LUJIAO = "鲁教版"
    HUASHIDA = "华师大版"
    RENJIAO_NEW = "人教版新教材"
```

**枚举：Status**

```python
class Status(str, Enum):
    """状态枚举"""
    ACTIVE = "active"      # 启用
    INACTIVE = "inactive"  # 停用
    DRAFT = "draft"        # 草稿
    ARCHIVED = "archived"  # 归档
```

## 三、数据表设计

### 3.1 年级表（grades）

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | VARCHAR(20) | 年级ID | PRIMARY KEY |
| name | VARCHAR(50) | 年级名称 | NOT NULL, UNIQUE |
| code | VARCHAR(10) | 年级代码 | NOT NULL, UNIQUE |
| level | VARCHAR(20) | 学段 | NOT NULL |
| sort_order | INT | 排序序号 | DEFAULT 0 |
| description | TEXT | 描述 | |
| status | VARCHAR(20) | 状态 | NOT NULL, DEFAULT 'active' |
| created_at | TIMESTAMP | 创建时间 | NOT NULL |
| updated_at | TIMESTAMP | 更新时间 | NOT NULL |

**索引：**
- PRIMARY KEY (id)
- UNIQUE KEY idx_name (name)
- UNIQUE KEY idx_code (code)
- INDEX idx_level_sort (level, sort_order)

### 3.2 年级-科目关联表（grade_subjects）

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | VARCHAR(50) | 关联ID | PRIMARY KEY |
| grade_id | VARCHAR(20) | 年级ID | NOT NULL, FOREIGN KEY |
| subject_id | VARCHAR(20) | 科目ID | NOT NULL, FOREIGN KEY |
| sort_order | INT | 排序序号 | DEFAULT 0 |
| status | VARCHAR(20) | 状态 | NOT NULL, DEFAULT 'active' |
| created_at | TIMESTAMP | 创建时间 | NOT NULL |
| updated_at | TIMESTAMP | 更新时间 | NOT NULL |

**索引：**
- PRIMARY KEY (id)
- UNIQUE KEY idx_grade_subject (grade_id, subject_id)
- INDEX idx_grade (grade_id)
- INDEX idx_subject (subject_id)
- FOREIGN KEY fk_grade (grade_id) REFERENCES grades(id) ON DELETE CASCADE
- FOREIGN KEY fk_subject (subject_id) REFERENCES subjects(id) ON DELETE CASCADE

**说明：**
- 该表记录每个年级下配置了哪些科目
- 通过 sort_order 控制科目在该年级下的显示顺序
- 同一科目可以被多个年级使用（多对多关系）
- 删除年级或科目时会级联删除关联记录

### 3.3 科目表（subjects）

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | VARCHAR(20) | 科目ID | PRIMARY KEY |
| name | VARCHAR(50) | 科目名称 | NOT NULL, UNIQUE |
| code | VARCHAR(20) | 科目代码 | NOT NULL, UNIQUE |
| category | VARCHAR(20) | 科目类别 | NOT NULL |
| icon | VARCHAR(255) | 图标 | |
| color | VARCHAR(20) | 主题色 | |
| sort_order | INT | 排序序号 | DEFAULT 0 |
| description | TEXT | 描述 | |
| status | VARCHAR(20) | 状态 | NOT NULL, DEFAULT 'active' |
| created_at | TIMESTAMP | 创建时间 | NOT NULL |
| updated_at | TIMESTAMP | 更新时间 | NOT NULL |

**索引：**
- PRIMARY KEY (id)
- UNIQUE KEY idx_name (name)
- UNIQUE KEY idx_code (code)
- INDEX idx_category_sort (category, sort_order)

### 3.4 章节表（chapters）

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | VARCHAR(50) | 章节ID | PRIMARY KEY |
| name | VARCHAR(100) | 章节名称 | NOT NULL |
| grade_id | VARCHAR(20) | 年级ID | NOT NULL, FOREIGN KEY |
| subject_id | VARCHAR(20) | 科目ID | NOT NULL, FOREIGN KEY |
| edition | VARCHAR(50) | 教材版本 | NOT NULL |
| description | TEXT | 描述 | |
| sort_order | INT | 排序序号 | DEFAULT 0 |
| total_knowledge_points | INT | 知识点总数 | DEFAULT 0 |
| estimated_hours | DECIMAL(4,1) | 预估学时 | |
| level_descriptions | JSON | 各级别描述 | |
| status | VARCHAR(20) | 状态 | NOT NULL, DEFAULT 'active' |
| created_at | TIMESTAMP | 创建时间 | NOT NULL |
| updated_at | TIMESTAMP | 更新时间 | NOT NULL |

**索引：**
- PRIMARY KEY (id)
- INDEX idx_grade_subject (grade_id, subject_id)
- INDEX idx_edition (edition)
- FOREIGN KEY fk_grade (grade_id) REFERENCES grades(id) ON DELETE RESTRICT
- FOREIGN KEY fk_subject (subject_id) REFERENCES subjects(id) ON DELETE RESTRICT

### 3.5 知识点表（knowledge_points）

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | VARCHAR(50) | 知识点ID | PRIMARY KEY |
| chapter_id | VARCHAR(50) | 所属章节ID | NOT NULL, FOREIGN KEY |
| name | VARCHAR(100) | 知识点名称 | NOT NULL |
| type | VARCHAR(20) | 类型 | NOT NULL |
| level | INT | 难度等级 | DEFAULT 0 |
| description | TEXT | 描述 | |
| sort_order | INT | 排序序号 | DEFAULT 0 |
| key_points | JSON | 关键点列表 | |
| mastery_criteria | JSON | 掌握标准 | |
| teaching_config | JSON | 教学配置 | |
| content_template | TEXT | 内容模板 | |
| created_at | TIMESTAMP | 创建时间 | NOT NULL |
| updated_at | TIMESTAMP | 更新时间 | NOT NULL |

**索引：**
- PRIMARY KEY (id)
- INDEX idx_chapter (chapter_id)
- FOREIGN KEY fk_chapter (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE

## 四、领域服务设计

### 4.1 GradeService（年级领域服务）

```python
class GradeService:
    """年级领域服务"""
    
    def create_grade(self, name: str, code: str, level: GradeLevel) -> Grade:
        """创建年级"""
        pass
    
    def update_grade(self, grade_id: str, name: str) -> Grade:
        """更新年级"""
        # 更新年级信息
        # 同时更新所有相关章节的引用
        pass
    
    def delete_grade(self, grade_id: str) -> None:
        """删除年级"""
        # 检查是否有关联章节
        # 如果有，阻止删除或级联处理
        # 级联删除 grade_subjects 关联记录
        pass
    
    def get_grade_with_chapters(self, grade_id: str) -> GradeWithChapters:
        """获取年级及其章节"""
        pass
    
    def add_subject_to_grade(self, grade_id: str, subject_id: str, sort_order: int = 0) -> GradeSubject:
        """为年级添加科目"""
        # 创建 GradeSubject 关联
        pass
    
    def remove_subject_from_grade(self, grade_id: str, subject_id: str) -> None:
        """从年级移除科目"""
        # 删除 GradeSubject 关联
        # 检查是否有关联章节，如果有则阻止删除
        pass
    
    def update_subject_order_in_grade(self, grade_id: str, subject_id: str, new_order: int) -> None:
        """更新年级下科目的排序"""
        pass
    
    def get_grade_subjects(self, grade_id: str) -> List[GradeSubject]:
        """获取年级下的所有科目"""
        pass
```

### 4.2 SubjectService（科目领域服务）

```python
class SubjectService:
    """科目领域服务"""
    
    def create_subject(self, name: str, code: str, category: SubjectCategory) -> Subject:
        """创建科目"""
        pass
    
    def update_subject(self, subject_id: str, name: str) -> Subject:
        """更新科目"""
        # 更新科目信息
        # 同时更新所有相关章节的引用
        pass
    
    def delete_subject(self, subject_id: str) -> None:
        """删除科目"""
        # 检查是否有关联章节
        pass
    
    def get_subject_with_chapters(self, subject_id: str) -> SubjectWithChapters:
        """获取科目及其章节"""
        pass
```

### 4.3 ChapterService（章节领域服务）

```python
class ChapterService:
    """章节领域服务"""
    
    def create_chapter(
        self, 
        name: str, 
        grade_id: str, 
        subject_id: str,
        edition: Edition
    ) -> Chapter:
        """创建章节"""
        pass
    
    def update_chapter_grade(self, chapter_id: str, new_grade_id: str) -> Chapter:
        """更新章节所属年级"""
        pass
    
    def update_chapter_subject(self, chapter_id: str, new_subject_id: str) -> Chapter:
        """更新章节所属科目"""
        pass
    
    def add_knowledge_point(self, chapter_id: str, kp: KnowledgePoint) -> None:
        """添加知识点"""
        pass
    
    def remove_knowledge_point(self, chapter_id: str, kp_id: str) -> None:
        """移除知识点"""
        pass
```

## 五、数据迁移方案

### 5.1 初始化年级和科目数据

```python
# 年级初始数据
initial_grades = [
    {"id": "G_C1", "name": "初一", "code": "C1", "level": "middle", "sort_order": 1},
    {"id": "G_C2", "name": "初二", "code": "C2", "level": "middle", "sort_order": 2},
    {"id": "G_C3", "name": "初三", "code": "C3", "level": "middle", "sort_order": 3},
    {"id": "G_S1", "name": "高一", "code": "S1", "level": "high", "sort_order": 4},
    {"id": "G_S2", "name": "高二", "code": "S2", "level": "high", "sort_order": 5},
    {"id": "G_S3", "name": "高三", "code": "S3", "level": "high", "sort_order": 6},
]

# 科目初始数据
initial_subjects = [
    {"id": "S_MATH", "name": "数学", "code": "MATH", "category": "science", "sort_order": 1},
    {"id": "S_CHINESE", "name": "语文", "code": "CHINESE", "category": "language", "sort_order": 2},
    {"id": "S_ENGLISH", "name": "英语", "code": "ENGLISH", "category": "language", "sort_order": 3},
    {"id": "S_PHYSICS", "name": "物理", "code": "PHYSICS", "category": "science", "sort_order": 4},
    {"id": "S_CHEMISTRY", "name": "化学", "code": "CHEMISTRY", "category": "science", "sort_order": 5},
]

# 年级-科目关联初始数据
initial_grade_subjects = [
    # 初一科目
    {"grade_id": "G_C1", "subject_id": "S_MATH", "sort_order": 1},
    {"grade_id": "G_C1", "subject_id": "S_CHINESE", "sort_order": 2},
    {"grade_id": "G_C1", "subject_id": "S_ENGLISH", "sort_order": 3},
    # 初二科目
    {"grade_id": "G_C2", "subject_id": "S_MATH", "sort_order": 1},
    {"grade_id": "G_C2", "subject_id": "S_CHINESE", "sort_order": 2},
    {"grade_id": "G_C2", "subject_id": "S_ENGLISH", "sort_order": 3},
    {"grade_id": "G_C2", "subject_id": "S_PHYSICS", "sort_order": 4},
    # 初三科目
    {"grade_id": "G_C3", "subject_id": "S_MATH", "sort_order": 1},
    {"grade_id": "G_C3", "subject_id": "S_CHINESE", "sort_order": 2},
    {"grade_id": "G_C3", "subject_id": "S_ENGLISH", "sort_order": 3},
    {"grade_id": "G_C3", "subject_id": "S_PHYSICS", "sort_order": 4},
    {"grade_id": "G_C3", "subject_id": "S_CHEMISTRY", "sort_order": 5},
    # 高一科目
    {"grade_id": "G_S1", "subject_id": "S_MATH", "sort_order": 1},
    {"grade_id": "G_S1", "subject_id": "S_CHINESE", "sort_order": 2},
    {"grade_id": "G_S1", "subject_id": "S_ENGLISH", "sort_order": 3},
    {"grade_id": "G_S1", "subject_id": "S_PHYSICS", "sort_order": 4},
    {"grade_id": "G_S1", "subject_id": "S_CHEMISTRY", "sort_order": 5},
    # 高二、高三类似...
]
```

### 5.2 迁移现有章节数据

```python
def migrate_chapters():
    """迁移现有章节数据"""
    # 1. 根据章节中的 grade 字段查找对应的年级ID
    # 2. 根据章节中的 subject 字段查找对应的科目ID
    # 3. 更新章节的 grade_id 和 subject_id 字段
    pass
```

## 六、API设计

### 6.1 年级管理API

```
GET    /api/v1/admin/grades              # 获取所有年级
POST   /api/v1/admin/grades              # 创建年级
GET    /api/v1/admin/grades/{id}         # 获取年级详情
PUT    /api/v1/admin/grades/{id}         # 更新年级
DELETE /api/v1/admin/grades/{id}         # 删除年级
GET    /api/v1/admin/grades/{id}/subjects # 获取年级下的所有科目
POST   /api/v1/admin/grades/{id}/subjects # 为年级添加科目
PUT    /api/v1/admin/grades/{id}/subjects/{subject_id} # 更新年级下科目配置
DELETE /api/v1/admin/grades/{id}/subjects/{subject_id} # 从年级移除科目
GET    /api/v1/admin/grades/{id}/chapters # 获取年级下的所有章节
```

### 6.2 科目管理API

```
GET    /api/v1/admin/subjects              # 获取所有科目
POST   /api/v1/admin/subjects              # 创建科目
GET    /api/v1/admin/subjects/{id}         # 获取科目详情
PUT    /api/v1/admin/subjects/{id}         # 更新科目
DELETE /api/v1/admin/subjects/{id}         # 删除科目
GET    /api/v1/admin/subjects/{id}/chapters # 获取科目下的所有章节
```

### 6.3 章节管理API

```
GET    /api/v1/admin/chapters                    # 获取所有章节（支持筛选）
POST   /api/v1/admin/chapters                    # 创建章节
GET    /api/v1/admin/chapters/{id}               # 获取章节详情
PUT    /api/v1/admin/chapters/{id}               # 更新章节
DELETE /api/v1/admin/chapters/{id}               # 删除章节
GET    /api/v1/admin/chapters/{id}/knowledge-points # 获取章节知识点
```

## 七、优势分析

### 7.1 DDD设计优势

1. **清晰的聚合边界**：
   - Grade、Subject、Chapter 各自独立管理
   - 通过ID引用建立关系，降低耦合

2. **领域行为封装**：
   - 业务逻辑集中在领域模型中
   - 提高代码可维护性和可测试性

3. **数据一致性**：
   - 通过领域服务保证数据完整性
   - 外键约束确保引用完整性

4. **扩展性强**：
   - 年级和科目可以独立扩展属性
   - 章节可以灵活关联不同的年级和科目

### 7.2 相比原设计的改进

| 对比项 | 原设计 | 新设计 |
|--------|--------|--------|
| 年级管理 | localStorage存储，无后端支持 | 独立数据表，完整CRUD支持 |
| 科目管理 | localStorage存储，无后端支持 | 独立数据表，完整CRUD支持 |
| 年级-科目关联 | 无独立管理，通过章节推断 | 独立关联表，支持灵活配置 |
| 章节关联 | 字符串字段存储年级和科目 | 外键引用，保证数据一致性 |
| 删除年级 | 可能导致孤立章节 | 外键约束阻止或级联处理 |
| 编辑年级/科目 | 需手动同步更新章节 | 自动更新所有关联章节 |
| 数据查询 | 无索引优化 | 完整索引支持 |
| 科目排序 | 无年级维度排序 | 每个年级可独立设置科目排序 |

## 八、实施建议

### 8.1 实施步骤

1. **第一阶段：创建数据表**
   - 创建 grades 表
   - 创建 subjects 表
   - 创建 grade_subjects 关联表
   - 修改 chapters 表结构

2. **第二阶段：迁移数据**
   - 初始化年级和科目数据
   - 初始化年级-科目关联数据
   - 迁移现有章节数据

3. **第三阶段：实现领域模型**
   - 实现 Grade、Subject、Chapter 领域模型
   - 实现领域服务

4. **第四阶段：实现API**
   - 实现年级管理API
   - 实现科目管理API
   - 修改章节管理API

5. **第五阶段：前端适配**
   - 移除 localStorage 配置逻辑
   - 对接新的API接口
   - 更新UI交互逻辑

### 8.2 兼容性考虑

- 保留原有字段：在过渡期保留 `grade` 和 `subject` 字符串字段
- 提供迁移工具：编写数据迁移脚本
- 向后兼容API：在过渡期支持两种数据格式

## 九、总结

本方案采用DDD领域驱动设计方法，将年级、科目、章节设计为独立的聚合根，通过外键引用建立关系。新增年级-科目关联表，实现灵活的年级科目配置。相比原设计，具有以下优势：

1. **数据完整性**：外键约束保证引用完整性
2. **可维护性**：清晰的领域边界和职责划分
3. **扩展性**：易于添加新属性和业务逻辑
4. **性能**：合理的索引设计提升查询效率
5. **灵活性**：年级-科目关联支持独立配置和排序

建议按照实施步骤逐步推进，确保数据迁移平滑过渡。
