import requests
from app.config import get_settings

class WebSearchService:
    def __init__(self):
        self.settings = get_settings()

    def search(self, query: str) -> str:
        try:
            url = "https://serpapi.com/search.json"
            params = {
                "q": query,
                "api_key": self.settings.serpapi_api_key,
                "engine": "google"
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            results = data.get("organic_results", [])[:3]
            if not results:
                return ""
            summary = ""
            for r in results:
                title = r.get("title", "")
                snippet = r.get("snippet", "")
                summary += f"{title} - {snippet}\n"
            return summary.strip()
        except Exception:
            return ""
        self.endpoint = "https://api.bing.microsoft.com/v7.0/search"

    async def search(self, query):
        if not self.api_key:
            return None
        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        params = {"q": query, "mkt": "en-US", "count": 5}
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(self.endpoint, headers=headers, params=params, timeout=8)
                if resp.status_code == 200:
                    data = resp.json()
                    results = []
                    for item in data.get("webPages", {}).get("value", []):
                        results.append({
                            "name": item.get("name"),
                            "snippet": item.get("snippet"),
                            "url": item.get("url")
                        })
                    return results
                return None
            except Exception:
                return None
