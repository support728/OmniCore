def format_weather_reply(weather):
    city = weather.get("city", "Unknown")
    desc = weather.get("description", "unavailable")
    temp = weather.get("temperature")

    # Validate temperature
    if temp is None:
        return f"Weather in {city}: {desc}, unavailable"

    try:
        temp = float(temp)
    except (TypeError, ValueError):
        return f"Weather in {city}: {desc}, unavailable"

    # Reject impossible temperatures
    if temp < -100 or temp > 100:
        return f"Weather in {city}: {desc}, unavailable"

    return f"Weather in {city}: {desc}, {round(temp, 1)}°C"


def test_weather_formatter():
    weather = {
        "type": "weather",
        "city": "London",
        "description": "scattered clouds",
        "temperature": 16.4,
    }
    assert format_weather_reply(weather) == "Weather in London: scattered clouds, 16.4°C"
def format_weather_insight(weather: dict[str, object]) -> str:
    request_type = str(weather.get("request_type") or "current")
    if request_type == "tomorrow":
        forecast_label = weather.get("forecast_label") or "Tomorrow"
        return f"{forecast_label} is based on the next forecast window rather than current conditions."

    if request_type in {"weekend", "forecast"}:
        forecast_days = weather.get("forecast_days") if isinstance(weather.get("forecast_days"), list) else []
        if not forecast_days:
            return "Forecast details are limited right now."
        labels = ", ".join(str(day.get("label") or "Forecast") for day in forecast_days)
        return f"This outlook is built from forecast periods for {labels}."

    feels_like = _format_metric(weather.get("feels_like"), "°F")
    humidity = _format_metric(weather.get("humidity"), "%")
    insight_parts = []
    if feels_like:
        insight_parts.append(f"Feels like {feels_like}")
    if humidity:
        insight_parts.append(f"with humidity around {humidity}")
    return " ".join(insight_parts) + "." if insight_parts else "Current-condition detail is limited right now."

import hashlib
import re
from difflib import SequenceMatcher



CONVERSATIONAL_SYSTEM_PROMPT = (
    "You are a sharp, practical assistant. "
    "Write like a real person speaking naturally, not like a textbook, worksheet, or generic AI assistant.\n\n"
    "Rules:\n"
    "- Default to 2 to 5 short sentences.\n"
    "- Keep responses short unless the user asks for more.\n"
    "- Expand only when the user asks for more.\n"
    "- Break longer answers into small chunks instead of one big block.\n"
    "- Avoid long structured lists unless necessary.\n"
    "- Do not use numbered sections, bold markdown, or report-style formatting unless the user asks for it.\n"
    "- Do not sound like a helpful school worksheet, catalog, or report.\n"
    "- Do not restate the user's question unless it is necessary to clarify a decision.\n"
    "- Do not repeat the user's name unless it is truly useful in the moment.\n"
    "- Do not include generic assistant phrases like 'I aim to assist', 'I'm here to help', or 'I can help with'.\n"
    "- Do not give generic advice like 'build partnerships' unless you immediately make it concrete with a real example.\n"
    "- Do not start with phrases like 'Certainly', 'In summary', or similar stock assistant wording.\n"
    "- Do not open with praise like 'That's a good one', 'Great question', or similar filler.\n"
    "- Start directly with the answer.\n"
    "- Prefer short paragraphs of 1 or 2 sentences each.\n"
    "- Keep responses concise and specific unless the user asks for more detail.\n"
    "- Expand gradually when the user asks for more detail, but still keep formatting light.\n"
    "- Give direct, specific, real-world answers.\n"
    "- Avoid generic advice. If the answer could apply to almost anyone, rewrite it to be more specific.\n"
    "- Answer the user's real goal first.\n"
    "- Respect constraints first: money, time, location, skill, team size, tools, or setup limits.\n"
    "- Focus on actionable steps, clear reasoning, and what would work in real life.\n"
    "- Respect the user's explicit constraints like money, time, skill, or team size.\n"
    "- Prefer clarity over politeness padding.\n"
    "- Avoid repeating the same idea in different words.\n"
    "- Each sentence should add new information.\n"
    "- Use spacing instead of heavy formatting.\n"
    "- Break complex answers into small, easy-to-read chunks.\n"
    "- Sound warm, smooth, direct, human, and not robotic or overly formal.\n"
    "- Occasionally ask one relevant follow-up question when it helps the conversation move forward.\n\n"
    "Before answering, silently follow this sequence:\n"
    "1. Figure out what the user is actually trying to do.\n"
    "2. Figure out which constraints matter most.\n"
    "3. Decide what would work in real life.\n"
    "4. Give the answer plainly.\n\n"
    "Do that reasoning internally. Return only the final answer.\n\n"
    "When possible, start with a direct answer, then expand briefly in a natural chat tone."

)


SUMMARY_SYSTEM_PROMPT = (
    "You are OmniCore, a conversational assistant. "
    "Summarize the provided results in a natural chat style.\n\n"
    "Rules:\n"
    "- Default to 2 to 4 short sentences unless the user asked for detail.\n"
    "- Start with the direct answer or main takeaway.\n"
    "- Do not restate the user query unless it is needed for clarity.\n"
    "- Avoid numbered sections, bold markdown, academic tone, and report formatting.\n"
    "- Do not sound like a report, product sheet, or worksheet.\n"
    "- Avoid generic assistant filler or politeness padding.\n"
    "- Avoid generic advice unless it is made concrete right away.\n"
    "- Prefer short paragraphs with plain language.\n"
    "- Each sentence should add new information.\n"
    "- Do not repeat raw links.\n"
    "- For news, keep it to 2 or 3 short sentences max.\n"
    "- For news, do not start with phrases like 'Today, major news includes'. Start more naturally, such as 'Big headline today', 'Here's what's going on', or 'Quick update'.\n"
    "- For news, explain the main development and why it matters.\n"
    "- For weather, mention current conditions and what to expect next.\n"
    "- For web or video search, explain the best next direction in a conversational way."
)


FILLER_PATTERNS = [
    r"\bCertainly[,.! ]*",
    r"\bIn summary[,: ]*",
    r"\bThat's a good one[,.! ]*",
    r"\bGreat question[,.! ]*",
    r"\bGood question[,.! ]*",
    r"\bInteresting question[,.! ]*",
    r"\bAbsolutely[,.! ]*",
    r"\bI aim to assist\b[^.?!]*[.?!]?",
    r"\bI am here to help\b[^.?!]*[.?!]?",
    r"\bI'm here to help\b[^.?!]*[.?!]?",
    r"\bI can help with\b[^.?!]*[.?!]?",
    r"\bI can assist with\b[^.?!]*[.?!]?",
    r"\bI can certainly help with that\b[^.?!]*[.?!]?",
    r"\bMy goal is to\b[^.?!]*[.?!]?",
    r"\bI hope that helps\b[^.?!]*[.?!]?",
    r"\bfor a smooth and enjoyable experience\b[^.?!]*[.?!]?",
]

FEATURE_SUGGESTION_PATTERNS = [
    re.compile(r"\bI can also add\b[^.?!]*[.?!]?", re.IGNORECASE),
    re.compile(r"\bIf you want, I can\b[^.?!]*[.?!]?", re.IGNORECASE),
    re.compile(r"\bWe could implement\b[^.?!]*[.?!]?", re.IGNORECASE),
    re.compile(r"\bI could add\b[^.?!]*[.?!]?", re.IGNORECASE),
]

QUESTION_RESTATEMENT_PATTERNS = [
    re.compile(r"^(?:you(?:'re| are) asking (?:about|whether|how|what|if)\b[^.?!]*[.?!]\s*)", re.IGNORECASE),
    re.compile(r"^(?:you(?:'re| are) looking (?:to|for)\b[^.?!]*[.?!]\s*)", re.IGNORECASE),
    re.compile(r"^(?:if you(?:'re| are) trying to\b[^.?!]*[.?!]\s*)", re.IGNORECASE),
    re.compile(r"^(?:you want to\b[^.?!]*[.?!]\s*)", re.IGNORECASE),
    re.compile(r"^(?:the goal here is to\b[^.?!]*[.?!]\s*)", re.IGNORECASE),
]

GENERIC_ADVICE_RULES = [
    (
        re.compile(r"\bbuild partnerships\b", re.IGNORECASE),
        "Pick 2 relevant local groups and contact them directly this week instead of waiting for broad partnerships.",
    ),
    (
        re.compile(r"\b(?:define|defining) your mission\b", re.IGNORECASE),
        "Write one plain sentence tonight that says who you help, what problem you solve, and why it matters.",
    ),
    (
        re.compile(r"\b(?:create|creating) a strategy\b", re.IGNORECASE),
        "Pick one goal for this week, one action to test, and one number you will track.",
    ),
    (
        re.compile(r"\b(?:develop|developing) a plan\b", re.IGNORECASE),
        "Pick one goal for this week, one action to test, and one number you will track.",
    ),
    (
        re.compile(r"\b(?:gather|gathering) support\b", re.IGNORECASE),
        "Ask 3 specific people or groups for a concrete yes or no this week.",
    ),
    (
        re.compile(r"\b(?:identify|identifying) opportunities\b", re.IGNORECASE),
        "List 5 real leads, rank them, and contact the top 2 first.",
    ),
    (
        re.compile(r"\b(?:research|researching) the market\b", re.IGNORECASE),
        "Check 5 competing offers today and write down their price, promise, and who they target.",
    ),
    (
        re.compile(r"\b(?:identify|identifying) your audience\b", re.IGNORECASE),
        "Pick one narrow group you can reach this week and message 5 of them directly.",
    ),
    (
        re.compile(r"\bleverage social media\b", re.IGNORECASE),
        "Post one clear offer where your target users already are and ask for one concrete response.",
    ),
    (
        re.compile(r"\bnetwork with the right people\b", re.IGNORECASE),
        "Make a shortlist of 5 people already in this space and send each one a direct question.",
    ),
    (
        re.compile(r"\bfocus on marketing\b", re.IGNORECASE),
        "Choose one channel, write one message, and send it to real prospects this week.",
    ),
    (
        re.compile(r"\bdo market research\b", re.IGNORECASE),
        "Talk to 5 likely users and ask what they do now, what it costs them, and what would make them switch.",
    ),
]

