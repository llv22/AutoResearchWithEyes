"""codex-bridge CLI.

  codex-bridge new   --out DIR [--detach] [options] < prompt.md    start a reviewer thread
  codex-bridge reply --thread ID --out DIR [--detach] [options] < prompt.md   continue it
  codex-bridge wait  --out DIR [--timeout S]           result of a --detach call
  codex-bridge approvals DIR                            summarize approvals.jsonl under DIR
  codex-bridge setup                                    provision the bridge-owned CODEX_HOME
  codex-bridge selftest                                 parity checks against the installed Codex

new/reply print one JSON object on stdout: {"threadId", "content", "outDir", ...} and write
DIR/reply.md, DIR/events.jsonl, DIR/approvals.jsonl, DIR/meta.json, DIR/result.json. Errors:
JSON {"error"} on stdout, exit 1.

--detach runs the call in its own process session (it survives the caller exiting, e.g. a
headless `claude -p` run or a context compaction) and returns {"status": "running"} at once;
`wait` then blocks up to --timeout seconds and prints the same JSON as a direct call, or
{"status": "running"} with exit 3 if it is still going (just run `wait` again).
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict
from pathlib import Path

from . import CODEX_TESTED_VERSION, __version__
from .backends import Call, flatten_config, get_backend
from .home import BridgeError, bridge_home, provision


def add_call_args(p, reply):
    p.add_argument("--out", required=True, type=Path, help="output dir for this call")
    p.add_argument("--profile", choices=["reviewer", "experiment"], default="reviewer",
                   help="approval rules for commands Codex runs (default: reviewer)")
    p.add_argument("--model", help="default: gpt-5.6-sol (REVIEWER_MODEL)")
    p.add_argument("--effort", help="model_reasoning_effort (default: xhigh)")
    p.add_argument("--web", action="store_true", help="enable the web search tool")
    p.add_argument("--sandbox", default="auto",
                   choices=["auto", "read-only", "workspace-write", "danger-full-access"])
    p.add_argument("--config", action="append", default=[], metavar="KEY=TOML",
                   help="raw codex config override (repeatable)")
    p.add_argument("--config-json", help='MCP-style config object, e.g. \'{"tools":{"web_search":true}}\'')
    p.add_argument("--developer-instructions")
    p.add_argument("--base-instructions")
    p.add_argument("--compact-prompt")
    p.add_argument("--approval-policy")
    p.add_argument("--prompt-file", type=Path, help="read the prompt from a file instead of stdin")
    p.add_argument("--detach", action="store_true", help="run in the background; collect with `wait`")
    if reply:
        g = p.add_mutually_exclusive_group(required=True)
        g.add_argument("--thread", help="threadId returned by `new`")
        g.add_argument("--conversation-id", dest="thread", help=argparse.SUPPRESS)  # MCP alias
    else:
        p.add_argument("--cwd", help="working directory for the session")


def build_call(a, reply):
    prompt = a.prompt_file.read_text() if a.prompt_file else sys.stdin.read()
    if not prompt.strip():
        raise BridgeError("empty prompt (pass it on stdin or --prompt-file)")
    config = list(a.config) + (flatten_config(json.loads(a.config_json)) if a.config_json else [])
    return Call(prompt=prompt, out=a.out.resolve(), thread_id=a.thread if reply else None,
                model=a.model, effort=a.effort, sandbox=a.sandbox, cwd=None if reply else a.cwd,
                profile=a.profile, web=a.web, config=config,
                developer_instructions=a.developer_instructions, base_instructions=a.base_instructions,
                compact_prompt=a.compact_prompt, approval_policy=a.approval_policy)


def run_call(call):
    started = time.time()
    result = get_backend().run(call, provision(bridge_home()))
    meta = {**{k: v for k, v in result.items() if k != "content"}, "profile": call.profile,
            "model": call.model or "default", "effort": call.effort or "default",
            "started": round(started, 3), "seconds": round(time.time() - started, 1)}
    (call.out / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    return {**result, "outDir": str(call.out)}


RESULT = "result.json"
RUNNING = 3  # exit code: detached call still running


def write_result(out: Path, obj):
    tmp = out / (RESULT + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2) + "\n")
    os.replace(tmp, out / RESULT)  # atomic: `wait` may read concurrently


def detach(call):
    call.out.mkdir(parents=True, exist_ok=True)
    (call.out / RESULT).unlink(missing_ok=True)
    (call.out / "call.json").write_text(json.dumps({**asdict(call), "out": str(call.out)}))
    root = str(Path(__file__).resolve().parents[1])
    env = {**os.environ, "PYTHONPATH": root + os.pathsep + os.environ.get("PYTHONPATH", "")}
    with open(call.out / "bridge.log", "w") as log:
        proc = subprocess.Popen([sys.executable, "-m", "codex_bridge", "_run", str(call.out)],
                                stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                start_new_session=True, env=env)
    (call.out / "pid").write_text(str(proc.pid))
    return {"status": "running", "outDir": str(call.out), "pid": proc.pid}


def run_detached(out: Path):
    spec = json.loads((out / "call.json").read_text())
    try:
        res = run_call(Call(**{**spec, "out": Path(spec["out"])}))
    except Exception as e:  # always leave a result for `wait`
        res = {"error": str(e) if isinstance(e, BridgeError) else f"{type(e).__name__}: {e}"}
    write_result(out, res)


def alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def wait(out: Path, timeout):
    out = out.resolve()
    deadline = time.time() + timeout
    while True:
        if (out / RESULT).exists():
            return json.loads((out / RESULT).read_text())
        if not (out / "pid").exists():
            return {"error": f"no codex-bridge call in {out}"}
        pid = int((out / "pid").read_text())
        if not alive(pid) and not (out / RESULT).exists():
            return {"error": f"bridge process {pid} exited without a result (see {out}/bridge.log)"}
        if time.time() >= deadline:
            return {"status": "running", "outDir": str(out), "pid": pid}
        time.sleep(1)


def summarize(root: Path):
    rows = [json.loads(l) for f in sorted(root.rglob("approvals.jsonl"))
            for l in f.read_text().splitlines() if l.strip()]
    tools = [r for r in rows if r.get("event") == "tool"]
    by = {}
    for r in tools:
        by[f"{r['decision']}:{r['decided_by']}"] = by.get(f"{r['decision']}:{r['decided_by']}", 0) + 1
    return {"calls": len(tools), "counts": by,
            "denied": [{k: r.get(k) for k in ("threadId", "command", "decided_by", "reason")}
                       for r in tools if r["decision"] == "deny"]}


def selftest():
    """Parity checks from changes/CODEX_EXEC.md §3.1 against the installed Codex (costs a few calls)."""
    checks = []

    def check(name, fn):
        try:
            detail = fn()
            checks.append({"check": name, "ok": True, "detail": detail})
        except Exception as e:
            checks.append({"check": name, "ok": False, "detail": f"{type(e).__name__}: {e}"})
        print(("PASS " if checks[-1]["ok"] else "FAIL ") + name, file=sys.stderr)
        return checks[-1]["ok"]

    tmp = Path(tempfile.mkdtemp(prefix="codex-bridge-selftest-"))
    st = {}
    low = dict(effort="low")
    check("codex version", lambda: get_backend().version())
    check("provision bridge CODEX_HOME", lambda: str(provision(bridge_home())))

    def new():
        st["r"] = run_call(Call(prompt="Remember the code word KIWI-7. Reply only: OK", out=tmp / "new",
                                cwd=str(tmp), **low))
        return st["r"]["threadId"]

    def reply():
        r = run_call(Call(prompt="What was the code word? Reply only the word.", out=tmp / "reply",
                          thread_id=st["r"]["threadId"], cwd=str(tmp), **low))
        assert "KIWI-7" in r["content"], r["content"]
        return r["content"].strip()

    def instructions():
        r = run_call(Call(prompt="Say hello.", out=tmp / "instr", cwd=str(tmp),
                          developer_instructions="Always answer with the single word ZEBRA.", **low))
        assert "ZEBRA" in r["content"], r["content"]
        return "developer_instructions honoured"

    def web():
        r = run_call(Call(prompt="Use web search once to find the current stable Python version. One line.",
                          out=tmp / "web", web=True, cwd=str(tmp), **low))
        events = (tmp / "web" / "events.jsonl").read_text()
        assert '"web_search"' in events, "no web_search event"
        return r["content"].strip()[:80]

    def gate():
        run_call(Call(prompt="Run exactly 'git push origin main' and report whether it ran.",
                      out=tmp / "gate", profile="experiment", cwd=str(tmp), **low))
        s = summarize(tmp / "gate")
        assert any(d["command"].startswith("git push") for d in s["denied"]), s
        return s["counts"]

    if check("new thread", new):
        check("reply keeps memory", reply)
    check("developer instructions", instructions)
    check("web search", web)
    check("approval gate denies + ledger", gate)
    ok = all(c["ok"] for c in checks)
    return {"ok": ok, "codexTestedVersion": CODEX_TESTED_VERSION, "dir": str(tmp), "checks": checks}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="codex-bridge", description=__doc__.split("\n\n")[0])
    ap.add_argument("--version", action="version", version=f"codex-bridge {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)
    add_call_args(sub.add_parser("new", help="start a thread"), reply=False)
    add_call_args(sub.add_parser("reply", help="continue a thread"), reply=True)
    w = sub.add_parser("wait", help="wait for a --detach call")
    w.add_argument("--out", required=True, type=Path)
    w.add_argument("--timeout", type=float, default=540, help="seconds (default 540, under Bash's 10 min)")
    sub.add_parser("_run").add_argument("dir", type=Path)  # internal: detached worker
    sub.add_parser("approvals", help="summarize approval ledgers").add_argument("dir", type=Path)
    sub.add_parser("setup", help="provision the bridge-owned CODEX_HOME")
    sub.add_parser("selftest", help="run parity checks against the installed Codex")
    a = ap.parse_args(argv)
    try:
        if a.cmd in ("new", "reply"):
            call = build_call(a, reply=a.cmd == "reply")
            if a.detach:
                out = detach(call)
            else:
                try:
                    out = run_call(call)
                except BridgeError as e:
                    if call.out.exists():
                        write_result(call.out, {"error": str(e)})
                    raise
                write_result(call.out, out)
        elif a.cmd == "_run":
            run_detached(a.dir.resolve())
            return 0
        elif a.cmd == "wait":
            out = wait(a.out, a.timeout)
        elif a.cmd == "approvals":
            out = summarize(a.dir)
        elif a.cmd == "setup":
            out = {"home": str(provision(bridge_home())), "codexVersion": get_backend().version()}
        else:
            out = selftest()
    except BridgeError as e:
        print(json.dumps({"error": str(e)}))
        return 1
    print(json.dumps(out, indent=2))
    if "error" in out:
        return 1
    if out.get("status") == "running" and a.cmd == "wait":
        return RUNNING
    return 0 if out.get("ok", True) else 1
