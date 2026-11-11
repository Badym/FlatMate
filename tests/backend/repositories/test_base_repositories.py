"""Repozytoria bazowe, sprawdzane na tymczasowym modelu testowym."""

from __future__ import annotations

from flask import Flask
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.extensions import db
from backend.models.base import Base
from backend.repositories import FlatScopedRepository, Repository


class Note(Base):
    __tablename__ = "test_note"

    id: Mapped[int] = mapped_column(primary_key=True)
    flat_id: Mapped[int] = mapped_column()
    body: Mapped[str] = mapped_column(String(50))


class NoteRepository(Repository[Note]):
    model = Note


class FlatNoteRepository(FlatScopedRepository[Note]):
    model = Note


def test_repository_crud(app: Flask) -> None:
    with app.app_context():
        repository = NoteRepository()
        note = repository.add(Note(flat_id=1, body="pierwsza"))
        repository.flush()

        assert repository.get(note.id) is note
        assert repository.list(Note.body == "pierwsza") == [note]

        repository.delete(note)
        repository.flush()

        assert repository.get(note.id) is None


def test_flat_scoped_repository_filters_by_flat(app: Flask) -> None:
    with app.app_context():
        repository = FlatNoteRepository()
        own = repository.add(Note(flat_id=1, body="moja"))
        foreign = repository.add(Note(flat_id=2, body="cudza"))
        repository.flush()

        assert repository.get_in_flat(1, own.id) is own
        assert repository.get_in_flat(1, foreign.id) is None
        assert repository.list_in_flat(1) == [own]
        assert not hasattr(repository, "get")

