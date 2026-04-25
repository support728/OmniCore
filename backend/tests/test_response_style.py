import re
import unittest

from backend.app.services.response_style import (
    build_constraint_context,
    format_conversational_response,
    run_enforced_pipeline,
    style_response,
)
from backend.app.services.youtube_service import summarize_youtube_results


class ResponseStyleTests(unittest.TestCase):
    def test_format_conversational_response_strips_numbered_sections(self):
        text = "1. First section\n2. Second section\n3. Third section"

        formatted = format_conversational_response(text)

        self.assertNotIn("1.", formatted)
        self.assertNotIn("2.", formatted)
        self.assertIn("First section", formatted)
        self.assertIn("Second section", formatted)

    def test_format_conversational_response_splits_long_paragraph(self):
        text = (
            "This answer starts directly. It keeps going with more context so the user has enough detail. "
            "It adds another sentence to explain tradeoffs clearly. It finishes with a final point that would make "
            "the paragraph too long for chat if it stayed in one block."
        )

        formatted = format_conversational_response(text)

        self.assertIn("\n\n", formatted)

    def test_format_conversational_response_removes_filler_phrases(self):
        text = (
            "I'm here to help with that. I can help with planning this change. "
            "The quickest fix is to update the router and keep the response compact."
        )

        formatted = format_conversational_response(text)

        self.assertNotIn("I'm here to help", formatted)
        self.assertNotIn("I can help with", formatted)
        self.assertIn("The quickest fix is to update the router", formatted)

    def test_format_conversational_response_dedupes_repeated_sentences(self):
        text = (
            "The fastest path is to update the backend prompt. "
            "The fastest path is to update the backend prompt. "
            "Then tighten the formatter."
        )

        formatted = format_conversational_response(text)

        self.assertEqual(formatted.count("The fastest path is to update the backend prompt."), 1)
        self.assertIn("Then tighten the formatter.", formatted)

    def test_summarize_youtube_results_uses_conversational_tone(self):
        summary = summarize_youtube_results(
            "AI agents",
            [
                {"channel": "OpenAI", "title": "Agents 101"},
                {"channel": "Anthropic", "title": "Agent workflows"},
            ],
        )

        self.assertIn('The top YouTube picks for "AI agents" are below.', summary)
        self.assertIn("OpenAI", summary)
        self.assertNotIn("1.", summary)

    def test_style_response_rewrites_generic_phrases_into_specific_actions(self):
        result = style_response(
            "Research the market and identify your audience.",
            query="I have a $100 budget and I need to start this week.",
            allow_personalization=False,
        )

        self.assertIn("5", result)
        self.assertRegex(result.lower(), r"today|this week")
        self.assertRegex(result.lower(), r"check|message|write")
        self.assertNotIn("Research the market", result)

    def test_style_response_blocks_constraint_violations(self):
        result = style_response(
            "Hire a small team and rent a kitchen.",
            query="I have $100, no team, no kitchen. Help me start a feeding program this week.",
            allow_personalization=False,
        )

        self.assertNotRegex(result.lower(), r"hire|rent a kitchen")
        self.assertRegex(result.lower(), r"10 to 15 meals|ready-made")
        self.assertRegex(result.lower(), r"this week")

    def test_style_response_forces_specificity_when_reply_is_vague(self):
        result = style_response(
            "Start small and build support.",
            query="I have $100, no team, and no kitchen. Help me start a feeding program.",
            allow_personalization=False,
        )

        self.assertRegex(result.lower(), r"\b\d+\b")
        self.assertRegex(result.lower(), r"this week")
        self.assertRegex(result.lower(), r"start|use|write|run")

    def test_build_constraint_context_extracts_all_priority_constraints(self):
        context = build_constraint_context(
            "I have $100 budget, no team, no kitchen, and I need to start this week in Minneapolis."
        )

        self.assertEqual(context, "funding: internal_only | loans not allowed | $100 budget | $100 | this week | this week | no team | no kitchen | Minneapolis")

    def test_style_response_default_brevity_caps_at_four_sentences(self):
        result = style_response(
            "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five.",
            query="What should I do next?",
            allow_personalization=False,
        )

        sentences = [part for part in re.split(r"(?<=[.!?])\s+", result) if part.strip()]
        self.assertLessEqual(len(sentences), 4)

    def test_style_response_rewrites_create_a_plan_into_specific_steps(self):
        result = style_response(
            "Create a plan for the launch.",
            query="I have $100 and need to start this week.",
            allow_personalization=False,
        )

        self.assertNotIn("Create a plan", result)
        self.assertRegex(result.lower(), r"\b\d+\b")
        self.assertRegex(result.lower(), r"today|this week")
        self.assertRegex(result.lower(), r"write|pick|test|message|check")

    def test_style_response_fallback_still_produces_actionable_output(self):
        result = style_response(
            "Important to consider your options.",
            query="I have $100, no team, no kitchen. Help me start a feeding program this week in Minneapolis.",
            allow_personalization=False,
        )

        self.assertNotRegex(result.lower(), r"important to consider")
        self.assertRegex(result.lower(), r"\b\d+\b")
        self.assertRegex(result.lower(), r"this week")
        self.assertRegex(result.lower(), r"minneapolis|local|ready-made")

    def test_style_response_never_returns_generic_constraint_violating_feeding_reply(self):
        result = style_response(
            "Build partnerships, hire volunteers, and rent a kitchen.",
            query="I have $100, no team, no kitchen. Help me start a feeding program.",
            allow_personalization=False,
        )

        self.assertNotRegex(result.lower(), r"build partnerships|hire volunteers|rent a kitchen")
        self.assertRegex(result.lower(), r"\b\d+\b")
        self.assertRegex(result.lower(), r"this week")
        self.assertRegex(result.lower(), r"start|use|serve|facility|ready-made")

    def test_style_response_decision_layer_picks_one_best_action(self):
        result = style_response(
            "You could build partnerships, rent a kitchen, or try a pilot meal run.",
            query="I have $100, no team, no kitchen. What should I do this week to start a feeding program in Minneapolis?",
            allow_personalization=False,
        )

        self.assertRegex(result.lower(), r"10 to 15.*meals")
        self.assertRegex(result.lower(), r"minneapolis")
        self.assertRegex(result.lower(), r"this week")
        self.assertNotRegex(result.lower(), r"rent a kitchen|build partnerships")
        self.assertNotRegex(result.lower(), r"\byou could\b|\bit depends\b|\bone option is\b")
        self.assertNotIn(" or ", result.lower())
        sentences = [part for part in re.split(r"(?<=[.!?])\s+", result) if part.strip()]
        self.assertLessEqual(len(sentences), 3)

    def test_style_response_honest_judgment_is_direct_and_not_soft(self):
        result = style_response(
            "You may want to consider narrowing your focus.",
            query="I want to start a nonprofit, a business, and make money fast. Be honest: am I doing too much? Don't be nice.",
            allow_personalization=False,
        )

        self.assertRegex(result.lower(), r"yes")
        self.assertRegex(result.lower(), r"3 different things|1 thing")
        self.assertNotRegex(result.lower(), r"consider|maybe|you could")
        sentences = [part for part in re.split(r"(?<=[.!?])\s+", result) if part.strip()]
        self.assertLessEqual(len(sentences), 3)

    def test_style_response_fallback_uses_strict_template(self):
        result = style_response(
            "You could explore some options and maybe build a plan.",
            query="I only have tomorrow and $50. What exactly do I do between 9am-3pm?",
            allow_personalization=False,
        )

        self.assertNotRegex(result.lower(), r"you could|maybe|consider|it depends|one option is")
        self.assertRegex(result, r"^[A-Z]")
        self.assertIn("$50", result)
        self.assertRegex(result.lower(), r"tomorrow|9am-3pm")

    def test_style_response_replaces_weak_first_sentence_with_direct_step(self):
        result = style_response(
            "Identify what you're passionate about or skilled at. Check 5 competing offers today and write down their price, promise, and who they target.",
            query="Give me steps to start something. Keep it short.",
            allow_personalization=False,
        )

        self.assertNotIn("Identify what you're passionate", result)
        self.assertRegex(result.lower(), r"start with|check 5|pick one small test|run one small test")

    def test_style_response_feeding_weekend_prompt_starts_tomorrow(self):
        result = style_response(
            "Build partnerships and create a plan.",
            query="I have $80, no kitchen, no team, and I need to feed people this weekend. Don't give me ideas. Give me exactly what to do starting tomorrow.",
            allow_personalization=False,
        )

        self.assertRegex(result.lower(), r"tomorrow")
        self.assertRegex(result.lower(), r"this weekend")
        self.assertRegex(result.lower(), r"10 to 15 meals|ready-made")
        self.assertNotRegex(result.lower(), r"want a few more")
        self.assertNotIn(" or ", result.lower())

    def test_style_response_never_suggests_loans_or_external_funding(self):
        result = style_response(
            "Take out a loan, ask an investor, and raise money before you start.",
            query="I only have $50 and need to do this inside Army Corps only.",
            allow_personalization=False,
        )

        self.assertNotRegex(result.lower(), r"loan|investor|raise money|funding|borrow|credit|financing")
        self.assertRegex(result.lower(), r"existing money|what you already have|no new money|inside army corps")

    def test_style_response_rewrites_external_execution_to_internal_only(self):
        result = style_response(
            "Use a platform, find a partner, and hire outside help.",
            query="I have no team, no resources, and this must stay inside Army Corps only.",
            allow_personalization=False,
        )

        self.assertNotRegex(result.lower(), r"platform|partner|hire|outside|external|marketplace")
        self.assertRegex(result.lower(), r"internal contact list|inside army corps|available person already in your unit|people already in your unit|existing resources")

    def test_style_response_blocks_one_option_is_and_it_depends_language(self):
        result = style_response(
            "One option is to wait. It depends on what happens next.",
            query="I have $40 and tomorrow afternoon. Just decide for me.",
            allow_personalization=False,
        )

        self.assertNotRegex(result.lower(), r"one option is|it depends|you could|consider")
        self.assertIn("$40", result)
        self.assertRegex(result.lower(), r"tomorrow afternoon")

    def test_style_response_varies_sentence_shape_across_different_prompts(self):
        first = style_response(
            "Start small and move fast.",
            query="I have $40, 3 hours, and need something working by tomorrow afternoon.",
            allow_personalization=False,
        )
        second = style_response(
            "Start small and move fast.",
            query="I have $20 and tomorrow morning between 9am-12pm. Give me one next step.",
            allow_personalization=False,
        )

        self.assertNotEqual(first.split(".")[0].strip(), second.split(".")[0].strip())

    def test_style_response_requires_exact_money_and_duration_literals(self):
        result = style_response(
            "Start small and move fast.",
            query="I have $40, 3 hours, and need something working by tomorrow afternoon.",
            allow_personalization=False,
        )

        self.assertIn("$40", result)
        self.assertRegex(result.lower(), r"3 hours")
        self.assertRegex(result.lower(), r"tomorrow afternoon")

    def test_style_response_changes_when_prompt_changes_even_under_fallback(self):
        first = style_response(
            "Consider your options.",
            query="I have $20 and tomorrow morning between 9am-12pm.",
            allow_personalization=False,
        )
        second = style_response(
            "Consider your options.",
            query="I have $10 and 3 hours today.",
            allow_personalization=False,
        )

        self.assertNotEqual(first, second)

    def test_run_enforced_pipeline_blocks_unknown_route(self):
        with self.assertRaises(ValueError):
            run_enforced_pipeline("hello", route_name="raw", intent="general", query="hello")

    def test_style_response_flags_unrelated_news_like_drift(self):
        result = style_response(
            "Coverage is led by The Times of India and The Times of India.",
            query="I'm in a bad spot. I need something that works now, not later. What do I do today?",
            allow_personalization=False,
        )

        self.assertNotIn("Coverage is led by", result)
        self.assertRegex(result.lower(), r"today")


if __name__ == "__main__":
    unittest.main()