# AI 虚拟教师系统 - 项目总结

> **文档目的**: 让大模型在新开工作空间后,通过此文档和worklog目录下的每日工作记录,快速了解项目情况

**项目状态**: MVP 开发阶段  
**当前版本**: 极简版  
**最后更新**: 2026年4月14日

---

## 📋 项目概述

### 项目定位

AI 虚拟教师系统是一款面向 K12 学生的个性化智能教学产品。系统通过预设的课程知识图谱,结合大语言模型的讲解与交互能力,为学生提供自适应的学习路径和精准的知识点讲解。

### MVP 验证目标

| 验证目标 | 成功标准 |
|---------|---------|
| AI 讲解+提问的效果 | 平均正确率 ≥ 70% |
| 学习目标达成率 | 达标率 ≥ 80% |

### MVP 试点范围

- **学科**: 数学
- **单元**: 初一数学"一次函数"
- **知识点数量**: 32个(极简版合并为10个模块)
- **目标用户**: 初一学生

---

## 🎯 核心功能特性

### 已实现功能

#### 1. **极简版学习系统** ✅
- 单列对话式布局,专注学习
- 三步学习循环: 讲解 → 提问 → 反馈
- 流式输出,打字机效果实时响应
- 公式渲染(KaTeX)
- 进度条展示学习进度

#### 2. **知识图谱可视化** ✅
- D3.js 分层布局展示知识点
- 7层层级结构(基础概念→综合应用)
- 层级框和层级描述
- 递归前置依赖关系展示
- 悬浮/点击交互显示关联

#### 3. **学生学习档案** ✅
- 学习进度跟踪
- 掌握率统计
- 学习时长记录
- 知识点状态管理

#### 4. **AI 讲解引擎** ✅
- 智谱 AI GLM-4 集成
- 个性化讲解内容生成
- 自适应提问策略
- 即时反馈机制

### 极简版设计原则

**砍掉的功能**:
- ❌ 白板组件(分散注意力)
- ❌ 学习地图可视化(进度条足够)
- ❌ 课前诊断测试(增加入口摩擦)
- ❌ 语音输入输出(数学学习打字更快)
- ❌ 多种教学模式(统一成一种)
- ❌ 跳过知识点功能(应证明掌握)

**保留的核心**:
- ✅ 单列对话式布局
- ✅ 三步学习循环
- ✅ 公式渲染
- ✅ 进度条
- ✅ 选择题交互
- ✅ 流式输出

---

## 🛠️ 技术栈

### 前端技术

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18.x | 前端框架 |
| TypeScript | 5.x | 类型安全 |
| Vite | 5.x | 构建工具 |
| Ant Design | 5.x | UI 组件库 |
| D3.js | 7.x | 知识图谱可视化 |
| KaTeX | 0.16.x | 数学公式渲染 |
| Zustand | 4.x | 状态管理 |
| Axios | 1.x | HTTP 请求 |

### 后端技术

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.11 | 后端语言 |
| FastAPI | 0.109+ | Web 框架 |
| Pydantic | 2.x | 数据验证 |
| 智谱 AI SDK | 2.x | LLM 调用 |

### 数据存储

| 数据库 | 用途 |
|--------|------|
| PostgreSQL 15 | 主数据库(核心业务数据) |
| Redis 7.x | 缓存、会话存储 |
| MongoDB 6.x | 日志存储(MVP阶段暂未使用) |

### AI 能力

| 服务 | 提供商 | 用途 |
|------|--------|------|
| GLM-4 | 智谱 AI | 讲解、提问、决策 |
| ASR | 讯飞(暂未使用) | 语音识别 |
| TTS | 讯飞(暂未使用) | 语音合成 |

---

## 🏗️ 系统架构

### 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                      客户端层                             │
│  React + TypeScript (Web端)                             │
│  - 对话组件 - 公式渲染 - 进度组件 - 知识图谱            │
└─────────────────────────────────────────────────────────┘
                        ↓ HTTP/WebSocket
┌─────────────────────────────────────────────────────────┐
│                      API 层                              │
│  FastAPI (Python)                                       │
│  - 学习服务 - 课程服务 - 对话服务 - LLM服务            │
└─────────────────────────────────────────────────────────┘
                        ↓
        ┌───────────────┼───────────────┐
        ↓               ↓               ↓
    智谱 AI          PostgreSQL       Redis
    (LLM能力)        (主数据库)        (缓存)
