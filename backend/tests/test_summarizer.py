import unittest
from unittest.mock import patch

from backend.app.services.summarizer import summarize_results


class SummarizerTests(unittest.TestCase):
    @patch("backend.app.services.summarizer.get_settings")
    def test_web_summary_falls_back_when_no_openai_key(self, settings_mock):
        settings_mock.return_value.openai_api_key = ""
        settings_mock.return_value.openai_model = "gpt-4o-mini"

        summary = summarize_results(
            "web_search",
            "AI agents",
            [
                {"title": "What are AI agents?", "snippet": "AI agents can plan and use tools.", "source": "Example"},
                {"title": "Enterprise AI", "snippet": "Businesses use AI agents for workflows.", "source": "Example 2"},
            ],
        )

        self.assertIn("The strongest results for AI agents point to", summary)
        self.assertIn("AI agents can plan and use tools", summary)

    @patch("backend.app.services.summarizer.get_settings")
    def test_news_summary_falls_back_when_results_empty(self, settings_mock):
        settings_mock.return_value.openai_api_key = ""
        settings_mock.return_value.openai_model = "gpt-4o-mini"

        summary = summarize_results("news", "latest AI news", [])

        self.assertEqual(summary, 'I could not find strong recent coverage for "latest AI news".')

    @patch("backend.app.services.summarizer.get_settings")
    def test_weather_summary_falls_back_for_forecast(self, settings_mock):
        settings_mock.return_value.openai_api_key = ""
        settings_mock.return_value.openai_model = "gpt-4o-mini"

        summary = summarize_results(
            "weather",
            "weather in Boston tomorrow",
            {
                "city": "Boston",
                "temperature": 68,
                "description": "clear skies",
                "forecast_days": [
                    {"label": "Tomorrow", "temperature": 70, "description": "light clouds"},
                ],
            },
        )

        self.assertIn("Boston is currently 68°F with clear skies.", summary)
        self.assertIn("Expect Tomorrow to be around 70°F with light clouds.", summary)


if __name__ == "__main__":
    unittest.main()