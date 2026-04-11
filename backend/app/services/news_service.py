import httpx
from app.core.config import get_settings

class NewsService:
	def __init__(self, client: httpx.AsyncClient):
		self.client = client
		self.settings = get_settings()

	async def handle(self, request):
		url = "https://newsapi.org/v2/top-headlines"
		params = {
			"apiKey": self.settings.news_api_key,
			"country": getattr(request, "country", None) or "us",
			"category": getattr(request, "category", None),
			"q": getattr(request, "news_query", None),
			"pageSize": 3,
		}
		# Remove None values
		params = {k: v for k, v in params.items() if v is not None}

		response = await self.client.get(url, params=params)
		response.raise_for_status()
		data = response.json()
		articles = data.get("articles", [])
		if not articles:
			answer = "No news found."
		else:
			headlines = [f"- {a['title']}" for a in articles[:3] if 'title' in a]
			answer = "Top news:\n" + "\n".join(headlines)
		return {"answer": answer}
