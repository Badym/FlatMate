"""Sprawdzanie dostępności bazy danych."""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db

logger = logging.getLogger(__name__)


class HealthRepository:
    def ping(self) -> bool:
        try:
            db.session.execute(text("SELECT 1"))
        except SQLAlchemyError:
            logger.exception("Baza danych nie odpowiada")
            db.session.rollback()
            return False
        return True
