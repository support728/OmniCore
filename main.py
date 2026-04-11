
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel



app = FastAPI(
    title="Amico Backend",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Optional root route
@app.get("/")
def root():
    return {"status": "ok"}


# ChatRequest model
class ChatRequest(BaseModel):
    message: str

# /chat endpoint
@app.post("/chat")
def chat(request: ChatRequest):
    return {
        "response": f"You said: {request.message}"
    }

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow frontend (localhost:5174)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