CONCRETE_ACTION_PATTERNS = [
    re.compile(r"\b\d+\b"),
    re.compile(r"\b(today|tomorrow|tonight|this week|this month|by (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b", re.IGNORECASE),
    re.compile(r"\b(call|email|text|dm|message|visit|ask|join|post|ship|test|contact|list|write|pick|book|compare|send|talk to|reach out to)\b", re.IGNORECASE),
]

ABSTRACT_ADVICE_PATTERNS = [
    re.compile(r"\b(should|could|can)\s+(?:just\s+)?(?:start|begin)\s+by\s+(defining|researching|creating|developing|identifying)\b", re.IGNORECASE),
    re.compile(r"\bimportant to\b", re.IGNORECASE),
    re.compile(r"\bconsider\b[^.?!]*$", re.IGNORECASE),
]

BUDGET_PATTERNS = [
    re.compile(r"\$\s?(\d+)", re.IGNORECASE),
    re.compile(r"under\s+\$\s?(\d+)", re.IGNORECASE),
    re.compile(r"budget\s+of\s+\$\s?(\d+)", re.IGNORECASE),
    re.compile(r"(no budget|low budget|tight budget|cheap|affordable|almost no money)", re.IGNORECASE),
]

TIME_PATTERNS = [
    re.compile(r"\b(this week|this weekend|today|tomorrow|tonight)\b", re.IGNORECASE),
    re.compile(r"\bby\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", re.IGNORECASE),
    re.compile(r"\b(quickly|fast|soon|right away|immediately)\b", re.IGNORECASE),
]

RESOURCE_PATTERNS = [
    re.compile(r"\bno team\b", re.IGNORECASE),
    re.compile(r"\bno help\b", re.IGNORECASE),
    re.compile(r"\bsolo\b", re.IGNORECASE),
    re.compile(r"\balone\b", re.IGNORECASE),
    re.compile(r"\bno connections\b", re.IGNORECASE),
    re.compile(r"\bno resources\b", re.IGNORECASE),
    re.compile(r"\bno kitchen\b", re.IGNORECASE),
    re.compile(r"\bno car\b", re.IGNORECASE),
    re.compile(r"\bno tools\b", re.IGNORECASE),
    re.compile(r"\bno money\b", re.IGNORECASE),
    re.compile(r"\bno time\b", re.IGNORECASE),
    re.compile(r"\bno staff\b", re.IGNORECASE),
]

LOCATION_HINT_PATTERNS = [
    re.compile(r"\b(?:in|near|around)\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,2})\b"),
]

CONSTRAINT_VIOLATION_PATTERNS = {
    "budget": [
        re.compile(r"\bhire\b", re.IGNORECASE),
        re.compile(r"\bbuild an app\b", re.IGNORECASE),
        re.compile(r"\bbuy equipment\b", re.IGNORECASE),
        re.compile(r"\brent\b", re.IGNORECASE),
        re.compile(r"\bpaid ads?\b", re.IGNORECASE),
    ],
    "no_team": [
        re.compile(r"\bbuild a team\b", re.IGNORECASE),
        re.compile(r"\bdelegate\b", re.IGNORECASE),
        re.compile(r"\bassign\b", re.IGNORECASE),
        re.compile(r"\brecruit\b", re.IGNORECASE),
    ],
    "no_kitchen": [
        re.compile(r"\bcook\b", re.IGNORECASE),
        re.compile(r"\bmeal prep\b", re.IGNORECASE),
        re.compile(r"\buse your kitchen\b", re.IGNORECASE),
    ],
}

DEFAULT_CONSTRAINT_STEPS = {
    "no_team": "Run the first version on your own this week instead of waiting on anyone else.",
    "no_kitchen": "Use ready-made food from one pickup point you already control for the first 10 to 15 meals this week instead of cooking yourself.",
}

EXTERNAL_FUNDING_PATTERNS = [
    re.compile(r"\bloan(?:s)?\b", re.IGNORECASE),
    re.compile(r"\bborrow(?:ing|ed)?\b", re.IGNORECASE),
    re.compile(r"\bcredit\b", re.IGNORECASE),
    re.compile(r"\bfinanc(?:e|ing)\b", re.IGNORECASE),
    re.compile(r"\binvestor(?:s)?\b", re.IGNORECASE),
    re.compile(r"\braise money\b", re.IGNORECASE),
    re.compile(r"\bfunding\b", re.IGNORECASE),
    re.compile(r"\bgrant(?:s)?\b", re.IGNORECASE),
]

EXTERNAL_DEPENDENCY_PATTERNS = [
    re.compile(r"\bpartner(?:s|ship|ships)?\b", re.IGNORECASE),
    re.compile(r"\boutside partner(?:s)?\b", re.IGNORECASE),
    re.compile(r"\bthird[- ]party\b", re.IGNORECASE),
    re.compile(r"\bplatform(?:s)?\b", re.IGNORECASE),
    re.compile(r"\bmarketplace(?:s)?\b", re.IGNORECASE),
    re.compile(r"\bamazon\b", re.IGNORECASE),
    re.compile(r"\betsy\b", re.IGNORECASE),
    re.compile(r"\btiktok(?: shop)?\b", re.IGNORECASE),
    re.compile(r"\bfacebook\b", re.IGNORECASE),
    re.compile(r"\binstagram\b", re.IGNORECASE),
    re.compile(r"\breddit\b", re.IGNORECASE),
    re.compile(r"\bdiscord\b", re.IGNORECASE),
    re.compile(r"\bhire\b", re.IGNORECASE),
    re.compile(r"\brecruit\b", re.IGNORECASE),
    re.compile(r"\bvendor(?:s)?\b", re.IGNORECASE),
    re.compile(r"\bcontractor(?:s)?\b", re.IGNORECASE),
    re.compile(r"\bexternal\b", re.IGNORECASE),
]

DETAIL_REQUEST_TERMS = (
    "in detail",
    "details",
    "more detail",
    "more details",
    "tell me more",
    "go deeper",
    "go into more detail",
    "expand",
    "explain",
    "why",
    "how",
    "break it down",
    "step by step",
)

OPEN_ENDED_PROMPTS = (
    "tell me something interesting",
    "tell me something cool",
    "tell me something fun",
    "tell me more",
    "give me an idea",
    "give me ideas",
    "suggest",
    "recommend",
)

DECISION_QUERY_PATTERNS = (
    "what should i do",
    "what should i focus on",
    "what do i do next",
    "what should i start with",
    "which should i do",
    "best next step",
    "one next step",
    "pick one",
    "just decide",
    "just decide for me",
    "don't give me ideas",
    "dont give me ideas",
    "no ideas",
    "what should i actually do",
    "tell me exactly what to do",
    "give me exactly what to do",
    "am i doing too much",
)

GENERIC_FAILURE_PATTERNS = [
    re.compile(r"\bconsider\b", re.IGNORECASE),
    re.compile(r"\byou could\b", re.IGNORECASE),
    re.compile(r"\bone option is\b", re.IGNORECASE),
    re.compile(r"\banother option is\b", re.IGNORECASE),
    re.compile(r"\bit depends\b", re.IGNORECASE),
    re.compile(r"\bthere are a few ways\b", re.IGNORECASE),
    re.compile(r"\byou may want to\b", re.IGNORECASE),
    re.compile(r"\bleverage\b", re.IGNORECASE),
    re.compile(r"\bexplore\b", re.IGNORECASE),
    re.compile(r"\bbuild a plan\b", re.IGNORECASE),
    re.compile(r"\bdo research\b", re.IGNORECASE),
    re.compile(r"\bdevelop a strategy\b", re.IGNORECASE),
    re.compile(r"\bcreate a plan\b", re.IGNORECASE),
    re.compile(r"\bmaybe\b", re.IGNORECASE),
]

TIME_WINDOW_PATTERNS = [
    re.compile(r"\b(\d{1,2}(?::\d{2})?\s?(?:am|pm)\s*[-–]\s*\d{1,2}(?::\d{2})?\s?(?:am|pm))\b", re.IGNORECASE),
]

TIMEFRAME_LITERAL_PATTERNS = [
    re.compile(r"\b(tomorrow morning|tomorrow afternoon|tomorrow evening|today|tomorrow|tonight|this week|this weekend)\b", re.IGNORECASE),
    re.compile(r"\bby\s+(tomorrow morning|tomorrow afternoon|tomorrow evening|today|tomorrow|tonight|this week|this weekend)\b", re.IGNORECASE),
]

DURATION_PATTERNS = [
    re.compile(r"\b(\d+\s+(?:hour|hours|day|days))\b", re.IGNORECASE),
]

TONE_TIGHTEN_REPLACEMENTS = [
    (r"\buse that first run to learn what people actually need\b", "see what people actually need"),
    (r"\buse the result to decide whether to keep going, change direction, or stop\b", "then decide whether it is worth continuing"),
    (r"\bwithout waiting on anyone else\b", "on your own"),
    (r"\bbefore spending more\b", "before you spend more"),
]

MAX_REWRITE_ATTEMPTS = 2
ENFORCED_PIPELINE_ROUTES = {"query", "api_chat", "ui", "weather_api"}
HARD_FAILURE_TYPES = {
    "constraint_violation",
    "external_funding",
    "external_dependency",
    "constraint_binding",
    "domain_mismatch",
    "drift",
    "multiple_options",
}

FALLBACK_TEMPLATE_POOL = (
    "{action}. Use {resource}. Finish by {time_hint}. Start with {quantity}.",
    "Pick this move: {action}. Use {resource}. Get it done by {time_hint}. Start with {quantity}.",
    "Here is the move: {action}. Work from {resource}. Finish by {time_hint}. Start with {quantity}.",
    "Go with this: {action}. Use {resource}. Close it by {time_hint}. Start with {quantity}.",
    "Keep it to this: {action}. Work from {resource}. Wrap it by {time_hint}. Start with {quantity}.",
    "Make this the whole play: {action}. Use {resource}. Finish by {time_hint}. Start with {quantity}.",
)

