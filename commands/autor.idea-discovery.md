---
name: autor.idea-discovery
description: "Workflow 1: Full idea discovery pipeline. Orchestrates research-lit → idea-creator → novelty-check → research-reviewer to go from a broad research direction to validated, pilot-tested ideas. Use when user says \"idea discovery pipeline\" or wants the complete idea exploration workflow."
argument-hint: [research-direction or path/to/spec.md]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, Agent, Skill, mcp__codex__codex, mcp__codex__codex-reply
---

# Workflow 1: Idea Discovery Pipeline

Orchestrate a complete idea discovery workflow for: **$ARGUMENTS**

## Overview

This skill chains four sub-skills into a single automated pipeline:

```
/research-lit → /idea-creator → /novelty-check → research-reviewer agent
  (survey)      (brainstorm)    (verify novel)    (critical feedback)
```

Each phase builds on the previous one's output. The final deliverable is a validated `IDEA_REPORT.md` with ranked ideas, pilot results, and a suggested execution plan.

## Constants

All constants (PILOT_MAX_HOURS, PILOT_TIMEOUT_HOURS, MAX_PILOT_IDEAS, MAX_TOTAL_GPU_HOURS, AUTO_PROCEED, REVIEWER_MODEL) are defined in the project's **CLAUDE.md**. Read them from there before proceeding.

> Override inline, e.g., `/autor.idea-discovery "topic" — pilot budget: 4h per idea, 20h total` or `/autor.idea-discovery "topic" — wait for my approval at each step`.

## Pipeline

### Phase 0: Argument Resolution

Before starting the pipeline, determine whether `$ARGUMENTS` is a **file path** or a **plain text direction**.

1. **Detect file path**: Check if `$ARGUMENTS` (after trimming quotes/whitespace) looks like a file path — i.e., ends with `.md`, `.txt`, `.pdf`, or contains `/` or `\`.
2. **If it's a file path**:
   - Read the file using the `Read` tool.
   - Extract the research direction, context, constraints, and any pre-specified ideas from the file content.
   - Use the file content as the **RESOLVED_DIRECTION** for all subsequent phases.
   - Preserve any inline overrides appended after the path (e.g., `tests/spec.md — pilot budget: 4h`): split on ` — ` and pass overrides through.
3. **If it's plain text**: Use `$ARGUMENTS` directly as the **RESOLVED_DIRECTION**.

> From this point forward, all references to `$ARGUMENTS` in the pipeline mean **RESOLVED_DIRECTION** (the file content or the original text).

### Phase 1: Literature Survey

Invoke `/research-lit` to map the research landscape:

```
/research-lit "$ARGUMENTS"
```

**What this does:**
- Search arXiv, Google Scholar, Semantic Scholar for recent papers
- Build a landscape map: sub-directions, approaches, open problems
- Identify structural gaps and recurring limitations
- Output a literature summary (saved to working notes)

**Checkpoint:** Present the landscape summary to the user. Ask:

```
Literature survey complete. Here's what I found:
- [key findings, gaps, open problems]

