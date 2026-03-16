---
name: autor.idea-discovery
description: "Workflow 1: Full idea discovery pipeline. Orchestrates research-lit → idea-creator → novelty-check → research-reviewer to go from a broad research direction to validated, pilot-tested ideas. Use when user says \"idea discovery pipeline\" or wants the complete idea exploration workflow."
argument-hint: [research-direction or path/to/spec.md]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, Agent, Skill, mcp__codex__codex, mcp__codex__codex-reply
---

# Workflow 1: Idea Discovery Pipeline

Orchestrate a complete idea discovery workflow for: **$ARGUMENTS**

## Output Directory

All intermediate and final results are saved to a dedicated output folder:

- **Default**: If the input is a file path like `path/to/spec.md`, the output folder is `path/to/autor.idea_discovery/`
- **Override**: Append `— output: path/to/output/` to the arguments
- **Plain text input**: Output folder is `./autor.idea_discovery/` in the current working directory

The output folder is **self-contained** — it includes the input spec, live status, and all generated results:
- `task_spec.md` — Copy of the input spec (preserved for reproducibility)
- `task_status.md` — Live pipeline status, decisions, and idea rankings with links to IDEA_REPORT sections
- `LITERATURE_SURVEY.md` — Literature landscape summary (Phase 1)
- `IDEA_REPORT.md` — Final ranked idea report (Phase 5)
- `REVIEW_*.md` — External reviewer feedback (Phase 4)
- Any pilot experiment logs (Phase 2, if applicable)

## Overview

This skill chains four sub-skills into a single automated pipeline:

```
/research-lit → /idea-creator → /novelty-check → research-reviewer agent
  (survey)      (brainstorm)    (verify novel)    (critical feedback)
```

Each phase builds on the previous one's output. The final deliverable is a validated `OUTPUT_DIR/IDEA_REPORT.md` with ranked ideas, pilot results, and a suggested execution plan. All files are saved to OUTPUT_DIR (see [Output Directory](#output-directory)).

## Constants

All constants (PILOT_MAX_HOURS, PILOT_TIMEOUT_HOURS, MAX_PILOT_IDEAS, MAX_TOTAL_GPU_HOURS, AUTO_PROCEED, REVIEWER_MODEL) are defined in the project's **CLAUDE.md**. Read them from there before proceeding.

> Override inline, e.g., `/autor.idea-discovery "topic" — pilot budget: 4h per idea, 20h total` or `/autor.idea-discovery "topic" — wait for my approval at each step`.

## Pipeline

### Phase 0: Argument & Output Resolution

Before starting the pipeline, determine whether `$ARGUMENTS` is a **file path** or a **plain text direction**, and resolve the output directory.

#### 0a. Parse Arguments

1. **Split on ` — `** to separate the main argument from inline overrides.
2. **Check for `output:` override** in overrides section. If present, use as OUTPUT_DIR.
3. **Detect file path**: Check if the main argument (after trimming quotes/whitespace) looks like a file path — i.e., ends with `.md`, `.txt`, `.pdf`, or contains `/` or `\`.
4. **If it's a file path**:
   - Read the file using the `Read` tool.
   - Extract the research direction, context, constraints, and any pre-specified ideas from the file content.
   - Use the file content as the **RESOLVED_DIRECTION** for all subsequent phases.
5. **If it's plain text**: Use the main argument directly as the **RESOLVED_DIRECTION**.

#### 0b. Resolve Output Directory

Determine OUTPUT_DIR using this priority:

1. **Explicit override**: `— output: path/to/output/` → use as-is
2. **File path input**: If input is `path/to/spec.md`, set OUTPUT_DIR = `path/to/autor.idea_discovery/`
3. **Plain text input**: OUTPUT_DIR = `./autor.idea_discovery/`

Create OUTPUT_DIR if it doesn't exist (`mkdir -p`). All subsequent phases save their outputs here.

#### 0c. Save Task Spec

Copy the input into the output folder for self-containment:

- **File path input**: Copy the input file to `OUTPUT_DIR/task_spec.md`
- **Plain text input**: Write the resolved direction text to `OUTPUT_DIR/task_spec.md`

This ensures the output folder is **portable and reproducible** — anyone can understand the full context from just this folder.

#### 0d. Initialize Task Status

Create `OUTPUT_DIR/task_status.md` with the initial pipeline state. This file is **updated at the end of each phase** to track progress, decisions, and results. It serves as the live dashboard for the pipeline run.

```markdown
# Task Status: Idea Discovery Pipeline

