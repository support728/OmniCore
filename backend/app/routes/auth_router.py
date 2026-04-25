import sqlite3
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from ..auth import create_token, hash_password, verify_password
from ..db import DB_PATH


router = APIRouter()


class AuthPayload(BaseModel):
    full_name: Optional[str] = None
    email: str
    password: str


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _get_auth_user_by_email(email: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id, email, password_hash FROM auth_users WHERE email = ?",
            (_normalize_email(email),),
        ).fetchone()

    return row


@router.post("/signup")
def signup(payload: AuthPayload):
    email = _normalize_email(payload.email)
    password = payload.password.strip()

    if len(password) < 6:
        return {
            "success": False,
            "message": "Password must be at least 6 characters.",
        }

    if _get_auth_user_by_email(email):
        return {
            "success": False,
            "message": "User already exists",
        }

    password_hash = hash_password(password)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO auth_users (email, password_hash) VALUES (?, ?)",
            (email, password_hash),
        )
        conn.commit()
        user_id = int(cursor.lastrowid)

    return {
        "success": True,
        "message": "Account created",
    }


@router.post("/login")
def login(payload: AuthPayload):
    email = _normalize_email(payload.email)
    user = _get_auth_user_by_email(email)

    if not user:
        return {
            "success": False,
            "message": "User not found",
        }

    if not verify_password(payload.password, str(user["password_hash"])):
        return {
            "success": False,
            "message": "Wrong password",
        }

    user_id = int(user["id"])
    token = create_token({"user_id": user_id, "email": email})
    return {
        "success": True,
        "token": token,
        "email": email,
    }