from __future__ import annotations

import re
from typing import Any

from .memory_store import (
    add_message,
    get_last_tool,
    get_long_term_facts,
    get_recent_messages,
    get_session_facts,
    get_user_id,
    get_session_value,
    set_session_facts,
    set_last_weather_city,
    set_session_value,
    update_long_term_memory,
)


LAST_NEWS_QUERY_KEY = "last_news_query"
LAST_NEWS_TOPIC_KEY = "last_news_topic"
MAX_HISTORY_MESSAGES = 20

NAME_PATTERNS = (
    re.compile(r"\bmy name is\s+([A-Za-z][A-Za-z .'-]{0,50})\b", re.IGNORECASE),
    re.compile(r"\bcall me\s+([A-Za-z][A-Za-z .'-]{0,50})\b", re.IGNORECASE),
    re.compile(r"\bi am called\s+([A-Za-z][A-Za-z .'-]{0,50})\b", re.IGNORECASE),
)

LOCATION_PATTERNS = (
    re.compile(r"\bi live in\s+([A-Za-z][A-Za-z0-9 .,'-]{0,60})\b", re.IGNORECASE),
    re.compile(r"\bi'?m in\s+([A-Za-z][A-Za-z0-9 .,'-]{0,60})\b", re.IGNORECASE),
    re.compile(r"\bi am in\s+([A-Za-z][A-Za-z0-9 .,'-]{0,60})\b", re.IGNORECASE),
    re.compile(r"\bi live near\s+([A-Za-z][A-Za-z0-9 .,'-]{0,60})\b", re.IGNORECASE),
)

PREFERENCE_PATTERNS = (
    re.compile(r"\bi like\s+(.+)$", re.IGNORECASE),
    re.compile(r"\bi love\s+(.+)$", re.IGNORECASE),
    re.compile(r"\bi enjoy\s+(.+)$", re.IGNORECASE),
    re.compile(r"\bi prefer\s+(.+)$", re.IGNORECASE),
    re.compile(r"\bi'?m into\s+(.+)$", re.IGNORECASE),
)

FAVORITE_TOPIC_PATTERNS = (
    re.compile(r"\bmy favorite topics? (?:is|are)\s+(.+)$", re.IGNORECASE),
    re.compile(r"\bmy favorite (?:subject|subjects) (?:is|are)\s+(.+)$", re.IGNORECASE),
)

GOAL_PATTERNS = (
    re.compile(r"\bmy goals? (?:is|are)\s+(.+)$", re.IGNORECASE),
    re.compile(r"\bmy goals? include\s+(.+)$", re.IGNORECASE),
    re.compile(r"\bi want to\s+(.+)$", re.IGNORECASE),
    re.compile(r"\bi'?m trying to\s+(.+)$", re.IGNORECASE),
)

PROJECT_PATTERNS = (
    re.compile(r"\bi'?m working on\s+(.+)$", re.IGNORECASE),
    re.compile(r"\bi am working on\s+(.+)$", re.IGNORECASE),
    re.compile(r"\bi'?m building\s+(.+)$", re.IGNORECASE),
    re.compile(r"\bi am building\s+(.+)$", re.IGNORECASE),
    re.compile(r"\bi'?m balancing\s+(.+)$", re.IGNORECASE),
    re.compile(r"\bi am balancing\s+(.+)$", re.IGNORECASE),
    re.compile(r"\bmy project is\s+(.+)$", re.IGNORECASE),
    re.compile(r"\bmy projects? (?:is|are|include)\s+(.+)$", re.IGNORECASE),
)

NAME_QUESTION_PATTERNS = (
    re.compile(r"\bwhat(?:'s| is) my name\b", re.IGNORECASE),
    re.compile(r"\bdo you know my name\b", re.IGNORECASE),
)

LOCATION_QUESTION_PATTERNS = (
    re.compile(r"\bwhere do i live\b", re.IGNORECASE),
    re.compile(r"\bwhere am i based\b", re.IGNORECASE),
    re.compile(r"\bwhat(?:'s| is) my (?:city|location)\b", re.IGNORECASE),
)

PREFERENCE_QUESTION_PATTERNS = (
    re.compile(r"\bwhat do i like\b", re.IGNORECASE),
    re.compile(r"\bwhat are my preferences\b", re.IGNORECASE),
    re.compile(r"\bwhat are my favorite topics\b", re.IGNORECASE),
    re.compile(r"\bwhat(?:'s| is) my favorite topic\b", re.IGNORECASE),
)

