from app.agents.general_agent import GeneralAgent
from app.agents.weather_agent import WeatherAgent
from app.agents.news_agent import NewsAgent
from app.agents.web_agent import WebAgent
from app.agents.time_agent import TimeAgent
from app.agents.identity_agent import IdentityAgent
from app.agents.supervisor_agent import choose_agent

AGENTS = {
    "general": GeneralAgent(),
    "weather": WeatherAgent(),
    "news": NewsAgent(),
    "web": WebAgent(),
    "time": TimeAgent(),
    "identity": IdentityAgent(),
}

def get_agent(user_input: str):
    agent_name = choose_agent(user_input)
    return AGENTS[agent_name]
