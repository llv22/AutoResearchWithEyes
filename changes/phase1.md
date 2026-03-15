# Phase 1 Setup Guide

How to install and configure AutoResearchWithEyes after the Phase 1 refactoring.

---

## Prerequisites

1. **Claude Code CLI** — installed and authenticated (`claude --version`)
2. **Codex CLI** — installed for cross-model review via MCP (`codex --version`)
3. **LaTeX distribution** — `latexmk` and `pdflatex` available on PATH (e.g., TeX Live or MacTeX)
4. **GPU environment** — accessible for `run-experiment` / `monitor-experiment` skills (SSH or local)

---

## Step 1: Clone and Enter the Project

```bash
git clone https://github.com/llv23/AutoResearchWithEyes.git
cd AutoResearchWithEyes
```

Claude Code auto-discovers components from the project directory:
- **Skills** — loaded from `skills/*/SKILL.md` (10 skills)
- **Commands** — loaded from `commands/*.md` (4 commands)
- **Agents** — referenced by commands from `agents/*.md` (2 agents)

Simply run `claude` from the project directory — no install step needed.

**Alternative usage methods:**

```bash
# Load as plugin from any directory
claude --plugin-dir /path/to/AutoResearchWithEyes

# Or copy skills globally
cp -r skills/* ~/.claude/skills/
cp -r commands/* ~/.claude/commands/
```

---

## Step 2: Configure Codex MCP

The `.mcp.json` at the repo root auto-configures the Codex MCP server (project-level):

```json
{
  "mcpServers": {
    "codex": {
      "command": "codex",
      "args": ["mcp-server"],
      "type": "stdio"
    }
  }
}
```

To also make Codex MCP available globally (user-level), run:

```bash
claude mcp add codex -s user -- codex mcp-server
```

Both project-level and user-level configs can coexist — the project-level `.mcp.json` takes precedence when running from this directory.

Verify Codex MCP is running:

```bash
claude mcp list          # should show "codex" server as ✓ Connected
```

If Codex is not installed, the `research-reviewer` agent and `novelty-check` skill will fail. Install Codex first:

```bash
npm install -g @openai/codex
codex auth login
```

---

## Step 3: Download Venue Templates

Templates are **not bundled** — you must download the official author kit for your target venue.

### ICLR 2026

1. Download the author kit from the ICLR 2026 OpenReview submission page
2. Place `.sty`, `.cls`, and `.bst` files into `templates/iclr2026/`:
   ```
   templates/iclr2026/
   ├── iclr2026_conference.sty
   └── (other style files from the kit)
   ```

### NeurIPS 2026

1. Download from the NeurIPS 2026 submission page
2. Place files into `templates/neurips2026/`

### ICML 2026

1. Download from the ICML 2026 submission page
2. Place files into `templates/icml2026/`

### EMNLP 2026

1. Download the ACL style files from https://github.com/acl-org/acl-style-files or the EMNLP 2026 call for papers
2. Place `acl.sty`, `acl_natbib.bst`, and other style files into `templates/emnlp2026/`:
   ```
   templates/emnlp2026/
   ├── acl.sty
   ├── acl_natbib.bst
   └── (other style files from the kit)
   ```
3. Page limits: 8 pages (long papers) / 4 pages (short papers)

### Custom venue

To add a new venue:
1. Create `templates/<venue-name>/` and add the style files
2. Update `VENUE` in `CLAUDE.md` to `<venue-name>`
3. Add the page limit entry under the **Page Limits** section in `CLAUDE.md`

---

## Step 4: Review and Customize Constants

All configurable values live in `CLAUDE.md` at the repo root. Review and adjust as needed:

