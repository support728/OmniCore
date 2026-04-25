import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db import load_user_memory
from backend.app.services.memory_store import (
    clear_session,
    get_conversation,
    get_long_term_facts,
    get_session_facts,
    get_user_id,
    get_session_value,
    reset_memory_store,
)


class MemoryChatTests(unittest.TestCase):
    def setUp(self):
        reset_memory_store()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        reset_memory_store()

    def test_name_recall(self):
        session_id = "memory-name"

        first = self.client.post("/api/chat", json={"message": "My name is Saye", "session_id": session_id})
        second = self.client.post("/api/chat", json={"message": "What's my name?", "session_id": session_id})

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json()["content"], "Got it, you're Saye.")
        self.assertEqual(second.json()["content"], "You're Saye.")

    def test_location_recall(self):
        session_id = "memory-location"

        self.client.post("/api/chat", json={"message": "I live in Minneapolis", "session_id": session_id})
        response = self.client.post("/api/chat", json={"message": "Where do I live?", "session_id": session_id})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["content"], "You're in Minneapolis.")

    @patch("backend.app.services.chat_router.get_weather_reply")
    def test_weather_follow_up_uses_remembered_location(self, weather_mock):
        session_id = "memory-weather"
        weather_mock.return_value = {
            "city": "Minneapolis",
            "request_type": "tomorrow",
            "description": "sunny",
            "temperature": 72,
            "feels_like": 70,
            "humidity": 40,
        }

        self.client.post("/api/chat", json={"message": "I live in Minneapolis", "session_id": session_id})
        response = self.client.post("/api/chat", json={"message": "What's the weather tomorrow?", "session_id": session_id})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["type"], "general")
        self.assertEqual(response.json()["meta"]["source_type"], "weather")
        self.assertIn("Minneapolis tomorrow", response.json()["content"])
        self.assertIn("72°F", response.json()["content"])
        weather_mock.assert_called_once_with("What's the weather tomorrow?", fallback_city="Minneapolis")

    @patch("backend.app.services.news_service.get_news")
    def test_query_route_news_follow_up_reuses_topic(self, news_mock):
        session_id = "memory-news"
        news_mock.return_value = {
            "status": "success",
            "articles": [
                {
                    "title": "AI headline",
                    "description": "New release",
                    "source": "Example",
                    "url": "https://example.com/ai",
                    "publishedAt": "2026-04-18T00:00:00+00:00",
                }
            ],
        }

        first = self.client.post("/query", json={"query": "Show me AI news", "session_id": session_id})
        second = self.client.post("/query", json={"query": "More headlines", "session_id": session_id})

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertGreaterEqual(news_mock.call_count, 2)
        self.assertEqual(str(news_mock.call_args_list[0].args[0]).lower(), "ai")
        self.assertEqual(str(news_mock.call_args_list[1].args[0]).lower(), "ai")

    def test_name_recall_persists_across_sessions_for_same_user(self):
        self.client.post("/api/chat", json={"message": "My name is Saye", "session_id": "old-session", "user_id": "user-saye"})
        response = self.client.post("/api/chat", json={"message": "What's my name?", "session_id": "new-session", "user_id": "user-saye"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["content"], "You're Saye.")
        self.assertEqual(get_session_facts("new-session"), {})

    def test_query_route_name_recall_persists_across_sessions_for_same_user(self):
        self.client.post("/query", json={"query": "My name is Saye", "session_id": "query-old-session", "user_id": "query-user"})
        response = self.client.post("/query", json={"query": "What's my name?", "session_id": "query-new-session", "user_id": "query-user"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["summary"], "You're Saye.")

    @patch("backend.app.services.news_service.get_ai_reply")
    def test_query_route_injects_persistent_memory_into_general_ai_context(self, ai_mock):
        ai_mock.return_value = {"reply": "Hey Saye, here's something useful."}

        self.client.post("/query", json={"query": "My name is Saye", "session_id": "memory-seed", "user_id": "same-user"})
        response = self.client.post("/query", json={"query": "Tell me something useful", "session_id": "fresh-chat", "user_id": "same-user"})

        self.assertEqual(response.status_code, 200)
        self.assertIn("Saye", response.json()["summary"])
        self.assertIn("Name: Saye", str(ai_mock.call_args.kwargs.get("user_memory") or ""))

    def test_different_user_does_not_receive_other_user_memory(self):
        self.client.post("/api/chat", json={"message": "My name is Saye", "session_id": "session-a", "user_id": "user-saye"})
        response = self.client.post("/api/chat", json={"message": "What's my name?", "session_id": "session-b", "user_id": "user-other"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["content"], "I don't think you've told me your name yet.")

    def test_memory_facts_are_stored_separately_from_session_state(self):
        session_id = "memory-facts-bucket"

        self.client.post("/api/chat", json={"message": "My name is Saye", "session_id": session_id})
        self.client.post("/api/chat", json={"message": "I live in Minneapolis", "session_id": session_id})

        self.assertEqual(get_session_facts(session_id)["name"], "Saye")
        self.assertEqual(get_session_facts(session_id)["location"], "Minneapolis")
        self.assertEqual(get_long_term_facts(get_user_id("default_user"))["name"], "Saye")
        self.assertEqual(get_long_term_facts(get_user_id("default_user"))["location"], "Minneapolis")
        persisted_memory = load_user_memory(get_user_id("default_user"))
        self.assertEqual(persisted_memory["name"], "Saye")
        self.assertEqual(persisted_memory["location"], "Minneapolis")
        self.assertEqual(get_session_value(session_id, "name"), None)
        self.assertEqual(get_session_value(session_id, "location"), None)
        self.assertEqual(get_session_value(session_id, "last_weather_city"), "Minneapolis")

    def test_goals_are_saved_to_long_term_memory(self):
        session_id = "memory-goals"

        self.client.post("/api/chat", json={"message": "My goals are to launch OmniCore and improve memory", "session_id": session_id, "user_id": "user-goals"})
        response = self.client.post("/api/chat", json={"message": "What are my goals?", "session_id": "fresh-session", "user_id": "user-goals"})

        self.assertEqual(response.status_code, 200)
        self.assertIn("launch OmniCore", response.json()["content"])
        self.assertIn("improve memory", response.json()["content"])

    @patch("backend.app.services.chat_router.get_ai_reply")
    def test_open_ended_general_reply_is_personalized_and_conversational(self, ai_mock):
        ai_mock.return_value = {
            "reply": "Certainly! Octopuses have three hearts and blue blood. They're also excellent problem solvers."
        }

        self.client.post("/api/chat", json={"message": "My name is Saye", "session_id": "style-session", "user_id": "style-user"})
        response = self.client.post(
            "/api/chat",
            json={"message": "Tell me something interesting", "session_id": "style-session", "user_id": "style-user"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["content"].startswith("Hey Saye,"))
        self.assertIn("octopuses have three hearts and blue blood.", response.json()["content"].lower())
        self.assertIn("Want another one?", response.json()["content"])

    def test_clear_session_removes_history_facts_and_state(self):
        session_id = "memory-clear-session"

        self.client.post("/api/chat", json={"message": "My name is Saye", "session_id": session_id})
        self.client.post("/api/chat", json={"message": "I live in Minneapolis", "session_id": session_id})

        self.assertTrue(get_conversation(session_id))
        self.assertTrue(get_session_facts(session_id))
        self.assertEqual(get_session_value(session_id, "last_weather_city"), "Minneapolis")

        clear_session(session_id)

        self.assertEqual(get_conversation(session_id), [])
        self.assertEqual(get_session_facts(session_id), {})
        self.assertEqual(get_session_value(session_id, "last_weather_city"), None)
        self.assertEqual(get_long_term_facts(get_user_id("default_user"))["name"], "Saye")
        self.assertEqual(get_long_term_facts(get_user_id("default_user"))["location"], "Minneapolis")


if __name__ == "__main__":
    unittest.main()