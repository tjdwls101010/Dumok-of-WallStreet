---
name: ppt
description: "Generate PPT slide images from markdown or PDF files using Nano-Banana"
argument-hint: '{source_file} "{instructions}" - Source file path and generation instructions'
allowed-tools: Task, Bash, AskUserQuestion, Read
model: opus
skills: pdf, Nano-Banana, Describe_Images
---

# PPT Slide Image Generator Command

This command transforms a single source document (markdown or PDF) into presentation slide images through complete agent delegation.

**Execution Model**: Orchestrates via `Task()` for planning and `Bash()` for file verification and script execution. Main command does NOT read source files directly.

---

## Command Purpose

Generate PPT slide images from a single source file through a two-stage process:
1. Analyze source content and create slide outline JSON (via Planner-PPT agent)
2. Generate slide images from JSON prompts (via Generate_Slides.py script)

**Parameters** (via `$ARGUMENTS`):
- `{source_file}`: File path (e.g., `TMP/document.md` or `TMP/report.pdf`)
- `{instructions}`: Generation instructions in quotes (e.g., `"easy for beginners"`)
- `{design_reference}`: (Optional) Design template image path in instructions for visual style reference

**Example Usage**:
```
/ppt TMP/report.md "executive summary style"
/ppt TMP/lecture.pdf "beginner-friendly with diagrams"
/ppt TMP/report.md "use .Seongjin/Templates_PPT/template.jpg as design reference"
```

---

## Tool Usage

- **Task()**: Delegates to Planner-PPT agent for JSON generation
	- WHY: Planner-PPT reads source files and generates structured slide outlines
	- IMPACT: Main command does NOT read source files directly

- **Bash()**: Used ONLY for:
	1. Verify file path: `ls "{file_path}"`
	2. Execute Describe-Images script (for markdown files)
	3. Execute Nano-Banana script: `uv run python Generate_Slides.py "{json_file}" --output-dir "{output_dir}"`
	4. Merge slide images into PDF: Python inline script with Pillow
	- NOTE: Use `uv run python` instead of `python` to ensure correct environment
	- Script path: Nano-Banana skill's `Scripts/Generate_Slides.py` (loaded via `skills:` frontmatter)

Main command delegates source file reading to Planner-PPT. Design reference images are read directly by main agent using Read() tool.

---

## Associated Components

**Core Agent**:
- **Planner-PPT**: Analyzes source files and generates slide outline JSON
	- Input: source_file_path, output_path, user_instruction, design_style_description (optional, text)
	- Output: JSON file with slide structure and Nano-Banana prompts
	- Handles: PDF processing, image extraction, style_guide.design_system generation

**Skill**:
- **Nano-Banana**: Generates slide images from JSON prompts
	- Script: Nano-Banana skill's `Scripts/Generate_Slides.py`
	- Input: JSON file path, output directory
	- Output: PNG images for each slide

---

## Execution Flow

### Step 1: Parse Arguments

Extract from `$ARGUMENTS`:
- Source file path (first argument)
- User instructions (remaining arguments in quotes)

### Step 2: Verify File Path

**Tool**: Bash

```bash
ls "{source_file}" 2>/dev/null
```

If file does not exist, report error and stop.

### Step 3: Extract Design Reference Path (Optional)

Parse design reference image path from user instructions:
- Pattern: paths ending in `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`
- Pattern: paths containing `.Seongjin/Templates_PPT/`
- Pattern: Korean keywords 디자인, 스타일, 참조 near image paths

If found, convert to absolute path using working_directory. Proceed to Step 3.5 for design analysis.

### Step 3.5: Design Reference Analysis (Optional)

**Condition**: Execute ONLY if design_reference_image_path was found in Step 3

**Tool**: Read

1. Read the design reference image using Read() tool

