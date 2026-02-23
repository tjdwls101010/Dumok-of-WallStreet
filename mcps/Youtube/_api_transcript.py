"""YouTube transcript extraction wrapper using youtube-transcript-api."""

from youtube_transcript_api import YouTubeTranscriptApi

from _utils import print_error

_ytt_api = YouTubeTranscriptApi()


def _expand_language_codes(languages: list[str]) -> list[str]:
    """Expand language codes to include regional variants.

    'en' -> ['en', 'en-US', 'en-GB']
    'ko' -> ['ko', 'ko-KR']
    """
    expanded = []
    variants = {
        "en": ["en", "en-US", "en-GB", "en-AU"],
        "ko": ["ko", "ko-KR"],
        "ja": ["ja", "ja-JP"],
        "zh": ["zh", "zh-CN", "zh-TW", "zh-Hant", "zh-Hans"],
        "pt": ["pt", "pt-BR", "pt-PT"],
        "es": ["es", "es-MX", "es-419"],
        "fr": ["fr", "fr-CA"],
    }
    for lang in languages:
        if lang in variants:
            expanded.extend(variants[lang])
        else:
            expanded.append(lang)
    return list(dict.fromkeys(expanded))  # dedupe preserving order


def get_transcript(video_id: str, language: str = None) -> str | None:
    """Extract transcript text from a YouTube video.

    Language priority:
    1. Manual transcript in preferred languages (with regional variants)
    2. Generated transcript in preferred languages
    3. Any transcript, translated to preferred language if possible
    4. Any transcript as-is

    Returns full transcript as a single string, or None if unavailable.
    """
    try:
        transcript_list = _ytt_api.list(video_id)
    except Exception:
        return None

    # Build language preference order with regional variants
    base_preferred = []
    if language:
        base_preferred.append(language)
    base_preferred.append("en")
    preferred = _expand_language_codes(base_preferred)

    # Try manually created transcripts in preferred languages
    transcript = None
    try:
        transcript = transcript_list.find_manually_created_transcript(preferred)
    except Exception:
        pass

    # Fall back to generated transcripts in preferred languages
    if transcript is None:
        try:
            transcript = transcript_list.find_generated_transcript(preferred)
        except Exception:
            pass

    # If no preferred language found, try to translate any available transcript
    if transcript is None:
        target_lang = language or "en"
        try:
            for t in transcript_list:
                trans_codes = [
                    lang.language_code for lang in (t.translation_languages or [])
                ]
                if target_lang in trans_codes:
                    transcript = t.translate(target_lang)
                    break
        except Exception:
            pass

    # Last resort: take whatever is available as-is
    if transcript is None:
        try:
            for t in transcript_list:
                transcript = t
                break
        except Exception:
            return None

    if transcript is None:
        return None

    try:
        fetched = transcript.fetch()
        text_parts = [snippet.text for snippet in fetched]
        return " ".join(text_parts)
    except Exception as e:
        print_error(f"Failed to fetch transcript for {video_id}: {e}")
        return None
