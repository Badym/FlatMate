"""Operacje na zadaniach jednorazowych."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from backend.audit import audit_event
from backend.core.extensions import db
from backend.models import Recurrence, Task, TaskStatus
from backend.repositories import MembershipRepository, TaskRepository, TaskTypeRepository

if TYPE_CHECKING:
    from backend.models import TaskType


class TaskActionError(Exception):
    """Nieprawidłowa lub niedozwolona operacja na zadaniu."""


class TaskNotFound(TaskActionError):
    pass


class TaskPermissionDenied(TaskActionError):
    pass


class InvalidTaskData(TaskActionError):
    def __init__(self, field: str, message: str) -> None:
        super().__init__(message)
        self.field = field


class TaskService:
    def __init__(
        self,
        tasks: TaskRepository | None = None,
        task_types: TaskTypeRepository | None = None,
        memberships: MembershipRepository | None = None,
    ) -> None:
        self._tasks = tasks or TaskRepository()
        self._task_types = task_types or TaskTypeRepository()
        self._memberships = memberships or MembershipRepository()

    def list_one_off(self, flat_id: int) -> list[Task]:
        return self._tasks.list_one_off(flat_id)

    def list_task_types(self, flat_id: int) -> list[TaskType]:
        return self._task_types.list_available(flat_id)

    def member_choices(self, flat_id: int) -> list[tuple[int, str]]:
        return [
            (membership.user_id, membership.user.display_name)
            for membership in self._memberships.list_active(flat_id)
        ]

    def get_one_off_for_management(
        self, flat_id: int, task_id: int, user_id: int, is_admin: bool
    ) -> Task:
        return self._get_manageable_task(flat_id, task_id, user_id, is_admin)

    def create_one_off(
        self,
        flat_id: int,
        user_id: int,
        is_admin: bool,
        *,
        title: str,
        description: str,
        task_type_id: int,
        due_date: date,
        assignee_id: int | None,
    ) -> Task:
        task_type = self._task_types.get_available(flat_id, task_type_id)
        if task_type is None:
            raise InvalidTaskData("task_type_id", "Wybierz typ dostępny w tym mieszkaniu.")
        self._validate_assignee(flat_id, user_id, is_admin, assignee_id)

        task = self._tasks.add(
            Task(
                flat_id=flat_id,
                task_type_id=task_type.id,
                created_by_id=user_id,
                assignee_id=assignee_id,
                title=title,
                description=description,
                due_date=due_date,
                status=TaskStatus.OPEN,
                recurrence=Recurrence.NONE,
            )
        )
        db.session.commit()
        audit_event("task_created", flat_id=flat_id, task_id=task.id)
        return task

    def update_one_off(
        self,
        flat_id: int,
        task_id: int,
        user_id: int,
        is_admin: bool,
        *,
        title: str,
        description: str,
        task_type_id: int,
        due_date: date,
        assignee_id: int | None,
    ) -> Task:
        task = self._get_manageable_task(flat_id, task_id, user_id, is_admin)
        task_type = self._task_types.get_available(flat_id, task_type_id)
        if task_type is None:
            raise InvalidTaskData("task_type_id", "Wybierz typ dostępny w tym mieszkaniu.")
        self._validate_assignee(flat_id, user_id, is_admin, assignee_id)

        task.title = title
        task.description = description
        task.task_type_id = task_type.id
        task.due_date = due_date
        task.assignee_id = assignee_id
        db.session.commit()
        audit_event("task_updated", flat_id=flat_id, task_id=task.id)
        return task

    def delete_one_off(self, flat_id: int, task_id: int, user_id: int, is_admin: bool) -> None:
        task = self._get_manageable_task(flat_id, task_id, user_id, is_admin)
        self._tasks.delete(task)
        db.session.commit()
        audit_event("task_deleted", flat_id=flat_id, task_id=task_id)

    def _get_manageable_task(
        self, flat_id: int, task_id: int, user_id: int, is_admin: bool
    ) -> Task:
        task = self._tasks.get_in_flat(flat_id, task_id)
        if (
            task is None
            or task.parent_task_id is not None
            or task.recurrence is not Recurrence.NONE
        ):
            raise TaskNotFound
        if not is_admin and task.created_by_id != user_id:
            raise TaskPermissionDenied
        return task

    def _validate_assignee(
        self, flat_id: int, user_id: int, is_admin: bool, assignee_id: int | None
    ) -> None:
        if assignee_id is None:
            return
        if not self._memberships.is_active_member(flat_id, assignee_id):
            raise InvalidTaskData("assignee_id", "Wybierz aktywnego członka tego mieszkania.")
        if not is_admin and assignee_id != user_id:
            raise InvalidTaskData("assignee_id", "Możesz przypisać zadanie tylko sobie lub do puli.")
