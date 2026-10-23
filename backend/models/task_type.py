"""Typ zadania: globalny (flat_id = NULL) albo własny typ mieszkania."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.constants import TASK_POINTS_MAX, TASK_POINTS_MIN, TASK_TYPE_NAME_MAX_LENGTH
from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.flat import Flat

DEFAULT_TASK_TYPE_ICON = "bi-check2-square"

# Globalne typy tworzone przez pierwszą migrację. Migracja ma własną kopię tej listy
# (migracje nie importują kodu aplikacji); zgodność sprawdza test.
DEFAULT_TASK_TYPES: tuple[dict[str, str | int], ...] = (
    {"name": "Sprzątanie", "icon": "bi-stars", "default_points": 10},
    {"name": "Łazienka", "icon": "bi-droplet-half", "default_points": 15},
    {"name": "Kuchnia", "icon": "bi-cup-hot", "default_points": 10},
    {"name": "Śmieci", "icon": "bi-trash3", "default_points": 5},
    {"name": "Zakupy", "icon": "bi-basket2", "default_points": 10},
    {"name": "Pranie", "icon": "bi-water", "default_points": 10},
    {"name": "Inne", "icon": DEFAULT_TASK_TYPE_ICON, "default_points": 5},
)


class TaskType(Base):
    __tablename__ = "task_types"
    __table_args__ = (
        UniqueConstraint("flat_id", "name"),
        CheckConstraint(
            f"default_points BETWEEN {TASK_POINTS_MIN} AND {TASK_POINTS_MAX}", name="default_points_range"
        ),
        # Ikona to klasa Bootstrap Icons wstawiana do atrybutu class w szablonie.
        CheckConstraint("icon LIKE 'bi-%'", name="icon_bootstrap_class"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    flat_id: Mapped[int | None] = mapped_column(ForeignKey("flats.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(TASK_TYPE_NAME_MAX_LENGTH))
    icon: Mapped[str] = mapped_column(String(40), default=DEFAULT_TASK_TYPE_ICON)
    default_points: Mapped[int] = mapped_column(SmallInteger, default=10)

    flat: Mapped[Flat | None] = relationship(back_populates="task_types")

    @property
    def is_global(self) -> bool:
        return self.flat_id is None

    def __repr__(self) -> str:
        return f"<TaskType id={self.id} flat={self.flat_id}>"
