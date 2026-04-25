import unittest
from unittest.mock import patch

from backend.app.services.news_service import get_search_analysis


class WebSearchTests(unittest.TestCase):
    def test_search_the_internet_without_topic_asks_for_topic(self):
        result = get_search_analysis("search the internet")

        self.assertEqual(result["type"], "analysis")
        self.assertEqual(result["tool"], "search")
        self.assertEqual(result["content"]["summary"], "What do you want to search for?")
        self.assertNotIn("executions", result["content"])

    @patch("backend.app.services.news_service.search_web", return_value="Answer: AI agents help orchestrate tools.\n\nSources:\n1. Example - https://example.com")
    def test_search_the_internet_for_topic_returns_internal_results(self, search_web_mock):
        result = get_search_analysis("search the internet for AI agents")
        executions = result["content"].get("executions", [])

        search_web_mock.assert_called_once_with("AI agents")
        self.assertEqual(
            result["content"]["summary"],
            "Answer: AI agents help orchestrate tools.\n\nSources:\n1. Example - https://example.com",
        )
        self.assertEqual(len(executions), 1)
        self.assertEqual(executions[0]["type"], "web_search")
        self.assertEqual(executions[0]["query"], "AI agents")

    @patch("backend.app.services.news_service.search_web", return_value="Answer: Expect local weather updates.\n\nSources:\n1. Example - https://example.com/weather")
    def test_look_up_returns_internal_results(self, search_web_mock):
        result = get_search_analysis("look up weather tomorrow")
        executions = result["content"].get("executions", [])

        search_web_mock.assert_called_once_with("weather tomorrow")
        self.assertEqual(len(executions), 1)
        self.assertEqual(executions[0]["type"], "web_search")
        self.assertEqual(executions[0]["query"], "weather tomorrow")


if __name__ == "__main__":
    unittest.main()