from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.logging import setup_logging
from app.routes.chat import router as chat_router
from app.routes.health import router as health_router


setup_logging()

# Print API keys (first 10 chars) for debugging
def _print_api_keys():
    print("OPENAI_API_KEY:", str(getattr(settings, 'openai_api_key', ''))[:10])
    print("SERPAPI_API_KEY:", str(getattr(settings, 'serpapi_api_key', ''))[:10])
    print("NEWS_API_KEY:", str(getattr(settings, 'news_api_key', ''))[:10])

_print_api_keys()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(chat_router)
app.include_router(health_router)