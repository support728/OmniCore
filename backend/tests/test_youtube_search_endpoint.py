import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import app


class YouTubeSearchEndpointTests(unittest.TestCase):
    def test_youtube_search_endpoint_returns_video_results(self):
        with patch(
            "backend.app.services.news_service.search_youtube_videos",
            return_value=[
                {
                    "videoId": "abc123xyz89",
                    "title": "AI Agents Explained",
                    "channel": "OmniCore Labs",
                    "thumbnail": "https://i.ytimg.com/vi/abc123xyz89/hqdefault.jpg",
                    "url": "https://www.youtube.com/watch?v=abc123xyz89",
                    "embedUrl": "https://www.youtube-nocookie.com/embed/abc123xyz89",
                    "snippet": "OmniCore Labs • 12:30 • 20K views",
                }
            ],
        ), patch(
            "backend.app.services.news_service.summarize_youtube_results",
            return_value="Top YouTube videos for AI agents are ready below.",
        ):
            with TestClient(app) as client:
                response = client.get("/youtube-search", params={"q": "AI agents"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "type": "video_results",
                "summary": "Top YouTube videos for AI agents are ready below.",
                "data": {
                    "intent": "youtube_search",
                    "tool": "search",
                    "query": "AI agents",
                    "results": [
                        {
                            "videoId": "abc123xyz89",
                            "title": "AI Agents Explained",
                            "channel": "OmniCore Labs",
                            "thumbnail": "https://i.ytimg.com/vi/abc123xyz89/hqdefault.jpg",
                            "url": "https://www.youtube.com/watch?v=abc123xyz89",
                            "embedUrl": "https://www.youtube-nocookie.com/embed/abc123xyz89",
                            "snippet": "OmniCore Labs • 12:30 • 20K views",
                        }
                    ],
                },
                "results": [
                    {
                        "videoId": "abc123xyz89",
                        "title": "AI Agents Explained",
                        "channel": "OmniCore Labs",
                        "thumbnail": "https://i.ytimg.com/vi/abc123xyz89/hqdefault.jpg",
                        "url": "https://www.youtube.com/watch?v=abc123xyz89",
                        "embedUrl": "https://www.youtube-nocookie.com/embed/abc123xyz89",
                        "snippet": "OmniCore Labs • 12:30 • 20K views",
                    }
                ],
            },
        )

    def test_youtube_search_endpoint_prompts_for_missing_query(self):
        with TestClient(app) as client:
            response = client.get("/youtube-search")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["type"], "analysis")
        self.assertEqual(response.json()["summary"], "Tell me what you want to search for on YouTube.")


if __name__ == "__main__":
    unittest.main()