MULTI_OPTION_DECISION_PATTERNS = [
    re.compile(r"\bone option is\b", re.IGNORECASE),
    re.compile(r"\banother option is\b", re.IGNORECASE),
    re.compile(r"\bit depends\b", re.IGNORECASE),
    re.compile(r"\beither\b", re.IGNORECASE),
    re.compile(r"\b(?:you could|you can)\b", re.IGNORECASE),
    re.compile(r",\s*or\s+", re.IGNORECASE),
]

DRIFT_PATTERNS = [
    re.compile(r"\bcoverage is led by\b", re.IGNORECASE),
    re.compile(r"\bheadline(?:s)?\b", re.IGNORECASE),
    re.compile(r"\bforecast\b", re.IGNORECASE),
    re.compile(r"\btemperature\b", re.IGNORECASE),
    re.compile(r"\bhumidity\b", re.IGNORECASE),
    re.compile(r"\btimes of india\b", re.IGNORECASE),
    re.compile(r"\bweather\b", re.IGNORECASE),
]

CONCRETE_CHANNEL_OR_LOCATION_PATTERNS = [
    re.compile(r"\b(email|dm|sms|text|phone|call|people you already know|current setup|your own setup|internal contact list|unit|office|facility|mess hall|supply room|local|minneapolis)\b", re.IGNORECASE),
]

FINAL_REPLY_MARKERS = (
    "final answer:",
    "final reply:",
    "assistant reply:",
    "user-facing reply:",
    "reply:",
)

META_LINE_PATTERNS = [
    re.compile(r"^\s*(?:task|goal|requirements|validation|implementation hint|implementation details?|file changes?|debug output|evaluation text|transformation logs?|summary of what was changed)\b", re.IGNORECASE),
    re.compile(r"^\s*(?:tests?|validation notes?|examples?)\b", re.IGNORECASE),
    re.compile(r"\bcurrent behavior is aligned\b", re.IGNORECASE),
    re.compile(r"\b(?:i|we)\s+(?:changed|updated|implemented|patched|validated|tested|fixed)\b", re.IGNORECASE),
    re.compile(r"\b(?:backend|frontend|system|router|sanitizer|filter)\b.*\b(?:behavior|details|works|changed|updated|implemented|validation)\b", re.IGNORECASE),
]

MEMORY_REPLACEMENTS = [
    (r"\bYour name is\s+([^.?!]+)[.?!]", r"You're \1."),
    (r"\bI don't know your name yet\.", "I don't think you've told me your name yet."),
    (r"\bYou live in\s+([^.?!]+)[.?!]", r"You're in \1."),
    (r"\bI don't know where you live yet\.", "I don't think you've told me where you're based yet."),
    (r"\bYou like\s+([^.?!]+)[.?!]", r"You like \1."),
    (r"\bYour goals are\s+([^.?!]+)[.?!]", r"Your goals are \1."),
    (r"\bFrom what you've told me,\s*", ""),
    (r"\bI remember that\s+", ""),
    (r"\bYou previously told me\s+", ""),
    (r"\bI know that\s+", ""),
]


