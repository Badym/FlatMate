"""Lista mieszkań zalogowanego użytkownika."""

from __future__ import annotations

from datetime import date

from backend.core.extensions import db
from backend.models import MembershipStatus, Recurrence, Task, TaskStatus
from backend.models.types import utcnow


def test_requires_login(client) -> None:
    response = client.get("/flats")

    assert response.status_code == 302
    assert "/login?next=" in response.headers["Location"]


def test_empty_state(client, login, make_user) -> None:
    login(make_user())

    html = client.get("/flats").get_data(as_text=True)

    assert "Nie należysz jeszcze do żadnego mieszkania" in html


def test_lists_only_active_memberships(client, login, make_user, make_flat, add_member) -> None:
    user = make_user()
    own = make_flat(admin=user, name="Moje własne")
    joined = make_flat(name="Dołączone")
    add_member(joined, user)
    pending = make_flat(name="Czeka na akceptację")
    add_member(pending, user, status=MembershipStatus.PENDING)
    make_flat(name="Cudze")
    login(user)

    html = client.get("/flats").get_data(as_text=True)

    assert own.name in html and joined.name in html
    assert "Czeka na akceptację" not in html
    assert "Cudze" not in html
    assert html.count(">admin<") == 1


def test_counts_open_tasks_without_series_templates(client, login, make_user, make_flat, default_task_types) -> None:
    user = make_user()
    flat = make_flat(admin=user)
    task_type = default_task_types[0]

    def task(**fields) -> Task:
        return Task(flat=flat, task_type=task_type, title="Zadanie", due_date=date.today(), **fields)

    template = task(recurrence=Recurrence.WEEKLY)
    db.session.add_all(
        [
            task(),
            task(),
            task(status=TaskStatus.DONE, done_at=utcnow()),
            template,
            task(parent=template, occurrence_index=0),
        ]
    )
    db.session.commit()
    login(user)

    html = client.get("/flats").get_data(as_text=True)

    assert "3 zadania do zrobienia" in html


def test_flat_name_is_escaped(client, login, make_user, make_flat) -> None:
    user = make_user()
    make_flat(admin=user, name="<img src=x onerror=alert(1)>")
    login(user)

    html = client.get("/flats").get_data(as_text=True)

    assert "<img src=x" not in html
    assert "&lt;img src=x onerror=alert(1)&gt;" in html
