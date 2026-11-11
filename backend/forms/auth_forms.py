"""Formularze logowania i rejestracji."""

from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length

from backend.core.constants import (
    DISPLAY_NAME_MAX_LENGTH,
    EMAIL_MAX_LENGTH,
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
)

_REQUIRED = "To pole jest wymagane."


def strip_whitespace(value: str | None) -> str | None:
    """Spacje na brzegach (częste przy wklejaniu) nie powinny psuć walidacji adresu ani nazwy."""
    return value.strip() if isinstance(value, str) else value


class LoginForm(FlaskForm):
    email = EmailField(
        "Adres e-mail",
        filters=[strip_whitespace],
        validators=[
            DataRequired(message=_REQUIRED),
            Email(message="Podaj poprawny adres e-mail."),
            Length(max=EMAIL_MAX_LENGTH),
        ],
    )
    password = PasswordField(
        "Hasło",
        validators=[DataRequired(message=_REQUIRED), Length(max=PASSWORD_MAX_LENGTH)],
    )
    submit = SubmitField("Zaloguj się")


class RegisterForm(FlaskForm):
    display_name = StringField(
        "Imię lub pseudonim",
        filters=[strip_whitespace],
        validators=[
            DataRequired(message=_REQUIRED),
            Length(min=2, max=DISPLAY_NAME_MAX_LENGTH, message="Od 2 do 50 znaków."),
        ],
    )
    email = EmailField(
        "Adres e-mail",
        filters=[strip_whitespace],
        validators=[
            DataRequired(message=_REQUIRED),
            Email(message="Podaj poprawny adres e-mail."),
            Length(max=EMAIL_MAX_LENGTH),
        ],
    )
    password = PasswordField(
        "Hasło",
        validators=[
            DataRequired(message=_REQUIRED),
            Length(
                min=PASSWORD_MIN_LENGTH,
                max=PASSWORD_MAX_LENGTH,
                message=f"Hasło musi mieć od {PASSWORD_MIN_LENGTH} do {PASSWORD_MAX_LENGTH} znaków.",
            ),
        ],
    )
    password_confirm = PasswordField(
        "Powtórz hasło",
        validators=[
            DataRequired(message=_REQUIRED),
            EqualTo("password", message="Hasła nie są takie same."),
        ],
    )
    submit = SubmitField("Załóż konto")
