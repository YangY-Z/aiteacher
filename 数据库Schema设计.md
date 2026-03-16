# AI虚拟教师系统 数据库Schema设计

**文档版本**: v1.0
**编写日期**: 2025年1月
**适用范围**: MVP阶段

---

## 一、数据库架构概览

### 1.1 数据库选型

| 数据库 | 用途 | 存储内容 |
|-------|------|---------|
| PostgreSQL | 主数据库 | 学生信息、课程图谱、学习档案、学习记录 |
| MongoDB | 日志数据库 | 会话日志、交互日志、错误日志 |
| Redis | 缓存 | 会话状态、热点数据缓存 |

### 1.2 ER图概览

```
┌─────────────┐       ┌─────────────┐       ┌─────────────────┐
│  students   │       │   courses   │       │ knowledge_points│
├─────────────┤       ├─────────────┤       ├─────────────────┤
│ id (PK)     │       │ id (PK)     │       │ id (PK)         │
│ name        │       │ name        │       │ course_id (FK)  │
│ grade       │       │ grade       │       │ name            │
│ phone       │       │ subject     │       │ type            │
│ password    │       │ description │       │ description     │
│ created_at  │       │ total_kp    │       │ level           │
│ updated_at  │       │ created_at  │       │ mastery_criteria│
└──────┬──────┘       └──────┬──────┘       │ teaching_config │
       │                     │              │ dependencies    │
       │                     │              └────────┬────────┘
       │                     │                       │
       │                     └───────────┬───────────┘
       │                                 │
       ▼                                 ▼
┌─────────────────┐           ┌─────────────────────┐
│ student_profiles│           │   learning_records  │
├─────────────────┤           ├─────────────────────┤
│ id (PK)         │           │ id (PK)             │
│ student_id (FK) │           │ student_id (FK)     │
│ course_id (FK)  │           │ kp_id (FK)          │
│ current_kp_id   │           │ status              │
│ mastery_rate    │           │ attempt_count       │
│ total_time      │           │ attempts (JSONB)    │
│ created_at      │           │ mastery_time        │
│ updated_at      │           │ total_time          │
└─────────────────┘           │ skip_info (JSONB)   │
                              │ review_info (JSONB) │
                              │ created_at          │
                              │ updated_at          │
                              └─────────────────────┘
```

---

## 二、PostgreSQL表结构

### 2.1 学生表 (students)

```sql
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL COMMENT '学生姓名',
    grade VARCHAR(20) NOT NULL COMMENT '年级',
    phone VARCHAR(20) UNIQUE COMMENT '手机号（登录账号）',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    avatar_url VARCHAR(255) COMMENT '头像URL',
    status VARCHAR(20) DEFAULT 'active' COMMENT '状态：active/inactive/banned',
    last_login_at TIMESTAMP COMMENT '最后登录时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_grade CHECK (grade IN ('初一', '初二', '初三', '高一', '高二', '高三'))
);

-- 索引
CREATE INDEX idx_students_phone ON students(phone);
CREATE INDEX idx_students_grade ON students(grade);
CREATE INDEX idx_students_status ON students(status);

-- 注释
COMMENT ON TABLE students IS '学生信息表';
COMMENT ON COLUMN students.id IS '学生ID';
COMMENT ON COLUMN students.name IS '学生姓名';
COMMENT ON COLUMN students.phone IS '手机号，作为登录账号';
COMMENT ON COLUMN students.password_hash IS 'bcrypt加密的密码哈希';
```

### 2.2 课程表 (courses)

