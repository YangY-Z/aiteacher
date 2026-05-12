# Meta-Cognitive Reflection Protocol

## Overview

The reflection protocol is the core mechanism that converts raw experience into structured knowledge. After each reflection trigger, the agent answers four questions in sequence to extract reusable insights.

## The Four Questions

### Q1: What difficulties were encountered?

**Goal:** Identify capability gaps and friction points.

Examine recent work and identify:
- Tasks that took longer than expected
- Errors or bugs that required significant debugging
- Unclear requirements or ambiguous specifications
- Repeated trial-and-error before finding a solution
- External dependencies or tools that caused issues
- Knowledge gaps (e.g., unfamiliar API, unclear documentation)

**Output format:**
```markdown
### Difficulties
1. [Difficulty description] — Spent {time} on {task}, caused by {root cause}
2. ...
```

### Q2: How were they resolved?

**Goal:** Extract effective strategies that worked.

For each difficulty identified in Q1, document:
- The actual solution that resolved it
- What search/query led to the solution (if any)
- Key insight that unlocked the problem
- Any tools or resources that helped

**Output format:**
```markdown
### Solutions
1. [Difficulty #1] → Resolved by [strategy]. Key insight: [insight]
2. ...
```

### Q3: Is this solution reusable?

**Goal:** Assess generalizability beyond the current context.

For each solution, evaluate:
- **Scope:** Does this apply only to this project, or across projects?
- **Frequency:** How likely is this problem to recur? (Common / Occasional / Rare)
- **Specificity:** Is the solution tightly coupled to current code, or abstract enough to reuse?
- **Boundary conditions:** Under what conditions does this solution NOT apply?

**Classification:**
| Category | Criteria | Example |
|----------|----------|---------|
| Reusable Pattern | Cross-project, recurring, well-bounded | FastAPI unified error handling |
| Project Pattern | Single-project, recurring | This project's auth flow |
| One-time Insight | Rare, tightly coupled | A specific data migration fix |

**Output format:**
```markdown
### Reusable Patterns
1. [Pattern name] — Scope: {cross-project/single-project}, Frequency: {common/occasional/rare}
   - Applies when: [conditions]
   - Does NOT apply when: [conditions]
2. ...
```

### Q4: How to do better next time?

**Goal:** Generate forward-looking improvement suggestions.

Based on the full reflection, identify:
- **Prevention:** How to avoid this difficulty entirely next time
- **Detection:** How to notice this problem earlier
- **Process improvement:** What workflow changes would help
- **Tooling:** What tools or automation could prevent this

**Output format:**
```markdown
### Improvements for Next Time
1. [Improvement suggestion] — Would save {estimated time/effort}
2. ...
```

## Reflection Quality Criteria

A good reflection entry should:
- Be **specific** enough that a future agent can act on it
- Include **concrete examples** (file paths, code snippets, error messages)
- Separate **signal from noise** (not everything is worth remembering)
- Be **honest about failures** (failed approaches are valuable too)

## Anti-Patterns to Avoid

- Vague statements: "Fixed a bug" (What bug? How? Why did it occur?)
- Over-generalization: "Always use X" (Without boundary conditions)
- Under-documentation: Only recording success, not failed attempts
- Analysis paralysis: Spending more time reflecting than the original task
