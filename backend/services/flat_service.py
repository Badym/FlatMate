"""Mieszkania z perspektywy zalogowanego użytkownika."""

from __future__ import annotations

from dataclasses import dataclass

from backend.models import Flat, MemberRole, User
from backend.repositories import FlatRepository, MembershipRepository, TaskRepository


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
