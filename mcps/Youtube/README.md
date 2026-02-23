# YouTube MCP Server

FastMCP server for YouTube video search and transcript retrieval. Designed for use with Claude Desktop App.

## Tools

| Tool | Description |
|------|-------------|
| `youtube_search` | Search YouTube videos with metadata + Gemini AI summary |
| `youtube_transcript` | Get full transcript for a specific video |

## Setup

### 1. Install dependencies

```bash
cd mcps/Youtube
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure API keys

Edit `.env` in this directory:

```
YOUTUBE_API_KEY=your_youtube_api_key
GEMINI_API_KEY=your_gemini_api_key
```

### 3. Register with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "youtube": {
      "command": "/absolute/path/to/mcps/Youtube/.venv/bin/python",
      "args": ["/absolute/path/to/mcps/Youtube/server.py"]
    }
  }
}
```

### 4. Restart Claude Desktop

Restart the app to load the new MCP server.

## Local Testing

```bash
cd mcps/Youtube
.venv/bin/python -c "import sys; sys.path.insert(0,'.'); from server import mcp; print('OK:', mcp.name)"
```

## Tool Parameters

### youtube_search

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| query | str | Yes | - | Search query |
| max_results | int | No | 10 | Results count (1-50) |
| after | str | No | None | After date (YYYY-MM-DD) |
| before | str | No | None | Before date (YYYY-MM-DD) |
| order | str | No | relevance | Sort: relevance/date/viewCount/rating |
| language | str | No | None | Language code (ko, en, etc.) |
| duration | str | No | None | Length: short/medium/long |
| region | str | No | None | Region code (US, KR, etc.) |

### youtube_transcript

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| video_id | str | Yes | - | YouTube video ID |
| language | str | No | None | Preferred language code |
