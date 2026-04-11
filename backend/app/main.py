
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import chat as chat_router

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

# Mount the new /api/chat endpoint
app.include_router(chat_router.router, prefix="/api")
