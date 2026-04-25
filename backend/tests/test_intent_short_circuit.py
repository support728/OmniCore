import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.news_service import classify_intent


class IntentShortCircuitTests(unittest.TestCase):
    def _query_response(self, query: str):
        with TestClient(app) as client:
            response = client.post("/query", json={"query": query, "session_id": "intent-short-circuit"})
            self.assertEqual(response.status_code, 200)
            return response.json()

    def test_unified_classifier_covers_all_target_intents(self):
        session_id = "intent-short-circuit"
        self.assertEqual(classify_intent("look up weather tomorrow", session_id), "web_search")
        self.assertEqual(classify_intent("search the internet for AI agents today", session_id), "web_search")
        self.assertEqual(classify_intent("search YouTube for AI agents", session_id), "youtube_search")
        self.assertEqual(classify_intent("forecast for Paris", session_id), "weather")
        self.assertEqual(classify_intent("latest news about AI", session_id), "news")
        self.assertEqual(classify_intent("write me a short poem", session_id), "general")

    def test_web_intent_bypasses_general_handler(self):
        with patch("backend.app.services.news_service.get_general_reply") as general_mock, patch(
            "backend.app.services.news_service.search_web_results",
            return_value=[{"title": "AI Agents", "link": "https://example.com", "snippet": "Snippet"}],
        ), patch(
            "backend.app.services.news_service.summarize_search_results",
            return_value="AI agents summary",
        ):
            payload = self._query_response("search the internet for AI agents")

        general_mock.assert_not_called()
        self.assertEqual(payload["type"], "search_results")
        self.assertEqual(payload["data"]["query"], "AI agents")

    def test_youtube_intent_bypasses_general_handler(self):
        with patch("backend.app.services.news_service.get_general_reply") as general_mock:
            payload = self._query_response("search YouTube for AI agents")

        general_mock.assert_not_called()
        self.assertEqual(payload["type"], "video_results")
        self.assertEqual(payload["data"]["query"], "AI agents")


if __name__ == "__main__":
    unittest.main()