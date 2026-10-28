"""Dane demonstracyjne: konta, mieszkanie i zadania do ręcznego testowania aplikacji."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import select

from backend.core.extensions import db
from backend.models import (
    AssignmentMode,
    Flat,
    Membership,
    MembershipStatus,
    MemberRole,
    Task,
    TaskStatus,
    User,
)
from backend.models.types import utcnow
from backend.repositories import FlatRepository, TaskTypeRepository, UserRepository
from backend.security.passwords import hash_password

# Domena .example jest zarezerwowana (RFC 2606), więc adresy nigdy nie trafią do prawdziwej skrzynki.
# Nie .test: email-validator odrzuca ją jako domenę specjalnego użytku, więc nie dałoby się zalogować.
DEMO_EMAIL_DOMAIN = "flatmate.example"
DEMO_FLAT_NAME = "Mickiewicza 12/4 (demo)"

# (nazwa, login w adresie, indeks koloru, rola)
DEMO_USERS: tuple[tuple[str, str, int, MemberRole], ...] = (
    ("Ola Nowak", "ola", 0, MemberRole.ADMIN),
    ("Kuba Wiśniewski", "kuba", 9, MemberRole.MEMBER),
    ("Marta Zając", "marta", 3, MemberRole.MEMBER),
)

# (tytuł, typ, login osoby lub None dla puli, przesunięcie terminu w dniach, czy wykonane)
DEMO_TASKS: tuple[tuple[str, str, str | None, int, bool], ...] = (
    ("Sprzątanie łazienki", "Łazienka", "ola", 0, False),
    ("Zakupy: środki czystości", "Zakupy", None, 2, False),
    ("Wyniesienie śmieci", "Śmieci", "kuba", -1, False),
    ("Odkurzanie salonu", "Sprzątanie", "marta", 3, False),
    ("Rozmrożenie lodówki", "Kuchnia", "marta", -3, True),
)


def demo_email(login: str) -> str:
    return f"{login}@{DEMO_EMAIL_DOMAIN}"


@dataclass(frozen=True)
class DemoSeedResult:
    created: bool
    emails: tuple[str, ...]


class DemoSeedService:
    def __init__(self) -> None:
        self._users = UserRepository()
        self._flats = FlatRepository()
        self._task_types = TaskTypeRepository()

    def seed(self, password: str, *, reset: bool = False) -> DemoSeedResult:
        emails = tuple(demo_email(login) for _name, login, _color, _role in DEMO_USERS)
        if self._users.get_by_email(emails[0]) is not None:
            if not reset:
                return DemoSeedResult(created=False, emails=emails)
            self._remove()

        users = self._create_users(password)
        flat = self._create_flat(users)
        self._create_tasks(flat, users)
        db.session.commit()
        return DemoSeedResult(created=True, emails=emails)

    def _remove(self) -> None:
        for flat in db.session.scalars(select(Flat).where(Flat.name == DEMO_FLAT_NAME)):
            db.session.delete(flat)
        for _name, login, _color, _role in DEMO_USERS:
            user = self._users.get_by_email(demo_email(login))
            if user is not None:
                db.session.delete(user)
        db.session.flush()

    def _create_users(self, password: str) -> dict[str, User]:
        users = {}
        for name, login, color, _role in DEMO_USERS:
            users[login] = self._users.add(
                User(
                    email=demo_email(login),
                    display_name=name,
                    password_hash=hash_password(password),
                    color_index=color,
                )
            )
        self._users.flush()
        return users

    def _create_flat(self, users: dict[str, User]) -> Flat:
        flat = self._flats.add(Flat(name=DEMO_FLAT_NAME))
        now = utcnow()
        for _name, login, _color, role in DEMO_USERS:
            flat.memberships.append(
                Membership(user=users[login], role=role, status=MembershipStatus.ACTIVE, joined_at=now)
            )
        self._flats.flush()
        return flat

    def _create_tasks(self, flat: Flat, users: dict[str, User]) -> None:
        types = {task_type.name: task_type for task_type in self._task_types.list_available(flat.id)}
        admin = users[DEMO_USERS[0][1]]
        today = date.today()
        for title, type_name, login, due_offset, done in DEMO_TASKS:
            task_type = types[type_name]
            assignee = users[login] if login else None
            task = Task(
                flat=flat,
                task_type=task_type,
                title=title,
                due_date=today + timedelta(days=due_offset),
                points=task_type.default_points,
                assignee=assignee,
                created_by=admin,
                assignment_mode=AssignmentMode.FIXED if assignee else AssignmentMode.POOL,
            )
            if done:
                task.status = TaskStatus.DONE
                task.done_at = utcnow()
                task.done_by = assignee
            db.session.add(task)
