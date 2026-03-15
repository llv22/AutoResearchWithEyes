# AutoResearchWithEyes: Centralized Constants

All skills, commands, and agents in this plugin reference these shared constants. Override per-invocation by passing inline arguments (e.g., `— pilot budget: 4h`).

## External Reviewer

- **REVIEWER_MODEL = `gpt-5.4`** — Model used via Codex MCP for brainstorming, review, and cross-verification.

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
