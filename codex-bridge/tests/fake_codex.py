#!/usr/bin/env python3
"""Stand-in for the `codex` binary used by the unit tests.

Behaviour is driven by env vars:
  FAKE_CODEX_LOG      append {"argv", "stdin", "codex_home"} per invocation
  FAKE_CODEX_VERSION  version string for `--version` (default 0.160.0)
  FAKE_CODEX_NO_HOOK  if set, do not write the SessionStart sentinel
  FAKE_CODEX_REJECT   if set, print a built-in execpolicy rejection for this command on stderr
"""
import json
import os
import sys

argv = sys.argv[1:]
if argv[:1] == ["--version"]:
    print(f"codex-cli {os.environ.get('FAKE_CODEX_VERSION', '0.160.0')}")
    sys.exit(0)
if argv[:1] == ["sandbox"]:
    sys.exit(0)

prompt = sys.stdin.read()
if os.environ.get("FAKE_CODEX_LOG"):
    with open(os.environ["FAKE_CODEX_LOG"], "a") as f:
        f.write(json.dumps({"argv": argv, "stdin": prompt, "codex_home": os.environ.get("CODEX_HOME")}) + "\n")

# resume: the thread id is the positional just before the trailing "-" (prompt on stdin)
thread = argv[-2] if "resume" in argv else "thread-new-1"

if not os.environ.get("FAKE_CODEX_NO_HOOK"):
    with open(os.environ["CODEX_BRIDGE_LEDGER"], "a") as f:
        f.write(json.dumps({"event": "session_start", "threadId": thread}) + "\n")
if os.environ.get("FAKE_CODEX_REJECT"):
    cmd = os.environ["FAKE_CODEX_REJECT"]
    sys.stderr.write(f'ERROR exec_command failed: CreateProcess {{ message: "Rejected(\\"`{cmd}` '
                     f'rejected: rm -f style commands are not permitted. Use a safer approach\\")" }}\n')

out = argv[argv.index("-o") + 1]
with open(out, "w") as f:
    f.write(f"echo: {prompt.strip()}")
print(json.dumps({"type": "thread.started", "thread_id": thread}))
print(json.dumps({"type": "turn.completed"}))
