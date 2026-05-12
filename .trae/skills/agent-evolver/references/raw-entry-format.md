# Raw Entry Format

## Overview

Raw entries are append-only records stored in `~/.claude/evolution/raw/{project-name}/`. They serve as the source material that gets compiled into wiki pages during reflection or Lint+Heal cycles.

## File Naming

```
~/.claude/evolution/raw/{project-name}/YYYY-MM-DD.md
```

- One file per project per day (multiple reflections on the same day append to the same file)
- Use the project's directory name as `{project-name}` (e.g., `aiteacher-2`, `my-webapp`)
- If the same file already exists, append a new entry section (do not overwrite)

## Entry Template

```markdown
## Reflection Entry - {YYYY-MM-DD HH:MM} - {Project Name}

### Difficulties
1. [{Short title}] — {Brief description of the difficulty, what went wrong, root cause}
2. ...

### Solutions
1. [{Difficulty #1}] → {How it was resolved, key insight, what search led to the fix}
2. ...

### Reusable Patterns
1. **{Pattern name}**
   - Scope: {cross-project | single-project}
   - Frequency: {common | occasional | rare}
   - Applies when: {conditions}
   - Does NOT apply when: {conditions}
   - Summary: {1-2 sentence description of the reusable solution}
2. ...

### Improvements for Next Time
1. [{Improvement}] — Would save {estimated impact}
2. ...

### Source Changes
- **Commits:** {count} commits since last reflection
- **Key commits:**
  - `{hash}` {commit message}
  - ...
- **Files changed:** {count} files
- **Key files:**
  - `{path}` — {what changed}
  - ...

### Signal Assessment
- Patterns identified: {count}
- High-signal candidates: {count} (list names)
- Low-signal entries: {count}
- Compilation action: {created: [...], updated: [...], raw-only: [...]}
```

## Examples

### Example 1: Reusable Pattern

```markdown
## Reflection Entry - 2026-04-28 15:30 - aiteacher-2

### Difficulties
1. [N+1 Query in Student List] — Loading student list with enrollments caused 200+ queries.
   Root cause: SQLAlchemy default lazy loading triggered a separate query per student.

### Solutions
1. [N+1 Query] → Added `selectinload(Student.enrollments)` to the query.
   Key insight: Always check query count when returning list endpoints with relationships.

### Reusable Patterns
1. **SQLAlchemy selectinload for list endpoints**
   - Scope: cross-project
   - Frequency: common
   - Applies when: Any list endpoint that includes relationship data
   - Does NOT apply when: Single entity detail endpoint (lazy loading is fine)
   - Summary: Use `selectinload()` / `joinedload()` for any relationship accessed in loops.

### Improvements for Next Time
1. Add query count assertion in tests for list endpoints — Would catch N+1 in CI

### Source Changes
- **Commits:** 3 commits since last reflection
- **Key commits:**
  - `a1b2c3d` fix: add selectinload to student list query
- **Files changed:** 2 files
- **Key files:**
  - `ai-teacher-backend/app/repositories/student.py` — Added selectinload
  - `ai-teacher-backend/tests/test_student_api.py` — Added query count test

### Signal Assessment
- Patterns identified: 1
- High-signal candidates: 1 (SQLAlchemy selectinload)
- Low-signal entries: 0
- Compilation action: created: [wiki/pitfalls/sqlalchemy-n-plus-1.md]
```

### Example 2: Low-Signal One-Time Issue

```markdown
## Reflection Entry - 2026-04-29 10:00 - aiteacher-2

### Difficulties
1. [Image Upload 413 Error] — Uploading a 5MB image returned HTTP 413.
   Root cause: Nginx default `client_max_body_size` is 1MB.

### Solutions
1. [413 Error] → Increased `client_max_body_size` to 10MB in nginx.conf.
   Quick fix, just a config value.

### Reusable Patterns
(none — this is a one-time config fix)

### Improvements for Next Time
1. Set reasonable upload size limits from project start

### Source Changes
- **Commits:** 1 commit
- **Key commits:**
  - `e4f5g6h` fix: increase nginx client_max_body_size
- **Files changed:** 1 file

### Signal Assessment
- Patterns identified: 0
- High-signal candidates: 0
- Low-signal entries: 1
- Compilation action: raw-only
```

## Guidelines

- **Be specific:** Include file paths, error messages, code snippets where helpful
- **Be honest:** Failed approaches are valuable — record what didn't work too
- **Be concise:** Each difficulty/solution should be 1-3 sentences
- **Don't over-record:** If nothing noteworthy happened, skip the reflection entirely