def format_conversational_response(text: str) -> str:
    cleaned = (text or "").replace("\r\n", "\n").strip()
    if not cleaned:
        return ""

    cleaned = re.sub(r"^\s*#{1,6}\s+", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^\s*\d+[.)]\s+", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^\s*[-*+]\s+", "", cleaned, flags=re.MULTILINE)
    cleaned = _strip_report_labels(cleaned)
    cleaned = _remove_filler(cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", cleaned) if part.strip()]
    normalized_paragraphs: list[str] = []

    for paragraph in paragraphs:
        normalized_paragraphs.extend(_split_paragraph(paragraph))

    return _dedupe_sentences("\n\n".join(normalized_paragraphs).strip())


def style_response(
    text: str,
    *,
    intent: str = "general",
    query: str = "",
    user_name: str | None = None,
    allow_personalization: bool = False,
    allow_follow_up: bool = True,
) -> str:
    strict_general_enforcement = _needs_strict_general_enforcement(query, intent)
    constraints = _extract_constraints(query) if strict_general_enforcement else {}
    styled = format_conversational_response(text)
    if not styled:
        return ""

    styled = _remove_question_restatement(styled)
    styled = _remove_feature_suggestions(styled)
    styled = _apply_generic_advice_gate(styled)
    styled = _normalize_memory_phrases(styled)
    styled = _remove_leading_name_stub(styled)
    styled = _normalize_sentence_start(styled)
    styled = _normalize_news_opening(styled, intent)
    styled = _maybe_personalize(styled, query, user_name, allow_personalization)
    if strict_general_enforcement:
        styled = _apply_constraint_override(styled, constraints)
        styled = _enforce_response_structure(styled, query, intent, constraints)
        styled = _apply_decision_layer(styled, query, intent, constraints)
        styled = _run_rewrite_loop(styled, query, intent, constraints)
    styled = _remove_similar_sentences(styled)
    styled = _final_tone_humanizer(styled, query, intent)
    if allow_follow_up:
        styled = _maybe_add_follow_up(styled, intent, query)
    styled = _limit_to_default_length(styled, query)
    return styled.strip()


def run_enforced_pipeline(
    text: str,
    *,
    route_name: str,
    intent: str = "general",
    query: str = "",
    user_name: str | None = None,
    allow_personalization: bool = False,
    allow_follow_up: bool = True,
) -> str:
    normalized_route = (route_name or "").strip().lower()
    if normalized_route not in ENFORCED_PIPELINE_ROUTES:
        raise ValueError(f"route {route_name!r} is not allowed to bypass the enforced pipeline")

    filtered = strict_output_filter(text)
    return style_response(
        filtered,
        intent=intent,
        query=query,
        user_name=user_name,
        allow_personalization=allow_personalization,
        allow_follow_up=allow_follow_up,
    )


def build_constraint_context(query: str) -> str:
    constraints = _extract_constraints(query)
    if not constraints:
        return ""

    parts: list[str] = []
    for key, value in constraints.items():
        if key == "funding_type":
            parts.append(f"funding: {value}")
            continue
        if key == "loan_allowed":
            parts.append("loans not allowed")
            continue
        if key in {"budget_amount", "timeframe_literal", "duration_literal"}:
            parts.append(str(value))
            continue
        if value is True:
            parts.append(key.replace("_", " "))
        else:
            parts.append(str(value))
    return " | ".join(parts)


def _needs_strict_general_enforcement(query: str, intent: str) -> bool:
    normalized_intent = (intent or "general").strip().lower()
    if normalized_intent not in {"general", "analysis"}:
        return False

    normalized_query = (query or "").strip().lower()
    if not normalized_query:
        return False

    extracted_constraints = _extract_constraints(query)
    non_default_constraints = {
        key: value
        for key, value in extracted_constraints.items()
        if key not in {"funding_type", "loan_allowed"}
    }
    if non_default_constraints:
        return True

    strict_phrases = (
        *DECISION_QUERY_PATTERNS,
        "give me steps",
        "steps to start",
        "start something",
        "keep it short",
        "step by step",
        "next step",
        "exactly what to do",
        "help me start",
        "decide for me",
        "be honest",
        "works now",
        "what do i do today",
        "what do i do tomorrow",
        "what do i do this week",
        "need to get something working",
    )
    return any(phrase in normalized_query for phrase in strict_phrases)


def strict_output_filter(text: str) -> str:
    cleaned = (text or "").replace("\r\n", "\n").strip()
    if not cleaned:
        return ""

    extracted = _extract_reply_after_marker(cleaned)
    if extracted:
        cleaned = extracted

    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    filtered_lines = [line for line in lines if not _is_meta_line(line)]

    candidate = " ".join(filtered_lines).strip() if filtered_lines else cleaned
    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", candidate) if sentence.strip()]
    filtered_sentences = [sentence for sentence in sentences if not _is_meta_line(sentence)]

    final_text = " ".join(filtered_sentences).strip() if filtered_sentences else candidate
    final_text = re.sub(r"\s+", " ", final_text).strip()
    return final_text


def contains_meta_artifacts(text: str) -> bool:
    normalized = (text or "").strip()
    if not normalized:
        return False
    if _extract_reply_after_marker(normalized):
        return True
    if any(line for line in normalized.splitlines() if _is_meta_line(line)):
        return True
    return False


def sanitize_frontend_payload(payload: dict[str, object]) -> dict[str, object]:
    response = dict(payload)
    data = dict(response.get("data") or {}) if isinstance(response.get("data"), dict) else None

    summary_source = str(response.get("summary") or (data.get("reply") if data else "") or "")
    summary = strict_output_filter(summary_source)
    if summary:
        response["summary"] = summary

    if data is not None:
        if "reply" in data:
            reply_source = str(data.get("reply") or summary or "")
            filtered_reply = strict_output_filter(reply_source)
            if filtered_reply:
                data["reply"] = filtered_reply
            elif summary:
                data["reply"] = summary
        response["data"] = data

    return response


def _remove_filler(text: str) -> str:
    trimmed = text
    for pattern in FILLER_PATTERNS:
        trimmed = re.sub(pattern, " ", trimmed, flags=re.IGNORECASE)

    trimmed = re.sub(r"\s+", " ", trimmed)
    trimmed = re.sub(r"\s*\n\s*", "\n", trimmed)
    return trimmed.strip()


def _remove_feature_suggestions(text: str) -> str:
    cleaned = text
    for pattern in FEATURE_SUGGESTION_PATTERNS:
        cleaned = pattern.sub(" ", cleaned)

    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _remove_question_restatement(text: str) -> str:
    cleaned = text.strip()
    for pattern in QUESTION_RESTATEMENT_PATTERNS:
        cleaned = pattern.sub("", cleaned).strip()
    return cleaned


def _apply_generic_advice_gate(text: str) -> str:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    rewritten_paragraphs: list[str] = []

    for paragraph in paragraphs:
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", paragraph) if part.strip()]
        rewritten_sentences: list[str] = []

        for sentence in sentences:
            rewritten = _rewrite_generic_advice_sentence(sentence)
            if rewritten:
                rewritten_sentences.append(rewritten)

        if rewritten_sentences:
            rewritten_paragraphs.append(" ".join(rewritten_sentences))

    cleaned = "\n\n".join(rewritten_paragraphs).strip()
    return re.sub(r"\s+", " ", cleaned).strip()


def _rewrite_generic_advice_sentence(sentence: str) -> str:
    stripped = sentence.strip()
    if not stripped:
        return ""

    matched_rewrites = [replacement for pattern, replacement in GENERIC_ADVICE_RULES if pattern.search(stripped)]
    if matched_rewrites:
        if _has_concrete_action(stripped):
            return stripped
        unique_rewrites: list[str] = []
        for rewrite in matched_rewrites:
            if rewrite not in unique_rewrites:
                unique_rewrites.append(rewrite)
        return " ".join(unique_rewrites[:2]).strip()

    return stripped


def _extract_constraints(query: str) -> dict[str, str | bool]:
    normalized = (query or "").strip()
    if not normalized:
        return {}

    constraints: dict[str, str | bool] = {
        "funding_type": "internal_only",
        "loan_allowed": False,
    }

    for pattern in BUDGET_PATTERNS:
        match = pattern.search(normalized)
        if not match:
            continue
        if match.lastindex:
            constraints["budget"] = f"${match.group(1)} budget"
            constraints["budget_amount"] = f"${match.group(1)}"
        else:
            constraints["budget"] = "low budget"
        break

    for pattern in DURATION_PATTERNS:
        match = pattern.search(normalized)
        if match:
            constraints["duration_literal"] = match.group(1).lower()
            break

    for pattern in TIMEFRAME_LITERAL_PATTERNS:
        match = pattern.search(normalized)
        if match:
            constraints["timeframe_literal"] = match.group(1).lower()
            break

    for pattern in TIME_PATTERNS:
        match = pattern.search(normalized)
        if match:
            constraints["time"] = match.group(1)
            break

    for pattern in TIME_WINDOW_PATTERNS:
        match = pattern.search(normalized)
        if match:
            constraints["time_window"] = match.group(1).replace("–", "-")
            break

    for pattern in RESOURCE_PATTERNS:
        match = pattern.search(normalized)
        if not match:
            continue
        value = match.group(0).lower().replace(" ", "_")
        constraints[value] = True

    for pattern in LOCATION_HINT_PATTERNS:
        match = pattern.search(normalized)
        if match:
            constraints["location"] = match.group(1)
            break

    return constraints


def _apply_constraint_override(text: str, constraints: dict[str, str | bool]) -> str:
    if not text or not constraints:
        return text

    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
    kept: list[str] = []
    removed_constraint_keys: set[str] = set()

    for sentence in sentences:
        violated = False
        for key, patterns in CONSTRAINT_VIOLATION_PATTERNS.items():
            if key not in constraints:
                continue
            if any(pattern.search(sentence) for pattern in patterns):
                violated = True
                removed_constraint_keys.add(key)
                break
        if not violated:
            kept.append(sentence)

    for key in ("budget", "no_team", "no_kitchen"):
        if key in constraints and (key in removed_constraint_keys or not _mentions_constraint_action(kept, key)):
            fallback = _build_constraint_fallback_step(key, constraints)
            if fallback and fallback not in kept:
                kept.append(fallback)

    return " ".join(kept).strip() or text


def _mentions_constraint_action(sentences: list[str], key: str) -> bool:
    joined = " ".join(sentences).lower()
    if key == "budget":
        return any(term in joined for term in ("cheap", "low-cost", "what you already have", "without spending", "free", "no new money", "existing money", "existing inventory"))
    if key == "no_team":
        return any(term in joined for term in ("alone", "solo", "yourself", "by yourself", "on your own", "available person already in your unit", "inside your unit"))
    if key == "no_kitchen":
        return any(term in joined for term in ("ready-made", "cold distribution", "existing facility", "army corps facility", "mess hall"))
    return False


def _build_constraint_fallback_step(key: str, constraints: dict[str, str | bool]) -> str:
    if key == "budget":
        budget_amount = str(constraints.get("budget_amount") or "").strip()
        time_hint = str(constraints.get("timeframe_literal") or constraints.get("time") or "this week").strip() or "this week"
        if budget_amount:
            return f"Keep the first test at {budget_amount} or less {time_hint} and use only money and supplies you already control."
        return f"Keep the first test low-cost {time_hint} and use only money and supplies you already control."
    return DEFAULT_CONSTRAINT_STEPS.get(key, "")


def _enforce_response_structure(text: str, query: str, intent: str, constraints: dict[str, str | bool]) -> str:
    normalized_intent = (intent or "general").lower().strip()
    if normalized_intent not in {"general", "analysis"}:
        return text

    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
    if not sentences:
        return text

    direct_answer = _ensure_direct_answer(sentences[0], query, constraints)
    concrete_steps = _collect_concrete_steps(sentences[1:] if len(sentences) > 1 else [], constraints)

    structured: list[str] = [direct_answer]
    structured.extend(concrete_steps[:2])

    if len(structured) < 2:
        fallback = _build_direct_step_fallback(query, constraints)
        if fallback and fallback not in structured and not _sentence_is_actionable(direct_answer):
            structured.append(fallback)

    optional_follow_up = _build_optional_follow_up(query)
    if optional_follow_up and _wants_detail(query):
        structured.append(optional_follow_up)

    return " ".join(structured).strip()


def _ensure_direct_answer(sentence: str, query: str, constraints: dict[str, str | bool]) -> str:
    cleaned = sentence.strip()
    if not cleaned:
        return _build_direct_step_fallback(query, constraints)

    lowered = cleaned.lower()
    if _needs_honest_judgment(query):
        return cleaned

    if any(pattern.search(cleaned) for pattern in ABSTRACT_ADVICE_PATTERNS):
        return _build_direct_step_fallback(query, constraints)

    if any(pattern.search(cleaned) for pattern, _ in GENERIC_ADVICE_RULES) and not _has_concrete_action(cleaned):
        return _build_direct_step_fallback(query, constraints)

    if not _requires_decision(query) and _concrete_action_score(cleaned) < 3:
        return _build_direct_step_fallback(query, constraints)

    if lowered.startswith(("start by", "begin by")):
        cleaned = re.sub(r"^(start|begin)\s+by\s+", "Start with ", cleaned, flags=re.IGNORECASE)

    return cleaned


def _collect_concrete_steps(sentences: list[str], constraints: dict[str, str | bool]) -> list[str]:
    concrete = [sentence for sentence in sentences if _sentence_is_actionable(sentence)]
    if concrete:
        return concrete

    fallback = _build_direct_step_fallback("", constraints)
    return [fallback] if fallback else []


def _build_direct_step_fallback(query: str, constraints: dict[str, str | bool]) -> str:
    location = str(constraints.get("location") or "").strip()
    time_hint = str(constraints.get("timeframe_literal") or constraints.get("time") or "this week").strip() or "this week"
    budget_amount = str(constraints.get("budget_amount") or "").strip()
    duration_literal = str(constraints.get("duration_literal") or "").strip()
    outreach_five = _contact_target(constraints, 5)

    normalized_query = (query or "").lower()
    if any(term in normalized_query for term in ("failed last week", "nothing worked")):
        return f"Tomorrow, change 1 variable only: use the same offer with 5 different {outreach_five.split(' ', 1)[1]} and write down which version gets a reply first."

    if any(term in normalized_query for term in ("works now", "bad spot", "what do i do today")):
        return f"Today, make 1 clear ask to {outreach_five} and write down who responds before the day ends."

    if "step by step" in normalized_query and duration_literal and budget_amount:
        return f"Use {budget_amount} and spend {duration_literal} on 3 blocks: block 1 write 1 simple offer, block 2 contact {outreach_five}, block 3 record the replies and keep the best one."

    if any(term in normalized_query for term in ("feeding", "meal", "food", "feed people")):
        if location:
            return f"Start with 10 to 15 meals in {location} {time_hint} and use that first run to learn what people actually need."
        return f"Start with 10 to 15 meals {time_hint} and use that first run to learn what people actually need."

    if any(term in normalized_query for term in ("sell", "market", "audience", "customers", "buy")):
        return f"Check 5 competing offers {time_hint}, compare the price and promise, and use that to pick your first angle."

    if "budget" in constraints or "no_money" in constraints:
        if budget_amount and duration_literal:
            return f"Use {budget_amount} to run 1 small test over {duration_literal} and record what happens before {time_hint}."
        if budget_amount:
            return f"Use {budget_amount} to run 1 cheap test {time_hint} and see if anyone says yes before spending more."
        return f"Pick 1 cheap test you can run {time_hint} and use it to get real feedback before spending more."
    if "no_team" in constraints or "solo" in constraints or "alone" in constraints:
        return f"Choose 1 small version you can run alone {time_hint} and test it with 5 real people first."
    if location:
        return f"Start with 1 local test in {location} {time_hint} so you can see what actually works before scaling."
    if query:
        return f"Start with 1 small real-world test {time_hint} and use the result to decide the next step."
    return "Start with 1 small real-world test this week and use the result to decide the next step."


def _build_optional_follow_up(query: str) -> str:
    normalized = (query or "").lower()
    if any(term in normalized for term in ("don't give me ideas", "dont give me ideas", "no list", "no maybe", "exactly what to do", "what should i", "help me start")):
        return ""
    if any(term in normalized for term in ("idea", "ideas", "recommend", "suggest")):
        return "If you want, I can narrow that to the best first move."
    return ""


def _apply_decision_layer(text: str, query: str, intent: str, constraints: dict[str, str | bool]) -> str:
    normalized_intent = (intent or "general").lower().strip()
    if normalized_intent not in {"general", "analysis"}:
        return text
    if not _requires_decision(query):
        return text

    return _compose_decision_response(query, constraints)


def _compose_decision_response(query: str, constraints: dict[str, str | bool]) -> str:
    if _needs_honest_judgment(query):
        return _build_judgment_response(query, constraints)

    best_action = _build_specific_action(query, constraints)
    if _prefers_ultra_concise(query):
        compact_parts = [best_action.strip()]
        if any(key in constraints for key in ("duration_literal", "timeframe_literal", "time_window")):
            next_step = _build_time_bound_step(query, constraints).strip()
            if next_step and next_step not in compact_parts:
                compact_parts.append(next_step)
        return " ".join(part for part in compact_parts if part).strip()
    reason = _build_decision_reason(query, constraints)
    next_step = _build_time_bound_step(query, constraints)

    parts: list[str] = []
    for part in (best_action, reason, next_step):
        if part and part not in parts:
            parts.append(part)
    return " ".join(parts[:3]).strip()


def _replace_external_or_funding_phrases(text: str) -> str:
    cleaned = text
    replacements = [
        (r"\bfind a partner\b", "use 1 person already in your current setup"),
        (r"\bbuild partnerships\b", "use 1 person already in your current setup"),
        (r"\bpartner(?:s|ships)?\b", "people already in your current setup"),
        (r"\buse a platform\b", "contact 5 people you already know directly"),
        (r"\bplatform(?:s)?\b", "your current setup"),
        (r"\bmarketplace(?:s)?\b", "your current setup"),
        (r"\bloan(?:s)?\b", "existing money"),
        (r"\bborrow(?:ing|ed)?\b", "use what you already have"),
        (r"\bcredit\b", "existing money"),
        (r"\bfinanc(?:e|ing)\b", "existing money"),
        (r"\binvestor(?:s)?\b", "people already in your current setup"),
        (r"\braise money\b", "use existing money"),
        (r"\bfunding\b", "existing money"),
        (r"\bgrant(?:s)?\b", "internal Army Corps grant"),
        (r"\bhire\b", "use"),
        (r"\brecruit\b", "use"),
        (r"\boutside partner(?:s)?\b", "people already in your current setup"),
        (r"\bthird[- ]party\b", "internal"),
        (r"\bexternal\b", "internal"),
        (r"\bamazon\b", "people you already know"),
        (r"\betsy\b", "people you already know"),
        (r"\btiktok(?: shop)?\b", "people you already know"),
        (r"\bfacebook\b", "people you already know"),
        (r"\binstagram\b", "people you already know"),
        (r"\breddit\b", "people you already know"),
        (r"\bdiscord\b", "people you already know"),
    ]

    for pattern, replacement in replacements:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _build_decision_reason(query: str, constraints: dict[str, str | bool]) -> str:
    normalized = (query or "").lower()
    if any(term in normalized for term in ("feeding", "meal", "food", "feed people")):
        options = (
            "It is the fastest version you can run with what you already control.",
            "It gets real proof without waiting on more people or more setup.",
            "It lets you test demand fast instead of building a bigger system first.",
        )
        return _choose_variant(query, "decision-reason-feeding", options)
    if any(term in normalized for term in ("solar charger", "sell", "market", "audience", "customers")):
        options = (
            "It tells you fast whether anyone will actually buy.",
            "It gives you proof before you waste time polishing the wrong offer.",
            "It shows demand now instead of leaving you guessing.",
        )
        return _choose_variant(query, "decision-reason-market", options)
    if any(term in normalized for term in ("saas", "app", "product", "launch")):
        options = (
            "It checks demand before you build too much.",
            "It proves interest before you sink more time into building.",
            "It keeps you from overbuilding before anyone says yes.",
        )
        return _choose_variant(query, "decision-reason-product", options)
    return ""


def _contact_target(constraints: dict[str, str | bool], count: int = 5) -> str:
    if constraints.get("no_connections"):
        return f"{count} people in your current environment"
    if constraints.get("funding_type") == "internal_only":
        return f"{count} people already in your unit"
    return f"{count} people you already know"


def _requires_decision(query: str) -> bool:
    normalized = (query or "").lower().strip()
    if not normalized:
        return False
    return any(pattern in normalized for pattern in DECISION_QUERY_PATTERNS) or any(
        phrase in normalized for phrase in ("which one", "be honest", "no list", "no maybe")
    )


def _needs_honest_judgment(query: str) -> bool:
    normalized = (query or "").lower().strip()
    return "am i doing too much" in normalized or ("be honest" in normalized and "too much" in normalized)


def _build_judgment_response(query: str, constraints: dict[str, str | bool]) -> str:
    normalized = (query or "").lower()
    if all(term in normalized for term in ("nonprofit", "business", "money fast")):
        return "Yes. You're trying to start 3 different things at once, and that is too much for one week. Cut it to 1 thing tomorrow and ignore the other 2 until one starts moving."
    time_hint = str(constraints.get("time") or "this week").strip() or "this week"
    return f"Yes. You're trying to carry too many priorities at once, and that will slow all of them down {time_hint}. Cut it to 1 thing {time_hint} and drop the rest until you get real traction."


def _remove_similar_sentences(text: str) -> str:
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
    if not sentences:
        return text

    kept: list[str] = []
    for sentence in sentences:
        if any(_sentence_similarity(sentence, existing) > 0.78 for existing in kept):
            continue
        kept.append(sentence)
    return " ".join(kept).strip()


def _sentence_similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, _sentence_key(left), _sentence_key(right)).ratio()


