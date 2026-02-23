"""YouTube transcript extraction with fallback for Cloud environments.

Primary: youtube-transcript-api (Innertube API, may be blocked on cloud IPs)
Fallback: Innertube player API with alternative client identities (less restricted)
"""

import json
import re

import requests
from youtube_transcript_api import YouTubeTranscriptApi

from _utils import print_error

_ytt_api = YouTubeTranscriptApi()

_INNERTUBE_CLIENTS = [
    {
        "name": "TV_EMBEDDED",
        "context": {
            "client": {
                "clientName": "TVHTML5_SIMPLY_EMBEDDED_PLAYER",
                "clientVersion": "2.0",
                "hl": "en",
            },
            "thirdParty": {"embedUrl": "https://www.google.com"},
        },
    },
    {
        "name": "WEB_CREATOR",
        "context": {
            "client": {
                "clientName": "WEB_CREATOR",
                "clientVersion": "1.20240723.00.00",
                "hl": "en",
            },
        },
    },
    {
        "name": "MWEB",
        "context": {
            "client": {
                "clientName": "MWEB",
                "clientVersion": "2.20240726.01.00",
                "hl": "en",
            },
        },
    },
]

_PLAYER_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "X-YouTube-Client-Name": "1",
    "X-YouTube-Client-Version": "2.20240726.01.00",
    "Origin": "https://www.youtube.com",
    "Referer": "https://www.youtube.com/",
}


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


def _try_ytt_api(video_id: str, language: str = None) -> str | None:
    """Try extracting transcript via youtube-transcript-api (Innertube)."""
    try:
        transcript_list = _ytt_api.list(video_id)
    except Exception as e:
        print_error(f"[ytt_api] list failed for {video_id}: {e}")
        return None

    base_preferred = []
    if language:
        base_preferred.append(language)
    base_preferred.append("en")
    preferred = _expand_language_codes(base_preferred)

    transcript = None
    try:
        transcript = transcript_list.find_manually_created_transcript(preferred)
    except Exception as e:
        print_error(f"[ytt_api] no manual transcript for {video_id}: {e}")

    if transcript is None:
        try:
            transcript = transcript_list.find_generated_transcript(preferred)
        except Exception as e:
            print_error(f"[ytt_api] no generated transcript for {video_id}: {e}")

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
        except Exception as e:
            print_error(f"[ytt_api] translation fallback failed for {video_id}: {e}")

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
        print_error(f"[ytt_api] fetch failed for {video_id}: {e}")
        return None


def _select_caption_track(
    captions: list[dict], language: str | None
) -> dict | None:
    """Select the best caption track based on language preference."""
    preferred = []
    if language:
        preferred.append(language)
    preferred.append("en")
    preferred = _expand_language_codes(preferred)

    for pref_lang in preferred:
        for track in captions:
            if track.get("languageCode", "") == pref_lang:
                return track
            vss_id = track.get("vssId", "")
            if pref_lang in vss_id:
                return track

    return captions[0] if captions else None


