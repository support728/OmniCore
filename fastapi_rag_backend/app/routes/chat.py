from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json
from app.models.schemas import ChatRequest
from app.agents.router import get_agent

router = APIRouter(prefix="/api", tags=["chat"])
print("CHAT ENDPOINT HIT")
@router.post("/chat")
def chat(payload: ChatRequest):
    user_input = payload.user_input.strip()

    if not user_input:
        raise HTTPException(status_code=400, detail="Empty input")

    agent = get_agent(user_input)
    result = agent.run(payload.session_id, user_input)

    return {
        "answer": result["answer"],
        "session_id": payload.session_id,
        "agent": result["agent"],
        "results": result.get("results", []),
    }

@router.post("/chat/stream")
def chat_stream(payload: ChatRequest):
    user_input = payload.user_input.strip()

    if not user_input:
        raise HTTPException(status_code=400, detail="Empty input")

    agent = get_agent(user_input)

    def event_generator():
        for chunk in agent.stream(payload.session_id, user_input):
            yield f"data: {json.dumps({'token': chunk})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
