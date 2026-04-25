import re
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.memory_store import reset_memory_store


class RouteResponseEnforcementTests(unittest.TestCase):
    def setUp(self):
        reset_memory_store()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        reset_memory_store()

    @patch("backend.app.services.chat_router.get_ai_reply")
    def test_api_chat_rewrites_generic_constraint_breaking_reply(self, ai_mock):
        ai_mock.return_value = {
            "reply": (
                "That's a good one, Saye. You're asking how to start a feeding program. "
                "Build partnerships and create a plan. Hire a small team and rent a kitchen."
            )
        }

        response = self.client.post(
            "/api/chat",
            json={
                "message": "I have $100, no team, no kitchen. Help me start a feeding program this week in Minneapolis.",
                "session_id": "api-route-constraints",
                "user_id": "api-route-user",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        summary = payload["content"]

        self.assertEqual(payload["type"], "general")
        self.assertNotRegex(summary.lower(), r"that's a good one|you'?re asking|build partnerships|create a plan")
        self.assertNotRegex(summary.lower(), r"hire|rent a kitchen")
        self.assertNotIn("Saye", summary)
        self.assertRegex(summary.lower(), r"\b\d+\b")
        self.assertRegex(summary.lower(), r"this week")
        self.assertRegex(summary.lower(), r"minneapolis|ready-made|meals")

    @patch("backend.app.services.news_service.get_ai_reply")
    def test_query_route_rewrites_generic_market_reply_into_specific_steps(self, ai_mock):
        ai_mock.return_value = {
            "reply": "Great question. Research the market and identify your audience."
        }

        response = self.client.post(
            "/query",
            json={
                "query": "I have a $100 budget and need to start this week. Should I sell solar chargers?",
                "session_id": "query-route-generic",
                "user_id": "query-route-user",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        summary = payload["summary"]

        self.assertIn(payload["type"], {"analysis", "general"})
        self.assertNotRegex(summary.lower(), r"great question|research the market|identify your audience")
        self.assertRegex(summary.lower(), r"\b\d+\b")
        self.assertRegex(summary.lower(), r"today|this week")
        self.assertRegex(summary.lower(), r"internal contact list|check|contact|message|scan|review")

    @patch("backend.app.services.news_service.get_ai_reply")
    def test_query_route_does_not_force_name_repetition_in_general_reply(self, ai_mock):
        ai_mock.return_value = {"reply": "Research the market and identify your audience."}

        self.client.post(
            "/query",
            json={
                "query": "My name is Saye",
                "session_id": "query-name-seed",
                "user_id": "shared-user",
            },
        )

        response = self.client.post(
            "/query",
            json={
                "query": "I have a $100 budget and need to start this week. Should I sell solar chargers?",
                "session_id": "query-name-fresh",
                "user_id": "shared-user",
            },
        )

        self.assertEqual(response.status_code, 200)
        summary = response.json()["summary"]
        self.assertNotIn("Saye", summary)

    @patch("backend.app.services.chat_router.get_ai_reply")
    def test_api_chat_fallback_stays_specific_not_vague(self, ai_mock):
        ai_mock.return_value = {"reply": "Start small. Consider your options."}

        response = self.client.post(
            "/api/chat",
            json={
                "message": "I have $100, no team, and no kitchen. Help me start a feeding program this week.",
                "session_id": "api-route-vague",
                "user_id": "api-route-user",
            },
        )

        self.assertEqual(response.status_code, 200)
        summary = response.json()["content"]
        self.assertNotRegex(summary.lower(), r"consider your options")
        self.assertRegex(summary.lower(), r"\b\d+\b")
        self.assertRegex(summary.lower(), r"this week")
        self.assertRegex(summary.lower(), r"start|use|serve|ready-made|meals")

    @patch("backend.app.services.chat_router.get_ai_reply")
    def test_api_chat_decision_query_returns_one_best_action(self, ai_mock):
        ai_mock.return_value = {
            "reply": "You could build partnerships, hire volunteers, or rent a kitchen to get started."
        }

        response = self.client.post(
            "/api/chat",
            json={
                "message": "I have $100, no team, no kitchen. What should I do this week to start a feeding program in Minneapolis?",
                "session_id": "api-route-decision",
                "user_id": "api-route-user",
            },
        )

        self.assertEqual(response.status_code, 200)
        summary = response.json()["content"]
        self.assertRegex(summary.lower(), r"10 to 15.*meals")
        self.assertRegex(summary.lower(), r"minneapolis")
        self.assertRegex(summary.lower(), r"this week")
        self.assertNotRegex(summary.lower(), r"hire volunteers|rent a kitchen|build partnerships")
        self.assertNotIn(" or ", summary.lower())
        sentences = [part for part in re.split(r"(?<=[.!?])\s+", summary) if part.strip()]
        self.assertLessEqual(len(sentences), 3)

    @patch("backend.app.services.news_service.get_ai_reply")
    def test_query_route_honest_judgment_is_direct(self, ai_mock):
        ai_mock.return_value = {
            "reply": "You could maybe consider slowing down and making a plan."
        }

        response = self.client.post(
            "/query",
            json={
                "query": "I want to start a nonprofit, a business, and make money fast. Be honest: am I doing too much? Don't be nice.",
                "session_id": "query-route-judgment",
                "user_id": "query-route-user",
            },
        )

        self.assertEqual(response.status_code, 200)
        summary = response.json()["summary"]
        self.assertRegex(summary.lower(), r"yes")
        self.assertRegex(summary.lower(), r"3 different things|1 thing")
        self.assertNotRegex(summary.lower(), r"consider|maybe|plan")

    @patch("backend.app.services.chat_router.get_ai_reply")
    def test_api_chat_weekend_prompt_stays_general_not_weather(self, ai_mock):
        ai_mock.return_value = {
            "reply": "You could build a plan and maybe consider some options."
        }

        response = self.client.post(
            "/api/chat",
            json={
                "message": "I have $80, no kitchen, no team, and I need to feed people this weekend. Don't give me ideas. Give me exactly what to do starting tomorrow.",
                "session_id": "api-route-weekend",
                "user_id": "api-route-user",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        summary = payload["content"]
        self.assertEqual(payload["type"], "general")
        self.assertRegex(summary.lower(), r"tomorrow|this weekend")
        self.assertRegex(summary.lower(), r"meals|ready-made")
        self.assertNotRegex(summary.lower(), r"plan|maybe|consider")
        self.assertNotIn(" or ", summary.lower())

    @patch("backend.app.services.news_service.get_ai_reply")
    def test_query_route_general_response_does_not_ship_generic_action_buttons(self, ai_mock):
        ai_mock.return_value = {
            "reply": "Research the market and identify your audience."
        }

        response = self.client.post(
            "/query",
            json={
                "query": "Help me start something with no money.",
                "session_id": "query-route-no-actions",
                "user_id": "query-route-user",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["data"]["actions"], [])

    @patch("backend.app.services.news_service.get_ai_reply")
    def test_query_route_blocks_loans_and_external_funding(self, ai_mock):
        ai_mock.return_value = {
            "reply": "Take out a loan, borrow money, and ask investors for funding before you start."
        }

        response = self.client.post(
            "/query",
            json={
                "query": "$50 only. Inside Army Corps only. What should I do?",
                "session_id": "query-route-no-loans",
                "user_id": "query-route-user",
            },
        )

        self.assertEqual(response.status_code, 200)
        summary = response.json()["summary"]
        self.assertNotRegex(summary.lower(), r"loan|borrow|investor|funding|credit|financing")
        self.assertRegex(summary.lower(), r"existing money|what you already have|no new money|inside army corps")

    @patch("backend.app.services.chat_router.get_ai_reply")
    def test_api_chat_rewrites_external_system_dependencies_to_internal_only(self, ai_mock):
        ai_mock.return_value = {
            "reply": "Use a platform, find a partner, hire outside help, and post on Facebook to get traction."
        }

        response = self.client.post(
            "/api/chat",
            json={
                "message": "No resources, no team, inside Army Corps only.",
                "session_id": "api-route-internal-only",
                "user_id": "api-route-user",
            },
        )

        self.assertEqual(response.status_code, 200)
        summary = response.json()["content"]
        self.assertNotRegex(summary.lower(), r"platform|partner|hire|facebook|outside|external")
        self.assertRegex(summary.lower(), r"what you already have|people you already know|people already in your unit|existing resources|on your own")

    @patch("backend.app.services.news_service.get_ai_reply")
    def test_query_route_today_prompt_does_not_drift_into_news(self, ai_mock):
        ai_mock.return_value = {
            "reply": "Coverage is led by The Times of India and The Times of India."
        }

        response = self.client.post(
            "/query",
            json={
                "query": "I'm in a bad spot. I need something that works NOW, not later. What do I do today?",
                "session_id": "query-route-no-news-drift",
                "user_id": "query-route-user",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        summary = payload["summary"]
        self.assertEqual(payload["type"], "analysis")
        self.assertNotIn("Coverage is led by", summary)
        self.assertRegex(summary.lower(), r"today")

    @patch("backend.app.services.news_service.get_ai_reply")
    def test_query_route_enforces_exact_money_and_time_literals(self, ai_mock):
        ai_mock.return_value = {
            "reply": "Start small and move fast."
        }

        response = self.client.post(
            "/query",
            json={
                "query": "I have $40, no help, and 1 day. I need to get something working by tomorrow afternoon. Tell me exactly what to do. No ideas.",
                "session_id": "query-route-exact-constraints",
                "user_id": "query-route-user",
            },
        )

        self.assertEqual(response.status_code, 200)
        summary = response.json()["summary"]
        self.assertIn("$40", summary)
        self.assertRegex(summary.lower(), r"1 day")
        self.assertRegex(summary.lower(), r"tomorrow afternoon")


if __name__ == "__main__":
    unittest.main()