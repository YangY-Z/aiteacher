# Summary Structure Guidelines

This document provides detailed guidelines for writing effective daily work summaries.

## Content Organization Principles

### 1. Context Independence
Summaries should be understandable without prior context. Future AI instances (potentially days or weeks later) should grasp what was done without referring to the original conversation.

**Good:**
```markdown
Added user authentication feature with JWT tokens. Implemented login, logout, 
and token refresh endpoints. Used bcrypt for password hashing.
```

**Bad:**
```markdown
Implemented the feature discussed earlier. Fixed the issue mentioned above.
```

### 2. File Path Precision
Always include complete file paths from the project root to enable quick navigation.

**Good:**
```markdown
**修改文件:**
- `ai-teacher-frontend/src/pages/LearningCenter.tsx` - Added knowledge map visualization
- `ai-teacher-frontend/src/pages/LearningCenter.css` - New styles for graph nodes
```

**Bad:**
```markdown
Modified LearningCenter files and CSS.
```

### 3. Technical Depth
Include enough technical detail to understand the "how" and "why," not just the "what."

**Include:**
- Key algorithms or logic patterns
- Design decisions and their rationale
- Dependencies or libraries used
- Configuration changes
- API contracts or data structures

## Category File Template

```markdown
# [Category Name] - YYYY-MM-DD

**涉及文件:** [number] 个文件
**提交次数:** [number] 次
**重要程度:** High/Medium/Low

## 工作概述

[1-3 sentence overview of what was accomplished in this category]

## 详细内容

### [Feature/Task Name]

**修改文件:**
- `path/to/file1.tsx` - Brief description of changes
- `path/to/file2.py` - Brief description of changes

**实现细节:**

[Detailed explanation of implementation approach]

- **核心逻辑:** [Key algorithm or business logic]
- **技术选型:** [Libraries, frameworks, or tools used]
- **设计方案:** [Design patterns or architecture decisions]

**代码示例:**

```typescript
// Key code snippet that demonstrates the core logic
const handleNodeClick = (kp: KnowledgePoint) => {
  if (kp.status === 'locked') {
    alert('请先完成前置知识点');
  } else {
    navigate(`/learn?kp_id=${kp.id}`);
  }
};
```

**测试验证:**

[How the changes were tested]

- Manual testing: [What was tested]
- Unit tests: [What scenarios are covered]
- Edge cases: [What edge cases were considered]

### [Another Feature/Task]

[Repeat the structure above]

## 技术要点

### 关键技术点

1. **[Technical Point 1]**
   - Why this approach was chosen
   - What alternatives were considered
   - Any trade-offs or limitations

2. **[Technical Point 2]**
   - Details about the implementation
   - Dependencies or prerequisites
   - Potential risks or gotchas

### 性能考虑

- [Performance optimizations made]
- [Bottlenecks identified]
- [Scalability considerations]

### 安全考虑

- [Security measures implemented]
- [Potential vulnerabilities addressed]
- [Best practices followed]

## 待解决问题

### 高优先级

- [ ] [Issue description and potential impact]
- [ ] [Issue description and potential impact]

### 中优先级

- [ ] [Issue description]
- [ ] [Issue description]

### 低优先级

- [ ] [Issue description]

## 相关链接

- [Link to related documentation]
- [Link to related issue or PR]
- [Link to external reference]
```

## Index File Template

