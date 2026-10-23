"""Polecenie ``flask seed-demo`` i serwis danych demonstracyjnych."""

from __future__ import annotations

import secrets

import pytest
from sqlalchemy import func, select

from backend.core.extensions import db
from backend.models import Flat, Membership, MemberRole, Task, TaskStatus, User
from backend.repositories import UserRepository
from backend.security.passwords import verify_password
from backend.services.demo_seed_service import DEMO_FLAT_NAME, DEMO_TASKS, DEMO_USERS, demo_email

DEMO_PASSWORD = secrets.token_urlsafe(16)


def _count(model: type) -> int:
    return db.session.scalar(select(func.count()).select_from(model))


@pytest.fixture
def demo_app(make_app):
    return make_app(DEMO_PASSWORD=DEMO_PASSWORD)


@pytest.fixture
def run(demo_app, default_task_types):
    runner = demo_app.test_cli_runner()

    def invoke(*args: str):
        return runner.invoke(args=["seed-demo", *args])

    return invoke


@pytest.fixture
def default_task_types(demo_app):
    """Nadpisuje fixture z conftest: typy muszą trafić do bazy aplikacji demo."""
    from backend.models import TaskType
    from backend.models.task_type import DEFAULT_TASK_TYPES

    with demo_app.app_context():
        db.session.add_all([TaskType(flat_id=None, **row) for row in DEFAULT_TASK_TYPES])
        db.session.commit()


def test_creates_demo_accounts_flat_and_tasks(demo_app, run) -> None:
    result = run()

    assert result.exit_code == 0, result.output
    assert "ola@flatmate.test" in result.output
    assert DEMO_PASSWORD not in result.output
    with demo_app.app_context():
        assert _count(User) == len(DEMO_USERS)
        assert _count(Task) == len(DEMO_TASKS)
        flat = db.session.scalars(select(Flat)).one()
        assert flat.name == DEMO_FLAT_NAME
        admins = [m for m in flat.memberships if m.role is MemberRole.ADMIN]
        assert [m.user.email for m in admins] == [demo_email("ola")]
        assert all(m.is_active for m in flat.memberships)
        done = db.session.scalars(select(Task).where(Task.status == TaskStatus.DONE)).one()
        assert done.done_by == done.assignee
        assert db.session.scalars(select(Task).where(Task.assignee_id.is_(None))).one().title.startswith("Zakupy")


def test_demo_password_works(demo_app, run) -> None:
    run()

    with demo_app.app_context():
        user = UserRepository().get_by_email(demo_email("kuba"))
        assert verify_password(user.password_hash, DEMO_PASSWORD)


def test_second_run_does_not_duplicate(demo_app, run) -> None:
    run()

    result = run()

    assert result.exit_code == 0
    assert "już istnieją" in result.output
    with demo_app.app_context():
        assert _count(User) == len(DEMO_USERS)


def test_reset_recreates_data(demo_app, run) -> None:
    run()
    with demo_app.app_context():
        first_tokens = set(db.session.scalars(select(User.session_token)))

    result = run("--reset")

    assert result.exit_code == 0
    with demo_app.app_context():
        assert _count(User) == len(DEMO_USERS)
        assert _count(Flat) == 1
        assert _count(Membership) == len(DEMO_USERS)
        # Konta utworzone od nowa mają nowe tokeny sesji.
        assert first_tokens.isdisjoint(db.session.scalars(select(User.session_token)))


def test_requires_demo_password(make_app) -> None:
    result = make_app(DEMO_PASSWORD="krotkie").test_cli_runner().invoke(args=["seed-demo"])

    assert result.exit_code != 0
    assert "DEMO_PASSWORD" in result.output


def test_refuses_to_run_in_production(make_app) -> None:
    app = make_app(DEMO_PASSWORD=DEMO_PASSWORD, ENV_NAME="production")

    result = app.test_cli_runner().invoke(args=["seed-demo"])

    assert result.exit_code != 0
    assert "produkcyjnym" in result.output
    with app.app_context():
        assert _count(User) == 0
