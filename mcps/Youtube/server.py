"""YouTube MCP Server — search videos and fetch transcripts via FastMCP.

Provides two tools:
  - youtube_search: Search YouTube with metadata + Gemini AI summary
  - youtube_transcript: Get full transcript for a specific video

Usage:
  fastmcp run server.py
  python server.py
"""

import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Add server directory to path for sibling module imports
sys.path.insert(0, str(Path(__file__).parent))

from fastmcp import FastMCP

from _api_gemini import summarize_transcript
from _api_transcript import get_transcript
from _api_youtube import get_channel_descriptions, get_video_details, search_videos
from _utils import date_to_iso8601, load_env, print_error

mcp = FastMCP(
    name="YouTube",
    instructions=(
        "YouTube video search and transcript retrieval server. "
        "Use youtube_search to find videos with AI-powered summaries. "
        "Use youtube_transcript to get full transcripts for deep analysis."
    ),
)


def _process_video(video: dict, gemini_key: str, language: str | None) -> dict:
    """Process a single video: fetch transcript + summarize. Runs in thread pool."""
    video_id = video["video_id"]
    try:
        transcript = get_transcript(video_id, language=language)
        summary = summarize_transcript(
            api_key=gemini_key,
            transcript=transcript,
            video_title=video["title"],
            video_description=video["description"],
        )
        video["summary"] = summary
    except Exception as e:
        print_error(f"Failed to process video {video_id}: {e}")
        video["summary"] = "Processing failed."
    return video


@mcp.tool
def youtube_search(
    query: str,
    max_results: int = 10,
    after: str | None = None,
    before: str | None = None,
    order: str = "relevance",
    language: str | None = None,
    duration: str | None = None,
    region: str | None = None,
) -> str:
    """Search YouTube videos and return metadata with AI-powered summaries.

    Each result includes title, URL, channel, view/like counts, duration,
    and a Gemini-generated summary of the video content.

    Args:
        query: Search query string.
        max_results: Number of results to return (1-50, default 10).
        after: Only videos published after this date (YYYY-MM-DD).
        before: Only videos published before this date (YYYY-MM-DD).
        order: Sort order — relevance, date, viewCount, or rating.
        language: Relevance language code (ko, en, ja, etc.).
        duration: Video length filter — short (<4min), medium (4-20min), long (>20min).
        region: Region code (US, KR, JP, etc.).

    Returns:
        JSON string with query, total_results, and results array.
    """
    youtube_key, gemini_key = load_env()

    # Step 1: Search videos
    results = search_videos(
        api_key=youtube_key,
        query=query,
        max_results=max_results,
        published_after=date_to_iso8601(after),
        published_before=date_to_iso8601(before),
        order=order,
        language=language,
        duration=duration,
        region=region,
    )

    if not results:
        return json.dumps(
            {"query": query, "total_results": 0, "results": []},
            indent=2,
            ensure_ascii=False,
        )

    # Step 2: Enrich with video details (viewCount, duration, likeCount)
    video_ids = [r["video_id"] for r in results]
    details = get_video_details(youtube_key, video_ids)
    for video in results:
        vid = video["video_id"]
        if vid in details:
            video["view_count"] = details[vid]["view_count"]
            video["like_count"] = details[vid]["like_count"]
            video["duration"] = details[vid]["duration"]
        else:
            video["view_count"] = 0
            video["like_count"] = 0
            video["duration"] = "0:00"

    # Step 3: Enrich with channel descriptions
    channel_ids = [r["channel_id"] for r in results]
    channel_descs = get_channel_descriptions(youtube_key, channel_ids)
    for video in results:
        video["channel_description"] = channel_descs.get(video["channel_id"], "")

    # Step 4: Parallel transcript extraction + Gemini summarization
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(_process_video, video, gemini_key, language): video
            for video in results
        }
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                video = futures[future]
                print_error(f"Thread error for {video['video_id']}: {e}")
                video["summary"] = "Processing failed."

    output = {
        "query": query,
        "total_results": len(results),
        "results": results,
    }
    return json.dumps(output, indent=2, ensure_ascii=False)


@mcp.tool
def youtube_transcript(
    video_id: str,
    language: str | None = None,
) -> str:
    """Get the full transcript of a YouTube video.

    Use this for deep analysis of a specific video's content.
    The transcript is returned as plain text suitable for further processing.

    Args:
        video_id: YouTube video ID (e.g. 'dQw4w9WgXcQ').
        language: Preferred transcript language code (ko, en, ja, etc.).

    Returns:
        JSON string with video_id, title, language, and transcript text.
    """
    from pyyoutube import Client

    youtube_key, _ = load_env()

    # Get video title
    title = ""
    try:
        client = Client(api_key=youtube_key)
        response = client.videos.list(video_id=video_id, parts=["snippet"])
        if response.items:
            title = response.items[0].snippet.title
    except Exception as e:
        print_error(f"Failed to fetch video title: {e}")

    # Get transcript
    transcript = get_transcript(video_id, language=language)

    if transcript is None:
        output = {
            "video_id": video_id,
            "title": title,
            "language": language or "N/A",
            "error": "No transcript available for this video.",
        }
    else:
        output = {
            "video_id": video_id,
            "title": title,
            "language": language or "auto",
            "transcript": transcript,
        }

    return json.dumps(output, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
