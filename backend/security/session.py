"""Sesja zalogowanego użytkownika (D-13, T-07)."""

from __future__ import annotations

from flask import session
from flask_login import login_user, logout_user

from backend.core.extensions import login_manager
from backend.models import User
from backend.repositories.user_repository import UserRepository
from backend.security.tokens import SESSION_TOKEN_LENGTH


def load_user(session_token: str) -> User | None:
    """Sesja przechowuje ``User.session_token``, a nie ID.

    Po wylogowaniu lub zmianie hasła token jest nowy, więc skopiowane
    wcześniej ciasteczko przestaje działać.
    """
    if len(session_token) != SESSION_TOKEN_LENGTH:
        return None
    return UserRepository().get_by_session_token(session_token)


def start_session(user: User) -> None:
    """Loguje użytkownika w nowej, czystej sesji.

    ``session.clear()`` usuwa wszystko, co było w sesji przed zalogowaniem
    (ochrona przed session fixation). Sesja trwa PERMANENT_SESSION_LIFETIME,
    bez „zapamiętaj mnie” (D-13).
    """
    session.clear()
    login_user(user, remember=False)
    session.permanent = True


def end_session() -> None:
    logout_user()
    session.clear()


def init_session() -> None:
    login_manager.user_loader(load_user)
