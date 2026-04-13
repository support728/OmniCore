def detect_route(request):
    text = request.message.lower()

    if "weather" in text:
        return "weather"
    elif "news" in text:
        return "news"
    else:
        return "general"
