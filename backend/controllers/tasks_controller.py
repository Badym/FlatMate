"""Trasy zarządzania zadaniami jednorazowymi."""

from __future__ import annotations

from datetime import date
from typing import TypedDict

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from flask_login import current_user

from backend.forms.flat_forms import EmptyActionForm
from backend.forms.task_forms import TaskForm
from backend.models import Task
from backend.security.access import flat_member_required
from backend.services.task_service import (
    InvalidTaskData,
    InvalidTaskFilter,
    TaskNotFound,
    TaskPermissionDenied,
    TaskService,
)

bp = Blueprint("tasks", __name__, url_prefix="/flats/<int:flat_id>/tasks")


class TaskFormData(TypedDict):
    title: str
    description: str
    task_type_id: int
    due_date: date
    assignee_id: int | None


def _service() -> TaskService:
    return TaskService()


def _prepare_form(form: TaskForm, flat_id: int) -> TaskForm:
    service = _service()
    form.task_type_id.choices = [
        ("", "Wybierz typ"),
        *((str(task_type.id), task_type.name) for task_type in service.list_task_types(flat_id)),
    ]
    member_choices = service.member_choices(flat_id)
    if g.membership.is_admin:
        allowed_members = member_choices
    else:
        allowed_members = [
            (member_id, name) for member_id, name in member_choices
            if member_id == current_user.id
        ]
    form.assignee_id.choices = [
        ("pool", "Do puli"),
        *((str(member_id), name) for member_id, name in allowed_members),
    ]
    return form


def _render_form(flat_id: int, form: TaskForm, *, task: Task | None = None) -> str:
    _prepare_form(form, flat_id)
    return render_template(
        "pages/tasks/form.html",
        flat=g.flat,
        form=form,
        task=task,
    )


def _form_values(form: TaskForm) -> TaskFormData:
    assignee_value = form.assignee_id.data
    return {
        "title": form.title.data,
        "description": form.description.data or "",
        "task_type_id": int(form.task_type_id.data),
        "due_date": form.due_date.data,
        "assignee_id": int(assignee_value) if assignee_value != "pool" else None,
    }


def _add_task_error(form: TaskForm, error: InvalidTaskData) -> None:
    getattr(form, error.field).errors.append(str(error))


@bp.get("")
@flat_member_required
def index(flat_id: int) -> str:
    list_filter = request.args.get("filter", "all")
    service = _service()
    try:
        tasks = service.list_one_off(flat_id, current_user.id, list_filter)
    except InvalidTaskFilter:
        abort(400)
    return render_template(
        "pages/tasks/index.html",
        flat=g.flat,
        membership=g.membership,
        tasks=tasks,
        list_filter=list_filter,
        today=date.today(),
        empty_title={
            "all": "Brak zadań jednorazowych",
            "mine": "Nie masz przypisanych zadań",
            "pool": "Pula zadań jest pusta",
            "overdue": "Brak zaległych zadań",
            "done": "Brak wykonanych zadań",
        }[list_filter],
        empty_text={
            "all": "Dodaj zadanie, aby zaplanować obowiązki w mieszkaniu.",
            "mine": "Przypisane do Ciebie otwarte zadania pojawią się tutaj.",
            "pool": "Nie ma teraz otwartych zadań do wzięcia.",
            "overdue": "Nie masz otwartych zadań po terminie.",
            "done": "Wykonane zadania pojawią się tutaj.",
        }[list_filter],
        filter_options=(
            ("all", "Wszystkie"),
            ("mine", "Moje"),
            ("pool", "Pula"),
            ("overdue", "Zaległe"),
            ("done", "Wykonane"),
        ),
        action_form=EmptyActionForm(),
    )


@bp.route("/new", methods=["GET", "POST"])
@flat_member_required
def create(flat_id: int) -> str:
    form = _prepare_form(TaskForm(), flat_id)
    if not form.is_submitted() and not form.assignee_id.data:
        form.assignee_id.data = str(current_user.id)
    if form.validate_on_submit():
        try:
            _service().create_one_off(
                flat_id,
                current_user.id,
                g.membership.is_admin,
                **_form_values(form),
            )
        except InvalidTaskData as exc:
            _add_task_error(form, exc)
        else:
            flash("Dodano zadanie.", "success")
            return redirect(url_for("tasks.index", flat_id=flat_id))
    return _render_form(flat_id, form)


@bp.route("/<int:task_id>/edit", methods=["GET", "POST"])
@flat_member_required
def edit(flat_id: int, task_id: int) -> str:
    service = _service()
    try:
        task = service.get_one_off_for_management(
            flat_id, task_id, current_user.id, g.membership.is_admin
        )
    except TaskNotFound:
        abort(404)
    except TaskPermissionDenied:
        abort(403)

    form = TaskForm(obj=task)
    _prepare_form(form, flat_id)
    if not form.is_submitted():
        form.task_type_id.data = str(task.task_type_id)
        form.assignee_id.data = str(task.assignee_id) if task.assignee_id is not None else "pool"
    if form.validate_on_submit():
        try:
            service.update_one_off(
                flat_id,
                task_id,
                current_user.id,
                g.membership.is_admin,
                **_form_values(form),
            )
        except TaskNotFound:
            abort(404)
        except TaskPermissionDenied:
            abort(403)
        except InvalidTaskData as exc:
            _add_task_error(form, exc)
        else:
            flash("Zapisano zmiany w zadaniu.", "success")
            return redirect(url_for("tasks.index", flat_id=flat_id))
    return _render_form(flat_id, form, task=task)


@bp.post("/<int:task_id>/delete")
@flat_member_required
def delete(flat_id: int, task_id: int):
    try:
        _service().delete_one_off(flat_id, task_id, current_user.id, g.membership.is_admin)
    except TaskNotFound:
        abort(404)
    except TaskPermissionDenied:
        abort(403)
    flash("Usunięto zadanie.", "info")
    return redirect(url_for("tasks.index", flat_id=flat_id))
