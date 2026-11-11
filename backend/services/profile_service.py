"""Edycja profilu: nazwa wyświetlana i kolor (FR-2)."""

from __future__ import annotations

from backend.audit import audit_event
from backend.core.extensions import db
from backend.models import User


class ProfileService:
    def update(self, user: User, *, display_name: str, color_index: int) -> None:
        changed = []
        display_name = display_name.strip()
        if display_name != user.display_name:
            user.display_name = display_name
            changed.append("display_name")
        if color_index != user.color_index:
            user.color_index = color_index
            changed.append("color_index")
        if not changed:
            return
        db.session.commit()
        audit_event("profile_updated", fields=changed)