```

### 核心数据模型

#### 1. 课程模型 (Course)
```python
@dataclass
class Course:
    id: str                          # 课程ID
    name: str                        # 课程名称
    grade: str                       # 年级
    subject: Subject                 # 学科
    description: Optional[str]       # 描述
    total_knowledge_points: int      # 知识点总数
    level_descriptions: dict[int, str]  # 层级描述
```

#### 2. 知识点模型 (KnowledgePoint)
```python
@dataclass
class KnowledgePoint:
    id: str                          # 知识点ID (K1, K2...)
    name: str                        # 知识点名称
    type: KnowledgePointType         # 类型: 概念/公式/技能
    description: str                 # 描述
    level: int                       # 层级 (0-6)
    dependencies: List[str]          # 前置依赖
    mastery_criteria: Dict           # 掌握标准
```

#### 3. 学生档案模型 (StudentProfile)
```python
@dataclass
class StudentProfile:
    student_id: int
    course_id: str
    current_kp_id: Optional[str]     # 当前知识点
    completed_kp_ids: List[str]      # 已完成知识点
    mastered_kp_ids: List[str]       # 已掌握知识点
    mastery_rate: float              # 掌握率
```

---

## 📁 项目目录结构

```
aiteacher-2/
├── ai-teacher-backend/           # 后端代码
│   ├── app/
│   │   ├── api/                  # API 路由
│   │   │   ├── learning.py       # 学习相关 API
│   │   │   ├── student.py        # 学生相关 API
│   │   │   └── ...
│   │   ├── models/               # 数据模型
│   │   │   ├── student.py
│   │   │   ├── course.py
│   │   │   └── learning.py
│   │   ├── services/             # 业务逻辑
│   │   │   ├── llm_service.py    # LLM 调用
│   │   │   ├── learning_service.py  # 学习服务
│   │   │   └── ...
│   │   ├── prompts/              # Prompt 模板
│   │   │   ├── teaching_prompt.py
│   │   │   ├── question_prompt.py
│   │   │   └── ...
│   │   └── db/                   # 数据库
│   │       ├── memory_db.py      # 内存数据库(MVP)
│   │       └── ...
│   └── .env                      # 环境变量
│
├── ai-teacher-frontend/          # 前端代码
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Learning.tsx      # 学习页面
│   │   │   └── ...
│   │   ├── components/
│   │   │   ├── chat/             # 对话组件
│   │   │   ├── knowledge-graph/  # 知识图谱组件
│   │   │   │   ├── KnowledgeGraph.tsx
│   │   │   │   └── KnowledgeGraph.css
│   │   │   └── ...
│   │   └── services/             # API 服务
│   └── package.json
│
├── worklog/                      # 工作日志目录 ⭐
│   ├── 2026-04-06/               # 每日工作记录
│   │   ├── README.md             # 当日概览
│   │   ├── 功能开发.md           # 功能开发记录
│   │   └── 问题修复.md           # 问题修复记录
│   └── README.md                 # 本文档
│
├── AI虚拟教师系统 MVP需求规格说明书.md
├── 技术选型方案.md
├── 数据库Schema设计.md
├── 极简版设计方案.md
├── 极简版学习系统设计文档.md
└── AGENT.md                      # AI 助手指引文档
```

---

## 🔑 关键技术实现

### 1. 知识图谱递归依赖算法

```typescript
// 递归获取所有前置依赖节点ID
const getAllPrerequisites = (
  nodeId: string,
  links: { source: string; target: string }[]
): Set<string> => {
  const prerequisites = new Set<string>();
  
  const findPrerequisites = (id: string) => {
    const directPrereqs = links
      .filter(link => link.target === id)
      .map(link => link.source);
    
    directPrereqs.forEach(prereqId => {
      if (!prerequisites.has(prereqId)) {
        prerequisites.add(prereqId);
        findPrerequisites(prereqId); // 递归查找
      }
    });
  };
  
  findPrerequisites(nodeId);
  return prerequisites;
};
```

### 2. 流式输出实现

后端使用 FastAPI 的 StreamingResponse:

```python
from fastapi.responses import StreamingResponse

async def chat_stream(request: ChatRequest):
    async def generate():
        async for chunk in llm_service.chat_stream(request):
            yield f"data: {chunk.json()}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

