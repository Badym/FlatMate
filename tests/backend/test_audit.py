"""Dziennik zdarzeń bezpieczeństwa."""

from __future__ import annotations

import json
import logging

import pytest
from flask import Flask

from backend.audit import REDACTED, audit_event, configure_audit_logging, logger


def _last_event(caplog) -> dict:
    return json.loads(caplog.records[-1].getMessage())


def test_event_outside_request(app_ctx, caplog) -> None:
    with caplog.at_level(logging.INFO, logger="flatmate.security"):
        audit_event("seed_demo", users=3)

    assert _last_event(caplog) == {"event": "seed_demo", "users": 3}


def test_event_in_request_has_ip_and_path(app: Flask, caplog) -> None:
    with app.test_request_context("/login", method="POST", environ_base={"REMOTE_ADDR": "203.0.113.7"}):
        with caplog.at_level(logging.INFO, logger="flatmate.security"):
            audit_event("login_failed", email_domain="example.test")

    event = _last_event(caplog)
    assert event["ip"] == "203.0.113.7"
    assert event["method"] == "POST"
    assert event["path"] == "/login"
    assert "user_id" not in event


@pytest.mark.parametrize(
    "field", ["password", "new_password", "session_token", "invite_token", "secret_key", "csrf_token", "cookie"]
)
def test_sensitive_fields_are_redacted(app_ctx, caplog, field: str) -> None:
    with caplog.at_level(logging.INFO, logger="flatmate.security"):
        audit_event("test", **{field: "tajna-wartosc"})

    assert _last_event(caplog)[field] == REDACTED
    assert "tajna-wartosc" not in caplog.text


def test_logging_writes_to_stdout_outside_tests(make_app) -> None:
    previous = list(logger.handlers), logger.propagate
    logger.handlers.clear()
    try:
        configure_audit_logging(make_app(TESTING=False))

        assert len(logger.handlers) == 1
        assert logger.propagate is False
    finally:
        logger.handlers[:], logger.propagate = previous
