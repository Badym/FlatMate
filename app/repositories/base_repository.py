"""Klasy bazowe repozytoriów."""

from __future__ import annotations

from typing import Any, ClassVar, Generic, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, scoped_session

from app.extensions import db
from app.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class _BaseRepository(Generic[ModelT]):
    """Operacje wspólne dla wszystkich repozytoriów."""

    model: ClassVar[type[Any]]

    def __init__(self, session: Session | scoped_session[Session] | None = None) -> None:
        self._session = session if session is not None else db.session

    def add(self, entity: ModelT) -> ModelT:
        self._session.add(entity)
        return entity

    def delete(self, entity: ModelT) -> None:
        self._session.delete(entity)

    def flush(self) -> None:
        self._session.flush()

    def _select(self) -> Select[tuple[ModelT]]:
        return select(self.model)


class Repository(_BaseRepository[ModelT]):
    """Repozytorium zasobów globalnych (np. użytkownicy, mieszkania)."""

    def get(self, entity_id: int) -> ModelT | None:
        return self._session.get(self.model, entity_id)

    def list(self, *criteria: Any) -> list[ModelT]:
        return list(self._session.scalars(self._select().where(*criteria)))


class FlatScopedRepository(_BaseRepository[ModelT]):
    """Repozytorium zasobów należących do mieszkania (zadania, zaproszenia…).

    Celowo nie ma metody ``get(id)``: każde zapytanie wymaga ``flat_id``,
    więc podmiana identyfikatora w adresie URL nie da dostępu do cudzego
    mieszkania (T-01).
    """

    def get_in_flat(self, flat_id: int, entity_id: int) -> ModelT | None:
        statement = self._select().where(self.model.id == entity_id, self.model.flat_id == flat_id)
        return self._session.scalars(statement).first()

    def list_in_flat(self, flat_id: int, *criteria: Any) -> list[ModelT]:
        statement = self._select().where(self.model.flat_id == flat_id, *criteria)
        return list(self._session.scalars(statement))