2. Analyze the image and extract DESIGN STYLE ONLY:

   **Extract (Visual Details)**:
   - Background style (color, texture, pattern)
   - Color palette (names only, no hex codes)
   - Visual elements (graphic elements actually visible)
   - Visual mood and atmosphere
   - Texture and effects if any

   **Do NOT Extract (CRITICAL)**:
   - Typography/font style (Planner-PPT selects for readability)
   - Any text content shown in the image
   - Names, dates, numbers, or specific data
   - **What is depicted in the image** (subject matter/content)
     - ❌ "medical illustrations", "anatomy diagrams", "photos of people"
     - ❌ "vintage illustrations", "scientific diagrams"
     - ❌ Specific objects or subjects visible in the image

   **Core Principle**: Describe HOW, not WHAT.
   - ❌ "vintage illustrations in the background" (what)
   - ✅ "light beige-toned watermark pattern in the background" (how)

3. Present extracted design to user in **natural language format**:

```markdown
## 디자인 레퍼런스 분석 결과

이 이미지에서 추출한 디자인 특성:

"{자연어 설명}"
```

**Writing Guidelines**:
- Use color names (no hex codes needed)
- **Describe graphic design elements only** (layout structure, color arrangement, decorative patterns, textures)
- Express mood/atmosphere richly
- Write in flowing, natural sentences
- ⚠️ Never mention WHAT is depicted in the image

**Examples - Abstract Design**:
- "Beige paper texture background. Coral pink, lavender purple, and black hand-drawn crayon/pencil scribbles scattered freely across the background. Doodle elements like stars, X marks, circles, squiggly lines, arrows. Modern yet playful and creative atmosphere. Minimal but energetic graphic design."
- "Deep navy blue background with gold and cream accents. Thin gold line geometric frames and decorative elements. Luxurious and classic atmosphere. Art deco style decorative patterns."

**Example - Extracting pure design from content-heavy images**:
- ❌ "Vintage anatomy illustrations in the background. Black and white medical photo collage."
- ✅ "Deep navy blue and steel gray as main colors. Dark horizontal bars at top and bottom for section division. Light beige/cream-toned watermark pattern in background. Horizontal band layout with clear section separation. Different background tones (navy, cream, gray) for each section creating visual hierarchy. Classic, academic, and refined atmosphere."

**NOTE**: Reference image may not be a PPT slide (could be poster, infographic, web design, album cover, etc.). Extract only design characteristics applicable to PPT format.

4. **Tool**: AskUserQuestion

```python
AskUserQuestion(
    questions=[
        {
            "question": "위 디자인 분석이 맞나요?",
            "header": "디자인 확인",
            "options": [
                {"label": "맞음", "description": "분석 결과대로 진행"},
                {"label": "수정 필요", "description": "일부 해석 조정 필요"}
            ],
            "multiSelect": False
        }
    ]
)
```

5. **Feedback Handling**:
   - If "맞음": Save design_style_description for Step 5
   - If "수정 필요": Ask user for specific corrections, incorporate feedback, re-present

**Output**: design_style_description (natural language design characteristics)

### Step 4: Image Pre-Processing (Markdown Only)

**Condition**: Execute only for `.md` files (skip for PDF)

**Tool**: Bash

Convert Wiki-style image links to Markdown format with AI-generated descriptions before Planner-PPT execution.

#### Step 4.1: Convert Wiki Links to Markdown Format

```bash
cd "<Describe_Images_skill>/Scripts" && source .venv/bin/activate && python Convert_Image-Link.py "{markdown_file_path}"
```

- Converts `![[image.png]]` to `![](path/image.png)`
- On failure: Log warning and continue

#### Step 4.2: Generate AI Descriptions for Images

```bash
cd "<Describe_Images_skill>/Scripts" && source .venv/bin/activate && python Describe_Images.py "{markdown_file_path}" -m gpt
```

- Converts `![](path)` to `![AI description](path)`
- On failure: Log warning and continue (Planner-PPT has fallback)

- WHY: Enables text-based image understanding without loading actual images
- IMPACT: Prevents context overflow in Planner-PPT
- All paths MUST be wrapped in double quotes (handles emoji, Korean, spaces)

### Step 5: JSON Generation via Planner-PPT

**Tool**: Task (Planner-PPT subagent)

