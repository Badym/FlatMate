"""Strona główna i healthcheck."""

from __future__ import annotations

from flask import Blueprint, Response, jsonify, render_template

from backend import demo_data
from backend.services.health_service import HealthService

bp = Blueprint("main", __name__)


@bp.get("/")
def index() -> str:
    return render_template(
        "pages/home.html",
        preview_members=demo_data.MEMBERS,
        preview_tasks=demo_data.TASKS[:4],
    )


@bp.get("/health")
def health() -> tuple[Response, int]:
    status = HealthService().check()
    return jsonify(status.as_dict()), 200 if status.healthy else 503
