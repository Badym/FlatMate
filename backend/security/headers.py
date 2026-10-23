"""Nagłówki bezpieczeństwa dodawane do każdej odpowiedzi (SR-6, T-05)."""

from __future__ import annotations

from flask import Flask, Response

# Bez inline JS i atrybutów style. ``data:`` w img-src jest potrzebne dla ikon
# SVG osadzonych w CSS Bootstrapa (strzałki selectów, checkboxy, przycisk
# zamknięcia); obrazy nie wykonują skryptów.
CONTENT_SECURITY_POLICY = "; ".join(
    [
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self'",
        "img-src 'self' data:",
        "font-src 'self'",
        "connect-src 'self'",
        "object-src 'none'",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "form-action 'self'",
    ]
)

SECURITY_HEADERS = {
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "same-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}

HSTS_HEADER = "max-age=31536000; includeSubDomains"


def register_security_headers(app: Flask) -> None:
    hsts_enabled = app.config["ENABLE_HSTS"]

    @app.after_request
    def set_security_headers(response: Response) -> Response:
        for name, value in SECURITY_HEADERS.items():
            response.headers.setdefault(name, value)
        if hsts_enabled:
            response.headers.setdefault("Strict-Transport-Security", HSTS_HEADER)
        return response
