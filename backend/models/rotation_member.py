"""Osoba w kolejce rotacji szablonu serii (FR-7)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, SmallInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.task import Task
    from backend.models.user import User


class RotationMember(Base):
    __tablename__ = "rotation_members"
    __table_args__ = (UniqueConstraint("task_id", "user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    # Wyszukiwanie po task_id obsługuje indeks ograniczenia unikalności (task_id, user_id).
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(SmallInteger)

    task: Mapped[Task] = relationship(back_populates="rotation_members")
    user: Mapped[User] = relationship()

    def __repr__(self) -> str:
        return f"<RotationMember task={self.task_id} user={self.user_id} pos={self.position}>"
