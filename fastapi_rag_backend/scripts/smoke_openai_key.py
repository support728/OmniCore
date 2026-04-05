import os
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def main() -> int:
    mode = (sys.argv[1] if len(sys.argv) > 1 else "current").strip().lower()

    if mode == "invalid":
        os.environ["OPENAI_API_KEY"] = "bad-key"

    from app.services.embeddings import _get_client

    print(f"mode={mode}")
    print(f"key_present={bool(os.getenv('OPENAI_API_KEY'))}")

    try:
        _get_client()
        print("CLIENT_INIT_SUCCESS")
        return 0
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