def _human_realism_pass(text: str, query: str, intent: str, constraints: dict[str, str | bool]) -> str:
    normalized_intent = (intent or "general").lower().strip()
    if normalized_intent not in {"general", "analysis", "memory"}:
        return text

    if _sounds_human_and_practical(text):
        return text

    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
    sentences = [sentence for sentence in sentences if not any(pattern.search(sentence) for pattern in ABSTRACT_ADVICE_PATTERNS)]
    if not sentences:
        sentences = [_build_direct_step_fallback(query, constraints)]

    tightened = " ".join(sentences[:3]).strip()
    tightened = _normalize_sentence_start(tightened)
    return tightened


def _sounds_human_and_practical(text: str) -> bool:
    if not text:
        return False
    if any(pattern.search(text) for pattern in ABSTRACT_ADVICE_PATTERNS):
        return False
    if any(pattern.search(text) for pattern, _ in GENERIC_ADVICE_RULES) and not _has_concrete_action(text):
        return False
    return True


def _force_specificity(text: str, query: str, intent: str, constraints: dict[str, str | bool]) -> str:
    normalized_intent = (intent or "general").lower().strip()
    if normalized_intent not in {"general", "analysis"}:
        return text

    if not _is_vague_response(text):
        return text

    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
    direct_answer = sentences[0] if sentences else _build_direct_step_fallback(query, constraints)
    specific_step = _build_specific_action(query, constraints)

    structured = [direct_answer]
    if specific_step and specific_step not in structured:
        structured.append(specific_step)

    time_step = _build_time_bound_step(query, constraints)
    if time_step and time_step not in structured:
        structured.append(time_step)

    return " ".join(structured[:4]).strip()


def _run_rewrite_loop(text: str, query: str, intent: str, constraints: dict[str, str | bool]) -> str:
    candidate = text.strip()
    for _ in range(MAX_REWRITE_ATTEMPTS):
        failures = _validate_response(candidate, query, intent, constraints)
        if not failures:
            return candidate
        candidate = _rewrite_response(candidate, query, intent, constraints, failures)

    final_failures = _validate_response(candidate, query, intent, constraints)
    if any(failure in HARD_FAILURE_TYPES for failure in final_failures):
        return _build_fallback_response(query, constraints)
    return candidate


def _validate_response(text: str, query: str, intent: str, constraints: dict[str, str | bool]) -> list[str]:
    normalized_intent = (intent or "general").lower().strip()
    if normalized_intent not in {"general", "analysis"}:
        return []

    failures: list[str] = []
    if _contains_unrewritten_generic_advice(text):
        failures.append("generic_advice")
    if _contains_banned_generic_phrase(text):
        failures.append("banned_generic")
    if _contains_constraint_violation(text, constraints):
        failures.append("constraint_violation")
    if _contains_external_funding(text):
        failures.append("external_funding")
    if _contains_external_dependency(text):
        failures.append("external_dependency")
    if not _uses_constraints(text, constraints):
        failures.append("constraint_binding")
    if not _has_required_actionability(text):
        failures.append("insufficient_actionability")
    if not _matches_query_domain(text, query):
        failures.append("domain_mismatch")
    if _has_pure_fluff_opener(text):
        failures.append("fluff")
    if _looks_like_restatement(text):
        failures.append("restatement")
    if _contains_drift(text, query):
        failures.append("drift")
    if _requires_decision(query) and not _makes_clear_decision(text):
        failures.append("decision_missing")
    if _requires_decision(query) and _contains_multiple_options(text):
        failures.append("multiple_options")
    return failures


def _rewrite_response(text: str, query: str, intent: str, constraints: dict[str, str | bool], failures: list[str]) -> str:
    rewritten = text

    if _requires_decision(query) and any(
        failure in failures
        for failure in (
            "generic_advice",
            "banned_generic",
            "constraint_binding",
            "insufficient_actionability",
            "decision_missing",
            "multiple_options",
        )
    ):
        rewritten = _compose_decision_response(query, constraints)

    if "external_funding" in failures or "external_dependency" in failures:
        rewritten = _replace_external_or_funding_phrases(rewritten)

    if "generic_advice" in failures:
        rewritten = _apply_generic_advice_gate(rewritten)

    if "banned_generic" in failures:
        rewritten = _remove_banned_generic_phrases(rewritten)

    if "constraint_violation" in failures:
        rewritten = _apply_constraint_override(rewritten, constraints)

    if "constraint_binding" in failures:
        rewritten = _apply_constraint_override(rewritten, constraints)
        rewritten = _force_specificity(rewritten, query, intent, constraints)

    if "insufficient_actionability" in failures:
        rewritten = _force_specificity(rewritten, query, intent, constraints)

    if "domain_mismatch" in failures:
        rewritten = _force_specificity(rewritten, query, intent, constraints)

    if "fluff" in failures:
        rewritten = _remove_filler(rewritten)

    if "restatement" in failures:
        rewritten = _remove_question_restatement(rewritten)
        rewritten = _force_specificity(rewritten, query, intent, constraints)

    if "decision_missing" in failures:
        rewritten = _apply_decision_layer(rewritten, query, intent, constraints)

    if "multiple_options" in failures:
        rewritten = _compose_decision_response(query, constraints)

    rewritten = _human_realism_pass(rewritten, query, intent, constraints)
    rewritten = _replace_external_or_funding_phrases(rewritten)
    rewritten = _remove_similar_sentences(rewritten)
    return rewritten.strip()


