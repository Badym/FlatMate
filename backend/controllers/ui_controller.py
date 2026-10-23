"""Podgląd komponentów interfejsu (tylko ENABLE_UI_PREVIEW, czyli dev i testy).

Wspólny katalog wzorców dla zespołu: tak mają wyglądać karty zadań, awatary,
odznaki i formularze w kolejnych etapach.
"""

from __future__ import annotations

from flask import Blueprint, render_template

from backend.core.constants import USER_COLORS
from backend import demo_data

bp = Blueprint("ui", __name__, url_prefix="/_ui")


@bp.get("/")
def components() -> str:
    return render_template(
        "pages/ui/components.html",
        colors=USER_COLORS,
        members=demo_data.MEMBERS,
        tasks=demo_data.TASKS,
        week=demo_data.WEEK,
    )
