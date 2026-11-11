"""Hashowanie i weryfikacja haseł (SR-1, T-03, T-04)."""

from __future__ import annotations

import secrets
from functools import cache

from werkzeug.security import check_password_hash, generate_password_hash

from backend.core.constants import PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH


class PasswordPolicyError(ValueError):
    """Hasło nie spełnia wymagań długości."""


def hash_password(password: str) -> str:
    """Hash z solą (scrypt z werkzeug). Długość sprawdza też formularz; tu to druga linia obrony."""
    if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
        raise PasswordPolicyError(
            f"Hasło musi mieć od {PASSWORD_MIN_LENGTH} do {PASSWORD_MAX_LENGTH} znaków."
        )
    return generate_password_hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    """Sprawdza hasło w podobnym czasie niezależnie od tego, czy konto istnieje.

    Dla nieistniejącego konta (``password_hash is None``) liczymy hash atrapy,
    żeby czas odpowiedzi nie zdradzał, które adresy e-mail są zarejestrowane.
    """
    if password_hash is None:
        check_password_hash(_dummy_hash(), password)
        return False
    return check_password_hash(password_hash, password)


@cache
def _dummy_hash() -> str:
    return generate_password_hash(secrets.token_hex(16))
