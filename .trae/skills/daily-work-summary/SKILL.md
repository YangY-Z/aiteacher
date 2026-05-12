---
name: daily-work-summary
description: Generate daily work summaries to help future AI instances quickly understand previous work without scanning the entire codebase. Use this skill when the user asks for a work summary, daily summary, or wants to document today's work. Automatically analyzes git commits, file changes, and generates categorized markdown files in a date-based directory structure.
---

# Daily Work Summary

## Overview

This skill automates the generation of daily work summaries, creating structured documentation that enables future AI instances to quickly understand previous work context. It analyzes git commits, file changes, and generates categorized markdown files organized by date and content type.

## When to Use This Skill

Use this skill when:
- The user asks to summarize today's work ("帮我总结一下今天的工作")
- The user wants to document their daily progress
- The user needs to create a daily report or work log
- The user says something like "生成工作总结" or "记录今天的工作"

## Workflow

### Step 1: Collect Work Information

Run the `scripts/collect_work_info.py` script to automatically gather today's work data:

```bash
python scripts/collect_work_info.py --date <YYYY-MM-DD> --output <output.json>
```

The script collects:
- Git commits from today
- File changes (added, modified, deleted)
- Code statistics (lines added/removed)
- Commit messages and authors

If the `--date` parameter is omitted, it defaults to today's date.

**Example output structure:**
```json
{
  "date": "2026-04-06",
  "git_commits": [...],
  "file_changes": {...},
  "statistics": {...}
}
```

### Step 2: Analyze and Categorize

After collecting work information, analyze the changes and categorize them into appropriate types:

**Common categories:**
- `功能开发.md` - New feature development
- `问题修复.md` - Bug fixes and issue resolution
- `重构优化.md` - Code refactoring and performance improvements
- `文档更新.md` - Documentation updates
- `技术决策.md` - Important technical decisions and rationale
- `待办事项.md` - Tasks for tomorrow or future work

Use the git commit messages, file paths, and code changes to determine appropriate categories. A single day's work may span multiple categories.

### Step 3: Generate Summary Files

Create summary files in the project's worklog directory with the following structure:

```
<project-root>/
  └── worklog/
      └── <YYYY-MM-DD>/
          ├── README.md (index file with overview)
          ├── 功能开发.md (if applicable)
          ├── 问题修复.md (if applicable)
          ├── 重构优化.md (if applicable)
          └── ... (other category files as needed)
```

**File naming convention:**
- Use Chinese category names for better readability
- One file per content category
- Only create files for categories with actual content

### Step 4: Create Index File

Generate a `README.md` index file in the date directory that provides:
- Quick overview of the day's work
- List of all category files with brief descriptions
- Key statistics (files changed, commits, etc.)
- Important highlights or achievements

Use the template from `assets/index_template.md` as a starting point.

## Summary Content Structure

Each category file should follow this structure to maximize future AI understanding:

### Header Section
```markdown
# [Category Name] - YYYY-MM-DD

**涉及文件:** List of relevant files with paths
**影响范围:** Which parts of the system are affected
**重要程度:** High/Medium/Low
```

### Main Content Section
```markdown
## 工作概述
Brief description of what was accomplished in this category.

## 详细内容

### [Task 1]
**修改文件:**
- `path/to/file1.tsx` - Description of changes
- `path/to/file2.py` - Description of changes

**实现细节:**
Detailed explanation of how it was implemented, including:
- Key algorithms or logic
- Important design decisions
- Dependencies introduced

**测试验证:**
How the changes were tested, if applicable.

### [Task 2]
...

## 技术要点
- Key technical insights or patterns used
- Important configurations or dependencies
- Potential risks or edge cases to be aware of

## 待解决问题
Issues that were identified but not yet resolved.

## 相关链接
Links to relevant documents, issues, or resources.
```

For detailed examples and best practices, refer to `references/summary_structure.md`.

## Best Practices

### For Code Changes
- Include file paths with brief descriptions
- Highlight key functions or components that were modified
- Note any breaking changes or API modifications
- Mention any new dependencies introduced

### For Technical Decisions
- Explain the problem that needed to be solved
- Document the alternatives considered
- Justify the chosen solution
- Note any trade-offs or limitations

### For Future Reference
- Use clear, descriptive language that doesn't require context
- Include code snippets or configuration examples when relevant
- Reference specific line numbers or commit hashes when useful
- Avoid assuming knowledge of the current conversation context

## Example Usage

**User:** "帮我总结一下今天的工作"

**Assistant should:**
1. Run `scripts/collect_work_info.py` to gather today's work data
2. Analyze the collected information
3. Categorize changes into appropriate types
4. Generate summary files in `<project-root>/<today's-date>/` directory
5. Create an index README.md file
6. Inform the user where the summaries are located

**User:** "生成昨天的工作总结"

**Assistant should:**
1. Run `scripts/collect_work_info.py --date <yesterday's-date>`
2. Follow the same process as above

## Resources

### scripts/

**collect_work_info.py**
Automated script that collects git repository information, including commits, file changes, and code statistics for a specified date.

**generate_summary.py**
Helper script that processes collected work information and generates categorized markdown files based on the changes detected.

### references/

**summary_structure.md**
Detailed examples and guidelines for writing effective summaries, including sample outputs and formatting best practices.

### assets/

**index_template.md**
Template for the README.md index file that provides a quick overview of the day's work and links to detailed category files.
