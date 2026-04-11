import httpx
from app.core.config import get_settings

def build_async_client():
	settings = get_settings()
	headers = {"User-Agent": "OmniCoreBot/1.0"}
	return httpx.AsyncClient(timeout=10, headers=headers)
