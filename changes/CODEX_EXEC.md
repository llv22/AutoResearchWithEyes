# Ticket: Support current Codex CLI (replace Codex MCP with `codex exec`)

Date: 2026-10-05
Status: **Implemented** (2026-10-05) — component in [`codex-bridge/`](../codex-bridge/README.md)

## 1. Problem

Every cross-model step (REVIEWER_MODEL brainstorm / review / novelty verdict) calls Codex
through the MCP tools `mcp__codex__codex` and `mcp__codex__codex-reply`, served by
`codex mcp-server` (configured in `.mcp.json`).

`codex mcp-server` was deprecated in Codex 0.150–0.153 and **removed in 0.154**. On current
Codex (0.160) the subcommand no longer exists — `codex mcp-server` is parsed as an interactive
prompt and exits with `Error: stdin is not a terminal`, so the MCP server never connects and
every reviewer step fails.

| Codex version | `codex mcp-server` |
|---|---|
| ≤ 0.145 | works |
| 0.150.1 – 0.153.4 | works, prints deprecation warning |
| ≥ 0.154.0 (incl. 0.160.0) | removed |

### Current stopgap (local machine only, not in repo)

A pinned `@openai/codex@0.153.4` is registered as a local-scope MCP server for this folder,
with its own `CODEX_HOME` (shared `auth.json`). Limitations:

- Dead end — no future Codex fixes/models.
- Old clients are **model-gated**: 0.153.4 + ChatGPT login rejects `gpt-6.1-sol`
  ("not supported when using Codex with a ChatGPT account"); only `gpt-5.6-sol` and older work.
- Calls without an explicit `model` fall back to `config.toml` (e.g. `novelty-check` doesn't
  pass `model:`), so the stopgap needs a separate `CODEX_HOME` with a compatible default.

## 2. Impact inventory

`mcp__codex__*` references (excluding READMEs):

| File | Refs | Uses `codex-reply` (multi-turn) |
|---|---|---|
| `skills/idea-creator/SKILL.md` | 3 | ✅ |
| `skills/novelty-check/SKILL.md` | 2 | |
| `skills/paper-plan/SKILL.md` | 2 | ✅ |
| `skills/paper-figure/SKILL.md` | 2 | ✅ |
| `skills/paper-write/SKILL.md` | 2 | ✅ |
| `agents/research-reviewer.md` | 2 | ✅ |
| `agents/paper-improver.md` | 4 | ✅ (threadId persisted in `PAPER_IMPROVEMENT_STATE.json`) |
| `commands/autor.auto-review-loop.md` | 5 | ✅ (threadId persisted in state file) |
| `commands/autor.idea-discovery.md` | 1 | ✅ |
| `commands/autor.paper-writing.md` | 1 | ✅ |
| `commands/autor.research-pipeline.md` | 1 | ✅ |

Also: `.mcp.json`, `CLAUDE.md` (REVIEWER_MODEL note), `README.md`, `README_aris.md`,
`README_CN_aris.md`, `changes/phase1.md` (setup), `.claude-plugin/plugin.json` (`codex-mcp` keyword),
and `allowed-tools` frontmatter in 9 files.

Features the replacement must keep:

1. **Multi-turn threads** — round N+1 continues the same reviewer conversation (`threadId`),
   including after context compaction (thread id stored in state files).
2. **Per-call config** — `model`, `model_reasoning_effort: xhigh`, `tools.web_search: true`,
   read-only sandbox.
3. **Clean result** — the reviewer's final message only, no event noise.
4. **Long calls** — xhigh reviews of a full paper can run many minutes.

## 3. Spike: `codex exec` on 0.160 (verified 2026-10-05)

