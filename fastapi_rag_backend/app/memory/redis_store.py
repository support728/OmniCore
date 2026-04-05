import json
import redis
from app.core.config import settings

class RedisMemoryStore:
    def __init__(self):
        try:
            client = redis.Redis(
                host="localhost",
                port=6379,
                decode_responses=True
            )
            client.ping()
            self.client = client
        except Exception:
            self.client = None
        self.max_messages = 20

    def _key(self, session_id: str):
        return f"chat:{session_id}"

    def get_messages(self, session_id: str):
        if self.client is None:
            return []
        data = self.client.get(self._key(session_id))
        return json.loads(data) if data else []

    def add_message(self, session_id: str, role: str, content: str):
        if self.client is None:
            return
        messages = self.get_messages(session_id)
        messages.append({"role": role, "content": content})
        messages = messages[-self.max_messages:]
        self.client.set(self._key(session_id), json.dumps(messages))

    def clear(self, session_id: str):
        if self.client is None:
            return
        self.client.delete(self._key(session_id))

memory_store = RedisMemoryStore()
