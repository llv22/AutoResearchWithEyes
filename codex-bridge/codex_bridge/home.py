"""Bridge-owned CODEX_HOME, regenerated on every call. The user's ~/.codex is never modified.

Layout:
  config.toml                 managed defaults (model, effort, approval_policy)
  auth.json  -> <user CODEX_HOME>/auth.json   (symlink: shared login + token refresh)
  hooks.json                  SessionStart + PreToolUse -> gate.py
  rules/autoresearch.rules    execpolicy overrides for prefixes the gate judges
  sandbox_probe.json          cached `codex sandbox -- true` result per Codex version
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parent
DEFAULT_MODEL = "gpt-5.6-sol"   # REVIEWER_MODEL in the plugin's CLAUDE.md
DEFAULT_EFFORT = "xhigh"


class BridgeError(RuntimeError):
    pass


def bridge_home() -> Path:
    if os.environ.get("CODEX_BRIDGE_HOME"):
        return Path(os.environ["CODEX_BRIDGE_HOME"]).expanduser()
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return Path(base) / "autoresearch" / "codex-home"


def user_codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or "~/.codex").expanduser()


def provision(home: Path) -> Path:
    (home / "rules").mkdir(parents=True, exist_ok=True)

    auth, link = user_codex_home() / "auth.json", home / "auth.json"
    if user_codex_home().resolve() != home.resolve():
        if not auth.exists():
            raise BridgeError(f"no Codex login at {auth} — run `codex login` first")
        if not (link.is_symlink() and os.readlink(link) == str(auth)):
            link.unlink(missing_ok=True)
            link.symlink_to(auth)

    (home / "config.toml").write_text(
        "# Managed by codex-bridge — regenerated on every call; do not edit.\n"
        f'model = "{DEFAULT_MODEL}"\n'
        f'model_reasoning_effort = "{DEFAULT_EFFORT}"\n'
        'approval_policy = "never"\n')
    shutil.copyfile(PKG / "templates" / "autoresearch.rules", home / "rules" / "autoresearch.rules")

    gate = f"{sys.executable} {PKG / 'gate.py'}"
    (home / "hooks.json").write_text(json.dumps({"hooks": {
        "SessionStart": [{"hooks": [{"type": "command", "command": gate, "timeout": 10}]}],
        "PreToolUse": [{"matcher": ".*", "hooks": [{"type": "command", "command": gate, "timeout": 90}]}],
    }}, indent=2) + "\n")
    return home


def sandbox_works(home: Path, codex: str, version: str) -> bool:
    """Whether Codex's OS sandbox can run commands on this machine (cached per Codex version)."""
    cache = home / "sandbox_probe.json"
    try:
        data = json.loads(cache.read_text())
        if data.get("version") == version:
            return data["works"]
    except (OSError, ValueError, KeyError):
        pass
    try:
        works = subprocess.run([codex, "sandbox", "--", "true"], capture_output=True,
                               timeout=30, env={**os.environ, "CODEX_HOME": str(home)}).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        works = False
    cache.write_text(json.dumps({"version": version, "works": works}) + "\n")
    return works
