"""Dostęp do zaproszeń ograniczony do mieszkania (T-01, T-08)."""

from __future__ import annotations

from sqlalchemy import select

from backend.models import Invite
from backend.repositories.base_repository import FlatScopedRepository


class InviteRepository(FlatScopedRepository[Invite]):
    model = Invite

    def get_by_token_hash(self, token_hash: str) -> Invite | None:
        return self._session.scalars(
            self._select().where(Invite.token_hash == token_hash)
        ).first()

    def list_for_flat(self, flat_id: int) -> list[Invite]:
        statement = (
            select(Invite)
            .where(Invite.flat_id == flat_id)
            .order_by(Invite.created_at.desc())
        )
        return list(self._session.scalars(statement))
