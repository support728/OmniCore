from app.agents.base import BaseAgent
from app.services.external_service import get_identity

class IdentityAgent(BaseAgent):
    name = "identity"

    def run(self, session_id: str, user_input: str):
        return {"answer": get_identity(), "agent": self.name}

    def stream(self, session_id: str, user_input: str):
        yield get_identity()