| Constant | Default | What it controls |
|----------|---------|------------------|
| `REVIEWER_MODEL` | `gpt-5.4` | Model used via Codex MCP for reviews |
| `PILOT_MAX_HOURS` | `2` | Max hours per pilot idea on GPU |
| `PILOT_TIMEOUT_HOURS` | `3` | Hard timeout for pilot execution |
| `MAX_PILOT_IDEAS` | `3` | Number of ideas piloted in parallel |
| `MAX_TOTAL_GPU_HOURS` | `8` | Total GPU budget across all pilots |
| `MAX_ROUNDS` | `4` | Max review-fix iterations |
| `POSITIVE_THRESHOLD` | `>= 6/10` | Score to pass review |
| `AUTO_PROCEED` | `true` | Auto-proceed at checkpoints (Phase 1 mode) |
| `MAX_IMPROVEMENT_ROUNDS` | `2` | Paper improvement iterations |
| `COMPILER` | `latexmk` | LaTeX build tool |
| `ENGINE` | `pdflatex` | LaTeX engine (`pdflatex` / `xelatex` / `lualatex`) |
| `MAX_COMPILE_ATTEMPTS` | `3` | Retries for compilation errors |
| `VENUE` | `iclr2026` | Target venue (must match a `templates/` subdirectory) |
| `TEMPLATE_DIR` | `templates/` | Base directory for venue templates |

Override any constant per-invocation by passing inline arguments:

```
/autor.idea-discovery "transformer efficiency" -- pilot budget: 4h, max ideas: 5
```

---

## Step 5: Verify Setup

Run these checks to confirm everything works:

### 5.1 Skills and commands are discovered

Launch Claude Code from the project directory and verify skills are available:

```bash
cd /path/to/AutoResearchWithEyes
claude
# Skills from skills/ and commands from commands/ are auto-discovered
# Try typing /idea- and tab-complete to confirm /autor.idea-discovery is available
```

### 5.2 Codex MCP responds

In a Claude Code session, verify the Codex MCP server is connected (auto-configured from `.mcp.json`).

### 5.3 Template resolution

In a Claude Code session:

```
/paper-compile
# Should resolve templates from templates/iclr2026/ (or show clear error
# with download instructions if style files are missing)
```

### 5.4 Dry-run a command

```
/autor.idea-discovery "test topic"
# Should chain: research-lit → idea-creator → novelty-check → research-reviewer
```

---

## Architecture Overview

After Phase 1, the project is organized as:

```
AutoResearchWithEyes/
├── CLAUDE.md                    # Centralized constants (single source of truth)
├── .mcp.json                    # Auto-configures Codex MCP server
├── skills/                      # 10 building-block skills (auto-discovered by Claude Code)
│   ├── research-lit/
│   ├── idea-creator/
│   ├── novelty-check/
│   ├── run-experiment/
│   ├── monitor-experiment/
│   ├── analyze-results/
│   ├── paper-plan/
│   ├── paper-figure/
│   ├── paper-write/
│   └── paper-compile/
├── commands/                    # 4 workflow orchestrators
│   ├── idea-discovery.md        # research-lit → idea-creator → novelty-check → reviewer
│   ├── auto-review-loop.md      # review → fix → re-review (×4 rounds max)
│   ├── paper-writing.md         # plan → figures → write → compile → improver
│   └── research-pipeline.md     # meta-pipeline (idea → implement → review)
├── agents/                      # 2 specialized agent personas
│   ├── research-reviewer.md     # Senior ML reviewer via Codex MCP
│   └── paper-improver.md        # 2-round auto-improvement loop
├── templates/                   # Venue-specific LaTeX style files
│   ├── iclr2026/
│   ├── neurips2026/
│   ├── icml2026/
│   └── emnlp2026/
└── changes/                     # Planning and discussion docs
```

### Key design principles

- **Skills** are atomic building blocks — each does one thing
- **Commands** orchestrate skills and agents into end-to-end workflows
- **Agents** are specialized personas with dedicated review/improvement logic
- **CLAUDE.md** is the single source of truth for all configurable constants
- **Template resolution** follows a fallback chain: `TEMPLATE_DIR/VENUE/` → bundled → error with instructions

---

## What's Next (Phase 2)

Phase 2 adds human involvement and optional integrations:
- Slack notifications at key pipeline stages
- Configurable human checkpoints (`AUTO_PROCEED=false`)
- Zotero/Obsidian MCP as optional data source fallbacks

See `changes/PLAN.md` Tasks 10–13 for details.
