import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import app


class NewsSearchEndpointTests(unittest.TestCase):
    def test_news_search_endpoint_returns_structured_news_payload(self):
        with patch(
            "backend.app.services.news_service.get_news",
            return_value={
                "status": "success",
                "articles": [
                    {
                        "title": "AI regulation expands",
                        "description": "Governments are broadening oversight of frontier AI systems.",
                        "source": "Example News",
                        "url": "https://example.com/news/ai",
                        "publishedAt": "2026-04-17T10:00:00+00:00",
                    }
                ],
            },
        ):
            with TestClient(app) as client:
                response = client.get("/news-search", params={"q": "AI"})

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["type"], "search_results")
        self.assertEqual(payload["response"], payload["summary"])
        self.assertEqual(payload["data"]["intent"], "news")
        self.assertEqual(payload["data"]["topic"], "AI")
        self.assertEqual(len(payload["data"]["results"]), 1)
        self.assertEqual(payload["results"][0]["title"], "AI regulation expands")
        self.assertEqual(payload["results"][0]["source"], "Example News")
        self.assertEqual(payload["results"][0]["rank"], 1)
        self.assertIn("why", payload["results"][0])


if __name__ == "__main__":
    unittest.main()