```python
Task(
    subagent_type="Planner-PPT",
    prompt="""
    Generate PPT slide outline JSON for the following source file:

    Source File Path: {absolute_path_to_source_file}
    Output Directory: {source_dir}
    User Instruction: {user_instructions}

    Design Reference Description:
    {design_style_description}
    (natural language design description; if empty, determine design_system from content)

    Requirements:
    - Create output folder: {source_dir}/PPT_{filename}/
    - Save JSON as: {source_dir}/PPT_{filename}/Plan_{filename}.json
    - Read the ENTIRE source file content
    - Generate slide outline following 4-field schema (page, title, key_message, nano_banana_prompt)
    - Be SPECIFIC and DETAILED - include actual names, events, dates, and facts from source
    - Reference the Design Reference Description when creating style_guide.design_system

    Return: Confirmation of JSON file creation with slide count and full path
    """
)
```

**Output Path Convention**:
- Source: `TMP/📰미국의 퇴장.md`
- Output Folder: `TMP/PPT_📰미국의 퇴장/`
- JSON: `TMP/PPT_📰미국의 퇴장/Plan_📰미국의 퇴장.json`

Plans must be SPECIFIC and DETAILED with actual names, events, dates, facts. Do NOT add safety constraints to prompts - safety issues are handled reactively in Step 8 after they occur.

**IMPORTANT**: Save the agent_id returned from the Task call for potential resume operations in Step 5.5.

### Step 5.5: User Feedback Loop (통합 호출)

After JSON generation, collect user feedback on design and slide structure **simultaneously** before proceeding to image generation.

**Role Division**:
- Planner-PPT (subagent): Generates JSON + Design Rationale in result report
- PPT.md (main): Parses report, displays summaries, calls AskUserQuestion, handles Resume

