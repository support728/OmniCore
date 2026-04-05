from collections import defaultdict
from threading import Lock

class SessionMemoryStore:
    def __init__(self, max_messages: int = 20):
        self._store = defaultdict(list)
        self._lock = Lock()
        self._max_messages = max_messages

    def get_messages(self, session_id: str) -> list[dict]:
        with self._lock:
            return list(self._store[session_id])

    def add_message(self, session_id: str, role: str, content: str) -> None:
        with self._lock:
            self._store[session_id].append({"role": role, "content": content})
            self._store[session_id] = self._store[session_id][-self._max_messages:]

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._store[session_id] = []

memory_store = SessionMemoryStore()