def _fetch_caption_text(base_url: str) -> str | None:
    """Download caption data from a baseUrl and extract text."""
    separator = "&" if "?" in base_url else "?"
    caption_url = f"{base_url}{separator}fmt=json3"
    resp = requests.get(caption_url, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    text_parts = []
    for event in data.get("events", []):
        for seg in event.get("segs", []):
            text = seg.get("utf8", "").strip()
            if text and text != "\n":
                text_parts.append(text)

    return " ".join(text_parts) if text_parts else None


def _try_innertube_player(video_id: str, language: str = None) -> str | None:
    """Fallback: use Innertube player API with alternative client identities.

    Tries multiple client configurations (TV_EMBEDDED, WEB_CREATOR, MWEB)
    which may have less aggressive IP blocking than the default WEB client.
    """
    player_url = "https://www.youtube.com/youtubei/v1/player"

    for client_cfg in _INNERTUBE_CLIENTS:
        client_name = client_cfg["name"]
        try:
            payload = {
                "context": client_cfg["context"],
                "videoId": video_id,
            }

            resp = requests.post(
                player_url,
                json=payload,
                headers=_PLAYER_HEADERS,
                timeout=15,
            )
            resp.raise_for_status()
            player_response = resp.json()

            # Check playability
            playability = player_response.get("playabilityStatus", {})
            status = playability.get("status", "")
            if status != "OK":
                reason = playability.get("reason", "unknown")
                print_error(
                    f"[innertube:{client_name}] {video_id} not playable: "
                    f"{status} - {reason}"
                )
                continue

            # Extract caption tracks
            captions = (
                player_response.get("captions", {})
                .get("playerCaptionsTracklistRenderer", {})
                .get("captionTracks", [])
            )
            if not captions:
                print_error(
                    f"[innertube:{client_name}] no caption tracks for {video_id}"
                )
                continue

            track = _select_caption_track(captions, language)
            if not track:
                print_error(
                    f"[innertube:{client_name}] no matching track for {video_id}"
                )
                continue

            base_url = track.get("baseUrl", "")
            if not base_url:
                print_error(
                    f"[innertube:{client_name}] no baseUrl for {video_id}"
                )
                continue

            text = _fetch_caption_text(base_url)
            if text:
                print_error(
                    f"[innertube:{client_name}] success for {video_id} "
                    f"({len(text)} chars)"
                )
                return text

            print_error(
                f"[innertube:{client_name}] no text segments for {video_id}"
            )

        except Exception as e:
            print_error(f"[innertube:{client_name}] failed for {video_id}: {e}")
            continue

    return None


def _try_direct_page(video_id: str, language: str = None) -> str | None:
    """Last resort: fetch YouTube watch page and parse caption URLs.

    Uses consent cookies. Only works if YouTube doesn't show a login wall.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    session = requests.Session()
    session.headers.update(headers)
    session.cookies.set("CONSENT", "PENDING+987", domain=".youtube.com")
    session.cookies.set(
        "SOCS",
        "CAISNQgDEitib3FfaWRlbnRpdHlfZnJvbnRlbmRfdWlzZXJ2ZXJfMjAyMzA4MjkuMDdfcDAGEAE",
        domain=".youtube.com",
    )

    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        html = resp.text

        if "accounts.google.com/ServiceLogin" in html:
            print_error(f"[direct_page] login wall for {video_id}")
            return None

        # Extract ytInitialPlayerResponse
        match = re.search(
            r"ytInitialPlayerResponse\s*=\s*(\{.+?\})\s*;\s*(?:var|const|let|</script>)",
            html,
            re.DOTALL,
        )
        if not match:
            match = re.search(
                r"ytInitialPlayerResponse\s*=\s*(\{.*?\})\s*;",
                html,
            )
        if not match:
            print_error(f"[direct_page] no playerResponse for {video_id}")
            return None

        player_response = json.loads(match.group(1))

        captions = (
            player_response.get("captions", {})
            .get("playerCaptionsTracklistRenderer", {})
            .get("captionTracks", [])
        )
        if not captions:
            print_error(f"[direct_page] no caption tracks for {video_id}")
            return None

        track = _select_caption_track(captions, language)
        if not track or not track.get("baseUrl"):
            print_error(f"[direct_page] no usable track for {video_id}")
            return None

        text = _fetch_caption_text(track["baseUrl"])
        if text:
            return text

        print_error(f"[direct_page] no text segments for {video_id}")
        return None

    except Exception as e:
        print_error(f"[direct_page] failed for {video_id}: {e}")
        return None


def get_transcript(video_id: str, language: str = None) -> str | None:
    """Extract transcript text from a YouTube video.

    Uses a three-stage fallback strategy:
    1. youtube-transcript-api (Innertube WEB client) - works locally
    2. Innertube player API with alt clients (TV_EMBEDDED, WEB_CREATOR, MWEB)
    3. Direct YouTube page parsing with consent cookies

    Returns full transcript as a single string, or None if unavailable.
    """
    result = _try_ytt_api(video_id, language)
    if result:
        return result

    print_error(
        f"[get_transcript] ytt_api failed, trying innertube player for {video_id}"
    )
    result = _try_innertube_player(video_id, language)
    if result:
        return result

    print_error(
        f"[get_transcript] innertube failed, trying direct page for {video_id}"
    )
    result = _try_direct_page(video_id, language)
    if result:
        return result

    print_error(f"[get_transcript] all methods failed for {video_id}")
    return None
