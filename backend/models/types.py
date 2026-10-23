"""Własne typy kolumn wspólne dla modeli."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import DateTime, Dialect
from sqlalchemy import Enum as SAEnum
from sqlalchemy.types import TypeDecorator


def utcnow() -> datetime:
    """Bieżący czas w UTC ze strefą czasową (D-17)."""
    return datetime.now(UTC)


class UTCDateTime(TypeDecorator[datetime]):
    """Znacznik czasu zawsze w UTC ze strefą czasową.

    PostgreSQL przechowuje ``timestamptz``. SQLite (szybkie testy lokalne) nie
    ma stref czasowych, więc zapisujemy tam czas UTC bez strefy i dopisujemy
    ją przy odczycie. Dzięki temu porównania dat działają tak samo na obu bazach.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("Znacznik czasu musi mieć strefę czasową; użyj utcnow().")
        value = value.astimezone(UTC)
        return value.replace(tzinfo=None) if dialect.name == "sqlite" else value

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def render_alembic_type(type_: str, obj: Any, _autogen_context: Any) -> str | bool:
    """Autogenerate Alembica: UTCDateTime w migracjach jako zwykłe ``sa.DateTime(timezone=True)``.

    Migracje nie importują kodu aplikacji, więc pozostają poprawne po zmianach w modelach.
    """
    if type_ == "type" and isinstance(obj, UTCDateTime):
        return "sa.DateTime(timezone=True)"
    return False


def enum_column(enum_class: type[StrEnum], name: str) -> SAEnum:
    """Typ wyliczeniowy zapisany jako tekst z ograniczeniem CHECK.

    Zamiast natywnego ENUM PostgreSQL: dodanie nowej wartości to zwykła
    migracja zmieniająca CHECK, bez ALTER TYPE. W bazie trafiają wartości
    (np. ``"admin"``), a nie nazwy elementów.
    """
    return SAEnum(
        enum_class,
        name=name,
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
        values_callable=_enum_values,
    )


def _enum_values(enum_class: type[StrEnum]) -> list[Any]:
    return [member.value for member in enum_class]
