"""Warstwa dostępu do danych.

Repozytoria są jedynym miejscem, w którym powstają zapytania do bazy
(wyłącznie przez ORM, SR-7). Nie zatwierdzają transakcji – robi to warstwa
serwisów, dzięki czemu jedna operacja biznesowa jest jedną transakcją.
"""

from backend.repositories.base_repository import FlatScopedRepository, Repository
from backend.repositories.flat_repository import FlatRepository
from backend.repositories.membership_repository import MembershipRepository
from backend.repositories.task_repository import TaskRepository
from backend.repositories.task_type_repository import TaskTypeRepository
from backend.repositories.user_repository import UserRepository

__all__ = [
    "FlatRepository",
    "FlatScopedRepository",
    "MembershipRepository",
    "Repository",
    "TaskRepository",
    "TaskTypeRepository",
    "UserRepository",
]
