---
name: autor.template
description: "Download and set up venue-specific LaTeX templates. Supports iclr2026, neurips2026, icml2026, emnlp2026, or a custom venue. Use when user says \"download template\", \"setup venue\", or wants to configure a new conference template."
argument-hint: <venue> (e.g., iclr2026, neurips2026, icml2026, emnlp2026, or custom:<venue-name>)
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, WebSearch, WebFetch
---

# Venue Template Setup

Download and configure LaTeX template files for: **$ARGUMENTS**

## Overview

This command downloads official conference style files into `templates/<venue>/` and updates `CLAUDE.md` with the venue's page limits. It supports both known venues (with pre-configured download URLs) and custom venues.

## Constants

Read `TEMPLATE_DIR` from **CLAUDE.md** (default: `templates/`).

## Known Venues

| Venue | Source | Key Files | Page Limit |
|-------|--------|-----------|------------|
| `iclr2026` | [ICLR GitHub](https://github.com/ICLR/Master-Template) — `iclr2026.zip` | `iclr2026_conference.sty`, `.bst`, `.tex`, `natbib.sty`, `fancyhdr.sty` | 9 pages |
| `neurips2026` | [NeurIPS media server](https://media.neurips.cc/Conferences/) — latest `Styles.zip` | `neurips_*.sty`, `.tex` | 9 pages |
| `icml2026` | [ICML media server](https://media.icml.cc/Conferences/) — latest `Styles.zip` or `icml*.zip` | `icml*.sty`, `.bst`, `algorithm.sty`, `algorithmic.sty`, `fancyhdr.sty` | 8 pages |
| `emnlp2026` | [ACL style files](https://github.com/acl-org/acl-style-files) | `acl.sty`, `acl_natbib.bst`, `acl_latex.tex` | 8 pages (long) / 4 pages (short) |

## Procedure

### Step 1: Parse the venue argument

Extract the venue name from `$ARGUMENTS`. Normalize to lowercase, strip whitespace.

- If the argument matches a known venue (iclr2026, neurips2026, icml2026, emnlp2026), proceed to Step 2.
- If the argument starts with `custom:`, extract the venue name and skip to Step 4 (Custom Venue).
- If no argument is given, read `VENUE` from `CLAUDE.md` and use that.

### Step 2: Create the template directory

```bash
mkdir -p templates/<venue>/
```

### Step 3: Download files for the known venue

Follow the venue-specific download procedure:

#### iclr2026

```bash
cd /tmp
curl -sLO https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2026.zip
unzip -o iclr2026.zip -d iclr2026_extracted
cp iclr2026_extracted/iclr2026/*.sty templates/iclr2026/
cp iclr2026_extracted/iclr2026/*.bst templates/iclr2026/
cp iclr2026_extracted/iclr2026/*.tex templates/iclr2026/
cp iclr2026_extracted/iclr2026/*.bib templates/iclr2026/
```

#### neurips2026

Try the latest year available from the NeurIPS media server:

```bash
cd /tmp
# Try 2026 first, fall back to 2025
curl -sfLO https://media.neurips.cc/Conferences/NeurIPS2026/Styles.zip || \
curl -sfLO https://media.neurips.cc/Conferences/NeurIPS2025/Styles.zip
unzip -o Styles.zip -d neurips_extracted
cp neurips_extracted/Styles/*.sty templates/neurips2026/
cp neurips_extracted/Styles/*.tex templates/neurips2026/
```

#### icml2026

Try the latest year available from the ICML media server:

```bash
cd /tmp
# Try 2026 first, fall back to 2025, then 2024
curl -sfLO https://media.icml.cc/Conferences/ICML2026/Styles/icml2026.zip || \
curl -sfLO https://media.icml.cc/Conferences/ICML2025/Styles/icml2025.zip || \
curl -sfLO https://media.icml.cc/Conferences/ICML2024/Styles/icml2024.zip
unzip -o icml*.zip -d icml_extracted
cp icml_extracted/icml*/*.sty templates/icml2026/
cp icml_extracted/icml*/*.bst templates/icml2026/
cp icml_extracted/icml*/*.tex templates/icml2026/
cp icml_extracted/icml*/*.bib templates/icml2026/
```

#### emnlp2026

```bash
cd templates/emnlp2026/
curl -sLO https://raw.githubusercontent.com/acl-org/acl-style-files/master/acl.sty
curl -sLO https://raw.githubusercontent.com/acl-org/acl-style-files/master/acl_natbib.bst
curl -sLO https://raw.githubusercontent.com/acl-org/acl-style-files/master/acl_latex.tex
curl -sLO https://raw.githubusercontent.com/acl-org/acl-style-files/master/custom.bib
```

### Step 4: Custom Venue (for `custom:<venue-name>`)

For custom venues that aren't pre-configured:

1. Create `templates/<venue-name>/`
2. Ask the user for:
   - The download URL or GitHub repository for style files
   - The page limit (main body pages)
   - Citation style (`natbib` or other)
3. Download the style files from the provided URL
4. Create a `README.md` in the template directory with setup instructions
5. Update `CLAUDE.md` page limits section

### Step 5: Verify downloaded files

List the downloaded files and verify at least a `.sty` file exists:

```bash
ls -la templates/<venue>/
```

If no `.sty` file was downloaded, report the error and provide manual download instructions.

### Step 6: Update CLAUDE.md (if venue is new)

Check if the venue already has a page limit entry in `CLAUDE.md`. If not, add it under the `### Page Limits` section.

### Step 7: Update VENUE (optional)

Ask the user:

```
Template for <venue> is ready. Would you like me to set VENUE = <venue> in CLAUDE.md as the active target?
```

- If yes, update the `VENUE` line in `CLAUDE.md`.
- If no (or AUTO_PROCEED=true), leave `VENUE` unchanged.

### Step 8: Report

Present a summary:

```
Template setup complete for <venue>:

Files downloaded:
  - [list of .sty, .bst, .tex, .bib files]

Location: templates/<venue>/
Page limit: X pages
Citation style: natbib

Note: [any fallback info, e.g., "Used NeurIPS 2025 style files — 2026 not yet released"]

To use this venue: set VENUE = <venue> in CLAUDE.md
```

## Key Rules

- **Never overwrite without checking.** If template files already exist, ask the user before overwriting.
- **Fall back gracefully.** If the latest year's style files aren't available yet, use the most recent year and note it clearly.
- **Clean up temp files.** Remove `/tmp` extraction directories after copying.
- **Preserve existing README.md.** Don't overwrite a `README.md` that already exists in the template directory unless the user asks.
