from __future__ import annotations

import pytest
from flask.testing import FlaskClient

from backend.security.headers import CONTENT_SECURITY_POLICY


@pytest.mark.parametrize("url", ["/", "/login", "/does-not-exist", "/static/css/main.css"])
def test_security_headers_on_every_response(client: FlaskClient, url: str) -> None:
    response = client.get(url)

    assert response.headers["Content-Security-Policy"] == CONTENT_SECURITY_POLICY
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "same-origin"


def test_csp_forbids_inline_code(client: FlaskClient) -> None:
    csp = client.get("/").headers["Content-Security-Policy"]

    assert "script-src 'self'" in csp
    assert "style-src 'self'" in csp
    assert "unsafe-inline" not in csp
    assert "frame-ancestors 'none'" in csp


def test_hsts_disabled_outside_production(client: FlaskClient) -> None:
    assert "Strict-Transport-Security" not in client.get("/").headers


def test_hsts_enabled_when_configured(make_app) -> None:
    response = make_app(ENABLE_HSTS=True).test_client().get("/")

    assert response.headers["Strict-Transport-Security"].startswith("max-age=31536000")
