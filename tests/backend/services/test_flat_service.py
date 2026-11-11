from __future__ import annotations

from datetime import timedelta

from backend.core.extensions import db
from backend.models import Invite, Membership, MembershipStatus, MemberRole
from backend.models.types import utcnow
from backend.repositories import MembershipRepository
from backend.security.tokens import hash_token
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


def test_concurrent_join_request_returns_existing_status(make_user, make_flat, add_member, monkeypatch) -> None:
    admin, applicant = make_user(), make_user()
    flat = make_flat(admin=admin)
    db.session.add(
        Invite(
            flat=flat,
            created_by=admin,
            token_hash=hash_token("race-token"),
            expires_at=utcnow() + timedelta(days=1),
        )
    )
    db.session.commit()
    add_member(flat, applicant, status=MembershipStatus.PENDING)
    original = MembershipRepository.get_for_user
    lookups = []

    def first_lookup_misses(self, flat_id: int, user_id: int):
        # Pierwsze sprawdzenie nie widzi prośby zapisanej przez równoległe żądanie.
        lookups.append(user_id)
        return None if len(lookups) == 1 else original(self, flat_id, user_id)

    monkeypatch.setattr(MembershipRepository, "get_for_user", first_lookup_misses)

    status = FlatService().request_to_join("race-token", applicant.id)

    assert status is MembershipStatus.PENDING
    assert db.session.query(Membership).filter_by(flat_id=flat.id, user_id=applicant.id).count() == 1
