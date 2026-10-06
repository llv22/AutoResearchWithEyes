"""Backends: map the stable call contract onto the interface the installed Codex ships.

The contract mirrors the 12 params of the retired `codex mcp-server` tools (`codex` /
`codex-reply`) and returns the same `{threadId, content}`. When Codex changes again, edit
CONFIG_KEYS or add a backend to BACKENDS — callers never change.
"""
import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .home import BridgeError, sandbox_works

# Contract param -> `codex exec -c` key. Version-specific renames live here (one row each).
CONFIG_KEYS = {
    "developer_instructions": "developer_instructions",
    "base_instructions": "instructions",      # `base_instructions` is an unknown key in 0.160
    "compact_prompt": "compact_prompt",
    "approval_policy": "approval_policy",
}
# Sandbox chosen for `--sandbox auto`: (sandbox works, sandbox broken -> gate is the only guard)
AUTO_SANDBOX = {"reviewer": ("read-only", "danger-full-access"),
                "experiment": ("workspace-write", "danger-full-access")}
REJECTED = re.compile(r'Rejected\(\\?"`(?P<cmd>.*?)` rejected: (?P<reason>.*?)\\?"\)')


@dataclass
class Call:
    prompt: str
    out: Path
    thread_id: str | None = None          # None => new thread (`codex`), else `codex-reply`
    model: str | None = None
    effort: str | None = None
    sandbox: str = "auto"
    cwd: str | None = None
    profile: str = "reviewer"
    web: bool = False
    config: list[str] = field(default_factory=list)       # raw `key=TOML` overrides
    developer_instructions: str | None = None
    base_instructions: str | None = None
    compact_prompt: str | None = None
    approval_policy: str | None = None