前端使用 EventSource 接收:

```typescript
const eventSource = new EventSource(url);
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  setMessages(prev => [...prev, data]);
};
```

### 3. 知识点层级描述

后端数据结构:

```python
course = Course(
    id="MATH_JUNIOR_01",
    name="一次函数",
    level_descriptions={
        0: "基础概念层",
        1: "核心概念层",
        2: "函数基础层",
        3: "正比例与一次函数层",
        4: "图象与性质层",
        5: "变换层",
        6: "综合应用层",
    }
)
```

---

## 📊 开发进度

### 已完成里程碑

- ✅ **2026-03-24**: 极简版设计完成
- ✅ **2026-03-25**: 前端基础架构搭建
- ✅ **2026-03-26**: 后端 API 开发
- ✅ **2026-03-27**: 知识图谱可视化初版
- ✅ **2026-04-06**: 知识图谱重构(分层布局+递归依赖)

### 当前工作重点

1. **知识图谱优化**: 分层布局、递归依赖展示 ✅
2. **学习流程优化**: 极简版三步循环
3. **AI 讲解质量**: Prompt 工程优化

### 待办事项

- [ ] 完善学生答题记录和统计分析
- [ ] 添加知识点掌握度评估
- [ ] 优化 LLM 调用成本(缓存策略)
- [ ] 添加错误处理和降级方案
- [ ] 性能优化和测试

---

## 🚀 如何使用 Worklog 目录

### 目录结构说明

`worklog/` 目录用于存储项目开发过程中的工作记录:

```
worklog/
├── README.md              # 项目总结文档(本文档)
├── 2026-04-06/           # 每日工作记录(按日期)
│   ├── README.md         # 当日工作概览
│   ├── 功能开发.md       # 功能开发详细记录
│   └── 问题修复.md       # Bug 修复记录
└── 2026-04-07/           # 新的一天记录
    └── ...
```

### 每日工作记录内容

每日子目录包含:

1. **README.md**: 当日工作概览
   - 工作日期、时长
   - 主要任务
   - 核心成果
   - 统计数据

2. **功能开发.md**: 新功能开发记录
   - 需求背景
   - 技术方案
   - 代码实现
   - 测试验证

3. **问题修复.md**: Bug 修复记录
   - 问题描述
   - 根因分析
   - 解决方案
   - 修复验证

### 如何快速了解项目

对于新开工作空间的大模型:

1. **先读本文档** (`worklog/README.md`)
   - 了解项目整体情况
   - 掌握技术栈和架构
   - 理解核心功能

2. **再看最近的工作记录**
   - 查看 `worklog/` 下的日期目录
   - 按时间倒序阅读
   - 了解最新进展

3. **然后查看关键设计文档**
   - `极简版设计方案.md` - 设计理念
   - `数据库Schema设计.md` - 数据结构
   - `技术选型方案.md` - 技术决策

4. **最后查看代码**
   - 根据需要在具体文件中查找实现细节

---

## 🎯 核心设计理念

### 极简主义

> "少即是多" - 乔布斯

**核心理念**: 砍掉一切不直接帮助学生理解知识点的功能,专注核心学习体验。

**设计原则**:
1. **专注** - 一页只做一件事
2. **即时反馈** - 答题后立即显示结果
3. **减少决策** - 系统自动推荐下一步
4. **成就感** - 可视化进度,明确提示完成

### 知识图谱可视化

**设计理念**: 清晰展示知识点之间的依赖关系,帮助学生理解学习路径。

**实现要点**:
- 使用分层布局替代力导向图,固定节点位置
- 递归展示所有前置依赖,而非只显示直接依赖
- 层级框和层级描述,增强可读性
- 悬浮/点击交互,按需显示关联关系

---

## 📈 项目指标

### 代码统计

- **前端代码**: ~3000 行 TypeScript/TSX
- **后端代码**: ~2000 行 Python
- **API 端点**: 5 个核心端点(极简版)
- **数据模型**: 10+ dataclass 模型

### 性能指标(目标)

| 指标 | 目标值 |
|------|--------|
| 页面加载时间 | < 1s |
| 首次学习时间 | < 15s |
| 单知识点学习时长 | ~5 分钟 |
| LLM 响应延迟 | < 2s |

### 成本估算

**单个学生完成一次函数单元**:
- LLM 调用: ~13.6 元
- 服务器: ~5.5 元/月(100 学生)
- **总计**: ~19 元/学生