```sql
CREATE TABLE courses (
    id VARCHAR(50) PRIMARY KEY COMMENT '课程ID，如MATH_JUNIOR_01',
    name VARCHAR(100) NOT NULL COMMENT '课程名称',
    grade VARCHAR(20) NOT NULL COMMENT '适用年级',
    subject VARCHAR(20) NOT NULL COMMENT '学科',
    description TEXT COMMENT '课程描述',
    total_knowledge_points INTEGER DEFAULT 0 COMMENT '知识点总数',
    estimated_hours DECIMAL(5,2) COMMENT '预估学习时长（小时）',
    status VARCHAR(20) DEFAULT 'active' COMMENT '状态：active/draft/archived',
    sort_order INTEGER DEFAULT 0 COMMENT '排序权重',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_subject CHECK (subject IN ('数学', '语文', '英语', '物理', '化学'))
);

-- 索引
CREATE INDEX idx_courses_grade ON courses(grade);
CREATE INDEX idx_courses_subject ON courses(subject);
CREATE INDEX idx_courses_status ON courses(status);

-- 注释
COMMENT ON TABLE courses IS '课程信息表';
```

### 2.3 知识点表 (knowledge_points)

```sql
CREATE TABLE knowledge_points (
    id VARCHAR(20) PRIMARY KEY COMMENT '知识点ID，如K1, K2',
    course_id VARCHAR(50) NOT NULL COMMENT '所属课程ID',
    name VARCHAR(100) NOT NULL COMMENT '知识点名称',
    type VARCHAR(20) NOT NULL COMMENT '类型：概念/公式/技能',
    description TEXT COMMENT '知识点描述',
    level INTEGER NOT NULL COMMENT '层级：0-6',
    sort_order INTEGER DEFAULT 0 COMMENT '同层级内排序',
    key_points JSONB COMMENT '核心要点数组',
    mastery_criteria JSONB NOT NULL COMMENT '掌握标准配置',
    teaching_config JSONB NOT NULL COMMENT '教学配置',
    content_template TEXT COMMENT '教学内容模板（可选）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_kp_course FOREIGN KEY (course_id) REFERENCES courses(id),
    CONSTRAINT chk_kp_type CHECK (type IN ('概念', '公式', '技能'))
);

-- 索引
CREATE INDEX idx_kp_course ON knowledge_points(course_id);
CREATE INDEX idx_kp_level ON knowledge_points(level);
CREATE INDEX idx_kp_type ON knowledge_points(type);

-- 注释
COMMENT ON TABLE knowledge_points IS '知识点表';
COMMENT ON COLUMN knowledge_points.mastery_criteria IS '掌握标准JSON，包含type/method/question_count/pass_threshold';
COMMENT ON COLUMN knowledge_points.teaching_config IS '教学配置JSON，包含use_examples/ask_questions/question_positions';
```

### 2.4 知识点依赖关系表 (knowledge_point_dependencies)

```sql
CREATE TABLE knowledge_point_dependencies (
    id SERIAL PRIMARY KEY,
    kp_id VARCHAR(20) NOT NULL COMMENT '知识点ID',
    depends_on_kp_id VARCHAR(20) NOT NULL COMMENT '依赖的知识点ID',
    dependency_type VARCHAR(20) DEFAULT 'prerequisite' COMMENT '依赖类型：prerequisite/related',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_kpd_kp FOREIGN KEY (kp_id) REFERENCES knowledge_points(id),
    CONSTRAINT fk_kpd_depends FOREIGN KEY (depends_on_kp_id) REFERENCES knowledge_points(id),
    CONSTRAINT uk_kpd UNIQUE (kp_id, depends_on_kp_id)
);

-- 索引
CREATE INDEX idx_kpd_kp ON knowledge_point_dependencies(kp_id);
CREATE INDEX idx_kpd_depends ON knowledge_point_dependencies(depends_on_kp_id);

-- 注释
COMMENT ON TABLE knowledge_point_dependencies IS '知识点依赖关系表';
```

### 2.5 学生学习档案表 (student_profiles)