**Display Preview Information** (extracted from Planner-PPT's result report):

```markdown
## 디자인 미리보기

**색상 팔레트**:
- 배경: {background_color} ({description})
- 주 강조색: {accent_primary}
- 보조 강조색: {accent_secondary}

**분위기**: {mood}

**디자인 의도**:
{design_rationale_text}

---

## 슬라이드 구성 미리보기

총 {total_pages}개 페이지

| 번호 | 제목 |
|:---:|:---|
| 1 | {slide_1_title} |
| 2 | {slide_2_title} |
| ... | ... |

**구성 의도**:
{structure_rationale_text}
```

**Combined AskUserQuestion Call** (2 questions simultaneously):

```python
AskUserQuestion(
    questions=[
        {
            "question": "이 디자인이 마음에 드시나요?",
            "header": "디자인",
            "options": [
                {"label": "만족", "description": "현재 디자인으로 진행"},
                {"label": "색상 변경", "description": "색상 팔레트 수정 필요"},
                {"label": "분위기 변경", "description": "전체적인 톤/무드 수정 필요"}
            ],
            "multiSelect": False
        },
        {
            "question": "슬라이드 구성이 적절한가요?",
            "header": "구성",
            "options": [
                {"label": "만족", "description": "현재 구성으로 진행"},
                {"label": "슬라이드 추가/삭제", "description": "슬라이드 수 조정 필요"},
                {"label": "내용 수정", "description": "특정 슬라이드 내용 변경 필요"},
                {"label": "순서 변경", "description": "슬라이드 순서 재배치 필요"}
            ],
            "multiSelect": False
        }
    ]
)
```

**Feedback Processing Logic**:

| Design | Structure | Action |
|--------|-----------|--------|
| 만족 | 만족 | → Proceed to Step 6 (Template Generation) |
| 수정 필요 | 만족 | → Resume(design feedback) → Repeat Step 5.5 |
| 만족 | 수정 필요 | → Resume(structure feedback) → Repeat Step 5.5 |
| 수정 필요 | 수정 필요 | → Resume(both feedbacks) → Repeat Step 5.5 |

**Resume Call** (when modification needed):

```python
modification_prompt = []
if design_feedback != "만족":
    modification_prompt.append(f"DESIGN: {design_feedback}")
if structure_feedback != "만족":
    modification_prompt.append(f"STRUCTURE: {structure_feedback}")

Task(
    resume=agent_id,
    subagent_type="Planner-PPT",
    prompt=" | ".join(modification_prompt) + ". Update JSON accordingly."
)
```

**Feedback Loop Flow**:
```
Step 5 → Step 5.5 (디자인+구성 동시 질문)
              │
              ├─[둘 다 만족]──────► Step 6 (템플릿 생성)
              │
              └─[하나라도 수정 필요]
                    │
                    ▼
              Resume(수정 내용) → Step 5.5로 복귀
```

### Step 6: Template Generation

**Tool**: Bash

Generate template image for consistent header/footer styling before slide generation:

```bash
cd "{script_directory}" && uv run python Generate_Template.py "{json_file}"
```

Example with special characters:
```bash
cd "<Nano-Banana_skill>/Scripts" && uv run python Generate_Template.py "{json_file}"
```

- Output: `template.png` in JSON directory (e.g., `PPT_📰제목/template.png`)
- WHY: Ensures consistent header/footer bar position and color across all slides
- On failure: Log warning and continue (slide generation works without template)

### Step 6.5: Template Feedback Loop

After template generation, ask user for approval before proceeding.

**Display Template Preview**:

```markdown
## 템플릿 미리보기

템플릿 이미지가 생성되었습니다:
`{ppt_folder}/template.png`

이 템플릿은 모든 슬라이드의 헤더/푸터 레이아웃의 기준이 됩니다.
```

**Tool**: AskUserQuestion

```python
AskUserQuestion(
    questions=[
        {
            "question": "생성된 템플릿이 만족스러우신가요?",
            "header": "템플릿",
            "options": [
                {"label": "만족", "description": "현재 템플릿으로 슬라이드 생성 진행"},
                {"label": "재생성", "description": "템플릿 이미지 다시 생성"}
            ],
            "multiSelect": False
        }
    ]
)
```

**Feedback Processing**:
- "만족" → Proceed to Step 7 (Slide Image Generation)
- "재생성" → Return to Step 6 (regenerate template)

**Feedback Loop Flow**:
```
Step 6 (Template Generation) → Step 6.5 (피드백)
                                    │
                                    ├─[만족]────► Step 7 (슬라이드 생성)
                                    │
                                    └─[재생성]──► Step 6로 복귀
```

### Step 7: Slide Image Generation via Nano-Banana

**Tool**: Bash

Execute from script directory with relative path (required for dependency loading):

```bash
cd "{script_directory}" && uv run python Generate_Slides.py "{json_file}" --output-dir "{ppt_folder}"
```

Example with special characters:
```bash
cd "<Nano-Banana_skill>/Scripts" && uv run python Generate_Slides.py "{json_file}" --output-dir "{ppt_folder}"
```

- `Generate_Slides.py` auto-detects `template.png` in JSON directory
- WHY: `uv run` needs script directory to load pyproject.toml dependencies
- All paths MUST be wrapped in double quotes
- Script creates `slide_001.png`, `slide_002.png`, etc.

### Step 8: Safety Error Recovery (If Needed)

**Condition**: Execute only if Step 7 produced failures with IMAGE_SAFETY reason

Parse script output for `FAILURE_REPORT_JSON_START` ... `FAILURE_REPORT_JSON_END` block.

If failed_slides exist with IMAGE_SAFETY or SAFETY_FILTER:

1. Call Planner-PPT to revise ONLY the failed slide prompts:
```python
Task(
    subagent_type="Planner-PPT",
    prompt="""
    SAFETY ERROR RECOVERY: Revise prompts for failed slides.

    JSON File Path: {json_file_path}
    Failed Slides: {list of failed slide pages}
    Failure Reason: IMAGE_SAFETY

    Requirements:
    - For ONLY the failed slides, revise nano_banana_prompt
    - Replace specific names with general descriptions
    - Remove references to sensitive symbols
    - Save updated JSON to SAME file path

    Return: Confirmation of revised slides
    """
)
```

2. Retry with `--slides` parameter:
```bash
cd "{script_directory}" && uv run python Generate_Slides.py "{json_file}" --output-dir "{output_dir}" --slides {failed_pages}
```

3. If still failing: Log to console and continue with available slides

Maximum 1 retry attempt. Workflow continues even if some slides cannot be generated.

### Step 9: PDF Merge

**Tool**: Bash (Python with Pillow)

```bash
uv run python -c "
from PIL import Image
import os

folder = '{ppt_folder}'
images = []

for i in range(1, {slide_count}+1):
    img_path = os.path.join(folder, f'slide_{i:03d}.png')
    if os.path.exists(img_path):
        img = Image.open(img_path).convert('RGB')
        images.append(img)

output_path = os.path.join(folder, '{filename}.pdf')
images[0].save(output_path, save_all=True, append_images=images[1:], resolution=100.0)
print(f'PDF created: {output_path}')
"
```

**PDF Output Convention**:
- Images: `PPT_📰미국의 퇴장/slide_001.png` ~ `slide_NNN.png`
- PDF: `PPT_📰미국의 퇴장/📰미국의 퇴장.pdf`

### Step 10: Results Summary

**Tool**: Direct Markdown output (no file creation)

```markdown
## ✅ {source_filename} - Complete

**Slides Generated**: {slide_count}
**PDF**: `{filename}.pdf`
**Output Folder**: `PPT_{filename}/`

### Slides
| Page | Title |
|:---:|:---|
| 1 | {slide_1_title} |
| 2 | {slide_2_title} |
| ... | ... |
```

Do NOT use AskUserQuestion. Do NOT save summary to file.

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Source Not Found | Invalid path | Verify file exists with `ls` |
| JSON Generation Failed | Planner-PPT parse error | Check file encoding and format |
| Image Generation Failed | API error | Script has built-in retry (10 retries, 30s delay) |
| API Key Missing | No .env file | Create Nano-Banana skill's `Scripts/.env` with `GOOGLE_API_KEY` |

---

## Quick Reference

| Item | Value |
|------|-------|
| Supported files | `.md`, `.pdf` |
| Output folder | `PPT_{filename}/` |
| JSON file | `Plan_{filename}.json` |
| Slide images | `slide_001.png` ~ `slide_NNN.png` |
| PDF file | `{filename}.pdf` |

---

## EXECUTION DIRECTIVE

Execute the following steps in sequence:

1. **Parse Arguments**: Extract source file path and instructions from `$ARGUMENTS`

2. **Extract Design Reference** (if present): Parse image path from instructions, convert to absolute path

3. **Verify File**: Run `ls "{source_file}"` to confirm file exists

4. **Design Reference Analysis** (if design reference found): Read image with Read(), extract design style as natural language, confirm with user via AskUserQuestion. Output: design_style_description

5. **Image Pre-Processing** (markdown only): Execute Convert_Image-Link.py then Describe_Images.py

6. **Delegate to Planner-PPT**: Call Task() with source path, output path, instructions, and design_style_description (text). **Save the returned agent_id.** Include actual names, events, dates - be SPECIFIC and DETAILED.

7. **User Feedback Loop** (Combined Call):
	- Display design + slide structure preview (from Planner-PPT's Design Rationale)
	- Call AskUserQuestion with 2 questions simultaneously (design, structure)
	- If both "만족": Proceed to Step 8
	- If modification needed: Resume Planner-PPT with feedback, repeat Step 7

8. **Generate Template**: Run Generate_Template.py to create template.png for consistent styling

9. **Template Feedback Loop**:
	- Display template path to user
	- Call AskUserQuestion (만족/재생성)
	- If "만족": Proceed to Step 10
	- If "재생성": Return to Step 8

10. **Execute Nano-Banana**: Run Generate_Slides.py from script directory with quoted paths (auto-detects template.png)

11. **Handle Safety Errors** (if any): Revise failed prompts via Planner-PPT, retry once

12. **Merge to PDF**: Combine slide images into single PDF

13. **Display Summary**: Output results via CLI (no file creation)

Proceed with execution immediately.
