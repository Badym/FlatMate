"""Warstwa kontrolerów: endpointy HTTP pogrupowane w blueprinty.

Kontroler przyjmuje żądanie, waliduje formularz, wywołuje serwis i wybiera
szablon. Nie zawiera logiki biznesowej ani zapytań do bazy.
"""

from __future__ import annotations

from datetime import UTC, datetime

from flask import Flask

from backend.controllers import (
    auth_controller,
    flats_controller,
    main_controller,
    ui_controller,
)
from backend.controllers.error_controller import register_error_handlers


def register_controllers(app: Flask) -> None:
    app.register_blueprint(main_controller.bp)
    app.register_blueprint(auth_controller.bp)
    app.register_blueprint(flats_controller.bp)
    if app.config["ENABLE_UI_PREVIEW"]:
        app.register_blueprint(ui_controller.bp)
    register_error_handlers(app)

    app.add_template_filter(plural_pl, "plural")

    @app.context_processor
    def inject_template_globals() -> dict[str, object]:
        return {"current_year": datetime.now(UTC).year}


def plural_pl(count: int, one: str, few: str, many: str) -> str:
    """Polska odmiana po liczebniku: 1 zadanie, 2–4 zadania, 5 zadań, 22 zadania, 12 zadań."""
    if count == 1:
        return one
    if count % 10 in (2, 3, 4) and count % 100 not in (12, 13, 14):
        return few
    return many
