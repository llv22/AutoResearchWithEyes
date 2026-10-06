# codex-bridge

A small, standalone component that gives AutoResearchWithEyes a **stable way to call Codex as an
external reviewer**, independent of which interface the installed Codex ships. Stdlib Python 3.10+,
no dependencies. Design and verification notes: [`../changes/CODEX_EXEC.md`](../changes/CODEX_EXEC.md).

Why it exists: the plugin used to call Codex through `codex mcp-server` (MCP tools
`mcp__codex__codex` / `codex-reply`). Codex deprecated that in 0.150 and removed it in 0.154.
The bridge keeps the same call contract and maps it onto `codex exec` — and the next interface
change is absorbed here, not in the skills.

```
skills / agents / commands ──(stable contract)──▶ codex-bridge ──▶ backend: exec (Codex ≥ 0.154)
                                                     │                 (add new backends here)
                                                     └─ bridge-owned CODEX_HOME + approval gate
```

## Contract

```bash
B=codex-bridge/bin/codex-bridge
$B new   --out DIR [--web] [--profile reviewer|experiment] [options] < prompt.md
$B reply --thread THREAD_ID --out DIR [--web] [options]              < prompt.md
```

Prints one JSON object on stdout and exits 0:

```json
{"threadId": "…", "content": "<final reviewer message>", "outDir": "DIR",
 "sandbox": "…", "codexVersion": "0.160.0", "backend": "exec"}
```

On failure: `{"error": "…"}` and exit 1 (never a partial review). Each call writes into `DIR`:
`reply.md`, `events.jsonl` (raw Codex events), `approvals.jsonl` (approval ledger),
`codex.stderr.log`, `meta.json`, `result.json` (the stdout JSON).

**Long calls** (xhigh reviews run for many minutes): add `--detach`. The call runs in its own
process session, so it survives the caller exiting — a headless `claude -p` run, a context
compaction, a dropped SSH session — and returns `{"status": "running"}` immediately. Then:

```bash
$B wait --out DIR [--timeout 540]   # same JSON as a direct call; exit 3 = still running, run again
```

`wait` is idempotent and reads only `DIR`, so any later session can collect the result.
A worker that died without writing a result is reported as an error, not waited on forever.

Options mirror the 12 params of the retired MCP tools, 1:1:

| Old MCP param | Bridge option | Codex mapping (exec backend) |
|---|---|---|
| `prompt` | stdin or `--prompt-file` | `-` (stdin) |
| `model` | `--model` (default `gpt-5.6-sol`) | `-m` |
| `sandbox` | `--sandbox` (default `auto`) | `-c sandbox_mode=…` |
| `cwd` | `--cwd` (`new` only) | `-C` |
| `config` | `--config KEY=TOML` (repeatable), `--config-json '{…}'` | `-c` per leaf |
| `developer-instructions` | `--developer-instructions` | `-c developer_instructions=…` |
| `base-instructions` | `--base-instructions` | `-c instructions=…` (renamed in Codex) |
| `compact-prompt` | `--compact-prompt` | `-c compact_prompt=…` |
| `approval-policy` | `--approval-policy` | `-c approval_policy=…` |
| `threadId` / `conversationId` | `--thread` / `--conversation-id` | `codex exec resume <id>` |
| — | `--effort` (default `xhigh`), `--web` | `-c model_reasoning_effort=…`, `-c tools.web_search=true` |

Other commands: `wait --out DIR` (see above), `approvals DIR` (summarize every ledger under DIR), `setup` (provision the home
and print it), `selftest` (live parity checks — run after every Codex upgrade).

## Bridge-owned `CODEX_HOME`

Calls never use your `~/.codex` config. The bridge regenerates its own home on every call
(`$CODEX_BRIDGE_HOME`, default `${XDG_DATA_HOME:-~/.local/share}/autoresearch/codex-home`):

| File | Purpose |
|---|---|
| `config.toml` | `model = gpt-5.6-sol`, `model_reasoning_effort = xhigh`, `approval_policy = never` |
| `auth.json` | symlink to your `$CODEX_HOME/auth.json` (shared login and token refresh) |
| `hooks.json` | `SessionStart` + `PreToolUse` → `codex_bridge/gate.py` |
| `rules/autoresearch.rules` | execpolicy override so the gate, not Codex's built-in `default.rules`, decides `rm …` |
| `sandbox_probe.json` | cached `codex sandbox -- true` result per Codex version |

