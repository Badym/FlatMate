"""Link zaproszenia do mieszkania (SR-8, T-08)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin
from backend.models.types import UTCDateTime, utcnow

if TYPE_CHECKING:
    from backend.models.flat import Flat
    from backend.models.user import User


class Invite(TimestampMixin, Base):
    """Wielorazowy link do wygaśnięcia lub unieważnienia (D-12).

    W bazie jest wyłącznie skrót SHA-256 tokenu; sam token pojawia się tylko
    w linku pokazanym adminowi.
    """

    __tablename__ = "invites"

    id: Mapped[int] = mapped_column(primary_key=True)
    flat_id: Mapped[int] = mapped_column(ForeignKey("flats.id", ondelete="CASCADE"), index=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime())
    revoked: Mapped[bool] = mapped_column(default=False)

    flat: Mapped[Flat] = relationship(back_populates="invites")
    created_by: Mapped[User] = relationship()

    def is_usable(self, now: datetime | None = None) -> bool:
        return not self.revoked and self.expires_at > (now or utcnow())

    def __repr__(self) -> str:
        return f"<Invite id={self.id} flat={self.flat_id}>"
