"""Mieszkanie, czyli odizolowana grupa użytkowników."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.constants import FLAT_NAME_MAX_LENGTH
from backend.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.models.invite import Invite
    from backend.models.membership import Membership
    from backend.models.task import Task
    from backend.models.task_type import TaskType


class Flat(TimestampMixin, Base):
    __tablename__ = "flats"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(FLAT_NAME_MAX_LENGTH))

    # Usunięcie mieszkania kasuje wszystko, co do niego należy (ON DELETE CASCADE w bazie).
    memberships: Mapped[list[Membership]] = relationship(
        back_populates="flat", cascade="all, delete-orphan", passive_deletes=True
    )
    invites: Mapped[list[Invite]] = relationship(
        back_populates="flat", cascade="all, delete-orphan", passive_deletes=True
    )
    task_types: Mapped[list[TaskType]] = relationship(
        back_populates="flat", cascade="all, delete-orphan", passive_deletes=True
    )
    tasks: Mapped[list[Task]] = relationship(
        back_populates="flat", cascade="all, delete-orphan", passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"<Flat id={self.id}>"
