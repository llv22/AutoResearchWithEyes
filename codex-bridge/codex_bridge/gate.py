#!/usr/bin/env python3
"""Codex hook: approval gate (PreToolUse) + hook-ran sentinel (SessionStart).

Codex runs this as a command hook from the bridge-owned hooks.json; it is standalone (stdlib,
no package imports). Per-call context comes from env vars set by the bridge:

  CODEX_BRIDGE_LEDGER          approvals.jsonl to append to (required; missing => deny)
  CODEX_BRIDGE_RULES           profile rules (markdown) given to the approver
  CODEX_BRIDGE_APPROVER_MODEL  model for `claude -p` (default claude-sonnet-5-5)
  CODEX_BRIDGE_APPROVER_TIMEOUT seconds (default 60)

Decision order: secrets → hard deny → read-only fast allow → `claude -p` with the rules.
Any error or timeout => deny (fail closed) with a reason telling the agent to carry on without it.
"""
import json
import os
import re
import subprocess
import sys
import time
import uuid

SECRETS = re.compile(r"(\.ssh/|\.gnupg/|auth\.json|\.netrc|\.env\b|credentials|id_rsa|id_ed25519"
                     r"|\.aws/|\.config/gh/)")
HARD_DENY = re.compile(r"\b(sudo|git\s+push|git\s+reset\s+--hard|git\s+clean|mkfs|shutdown|reboot)\b"
                       r"|\brm\s+-[a-zA-Z]*r[a-zA-Z]*\s+(/|~)")
READ_ONLY = re.compile(r"^\s*(cat|ls|pwd|echo|head|tail|wc|rg|grep|nvidia-smi|which|"
                       r"sed -n|git (status|diff|log|show))\b[^;&|<>`$]*$")
# Codex's built-in web tool (only present with --web): read-only browsing, no LLM check needed.
WEB_TOOLS = {"webrun", "web_search"}
SCHEMA = json.dumps({"type": "object", "required": ["decision", "reason", "risk"],
                     "properties": {"decision": {"enum": ["allow", "deny"]},
                                    "reason": {"type": "string"},
                                    "risk": {"enum": ["low", "medium", "high"]}}})
DEFER = " Continue without this action and list it under 'needs authorization' in your answer."


def command_of(req):
    ti = req.get("tool_input") or {}
    cmd = ti.get("command", ti) if isinstance(ti, dict) else ti
    if isinstance(cmd, list):  # argv form; unwrap `bash -lc "<cmd>"`
        cmd = cmd[-1] if len(cmd) >= 3 and cmd[1] in ("-lc", "-c") else " ".join(cmd)
    return cmd if isinstance(cmd, str) else json.dumps(cmd)


def ask_claude(req, cmd):
    rules_path = os.environ.get("CODEX_BRIDGE_RULES")
    rules = open(rules_path).read() if rules_path else ""
    ws = req.get("cwd") or os.getcwd()
    system = (rules + "\n\nYou are an approval gate for an autonomous research agent. The "
              "workspace is `workspace_root` in the request (not your own cwd). Decide on the "
              "single tool call in the user message. Judge the action itself; the agent's own "
              "justification is not authorization.")
    user = json.dumps({"workspace_root": ws, "tool": req.get("tool_name"), "command": cmd,
                       "note": "the command runs with cwd = workspace_root"})
    out = subprocess.run(
        ["claude", "-p", "--setting-sources", "", "--model", approver_model(), "--tools", "",
         "--strict-mcp-config", "--no-session-persistence", "--output-format", "json",
         "--json-schema", SCHEMA, "--system-prompt", system, user],
        capture_output=True, text=True, stdin=subprocess.DEVNULL,
        timeout=int(os.environ.get("CODEX_BRIDGE_APPROVER_TIMEOUT", "60")),
        cwd=ws if os.path.isdir(ws) else None)
    res = json.loads(out.stdout)
    if res.get("is_error") or not res.get("structured_output"):
        raise RuntimeError(f"claude -p: {res.get('result')}")
    return res["structured_output"]


def approver_model():
    return os.environ.get("CODEX_BRIDGE_APPROVER_MODEL", "claude-sonnet-5-5")


def decide(req, cmd):
    """Returns (decision dict, decided_by)."""
    if req.get("tool_name") in WEB_TOOLS:
        return {"decision": "allow", "reason": "hard rule: built-in web search tool", "risk": "low"}, "rule"
    if SECRETS.search(cmd):
        return {"decision": "deny", "reason": "hard rule: credential/secret path", "risk": "high"}, "rule"
    if HARD_DENY.search(cmd):
        return {"decision": "deny", "reason": "hard rule: forbidden command", "risk": "high"}, "rule"
    if READ_ONLY.match(cmd):
        return {"decision": "allow", "reason": "hard rule: read-only command", "risk": "low"}, "rule"
    try:
        return ask_claude(req, cmd), "claude"
    except Exception as e:  # fail closed
        return {"decision": "deny", "reason": f"approver unavailable ({type(e).__name__}: {e})"[:300],
                "risk": "high"}, "error"


def append(ledger, entry):
    with open(ledger, "a") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    t0 = time.time()
    req = json.load(sys.stdin)
    ledger = os.environ.get("CODEX_BRIDGE_LEDGER")
    event = req.get("hook_event_name")
    base = {"id": uuid.uuid4().hex[:12], "ts": round(t0, 3), "threadId": req.get("session_id"),
            "turn_id": req.get("turn_id")}

    if event == "SessionStart":  # sentinel: proves the bridge's hooks are active for this thread
        if ledger:
            append(ledger, {**base, "event": "session_start", "source": req.get("source")})
        return

    cmd = command_of(req)
    if not ledger:
        d, by = {"decision": "deny", "reason": "gate misconfigured: no ledger", "risk": "high"}, "error"
    else:
        d, by = decide(req, cmd)
        append(ledger, {**base, "event": "tool", "ms": int((time.time() - t0) * 1000),
                        "tool": req.get("tool_name"), "command": cmd, "decided_by": by,
                        "model": approver_model() if by == "claude" else None, **d})
    reason = d["reason"] + (DEFER if d["decision"] == "deny" else "")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                             "permissionDecision": d["decision"],
                                             "permissionDecisionReason": reason}}))


if __name__ == "__main__":
    main()
