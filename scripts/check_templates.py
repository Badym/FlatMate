"""Kontrola szablonów i kodu pod kątem konstrukcji niezgodnych z CSP i ryzykownych dla XSS.

Uruchamiane w CI (job ``templates``). Zwraca kod 1, gdy znajdzie naruszenie:

- filtr ``|safe`` i ``Markup()`` (wyłączają escapowanie, T-05),
- inline ``<script>`` bez ``src`` i atrybuty ``on*=`` (CSP: script-src 'self'),
- atrybuty ``style=`` (CSP: style-src 'self'),
- adresy ``javascript:``.

Użycie: ``python scripts/check_templates.py [katalog_projektu]``
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

TEMPLATE_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("filtr |safe wyłącza escapowanie", re.compile(r"\|\s*safe\b")),
    ("inline <script> bez src", re.compile(r"<script\b(?![^>]*\bsrc\s*=)[^>]*>", re.IGNORECASE)),
    ("atrybut obsługi zdarzenia on*=", re.compile(r"<[^>]+\son[a-z]+\s*=", re.IGNORECASE)),
    ("atrybut style= (użyj klasy CSS)", re.compile(r"<[^>]+\sstyle\s*=", re.IGNORECASE)),
    ("adres javascript:", re.compile(r"javascript\s*:", re.IGNORECASE)),
)

PYTHON_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("Markup() wyłącza escapowanie", re.compile(r"\bMarkup\s*\(")),
)


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.message}"


def _scan(path: Path, rules: tuple[tuple[str, re.Pattern[str]], ...]) -> list[Violation]:
    violations = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        for message, pattern in rules:
            if pattern.search(line):
                violations.append(Violation(path, number, message))
    return violations


def find_violations(project_root: Path) -> list[Violation]:
    """Sprawdza szablony w frontend/templates i moduły Pythona w backend."""
    violations: list[Violation] = []
    for template in sorted((project_root / "frontend" / "templates").rglob("*.html")):
        violations.extend(_scan(template, TEMPLATE_RULES))
    for module in sorted((project_root / "backend").rglob("*.py")):
        violations.extend(_scan(module, PYTHON_RULES))
    return violations


def main(argv: list[str]) -> int:
    project_root = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parent.parent
    violations = find_violations(project_root)
    for violation in violations:
        print(violation)
    if violations:
        print(f"\nZnaleziono naruszeń: {len(violations)}")
        return 1
    print("Szablony zgodne z zasadami CSP i XSS.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
