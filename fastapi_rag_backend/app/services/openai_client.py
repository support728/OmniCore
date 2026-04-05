from openai import OpenAI
from fastapi_rag_backend.app.config import settings

client = OpenAI(api_key=settings.openai_api_key)
