"""Zadanie: jednorazowe, szablon serii cyklicznej albo wystąpienie serii (sekcja 3 planu)."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.constants import (
    TASK_DESCRIPTION_MAX_LENGTH,
    TASK_POINTS_MAX,
    TASK_POINTS_MIN,
    TASK_TITLE_MAX_LENGTH,
)
from backend.models.base import Base, TimestampMixin
from backend.models.enums import AssignmentMode, Recurrence, TaskStatus
from backend.models.types import UTCDateTime, enum_column

if TYPE_CHECKING:
    from backend.models.flat import Flat
    from backend.models.rotation_member import RotationMember
    from backend.models.task_type import TaskType
    from backend.models.user import User


class Task(TimestampMixin, Base):
    """Rodzaj wiersza wynika z ``parent_task_id`` i ``recurrence``:

    - brak rodzica i ``recurrence = none`` – zadanie jednorazowe,
    - brak rodzica i ``recurrence != none`` – szablon serii (nie jest zadaniem do zrobienia),
    - rodzic ustawiony – wystąpienie serii o numerze ``occurrence_index``.
    """

    __tablename__ = "tasks"
    __table_args__ = (
        UniqueConstraint("parent_task_id", "occurrence_index"),
        CheckConstraint(f"points BETWEEN {TASK_POINTS_MIN} AND {TASK_POINTS_MAX}", name="points_range"),
        CheckConstraint(
            f"length(description) <= {TASK_DESCRIPTION_MAX_LENGTH}", name="description_length"
        ),
        CheckConstraint(
            "(status = 'done') = (done_at IS NOT NULL)", name="done_at_matches_status"
        ),
        CheckConstraint(
            "parent_task_id IS NULL OR recurrence = 'none'", name="occurrence_not_recurring"
        ),
        Index("ix_tasks_flat_id_due_date", "flat_id", "due_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Wyszukiwanie po flat_id obsługuje indeks złożony ix_tasks_flat_id_due_date.
    flat_id: Mapped[int] = mapped_column(ForeignKey("flats.id", ondelete="CASCADE"))
    task_type_id: Mapped[int] = mapped_column(ForeignKey("task_types.id"))
    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    # Usunięcie serii zostawia wykonane wystąpienia jako historię punktów.
    parent_task_id: Mapped[int | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"), index=True
    )
    occurrence_index: Mapped[int | None] = mapped_column()

    title: Mapped[str] = mapped_column(String(TASK_TITLE_MAX_LENGTH))
    description: Mapped[str] = mapped_column(Text, default="")
    due_date: Mapped[date] = mapped_column(Date)
    points: Mapped[int] = mapped_column(SmallInteger, default=10)
    status: Mapped[TaskStatus] = mapped_column(enum_column(TaskStatus, "task_status"), default=TaskStatus.OPEN)
    done_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    done_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    recurrence: Mapped[Recurrence] = mapped_column(
        enum_column(Recurrence, "task_recurrence"), default=Recurrence.NONE
    )
    assignment_mode: Mapped[AssignmentMode] = mapped_column(
        enum_column(AssignmentMode, "task_assignment_mode"), default=AssignmentMode.FIXED
    )

    flat: Mapped[Flat] = relationship(back_populates="tasks")
    task_type: Mapped[TaskType] = relationship()
    assignee: Mapped[User | None] = relationship(foreign_keys=[assignee_id])
    created_by: Mapped[User | None] = relationship(foreign_keys=[created_by_id])
    done_by: Mapped[User | None] = relationship(foreign_keys=[done_by_id])
    parent: Mapped[Task | None] = relationship(remote_side=[id], back_populates="occurrences")
    occurrences: Mapped[list[Task]] = relationship(back_populates="parent", passive_deletes=True)
    rotation_members: Mapped[list[RotationMember]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="RotationMember.position",
    )

    @property
    def is_template(self) -> bool:
        return self.parent_task_id is None and self.recurrence is not Recurrence.NONE

    @property
    def is_occurrence(self) -> bool:
        return self.parent_task_id is not None

    @property
    def is_done(self) -> bool:
        return self.status is TaskStatus.DONE

    def __repr__(self) -> str:
        return f"<Task id={self.id} flat={self.flat_id} {self.status}>"
