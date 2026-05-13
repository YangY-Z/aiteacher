"""
HTML Lesson Engine — 基于"HTML是AI Agent的通用接口"理念

核心思想（The Unreasonable Effectiveness of HTML）：
  将教学内容输出为语义化 HTML，使得：
  1. 学生看到的 HTML 就是 AI Agent 能解析的界面
  2. LLM 直接理解和操作 HTML，无需自定义 API
  3. HTML 的层级结构天然适合知识表示
"""

import logging
from typing import Any, Optional

from app.services.course_service import course_service
from app.repositories.course_repository import (
    knowledge_point_repository,
    knowledge_point_dependency_repository,
)

logger = logging.getLogger(__name__)

# ── HTML 构建器（轻量，无依赖） ──────────────────────────────────

def _h(tag: str, content: str = "", **attrs: str) -> str:
    """Build a single HTML element."""
    attr_str = " ".join(f'{k}="{v}"' for k, v in attrs.items() if v)
    attr_str = f" {attr_str}" if attr_str else ""
    return f"<{tag}{attr_str}>{content}</{tag}>"


def _wrap(tag: str, *children: str, **attrs: str) -> str:
    """Wrap children in a tag."""
    return _h(tag, "\n".join(children), **attrs)


def _safe(text: str) -> str:
    """Basic HTML escaping."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# ── CSS 样式（暗色主题，黑板风格） ──────────────────────────────

AGENT_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans SC', sans-serif;
  background: #0f0f1a;
  color: #e0e0e0;
  line-height: 1.7;
  padding: 2rem;
  max-width: 960px;
  margin: 0 auto;
}
a { color: #7ec8e3; text-decoration: none; }
a:hover { color: #b0e0f0; text-decoration: underline; }
h1 { font-size: 1.8rem; color: #f0f0ff; border-bottom: 2px solid #2a2a4a; padding-bottom: 0.5rem; margin-bottom: 1.5rem; }
h2 { font-size: 1.3rem; color: #c8d8ff; margin-top: 1.5rem; margin-bottom: 0.75rem; }
h3 { font-size: 1.1rem; color: #a8c0ff; margin-top: 1rem; margin-bottom: 0.5rem; }
.kp-card {
  background: #1a1a2e;
  border: 1px solid #2a2a4a;
  border-radius: 8px;
  padding: 1rem 1.25rem;
  margin-bottom: 0.75rem;
  transition: border-color 0.2s;
}
.kp-card:hover { border-color: #4a6aff; }
.kp-card.completed { border-left: 4px solid #4caf50; }
.kp-card.active { border-left: 4px solid #ff9800; }
.kp-card.pending { border-left: 4px solid #555; }
.kp-level { font-size: 0.75rem; color: #888; margin-bottom: 0.25rem; }
.kp-name { font-size: 1rem; color: #e0e0ff; font-weight: 500; }
.kp-type {
  display: inline-block;
  font-size: 0.7rem;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  margin-left: 0.5rem;
}
.kp-type.concept { background: #2a3a6a; color: #8ab4ff; }
.kp-type.formula { background: #3a2a4a; color: #c8a0ff; }
.kp-type.skill { background: #2a4a3a; color: #80c8a0; }
.kp-prereqs { font-size: 0.8rem; color: #999; margin-top: 0.4rem; }
.badge {
  display: inline-block;
  font-size: 0.7rem;
  padding: 0.1rem 0.4rem;
  border-radius: 3px;
  margin: 0.1rem;
}
.badge.prereq { background: #3a3a2a; color: #d0b080; }
.phase-list { list-style: none; padding: 0; }
.phase-item {
  background: #141428;
  border: 1px solid #2a2a3a;
  border-radius: 6px;
  padding: 0.75rem 1rem;
  margin-bottom: 0.5rem;
}
.phase-item.active { border-color: #4a6aff; }
.phase-title { font-weight: 500; color: #c0d0ff; }
.phase-desc { font-size: 0.85rem; color: #aaa; margin-top: 0.25rem; }
.tool-badge {
  display: inline-block;
  font-size: 0.75rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  margin: 0.15rem;
  background: #2a2a40;
  color: #a0b0d0;
}
footer {
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid #2a2a3a;
  font-size: 0.8rem;
  color: #666;
  text-align: center;
}
"""


