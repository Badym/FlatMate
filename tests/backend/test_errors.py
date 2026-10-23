from __future__ import annotations

from flask.testing import FlaskClient


def test_not_found_page(client: FlaskClient) -> None:
    response = client.get("/missing-page")

    assert response.status_code == 404
    html = response.get_data(as_text=True)
    assert "Nie znaleziono strony" in html
    assert "Traceback" not in html


def test_method_not_allowed_page(client: FlaskClient) -> None:
    response = client.post("/health")

    assert response.status_code == 405
    assert "Niedozwolona metoda" in response.get_data(as_text=True)


def test_routing_redirect_is_not_turned_into_error(client: FlaskClient) -> None:
    response = client.get("/_ui")

    assert response.status_code == 308
    assert response.headers["Location"].endswith("/_ui/")


def test_request_too_large(make_app) -> None:
    client = make_app(MAX_CONTENT_LENGTH=10).test_client()

    response = client.post("/login", data={"email": "a" * 100})

    assert response.status_code == 413
    assert "Za duży plik" in response.get_data(as_text=True)


def test_unhandled_exception_shows_generic_page(make_app) -> None:
    application = make_app(PROPAGATE_EXCEPTIONS=False)

    @application.get("/boom")
    def boom() -> str:
        raise RuntimeError("tajny szczegół błędu")

    response = application.test_client().get("/boom")

    assert response.status_code == 500
    html = response.get_data(as_text=True)
    assert "Coś poszło nie tak" in html
    assert "tajny szczegół błędu" not in html


def test_missing_csrf_token_is_rejected(make_app) -> None:
    client = make_app(WTF_CSRF_ENABLED=True).test_client()

    response = client.post("/login", data={"email": "ola@example.com", "password": "x" * 12})

    assert response.status_code == 400
    assert "Formularz wygasł" in response.get_data(as_text=True)
