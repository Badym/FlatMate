"""Dekoratory dostępu do mieszkań i ładowanie użytkownika z sesji (SR-4, T-01, T-02, D-13)."""

from __future__ import annotations

import json
import logging

import pytest
from flask import Flask, g

from backend.core.extensions import db
from backend.models import MembershipStatus
from backend.security.access import flat_admin_required, flat_member_required
from backend.security.session import load_user


@pytest.fixture
def protected_app(app: Flask) -> Flask:
    @app.get("/test/flats/<int:flat_id>/member")
    @flat_member_required
    def member_view(flat_id: int) -> str:
        return f"member:{g.flat.id}:{g.membership.user_id}"

    @app.get("/test/flats/<int:flat_id>/admin")
    @flat_admin_required
    def admin_view(flat_id: int) -> str:
        return "admin"

    @app.get("/test/no-flat")
    @flat_member_required
    def misconfigured_view() -> str:
        return "nigdy"

    return app


@pytest.fixture
def flat(protected_app, make_flat):
    return make_flat()


def _admin(flat):
    return next(m.user for m in flat.memberships if m.is_admin)


def test_anonymous_is_sent_to_login(client, flat) -> None:
    response = client.get(f"/test/flats/{flat.id}/member")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_outsider_gets_404_and_event_is_logged(client, login, flat, make_user, caplog) -> None:
    login(make_user())

    with caplog.at_level(logging.INFO, logger="flatmate.security"):
        response = client.get(f"/test/flats/{flat.id}/member")

    assert response.status_code == 404
    event = json.loads(caplog.records[-1].getMessage())
    assert event["event"] == "access_denied"
    assert event["reason"] == "not_member"
    assert event["flat_id"] == flat.id


def test_missing_flat_gets_404(client, login, flat) -> None:
    login(_admin(flat))

    assert client.get("/test/flats/999999/member").status_code == 404


@pytest.mark.parametrize("status", [MembershipStatus.PENDING, MembershipStatus.REJECTED])
def test_inactive_membership_gets_404(client, login, flat, make_user, add_member, status) -> None:
    user = make_user()
    add_member(flat, user, status=status)
    login(user)

    assert client.get(f"/test/flats/{flat.id}/member").status_code == 404


def test_member_sees_flat_but_not_admin_routes(client, login, flat, make_user, add_member) -> None:
    member = make_user()
    add_member(flat, member)
    login(member)

    member_response = client.get(f"/test/flats/{flat.id}/member")
    admin_response = client.get(f"/test/flats/{flat.id}/admin")

    assert member_response.get_data(as_text=True) == f"member:{flat.id}:{member.id}"
    assert admin_response.status_code == 403


def test_admin_sees_admin_routes(client, login, flat) -> None:
    login(_admin(flat))

    assert client.get(f"/test/flats/{flat.id}/admin").get_data(as_text=True) == "admin"


def test_member_of_other_flat_cannot_use_its_id(client, login, flat, make_flat) -> None:
    other_flat = make_flat()
    login(_admin(other_flat))

    assert client.get(f"/test/flats/{flat.id}/member").status_code == 404
    assert client.get(f"/test/flats/{flat.id}/admin").status_code == 404


def test_route_without_flat_id_is_a_programming_error(client, login, flat) -> None:
    login(_admin(flat))

    with pytest.raises(RuntimeError, match="flat_id"):
        client.get("/test/no-flat")


class TestLoadUser:
    def test_finds_user_by_session_token(self, make_user) -> None:
        user = make_user()

        assert load_user(user.session_token) == user

    @pytest.mark.parametrize("token", ["", "abc", "x" * 64])
    def test_rejects_unknown_or_malformed_token(self, app_ctx, token: str) -> None:
        assert load_user(token) is None

    def test_old_token_stops_working_after_rotation(self, make_user, client, login, flat) -> None:
        admin = _admin(flat)
        login(admin)
        assert client.get(f"/test/flats/{flat.id}/member").status_code == 200

        admin.rotate_session_token()
        db.session.commit()

        assert client.get(f"/test/flats/{flat.id}/member").status_code == 302