---

## 🔧 开发环境设置

### 后端启动

```bash
cd ai-teacher-backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入智谱 AI API Key

# 启动服务
uvicorn app.main:app --reload
```

### 前端启动

```bash
cd ai-teacher-frontend
npm install
npm run dev
```

### 环境变量

后端 `.env` 文件:

```env
ZHIPU_API_KEY=your_api_key_here
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
```

---

## 🐛 已知问题和解决方案

### 1. 知识图谱节点抽搐问题 ✅ 已解决

**问题**: 鼠标悬浮时节点发生抽搐

**原因**: CSS `transform: scale()` 与 D3 transform 冲突

**解决**: 移除 CSS transform,改用 stroke-width 和 drop-shadow

### 2. 层级描述不显示 ✅ 已解决

**原因**: 后端数据未更新

**解决**: 在 memory_db.py 中添加 level_descriptions 字段并重启服务

### 3. 后置依赖连线仍显示 ✅ 已解决

**原因**: 连线逻辑未过滤方向

**解决**: 只显示 target 指向当前节点的连线

---

## 📚 相关文档

### 设计文档

- `AI虚拟教师系统 MVP需求规格说明书.md` - 完整需求规格
- `极简版设计方案.md` - 极简版设计理念
- `极简版学习系统设计文档.md` - 极简版详细设计
- `技术选型方案.md` - 技术选型决策
- `数据库Schema设计.md` - 数据库设计

### 开发文档

- `开发任务分解.md` - 任务分解和排期
- `学生档案功能设计方案.md` - 学生档案功能设计
- `流式输出方案实现总结.md` - 流式输出技术方案
- `进度展示设计方案.md` - 进度展示设计

### 数据文件

- `课程图谱_一次函数.json` - 一次函数课程数据
- `评估题库_一次函数.json` - 评估题目数据

---

## 🤝 AI 助手工作指引

### 当你接手这个项目时

1. **第一件事**: 阅读本文档,了解项目概况
2. **第二件事**: 查看 worklog 目录下最近的工作记录
3. **第三件事**: 检查 git status 了解当前状态
4. **第四件事**: 根据用户需求,参考相关设计文档

### 开发规范

1. **代码风格**: 遵循已有代码风格，后端代码规范参考worklog/rules.md 文档
2. **提交规范**: 使用语义化提交信息
3. **文档更新**: 重要改动需更新相关文档
4. **工作记录**: 每日使用 `@daily-work-summary` 生成工作记录

### 关键文件提示

- `ai-teacher-backend/app/db/memory_db.py` - 测试数据在这里
- `ai-teacher-backend/app/services/llm_service.py` - LLM 调用逻辑
- `ai-teacher-frontend/src/components/knowledge-graph/` - 知识图谱组件
- `ai-teacher-frontend/src/pages/Learning.tsx` - 学习主页面

---

## 📞 联系方式

项目维护者: 赵阳  
工作分支: `feature-zhaoyangyang`  
远程仓库: `origin/feature-zhaoyangyang`

---

## 📅 最近工作记录

### 2026年4月14日 - OpenSandbox沙箱环境集成 ⭐

**主要成果:**
- ✅ 完成OpenSandbox沙箱环境集成
- ✅ 实现Manim动画生成系统
- ✅ 编写完整技术文档体系（5份文档）
- ✅ 创建测试和部署脚本

**关键决策:**
- 沙箱方案选型: OpenSandbox + Docker
- 动画技术栈: Manim + LLM
- 部署架构: 分阶段部署策略

**统计数据:**
- 新增文件: 17个
- 新增代码: 4808行
- 提交次数: 1次

**详细文档:**
- [工作总结](./2026-04-14/README.md)
- [功能开发](./2026-04-14/功能开发.md)
- [文档更新](./2026-04-14/文档更新.md)
- [技术决策](./2026-04-14/技术决策.md)

### 2026年4月6日 - 知识图谱重构

**主要成果:**
- 知识图谱分层布局优化
- 递归依赖关系展示
- 层级描述完善

---

**文档版本**: v1.1  
**创建日期**: 2026年4月6日  
**最后更新**: 2026年4月14日

---

*此文档旨在帮助 AI 助手快速理解项目,提高协作效率。如有疑问,请参考 worklog 目录下的每日工作记录。*
