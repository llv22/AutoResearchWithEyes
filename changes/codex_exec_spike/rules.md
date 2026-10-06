# AutoResearch approval rules (profile: experiment)
ALLOW: read-only inspection (cat, ls, rg, grep, sed -n, head, tail, git status/diff/log/show, nvidia-smi, pwd, echo).
ALLOW: running experiment code inside the workspace (python/bash scripts under the workspace, pip list).
ALLOW: writing or deleting files INSIDE the workspace (cwd) only.
DENY: deleting or modifying anything outside the workspace; rm -rf on absolute paths outside cwd.
DENY: git push, git reset --hard, git clean, force operations, rewriting history.
DENY: sending local files or secrets over the network (curl/wget uploads, scp), reading credential files (~/.ssh, auth.json, .env).
DENY: installing system packages (sudo, apt), changing shell profiles or global config.
If unsure, DENY with a reason that tells the agent what it may do instead.