def _build_fallback_response(query: str, constraints: dict[str, str | bool]) -> str:
    if _needs_honest_judgment(query):
        return _build_judgment_response(query, constraints)

    if _requires_decision(query):
        return _compose_decision_response(query, constraints)

    if constraints:
        parts: list[str] = []
        for part in (_build_specific_action(query, constraints), _build_time_bound_step(query, constraints)):
            normalized_part = (part or "").strip()
            if normalized_part and normalized_part not in parts:
                parts.append(normalized_part)
        if parts:
            return " ".join(parts[:2]).strip()

    specific = _build_fallback_specific_action(query, constraints)
    time_hint = _build_fallback_deadline(constraints)
    quantity, resource = _build_fallback_start(query, constraints)
    template = FALLBACK_TEMPLATE_POOL[_fallback_template_index(query)]
    return template.format(action=specific, resource=resource, time_hint=time_hint, quantity=quantity)


def _fallback_template_index(query: str) -> int:
    normalized = (query or "").encode("utf-8")
    digest = hashlib.sha256(normalized).hexdigest()
    return int(digest[:8], 16) % len(FALLBACK_TEMPLATE_POOL)


def _contains_external_funding(text: str) -> bool:
    normalized = (text or "").strip()
    if not normalized:
        return False
    if re.search(r"\binternal Army Corps grant\b", normalized, re.IGNORECASE):
        normalized = re.sub(r"\binternal Army Corps grant\b", "", normalized, flags=re.IGNORECASE)
    return any(pattern.search(normalized) for pattern in EXTERNAL_FUNDING_PATTERNS)


def _contains_external_dependency(text: str) -> bool:
    normalized = (text or "").strip()
    if not normalized:
        return False
    return any(pattern.search(normalized) for pattern in EXTERNAL_DEPENDENCY_PATTERNS)


def _contains_unrewritten_generic_advice(text: str) -> bool:
    normalized = (text or "").strip()
    if not normalized:
        return True
    return any(pattern.search(normalized) for pattern, _ in GENERIC_ADVICE_RULES) and not _has_required_actionability(normalized)


def _contains_banned_generic_phrase(text: str) -> bool:
    normalized = (text or "").strip()
    if not normalized:
        return True
    return any(pattern.search(normalized) for pattern in GENERIC_FAILURE_PATTERNS)


def _contains_constraint_violation(text: str, constraints: dict[str, str | bool]) -> bool:
    if not text or not constraints:
        return False
    for key, patterns in CONSTRAINT_VIOLATION_PATTERNS.items():
        if key not in constraints:
            continue
        if any(pattern.search(text) for pattern in patterns):
            return True
    return False


def _matches_query_domain(text: str, query: str) -> bool:
    normalized_query = (query or "").lower()
    normalized_text = (text or "").lower()

    if any(term in normalized_query for term in ("feeding", "meal", "food", "feed people")):
        return any(term in normalized_text for term in ("meal", "meals", "food", "grocery", "partner site", "serve"))

    if any(term in normalized_query for term in ("solar charger", "solar chargers")):
        return any(term in normalized_text for term in ("amazon", "etsy", "tiktok", "solar charger", "price", "buyers"))

    if "too much" in normalized_query:
        return any(term in normalized_text for term in ("yes", "no", "1 thing", "3 different things", "cut"))

    return True


def _uses_constraints(text: str, constraints: dict[str, str | bool]) -> bool:
    if not constraints:
        return True

    normalized = (text or "").lower()
    checks: list[bool] = []
    if "budget_amount" in constraints:
        checks.append(str(constraints.get("budget_amount") or "").lower() in normalized)
    if "budget" in constraints:
        checks.append(any(term in normalized for term in ("$", "under", "cheap", "free", "what you already have", "spend", "no new money", "existing money", "existing inventory")))
    if "duration_literal" in constraints:
        checks.append(str(constraints.get("duration_literal") or "").lower() in normalized)
    if "timeframe_literal" in constraints:
        checks.append(str(constraints.get("timeframe_literal") or "").lower() in normalized)
    if "time" in constraints:
        checks.append(str(constraints.get("time") or "").lower() in normalized)
    if "time_window" in constraints:
        checks.append(str(constraints.get("time_window") or "").lower() in normalized)
    if "no_team" in constraints:
        checks.append(any(term in normalized for term in ("solo", "alone", "on your own", "yourself", "available person already in your unit", "inside your unit")))
    if "no_kitchen" in constraints:
        checks.append(any(term in normalized for term in ("grocery", "ready-made", "cold distribution", "existing facility", "army corps facility", "no kitchen")))
    if "location" in constraints:
        checks.append(str(constraints.get("location") or "").lower() in normalized)
    if constraints.get("funding_type") == "internal_only":
        checks.append(any(term in normalized for term in ("current setup", "your own setup", "people you already know", "army corps", "inside the system", "inside your unit", "internal contact list", "existing resources", "what you already have", "existing money", "existing inventory", "no new money")))
    if constraints.get("loan_allowed") is False:
        checks.append("loan" not in normalized and "borrow" not in normalized and "credit" not in normalized and "financing" not in normalized)
    return all(checks) if checks else True


def _contains_drift(text: str, query: str) -> bool:
    normalized_text = (text or "").lower()
    normalized_query = (query or "").lower()
    if not normalized_text:
        return False

    if any(pattern.search(normalized_text) for pattern in DRIFT_PATTERNS):
        if not any(term in normalized_query for term in ("news", "headline", "weather", "forecast", "temperature", "rain", "snow")):
            return True

    return False


def _looks_like_restatement(text: str) -> bool:
    first_sentence = re.split(r"(?<=[.!?])\s+", (text or "").strip())[0] if (text or "").strip() else ""
    if not first_sentence:
        return False
    if any(pattern.search(first_sentence) for pattern in QUESTION_RESTATEMENT_PATTERNS):
        return True
    lowered = first_sentence.lower()
    return lowered.startswith(("you want to", "you need to", "you're asking", "you are asking", "the question is"))


def _makes_clear_decision(text: str) -> bool:
    normalized = (text or "").lower()
    if not normalized:
        return False
    if any(pattern.search(normalized) for pattern in GENERIC_FAILURE_PATTERNS if pattern.pattern in {r"\byou could\b", r"\bmaybe\b", r"\bit depends\b", r"\bone option is\b"}):
        return False
    if _contains_multiple_options(text):
        return False
    return any(term in normalized for term in ("start with", "pick this move", "here is the move", "go with this", "make this the whole play", "yes.", "no.", "cut it to 1 thing", "do this first", "take 1 step"))


def _contains_multiple_options(text: str) -> bool:
    normalized = (text or "").strip()
    if not normalized:
        return False
    first_sentence = re.split(r"(?<=[.!?])\s+", normalized)[0]
    if any(pattern.search(first_sentence) for pattern in MULTI_OPTION_DECISION_PATTERNS):
        return True
    if re.search(r"\b(?:or|either)\b", first_sentence, re.IGNORECASE) and re.search(r"\b(?:start|build|hire|rent|choose|pick|use|sell|serve|run|contact)\b", first_sentence, re.IGNORECASE):
        return True
    return False


def _has_required_actionability(text: str) -> bool:
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
    return any(_sentence_is_actionable(sentence) for sentence in sentences)


def _sentence_is_actionable(sentence: str) -> bool:
    has_number = bool(re.search(r"\b\d+\b", sentence))
    has_time = bool(re.search(r"\b(today|tomorrow|tonight|this week|this weekend|this month|by (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b", sentence, re.IGNORECASE))
    has_action = _has_action_verb(sentence)
    return has_number and has_time and has_action and _concrete_action_score(sentence) >= 2


def _concrete_action_score(sentence: str) -> int:
    score = 0
    if _has_action_verb(sentence):
        score += 1
    if bool(re.search(r"\b\d+\b", sentence)):
        score += 1
    if any(pattern.search(sentence) for pattern in CONCRETE_CHANNEL_OR_LOCATION_PATTERNS):
        score += 1
    if bool(re.search(r"\b(today|tomorrow|tonight|this week|this weekend|this month|by (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b", sentence, re.IGNORECASE)):
        score += 1
    return score


def _has_action_verb(sentence: str) -> bool:
    return bool(re.search(r"\b(call|email|text|dm|message|visit|ask|join|post|ship|test|contact|list|write|pick|book|compare|send|talk|reach|start|run|buy|serve|show|note|track|cut|drop|focus|ignore|stop|do)\b", sentence, re.IGNORECASE))


def _has_pure_fluff_opener(text: str) -> bool:
    first_sentence = re.split(r"(?<=[.!?])\s+", (text or "").strip())[0] if (text or "").strip() else ""
    if not first_sentence:
        return False
    fluff = any(re.search(pattern, first_sentence, re.IGNORECASE) for pattern in FILLER_PATTERNS)
    return fluff and _concrete_action_score(first_sentence) == 0


def _is_vague_response(text: str) -> bool:
    cleaned = (text or "").strip()
    if not cleaned:
        return True

    return not _has_required_actionability(cleaned)


