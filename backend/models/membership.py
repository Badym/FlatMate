"""Członkostwo użytkownika w mieszkaniu (relacja N:M z rolą i statusem)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin
from backend.models.enums import MemberRole, MembershipStatus
from backend.models.types import UTCDateTime, enum_column

if TYPE_CHECKING:
    from backend.models.flat import Flat
    from backend.models.user import User


class Membership(TimestampMixin, Base):
    """``created_at`` to chwila prośby o dołączenie, ``joined_at`` – akceptacji."""

    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "flat_id"),
        # Co najwyżej jeden admin w mieszkaniu, pilnowane przez bazę (indeks częściowy).
        Index(
            "uq_memberships_one_admin_per_flat",
            "flat_id",
            unique=True,
            postgresql_where=text("role = 'admin'"),
            sqlite_where=text("role = 'admin'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Wyszukiwanie po user_id obsługuje indeks ograniczenia unikalności (user_id, flat_id).
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    flat_id: Mapped[int] = mapped_column(ForeignKey("flats.id", ondelete="CASCADE"), index=True)
    role: Mapped[MemberRole] = mapped_column(
        enum_column(MemberRole, "member_role"), default=MemberRole.MEMBER
    )
    status: Mapped[MembershipStatus] = mapped_column(
        enum_column(MembershipStatus, "membership_status"), default=MembershipStatus.PENDING
    )
    joined_at: Mapped[datetime | None] = mapped_column(UTCDateTime())

    user: Mapped[User] = relationship(back_populates="memberships")
    flat: Mapped[Flat] = relationship(back_populates="memberships")

    @property
    def is_active(self) -> bool:
        return self.status is MembershipStatus.ACTIVE

    @property
    def is_admin(self) -> bool:
        return self.is_active and self.role is MemberRole.ADMIN

    def __repr__(self) -> str:
        return f"<Membership user={self.user_id} flat={self.flat_id} {self.role}/{self.status}>"
