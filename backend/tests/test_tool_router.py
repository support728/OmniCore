import unittest
from unittest.mock import patch

from backend.app.services.tool_router import route_query


class ToolRouterTests(unittest.TestCase):
    @patch("backend.app.services.tool_router.classify_intent", return_value="youtube_search")
    @patch("backend.app.services.tool_router._extract_youtube_query", return_value="cooking")
    @patch("backend.app.services.tool_router.search_youtube_videos", return_value=[{"videoId": "abc"}])
    @patch("backend.app.services.tool_router.summarize_youtube_results", return_value="YouTube results ready.")
    def test_route_query_returns_youtube_payload(self, _summary_mock, _search_mock, _extract_mock, _intent_mock):
        result = route_query("search youtube for cooking")

        self.assertEqual(result["type"], "youtube_search")
        self.assertEqual(result["summary"], "YouTube results ready.")
        self.assertEqual(result["data"], [{"videoId": "abc"}])

    @patch("backend.app.services.tool_router.classify_intent", return_value="web_search")
    @patch("backend.app.services.tool_router._extract_web_query", return_value="best laptops")
    @patch("backend.app.services.tool_router.search_web_results", return_value=[{"title": "Best Laptops"}])
    @patch("backend.app.services.tool_router.summarize_search_results", return_value="Web results ready.")
    def test_route_query_returns_web_payload(self, _summary_mock, _search_mock, _extract_mock, _intent_mock):
        result = route_query("find the best laptops")

        self.assertEqual(result["type"], "web_search")
        self.assertEqual(result["summary"], "Web results ready.")
        self.assertEqual(result["data"], [{"title": "Best Laptops"}])

    @patch("backend.app.services.tool_router.classify_intent", return_value="weather")
    @patch("backend.app.services.tool_router.get_weather_reply", return_value={"city": "Paris", "temperature": 70})
    @patch("backend.app.services.tool_router.format_weather_reply", return_value="Paris weather ready.")
    def test_route_query_returns_weather_payload(self, _format_mock, _weather_mock, _intent_mock):
        result = route_query("weather in Paris")

        self.assertEqual(result["type"], "weather")
        self.assertEqual(result["summary"], "Paris weather ready.")
        self.assertEqual(result["data"]["city"], "Paris")

    @patch("backend.app.services.tool_router.classify_intent", return_value="news")
    @patch("backend.app.services.tool_router._extract_news_topic", return_value="AI")
    @patch(
        "backend.app.services.tool_router.get_news",
        return_value={
            "status": "success",
            "articles": [
                {
                    "title": "AI News",
                    "description": "New model released",
                    "source": "Example News",
                    "url": "https://example.com/news",
                    "publishedAt": "2026-04-17T00:00:00+00:00",
                }
            ],
        },
    )
    def test_route_query_returns_news_payload(self, _news_mock, _extract_mock, _intent_mock):
        result = route_query("latest news about AI")

        self.assertEqual(result["type"], "news")
        self.assertEqual(result["data"][0]["title"], "AI News")
        self.assertEqual(result["data"][0]["source"], "Example News")

    @patch("backend.app.services.tool_router.classify_intent", return_value="general")
    def test_route_query_returns_general_payload(self, _intent_mock):
        result = route_query("help me write a poem")

        self.assertEqual(result["type"], "general")
        self.assertEqual(result["summary"], "I can help with that. What would you like to know?")
        self.assertEqual(result["data"], [])


if __name__ == "__main__":
    unittest.main()