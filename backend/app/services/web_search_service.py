from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def search_web(query: str) -> str:
    query = (query or "").strip()

    if not query:
        return "Please enter a search query."

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            tools=[{"type": "web_search"}],
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are Amico AI.\n"
                        "Search the web and answer ONLY the user's query.\n\n"

                        "STRICT RULES:\n"
                        "- Answer must be MAX 2–3 short lines\n"
                        "- Then show EXACTLY 3 clean links\n"
                        "- No long paragraphs\n"
                        "- No extra explanations\n\n"

                        "FORMAT:\n"
                        "Answer: <short answer>\n\n"
                        "Links:\n"
                        "1. <title> - <url>\n"
                        "2. <title> - <url>\n"
                        "3. <title> - <url>"
                    ),
                },
                {
                    "role": "user",
                    "content": f"Search the web for: {query}",
                },
            ],
        )

        output_text = ""

        if hasattr(response, "output") and response.output:
            for item in response.output:
                if hasattr(item, "content") and item.content:
                    for part in item.content:
                        if hasattr(part, "text") and part.text:
                            output_text += part.text

        cleaned = output_text.strip()

        if not cleaned:
            return "No response found."

        return cleaned

    except Exception as e:
        return f"Web search failed: {str(e)}"