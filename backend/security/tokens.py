"""Losowe tokeny i ich skróty (SR-8, D-13)."""

from __future__ import annotations

import hashlib
import secrets

SESSION_TOKEN_LENGTH = 64  # znaki szesnastkowe = 256 bitów
INVITE_TOKEN_BYTES = 32  # 256 bitów (T-08)


def new_session_token() -> str:
    """Token sesji zwracany przez User.get_id(); nowy przy wylogowaniu i zmianie hasła."""
    return secrets.token_hex(SESSION_TOKEN_LENGTH // 2)


def new_invite_token() -> str:
    """Token do linku zaproszenia. W bazie zapisujemy wyłącznie jego skrót."""
    return secrets.token_urlsafe(INVITE_TOKEN_BYTES)


def hash_token(token: str) -> str:
    """SHA-256 tokenu; wyciek bazy nie ujawnia działających linków."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
