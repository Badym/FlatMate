"""Podgląd komponentów interfejsu (tylko ENABLE_UI_PREVIEW, czyli dev i testy).

Wspólny katalog wzorców dla zespołu: tak mają wyglądać karty zadań, awatary,
odznaki i formularze w kolejnych etapach.
"""

from __future__ import annotations

from flask import Blueprint, render_template

from app.constants import USER_COLORS
from app.controllers import samples

bp = Blueprint("ui", __name__, url_prefix="/_ui")


@bp.get("/")
def components() -> str:
    return render_template(
        "ui/components.html",
        colors=USER_COLORS,
        members=samples.MEMBERS,
        tasks=samples.TASKS,
        week=samples.WEEK,
    )
