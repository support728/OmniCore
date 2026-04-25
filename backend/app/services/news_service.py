
import re
import logging
import urllib.parse
from datetime import datetime
import os
import requests

# --- Dependency restoration ---
from ..config import get_settings
from .ai_service import get_ai_reply
from .finance_service import get_finance_reply
from .memory_service import (
    answer_memory_question,
    append_message,
    build_memory_acknowledgement,
    build_relevant_user_memory_context,
    get_user_memory,
    is_memory_statement,
    remember_news_context,
    get_session_value,
    set_session_value,
    get_last_tool,
)
from .web_search_service import search_web_results, summarize_search_results
from .youtube_service import search_youtube_videos, summarize_youtube_results
from .weather_service import get_weather_reply, build_weather_actions
# from .response_style import format_weather_reply, format_weather_insight
from .memory_store import get_last_weather_city, set_last_weather_city
from .search_intelligence import normalize_and_rank_results, build_answer_first_summary

# Logger setup
logger = logging.getLogger(__name__)

# Constants (stubbed if missing)
FOLLOW_UP_PREFIXES = ("what about", "how about", "and ", "also ")
WEATHER_FOLLOW_UP_TERMS = ("weather", "forecast", "temperature")
WEATHER_TERMS = ("weather", "forecast", "temperature")
NEWS_TERMS = ("news", "headline", "headlines", "happening", "latest", "current events")


# Stubs for missing functions (if not defined elsewhere)
def get_last_weather_city(session_id):
    return ""

def set_last_weather_city(session_id, city):
    pass

def format_weather_reply(weather):
    return str(weather)

def search_web(query):
    return {}

def get_news(query: str):
    api_key = os.getenv("NEWS_API_KEY")

    if not api_key:
        return [
                {"title": "ERROR: NEWS_API_KEY not set", "url": ""}
            ]
        print("DEBUG weather:", weather)
        if isinstance(weather, str):
            return {
                "type": "error",
                "message": weather
            }
        if not isinstance(weather, dict):
            return {
                "type": "error",
                "message": "Invalid weather response"
            }
        city_line = weather.get("city", "Unknown")
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "sortBy": "publishedAt",
                "language": "en",
                "pageSize": 3,
                "apiKey": api_key,
            }

            response = requests.get(url, params=params, timeout=5)

            if response.status_code != 200:
                return [
                    {"title": f"API error: {response.status_code}", "url": ""}
                ]

            data = response.json()

            articles = data.get("articles", [])

            if not articles:
                return [
                    {"title": "No news found", "url": ""}
                ]

            results = []
            for a in articles:
                results.append({
                    "title": a.get("title", "No title"),
                    "url": a.get("url", "")
                })

            return results

        except Exception as e:
            return [
                {"title": f"Exception: {str(e)}", "url": ""}
            ]




