# 年级科目管理API使用文档

## 概述

本文档描述了基于DDD设计的年级和科目管理API接口。

## 数据模型

### Grade（年级）

- `id`: 年级ID（格式：G_{code}，如 G_C1）
- `name`: 年级名称（如"初一"）
- `code`: 年级代码（如"C1"）
- `level`: 学段（primary/middle/high）
- `subjects`: 该年级下的科目列表
- `sort_order`: 排序序号
- `status`: 状态（active/inactive）

### Subject（科目）

- `id`: 科目ID（格式：S_{code}，如 S_MATH）
- `name`: 科目名称（如"数学"）
- `code`: 科目代码（如"MATH"）
- `category`: 科目类别（science/arts/language/comprehensive）
- `sort_order`: 排序序号
- `status`: 状态（active/inactive）

### GradeSubject（年级-科目关联）

- `id`: 关联ID
- `grade_id`: 年级ID
- `subject_id`: 科目ID
- `sort_order`: 该年级下科目的排序
- `status`: 状态

## API接口

### 年级管理

#### 获取所有年级

```http
GET /api/v1/admin/grades
```

查询参数：
- `level`（可选）：按学段过滤（primary/middle/high）
- `active_only`（可选）：仅返回启用的年级

响应示例：
```json
{
  "grades": [
    {
      "id": "G_C1",
      "name": "初一",
      "code": "C1",
      "level": "middle",
      "subjects": [...],
      "sort_order": 1,
      "status": "active",
      "created_at": "2026-04-08T16:00:00",
      "updated_at": "2026-04-08T16:00:00"
    }
  ],
  "total": 6
}
```

#### 创建年级

```http
POST /api/v1/admin/grades
```

请求体：
```json
{
  "name": "初一",
  "code": "C1",
  "level": "middle",
  "sort_order": 1,
  "description": "初中一年级"
}
```

#### 获取年级详情

```http
GET /api/v1/admin/grades/{grade_id}
```

#### 更新年级

```http
PUT /api/v1/admin/grades/{grade_id}
```

请求体：
```json
{
  "name": "初一",
  "sort_order": 1,
  "status": "active"
}
```

#### 删除年级

```http
DELETE /api/v1/admin/grades/{grade_id}
```

### 年级科目关联管理

#### 获取年级下的所有科目

```http
GET /api/v1/admin/grades/{grade_id}/subjects
```

响应示例：
```json
[
  {
    "id": "GS_G_C1_S_MATH",
    "grade_id": "G_C1",
    "subject_id": "S_MATH",
    "sort_order": 1,
    "status": "active",
    "created_at": "2026-04-08T16:00:00",
    "updated_at": "2026-04-08T16:00:00"
  }
]
```

#### 为年级添加科目

```http
POST /api/v1/admin/grades/{grade_id}/subjects
```

请求体：
```json
{
  "subject_id": "S_MATH",
  "sort_order": 1
}
```

#### 从年级移除科目

```http
DELETE /api/v1/admin/grades/{grade_id}/subjects/{subject_id}
```

### 科目管理

#### 获取所有科目

```http
GET /api/v1/admin/subjects
```

查询参数：
- `category`（可选）：按类别过滤
- `active_only`（可选）：仅返回启用的科目

#### 创建科目

```http
POST /api/v1/admin/subjects
```

请求体：
```json
{
  "name": "数学",
  "code": "MATH",
  "category": "science",
  "sort_order": 1,
  "description": "数学科目"
}
```

#### 获取科目详情

```http
GET /api/v1/admin/subjects/{subject_id}
```

#### 更新科目

```http
PUT /api/v1/admin/subjects/{subject_id}
```

#### 删除科目

```http
DELETE /api/v1/admin/subjects/{subject_id}
```

## 使用示例

### 示例1：创建年级并添加科目

```bash
# 1. 创建年级
curl -X POST http://localhost:8000/api/v1/admin/grades \
  -H "Content-Type: application/json" \
  -d '{
    "name": "初一",
    "code": "C1",
    "level": "middle",
    "sort_order": 1
  }'

# 2. 为年级添加科目
curl -X POST http://localhost:8000/api/v1/admin/grades/G_C1/subjects \
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": "S_MATH",
    "sort_order": 1
  }'

# 3. 查看年级详情（包含科目列表）
curl http://localhost:8000/api/v1/admin/grades/G_C1
```

### 示例2：初始化年级科目数据

```bash
# 运行初始化脚本
python scripts/init_grade_subjects.py
```

## 数据持久化

年级和科目数据存储在以下JSON文件中：
- `data/grades.json` - 年级数据
- `data/subjects.json` - 科目数据

每次创建、更新或删除操作都会自动保存到文件。

## 错误处理

API返回标准的HTTP状态码：
- `200 OK` - 成功
- `201 Created` - 创建成功
- `204 No Content` - 删除成功
- `400 Bad Request` - 请求参数错误
- `404 Not Found` - 资源不存在
- `409 Conflict` - 资源冲突（如重复创建）

错误响应格式：
```json
{
  "detail": "Grade with name '初一' already exists"
}
```

## 下一步工作

1. **章节数据迁移**：将现有章节的 `grade` 和 `subject` 字段迁移为外键引用
2. **前端集成**：更新前端代码使用新的API接口
3. **数据验证**：添加更完善的业务规则验证
4. **测试覆盖**：编写单元测试和集成测试
