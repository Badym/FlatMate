"""Konfiguracja aplikacji dla poszczególnych środowisk.

Wartości wrażliwe (SECRET_KEY, DATABASE_URL) pochodzą wyłącznie ze zmiennych
środowiskowych lub z pliku .env, który nie trafia do repozytorium (SR-10).
Konfiguracja jest tworzona w chwili uruchomienia fabryki aplikacji, a nie przy
imporcie modułu, więc zawsze widzi aktualne zmienne środowiskowe.
"""

from __future__ import annotations

import os
import secrets
from datetime import timedelta
from pathlib import Path

MIN_SECRET_KEY_LENGTH = 32

# Awatary leżą wśród plików statycznych (losowe nazwy); w Dockerze to osobny wolumen.
DEFAULT_AVATAR_UPLOAD_DIR = Path(__file__).resolve().parents[2] / "frontend" / "static" / "uploads" / "avatars"


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Brak wymaganej zmiennej środowiskowej {name}. "
            "Uzupełnij plik .env na podstawie .env.example."
        )
    return value


class BaseConfig:
    """Ustawienia wspólne dla wszystkich środowisk."""

    ENV_NAME = "base"
    DEBUG = False
    TESTING = False

    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Sesja: SR-3, T-07
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)

    # Limit rozmiaru żądania, m.in. dla awatarów: SR-9, T-10
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
    AVATAR_UPLOAD_DIR = DEFAULT_AVATAR_UPLOAD_DIR

    # Limity żądań: SR-2, T-03. Jeden proces gunicorna, więc wystarcza pamięć.
    RATELIMIT_STORAGE_URI = "memory://"
    RATELIMIT_HEADERS_ENABLED = False

    ENABLE_HSTS = True
    ENABLE_UI_PREVIEW = False

    def __init__(self) -> None:
        self.SECRET_KEY = os.environ.get("SECRET_KEY", "").strip()
        self.SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "").strip()
        self.TRUST_PROXY = _env_bool("TRUST_PROXY")
        # Hasło kont demo dla `flask seed-demo` (niedostępne w produkcji).
        self.DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "")


class DevelopmentConfig(BaseConfig):
    """Lokalna praca nad aplikacją (http://localhost)."""

    ENV_NAME = "development"
    SESSION_COOKIE_SECURE = False
    ENABLE_HSTS = False
    ENABLE_UI_PREVIEW = True

    def __init__(self) -> None:
        super().__init__()
        self.SQLALCHEMY_DATABASE_URI = _require_env("DATABASE_URL")
        if not self.SECRET_KEY:
            # Klucz tymczasowy: sesje wygasają przy każdym restarcie serwera.
            self.SECRET_KEY = secrets.token_hex(32)


class TestingConfig(BaseConfig):
    """Testy automatyczne (pytest)."""

    ENV_NAME = "testing"
    TESTING = True
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    SESSION_COOKIE_SECURE = False
    ENABLE_HSTS = False
    ENABLE_UI_PREVIEW = True

    def __init__(self) -> None:
        super().__init__()
        self.SECRET_KEY = secrets.token_hex(32)
        # Osobna baza PostgreSQL tylko dla testów: docker compose up -d db-test
        self.SQLALCHEMY_DATABASE_URI = _require_env("TEST_DATABASE_URL")


class ProductionConfig(BaseConfig):
    """Wdrożenie: wymaga kompletnej konfiguracji, inaczej aplikacja nie startuje."""

    ENV_NAME = "production"
    # Prefiks __Host-: przeglądarka przyjmie ciasteczko tylko przez HTTPS, bez domeny, dla ścieżki /.
    SESSION_COOKIE_NAME = "__Host-flatmate"

    def __init__(self) -> None:
        super().__init__()
        self.SECRET_KEY = _require_env("SECRET_KEY")
        self.SQLALCHEMY_DATABASE_URI = _require_env("DATABASE_URL")
        if len(self.SECRET_KEY) < MIN_SECRET_KEY_LENGTH:
            raise RuntimeError(
                f"SECRET_KEY musi mieć co najmniej {MIN_SECRET_KEY_LENGTH} znaki."
            )


CONFIGS: dict[str, type[BaseConfig]] = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None = None) -> BaseConfig:
    """Zwraca konfigurację środowiska; domyślnie produkcyjną (bezpieczny wybór)."""
    env_name = (name or os.environ.get("APP_ENV") or "production").strip().lower()
    try:
        config_class = CONFIGS[env_name]
    except KeyError as exc:
        allowed = ", ".join(sorted(CONFIGS))
        raise ValueError(f"Nieznane środowisko APP_ENV={env_name!r}. Dozwolone: {allowed}.") from exc
    return config_class()
