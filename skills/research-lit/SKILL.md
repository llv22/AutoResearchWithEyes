---
name: research-lit
description: Search and analyze research papers, find related work, summarize key ideas. Use when user says "find papers", "related work", "literature review", "what does this paper say", or needs to understand academic papers.
argument-hint: [paper-topic-or-url-or-path/to/spec.md]
allowed-tools: Bash(*), Read, Glob, Grep, WebSearch, WebFetch, Write, Agent
---

# Research Literature Review

Research topic: $ARGUMENTS

## Step 0: Argument Resolution

Before starting the workflow, determine whether `$ARGUMENTS` is a **file path** or a **plain text topic**.

1. **Detect file path**: Check if `$ARGUMENTS` (after trimming quotes/whitespace) looks like a file path — i.e., ends with `.md`, `.txt`, `.pdf`, or contains `/` or `\`.
2. **If it's a file path**:
   - Read the file using the `Read` tool.
   - Extract the research topic, context, constraints, and any scope guidance from the file content.
   - Use the file content as the **RESOLVED_TOPIC** for all subsequent steps.
   - Preserve any inline overrides appended after the path (e.g., `spec.md — sources: local`): split on ` — ` and pass overrides through.
3. **If it's plain text**: Use `$ARGUMENTS` directly as the **RESOLVED_TOPIC**.

> From this point forward, all references to `$ARGUMENTS` in the workflow mean **RESOLVED_TOPIC** (the file content or the original text).

## Constants

- **PAPER_LIBRARY** — Local directory containing user's paper collection (PDFs). Check these paths in order:
  1. `papers/` in the current project directory
  2. `literature/` in the current project directory
  3. Custom path specified by user in `CLAUDE.md` under `## Paper Library`
- **MAX_LOCAL_PAPERS = 20** — Maximum number of local PDFs to scan (read first 3 pages each). If more are found, prioritize by filename relevance to the topic.

> 💡 Overrides:
> - `/research-lit "topic" — paper library: ~/my_papers/` — custom local PDF path
> - `/research-lit "topic" — sources: local` — only search local PDFs
> - `/research-lit "topic" — sources: web` — only search the web (skip all local)
> - `/research-lit "topic" — sources: local, web` — local PDFs + web search

## Data Sources

This skill checks multiple sources **in priority order**. All are optional — if a source is not configured or not requested, skip it silently.

### Source Selection

Parse `$ARGUMENTS` for a `— sources:` directive:
- **If `— sources:` is specified**: Only search the listed sources (comma-separated). Valid values: `local`, `web`, `all`.
- **If not specified**: Default to `all` — search every available source in priority order.

Examples:
```
/research-lit "diffusion models"                        → all (default)
/research-lit "diffusion models" — sources: all         → all
/research-lit "diffusion models" — sources: local       → local PDFs only
/research-lit "diffusion models" — sources: web         → web search only
/research-lit "diffusion models" — sources: local, web  → local + web
```

### Source Table

| Priority | Source | ID | How to detect | What it provides |
|----------|--------|----|---------------|-----------------|
| 1 | **Local PDFs** | `local` | `Glob: papers/**/*.pdf, literature/**/*.pdf` | Raw PDF content (first 3 pages) |
| 2 | **arXiv TeX source** | `arxiv` | Fetch from `https://arxiv.org/src/{id}` | Full paper text from TeX source — higher quality, lower token count than PDF |
| 3 | **Web search** | `web` | Always available (WebSearch) | arXiv, Semantic Scholar, Google Scholar |

> **Graceful degradation**: If arXiv TeX source is unavailable for a paper, fall back to PDF. All sources are optional — skip silently if not available.

## Workflow

### Step 0a: arXiv TeX Source Reading

When a paper is identified as an arXiv preprint (by URL or ID), prefer fetching its TeX source instead of the PDF:

1. **Extract arXiv ID** from the URL or reference (e.g., `2301.12345`)
2. **Fetch TeX source**: `WebFetch https://arxiv.org/src/{id}` — this returns the raw TeX/LaTeX source
3. **Parse content**: Extract title, abstract, sections, equations, and references from the `.tex` file(s)
4. **Cache locally**: Save the fetched TeX source to `~/.cache/aris/arxiv/{id}/` for reuse across sessions
5. **Benefits**: TeX source provides higher-quality text extraction (no OCR artifacts), lower token count (no PDF overhead), and access to exact equations and BibTeX references

> If TeX source is unavailable (e.g., author opted out, non-arXiv paper), fall back to PDF reading. Always check the cache before fetching.

### Step 0b: Scan Local Paper Library

Before searching online, check if the user already has relevant papers locally:

1. **Locate library**: Check PAPER_LIBRARY paths for PDF files
   ```
   Glob: papers/**/*.pdf, literature/**/*.pdf
   ```

2. **Filter by relevance**: Match filenames and first-page content against the research topic. Skip clearly unrelated papers.

3. **Summarize relevant papers**: For each relevant local PDF (up to MAX_LOCAL_PAPERS):
   - Read first 3 pages (title, abstract, intro)
   - Extract: title, authors, year, core contribution, relevance to topic
   - Flag papers that are directly related vs tangentially related

4. **Build local knowledge base**: Compile summaries into a "papers you already have" section. This becomes the starting point — external search fills the gaps.

> 📚 If no local papers are found, skip to Step 1. If the user has a comprehensive local collection, the external search can be more targeted (focus on what's missing).

### Step 1: Search (external)
- Use WebSearch to find recent papers on the topic
- Check arXiv, Semantic Scholar, Google Scholar
- Focus on papers from last 2 years unless studying foundational work
- **De-duplicate**: Skip papers already found in the local library or arXiv TeX cache

### Step 2: Analyze Each Paper
For each relevant paper (from all sources), extract:
- **Problem**: What gap does it address?
- **Method**: Core technical contribution (1-2 sentences)
- **Results**: Key numbers/claims
- **Relevance**: How does it relate to our work?
- **Source**: Where we found it (local/arxiv-tex/web) — helps user know what they already have vs what's new

### Step 3: Synthesize
- Group papers by approach/theme
- Identify consensus vs disagreements in the field
- Find gaps that our work could fill
- Incorporate insights from arXiv TeX sources (exact equations, theorem statements) when available

### Step 4: Output
Present as a structured literature table:

```
| Paper | Venue | Method | Key Result | Relevance to Us | Source |
|-------|-------|--------|------------|-----------------|--------|
```

Plus a narrative summary of the landscape (3-5 paragraphs).

If BibTeX entries were extracted from arXiv TeX sources, include a `references.bib` snippet for direct use in paper writing.

### Step 5: Save (if requested)
- Save paper PDFs to `literature/` or `papers/`
- Cache arXiv TeX sources to `~/.cache/aris/arxiv/` for future reuse
- Update related work notes in project memory

## Key Rules
- Always include paper citations (authors, year, venue)
- Distinguish between peer-reviewed and preprints
- Be honest about limitations of each paper
- Note if a paper directly competes with or supports our approach
- **Graceful degradation** — if arXiv TeX source is unavailable, fall back to PDF; if no local papers exist, proceed to web search
