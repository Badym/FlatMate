"""Mieszkania z perspektywy zalogowanego użytkownika."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from backend.audit import audit_event
from backend.core.extensions import db
from backend.core.constants import INVITE_VALIDITY_DAYS
from backend.models import (
    Flat,
    Invite,
    MemberRole,
    Membership,
    MembershipStatus,
    User,
)
from backend.models.types import utcnow
from backend.repositories import (
    FlatRepository,
    InviteRepository,
    MembershipRepository,
    TaskRepository,
    UserRepository,
)
from backend.security.tokens import hash_token, new_invite_token


class HousingActionError(Exception):
    """Expected invalid state or permission while managing a flat."""


class FlatAccessDenied(HousingActionError):
    pass


class MembershipNotFound(HousingActionError):
    pass


class InvalidMembershipTransition(HousingActionError):
    pass


class InviteUnavailable(HousingActionError):
    pass


class AdminTransferRequired(HousingActionError):
    pass


class FlatNameMismatch(HousingActionError):
    pass


class LastAdminMustDelete(HousingActionError):
    pass


@dataclass(frozen=True)
class FlatSummary:
    flat: Flat
    role: MemberRole
    members: list[User]
    open_tasks: int

    @property
    def is_admin(self) -> bool:
        return self.role is MemberRole.ADMIN


class FlatService:
    def __init__(self) -> None:
        self._flats = FlatRepository()
        self._memberships = MembershipRepository()
        self._tasks = TaskRepository()
        self._invites = InviteRepository()
        self._users = UserRepository()

    def list_for_user(self, user_id: int) -> list[FlatSummary]:
        """Mieszkania, w których użytkownik jest aktywnym członkiem, z członkami i liczbą zadań."""
        summaries = []
        for flat in self._flats.list_for_user(user_id):
            memberships = self._memberships.list_active(flat.id)
            role = next(m.role for m in memberships if m.user_id == user_id)
            summaries.append(
                FlatSummary(
                    flat=flat,
                    role=role,
                    members=[m.user for m in memberships],
                    open_tasks=self._tasks.count_open(flat.id),
                )
            )
        return summaries

    def list_members(self, flat_id: int) -> list[Membership]:
        return self._memberships.list_for_flat(flat_id)

    def create(self, name: str, user_id: int) -> Flat:
        user = self._users.get(user_id)
        if user is None:
            raise MembershipNotFound
        flat = self._flats.add(Flat(name=name))
        self._flats.flush()
        self._memberships.add(
            Membership(
                flat_id=flat.id,
                user_id=user.id,
                role=MemberRole.ADMIN,
                status=MembershipStatus.ACTIVE,
                joined_at=utcnow(),
            )
        )
        db.session.commit()
        audit_event("flat_created", flat_id=flat.id)
        return flat

    def create_invite(self, flat_id: int, user_id: int) -> tuple[Invite, str]:
        self._require_admin(flat_id, user_id)
        token = new_invite_token()
        invite = self._invites.add(
            Invite(
                flat_id=flat_id,
                created_by_id=user_id,
                token_hash=hash_token(token),
                expires_at=utcnow() + timedelta(days=INVITE_VALIDITY_DAYS),
            )
        )
        db.session.commit()
        audit_event("invite_created", flat_id=flat_id, invite_id=invite.id)
        return invite, token

    def list_invites(self, flat_id: int) -> list[Invite]:
        return self._invites.list_for_flat(flat_id)

    def revoke_invite(self, flat_id: int, invite_id: int, user_id: int) -> None:
        self._require_admin(flat_id, user_id)
        invite = self._invites.get_in_flat(flat_id, invite_id)
        if invite is None:
            raise MembershipNotFound
        if not invite.revoked:
            invite.revoked = True
            db.session.commit()
            audit_event("invite_revoked", flat_id=flat_id, invite_id=invite.id)

    def join_context(self, token: str, user_id: int) -> tuple[Flat, Membership | None] | None:
        invite = self._get_usable_invite(token)
        if invite is None:
            return None
        return invite.flat, self._memberships.get_for_user(invite.flat_id, user_id)

    def request_to_join(self, token: str, user_id: int) -> MembershipStatus:
        invite = self._get_usable_invite(token)
        if invite is None:
            raise InviteUnavailable
        existing = self._memberships.get_for_user(invite.flat_id, user_id)
        if existing is not None:
            return existing.status
        self._memberships.add(
            Membership(
                flat_id=invite.flat_id,
                user_id=user_id,
                role=MemberRole.MEMBER,
                status=MembershipStatus.PENDING,
            )
        )
        db.session.commit()
        audit_event("membership_requested", flat_id=invite.flat_id)
        return MembershipStatus.PENDING

    def approve_member(self, flat_id: int, membership_id: int, admin_id: int) -> None:
        self._require_admin(flat_id, admin_id)
        membership = self._memberships.get_in_flat(flat_id, membership_id)
        if membership is None:
            raise MembershipNotFound
        if membership.status is not MembershipStatus.PENDING:
            raise InvalidMembershipTransition
        membership.status = MembershipStatus.ACTIVE
        membership.joined_at = utcnow()
        db.session.commit()
        audit_event("membership_approved", flat_id=flat_id, membership_id=membership.id)

    def reject_member(self, flat_id: int, membership_id: int, admin_id: int) -> None:
        self._require_admin(flat_id, admin_id)
        membership = self._memberships.get_in_flat(flat_id, membership_id)
        if membership is None:
            raise MembershipNotFound
        if membership.status is not MembershipStatus.PENDING:
            raise InvalidMembershipTransition
        membership.status = MembershipStatus.REJECTED
        db.session.commit()
        audit_event("membership_rejected", flat_id=flat_id, membership_id=membership.id)

    def remove_member(self, flat_id: int, membership_id: int, admin_id: int) -> None:
        self._require_admin(flat_id, admin_id)
        membership = self._memberships.get_in_flat(flat_id, membership_id)
        if membership is None:
            raise MembershipNotFound
        if membership.is_admin or membership.status not in (
            MembershipStatus.ACTIVE,
            MembershipStatus.REJECTED,
        ):
            raise InvalidMembershipTransition
        if membership.status is MembershipStatus.ACTIVE:
            from backend.services.membership_service import MembershipService

            MembershipService().release_member_tasks(flat_id, membership.user_id)
        self._memberships.delete(membership)
        db.session.commit()
        audit_event("membership_removed", flat_id=flat_id, membership_id=membership_id)

    def make_admin(self, flat_id: int, membership_id: int, admin_id: int) -> None:
        self._require_admin(flat_id, admin_id)
        current_admin = self._memberships.get_active(flat_id, admin_id)
        target = self._memberships.get_in_flat(flat_id, membership_id)
        if target is None:
            raise MembershipNotFound
        if target.status is not MembershipStatus.ACTIVE or target.user_id == admin_id:
            raise InvalidMembershipTransition
        if current_admin is None:
            raise FlatAccessDenied
        current_admin.role = MemberRole.MEMBER
        db.session.flush()
        target.role = MemberRole.ADMIN
        db.session.commit()
        audit_event("admin_transferred", flat_id=flat_id, membership_id=target.id)

    def leave(self, flat_id: int, user_id: int) -> None:
        membership = self._memberships.get_active(flat_id, user_id)
        if membership is None:
            raise MembershipNotFound
        if membership.is_admin:
            active = self._memberships.list_active(flat_id)
            if len(active) == 1:
                raise LastAdminMustDelete
            raise AdminTransferRequired
        from backend.services.membership_service import MembershipService

        MembershipService().release_member_tasks(flat_id, user_id)
        self._memberships.delete(membership)
        db.session.commit()
        audit_event("flat_left", flat_id=flat_id)

    def delete_flat(self, flat_id: int, admin_id: int, confirmation: str) -> None:
        self._require_admin(flat_id, admin_id)
        flat = self._flats.get(flat_id)
        if flat is None:
            raise MembershipNotFound
        if flat.name != confirmation:
            raise FlatNameMismatch
        self._flats.delete(flat)
        db.session.commit()
        audit_event("flat_deleted", flat_id=flat_id)

    def _require_admin(self, flat_id: int, user_id: int) -> Membership:
        membership = self._memberships.get_active(flat_id, user_id)
        if membership is None or not membership.is_admin:
            raise FlatAccessDenied
        return membership

    def _get_usable_invite(self, token: str) -> Invite | None:
        invite = self._invites.get_by_token_hash(hash_token(token))
        return invite if invite is not None and invite.is_usable() else None