```markdown
# 工作总结 - YYYY-MM-DD

## 📊 今日概况

- **提交次数:** X 次
- **文件变更:** X 个文件
- **代码统计:** +XXX / -XXX 行
- **工作类别:** X 个

## 📁 详细文档

### [Category 1](category1.md)
- 提交: X 次
- 文件: X 个

### [Category 2](category2.md)
- 提交: X 次
- 文件: X 个

## 🎯 工作重点

[List 3-5 major achievements or progress made today]

1. Implemented knowledge map visualization with interactive nodes
2. Refactored module list to use compact card layout
3. Added popup layer for knowledge point details
4. Optimized graph layout with Bézier curves
5. Improved overall user experience with smooth animations

## 💡 技术亮点

[Record important technical discoveries, solutions, or optimizations]

- **SVG Path Optimization:** Used quadratic Bézier curves for cleaner graph connections
- **State Management:** Implemented local state with React hooks for hover effects
- **Performance:** Lazy loading of knowledge points reduces initial render time by 40%
- **Accessibility:** Added keyboard navigation support for graph nodes

## ⚠️ 注意事项

[Record issues or risks that need follow-up attention]

- **API Integration:** Backend endpoint for knowledge map data needs optimization
- **Mobile Responsiveness:** Graph visualization needs touch gesture support
- **Data Model:** Consider adding prerequisite relationship field to knowledge points
- **Testing:** E2E tests needed for interactive graph features

## 📝 明日计划

[List tasks for tomorrow]

- [ ] Add zoom and pan functionality to knowledge map
- [ ] Implement search/filter for knowledge points
- [ ] Add progress tracking animations
- [ ] Write unit tests for graph component
- [ ] Update API documentation

---

**生成时间:** YYYY-MM-DD HH:MM:SS
```

## Best Practices by Category

### 功能开发.md (Feature Development)

Focus on:
- User-facing functionality and UX improvements
- Implementation approach and technical decisions
- Dependencies and integration points
- Testing strategies

### 问题修复.md (Bug Fixes)

Focus on:
- Problem description and symptoms
- Root cause analysis
- Solution approach and implementation
- Prevention measures

### 重构优化.md (Refactoring)

Focus on:
- What was refactored and why
- Before/after comparison
- Performance improvements (quantified if possible)
- Breaking changes or migration notes

### 文档更新.md (Documentation)

Focus on:
- What documentation was added or updated
- Why the update was needed
- Target audience
- Key sections or highlights

### 技术决策.md (Technical Decisions)

Focus on:
- The problem being solved
- Alternatives considered
- Decision rationale
- Trade-offs and limitations
- Implementation roadmap

## Content Quality Checklist

Before finalizing any summary file, verify:

- [ ] File paths are complete and accurate
- [ ] Technical terms are explained or contextualized
- [ ] No references to "above" or "below" that won't make sense later
- [ ] Code snippets include necessary context
- [ ] Important decisions are justified
- [ ] Risks and gotchas are highlighted
- [ ] Links to external resources are provided where helpful
- [ ] The content would be clear to someone reading it weeks later

## Example Scenarios

### Scenario 1: Multiple Small Features

If multiple small features were implemented in one day, group them logically:

```markdown
## 详细内容

### 前端优化

**修改文件:**
- `frontend/src/App.tsx` - Added loading states
- `frontend/src/components/Header.tsx` - Improved navigation

[Details...]

### 后端接口增强

**修改文件:**
- `backend/api/users.py` - Added pagination
- `backend/services/auth.py` - Improved token validation

[Details...]
```

### Scenario 2: Large Refactoring

For significant refactoring, focus on the migration path:

```markdown
## 详细内容

### 状态管理重构

**背景:**
原有的状态管理方案在大型应用中性能不佳，需要迁移到更高效的方案。

**修改文件:**
[List all affected files...]

**迁移方案:**
1. 第一阶段：保留旧实现，添加新实现
2. 第二阶段：逐步迁移组件到新实现
3. 第三阶段：移除旧实现代码

**向后兼容性:**
- 保留了旧 API 的兼容层
- 添加了迁移指南文档
- 提供了自动化迁移脚本

**影响范围:**
- 所有使用状态的组件需要更新导入路径
- 单元测试需要相应调整
- 文档需要更新示例代码
```

### Scenario 3: Bug Investigation

For bug fixes, document the investigation process:

```markdown
## 详细内容

### 内存泄漏问题修复

**问题描述:**
在长时间使用知识地图时，浏览器内存持续增长，最终导致页面卡顿。

**问题排查:**
1. 使用 Chrome DevTools Memory profiler 分析内存快照
2. 发现 SVG 节点未正确释放
3. 定位到事件监听器未在组件卸载时移除

**修复方案:**
- 添加 useEffect 清理函数移除事件监听器
- 使用 React.memo 优化节点渲染
- 实现 IntersectionObserver 替代全量渲染

**验证方法:**
- Chrome DevTools 内存分析确认泄漏已修复
- 长时间使用测试（4小时+）内存稳定
- 性能监控显示内存占用降低 60%
```
