---
name: Prepare_Book
description: Prepares PDF books for LLM analysis. Creates analysis-ready chunks through TOC-based splitting and markdown conversion while preventing Context Overflow. Use when you need PDF book analysis, chapter-based splitting, or markdown conversion.
allowed-tools: Read, Bash, Glob, Grep
version: 2.0.0
status: active
updated: 2026-01-26
---

# Book-Prep: PDF Book LLM Analysis Preparation Skill

Prepares PDF books in an optimized format for LLM analysis. Provides TOC-based splitting and markdown conversion.

**Note**: Image description generation has been moved to the `Describe_Images` skill. Use it separately after markdown conversion.

## Quick Reference

### Script Locations

All scripts are located in a single directory within the skill folder:

- Script Directory: `.claude/skills/Prepare_Book/Scripts/`
- Contains: `check_toc.py`, `split_pdf.py`, `pdf_to_md.py`

### Core Workflow

1. TOC Analysis: Run check_toc.py to generate toc.json
2. Level Selection: Analyze TOC structure to select optimal level
3. PDF Splitting: Run split_pdf.py --level N
4. Markdown Conversion: Convert each split PDF with pdf_to_md.py
5. (Optional) Image Description: Use `Describe_Images` skill separately

### Basic Commands

All commands use the Scripts directory. Use absolute path or set SCRIPTS_DIR variable:

```bash
SCRIPTS_DIR="/path/to/vault/.claude/skills/Prepare_Book/Scripts"
```

TOC Analysis:

```bash
cd "$SCRIPTS_DIR"
source .venv/bin/activate
python3 check_toc.py "/path/to/book.pdf"
```

PDF Splitting:

```bash
python3 "$SCRIPTS_DIR/split_pdf.py" --level 1 "/path/to/book.pdf"
```

Markdown Conversion:

```bash
python3 "$SCRIPTS_DIR/pdf_to_md.py" -p "/path/to/split/chapter.pdf"
```

Image Description (separate skill):

```bash
cd ".claude/skills/Describe_Images/Scripts"
source .venv/bin/activate
python Describe_Images.py "/path/to/chapter.md" -m gpt
```

### Output Structure

```
book.pdf (original)
book/
  toc.json (TOC analysis result)
  1. Chapter One.pdf (split PDF)
  1. Chapter One.md (markdown)
  2. Chapter Two.pdf
  2. Chapter Two.md
  images/ (shared image folder)
```

---

## Environment Setup

### Prerequisites

- Python 3.10+ (use `python3`, not `python` on macOS)
- Virtual environment in Scripts directory

### Initial Setup

```bash
SCRIPTS_DIR="/path/to/vault/.claude/skills/Prepare_Book/Scripts"
cd "$SCRIPTS_DIR"
python3 -m venv .venv
source .venv/bin/activate
pip install pymupdf pymupdf4llm python-dotenv
```

---

## Implementation Guide

### Step 1: TOC Analysis

Analyzes the PDF's table of contents structure and saves it as JSON.

```bash
SCRIPTS_DIR="/path/to/vault/.claude/skills/Prepare_Book/Scripts"
"$SCRIPTS_DIR/.venv/bin/python" "$SCRIPTS_DIR/check_toc.py" "/path/to/book.pdf"
```

Generated toc.json structure:

```json
{
  "pdf_name": "Value.pdf",
  "total_pages": 561,
  "summary": {
    "max_level": 4,
    "levels": {
      "level_1": {
        "count": 6,
        "total_pages": 380,
        "avg_pages": 89.7
      },
      "level_2": {
        "count": 5,
        "total_pages": 342,
        "avg_pages": 101.0
      }
    }
  },
  "toc": [
    {
      "level": 1,
      "title": "Part I",
      "start_page": 20,
      "end_page": 161,
      "page_count": 142,
      "characters": 236255,
      "has_children": true
    }
  ]
}
```

### Step 2: Split Level Decision

Split level decision is the core of this skill. Wrong level selection creates chunks that are too large (Context Overflow) or too small (insufficient context).

#### Decision Rules

Default rule: Use level=1 when it represents the top-level of main body content

Exception rule: Use level=2 when level=1 contains a single entry encompassing the entire body

#### Judgment Criteria

Use level=2 when ALL of the following conditions are met:
- A specific level_1 entry occupies 70% or more of total pages
- That entry has has_children: true

Use level=1 when:
- level_1 entries are relatively evenly distributed
- Each entry is an independent Part or Section

### Step 3: PDF Splitting

