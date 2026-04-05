from app.agents.base import BaseAgent
from app.services.external_service import get_weather

class WeatherAgent(BaseAgent):
    name = "weather"

    def run(self, session_id: str, user_input: str):
        return {"answer": get_weather(), "agent": self.name}

    def stream(self, session_id: str, user_input: str):
        yield get_weather()
