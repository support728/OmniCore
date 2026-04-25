import logging
from .intent_router import classify_intent


logger = logging.getLogger(__name__)

ALLOWED_TOOLS = {"news", "finance", "weather", "search", "general"}

def ai_route_query(query: str, session_id: str):
    logger.warning(
        "Legacy ai_router.ai_route_query called for session_id=%s; delegating to intent_router.classify_intent",
        session_id,
    )
    result = classify_intent(query)
    if result in {"youtube_search", "web_search"}:
        return "search"
    if result in ALLOWED_TOOLS:
        return result
    return "general"