"""Modele i ograniczenia bazy: unikalności, CHECK, kaskady, SET NULL."""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, StatementError

from backend.core.extensions import db
from backend.models import (
    Flat,
    Invite,
    Membership,
    MembershipStatus,
    MemberRole,
    Recurrence,
    Task,
    TaskStatus,
    TaskType,
    User,
)
from backend.models.types import utcnow
from backend.security.tokens import SESSION_TOKEN_LENGTH


def _count(model: type) -> int:
    return db.session.scalar(select(func.count()).select_from(model))


def _task(flat: Flat, task_type: TaskType, **fields) -> Task:
    fields.setdefault("title", "Zadanie")
    fields.setdefault("due_date", date.today())
    return Task(flat=flat, task_type=task_type, **fields)


@pytest.fixture
def task_type(app_ctx) -> TaskType:
    task_type = TaskType(name="Sprzątanie")
    db.session.add(task_type)
    db.session.commit()
    return task_type


class TestUser:
    def test_email_is_normalized(self, make_user) -> None:
        user = make_user(email="  Ola.Nowak@Example.COM ")

        assert user.email == "ola.nowak@example.com"

    def test_email_is_unique_regardless_of_case(self, make_user) -> None:
        make_user(email="ola@example.com")

        with pytest.raises(IntegrityError):
            make_user(email="OLA@example.com")
        db.session.rollback()

    def test_session_token_is_generated_and_used_as_login_id(self, make_user) -> None:
        first, second = make_user(), make_user()

        assert len(first.session_token) == SESSION_TOKEN_LENGTH
        assert first.session_token != second.session_token
        assert first.get_id() == first.session_token

    def test_rotate_session_token(self, make_user) -> None:
        user = make_user()
        old_token = user.session_token

        user.rotate_session_token()

        assert user.session_token != old_token

    def test_color_index_must_be_in_palette(self, make_user) -> None:
        with pytest.raises(IntegrityError):
            make_user(color_index=12)
        db.session.rollback()


class TestMembership:
    def test_user_joins_flat_once(self, make_flat, make_user, add_member) -> None:
        flat, user = make_flat(), make_user()
        add_member(flat, user)

        with pytest.raises(IntegrityError):
            add_member(flat, user)
        db.session.rollback()

    def test_only_one_admin_per_flat(self, make_flat, make_user, add_member) -> None:
        flat = make_flat()

        with pytest.raises(IntegrityError):
            add_member(flat, make_user(), role=MemberRole.ADMIN)
        db.session.rollback()

    def test_admin_of_another_flat_is_allowed(self, make_flat, make_user) -> None:
        admin = make_user()
        make_flat(admin=admin)
        make_flat(admin=admin)

        assert _count(Membership) == 2

    def test_defaults_to_pending_member(self, make_flat, make_user) -> None:
        membership = Membership(flat=make_flat(), user=make_user())
        db.session.add(membership)
        db.session.commit()

        assert membership.role is MemberRole.MEMBER
        assert membership.status is MembershipStatus.PENDING
        assert not membership.is_active
        assert not membership.is_admin

    def test_rejects_unknown_role(self, make_flat, make_user) -> None:
        db.session.add(Membership(flat=make_flat(), user=make_user(), role="superadmin"))

        with pytest.raises((StatementError, LookupError)):
            db.session.flush()
        db.session.rollback()


class TestFlatDeletion:
    def test_cascades_to_everything_in_flat(self, make_flat, make_user, add_member, task_type) -> None:
        member = make_user()
        flat = make_flat()
        add_member(flat, member)
        own_type = TaskType(flat=flat, name="Podlewanie kwiatów")
        db.session.add_all(
            [
                own_type,
                _task(flat, own_type, assignee=member),
                _task(flat, task_type),
                Invite(flat=flat, created_by=member, token_hash="a" * 64, expires_at=utcnow()),
            ]
        )
        db.session.commit()

        db.session.delete(flat)
        db.session.commit()

        assert _count(Flat) == 0
        assert _count(Membership) == 0
        assert _count(Task) == 0
        assert _count(Invite) == 0
        assert db.session.scalars(select(TaskType)).all() == [task_type]
        assert _count(User) == 2


