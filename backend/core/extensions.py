"""Instancje rozszerzeń Flaska, podpinane do aplikacji w fabryce."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from sqlalchemy import event
from sqlalchemy.engine import Engine

from backend.models.base import Base
from backend.models.types import render_alembic_type

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"

db = SQLAlchemy(model_class=Base)
migrate = Migrate(compare_type=True, render_item=render_alembic_type)
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Zaloguj się, aby kontynuować."
login_manager.login_message_category = "info"


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection: Any, _connection_record: Any) -> None:
    """SQLite domyślnie nie pilnuje kluczy obcych; PostgreSQL robi to zawsze."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def init_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db, directory=str(MIGRATIONS_DIR))
    csrf.init_app(app)
    limiter.init_app(app)
    login_manager.init_app(app)
