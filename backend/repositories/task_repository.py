"""Dostęp do zadań mieszkania."""

from __future__ import annotations

from sqlalchemy import update

from backend.models import Task, TaskStatus
from backend.repositories.base_repository import FlatScopedRepository


class TaskRepository(FlatScopedRepository[Task]):
    model = Task

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
