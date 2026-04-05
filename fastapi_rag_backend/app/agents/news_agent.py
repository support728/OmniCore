from app.agents.base import BaseAgent
from app.services.external_service import get_news

class NewsAgent(BaseAgent):
    name = "news"

    def run(self, session_id: str, user_input: str):
        return {"answer": get_news(), "agent": self.name}

    def stream(self, session_id: str, user_input: str):
        yield get_news()
