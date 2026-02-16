---
name: Mermaid
description: "Generate comprehensive Mermaid diagrams from markdown or text files"
argument-hint: '{source} "{instructions}" - Source folder or file path, and optional diagram generation instructions'
allowed-tools: Task, Bash
model: opus
---

# Mermaid Command

**User Interaction Architecture**: This command operates without user interaction. All processing is automatic. User provides feedback only if needed after completion.

**Execution Model**: Commands orchestrate through `Task()` tool. Bash is used only for file listing and directory creation.

**Delegation Pattern**: Parallel workflow with automatic file processing:
- Step 1: Source type determination (folder vs file)
- Step 2: Collect all eligible markdown files (if folder, process all .md files automatically)
- Step 3: Architector-Mermaid agent delegation for diagram generation (PARALLEL for multiple files)
- Step 4: Report results

---

## Command Purpose

Generate comprehensive Mermaid diagrams from markdown or text source files through agent delegation:
1. Analyze source content structure and extract key concepts
2. Generate Mermaid diagrams that visualize the content (via Architector-Mermaid agent)

**Parameters**: Supply via `$ARGUMENTS`
- `{source}`: Folder path (e.g., `TMP/`) or file path (e.g., `TMP/document.md`)
- `{instructions}`: Diagram generation instructions in quotes (optional, e.g., `"focus on relationships"`)

**Example Usage**:
```
/Mermaid TMP/
/Mermaid TMP/document.md "emphasize flow diagrams"
/Mermaid TMP/notes/ "focus on hierarchies"
```

---

## Execution Philosophy: "Content to Diagrams"

The `/Mermaid` command transforms text content into comprehensive Mermaid diagrams through complete agent delegation.

### Core Principles

1. **Visual Representation**: Transform textual concepts into visual diagrams
2. **Comprehensive Coverage**: Generate multiple diagram types to capture different aspects
3. **Logical Structure**: Diagrams reflect the logical structure of source content
4. **Clarity First**: Diagrams are readable and well-organized

### Output Format Rules

[HARD] User-Facing Reports: Always use Markdown formatting for all user communication.

User Report Example:

```
Mermaid Diagram Generation Complete

Source Analysis:
- Files Processed: 2
- Output Documents: 2

Generated Artifacts:
1. Input: TMP/document.md
   Output: TMP/Mermaid_document/Mermaid_document.md

2. Input: TMP/notes.md
   Output: TMP/Mermaid_notes/Mermaid_notes.md

Status: SUCCESS
```

[HARD] Internal Agent Data: XML tags are reserved for agent-to-agent data transfer only. Never display XML tags to users.

### Tool Usage Discipline [HARD]

This command uses these tools:

- **Task()**: Delegates to Architector-Mermaid agent for diagram generation
  - WHY: Architector-Mermaid reads source files and generates Mermaid diagrams
  - IMPACT: Main command does NOT read source file contents directly

- **Bash()**: Used ONLY for two purposes:
  1. List files in source folder: `ls "{folder}"`
  2. Create output directories: `mkdir -p "{output_folder}"`
  - WHY: File listing and directory creation require shell access
  - IMPACT: Limited to non-content-reading operations

[HARD] Main command MUST NOT use Read() tool on source files.
- WHY: Architector-Mermaid agent handles all file reading
- IMPACT: Ensures clean separation of concerns

---

## Associated Agents

**Core Agent**:

- **Architector-Mermaid**: Analyzes source files and generates comprehensive Mermaid diagrams
  - Input: source_file_path, output_file_path, user_instructions
  - Output: Markdown file containing multiple Mermaid diagrams with explanations
  - Capabilities: Content analysis, diagram generation, visual representation

---

## Agent Invocation Patterns (CLAUDE.md Compliance)

This command uses agent execution patterns defined in CLAUDE.md.

### Parallel Execution Workflow

Command implements parallel workflow for maximum efficiency:

Step Flow:
- Step 1: Source Type Determination (Bash ls check)
- Step 2: Collect All Eligible Files (automatic for folders)
- Step 3: Diagram Generation - PARALLEL (all Architector-Mermaid subagents run simultaneously)
- Step 4: Report Results

WHY: Parallel processing maximizes throughput
- Steps 1-2: Sequential (dependency chain)
- Step 3: PARALLEL - All Task() calls execute simultaneously

IMPACT: Multiple files processed in parallel for faster completion

### Execution Mode Details

**Step 3 - PARALLEL Execution (Diagram Generation Phase)**:
- [HARD] Launch ALL Task() calls to Architector-Mermaid in a SINGLE message (parallel execution)
- WHY: Claude-based processing has no rate limit concerns
- IMPACT: Multiple files processed simultaneously

### Resumable Agent Support FAIL

Not applicable - diagram generation is atomic per file

WHY: Each file generates one output document
- Typical execution time: 1-3 minutes per file depending on content length
- No intermediate checkpoints needed

IMPACT: If interrupted, re-run the command with same parameters

---

## Workflow Execution Details

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

[HARD] Automatically process ALL .md files in the folder
- WHY: Eliminates unnecessary user interaction
- IMPACT: Streamlined workflow for batch processing

Collect all eligible file paths for Step 3.

---

### Step 3: Diagram Generation via Architector-Mermaid

**Tool**: Task (Architector-Mermaid subagent)

For each file, determine output paths:
- Source file: `{source_folder}/{filename}.md`
- Output folder: `{source_folder}/Mermaid_{filename_without_ext}/`
- Output file: `{source_folder}/Mermaid_{filename_without_ext}/Mermaid_{filename_without_ext}.md`

