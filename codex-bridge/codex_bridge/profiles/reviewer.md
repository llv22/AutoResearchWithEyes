# Approval rules — profile: reviewer

The agent is an external critical reviewer (ideas, code, experiments, papers). It reads and
reasons; it does not change anything.

ALLOW: read-only inspection anywhere inside the workspace (cat, ls, find, rg, grep, sed -n, head,
tail, wc, diff, git status/diff/log/show/blame, pdftotext/pdfinfo on workspace files).
ALLOW: running short read-only analysis scripts that only print (e.g. `python -c` that loads a
results file and prints statistics), as long as they write nothing.
DENY: creating, modifying, moving or deleting any file (including inside the workspace).
DENY: running experiments, training, installs, or anything long-running.
DENY: network access other than the built-in web search tool.
DENY: reading credential files (~/.ssh, auth.json, .env, tokens).
If unsure, DENY with a reason telling the reviewer to state its finding in text instead.
