from fastapi_rag_backend.app.services.openai_client import client
from fastapi_rag_backend.app.config import settings

AVAILABLE_AGENTS = [
    "weather",
    "news",
    "web",
    "time",
    "identity",
    "general"
]
print("CHOOSING AGENT")
def choose_agent(user_input: str) -> str:
    prompt = f"""
You are a routing system.

User input:
"{user_input}"

Choose the best agent from:
{AVAILABLE_AGENTS}

Rules:
- Return ONLY the agent name
- No explanation

Example:
weather
"""

    print("USING KEY:", settings.openai_api_key[:10])
    print("CALLING OPENAI NOW")
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": prompt}],
    )

    agent = response.choices[0].message.content.strip().lower()

    if agent not in AVAILABLE_AGENTS:
        return "general"

    return agent