Pipeline sessions therefore stay out of your interactive Codex history, and your own Codex
settings (default model, MCP servers, plugins) don't leak into reviews.

## Automatic approvals

Codex runs non-interactively, so nobody is asked to click "approve". Every command Codex tries
to run passes through `gate.py` (a Codex `PreToolUse` hook):

1. **Hard rules** (no LLM): credential paths, `sudo`, `git push`, `reset --hard`,
   `rm -r` on absolute/home paths → **deny**; plain read-only commands and the built-in web
   search tool (`webrun`) → **allow**.
2. **`claude -p`** with the profile's rules (`profiles/reviewer.md`, `profiles/experiment.md`)
   for everything else → allow/deny with a reason. Isolated: `--setting-sources ""`
   (no user hooks/plugins), `--tools ""`, structured JSON output.
3. **Fail closed**: approver error or timeout (60 s) → deny. Denials tell Codex to continue
   without the action and list it as "needs authorization" — reviews never block.

Every decision goes to `approvals.jsonl`:
`{threadId, turn_id, command, decision, reason, risk, decided_by: rule|claude|error|codex_policy, model, ms}`.
Codex's own built-in policy rejections (stderr only) are imported as `decided_by: codex_policy`.

Safety checks:

- Hooks only run if Codex trusts them, and untrusted hooks are skipped silently. The bridge
  passes `--dangerously-bypass-hook-trust` for its own `hooks.json` and **requires the
  `SessionStart` sentinel** for the thread in the ledger. If it's missing, the result is discarded.
- It refuses to run in a `--cwd` that has its own `.codex/hooks.json`, since the trust bypass
  would cover that file too.
- Sandbox `auto`: `read-only` (reviewer) / `workspace-write` (experiment) when Codex's OS sandbox
  works; when it doesn't (e.g. bwrap blocked), it uses `danger-full-access` and the gate is the guard.

| Env var | Default | Meaning |
|---|---|---|
| `CODEX_BRIDGE_HOME` | see above | bridge-owned `CODEX_HOME` |
| `CODEX_BRIDGE_CODEX` | `codex` | Codex binary to drive |
| `CODEX_BRIDGE_BACKEND` | `exec` | backend name |
| `CODEX_BRIDGE_APPROVER_MODEL` | `claude-sonnet-5-5` | model for `claude -p` approvals |
| `CODEX_BRIDGE_APPROVER_TIMEOUT` | `60` | seconds before an approval is denied |

## When Codex changes again

- **Renamed config key** → one row in `CONFIG_KEYS` (`codex_bridge/backends.py`). `--strict-config`
  makes Codex reject unknown keys, so a rename fails loudly instead of being ignored.
- **New interface** (e.g. `app-server` stabilizes) → add a class next to `ExecBackend` and register it
  in `BACKENDS`. Callers keep using `new`/`reply`.
- After any upgrade, run `codex-bridge selftest` and bump `CODEX_TESTED_VERSION` in
  `codex_bridge/__init__.py`.

## Layout

```
codex-bridge/
├── bin/codex-bridge            # entry point (bash → python3 -m codex_bridge)
├── codex_bridge/
│   ├── cli.py                  # contract: new / reply (--detach) / wait / approvals / setup / selftest
│   ├── backends.py             # contract → Codex mapping; ExecBackend; BACKENDS registry
│   ├── home.py                 # bridge-owned CODEX_HOME provisioning, sandbox probe
│   ├── gate.py                 # standalone Codex hook: approvals + sentinel + ledger
│   ├── profiles/               # approval rules per call type
│   └── templates/autoresearch.rules
└── tests/                      # offline unit tests (fake codex / fake claude)
```

## Tests

```bash
python3 -m unittest discover -s codex-bridge/tests   # offline: fake codex + fake claude
codex-bridge/bin/codex-bridge selftest               # live: real Codex + claude -p (~30 s)
```
