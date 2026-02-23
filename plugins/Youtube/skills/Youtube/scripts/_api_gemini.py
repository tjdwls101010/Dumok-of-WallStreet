"""Gemini API wrapper for transcript summarization."""

from pathlib import Path

from google import genai
from google.genai import types

from _utils import print_error

_PROMPT_PATH = Path(__file__).parent / "prompt_summary.md"


def _load_prompt() -> str:
    """Load the summary prompt template from prompt_summary.md."""
    return _PROMPT_PATH.read_text(encoding="utf-8")


def summarize_transcript(
    api_key: str,
    transcript: str | None,
    video_title: str,
    video_description: str = "",
) -> str:
    """Summarize a transcript using Gemini flash with low thinking.

    If transcript is None, generates a brief description from the video metadata.
    If Gemini call fails, returns the first 500 chars of the transcript as fallback.
    """
    client = genai.Client(api_key=api_key)

    if not transcript:
        if video_description:
            return f"No transcript available. Video description: {video_description[:300]}"
        return "No transcript available."

    # Truncate transcript to ~50K chars to save tokens while retaining enough for summary
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
            model="gemini-3-flash-preview",
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
