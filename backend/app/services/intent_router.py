def detect_route(request):
    msg = request.message.lower()

    if any(k in msg for k in ["weather", "temperature", "forecast"]):
        return "weather"
    elif any(k in msg for k in ["news", "headline", "latest", "breaking"]):
        return "news"
    else:
        return "general"