GOAL_QUESTION_PATTERNS = (
    re.compile(r"\bwhat are my goals\b", re.IGNORECASE),
    re.compile(r"\bwhat(?:'s| is) my goal\b", re.IGNORECASE),
)

PROJECT_QUESTION_PATTERNS = (
    re.compile(r"\bwhat am i working on\b", re.IGNORECASE),
    re.compile(r"\bwhat are my projects\b", re.IGNORECASE),
    re.compile(r"\bwhat project am i working on\b", re.IGNORECASE),
    re.compile(r"\bwhat ongoing projects do i have\b", re.IGNORECASE),
)

PROFILE_QUESTION_PATTERNS = (
    re.compile(r"\bwhat do you know about me\b", re.IGNORECASE),
    re.compile(r"\bwhat do you remember about me\b", re.IGNORECASE),
)

NEWS_FOLLOW_UP_PATTERNS = (
    re.compile(r"^more(?:\s+headlines)?[?.!]*$", re.IGNORECASE),
    re.compile(r"^more\s+news[?.!]*$", re.IGNORECASE),
    re.compile(r"^more\s+articles[?.!]*$", re.IGNORECASE),
    re.compile(r"^more\s+stories[?.!]*$", re.IGNORECASE),
    re.compile(r"^(?:show|give)\s+me\s+more(?:\s+headlines)?[?.!]*$", re.IGNORECASE),
)

MEMORY_STATEMENT_PREFIXES = (
    "my name is",
    "call me",
    "i am called",
    "i live in",
    "i'm in",
    "i am in",
    "i live near",
    "i like",
    "i love",
    "i enjoy",
    "i prefer",
    "i'm into",
    "my favorite topic is",
    "my favorite topics are",
    "my goal is",
    "my goals are",
    "my goals include",
    "i want to",
    "i'm trying to",
    "i'm working on",
    "i am working on",
    "i'm building",
    "i am building",
    "i'm balancing",
    "i am balancing",
    "my project is",
    "my projects are",
    "my projects include",
)

MEMORY_TRIGGER_TERMS = (
    "my name",
    "where do i live",
    "what do i like",
    "my preferences",
    "my goals",
    "what am i working on",
    "my projects",
    "what do you know about me",
    "what do you remember about me",
)

LOCATION_RELEVANCE_TERMS = (
    "weather",
    "forecast",
    "temperature",
    "near me",
    "nearby",
    "local",
    "commute",
    "travel",
    "trip",
    "vacation",
    "move",
    "moving",
    "relocate",
    "city",
    "area",
)

PREFERENCE_RELEVANCE_TERMS = (
    "recommend",
    "suggest",
    "idea",
    "ideas",
    "best",
    "favorite",
    "prefer",
    "like",
    "buy",
    "choose",
    "pick",
    "worth it",
    "should i",
)

GOAL_RELEVANCE_TERMS = (
    "goal",
    "goals",
    "focus",
    "this week",
    "priority",
    "priorities",
    "plan",
    "roadmap",
    "strategy",
    "next step",
    "next steps",
    "help me",
    "trying to",
    "want to",
    "build",
    "start",
    "grow",
    "improve",
    "launch",
)

PROJECT_RELEVANCE_TERMS = (
    "focus",
    "this week",
    "priority",
    "priorities",
    "project",
    "projects",
    "working on",
    "build",
    "launch",
    "ship",
    "test",
    "validate",
    "next step",
    "next steps",
)


def get_session_history(session_id: str, limit: int = MAX_HISTORY_MESSAGES) -> list[dict[str, Any]]:
    bounded_limit = max(1, min(limit, MAX_HISTORY_MESSAGES))
    return get_recent_messages(session_id, limit=bounded_limit)


def append_message(session_id: str, role: str, content: str, tool: str | None = None):
    add_message(session_id, role, content, tool)


def get_session_memory(session_id: str) -> dict[str, Any]:
    stored = get_session_facts(session_id)
    if not isinstance(stored, dict):
        stored = {}

    return {
        "name": str(stored.get("name") or "").strip(),
        "location": str(stored.get("location") or "").strip(),
        "preferences": _as_clean_list(stored.get("preferences")),
        "goals": _as_clean_list(stored.get("goals")),
        "projects": _as_clean_list(stored.get("projects")),
    }


