"""Formularze profilu: dane, hasło, awatar (FR-2)."""

from __future__ import annotations

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired, FileSize
from wtforms import PasswordField, RadioField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length

from backend.core.constants import (
    DISPLAY_NAME_MAX_LENGTH,
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    USER_COLORS,
)
from backend.forms.auth_forms import strip_whitespace

_REQUIRED = "To pole jest wymagane."
AVATAR_MAX_BYTES = 2 * 1024 * 1024


class ProfileForm(FlaskForm):
    display_name = StringField(
        "Imię lub pseudonim",
        filters=[strip_whitespace],
        validators=[
            DataRequired(message=_REQUIRED),
            Length(min=2, max=DISPLAY_NAME_MAX_LENGTH, message="Od 2 do 50 znaków."),
        ],
    )
    # Wybór tylko z palety (D-6); spoza listy WTForms odrzuca wartość.
    color_index = RadioField(
        "Kolor",
        choices=[(index, name) for index, (name, _hex) in enumerate(USER_COLORS)],
        coerce=int,
        validate_choice=True,
    )
    submit = SubmitField("Zapisz zmiany")


class PasswordChangeForm(FlaskForm):
    current_password = PasswordField("Obecne hasło", validators=[DataRequired(message=_REQUIRED)])
    new_password = PasswordField(
        "Nowe hasło",
        validators=[
            DataRequired(message=_REQUIRED),
            Length(
                min=PASSWORD_MIN_LENGTH,
                max=PASSWORD_MAX_LENGTH,
                message=f"Hasło musi mieć od {PASSWORD_MIN_LENGTH} do {PASSWORD_MAX_LENGTH} znaków.",
            ),
        ],
    )
    new_password_confirm = PasswordField(
        "Powtórz nowe hasło",
        validators=[
            DataRequired(message=_REQUIRED),
            EqualTo("new_password", message="Hasła nie są takie same."),
        ],
    )
    submit = SubmitField("Zmień hasło")


class AvatarForm(FlaskForm):
    # Rozszerzenie sprawdzamy tylko dla wygody użytkownika; o formacie decyduje zawartość pliku.
    file = FileField(
        "Nowy awatar",
        validators=[
            FileRequired(message="Wybierz plik obrazu."),
            FileAllowed(["png", "jpg", "jpeg"], message="Dozwolone są tylko obrazy PNG i JPEG."),
            FileSize(max_size=AVATAR_MAX_BYTES, message="Plik może mieć najwyżej 2 MB."),
        ],
    )
    submit = SubmitField("Wgraj awatar")
