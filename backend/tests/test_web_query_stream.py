import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import app


class WebQueryStreamTests(unittest.TestCase):
    def _query_response(self, query: str):
        payload = {"query": query, "session_id": "test-web-stream"}

        with TestClient(app) as client:
            response = client.post("/query", json=payload)
            self.assertEqual(response.status_code, 200)
            return response.json()

    @patch("backend.app.services.news_service.search_web", return_value="Answer: AI agents help coordinate tools.\n\nSources:\n1. Example - https://example.com")
    def test_web_topic_emits_internal_summary(self, _search_web_mock):
        with patch(
            "backend.app.services.news_service.search_web_results",
            return_value=[{"title": "AI Agents", "link": "https://example.com", "snippet": "AI agents help coordinate tools."}],
        ), patch(
            "backend.app.services.news_service.summarize_search_results",
            return_value="AI agents help coordinate tools.",
        ):
            payload = self._query_response("search the internet for AI agents")

        self.assertEqual(payload["type"], "search_results")
        self.assertEqual(payload["data"]["query"], "AI agents")
        self.assertIn("AI agents help coordinate tools.", payload["summary"])

    def test_empty_web_topic_emits_no_execution(self):
        payload = self._query_response("search the internet")

        self.assertEqual(payload["type"], "analysis")
        self.assertEqual(payload["summary"], "What do you want to search for?")
        self.assertEqual(payload["data"]["intent"], "web_search")


if __name__ == "__main__":
    unittest.main()