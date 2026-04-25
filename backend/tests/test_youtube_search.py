import unittest

from backend.app.services.news_service import get_search_analysis


class YouTubeSearchTests(unittest.TestCase):
    def test_search_youtube_without_topic_asks_for_topic(self):
        result = get_search_analysis("search YouTube")

        self.assertEqual(result["type"], "analysis")
        self.assertEqual(result["tool"], "search")
        self.assertEqual(
            result["content"]["summary"],
            "Tell me what you want to search for on YouTube.",
        )
        self.assertNotIn("executions", result["content"])

    def test_search_youtube_for_topic_returns_open_url_execution(self):
        result = get_search_analysis("search YouTube for AI agents")
        executions = result["content"].get("executions", [])

        self.assertEqual(len(executions), 1)
        self.assertEqual(executions[0]["type"], "youtube_search")
        self.assertEqual(executions[0]["query"], "AI agents")
        self.assertEqual(
            result["content"]["summary"],
            'Showing YouTube results for "AI agents" inside OmniCore.',
        )

    def test_look_up_on_youtube_returns_open_url_execution(self):
        result = get_search_analysis("look up cooking shorts on YouTube")
        executions = result["content"].get("executions", [])

        self.assertEqual(len(executions), 1)
        self.assertEqual(executions[0]["type"], "youtube_search")
        self.assertEqual(executions[0]["query"], "cooking shorts")

    def test_plain_youtube_prefix_returns_open_url_execution(self):
        result = get_search_analysis("YouTube funny cats")
        executions = result["content"].get("executions", [])

        self.assertEqual(len(executions), 1)
        self.assertEqual(executions[0]["type"], "youtube_search")
        self.assertEqual(executions[0]["query"], "funny cats")


if __name__ == "__main__":
    unittest.main()