"""Dostęp do zadań mieszkania."""

from __future__ import annotations

from datetime import date
from typing import Literal

from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import joinedload

from backend.models import Recurrence, Task, TaskStatus
from backend.repositories.base_repository import FlatScopedRepository

TaskListFilter = Literal["all", "mine", "pool", "overdue", "done"]


class TaskRepository(FlatScopedRepository[Task]):
    model = Task

    def list_one_off(
        self, flat_id: int, list_filter: TaskListFilter, user_id: int
    ) -> list[Task]:
        statement = self._select().options(
            joinedload(Task.task_type),
            joinedload(Task.assignee),
        ).where(
            Task.flat_id == flat_id,
            Task.parent_task_id.is_(None),
            Task.recurrence == Recurrence.NONE,
        )
        if list_filter == "mine":
            statement = statement.where(
                Task.assignee_id == user_id,
                Task.status == TaskStatus.OPEN,
            )
        elif list_filter == "pool":
            statement = statement.where(
                Task.assignee_id.is_(None),
                Task.status == TaskStatus.OPEN,
            )
        elif list_filter == "overdue":
            statement = statement.where(
                Task.status == TaskStatus.OPEN,
                Task.due_date < date.today(),
            )
        elif list_filter == "done":
            statement = statement.where(Task.status == TaskStatus.DONE)
        statement = statement.order_by(Task.due_date, Task.id)
        return list(self._session.scalars(statement))

    def count_open(self, flat_id: int) -> int:
        """Niewykonane zadania do zrobienia (bez szablonów serii, które same nie są zadaniami)."""
        statement = select(func.count()).select_from(Task).where(
            Task.flat_id == flat_id,
            Task.status == TaskStatus.OPEN,
            or_(Task.parent_task_id.is_not(None), Task.recurrence == Recurrence.NONE),
        )
        return self._session.scalar(statement) or 0

    def unassign_open_tasks(self, flat_id: int, user_id: int) -> int:
        """Niewykonane zadania osoby wracają do puli; zwraca liczbę zmienionych zadań."""
        statement = (
            update(Task)
            .where(
                Task.flat_id == flat_id,
                Task.assignee_id == user_id,
                Task.status == TaskStatus.OPEN,
            )
            .values(assignee_id=None)
            .execution_options(synchronize_session="fetch")
        )
        return self._session.execute(statement).rowcount
