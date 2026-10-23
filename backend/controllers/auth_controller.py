"""Logowanie i rejestracja.

Szkielet: formularze i walidacja działają, a obsługa kont (AuthService,
limit prób, blokada konta, session_token) powstaje w etapie 4.
"""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, url_for
from werkzeug.wrappers import Response

from backend.core.constants import PASSWORD_MIN_LENGTH
from backend.forms.auth_forms import LoginForm, RegisterForm

bp = Blueprint("auth", __name__)

_NOT_READY = "Konta użytkowników zostaną uruchomione w etapie 4."


@bp.route("/login", methods=["GET", "POST"])
def login() -> str | Response:
    form = LoginForm()
    if form.validate_on_submit():
        flash(_NOT_READY, "info")
        return redirect(url_for("auth.login"))
    return render_template("pages/auth/login.html", form=form)


@bp.route("/register", methods=["GET", "POST"])
def register() -> str | Response:
    form = RegisterForm()
    if form.validate_on_submit():
        flash(_NOT_READY, "info")
        return redirect(url_for("auth.register"))
    return render_template(
        "pages/auth/register.html", form=form, password_min_length=PASSWORD_MIN_LENGTH
    )
