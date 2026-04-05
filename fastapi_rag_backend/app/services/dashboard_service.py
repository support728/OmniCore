import asyncio
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api", tags=["rag"])


# --- SIMPLE TEST FUNCTION (no AI yet) ---
def generate_dashboard_update(question: str) -> dict:
    return {
        "mode": "general",
        "answer": f"Nova received: {question}"
    }


# --- ROUTE ---
@router.post("/chat/dashboard-update")
async def chat_dashboard_update(payload: dict):
    print("ROUTE HIT")

    question = (payload.get("user_input") or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="user_input is required")

    try:
        result = await asyncio.to_thread(generate_dashboard_update, question)
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Dashboard update failed: {type(exc).__name__}"
        )