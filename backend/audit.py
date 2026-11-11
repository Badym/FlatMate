"""Dziennik zdarzeń bezpieczeństwa (OWASP A09).

Każde zdarzenie to jedna linia JSON w loggerze ``flatmate.security``:
nazwa zdarzenia, ID użytkownika, adres IP, ścieżka i dodatkowe pola.
Pola o nazwach sugerujących sekret są zastępowane znacznikiem, więc do logów
nie trafiają hasła, tokeny ani ciasteczka.
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

from flask import Flask, has_request_context, request
from flask_login import current_user

logger = logging.getLogger("flatmate.security")

REDACTED = "[ukryte]"
SENSITIVE_KEY_PARTS = ("password", "haslo", "token", "secret", "cookie", "session", "hash", "csrf")


def _is_sensitive(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in SENSITIVE_KEY_PARTS)


def audit_event(event: str, **fields: Any) -> None:
    payload: dict[str, Any] = {"event": event}
    if has_request_context():
        payload["ip"] = request.remote_addr
        payload["method"] = request.method
        payload["path"] = request.path
        if current_user.is_authenticated:
            payload["user_id"] = current_user.id
    for key, value in fields.items():
        payload[key] = REDACTED if _is_sensitive(key) else value
    logger.info(json.dumps(payload, ensure_ascii=False, default=str))


def configure_audit_logging(app: Flask) -> None:
    """Na stdout (logi kontenera); w testach zdarzenia przechwytuje caplog."""
    logger.setLevel(logging.INFO)
    if app.testing or logger.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s %(name)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
