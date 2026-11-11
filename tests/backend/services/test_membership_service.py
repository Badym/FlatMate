from __future__ import annotations

from datetime import date

from backend.core.extensions import db
from backend.models import MembershipStatus, Task
from backend.services.membership_service import MembershipService


def test_member_choices_contain_only_active_members(make_user, make_flat, add_member) -> None:
    admin = make_user(display_name="Ola")
    flat = make_flat(admin=admin)
    member = make_user(display_name="Kuba")
    add_member(flat, member)
    add_member(flat, make_user(display_name="Czeka"), status=MembershipStatus.PENDING)
    outsider = make_user()
    service = MembershipService()

    assert service.member_choices(flat.id) == [(admin.id, "Ola"), (member.id, "Kuba")]
    assert service.is_active_member(flat.id, member.id)
    assert not service.is_active_member(flat.id, outsider.id)


def test_release_member_tasks_returns_them_to_pool(make_user, make_flat, add_member, default_task_types) -> None:
    flat, member = make_flat(), make_user()
    add_member(flat, member)
    task = Task(flat=flat, task_type=default_task_types[0], title="Śmieci", due_date=date.today(), assignee=member)
    db.session.add(task)
    db.session.commit()

    released = MembershipService().release_member_tasks(flat.id, member.id)
    db.session.commit()

    assert released == 1
    assert task.assignee_id is None