def get_long_term_memory(user_id: str | None = None) -> dict[str, Any]:
    stored = get_long_term_facts(get_user_id(user_id))
    if not isinstance(stored, dict):
        stored = {}

    return {
        "name": str(stored.get("name") or "").strip(),
        "location": str(stored.get("location") or "").strip(),
        "preferences": _as_clean_list(stored.get("preferences")),
        "goals": _as_clean_list(stored.get("goals")),
        "projects": _as_clean_list(stored.get("projects")),
    }


def get_user_memory(session_id: str, user_id: str | None = None) -> dict[str, Any]:
    memory = get_long_term_memory(user_id)
    session_memory = get_session_memory(session_id)

    if session_memory.get("name"):
        memory["name"] = session_memory["name"]
    if session_memory.get("location"):
        memory["location"] = session_memory["location"]

    memory["preferences"] = _merge_unique(memory.get("preferences"), session_memory.get("preferences"))
    memory["goals"] = _merge_unique(memory.get("goals"), session_memory.get("goals"))
    memory["projects"] = _merge_unique(memory.get("projects"), session_memory.get("projects"))

    return memory


def update_user_memory(session_id: str, user_id: str | None, facts: dict[str, Any]) -> dict[str, Any]:
    memory = get_session_memory(session_id)

    name = str(facts.get("name") or "").strip()
    if name:
        memory["name"] = name

    location = str(facts.get("location") or "").strip()
    if location:
        memory["location"] = location
        set_last_weather_city(session_id, location)

    memory["preferences"] = _merge_unique(memory.get("preferences"), facts.get("preferences"))
    memory["goals"] = _merge_unique(memory.get("goals"), facts.get("goals"))
    memory["projects"] = _merge_unique(memory.get("projects"), facts.get("projects"))

    set_session_facts(session_id, memory)
    if facts:
        update_long_term_memory(get_user_id(user_id), {
            "name": memory.get("name"),
            "location": memory.get("location"),
            "preferences": memory.get("preferences"),
            "goals": memory.get("goals"),
            "projects": memory.get("projects"),
        })

    return get_user_memory(session_id, user_id)


def extract_user_memory(text: str) -> dict[str, Any]:
    cleaned = _clean_text(text)
    if not cleaned:
        return {}

    facts: dict[str, Any] = {}

    for pattern in NAME_PATTERNS:
        match = pattern.search(cleaned)
        if match:
            facts["name"] = _clean_fact_value(match.group(1))
            break

    for pattern in LOCATION_PATTERNS:
        match = pattern.search(cleaned)
        if match:
            facts["location"] = _clean_fact_value(match.group(1))
            break

    preferences: list[str] = []
    for pattern in PREFERENCE_PATTERNS:
        match = pattern.search(cleaned)
        if match:
            preferences.extend(_split_fact_list(match.group(1)))
            break

    goals: list[str] = []
    for pattern in GOAL_PATTERNS:
        match = pattern.search(cleaned)
        if match:
            goals.extend(_split_fact_list(match.group(1)))
            break

    projects: list[str] = []
    for pattern in PROJECT_PATTERNS:
        match = pattern.search(cleaned)
        if match:
            projects.extend(_split_fact_list(match.group(1)))
            break

    favorite_topics: list[str] = []
    for pattern in FAVORITE_TOPIC_PATTERNS:
        match = pattern.search(cleaned)
        if match:
            favorite_topics.extend(_split_fact_list(match.group(1)))
            break

    if preferences:
        facts["preferences"] = preferences

    if favorite_topics:
        facts["preferences"] = _merge_unique(facts.get("preferences"), favorite_topics)

    if goals:
        facts["goals"] = goals

    if projects:
        facts["projects"] = projects

    return {key: value for key, value in facts.items() if value}


def remember_user_message(session_id: str, text: str, user_id: str | None = None) -> dict[str, Any]:
    facts = extract_user_memory(text)
    if facts:
        update_user_memory(session_id, user_id, facts)
    return facts


def should_use_memory(question: str) -> bool:
    normalized = _clean_text(question).lower()
    return any(trigger in normalized for trigger in MEMORY_TRIGGER_TERMS)


