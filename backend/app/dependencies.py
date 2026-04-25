import sqlite3

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .auth import decode_token
from .db import DB_PATH


security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


def _lookup_auth_user(user_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id, email FROM auth_users WHERE id = ?",
            (user_id,),
        ).fetchone()

    if not row:
        return None

    return {
        "id": int(row["id"]),
        "email": str(row["email"]),
    }


def _decode_user_from_credentials(credentials: HTTPAuthorizationCredentials | None):
    if credentials is None:
        return None

    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id = payload.get("user_id")
    except Exception as error:
        raise HTTPException(status_code=401, detail="Invalid token") from error

    if not isinstance(user_id, int):
        raise HTTPException(status_code=401, detail="Invalid token")

    user = _lookup_auth_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return _decode_user_from_credentials(credentials)


def get_optional_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(optional_security)):
    return _decode_user_from_credentials(credentials)