def _build_specific_action(query: str, constraints: dict[str, str | bool]) -> str:
    normalized = (query or "").lower()
    location = str(constraints.get("location") or "local").strip() or "local"
    time_hint = str(constraints.get("timeframe_literal") or constraints.get("time") or "this week").strip() or "this week"
    budget_amount = str(constraints.get("budget_amount") or "").strip()
    duration_literal = str(constraints.get("duration_literal") or "").strip()
    internal_only_clause = " inside Army Corps only using what you already have" if constraints.get("funding_type") == "internal_only" else ""
    outreach_five = _contact_target(constraints, 5)
    outreach_three = _contact_target(constraints, 3)

    if any(term in normalized for term in ("failed last week", "nothing worked")):
        return f"Tomorrow, change 1 variable only: use the same offer with 5 different {outreach_five.split(' ', 1)[1]} and write down which message gets a reply first."

    if any(term in normalized for term in ("works now", "bad spot", "what do i do today")):
        options = (
            f"Today, make 1 direct ask to {outreach_five} and record who says yes before the day ends.",
            f"Today, send 1 blunt offer to {outreach_five} and note who replies before tonight.",
            f"Today, ask {outreach_five} for one clear yes or no and track every reply before the day ends.",
        )
        return _choose_variant(query, "specific-action-urgent", options)

    if "one next step" in normalized:
        options = (
            f"Take 1 step {time_hint}: send 1 simple ask to {outreach_five} and write down who replies.",
            f"Make your 1 move {time_hint}: send one clear ask to {outreach_five} and note who answers.",
            f"Do 1 thing {time_hint}: send one direct ask to {outreach_five} and track every reply.",
        )
        return _choose_variant(query, "specific-action-one-step", options)

    if "step by step" in normalized and duration_literal and budget_amount:
        return f"Use {budget_amount} over {duration_literal}: first 1 hour write 1 simple offer, next 1 hour contact {outreach_five}, final 1 hour record replies and keep the strongest one."

    if any(term in normalized for term in ("feeding", "meal", "food", "feed people")):
        if "tomorrow" in normalized and "weekend" in normalized:
            options = (
                f"Tomorrow, secure ready-made food for 10 to 15 meals in {location} and lock one pickup point for this weekend.",
                f"Tomorrow, line up ready-made food for 10 to 15 meals in {location} and set one handout point for this weekend.",
                f"Tomorrow, buy or pull ready-made food for 10 to 15 meals in {location} and confirm one distribution spot for this weekend.",
            )
            return _choose_variant(query, "specific-action-feeding-weekend", options)
        if constraints.get("time") == "this weekend":
            options = (
                f"Run 10 to 15 ready-made meals in {location} this weekend from one pickup spot you already control.",
                f"Serve 10 to 15 ready-made meals in {location} this weekend through one simple pickup point.",
                f"Do one ready-made meal run for 10 to 15 people in {location} this weekend from a single handout spot.",
            )
            return _choose_variant(query, "specific-action-feeding-weekend-only", options)
        if constraints.get("time") == "tomorrow":
            options = (
                f"Run 10 to 15 ready-made meals in {location} tomorrow from one pickup point you already control.",
                f"Serve 10 to 15 ready-made meals in {location} tomorrow through one simple handout spot.",
                f"Do one ready-made meal run for 10 to 15 people in {location} tomorrow from a single pickup location.",
            )
            return _choose_variant(query, "specific-action-feeding-tomorrow", options)
        options = (
            f"Run 10 to 15 ready-made meals in {location} this week from one pickup point you already control.",
            f"Serve 10 to 15 ready-made meals in {location} this week through one simple handout spot.",
            f"Do one ready-made meal run for 10 to 15 people in {location} this week from a single pickup location.",
        )
        return _choose_variant(query, "specific-action-feeding-week", options)

    if any(term in normalized for term in ("sell", "market", "audience", "customers", "buy")):
        options = (
            f"Check 5 similar requests today, note the need and urgency, and contact {outreach_five} this week{internal_only_clause}.",
            f"Scan 5 similar offers today, write down the price and promise, and message {outreach_five} this week{internal_only_clause}.",
            f"Review 5 competing offers today, pick one angle, and contact {outreach_five} this week{internal_only_clause}.",
        )
        return _choose_variant(query, "specific-action-market", options)

    if any(term in normalized for term in ("saas", "app", "product", "build", "launch")):
        options = (
            f"Pick one narrow problem, show it to {outreach_five} this week, and ask whether they would use it now.",
            f"Choose one pain point, show one rough offer to {outreach_five} this week, and ask for a yes or no.",
            f"Lock one problem, test one offer with {outreach_five} this week, and record who says yes.",
        )
        return _choose_variant(query, "specific-action-product", options)

    if "no_money" in constraints and "no_connections" in constraints and "no_time" in constraints:
        options = (
            f"Use the next 15 minutes today to write 1 simple ask and say it directly to {outreach_three}.",
            f"Spend the next 15 minutes today writing one blunt ask and sending it to {outreach_three}.",
            f"Use the next 15 minutes today to send one clear ask to {outreach_three} and wait for real replies.",
        )
        return _choose_variant(query, "specific-action-no-money-no-time", options)

    if "budget" in constraints or "no_money" in constraints:
        if "time_window" in constraints:
            options = (
                f"Use {budget_amount} and write one simple offer before {constraints['time_window']} using existing money only{internal_only_clause}, then contact {outreach_five} during {constraints['time_window']}.",
                f"Put {budget_amount} into one tight test{internal_only_clause}: write one simple offer before {constraints['time_window']} and contact {outreach_five} during that window.",
                f"Spend {budget_amount} on one small test{internal_only_clause}: write one simple offer before {constraints['time_window']} and get it in front of {outreach_five} during that window.",
            ) if budget_amount else (
                f"Write one simple offer before {constraints['time_window']} using existing money only{internal_only_clause}, then contact {outreach_five} during {constraints['time_window']}.",
                f"Run one tight test before {constraints['time_window']}{internal_only_clause}: write one simple offer and put it in front of {outreach_five} during that window.",
            )
            return _choose_variant(query, "specific-action-budget-window", options)
        if "tomorrow" in time_hint.lower():
            options = (
                f"Use {budget_amount} and write one simple offer tonight using existing money only{internal_only_clause}, contact {outreach_five} tomorrow, and ask for a clear yes or no.",
                f"Take {budget_amount} and put it into one tight test tonight{internal_only_clause}: write one simple offer, then contact {outreach_five} tomorrow for a yes or no.",
                f"Spend {budget_amount} on one small test tonight{internal_only_clause}: write one simple offer and take it to {outreach_five} tomorrow for a direct answer.",
            ) if budget_amount else (
                f"Write one simple offer tonight using existing money only{internal_only_clause}, contact {outreach_five} tomorrow, and ask for a clear yes or no.",
                f"Run one tight test tonight{internal_only_clause}: write one simple offer and take it to {outreach_five} tomorrow for a direct answer.",
            )
            return _choose_variant(query, "specific-action-budget-tomorrow", options)
        options = (
            f"Use {budget_amount} and write one simple offer today using existing money only{internal_only_clause}, contact {outreach_five} {time_hint}, and ask for a clear yes or no.",
            f"Take {budget_amount} and put it into one tight test today{internal_only_clause}: write one simple offer, then contact {outreach_five} {time_hint} for a clear answer.",
            f"Spend {budget_amount} on one small test today{internal_only_clause}: write one simple offer and get it in front of {outreach_five} {time_hint}.",
        ) if budget_amount else (
            f"Write one simple offer today using existing money only{internal_only_clause}, contact {outreach_five} {time_hint}, and ask for a clear yes or no.",
            f"Run one tight test today{internal_only_clause}: write one simple offer and get it in front of {outreach_five} {time_hint}.",
        )
        return _choose_variant(query, "specific-action-budget-general", options)

    if "time_window" in constraints:
        options = (
            f"Write one simple offer before {constraints['time_window']}, then contact {outreach_five} during {constraints['time_window']}.",
            f"Use {constraints['time_window']} for one tight push: write one simple offer first, then put it in front of {outreach_five}.",
            f"Before {constraints['time_window']}, lock one simple offer and take it to {outreach_five} during that window.",
        )
        return _choose_variant(query, "specific-action-time-window", options)
    if "tomorrow" in time_hint.lower():
        options = (
            f"Pick one small test, run it with {outreach_five} tomorrow, and write down what worked and what failed.",
            f"Run one small test with {outreach_five} tomorrow and record exactly what landed and what did not.",
            f"Do one small test with {outreach_five} tomorrow and note what got a response and what fell flat.",
        )
        return _choose_variant(query, "specific-action-tomorrow-generic", options)
    options = (
        f"Pick one small test, run it with {outreach_five} {time_hint}, and write down what worked and what failed.",
        f"Run one small test with {outreach_five} {time_hint} and record exactly what landed and what did not.",
        f"Do one small test with {outreach_five} {time_hint} and note what got a response and what fell flat.",
    )
    return _choose_variant(query, "specific-action-generic", options)


def _build_time_bound_step(query: str, constraints: dict[str, str | bool]) -> str:
    normalized = (query or "").lower()
    duration_literal = str(constraints.get("duration_literal") or "").strip()
    timeframe_literal = str(constraints.get("timeframe_literal") or constraints.get("time") or "this week").strip() or "this week"
    if "tomorrow" in normalized and "weekend" in normalized and any(term in normalized for term in ("feeding", "meal", "food", "feed people")):
        return "Serve those 10 to 15 meals this weekend and write down how many people showed up and what ran out first."
    if "time_window" in constraints:
        time_window = str(constraints.get("time_window") or "").strip()
        day_hint = timeframe_literal
        return f"Do it {day_hint} between {time_window} and write down the result by the end of that window."
    time_hint = timeframe_literal
    if duration_literal and time_hint:
        return f"Use the result within {duration_literal} and decide the next move by {time_hint}."
    if "today" in time_hint.lower():
        return "Write down the result today so you can decide the next move immediately."
    options = (
        f"Do it {time_hint} and decide by the end whether it earned a second run.",
        f"Finish it {time_hint} and judge it on the result, not the idea.",
        f"Get it done {time_hint} and let the result decide if it is worth repeating.",
    )
    return _choose_variant(query, "time-bound-step", options)