def answer_memory_question(session_id: str, query: str, user_id: str | None = None) -> str | None:
    if not should_use_memory(query):
        return None

    normalized = _clean_text(query)
    memory = get_user_memory(session_id, user_id)

    if any(pattern.search(normalized) for pattern in NAME_QUESTION_PATTERNS):
        if memory.get("name"):
            return f"Your name is {memory['name']}."
        return "I don't know your name yet."

    if any(pattern.search(normalized) for pattern in LOCATION_QUESTION_PATTERNS):
        if memory.get("location"):
            return f"You live in {memory['location']}."
        return "I don't know where you live yet."

    if any(pattern.search(normalized) for pattern in PREFERENCE_QUESTION_PATTERNS):
        likes = _merge_unique(memory.get("preferences"), [])
        if likes:
            return f"You like {_join_human_list(likes)}."
        return "I don't know what you like yet."

    if any(pattern.search(normalized) for pattern in GOAL_QUESTION_PATTERNS):
        goals = _merge_unique(memory.get("goals"), [])
        if goals:
            return f"Your goals are {_join_human_list(goals)}."
        return "I don't know your goals yet."

    if any(pattern.search(normalized) for pattern in PROJECT_QUESTION_PATTERNS):
        projects = _merge_unique(memory.get("projects"), [])
        if projects:
            return f"You're working on {_join_human_list(projects)}."
        return "I don't know your current projects yet."

    if any(pattern.search(normalized) for pattern in PROFILE_QUESTION_PATTERNS):
        remembered_parts: list[str] = []
        if memory.get("name"):
            remembered_parts.append(f"your name is {memory['name']}")
        if memory.get("location"):
            remembered_parts.append(f"you live in {memory['location']}")
        if memory.get("preferences"):
            remembered_parts.append(f"you like {_join_human_list(memory['preferences'])}")
        if memory.get("goals"):
            remembered_parts.append(f"your goals are {_join_human_list(memory['goals'])}")
        if memory.get("projects"):
            remembered_parts.append(f"you're working on {_join_human_list(memory['projects'])}")

        if remembered_parts:
            return f"I know that {'; '.join(remembered_parts)}."
        return "I don't know much about you yet."

    return None


def is_memory_statement(text: str) -> bool:
    normalized = _clean_text(text).lower()
    if "?" in normalized:
        return False
    if any(term in normalized for term in ("help me", "what should", "be honest", "don't", "dont", "am i", "do i")):
        return False
    return normalized.startswith(MEMORY_STATEMENT_PREFIXES)


def build_memory_acknowledgement(facts: dict[str, Any]) -> str | None:
    if not facts:
        return None

    if facts.get("name") and facts.get("location"):
        return f"Got it, you're {facts['name']} and you're in {facts['location']}."

    if facts.get("name"):
        return f"Got it, you're {facts['name']}."

    if facts.get("location"):
        return f"Got it, you're in {facts['location']}."

    if facts.get("goals") or facts.get("projects"):
        return "I'll keep that in mind."

    if facts.get("preferences"):
        return "Okay."

    return None


def build_context(session_id: str, user_id: str | None = None) -> dict[str, Any]:
    resolved_user_id = get_user_id(user_id)
    return {
        "history": get_session_history(session_id, limit=MAX_HISTORY_MESSAGES),
        "session_facts": get_session_memory(session_id),
        "long_term_facts": get_long_term_memory(resolved_user_id),
    }


