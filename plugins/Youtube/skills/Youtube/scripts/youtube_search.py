#!/usr/bin/env python3
"""YouTube search pipeline: search + video details + transcript + Gemini summary.

Usage:
    python youtube_search.py "query" [--max_results 10] [--after 2025-01-01]
        [--before 2026-02-23] [--order relevance] [--language ko]
        [--duration medium] [--region US]

Output: JSON to stdout.
"""

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add script directory to path for sibling imports
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _api_gemini import summarize_transcript
from _api_transcript import get_transcript
from _api_youtube import get_channel_descriptions, get_video_details, search_videos
from _utils import date_to_iso8601, load_env, print_error


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


def main():
    parser = argparse.ArgumentParser(description="Search YouTube videos with summaries")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--max_results", type=int, default=10, help="Number of results (1-50)")
    parser.add_argument("--after", default=None, help="Published after (YYYY-MM-DD)")
    parser.add_argument("--before", default=None, help="Published before (YYYY-MM-DD)")
    parser.add_argument("--order", default="relevance", choices=["relevance", "date", "viewCount", "rating"], help="Sort order")
    parser.add_argument("--language", default=None, help="Relevance language (ko, en, etc.)")
    parser.add_argument("--duration", default=None, choices=["short", "medium", "long"], help="Video duration filter")
    parser.add_argument("--region", default=None, help="Region code (US, KR, etc.)")
    args = parser.parse_args()

    youtube_key, gemini_key = load_env()

    # Step 1: Search videos
    results = search_videos(
        api_key=youtube_key,
        query=args.query,
        max_results=args.max_results,
        published_after=date_to_iso8601(args.after),
        published_before=date_to_iso8601(args.before),
        order=args.order,
        language=args.language,
        duration=args.duration,
        region=args.region,
    )

    if not results:
        json.dump({"query": args.query, "total_results": 0, "results": []}, sys.stdout, indent=2)
        return

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
            executor.submit(_process_video, video, gemini_key, args.language): video
            for video in results
        }
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                video = futures[future]
                print_error(f"Thread error for {video['video_id']}: {e}")
                video["summary"] = "Processing failed."

    # Output JSON
    output = {
        "query": args.query,
        "total_results": len(results),
        "results": results,
    }
    json.dump(output, sys.stdout, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
