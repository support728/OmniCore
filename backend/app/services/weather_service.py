import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

WEATHER_SYSTEM_PROMPT = """
You are Amico AI weather service.

Your job:
- Answer weather questions using current web information.
- Give a direct weather summary first.
- Include location if known.
- Include temperature/conditions when available.
- If the user did not clearly provide a location, ask them which city or area they want.
- Do not make up weather data.
"""

def get_weather(query: str) -> str:
    if not os.getenv("OPENAI_API_KEY"):
        return "OPENAI_API_KEY is missing on the backend."

    cleaned_query = query.strip()
    if not cleaned_query:
        return "Please provide a weather question."

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            instructions=WEATHER_SYSTEM_PROMPT,
            tools=[{"type": "web_search"}],
            input=cleaned_query,
        )

        text = getattr(response, "output_text", None)
        if text and text.strip():
            return text.strip()

        return "I checked the weather, but I could not produce a response."
    except Exception as e:
        return f"Weather service failed: {str(e)}"