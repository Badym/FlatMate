"""Dostęp do typów zadań: globalnych i własnych typów mieszkania."""

from __future__ import annotations

from sqlalchemy import or_

from backend.models import TaskType
from backend.repositories.base_repository import Repository


class TaskTypeRepository(Repository[TaskType]):
    """Typy globalne (``flat_id IS NULL``) są wspólne, więc to nie jest FlatScopedRepository.

    Typ z formularza zawsze pobieramy przez ``get_available``: typ innego
    mieszkania jest dla tego mieszkania niewidoczny (T-01).
    """

    model = TaskType

    def list_available(self, flat_id: int) -> list[TaskType]:
        statement = (
            self._select()
            .where(or_(TaskType.flat_id.is_(None), TaskType.flat_id == flat_id))
            .order_by(TaskType.flat_id.is_not(None), TaskType.name)
        )
        return list(self._session.scalars(statement))

    def get_available(self, flat_id: int, task_type_id: int) -> TaskType | None:
        statement = self._select().where(
            TaskType.id == task_type_id,
            or_(TaskType.flat_id.is_(None), TaskType.flat_id == flat_id),
        )
        return self._session.scalars(statement).first()
