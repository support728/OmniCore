from fastapi_rag_backend.app.services.openai_client import client
from fastapi_rag_backend.app.config import settings

try:
    print("USING KEY:", settings.openai_api_key[:10])
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say hello from OpenAI."}]
    )
    print(response.choices[0].message.content)
except Exception as e:
    print(f"ERROR: {e}")
