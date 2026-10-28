"""Dostęp do zadań mieszkania."""

from __future__ import annotations

from sqlalchemy import func, or_, select, update

from backend.models import Recurrence, Task, TaskStatus
from backend.repositories.base_repository import FlatScopedRepository


class TaskRepository(FlatScopedRepository[Task]):
    model = Task

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
