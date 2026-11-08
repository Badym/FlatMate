"""Formularze zadań jednorazowych."""

from __future__ import annotations

from datetime import date

from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, InputRequired, Length, Optional, ValidationError

from backend.core.constants import TASK_DESCRIPTION_MAX_LENGTH, TASK_TITLE_MAX_LENGTH
from backend.forms.auth_forms import strip_whitespace


def validate_selected_choice(_form: FlaskForm, field: SelectField) -> None:
    if not any(str(value) == field.data for value, _label in field.choices):
        raise ValidationError("Wybierz prawidłową opcję.")


class TaskForm(FlaskForm):
    title = StringField(
        "Nazwa zadania",
        filters=[strip_whitespace],
        validators=[
            DataRequired(message="Podaj nazwę zadania."),
            Length(max=TASK_TITLE_MAX_LENGTH, message="Nazwa może mieć najwyżej 100 znaków."),
        ],
    )
    description = TextAreaField(
        "Opis",
        filters=[strip_whitespace],
        validators=[
            Optional(),
            Length(
                max=TASK_DESCRIPTION_MAX_LENGTH,
                message="Opis może mieć najwyżej 1000 znaków.",
            ),
        ],
    )
    task_type_id = SelectField(
        "Typ zadania",
        choices=[],
        validate_choice=False,
        validators=[
            InputRequired(message="Wybierz typ zadania."),
            validate_selected_choice,
        ],
    )
    due_date = DateField(
        "Termin",
        default=date.today,
        validators=[DataRequired(message="Podaj termin zadania.")],
    )
    assignee_id = SelectField(
        "Przypisanie",
        choices=[],
        validate_choice=False,
        validators=[
            InputRequired(message="Wybierz przypisanie."),
            validate_selected_choice,
        ],
    )
    submit = SubmitField()
