"""Lista mieszkań zalogowanego użytkownika."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from backend.core.extensions import db
from backend.models import (
    Flat,
    Invite,
    MemberRole,
    MembershipStatus,
    Recurrence,
    Task,
    TaskStatus,
)
from backend.models.types import utcnow
from backend.security.tokens import hash_token


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


def test_create_flat_makes_creator_active_admin(client, login, make_user) -> None:
    user = make_user()
    login(user)

    response = client.post("/flats/new", data={"name": "  Nasze mieszkanie  "})

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/flats/1")
    flat = db.session.get(Flat, 1)
    membership = flat.memberships[0]
    assert flat.name == "Nasze mieszkanie"
    assert membership.user_id == user.id
    assert membership.role is MemberRole.ADMIN
    assert membership.status is MembershipStatus.ACTIVE


def test_create_flat_validates_name(client, login, make_user) -> None:
    login(make_user())

    response = client.post("/flats/new", data={"name": " "})

    assert response.status_code == 200
    assert "Podaj nazwę mieszkania." in response.get_data(as_text=True)


def test_flat_dashboard_and_member_routes_are_scoped(client, login, make_user, make_flat) -> None:
    owner, outsider = make_user(), make_user()
    flat = make_flat(admin=owner)
    login(outsider)

    assert client.get(f"/flats/{flat.id}").status_code == 404
    assert client.get(f"/flats/{flat.id}/members").status_code == 404


def test_member_cannot_use_admin_member_actions(client, login, make_user, make_flat, add_member) -> None:
    admin, member = make_user(), make_user()
    flat = make_flat(admin=admin)
    target = add_member(flat, make_user())
    add_member(flat, member)
    login(member)

    response = client.post(f"/flats/{flat.id}/members/{target.id}/remove")

    assert response.status_code == 403
    assert target in db.session


def test_invite_request_requires_admin_approval(client, login, make_user) -> None:
    admin, applicant = make_user(), make_user()
    login(admin)

    created = client.post("/flats/new", data={"name": "Wspólny lokal"})
    assert created.status_code == 302
    flat_id = int(created.headers["Location"].rsplit("/", 1)[1])

    invite_page = client.post(f"/flats/{flat_id}/invites")
    assert invite_page.status_code == 200
    token = db.session.query(Invite).one().token_hash
    html = invite_page.get_data(as_text=True)
    assert token not in html
    assert "Skopiuj link i przekaż go współlokatorowi" in html
    invite_link = next(
        line.split('href="', 1)[1].split('"', 1)[0]
        for line in html.splitlines()
        if "/join/" in line and 'href="' in line
    )
    raw_token = invite_link.rsplit("/", 1)[1]
    invite = db.session.query(Invite).one()
    assert invite.token_hash == hash_token(raw_token)

    login(applicant)
    request_page = client.post(invite_link)
    assert request_page.status_code == 200
    assert "Prośba oczekuje na akceptację administratora." in request_page.get_data(as_text=True)
    membership = next(item for item in invite.flat.memberships if item.user_id == applicant.id)
    assert membership.status is MembershipStatus.PENDING

    login(admin)
    approved = client.post(f"/flats/{flat_id}/members/{membership.id}/approve")
    assert approved.status_code == 302
    assert membership.status is MembershipStatus.ACTIVE


def test_rejected_join_request_is_not_duplicated(client, login, make_user, make_flat, add_member) -> None:
    admin, applicant = make_user(), make_user()
    flat = make_flat(admin=admin)
    rejected = add_member(flat, applicant, status=MembershipStatus.REJECTED)
    invite = Invite(
        flat=flat,
        created_by=admin,
        token_hash=hash_token("join-token"),
        expires_at=utcnow() + timedelta(days=1),
    )
    db.session.add(invite)
    db.session.commit()
    login(applicant)

    response = client.post("/join/join-token")

    assert response.status_code == 200
    assert "Twoja poprzednia prośba została odrzucona" in response.get_data(as_text=True)
    assert len(flat.memberships) == 2
    assert rejected.status is MembershipStatus.REJECTED


def test_expired_invite_cannot_be_used(client, login, make_user, make_flat) -> None:
    admin, applicant = make_user(), make_user()
    flat = make_flat(admin=admin)
    invite = Invite(
        flat=flat,
        created_by=admin,
        token_hash=hash_token("expired-token"),
        expires_at=datetime(2020, 1, 1, tzinfo=UTC),
    )
    db.session.add(invite)
    db.session.commit()
    login(applicant)

    assert client.get("/join/expired-token").status_code == 404


def test_admin_transfer_allows_previous_admin_to_leave(client, login, make_user, make_flat, add_member) -> None:
    old_admin, new_admin = make_user(), make_user()
    flat = make_flat(admin=old_admin)
    target = add_member(flat, new_admin)
    login(old_admin)

    transferred = client.post(f"/flats/{flat.id}/members/{target.id}/make-admin")
    assert transferred.status_code == 302
    assert target.role is MemberRole.ADMIN
    assert flat.memberships[0].role is MemberRole.MEMBER

    left = client.post(f"/flats/{flat.id}/leave")
    assert left.status_code == 302
    assert left.headers["Location"].endswith("/flats")
    assert all(item.user_id != old_admin.id for item in flat.memberships)


def test_last_admin_must_confirm_flat_deletion(client, login, make_user, make_flat) -> None:
    admin = make_user()
    flat = make_flat(admin=admin)
    login(admin)

    leave = client.post(f"/flats/{flat.id}/leave")
    assert leave.status_code == 302
    assert leave.headers["Location"].endswith(f"/flats/{flat.id}/delete")

    wrong_name = client.post(
        f"/flats/{flat.id}/delete",
        data={"confirmation": "inna nazwa"},
    )
    assert wrong_name.status_code == 200
    assert "Wpisana nazwa nie pasuje" in wrong_name.get_data(as_text=True)
    assert db.session.get(type(flat), flat.id) is not None

    deleted = client.post(f"/flats/{flat.id}/delete", data={"confirmation": flat.name})
    assert deleted.status_code == 302
    assert db.session.get(type(flat), flat.id) is None


def test_removing_member_releases_open_tasks(client, login, make_user, make_flat, add_member, default_task_types) -> None:
    admin, member = make_user(), make_user()
    flat = make_flat(admin=admin)
    membership = add_member(flat, member)
    task = Task(
        flat=flat,
        task_type=default_task_types[0],
        title="Wynieść śmieci",
        due_date=date.today(),
        assignee=member,
    )
    db.session.add(task)
    db.session.commit()
    login(admin)

    response = client.post(f"/flats/{flat.id}/members/{membership.id}/remove")

    assert response.status_code == 302
    assert task.assignee_id is None
    assert membership not in flat.memberships


def test_invite_can_be_revoked(client, login, make_user, make_flat) -> None:
    admin = make_user()
    flat = make_flat(admin=admin)
    invite = Invite(
        flat=flat,
        created_by=admin,
        token_hash=hash_token("revoke-token"),
        expires_at=utcnow() + timedelta(days=1),
    )
    db.session.add(invite)
    db.session.commit()
    login(admin)

    response = client.post(f"/flats/{flat.id}/invites/{invite.id}/revoke")

    assert response.status_code == 302
    assert invite.revoked is True
    login(make_user())
    assert client.get("/join/revoke-token").status_code == 404
