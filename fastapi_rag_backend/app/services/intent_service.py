def detect_intent(query: str) -> str:
    q = query.lower().strip()

    if any(w in q for w in ["weather", "temperature", "forecast"]):
        return "weather"

    if any(w in q for w in ["news", "headline", "breaking"]):
        return "news"

    if any(w in q for w in ["search", "find", "look up", ".com"]):
        return "web"

    if "time" in q:
        return "time"

    if "who am i" in q or "my name" in q:
        return "identity"

    return "general"
