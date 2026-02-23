"""Gemini API wrapper for transcript summarization and video understanding."""

from pathlib import Path

from google import genai
from google.genai import types

from _utils import print_error

_PROMPT_PATH = Path(__file__).parent / "prompt_summary.md"

# 1M token context limit ≈ 45 min of video
# Use a conservative threshold for YouTube URL understanding
_MAX_VIDEO_DURATION_MINUTES = 35

_MODEL = "gemini-3-flash-preview"


def _load_prompt() -> str:
    """Load the summary prompt template from prompt_summary.md."""
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _duration_to_minutes(duration_str: str) -> float:
    """Convert readable duration (e.g. '1:02:03', '15:30') to minutes."""
    if not duration_str:
        return 0
    parts = duration_str.split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 60 + int(parts[1]) + int(parts[2]) / 60
        elif len(parts) == 2:
            return int(parts[0]) + int(parts[1]) / 60
        return 0
    except (ValueError, IndexError):
        return 0


def _summarize_via_youtube_url(
    client: genai.Client,
    video_id: str,
    video_title: str,
) -> str | None:
    """Use Gemini's native YouTube video understanding to summarize.

    Gemini can process YouTube URLs directly, bypassing transcript extraction.
    This works even when transcript APIs are blocked (e.g., from cloud IPs).
    """
    prompt_template = _load_prompt()
    prompt = prompt_template.replace("{{TITLE}}", video_title).replace(
        "{{TRANSCRIPT}}", "[Video content provided via YouTube URL below]"
    )

    youtube_url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        response = client.models.generate_content(
            model=_MODEL,
            contents=[
                types.Part.from_uri(
                    file_uri=youtube_url,
                    mime_type="video/*",
                ),
                prompt,
            ],
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_level="low"),
                temperature=0.3,
            ),
        )
        text = response.text.strip()
        if text and len(text) > 20:
            return text
    except Exception as e:
        print_error(
            f"Gemini YouTube URL summarization failed for '{video_title}': {e}"
        )

    return None


def summarize_transcript(
    api_key: str,
    transcript: str | None,
    video_title: str,
    video_description: str = "",
    video_id: str = "",
    video_duration: str = "",
) -> str:
    """Summarize a video using Gemini.

    Strategy:
    1. If transcript is available, summarize via text prompt (fastest, cheapest)
    2. If transcript is None and video is short enough, use Gemini's YouTube URL
       understanding (bypasses transcript API blocks from cloud IPs)
    3. Fall back to video description if all else fails
    """
    client = genai.Client(api_key=api_key)

    # Strategy 1: Transcript-based summarization (preferred)
    if transcript:
        max_transcript_chars = 50000
        truncated = transcript[:max_transcript_chars]
        if len(transcript) > max_transcript_chars:
            truncated += "\n[...transcript truncated...]"

        prompt_template = _load_prompt()
        user_prompt = prompt_template.replace("{{TITLE}}", video_title).replace(
            "{{TRANSCRIPT}}", truncated
        )

        try:
            response = client.models.generate_content(
                model=_MODEL,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_level="low"),
                    temperature=0.3,
                ),
            )
            return response.text.strip()
        except Exception as e:
            print_error(f"Gemini summarization failed for '{video_title}': {e}")
            return transcript[:500] + ("..." if len(transcript) > 500 else "")

    # Strategy 2: Gemini YouTube URL understanding (for videos under threshold)
    if video_id:
        duration_mins = _duration_to_minutes(video_duration)
        if duration_mins <= 0 or duration_mins <= _MAX_VIDEO_DURATION_MINUTES:
            result = _summarize_via_youtube_url(client, video_id, video_title)
            if result:
                return result
        else:
            print_error(
                f"Skipping YouTube URL summarization for '{video_title}': "
                f"{duration_mins:.0f}min exceeds {_MAX_VIDEO_DURATION_MINUTES}min limit"
            )

    # Strategy 3: Description fallback
    if video_description:
        return (
            f"No transcript available. "
            f"Video description: {video_description[:300]}"
        )
    return "No transcript available."
