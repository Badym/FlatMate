"""Konta użytkowników: rejestracja, logowanie z blokadą konta, wylogowanie, zmiana hasła.

Serwis zmienia tylko dane w bazie. Sesją HTTP (``session``, Flask-Login)
zajmują się kontrolery przez ``security.session``.
"""

from __future__ import annotations

import secrets
from datetime import timedelta

from sqlalchemy.exc import IntegrityError

from backend.audit import audit_event
from backend.core.constants import LOGIN_LOCK_MINUTES, LOGIN_MAX_FAILURES, USER_COLORS
from backend.core.extensions import db
from backend.models import User
from backend.models.types import utcnow
from backend.repositories import UserRepository
from backend.security.passwords import hash_password, verify_password

# Jeden komunikat dla złego hasła, nieznanego e-maila i zablokowanego konta (SR-2).
LOGIN_FAILED_MESSAGE = "Nieprawidłowy e-mail lub hasło."


class EmailTakenError(Exception):
    """Na ten adres jest już konto (enumeracja przy rejestracji to ryzyko przyjęte w D-14)."""


class InvalidCurrentPasswordError(Exception):
    pass


class SamePasswordError(Exception):
    pass


class AuthService:
    def __init__(self, users: UserRepository | None = None) -> None:
        self._users = users or UserRepository()

    def register(self, *, display_name: str, email: str, password: str) -> User:
        if self._users.get_by_email(email) is not None:
            raise EmailTakenError
        user = self._users.add(
            User(
                email=email,
                display_name=display_name.strip(),
                password_hash=hash_password(password),
                color_index=secrets.randbelow(len(USER_COLORS)),
            )
        )
        try:
            db.session.commit()
        except IntegrityError as exc:
            # Dwie równoległe rejestracje na ten sam adres: wygrywa pierwsza.
            db.session.rollback()
            raise EmailTakenError from exc
        audit_event("user_registered", target_user_id=user.id)
        return user

    def authenticate(self, email: str, password: str) -> User | None:
        """Zwraca użytkownika albo ``None``; przyczyny niepowodzenia trafiają tylko do dziennika.

        Hasło jest sprawdzane zawsze, także dla nieistniejącego lub
        zablokowanego konta, żeby czas odpowiedzi niczego nie zdradzał.
        """
        user = self._users.get_by_email(email)
        password_ok = verify_password(user.password_hash if user else None, password)
        now = utcnow()

        if user is None:
            audit_event("login_failed", reason="unknown_account")
            return None
        if user.locked_until is not None and user.locked_until > now:
            audit_event("login_failed", reason="account_locked", target_user_id=user.id)
            return None
        if not password_ok:
            self._register_failure(user)
            return None

        user.failed_logins = 0
        user.locked_until = None
        db.session.commit()
        audit_event("login_success", target_user_id=user.id)
        return user

    def _register_failure(self, user: User) -> None:
        user.failed_logins += 1
        if user.failed_logins >= LOGIN_MAX_FAILURES:
            user.locked_until = utcnow() + timedelta(minutes=LOGIN_LOCK_MINUTES)
            user.failed_logins = 0
            audit_event("account_locked", target_user_id=user.id, minutes=LOGIN_LOCK_MINUTES)
        db.session.commit()
        audit_event("login_failed", reason="wrong_password", target_user_id=user.id)

    def logout(self, user: User) -> None:
        """Nowy token sesji: skopiowane wcześniej ciasteczko przestaje działać (D-13)."""
        audit_event("logout")
        user.rotate_session_token()
        db.session.commit()

    def change_password(self, user: User, current_password: str, new_password: str) -> None:
        """Po zmianie wszystkie sesje tego konta wygasają; kontroler loguje bieżącą od nowa."""
        if not verify_password(user.password_hash, current_password):
            audit_event("password_change_failed", reason="wrong_current_password")
            raise InvalidCurrentPasswordError
        if verify_password(user.password_hash, new_password):
            raise SamePasswordError
        user.password_hash = hash_password(new_password)
        user.rotate_session_token()
        db.session.commit()
        audit_event("password_changed")
