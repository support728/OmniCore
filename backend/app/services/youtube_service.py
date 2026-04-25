from __future__ import annotations

import json
import re
from typing import Any

import requests

from .response_style import format_conversational_response


YOUTUBE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def _extract_json_block(source: str, marker: str) -> dict[str, Any] | None:
    marker_index = source.find(marker)
    if marker_index == -1:
        return None

    start_index = source.find("{", marker_index)
    if start_index == -1:
        return None

    depth = 0
    in_string = False
    escaped = False

    for index in range(start_index, len(source)):
        character = source[index]

        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue

        if character == '"':
            in_string = True
            continue

        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(source[start_index : index + 1])
                except json.JSONDecodeError:
                    return None

    return None


def _extract_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()

    if not isinstance(value, dict):
        return ""

    simple_text = value.get("simpleText")
    if isinstance(simple_text, str):
        return simple_text.strip()

    runs = value.get("runs")
    if isinstance(runs, list):
        return "".join(str(run.get("text") or "") for run in runs).strip()

    return ""


def _iter_video_renderers(node: Any):
    if isinstance(node, dict):
        video_renderer = node.get("videoRenderer")
        if isinstance(video_renderer, dict):
            yield video_renderer

        for value in node.values():
            yield from _iter_video_renderers(value)
        return

    if isinstance(node, list):
        for item in node:
            yield from _iter_video_renderers(item)


def _build_video_result(video_renderer: dict[str, Any]) -> dict[str, str] | None:
    video_id = str(video_renderer.get("videoId") or "").strip()
    if not video_id:
        return None

    title = _extract_text(video_renderer.get("title")) or "YouTube video"
    channel = _extract_text(video_renderer.get("ownerText"))
    duration = _extract_text(video_renderer.get("lengthText"))
    published = _extract_text(video_renderer.get("publishedTimeText"))
    views = _extract_text(video_renderer.get("viewCountText"))

    thumbnail_url = ""
    thumbnail_data = video_renderer.get("thumbnail")
    if isinstance(thumbnail_data, dict):
        thumbnails = thumbnail_data.get("thumbnails")
        if isinstance(thumbnails, list) and thumbnails:
            thumbnail_url = str(thumbnails[-1].get("url") or "").strip()

    snippet_parts: list[str] = []
    for value in [channel, duration, published, views]:
        cleaned = value.strip()
        if cleaned:
            snippet_parts.append(cleaned)

    return {
        "videoId": video_id,
        "title": title,
        "channel": channel,
        "thumbnail": thumbnail_url or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "embedUrl": f"https://www.youtube-nocookie.com/embed/{video_id}",
        "snippet": " • ".join(snippet_parts) or "Watch this video inside OmniCore.",
    }


def _fallback_video_results(query: str) -> list[dict[str, str]]:
    cleaned_query = (query or "").strip()
    if not cleaned_query:
        return []

    normalized_id = re.sub(r"[^a-zA-Z0-9_-]", "", cleaned_query.replace(" ", ""))[:11]
    if len(normalized_id) < 11:
        normalized_id = f"{normalized_id}omnicore"[:11].ljust(11, "x")

    return [
        {
            "videoId": normalized_id,
            "title": f'YouTube results for "{cleaned_query}"',
            "channel": "YouTube",
            "thumbnail": f"https://i.ytimg.com/vi/{normalized_id}/hqdefault.jpg",
            "url": f"https://www.youtube.com/results?search_query={requests.utils.quote(cleaned_query)}",
            "embedUrl": f"https://www.youtube.com/embed?listType=search&list={requests.utils.quote(cleaned_query)}",
            "snippet": f'Showing a fallback YouTube search view for "{cleaned_query}" inside OmniCore.',
        }
    ]


def summarize_youtube_results(query: str, results: list[dict[str, str]]) -> str:
    cleaned_query = (query or "").strip()
    if not cleaned_query:
        return ""

    if not results:
        return format_conversational_response(f'I could not find YouTube videos for "{cleaned_query}" right now.')

    channels = [result.get("channel", "").strip() for result in results[:3] if result.get("channel")]
    unique_channels: list[str] = []
    for channel in channels:
        if channel and channel not in unique_channels:
            unique_channels.append(channel)

    if unique_channels:
        return format_conversational_response(
            f'The top YouTube picks for "{cleaned_query}" are below. A couple good starting points are from {", ".join(unique_channels[:2])}.'
        )

    return format_conversational_response(f'The top YouTube videos for "{cleaned_query}" are ready below.')


def search_youtube_videos(query: str) -> list[dict[str, str]]:
    cleaned_query = (query or "").strip()
    if not cleaned_query:
        return []

    try:
        response = requests.get(
            "https://www.youtube.com/results",
            params={"search_query": cleaned_query},
            headers=YOUTUBE_HEADERS,
            timeout=8,
        )
        response.raise_for_status()
        html = response.text
    except Exception:
        return _fallback_video_results(cleaned_query)

    payload = (
        _extract_json_block(html, "var ytInitialData =")
        or _extract_json_block(html, "window['ytInitialData'] =")
        or _extract_json_block(html, 'window["ytInitialData"] =')
    )
    if not payload:
        return _fallback_video_results(cleaned_query)

    results: list[dict[str, str]] = []
    seen_video_ids: set[str] = set()

    for video_renderer in _iter_video_renderers(payload):
        video = _build_video_result(video_renderer)
        if not video:
            continue

        video_id = video["videoId"]
        if video_id in seen_video_ids:
            continue

        seen_video_ids.add(video_id)
        results.append(video)
        if len(results) >= 6:
            break

    return results or _fallback_video_results(cleaned_query)