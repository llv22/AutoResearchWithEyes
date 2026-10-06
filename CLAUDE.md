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
  codex-bridge (see below). Always run at `model_reasoning_effort: xhigh`. (Verified via `codex exec -m
  gpt-5.6-sol` on 2026-07-14; upgraded from `gpt-5.5`.)

> Note: raw idea *generation* and *review* go to REVIEWER_MODEL (Codex/GPT); the EXECUTOR
> (Claude/Fable 5) orchestrates, filters, and writes. Keeping them in separate families is what
> makes the review adversarial rather than self-review.

## External Reviewer Calls (codex-bridge)

- **CODEX_BRIDGE = `<plugin root>/codex-bridge/bin/codex-bridge`** — the only way skills, agents
  and commands talk to REVIEWER_MODEL (replaces Codex MCP; `codex mcp-server` was removed in
  Codex 0.154). `<plugin root>` is `${CLAUDE_PLUGIN_ROOT}` when loaded as a plugin, else this
  repo's root — always call it by absolute path. Details: [codex-bridge/README.md](codex-bridge/README.md).

Every `REVIEWER_CALL` block in this plugin means:

```
REVIEWER_CALL new [--web]                       # start a reviewer thread
REVIEWER_CALL reply --thread <threadId> [--web] # continue the same thread (keeps its memory)
  prompt: |
    ...
```

1. Write the prompt to `<REVIEW_DIR>/<step>/prompt.md`.
2. Start it detached (returns at once; the call survives this session ending or compacting):
   `CODEX_BRIDGE new --detach --out <REVIEW_DIR>/<step> --prompt-file <REVIEW_DIR>/<step>/prompt.md [--web]`
   (`reply` adds `--thread <threadId>`).
3. Collect it in the foreground: `CODEX_BRIDGE wait --out <REVIEW_DIR>/<step>` (blocks ≤ 9 min).
   Exit 3 / `{"status": "running"}` → run the same `wait` again. Do **not** use
   `run_in_background` for this — headless runs exit before the notification arrives.
4. Read the JSON on stdout: `threadId` (save it — state files keep this field) and `content` (the
   full reviewer response, also in `<step>/reply.md`). On `{"error": ...}` / exit 1, report the
   error — never fabricate a review. After a compaction, `wait` on the same dir recovers the result.

- Defaults: model = REVIEWER_MODEL, effort = xhigh, approval profile = `reviewer`. Don't pass
  `--model`/`--effort` unless overriding. `--web` is per call (each call is a new Codex process),
  so repeat it on `reply` when the thread needs search.
- `<REVIEW_DIR>` = `<command output folder>/reviewer/` (`./reviewer/` when a skill runs
  standalone); `<step>` is unique per call, e.g. `round2`, `novelty-idea3`.
- **Approvals are automatic**: every command the reviewer tries to run is decided by the bridge's
  gate (hard rules, then `claude -p` with the profile rules) and logged in `<step>/approvals.jsonl`.
  Denied actions are not retried — the reviewer lists them as "needs authorization";
  `CODEX_BRIDGE approvals <REVIEW_DIR>` shows them. Grant one by running it yourself and sending the
  output back with `reply`.
- After upgrading Codex, run `CODEX_BRIDGE selftest`.

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