# ── 课程 HTML 生成器 ────────────────────────────────────────────

def build_curriculum_html(
    course_id: str,
    completed_kp_ids: Optional[list[str]] = None,
    active_kp_id: Optional[str] = None,
) -> str:
    """
    生成整个课程的 HTML 视图。
    这是 AI Agent 也能"浏览"的课程地图。

    Args:
        course_id: 课程 ID
        completed_kp_ids: 已学完的知识点 ID 列表
        active_kp_id: 当前正在学习的知识点 ID

    Returns:
        完整的 HTML 字符串
    """
    completed_kp_ids = completed_kp_ids or []
    course = course_service.get_course(course_id)
    kps = course_service.get_course_knowledge_points(course_id)

    # 按层级分组
    levels: dict[int, list[Any]] = {}
    for kp in kps:
        levels.setdefault(kp.level, []).append(kp)

    sections = []
    sections.append(
        _h("h1", _safe(f"📚 {course.name}"))
    )
    sections.append(
        _h("p", _safe(course.description or ""), style="color:#888;margin-bottom:1.5rem;")
    )
    sections.append(
        _h(
            "p",
            f"知识点总数: {len(kps)} | "
            f"已完成: {len(completed_kp_ids)} | "
            f"进度: {len(completed_kp_ids)/max(len(kps),1)*100:.0f}%",
            style="font-size:0.9rem;color:#aaa;margin-bottom:1.5rem;",
        )
    )

    for level in sorted(levels.keys()):
        level_desc = course.level_descriptions.get(level, f"第 {level+1} 层")
        items = []
        for kp in levels[level]:
            is_completed = kp.id in completed_kp_ids
            is_active = kp.id == active_kp_id
            status_class = "completed" if is_completed else ("active" if is_active else "pending")
            status_label = "✅ 已掌握" if is_completed else ("▶ 学习中" if is_active else "⏳ 未开始")

            # 获取依赖
            deps = knowledge_point_dependency_repository.get_dependencies(kp.id)
            dep_names = []
            for d in deps:
                dep_kp = knowledge_point_repository.get_by_id(d)
                if dep_kp:
                    dep_names.append(dep_kp.name)

            type_badge = _h(
                "span", _safe(kp.type.value),
                class_=f"kp-type {kp.type.value.lower()}",
            )

            prereq_html = ""
            if dep_names:
                prereq_html = _h(
                    "div", "前置知识: " + " ".join(
                        _h("span", _safe(n), class_="badge prereq")
                        for n in dep_names
                    ),
                    class_="kp-prereqs",
                )

            card = _wrap(
                "div",
                _h("div", _safe(status_label), class_="kp-level"),
                _h("div", _safe(kp.name) + type_badge, class_="kp-name"),
                _h("div", _safe(kp.description or ""), style="font-size:0.85rem;color:#aaa;margin-top:0.3rem;"),
                prereq_html,
                class_=f"kp-card {status_class}",
                data_kp_id=kp.id,
                data_level=str(level),
            )
            items.append(card)

        sections.append(
            _wrap("div", _h("h2", f"📖 {_safe(level_desc)}"), *items, class_="level-section")
        )

    # 教学模板说明
    sections.append(
        _wrap(
            "div",
            _h("h2", "📋 教学模式"),
            _h("p", "每个知识点根据类型自动匹配教学模式：", style="color:#888;"),
            _wrap(
                "ul",
                _h("li", "概念建构 (concept_construction) — 适用于概念类知识点"),
                _h("li", "程序技能 (procedural_skill) — 适用于技能/操作类知识点"),
                _h("li", "视觉理解 (visual_understanding) — 适用于图形/视觉类知识点"),
                _h("li", "对比分析 (contrast_analysis) — 适用于易混淆知识点"),
                _h("li", "问题探究 (problem_inquiry) — 适用于探究类知识点"),
                _h("li", "错误诊断 (error_diagnosis) — 适用于纠错类知识点"),
                style="list-style:disc;padding-left:1.5rem;color:#bbb;",
            ),
            style="margin-top:2rem;padding:1rem;background:#141428;border-radius:8px;",
        )
    )

    # Agent 元数据（供 AI Agent 解析用）
    agent_meta = _wrap(
        "div",
        _h("h2", "🤖 Agent 元数据"),
        _h(
            "pre",
            f"""{{
  "course_id": "{course.id}",
  "total_kps": {len(kps)},
  "completed_kps": {len(completed_kp_ids)},
  "levels": {list(levels.keys())},
  "teaching_modes": ["concept_construction", "procedural_skill", "visual_understanding", "contrast_analysis", "problem_inquiry", "error_diagnosis"],
  "interface_version": "1.0"
}}""",
            style="font-size:0.8rem;color:#8a8;background:#0a0a15;padding:0.75rem;border-radius:4px;overflow-x:auto;",
        ),
        style="margin-top:2rem;",
    )
    sections.append(agent_meta)

    body_content = "\n".join(sections)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="agent-interface" content="true">
