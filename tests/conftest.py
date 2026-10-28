"""Wspólne fixture'y testów.

Testy działają na osobnej bazie PostgreSQL z TEST_DATABASE_URL:
lokalnie ``docker compose up -d db-test``, w CI usługa postgres, w Dockerze
``docker compose --profile test run --rm tests``.

Fixture'y danych (``make_user``, ``make_flat``, ``add_member``) działają
w kontekście aplikacji z fixture'a ``app_ctx``; zapytania klienta testowego
korzystają z tej samej sesji bazy.
"""

from __future__ import annotations

import itertools
import secrets
from collections.abc import Callable, Iterator
from functools import cache
from typing import Any

import pytest
from dotenv import load_dotenv
from flask import Flask, g, has_app_context
from flask.testing import FlaskClient
from sqlalchemy.exc import OperationalError

from backend import create_app
from backend.core.extensions import db
from backend.models import Flat, Membership, MembershipStatus, MemberRole, TaskType, User
from backend.models.task_type import DEFAULT_TASK_TYPES
from backend.models.types import utcnow
from backend.security.passwords import hash_password

load_dotenv()

# Losowe przy każdym uruchomieniu, więc w repozytorium nie ma żadnego hasła.
TEST_PASSWORD = secrets.token_urlsafe(16)


@cache
def _test_password_hash() -> str:
    """Jeden hash na całą sesję testów: scrypt jest celowo wolny."""
    return hash_password(TEST_PASSWORD)


class IsolatedClient(FlaskClient):
    """Klient testowy, w którym każde żądanie zaczyna z pustym ``g``.

    Gdy test trzyma otwarty kontekst aplikacji (``app_ctx``), Flask używa go
    ponownie dla żądań klienta, więc ``g`` – a w nim zalogowany użytkownik
    z Flask-Login – przechodziłby między żądaniami. Na serwerze każde żądanie
    ma nowy kontekst; tu odtwarzamy to zachowanie.
    """

    def open(self, *args: Any, **kwargs: Any) -> Any:
        if has_app_context():
            g.__dict__.clear()
        return super().open(*args, **kwargs)


@pytest.fixture
def make_app() -> Iterator[Callable[..., Flask]]:
    """Fabryka aplikacji testowych z własnymi ustawieniami (np. włączonym CSRF)."""
    created: list[Flask] = []

    def factory(**overrides: Any) -> Flask:
        application = create_app("testing", overrides=overrides)
        application.test_client_class = IsolatedClient
        with application.app_context():
            try:
                db.create_all()
            except OperationalError:
                pytest.exit("Baza testowa nie odpowiada. Uruchom: docker compose up -d db-test", returncode=1)
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


@pytest.fixture
def app_ctx(app: Flask) -> Iterator[Flask]:
    with app.app_context():
        yield app


@pytest.fixture
def make_user(app_ctx: Flask) -> Callable[..., User]:
    counter = itertools.count(1)

    def factory(**fields: Any) -> User:
        number = next(counter)
        fields.setdefault("email", f"osoba{number}@example.com")
        fields.setdefault("display_name", f"Osoba {number}")
        fields.setdefault("password_hash", _test_password_hash())
        user = User(**fields)
        db.session.add(user)
        db.session.commit()
        return user

    return factory


@pytest.fixture
def add_member(app_ctx: Flask) -> Callable[..., Membership]:
    def factory(
        flat: Flat,
        user: User,
        role: MemberRole = MemberRole.MEMBER,
        status: MembershipStatus = MembershipStatus.ACTIVE,
    ) -> Membership:
        membership = Membership(
            flat=flat,
            user=user,
            role=role,
            status=status,
            joined_at=utcnow() if status is MembershipStatus.ACTIVE else None,
        )
        db.session.add(membership)
        db.session.commit()
        return membership

    return factory


@pytest.fixture
def make_flat(app_ctx: Flask, make_user: Callable[..., User], add_member: Callable[..., Membership]):
    """Mieszkanie z aktywnym adminem (domyślnie nowym użytkownikiem)."""
    counter = itertools.count(1)

    def factory(admin: User | None = None, name: str | None = None) -> Flat:
        flat = Flat(name=name or f"Mieszkanie {next(counter)}")
        db.session.add(flat)
        db.session.commit()
        add_member(flat, admin or make_user(), role=MemberRole.ADMIN)
        return flat

    return factory


@pytest.fixture
def default_task_types(app_ctx: Flask) -> list[TaskType]:
    """Globalne typy zadań, które w prawdziwej bazie tworzy pierwsza migracja."""
    task_types = [TaskType(flat_id=None, **row) for row in DEFAULT_TASK_TYPES]
    db.session.add_all(task_types)
    db.session.commit()
    return task_types


@pytest.fixture
def login(client: FlaskClient) -> Callable[[User], None]:
    """Loguje użytkownika w kliencie testowym przez token sesji (D-13), bez formularza."""

    def do_login(user: User) -> None:
        with client.session_transaction() as session:
            session["_user_id"] = user.session_token
            session["_fresh"] = True

    return do_login
