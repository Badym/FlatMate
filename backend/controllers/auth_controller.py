"""Rejestracja, logowanie i wylogowanie (FR-1, SR-1, SR-2, SR-3)."""

from __future__ import annotations

from flask import Blueprint, Response, flash, redirect, render_template, request, url_for
from flask_limiter import RequestLimit
from flask_login import current_user, login_required
from werkzeug.wrappers import Response as WerkzeugResponse

from backend.audit import audit_event
from backend.core.constants import LOGIN_RATE_LIMIT, PASSWORD_MIN_LENGTH, REGISTER_RATE_LIMIT
from backend.core.extensions import limiter
from backend.forms.auth_forms import LoginForm, RegisterForm
from backend.security.redirects import is_safe_next
from backend.security.session import end_session, start_session
from backend.services.auth_service import LOGIN_FAILED_MESSAGE, AuthService, EmailTakenError

bp = Blueprint("auth", __name__)

HOME_ENDPOINT = "flats.index"
EMAIL_TAKEN_MESSAGE = "Konto z tym adresem e-mail już istnieje."


def _is_failed_login(response: Response) -> bool:
    """Limit na IP liczy tylko nieudane próby logowania (401), nie każde wejście na stronę."""
    return response.status_code == 401


def _log_rate_limit(limit: RequestLimit) -> None:
    audit_event("rate_limited", limit=str(limit.limit))


def _safe_next() -> str | None:
    target = request.args.get("next")
    return target if is_safe_next(target) else None


@bp.route("/login", methods=["GET", "POST"])
@limiter.limit(LOGIN_RATE_LIMIT, methods=["POST"], deduct_when=_is_failed_login, on_breach=_log_rate_limit)
def login() -> str | WerkzeugResponse | tuple[str, int]:
    if current_user.is_authenticated:
        return redirect(url_for(HOME_ENDPOINT))
    next_url = _safe_next()
    form = LoginForm()
    if form.validate_on_submit():
        user = AuthService().authenticate(form.email.data, form.password.data)
        if user is not None:
            start_session(user)
            return redirect(next_url or url_for(HOME_ENDPOINT))
        html = render_template(
            "pages/auth/login.html", form=form, next_url=next_url, auth_error=LOGIN_FAILED_MESSAGE
        )
        return html, 401
    return render_template("pages/auth/login.html", form=form, next_url=next_url)


@bp.route("/register", methods=["GET", "POST"])
@limiter.limit(REGISTER_RATE_LIMIT, methods=["POST"], on_breach=_log_rate_limit)
def register() -> str | WerkzeugResponse:
    if current_user.is_authenticated:
        return redirect(url_for(HOME_ENDPOINT))
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            user = AuthService().register(
                display_name=form.display_name.data,
                email=form.email.data,
                password=form.password.data,
            )
        except EmailTakenError:
            form.email.errors.append(EMAIL_TAKEN_MESSAGE)
        else:
            start_session(user)
            flash("Konto zostało utworzone. Witaj w FlatMate!", "success")
            return redirect(url_for(HOME_ENDPOINT))
    return render_template(
        "pages/auth/register.html", form=form, password_min_length=PASSWORD_MIN_LENGTH
    )


@bp.post("/logout")
@login_required
def logout() -> WerkzeugResponse:
    AuthService().logout(current_user._get_current_object())
    end_session()
    flash("Wylogowano.", "info")
    return redirect(url_for("main.index"))
