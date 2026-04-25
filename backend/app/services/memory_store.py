from typing import Any
from uuid import uuid4
import logging

from ..db import clear_user_memory, load_user_memory, save_user_memory


logger = logging.getLogger(__name__)


session_memory: dict[str, dict[str, Any]] = {}
MAX_SESSION_MESSAGES = 20
LONG_TERM_FACT_KEYS = {"name", "location", "preferences", "goals", "projects"}


def _create_session_bucket() -> dict[str, Any]:
    return {
        "history": [],
        "facts": {},
        "state": {},
    }

def _get_session_bucket(session_id: str, create: bool = False) -> dict[str, Any] | None:
    bucket = session_memory.get(session_id)
    if bucket is None and create:
        bucket = _create_session_bucket()
        session_memory[session_id] = bucket
    return bucket

def _normalize_bucket_list(bucket: dict[str, Any], key: str) -> list[Any]:
    value = bucket.get(key)
    if isinstance(value, list):
        return value

    bucket[key] = []
    return bucket[key]


def _normalize_bucket_dict(bucket: dict[str, Any], key: str) -> dict[str, Any]:
    value = bucket.get(key)
    if isinstance(value, dict):
        return value

    bucket[key] = {}
    return bucket[key]


def _cleanup_session_bucket(session_id: str):
    bucket = session_memory.get(session_id)
    if not bucket:
        return

    history = bucket.get("history")
    facts = bucket.get("facts")
    state = bucket.get("state")
    if not history and not facts and not state:
        session_memory.pop(session_id, None)


def create_session_id() -> str:
    return str(uuid4())


def get_user_id(user_id: str | None = None) -> str:
    cleaned_user_id = str(user_id or "").strip()
    return cleaned_user_id or "default_user"


def get_conversation(session_id: str):
    bucket = _get_session_bucket(session_id)
    if not bucket:
        return []
    return _normalize_bucket_list(bucket, "history")


def get_recent_messages(session_id: str, limit: int = 10):
    return get_conversation(session_id)[-limit:]


def add_message(session_id: str, role: str, content: str, tool: str | None = None):
    bucket = _get_session_bucket(session_id, create=True)
    history = _normalize_bucket_list(bucket, "history")

    message = {
        "role": role,
        "content": content,
    }
    if tool:
        message["tool"] = tool

    history.append(message)
    if len(history) > MAX_SESSION_MESSAGES:
        bucket["history"] = history[-MAX_SESSION_MESSAGES:]


def get_last_tool(session_id: str):
    for message in reversed(get_conversation(session_id)):
        tool = message.get("tool")
        if tool:
            return tool

    return None


def get_session_value(session_id: str, key: str, default=None):
    bucket = _get_session_bucket(session_id)
    if not bucket:
        return default
    return _normalize_bucket_dict(bucket, "state").get(key, default)


def set_session_value(session_id: str, key: str, value):
    bucket = _get_session_bucket(session_id, create=True)
    state = _normalize_bucket_dict(bucket, "state")
    state[key] = value


def get_session_facts(session_id: str) -> dict[str, Any]:
    bucket = _get_session_bucket(session_id)
    if not bucket:
        return {}
    return _normalize_bucket_dict(bucket, "facts")


def set_session_facts(session_id: str, facts: dict[str, Any]):
    bucket = _get_session_bucket(session_id, create=True)
    bucket["facts"] = dict(facts) if isinstance(facts, dict) else {}
    _cleanup_session_bucket(session_id)


def get_long_term_facts(user_id: str) -> dict[str, Any]:
    facts = load_user_memory(user_id)
    logger.info("Memory fetch user_id=%s keys=%s", user_id, sorted(facts.keys()))
    return facts


def update_long_term_memory(user_id: str, new_facts: dict[str, Any]):
    facts = get_long_term_facts(user_id)

    if not isinstance(new_facts, dict):
        return facts

    for key, value in new_facts.items():
        if key not in LONG_TERM_FACT_KEYS or value in (None, "", []):
            continue

        if isinstance(value, list):
            existing = facts.get(key)
            merged: list[Any] = []
            for item in (existing if isinstance(existing, list) else []) + value:
                if item not in merged:
                    merged.append(item)
            facts[key] = merged
            continue

        facts[key] = value

    save_user_memory(user_id, facts)
    logger.info("Memory save user_id=%s keys=%s", user_id, sorted(facts.keys()))
    return facts


def get_last_weather_city(session_id: str) -> str | None:
    value = get_session_value(session_id, "last_weather_city")
    return value if isinstance(value, str) and value else None


def set_last_weather_city(session_id: str, city: str):
    cleaned_city = (city or "").strip()
    if cleaned_city:
        set_session_value(session_id, "last_weather_city", cleaned_city)


def clear_conversation(session_id: str):
    bucket = _get_session_bucket(session_id)
    if not bucket:
        return

    bucket["history"] = []
    _cleanup_session_bucket(session_id)


def clear_session_values(session_id: str, keep_keys: set[str] | None = None):
    bucket = _get_session_bucket(session_id)
    if not bucket:
        return

    existing = _normalize_bucket_dict(bucket, "state")

    if not keep_keys:
        bucket["state"] = {}
        _cleanup_session_bucket(session_id)
        return

    bucket["state"] = {
        key: value
        for key, value in existing.items()
        if key in keep_keys
    }
    _cleanup_session_bucket(session_id)


def clear_session(session_id: str):
    session_memory.pop(session_id, None)


def reset_memory_store():
    session_memory.clear()
    clear_user_memory()