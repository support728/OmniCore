import requests
from app.core.config import settings

def run_news() -> str:
    if not settings.NEWS_API_KEY:
        return "Missing NEWS_API_KEY"

    try:
        url = "https://newsapi.org/v2/top-headlines"
        params = {"country": "us", "apiKey": settings.NEWS_API_KEY}
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        articles = data.get("articles", [])
        if not articles:
            return "No news available"
        return articles[0].get("title", "No news available")
    except Exception:
        return "News unavailable"
