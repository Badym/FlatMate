"""Dostęp do użytkowników."""

from __future__ import annotations

from backend.models import User
from backend.models.user import normalize_email
from backend.repositories.base_repository import Repository


class UserRepository(Repository[User]):
    model = User

    def get_by_email(self, email: str) -> User | None:
        statement = self._select().where(User.email == normalize_email(email))
        return self._session.scalars(statement).first()

    def get_by_session_token(self, session_token: str) -> User | None:
        statement = self._select().where(User.session_token == session_token)
        return self._session.scalars(statement).first()
