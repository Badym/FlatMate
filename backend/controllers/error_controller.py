"""Własne strony błędów, bez stack trace'ów i szczegółów serwera (T-11)."""

from __future__ import annotations

from flask import Flask, render_template
from flask_wtf.csrf import CSRFError
from werkzeug.exceptions import HTTPException

ERROR_PAGES: dict[int, tuple[str, str, str]] = {
    400: ("bi-exclamation-octagon", "Nieprawidłowe żądanie", "Serwer nie mógł przetworzyć tego żądania."),
    403: ("bi-shield-lock", "Brak uprawnień", "Ta akcja wymaga innej roli w mieszkaniu."),
    404: ("bi-signpost-split", "Nie znaleziono strony", "Ta strona nie istnieje albo nie masz do niej dostępu."),
    405: ("bi-slash-circle", "Niedozwolona metoda", "Ten adres nie obsługuje takiego żądania."),
    413: ("bi-file-earmark-x", "Za duży plik", "Przesłane dane przekraczają dozwolony rozmiar 2 MB."),
    429: ("bi-hourglass-split", "Zbyt wiele prób", "Odczekaj chwilę i spróbuj ponownie."),
    500: ("bi-bug", "Coś poszło nie tak", "Wystąpił nieoczekiwany błąd. Spróbuj ponownie za chwilę."),
}

CSRF_PAGE = ("bi-clock-history", "Formularz wygasł", "Odśwież stronę i wyślij formularz ponownie.")


def _render_error(code: int, page: tuple[str, str, str]) -> tuple[str, int]:
    icon, title, description = page
    html = render_template(
        "pages/errors/error.html", code=code, icon=icon, title=title, description=description
    )
    return html, code


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(CSRFError)
    def handle_csrf_error(_error: CSRFError) -> tuple[str, int]:
        return _render_error(400, CSRF_PAGE)

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException) -> tuple[str, int]:
        # Nieobsłużone wyjątki Flask zamienia na InternalServerError (500), a
        # przekierowania routingu (308) obsługuje sam, zanim trafią tutaj.
        code = error.code or 500
        return _render_error(code, ERROR_PAGES.get(code, ERROR_PAGES[500]))
