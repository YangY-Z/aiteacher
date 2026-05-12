# Signal Detection Criteria

## Overview

Not every experience deserves to be compiled into a wiki page. This document defines criteria for distinguishing high-signal experiences (compile to wiki) from low-signal experiences (raw only).

## High-Signal Indicators (Compile to Wiki)

An experience should be compiled into a wiki page when it meets **at least 2** of the following:

### 1. Repetition
- The same type of problem has appeared **2 or more times** across sessions
- Manual search for the solution was needed more than once
- A colleague or the user asked about the same thing again

### 2. Well-Bounded Solution
- The solution has a clear **input/output boundary**
- It can be described in a step-by-step procedure
- It applies to a recognizable category of problems

### 3. Significant Time Investment
- The problem took more than **30 minutes** to resolve
- The solution required external research or experimentation
- A simpler approach could have saved considerable time

### 4. Cross-Project Applicability
- The solution is not specific to one project's unique business logic
- It involves general programming patterns, framework usage, or tool configuration
- It would help in any project using the same tech stack

### 5. Preventive Value
- Knowing this in advance would have **prevented** the difficulty entirely
- It reveals a common misconception or anti-pattern
- It's something a developer "should know" but often doesn't

## Low-Signal Indicators (Raw Only)

An experience should stay as raw entry only when:

### 1. One-Time Occurrence
- Highly specific to a unique business requirement
- Tightly coupled to a specific codebase's idiosyncrasies
- Unlikely to recur in any form

### 2. Trivial Solution
- The fix was obvious once identified (typo, missing import, etc.)
- Took less than 5 minutes to resolve
- No lesson to be learned

### 3. Already Covered
- An existing wiki page already describes this pattern
- The new experience adds no meaningful new information
- (In this case, still update the existing page if it adds detail, but don't create a new one)

### 4. Too Broad
- The "lesson" is too generic to be actionable (e.g., "write clean code")
- Cannot be distilled into a specific pattern or rule
- Would result in a wiki page that's useless for future reference

## Decision Flowchart

```
Experience identified
       │
       ▼
  Is it already covered by an existing wiki page?
       │
   YES → Update existing page (if new info) or skip
   NO  →
       │
       ▼
  Does it meet ≥ 2 high-signal criteria?
       │
   YES → Create new wiki page
   NO  →
       │
       ▼
  Is it potentially useful for future reference?
       │
   YES → Raw entry only (may be compiled later during Lint+Heal)
   NO  → Skip entirely
```

## Special Cases

### Stale wiki pages
If a new raw entry **contradicts** an existing wiki page, always compile the update — mark the old content as superseded.

### Emerging patterns
If you see 2-3 raw entries on similar topics but none individually meet the threshold, consider **merging them** into a single wiki page during Lint+Heal.

### Tech stack changes
When a new technology or framework is adopted, be more permissive — compile even lower-signal entries early on, as the knowledge base for that tech is still thin.
