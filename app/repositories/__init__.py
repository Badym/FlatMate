"""Warstwa dostępu do danych.

Repozytoria są jedynym miejscem, w którym powstają zapytania do bazy
(wyłącznie przez ORM, SR-7). Nie zatwierdzają transakcji – robi to warstwa
serwisów, dzięki czemu jedna operacja biznesowa jest jedną transakcją.
"""

from app.repositories.base_repository import FlatScopedRepository, Repository

__all__ = ["FlatScopedRepository", "Repository"]
