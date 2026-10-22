"""Instancje rozszerzeń Flaska, podpinane do aplikacji w fabryce."""

from __future__ import annotations

import sqlite3
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

from app.models.base import Base

db = SQLAlchemy(model_class=Base)
migrate = Migrate()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Zaloguj się, aby kontynuować."
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(session_token: str) -> Any:
    """Ładuje użytkownika z sesji.

    Etap 4: wyszukanie po ``User.session_token`` (D-13), dzięki czemu
    wylogowanie i zmiana hasła unieważniają stare ciasteczka.
    """
    return None


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection: Any, _connection_record: Any) -> None:
    """SQLite domyślnie nie pilnuje kluczy obcych; PostgreSQL robi to zawsze."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def init_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    limiter.init_app(app)
    login_manager.init_app(app)