class TestTask:
    def test_done_requires_done_at(self, make_flat, task_type) -> None:
        db.session.add(_task(make_flat(), task_type, status=TaskStatus.DONE))

        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

    def test_occurrence_number_is_unique_in_series(self, make_flat, task_type) -> None:
        flat = make_flat()
        template = _task(flat, task_type, recurrence=Recurrence.WEEKLY)
        db.session.add_all(
            [template, _task(flat, task_type, parent=template, occurrence_index=0)]
        )
        db.session.commit()

        db.session.add(_task(flat, task_type, parent=template, occurrence_index=0))
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

    def test_occurrence_cannot_recur(self, make_flat, task_type) -> None:
        flat = make_flat()
        template = _task(flat, task_type, recurrence=Recurrence.WEEKLY)
        db.session.add_all(
            [template, _task(flat, task_type, parent=template, occurrence_index=0, recurrence=Recurrence.DAILY)]
        )

        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

    def test_deleting_series_keeps_done_occurrences(self, make_flat, task_type) -> None:
        flat = make_flat()
        template = _task(flat, task_type, recurrence=Recurrence.WEEKLY)
        done = _task(flat, task_type, parent=template, occurrence_index=0, status=TaskStatus.DONE, done_at=utcnow())
        db.session.add_all([template, done])
        db.session.commit()

        db.session.delete(template)
        db.session.commit()

        assert db.session.get(Task, done.id).parent_task_id is None

    def test_kinds(self, make_flat, task_type) -> None:
        flat = make_flat()
        one_off = _task(flat, task_type)
        template = _task(flat, task_type, recurrence=Recurrence.MONTHLY)
        occurrence = _task(flat, task_type, parent=template, occurrence_index=3)
        db.session.add_all([one_off, template, occurrence])
        db.session.commit()

        assert (one_off.is_template, one_off.is_occurrence) == (False, False)
        assert (template.is_template, template.is_occurrence) == (True, False)
        assert (occurrence.is_template, occurrence.is_occurrence) == (False, True)
        assert not one_off.is_done

    def test_deleting_user_unassigns_tasks(self, make_flat, make_user, add_member, task_type) -> None:
        flat, member = make_flat(), make_user()
        add_member(flat, member)
        task = _task(flat, task_type, assignee=member)
        db.session.add(task)
        db.session.commit()

        db.session.delete(member)
        db.session.commit()
        db.session.expire_all()

        assert db.session.get(Task, task.id).assignee_id is None


class TestTaskType:
    def test_global_and_own_types(self, make_flat, task_type) -> None:
        own = TaskType(flat=make_flat(), name="Rośliny")
        db.session.add(own)
        db.session.commit()

        assert task_type.is_global
        assert not own.is_global

    def test_icon_must_be_bootstrap_icon_class(self, app_ctx) -> None:
        db.session.add(TaskType(name="Zły", icon="javascript:alert(1)"))

        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

    def test_name_unique_within_flat(self, make_flat) -> None:
        flat = make_flat()
        db.session.add_all([TaskType(flat=flat, name="Rośliny"), TaskType(flat=flat, name="Rośliny")])

        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()


class TestInvite:
    @pytest.mark.parametrize(
        ("expires_in", "revoked", "usable"),
        [(timedelta(days=1), False, True), (timedelta(seconds=-1), False, False), (timedelta(days=1), True, False)],
    )
    def test_is_usable(self, make_flat, make_user, expires_in, revoked, usable) -> None:
        invite = Invite(
            flat=make_flat(), created_by=make_user(), token_hash="b" * 64,
            expires_at=utcnow() + expires_in, revoked=revoked,
        )
        db.session.add(invite)
        db.session.commit()

        assert invite.is_usable() is usable
