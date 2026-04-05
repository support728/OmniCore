from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_rag_backend.app.config import settings
from fastapi_rag_backend.app.models import UserAccount, UserSession


def _normalize_username(username: str) -> str:
    return (username or "").strip().lower()


def _password_hash(password: str, salt_hex: str) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        210_000,
    )
    return digest.hex()


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _new_salt() -> str:
    return secrets.token_hex(16)


def _new_token() -> str:
    return secrets.token_urlsafe(48)


def _validate_password_strength(password: str) -> None:
    if len(password) < settings.auth_min_password_length:
        raise ValueError(f"Password must be at least {settings.auth_min_password_length} characters long")


async def create_user_account(
    db: AsyncSession,
    username: str,
    password: str,
    display_name: str | None = None,
) -> UserAccount:
    normalized_username = _normalize_username(username)
    if not normalized_username:
        raise ValueError("Username is required")

    _validate_password_strength(password)

    existing = await db.execute(select(UserAccount).where(UserAccount.username == normalized_username))
    if existing.scalar_one_or_none() is not None:
        raise ValueError("Username is already in use")

    salt = _new_salt()
    row = UserAccount(
        username=normalized_username,
        password_salt=salt,
        password_hash=_password_hash(password, salt),
        display_name=(display_name or "").strip() or None,
        updated_at=datetime.utcnow(),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def authenticate_user_account(db: AsyncSession, username: str, password: str) -> UserAccount | None:
    normalized_username = _normalize_username(username)
    result = await db.execute(select(UserAccount).where(UserAccount.username == normalized_username))
    user = result.scalar_one_or_none()
    if user is None:
        return None

    expected = _password_hash(password, user.password_salt)
    if not hmac.compare_digest(expected, user.password_hash):
        return None

    user.last_login_at = datetime.utcnow()
    user.updated_at = datetime.utcnow()
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_user_session(db: AsyncSession, user_id: str) -> tuple[str, UserSession]:
    now = datetime.utcnow()
    token = _new_token()
    session = UserSession(
        user_id=uuid.UUID(user_id),
        token_hash=_token_hash(token),
        created_at=now,
        expires_at=now + timedelta(hours=settings.auth_session_ttl_hours),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return token, session


async def get_user_for_token(db: AsyncSession, token: str) -> UserAccount | None:
    now = datetime.utcnow()
    result = await db.execute(
        select(UserSession, UserAccount)
        .join(UserAccount, UserAccount.id == UserSession.user_id)
        .where(UserSession.token_hash == _token_hash(token))
        .where(UserSession.revoked_at.is_(None))
        .where(UserSession.expires_at > now)
    )
    row = result.first()
    if row is None:
        return None
    _, user = row
    return user


async def revoke_token(db: AsyncSession, token: str) -> bool:
    result = await db.execute(select(UserSession).where(UserSession.token_hash == _token_hash(token)))
    session = result.scalar_one_or_none()
    if session is None:
        return False

    if session.revoked_at is None:
        session.revoked_at = datetime.utcnow()
        db.add(session)
        await db.commit()
    return True


async def find_user_by_id(db: AsyncSession, user_id: str) -> UserAccount | None:
    result = await db.execute(select(UserAccount).where(UserAccount.id == uuid.UUID(user_id)))
    return result.scalar_one_or_none()


async def update_account_profile(
    db: AsyncSession,
    user_id: str,
    display_name: str | None,
) -> UserAccount | None:
    user = await find_user_by_id(db, user_id)
    if user is None:
        return None

    user.display_name = (display_name or "").strip() or None
    user.updated_at = datetime.utcnow()
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def change_account_password(
    db: AsyncSession,
    user_id: str,
    current_password: str,
    new_password: str,
) -> bool:
    user = await find_user_by_id(db, user_id)
    if user is None:
        return False

    expected = _password_hash(current_password, user.password_salt)
    if not hmac.compare_digest(expected, user.password_hash):
        return False

    _validate_password_strength(new_password)
    new_salt = _new_salt()
    user.password_salt = new_salt
    user.password_hash = _password_hash(new_password, new_salt)
    user.updated_at = datetime.utcnow()
    db.add(user)
    await db.commit()
    return True
