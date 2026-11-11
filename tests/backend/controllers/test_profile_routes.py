"""Profil: dane i kolor, zmiana hasła, awatar (FR-2, SR-9, D-13)."""

from __future__ import annotations

import re
from io import BytesIO

import pytest

from backend.core.extensions import db
from backend.models import User
from backend.security.passwords import verify_password
from backend.services.avatar_service import AVATAR_FILENAME_PATTERN

NEW_PASSWORD = "zupelnie-nowe-haslo-42"  # gitleaks:allow (wymyślone hasło testowe)


@pytest.fixture
def user(make_user, login) -> User:
    user = make_user(display_name="Ola Nowak", color_index=2)
    login(user)
    return user


def _reload(user: User) -> User:
    db.session.expire_all()
    return db.session.get(User, user.id)


def _upload(client, content: bytes, filename: str = "awatar.png"):
    return client.post(
        "/profile/avatar",
        data={"avatar-file": (BytesIO(content), filename)},
        content_type="multipart/form-data",
    )


@pytest.mark.parametrize(
    ("method", "url"),
    [("get", "/profile"), ("post", "/profile"), ("post", "/profile/password"), ("post", "/profile/avatar"), ("post", "/profile/avatar/delete")],
)
def test_requires_login(client, method: str, url: str) -> None:
    response = getattr(client, method)(url)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_profile_is_linked_in_navigation(client, user) -> None:
    html = client.get("/flats").get_data(as_text=True)

    assert 'href="/profile"' in html


def test_page_shows_current_data(client, user) -> None:
    html = client.get("/profile").get_data(as_text=True)

    assert 'value="Ola Nowak"' in html
    assert user.email in html
    assert re.search(r'<input checked[^>]*id="profile-color_index-2"', html)


class TestProfileData:
    def test_updates_name_and_color(self, client, user) -> None:
        response = client.post("/profile", data={"profile-display_name": "  Ola N. ", "profile-color_index": "5"})

        assert response.headers["Location"].endswith("/profile")
        user = _reload(user)
        assert (user.display_name, user.color_index) == ("Ola N.", 5)
        assert "Zapisano zmiany w profilu." in client.get("/profile").get_data(as_text=True)

    @pytest.mark.parametrize("color", ["12", "-1", "czerwony"])
    def test_rejects_color_outside_palette(self, client, user, color: str) -> None:
        response = client.post("/profile", data={"profile-display_name": "Ola", "profile-color_index": color})

        assert response.status_code == 200
        assert _reload(user).color_index == 2

    def test_rejects_too_short_name(self, client, user) -> None:
        response = client.post("/profile", data={"profile-display_name": "O", "profile-color_index": "1"})

        assert "Od 2 do 50 znaków." in response.get_data(as_text=True)
        assert _reload(user).display_name == "Ola Nowak"

    def test_name_is_escaped_in_navigation(self, client, user) -> None:
        client.post("/profile", data={"profile-display_name": "<b>Ola</b>", "profile-color_index": "1"})

        html = client.get("/flats").get_data(as_text=True)

        assert "<b>Ola</b>" not in html
        assert "&lt;b&gt;Ola&lt;/b&gt;" in html

    def test_requires_csrf_token(self, make_app, make_user) -> None:
        client = make_app(WTF_CSRF_ENABLED=True).test_client()
        with client.session_transaction() as session:
            session["_user_id"] = make_user().session_token

        assert client.post("/profile", data={"profile-display_name": "Ola"}).status_code == 400


class TestPasswordChange:
    def _change(self, client, current: str, new: str = NEW_PASSWORD, confirm: str | None = None):
        return client.post(
            "/profile/password",
            data={
                "password-current_password": current,
                "password-new_password": new,
                "password-new_password_confirm": confirm or new,
            },
        )

    def test_changes_password_and_logs_out_other_sessions(self, app, client, user, test_password) -> None:
        other_device = app.test_client()
        with other_device.session_transaction() as session:
            session["_user_id"] = user.session_token

        response = self._change(client, test_password)

        assert response.headers["Location"].endswith("/profile")
        assert verify_password(_reload(user).password_hash, NEW_PASSWORD)
        assert client.get("/profile").status_code == 200
        assert other_device.get("/profile").status_code == 302

    def test_rejects_wrong_current_password(self, client, user, test_password) -> None:
        response = self._change(client, "zle-obecne-haslo")

        assert "Obecne hasło jest nieprawidłowe." in response.get_data(as_text=True)
        assert verify_password(_reload(user).password_hash, test_password)

    def test_rejects_same_password(self, client, user, test_password) -> None:
        response = self._change(client, test_password, new=test_password)

        assert "Nowe hasło musi różnić się od obecnego." in response.get_data(as_text=True)

    def test_rejects_mismatched_confirmation(self, client, user, test_password) -> None:
        response = self._change(client, test_password, confirm=NEW_PASSWORD + "x")

        assert "Hasła nie są takie same." in response.get_data(as_text=True)

    def test_is_rate_limited(self, make_app, make_user) -> None:
        client = make_app(RATELIMIT_ENABLED=True).test_client()
        with client.session_transaction() as session:
            session["_user_id"] = make_user().session_token

        statuses = [self._change(client, "zle-obecne-haslo").status_code for _ in range(11)]

        assert statuses[:10] == [200] * 10
        assert statuses[10] == 429


class TestAvatar:
    def test_upload_saves_processed_file(self, client, user, avatar_dir, image_bytes) -> None:
        response = _upload(client, image_bytes("PNG", (600, 300)))

        assert response.headers["Location"].endswith("/profile")
        filename = _reload(user).avatar_filename
        assert AVATAR_FILENAME_PATTERN.fullmatch(filename)
        assert (avatar_dir / filename).is_file()
        assert f'/static/uploads/avatars/{filename}' in client.get("/profile").get_data(as_text=True)

    def test_new_upload_replaces_old_file(self, client, user, avatar_dir, image_bytes) -> None:
        _upload(client, image_bytes("PNG"))
        first = _reload(user).avatar_filename

        _upload(client, image_bytes("JPEG"), "nowy.jpg")

        second = _reload(user).avatar_filename
        assert second.endswith(".jpg")
        assert not (avatar_dir / first).exists()
        assert [path.name for path in avatar_dir.iterdir()] == [second]

    @pytest.mark.parametrize(
        ("content", "filename", "message"),
        [
            (b"<svg xmlns='http://www.w3.org/2000/svg' onload='alert(1)'/>", "awatar.png", "tylko obrazy PNG i JPEG"),
            (b"<html><script>alert(1)</script></html>", "awatar.jpg", "tylko obrazy PNG i JPEG"),
            (b"GIF89a", "awatar.gif", "tylko obrazy PNG i JPEG"),
        ],
    )
    def test_rejects_non_images(self, client, user, avatar_dir, content, filename, message) -> None:
        response = _upload(client, content, filename)

        assert response.status_code == 200
        assert message in response.get_data(as_text=True)
        assert _reload(user).avatar_filename is None
        assert not avatar_dir.exists() or not any(avatar_dir.iterdir())

    def test_rejects_file_over_two_megabytes(self, client, user) -> None:
        response = _upload(client, b"0" * (2 * 1024 * 1024 + 1))

        assert response.status_code == 413

    def test_delete_removes_file(self, client, user, avatar_dir, image_bytes) -> None:
        _upload(client, image_bytes("PNG"))
        filename = _reload(user).avatar_filename

        response = client.post("/profile/avatar/delete")

        assert response.headers["Location"].endswith("/profile")
        assert _reload(user).avatar_filename is None
        assert not (avatar_dir / filename).exists()