**Output Path Convention Examples**:
- Source: `TMP/document.md`
- Output Folder: `TMP/Mermaid_document/`
- Output File: `TMP/Mermaid_document/Mermaid_document.md`

- Source: `TMP/Widening Inequalities of Place.md`
- Output Folder: `TMP/Mermaid_Widening Inequalities of Place/`
- Output File: `TMP/Mermaid_Widening Inequalities of Place/Mermaid_Widening Inequalities of Place.md`

For each file, first create the output directory:

```bash
mkdir -p "{output_folder}"
```

Then delegate to Architector-Mermaid:

```python
Task(
    subagent_type="Architector-Mermaid",
    prompt="""
    Generate comprehensive Mermaid diagrams for the following source file:

    Input File: {absolute_path_to_source_file}
    Output File: {absolute_path_to_output_file}
    User Instructions: {user_instructions or "None provided"}

    Requirements:
    - Read the ENTIRE source file content
    - Analyze the content structure and key concepts
    - Generate multiple Mermaid diagrams to visualize different aspects
    - Include explanatory text for each diagram
    - Save the output to the specified output file path

    Return: Confirmation of output file creation with diagram count
    """
)
```

[HARD] Pass ONLY file paths to the subagent. Do NOT read file contents in main command.
- WHY: Architector-Mermaid agent handles file reading and content processing
- IMPACT: Ensures complete file processing without truncation

[HARD] Launch ALL Task() calls in a SINGLE message for parallel execution
- WHY: No rate limit concerns for Claude-based processing
- IMPACT: All files processed simultaneously for maximum speed

---

### Step 4: Results Summary (CLI Output Only)

**Tool**: Direct Markdown output

After all files are processed, output a summary to the user via CLI.

**Summary Template**:

```markdown
## Mermaid Diagram Generation Complete

**Files Processed**: {file_count}

### Generated Documents

| Source | Output |
|:-------|:-------|
| {source_1} | {output_1} |
| {source_2} | {output_2} |
| ... | ... |

**Status**: SUCCESS
```

[HARD] Do NOT use AskUserQuestion for next steps
- WHY: User will provide feedback if needed; unnecessary prompting interrupts workflow
- IMPACT: Streamlined completion without forced interaction

---

## Error Handling

Common Errors and Solutions:

**Source Not Found**:
- Check if path is correct
- Verify file or folder exists using `ls` command

**No Eligible Files**:
- Folder contains no .md files
- Suggest adding markdown files or specifying different path

**Diagram Generation Failed**:
- Architector-Mermaid could not read or parse source file
- Check file encoding and format

**Output Directory Creation Failed**:
- Permission issues on target directory
- Check write permissions

---

## Quick Reference

| Scenario | Command | Expected Outcome |
|----------|---------|------------------|
| Single file | `/Mermaid TMP/doc.md` | 1 diagram document generated |
| Single file with instructions | `/Mermaid TMP/doc.md "flow diagrams"` | 1 diagram document with style applied |
| Folder (all files) | `/Mermaid TMP/` | All .md files processed in parallel |

**File Types Supported**:
- Markdown (.md): Direct reading and diagram generation

**Output Structure**:
- Source: `{folder}/{filename}.md`
- Output: `{folder}/Mermaid_{filename_without_ext}/Mermaid_{filename_without_ext}.md`

Version: 1.0.0
Last Updated: 2025-12-31
Architecture: Command -> Architector-Mermaid Agent (PARALLEL) -> Results Summary

---

## EXECUTION DIRECTIVE

[HARD] Execute the command following the "Content to Diagrams" philosophy described above.

1. Parse $ARGUMENTS to extract source path and instructions
   - First argument: source path (folder or file)
   - Remaining arguments in quotes: user instructions (optional)

2. [HARD] Determine if source is folder or file using Bash ls
   - WHY: Different workflow for folder vs file
   - IMPACT: Ensures correct file collection

3. [HARD] If folder, collect all .md files automatically
   - WHY: Eliminates unnecessary user interaction
   - IMPACT: Streamlined batch processing

4. [HARD] Calculate output paths for each file
   - For source `{folder}/{filename}.md`:
   - Output folder: `{folder}/Mermaid_{filename_without_ext}/`
   - Output file: `{folder}/Mermaid_{filename_without_ext}/Mermaid_{filename_without_ext}.md`
   - Use absolute paths for all file references

5. [HARD] Create output directories using Bash mkdir -p for each file
   - WHY: Ensures output directories exist before agent writes files
   - IMPACT: Prevents file write failures

6. [HARD] Launch ALL Task() calls to Architector-Mermaid in PARALLEL (single message with multiple tool calls)
   - [HARD] For MULTIPLE files: Call ALL Task() tools in ONE message to execute in parallel
   - Pass ONLY: input_file_path, output_file_path, user_instructions
   - Do NOT read source file content in main command
   - WHY: Parallel execution is significantly faster
   - IMPACT: All diagram generation completes simultaneously

7. [HARD] After ALL files are processed, display results summary via CLI
   - Output summary directly to user (no file creation)
   - Include: files processed count, source-to-output mapping
   - Do NOT use AskUserQuestion
   - WHY: Completion feedback informs user of results
   - IMPACT: User sees all results at once

8. [HARD] Proceed with execution immediately - implement all steps in sequence
   - WHY: Immediate execution ensures command completion
   - IMPACT: Describing work without executing blocks productivity
