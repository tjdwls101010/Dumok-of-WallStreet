"""Common utilities for YouTube skill scripts."""

import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv


def load_env():
    """Load API keys from .env file in the scripts directory."""
    env_path = Path(__file__).parent / ".env"
    load_dotenv(env_path)

    youtube_key = os.getenv("YOUTUBE_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if not youtube_key:
        print_error("YOUTUBE_API_KEY not found in .env")
        sys.exit(1)
    if not gemini_key:
        print_error("GEMINI_API_KEY not found in .env")
        sys.exit(1)

    return youtube_key, gemini_key


def iso_duration_to_readable(duration: str) -> str:
    """Convert ISO 8601 duration to readable format.

    "PT15M30S" -> "15:30"
    "PT1H2M3S" -> "1:02:03"
    "PT45S"    -> "0:45"
    """
    if not duration:
        return "0:00"

    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
    if not match:
        return duration

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)

    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def date_to_iso8601(date_str: str) -> str:
    """Convert YYYY-MM-DD to ISO 8601 datetime string.

    "2025-01-01" -> "2025-01-01T00:00:00Z"
    """
    if not date_str:
        return None
    if "T" in date_str:
        return date_str
    return f"{date_str}T00:00:00Z"


def print_error(message: str):
    """Print error message to stderr."""
    print(f"[ERROR] {message}", file=sys.stderr)


def truncate(text: str, max_length: int = 200) -> str:
    """Truncate text to max_length, appending '...' if truncated."""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "..."
