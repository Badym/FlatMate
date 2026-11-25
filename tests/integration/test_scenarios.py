"""Testy integracyjne: scenariusze, w których kilka funkcji aplikacji działa razem.

Każdy scenariusz przechodzi przez aplikację jak użytkownik w przeglądarce:
formularze wysyłane przez HTTP, logowanie hasłem, linki i przyciski odczytane
ze stron. Każda osoba ma własnego klienta (osobne ciasteczka sesji). Konta,
mieszkania i zadania powstają w samym teście, a baza jest czyszczona po każdym
teście (tests/conftest.py).
"""

from __future__ import annotations

import re
import secrets
from datetime import date, timedelta

import pytest
from flask.testing import FlaskClient

from backend.core.extensions import db
from backend.models import MemberRole, Membership, MembershipStatus, Task
from backend.repositories import UserRepository

pytestmark = pytest.mark.integration


def _register(client: FlaskClient, name: str, email: str, password: str) -> None:
    response = client.post(
        "/register",
        data={"display_name": name, "email": email, "password": password, "password_confirm": password},
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/flats")


def _login(client: FlaskClient, email: str, password: str):
    return client.post("/login", data={"email": email, "password": password})


def _user_id(email: str) -> int:
    return UserRepository().get_by_email(email).id


def _create_flat(client: FlaskClient, name: str) -> int:
    response = client.post("/flats/new", data={"name": name})
    assert response.status_code == 302
    return int(response.headers["Location"].rsplit("/", 1)[1])


def _invite_link(client: FlaskClient, flat_id: int) -> str:
    """Admin generuje zaproszenie i odczytuje link ze strony, tak jak kopiuje go użytkownik."""
    html = client.post(f"/flats/{flat_id}/invites").get_data(as_text=True)
    match = re.search(r'href="(/join/[^"]+)"', html)
    assert match is not None
    return match.group(1)


def _member_action(client: FlaskClient, flat_id: int, action: str) -> str:
    """Adres przycisku z listy członków, np. ``approve`` albo ``make-admin``."""
    html = client.get(f"/flats/{flat_id}/members").get_data(as_text=True)
    urls = re.findall(rf'action="(/flats/{flat_id}/members/\d+/{action})"', html)
    assert len(urls) == 1
    return urls[0]


def _task_data(title: str, task_type_id: int, due_date: date, assignee_id: int | None) -> dict[str, str]:
    return {
        "title": title,
        "description": "",
        "task_type_id": str(task_type_id),
        "due_date": due_date.isoformat(),
        "assignee_id": "pool" if assignee_id is None else str(assignee_id),
    }


def _task_list(client: FlaskClient, flat_id: int, list_filter: str) -> str:
    response = client.get(f"/flats/{flat_id}/tasks", query_string={"filter": list_filter})
    assert response.status_code == 200
    return response.get_data(as_text=True)


def test_new_user_registers_logs_in_again_and_updates_profile(client, app_ctx, test_password) -> None:
    _register(client, "Ola", "ola@example.com", test_password)
    assert "Konto zostało utworzone" in client.get("/flats").get_data(as_text=True)

    assert client.post("/logout").status_code == 302
    assert client.get("/flats").status_code == 302

    assert _login(client, "ola@example.com", test_password).status_code == 302
    updated = client.post(
        "/profile",
        data={"profile-display_name": "Ola Nowak", "profile-color_index": "3"},
        follow_redirects=True,
    )

    assert "Zapisano zmiany w profilu." in updated.get_data(as_text=True)
    user = UserRepository().get_by_email("ola@example.com")
    assert (user.display_name, user.color_index) == ("Ola Nowak", 3)
    assert "Ola Nowak" in client.get("/flats").get_data(as_text=True)


def test_changed_password_replaces_old_one_at_next_login(client, app_ctx, test_password) -> None:
    new_password = secrets.token_urlsafe(16)
    _register(client, "Kuba", "kuba@example.com", test_password)

    changed = client.post(
        "/profile/password",
        data={
            "password-current_password": test_password,
            "password-new_password": new_password,
            "password-new_password_confirm": new_password,
        },
        follow_redirects=True,
    )
    assert "Hasło zostało zmienione." in changed.get_data(as_text=True)
    assert client.post("/logout").status_code == 302

    assert _login(client, "kuba@example.com", test_password).status_code == 401
    assert _login(client, "kuba@example.com", new_password).status_code == 302
    assert client.get("/profile").status_code == 200


def test_roommate_joins_flat_through_invite_after_admin_approval(app, app_ctx, test_password) -> None:
    admin, roommate = app.test_client(), app.test_client()
    _register(admin, "Ola", "ola@example.com", test_password)
    flat_id = _create_flat(admin, "Mieszkanie na Kwiatowej")
    invite_link = _invite_link(admin, flat_id)

    _register(roommate, "Kuba", "kuba@example.com", test_password)
    requested = roommate.post(invite_link)
    assert "Prośba oczekuje na akceptację administratora." in requested.get_data(as_text=True)
    assert roommate.get(f"/flats/{flat_id}").status_code == 404

    approved = admin.post(_member_action(admin, flat_id, "approve"), follow_redirects=True)
    assert "Zaakceptowano prośbę o dołączenie." in approved.get_data(as_text=True)

    membership = (
        db.session.query(Membership)
        .filter_by(flat_id=flat_id, user_id=_user_id("kuba@example.com"))
        .one()
    )
    assert membership.status is MembershipStatus.ACTIVE
    assert membership.role is MemberRole.MEMBER
    assert "Mieszkanie na Kwiatowej" in roommate.get("/flats").get_data(as_text=True)
    assert roommate.get(f"/flats/{flat_id}").status_code == 200


def test_task_goes_from_creation_through_edit_to_deletion(
    client, app_ctx, default_task_types, test_password
) -> None:
    _register(client, "Ola", "ola@example.com", test_password)
    flat_id = _create_flat(client, "Mieszkanie")
    user_id = _user_id("ola@example.com")
    task_type_id = default_task_types[0].id

    created = client.post(
        f"/flats/{flat_id}/tasks/new",
        data=_task_data("Umyć okna", task_type_id, date.today() + timedelta(days=3), user_id),
        follow_redirects=True,
    )
    assert "Dodano zadanie." in created.get_data(as_text=True)
    assert "Umyć okna" in _task_list(client, flat_id, "mine")
    assert "Umyć okna" not in _task_list(client, flat_id, "pool")
    assert "Umyć okna" not in _task_list(client, flat_id, "overdue")

    edit_link = re.search(rf'href="(/flats/{flat_id}/tasks/\d+/edit)"', _task_list(client, flat_id, "all"))
    assert edit_link is not None
    edit_url = edit_link.group(1)
    edited = client.post(
        edit_url,
        data=_task_data("Umyć okna w kuchni", task_type_id, date.today() - timedelta(days=1), user_id),
        follow_redirects=True,
    )
    assert "Zapisano zmiany w zadaniu." in edited.get_data(as_text=True)
    assert "Umyć okna w kuchni" in _task_list(client, flat_id, "overdue")
    task = db.session.query(Task).one()
    assert (task.title, task.due_date) == ("Umyć okna w kuchni", date.today() - timedelta(days=1))

    deleted = client.post(edit_url.replace("/edit", "/delete"), follow_redirects=True)
    assert "Usunięto zadanie." in deleted.get_data(as_text=True)
    assert db.session.query(Task).count() == 0
    assert "Umyć okna" not in _task_list(client, flat_id, "all")


def test_admin_hands_over_flat_and_leaves_with_tasks_returned_to_pool(
    app, app_ctx, default_task_types, test_password
) -> None:
    admin, roommate = app.test_client(), app.test_client()
    _register(admin, "Ola", "ola@example.com", test_password)
    flat_id = _create_flat(admin, "Mieszkanie")
    invite_link = _invite_link(admin, flat_id)
    _register(roommate, "Kuba", "kuba@example.com", test_password)
    roommate.post(invite_link)
    admin.post(_member_action(admin, flat_id, "approve"))
    admin.post(
        f"/flats/{flat_id}/tasks/new",
        data=_task_data(
            "Sprzątanie łazienki",
            default_task_types[0].id,
            date.today() + timedelta(days=2),
            _user_id("ola@example.com"),
        ),
    )

    blocked = admin.post(f"/flats/{flat_id}/leave", follow_redirects=True)
    assert "Przed opuszczeniem mieszkania przekaż rolę administratora" in blocked.get_data(as_text=True)

    handed_over = admin.post(_member_action(admin, flat_id, "make-admin"), follow_redirects=True)
    assert "Przekazano rolę administratora." in handed_over.get_data(as_text=True)
    left = admin.post(f"/flats/{flat_id}/leave", follow_redirects=True)
    assert "Opuszczono mieszkanie." in left.get_data(as_text=True)
    assert admin.get(f"/flats/{flat_id}").status_code == 404

    assert roommate.get(f"/flats/{flat_id}/invites").status_code == 200
    assert "Sprzątanie łazienki" in _task_list(roommate, flat_id, "pool")
    assert db.session.query(Task).one().assignee_id is None
