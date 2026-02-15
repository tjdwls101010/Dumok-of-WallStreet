---
name: Knowledge
description: "Restructure text-based learning materials into logically organized prose documents with zero information loss"
argument-hint: '{source} "{instructions}" - Source folder or file path, and restructuring instructions'
allowed-tools: Task, Bash
model: sonnet
---

# Knowledge Architect Command

**User Interaction Architecture**: This command operates without user interaction. All processing is automatic. User provides feedback only if needed after completion.

**Execution Model**: Commands orchestrate through `Task()` tool. Bash is used only for file listing and directory creation.

**Delegation Pattern**: Parallel workflow with automatic file processing:
- Step 1: Source type determination (folder vs file)
- Step 2: Collect all eligible markdown files (if folder, process all .md files automatically)
- Step 3: Architector-Knowledge agent delegation for restructuring (PARALLEL for multiple files)
- Step 4: Report results

---

## Command Purpose

Restructure text-based learning materials into logically organized, well-structured prose documents through agent delegation:
1. Analyze source content structure and information architecture
2. Reorganize into logical, readable prose with zero information loss (via Architector-Knowledge agent)

**Parameters**: Supply via `$ARGUMENTS`
- `{source}`: Folder path (e.g., `TMP/examples2`) or file path (e.g., `TMP/examples2/0.intro.md`)
- `{instructions}`: Restructuring instructions in quotes (optional, e.g., `"focus on main concepts"`)

**Example Usage**:
```
/Knowledge TMP/examples2
/Knowledge TMP/examples2/0.intro.md "emphasize key takeaways"
/Knowledge TMP/notes/ "academic style"
```

---

## Execution Philosophy: "Information Architecture with Zero Loss"

The `/Knowledge` command transforms scattered learning materials into well-organized prose documents through complete agent delegation.

### Core Principles

1. **Absolute Source Fidelity**: Every piece of information from the original must be preserved
2. **Prose-Centric Writing**: All content flows as natural, readable prose (not bullet lists)
3. **Logical Structure**: Information reorganized for optimal comprehension
4. **Zero Summarization**: No information compression or loss

### Output Format Rules

User-Facing Reports: Always use Markdown formatting for all user communication.

User Report Example:

```
Knowledge Architecture Complete

Source Analysis:
- Files Processed: 2
- Output Documents: 2

Generated Artifacts:
1. Input: TMP/examples2/0.intro.md
   Output: TMP/examples2/Reconstruct_0.intro.md

2. Input: TMP/examples2/1.chapter.md
   Output: TMP/examples2/Reconstruct_1.chapter.md

Status: SUCCESS
```

Internal Agent Data: XML tags are reserved for agent-to-agent data transfer only. Never display XML tags to users.

### Tool Usage Discipline

This command uses these tools:

- **Task()**: Delegates to Architector-Knowledge agent for content restructuring
- **Bash()**: Used ONLY for file listing (`ls "{folder}"`)

[HARD] Main command MUST NOT use Read() tool on source files.
- WHY: Architector-Knowledge agent handles all file reading
- IMPACT: Ensures clean separation of concerns

---

## Associated Agents

**Core Agent**:

- **Architector-Knowledge**: Analyzes source files and generates restructured prose documents
  - Input: source_file_path, output_file_path, user_instructions
  - Output: Restructured markdown file with logical organization and zero information loss
  - Capabilities: Information architecture, prose writing, structural reorganization

---

## Workflow Execution

### Step 1: Determine Source Type

**Tool**: Bash

Check if source is a folder or individual file:

```bash
ls "{source}" 2>/dev/null
```

Decision Logic:
- If source ends with `/` or ls shows directory contents: Treat as folder
- If source is a single file path (ends with .md): Treat as file
- If source does not exist: Report error

---

### Step 2: Collect All Eligible Files (Folder Only)

**Condition**: Execute only if source is a folder

