"""Profil zalogowanego użytkownika: dane, hasło i awatar (FR-2)."""

from __future__ import annotations

from flask import Blueprint, current_app, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from werkzeug.wrappers import Response

from backend.core.constants import PASSWORD_CHANGE_RATE_LIMIT, PASSWORD_MIN_LENGTH
from backend.core.extensions import limiter
from backend.forms.profile_forms import AvatarForm, PasswordChangeForm, ProfileForm
from backend.models import User
from backend.security.session import start_session
from backend.services.auth_service import AuthService, InvalidCurrentPasswordError, SamePasswordError
from backend.services.avatar_service import AvatarService, InvalidAvatarError
from backend.services.profile_service import ProfileService

bp = Blueprint("profile", __name__, url_prefix="/profile")


def _user() -> User:
    return current_user._get_current_object()


def _avatars() -> AvatarService:
    return AvatarService(current_app.config["AVATAR_UPLOAD_DIR"])


def _render(
    profile_form: ProfileForm | None = None,
    password_form: PasswordChangeForm | None = None,
    avatar_form: AvatarForm | None = None,
) -> str:
    """Strona ma trzy niezależne formularze; prefiksy rozdzielają nazwy pól i tokeny CSRF."""
    return render_template(
        "pages/profile/index.html",
        profile_form=profile_form or ProfileForm(obj=_user(), prefix="profile", formdata=None),
        password_form=password_form or PasswordChangeForm(prefix="password", formdata=None),
        avatar_form=avatar_form or AvatarForm(prefix="avatar", formdata=None),
        password_min_length=PASSWORD_MIN_LENGTH,
    )


@bp.get("")
@login_required
def index() -> str:
    return _render()


@bp.post("")
@login_required
def update() -> str | Response:
    form = ProfileForm(prefix="profile")
    if not form.validate_on_submit():
        return _render(profile_form=form)
    ProfileService().update(_user(), display_name=form.display_name.data, color_index=form.color_index.data)
    flash("Zapisano zmiany w profilu.", "success")
    return redirect(url_for("profile.index"))


@bp.post("/password")
@login_required
@limiter.limit(PASSWORD_CHANGE_RATE_LIMIT)
def change_password() -> str | Response:
    form = PasswordChangeForm(prefix="password")
    if not form.validate_on_submit():
        return _render(password_form=form)
    user = _user()
    try:
        AuthService().change_password(user, form.current_password.data, form.new_password.data)
    except InvalidCurrentPasswordError:
        form.current_password.errors.append("Obecne hasło jest nieprawidłowe.")
        return _render(password_form=form)
    except SamePasswordError:
        form.new_password.errors.append("Nowe hasło musi różnić się od obecnego.")
        return _render(password_form=form)
    # Nowy token sesji wylogował wszystkie urządzenia; to urządzenie logujemy od nowa.
    start_session(user)
    flash("Hasło zostało zmienione. Pozostałe sesje zostały wylogowane.", "success")
    return redirect(url_for("profile.index"))


@bp.post("/avatar")
@login_required
def upload_avatar() -> str | Response:
    form = AvatarForm(prefix="avatar")
    if not form.validate_on_submit():
        return _render(avatar_form=form)
    try:
        _avatars().save(_user(), form.file.data.stream)
    except InvalidAvatarError as exc:
        form.file.errors.append(str(exc))
        return _render(avatar_form=form)
    flash("Zapisano nowy awatar.", "success")
    return redirect(url_for("profile.index"))


@bp.post("/avatar/delete")
@login_required
def delete_avatar() -> Response:
    _avatars().delete(_user())
    flash("Usunięto awatar.", "info")
    return redirect(url_for("profile.index"))