```sql
CREATE TABLE student_profiles (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL COMMENT '学生ID',
    course_id VARCHAR(50) NOT NULL COMMENT '课程ID',
    current_kp_id VARCHAR(20) COMMENT '当前学习的知识点ID',
    completed_kp_ids JSONB DEFAULT '[]' COMMENT '已完成的知识点ID列表',
    mastered_kp_ids JSONB DEFAULT '[]' COMMENT '已掌握的知识点ID列表',
    skipped_kp_ids JSONB DEFAULT '[]' COMMENT '已跳过的知识点ID列表',
    mastery_rate DECIMAL(5,4) DEFAULT 0 COMMENT '掌握率',
    total_time INTEGER DEFAULT 0 COMMENT '总学习时长（秒）',
    session_count INTEGER DEFAULT 0 COMMENT '学习会话次数',
    last_session_at TIMESTAMP COMMENT '最后学习时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_sp_student FOREIGN KEY (student_id) REFERENCES students(id),
    CONSTRAINT fk_sp_course FOREIGN KEY (course_id) REFERENCES courses(id),
    CONSTRAINT fk_sp_kp FOREIGN KEY (current_kp_id) REFERENCES knowledge_points(id),
    CONSTRAINT uk_sp_student_course UNIQUE (student_id, course_id)
);

-- 索引
CREATE INDEX idx_sp_student ON student_profiles(student_id);
CREATE INDEX idx_sp_course ON student_profiles(course_id);
CREATE INDEX idx_sp_current_kp ON student_profiles(current_kp_id);

-- 注释
COMMENT ON TABLE student_profiles IS '学生学习档案表';
```

### 2.6 学习记录表 (learning_records)

```sql
CREATE TABLE learning_records (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL COMMENT '学生ID',
    kp_id VARCHAR(20) NOT NULL COMMENT '知识点ID',
    status VARCHAR(20) NOT NULL COMMENT '状态：learning/mastered/skipped/pending',
    attempt_count INTEGER DEFAULT 0 COMMENT '尝试次数',
    attempts JSONB DEFAULT '[]' COMMENT '每次尝试的详细信息',
    mastery_time TIMESTAMP COMMENT '掌握时间',
    total_time INTEGER DEFAULT 0 COMMENT '总学习时长（秒）',
    skip_info JSONB COMMENT '跳过信息',
    review_info JSONB COMMENT '复习信息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_lr_student FOREIGN KEY (student_id) REFERENCES students(id),
    CONSTRAINT fk_lr_kp FOREIGN KEY (kp_id) REFERENCES knowledge_points(id),
    CONSTRAINT chk_lr_status CHECK (status IN ('learning', 'mastered', 'skipped', 'pending', 'backtrack'))
);

-- 索引
CREATE INDEX idx_lr_student ON learning_records(student_id);
CREATE INDEX idx_lr_kp ON learning_records(kp_id);
CREATE INDEX idx_lr_status ON learning_records(status);
CREATE INDEX idx_lr_student_kp ON learning_records(student_id, kp_id);

-- 注释
COMMENT ON TABLE learning_records IS '学习记录表';
COMMENT ON COLUMN learning_records.attempts IS '尝试记录JSON数组，每次包含attempt_id/start_time/end_time/result/error_type等';
COMMENT ON COLUMN learning_records.skip_info IS '跳过信息JSON，包含skip_time/reason/later_reviewed';
COMMENT ON COLUMN learning_records.review_info IS '复习信息JSON，包含review_count/last_review_time';
```

### 2.7 学习会话表 (learning_sessions)

```sql
CREATE TABLE learning_sessions (
    id VARCHAR(50) PRIMARY KEY COMMENT '会话ID',
    student_id INTEGER NOT NULL COMMENT '学生ID',
    course_id VARCHAR(50) NOT NULL COMMENT '课程ID',
    kp_id VARCHAR(20) COMMENT '当前知识点ID',
    status VARCHAR(20) DEFAULT 'active' COMMENT '状态：active/completed/abandoned',
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
    end_time TIMESTAMP COMMENT '结束时间',
    duration INTEGER COMMENT '持续时间（秒）',
    result VARCHAR(20) COMMENT '结果：passed/failed/skipped',
    summary JSONB COMMENT '会话摘要',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_ls_student FOREIGN KEY (student_id) REFERENCES students(id),
    CONSTRAINT fk_ls_course FOREIGN KEY (course_id) REFERENCES courses(id),
    CONSTRAINT fk_ls_kp FOREIGN KEY (kp_id) REFERENCES knowledge_points(id),
    CONSTRAINT chk_ls_status CHECK (status IN ('active', 'completed', 'abandoned'))
);

-- 索引
CREATE INDEX idx_ls_student ON learning_sessions(student_id);
CREATE INDEX idx_ls_course ON learning_sessions(course_id);
CREATE INDEX idx_ls_kp ON learning_sessions(kp_id);
CREATE INDEX idx_ls_status ON learning_sessions(status);
CREATE INDEX idx_ls_start_time ON learning_sessions(start_time);

-- 注释
COMMENT ON TABLE learning_sessions IS '学习会话表';
```

