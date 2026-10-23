"""Kontrola dostępu do mieszkań po stronie serwera (SR-4, T-01, T-02).

Każda trasa mieszkania ma parametr ``<int:flat_id>`` i jeden z dekoratorów:

    @bp.get("/flats/<int:flat_id>/tasks")
    @flat_member_required
    def tasks(flat_id: int): ...

Dekorator ładuje aktywne członkostwo do ``g.membership`` i mieszkanie do
``g.flat``. Osoba spoza mieszkania dostaje 404 (nie zdradzamy, że mieszkanie
istnieje), członek bez roli admina na trasie admina dostaje 403 (D-5).
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from flask import abort, g
from flask_login import current_user, login_required

from backend.audit import audit_event
from backend.models import Membership
from backend.repositories import MembershipRepository

ViewFunc = TypeVar("ViewFunc", bound=Callable[..., Any])


def _load_membership(view_kwargs: dict[str, Any]) -> Membership:
    flat_id = view_kwargs.get("flat_id")
    if not isinstance(flat_id, int):
        raise RuntimeError("Trasa mieszkania musi mieć parametr <int:flat_id>.")
    membership = MembershipRepository().get_active(flat_id, current_user.id)
    if membership is None:
        audit_event("access_denied", reason="not_member", flat_id=flat_id)
        abort(404)
    g.membership = membership
    g.flat = membership.flat
    return membership


def flat_member_required(view: ViewFunc) -> ViewFunc:
    @wraps(view)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        _load_membership(kwargs)
        return view(*args, **kwargs)

    return login_required(wrapper)  # type: ignore[return-value]


def flat_admin_required(view: ViewFunc) -> ViewFunc:
    @wraps(view)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        membership = _load_membership(kwargs)
        if not membership.is_admin:
            audit_event("access_denied", reason="not_admin", flat_id=membership.flat_id)
            abort(403)
        return view(*args, **kwargs)

    return login_required(wrapper)  # type: ignore[return-value]