def build_user_memory_context(session_id: str, user_id: str | None = None) -> str:
    context = build_context(session_id, user_id)
    session_memory = context["session_facts"]
    long_term_memory = context["long_term_facts"]
    parts: list[str] = []

    session_parts: list[str] = []
    if session_memory.get("name"):
        session_parts.append(f"Name: {session_memory['name']}")
    if session_memory.get("location"):
        session_parts.append(f"Location: {session_memory['location']}")
    if session_memory.get("preferences"):
        session_parts.append(f"Preferences: {_join_human_list(session_memory['preferences'])}")
    if session_memory.get("goals"):
        session_parts.append(f"Goals: {_join_human_list(session_memory['goals'])}")
    if session_memory.get("projects"):
        session_parts.append(f"Projects: {_join_human_list(session_memory['projects'])}")

    long_term_parts: list[str] = []
    if long_term_memory.get("name"):
        long_term_parts.append(f"Name: {long_term_memory['name']}")
    if long_term_memory.get("location"):
        long_term_parts.append(f"Location: {long_term_memory['location']}")
    if long_term_memory.get("preferences"):
        long_term_parts.append(f"Preferences: {_join_human_list(long_term_memory['preferences'])}")
    if long_term_memory.get("goals"):
        long_term_parts.append(f"Goals: {_join_human_list(long_term_memory['goals'])}")
    if long_term_memory.get("projects"):
        long_term_parts.append(f"Projects: {_join_human_list(long_term_memory['projects'])}")

    if session_parts:
        parts.append(f"Session facts: {' | '.join(session_parts)}")
    if long_term_parts:
        parts.append(f"Long-term facts: {' | '.join(long_term_parts)}")

    return " | ".join(parts)


def build_relevant_user_memory_context(session_id: str, query: str, user_id: str | None = None) -> str:
    memory = get_user_memory(session_id, user_id)
    normalized_query = _clean_text(query).lower()
    if not normalized_query:
        return ""

    relevant_parts: list[str] = []

    if memory.get("name"):
        relevant_parts.append(f"Name: {memory['name']}")

    if memory.get("location") and any(term in normalized_query for term in LOCATION_RELEVANCE_TERMS):
        relevant_parts.append(f"Location: {memory['location']}")

    if memory.get("preferences") and any(term in normalized_query for term in PREFERENCE_RELEVANCE_TERMS):
        relevant_parts.append(f"Preferences: {_join_human_list(memory['preferences'])}")

    if memory.get("goals") and any(term in normalized_query for term in GOAL_RELEVANCE_TERMS):
        relevant_parts.append(f"Goals: {_join_human_list(memory['goals'])}")

    if memory.get("projects") and any(term in normalized_query for term in PROJECT_RELEVANCE_TERMS):
        relevant_parts.append(f"Projects: {_join_human_list(memory['projects'])}")

    return " | ".join(relevant_parts)


def remember_news_context(session_id: str, topic: str, query: str | None = None):
    cleaned_topic = _clean_fact_value(topic)
    if cleaned_topic:
        set_session_value(session_id, LAST_NEWS_TOPIC_KEY, cleaned_topic)

    cleaned_query = _clean_fact_value(query or "")
    if cleaned_query:
        set_session_value(session_id, LAST_NEWS_QUERY_KEY, cleaned_query)
    elif cleaned_topic:
        set_session_value(session_id, LAST_NEWS_QUERY_KEY, f"latest news about {cleaned_topic}")


def resolve_news_follow_up_query(session_id: str, query: str) -> str:
    cleaned_query = _clean_text(query)
    if get_last_tool(session_id) != "news":
        return query

    if not any(pattern.match(cleaned_query) for pattern in NEWS_FOLLOW_UP_PATTERNS):
        return query

    remembered_query = str(get_session_value(session_id, LAST_NEWS_QUERY_KEY, "") or "").strip()
    if remembered_query:
        return remembered_query

    remembered_topic = str(get_session_value(session_id, LAST_NEWS_TOPIC_KEY, "") or "").strip()
    if remembered_topic:
        return f"latest news about {remembered_topic}"

    return query


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def _clean_fact_value(value: str) -> str:
    cleaned = _clean_text(value).strip(" .,!?:;")
    cleaned = re.sub(r"\b(?:please|thanks|thank you)$", "", cleaned, flags=re.IGNORECASE).strip(" .,!?:;")
    return cleaned


def _split_fact_list(value: str) -> list[str]:
    cleaned = _clean_fact_value(value)
    if not cleaned:
        return []

    cleaned = re.sub(r"\b(?:a lot|the most|mostly)$", "", cleaned, flags=re.IGNORECASE).strip(" .,!?:;")
    parts = re.split(r",|\band\b|\+", cleaned, flags=re.IGNORECASE)
    return [part for part in (_clean_fact_value(item) for item in parts) if part]


def _as_clean_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in (_clean_fact_value(str(entry)) for entry in value) if item]


def _merge_unique(existing: Any, incoming: Any) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()

    for item in _as_clean_list(existing) + _as_clean_list(incoming):
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)

    return merged


def _join_human_list(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"