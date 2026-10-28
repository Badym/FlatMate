"""Mieszkania zalogowanego użytkownika. Tworzenie, zaproszenia i pulpit: etap 5."""

from __future__ import annotations

from flask import Blueprint, render_template
from flask_login import current_user, login_required

from backend.services.flat_service import FlatService

bp = Blueprint("flats", __name__, url_prefix="/flats")


@bp.get("")
@login_required
def index() -> str:
    return render_template("pages/flats/index.html", flats=FlatService().list_for_user(current_user.id))
