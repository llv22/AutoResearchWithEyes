# AutoResearchWithEyes

> **Let Claude Code do research while you sleep.** Wake up to find your paper scored, weaknesses identified, experiments run, and narrative rewritten — autonomously.

[![Featured in awesome-agent-skills](https://img.shields.io/badge/Featured%20in-awesome--agent--skills-blue?style=flat&logo=github)](https://github.com/VoltAgent/awesome-agent-skills) · [Join Community](#-community)

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) plugin for autonomous ML research workflows. Orchestrates **cross-model collaboration** — Claude Code drives the research while an external LLM (via [Codex MCP](https://github.com/openai/codex)) acts as a critical reviewer. Also supports [alternative model combinations](#-alternative-model-combinations) (e.g., GLM + GPT, GLM + MiniMax) — no Claude API required.

> **Why cross-model?** A single model reviewing its own output creates blind spots. Two complementary models — Claude Code for fast execution, GPT-5.4 xhigh for rigorous critique — produce better outcomes than either alone. Going from 1 to 2 models is the biggest gain; adding more gives diminishing returns.

---

## Quick Start

```bash
# 1. Clone and enter the project
git clone https://github.com/llv23/AutoResearchWithEyes.git
cd AutoResearchWithEyes

# 2. Set up Codex MCP (for cross-model review)
npm install -g @openai/codex
codex auth login
# Codex MCP auto-configures from .mcp.json when running in the project directory

# 3. Launch Claude Code — skills and commands are auto-discovered
claude
> /autor.idea-discovery "your research direction"      # Command: literature → brainstorm → validate
> /autor.auto-review-loop                              # Command: review → fix → re-review overnight
> /autor.paper-writing "NARRATIVE_REPORT.md"           # Command: narrative → polished PDF
> /autor.research-pipeline "your research direction"   # Command: full end-to-end pipeline
```

See [Setup](#%EF%B8%8F-setup) for full details.

## Features

- **10 composable skills** — atomic building blocks: literature search, idea generation, novelty check, experiments, paper writing
- **4 workflow commands** — orchestrate skills + agents into end-to-end pipelines (`/autor.idea-discovery`, `/autor.auto-review-loop`, `/autor.paper-writing`, `/autor.research-pipeline`)
- **2 specialized agents** — `research-reviewer` (senior ML reviewer via Codex MCP) and `paper-improver` (2-round auto-improvement)
- **Cross-model collaboration** — Claude Code executes, GPT-5.4 xhigh reviews. Adversarial, not self-play
- **Centralized configuration** — all constants in `CLAUDE.md`, override per-invocation with inline arguments
- **Venue templates** — bundled template directories with fallback resolution: `TEMPLATE_DIR/VENUE/` → bundled → error with instructions
- **GPU deployment** — auto rsync, screen sessions, multi-GPU parallel experiments, live monitoring
- **Flexible models** — default Claude x GPT-5.4, also supports [GLM + GPT, GLM + MiniMax](#-alternative-model-combinations)

---

## Architecture

```
AutoResearchWithEyes/
├── CLAUDE.md                    # Centralized constants (single source of truth)
├── .mcp.json                    # Auto-configures Codex MCP server
├── .claude-plugin/
│   └── plugin.json              # Plugin metadata (name, version, author)
├── skills/                      # 10 atomic building blocks (auto-discovered)
│   ├── research-lit/            # Literature search (arXiv TeX, local PDFs, web)
│   ├── idea-creator/            # Brainstorm 8-12 ideas, rank by feasibility
│   ├── novelty-check/           # Verify novelty against recent literature
│   ├── run-experiment/          # Deploy to local/remote GPU
│   ├── monitor-experiment/      # Check progress, collect results
│   ├── analyze-results/         # Statistics, insights, comparison tables
│   ├── paper-plan/              # Claims-evidence matrix, section outline
│   ├── paper-figure/            # Publication-quality plots from data
│   ├── paper-write/             # Section-by-section LaTeX generation
│   └── paper-compile/           # Compile PDF, auto-fix errors, page check
├── commands/                    # 4 workflow orchestrators (user-invoked)
│   ├── idea-discovery.md        # research-lit → idea-creator → novelty-check → reviewer
│   ├── auto-review-loop.md      # review → fix → re-review (×4 rounds max)
│   ├── paper-writing.md         # plan → figures → write → compile → improver
│   └── research-pipeline.md     # meta-pipeline: idea → implement → review
├── agents/                      # 2 specialized personas
│   ├── research-reviewer.md     # Senior ML reviewer via Codex MCP (GPT-5.4 xhigh)
│   └── paper-improver.md        # 2-round auto-improvement loop
└── templates/                   # Venue-specific LaTeX style files
    ├── iclr2026/
    ├── neurips2026/
    └── icml2026/
```

### Design principles

- **Skills** are atomic — each does one thing well
- **Commands** orchestrate skills and agents into end-to-end workflows
- **Agents** are specialized personas with dedicated review/improvement logic
- **CLAUDE.md** is the single source of truth for all configurable constants
- **Templates** resolve via a fallback chain: user config → bundled → error with download instructions

---

## Workflows

These commands compose skills + agents into a full research lifecycle. Use independently or chain together:

- **Exploring a new area?** Start with `/autor.idea-discovery`
- **Already have an idea + code?** Jump to `/autor.auto-review-loop`
- **Ready to write?** Use `/autor.paper-writing`
- **Full pipeline?** `/autor.research-pipeline` — from literature survey to submission

> **Important:** These tools accelerate research, but they don't replace your own critical thinking. Always review generated ideas with your domain expertise.

### Full Pipeline

```
/research-lit → /idea-creator → /novelty-check → implement → /run-experiment → /autor.auto-review-loop → /paper-plan → /paper-figure → /paper-write → /paper-compile → submit
  (survey)      (brainstorm)    (verify novel)    (code)      (deploy & run)    (review & fix)      (outline)     (plots)        (LaTeX+PDF)     (compile)       (done!)
  ├──── Command: /autor.idea-discovery ──────┤              ├── Command: /autor.auto-review-loop ─┤   ├────────── Command: /autor.paper-writing ───────────────────┤
```

### Command 1: Idea Discovery (`/autor.idea-discovery`)

> **"What's the state of the art? Where are the gaps?"**

Give a research direction — the command handles the rest:

1. **Survey** the landscape via `research-lit` (arXiv TeX sources, local PDFs, web search)
2. **Brainstorm** 8-12 concrete ideas via `idea-creator` (GPT-5.4 xhigh)
3. **Filter** by feasibility, compute cost, and quick novelty search
4. **Validate** top ideas with `novelty-check` + `research-reviewer` agent
5. **Pilot** top 2-3 ideas in parallel on GPUs (30 min - 2 hr each)
6. **Rank** by empirical signal — ideas with positive pilot results rise to the top

```
┌─────────────────────────────────────────────────────────────┐
│                  /autor.idea-discovery                             │
│                                                              │
│   research-lit     idea-creator       novelty-check          │
│   (skill)          (skill)            (skill)                │
│       │                │                  │                  │
│       ▼                ▼                  ▼                  │
│   ┌──────────┐    ┌──────────┐      ┌──────────┐           │
│   │ Scan     │───▶│ Generate │─────▶│ Check if │           │
│   │ arXiv +  │    │ 8-12     │      │ idea is  │           │
│   │ local +  │    │ ideas    │      │ novel    │           │
│   │ web      │    │ + rank   │      │          │           │
│   └──────────┘    └──────────┘      └──────────┘           │
│                                          │                  │
│                                          ▼                  │
│                                    ┌──────────┐            │
│                                    │research- │            │
│                                    │reviewer  │            │
│                                    │(agent)   │            │
│                                    └──────────┘            │
│                                                              │
│   Output: IDEA_REPORT.md with ranked ideas + pilot results   │
└─────────────────────────────────────────────────────────────┘
```

**Components:** `research-lit` skill + `idea-creator` skill + `novelty-check` skill + `research-reviewer` agent

### Command 2: Auto Review Loop (`/autor.auto-review-loop`)

> **"Review my paper, fix what's wrong, repeat until it's good."**

```
┌─────────────────────────────────────────────────────────────┐
│                  /autor.auto-review-loop                            │
│                                                              │
│   research-reviewer        run-experiment                    │
│   (agent)                  (skill)                           │
│         │                       │                            │
│         ▼                       ▼                            │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐               │
│   │ External │──▶│ Implement│──▶│ Monitor  │──▶ repeat      │
│   │ LLM      │   │ fixes    │   │ results  │    until       │
│   │ reviews  │   │ & run    │   │          │    score ≥ 6   │
│   └──────────┘   │experiments│  └──────────┘               │
│                   └──────────┘                               │
│                                                              │
│   State: REVIEW_STATE.json + AUTO_REVIEW.md                  │
│   Recovery: 24-hour window from persisted state              │
└─────────────────────────────────────────────────────────────┘
```

**Components:** `research-reviewer` agent + `run-experiment` skill + `analyze-results` skill + `monitor-experiment` skill + `novelty-check` skill

**Safety features:**

- **MAX_ROUNDS = 4** — prevents infinite loops; stops early if score threshold is met
- **> 4 GPU-hour experiments skipped** — flags for manual follow-up
- **Prefer reframing over new experiments** — chooses the cheaper path
- **No hiding weaknesses** — explicit rule against gaming scores
- **Compact recovery** — persists state after each round; resumes after context compaction

### Command 3: Paper Writing (`/autor.paper-writing`)

> **"Turn my research narrative into a submission-ready PDF."**

```
┌─────────────────────────────────────────────────────────────┐
│                  /autor.paper-writing                               │
│                                                               │
│   paper-plan      paper-figure     paper-write                │
│   (skill)         (skill)          (skill)                    │
│        │                │                 │                   │
│        ▼                ▼                 ▼                   │
│   ┌──────────┐    ┌──────────┐     ┌──────────┐              │
│   │ Claims-  │───▶│ Generate │────▶│ Section  │──┐           │
│   │ Evidence │    │ figures, │     │ by       │  │           │
│   │ Matrix   │    │ tables   │     │ section  │  │           │
│   └──────────┘    └──────────┘     └──────────┘  │           │
│                                                   │           │
│        paper-compile       paper-improver         │           │
│        (skill)             (agent)                │           │
│             │                   │                 │           │
│             ▼                   ▼                 ▼           │
│   ┌──────────────────────────────────────────────────┐       │
│   │ NARRATIVE_REPORT.md ──▶ paper/ (LaTeX + PDF)      │       │
│   │ Template: templates/VENUE/ (from CLAUDE.md)       │       │
│   └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

**Components:** `paper-plan` skill + `paper-figure` skill + `paper-write` skill + `paper-compile` skill + `paper-improver` agent

**Input:** A `NARRATIVE_REPORT.md` describing the research.

**Output:** A submission-ready `paper/` directory with LaTeX source, clean `.bib`, and compiled PDF.

**Key features:**
- **Claims-Evidence Matrix** — every claim maps to evidence, every experiment supports a claim
- **Auto figure generation** — line plots, bar charts, comparison tables from JSON data
- **Clean bib** — automated filtering removes uncited entries
- **Template resolution** — automatically loads venue style files from `templates/VENUE/`
- **GPT-5.4 review** — `paper-improver` agent runs 2 rounds of content review + format check
- **De-AI polish** — removes AI writing patterns (delve, pivotal, landscape...)
- **Page verification** — `pdftotext`-based precise check against venue page limit

> **What `/paper-figure` can and cannot do:** It auto-generates **data-driven plots** (training curves, bar charts, heatmaps) and **comparison tables**. It **cannot** generate architecture diagrams or pipeline figures — create those manually and place in `figures/` before running `/paper-write`.

#### Paper Improvement (via `paper-improver` agent)

After `/autor.paper-writing` generates the paper, the `paper-improver` agent runs 2 rounds of GPT-5.4 xhigh content review + fix + recompile, plus a final format compliance check.

### Command 4: Research Pipeline (`/autor.research-pipeline`)

Meta-pipeline: `/autor.idea-discovery` → (mandatory human gate) → implementation → `/autor.auto-review-loop`. Does NOT include paper-writing (run `/autor.paper-writing` separately after).

The mandatory human gate ensures you review and approve the selected idea before committing GPU time to full implementation.

---

## All Components

### Skills (10 building blocks)

| Skill | Description | Needs Codex MCP? |
|-------|-------------|-----------------|
| [`research-lit`](skills/research-lit/SKILL.md) | Literature search: arXiv TeX sources, local PDFs, web search | No |
| [`idea-creator`](skills/idea-creator/SKILL.md) | Generate and rank 8-12 research ideas given a direction | Yes |
| [`novelty-check`](skills/novelty-check/SKILL.md) | Verify idea novelty against recent literature | Yes |
| [`run-experiment`](skills/run-experiment/SKILL.md) | Deploy experiments to local (MPS/CUDA) or remote GPU | No |
| [`monitor-experiment`](skills/monitor-experiment/SKILL.md) | Monitor running experiments, check progress, collect results | No |
| [`analyze-results`](skills/analyze-results/SKILL.md) | Analyze results, compute statistics, generate insights | No |
| [`paper-plan`](skills/paper-plan/SKILL.md) | Claims-evidence matrix + section outline + citation scaffolding | Yes |
| [`paper-figure`](skills/paper-figure/SKILL.md) | Publication-quality matplotlib/seaborn plots with LaTeX snippets | Optional |
| [`paper-write`](skills/paper-write/SKILL.md) | Section-by-section LaTeX generation with venue templates | Yes |
| [`paper-compile`](skills/paper-compile/SKILL.md) | Compile LaTeX to PDF, auto-fix errors, submission readiness check | No |

### Commands (4 workflow orchestrators)

| Command | Composes | Description |
|---------|----------|-------------|
| [`/autor.idea-discovery`](commands/autor.idea-discovery.md) | research-lit → idea-creator → novelty-check → research-reviewer | Literature survey to validated, ranked ideas |
| [`/autor.auto-review-loop`](commands/autor.auto-review-loop.md) | research-reviewer → fix → run-experiment → re-review (x4) | Autonomous review-fix iteration loop |
| [`/autor.paper-writing`](commands/autor.paper-writing.md) | paper-plan → paper-figure → paper-write → paper-compile → paper-improver | Narrative report to submission-ready PDF |
| [`/autor.research-pipeline`](commands/autor.research-pipeline.md) | idea-discovery → human gate → implement → auto-review-loop | Full end-to-end research pipeline |

### Agents (2 specialized personas)

| Agent | Description | Model |
|-------|-------------|-------|
| [`research-reviewer`](agents/research-reviewer.md) | Senior ML reviewer — multi-round critical feedback on ideas, papers, results | GPT-5.4 xhigh via Codex MCP |
| [`paper-improver`](agents/paper-improver.md) | 2-round auto-improvement: review → fix → recompile. State via PAPER_IMPROVEMENT_STATE.json | GPT-5.4 xhigh via Codex MCP |

---

## Setup

### Prerequisites

1. [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed
2. [Codex CLI](https://github.com/openai/codex) installed (for review skills and agents):
   ```bash
   npm install -g @openai/codex
   codex auth login
   ```
   Codex MCP is auto-configured via `.mcp.json` (project-level). To also make it available globally:
   ```bash
   claude mcp add codex -s user -- codex mcp-server
   ```
3. (For paper writing) **LaTeX** environment with `latexmk` and `pdfinfo`:
   ```bash
   # macOS
   brew install --cask mactex    # or: brew install basictex
   brew install poppler          # provides pdfinfo

   # Ubuntu/Debian
   sudo apt install texlive-full latexmk poppler-utils

   # Verify
   latexmk --version && pdfinfo -v
   ```
   > If you only need idea discovery + auto review, LaTeX is not required.

### Install

```bash
git clone https://github.com/llv23/AutoResearchWithEyes.git
cd AutoResearchWithEyes
```

**Option A: Use from project directory** (recommended)

Simply run `claude` from the repo. Claude Code auto-discovers skills from `skills/`, commands from `commands/`, and agents from `agents/`:

```bash
cd AutoResearchWithEyes
claude
```

**Option B: Load as a plugin from any directory**

Use `--plugin-dir` to load the plugin for a session without being in the repo:

```bash
claude --plugin-dir /path/to/AutoResearchWithEyes
```

**Option C: Install skills globally**

Copy skills to your user directory so they're available from any project:

```bash
cp -r skills/* ~/.claude/skills/
cp -r commands/* ~/.claude/commands/
```

The Codex MCP server auto-configures from `.mcp.json` (project-level) when running from the project directory. You can also add it at user scope (`claude mcp add codex -s user -- codex mcp-server`) to make it available in all projects — both can coexist.

### Download Venue Templates

Templates are **not bundled** — download the official author kit for your target venue:

| Venue | Place files in | Page limit |
|-------|---------------|------------|
| ICLR 2026 | `templates/iclr2026/` | 9 pages |
| NeurIPS 2026 | `templates/neurips2026/` | 9 pages |
| ICML 2026 | `templates/icml2026/` | 8 pages |

Each `templates/<venue>/README.md` has specific download instructions.

**Custom venue:** Create `templates/<venue-name>/`, add style files, update `VENUE` and page limit in `CLAUDE.md`.

### Usage

```
# Commands (workflow orchestrators)
> /autor.idea-discovery "your research direction"      # Workflow 1
> /autor.auto-review-loop "your paper topic"           # Workflow 2
> /autor.paper-writing "NARRATIVE_REPORT.md"           # Workflow 3
> /autor.research-pipeline "your research direction"   # Full pipeline

# Individual skills
> /research-lit "topic"                          # just literature survey
> /idea-creator "topic"                          # just brainstorm
> /novelty-check "specific idea"                 # just novelty verification
> /run-experiment train.py --lr 1e-4 --epochs 100
> /analyze-results figures/*.json
> /monitor-experiment server5
> /paper-plan "NARRATIVE_REPORT.md"              # just outline
> /paper-compile "paper/"                        # just compile
```

### Auto-Allow for Overnight Runs (Optional)

To run without permission prompts, add to `.claude/settings.local.json`:

```json
{
  "permissions": {
    "allow": [
      "mcp__codex__codex",
      "mcp__codex__codex-reply",
      "Write",
      "Edit",
      "Skill(auto-review-loop)"
    ]
  }
}
```

<details>
<summary><h3>GPU Server Setup (For Auto-Experiments)</h3></summary>

When GPT-5.4 says "run an ablation study", Claude Code writes the script and deploys it to your GPU server. Add your server info to your project's `CLAUDE.md`:

```markdown
## Remote Server

- SSH: `ssh my-gpu-server` (key-based auth, no password)
- GPU: 4x A100
- Conda env: `research` (Python 3.10 + PyTorch)
- Activate: `eval "$(/opt/conda/bin/conda shell.bash hook)" && conda activate research`
- Code directory: `/home/user/experiments/`
- Use `screen` for background jobs: `screen -dmS exp0 bash -c '...'`
```

**No server?** Review and rewriting skills work without GPU access. Experiment-related fixes will be flagged for manual follow-up.

</details>

---

## Customization

All constants live in `CLAUDE.md` at the repo root. Edit to customize:

| Constant | Default | Description |
|----------|---------|-------------|
| `REVIEWER_MODEL` | `gpt-5.4` | Model used via Codex MCP |
| `PILOT_MAX_HOURS` | `2` | Max hours per pilot idea |
| `PILOT_TIMEOUT_HOURS` | `3` | Hard timeout for pilots |
| `MAX_PILOT_IDEAS` | `3` | Ideas piloted in parallel |
| `MAX_TOTAL_GPU_HOURS` | `8` | Total GPU budget |
| `MAX_ROUNDS` | `4` | Review-fix iterations |
| `POSITIVE_THRESHOLD` | `>= 6/10` | Score to pass review |
| `AUTO_PROCEED` | `true` | Auto-proceed at checkpoints |
| `MAX_IMPROVEMENT_ROUNDS` | `2` | Paper improvement iterations |
| `COMPILER` | `latexmk` | LaTeX build tool |
| `ENGINE` | `pdflatex` | LaTeX engine |
| `MAX_COMPILE_ATTEMPTS` | `3` | Compilation retries |
| `VENUE` | `iclr2026` | Target venue |
| `TEMPLATE_DIR` | `templates/` | Template base directory |

Override per-invocation with inline arguments:

```
/autor.idea-discovery "topic" -- pilot budget: 4h, max ideas: 5
/autor.paper-writing "NARRATIVE_REPORT.md" -- venue: neurips2026, engine: xelatex
```

---

## Alternative Model Combinations

Don't have Claude / OpenAI API? Swap in other models — same cross-model architecture, different providers.

| Role | Default | Alt A: GLM + GPT | Alt B: GLM + MiniMax |
|------|---------|-------------------|----------------------|
| Executor (Claude Code) | Claude Opus/Sonnet | GLM-5 (ZhiPu API) | GLM-5 (ZhiPu API) |
| Reviewer (Codex MCP) | GPT-5.4 | GPT-5.4 (OpenAI API) | MiniMax-M2.5 (MiniMax API) |
| Need OpenAI API? | Yes | Yes | **No** |

<details>
<summary><b>Alt A: GLM (executor) + GPT (reviewer)</b></summary>

```json
{
    "env": {
        "ANTHROPIC_AUTH_TOKEN": "your_zai_api_key",
        "ANTHROPIC_BASE_URL": "https://api.z.ai/api/anthropic",
        "API_TIMEOUT_MS": "3000000",
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": "glm-4.5-air",
        "ANTHROPIC_DEFAULT_SONNET_MODEL": "glm-4.7",
        "ANTHROPIC_DEFAULT_OPUS_MODEL": "glm-5"
    },
    "mcpServers": {
        "codex": {
            "command": "codex",
            "args": ["mcp-server"],
            "type": "stdio"
        }
    }
}
```

</details>

<details>
<summary><b>Alt B: GLM (executor) + MiniMax (reviewer)</b> — No Claude or OpenAI API needed</summary>

```json
{
    "env": {
        "ANTHROPIC_AUTH_TOKEN": "your_zai_api_key",
        "ANTHROPIC_BASE_URL": "https://api.z.ai/api/anthropic",
        "API_TIMEOUT_MS": "3000000",
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": "glm-4.5-air",
        "ANTHROPIC_DEFAULT_SONNET_MODEL": "glm-4.7",
        "ANTHROPIC_DEFAULT_OPUS_MODEL": "glm-5",
        "CODEX_API_KEY": "your_minimax_api_key",
        "CODEX_API_BASE": "https://api.minimax.chat/v1/",
        "CODEX_MODEL": "MiniMax-M2.5"
    },
    "mcpServers": {
        "codex": {
            "command": "codex",
            "args": ["mcp-server"],
            "type": "stdio"
        }
    }
}
```

</details>

---

## Roadmap

- [ ] **Slack notifications** — webhook notifications at key pipeline events (off by default)
- [ ] **Configurable human checkpoints** — `AUTO_PROCEED=false` to pause at each decision point
- [ ] **Zotero MCP integration** — search collections, read annotations, export BibTeX as optional data source
- [ ] **Obsidian MCP integration** — search vault for research notes as optional data source
- [ ] **W&B integration** — pull training curves as feedback signal for auto-review
- [ ] More executor x reviewer combinations (Gemini, DeepSeek, etc.)

---

## Community

Join the WeChat group for discussion on Claude Code + AI-driven research workflows:

<img src="docs/wechat_group.jpg" alt="WeChat Group QR Code" width="300">

## Star History

![GitHub stars](https://img.shields.io/github/stars/llv23/AutoResearchWithEyes?style=social)

[![Star History Chart](https://api.star-history.com/svg?repos=llv23/AutoResearchWithEyes&type=Date&v=20260312&r=2)](https://star-history.com/#llv23/AutoResearchWithEyes&Date)

## Acknowledgements

**Core Infrastructure**
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) — Anthropic's CLI for Claude, the execution backbone
- [Codex CLI](https://github.com/openai/codex) — OpenAI's CLI, used as MCP server for cross-model review

**Paper Writing Inspiration**
- [claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) — Academic paper writing with Claude
- [Research-Paper-Writing-Skills](https://github.com/Master-cai/Research-Paper-Writing-Skills) — Paper writing skill templates
- [baoyu-skills](https://github.com/jimliu/baoyu-skills) — Claude Code skills collection

**Community**
- [awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) — Curated list of Claude Code skills (featured)

## License

MIT
