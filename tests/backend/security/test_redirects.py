from __future__ import annotations

import pytest

from backend.security.redirects import is_safe_next


@pytest.mark.parametrize("target", ["/", "/flats", "/profile?tab=haslo", "/flats/1#zadania"])
def test_accepts_paths_inside_application(target: str) -> None:
    assert is_safe_next(target)


@pytest.mark.parametrize(
    "target",
    [
        None,
        "",
        "flats",
        "https://evil.example/",
        "http://localhost/flats",
        "//evil.example",
        "///evil.example",
        "/\\evil.example",
        "\\\\evil.example",
        "javascript:alert(1)",
        "/flats\r\nSet-Cookie: x=1",
        "/flats\x00",
    ],
)
def test_rejects_external_or_malformed_targets(target: str | None) -> None:
    assert not is_safe_next(target)
