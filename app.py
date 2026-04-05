from importlib import import_module
from pathlib import Path

BACKEND_APP_DIR = Path(__file__).resolve().parent / "fastapi_rag_backend" / "app"

# Expose this module as a package root for the backend so imports like
# `from app.api.routes import ...` continue to work when the server starts via
# `uvicorn run:app` from the repository root.
__path__ = [str(BACKEND_APP_DIR)]

app = import_module("app.main").app
