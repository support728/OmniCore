import logging

from .intent_router import classify_intent
from .memory_store import create_session_id
from .news_service import _extract_news_topic, _extract_web_query, _extract_youtube_query, get_news, handle_intent
from .weather_service import format_weather_reply, get_weather_reply
from .web_search_service import search_web_results, summarize_search_results
from .youtube_service import search_youtube_videos, summarize_youtube_results


logger = logging.getLogger(__name__)


def route_query(query: str):
    logger.warning("Legacy tool_router.route_query called; delegating to news_service.handle_intent")

    intent = classify_intent(query)

    if intent == "youtube_search":
        youtube_query = _extract_youtube_query(query) or query
        results = search_youtube_videos(youtube_query)
        return {
            "type": intent,
            "summary": summarize_youtube_results(youtube_query, results),
            "data": results,
        }

    if intent == "web_search":
        web_query = _extract_web_query(query) or query
        results = search_web_results(web_query)
        return {
            "type": intent,
            "summary": summarize_search_results(web_query, results),
            "data": results,
        }

    if intent == "weather":
        results = get_weather_reply(query)
        if isinstance(results, str):
            return {
                "type": intent,
                "summary": results,
                "data": [],
            }

        return {
            "type": intent,
            "summary": format_weather_reply(results),
            "data": results,
        }

    if intent == "news":
        topic = _extract_news_topic(query)
        response = get_news(topic)
        if isinstance(response.get("articles"), list):
            return {
                "type": intent,
                "summary": response.get("message", "") if response.get("status") == "error" else "",
                "data": [
                    {
                        "title": str(article.get("title") or "Untitled article"),
                        "link": str(article.get("url") or ""),
                        "snippet": str(
                            article.get("description")
                            or article.get("publishedAt")
                            or "Latest coverage is available for this story."
                        ),
                        "source": str(article.get("source") or "Unknown source"),
                    }
                    for article in response.get("articles", [])
                ],
            }

    if intent == "general":
        return {
            "type": "general",
            "summary": "I can help with that. What would you like to know?",
            "data": [],
        }

    response = handle_intent(query, create_session_id())
    summary = str(response.get("summary") or "")
    data = response.get("data") if isinstance(response.get("data"), dict) else {}
    response_type = str(response.get("type") or "general")
    intent = str(data.get("intent") or response_type)

    if response_type == "video_results":
        return {
            "type": "youtube_search",
            "summary": summary,
            "data": data.get("results", []),
        }

    if response_type == "search_results" and intent == "web_search":
        return {
            "type": "web_search",
            "summary": summary,
            "data": data.get("results", []),
        }

    if response_type == "search_results" and intent == "news":
        return {
            "type": "news",
            "summary": summary,
            "data": data.get("results", []),
        }

    if intent == "weather":
        weather = data.get("weather") if isinstance(data.get("weather"), dict) else data
        return {
            "type": "weather",
            "summary": summary,
            "data": weather,
        }

    return {
        "type": "general",
        "summary": summary or "I can help with that. What would you like to know?",
        "data": [],
    }