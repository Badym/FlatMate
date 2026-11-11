"""Typy wyliczeniowe domeny (zapisywane jako tekst, patrz types.enum_column)."""

from __future__ import annotations

from enum import StrEnum


class MemberRole(StrEnum):
    ADMIN = "admin"
    MEMBER = "member"


class MembershipStatus(StrEnum):
    """Stan członkostwa; prośba o dołączenie zaczyna jako PENDING (D-4)."""

    PENDING = "pending"
    ACTIVE = "active"
    REJECTED = "rejected"


class TaskStatus(StrEnum):
    OPEN = "open"
    DONE = "done"


class Recurrence(StrEnum):
    """Powtarzanie zadania; NONE dla zadań jednorazowych i wystąpień serii."""

    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class AssignmentMode(StrEnum):
    """Sposób przypisania osoby (FR-7)."""

    FIXED = "fixed"
    ROTATION = "rotation"
    POOL = "pool"