Does this match your understanding? Should I adjust the scope before generating ideas?
(If no response, I'll proceed with the top-ranked direction.)
```

- **User approves** (or no response + AUTO_PROCEED=true) → proceed to Phase 2 with best direction.
- **User requests changes** (e.g., "focus more on X", "ignore Y", "too broad") → refine the search with updated queries, re-run `/research-lit` with adjusted scope, and present again. Repeat until the user is satisfied.

### Phase 2: Idea Generation + Filtering + Pilots

Invoke `/idea-creator` with the landscape context:

```
/idea-creator "$ARGUMENTS"
```

**What this does:**
- Brainstorm 8-12 concrete ideas via REVIEWER_MODEL xhigh
- Filter by feasibility, compute cost, quick novelty search
- Deep validate top ideas (full novelty check + devil's advocate)
- Run parallel pilot experiments on available GPUs (top 2-3 ideas)
- Rank by empirical signal
- Output `IDEA_REPORT.md`

**Checkpoint:** Present `IDEA_REPORT.md` ranked ideas to the user. Ask:

```
Generated X ideas, filtered to Y, piloted Z. Top results:

1. [Idea 1] — Pilot: POSITIVE (+X%)
2. [Idea 2] — Pilot: WEAK POSITIVE (+Y%)
3. [Idea 3] — Pilot: NEGATIVE, eliminated

Which ideas should I validate further? Or should I regenerate with different constraints?
(If no response, I'll proceed with the top-ranked ideas.)
```

- **User picks ideas** (or no response + AUTO_PROCEED=true) → proceed to Phase 3 with top-ranked ideas.
- **User unhappy with all ideas** → collect feedback ("what's missing?", "what direction do you prefer?"), update the prompt with user's constraints, and re-run Phase 2 (idea generation). Repeat until the user selects at least 1 idea.
- **User wants to adjust scope** → go back to Phase 1 with refined direction.

### Phase 3: Deep Novelty Verification

For each top idea (positive pilot signal), run a thorough novelty check:

```
/novelty-check "[top idea 1 description]"
/novelty-check "[top idea 2 description]"
```

**What this does:**
- Multi-source literature search (arXiv, Scholar, Semantic Scholar)
- Cross-verify with REVIEWER_MODEL xhigh
- Check for concurrent work (last 3-6 months)
- Identify closest existing work and differentiation points

**Update `IDEA_REPORT.md`** with deep novelty results. Eliminate any idea that turns out to be already published.

### Phase 4: External Critical Review

For the surviving top idea(s), get brutal feedback:

Invoke the `research-reviewer` agent with the top idea context:

```
Use the research-reviewer agent for: "[top idea with hypothesis + pilot results]"
```

**What this does:**
- REVIEWER_MODEL xhigh acts as a senior reviewer (NeurIPS/ICML level)
- Scores the idea, identifies weaknesses, suggests minimum viable improvements
- Provides concrete feedback on experimental design

**Update `IDEA_REPORT.md`** with reviewer feedback and revised plan.

### Phase 5: Final Report

Finalize `IDEA_REPORT.md` with all accumulated information:

```markdown
# Idea Discovery Report

**Direction**: $ARGUMENTS
**Date**: [today]
**Pipeline**: research-lit → idea-creator → novelty-check → research-reviewer

## Executive Summary
[2-3 sentences: best idea, key evidence, recommended next step]

## Literature Landscape
[from Phase 1]

## Ranked Ideas
[from Phase 2, updated with Phase 3-4 results]

### Idea 1: [title] — RECOMMENDED
- Pilot: POSITIVE (+X%)
- Novelty: CONFIRMED (closest: [paper], differentiation: [what's different])
- Reviewer score: X/10
- Next step: implement full experiment → /autor.auto-review-loop

### Idea 2: [title] — BACKUP
...

## Eliminated Ideas
[ideas killed at each phase, with reasons]

## Next Steps
- [ ] Implement Idea 1
- [ ] /run-experiment to deploy full-scale experiments
- [ ] /autor.auto-review-loop to iterate until submission-ready
- [ ] Or invoke /autor.research-pipeline for the complete end-to-end flow
```

## Key Rules

- **Don't skip phases.** Each phase filters and validates — skipping leads to wasted effort later.
- **Checkpoint between phases.** Briefly summarize what was found before moving on.
- **Kill ideas early.** It's better to kill 10 bad ideas in Phase 3 than to implement one and fail.
- **Empirical signal > theoretical appeal.** An idea with a positive pilot outranks a "sounds great" idea without evidence.
- **Document everything.** Dead ends are just as valuable as successes for future reference.
- **Be honest with the reviewer.** Include negative results and failed pilots in the review prompt.

## Composing with Workflow 2

After this pipeline produces a validated top idea:

```
/autor.idea-discovery "direction"         ← you are here (Workflow 1)
implement                           ← write code for the top idea
/run-experiment                     ← deploy full-scale experiments
/autor.auto-review-loop "top idea"        ← Workflow 2: iterate until submission-ready

Or use /autor.research-pipeline for the full end-to-end flow.
```
