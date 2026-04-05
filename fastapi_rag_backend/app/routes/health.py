from fastapi import APIRouter
from app.services.redis_memory import memory

router = APIRouter(tags=["health"])

@router.get("/health")
def health():
    try:
        memory.client.ping()
        redis_ok = True
    except Exception:
        redis_ok = False

    return {"ok": True, "redis": redis_ok}
