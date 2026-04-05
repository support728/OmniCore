from app.agents.base import BaseAgent
from app.services.external_service import get_time

class TimeAgent(BaseAgent):
    name = "time"

    def run(self, session_id: str, user_input: str):
        return {"answer": get_time(), "agent": self.name}

    def stream(self, session_id: str, user_input: str):
        yield get_time()