<title>{_safe(course.name)} — AI 虚拟教师课程地图</title>
<style>{AGENT_CSS}</style>
</head>
<body>
{body_content}
<footer>
  AI 虚拟教师系统 · 课程地图 · 本页面 HTML 结构可供 AI Agent 直接解析
</footer>
</body>
</html>"""
    return html


def build_lesson_html(
    kp_id: str,
    student_name: str = "",
    phase: int = 1,
    total_phases: int = 4,
    whiteboard_data: Optional[dict[str, Any]] = None,
) -> str:
    """
    生成单个知识点的教学内容 HTML 视图。
    这是每次教学时生成的可交互 HTML 文档。

    Args:
        kp_id: 知识点 ID
        student_name: 学生姓名
        phase: 当前教学阶段 (1-based)
        total_phases: 总阶段数
        whiteboard_data: 当前白板数据 {title, key_points, formulas, examples, notes, image}

    Returns:
        教学 HTML 片段（可嵌入白板）
    """
    kp = knowledge_point_repository.get_by_id(kp_id)
    if not kp:
        return _h("p", f"知识点 {kp_id} 未找到", style="color:red;")

    deps = knowledge_point_dependency_repository.get_dependencies(kp_id)
    dep_names = []
    for d in deps:
        dep_kp = knowledge_point_repository.get_by_id(d)
        if dep_kp:
            dep_names.append(dep_kp.name)

    whiteboard = whiteboard_data or {}

    lesson_css = """
