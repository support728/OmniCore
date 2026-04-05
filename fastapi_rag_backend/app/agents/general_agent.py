from app.agents.base import BaseAgent
from app.services.openai_service import chat_with_memory, stream_chat_with_memory

class GeneralAgent(BaseAgent):
    name = "general"

    def run(self, session_id: str, user_input: str):
        return {"answer": chat_with_memory(session_id, user_input), "agent": self.name}

    def stream(self, session_id: str, user_input: str):
        return stream_chat_with_memory(session_id, user_input)
