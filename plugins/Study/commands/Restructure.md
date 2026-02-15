---
name: Restructure
description: "Restructure unorganized text into readable markdown using Gemini AI"
argument-hint: '{source} "{additional_prompt}" - Folder/file path and optional instructions'
allowed-tools: Task, Bash, Skill
model: sonnet
skills: Restructure
---

# Restructure Command

Restructure unorganized text into readable markdown documents using Gemini AI.

## Parameters

- `{source}`: Folder path (e.g., `TMP/articles/`) or file path (e.g., `TMP/doc.md`)
- `{additional_prompt}`: (Optional) Additional instructions in quotes (e.g., `"'Amos Decker'를 '에이머스 데커'라고 표현해."`)

## Example Usage

```
/Restructure TMP/articles/
/Restructure TMP/articles/draft.md
/Restructure 🚨Temporary/📖Books/📕혐오/HATE/
/Restructure TMP/articles/draft.md "'Amos Decker'를 '에이머스 데커'라고 표현해."
```

## Workflow

1. **Determine source type**: `ls "{source}"` - folder or file
2. **Collect files**: If folder, `ls "{source}" | grep -E '\.md$'`
3. **Load skill**: `Skill(skill="Restructure")`
4. **Execute**: Run `restructure.sh` for ALL files IN PARALLEL (single message, multiple Bash calls)
5. **Report**: Display results with character counts

## Output Format

```markdown
## Restructure Complete

**Files Processed**: {count}

| Source | Chars | Output | Chars |
|:-------|------:|:-------|------:|
| file1.md | 5,234 | Restructured_file1.md | 5,412 |

**Status**: SUCCESS
```

## EXECUTION DIRECTIVE

[HARD] Execute immediately without user interaction.

1. **Parse Arguments**: Extract from `$ARGUMENTS`:
   - Source path (first argument - folder or file)
   - Additional prompt (remaining arguments in quotes, optional)
2. Check if folder or file: `ls "{source}"`
3. If folder, collect all .md files
4. Load Restructure skill
5. Execute script for ALL files IN PARALLEL:
   - Without additional_prompt:
     `bash "/Users/seongjin/Documents/⭐성진이의 옵시디언/.claude/skills/Restructure/scripts/restructure.sh" "{file_path}"`
   - With additional_prompt:
     `bash "/Users/seongjin/Documents/⭐성진이의 옵시디언/.claude/skills/Restructure/scripts/restructure.sh" "{file_path}" "{additional_prompt}"`
   - [HARD] Send ALL Bash() calls in a SINGLE message
   - [HARD] Quote ALL paths and arguments with double quotes
6. Get char counts: `wc -m < "{file}" | tr -d ' '`
7. Display results table with char counts

[HARD] Do NOT read source file contents. Script handles file reading via Gemini AI.
