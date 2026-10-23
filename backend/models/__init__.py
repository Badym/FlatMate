"""Warstwa modelu: encje ORM.

Każda encja w osobnym module (``user.py``, ``flat.py``, ``task.py`` …),
importowana tutaj, żeby Alembic widział komplet tabel. Modele powstają
w etapie 3 planu implementacji.
"""

from backend.models.base import Base

__all__ = ["Base"]
