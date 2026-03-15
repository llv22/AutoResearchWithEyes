# Implementation Plan

Based on [DISCUSSION.md](./DISCUSSION.md). Two phases: Phase 1 (end-to-end automation), Phase 2 (human involvement + optional integrations).

---

## Phase 1: End-to-End Automation

### Task 1: Create Directory Structure

Create the new `skills/`, `commands/`, `agents/`, `templates/` layout.

- [x] 1.1 Create `commands/` directory
- [x] 1.2 Create `agents/` directory
- [x] 1.3 Create `templates/iclr2026/`, `templates/neurips2026/`, `templates/icml2026/` directories
- [x] 1.4 Create `.claude-plugin/plugin.json` manifest

### Task 2: Centralize Constants in CLAUDE.md

Extract all hardcoded values from skills into a single constants section in CLAUDE.md.

- [x] 2.1 Create project CLAUDE.md with constants section:
  ```
  REVIEWER_MODEL = gpt-5.4
  PILOT_MAX_HOURS = 2
  PILOT_TIMEOUT_HOURS = 3
  MAX_PILOT_IDEAS = 3
  MAX_TOTAL_GPU_HOURS = 8
  MAX_ROUNDS = 4
  POSITIVE_THRESHOLD = >= 6/10
  AUTO_PROCEED = true
  MAX_IMPROVEMENT_ROUNDS = 2
  COMPILER = latexmk
  ENGINE = pdflatex
  MAX_COMPILE_ATTEMPTS = 3
  VENUE = iclr2026
  TEMPLATE_DIR = templates/
  ```
- [x] 2.2 Remove hardcoded constants from each skill file (replace with "read from CLAUDE.md")

### Task 3: Refactor 10 Skills (Building Blocks)

Refactor each retained skill: remove Feishu references, remove hardcoded constants, reference CLAUDE.md, and add arXiv TeX source reading where applicable.

- [x] 3.1 **research-lit** — Remove Zotero/Obsidian MCP references (Phase 2), add arXiv TeX source fetching (`/src/{id}`), remove Feishu
- [x] 3.2 **idea-creator** — Remove Feishu, reference CLAUDE.md for PILOT_* constants and REVIEWER_MODEL
- [x] 3.3 **novelty-check** — Reference CLAUDE.md for REVIEWER_MODEL, no other changes
- [x] 3.4 **run-experiment** — Remove Feishu notifications, reference CLAUDE.md
- [x] 3.5 **monitor-experiment** — Remove Feishu notifications, reference CLAUDE.md
- [x] 3.6 **analyze-results** — Minimal changes (no constants to extract)
- [x] 3.7 **paper-plan** — Remove hardcoded venue logic, reference CLAUDE.md for VENUE + TEMPLATE_DIR + REVIEWER_MODEL
- [x] 3.8 **paper-figure** — Reference CLAUDE.md for REVIEWER_MODEL, keep figure constants (DPI=300, FORMAT=pdf)
- [x] 3.9 **paper-write** — Remove hardcoded ICLR/NeurIPS/ICML templates, use `TEMPLATE_DIR/VENUE/` resolution, reference CLAUDE.md
- [x] 3.10 **paper-compile** — Reference CLAUDE.md for COMPILER, ENGINE, MAX_COMPILE_ATTEMPTS; derive MAX_PAGES from VENUE

### Task 4: Create 2 Agents

Extract review/improvement logic into dedicated agent personas.

- [x] 4.1 **agents/research-reviewer.md** — Extract from `research-review` skill. Senior ML reviewer persona, uses Codex MCP (REVIEWER_MODEL xhigh). Multi-round critical feedback on ideas, papers, results.
- [x] 4.2 **agents/paper-improver.md** — Extract from `auto-paper-improvement-loop` skill. 2-round auto-improvement: review → fix → recompile. State persistence via PAPER_IMPROVEMENT_STATE.json.

### Task 5: Create 4 Commands (Workflow Orchestrators)

Convert workflow skills into commands that compose skills + agents.

- [x] 5.1 **commands/autor.idea-discovery.md** — Orchestrates: `/research-lit` → `/idea-creator` → `/novelty-check` → `research-reviewer` agent. 3 checkpoints. Output: IDEA_REPORT.md
- [x] 5.2 **commands/autor.auto-review-loop.md** — Max 4 rounds: review (Codex MCP) → implement fixes → re-review. State persistence via REVIEW_STATE.json + AUTO_REVIEW.md. 24-hour recovery window.
- [x] 5.3 **commands/autor.paper-writing.md** — Orchestrates: `/paper-plan` → `/paper-figure` → `/paper-write` → `/paper-compile` → `paper-improver` agent. 5 checkpoints. Template resolution from CLAUDE.md.
- [x] 5.4 **commands/autor.research-pipeline.md** — Meta-pipeline: `idea-discovery` → (mandatory human gate) → implementation → `auto-review-loop`. Does NOT include paper-writing (run separately).

### Task 6: Populate Venue Templates

