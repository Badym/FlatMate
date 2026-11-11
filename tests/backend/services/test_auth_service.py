"""Logika kont bez warstwy HTTP: blokada konta, stały czas, rotacja tokenów."""

from __future__ import annotations

from datetime import timedelta

import pytest

from backend.core.constants import LOGIN_LOCK_MINUTES, LOGIN_MAX_FAILURES
from backend.core.extensions import db
from backend.models.types import utcnow
from backend.repositories import UserRepository
from backend.security import passwords
from backend.services import auth_service
from backend.services.auth_service import (
    AuthService,
    EmailTakenError,
    InvalidCurrentPasswordError,
    SamePasswordError,
)

NEW_PASSWORD = "inne-dlugie-haslo-77"  # gitleaks:allow (wymyślone hasło testowe)


class TestAuthenticate:
    def test_unknown_account_still_checks_a_password_hash(self, app_ctx, monkeypatch) -> None:
        calls = []
        monkeypatch.setattr(auth_service, "verify_password", lambda h, p: calls.append(h) or False)

        assert AuthService().authenticate("nikt@example.com", "cokolwiek-123") is None
        assert calls == [None]

    def test_locked_account_still_checks_password(self, make_user, test_password, monkeypatch) -> None:
        user = make_user(locked_until=utcnow() + timedelta(minutes=5))
        calls = []
        real = auth_service.verify_password
        monkeypatch.setattr(auth_service, "verify_password", lambda h, p: calls.append(h) or real(h, p))

        assert AuthService().authenticate(user.email, test_password) is None
        assert calls == [user.password_hash]

    def test_lock_after_exactly_max_failures(self, make_user) -> None:
        user = make_user()
        service = AuthService()

        for _ in range(LOGIN_MAX_FAILURES - 1):
            service.authenticate(user.email, "zle-haslo-123456")
        assert user.locked_until is None
        assert user.failed_logins == LOGIN_MAX_FAILURES - 1

        service.authenticate(user.email, "zle-haslo-123456")

        assert user.failed_logins == 0
        remaining = user.locked_until - utcnow()
        assert timedelta(minutes=LOGIN_LOCK_MINUTES - 1) < remaining <= timedelta(minutes=LOGIN_LOCK_MINUTES)

    def test_success_resets_failures(self, make_user, test_password) -> None:
        user = make_user(failed_logins=4)

        assert AuthService().authenticate(user.email, test_password) == user
        assert user.failed_logins == 0


class TestRegister:
    def test_rejects_taken_email(self, make_user) -> None:
        make_user(email="ola@example.com")

        with pytest.raises(EmailTakenError):
            AuthService().register(display_name="Ola", email="Ola@example.com", password=NEW_PASSWORD)

    def test_concurrent_registration_is_reported_as_taken(self, make_user, monkeypatch) -> None:
        make_user(email="ola@example.com")
        monkeypatch.setattr(UserRepository, "get_by_email", lambda self, email: None)

        with pytest.raises(EmailTakenError):
            AuthService().register(display_name="Ola", email="ola@example.com", password=NEW_PASSWORD)
        db.session.rollback()


class TestSessionTokens:
    def test_logout_rotates_token(self, make_user) -> None:
        user = make_user()
        old_token = user.session_token

        AuthService().logout(user)

        assert user.session_token != old_token

    def test_change_password_rotates_token(self, make_user, test_password) -> None:
        user = make_user()
        old_token = user.session_token

        AuthService().change_password(user, test_password, NEW_PASSWORD)

        assert user.session_token != old_token
        assert passwords.verify_password(user.password_hash, NEW_PASSWORD)

    def test_change_password_errors(self, make_user, test_password) -> None:
        user = make_user()
        old_token = user.session_token

        with pytest.raises(InvalidCurrentPasswordError):
            AuthService().change_password(user, "zle-obecne-haslo", NEW_PASSWORD)
        with pytest.raises(SamePasswordError):
            AuthService().change_password(user, test_password, test_password)
        assert user.session_token == old_token
