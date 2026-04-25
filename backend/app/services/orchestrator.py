import logging

from .ai_router import ai_route_query


logger = logging.getLogger(__name__)

FOLLOW_UP_PREFIXES = (
    "what about",
    "how about",
    "and ",
    "also ",
)

EXPLICIT_YOUTUBE_TERMS = (
    "youtube",
    "find videos",
    "find video",
    "videos about",
    "video about",
    "youtube shorts",
    "shorts about",
)

EXPLICIT_WEB_TERMS = (
    "search the internet",
    "search internet",
    "search google",
    "search the web",
    "search for",
    "look up",
    "find information on",
    "find online",
)

EXPLICIT_WEATHER_TERMS = ("weather", "temperature", "forecast", "rain", "snow")

EXPLICIT_NEWS_TERMS = ("news", "headline", "headlines", "happening", "latest", "current events")


def _is_ambiguous_follow_up(query: str) -> bool:
    normalized = (query or "").strip().lower()
    if not normalized:
        return False

    return normalized.startswith(FOLLOW_UP_PREFIXES) or len(normalized.split()) <= 3


def detect_direct_tool(query: str):
    query_lower = (query or "").strip().lower()
    if not query_lower:
        return None

    if any(term in query_lower for term in EXPLICIT_YOUTUBE_TERMS):
        return "search"

    if any(term in query_lower for term in EXPLICIT_WEB_TERMS):
        return "search"

    if any(term in query_lower for term in EXPLICIT_WEATHER_TERMS):
        return "weather"

    if any(term in query_lower for term in EXPLICIT_NEWS_TERMS):
        return "news"

    return None


def run_tools(query: str, session_id: str):
    logger.warning(
        "Legacy orchestrator.run_tools called for session_id=%s; returning compatibility tool selection",
        session_id,
    )
    direct_tool = detect_direct_tool(query)
    if direct_tool:
        return [direct_tool]
    ai_tool = ai_route_query(query, session_id)
    return [ai_tool if ai_tool in {"news", "finance", "weather", "search", "general"} else "general"]


def _mechanical_combine(results: list):
    summaries = []
    insights = []
    actions = []
    sections = []
    executions = []

    for response in results:
        content = response.get("content", {})
        tool = response.get("tool", "general")
        summary = content.get("summary", "")
        insight = content.get("insight", "")
        tool_label = tool.capitalize()

        summaries.append(summary)
        insights.append(insight)
        actions.extend(content.get("actions", []))
        executions.extend(content.get("executions", []))

        if insight:
            sections.append({
                "title": f"{tool_label} Insight",
                "body": insight,
            })

    return {
        "type": "analysis",
        "tool": "multi",
        "content": {
            "summary": " | ".join(filter(None, summaries)),
            "insight": " ".join(filter(None, insights)),
            "actions": list(dict.fromkeys(actions)),
            "executions": executions,
            "confidence": "medium",
            "sections": sections,
        }
    }


def combine_responses(results: list):
    logger.warning("Legacy orchestrator.combine_responses called; using mechanical combine only")
    return _mechanical_combine(results)