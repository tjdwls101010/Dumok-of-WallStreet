# Changelog

## [1.1.1] - 2026-02-23

### Fixed
- MCP server transcript retrieval failing on Cloud Run (YouTube blocks cloud IPs for Innertube API)
- Added direct YouTube page parsing fallback: fetches page HTML → extracts `ytInitialPlayerResponse` → parses caption track URLs → downloads subtitles in JSON format
- Improved error logging across all transcript extraction methods (replaced silent `except: pass` with descriptive messages)

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
