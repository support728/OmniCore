import unittest

from fastapi.testclient import TestClient

from backend.app.main import app


class YouTubeQueryStreamTests(unittest.TestCase):
    def _query_response(self, query: str):
        payload = {"query": query, "session_id": "test-youtube-stream"}

        with TestClient(app) as client:
            response = client.post("/query", json=payload)
            self.assertEqual(response.status_code, 200)
            return response.json()

    def test_youtube_topic_emits_open_url_execution(self):
        payload = self._query_response("search YouTube for AI agents")

        self.assertEqual(payload["type"], "video_results")
        self.assertEqual(payload["data"]["query"], "AI agents")
        self.assertIn("results", payload["data"])

    def test_empty_youtube_topic_emits_no_execution(self):
        payload = self._query_response("search YouTube")

        self.assertEqual(payload["type"], "analysis")
        self.assertEqual(payload["summary"], "Tell me what you want to search for on YouTube.")
        self.assertEqual(payload["data"]["intent"], "youtube_search")


if __name__ == "__main__":
    unittest.main()