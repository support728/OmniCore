import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.chat_router import route_user_query
from backend.app.services.memory_service import append_message
from backend.app.services.intent_router import classify_intent
from backend.app.services.response_style import sanitize_frontend_payload, strict_output_filter


class ChatRouterTests(unittest.TestCase):
    def test_classify_intent_detects_today_headline_as_news(self):
        self.assertEqual(classify_intent("top headline from today"), "news")

    def test_classify_intent_detects_current_events_as_news(self):
        self.assertEqual(classify_intent("current events"), "news")

    @patch("backend.app.services.chat_router.search_youtube_videos", return_value=[{"videoId": "abc", "title": "Cooking 101", "channel": "Chef", "thumbnail": "thumb", "url": "https://youtube.com/watch?v=abc", "embedUrl": "https://youtube.com/embed/abc", "snippet": "Basics"}])
    @patch("backend.app.services.chat_router.summarize_youtube_results", return_value="YouTube results ready.")
    def test_route_user_query_returns_youtube_response(self, _summary_mock, _search_mock):
        result = route_user_query("search youtube for cooking")

        self.assertEqual(result["type"], "youtube_search")
        self.assertEqual(result["summary"], "YouTube results ready.")
        self.assertEqual(result["data"]["query"], "cooking")
        self.assertEqual(result["data"]["actions"], ["Play video", "Show more videos"])

    @patch("backend.app.services.chat_router.search_web_results", return_value=[{"title": "Best Laptops", "link": "https://example.com", "snippet": "Top picks", "source": "example.com", "why": "Relevant because the title directly addresses best laptops.", "rank": 1, "score": 8.0}])
    @patch("backend.app.services.chat_router.summarize_results", return_value="Web results ready.")
    def test_route_user_query_returns_web_search_response(self, _summary_mock, _search_mock):
        result = route_user_query("find the best laptops")

        self.assertEqual(result["type"], "web_search")
        self.assertEqual(result["summary"], "Web results ready.")
        self.assertEqual(result["response"], "Web results ready.")
        self.assertEqual(result["data"]["results"][0]["title"], "Best Laptops")
        self.assertEqual(result["data"]["results"][0]["rank"], 1)
        self.assertEqual(result["data"]["actions"], ["Summarize results", "Open top result", "Search deeper"])

    @patch("backend.app.services.chat_router.get_weather_reply", return_value={"city": "Paris", "temperature": 70, "description": "clear skies"})
    @patch("backend.app.services.chat_router.summarize_results", return_value="Paris is warm today with clear skies.")
    def test_route_user_query_returns_weather_response(self, _summary_mock, _weather_mock):
        result = route_user_query("weather in Paris")

        self.assertEqual(result["type"], "weather")
        self.assertEqual(result["summary"], "Right now in Paris, it's 70°F with clear skies.")
        self.assertEqual(result["data"]["city"], "Paris")
        self.assertIn("Compare current conditions with tomorrow's forecast in Paris", result["data"]["actions"])

    @patch("backend.app.services.chat_router.get_news", return_value={"status": "success", "articles": [{"title": "AI News", "description": "New model released", "source": "Example News", "url": "https://example.com/news", "publishedAt": "2026-04-17T00:00:00+00:00"}]})
    @patch("backend.app.services.chat_router.summarize_results", return_value="The latest AI news centers on a new model release and its business impact.")
    def test_route_user_query_returns_news_response(self, _summary_mock, _news_mock):
        result = route_user_query("latest news about AI")

        self.assertEqual(result["type"], "news")
        self.assertEqual(result["summary"], "The latest AI news centers on a new model release and its business impact.")
        self.assertEqual(result["response"], result["summary"])
        self.assertEqual(result["data"]["query"], "latest news about AI")
        self.assertEqual(result["data"]["results"][0]["source"], "Example News")
        self.assertEqual(result["data"]["results"][0]["rank"], 1)
        self.assertEqual(result["data"]["actions"], ["Summarize coverage", "Compare sources", "Search related news"])

    @patch("backend.app.services.chat_router.get_news", return_value={"status": "error", "message": "News service unavailable.", "articles": []})
    def test_route_user_query_returns_news_error_summary_without_ai(self, _news_mock):
        result = route_user_query("latest AI news")

        self.assertEqual(result["type"], "news")
        self.assertEqual(result["summary"], "I couldn't find live headlines right now, but here are some general updates.")
        self.assertEqual(result["data"]["results"], [])

    @patch("backend.app.services.chat_router.get_news", return_value={"status": "no_results", "message": "No results.", "articles": []})
    def test_route_user_query_returns_news_fallback_when_empty(self, _news_mock):
        result = route_user_query("top headline from today")

        self.assertEqual(result["type"], "news")
        self.assertEqual(result["summary"], "I couldn't find live headlines right now, but here are some general updates.")
        self.assertEqual(result["data"]["results"], [])

    @patch("backend.app.services.chat_router.get_news", return_value={"status": "success", "articles": [{"title": "OpenAI Update", "description": "Major release", "source": "Wire", "url": "https://example.com/openai", "publishedAt": "2026-04-17T00:00:00+00:00"}]})
    @patch("backend.app.services.chat_router.summarize_results", return_value="OpenAI remains the focus of today's headlines.")
    def test_route_user_query_routes_today_headline_query_to_news(self, _summary_mock, _news_mock):
        result = route_user_query("top headline from today")

        self.assertEqual(result["type"], "news")
        self.assertEqual(result["summary"], "OpenAI remains the focus of today's headlines.")

    @patch("backend.app.services.chat_router.get_news", return_value={"status": "success", "articles": [{"title": "OpenAI Update", "description": "Major release", "source": "Wire", "url": "https://example.com/openai", "publishedAt": "2026-04-17T00:00:00+00:00"}]})
    @patch("backend.app.services.chat_router.summarize_results", return_value="Current events are available in structured form.")
    def test_route_user_query_routes_current_events_to_news(self, _summary_mock, _news_mock):
        result = route_user_query("current events")

        self.assertEqual(result["type"], "news")
        self.assertEqual(result["summary"], "Current events are available in structured form.")

    @patch("backend.app.services.chat_router.get_ai_reply", return_value={"reply": "Here is a short poem."})
    def test_route_user_query_returns_general_response(self, _ai_mock):
        result = route_user_query("write me a poem")

        self.assertEqual(result["type"], "general")
        self.assertEqual(result["summary"], "Here is a short poem.")
        self.assertEqual(result["data"]["reply"], "Here is a short poem.")
        self.assertEqual(result["data"]["actions"], ["Explain that differently", "Give me next steps"])

    @patch(
        "backend.app.services.chat_router.get_ai_reply",
        return_value={
            "reply": "Tests passed. I updated the backend system behavior. Final answer: You're Saye."
        },
    )
    def test_route_user_query_strips_meta_commentary_from_general_reply(self, _ai_mock):
        result = route_user_query("tell me something interesting", session_id="s1", user_id="u1")

        self.assertEqual(result["type"], "general")
        self.assertEqual(result["summary"], "You're Saye.")
        self.assertEqual(result["data"]["reply"], "You're Saye.")

    @patch("backend.app.services.chat_router.get_ai_reply", return_value={"reply": "You asked me to expand the earlier LLC answer, so here is a deeper version."})
    def test_route_user_query_uses_explicit_history_for_context(self, ai_mock):
        result = route_user_query(
            "expand that",
            session_id="explicit-history-session",
            history=[
                {"role": "user", "content": "What is an LLC?"},
                {"role": "assistant", "content": "An LLC protects the owner from business liabilities."},
            ],
        )

        self.assertEqual(result["type"], "general")
        self.assertIn("deeper version", result["summary"])
        _, kwargs = ai_mock.call_args
        self.assertEqual(
            kwargs["conversation_history"],
            [
                {"role": "user", "content": "What is an LLC?"},
                {"role": "assistant", "content": "An LLC protects the owner from business liabilities."},
            ],
        )

    def test_strict_output_filter_removes_examples_and_meta_lines(self):
        raw = (
            "Validation: current behavior is aligned.\n"
            "Replace: Your name is Saye. -> You're Saye.\n"
            "Final reply: You're Saye."
        )

        self.assertEqual(strict_output_filter(raw), "You're Saye.")

    def test_sanitize_frontend_payload_filters_summary_and_reply(self):
        payload = {
            "type": "general",
            "summary": "Implementation details: patched the router. Final answer: You're Saye.",
            "data": {
                "reply": "Tests passed. Final reply: You're Saye.",
                "actions": ["Explain that differently"],
            },
        }

        sanitized = sanitize_frontend_payload(payload)
        self.assertEqual(sanitized["summary"], "You're Saye.")
        self.assertEqual(sanitized["data"]["reply"], "You're Saye.")

    @patch("backend.app.services.chat_router.search_web_results", return_value=[{"title": "Best Laptops", "link": "https://example.com", "snippet": "Top picks", "source": "example.com", "why": "Relevant because the title directly addresses best laptops.", "rank": 1, "score": 8.0}])
    @patch("backend.app.services.chat_router.summarize_results", return_value="Web results ready.")
    def test_chat_endpoint_uses_main_router(self, _summary_mock, _search_mock):
        with TestClient(app) as client:
            response = client.post("/api/chat", json={"message": "find the best laptops"})

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["type"], "general")
        self.assertEqual(payload["content"], "Web results ready.")
        self.assertEqual(payload["actions"], ["Summarize results", "Open top result", "Search deeper"])
        self.assertEqual(payload["meta"]["source_type"], "web_search")

    @patch("backend.app.services.chat_router.search_web_results", return_value=[{"title": "Best Laptops", "link": "https://example.com", "snippet": "Top picks", "source": "example.com", "why": "Relevant because the title directly addresses best laptops.", "rank": 1, "score": 8.0}])
    @patch("backend.app.services.chat_router.summarize_results", return_value="Web results ready.")
    def test_chat_endpoint_accepts_query_alias(self, _summary_mock, _search_mock):
        with TestClient(app) as client:
            response = client.post("/api/chat", json={"query": "find the best laptops"})

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["type"], "general")
        self.assertEqual(payload["content"], "Web results ready.")
        self.assertEqual(payload["meta"]["source_type"], "web_search")

    @patch("backend.app.services.chat_router.get_ai_reply", return_value={"reply": "You asked for more detail on the earlier answer, so here is the expanded version."})
    def test_chat_endpoint_accepts_history_payload(self, ai_mock):
        with TestClient(app) as client:
            response = client.post(
                "/api/chat",
                json={
                    "message": "expand that",
                    "history": [
                        {"role": "user", "content": "What is an LLC?"},
                        {"role": "assistant", "content": "An LLC protects the owner from business liabilities."},
                    ],
                },
            )

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["type"], "general")
        self.assertIn("expanded version", payload["content"])
        _, kwargs = ai_mock.call_args
        self.assertEqual(len(kwargs["conversation_history"]), 2)

    def test_chat_endpoint_requires_message(self):
        with TestClient(app) as client:
            response = client.post("/api/chat", json={"mode": "general"})

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["type"], "error")
        self.assertEqual(payload["content"], "Message is required.")
        self.assertEqual(payload["actions"], ["Retry"])

    def test_chat_endpoint_business_mode_returns_strict_contract(self):
        with TestClient(app) as client:
            response = client.post("/api/chat", json={"message": "Create a 90-day launch plan", "mode": "business"})

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["type"], "business")
        self.assertIn("Step 1", payload["content"])
        self.assertIn("Days 1-30", payload["content"])
        self.assertEqual(payload["actions"], ["Turn into checklist", "Generate pricing model", "Create staffing plan"])
        self.assertTrue(isinstance(payload["meta"].get("sections"), list))

    @patch("backend.app.services.chat_router.generate_image_result")
    def test_chat_endpoint_images_mode_returns_generated_image(self, image_mock):
        image_mock.return_value = {
            "type": "images",
            "content": "Generated image",
            "image_url": "https://example.com/image.png",
            "actions": ["Regenerate", "Make variations"],
            "meta": {"prompt": "Create a luxury real estate poster", "aspect_ratio": "4:5"},
        }

        with TestClient(app) as client:
            response = client.post(
                "/api/chat",
                json={"message": "Create a luxury real estate poster", "mode": "images", "aspect_ratio": "4:5"},
            )

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["type"], "images")
        self.assertEqual(payload["content"], "Generated image")
        self.assertEqual(payload["image_url"], "https://example.com/image.png")
        self.assertEqual(payload["actions"], ["Regenerate", "Make variations"])

    @patch("backend.app.services.chat_router.get_ai_reply", return_value={"reply": "An LLC protects the owner from business liabilities and separates personal and company obligations."})
    def test_chat_endpoint_general_mode_returns_strict_contract(self, _ai_mock):
        with TestClient(app) as client:
            response = client.post("/api/chat", json={"message": "Explain what an LLC is", "mode": "general"})

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["type"], "general")
        self.assertIn("LLC", payload["content"])
        self.assertNotIn("summary", payload)
        self.assertNotIn("response", payload)

    def test_route_user_query_explain_differently_rewrites_last_answer_shorter(self):
        session_id = "follow-up-explain"
        original = "An LLC protects the owner from business liabilities and separates personal and company obligations."
        append_message(session_id, "assistant", original, "general")

        result = route_user_query("Explain that differently", session_id=session_id)

        self.assertEqual(result["type"], "general")
        self.assertNotEqual(result["summary"], original)
        self.assertLess(len(result["summary"]), len(original))
        self.assertIn("LLC", result["summary"])

    def test_route_user_query_give_me_next_steps_returns_ordered_steps(self):
        session_id = "follow-up-steps"
        append_message(
            session_id,
            "assistant",
            "Choose the customer segment first. Set the offer and delivery scope. Track response rates after launch.",
            "general",
        )

        result = route_user_query("Give me next steps", session_id=session_id)

        self.assertEqual(result["type"], "general")
        self.assertIn("1.", result["summary"])
        self.assertIn("2.", result["summary"])
        self.assertIn("today", result["summary"].lower())

    @patch("backend.app.services.chat_router.get_ai_reply", return_value={"reply": "Additional angles: Evaluate vendor lock-in, team capability, and rollout dependencies before scaling.\n\nRisks and dependencies: Account for compliance review, data migration, and support load as adoption increases."})
    def test_route_user_query_search_deeper_returns_expanded_answer(self, _ai_mock):
        session_id = "follow-up-search-deeper"
        append_message(session_id, "assistant", "Start with one deployment path and validate it quickly.", "web_search")

        result = route_user_query("Search deeper", session_id=session_id)

        self.assertEqual(result["type"], "general")
        self.assertIn("Additional angles", result["summary"])
        self.assertIn("Risks and dependencies", result["summary"])
        self.assertEqual(result["data"]["actions"], ["Summarize results", "Open top result", "Search deeper"])

    @patch("backend.app.services.chat_router.get_ai_reply", return_value={"reply": "Best available answer: Start with the path that reduces implementation risk while preserving the required outcome.\n\nWhat it means: Use the most reliable source of truth, confirm dependencies, and avoid overbuilding before validation.\n\nWhat to look at next: Check prerequisites, ownership, and the first measurable milestone before rollout."})
    def test_chat_endpoint_open_top_result_returns_structured_full_answer(self, _ai_mock):
        session_id = "follow-up-open-top-result"
        append_message(session_id, "assistant", "Start with the path that reduces implementation risk.", "web_search")

        with TestClient(app) as client:
            response = client.post(
                "/api/chat",
                json={
                    "message": "Start with the path that reduces implementation risk.",
                    "action": "Open top result",
                    "mode": "general",
                    "session_id": session_id,
                },
            )

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["type"], "general")
        self.assertIn("Best available answer", payload["content"])
        self.assertIn("What it means", payload["content"])
        self.assertIn("What to look at next", payload["content"])


if __name__ == "__main__":
    unittest.main()