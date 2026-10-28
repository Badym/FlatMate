from __future__ import annotations

from backend.models import MemberRole
from backend.services.flat_service import FlatService


def test_flat_summaries(make_user, make_flat, add_member) -> None:
    user, other = make_user(), make_user()
    own = make_flat(admin=user, name="A")
    joined = make_flat(admin=other, name="B")
    add_member(joined, user)

    summaries = FlatService().list_for_user(user.id)

    assert [(s.flat, s.role, s.is_admin) for s in summaries] == [
        (own, MemberRole.ADMIN, True),
        (joined, MemberRole.MEMBER, False),
    ]
    assert summaries[1].members == [other, user]
    assert summaries[0].open_tasks == 0
