---
name: autor.research-pipeline
description: "Full research pipeline: Workflow 1 (idea discovery) → implementation → Workflow 2 (auto review loop). Goes from a broad research direction to validated, reviewed research. Use when user says \"full pipeline\", \"end-to-end research\", or wants the complete autonomous research lifecycle. Does NOT include paper writing (Workflow 3) — invoke /autor.paper-writing separately after this completes."
argument-hint: [research-direction]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, Agent, Skill, mcp__codex__codex, mcp__codex__codex-reply
---

# Full Research Pipeline: Idea → Experiments → Reviewed Research

End-to-end autonomous research workflow for: **$ARGUMENTS**

## Constants

All constants (PILOT_MAX_HOURS, MAX_ROUNDS, POSITIVE_THRESHOLD, REVIEWER_MODEL) are defined in the project's **CLAUDE.md**. Read them from there before proceeding.

## Overview

This skill chains two major workflows plus the implementation bridge between them:

```
/autor.idea-discovery → implement → /run-experiment → /autor.auto-review-loop → reviewed research
├── Workflow 1 ──┤            ├────────── Workflow 2 ──────────────┤
```

> **Note:** This pipeline ends at reviewed research. To generate a submission-ready PDF, run `/autor.paper-writing` separately after this completes.

## Pipeline

### Stage 1: Idea Discovery (Workflow 1)

Invoke the idea discovery pipeline:

```
/autor.idea-discovery "$ARGUMENTS"
```

This internally runs: `/research-lit` → `/idea-creator` → `/novelty-check` → `research-reviewer` agent

**Output:** `IDEA_REPORT.md` with ranked, validated, pilot-tested ideas.

**Gate 1 — Human Checkpoint:**

After `IDEA_REPORT.md` is generated, **pause and present the top ideas to the user**:

```
Idea Discovery complete. Top ideas:

1. [Idea 1 title] — Pilot: POSITIVE (+X%), Novelty: CONFIRMED
2. [Idea 2 title] — Pilot: WEAK POSITIVE (+Y%), Novelty: CONFIRMED
3. [Idea 3 title] — Pilot: NEGATIVE, eliminated

Recommended: Idea 1. Shall I proceed with implementation?
```

**Wait for user confirmation before continuing.** The user may:
- **Approve an idea** → proceed to Stage 2.
- **Pick a different idea** → proceed with their choice.
- **Request changes** (e.g., "combine Idea 1 and 3", "focus more on X") → update the idea prompt with user feedback, re-run `/autor.idea-discovery` with refined constraints, and present again.
- **Reject all ideas** → collect feedback on what's missing, re-run Stage 1 with adjusted research direction. Repeat until the user commits to an idea.
- **Stop here** → save current state to `IDEA_REPORT.md` for future reference.

> **This gate ALWAYS waits for explicit user confirmation** — unlike `/autor.idea-discovery` checkpoints which can auto-proceed. The rest of the pipeline is expensive (GPU time + multiple review rounds). Do NOT proceed until the user says which idea to pursue.

### Stage 2: Implementation

Once the user confirms which idea to pursue:

1. **Read the idea details** from `IDEA_REPORT.md` (hypothesis, experimental design, pilot code)

2. **Implement the full experiment**:
   - Extend pilot code to full scale (multi-seed, full dataset, proper baselines)
   - Add proper evaluation metrics and logging (wandb if configured)
   - Write clean, reproducible experiment scripts
   - Follow existing codebase conventions

3. **Code review**: Before deploying, do a self-review:
   - Are all hyperparameters configurable via argparse?
   - Is the random seed fixed and controllable?
   - Are results saved to JSON/CSV for later analysis?
   - Is there proper logging for debugging?

### Stage 3: Deploy Experiments (Workflow 2 — Part 1)

Deploy the full-scale experiments:

```
/run-experiment [experiment command]
```

**What this does:**
- Check GPU availability on configured servers
- Sync code to remote server
- Launch experiments in screen sessions with proper CUDA_VISIBLE_DEVICES
- Verify experiments started successfully

**Monitor progress:**

```
/monitor-experiment [server]
```

Wait for experiments to complete. Collect results.

### Stage 4: Auto Review Loop (Workflow 2 — Part 2)

Once initial results are in, start the autonomous improvement loop:

```
/autor.auto-review-loop "$ARGUMENTS — [chosen idea title]"
```

**What this does (up to MAX_ROUNDS):**
1. REVIEWER_MODEL xhigh reviews the work (score, weaknesses, minimum fixes)
2. Claude Code implements fixes (code changes, new experiments, reframing)
3. Deploy fixes, collect new results
4. Re-review → repeat until POSITIVE_THRESHOLD met or MAX_ROUNDS reached

**Output:** `AUTO_REVIEW.md` with full review history and final assessment.

### Stage 5: Final Summary

After the auto-review loop completes, write a final status report:

```markdown
# Research Pipeline Report

**Direction**: $ARGUMENTS
**Chosen Idea**: [title]
**Date**: [start] → [end]
**Pipeline**: idea-discovery → implement → run-experiment → auto-review-loop

## Journey Summary
- Ideas generated: X → filtered to Y → piloted Z → chose 1
- Implementation: [brief description of what was built]
- Experiments: [number of GPU experiments, total compute time]
- Review rounds: N/MAX_ROUNDS, final score: X/10

## Final Status
- [ ] Ready for submission / [ ] Needs manual follow-up

## Remaining TODOs (if any)
- [items flagged by reviewer that weren't addressed]

## Files Changed
- [list of key files created/modified]
```

## Key Rules

- **Human checkpoint after Stage 1 is MANDATORY.** Do not auto-proceed to implementation without user confirmation.
- **Stages 2-4 can run autonomously** once the user confirms the idea. This is the "sleep and wake up to results" part.
- **If Stage 4 ends at MAX_ROUNDS without positive assessment**, stop and report remaining issues. Do not loop forever.
- **Budget awareness**: Track total GPU-hours across the pipeline. Flag if approaching user-defined limits.
- **Documentation**: Every stage updates its own output file. The full history should be self-contained.
- **Fail gracefully**: If any stage fails (no good ideas, experiments crash, review loop stuck), report clearly and suggest alternatives rather than forcing forward.

## Typical Timeline

| Stage | Duration | Can sleep? |
|-------|----------|------------|
| 1. Idea Discovery | 30-60 min | No (interactive checkpoints) |
| 2. Implementation | 15-60 min | No (may need user input) |
| 3. Deploy | 5 min + experiment time | Yes |
| 4. Auto Review | 1-4 hours (depends on experiments) | Yes |

**Sweet spot**: Run Stage 1-2 in the evening, launch Stage 3-4 before bed, wake up to a reviewed paper.
