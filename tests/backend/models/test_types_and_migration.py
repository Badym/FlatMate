"""Własne typy kolumn oraz zgodność pierwszej migracji z modelami."""

from __future__ import annotations

import importlib.util
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy.exc import StatementError

from backend.core.extensions import MIGRATIONS_DIR, db
from backend.models import User
from backend.models.task_type import DEFAULT_TASK_TYPES
from backend.models.types import UTCDateTime, render_alembic_type


def test_datetime_is_stored_and_read_as_utc(make_user) -> None:
    warsaw = timezone(timedelta(hours=2))
    user = make_user(locked_until=datetime(2026, 10, 23, 12, 0, tzinfo=warsaw))
    db.session.expire_all()

    locked_until = db.session.get(User, user.id).locked_until

    assert locked_until == datetime(2026, 10, 23, 10, 0, tzinfo=UTC)
    assert locked_until.tzinfo is UTC


def test_naive_datetime_is_rejected(make_user) -> None:
    with pytest.raises(StatementError, match="strefę czasową"):
        make_user(locked_until=datetime(2026, 10, 23, 12, 0))
    db.session.rollback()


def test_alembic_renders_plain_datetime() -> None:
    assert render_alembic_type("type", UTCDateTime(), None) == "sa.DateTime(timezone=True)"
    assert render_alembic_type("type", object(), None) is False


def _initial_migration():
    path = next(Path(MIGRATIONS_DIR, "versions").glob("*_schemat_poczatkowy.py"))
    spec = importlib.util.spec_from_file_location("initial_migration", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migration_default_task_types_match_model() -> None:
    assert list(_initial_migration().DEFAULT_TASK_TYPES) == [dict(row) for row in DEFAULT_TASK_TYPES]


def test_migration_does_not_import_application_code() -> None:
    path = next(Path(MIGRATIONS_DIR, "versions").glob("*_schemat_poczatkowy.py"))

    assert "backend" not in path.read_text(encoding="utf-8")
