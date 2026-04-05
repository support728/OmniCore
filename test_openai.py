from fastapi_rag_backend.app.services.openai_client import client
from fastapi_rag_backend.app.config import settings

try:
    print("USING KEY:", settings.openai_api_key[:10])
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "say hello"}]
    )
    print("SUCCESS:", res.choices[0].message.content)
except Exception as e:
    print("ERROR:", e)