| Need | `codex exec` equivalent | Result |
|---|---|---|
| Start thread | `codex exec --json -m M -s read-only -c model_reasoning_effort=xhigh -o last.md "PROMPT"` | ✅ first JSONL event is `{"type":"thread.started","thread_id":"…"}` |
| Continue thread | `codex exec resume --json -o last.md <thread_id> "PROMPT"` | ✅ recalled a fact from turn 1; same `thread_id` |
| Final message only | `-o/--output-last-message <file>` | ✅ |
| Web search | `-c tools.web_search=true` (also `-c web_search="live"`) | ✅ `web_search` events emitted |
| Current models | default `gpt-6.1-sol` | ✅ works (unlike the 0.153.4 stopgap) |
| Structured output | `--output-schema <file>` | available (not needed now) |

Gotchas found:

- `codex exec` **waits on stdin** when it is not a TTY ("Reading additional input from
  stdin…") — always redirect `< /dev/null` (or pipe the prompt via stdin with `-`).
- `resume` has no `-s/--sandbox` flag — sandbox is inherited from the session (or `-c sandbox_mode=…`).
- Run outside a git repo needs `--skip-git-repo-check`.
- Claude Code's Bash tool caps foreground calls at 10 min → long reviews must run with
  `run_in_background: true` (completion notification) or be polled.

### 3.1 Full parity with the old `codex mcp-server` (verified 2026-10-05)

`tools/list` on `codex mcp-server` 0.153.4 exposes exactly **2 tools, 12 params**, plus
`{threadId, content}` output. Each mapped to `codex exec` 0.160 and run with `--strict-config`:

| MCP tool.param | `codex exec` 0.160 equivalent | Verified |
|---|---|---|
| `codex.prompt`* | positional arg, or stdin with `-` | ✅ |
| `codex.model` | `-m M` | ✅ |
| `codex.sandbox` | `-s read-only\|workspace-write\|danger-full-access` (resume: `-c sandbox_mode="…"`) | ✅ |
| `codex.cwd` | `-C DIR` | ✅ |
| `codex.config` (object) | one `-c dotted.key=TOML` per leaf | ✅ |
| `codex.developer-instructions` | `-c developer_instructions="…"` | ✅ |
| `codex.base-instructions` | **renamed**: `base_instructions` → unknown key; use `-c instructions="…"` or `-c model_instructions_file="path"` | ✅ |
| `codex.compact-prompt` | `-c compact_prompt="…"` | ✅ |
| `codex.approval-policy` | `-c approval_policy="never\|on-request"` | ✅ accepted — see gap 1 |
| `codex-reply.threadId`* | `codex exec resume <id>` | ✅ (memory kept) |
| `codex-reply.conversationId` (deprecated) | alias of threadId | ✅ (wrapper accepts both) |
| `codex-reply.prompt`* | positional arg / stdin | ✅ |
| output `threadId` | first JSONL event `thread.started.thread_id` | ✅ |
| output `content` | `-o last.md` (final agent message) | ✅ |

Behavioural differences (not params):

1. **Interactive approvals** — the MCP server could forward `on-request` approvals to the MCP
   client (elicitation). `exec` has no back channel: approvals can only be `never`, or delegated
   to automatic review via `--approve-for-me`. **No current skill uses this** (all reviewer calls
   are read-only). Replaced by hook-based trackable approvals — see §5.2.
2. **Progress events** — MCP streamed `codex/event` notifications; `exec --json` streams the same
   kind of events as JSONL to stdout → kept as `events.jsonl` per call (better: persisted).
3. Env note (this box, not Codex): the Linux sandbox can't run shell commands here
   (`bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted`); text-only reviews unaffected.
   Same on both paths.

## 4. Options

### A. Keep pinning Codex ≤ 0.153.4 (status quo stopgap)
Zero repo changes. Dead end; model-gated; breaks for anyone installing current Codex. **Reject.**

### B. Inline `codex exec` commands in every skill/agent/command
Replace each `mcp__codex__codex:` block with a Bash snippet. Simple and transparent, but the
flags (`--json`, `-o`, `< /dev/null`, thread-id extraction, web search, sandbox) get
duplicated across ~11 files and drift.

### C. One wrapper script + skills call it via Bash  ⭐ recommended
Add `scripts/codex-review.sh` (small bash, no deps beyond `codex` + `jq`/`grep`):

```bash
# new thread → prints thread_id on stdout, writes the final reply to --out
scripts/codex-review.sh new    --out DIR/reply.md [--model M] [--effort xhigh] [--web] < prompt.md
# continue the same thread
scripts/codex-review.sh reply  --thread THREAD_ID --out DIR/reply.md < prompt.md
```

- Centralizes flags and gotchas in one place; REVIEWER_MODEL default read from env/arg.
- Prompt via stdin file → no shell-quoting issues for long paper prompts.
- Writes `reply.md` + `thread_id` into the command's output folder → fits the existing
  state-file recovery (`threadId` field keeps its meaning).
- Skills change from "call `mcp__codex__codex` with {…}" to "run `scripts/codex-review.sh …`
  (with `run_in_background: true` for xhigh reviews), then read `reply.md`".
- `allowed-tools`: drop `mcp__codex__*`, rely on `Bash(*)` (already present in most files).

### D. Write a tiny replacement MCP server that wraps `codex exec`
Keep tool names `mcp__codex__codex` / `codex-reply` so **no skill text changes**; implement
them over `codex exec` / `exec resume`. Least churn in skills, but adds a server component
(Python/Node + MCP SDK) to maintain, and keeps MCP tool-timeout limits on long calls.

### E. `codex app-server` (JSON-RPC)
Marked `[experimental]`; protocol may change. **Reject** for now.

## 5. Recommendation

**Option C.** It uses the officially supported non-interactive interface, keeps all four
required features, puts every Codex-specific detail in one script, and removes the MCP
dependency (and `.mcp.json`) entirely. D is the fallback if we want to avoid touching skill text.
The wrapper is refined in §5.1 (`scripts/codex_bridge.py`, replacing the bash sketch above).

### 5.1 Future-proofing: stable contract + swappable backends

Codex has already changed this interface twice (MCP server removed; `base_instructions`
renamed). Design the wrapper so the next change touches **one file**, never the skills:

```
skills / agents / commands
        │  stable contract (never changes)
        ▼
scripts/codex_bridge.py  (Python stdlib only)
   ├─ contract: new|reply  — params = the 12 MCP params, 1:1 names
   │            output     = {"threadId","content"} JSON on stdout (+ reply.md, events.jsonl)
   ├─ key map:  contract param → current Codex flag/config key (version-gated table)
   └─ backends: exec (default, ≥0.154) │ mcp (legacy ≤0.153) │ app-server (future)
                selected by CODEX_BACKEND=auto|exec|mcp, auto = probe `codex --version`/--help
```

1. **Stable contract mirrors the old MCP schema** — same param names and output shape, so the
   skills' mental model ("call codex, get threadId + content, reply with threadId") is unchanged,
   and state files keep their `threadId` field.
2. **One mapping table** — e.g. `base-instructions → instructions` (≥0.160) / `base_instructions`
   (older). A Codex rename = one table row.
3. **Pluggable backends** — `exec` now; keep `mcp` for old installs; add `app-server` if it
   stabilizes, or a non-Codex reviewer (e.g. another CLI) behind the same contract.
4. **Fail loudly** — always pass `--strict-config`, so a renamed/removed key errors immediately
   instead of being silently ignored (verified: unknown key → exit 1).
5. **`selftest` subcommand** — runs the parity checks of §3.1 (round trip, resume memory, web
   search, each param) and prints the Codex version; run after every Codex upgrade.
6. **Record tested version** — CLAUDE.md states `CODEX_TESTED_VERSION`; `selftest` warns on mismatch.

Why Python instead of bash: the mapping table, JSON event parsing and backend switch are
awkward in bash; stdlib Python 3 is already required on any machine running Claude Code skills.

### 5.2 Trackable approvals (replaces MCP elicitation)

Codex 0.160 has stable **hooks** (`hooks.json`, same wire format as Claude Code):
`PreToolUse` can return `permissionDecision: allow|deny` + reason, and receives
`session_id` (= threadId), `turn_id`, `tool_name`, `tool_input`, `cwd`.

Spike results (2026-10-05):

| Test | Result |
|---|---|
| Hook logs every tool call | ✅ `{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"echo hi"},"session_id":…,"turn_id":…}` |
| Hook denies `rm keep.txt` | ✅ blocked, file kept; Codex sees the reason and reports it |
| Hook blocks until an external decision file appears, then allows | ✅ Codex paused, resumed on `{"decision":"allow"}`, command ran |
| Hook **not trusted** (no `--dangerously-bypass-hook-trust`, no TUI trust) | ⚠️ hook **silently skipped**, command ran ungated |

Design — three layers, all owned by `codex_bridge.py`:

```
Codex tool call ──PreToolUse hook──▶ approval_gate.py
   1. policy   (approvals.toml: allow / deny / ask by tool + command pattern, per call profile)
   2. ask  ──▶ <out>/approvals/pending/<id>.json ──▶ decided by Claude orchestrator or human
              ◀── <out>/approvals/decided/<id>.json   (timeout ⇒ deny)
   3. ledger   <out>/approvals.jsonl  (append-only, one line per decision)
```

1. **Policy first** — profiles per call type, e.g. `reviewer` = deny anything that writes
   (reviews are read-only); `experiment` = allow `python`, `nvidia-smi`, `tail`…, ask for the rest;
   always deny `rm -rf`, `git push`, network installs. Most calls never need a human.
2. **Pending queue for `ask`** — gate writes a request and blocks (bounded, default 10 min,
   then **deny**). Answered via `codex_bridge.py approvals list` /
   `codex_bridge.py approvals decide <id> allow|deny --reason …`. Who answers follows the
   existing CLAUDE.md constant: `AUTO_PROCEED=true` → Claude orchestrator decides;
   `false` → human (Phase-2 human checkpoints / slack-notify can surface pending requests).
3. **Ledger** — `approvals.jsonl` in the command's output folder:
   `{id, ts_requested, ts_decided, threadId, turn_id, tool, input, decision, decided_by:
   policy|claude|human|timeout, rule, reason}`. Lives next to `events.jsonl` and the state
   file, so it survives compaction and makes every run auditable after the fact.
4. **Fail closed on trust** — untrusted hooks are silently skipped, so the bridge (a) passes
   `--dangerously-bypass-hook-trust` only for its own repo-tracked hook file, and (b) requires a
   `SessionStart` hook sentinel in the ledger before accepting the result; no sentinel ⇒ abort.
5. Codex sandbox (`-s read-only` for reviewers) stays as defence in depth.

### 5.3 Runtime authorization without blocking the review

Concern: a blocking `ask` (§5.2 layer 2) stalls the review until someone answers. Rule: **the
reviewer never waits on a human.** Runtime authorization options, in order of preference:

1. **Reads never need approval** — `reviewer` profile auto-allows read-only commands
   (`cat`, `rg`, `sed -n`, `ls`, `git diff/log/show`), so normal code review can't stall.
2. **Deny-and-defer (non-blocking)** — anything outside the profile is denied *immediately* with a
   reason ("not authorized yet; continue the review and list what you need"). The gate records it
   in `approvals.jsonl` as `deferred`. Codex finishes the review and states what it wanted (spike:
   Codex reports denied commands and their reasons).
3. **Grant between turns** — after the turn, Claude (or the human) reviews deferred requests and
   either (a) runs the command itself and feeds the output back via `codex_bridge.py reply`, or
   (b) widens the grant for the next turn only: each `exec resume` is a new process, so the bridge
   can resume the same thread with a broader profile / `-c sandbox_mode=…` (resume +
   `-c sandbox_mode` verified). Every grant is logged with `decided_by` and scope = `turn`.
4. **Live LLM approver (default — see §5.4)** — the gate delegates `ask` to `claude -p` with the
   rules instead of a human. Bounded (≤60 s), logged as `decided_by: claude`, falls back to
   deny-and-defer. (`--approve-for-me` was tested and rejected as default.)
5. **Blocking human `ask`** — only when `AUTO_PROCEED=false`, short timeout, then falls back to
   deny-and-defer rather than failing the run.

### 5.4 Auto-approval: `--approve-for-me` vs `claude -p` (tested 2026-10-05)

**Decision: auto-approval is the default; approver = `claude -p` with our rules.** Humans are
not in the loop unless they opt in (`AUTO_PROCEED=false`). Prototype + rules + test cases:
[`codex_exec_spike/`](codex_exec_spike/).

| | Codex `--approve-for-me` (guardian) | `claude -p` gate (PreToolUse hook) |
|---|---|---|
| Works on Codex 0.160 | ✅ separate reviewer thread, model `codex-auto-review` | ✅ |
| Output | `{risk_level, user_authorization, outcome, rationale}` | `{decision, reason, risk}` + `decided_by` |
| Where recorded | only Codex rollout files (`$CODEX_HOME/sessions/…`), not in `--json` events | our `approvals.jsonl` ledger, per run |
| Our rules | ❌ uses Codex's own workspace policy | ✅ `rules.md` per profile |
| Behaviour | **approved** `rm -rf ~/dummy` *and* a high-risk `git push --force` because "the user explicitly authorized it" — in our pipeline the "user" is the orchestrator, so this is effectively allow-all | judges the action, not the agent's justification |
| Accuracy (12 labelled cases) | not scored | **12/12** (Sonnet 5.5 and Haiku 4.5) after fixes below |
| Latency | ~5 s per escalation | rules: 0 ms; Sonnet 5.5: **~3.4 s**; Haiku 4.5: ~8.7 s |

Gate design (prototype `approval_gate.py`):

1. **Hard rules first, no LLM** — secrets paths (`.ssh/`, `auth.json`, `.env`, …) → deny;
   `sudo`, `git push`, `reset --hard`, `rm -rf /…|~…` → deny; plain read-only commands → allow.
2. **`claude -p` for everything else** — `--setting-sources ""` (no user hooks/plugins → no
   recursion, no memory pollution), `--tools ""`, `--strict-mcp-config`, `--json-schema` for
   structured output, `--no-session-persistence`, default model `claude-sonnet-5-5`.
3. **Fail closed** — approver error/timeout (60 s) ⇒ deny with a "continue without it" reason
   (§5.3 deny-and-defer).
4. **Ledger** — every decision → `approvals.jsonl` (`threadId`, `turn_id`, command, decision,
   reason, risk, `decided_by: rule|claude|error`, model, latency).

Bugs found and fixed during the spike:

- `--bare` skips OAuth → `Not logged in`; use `--setting-sources ""` instead.
- The approver must run with `cwd = workspace_root` and be told the workspace explicitly;
  otherwise it judged Codex's cwd as "outside the workspace" and denied legit experiment runs.
- Fast-allow `cat …` let `cat ~/.ssh/id_rsa` through; the secrets check now runs first.

End-to-end (Codex 0.160 + hook, 6 commands): `ls`, `python3 train.py` allowed; `rm -rf ~/dummy`,
`cat ~/.ssh/id_rsa`, `git push` denied with reasons Codex reported back — all 6 in the ledger.

**Extra layer found: Codex built-in exec policy.** Codex ships a non-overridable `default.rules`
that rejects `rm -f`-style commands ("rm -f style commands are not permitted. Use a safer
approach") even after our gate allowed it, with `approval_policy="never"` and `--ignore-rules`.
It is deny-only (can't weaken our gate).

**Resolution — override via Codex config (verified):** a user execpolicy rule takes precedence
over the built-in `default.rules`:

```python
# <CODEX_HOME>/rules/autoresearch.rules   (Starlark)
prefix_rule(pattern = ["rm"], decision = "allow")
```

`codex execpolicy check --rules autoresearch.rules rm -f x` → `allow`; in a real run the hook
was still consulted first (`decided_by: claude`, logged), then `rm -f outputs/tmp.log` ran.
So our gate becomes the single authority. Design choices:

- **Bridge-owned `CODEX_HOME`** (e.g. `~/.local/share/autoresearch/codex-home`: own
  `config.toml`, `rules/autoresearch.rules`, `hooks.json`, `auth.json` → symlink to the user's)
  rather than editing the user's global `~/.codex` — the override applies only to pipeline runs,
  and pipeline sessions are isolated from interactive Codex history.
- Only override prefixes the gate already judges (start with `rm`); any *other* built-in
  rejection is still logged from `events.jsonl` into the ledger as `decided_by: codex_policy`,
  and a new override is added only after review.

## 6. Decisions (2026-10-05)

1. **Option C** — standalone component `codex-bridge/` (top-level, independent of skills), skills
   call it through Bash. Option D (replacement MCP server) not pursued.
2. **Bridge-owned `CODEX_HOME`** — the user's `~/.codex` is never modified.
3. **REVIEWER_MODEL stays `gpt-5.6-sol`** (bridge default, xhigh).
4. **Auto-approval on by default** — hard rules + `claude -p` (`claude-sonnet-5-5`); humans only on demand.
5. Long calls: `--detach` + foreground `wait` (≤ 9 min per `wait`, repeat while running).
   First tried `run_in_background` + notification — the regression showed a headless
   `claude -p` run exits right after launching it and kills the in-flight review (thread
   started, no `turn.completed`, no result). Detached calls survive the caller and any later
   session can collect them from the call dir. `.mcp.json` removed — the bridge refuses Codex < 0.154, so there is
   no legacy path to keep. Replies live in the command's output folder (`<out>/reviewer/<step>/`).
6. Only the `exec` backend is implemented; the `mcp` legacy backend from §5.1 was dropped (no
   remaining user of Codex ≤ 0.153). The `BACKENDS` registry is the extension point.

## 7. Plan

- [x] 1. `codex-bridge/` component per §5.1: contract (`new`/`reply`, 12 MCP params 1:1), `CONFIG_KEYS`
      map, `ExecBackend`, `BACKENDS` registry, `selftest`, offline unit tests
      → 14/14 unit tests; `selftest` 7/7 on Codex 0.160.0 (new, reply memory, developer
      instructions, web search, gate deny + ledger)
- [x] 1b. Approval gate (`codex_bridge/gate.py`) per §5.2–5.4: hard rules, `claude -p` approver,
      `reviewer`/`experiment` profiles, ledger, `SessionStart` sentinel (missing ⇒ result discarded),
      `codex_policy` rejections imported from stderr, refuses cwd with project `.codex/hooks.json`
- [x] 2. CLAUDE.md: `CODEX_BRIDGE` constant + `REVIEWER_CALL` invocation contract (once)
- [x] 3. Skills migrated: idea-creator, novelty-check (+ `Bash(*)`), paper-plan, paper-figure, paper-write
- [x] 4. Agents migrated: research-reviewer, paper-improver (state-file `threadId` unchanged)
- [x] 5. Commands migrated: auto-review-loop, idea-discovery, paper-writing, research-pipeline
- [x] 6. `mcp__codex__*` removed from `allowed-tools`; `.mcp.json` deleted; plugin keyword/description updated
- [x] 7. README.md updated (setup, layout, permissions, alt-model notes). README_aris.md /
      README_CN_aris.md (upstream ARIS docs), xhs_post.md and `changes/` history left as-is.
- [x] 8. Regression: `grep -r mcp__codex` → only historical docs + bridge README.
      Headless `claude -p "/novelty-check …"` from the repo root (2026-10-05):
      run 1 (`run_in_background`) lost the review when the session exited → added `--detach`/`wait`;
      run 2 passed in 229 s: detached call, `wait` collected a 168 s `gpt-5.6-sol` xhigh review
      with 13 web-search calls, sentinel present, all gate decisions logged. Fix from run 2: built-in
      web tool (`webrun`) is now rule-allowed (was ~3.5 s of `claude -p` per search).
      Unit tests 18/18; live `selftest` 7/7 on Codex 0.160.0.
- [x] 9. Local stopgap removed (local-scope MCP registration + pinned Codex 0.153.4 install).
