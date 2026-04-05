
from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse

router = APIRouter()

from fastapi_rag_backend.app.services.openai_client import client
from fastapi_rag_backend.app.config import settings

# In-memory short-term chat history: {user_id: [msg, ...]}
chat_histories = {}

def _get_history(user_id):
    return chat_histories.get(user_id, [])

def _append_history(user_id, role, content):
    history = chat_histories.get(user_id, [])
    history.append({"role": role, "content": content})
    if len(history) > 5:
        history = history[-5:]
    chat_histories[user_id] = history

def _generate_dashboard_update(question: str, user_id: str) -> dict:
    try:
        # System prompt
        system_msg = {
            "role": "system",
            "content": (
                "You are Nova, an intelligent assistant. "
                "Respond clearly, directly, and helpfully. "
                "Avoid vague or generic answers. "
                "Give practical, understandable guidance."
            )
        }
        # Get last 5 messages (user+assistant) for this user
        history = _get_history(user_id)
        # Compose OpenAI input: [system, history..., current user]
        messages = [system_msg] + history + [{"role": "user", "content": question}]
        print("USING KEY:", settings.openai_api_key[:10])
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        answer = response.choices[0].message.content.strip()
        if not answer:
            answer = "I’m here. Ask me anything and I’ll help you step by step."
        # Update memory: add user and assistant messages
        _append_history(user_id, "user", question)
        _append_history(user_id, "assistant", answer)
        return {
            "mode": "general",
            "answer": answer
        }
    except Exception as e:
        return {
            "mode": "general",
            "answer": f"Error: {str(e)}"
        }
print("CHAT ENDPOINT HIT")
@router.post("/chat/dashboard-update")
async def chat_dashboard_update(payload: dict = Body(...)):
    question = payload.get("question") or payload.get("user_input")
    user_id = payload.get("user_id", "default")
    if not question:
        return JSONResponse({"mode": "general", "answer": "No question provided."}, status_code=400)
    result = _generate_dashboard_update(question, user_id)
    return JSONResponse(result)