**Direction**: [1-line summary of RESOLVED_DIRECTION]
**Input**: `task_spec.md`
**Date**: [today]
**Status**: IN PROGRESS

---

## Phase Status

| Phase | Status | Output |
|-------|--------|--------|
| Phase 0: Argument & Output Resolution | COMPLETED | Resolved input, created output folder |
| Phase 1: Literature Survey | PENDING | |
| Phase 2: Idea Generation + Filtering | PENDING | |
| Phase 3: Deep Novelty Verification | PENDING | |
| Phase 4: External Critical Review | PENDING | |
| Phase 5: Final Report | PENDING | |
```

> **Status tracking rule**: After completing each phase, update `task_status.md`:
> 1. Set the phase status to `COMPLETED` with a brief output summary
> 2. Set the next phase to `IN PROGRESS`
> 3. Add any key decisions to the "Key Decisions" section
> 4. If the pipeline is interrupted or fails, the status file shows exactly where it stopped

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
- Output a literature summary → save as `OUTPUT_DIR/LITERATURE_SURVEY.md`

**Checkpoint:** Present the landscape summary to the user. Ask:

```
Literature survey complete. Here's what I found:
- [key findings, gaps, open problems]

Does this match your understanding? Should I adjust the scope before generating ideas?
(If no response, I'll proceed with the top-ranked direction.)
```

- **User approves** (or no response + AUTO_PROCEED=true) → proceed to Phase 2 with best direction.
- **User requests changes** (e.g., "focus more on X", "ignore Y", "too broad") → refine the search with updated queries, re-run `/research-lit` with adjusted scope, and present again. Repeat until the user is satisfied.

**Update `OUTPUT_DIR/task_status.md`**: Set Phase 1 → COMPLETED with paper count and gap count.

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
- Output → save as `OUTPUT_DIR/IDEA_REPORT.md`

**Checkpoint:** Present ranked ideas to the user. Ask:

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

**Update `OUTPUT_DIR/task_status.md`**: Set Phase 2 → COMPLETED with idea counts (generated/filtered/piloted).

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

**Update `OUTPUT_DIR/IDEA_REPORT.md`** with deep novelty results. Eliminate any idea that turns out to be already published.

**Update `OUTPUT_DIR/task_status.md`**: Set Phase 3 → COMPLETED with novelty scores for each checked idea.

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
- Saves review document → `OUTPUT_DIR/REVIEW_[topic]_[date].md`

**Update `OUTPUT_DIR/IDEA_REPORT.md`** with reviewer feedback and revised plan.

**Update `OUTPUT_DIR/task_status.md`**: Set Phase 4 → COMPLETED with reviewer score and key decisions (packaging choice, framing).

### Phase 5: Final Report

Finalize `OUTPUT_DIR/IDEA_REPORT.md` with all accumulated information:

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

#### Finalize `OUTPUT_DIR/task_status.md`

After writing `IDEA_REPORT.md`, finalize the task status file with:

1. **All phases set to COMPLETED** with output summaries
2. **Overall status set to COMPLETED**
3. **Key Decisions** section with packaging choice, framing advice, critical gates
4. **Idea Rankings table with links** — each idea name is a relative markdown link to its section in IDEA_REPORT.md

Use this anchor format for linking ideas: `[Idea Title](IDEA_REPORT.md#idea-N-slug)` where `slug` is the heading text lowercased, spaces replaced with `-`, special characters removed. For example:

```markdown
## Idea Rankings (Final)

| Rank | Idea | Novelty | Risk | Status |
|------|------|:-------:|------|--------|
| 1 | [Idea Title](IDEA_REPORT.md#idea-1-idea-title--recommended-lead-contribution) | 7/10 | MEDIUM | RECOMMENDED |
```

5. **Next Steps** checklist matching the IDEA_REPORT
6. **Files in This Folder** manifest listing all output files with descriptions

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
