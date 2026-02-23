---
name: Youtube
description: YouTube video search and transcript summarization. Use when the user asks to search YouTube, find video content, look up tutorials/lectures/talks on YouTube, get video transcripts, or when web search alone is insufficient and video content would be valuable. Triggers on keywords like "YouTube", "video search", "영상 검색", "유튜브", "transcript", "자막".
allowed-tools: Bash, Read
version: 1.0.0
updated: 2026-02-23
status: active
color: red
---

# Youtube: Video Search & Transcript Summarization

Search YouTube videos by query with filters, then automatically extract transcripts and generate AI summaries using Gemini. Provides structured JSON output with video metadata, engagement stats, and content summaries.

---

## Quick Reference (30 seconds)

**Purpose**: YouTube 영상 검색 + transcript 기반 AI 요약을 한번에 제공

**Script Location**: `scripts/youtube_search.py`, `scripts/youtube_transcript.py`

**Execution Command**:
```bash
# Search videos with summaries
python scripts/youtube_search.py "query" --max_results 10

# Get full transcript for a specific video
python scripts/youtube_transcript.py VIDEO_ID
```

**Prerequisites**:
```bash
pip install python-youtube youtube-transcript-api google-genai python-dotenv
```

**Output**: JSON to stdout

---

## Implementation Guide (5 minutes)

### 2-Step Usage Pattern

**Step 1 — Search**: Find relevant videos with AI-powered summaries.
```bash
python scripts/youtube_search.py "supply chain analysis" --max_results 5
```

**Step 2 — Deep Dive**: If a specific video's summary looks promising, get the full transcript.
```bash
python scripts/youtube_transcript.py abc123 --language en
```

### youtube_search.py Parameters

| Parameter | CLI Flag | Default | Description |
|-----------|----------|---------|-------------|
| query | positional | (required) | Search query |
| max_results | `--max_results` | 10 | Number of results (1-50) |
| published_after | `--after` | None | Published after date (YYYY-MM-DD) |
| published_before | `--before` | None | Published before date (YYYY-MM-DD) |
| order | `--order` | relevance | Sort: relevance / date / viewCount / rating |
| language | `--language` | None | Relevance language code (ko, en, etc.) |
| duration | `--duration` | None | Filter: short (<4min) / medium (4-20min) / long (>20min) |
| region | `--region` | None | Country code (US, KR, etc.) |

### youtube_transcript.py Parameters

| Parameter | CLI Flag | Default | Description |
|-----------|----------|---------|-------------|
| video_id | positional | (required) | YouTube video ID |
| language | `--language` | None | Preferred transcript language |

### Search Output Schema

```json
{
  "query": "supply chain analysis",
  "total_results": 5,
  "results": [
    {
      "video_id": "abc123",
      "url": "https://www.youtube.com/watch?v=abc123",
      "title": "Supply Chain Analysis 101",
      "description": "Learn the basics of...",
      "date_published": "2025-12-15",
      "channel_id": "UCxxx",
      "channel_name": "Finance Channel",
      "channel_description": "Finance education channel...",
      "view_count": 150000,
      "like_count": 4200,
      "duration": "15:30",
      "summary": "The video explains how modern supply chains..."
    }
  ]
}
```

### Transcript Output Schema

```json
{
  "video_id": "abc123",
  "title": "Supply Chain Analysis 101",
  "language": "en",
  "transcript": "Hello everyone, today we're going to talk about..."
}
```

---

## Advanced Implementation (10+ minutes)

### Pipeline Architecture

```
youtube_search.py
├── 1. YouTube Search API  →  basic video metadata
├── 2. videos.list()       →  viewCount, likeCount, duration
├── 3. channels.list()     →  channel descriptions (200 char truncate)
└── 4. Parallel per video:
    ├── youtube-transcript-api  →  transcript text
    └── Gemini flash (low thinking)  →  ~500 char English summary
```

### Error Handling

| Scenario | Behavior |
|----------|----------|
| No transcript available | Summary says "No transcript available" + uses video description |
| Gemini API failure | Returns first 500 chars of raw transcript |
| Individual video failure | That video gets error message; others continue |
| YouTube API quota exceeded | Returns clear error JSON |
| Missing API keys | Exits immediately with error |

### Configuration

**API Keys**: Set in `scripts/.env`
```
YOUTUBE_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
```

**Summary Prompt**: Edit `scripts/prompt_summary.md` to customize the Gemini summarization behavior.

### Example Queries

```bash
# Recent Korean tech videos
python scripts/youtube_search.py "AI 기술 트렌드" --language ko --after 2025-01-01 --order date

# High-view finance content
python scripts/youtube_search.py "macro investing" --order viewCount --duration medium --region US

# Specific topic with date range
python scripts/youtube_search.py "semiconductor supply chain" --after 2025-06-01 --before 2026-01-01 --max_results 5
```

---

## Related Resources

**Dependencies**:
- `python-youtube`: YouTube Data API v3 client
- `youtube-transcript-api`: Transcript extraction (no OAuth needed)
- `google-genai`: Gemini API for summarization
- `python-dotenv`: Environment variable loading

**File Structure**:
```
Youtube/
├── SKILL.md
└── scripts/
    ├── .env                    # API keys
    ├── prompt_summary.md       # Gemini summary prompt
    ├── youtube_search.py       # Main search + summary pipeline
    ├── youtube_transcript.py   # Full transcript retrieval
    ├── _api_youtube.py         # YouTube Data API wrapper
    ├── _api_transcript.py      # Transcript extraction wrapper
    ├── _api_gemini.py          # Gemini summarization wrapper
    └── _utils.py               # Common utilities
```

---

## Troubleshooting

**YouTube API quota exceeded**:
- YouTube Data API has a daily quota of 10,000 units
- search.list costs 100 units, videos.list costs 1 unit, channels.list costs 1 unit
- Reduce `--max_results` to conserve quota

**No transcript for a video**:
- Some videos have transcripts disabled
- Live streams and very new videos may not have transcripts yet
- Try `--language en` as English transcripts are most common

**Gemini summarization errors**:
- Verify `GEMINI_API_KEY` in `.env`
- Very long transcripts may hit token limits — the script handles this gracefully

**Import errors**:
```bash
pip install python-youtube youtube-transcript-api google-genai python-dotenv
```
