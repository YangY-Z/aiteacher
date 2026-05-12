#!/usr/bin/env python3
"""
Generate categorized summary files from collected work information.
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


def categorize_file(filepath: str) -> str:
    """Determine the category of a file based on its path and extension."""
    
    # Test files
    if 'test' in filepath.lower() or filepath.endswith('.test.ts') or filepath.endswith('.test.tsx'):
        return "测试"
    
    # Frontend files
    if any(ext in filepath for ext in ['.tsx', '.jsx', '.css', '.scss', '.vue']):
        if 'component' in filepath.lower():
            return "前端组件"
        elif 'page' in filepath.lower():
            return "前端页面"
        elif 'api' in filepath.lower():
            return "API接口"
        else:
            return "前端开发"
    
    # Backend files
    if any(ext in filepath for ext in ['.py', '.go', '.java', '.rb']):
        if 'api' in filepath.lower() or 'route' in filepath.lower():
            return "API开发"
        elif 'service' in filepath.lower():
            return "后端服务"
        elif 'model' in filepath.lower() or 'schema' in filepath.lower():
            return "数据模型"
        else:
            return "后端开发"
    
    # Documentation
    if filepath.endswith('.md') or filepath.endswith('.txt'):
        return "文档更新"
    
    # Configuration
    if any(ext in filepath for ext in ['.json', '.yaml', '.yml', '.toml', '.env']):
        return "配置文件"
    
    # Default
    return "其他"


def categorize_commit(message: str) -> str:
    """Determine the category of a commit based on its message."""
    
    message_lower = message.lower()
    
    # Bug fixes
    if any(word in message_lower for word in ['fix', '修复', 'bug', '解决']):
        return "问题修复"
    
    # Features
    if any(word in message_lower for word in ['feat', 'feature', '添加', '新增', '实现']):
        return "功能开发"
    
    # Refactoring
    if any(word in message_lower for word in ['refactor', '重构', '优化', 'improve']):
        return "重构优化"
    
    # Documentation
    if any(word in message_lower for word in ['doc', '文档', 'readme']):
        return "文档更新"
    
    # Tests
    if any(word in message_lower for word in ['test', '测试']):
        return "测试"
    
    # Default
    return "其他开发"


def analyze_work_data(work_info: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Analyze work data and categorize it."""
    
    categories = {}
    
    # Analyze commits
    for commit in work_info.get('git_commits', []):
        category = categorize_commit(commit['message'])
        
        if category not in categories:
            categories[category] = {
                'commits': [],
                'files': set(),
                'details': []
            }
        
        categories[category]['commits'].append(commit)
    
    # Analyze file changes
    file_changes = work_info.get('file_changes', {})
    
    for filepath in file_changes.get('added', []):
        category = categorize_file(filepath)
        if category not in categories:
            categories[category] = {'commits': [], 'files': set(), 'details': []}
        categories[category]['files'].add(f"新增: {filepath}")
    
    for filepath in file_changes.get('modified', []):
        category = categorize_file(filepath)
        if category not in categories:
            categories[category] = {'commits': [], 'files': set(), 'details': []}
        categories[category]['files'].add(f"修改: {filepath}")
    
    for filepath in file_changes.get('deleted', []):
        category = categorize_file(filepath)
        if category not in categories:
            categories[category] = {'commits': [], 'files': set(), 'details': []}
        categories[category]['files'].add(f"删除: {filepath}")
    
    return categories