**Tool**: Bash

List all eligible files in folder:

```bash
ls "{source}" | grep -E '\.md$'
```

[HARD] Automatically process ALL .md files in the folder without user confirmation.

Collect all eligible file paths for Step 3.

---

### Step 3: Content Restructuring via Architector-Knowledge (PARALLEL)

**Tool**: Task (Architector-Knowledge subagent)

For each file, determine output path:
- Source file: `{source_folder}/{filename}.md`
- Output file: `{source_folder}/Reconstruct_{filename_without_ext}.md`

**Output Path Convention Examples**:
- Source: `TMP/examples2/0.서론.md` → Output: `TMP/examples2/Reconstruct_0.서론.md`
- Source: `TMP/examples2/1.운명적 동맹.md` → Output: `TMP/examples2/Reconstruct_1.운명적 동맹.md`

For each file, delegate to Architector-Knowledge:

```python
Task(
    subagent_type="Architector-Knowledge",
    prompt="""
    Restructure the following source file into a well-organized prose document:

    Input File Path: {absolute_path_to_source_file}
    Output File Path: {absolute_path_to_output_file}
    User Instructions: {user_instructions or "None provided"}

    Requirements:
    - Read the ENTIRE source file content
    - Restructure into logical, flowing prose
    - Preserve ALL information from the source (zero summarization)
    - Apply prose-centric writing style (avoid bullet lists)
    - Follow the formatting rules in the agent definition
    - Save the restructured content to the output file path

    Return: Confirmation of output file creation with word count comparison (original vs restructured)
    """
)
```

[HARD] Pass ONLY file paths to the subagent. Do NOT read file contents in main command.
- WHY: Architector-Knowledge agent handles file reading and content processing
- IMPACT: Ensures complete file processing without truncation

[HARD] PARALLEL EXECUTION: Launch ALL Task() calls in a SINGLE message.
- For multiple files, send ALL Task() tool calls simultaneously in one response
- No rate limit concerns for Claude-based processing
- 10 files processed in parallel = 10x faster than sequential

---

### Step 4: Results Summary (CLI Output Only)

**Tool**: Direct Markdown output

After all files are processed, output a summary to the user via CLI.

**Summary Template**:

```markdown
## Knowledge Architecture Complete

**Files Processed**: {file_count}

### Generated Documents

| Source | Source Chars | Output | Output Chars |
|:-------|-------------:|:-------|-------------:|
| {source_1} | {chars} | {output_1} | {chars} |
| {source_2} | {chars} | {output_2} | {chars} |
| ... | ... | ... | ... |

**Status**: SUCCESS
```

Do NOT use AskUserQuestion for next steps. User will provide feedback if needed.

---

## Error Handling

Common Errors and Solutions:

**Source Not Found**:
- Check if path is correct
- Verify file or folder exists using `ls` command

**No Eligible Files**:
- Folder contains no .md files
- Suggest adding markdown files or specifying different path

**Content Restructuring Failed**:
- Architector-Knowledge could not read or parse source file
- Check file encoding and format

**Output Directory Creation Failed**:
- Permission issues on target directory
- Check write permissions

---

## Quick Reference

| Scenario | Command | Expected Outcome |
|----------|---------|------------------|
| Single file | `/Knowledge TMP/doc.md` | 1 restructured document generated |
| Single file with instructions | `/Knowledge TMP/doc.md "academic style"` | 1 restructured document with style applied |
| Folder (all files) | `/Knowledge TMP/notes/` | All .md files processed in parallel |

**File Types Supported**:
- Markdown (.md): Direct reading and restructuring

**Output Structure**:
- Source: `{folder}/{filename}.md`
- Output: `{folder}/Reconstruct_{filename_without_ext}.md`

Version: 1.1.0
Last Updated: 2026-01-22
Architecture: Command -> Architector-Knowledge Agent (PARALLEL) -> Results Summary
