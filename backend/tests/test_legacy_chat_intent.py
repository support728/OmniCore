import unittest
from unittest.mock import patch

from backend.app.services.intent_router import handle_message


class LegacyChatIntentTests(unittest.TestCase):
    @patch(
        "backend.app.services.news_service.search_web_results",
        return_value=[{"title": "AI Agents", "link": "https://example.com", "snippet": "AI agents help coordinate tools."}],
    )
    @patch("backend.app.services.news_service.summarize_search_results", return_value="AI agents help coordinate tools.")
    def test_web_intent_bypasses_ai_reply_and_returns_internal_reply(self, _summary_mock, _search_results_mock):
        with patch("backend.app.services.intent_router.get_ai_reply") as ai_reply_mock:
            result = handle_message("search the internet for AI agents", "legacy-chat-web")

        ai_reply_mock.assert_not_called()
        self.assertEqual(result["type"], "search_results")
        self.assertEqual(result["reply"], "AI agents help coordinate tools.")
        self.assertEqual(result["action"]["type"], "web_search")
        self.assertEqual(result["action"]["query"], "AI agents")
        self.assertEqual(result["data"]["intent"], "web_search")

    def test_youtube_intent_bypasses_ai_reply_and_returns_open_url_action(self):
        with patch("backend.app.services.intent_router.get_ai_reply") as ai_reply_mock:
            result = handle_message("search YouTube for AI agents", "legacy-chat-youtube")

        ai_reply_mock.assert_not_called()
        self.assertEqual(result["type"], "video_results")
        self.assertEqual(result["action"]["type"], "youtube_search")
        self.assertEqual(result["action"]["query"], "AI agents")



if __name__ == "__main__":
    unittest.main()