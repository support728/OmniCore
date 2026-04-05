import requests
from app.core.config import settings

def run_web_search(query: str) -> dict:
    if not settings.SERPAPI_API_KEY:
        return {"answer": "Missing SERPAPI_API_KEY", "results": []}

    try:
        response = requests.get(
            "https://serpapi.com/search",
            params={
                "q": query,
                "api_key": settings.SERPAPI_API_KEY,
                "engine": "google",
            },
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("organic_results", [])[:5]:
            results.append(
                {
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "snippet": item.get("snippet"),
                }
            )

        return {"answer": f"Top results for '{query}'", "results": results}
    except Exception as exc:
        return {"answer": f"Search failed: {exc}", "results": []}