.lesson-content { padding: 0.5rem 0; }
.lesson-header { margin-bottom: 1rem; }
.lesson-header .kp-title {
  font-size: 1.3rem; font-weight: 600; color: #e0e0ff;
  border-left: 3px solid #4a6aff; padding-left: 0.75rem;
}
.lesson-header .kp-type-badge {
  display: inline-block; font-size: 0.75rem; padding: 0.15rem 0.5rem;
  border-radius: 4px; margin-left: 0.5rem;
  background: #2a3a6a; color: #8ab4ff;
}
.lesson-header .kp-description { font-size: 0.85rem; color: #aaa; margin-top: 0.4rem; padding-left: 1rem; }
.lesson-header .kp-prereqs { font-size: 0.8rem; color: #777; margin-top: 0.3rem; padding-left: 1rem; }
.phase-progress {
  display: flex; gap: 0.4rem; margin: 0.75rem 0 1rem;
  padding: 0.5rem; background: #141428; border-radius: 6px;
}
.phase-dot {
  flex: 1; height: 6px; border-radius: 3px;
  background: #333; transition: all 0.3s;
}
.phase-dot.done { background: #4caf50; }
.phase-dot.current { background: #4a6aff; box-shadow: 0 0 6px #4a6aff; }
.whiteboard-section {
  background: #141428; border-radius: 8px; padding: 1rem; margin-bottom: 0.75rem;
  border: 1px solid #2a2a3a;
}
.whiteboard-section h3 {
  font-size: 0.9rem; color: #8ab4ff; margin-bottom: 0.5rem;
  display: flex; align-items: center; gap: 0.4rem;
}
.whiteboard-section .section-icon { font-size: 1rem; }
.whiteboard-section ul { list-style: none; padding: 0; }
.whiteboard-section li {
  padding: 0.3rem 0; padding-left: 1rem;
  border-left: 2px solid #2a2a4a; margin-bottom: 0.2rem;
  font-size: 0.9rem; color: #d0d0e0;
}
.whiteboard-section li:last-child { margin-bottom: 0; }
.formula-block {
  background: #0a0a18; border-radius: 4px; padding: 0.6rem 1rem;
  margin-bottom: 0.4rem; font-family: 'KaTeX_Main', serif;
  font-size: 1.05rem; color: #c8d0ff; text-align: center;
}
.example-block {
  background: #1a1a2e; border: 1px solid #2a3a3a;
  border-radius: 6px; padding: 0.6rem 1rem; margin-bottom: 0.4rem;
  font-size: 0.9rem; color: #d0d8c0;
}
.example-block::before { content: "📌 "; }
.note-block {
  background: #2a2a1a; border-left: 3px solid #d0a050;
  border-radius: 0 4px 4px 0; padding: 0.5rem 0.75rem; margin-bottom: 0.3rem;
  font-size: 0.85rem; color: #d0c8a0;
}
.note-block::before { content: "⚠️ "; }
"""

    # 构建知识点头部
    header_parts = [_h("div", _safe(kp.name), class_="kp-title")]
    header_parts.append(
        _h("span", _safe(kp.type.value), class_="kp-type-badge")
    )
    if kp.description:
        header_parts.append(
            _h("div", _safe(kp.description), class_="kp-description")
        )
    if dep_names:
        header_parts.append(
            _h(
                "div",
                f"前置: {' → '.join(_safe(n) for n in dep_names)}",
                class_="kp-prereqs",
            )
        )
    header = _h("div", "\n".join(header_parts), class_="lesson-header")

    # 阶段进度条
    phase_dots = []
    for i in range(1, total_phases + 1):
        cls = "done" if i < phase else ("current" if i == phase else "")
        phase_dots.append(_h("div", "", class_=f"phase-dot {cls}"))
    progress = _h("div", "\n".join(phase_dots), class_="phase-progress")
    progress += _h(
        "div",
        f"教学阶段 {phase}/{total_phases}",
        style="text-align:center;font-size:0.8rem;color:#888;margin-bottom:0.5rem;",
    )

    # 白板内容
    wb_sections = []
    if whiteboard.get("title"):
        wb_sections.append(
            _h(
                "h3",
                _h("span", "📖", class_="section-icon") + _safe(whiteboard["title"]),
            )
        )

    if whiteboard.get("key_points"):
        items = "\n".join(
            _h("li", _safe(p)) for p in whiteboard["key_points"]
        )
        wb_sections.append(
            _wrap(
                "div",
                _h("h3", _h("span", "🎯", class_="section-icon") + "要点"),
                _wrap("ul", items),
                class_="whiteboard-section",
            )
        )

    if whiteboard.get("formulas"):
        items = "\n".join(
            _h("div", _safe(f), class_="formula-block") for f in whiteboard["formulas"]
        )
        wb_sections.append(
            _wrap(
                "div",
                _h("h3", _h("span", "📐", class_="section-icon") + "公式"),
                items,
                class_="whiteboard-section",
            )
        )

    if whiteboard.get("examples"):
        items = "\n".join(
            _h("div", _safe(e), class_="example-block") for e in whiteboard["examples"]
        )
        wb_sections.append(
            _wrap(
                "div",
                _h("h3", _h("span", "💡", class_="section-icon") + "示例"),
                items,
                class_="whiteboard-section",
            )
        )

    if whiteboard.get("notes"):
        items = "\n".join(
            _h("div", _safe(n), class_="note-block") for n in whiteboard["notes"]
        )
        wb_sections.append(
            _wrap(
                "div",
                _h("h3", _h("span", "⚠️", class_="section-icon") + "注意事项"),
                items,
                class_="whiteboard-section",
            )
        )

    wb_html = "\n".join(wb_sections)

    html = f"""<div class="lesson-content">
<style>{lesson_css}</style>
{header}
{progress}
{wb_html}
</div>"""
    return html


def build_agent_instructions_html() -> str:
    """
    生成 AI Agent 交互指引页。
    说明本系统的 HTML 接口约定，供 Agent 解析。
    """
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="agent-interface" content="true">
<meta name="agent-version" content="1.0">
<title>AI 虚拟教师 — Agent 接口文档</title>
<style>{AGENT_CSS}</style>
</head>
<body>
<h1>🤖 AI Agent 接口说明</h1>

<h2>HTML as Interface</h2>
<p>本系统基于 <strong>"The Unreasonable Effectiveness of HTML"</strong> 理念，
所有教学界面均输出为结构化 HTML，AI Agent 可直接解析。</p>

<h2>可用端点</h2>
<div class="kp-card">
  <div class="kp-name">GET /api/v1/curriculum/html?course_id=&lt;id&gt;</div>
  <div style="font-size:0.85rem;color:#aaa;">
    返回完整课程地图 HTML。包含所有知识点层级、依赖关系、完成状态。
    添加 <code>?completed=id1,id2</code> 标记已学知识点。
  </div>
</div>
<div class="kp-card">
  <div class="kp-name">GET /api/v1/teaching-v2/session/&lt;id&gt;/html</div>
  <div style="font-size:0.85rem;color:#aaa;">
    返回当前教学会话的 HTML 视图。包含知识点详情和白板内容。
  </div>
</div>
<div class="kp-card">
  <div class="kp-name">POST /api/v1/teaching-v2/session/&lt;id&gt;/teach-v2</div>
  <div style="font-size:0.85rem;color:#aaa;">
    SSE 流式教学接口。LLM 返回 JSONL 格式教学内容。
    输出中的 <code>html</code> 字段可直接渲染为教学白板。
  </div>
</div>

<h2>HTML 语义约定</h2>
<ul>
  <li><code>.kp-card</code> — 知识点卡片，包含名称、类型、状态</li>
  <li><code>.kp-card.completed</code> — 已完成的知识点</li>
  <li><code>.kp-card.active</code> — 正在学习的知识点</li>
  <li><code>.kp-type.concept|.formula|.skill</code> — 知识点类型</li>
  <li><code>.whiteboard-section</code> — 白板内容区块</li>
  <li><code>data-kp-id</code> — 知识点唯一标识</li>
  <li><code>data-level</code> — 知识点层级</li>
</ul>

<h2>Agent 操作模式</h2>
<ol>
  <li><strong>浏览课程地图</strong> — GET /curriculum/html</li>
  <li><strong>分析学生进度</strong> — 解析 HTML 中的 <code>.kp-card</code> 状态</li>
  <li><strong>生成教学内容</strong> — LLM 返回包含 <code>html</code> 字段的 JSONL</li>
  <li><strong>评估学生理解</strong> — 从教学 HTML 的 <code>.example-block</code> 和 <code>.note-block</code> 提取反馈</li>
</ol>

<footer>
  AI 虚拟教师 · Agent Interface v1.0
</footer>
</body>
</html>"""
