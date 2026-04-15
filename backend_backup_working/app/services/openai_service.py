import os
import json
from openai import OpenAI

# Get project root (OmniCore)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
MEMORY_FILE = os.path.join(BASE_DIR, "memory.json")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ---------------- MEMORY ---------------- #

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f)


# ---------------- AI RESPONSE ---------------- #

async def get_ai_response(message: str) -> str:
    try:
        # ✅ Ensure message is always a string
        if isinstance(message, list):
            message = " ".join(message)

        memory = load_memory()

        # ✅ Save user name if provided
        if "my name is" in message.lower():
            name = message.split("is")[-1].strip()
            memory["name"] = name
            save_memory(memory)

        system_prompt = "You are Amico, a helpful AI assistant."

        # Optional personalization
        if "name" in memory:
            system_prompt += f" The user's name is {memory['name']}."

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        print("🔥 OPENAI ERROR:", repr(e))
        return f"ERROR: {str(e)}"