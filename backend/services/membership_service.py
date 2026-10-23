"""Reguły członkostwa w mieszkaniu wspólne dla kolejnych etapów."""

from __future__ import annotations

from backend.repositories import MembershipRepository, TaskRepository


class MembershipService:
    def __init__(
        self,
        memberships: MembershipRepository | None = None,
        tasks: TaskRepository | None = None,
    ) -> None:
        self._memberships = memberships or MembershipRepository()
        self._tasks = tasks or TaskRepository()

    def is_active_member(self, flat_id: int, user_id: int) -> bool:
        """Do walidacji ID osób z formularzy: przypisać można tylko aktywnego członka (T-01, T-02)."""
        return self._memberships.is_active_member(flat_id, user_id)

    def member_choices(self, flat_id: int) -> list[tuple[int, str]]:
        """Opcje pola wyboru osoby: wyłącznie aktywni członkowie tego mieszkania."""
        return [(m.user_id, m.user.display_name) for m in self._memberships.list_active(flat_id)]

    def release_member_tasks(self, flat_id: int, user_id: int) -> int:
        """Niewykonane zadania odchodzącej osoby wracają do puli (D-10, sekcja 3.2 planu).

        Wywołuje to usunięcie członka i opuszczenie mieszkania (etap 5) w swojej
        transakcji, więc metoda nie zatwierdza zmian. Etap 7 dopisze rotację:
        usunięcie z ``rotation_members`` i przeliczenie przyszłych wystąpień serii.
        """
        return self._tasks.unassign_open_tasks(flat_id, user_id)