def _remove_banned_generic_phrases(text: str) -> str:
    cleaned = text
    for pattern in GENERIC_FAILURE_PATTERNS:
        cleaned = pattern.sub(" ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _build_fallback_specific_action(query: str, constraints: dict[str, str | bool]) -> str:
    action = _build_specific_action(query, constraints).strip()
    if action.endswith("."):
        action = action[:-1]
    return action if action else "Run one small test"


def _build_fallback_deadline(constraints: dict[str, str | bool]) -> str:
    if "time_window" in constraints:
        day_hint = str(constraints.get("timeframe_literal") or constraints.get("time") or "tomorrow").strip() or "tomorrow"
        return f"{day_hint} between {constraints['time_window']}"
    if "duration_literal" in constraints and "timeframe_literal" in constraints:
        return f"{constraints['duration_literal']} ending {constraints['timeframe_literal']}"
    return str(constraints.get("timeframe_literal") or constraints.get("time") or "this week").strip() or "this week"


def _build_fallback_start(query: str, constraints: dict[str, str | bool]) -> tuple[str, str]:
    normalized = (query or "").lower()
    budget_amount = str(constraints.get("budget_amount") or "").strip()
    if any(term in normalized for term in ("feeding", "meal", "food", "feed people")):
        return ("10 to 15 meals", "ready-made food and one pickup point you already control")
    if any(term in normalized for term in ("sell", "solar charger", "market", "customers", "buyers")):
        return ("5 direct contacts", "people you already know and your phone")
    if "budget" in constraints or "no_money" in constraints:
        resource = "existing money, existing inventory, and people you already know"
        if budget_amount:
            resource = f"{budget_amount}, existing inventory, and people you already know"
        return ("5 direct contacts", resource)
    return ("5 direct contacts", "existing resources you already control")


def _final_tone_humanizer(text: str, query: str, intent: str) -> str:
    normalized_intent = (intent or "general").lower().strip()
    if normalized_intent not in {"general", "analysis", "memory"}:
        return text

    cleaned = (text or "").strip()
    if not cleaned:
        return ""

    cleaned = _prune_stock_closers(cleaned, query)

    for pattern, replacement in TONE_TIGHTEN_REPLACEMENTS:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r"\bthat is the\b", "That is the", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", cleaned) if part.strip()]

    tightened: list[str] = []
    for sentence in sentences:
        if sentence not in tightened:
            tightened.append(sentence)

    if any(pattern in (query or "").lower() for pattern in DECISION_QUERY_PATTERNS):
        return " ".join(tightened[:3]).strip()

    return " ".join(tightened).strip()


def _choose_variant(query: str, salt: str, options: tuple[str, ...] | list[str]) -> str:
    pool = tuple(option for option in options if option)
    if not pool:
        return ""
    if len(pool) == 1:
        return pool[0]

    seed = f"{salt}::{(query or '').strip().lower()}".encode("utf-8")
    digest = hashlib.sha256(seed).hexdigest()
    index = int(digest[:8], 16) % len(pool)
    return pool[index]


def _has_concrete_action(sentence: str) -> bool:
    return any(pattern.search(sentence) for pattern in CONCRETE_ACTION_PATTERNS)


def _strip_report_labels(text: str) -> str:
    cleaned = re.sub(
        r"(?:(?<=^)|(?<=[.!?]\s))([A-Z][A-Za-z ]{2,30}):\s+",
        "",
        text,
    )
    return cleaned.strip()


def _normalize_news_opening(text: str, intent: str) -> str:
    if (intent or "").lower().strip() != "news":
        return text

    normalized = re.sub(r"^Today, major news includes\s+", "Quick update: ", text, flags=re.IGNORECASE)
    normalized = re.sub(r"^The latest coverage for\s+", "Here's what's going on with ", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"^The latest coverage\s+", "Quick update: ", normalized, flags=re.IGNORECASE)

    if normalized == text and normalized:
      first_char = normalized[:1]
      if first_char.isalpha() and normalized.lower().startswith(("big headline today", "here's what's going on", "quick update")):
          return normalized

    return normalized


def _normalize_memory_phrases(text: str) -> str:
    normalized = text
    normalized = re.sub(r"\bGot it, your name is\s+([^.?!]+) and you live in\s+([^.?!]+)[.?!]", r"Got it, you're \1 and you're in \2.", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bGot it, your name is\s+([^.?!]+)[.?!]", r"Got it, you're \1.", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bGot it, you live in\s+([^.?!]+)[.?!]", r"Got it, you're in \1.", normalized, flags=re.IGNORECASE)
    for pattern, replacement in MEMORY_REPLACEMENTS:
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def _remove_leading_name_stub(text: str) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        return ""

    cleaned = re.sub(r"^[A-Z][A-Za-z .'-]{0,40}[.?!]\s+(?=[A-Z])", "", cleaned)
    return cleaned.strip()


def _normalize_sentence_start(text: str) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        return ""

    first_char = cleaned[:1]
    if first_char.islower():
        return first_char.upper() + cleaned[1:]

    return cleaned


def _limit_to_default_length(text: str, query: str) -> str:
    if _wants_detail(query):
        return text

    if (text or "").startswith("Do this with what you already have:"):
        return text

    if _prefers_ultra_concise(query):
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
        return " ".join(sentences[:2]).strip()

    if "step by step" in (query or "").lower():
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
        return " ".join(sentences[:1]).strip()

    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
    if len(sentences) <= 4:
        return text

    return " ".join(sentences[:4]).strip()


def _wants_detail(query: str) -> bool:
    normalized = (query or "").lower()
    return any(term in normalized for term in DETAIL_REQUEST_TERMS)


def _prefers_ultra_concise(query: str) -> bool:
    normalized = (query or "").lower()
    return any(
        term in normalized
        for term in (
            "under 2 sentences",
            "one next step",
            "just decide",
            "just decide for me",
            "no ideas",
            "exactly what to do",
            "pick one",
            "no list",
        )
    )


def _prune_stock_closers(text: str, query: str) -> str:
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
    if len(sentences) < 2:
        return text

    stock_prefixes = (
        "Start with 1 small real-world test",
        "Do that this week and then decide",
        "Write down the result today",
        "Use $10 to run 1 small test",
        "Pick 1 cheap test you can run",
    )
    actionable_count = sum(1 for sentence in sentences if _sentence_is_actionable(sentence))
    pruned = []
    for index, sentence in enumerate(sentences):
        if index > 0 and actionable_count >= 1 and sentence.startswith(stock_prefixes):
            continue
        pruned.append(sentence)

    if "no outside systems" in (query or "").lower() or "no external help" in (query or "").lower():
        return " ".join(pruned[:1]).strip()

    return " ".join(pruned).strip()


def _maybe_personalize(text: str, query: str, user_name: str | None, allow_personalization: bool) -> str:
    if not allow_personalization:
        return text

    cleaned_name = str(user_name or "").strip()
    if not cleaned_name:
        return text

    normalized_text = text.strip()
    if not normalized_text:
        return text

    if cleaned_name.lower() in normalized_text.lower():
        return text

    if normalized_text.lower().startswith((f"hey {cleaned_name.lower()}", f"hi {cleaned_name.lower()}")):
        return text

    if _is_open_ended_query((query or "").lower()):
        return f"Hey {cleaned_name}, {normalized_text}"

    return text


def _maybe_add_follow_up(text: str, intent: str, query: str) -> str:
    normalized_query = (query or "").lower().strip()
    normalized_intent = (intent or "general").lower().strip()

    if "?" in text or normalized_intent not in {"general", "analysis"}:
        return text

    if any(term in normalized_query for term in ("don't give me ideas", "dont give me ideas", "no list", "no maybe", "exactly what to do", "what should i", "be honest", "help me start")):
        return text

    if not _is_open_ended_query(normalized_query):
        return text

    if "interesting" in normalized_query or "fun" in normalized_query or "cool" in normalized_query:
        return f"{text} Want another one?"

    if any(term in normalized_query for term in ("idea", "ideas", "suggest", "recommend")):
        return f"{text} Want a few more?"

    return text


def _is_open_ended_query(query: str) -> bool:
    return any(prompt in query for prompt in OPEN_ENDED_PROMPTS)


def _extract_reply_after_marker(text: str) -> str:
    lowered = text.lower()
    last_match = -1
    matched_marker = ""

    for marker in FINAL_REPLY_MARKERS:
        index = lowered.rfind(marker)
        if index > last_match:
            last_match = index
            matched_marker = marker

    if last_match < 0:
        return ""

    extracted = text[last_match + len(matched_marker):].strip()
    return extracted


def _is_meta_line(text: str) -> bool:
    normalized = (text or "").strip()
    lowered = normalized.lower()
    if not normalized:
        return False
    if "->" in normalized or "→" in normalized:
        return True
    for pattern in META_LINE_PATTERNS:
        if pattern.search(normalized):
            return True
    if lowered.startswith(("replace:", "strip meta", "remove meta", "hide all non-user-facing")):
        return True
    return False


def _sentence_key(sentence: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", sentence.lower()).strip()


def _dedupe_sentences(text: str) -> str:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    seen: set[str] = set()
    result: list[str] = []

    for paragraph in paragraphs:
        kept_sentences: list[str] = []
        for sentence in re.split(r"(?<=[.!?])\s+", paragraph):
            sentence = sentence.strip()
            if not sentence:
                continue

            key = _sentence_key(sentence)
            if key and key in seen:
                continue

            if key:
                seen.add(key)
            kept_sentences.append(sentence)

        if kept_sentences:
            result.append(" ".join(kept_sentences))

    return "\n\n".join(result).strip()


def _split_paragraph(paragraph: str) -> list[str]:
    paragraph = re.sub(r"\s+", " ", paragraph).strip()
    if not paragraph:
        return []

    if len(paragraph) <= 180:
        return [paragraph]

    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
    if len(sentences) <= 1:
        return [paragraph]

    chunks: list[str] = []
    current: list[str] = []

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        proposed = " ".join(current + [sentence]).strip()
        if current and (len(proposed) > 180 or len(current) >= 2):
            chunks.append(" ".join(current).strip())
            current = [sentence]
        else:
            current.append(sentence)

    if current:
        chunks.append(" ".join(current).strip())

    return chunks or [paragraph]