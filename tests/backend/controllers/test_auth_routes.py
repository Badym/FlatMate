"""Rejestracja, logowanie i wylogowanie przez formularze (FR-1, SR-1–SR-3, T-03, T-07)."""

from __future__ import annotations

import json
import logging
from datetime import timedelta
from urllib.parse import quote

import pytest

from backend.controllers.auth_controller import EMAIL_TAKEN_MESSAGE
from backend.core.constants import LOGIN_MAX_FAILURES, PASSWORD_MIN_LENGTH, USER_COLORS
from backend.core.extensions import db
from backend.models import User
from backend.models.types import utcnow
from backend.repositories import UserRepository
from backend.services.auth_service import LOGIN_FAILED_MESSAGE
from backend.services.demo_seed_service import DEMO_FLAT_NAME, DemoSeedService, demo_email

NEW_PASSWORD = "dluga-fraza-do-testow"  # gitleaks:allow (wymyślone hasło testowe)
MISMATCHED_PASSWORD = NEW_PASSWORD + "-inne"


def _login(client, email: str, password: str, next_url: str | None = None):
    url = "/login" if next_url is None else f"/login?next={quote(next_url, safe='')}"
    return client.post(url, data={"email": email, "password": password})


def _register(client, **fields):
    data = {
        "display_name": "Ola",
        "email": "ola@example.com",
        "password": NEW_PASSWORD,
        "password_confirm": NEW_PASSWORD,
    }
    data.update(fields)
    return client.post("/register", data=data)


def _is_logged_in(client) -> bool:
    return client.get("/flats").status_code == 200


def _reload(user: User) -> User:
    db.session.expire_all()
    return db.session.get(User, user.id)


class TestLoginPage:
    def test_renders_form(self, client) -> None:
        html = client.get("/login").get_data(as_text=True)

        assert 'name="email"' in html
        assert 'name="password"' in html
        assert 'autocomplete="current-password"' in html

    def test_forms_include_csrf_token_when_enabled(self, make_app) -> None:
        client = make_app(WTF_CSRF_ENABLED=True).test_client()

        for url in ("/login", "/register"):
            assert 'name="csrf_token"' in client.get(url).get_data(as_text=True)

    def test_invalid_email_format_is_a_form_error(self, client) -> None:
        response = client.post("/login", data={"email": "nie-email", "password": "cokolwiek"})

        assert response.status_code == 200
        assert "Podaj poprawny adres e-mail." in response.get_data(as_text=True)

    def test_logged_in_user_is_redirected_away(self, client, login, make_user) -> None:
        login(make_user())

        assert client.get("/login").headers["Location"].endswith("/flats")
        assert client.get("/register").headers["Location"].endswith("/flats")


class TestLogin:
    def test_success_redirects_to_flats(self, client, make_user, test_password) -> None:
        user = make_user()

        response = _login(client, user.email, test_password)

        assert response.status_code == 302
        assert response.headers["Location"].endswith("/flats")
        assert _is_logged_in(client)

    def test_email_is_case_insensitive(self, client, make_user, test_password) -> None:
        user = make_user(email="ola@example.com")

        assert _login(client, "  OLA@Example.COM ", test_password).status_code == 302

    def test_wrong_password_and_unknown_email_look_the_same(self, client, make_user) -> None:
        user = make_user()

        wrong_password = _login(client, user.email, "zle-haslo-123456")
        unknown_email = _login(client, "nikt@example.com", "zle-haslo-123456")

        for response in (wrong_password, unknown_email):
            html = response.get_data(as_text=True)
            assert response.status_code == 401
            assert LOGIN_FAILED_MESSAGE in html
            assert "nie istnieje" not in html
        assert not _is_logged_in(client)

    def test_failed_login_is_logged_without_password(self, client, make_user, caplog) -> None:
        user = make_user()

        with caplog.at_level(logging.INFO, logger="flatmate.security"):
            _login(client, user.email, "zle-haslo-123456")

        event = json.loads(caplog.records[-1].getMessage())
        assert event["event"] == "login_failed"
        assert event["target_user_id"] == user.id
        assert "zle-haslo-123456" not in caplog.text

    def test_account_locks_after_max_failures(self, client, make_user, test_password) -> None:
        user = make_user()
        for _ in range(LOGIN_MAX_FAILURES):
            assert _login(client, user.email, "zle-haslo-123456").status_code == 401

        response = _login(client, user.email, test_password)

        assert response.status_code == 401
        assert LOGIN_FAILED_MESSAGE in response.get_data(as_text=True)
        assert _reload(user).locked_until > utcnow() + timedelta(minutes=14)

    def test_lock_expires(self, client, make_user, test_password) -> None:
        user = make_user(locked_until=utcnow() - timedelta(seconds=1), failed_logins=3)

        assert _login(client, user.email, test_password).status_code == 302
        user = _reload(user)
        assert user.locked_until is None
        assert user.failed_logins == 0

    def test_session_is_renewed_on_login(self, client, make_user, test_password) -> None:
        user = make_user()
        with client.session_transaction() as session:
            session["podrzucone"] = "wartosc-atakujacego"

        _login(client, user.email, test_password)

        with client.session_transaction() as session:
            assert "podrzucone" not in session
            assert session.permanent

    def test_session_cookie_flags(self, client, make_user, test_password) -> None:
        user = make_user()

        cookie = _login(client, user.email, test_password).headers["Set-Cookie"]

        assert "HttpOnly" in cookie
        assert "SameSite=Lax" in cookie

    @pytest.mark.parametrize("target", ["/profile", "/flats?tab=1"])
    def test_follows_safe_next(self, client, make_user, test_password, target: str) -> None:
        user = make_user()

        response = _login(client, user.email, test_password, next_url=target)

        assert response.headers["Location"].endswith(target)

    @pytest.mark.parametrize("target", ["https://evil.example/", "//evil.example", "/\\evil.example"])
    def test_ignores_unsafe_next(self, client, make_user, test_password, target: str) -> None:
        user = make_user()

        response = _login(client, user.email, test_password, next_url=target)

        assert response.headers["Location"].endswith("/flats")

    def test_protected_page_redirects_to_login_and_back(self, client, make_user, test_password) -> None:
        user = make_user()

        redirect = client.get("/flats?widok=lista")
        login_url = redirect.headers["Location"]
        response = client.post(login_url, data={"email": user.email, "password": test_password})

        assert "/login?next=" in login_url
        assert response.headers["Location"].endswith("/flats?widok=lista")


