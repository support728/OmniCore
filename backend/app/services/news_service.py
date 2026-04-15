import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

NEWS_SYSTEM_PROMPT = """
You are Amico AI news service.

Your job:
- Answer news questions using current web information.
- Give a clear summary of the latest relevant news.
- If the user asks for general news, provide major current headlines.
- If the user asks about a topic, company, person, or place, focus on that.
- Keep the response practical and easy to read.
- Do not make up news.
"""

def get_news(query: str = "latest news") -> str:
    if not os.getenv("OPENAI_API_KEY"):
        return "OPENAI_API_KEY is missing on the backend."

    cleaned_query = query.strip() if query else "latest news"
    if not cleaned_query:
        cleaned_query = "latest news"

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            instructions=NEWS_SYSTEM_PROMPT,
            tools=[{"type": "web_search"}],
            input=cleaned_query,
        )

        text = getattr(response, "output_text", None)
        if text and text.strip():
            return text.strip()

        return "I checked the news, but I could not produce a response."
    except Exception as e:
        return f"News service failed: {str(e)}"