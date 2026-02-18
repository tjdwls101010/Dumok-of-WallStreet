---
name: Describe_Images
description: Convert Wiki-style image links to Markdown format with AI-generated descriptions. Use when preprocessing markdown files for PPT generation, converting ![[image.png]] to ![description](path) format, or enabling text-based image understanding.
allowed-tools: Read, Bash, Glob
version: 2.0.0
updated: 2026-01-26
status: active
color: green
---

# Describe_Images: Wiki to Markdown Image Link Converter

Convert Wiki-style image links (![[image.png]]) to Markdown format (![AI-generated description](path)) with intelligent AI-powered image analysis.

---

## Quick Reference (30 seconds)

**Purpose**: Convert Wiki-style image links to Markdown format with AI-generated alt text descriptions.

**Script Location**: `Scripts/`

**Two Scripts**:
1. `Convert_Image-Link.py` - Wiki link to Markdown conversion only
2. `Describe_Images.py` - AI description generation for images

**Execution Commands**:

```bash
# Step 1: Convert Wiki links to Markdown format
cd "Scripts" && \
source .venv/bin/activate && \
python3 Convert_Image-Link.py "{markdown_path}"

# Step 2: Generate AI descriptions for images
cd "Scripts" && \
source .venv/bin/activate && \
python3 Describe_Images.py "{markdown_path}" -m gpt
```

**Prerequisites**:
- Python venv with: `openai`, `google-generativeai`, `pillow`, `python-dotenv`
- API Key: `.env` in working directory (or `Scripts/.env` as fallback) with `OPENAI_API_KEY` or `GOOGLE_API_KEY`

**Output**: In-place modification of the markdown file.

---

## Implementation Guide (5 minutes)

### Basic Usage

**Step 1**: Ensure virtual environment is set up
```bash
cd "Scripts"
python -m venv .venv
source .venv/bin/activate
pip install python-dotenv openai google-generativeai Pillow
```

**Step 2**: Create `.env` file in your working directory (project root)
```bash
# Create at: <working_directory>/.env
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_MODEL=gpt-5-mini

# Or for Gemini
GOOGLE_API_KEY=AIza-your-google-key-here
GOOGLE_MODEL=gemini-3-flash-preview
```

**Step 3**: Execute the scripts

```bash
# Wiki link conversion only
python Convert_Image-Link.py "/path/to/document.md"

# Wiki link conversion (dry-run)
python Convert_Image-Link.py "/path/to/document.md" -n

# AI description generation using GPT (default)
python Describe_Images.py "/path/to/document.md" -m gpt

# AI description generation using Gemini
python Describe_Images.py "/path/to/document.md" -m gemini

# AI description generation (dry-run)
python Describe_Images.py "/path/to/document.md" -n
```

### Input/Output Format

**Input (Wiki-style)**:
```markdown
![[image.png]]
![[folder/diagram.jpg]]
![[screenshot.webp]]
```

**After Convert_Image-Link.py**:
```markdown
![](absolute/path/to/image.png)
![](absolute/path/to/folder/diagram.jpg)
![](absolute/path/to/screenshot.webp)
```

**After Describe_Images.py**:
```markdown
![Detailed AI-generated description of the image content](absolute/path/to/image.png)
![System architecture diagram showing...](absolute/path/to/folder/diagram.jpg)
![Screenshot of the application interface...](absolute/path/to/screenshot.webp)
```

### CLI Options

**Convert_Image-Link.py**:
| Option | Description |
|--------|-------------|
| `-n, --dry-run` | Preview changes without modifying the file |

**Describe_Images.py**:
| Option | Description |
|--------|-------------|
| `-n, --dry-run` | Preview changes without modifying the file (outputs JSON) |
| `-m, --model` | AI model selection: `gpt` (default) or `gemini` |

### Script Configuration

Configurable constants in Describe_Images.py:

```python
CONTEXT_CHARS = 500   # Characters before/after image for context
MAX_RETRIES = 3       # API call retry attempts
CONCURRENT = 20       # Maximum parallel image analyses
```

### Image Search Behavior

Convert_Image-Link.py searches for images in the following order:
1. Image index built from entire vault
2. Path specified in wiki link (if contains /)
3. Full vault search as fallback

### Supported Image Formats

png, jpg, jpeg, gif, webp, svg, bmp, tiff, ico

---

## PPT Workflow Integration

This skill serves as a critical pre-processing step in the PPT generation workflow.

### Integration Flow

**Step 1**: Convert_Image-Link.py converts Wiki links
- `![[image.png]]` → `![](path/image.png)`

**Step 2**: Describe_Images.py generates AI descriptions
- `![](path/image.png)` → `![AI description](path/image.png)`

**Step 3**: Planner-PPT reads pre-processed markdown
- Understands image content through text descriptions
- Creates slide outlines based on visual content

**Step 4**: Nano-Banana generates slide images
- Uses Planner-PPT output to create final slides

### Benefits

**Context Overflow Prevention**:
- Visual content converted to text descriptions
- Significantly reduces token usage in Planner-PPT

**Enhanced Understanding**:
- Planner-PPT can make intelligent decisions about image placement
- AI descriptions provide semantic understanding of visual content

---

## Book Workflow Integration

This skill is also used in the Book processing workflow.

### Integration Flow

**Step 1**: Prepare_Book converts PDF to Markdown
- Creates markdown files without image descriptions

**Step 2**: Describe_Images.py generates AI descriptions (Phase 1.5)
- Adds AI descriptions to all images in parallel

**Step 3**: Restructure skill processes markdown
- Works with pre-described images

---

## Related Resources

**Related Agent**:
- `Planner-PPT`: Consumes pre-processed markdown for slide planning

**Related Skills**:
- `Nano-Banana`: Generates final PPT slide images
- `Prepare_Book`: PDF to Markdown conversion (uses Describe_Images for image descriptions)

**Related Commands**:
- `/ppt`: Orchestrates complete PPT workflow including image pre-processing
- `/Book`: Orchestrates book restructuring workflow including image description

---

## Troubleshooting

**API Key Not Found**:
- Ensure `.env` file exists in your working directory (CWD) or at `Scripts/.env` as fallback
- Verify `OPENAI_API_KEY` or `GOOGLE_API_KEY` is set correctly

**Image Not Found**:
- Check if image file exists in the vault
- Verify file extension matches supported formats
- Use dry-run mode to preview path resolution

**Empty Descriptions**:
- Check API connectivity
- Verify API key has sufficient quota
- Review API error messages in console output

**Partial Processing**:
- Script saves progress after each image
- Re-run script to process remaining images
- Already-processed images (with alt text) are skipped

**Virtual Environment Issues**:
```bash
# Recreate virtual environment
cd "Scripts"
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install python-dotenv openai google-generativeai Pillow
```

---

## Version History

**v2.0.0** (2026-01-26): Split into two scripts
- `Convert_Image-Link.py`: Wiki link conversion only
- `Describe_Images.py`: AI description generation only
- Removed: `Convert_Image-Link_Wiki-to-Markdown.py` (combined script)
- Now used by both PPT and Book workflows

**v1.0.0** (2026-01-04): Initial release
- Single combined script for conversion and description