### 2.8 评估题目表 (assessment_questions)

```sql
CREATE TABLE assessment_questions (
    id VARCHAR(20) PRIMARY KEY COMMENT '题目ID，如K1_Q1',
    kp_id VARCHAR(20) NOT NULL COMMENT '知识点ID',
    type VARCHAR(20) NOT NULL COMMENT '题型：选择题/填空题/判断题/计算题',
    content TEXT NOT NULL COMMENT '题目内容',
    options JSONB COMMENT '选项（选择题时）',
    correct_answer JSONB NOT NULL COMMENT '正确答案',
    explanation TEXT COMMENT '答案解析',
    difficulty VARCHAR(20) DEFAULT '基础' COMMENT '难度：基础/中等/困难',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_aq_kp FOREIGN KEY (kp_id) REFERENCES knowledge_points(id),
    CONSTRAINT chk_aq_type CHECK (type IN ('选择题', '填空题', '判断题', '计算题', '作图题'))
);

-- 索引
CREATE INDEX idx_aq_kp ON assessment_questions(kp_id);
CREATE INDEX idx_aq_type ON assessment_questions(type);
CREATE INDEX idx_aq_difficulty ON assessment_questions(difficulty);

-- 注释
COMMENT ON TABLE assessment_questions IS '评估题目表';
```

### 2.9 学生答题记录表 (student_answers)

```sql
CREATE TABLE student_answers (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL COMMENT '会话ID',
    student_id INTEGER NOT NULL COMMENT '学生ID',
    question_id VARCHAR(20) NOT NULL COMMENT '题目ID',
    kp_id VARCHAR(20) NOT NULL COMMENT '知识点ID',
    student_answer JSONB NOT NULL COMMENT '学生答案',
    is_correct BOOLEAN NOT NULL COMMENT '是否正确',
    response_time INTEGER COMMENT '答题时长（秒）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_sa_session FOREIGN KEY (session_id) REFERENCES learning_sessions(id),
    CONSTRAINT fk_sa_student FOREIGN KEY (student_id) REFERENCES students(id),
    CONSTRAINT fk_sa_question FOREIGN KEY (question_id) REFERENCES assessment_questions(id),
    CONSTRAINT fk_sa_kp FOREIGN KEY (kp_id) REFERENCES knowledge_points(id)
);

-- 索引
CREATE INDEX idx_sa_session ON student_answers(session_id);
CREATE INDEX idx_sa_student ON student_answers(student_id);
CREATE INDEX idx_sa_question ON student_answers(question_id);
CREATE INDEX idx_sa_kp ON student_answers(kp_id);
CREATE INDEX idx_sa_created ON student_answers(created_at);

-- 注释
COMMENT ON TABLE student_answers IS '学生答题记录表';
```

---

## 三、MongoDB集合设计

### 3.1 会话日志集合 (session_logs)

