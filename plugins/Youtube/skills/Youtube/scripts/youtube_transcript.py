#!/usr/bin/env python3
"""Fetch full transcript for a YouTube video.

Usage:
    python youtube_transcript.py VIDEO_ID [--language ko]

Output: JSON to stdout.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _api_transcript import get_transcript
from _utils import load_env, print_error
from pyyoutube import Client


def main():
    parser = argparse.ArgumentParser(description="Get full YouTube video transcript")
    parser.add_argument("video_id", help="YouTube video ID")
    parser.add_argument("--language", default=None, help="Preferred transcript language")
    args = parser.parse_args()

    youtube_key, _ = load_env()

    # Get video title
    title = ""
    try:
        client = Client(api_key=youtube_key)
        response = client.videos.list(video_id=args.video_id, parts=["snippet"])
        if response.items:
            title = response.items[0].snippet.title
    except Exception as e:
        print_error(f"Failed to fetch video title: {e}")

    # Get transcript
    transcript = get_transcript(args.video_id, language=args.language)

    if transcript is None:
        output = {
            "video_id": args.video_id,
            "title": title,
            "language": args.language or "N/A",
            "error": "No transcript available for this video.",
        }
    else:
        output = {
            "video_id": args.video_id,
            "title": title,
            "language": args.language or "auto",
            "transcript": transcript,
        }

    json.dump(output, sys.stdout, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
