"""Bezpieczne przekierowania po zalogowaniu (ochrona przed open redirect)."""

from __future__ import annotations

from urllib.parse import urlsplit


def is_safe_next(target: str | None) -> bool:
    """Czy ``target`` (np. parametr ``?next=``) to ścieżka wewnątrz aplikacji.

    Dopuszczamy wyłącznie ścieżki względne zaczynające się od ``/``. Odrzucamy
    adresy z innym hostem lub schematem (``https://…``, ``//host``,
    ``javascript:``), odwrócone ukośniki, które przeglądarki traktują jak ``/``,
    oraz znaki sterujące.
    """
    if not target or not target.startswith("/") or target.startswith("//"):
        return False
    if "\\" in target or any(ord(char) < 32 or ord(char) == 127 for char in target):
        return False
    parts = urlsplit(target)
    return not parts.scheme and not parts.netloc
