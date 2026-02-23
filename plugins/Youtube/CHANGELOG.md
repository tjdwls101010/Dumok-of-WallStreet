# Changelog

## [1.1.1] - 2026-02-23

### Fixed
- MCP server transcript/summary failing on Cloud Run (YouTube blocks all cloud IPs for Innertube API)
- Added Gemini YouTube URL understanding as fallback: when transcript API is blocked, Gemini directly analyzes the video via its URL (works for videos under ~35 minutes)
- Videos over 35 minutes gracefully fall back to description-based summary
- `youtube_transcript` tool now returns AI-generated summary when transcript API is unavailable
- Improved error logging in transcript extraction (replaced silent `except: pass`)

## [1.1.0] - 2026-02-23

### Added
- YouTube MCP Server (`mcps/Youtube/`) for Claude Desktop App integration
- FastMCP-based `youtube_search` tool: search + metadata + Gemini AI summary
- FastMCP-based `youtube_transcript` tool: full transcript retrieval
- Virtual environment setup with `requirements.txt`
- Claude Desktop configuration in `claude_desktop_config.json`

## [1.0.0] - 2026-02-23

### Added
- Youtube skill: YouTube video search + transcript-based AI summarization
- `youtube_search.py`: Search pipeline with filters (date, order, duration, region, language)
- `youtube_transcript.py`: Full transcript retrieval for individual videos
- Gemini flash summarization with ~1000 character English summaries
- Parallel transcript extraction and summarization via ThreadPoolExecutor
- Language variant handling (en-US, zh-Hant, etc.) with translation fallback
- Video metadata enrichment: viewCount, likeCount, duration, channel description
- Graceful error handling: per-video failures don't block other results
