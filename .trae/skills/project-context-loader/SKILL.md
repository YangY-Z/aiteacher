---
name: project-context-loader
description: Load project context from worklog directory when starting daily work. Use this skill when the user indicates they are starting work for the day or wants to review project status. Automatically loads the project overview README and development rules from worklog directory.
---

# Project Context Loader

## Overview

Load project context from the worklog directory when starting daily work. This skill automatically reads the project overview README and development rules file to help AI assistants quickly understand the project status, guidelines, and continue work seamlessly.

## When to Use This Skill

This skill should be triggered when:
- User says "开始工作", "start work", "今天的工作", or similar phrases indicating the start of daily work
- User wants to review project status and overview
- User opens a new conversation session and wants to understand the project context
- User asks about project overview

## Core Workflow

### Step 1: Identify Worklog Directory

Locate the worklog directory at the project root:
```
<workspace>/worklog/
```

If the worklog directory does not exist, inform the user and suggest alternative ways to understand the project.

### Step 2: Load Project Overview

Read the project overview file:
```
worklog/README.md
```

This file typically contains:
- Project background and positioning
- Technical stack and architecture
- Core features and design principles
- Development progress and milestones
- Current status and next steps

### Step 3: Load Development Rules

Read the development rules file:
```
worklog/rules.md
```

This file typically contains:
- Coding standards and best practices
- Design principles (SOLID, DRY, KISS, etc.)
- Code review checklist
- Testing and security requirements
- Project-specific development guidelines

### Step 4: Present Context Summary

Provide a concise summary including:

#### Project Overview
- Project name and current phase
- MVP scope and validation goals
- Technology stack highlights
- Core features and design principles

#### Development Guidelines
- Key coding standards
- Important design principles
- Must-follow rules

#### Current Status
- Active features or components
- Development progress
- Known issues or blockers

#### Next Steps
- Pending tasks
- Recommended priorities
- Immediate action items

## Implementation Details

### File Reading Strategy

When loading project context:
- **Always read both files**: worklog/README.md and worklog/rules.md
- README.md provides project overview and status
- rules.md provides development guidelines and standards
- Both files are essential for maintaining code quality and consistency

### Handling Missing Information

If certain files are missing:
- Worklog directory not found: Check project structure, suggest reading other documentation
- README.md missing: Inform user about missing project overview
- rules.md missing: Inform user about missing development guidelines

## Example Usage

**User**: "开始今天的工作"

**AI Response**:
1. Check if worklog directory exists
2. Read worklog/README.md
3. Read worklog/rules.md
4. Present project context summary with guidelines

**Output Example**:
```
# 项目上下文加载完成

## 项目概况
- 项目: AI 虚拟教师系统
- 当前阶段: MVP 开发阶段
- 技术栈: React + TypeScript (前端), Python FastAPI (后端)
- 学科: 数学 - 一次函数单元

## 核心功能
- 极简版学习系统（三步学习循环）
- 知识图谱可视化（分层布局+递归依赖）
- 学生学习档案
- AI 讲解引擎

## 开发规范要点
- 遵循 SOLID 原则，单一职责，避免"上帝类"
- 使用类型注解（Python 3.9+ 必须使用）
- 所有用户输入必须验证（Pydantic validator）
- 密码使用 bcrypt 哈希存储
- SQL 查询必须参数化，防止注入
- 单元测试覆盖率要求 >80%

## 开发进度
- ✅ 前端基础架构搭建
- ✅ 后端 API 开发
- ✅ 知识图谱重构
- 🔄 教学图片生成方案优化

## 待办事项
- 完善学生答题记录和统计分析
- 添加知识点掌握度评估
- 优化 LLM 调用成本

准备好开始工作了!请问今天要做什么?
```

## Notes

- This skill always loads both README.md and rules.md
- worklog/README.md should be maintained to include all critical project information
- worklog/rules.md should be maintained to include all development guidelines
- Both files are essential for ensuring code quality and project consistency
