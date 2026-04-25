import unittest

from backend.app.services.intent_router import classify_intent


class IntentRouterClassifierTests(unittest.TestCase):
    def test_returns_youtube_search_for_youtube_queries(self):
        self.assertEqual(classify_intent("search youtube for cooking"), "youtube_search")

    def test_returns_weather_for_weather_terms(self):
        self.assertEqual(classify_intent("weather tomorrow in Paris"), "weather")
        self.assertEqual(classify_intent("weekend forecast"), "weather")

    def test_does_not_treat_plain_weekend_or_tomorrow_as_weather(self):
        self.assertEqual(classify_intent("I need to feed people this weekend"), "general")
        self.assertEqual(classify_intent("What should I actually do tomorrow?"), "general")

    def test_returns_news_for_news_terms(self):
        self.assertEqual(classify_intent("latest news about AI"), "news")
        self.assertEqual(classify_intent("headlines today"), "news")

    def test_returns_web_search_for_search_terms(self):
        self.assertEqual(classify_intent("find the best laptops"), "web_search")
        self.assertEqual(classify_intent("search the internet for recipes"), "web_search")

    def test_returns_general_when_no_keywords_match(self):
        self.assertEqual(classify_intent("write me a poem"), "general")


if __name__ == "__main__":
    unittest.main()