def toml_value(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    return json.dumps(v)  # strings and string lists: JSON escapes are valid TOML


def flatten_config(obj, prefix=""):
    """{"tools": {"web_search": true}} -> ["tools.web_search=true"] (MCP `config` param)."""
    out = []
    for k, v in obj.items():
        key = f"{prefix}{k}"
        out += flatten_config(v, key + ".") if isinstance(v, dict) else [f"{key}={toml_value(v)}"]
    return out


def parse_version(text):
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", text or "")
    if not m:
        raise BridgeError(f"cannot parse Codex version from {text!r}")
    return tuple(int(x) for x in m.groups())


class ExecBackend:
    """`codex exec` / `codex exec resume` (Codex >= 0.154, where `mcp-server` was removed)."""
    name = "exec"
    min_version = (0, 154, 0)

    def __init__(self, codex="codex"):
        self.codex = codex

    def version(self):
        try:
            out = subprocess.run([self.codex, "--version"], capture_output=True, text=True, timeout=30)
        except OSError as e:
            raise BridgeError(f"codex not found ({e}); install with `npm i -g @openai/codex`")
        v = parse_version(out.stdout)
        if v < self.min_version:
            raise BridgeError(f"Codex {'.'.join(map(str, v))} is too old for the exec backend "
                              f"(need >= {'.'.join(map(str, self.min_version))}); run `codex update`")
        return ".".join(map(str, v))

    def argv(self, call: Call, sandbox: str):
        overrides = [f"sandbox_mode={toml_value(sandbox)}"]
        if call.effort:
            overrides.append(f"model_reasoning_effort={toml_value(call.effort)}")
        if call.web:
            overrides.append("tools.web_search=true")
        for param, key in CONFIG_KEYS.items():
            if getattr(call, param) is not None:
                overrides.append(f"{key}={toml_value(getattr(call, param))}")
        overrides += call.config

        head = [self.codex, "exec"] + (["resume"] if call.thread_id else [])
        args = ["--json", "--strict-config", "--skip-git-repo-check",
                "--dangerously-bypass-hook-trust",  # only the bridge-owned hooks.json (see run())
                "-o", str(call.out / "reply.md")]
        if call.model:
            args += ["-m", call.model]
        if call.cwd and not call.thread_id:
            args += ["-C", call.cwd]
        for o in overrides:
            args += ["-c", o]
        tail = ([call.thread_id] if call.thread_id else []) + ["-"]   # prompt on stdin
        return head + args + tail

    def run(self, call: Call, home: Path):
        version = self.version()
        cwd = Path(call.cwd or os.getcwd())
        if (cwd / ".codex" / "hooks.json").exists():
            raise BridgeError(f"{cwd}/.codex/hooks.json exists; the bridge bypasses hook trust, so it "
                              "refuses to run where project hooks would also be trusted")
        sandbox = call.sandbox
        if sandbox == "auto":
            ok, broken = AUTO_SANDBOX[call.profile]
            sandbox = ok if sandbox_works(home, self.codex, version) else broken

        call.out.mkdir(parents=True, exist_ok=True)
        (call.out / "reply.md").unlink(missing_ok=True)
        ledger = call.out / "approvals.jsonl"
        env = {**os.environ, "CODEX_HOME": str(home), "CODEX_BRIDGE_LEDGER": str(ledger),
               "CODEX_BRIDGE_RULES": str(Path(__file__).parent / "profiles" / f"{call.profile}.md")}
        with open(call.out / "events.jsonl", "w") as ev, open(call.out / "codex.stderr.log", "w") as er:
            proc = subprocess.run(self.argv(call, sandbox), input=call.prompt, text=True,
                                  stdout=ev, stderr=er, cwd=cwd, env=env)

        events = [json.loads(l) for l in (call.out / "events.jsonl").read_text().splitlines() if l.strip()]
        thread = next((e.get("thread_id") for e in events if e.get("type") == "thread.started"), None)
        errors = [e.get("message") or json.dumps(e.get("error")) for e in events
                  if e.get("type") in ("error", "turn.failed")]
        self._log_policy_rejections(call.out / "codex.stderr.log", ledger, thread)

        if proc.returncode != 0 or errors or not thread:
            raise BridgeError(f"codex exited {proc.returncode}: {'; '.join(errors) or 'no thread started'} "
                              f"(see {call.out}/codex.stderr.log)")
        if not self._sentinel_seen(ledger, thread):
            raise BridgeError("approval hooks did not run for this thread (hook trust or hooks.json "
                              "not loaded); result discarded")
        reply = call.out / "reply.md"
        if not reply.exists():
            raise BridgeError("codex produced no final message")
        return {"threadId": thread, "content": reply.read_text(), "sandbox": sandbox,
                "codexVersion": version, "backend": self.name}

    @staticmethod
    def _sentinel_seen(ledger: Path, thread):
        if not ledger.exists():
            return False
        return any(e.get("event") == "session_start" and e.get("threadId") == thread
                   for e in map(json.loads, ledger.read_text().splitlines()))

    @staticmethod
    def _log_policy_rejections(stderr_log: Path, ledger: Path, thread):
        """Codex's built-in execpolicy rejections only show up in stderr; make them traceable."""
        seen = set()
        with open(ledger, "a") as f:
            for m in REJECTED.finditer(stderr_log.read_text()):
                if m["cmd"] in seen:
                    continue
                seen.add(m["cmd"])
                f.write(json.dumps({"event": "tool", "threadId": thread, "command": m["cmd"],
                                    "decision": "deny", "decided_by": "codex_policy",
                                    "reason": m["reason"]}) + "\n")


BACKENDS = {"exec": ExecBackend}


def get_backend(name=None):
    name = name or os.environ.get("CODEX_BRIDGE_BACKEND", "exec")
    if name not in BACKENDS:
        raise BridgeError(f"unknown backend {name!r}; available: {', '.join(BACKENDS)}")
    return BACKENDS[name](os.environ.get("CODEX_BRIDGE_CODEX", "codex"))
