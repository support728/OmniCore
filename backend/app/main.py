from app.db import init_db, get_db
import atexit
init_db()




from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChatRequest(BaseModel):
    user_id: str
    message: str

app = FastAPI()

# Allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for now, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"status": "ok"}


# /chat endpoint

@app.post("/chat")
def chat(request: ChatRequest):
    from app.db import get_db
    system_prompt = {"role": "system", "content": "You are OmniCore AI."}
    with get_db() as conn:
        c = conn.cursor()
        # Ensure user exists
        c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (request.user_id,))
        # Find or create conversation for user (latest open conversation)
        c.execute("SELECT id FROM conversations WHERE user_id=? ORDER BY created_at DESC LIMIT 1", (request.user_id,))
        row = c.fetchone()
        if row:
            conversation_id = row[0]
        else:
            c.execute("INSERT INTO conversations (user_id) VALUES (?)", (request.user_id,))
            conversation_id = c.lastrowid
        # Load all messages for this conversation
        c.execute("SELECT role, content FROM messages WHERE conversation_id=? ORDER BY id ASC", (conversation_id,))
        messages = c.fetchall()
        chat_history = [system_prompt] if not messages else [system_prompt] + [{"role": r, "content": m} for r, m in messages]
        # Add user message
        chat_history.append({"role": "user", "content": request.message})
        # Call OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=chat_history
        )
        reply = response.choices[0].message.content
        # Save user message
        c.execute("INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)", (conversation_id, "user", request.message))
        # Save assistant reply
        c.execute("INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)", (conversation_id, "assistant", reply))
        conn.commit()
    return {"response": reply}