def _strip_search_command(query: str):
    cleaned = (query or "").strip()
    cleaned = re.sub(
        r"^(?:search(?:\s+the)?\s+(?:web|internet)\s+for|search\s+for|look\s+up|find\s+online|google|open)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s+on\s+(?:the\s+)?web$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+online$", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip().rstrip("?!.,")


def _extract_copy_text(query: str):
    match = re.search(r"^(?:copy|copy this|copy the following)[:\s]+(.+)$", (query or "").strip(), re.IGNORECASE)
    if not match:
        return ""

    return match.group(1).strip().rstrip("?!")


def _extract_weather_city(query: str):
    patterns = [
        r"(?:open|show|get)\s+(?:the\s+)?weather\s+(?:in|for)\s+(.+)$",
        r"(?:open|show|get)\s+(?:forecast|temperature)\s+(?:in|for)\s+(.+)$",
    ]

    for pattern in patterns:
        match = re.search(pattern, (query or "").strip(), re.IGNORECASE)
        if match and match.group(1).strip():
            return match.group(1).strip().rstrip("?!.,")

    return ""


def _extract_youtube_query(query: str):
    cleaned = (query or "").strip()
    if not cleaned:
        return ""

    lowered = cleaned.lower()
    if "youtube" not in lowered:
        return ""

    before_youtube, after_youtube = re.split(r"youtube", cleaned, maxsplit=1, flags=re.IGNORECASE)
    after_youtube = after_youtube.strip()
    before_youtube = before_youtube.strip()

    if after_youtube:
        if after_youtube.lower().startswith("for "):
            after_youtube = after_youtube[4:].strip()
        after_youtube = re.sub(r"^(?:search|search for|videos|video|shorts|short)\s+", "", after_youtube, flags=re.IGNORECASE)
        after_youtube = re.sub(r"\s+and\s+(?:the\s+)?web$", "", after_youtube, flags=re.IGNORECASE)
        normalized_after = after_youtube.strip().rstrip("?!.,")
        if normalized_after and normalized_after.lower() not in {"search", "youtube", "videos", "video", "shorts", "short"}:
            return normalized_after

    if " for " in before_youtube.lower():
        before_youtube = re.split(r"\bfor\b", before_youtube, maxsplit=1, flags=re.IGNORECASE)[1].strip()

    before_youtube = re.sub(r"\bon$", "", before_youtube, flags=re.IGNORECASE).strip()
    normalized_before = _strip_search_command(before_youtube)
    if normalized_before and normalized_before.lower() not in {"search", "youtube", "videos", "video", "shorts", "short"}:
        return normalized_before

    return ""


def _is_youtube_search_request(query: str):
    lowered = (query or "").lower()
    if not lowered:
        return False

    normalized = lowered.strip()
    if normalized == "youtube" or normalized.startswith("youtube "):
        return True

    return any(
        phrase in lowered
        for phrase in [
            "search youtube",
            "on youtube",
            "youtube search",
            "find videos",
            "find video",
            "videos about",
            "video about",
            "youtube shorts",
            "shorts on youtube",
            "shorts about",
        ]
    )


def _build_youtube_search_execution(query: str):
    youtube_query = _extract_youtube_query(query)
    if not youtube_query:
        return None

    logger.info("YouTube intent detected: %s", youtube_query)

    return {
        "type": "youtube_search",
        "query": youtube_query,
        "label": "Show YouTube results",
        "success_summary": f'Showing YouTube results for "{youtube_query}" inside OmniCore.',
        "blocked_summary": "OmniCore could not load the YouTube view.",
        "success_insight": f'YouTube results for "{youtube_query}" are loading in the OmniCore workspace.',
        "blocked_insight": "Try the request again if the embedded YouTube view does not load correctly.",
        "tool": "search",
    }


def _extract_web_query(query: str):
    cleaned = (query or "").strip()
    if not cleaned:
        return ""

    if re.match(r"^search\s+google$", cleaned, re.IGNORECASE):
        return ""

    if re.match(r"^search(?:\s+the)?\s+internet$", cleaned, re.IGNORECASE):
        return ""

    if re.match(r"^search\s+for$", cleaned, re.IGNORECASE):
        return ""

    if re.match(r"^look\s+up$", cleaned, re.IGNORECASE):
        return ""

    if re.match(r"^find\s+information\s+on$", cleaned, re.IGNORECASE):
        return ""

    explicit_match = re.search(
        r"(?:search(?:\s+the)?\s+(?:web|internet)\s+for|search\s+google\s+for|search\s+for|look\s+up|find\s+information\s+on|find\s+online|google)\s+(.+)$",
        cleaned,
        re.IGNORECASE,
    )
    if explicit_match and explicit_match.group(1).strip():
        web_query = explicit_match.group(1).strip()
        web_query = re.sub(r"\s+on\s+youtube$", "", web_query, flags=re.IGNORECASE)
        web_query = re.sub(r"\s+on\s+youtube\s+and\s+(?:the\s+)?web$", "", web_query, flags=re.IGNORECASE)
        return web_query.strip().rstrip("?!.,")

    if re.search(r"\b(?:web|internet)\b", cleaned, re.IGNORECASE):
        return _strip_search_command(cleaned.replace("web", "", 1).replace("internet", "", 1))

    return ""


def _is_explicit_web_search_request(query: str):
    cleaned = (query or "").strip().lower()
    if not cleaned:
        return False

    return any(
        cleaned.startswith(prefix)
        for prefix in [
            "search the internet",
            "search internet",
            "search google",
            "look up",
            "find information on",
            "search for",
        ]
    )


def _build_web_search_execution(query: str):
    web_query = _extract_web_query(query)
    if not web_query:
        return None

    logger.info("Web search intent detected: %s", web_query)

    return {
        "type": "web_search",
        "query": web_query,
        "label": "Show web results",
        "success_summary": f'Searching the web for "{web_query}" inside OmniCore.',
        "blocked_summary": "OmniCore could not load the web search results.",
        "success_insight": f'Web results for "{web_query}" stay inside the OmniCore workspace.',
        "blocked_insight": "Try the request again if the in-app web results do not load correctly.",
        "tool": "search",
    }


def _extract_map_query(query: str):
    match = re.search(r"(?:maps?|directions?\s+to|show\s+.+\s+on\s+map|where\s+is)\s+(.+)$", query, re.IGNORECASE)
    if not match:
        return ""

    return match.group(1).strip().rstrip("?!.,")


def _detect_media_kind(query: str):
    lowered = (query or "").lower()
    image_terms = any(term in lowered for term in ["image", "images", "picture", "photo", "art", "logo"])
    video_terms = any(term in lowered for term in ["video", "videos", "clip", "movie", "animation", "reel"])

    if image_terms and video_terms:
        return "both"
    if image_terms:
        return "image"
    if video_terms:
        return "video"

    return None


def _extract_media_subject(query: str):
    match = re.search(
        r"(?:create|make|generate|produce|build)\s+(?:an?|the)?\s*(?:image|images|picture|photo|art|logo|video|videos|clip|movie|animation|reel)?\s*(?:of|about|for)?\s*(.+)$",
        (query or "").strip(),
        re.IGNORECASE,
    )
    if match and match.group(1).strip():
        return match.group(1).strip().rstrip("?!.,")

    return ""


def _extract_media_prompt_subject(query: str):
    match = re.search(
        r"(?:turn|convert|make|write)\s+.+?\s+into\s+(?:an?\s+)?(?:image|video)?\s*prompt\s*(?:for|about|of)?\s*(.+)$",
        (query or "").strip(),
        re.IGNORECASE,
    )
    if match and match.group(1).strip():
        return match.group(1).strip().rstrip("?!.,")

    return ""


def _extract_media_style_profile(query: str):
    lowered = (query or "").lower()
    style_tokens = []

    if any(term in lowered for term in ["anime", "manga"]):
        style_tokens.append("anime illustration")
    if any(term in lowered for term in ["realistic", "photorealistic", "photo realistic", "photo-realistic"]):
        style_tokens.append("photorealistic")
    if any(term in lowered for term in ["3d", "3-d", "cgi", "rendered"]):
        style_tokens.append("3D render")
    if any(term in lowered for term in ["cinematic", "film", "movie-like"]):
        style_tokens.append("cinematic")
    if any(term in lowered for term in ["illustration", "illustrated"]):
        style_tokens.append("digital illustration")

    aspect_ratio = "16:9"
    if any(term in lowered for term in ["vertical", "portrait", "short", "reel", "tiktok"]):
        aspect_ratio = "9:16"
    elif any(term in lowered for term in ["square", "instagram post"]):
        aspect_ratio = "1:1"
    elif any(term in lowered for term in ["wide", "landscape", "youtube thumbnail", "horizontal"]):
        aspect_ratio = "16:9"

    return {
        "style_tokens": style_tokens,
        "aspect_ratio": aspect_ratio,
        "is_vertical": aspect_ratio == "9:16",
    }


def _extract_media_platform(query: str):
    lowered = (query or "").lower()
    if "midjourney" in lowered:
        return "midjourney"
    if "flux" in lowered:
        return "flux"
    if "runway" in lowered:
        return "runway"
    if "kling" in lowered:
        return "kling"
    if "sora" in lowered:
        return "sora"

    return ""


def _is_media_creation_query(query: str):
    lowered = (query or "").lower()
    media_kind = _detect_media_kind(query)
    if not media_kind:
        return False

    return any(term in lowered for term in ["create", "make", "generate", "produce", "how to", "prompt"])


def _is_media_prompt_request(query: str):
    lowered = (query or "").lower()
    return "prompt" in lowered and any(term in lowered for term in ["turn", "convert", "make", "write", "create"])

class get_conversation:
    def __init__(self, session_id):
        self.session_id = session_id

    def __call__(self, *args, **kwargs):
        raise NotImplementedError


def _get_recent_media_idea(session_id: str):
    conversation = get_conversation(session_id)
    for message in reversed(conversation[:-1]):
        if message.get("role") != "user":
            continue

        content = str(message.get("content") or "").strip()
        if not content or _is_media_prompt_request(content):
            continue

        if _detect_media_kind(content) or _extract_media_subject(content):
            return content

    return ""


def _merge_media_style_profile(primary, fallback):
    primary = primary if isinstance(primary, dict) else {}
    fallback = fallback if isinstance(fallback, dict) else {}

    merged_tokens = []
    for token in primary.get("style_tokens", []) + fallback.get("style_tokens", []):
        if token and token not in merged_tokens:
            merged_tokens.append(token)

    return {
        "style_tokens": merged_tokens,
        "aspect_ratio": primary.get("aspect_ratio") or fallback.get("aspect_ratio") or "16:9",
        "is_vertical": bool(primary.get("is_vertical") or fallback.get("is_vertical")),
    }


def _build_media_tags(media_kind: str, subject: str, style_profile=None, platform: str = ""):
    profile = style_profile if isinstance(style_profile, dict) else {}
    tags = []

    if media_kind:
        tags.append(f"Mode: {media_kind.capitalize()}")
    if platform:
        tags.append(f"Platform: {platform.capitalize()}")
    if subject:
        tags.append(f"Subject: {subject}")
    for token in profile.get("style_tokens", []):
        tags.append(f"Style: {token}")
    aspect_ratio = profile.get("aspect_ratio")
    if aspect_ratio:
        tags.append(f"Aspect: {aspect_ratio}")

    return tags


def _normalize_media_platform(platform: str | None):
    value = (platform or "").strip().lower()
    if value in {"midjourney", "flux", "runway", "kling", "sora"}:
        return value

    return ""


def _build_image_negative_prompt(platform: str = ""):
    common = "blurry details, distorted anatomy, extra limbs, duplicate subjects, muddy lighting, unreadable text, low-resolution artifacts"
    if platform == "midjourney":
        return f"--no {common}, oversaturated highlights, flat composition"
    if platform == "flux":
        return f"Negative prompt: {common}, plastic skin texture, overprocessed contrast"

    return ""


def _build_video_duration(style_profile=None, platform: str = ""):
    profile = style_profile if isinstance(style_profile, dict) else {}
    if platform == "runway":
        return "6 to 8 seconds"
    if platform == "kling":
        return "8 to 10 seconds"
    if platform == "sora":
        return "10 to 12 seconds"
    if profile.get("is_vertical"):
        return "8 to 10 seconds"

    return "8 seconds"


def _build_video_lens_notes(style_profile=None, platform: str = ""):
    profile = style_profile if isinstance(style_profile, dict) else {}
    if platform == "runway":
        return "Lens: 35mm cinematic lens, shallow depth of field, stabilized framing"
    if platform == "kling":
        return "Lens: 28mm dynamic wide lens, energetic perspective, crisp subject separation"
    if platform == "sora":
        return "Lens: 50mm natural perspective, realistic depth falloff, filmic motion blur"
    if profile.get("is_vertical"):
        return "Lens: 35mm vertical composition, centered subject, clean foreground separation"

    return "Lens: 35mm cinematic lens, balanced depth of field"


def _build_video_camera_notes(style_profile=None, platform: str = ""):
    profile = style_profile if isinstance(style_profile, dict) else {}
    if platform == "runway":
        return "Camera: slow dolly-in, stable framing, subtle parallax, smooth focus transitions"
    if platform == "kling":
        return "Camera: cinematic tracking shot with expressive motion and smooth speed ramp"
    if platform == "sora":
        return "Camera: physically plausible handheld-to-dolly transition with realistic inertia and depth"
    if profile.get("is_vertical"):
        return "Camera: vertical framing, center-weighted composition, smooth upward reveal"

    return "Camera: cinematic movement with stable framing"


def _build_image_prompt(subject: str, style_profile=None, platform: str = ""):
    idea = subject or "futuristic city skyline at dawn"
    profile = style_profile if isinstance(style_profile, dict) else {}
    style_tokens = profile.get("style_tokens", [])
    aspect_ratio = profile.get("aspect_ratio", "16:9")
    visual_style = ", ".join(style_tokens) if style_tokens else "cinematic"

    if platform == "midjourney":
        return (
            f"{idea}, {visual_style}, cinematic composition, detailed environment, intentional color palette, dramatic lighting, "
            f"high detail, clean focal point, depth of field, professional quality --ar {aspect_ratio} --stylize 250 --quality 1"
        )

    if platform == "flux":
        return (
            f"{idea}, {visual_style}, highly controlled composition, rich material detail, cinematic lighting, "
            f"clean focal hierarchy, polished color separation, professional quality, aspect ratio {aspect_ratio}"
        )

    return (
        f"{idea}, {visual_style}, cinematic composition, detailed environment, intentional color palette, "
        f"dramatic lighting, high detail, clean focal point, depth of field, professional quality, aspect ratio {aspect_ratio}"
    )


def _build_video_prompt(subject: str, style_profile=None, platform: str = ""):
    idea = subject or "astronaut walking through a neon alley"
    profile = style_profile if isinstance(style_profile, dict) else {}
    style_tokens = profile.get("style_tokens", [])
    aspect_ratio = profile.get("aspect_ratio", "16:9")
    visual_style = ", ".join(style_tokens) if style_tokens else "cinematic"
    shot_duration = _build_video_duration(profile, platform)

    if platform == "runway":
        return (
            f"Scene: {idea}. Style: {visual_style}. Camera: cinematic movement with stable framing. Motion: clear subject motion and natural secondary motion. "
            f"Lighting: dramatic and polished. Duration: {shot_duration}. Output: aspect ratio {aspect_ratio}, professional quality."
        )

    if platform == "kling":
        return (
            f"{idea}, {visual_style}, vivid environment detail, expressive subject motion, cinematic camera move, dramatic lighting, "
            f"smooth pacing, duration {shot_duration}, aspect ratio {aspect_ratio}, polished output"
        )

    if platform == "sora":
        return (
            f"{idea}, {visual_style}, realistic physical motion, coherent environment interaction, cinematic camera choreography, "
            f"dramatic lighting, polished color grading, duration {shot_duration}, professional quality, aspect ratio {aspect_ratio}"
        )

    return (
        f"{idea}, {visual_style}, clear subject motion, cinematic camera movement, strong environment detail, natural secondary motion, "
        f"dramatic lighting, polished color grading, duration {shot_duration}, smooth pacing, professional quality, aspect ratio {aspect_ratio}"
    )


def _format_image_prompt_output(prompt: str, platform: str = ""):
    negative_prompt = _build_image_negative_prompt(platform)
    platform_label = platform.capitalize() if platform else "General"
    if not negative_prompt:
        return f"{platform_label} image prompt:\n{prompt}"

    return f"{platform_label} image prompt:\n{prompt}\n\n{negative_prompt}"


def _format_video_prompt_output(prompt: str, style_profile=None, platform: str = ""):
    camera_notes = _build_video_camera_notes(style_profile, platform)
    lens_notes = _build_video_lens_notes(style_profile, platform)
    platform_label = platform.capitalize() if platform else "General"
    return f"{platform_label} video prompt:\n{prompt}\n\n{camera_notes}\n{lens_notes}"


def _build_media_prompt_sections(media_kind: str, image_prompt_output: str = "", video_prompt_output: str = "", platform: str = ""):
    sections = []
    platform_label = platform.capitalize() if platform else "General"

    if image_prompt_output:
        sections.append(
            {
                "title": f"{platform_label} Image Prompt",
                "body": image_prompt_output,
            }
        )

    if video_prompt_output:
        sections.append(
            {
                "title": f"{platform_label} Video Prompt",
                "body": video_prompt_output,
            }
        )

    if media_kind == "both" and image_prompt_output and video_prompt_output:
        sections.append(
            {
                "title": "Copy Strategy",
                "body": "Use Copy all prompts if you want the complete image and video package in one clipboard payload.",
            }
        )

    return sections


def _append_provider_reset_action(actions: list[str], platform: str = ""):
    if platform and "Use automatic provider" not in actions:
        actions.append("Use automatic provider")

    return actions


def _get_search_summary(search_result: object) -> str:
    if isinstance(search_result, dict):
        return str(search_result.get("summary") or "")

    return str(search_result or "")


def _get_media_prompt_generation_reply(query: str, session_id: str):
    if not _is_media_prompt_request(query):
        return None

    explicit_kind = _detect_media_kind(query)
    remembered_kind = get_session_value(session_id, "last_media_kind")
    media_kind = explicit_kind or (remembered_kind if remembered_kind in {"image", "video", "both"} else None)
    if not media_kind:
        return None

    subject = _extract_media_prompt_subject(query)
    if not subject:
        subject = str(get_session_value(session_id, "last_media_subject", "") or "").strip()
    if not subject:
        subject = _extract_media_subject(_get_recent_media_idea(session_id))

    current_style_profile = _extract_media_style_profile(query)
    remembered_style_profile = get_session_value(session_id, "last_media_style_profile")
    style_profile = _merge_media_style_profile(current_style_profile, remembered_style_profile)
    explicit_platform = _extract_media_platform(query)
    remembered_platform = _normalize_media_platform(get_session_value(session_id, "last_media_platform", ""))
    platform = explicit_platform or remembered_platform

    if media_kind == "image":
        image_prompt = _build_image_prompt(subject, style_profile, platform)
        image_prompt_output = _format_image_prompt_output(image_prompt, platform)
        image_negative_prompt = _build_image_negative_prompt(platform)
        executions = [
            {
                "type": "copy_text",
                "text": image_prompt_output,
                "label": "Copy image prompt",
                "success_summary": "Copying the image prompt to your clipboard.",
                "success_insight": "The image prompt is ready to paste into an image generator.",
                "failure_summary": "Clipboard copy failed.",
                "failure_insight": "Allow clipboard access and try again.",
                "tool": "general",
            }
        ]
        if image_negative_prompt:
            executions.append(
                {
                    "type": "copy_text",
                    "text": image_negative_prompt,
                    "label": "Copy negative prompt",
                    "success_summary": "Copying the negative prompt to your clipboard.",
                    "success_insight": "The negative prompt is ready to paste into the provider's negative field.",
                    "failure_summary": "Clipboard copy failed.",
                    "failure_insight": "Allow clipboard access and try again.",
                    "tool": "general",
                }
            )
        summary = f"Here is a ready-to-paste image prompt{f' for {subject}' if subject else ''}."
        insight = image_prompt_output
        sections = _build_media_prompt_sections(media_kind, image_prompt_output=image_prompt_output, platform=platform)
        actions = [
            "Copy image prompt",
            "Copy negative prompt",
            "Open image tools",
            "Open image tutorial",
            "Generate another image prompt",
            "Generate Midjourney prompt",
            "Generate Flux prompt",
        ]
        actions = _append_provider_reset_action(actions, platform)
    elif media_kind == "video":
        video_prompt = _build_video_prompt(subject, style_profile, platform)
        video_prompt_output = _format_video_prompt_output(video_prompt, style_profile, platform)
        video_camera_notes = _build_video_camera_notes(style_profile, platform)
        video_lens_notes = _build_video_lens_notes(style_profile, platform)
        executions = [
            {
                "type": "copy_text",
                "text": video_prompt_output,
                "label": "Copy video prompt",
                "success_summary": "Copying the video prompt to your clipboard.",
                "success_insight": "The video prompt is ready to paste into a video generator.",
                "failure_summary": "Clipboard copy failed.",
                "failure_insight": "Allow clipboard access and try again.",
                "tool": "general",
            }
            ,
            {
                "type": "copy_text",
                "text": video_camera_notes,
                "label": "Copy camera notes",
                "success_summary": "Copying the camera notes to your clipboard.",
                "success_insight": "The camera direction is ready to paste into your video prompt workflow.",
                "failure_summary": "Clipboard copy failed.",
                "failure_insight": "Allow clipboard access and try again.",
                "tool": "general",
            },
            {
                "type": "copy_text",
                "text": video_lens_notes,
                "label": "Copy lens notes",
                "success_summary": "Copying the lens notes to your clipboard.",
                "success_insight": "The lens direction is ready to paste into your video prompt workflow.",
                "failure_summary": "Clipboard copy failed.",
                "failure_insight": "Allow clipboard access and try again.",
                "tool": "general",
            }
        ]
        summary = f"Here is a ready-to-paste video prompt{f' for {subject}' if subject else ''}."
        insight = video_prompt_output
        sections = _build_media_prompt_sections(media_kind, video_prompt_output=video_prompt_output, platform=platform)
        actions = [
            "Copy video prompt",
            "Copy camera notes",
            "Copy lens notes",
            "Open video tools",
            "Open video tutorial",
            "Generate another video prompt",
            "Generate Runway prompt",
            "Generate Kling prompt",
            "Generate Sora prompt",
        ]
        actions = _append_provider_reset_action(actions, platform)
    else:
        image_prompt = _build_image_prompt(subject, style_profile, platform)
        video_prompt = _build_video_prompt(subject, style_profile, platform)
        image_prompt_output = _format_image_prompt_output(image_prompt, platform)
        video_prompt_output = _format_video_prompt_output(video_prompt, style_profile, platform)
        image_negative_prompt = _build_image_negative_prompt(platform)
        video_camera_notes = _build_video_camera_notes(style_profile, platform)
        video_lens_notes = _build_video_lens_notes(style_profile, platform)
        combined_prompt_output = f"{image_prompt_output}\n\n---\n\n{video_prompt_output}"
        executions = [
            {
                "type": "copy_text",
                "text": image_prompt_output,
                "label": "Copy image prompt",
                "success_summary": "Copying the image prompt to your clipboard.",
                "success_insight": "The image prompt is ready to paste into an image generator.",
                "failure_summary": "Clipboard copy failed.",
                "failure_insight": "Allow clipboard access and try again.",
                "tool": "general",
            },
            {
                "type": "copy_text",
                "text": image_negative_prompt or "No dedicated negative prompt for this provider.",
                "label": "Copy negative prompt",
                "success_summary": "Copying the negative prompt to your clipboard.",
                "success_insight": "The negative prompt is ready to paste into the provider's negative field.",
                "failure_summary": "Clipboard copy failed.",
                "failure_insight": "Allow clipboard access and try again.",
                "tool": "general",
            },
            {
                "type": "copy_text",
                "text": video_prompt_output,
                "label": "Copy video prompt",
                "success_summary": "Copying the video prompt to your clipboard.",
                "success_insight": "The video prompt is ready to paste into a video generator.",
                "failure_summary": "Clipboard copy failed.",
                "failure_insight": "Allow clipboard access and try again.",
                "tool": "general",
            },
            {
                "type": "copy_text",
                "text": video_camera_notes,
                "label": "Copy camera notes",
                "success_summary": "Copying the camera notes to your clipboard.",
                "success_insight": "The camera direction is ready to paste into your video prompt workflow.",
                "failure_summary": "Clipboard copy failed.",
                "failure_insight": "Allow clipboard access and try again.",
                "tool": "general",
            },
            {
                "type": "copy_text",
                "text": video_lens_notes,
                "label": "Copy lens notes",
                "success_summary": "Copying the lens notes to your clipboard.",
                "success_insight": "The lens direction is ready to paste into your video prompt workflow.",
                "failure_summary": "Clipboard copy failed.",
                "failure_insight": "Allow clipboard access and try again.",
                "tool": "general",
            },
            {
                "type": "copy_text",
                "text": combined_prompt_output,
                "label": "Copy all prompts",
                "success_summary": "Copying both prompts to your clipboard.",
                "success_insight": "The image and video prompts are ready to paste together.",
                "failure_summary": "Clipboard copy failed.",
                "failure_insight": "Allow clipboard access and try again.",
                "tool": "general",
            },
        ]
        summary = f"Here are ready-to-paste image and video prompts{f' for {subject}' if subject else ''}."
        insight = f"{image_prompt_output}\n\n---\n\n{video_prompt_output}"
        sections = _build_media_prompt_sections(
            media_kind,
            image_prompt_output=image_prompt_output,
            video_prompt_output=video_prompt_output,
            platform=platform,
        )
        actions = [
            "Copy all prompts",
            "Copy image prompt",
            "Copy negative prompt",
            "Copy video prompt",
            "Copy camera notes",
            "Copy lens notes",
            "Open image tools",
            "Open video tools",
            "Generate another image prompt",
            "Generate another video prompt",
            "Generate Midjourney prompt",
            "Generate Flux prompt",
            "Generate Runway prompt",
            "Generate Kling prompt",
            "Generate Sora prompt",
        ]
        actions = _append_provider_reset_action(actions, platform)

    if media_kind:
        set_session_value(session_id, "last_media_kind", media_kind)
    if subject:
        set_session_value(session_id, "last_media_subject", subject)
    if style_profile.get("style_tokens") or style_profile.get("aspect_ratio"):
        set_session_value(session_id, "last_media_style_profile", style_profile)
    if platform:
        set_session_value(session_id, "last_media_platform", platform)

    tags = _build_media_tags(media_kind, subject, style_profile, platform)

    return {
        "type": "analysis",
        "tool": "general",
        "content": {
            "summary": summary,
            "insight": insight,
            "actions": actions,
            "executions": executions,
            "tags": tags,
            "confidence": "high",
            "sections": sections,
        },
    }


def _build_media_creation_executions(media_kind: str, subject: str):
    executions = []
    search_subject = subject or "creative workflow"

    if media_kind in {"image", "both"}:
        executions.append(
            {
                "type": "web_search",
                "query": f"ai image generator for {search_subject}",
                "label": "Open image tools",
                "success_summary": "Showing image creation tools for you.",
                "blocked_summary": "Image creation tools are available inside OmniCore.",
                "success_insight": "Web search results now stay inside OmniCore for current AI image creation tools.",
                "blocked_insight": "Image tool results remain available in the OmniCore chat workspace.",
                "tool": "search",
            }
        )
        executions.append(
            {
                "type": "youtube_search",
                "query": f"ai image prompt tutorial {search_subject}",
                "label": "Open image tutorial",
                "success_summary": "Showing an image creation tutorial for you.",
                "blocked_summary": "Image tutorials are available inside OmniCore.",
                "success_insight": "YouTube tutorial search results now stay inside OmniCore for image prompting and refinement.",
                "blocked_insight": "Image tutorial results remain available in the OmniCore chat workspace.",
                "tool": "search",
            }
        )

    if media_kind in {"video", "both"}:
        executions.append(
            {
                "type": "web_search",
                "query": f"ai video generator for {search_subject}",
                "label": "Open video tools",
                "success_summary": "Showing video creation tools for you.",
                "blocked_summary": "Video creation tools are available inside OmniCore.",
                "success_insight": "Web search results now stay inside OmniCore for current AI video creation tools.",
                "blocked_insight": "Video tool results remain available in the OmniCore chat workspace.",
                "tool": "search",
            }
        )
        executions.append(
            {
                "type": "youtube_search",
                "query": f"ai video prompt tutorial {search_subject}",
                "label": "Open video tutorial",
                "success_summary": "Showing a video creation tutorial for you.",
                "blocked_summary": "Video tutorials are available inside OmniCore.",
                "success_insight": "YouTube tutorial search results now stay inside OmniCore for video prompting and shot planning.",
                "blocked_insight": "Video tutorial results remain available in the OmniCore chat workspace.",
                "tool": "search",
            }
        )

    return executions


def _get_media_creation_reply(query: str, session_id: str):
    media_kind = _detect_media_kind(query)
    if not media_kind or not _is_media_creation_query(query):
        return None

    subject = _extract_media_subject(query)
    executions = _build_media_creation_executions(media_kind, subject)
    style_profile = _extract_media_style_profile(query)
    explicit_platform = _extract_media_platform(query)
    remembered_platform = _normalize_media_platform(get_session_value(session_id, "last_media_platform", ""))
    platform = explicit_platform or remembered_platform
    tags = _build_media_tags(media_kind, subject, style_profile, platform)

    if media_kind == "image":
        summary = (
            f"To create an image, start with a generator and a precise prompt{f' for {subject}' if subject else ''}. "
            "Describe the subject, style, lighting, camera angle, and aspect ratio in one clean line."
        )
        insight = (
            "A strong image prompt usually follows: subject + scene + style + lighting + composition + quality modifiers. "
            f"Example: {('"' + subject + '" as a cinematic portrait, golden-hour lighting, shallow depth of field, ultra-detailed, 16:9') if subject else '"futuristic city skyline at dawn, cinematic lighting, volumetric fog, ultra-detailed, 16:9"'}."
        )
        actions = [
            "Turn my idea into an image prompt",
            "Generate image prompt",
            "Open image tools",
            "Open image tutorial",
        ]
        actions = _append_provider_reset_action(actions, platform)
    elif media_kind == "video":
        summary = (
            f"To create a video, break the idea into scenes{f' for {subject}' if subject else ''}, then define motion, camera moves, duration, and style. "
            "Good video prompts specify what happens second by second."
        )
        insight = (
            "A strong video prompt includes subject, action, camera movement, environment, mood, duration, and aspect ratio. "
            f"Example: {('"' + subject + '" walking through a neon alley, slow dolly-in, rain reflections, cinematic lighting, 8 seconds, 16:9') if subject else '"astronaut walking through a neon alley, slow dolly-in, rain reflections, cinematic lighting, 8 seconds, 16:9"'}."
        )
        actions = [
            "Turn my idea into a video prompt",
            "Generate video prompt",
            "Open video tools",
            "Open video tutorial",
        ]
        actions = _append_provider_reset_action(actions, platform)
    else:
        summary = (
            "To create images and videos well, start with a precise concept, then write separate prompts for still visuals and motion. "
            "Images need composition and style; videos need scenes, timing, and camera movement."
        )
        insight = (
            "Use one image prompt to lock the visual style, then convert that into a video prompt by adding action, transitions, shot timing, and movement. "
            f"Use the same subject and style words throughout{f' for {subject}' if subject else ''} so the outputs stay consistent."
        )
        actions = [
            "Turn my idea into an image prompt",
            "Turn my idea into a video prompt",
            "Generate image prompt",
            "Generate video prompt",
            "Open image tools",
            "Open video tools",
        ]
        actions = _append_provider_reset_action(actions, platform)

    return {
        "type": "analysis",
        "tool": "general",
        "content": {
            "summary": summary,
            "insight": insight,
            "actions": actions,
            "executions": executions,
            "tags": tags,
            "confidence": "high",
        },
    }


def _build_query_executions(query: str):
    cleaned = (query or "").strip()
    lowered = cleaned.lower()
    if not cleaned:
        return []

    executions = []

    copy_text = _extract_copy_text(cleaned)
    if copy_text:
        return [
            {
                "type": "copy_text",
                "text": copy_text,
                "label": "Copy requested text",
                "success_summary": "Copying the requested text to your clipboard.",
                "success_insight": f'The clipboard will contain: "{copy_text}".',
                "failure_summary": "Clipboard access failed.",
                "failure_insight": "Allow clipboard permissions in your browser and try again.",
                "tool": "general",
            }
        ]

    weather_city = _extract_weather_city(cleaned)
    if weather_city:
        return [
            {
                "type": "open_weather",
                "city": weather_city,
                "label": "Fetch live weather",
                "success_summary": f"Fetching live weather for {weather_city}.",
                "success_insight": f"The assistant is retrieving live weather data for {weather_city} from the backend weather route.",
                "failure_summary": "Weather fetch failed.",
                "failure_insight": "The backend weather route did not return a valid live response.",
                "tool": "weather",
            }
        ]

    if "food near me" in lowered:
        executions.append(
            {
                "type": "web_search",
                "query": "food near me",
                "label": "Show nearby food options",
                "success_summary": "Showing nearby food options inside OmniCore.",
                "blocked_summary": "Nearby food options are available inside OmniCore.",
                "success_insight": "A local food search is being shown inside the workspace.",
                "blocked_insight": "Nearby food options stay available in the chat workspace.",
                "tool": "search",
            }
        )

    youtube_execution = _build_youtube_search_execution(cleaned)
    if youtube_execution:
        executions.append(youtube_execution)

    web_execution = _build_web_search_execution(cleaned)
    if web_execution:
        executions.append(
            web_execution
        )

    map_query = _extract_map_query(cleaned)
    if map_query:
        executions.append(
            {
                "type": "web_search",
                "query": map_query,
                "label": "Show map-related results",
                "success_summary": f'Showing location results for "{map_query}" inside OmniCore.',
                "blocked_summary": "Location results are available inside OmniCore.",
                "success_insight": f'Location-related search results for "{map_query}" are being shown in the workspace.',
                "blocked_insight": "Location results stay available in the chat workspace.",
                "tool": "search",
            }
        )

    return executions


def format_news_response(news_data):
    if news_data["status"] != "success":
        return news_data.get("message", "Error fetching news.")

    response = "Latest Headlines:\n\n"

    for article in news_data["articles"]:
        response += f"- {article['title']}\n"
        response += f"  Source: {article['source']}\n"
        response += f"  Link: {article['url']}\n\n"

    return response.strip()


def get_news(query: str = "technology"):
    settings = get_settings()

    try:
        attempts = [
            (
                "everything",
                {
                    "q": query,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": 5,
                },
                query,
            ),
            (
                "everything",
                {
                    "q": "latest news",
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": 5,
                },
                "latest news",
            ),
            (
                "top-headlines",
                {
                    "country": "us",
                    "pageSize": 5,
                },
                "top headlines",
            ),
        ]

        for endpoint, params, topic_used in attempts:
            response = requests.get(
                f"{settings.news_api_base_url}/{endpoint}",
                params={**params, "apiKey": settings.news_api_key},
                timeout=8,
            )
            data = response.json()
            logger.info("News API raw response [simple:%s]: %s", topic_used, response.text)

            if response.status_code != 200:
                return {
                    "status": "error",
                    "message": data.get("message", "Unable to fetch news."),
                }

            articles = data.get("articles", [])
            logger.info("News topic used [simple]: %s", topic_used)
            logger.info("News articles returned [simple]: %d", len(articles))

            if not articles:
                continue

            formatted_articles = []
            for article in articles[:5]:
                published_at = article.get("publishedAt")
                if published_at:
                    try:
                        published_at = datetime.fromisoformat(
                            published_at.replace("Z", "+00:00")
                        ).isoformat()
                    except ValueError:
                        pass

                formatted_articles.append(
                    {
                        "title": article.get("title", "Untitled article"),
                        "description": article.get("description") or article.get("content") or "",
                        "source": (article.get("source") or {}).get("name", "Unknown source"),
                        "url": article.get("url", ""),
                        "publishedAt": published_at,
                    }
                )

            return {
                "status": "success",
                "articles": formatted_articles,
            }

        return {
            "status": "no_results",
            "message": f"No real headlines found for '{query}'.",
        }

    except Exception as error:
        return {
            "status": "error",
            "message": str(error),
        }


def _extract_news_topic(query: str) -> str:
    cleaned_query = (query or "").strip()
    if not cleaned_query:
        return "technology"

    match = re.search(r"(.+?)\s+news$", cleaned_query, re.IGNORECASE)
    if match and match.group(1).strip():
        candidate = re.sub(r"^(?:show|give|tell)\s+me\s+", "", match.group(1).strip(), flags=re.IGNORECASE)
        candidate = re.sub(r"^(?:latest|top|more)\s+", "", candidate, flags=re.IGNORECASE)
        if candidate and candidate.lower() not in {"the", "some", "any"}:
            return candidate.strip(" ?!.,")

    match = re.search(r"news\s+(?:about|on|for)?\s*(.+)$", cleaned_query, re.IGNORECASE)
    if match and match.group(1).strip():
        return match.group(1).strip(" ?!.,")

    match = re.search(r"(?:happening with|about|on|for)\s+(.+)$", cleaned_query, re.IGNORECASE)
    if match and match.group(1).strip():
        return match.group(1).strip(" ?!.,")

    match = re.search(r"headline(?:s)?\s+(?:from|for|about|on)?\s*(.+)$", cleaned_query, re.IGNORECASE)
    if match and match.group(1).strip():
        return match.group(1).strip(" ?!.,")

    words = cleaned_query.strip(" ?!.,").split()
    if words:
        candidate = words[-1]
        if candidate.lower() not in {"today", "now", "latest", "headline", "headlines", "news"}:
            return candidate

    return "technology"


def _is_follow_up_query(query: str) -> bool:
    normalized = (query or "").strip().lower()
    if not normalized:
        return False
    return normalized.startswith(FOLLOW_UP_PREFIXES) or normalized in WEATHER_FOLLOW_UP_TERMS


def _looks_like_weather_query(query: str, session_id: str) -> bool:
    normalized = (query or "").strip().lower()
    if any(term in normalized for term in WEATHER_TERMS):
        return True
    if normalized in WEATHER_FOLLOW_UP_TERMS and get_last_tool(session_id) == "weather":
        return True
    return False


def _looks_like_news_query(query: str, session_id: str) -> bool:
    normalized = (query or "").strip().lower()
    if any(term in normalized for term in NEWS_TERMS):
        return True
    if _is_follow_up_query(query) and get_last_tool(session_id) == "news":
        return True
    return False


def classify_intent(query: str, session_id: str) -> str:
    if _is_youtube_search_request(query):
        return "youtube_search"
    if _is_explicit_web_search_request(query):
        return "web_search"
    if _looks_like_weather_query(query, session_id):
        return "weather"
    if _looks_like_news_query(query, session_id):
        return "news"
    return "general"


def _normalize_analysis_response(response: dict, default_intent: str = "general"):
    content = response.get("content", {}) if isinstance(response.get("content"), dict) else {}
    summary = content.get("summary") or content.get("insight") or ""
    tool = response.get("tool", "general")

    return {
        "type": "error" if response.get("type") == "error" else "analysis",
        "summary": summary,
        "data": {
            "intent": default_intent,
            "tool": tool,
            "insight": content.get("insight", ""),
            "actions": content.get("actions", []),
            "tags": content.get("tags", []),
            "executions": content.get("executions", []),
            "confidence": content.get("confidence", "medium"),
            "sections": content.get("sections", []),
        },
    }


def _build_web_search_response(query: str):
    web_query = _extract_web_query(query)
    if not web_query and not _is_explicit_web_search_request(query):
        web_query = (query or "").strip().rstrip("?!.,")
    if not web_query:
        return {
            "type": "analysis",
            "summary": "What do you want to search for?",
            "data": {
                "intent": "web_search",
                "tool": "search",
                "insight": "Try a request like \"search the internet for AI agents\" or \"look up best laptops 2026\".",
                "actions": [
                    "Search the internet for AI agents",
                    "Look up best laptops 2026",
                ],
                "results": [],
                "query": "",
                "confidence": "high",
            },
            "results": [],
        }

    results = search_web_results(web_query)
    summary = summarize_search_results(web_query, results)
    return {
        "type": "search_results",
        "summary": summary,
        "response": summary,
        "data": {
            "intent": "web_search",
            "tool": "search",
            "query": web_query,
            "results": results,
        },
        "results": results,
    }


def _build_youtube_search_response(query: str):
    youtube_query = _extract_youtube_query(query)
    if not youtube_query and not _is_youtube_search_request(query):
        youtube_query = (query or "").strip().rstrip("?!.,")
    if not youtube_query:
        return {
            "type": "analysis",
            "summary": "Tell me what you want to search for on YouTube.",
            "data": {
                "intent": "youtube_search",
                "tool": "search",
                "insight": "Try a request like \"search YouTube for AI agents\" or \"look up cooking shorts on YouTube\".",
                "actions": [
                    "Search YouTube for AI agents",
                    "Look up cooking shorts on YouTube",
                ],
                "results": [],
                "query": "",
                "confidence": "high",
            },
            "results": [],
        }

    results = search_youtube_videos(youtube_query)
    summary = summarize_youtube_results(youtube_query, results)
    return {
        "type": "video_results",
        "summary": summary,
        "data": {
            "intent": "youtube_search",
            "tool": "search",
            "query": youtube_query,
            "results": results,
        },
        "results": results,
    }


def _build_weather_response(query: str, session_id: str):
    weather = get_weather_reply(query, fallback_city=get_last_weather_city(session_id))
    if isinstance(weather, str):
        return {
            "type": "error",
            "summary": weather,
            "data": {
                "intent": "weather",
                "tool": "weather",
                "insight": "The weather request could not be completed.",
                "actions": ["Try rephrasing the city name", "Retry the request"],
                "confidence": "low",
            },
        }

    set_last_weather_city(session_id, str(weather.get("city") or ""))
    return {
        "type": "analysis",
        "summary": format_weather_reply(weather),
        "data": {
            "intent": "weather",
            "tool": "weather",
            "weather": weather,
            "insight": format_weather_insight(weather),
            "actions": build_weather_actions(weather),
            "confidence": "high",
        },
    }


def _build_news_response(query: str):
    topic = _extract_news_topic(query)
    simple_result = get_news(topic)
    status = simple_result.get("status")
    articles = simple_result.get("articles", []) if isinstance(simple_result.get("articles"), list) else []
    analysis = _analysis_from_simple_articles(topic, articles)
    content = analysis.get("content", {}) if isinstance(analysis.get("content"), dict) else {}
    normalized_articles = [
        {
            "title": article.get("title", "Untitled article"),
            "link": article.get("url", ""),
            "snippet": article.get("description") or article.get("publishedAt") or "Latest coverage is available for this story.",
            "source": article.get("source", "Unknown source"),
            "publishedAt": article.get("publishedAt", ""),
        }
        for article in articles
    ]
    results = normalize_and_rank_results(topic, normalized_articles, "news")

    if status == "error":
        return {
            "type": "error",
            "summary": simple_result.get("message", "Unable to fetch news."),
            "data": {
                "intent": "news",
                "tool": "news",
                "topic": topic,
                "results": [],
                "insight": "The news request could not be completed.",
                "actions": ["Try a broader topic", "Retry the request"],
                "confidence": "low",
            },
            "results": [],
        }

    summary = summarize_search_results(topic, results) if results else build_answer_first_summary("news", topic, results)
    return {
        "type": "search_results",
        "summary": summary,
        "response": summary,
        "data": {
            "intent": "news",
            "tool": "news",
            "query": topic,
            "topic": topic,
            "results": results,
            "insight": content.get("insight", ""),
            "actions": content.get("actions", []),
            "confidence": content.get("confidence", "medium"),
        },
        "results": results,
    }


def _error_response(message: str, tool: str = "general"):
    return {
        "type": "error",
        "tool": tool,
        "content": {
            "summary": message,
            "insight": "The request could not be completed.",
            "actions": ["Try rephrasing the query", "Retry the request"],
            "confidence": "low",
        },
    }


def _get_confidence(articles: list[dict]) -> str:
    strong_sources = {
        "reuters",
        "associated press",
        "ap news",
        "bbc news",
        "the verge",
        "financial times",
        "the wall street journal",
        "new york times",
        "bloomberg",
    }
    source_names = {
        (article.get("source") or {}).get("name", "").strip().lower()
        for article in articles
    }
    has_strong_source = any(source in strong_sources for source in source_names)

    if len(articles) >= 3 and has_strong_source:
        return "high"
    if len(articles) >= 2 or has_strong_source:
        return "medium"
    return "low"


def _analysis_response(topic: str, articles: list[dict]):
    if not articles:
        return {
            "type": "analysis",
            "tool": "news",
            "content": {
                "summary": f"No recent headlines found for {topic}.",
                "insight": f"Coverage for {topic} is thin right now, so there is not enough signal to summarize further.",
                "actions": [
                    f"Show broader news on {topic}",
                    f"Try a different angle on {topic}",
                ],
                "confidence": "medium",
            },
        }

    top_articles = articles[:3]
    top_titles = [article.get("title", "Untitled article") for article in top_articles]
    source_names = [
        (article.get("source") or {}).get("name", "a major outlet")
        for article in top_articles
    ]
    actions = [
        f"Show me more {topic} headlines",
        f"Summarize the biggest {topic} development",
        f"What should I watch next in {topic}?",
    ]

    summary = f"{topic.title()} headlines are active today. Coverage is led by {source_names[0]}"
    if len(source_names) > 1:
        summary += f" and {source_names[1]}"
    summary += "."

    insight = f"The strongest {topic} signal in this batch is around {top_titles[0]}"
    if len(top_titles) > 1:
        insight += f", with follow-up attention on {top_titles[1]}"
    insight += "."

    return {
        "type": "analysis",
        "tool": "news",
        "content": {
            "summary": summary,
            "insight": insight,
            "actions": actions[: max(2, min(3, len(actions)))],
            "confidence": _get_confidence(top_articles),
        },
    }


def _analysis_from_simple_articles(topic: str, formatted_articles: list[dict]):
    if not formatted_articles:
        return _analysis_response(topic, [])

    normalized_articles = []
    for article in formatted_articles:
        normalized_articles.append(
            {
                "title": article.get("title", "Untitled article"),
                "url": article.get("url", ""),
                "publishedAt": article.get("publishedAt"),
                "source": {
                    "name": article.get("source", "Unknown source"),
                },
            }
        )

    return _analysis_response(topic, normalized_articles)


def _fetch_news(settings, endpoint: str, params: dict, log_label: str):
    response = requests.get(
        f"{settings.news_api_base_url}/{endpoint}",
        params={**params, "apiKey": settings.news_api_key},
        timeout=8,
    )
    raw_body = response.text
    logger.info("News API raw response [%s]: %s", log_label, raw_body)

    data = response.json()
    if response.status_code != 200:
        return None, data.get("message", "Unable to fetch news.")

    articles = data.get("articles", [])
    logger.info("News API topic used [%s]: %s", log_label, params.get("q", "general-headlines"))
    logger.info("News API articles returned [%s]: %d", log_label, len(articles))
    return articles, None


def get_news_reply(query: str):
    settings = get_settings()
    if not settings.news_api_key:
        return _error_response("News API key not configured.", "news")

    topic = _extract_news_topic(query)
    logger.info("News topic used: %s", topic)

    simple_result = get_news(topic)
    status = simple_result.get("status")

    if status == "success":
        articles = simple_result.get("articles", [])
        logger.info("News topic used (final): %s", topic)
        logger.info("News articles returned (final): %d", len(articles))
        return {
            "type": "analysis",
            "tool": "news",
            "content": {
                "summary": format_news_response(simple_result),
                "insight": "",
                "actions": [],
                "confidence": "high" if articles else "medium",
            },
        }

    if status == "error":
        return _error_response(simple_result.get("message", "Unable to fetch news."), "news")

    return {
        "type": "analysis",
        "tool": "news",
        "content": {
            "summary": format_news_response(simple_result),
            "insight": "",
            "actions": [],
            "confidence": "medium",
        },
    }


def get_general_reply(query: str, session_id: str, user_id: str | None = None):
    cleaned_query = (query or "").strip() or "your request"
    executions = _build_query_executions(query)
    conversation = get_conversation(session_id)[-5:]

    media_prompt_reply = _get_media_prompt_generation_reply(query, session_id)
    if media_prompt_reply:
        return media_prompt_reply

    media_reply = _get_media_creation_reply(query, session_id)
    if media_reply:
        media_kind = _detect_media_kind(query)
        media_subject = _extract_media_subject(query)
        media_style_profile = _extract_media_style_profile(query)
        media_platform = _extract_media_platform(query)
        if media_kind:
            set_session_value(session_id, "last_media_kind", media_kind)
        if media_subject:
            set_session_value(session_id, "last_media_subject", media_subject)
        if media_style_profile.get("style_tokens") or media_style_profile.get("aspect_ratio"):
            set_session_value(session_id, "last_media_style_profile", media_style_profile)
        if media_platform:
            set_session_value(session_id, "last_media_platform", media_platform)
        return media_reply

    if executions:
        primary_execution = executions[0]
        return {
            "type": "analysis",
            "tool": primary_execution.get("tool", "general"),
            "content": {
                "summary": primary_execution.get("success_summary", "Executing the requested action."),
                "insight": primary_execution.get("success_insight", "The assistant is carrying out the requested browser action."),
                "actions": ["Ask for another action", "Request a follow-up after the tab opens"],
                "executions": executions,
                "confidence": "high",
            },
        }

    ai_reply = get_ai_reply(
        cleaned_query,
        conversation_history=conversation,
        user_memory=build_relevant_user_memory_context(session_id, cleaned_query, user_id),
    )
    raw_summary = str(ai_reply.get("reply") or ai_reply.get("error") or "")
    allow_follow_up = not contains_meta_artifacts(raw_summary)
    summary = run_enforced_pipeline(
        raw_summary,
        route_name="query",
        intent="general",
        query=cleaned_query,
        user_name=str(get_user_memory(session_id, user_id).get("name") or "").strip() or None,
        allow_personalization=False,
        allow_follow_up=allow_follow_up,
    )

    return {
        "type": "analysis",
        "tool": "general",
        "content": {
            "summary": summary,
            "insight": "",
            "actions": [],
            "executions": executions,
            "confidence": "medium",
        },
    }


def get_weather_analysis(query: str, session_id: str):
    weather = get_weather_reply(query, fallback_city=get_last_weather_city(session_id))
    if isinstance(weather, str):
        return _error_response(weather, "weather")

    set_last_weather_city(session_id, str(weather.get("city") or ""))

    city_line = weather["city"]
    if weather.get("country"):
        city_line = f"{city_line}, {weather['country']}"

    return {
        "type": "analysis",
        "tool": "weather",
        "content": {
            "summary": format_weather_reply(weather),
            "insight": format_weather_insight(weather),
            "actions": build_weather_actions(weather),
            "confidence": "high",
        },
    }


def get_search_analysis(query: str):
    if _is_youtube_search_request(query):
        youtube_execution = _build_youtube_search_execution(query)
        if not youtube_execution:
            logger.info("YouTube intent detected without topic: %s", query)
            return {
                "type": "analysis",
                "tool": "search",
                "content": {
                    "summary": "Tell me what you want to search for on YouTube.",
                    "insight": "Try a request like \"search YouTube for AI agents\" or \"look up cooking shorts on YouTube\".",
                    "actions": [
                        "Search YouTube for AI agents",
                        "Look up cooking shorts on YouTube",
                    ],
                    "confidence": "high",
                },
            }

        youtube_query = _extract_youtube_query(query)
        logger.info("Returning YouTube action payload for query: %s", youtube_query)
        return {
            "type": "analysis",
            "tool": "search",
            "content": {
                "summary": f'Showing YouTube results for "{youtube_query}" inside OmniCore.',
                "insight": f'OmniCore is loading YouTube results for "{youtube_query}" inside the workspace.',
                "actions": [
                    "Search another topic on YouTube",
                    "Search the web for the same topic",
                ],
                "executions": [youtube_execution],
                "confidence": "high",
            },
        }

    if _is_explicit_web_search_request(query):
        web_query = _extract_web_query(query)
        if not web_query:
            logger.info("Web search intent detected without topic: %s", query)
            return {
                "type": "analysis",
                "tool": "search",
                "content": {
                    "summary": "What do you want to search for?",
                    "insight": "Try a request like \"search the internet for AI agents\" or \"look up best laptops 2026\".",
                    "actions": [
                        "Search the internet for AI agents",
                        "Look up best laptops 2026",
                    ],
                    "confidence": "high",
                },
            }

        logger.info("Returning internal web search results for query: %s", web_query)
        web_execution = _build_web_search_execution(query)
        search_result = search_web(web_query)
        search_summary = _get_search_summary(search_result)

        return {
            "type": "analysis",
            "tool": "search",
            "content": {
                "summary": search_summary,
                "insight": f'OmniCore searched the web for "{web_query}" and kept the results inside the workspace.',
                "actions": [
                    "Search another topic",
                    "Search the same topic on YouTube",
                ],
                "executions": [web_execution] if web_execution else [],
                "confidence": "medium",
            },
        }

    search_result = search_web(query)
    search_summary = _get_search_summary(search_result)

    return {
        "type": "analysis",
        "tool": "search",
        "content": {
            "summary": search_summary,
            "insight": "Live web results were fetched from the web search tool and condensed into a short answer with sources.",
            "actions": [
                "Open web search results",
                "Search the same topic on YouTube",
            ],
            "confidence": "medium",
        },
    }


def handle_intent(query: str, session_id: str, user_id: str | None = None):
    intent = classify_intent(query, session_id)
    logger.info("Unified intent router selected intent=%s", intent)

    if intent == "web_search":
        return _build_web_search_response(query)
    if intent == "youtube_search":
        return _build_youtube_search_response(query)
    if intent == "weather":
        return _build_weather_response(query, session_id)
    if intent == "news":
        return _build_news_response(query)

    return _normalize_analysis_response(get_general_reply(query, session_id, user_id), "general")


