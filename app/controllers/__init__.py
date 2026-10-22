"""Warstwa kontrolerów: endpointy HTTP pogrupowane w blueprinty.

Kontroler przyjmuje żądanie, waliduje formularz, wywołuje serwis i wybiera
szablon. Nie zawiera logiki biznesowej ani zapytań do bazy.
"""

from __future__ import annotations

from datetime import UTC, datetime

from flask import Flask

from app.controllers import auth_controller, main_controller, ui_controller
from app.controllers.errors import register_error_handlers


def register_controllers(app: Flask) -> None:
    app.register_blueprint(main_controller.bp)
    app.register_blueprint(auth_controller.bp)
    if app.config["ENABLE_UI_PREVIEW"]:
        app.register_blueprint(ui_controller.bp)
    register_error_handlers(app)

    @app.context_processor
    def inject_template_globals() -> dict[str, object]:
        return {"current_year": datetime.now(UTC).year}
