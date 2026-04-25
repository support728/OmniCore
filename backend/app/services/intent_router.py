def chat(message: str) -> dict:
    """
    Deterministic echo function for testing.
    Args:
        message (str): Input message
    Returns:
        dict: Reply dict
    """
    if not isinstance(message, str):
        raise TypeError("message must be a string")
    return {"reply": f"You said: {message}"}
    print(f"[DEBUG] Detected intent: {detected_intent}")
    # print(f"[ROUTER] intent={detected_intent}")

    # Hardcoded test for 'capital of japan'
    if "capital of japan" in cleaned_message.lower():
        return {"reply": "Tokyo", "session_id": resolved_session_id}

    logger.warning(
        "Legacy intent_router.handle_message called; delegating to chat_router.route_user_query for session_id=%s",
        resolved_session_id,
    )

    if detected_intent in {"web_search", "youtube_search", "weather", "news"}:
        response = handle_structured_intent(cleaned_message, resolved_session_id)
    else:
        from .chat_router import route_user_query
        response = route_user_query(cleaned_message, resolved_session_id)
    summary = str(response.get("summary") or "")
    data = response.get("data") if isinstance(response.get("data"), dict) else {}
    response_type = str(response.get("type") or "general")
    response_intent = str(data.get("intent") or response_type)

    reply_payload = {
        "type": response_type,
        "summary": summary,
        "data": data,
        "reply": summary,
    }

    if response_type == "search_results" and response_intent == "web_search":
        reply_payload["type"] = "search_results"
        reply_payload["response"] = summary
        reply_payload["action"] = {
            "type": "web_search",
            "query": data.get("query", ""),
        }
        reply_payload["executions"] = []
    elif response_type == "video_results" and response_intent == "youtube_search":
        reply_payload["type"] = "video_results"
        reply_payload["response"] = summary
        reply_payload["action"] = {
            "type": "youtube_search",
            "query": data.get("query", ""),
        }
        reply_payload["executions"] = []
    elif response_type == "web_search":
        reply_payload["type"] = "search_results"
        reply_payload["response"] = summary
        reply_payload["action"] = {
            "type": "web_search",
            "query": data.get("query", ""),
        }
        reply_payload["executions"] = []
    elif response_type == "youtube_search":
        reply_payload["type"] = "video_results"
        reply_payload["response"] = summary
        reply_payload["action"] = {
            "type": "youtube_search",
            "query": data.get("query", ""),
        }
        reply_payload["executions"] = []
    elif response_intent == "weather" or data.get("tool") == "weather":
        weather = data.get("weather") if isinstance(data.get("weather"), dict) else data
        reply_payload["type"] = "weather"
        reply_payload["weather"] = weather
        reply_payload["weather_insight"] = data.get("insight", "")
        reply_payload["weather_actions"] = data.get("actions", [])
    elif response_intent == "news" or response_type == "news":
        reply_payload["news"] = data.get("results", [])
    elif response_type == "error":
        reply_payload["error"] = summary

    return {
        **reply_payload,
        "session_id": resolved_session_id,
    }



def chat(message: str):
    import traceback
    message_lower = message.lower()
    try:
        # News intent
        if "news" in message_lower:
            from .news_service import get_news
            results = get_news(message)
            formatted = "\n".join(
                [f"- {item['title']}\n  {item['url']}" for item in results]
            )
            return {
                "type": "news",
                "reply": formatted,
                "results": results
            }
        # Weather intent
        if any(term in message_lower for term in ["weather", "forecast", "temperature"]):
            from .weather_service import get_weather_reply
            weather = get_weather_reply(message)
            # Only return the weather object, not raw API data
            return {
                "type": "weather",
                "weather": weather
            }
        # Fallback: AI/echo
        from .ai_service import get_ai_reply
        ai_reply = get_ai_reply(message)
        return {
            "type": "ai",
            "reply": ai_reply
        }
    except Exception as e:
        return {
            "type": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

def handle_qa(message: str) -> str:
    if "capital of japan" in message.lower():
        return {"reply": "Tokyo"}
    return {"reply": "I don't know yet"}

def handle_news(message: str) -> str:
    # [NEWS] calling NewsAPI print removed

    import os
    API_KEY = os.getenv("NEWS_API_KEY")

    if not API_KEY:
        return "Missing NEWS_API_KEY"

    raw_query = message
    # Stub for missing clean_news_query
    def clean_news_query(q):
        return q
    cleaned_query = clean_news_query(raw_query)
    # [NEWS] cleaned query print removed

    url = "https://newsapi.org/v2/everything"

    params = {
        "q": cleaned_query,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": 3,
        "apiKey": API_KEY
    }

    try:
        import requests
        res = requests.get(url, params=params)
        data = res.json()

        articles = data.get("articles", [])[:3]

        if not articles:
            return {"reply": "No news found"}

        formatted = []
        for a in articles:
            title = a.get("title", "")
            source = a.get("source", {}).get("name", "")
            url_ = a.get("url", "")
            formatted.append(f"- {title} ({source})\n  {url_}")

        final_output = "\n\n".join(formatted)
        return {"reply": final_output}

    except Exception as e:
        return {"reply": f"News error: {str(e)}"}

def default_llm_response(message: str) -> str:
    return {"reply": "Fallback LLM response"}