class TestRateLimit:
    @pytest.fixture
    def limited_app(self, make_app):
        return make_app(RATELIMIT_ENABLED=True)

    def test_ip_is_limited_after_five_failed_logins(self, limited_app, caplog) -> None:
        client = limited_app.test_client()
        for _ in range(5):
            assert _login(client, "nikt@example.com", "zle-haslo-123456").status_code == 401

        with caplog.at_level(logging.INFO, logger="flatmate.security"):
            response = _login(client, "nikt@example.com", "zle-haslo-123456")

        assert response.status_code == 429
        assert "Zbyt wiele prób" in response.get_data(as_text=True)
        assert any('"rate_limited"' in record.getMessage() for record in caplog.records)

    def test_successful_logins_are_not_counted(self, limited_app, make_user, test_password) -> None:
        user = make_user()

        for _ in range(7):
            assert _login(limited_app.test_client(), user.email, test_password).status_code == 302

    def test_registration_is_limited(self, limited_app) -> None:
        client = limited_app.test_client()
        for _ in range(10):
            assert _register(client, password_confirm=MISMATCHED_PASSWORD).status_code == 200

        assert _register(client, password_confirm=MISMATCHED_PASSWORD).status_code == 429


class TestRegister:
    def test_creates_account_and_logs_in(self, client, app_ctx) -> None:
        response = _register(client, display_name="  Ola Nowak ", email="Ola@Example.COM")

        assert response.headers["Location"].endswith("/flats")
        user = UserRepository().get_by_email("ola@example.com")
        assert user.display_name == "Ola Nowak"
        assert user.password_hash.startswith("scrypt:")
        assert NEW_PASSWORD not in user.password_hash
        assert 0 <= user.color_index < len(USER_COLORS)
        page = client.get("/flats").get_data(as_text=True)
        assert "Konto zostało utworzone" in page

    def test_rejects_taken_email(self, client, make_user) -> None:
        make_user(email="ola@example.com")

        response = _register(client, email="OLA@example.com")

        assert response.status_code == 200
        assert EMAIL_TAKEN_MESSAGE in response.get_data(as_text=True)
        assert db.session.query(User).count() == 1

    def test_requires_min_password_length(self, client, app_ctx) -> None:
        short = "a" * (PASSWORD_MIN_LENGTH - 1)

        response = _register(client, password=short, password_confirm=short)

        assert f"od {PASSWORD_MIN_LENGTH} do 128 znaków" in response.get_data(as_text=True)
        assert db.session.query(User).count() == 0

    def test_requires_matching_passwords(self, client) -> None:
        response = _register(client, password_confirm=NEW_PASSWORD + "x")

        assert "Hasła nie są takie same." in response.get_data(as_text=True)

    def test_user_input_is_escaped(self, client) -> None:
        payload = "<script>alert(1)</script>"

        html = _register(client, display_name=payload, email="zly").get_data(as_text=True)

        assert payload not in html
        assert "&lt;script&gt;" in html


class TestLogout:
    def test_requires_post(self, client, login, make_user) -> None:
        login(make_user())

        assert client.get("/logout").status_code == 405

    def test_logs_out_and_invalidates_copied_cookie(self, app, client, make_user, test_password) -> None:
        user = make_user()
        _login(client, user.email, test_password)
        cookie_name = app.config["SESSION_COOKIE_NAME"]
        stolen_cookie = client.get_cookie(cookie_name).value

        response = client.post("/logout")

        assert response.headers["Location"].endswith("/")
        assert not _is_logged_in(client)
        attacker = app.test_client()
        attacker.set_cookie(cookie_name, stolen_cookie)
        assert attacker.get("/flats").status_code == 302

    def test_requires_csrf_token(self, make_app, make_user) -> None:
        client = make_app(WTF_CSRF_ENABLED=True).test_client()
        user = make_user()
        with client.session_transaction() as session:
            session["_user_id"] = user.session_token

        assert client.post("/logout").status_code == 400

    def test_anonymous_is_sent_to_login(self, client) -> None:
        assert "/login" in client.post("/logout").headers["Location"]


def test_demo_account_can_log_in(app, client, default_task_types) -> None:
    password = "haslo-demo-do-testu"  # gitleaks:allow (wymyślone hasło testowe)
    DemoSeedService().seed(password)

    _login(client, demo_email("ola"), password)

    assert DEMO_FLAT_NAME in client.get("/flats").get_data(as_text=True)
