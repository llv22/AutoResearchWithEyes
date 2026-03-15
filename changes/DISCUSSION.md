# Simplification Discussion Results

Date: 2026-03-13

## Decisions

### 1. Skills to REMOVE (4)

| Skill | Decision | Reason |
|-------|----------|--------|
| feishu-notify | Remove → replace with **slack-notify** in Phase 2 | Slack is more universal; plug into key pipeline phases |
| pixel-art | Remove | Unrelated to ML research pipeline |
| paper-writing | Remove | Duplicate orchestrator — replaced by paper-writing command |
| research-review | Remove as skill → extract into **research-reviewer agent** | Review logic belongs in a dedicated agent persona |

### 2. Skills to MERGE → Commands

| New Command | Composed From | Purpose |
|-------------|---------------|---------|
| idea-discovery | research-lit → idea-creator → novelty-check → research-reviewer agent | Workflow 1: direction → validated ideas |
| auto-review-loop | review → fix → run-experiment → re-review (×4) | Workflow 2: autonomous iteration |
| paper-writing | paper-plan → paper-figure → paper-write → paper-compile → paper-improver agent | Workflow 3: narrative → submission PDF |
| research-pipeline | idea-discovery → implementation → auto-review-loop → paper-writing | Meta-pipeline: full end-to-end |

### 3. New Architecture: Skills + Commands + Agents

**10 Skills** (building blocks, auto-invoked by commands):
1. research-lit
2. idea-creator
3. novelty-check
4. run-experiment
5. monitor-experiment
6. analyze-results
7. paper-plan
8. paper-figure
9. paper-write
10. paper-compile

**4 Commands** (user-invoked workflow orchestrators):
1. idea-discovery
2. auto-review-loop
3. paper-writing
4. research-pipeline

**2 Agents** (specialized personas):
1. research-reviewer — critical ML reviewer via Codex MCP (GPT-5.4 xhigh)
2. paper-improver — 2-round auto-improvement loop

### 4. Cross-Cutting Changes

| Change | Decision |
|--------|----------|
| Constants centralization | Move all hardcoded values to CLAUDE.md |
| Venue templates | Bundle defaults in `templates/VENUE/`, configurable via `VENUE` + `TEMPLATE_DIR` in CLAUDE.md, with user override support |
| arXiv reading | Add TeX source fetching (`/src/{id}`) instead of PDF |
| Plugin format | Adopt `.claude-plugin/plugin.json` for `claude plugin install` |
| Reviewer model | Keep Codex MCP (GPT-5.4 xhigh) as cross-model reviewer |

### 5. Phase Plan

**Phase 1: End-to-end automation**
- Restructure 18 skills → 10 skills + 4 commands + 2 agents
- Remove feishu-notify, pixel-art, paper-writing (duplicate), research-review (→ agent)
- Centralize constants in CLAUDE.md
- Configurable venue templates: bundled defaults in `templates/VENUE/`, `VENUE` + `TEMPLATE_DIR` constants in CLAUDE.md, fallback chain (TEMPLATE_DIR → bundled → error)
- Add arXiv TeX source reading
- Plugin format adoption
- Regression testing

**Phase 2: Human involvement + optional integrations**
- slack-notify at key pipeline phases (idea approval, experiment complete, paper ready)
- Zotero MCP as optional fallback in research-lit
- Obsidian MCP as optional fallback in research-lit
- Configurable human checkpoints (novelty-check gate, paper-plan gate)
