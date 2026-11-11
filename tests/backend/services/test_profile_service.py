from __future__ import annotations

import logging

from backend.services.profile_service import ProfileService


def test_profile_update_logs_changed_fields(make_user, caplog) -> None:
    user = make_user(display_name="Ola", color_index=1)

    with caplog.at_level(logging.INFO, logger="flatmate.security"):
        ProfileService().update(user, display_name=" Ola ", color_index=4)

    assert (user.display_name, user.color_index) == ("Ola", 4)
    assert '"fields": ["color_index"]' in caplog.text


def test_profile_update_without_changes_does_nothing(make_user, caplog) -> None:
    user = make_user(display_name="Ola", color_index=1)

    with caplog.at_level(logging.INFO, logger="flatmate.security"):
        ProfileService().update(user, display_name="Ola", color_index=1)

    assert "profile_updated" not in caplog.text
