---
name: agent-evolver
description: |
  Self-evolving agent skill that makes the AI progressively smarter through experience accumulation. 
  This skill should be used when the user says "反思一下", "进化一下", "总结经验", "反思", "进化", 
  "evolve", "reflect", or asks to review and improve agent behavior based on past work. 
  It analyzes recent code changes, extracts reusable patterns and pitfalls, 
  and compiles them into a structured knowledge wiki for future sessions.
---

# Agent Evolver

## Overview

This skill implements a closed-loop self-evolution mechanism for the AI agent. It transforms raw work experiences into structured, searchable knowledge that accumulates over time — making every future session smarter.

**Core philosophy (from Karpathy's LLM Wiki):** Do NOT load all experiences into context. Only load the compact index, then drill into specific wiki pages on demand.

**Relationship with daily-work-summary:** `daily-work-summary` produces time-oriented work logs (raw material). `agent-evolver` consumes those logs + session context to produce knowledge-oriented wiki pages (compiled knowledge).

## Knowledge Architecture

All evolution data lives under `~/.claude/evolution/`:

```
~/.claude/evolution/
├── schema/
│   └── evolution-schema.md          # Wiki organization rules
├── wiki/                            # Compiled knowledge (LLM-owned)
│   ├── index.md                     # ★ The ONLY file loaded in full
│   ├── log.md                       # Timeline of evolution actions
│   ├── patterns/                    # Reusable patterns
│   ├── pitfalls/                    # Mistakes to avoid
│   └── heuristics/                  # Rules of thumb
└── raw/                             # Raw material (append-only)
    └── {project-name}/              # Per-project subdirectories
        └── YYYY-MM-DD.md
```

**Three layers:**
| Layer | Content | Owner | Mutability |
|-------|---------|-------|------------|
| Schema | Organization rules | User + LLM | Evolves with use |
| Wiki | Compiled knowledge pages | LLM | Fully LLM-owned |
| Raw | Source material (worklogs, session notes) | LLM | Append-only |

## Context Budget Strategy

**CRITICAL: Never load all wiki pages into context.**

```
Step 1: Load ONLY index.md (~200 lines, ~500 tokens)
Step 2: Scan index, identify 2-3 relevant pages for current task
Step 3: Load ONLY those specific pages (~500-1500 tokens total)
Step 4: Execute task with enriched context
```

Maximum experience context overhead: ~2000 tokens. This is sustainable even as the knowledge base grows.

## When to Use This Skill

Trigger this skill when the user says:
- "反思一下" / "反思"
- "进化一下" / "进化" / "evolve"
- "总结经验" / "总结一下经验"
- "经验库健康检查" / "清理经验库"
- "lint" / "heal" (in evolution context)

## Workflow

### Workflow A: Reflect & Evolve (Primary)

#### Step 1: Collect Recent Changes

Run the reflection script to gather recent git activity:

```bash
python3 ~/.claude/skills/agent-evolver/scripts/reflect.py --project-root <current-project-path>
```

This collects:
- Git commits and diffs since last reflection
- Files changed
- Worklog entries from `worklog/` (if daily-work-summary was used)

If the script fails or is unavailable, manually analyze recent git changes using standard tools.

#### Step 2: Execute Meta-Cognitive Reflection

Analyze the collected changes and answer the **Four Reflection Questions**. Read `references/reflection-protocol.md` for the detailed protocol.

The four questions:
1. **What difficulties were encountered?** → Identify capability gaps
2. **How were they resolved?** → Extract effective strategies
3. **Is this solution reusable?** → Assess generalizability
4. **How to do better next time?** → Generate improvement suggestions

#### Step 3: Write to Raw

Append the reflection results to `~/.claude/evolution/raw/{project-name}/{YYYY-MM-DD}.md`.

Format (see `references/raw-entry-format.md` for details):

```markdown
## Reflection Entry - {YYYY-MM-DD} - {Project}

### Difficulties
- ...

### Solutions
- ...

### Reusable Patterns (if any)
- ...

### Improvements for Next Time
- ...

### Source Changes
- Commits: ...
- Files: ...
```

#### Step 4: Compile into Wiki

Evaluate the reflection using the **Signal Detection** criteria (see `references/signal-detection.md`):

- **High signal** → Create or update wiki page(s) + update `index.md`
- **Low signal** → Leave in raw only, will be compiled during future Lint+Heal

When creating a wiki page:

1. Check if an existing wiki page covers this topic (search `index.md`)
2. If exists → **update** the page with new insights
3. If not → **create** a new page following the wiki page template
4. Always update `index.md` with the new/updated entry

Wiki page categories:
- `wiki/patterns/` — Reusable solutions (e.g., "fastapi-error-handling.md")
- `wiki/pitfalls/` — Mistakes to avoid (e.g., "sqlalchemy-n-plus-1.md")
- `wiki/heuristics/` — Rules of thumb (e.g., "python-naming.md")

#### Step 5: Update Log

Append an entry to `~/.claude/evolution/wiki/log.md`:

```markdown
## [{YYYY-MM-DD}] reflect | {project-name}
- Analyzed X commits, Y files changed
- Created: {wiki-page} (pattern/pitfall/heuristic)
- Updated: {wiki-page} with new insight
- Raw entries: {count}
```

#### Step 6: Report to User

Present a concise summary:
- What was analyzed
- What experiences were extracted
- What wiki pages were created/updated
- Any actionable improvements identified

### Workflow B: Lint & Heal (Maintenance)

#### Step 1: Diagnose (Lint)

Scan the evolution knowledge base for health issues:

1. **Uncompiled raw entries** — Check `raw/` for entries not yet reflected in wiki
2. **Contradictions** — Check if any wiki pages conflict with each other
3. **Orphan pages** — Wiki pages with no index entry
4. **Stale content** — Pages marked with old dates that may be outdated
5. **Duplicate patterns** — Similar patterns that should be merged

#### Step 2: Fix (Heal)

For each issue found:
1. **Uncompiled entries** → Evaluate signal strength, compile high-signal ones into wiki
2. **Contradictions** → Mark older entry as deprecated, note the resolution
3. **Orphan pages** → Add missing index.md entry
4. **Stale content** → Review and update or mark deprecated
5. **Duplicates** → Merge into a single comprehensive page

#### Step 3: Update Index and Log

After healing, ensure `index.md` is accurate and log all changes.

### Workflow C: Passive Knowledge Loading (Automatic)

When this skill is loaded for a task (not explicitly triggered), it should:

1. Read `~/.claude/evolution/wiki/index.md`
2. Identify relevant wiki pages for the current task based on:
   - Tech stack (Python, TSX, etc.)
   - Task type (error handling, state management, database, etc.)
   - Keywords in the user's request
3. Load only the 2-3 most relevant pages
4. Apply the knowledge silently — inform the user only if a pattern is directly applied

## Wiki Page Template

Each wiki page should follow this structure:

```markdown
# {Title}

**Category:** pattern / pitfall / heuristic
**Tech Stack:** Python / TSX / General
**Created:** YYYY-MM-DD
**Last Updated:** YYYY-MM-DD
**Source Projects:** project-a, project-b

## Problem / Context
What problem does this address?

## Solution / Pattern
The actual solution, pattern, or rule.

## Code Example (if applicable)
```language
// Minimal reproducible example
```

## When to Apply
Specific conditions under which this applies.

## Caveats
Edge cases, limitations, or conditions where this does NOT apply.

## Cross References
- Related: [[other-page]]
- Supersedes: [[old-page]] (if this replaces an older entry)
```

## Decision: Create New Skill vs Expand Existing

Before creating a new wiki page, answer:
1. Can an existing page be extended to cover this? → **Update existing page**
2. Is this a one-time issue? → **Raw entry only**
3. Does this have clear input/output boundaries? → **Candidate for new page**
4. Has a similar problem appeared before? → **Strong candidate for new page**

## Resources

### scripts/

**reflect.py**
Analyzes git history since the last reflection entry, producing a structured summary of recent changes. Run with `--project-root` pointing to the project directory.

### references/

**reflection-protocol.md**
Detailed meta-cognitive reflection protocol — the four questions framework with evaluation criteria and examples.

**signal-detection.md**
Criteria for distinguishing high-signal (should compile to wiki) vs low-signal (raw only) experiences.

**raw-entry-format.md**
Template and examples for raw reflection entries.

### No assets/ directory

This skill does not produce output files for users. It manages its own knowledge base under `~/.claude/evolution/`.
