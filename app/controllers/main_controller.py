"""Strona główna i healthcheck."""

from __future__ import annotations

from flask import Blueprint, Response, jsonify, render_template

from app.controllers import samples
from app.services.health_service import HealthService

bp = Blueprint("main", __name__)


@bp.get("/")
def index() -> str:
    return render_template(
        "main/index.html",
        preview_members=samples.MEMBERS,
        preview_tasks=samples.TASKS[:4],
    )


@bp.get("/health")
def health() -> tuple[Response, int]:
    status = HealthService().check()
    return jsonify(status.as_dict()), 200 if status.healthy else 503
