import unittest

from backend.app.services.search_intelligence import build_answer_first_summary, normalize_and_rank_results


class SearchIntelligenceTests(unittest.TestCase):
    def test_normalize_and_rank_results_prefers_exact_title_and_recent_source(self):
        results = normalize_and_rank_results(
            "latest ai agents",
            [
                {
                    "title": "Latest AI agents market update",
                    "link": "https://www.reuters.com/technology/ai-agents",
                    "snippet": "A current roundup of AI agent releases and adoption.",
                    "publishedAt": "2026-04-18T12:00:00+00:00",
                    "source": "Reuters",
                },
                {
                    "title": "Enterprise automation overview",
                    "link": "https://example.com/automation",
                    "snippet": "Background on enterprise automation patterns.",
                    "source": "Example",
                },
            ],
            "web_search",
        )

        self.assertEqual(results[0]["title"], "Latest AI agents market update")
        self.assertEqual(results[0]["rank"], 1)
        self.assertIn("Relevant because", results[0]["why"])

    def test_build_answer_first_summary_handles_empty_results(self):
        summary = build_answer_first_summary("web_search", "AI agents", [])

        self.assertEqual(summary, 'I could not find strong results for "AI agents".')


if __name__ == "__main__":
    unittest.main()