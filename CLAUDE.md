# AutoResearchWithEyes: Centralized Constants

All skills, commands, and agents in this plugin reference these shared constants. Override per-invocation by passing inline arguments (e.g., `— pilot budget: 4h`).

## Models (cross-model, no self-play)

Two roles, two **different families** — Claude executes, GPT reviews. This adversarial split is
the framework's core principle; do not collapse both roles onto one family.

- **EXECUTOR_MODEL = `claude-fable-5`** (Fable 5) — the Claude Code model that *drives* the
  pipeline: idea filtering/synthesis, literature review, novelty judgment, and writing. Use it
  for more solid `idea-discovery` output. Run the `/autor.*` commands under this model (`/model
  fable` in Claude Code, or spawn via an `Agent` with model `fable`). (Verified available as
  `claude-fable-5` on 2026-07-14.)
- **REVIEWER_MODEL = `gpt-5.6-sol`** — external critical reviewer + divergent brainstorm via
  Codex MCP. Always run at `model_reasoning_effort: xhigh`. (Verified via `codex exec -m
  gpt-5.6-sol` on 2026-07-14; upgraded from `gpt-5.5`.)

> Note: raw idea *generation* and *review* go to REVIEWER_MODEL (Codex/GPT); the EXECUTOR
> (Claude/Fable 5) orchestrates, filters, and writes. Keeping them in separate families is what
> makes the review adversarial rather than self-review.

## Idea Discovery & Pilot Experiments

- **PILOT_MAX_HOURS = 2** — Skip any pilot estimated to take > 2 hours per GPU. Flag as "needs manual pilot".
- **PILOT_TIMEOUT_HOURS = 3** — Hard timeout: kill pilots exceeding 3 hours. Collect partial results if available.
- **MAX_PILOT_IDEAS = 3** — Pilot at most 3 ideas in parallel. Additional ideas are validated on paper only.
- **MAX_TOTAL_GPU_HOURS = 8** — Total GPU budget for all pilots combined.

## Review Loop

- **MAX_ROUNDS = 4** — Maximum review-fix-review iterations in the auto-review loop.
- **POSITIVE_THRESHOLD** — Score >= 6/10, or verdict contains "accept", "sufficient", "ready for submission".

## Workflow Orchestration

- **AUTO_PROCEED = true** — If user doesn't respond at a checkpoint, automatically proceed with the best option. Set to `false` to always wait for explicit user confirmation.
- **MAX_IMPROVEMENT_ROUNDS = 2** — Number of review-fix-recompile rounds in the paper improvement loop.

## Paper Compilation

- **COMPILER = `latexmk`** — LaTeX build tool. Handles multi-pass compilation automatically.
- **ENGINE = `pdflatex`** — LaTeX engine. Options: `pdflatex` (default), `xelatex` (for CJK/custom fonts), `lualatex`.
- **MAX_COMPILE_ATTEMPTS = 3** — Maximum attempts to fix errors and recompile.

## Venue & Templates

- **VENUE = `iclr2026`** — Current target venue. Determines which template directory to use.
- **TEMPLATE_DIR = `templates/`** — Directory containing venue template subdirectories. Each subdirectory (e.g., `templates/iclr2026/`) contains the venue's `.sty`, `.cls`, and `.bst` files.

### Template Resolution

When a skill needs venue files, it resolves them in this order:
1. `TEMPLATE_DIR/VENUE/` — user's configured template directory
2. Bundled `templates/VENUE/` — default templates shipped with the plugin
3. **Error** — clear message with download instructions for the venue's official author kit

### Page Limits

Page limits are venue-dependent (main body to end of Conclusion, excluding references & appendix):
- `iclr2026` = 9 pages
- `neurips2026` = 9 pages
- `icml2026` = 8 pages
- `emnlp2026` = 8 pages (long) / 4 pages (short)

All ML venues use `natbib` (`\citep`/`\citet`).