def generate_category_file(
    category: str,
    data: Dict[str, Any],
    date: str,
    output_dir: Path
) -> Path:
    """Generate a markdown file for a specific category."""
    
    # Map category names to Chinese filenames
    filename_map = {
        "功能开发": "功能开发.md",
        "问题修复": "问题修复.md",
        "重构优化": "重构优化.md",
        "文档更新": "文档更新.md",
        "测试": "测试.md",
        "API开发": "API开发.md",
        "前端开发": "前端开发.md",
        "后端开发": "后端开发.md",
        "技术决策": "技术决策.md",
        "其他开发": "其他开发.md",
        "其他": "其他.md"
    }
    
    filename = filename_map.get(category, f"{category}.md")
    filepath = output_dir / filename
    
    # Generate content
    content = f"""# {category} - {date}

**涉及文件:** {len(data['files'])} 个文件
**提交次数:** {len(data['commits'])} 次
**重要程度:** {"高" if len(data['commits']) > 3 or len(data['files']) > 5 else "中" if len(data['commits']) > 1 else "低"}

## 工作概述

"""
    
    # Add commit summaries
    if data['commits']:
        content += "### 提交记录\n\n"
        for commit in data['commits']:
            content += f"- **{commit['message']}** ({commit['hash'][:7]})\n"
        content += "\n"
    
    # Add file changes
    if data['files']:
        content += "### 修改文件\n\n"
        for filepath in sorted(data['files']):
            content += f"- `{filepath}`\n"
        content += "\n"
    
    # Add placeholder sections for AI to fill
    content += """## 详细内容

*[此部分需要人工或AI补充详细内容]*

### 主要变更

- [ ] 补充关键实现细节
- [ ] 记录重要技术决策
- [ ] 说明潜在影响范围

## 技术要点

*[记录关键技术点、设计模式、依赖关系等]*

## 待解决问题

*[记录发现但未解决的问题]*

## 相关链接

-[相关文档或资源的链接]
"""
    
    # Write file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath


def generate_index_file(
    date: str,
    categories: Dict[str, Dict[str, Any]],
    work_info: Dict[str, Any],
    output_dir: Path
) -> Path:
    """Generate the index README.md file."""
    
    filepath = output_dir / "README.md"
    
    # Get statistics
    stats = work_info.get('statistics', {})
    
    content = f"""# 工作总结 - {date}

## 📊 今日概况

- **提交次数:** {len(work_info.get('git_commits', []))} 次
- **文件变更:** {stats.get('files_changed', 0)} 个文件
- **代码统计:** +{stats.get('lines_added', 0)} / -{stats.get('lines_removed', 0)} 行
- **工作类别:** {len(categories)} 个

## 📁 详细文档

"""
    
    # List category files
    for category, data in sorted(categories.items()):
        commit_count = len(data['commits'])
        file_count = len(data['files'])
        
        content += f"### [{category}]({category}.md)\n"
        content += f"- 提交: {commit_count} 次\n"
        content += f"- 文件: {file_count} 个\n\n"
    
    content += f"""## 🎯 工作重点

*[列出今天的主要工作成果和重要进展]*

1. 
2. 
3. 

## 💡 技术亮点

*[记录今天的重要技术发现、解决方案或优化点]*

- 
- 

## ⚠️ 注意事项

*[记录需要后续关注的问题或风险]*

- 
- 

## 📝 明日计划

*[列出明天需要完成的任务]*

- [ ] 
- [ ] 
- [ ] 

---

**生成时间:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
    
    # Write file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath


def generate_summaries(work_info_path: str, output_dir: str = None) -> None:
    """Generate categorized summary files from work information."""
    
    # Load work information
    with open(work_info_path, 'r', encoding='utf-8') as f:
        work_info = json.load(f)
    
    date = work_info['date']
    
    # Determine output directory
    if output_dir is None:
        # Default to project root / worklog / date
        output_dir = Path.cwd() / "worklog" / date
    else:
        output_dir = Path(output_dir)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📝 Generating summary files for {date}...")
    
    # Analyze and categorize
    categories = analyze_work_data(work_info)
    
    print(f"\n📊 Found {len(categories)} categories:")
    for category, data in categories.items():
        print(f"  - {category}: {len(data['commits'])} commits, {len(data['files'])} files")
    
    # Generate category files
    generated_files = []
    for category, data in categories.items():
        filepath = generate_category_file(category, data, date, output_dir)
        generated_files.append(filepath)
        print(f"  ✅ Generated: {filepath.name}")
    
    # Generate index file
    index_file = generate_index_file(date, categories, work_info, output_dir)
    print(f"  ✅ Generated: {index_file.name}")
    
    print(f"\n✅ All summary files generated in: {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate categorized summary files from collected work information"
    )
    parser.add_argument(
        "work_info",
        type=str,
        help="Path to work information JSON file"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output directory (default: <project-root>/worklog/<date>)",
        default=None
    )
    
    args = parser.parse_args()
    
    generate_summaries(args.work_info, args.output)


if __name__ == "__main__":
    main()
