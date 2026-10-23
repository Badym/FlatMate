"""Wspólne fixture'y testów.

Domyślnie testy działają na SQLite w pamięci. Po ustawieniu TEST_DATABASE_URL
(CI, ``docker compose --profile test run --rm tests``) idą na PostgreSQL.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

from backend import create_app
from backend.core.extensions import db


@pytest.fixture
def make_app() -> Iterator[Callable[..., Flask]]:
    """Fabryka aplikacji testowych z własnymi ustawieniami (np. włączonym CSRF)."""
    created: list[Flask] = []

    def factory(**overrides: Any) -> Flask:
        application = create_app("testing", overrides=overrides)
        with application.app_context():
            db.create_all()
        created.append(application)
        return application

    yield factory

    for application in created:
        with application.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()


@pytest.fixture
def app(make_app: Callable[..., Flask]) -> Flask:
    return make_app()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()
