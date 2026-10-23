"""Backend FlatMate: fabryka aplikacji.

Architektura warstwowa (MVC), szczegóły w backend/README.md:

- ``controllers`` – endpointy HTTP (blueprinty); przyjmują żądanie, wywołują
  serwis i wybierają widok,
- ``services`` – logika biznesowa i granice transakcji,
- ``repositories`` – jedyne miejsce z zapytaniami do bazy,
- ``models`` – encje ORM,
- ``forms`` – formularze i walidacja danych wejściowych,
- ``security`` – nagłówki, a później dekoratory dostępu,
- ``core`` – konfiguracja, rozszerzenia Flaska i stałe.

Warstwa widoku (szablony Jinja2, CSS, JS) jest w osobnym katalogu
``frontend/`` w głównym katalogu projektu.
"""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from backend.audit import configure_audit_logging
from backend.controllers import register_controllers
from backend.core.config import get_config
from backend.core.extensions import init_extensions
from backend.security.headers import register_security_headers
from backend.security.session import init_session

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

# Na Windowsie typy MIME pochodzą z rejestru systemu i .woff2 bywa nieznane.
mimetypes.add_type("font/woff2", ".woff2")


def create_app(config_name: str | None = None, overrides: dict[str, Any] | None = None) -> Flask:
    """Tworzy i konfiguruje instancję aplikacji.

    :param config_name: nazwa środowiska (``development``, ``testing``,
        ``production``); domyślnie wartość zmiennej ``APP_ENV``.
    :param overrides: pojedyncze ustawienia nadpisywane po wczytaniu
        konfiguracji, używane głównie w testach.
    """
    load_dotenv()

    app = Flask(
        __name__,
        template_folder=FRONTEND_DIR / "templates",
        static_folder=FRONTEND_DIR / "static",
    )
    app.config.from_object(get_config(config_name))
    if overrides:
        app.config.update(overrides)

    if app.config["TRUST_PROXY"]:
        # Za reverse proxy: prawdziwy adres IP klienta i schemat HTTPS.
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)  # type: ignore[method-assign]

    init_extensions(app)
    init_session()
    configure_audit_logging(app)
    register_security_headers(app)
    register_controllers(app)

    return app
