from __future__ import annotations

import pytest
from flask import Flask
from flask.testing import FlaskClient
from werkzeug.middleware.proxy_fix import ProxyFix

from app.repositories.health_repository import HealthRepository


def test_landing_page(client: FlaskClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "uczciwy podział" in html
    assert 'id="funkcje"' in html


def test_health_reports_database_ok(client: FlaskClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "database": "ok"}


def test_health_reports_database_failure(client: FlaskClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(HealthRepository, "ping", lambda self: False)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.get_json() == {"status": "degraded", "database": "error"}


def test_health_repository_handles_database_error(app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
    from sqlalchemy.exc import OperationalError

    from app.extensions import db

    def broken_execute(*_args: object, **_kwargs: object) -> None:
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    with app.app_context():
        monkeypatch.setattr(db.session, "execute", broken_execute)
        assert HealthRepository().ping() is False


def test_ui_preview_available_when_enabled(client: FlaskClient) -> None:
    response = client.get("/_ui/")

    assert response.status_code == 200
    assert "Biblioteka komponentów" in response.get_data(as_text=True)


def test_ui_preview_hidden_when_disabled(make_app) -> None:
    client = make_app(ENABLE_UI_PREVIEW=False).test_client()

    assert client.get("/_ui/").status_code == 404
    assert "Komponenty" not in client.get("/").get_data(as_text=True)


def test_proxy_fix_enabled_by_config(make_app) -> None:
    application = make_app(TRUST_PROXY=True)

    assert isinstance(application.wsgi_app, ProxyFix)


def test_user_loader_treats_unknown_session_as_anonymous(client: FlaskClient) -> None:
    with client.session_transaction() as session:
        session["_user_id"] = "unknown-token"

    response = client.get("/")

    assert response.status_code == 200
    assert "Zaloguj się" in response.get_data(as_text=True)
