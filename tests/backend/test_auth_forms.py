"""Formularze logowania i rejestracji (sama walidacja; konta powstają w etapie 4)."""

from __future__ import annotations

from flask.testing import FlaskClient

VALID_PASSWORD = "dlugie-haslo-123"


def test_login_page_renders_form(client: FlaskClient) -> None:
    html = client.get("/login").get_data(as_text=True)

    assert 'name="email"' in html
    assert 'name="password"' in html
    assert 'autocomplete="current-password"' in html


def test_forms_include_csrf_token_when_enabled(make_app) -> None:
    client = make_app(WTF_CSRF_ENABLED=True).test_client()

    for url in ("/login", "/register"):
        assert 'name="csrf_token"' in client.get(url).get_data(as_text=True)


def test_login_rejects_invalid_email(client: FlaskClient) -> None:
    response = client.post("/login", data={"email": "not-an-email", "password": "secret"})

    assert response.status_code == 200
    assert "Podaj poprawny adres e-mail." in response.get_data(as_text=True)


def test_login_with_valid_form_redirects(client: FlaskClient) -> None:
    response = client.post(
        "/login", data={"email": "ola@example.com", "password": VALID_PASSWORD}, follow_redirects=True
    )

    assert response.request.path == "/login"
    assert "etapie 4" in response.get_data(as_text=True)


def test_register_requires_min_password_length(client: FlaskClient) -> None:
    response = client.post(
        "/register",
        data={
            "display_name": "Ola",
            "email": "ola@example.com",
            "password": "short",
            "password_confirm": "short",
        },
    )

    assert "od 12 do 128 znaków" in response.get_data(as_text=True)


def test_register_requires_matching_passwords(client: FlaskClient) -> None:
    response = client.post(
        "/register",
        data={
            "display_name": "Ola",
            "email": "ola@example.com",
            "password": VALID_PASSWORD,
            "password_confirm": VALID_PASSWORD + "x",
        },
    )

    assert "Hasła nie są takie same." in response.get_data(as_text=True)


def test_register_with_valid_form_redirects(client: FlaskClient) -> None:
    response = client.post(
        "/register",
        data={
            "display_name": "Ola",
            "email": "ola@example.com",
            "password": VALID_PASSWORD,
            "password_confirm": VALID_PASSWORD,
        },
        follow_redirects=True,
    )

    assert response.request.path == "/register"
    assert "etapie 4" in response.get_data(as_text=True)


def test_user_input_is_escaped(client: FlaskClient) -> None:
    payload = "<script>alert(1)</script>"

    response = client.post("/register", data={"display_name": payload, "email": "bad"})

    html = response.get_data(as_text=True)
    assert payload not in html
    assert "&lt;script&gt;" in html
