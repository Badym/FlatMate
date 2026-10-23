"""Dostęp do członkostw w mieszkaniach."""

from __future__ import annotations

from sqlalchemy import exists, select
from sqlalchemy.orm import joinedload

from backend.models import Membership, MembershipStatus, MemberRole, User
from backend.repositories.base_repository import FlatScopedRepository


class MembershipRepository(FlatScopedRepository[Membership]):
    model = Membership

    def get_for_user(self, flat_id: int, user_id: int) -> Membership | None:
        """Członkostwo w dowolnym statusie (np. do obsługi prośby o dołączenie)."""
        statement = self._select().where(Membership.flat_id == flat_id, Membership.user_id == user_id)
        return self._session.scalars(statement).first()

    def get_active(self, flat_id: int, user_id: int) -> Membership | None:
        statement = (
            self._select()
            .options(joinedload(Membership.flat))
            .where(
                Membership.flat_id == flat_id,
                Membership.user_id == user_id,
                Membership.status == MembershipStatus.ACTIVE,
            )
        )
        return self._session.scalars(statement).first()

    def is_active_member(self, flat_id: int, user_id: int) -> bool:
        statement = select(
            exists().where(
                Membership.flat_id == flat_id,
                Membership.user_id == user_id,
                Membership.status == MembershipStatus.ACTIVE,
            )
        )
        return bool(self._session.scalar(statement))

    def list_active(self, flat_id: int) -> list[Membership]:
        """Aktywni członkowie, admin pierwszy, dalej alfabetycznie."""
        statement = (
            self._select()
            .join(User, User.id == Membership.user_id)
            .options(joinedload(Membership.user))
            .where(Membership.flat_id == flat_id, Membership.status == MembershipStatus.ACTIVE)
            .order_by((Membership.role == MemberRole.ADMIN).desc(), User.display_name)
        )
        return list(self._session.scalars(statement))

    def get_admin(self, flat_id: int) -> Membership | None:
        statement = self._select().where(
            Membership.flat_id == flat_id,
            Membership.role == MemberRole.ADMIN,
            Membership.status == MembershipStatus.ACTIVE,
        )
        return self._session.scalars(statement).first()
