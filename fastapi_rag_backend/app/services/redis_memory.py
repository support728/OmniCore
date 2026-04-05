import json
import redis
from app.core.config import settings

class RedisMemory:
    def __init__(self) -> None:
        self.client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

    def _key(self, session_id: str) -> str:
        return f"chat:session:{session_id}"

    def get_messages(self, session_id: str) -> list[dict]:
        raw = self.client.get(self._key(session_id))
        return json.loads(raw) if raw else []

    def save_messages(self, session_id: str, messages: list[dict]) -> None:
        trimmed = messages[-settings.MEMORY_MAX_MESSAGES :]
        self.client.set(self._key(session_id), json.dumps(trimmed))

    def append_message(self, session_id: str, role: str, content: str) -> None:
        messages = self.get_messages(session_id)
        messages.append({"role": role, "content": content})
        self.save_messages(session_id, messages)

    def clear(self, session_id: str) -> None:
        self.client.delete(self._key(session_id))

memory = RedisMemory()
