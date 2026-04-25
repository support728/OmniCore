import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import app


class SearchEndpointTests(unittest.TestCase):
    def test_web_search_endpoint_returns_structured_results(self):
        with patch(
            "backend.app.services.news_service.search_web_results",
            return_value=[
                {
                    "title": "AI Agents Overview",
                    "link": "https://example.com/ai-agents",
                    "snippet": "A concise explanation of AI agents.",
                    "source": "example.com",
                    "why": "Relevant because the title directly addresses AI agents.",
                    "score": 10.0,
                    "rank": 1,
                }
            ],
        ), patch(
            "backend.app.services.news_service.summarize_search_results",
            return_value="AI agents combine reasoning, tools, and automation across the top sources.",
        ):
            with TestClient(app) as client:
                response = client.get("/web-search", params={"q": "AI agents"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["type"], "search_results")
        self.assertEqual(payload["summary"], "AI agents combine reasoning, tools, and automation across the top sources.")
        self.assertEqual(payload["response"], payload["summary"])
        self.assertEqual(payload["data"]["intent"], "web_search")
        self.assertEqual(payload["data"]["query"], "AI agents")
        self.assertEqual(payload["data"]["results"][0]["rank"], 1)
        self.assertIn("why", payload["data"]["results"][0])

    def test_web_search_endpoint_prompts_for_missing_query(self):
        with TestClient(app) as client:
            response = client.get("/web-search")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["type"], "analysis")
        self.assertEqual(response.json()["summary"], "What do you want to search for?")

    def test_search_endpoint_remains_alias_for_web_search(self):
        with patch(
            "backend.app.services.news_service.search_web_results",
            return_value=[{"title": "Example", "link": "https://example.com", "snippet": "Example snippet"}],
        ), patch(
            "backend.app.services.news_service.summarize_search_results",
            return_value="Example summary",
        ):
            with TestClient(app) as client:
                response = client.get("/search", params={"q": "example"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["type"], "search_results")
        self.assertEqual(response.json()["summary"], "Example summary")
        self.assertEqual(response.json()["response"], "Example summary")


if __name__ == "__main__":
    unittest.main()