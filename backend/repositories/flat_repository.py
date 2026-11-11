"""Dostęp do mieszkań."""

from __future__ import annotations

from backend.models import Flat, Membership, MembershipStatus
from backend.repositories.base_repository import Repository


class FlatRepository(Repository[Flat]):
    model = Flat

    def list_for_user(self, user_id: int) -> list[Flat]:
        """Mieszkania, w których użytkownik jest aktywnym członkiem."""
        statement = (
            self._select()
            .join(Membership, Membership.flat_id == Flat.id)
            .where(Membership.user_id == user_id, Membership.status == MembershipStatus.ACTIVE)
            .order_by(Flat.name)
        )
        return list(self._session.scalars(statement))
