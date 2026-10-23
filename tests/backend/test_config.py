from __future__ import annotations

import pytest

from backend.core import config as config_module
from backend.core.config import DevelopmentConfig, ProductionConfig, get_config

VALID_SECRET = "x" * 64
DATABASE_URL = "postgresql+psycopg://user:pass@localhost:5432/flatmate"


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("APP_ENV", "SECRET_KEY", "DATABASE_URL", "TRUST_PROXY"):
        monkeypatch.delenv(name, raising=False)


def test_default_environment_is_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", VALID_SECRET)
    monkeypatch.setenv("DATABASE_URL", DATABASE_URL)

    assert isinstance(get_config(), ProductionConfig)


def test_app_env_selects_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "testing")

    assert isinstance(get_config(), config_module.TestingConfig)


def test_unknown_environment_is_rejected() -> None:
    with pytest.raises(ValueError, match="Nieznane środowisko"):
        get_config("staging")


@pytest.mark.parametrize("missing", ["SECRET_KEY", "DATABASE_URL"])
def test_production_requires_secrets(monkeypatch: pytest.MonkeyPatch, missing: str) -> None:
    values = {"SECRET_KEY": VALID_SECRET, "DATABASE_URL": DATABASE_URL}
    values.pop(missing)
    for name, value in values.items():
        monkeypatch.setenv(name, value)

    with pytest.raises(RuntimeError, match=missing):
        ProductionConfig()


def test_production_rejects_short_secret_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "too-short")
    monkeypatch.setenv("DATABASE_URL", DATABASE_URL)

    with pytest.raises(RuntimeError, match="co najmniej 32"):
        ProductionConfig()


def test_production_is_secure_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", VALID_SECRET)
    monkeypatch.setenv("DATABASE_URL", DATABASE_URL)

    config = ProductionConfig()

    assert config.DEBUG is False
    assert config.SESSION_COOKIE_SECURE is True
    assert config.SESSION_COOKIE_HTTPONLY is True
    assert config.SESSION_COOKIE_SAMESITE == "Lax"
    assert config.ENABLE_HSTS is True
    assert config.ENABLE_UI_PREVIEW is False


def test_development_requires_database_url() -> None:
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        DevelopmentConfig()


def test_development_generates_temporary_secret_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", DATABASE_URL)

    config = DevelopmentConfig()

    assert len(config.SECRET_KEY) >= 32
    assert config.SESSION_COOKIE_SECURE is False


def test_trust_proxy_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRUST_PROXY", "1")

    assert config_module.TestingConfig().TRUST_PROXY is True
