from datetime import datetime
import requests
from app.core.config import settings

def web_search(query: str) -> dict:
    if not settings.SERPAPI_API_KEY:
        return {"answer": "Missing SERPAPI_API_KEY", "results": []}

    url = "https://serpapi.com/search"
    params = {
        "q": query,
        "api_key": settings.SERPAPI_API_KEY,
        "engine": "google",
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

        results = []
        for r in data.get("organic_results", [])[:5]:
            results.append(
                {
                    "title": r.get("title"),
                    "link": r.get("link"),
                    "snippet": r.get("snippet"),
                }
            )

        return {
            "answer": f"Top results for '{query}'",
            "results": results,
        }
    except Exception as e:
        return {"answer": f"Search failed: {e}", "results": []}

def get_weather() -> str:
    try:
        response = requests.get("https://wttr.in/?format=3", timeout=10)
        response.raise_for_status()
        return response.text
    except Exception:
        return "Weather unavailable"

def get_news() -> str:
    if not settings.NEWS_API_KEY:
        return "Missing NEWS_API_KEY"

    try:
        url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={settings.NEWS_API_KEY}"
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        data = response.json()
        articles = data.get("articles", [])
        if not articles:
            return "No news available"
        return articles[0].get("title", "No news available")
    except Exception:
        return "News unavailable"

def get_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_identity() -> str:
    return "I'm Nova, your personal AI assistant."