- [x] 6.1 Add placeholder `templates/iclr2026/README.md` with instructions to download official author kit
- [x] 6.2 Add placeholder `templates/neurips2026/README.md` with same
- [x] 6.3 Add placeholder `templates/icml2026/README.md` with same
- [x] 6.4 Document template resolution logic in CLAUDE.md: `TEMPLATE_DIR/VENUE/` → bundled `templates/VENUE/` → error with download instructions

### Task 7: Create Plugin Manifest

- [x] 7.1 Create `.claude-plugin/plugin.json` with name, version, description, skill/command/agent paths
- [x] 7.2 Create `.mcp.json` for auto-configured Codex MCP server
- [x] 7.3 Update README.md with `claude plugin install` instructions

### Task 8: Remove Deprecated Skills

- [x] 8.1 Delete `skills/feishu-notify/`
- [x] 8.2 Delete `skills/pixel-art/`
- [x] 8.3 Delete `skills/autor.paper-writing/` (replaced by `commands/autor.paper-writing.md`)
- [x] 8.4 Delete `skills/research-review/` (replaced by `agents/research-reviewer.md`)
- [x] 8.5 Delete `skills/autor.idea-discovery/` (replaced by `commands/autor.idea-discovery.md`)
- [x] 8.6 Delete `skills/autor.auto-review-loop/` (replaced by `commands/autor.auto-review-loop.md`)
- [x] 8.7 Delete `skills/auto-paper-improvement-loop/` (replaced by `agents/paper-improver.md`)
- [x] 8.8 Delete `skills/autor.research-pipeline/` (replaced by `commands/autor.research-pipeline.md`)

### Task 9: Phase 1 Regression Testing

- [x] 9.1 Verify all 10 skills load correctly (`claude skill list`)
- [x] 9.2 Verify all 4 commands load correctly
- [x] 9.3 Verify both agents load correctly
- [x] 9.4 Dry-run `/autor.idea-discovery "test topic"` — confirm skill chain executes
- [x] 9.5 Dry-run `/autor.paper-writing "test narrative"` — confirm template resolution from CLAUDE.md
- [x] 9.6 Dry-run `/autor.research-pipeline "test direction"` — confirm mandatory gate works
- [x] 9.7 Verify `claude plugin install` works from clean state
- [x] 9.8 Verify Codex MCP auto-configures from `.mcp.json`

---

## Phase 2: Human Involvement + Optional Integrations

### Task 10: Slack Notifications

- [ ] 10.1 Create `skills/slack-notify/SKILL.md` — Send Slack webhook notifications. Modes: off (default) / push
- [ ] 10.2 Add SLACK_WEBHOOK_URL constant to CLAUDE.md
- [ ] 10.3 Integrate into `commands/autor.idea-discovery.md` — notify after idea validation complete
- [ ] 10.4 Integrate into `commands/autor.auto-review-loop.md` — notify after each review round score
- [ ] 10.5 Integrate into `commands/autor.paper-writing.md` — notify after paper compilation
- [ ] 10.6 Integrate into `commands/autor.research-pipeline.md` — notify at mandatory gate + pipeline completion

### Task 11: Configurable Human Checkpoints

- [ ] 11.1 Add `AUTO_PROCEED` constant to CLAUDE.md (default: true for Phase 1 compatibility)
- [ ] 11.2 Add checkpoint gates in `commands/autor.idea-discovery.md` — pause after novelty-check if AUTO_PROCEED=false
- [ ] 11.3 Add checkpoint gate in `commands/autor.paper-writing.md` — pause after paper-plan if AUTO_PROCEED=false
- [ ] 11.4 Add checkpoint gate in `commands/autor.research-pipeline.md` — mandatory gate always waits (regardless of AUTO_PROCEED)

### Task 12: Zotero/Obsidian MCP as Optional Fallbacks

- [ ] 12.1 Add Zotero MCP support back to `research-lit` with graceful degradation
- [ ] 12.2 Add Obsidian MCP support back to `research-lit` with graceful degradation
- [ ] 12.3 Document data source priority in CLAUDE.md: Zotero → Obsidian → Local PDFs → arXiv TeX → Web

### Task 13: Phase 2 Regression Testing

- [ ] 13.1 Test slack-notify with webhook URL configured → verify notifications arrive
- [ ] 13.2 Test slack-notify with no config → verify silent no-op
- [ ] 13.3 Test AUTO_PROCEED=false → verify commands pause at checkpoints
- [ ] 13.4 Test AUTO_PROCEED=true → verify commands proceed automatically
- [ ] 13.5 Test Zotero MCP configured → verify paper search works
- [ ] 13.6 Test Zotero MCP absent → verify graceful fallback to next source
- [ ] 13.7 Full end-to-end pipeline test with all Phase 2 features enabled

---

## Execution Order

```
Phase 1:  Task 1 → Task 2 → Task 3 (parallel) → Task 4 → Task 5 → Task 6 → Task 7 → Task 8 → Task 9
Phase 2:  Task 10 → Task 11 → Task 12 → Task 13
```

Tasks 3.1–3.10 can be parallelized. Tasks 4.1–4.2 can be parallelized. Tasks 5.1–5.4 depend on Tasks 3+4 completion. Task 8 (deletions) must come after Task 5 (commands created).
