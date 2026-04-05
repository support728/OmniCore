from collections.abc import Generator
from fastapi_rag_backend.app.services.openai_client import client
from fastapi_rag_backend.app.config import settings
from app.memory.redis_store import memory_store

def build_messages(session_id: str, user_input: str):
    return [
        {"role": "system", "content": "you are Nova, a smart AI assistant. Answer the user's question based on your knowledge and any provided context."}
    ]
     
    history = memory_store.get_messages(session_id)


def chat_with_memory(session_id: str, user_input: str) -> str:
    messages = build_messages(session_id, user_input)

    print("USING KEY:", settings.openai_api_key[:10])
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
    )

    answer = response.choices[0].message.content.strip()

    memory_store.add_message(session_id, "user", user_input)
    memory_store.add_message(session_id, "assistant", answer)

    return answer

def stream_chat_with_memory(session_id: str, user_input: str) -> Generator[str, None, None]:
    messages = build_messages(session_id, user_input)

    print("USING KEY:", settings.openai_api_key[:10])
    stream = client.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
        stream=True,
    )

    full_answer = []

    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if delta:
            full_answer.append(delta)
            yield delta

    final_answer = "".join(full_answer).strip()

    memory_store.add_message(session_id, "user", user_input)
    memory_store.add_message(session_id, "assistant", final_answer)
