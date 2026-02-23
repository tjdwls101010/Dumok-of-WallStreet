"""YouTube Data API wrapper using python-youtube (pyyoutube)."""

from pyyoutube import Client

from _utils import iso_duration_to_readable, truncate


def search_videos(
    api_key: str,
    query: str,
    max_results: int = 10,
    published_after: str = None,
    published_before: str = None,
    order: str = "relevance",
    language: str = None,
    duration: str = None,
    region: str = None,
) -> list[dict]:
    """Search YouTube videos and return basic metadata.

    Returns list of dicts with: video_id, title, description,
    date_published, channel_id, channel_name.
    """
    client = Client(api_key=api_key)

    kwargs = {
        "q": query,
        "type": "video",
        "max_results": max_results,
        "order": order,
    }
    if published_after:
        kwargs["published_after"] = published_after
    if published_before:
        kwargs["published_before"] = published_before
    if language:
        kwargs["relevance_language"] = language
    if duration:
        kwargs["video_duration"] = duration
    if region:
        kwargs["region_code"] = region

    response = client.search.list(**kwargs)

    results = []
    for item in response.items:
        results.append(
            {
                "video_id": item.id.videoId,
                "url": f"https://www.youtube.com/watch?v={item.id.videoId}",
                "title": item.snippet.title,
                "description": item.snippet.description or "",
                "date_published": (
                    item.snippet.publishedAt[:10] if item.snippet.publishedAt else ""
                ),
                "channel_id": item.snippet.channelId,
                "channel_name": item.snippet.channelTitle or "",
            }
        )

    return results


def get_video_details(api_key: str, video_ids: list[str]) -> dict:
    """Get video details (viewCount, likeCount, duration) for a list of video IDs.

    Returns dict mapping video_id -> {view_count, like_count, duration}.
    """
    if not video_ids:
        return {}

    client = Client(api_key=api_key)

    # API allows up to 50 IDs per request
    details = {}
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i : i + 50]
        response = client.videos.list(
            video_id=",".join(batch), parts=["statistics", "contentDetails"]
        )
        for item in response.items:
            vid = item.id
            stats = item.statistics or {}
            content = item.contentDetails or {}

            details[vid] = {
                "view_count": int(getattr(stats, "viewCount", 0) or 0),
                "like_count": int(getattr(stats, "likeCount", 0) or 0),
                "duration": iso_duration_to_readable(
                    getattr(content, "duration", "") or ""
                ),
            }

    return details


def get_channel_descriptions(api_key: str, channel_ids: list[str]) -> dict:
    """Get channel descriptions for a list of channel IDs.

    Returns dict mapping channel_id -> truncated description (200 chars).
    """
    if not channel_ids:
        return {}

    client = Client(api_key=api_key)

    descriptions = {}
    unique_ids = list(set(channel_ids))

    for i in range(0, len(unique_ids), 50):
        batch = unique_ids[i : i + 50]
        response = client.channels.list(
            channel_id=",".join(batch), parts=["snippet"]
        )
        for item in response.items:
            desc = getattr(item.snippet, "description", "") or ""
            descriptions[item.id] = truncate(desc, 200)

    return descriptions
