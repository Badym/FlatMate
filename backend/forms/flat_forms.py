"""Formularze zarządzania mieszkaniami i dołączaniem."""

from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length

from backend.core.constants import FLAT_NAME_MAX_LENGTH
from backend.forms.auth_forms import strip_whitespace


class FlatForm(FlaskForm):
    name = StringField(
        "Nazwa mieszkania",
        filters=[strip_whitespace],
        validators=[
            DataRequired(message="Podaj nazwę mieszkania."),
            Length(max=FLAT_NAME_MAX_LENGTH, message="Nazwa może mieć najwyżej 80 znaków."),
        ],
    )
    submit = SubmitField("Utwórz mieszkanie")


class DeleteFlatForm(FlaskForm):
    confirmation = StringField(
        "Wpisz nazwę mieszkania, aby potwierdzić",
        filters=[strip_whitespace],
        validators=[DataRequired(message="Wpisz nazwę mieszkania.")],
    )
    submit = SubmitField("Usuń mieszkanie")


class EmptyActionForm(FlaskForm):
    submit = SubmitField()
