"""Fabryka aplikacji FlatMate.

Architektura warstwowa (MVC):

- ``controllers`` – endpointy HTTP (blueprinty); przyjmują żądanie, wywołują
  serwis i wybierają widok,
- ``services`` – logika biznesowa i granice transakcji,
- ``repositories`` – jedyne miejsce z zapytaniami do bazy,
- ``models`` – encje ORM,
- ``forms`` – formularze i walidacja danych wejściowych,
- ``templates`` i ``static`` – warstwa widoku.
"""

from __future__ import annotations

from typing import Any

from dotenv import load_dotenv
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import get_config
from app.controllers import register_controllers
from app.extensions import init_extensions
from app.security.headers import register_security_headers


def create_app(config_name: str | None = None, overrides: dict[str, Any] | None = None) -> Flask:
    """Tworzy i konfiguruje instancję aplikacji.

    :param config_name: nazwa środowiska (``development``, ``testing``,
        ``production``); domyślnie wartość zmiennej ``APP_ENV``.
    :param overrides: pojedyncze ustawienia nadpisywane po wczytaniu
        konfiguracji, używane głównie w testach.
    """
    load_dotenv()

    app = Flask(__name__)
    app.config.from_object(get_config(config_name))
    if overrides:
        app.config.update(overrides)

    if app.config["TRUST_PROXY"]:
        # Za reverse proxy: prawdziwy adres IP klienta i schemat HTTPS.
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)  # type: ignore[method-assign]

    init_extensions(app)
    register_security_headers(app)
    register_controllers(app)

    return app
