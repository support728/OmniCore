from app.agents.base import BaseAgent
from app.services.external_service import web_search

class WebAgent(BaseAgent):
    name = "web"

    def run(self, session_id: str, user_input: str):
        query = (
            user_input.lower()
            .replace("search", "")
            .replace("find", "")
            .replace("look up", "")
            .strip()
        )
        result = web_search(query)
        result["agent"] = self.name
        return result

    def stream(self, session_id: str, user_input: str):
        result = self.run(session_id, user_input)
        yield result["answer"]