```javascript
// 集合结构
db.createCollection("session_logs", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["session_id", "student_id", "kp_id", "start_time"],
            properties: {
                _id: { bsonType: "objectId" },
                session_id: { bsonType: "string" },
                student_id: { bsonType: "int" },
                kp_id: { bsonType: "string" },
                start_time: { bsonType: "date" },
                end_time: { bsonType: "date" },
                interactions: {
                    bsonType: "array",
                    items: {
                        bsonType: "object",
                        properties: {
                            sequence: { bsonType: "int" },
                            timestamp: { bsonType: "date" },
                            actor: { bsonType: "string" },  // AI / Student
                            type: { bsonType: "string" },    // 讲解/提问/回答/反馈
                            content: { bsonType: "string" },
                            whiteboard_content: { bsonType: "object" },
                            input_method: { bsonType: "string" }  // text/voice
                        }
                    }
                },
                result: { bsonType: "string" },
                assessment: {
                    bsonType: "object",
                    properties: {
                        questions_asked: { bsonType: "int" },
                        correct_answers: { bsonType: "int" },
                        pass_threshold: { bsonType: "int" },
                        passed: { bsonType: "bool" }
                    }
                },
                llm_calls: {
                    bsonType: "array",
                    items: {
                        bsonType: "object",
                        properties: {
                            call_id: { bsonType: "string" },
                            timestamp: { bsonType: "date" },
                            prompt_tokens: { bsonType: "int" },
                            completion_tokens: { bsonType: "int" },
                            total_tokens: { bsonType: "int" },
                            response_time_ms: { bsonType: "int" },
                            model: { bsonType: "string" }
                        }
                    }
                }
            }
        }
    }
});

// 索引
db.session_logs.createIndex({ "session_id": 1 }, { unique: true });
db.session_logs.createIndex({ "student_id": 1 });
db.session_logs.createIndex({ "kp_id": 1 });
db.session_logs.createIndex({ "start_time": -1 });
db.session_logs.createIndex({ "student_id": 1, "start_time": -1 });
```

### 3.2 交互日志集合 (interaction_logs)

```javascript
// 集合结构
db.createCollection("interaction_logs", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["session_id", "student_id", "timestamp"],
            properties: {
                _id: { bsonType: "objectId" },
                session_id: { bsonType: "string" },
                student_id: { bsonType: "int" },
                timestamp: { bsonType: "date" },
                interaction_type: { bsonType: "string" },
                actor: { bsonType: "string" },
                content: { bsonType: "string" },
                response_time_ms: { bsonType: "int" },
                metadata: { bsonType: "object" }
            }
        }
    }
});

// 索引
db.interaction_logs.createIndex({ "session_id": 1 });
db.interaction_logs.createIndex({ "student_id": 1 });
db.interaction_logs.createIndex({ "timestamp": -1 });
db.interaction_logs.createIndex({ "interaction_type": 1 });
```

### 3.3 错误日志集合 (error_logs)

```javascript
// 集合结构
db.createCollection("error_logs", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["timestamp", "error_type"],
            properties: {
                _id: { bsonType: "objectId" },
                timestamp: { bsonType: "date" },
                error_type: { bsonType: "string" },
                error_message: { bsonType: "string" },
                stack_trace: { bsonType: "string" },
                session_id: { bsonType: "string" },
                student_id: { bsonType: "int" },
                request_info: {
                    bsonType: "object",
                    properties: {
                        url: { bsonType: "string" },
                        method: { bsonType: "string" },
                        headers: { bsonType: "object" },
                        body: { bsonType: "object" }
                    }
                },
                resolved: { bsonType: "bool" },
                resolved_at: { bsonType: "date" },
                resolved_by: { bsonType: "string" }
            }
        }
    }
});

// 索引
db.error_logs.createIndex({ "timestamp": -1 });
db.error_logs.createIndex({ "error_type": 1 });
db.error_logs.createIndex({ "resolved": 1 });
db.error_logs.createIndex({ "session_id": 1 });
```

---

## 四、Redis数据结构设计

### 4.1 会话状态缓存

```
# Key: session:{session_id}
# Type: Hash
# TTL: 24小时

session:SESSION_001 = {
    "student_id": "1",
    "course_id": "MATH_JUNIOR_01",
    "current_kp_id": "K15",
    "status": "active",
    "start_time": "2025-01-15T10:00:00Z",
    "last_activity": "2025-01-15T10:30:00Z",
    "message_count": "15",
    "teaching_stage": "讲解"
}
```

### 4.2 学习进度缓存

