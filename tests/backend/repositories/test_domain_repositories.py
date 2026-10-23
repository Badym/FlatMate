"""Repozytoria encji domeny."""

from __future__ import annotations

from datetime import date

from backend.core.extensions import db
from backend.models import MembershipStatus, MemberRole, Task, TaskStatus, TaskType
from backend.models.types import utcnow
from backend.repositories import (
    FlatRepository,
    MembershipRepository,
    TaskRepository,
    TaskTypeRepository,
    UserRepository,
)


class TestUserRepository:
    def test_get_by_email_ignores_case_and_spaces(self, make_user) -> None:
        user = make_user(email="ola@example.test")

        assert UserRepository().get_by_email("  OLA@Example.test ") == user
        assert UserRepository().get_by_email("ktos@example.test") is None

    def test_get_by_session_token(self, make_user) -> None:
        user = make_user()

        assert UserRepository().get_by_session_token(user.session_token) == user
        assert UserRepository().get_by_session_token("0" * 64) is None


def test_flats_of_user_are_only_active_ones(make_flat, make_user, add_member) -> None:
    user = make_user()
    active = make_flat(name="B mieszkanie")
    own = make_flat(admin=user, name="A mieszkanie")
    pending = make_flat()
    add_member(active, user)
    add_member(pending, user, status=MembershipStatus.PENDING)

    assert FlatRepository().list_for_user(user.id) == [own, active]


class TestMembershipRepository:
    def test_active_membership_lookup(self, make_flat, make_user, add_member) -> None:
        flat, member, pending = make_flat(), make_user(), make_user()
        add_member(flat, member)
        add_member(flat, pending, status=MembershipStatus.PENDING)
        repository = MembershipRepository()

        assert repository.get_active(flat.id, member.id).user == member
        assert repository.get_active(flat.id, pending.id) is None
        assert repository.get_for_user(flat.id, pending.id).status is MembershipStatus.PENDING
        assert repository.is_active_member(flat.id, member.id)
        assert not repository.is_active_member(flat.id, pending.id)

    def test_list_active_puts_admin_first(self, make_user, make_flat, add_member) -> None:
        admin = make_user(display_name="Zenon")
        flat = make_flat(admin=admin)
        add_member(flat, make_user(display_name="Ola"))
        add_member(flat, make_user(display_name="Basia"))
        add_member(flat, make_user(display_name="Pending"), status=MembershipStatus.PENDING)

        names = [m.user.display_name for m in MembershipRepository().list_active(flat.id)]

        assert names == ["Zenon", "Basia", "Ola"]
        assert MembershipRepository().get_admin(flat.id).user == admin
        assert MembershipRepository().get_admin(flat.id).role is MemberRole.ADMIN


class TestTaskTypeRepository:
    def test_available_types_are_global_and_own(self, make_flat, default_task_types) -> None:
        flat, other_flat = make_flat(), make_flat()
        own = TaskType(flat=flat, name="Akwarium")
        foreign = TaskType(flat=other_flat, name="Ogród")
        db.session.add_all([own, foreign])
        db.session.commit()
        repository = TaskTypeRepository()

        available = repository.list_available(flat.id)

        assert own in available
        assert foreign not in available
        assert set(default_task_types) <= set(available)
        assert available[-1] == own
        assert repository.get_available(flat.id, foreign.id) is None
        assert repository.get_available(flat.id, default_task_types[0].id) == default_task_types[0]


def test_unassign_open_tasks_only_for_user_in_flat(make_flat, make_user, add_member, default_task_types) -> None:
    flat, other_flat, user, other_user = make_flat(), make_flat(), make_user(), make_user()
    add_member(flat, user)
    add_member(other_flat, user)
    add_member(flat, other_user)
    task_type = default_task_types[0]

    def task(flat_, assignee, **fields) -> Task:
        return Task(flat=flat_, task_type=task_type, title="Zadanie", due_date=date.today(), assignee=assignee, **fields)

    open_task = task(flat, user)
    done_task = task(flat, user, status=TaskStatus.DONE, done_at=utcnow())
    colleague_task = task(flat, other_user)
    other_flat_task = task(other_flat, user)
    db.session.add_all([open_task, done_task, colleague_task, other_flat_task])
    db.session.commit()

    released = TaskRepository().unassign_open_tasks(flat.id, user.id)
    db.session.commit()

    assert released == 1
    assert open_task.assignee_id is None
    assert done_task.assignee_id == user.id
    assert colleague_task.assignee_id == other_user.id
    assert other_flat_task.assignee_id == user.id