Split the PDF with the determined level.

```bash
"$SCRIPTS_DIR/.venv/bin/python" "$SCRIPTS_DIR/split_pdf.py" --level 2 "/path/to/book.pdf"
```

Split result:

```
The Idea of Justice/
  1. Introduction.pdf
  2. PART ONE The Demands of Justice.pdf
  3. PART TWO Forms of Reasoning.pdf
  4. PART THREE The Materials of Justice.pdf
  5. PART FOUR Public Reasoning and Democracy.pdf
```

#### Split Options

- --level 1: Top-level TOC (Part level)
- --level 2: Second-level TOC (Chapter level)
- --level 3: Third-level TOC (Section level)

### Step 4: Markdown Conversion

Convert each split PDF to markdown.

```bash
"$SCRIPTS_DIR/.venv/bin/python" "$SCRIPTS_DIR/pdf_to_md.py" -p "/path/to/chapter.pdf"
```

Conversion result (files created in same folder as PDF):

```
folder/
  Chapter.pdf (input)
  Chapter.md (markdown)
  images/
    Chapter.pdf-0-0.png
    Chapter.pdf-1-0.png
```

### Step 5: Image Description (Optional, Separate Skill)

For AI image descriptions, use the `Describe_Images` skill:

```bash
cd ".claude/skills/Describe_Images/Scripts"
source .venv/bin/activate
python Describe_Images.py "/path/to/chapter.md" -m gpt
```

This is handled automatically by the `/Book` command in Phase 1.5.

---

## Advanced Patterns

### Batch Processing

Process multiple PDFs sequentially:

```bash
for pdf in "/path/to/split/folder"/*.pdf; do
  "$SCRIPTS_DIR/.venv/bin/python" "$SCRIPTS_DIR/pdf_to_md.py" -p "$pdf"
done
```

### Parallel Processing

Run multiple conversions in parallel (background jobs):

```bash
"$SCRIPTS_DIR/.venv/bin/python" "$SCRIPTS_DIR/pdf_to_md.py" -p "chapter1.pdf" &
"$SCRIPTS_DIR/.venv/bin/python" "$SCRIPTS_DIR/pdf_to_md.py" -p "chapter2.pdf" &
"$SCRIPTS_DIR/.venv/bin/python" "$SCRIPTS_DIR/pdf_to_md.py" -p "chapter3.pdf" &
wait
```

### Large Book Processing Strategy

For books over 500 pages:

1. Understand structure with check_toc.py
2. Consider more granular splitting with level_2 or level_3
3. Adjust so each chunk is around 100-200 pages

---

## Troubleshooting

### Command not found: python

Error: `command not found: python`

Cause: macOS uses `python3` instead of `python`

Solution: Always use `python3` or activate virtual environment first

### Module not found: pymupdf

Error: `ModuleNotFoundError: No module named 'pymupdf'`

Cause: Virtual environment not activated or packages not installed

Solution:
```bash
cd "$SCRIPTS_DIR"
source .venv/bin/activate
pip install pymupdf pymupdf4llm python-dotenv
```

### PDF Without TOC

Error message: "No TOC found"

Solution:
- Verify TOC exists in PDF viewer
- If no TOC, manual page range specification required
- Add TOC with Adobe Acrobat and retry

### Corrupted Virtual Environment

Error: `No such file or directory: .../python3.14`

Solution: Recreate the virtual environment:
```bash
cd "$SCRIPTS_DIR"
rm -rf .venv
python3 -m venv .venv
./.venv/bin/pip install pymupdf pymupdf4llm python-dotenv
```

---

## Dependencies

Required packages:
- Python 3.10+
- PyMuPDF 1.26.7+
- pymupdf4llm
- python-dotenv

Installation (within virtual environment):

```bash
pip install pymupdf pymupdf4llm python-dotenv
```

---

## Related Resources

**Related Skills**:
- `Describe_Images`: AI image description generation (use after markdown conversion)
- `pdf`: PDF manipulation and form processing

**Related Commands**:
- `/Book`: Orchestrates complete book restructuring workflow (includes Phase 1.5 for image description)

---

## Version History

**v2.0.0** (2026-01-26): Removed AI image description
- Image description functionality moved to `Describe_Images` skill
- Simplified `pdf_to_md.py` (PDF to Markdown conversion only)
- Reduced dependencies (removed openai, google-generativeai, Pillow)
- `/Book` command now handles image description in Phase 1.5

**v1.1.0** (2026-01-01): Previous version with integrated image description