```
# Key: student:{student_id}:progress:{course_id}
# Type: Hash
# TTL: 7天

student:1:progress:MATH_JUNIOR_01 = {
    "current_kp": "K22",
    "completed_count": "21",
    "mastered_count": "19",
    "mastery_rate": "0.59",
    "total_time": "36000"
}
```

### 4.3 知识点模板缓存

```
# Key: kp:template:{kp_id}
# Type: String (JSON)
# TTL: 24小时

kp:template:K15 = '{"introduction":"...", "definition":"...", "example":"...", "summary":"..."}'
```

### 4.4 LLM响应缓存

```
# Key: llm:cache:{hash(prompt)}
# Type: String (JSON)
# TTL: 1小时

llm:cache:abc123 = '{"response_type":"讲解", "content":{...}}'
```

### 4.5 请求限流

```
# Key: rate_limit:{ip}
# Type: String (计数器)
# TTL: 1分钟

rate_limit:192.168.1.1 = "45"  # 1分钟内请求45次
```

---

## 五、JSON字段详细结构

### 5.1 mastery_criteria 结构

```json
{
    "type": "concept_check",
    "method": "选择题",
    "question_count": 2,
    "pass_threshold": 1
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 检查类型：concept_check/formula_check/skill_check |
| method | string | 评估方式：选择题/填空题/判断题/计算题 |
| question_count | int | 题目数量 |
| pass_threshold | int | 通过阈值（答对题数） |

### 5.2 teaching_config 结构

```json
{
    "use_examples": true,
    "ask_questions": true,
    "question_positions": ["讲解中段", "讲解结束"]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| use_examples | boolean | 是否使用示例 |
| ask_questions | boolean | 是否提问 |
| question_positions | array | 提问位置列表 |

### 5.3 attempts 结构（学习记录表）

```json
[
    {
        "attempt_id": 1,
        "start_time": "2025-01-15T10:00:00Z",
        "end_time": "2025-01-15T10:15:00Z",
        "result": "failed",
        "error_type": "概念混淆",
        "backtrack_to": "K12",
        "score": 0.5
    },
    {
        "attempt_id": 2,
        "start_time": "2025-01-15T10:20:00Z",
        "end_time": "2025-01-15T10:30:00Z",
        "result": "passed",
        "score": 1.0
    }
]
```

### 5.4 skip_info 结构

```json
{
    "skip_time": "2025-01-15T09:00:00Z",
    "reason": "学生表示已掌握",
    "later_reviewed": false
}
```

### 5.5 review_info 结构

```json
{
    "review_count": 2,
    "reviews": [
        {
            "request_time": "2025-01-16T14:00:00Z",
            "trigger_type": "student_initiated"
        }
    ]
}
```

---

## 六、数据迁移脚本

### 6.1 初始化课程数据

```sql
-- 插入课程
INSERT INTO courses (id, name, grade, subject, description, total_knowledge_points, estimated_hours)
VALUES ('MATH_JUNIOR_01', '一次函数', '初一', '数学', '初一数学一次函数单元', 32, 12);

-- 插入知识点（示例）
INSERT INTO knowledge_points (id, course_id, name, type, description, level, mastery_criteria, teaching_config)
VALUES
('K1', 'MATH_JUNIOR_01', '坐标系', '概念', '平面直角坐标系的建立', 0,
 '{"type":"concept_check","method":"选择题","question_count":2,"pass_threshold":1}',
 '{"use_examples":true,"ask_questions":true,"question_positions":["讲解结束"]}'),
('K2', 'MATH_JUNIOR_01', '点的坐标', '技能', '用有序数对表示点的位置', 1,
 '{"type":"skill_check","method":"填空题","question_count":2,"pass_threshold":1}',
 '{"use_examples":true,"ask_questions":true,"question_positions":["讲解中段","讲解结束"]}')
-- ... 其他知识点
;

-- 插入依赖关系
INSERT INTO knowledge_point_dependencies (kp_id, depends_on_kp_id)
VALUES
('K2', 'K1'),
('K6', 'K4'),
('K6', 'K5')
-- ... 其他依赖关系
;
```

### 6.2 导入评估题目

```sql
-- 从JSON文件导入
\set content `cat /path/to/assessment_questions.json`

INSERT INTO assessment_questions (id, kp_id, type, content, options, correct_answer, explanation, difficulty)
SELECT
    item->>'id',
    item->>'kp_id',
    item->>'type',
    item->>'content',
    item->'options',
    item->'correct_answer',
    item->>'explanation',
    item->>'difficulty'
FROM json_array_elements(:'content::json) AS item;
```

---

## 七、数据库连接配置

### 7.1 SQLAlchemy模型示例

```python
# models/student.py
from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean
from sqlalchemy.sql import func
from app.database import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    grade = Column(String(20), nullable=False)
    phone = Column(String(20), unique=True)
    password_hash = Column(String(255), nullable=False)
    avatar_url = Column(String(255))
    status = Column(String(20), default='active')
    last_login_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
```

### 7.2 连接池配置

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # PostgreSQL
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "ai_teacher"

    @property
    def DATABASE_URL(self):
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # MongoDB
    MONGO_HOST: str = "localhost"
    MONGO_PORT: int = 27017
    MONGO_DB: str = "ai_teacher_logs"

    @property
    def MONGO_URL(self):
        return f"mongodb://{self.MONGO_HOST}:{self.MONGO_PORT}"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 八、查询示例

### 8.1 获取学生的下一个待学习知识点

```sql
-- 查询学生的当前知识点和下一个知识点
WITH current_kp AS (
    SELECT current_kp_id, level
    FROM student_profiles sp
    JOIN knowledge_points kp ON sp.current_kp_id = kp.id
    WHERE sp.student_id = :student_id AND sp.course_id = :course_id
),
next_kp AS (
    SELECT kp.id, kp.name, kp.level
    FROM knowledge_points kp
    WHERE kp.course_id = :course_id
    AND (
        kp.level > (SELECT level FROM current_kp)
        OR (kp.level = (SELECT level FROM current_kp) AND kp.sort_order >
            (SELECT sort_order FROM knowledge_points WHERE id = (SELECT current_kp_id FROM current_kp)))
    )
    AND kp.id NOT IN (
        SELECT jsonb_array_elements_text(completed_kp_ids)
        FROM student_profiles
        WHERE student_id = :student_id AND course_id = :course_id
    )
    ORDER BY kp.level, kp.sort_order
    LIMIT 1
)
SELECT * FROM next_kp;
```

### 8.2 获取知识点的所有前置依赖（递归）

```sql
WITH RECURSIVE kp_dependencies AS (
    -- 基础查询：直接依赖
    SELECT kp_id, depends_on_kp_id, 1 AS depth
    FROM knowledge_point_dependencies
    WHERE kp_id = :kp_id

    UNION ALL

    -- 递归查询：间接依赖
    SELECT kpd.kp_id, kpd.depends_on_kp_id, kd.depth + 1
    FROM knowledge_point_dependencies kpd
    JOIN kp_dependencies kd ON kpd.kp_id = kd.depends_on_kp_id
    WHERE kd.depth < 10  -- 防止无限递归
)
SELECT DISTINCT depends_on_kp_id AS kp_id, kp.name, kp.type
FROM kp_dependencies kd
JOIN knowledge_points kp ON kd.depends_on_kp_id = kp.id
ORDER BY kd.depth DESC;
```

### 8.3 统计学生的学习效果

```sql
-- 按知识点类型统计掌握率
SELECT
    kp.type,
    COUNT(*) AS total_kp,
    COUNT(CASE WHEN lr.status = 'mastered' THEN 1 END) AS mastered_kp,
    ROUND(
        COUNT(CASE WHEN lr.status = 'mastered' THEN 1 END)::numeric / COUNT(*)::numeric * 100,
        2
    ) AS mastery_rate
FROM learning_records lr
JOIN knowledge_points kp ON lr.kp_id = kp.id
WHERE lr.student_id = :student_id
GROUP BY kp.type;
```

---

**文档结束**