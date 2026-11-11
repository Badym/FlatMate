"""Komponenty i filtry szablonów używane przez strony z prawdziwymi danymi."""

from __future__ import annotations

import pytest
from flask import render_template_string

from backend.controllers import plural_pl
from backend.models import User


@pytest.mark.parametrize(
    ("count", "expected"),
    [(0, "zadań"), (1, "zadanie"), (2, "zadania"), (4, "zadania"), (5, "zadań"), (12, "zadań"), (14, "zadań"), (22, "zadania"), (25, "zadań"), (104, "zadania")],
)
def test_polish_plural(count: int, expected: str) -> None:
    assert plural_pl(count, "zadanie", "zadania", "zadań") == expected


@pytest.mark.parametrize(
    ("display_name", "initials"),
    [("Ola Nowak", "ON"), ("kuba", "KU"), ("Łucja Żak-Ślęzak", "ŁŻ"), ("X", "X"), ("   ", "?")],
)
def test_user_initials(display_name: str, initials: str) -> None:
    assert User(display_name=display_name).initials == initials


def _avatar(app, member) -> str:
    with app.test_request_context():
        return render_template_string(
            '{% from "components/avatar.html" import avatar %}{{ avatar(member, "sm") }}', member=member
        )


def test_avatar_shows_initials_in_user_color(app) -> None:
    html = _avatar(app, User(display_name="Ola Nowak", color_index=3))

    assert 'class="fm-avatar fm-avatar-sm u-color-3"' in html
    assert ">ON<" in html


def test_avatar_shows_uploaded_image(app) -> None:
    html = _avatar(app, User(display_name="Ola", color_index=0, avatar_filename="a" * 32 + ".png"))

    assert '<img class="fm-avatar fm-avatar-img fm-avatar-sm"' in html
    assert 'src="/static/uploads/avatars/' + "a" * 32 + '.png"' in html


def test_avatar_without_person_is_empty_slot(app) -> None:
    assert "fm-avatar-empty" in _avatar(app, None)


def test_navbar_for_logged_in_user(client, login, make_user) -> None:
    login(make_user(display_name="Ola Nowak"))

    html = client.get("/flats").get_data(as_text=True)

    assert "Ola Nowak" in html
    assert 'action="/logout"' in html
    assert 'href="/flats"' in html
    assert ">Zaloguj się<" not in html
