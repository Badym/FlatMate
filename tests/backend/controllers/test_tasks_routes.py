from __future__ import annotations

from datetime import date

from backend.core.extensions import db
from backend.models import Recurrence, Task, TaskStatus, TaskType


def _task(flat, task_type, author, **fields) -> Task:
    task = Task(
        flat=flat,
        task_type=task_type,
        created_by=author,
        title="Odkurzyć salon",
        due_date=date(2026, 11, 12),
        **fields,
    )
    db.session.add(task)
    db.session.commit()
    return task


def test_member_can_create_one_off_task_for_self_or_pool(
    client, login, make_user, make_flat, add_member, default_task_types
) -> None:
    admin, member = make_user(), make_user()
    flat = make_flat(admin=admin)
    add_member(flat, member)
    login(member)

    response = client.post(
        f"/flats/{flat.id}/tasks/new",
        data={
            "title": "  Odkurzyć salon ",
            "description": "Przed wizytą",
            "task_type_id": str(default_task_types[0].id),
            "due_date": "2026-11-12",
            "assignee_id": str(member.id),
        },
    )

    assert response.status_code == 302
    task = db.session.query(Task).one()
    assert task.flat_id == flat.id
    assert task.created_by_id == member.id
    assert task.assignee_id == member.id
    assert task.title == "Odkurzyć salon"
    assert task.description == "Przed wizytą"
    assert task.due_date == date(2026, 11, 12)
    assert task.recurrence is Recurrence.NONE
    assert task.status is TaskStatus.OPEN

    pool_response = client.post(
        f"/flats/{flat.id}/tasks/new",
        data={
            "title": "Wynieść śmieci",
            "task_type_id": str(default_task_types[0].id),
            "due_date": "2026-11-13",
            "assignee_id": "pool",
        },
    )
    assert pool_response.status_code == 302
    assert db.session.query(Task).count() == 2
    assert db.session.query(Task).order_by(Task.id.desc()).first().assignee_id is None


def test_admin_can_assign_new_task_to_active_member(
    client, login, make_user, make_flat, add_member, default_task_types
) -> None:
    admin, member = make_user(), make_user()
    flat = make_flat(admin=admin)
    add_member(flat, member)
    login(admin)

    response = client.post(
        f"/flats/{flat.id}/tasks/new",
        data={
            "title": "Posprzątać kuchnię",
            "task_type_id": str(default_task_types[0].id),
            "due_date": "2026-11-13",
            "assignee_id": str(member.id),
        },
    )

    assert response.status_code == 302
    assert db.session.query(Task).one().assignee_id == member.id


def test_author_can_edit_and_delete_own_task(
    client, login, make_user, make_flat, add_member, default_task_types
) -> None:
    admin, author, other = make_user(), make_user(), make_user()
    flat = make_flat(admin=admin)
    add_member(flat, author)
    add_member(flat, other)
    task = _task(flat, default_task_types[0], author, assignee_id=author.id)
    login(author)

    edited = client.post(
        f"/flats/{flat.id}/tasks/{task.id}/edit",
        data={
            "title": "Umyć podłogę",
            "description": "Dokładnie",
            "task_type_id": str(default_task_types[1].id),
            "due_date": "2026-11-15",
            "assignee_id": "pool",
        },
    )
    assert edited.status_code == 302
    assert task.title == "Umyć podłogę"
    assert task.task_type_id == default_task_types[1].id
    assert task.due_date == date(2026, 11, 15)
    assert task.assignee_id is None

    deleted = client.post(f"/flats/{flat.id}/tasks/{task.id}/delete")
    assert deleted.status_code == 302
    assert db.session.get(Task, task.id) is None


def test_admin_can_manage_other_members_task(
    client, login, make_user, make_flat, add_member, default_task_types
) -> None:
    admin, author = make_user(), make_user()
    flat = make_flat(admin=admin)
    add_member(flat, author)
    task = _task(flat, default_task_types[0], author)
    login(admin)

    response = client.post(
        f"/flats/{flat.id}/tasks/{task.id}/edit",
        data={
            "title": "Umyć łazienkę",
            "task_type_id": str(default_task_types[1].id),
            "due_date": "2026-11-16",
            "assignee_id": str(author.id),
        },
    )

    assert response.status_code == 302
    assert task.title == "Umyć łazienkę"


def test_member_cannot_manage_another_authors_task(
    client, login, make_user, make_flat, add_member, default_task_types
) -> None:
    admin, author, member = make_user(), make_user(), make_user()
    flat = make_flat(admin=admin)
    add_member(flat, author)
    add_member(flat, member)
    task = _task(flat, default_task_types[0], author)
    login(member)

    assert client.get(f"/flats/{flat.id}/tasks/{task.id}/edit").status_code == 403
    assert client.post(f"/flats/{flat.id}/tasks/{task.id}/delete").status_code == 403
    assert db.session.get(Task, task.id) is not None


def test_task_routes_are_scoped_to_flat(
    client, login, make_user, make_flat, default_task_types
) -> None:
    owner, outsider = make_user(), make_user()
    flat = make_flat(admin=owner)
    task = _task(flat, default_task_types[0], owner)
    login(outsider)

    assert client.get(f"/flats/{flat.id}/tasks").status_code == 404
    assert client.get(f"/flats/{flat.id}/tasks/{task.id}/edit").status_code == 404
    assert client.post(f"/flats/{flat.id}/tasks/{task.id}/delete").status_code == 404


def test_member_can_open_task_list_and_admin_controls_are_visible(
    client, login, make_user, make_flat, default_task_types
) -> None:
    admin = make_user()
    flat = make_flat(admin=admin)
    _task(flat, default_task_types[0], admin)
    login(admin)

    response = client.get(f"/flats/{flat.id}/tasks")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Odkurzyć salon" in html
    assert "Edytuj" in html
    assert "Usuń" in html


def test_task_form_rejects_type_from_another_flat(
    client, login, make_user, make_flat, default_task_types
) -> None:
    admin = make_user()
    flat = make_flat(admin=admin)
    foreign_flat = make_flat()
    foreign_type = TaskType(flat_id=foreign_flat.id, name="Obcy typ")
    db.session.add(foreign_type)
    db.session.commit()
    login(admin)

    response = client.post(
        f"/flats/{flat.id}/tasks/new",
        data={
            "title": "Niepoprawne zadanie",
            "task_type_id": str(foreign_type.id),
            "due_date": "2026-11-16",
            "assignee_id": "pool",
        },
    )

    assert response.status_code == 200
    assert "Wybierz prawidłową opcję." in response.get_data(as_text=True)
    assert db.session.query(Task).count() == 0
