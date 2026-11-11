"""Użytkownik aplikacji."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from flask_login import UserMixin
from sqlalchemy import CheckConstraint, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from backend.core.constants import DISPLAY_NAME_MAX_LENGTH, EMAIL_MAX_LENGTH, USER_COLORS
from backend.models.base import Base, TimestampMixin
from backend.models.types import UTCDateTime
from backend.security.tokens import SESSION_TOKEN_LENGTH, new_session_token

if TYPE_CHECKING:
    from backend.models.membership import Membership


def normalize_email(email: str) -> str:
    return email.strip().lower()


class User(UserMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(f"color_index BETWEEN 0 AND {len(USER_COLORS) - 1}", name="color_index_range"),
        CheckConstraint("failed_logins >= 0", name="failed_logins_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(EMAIL_MAX_LENGTH), unique=True)
    display_name: Mapped[str] = mapped_column(String(DISPLAY_NAME_MAX_LENGTH))
    password_hash: Mapped[str] = mapped_column(String(255))
    color_index: Mapped[int] = mapped_column(SmallInteger, default=0)
    avatar_filename: Mapped[str | None] = mapped_column(String(64))
    session_token: Mapped[str] = mapped_column(
        String(SESSION_TOKEN_LENGTH), unique=True, default=new_session_token
    )
    failed_logins: Mapped[int] = mapped_column(default=0)
    locked_until: Mapped[datetime | None] = mapped_column(UTCDateTime())

    memberships: Mapped[list[Membership]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )

    @validates("email")
    def _normalize_email(self, _key: str, email: str) -> str:
        return normalize_email(email)

    @property
    def initials(self) -> str:
        """Dwie litery do awatara bez zdjęcia: inicjały imienia i nazwiska albo początek nazwy."""
        words = self.display_name.split()
        if not words:
            return "?"
        second = words[1][0] if len(words) > 1 else words[0][1:2]
        return (words[0][0] + second).upper()

    def get_id(self) -> str:
        """Flask-Login zapisuje w sesji token, a nie ID: zmiana tokenu unieważnia sesje (D-13)."""
        return self.session_token

    def rotate_session_token(self) -> None:
        self.session_token = new_session_token()

    def __repr__(self) -> str:
        return f"<User id={self.id}>"
