"""Przykładowe dane do makiet: podgląd na stronie głównej i w /_ui.

To wyłącznie treść prezentacyjna; nie trafia do bazy. Kształt słowników
odpowiada parametrom komponentów w frontend/templates/components/
(avatar, task_item), więc makiety i prawdziwe ekrany używają tych samych
komponentów.
"""

from __future__ import annotations

from typing import Any

MEMBERS: list[dict[str, Any]] = [
    {"display_name": "Ola Nowak", "initials": "ON", "color_index": 0, "points": 64, "role": "admin"},
    {"display_name": "Kuba Wiśniewski", "initials": "KW", "color_index": 9, "points": 51, "role": "member"},
    {"display_name": "Marta Zając", "initials": "MZ", "color_index": 3, "points": 38, "role": "member"},
    {"display_name": "Piotr Lis", "initials": "PL", "color_index": 6, "points": 22, "role": "member"},
]

TASKS: list[dict[str, Any]] = [
    {
        "title": "Sprzątanie łazienki",
        "type": "Sprzątanie",
        "icon": "bi-droplet-half",
        "due": "Dziś",
        "status": "today",
        "mode": "rotation",
        "assignee": MEMBERS[0],
        "points": 15,
    },
    {
        "title": "Zakupy: środki czystości",
        "type": "Zakupy",
        "icon": "bi-basket2",
        "due": "Pt, 24 paź",
        "status": "pool",
        "mode": "pool",
        "assignee": None,
        "points": 10,
    },
    {
        "title": "Wyniesienie śmieci",
        "type": "Śmieci",
        "icon": "bi-trash3",
        "due": "Wczoraj",
        "status": "overdue",
        "mode": "fixed",
        "assignee": MEMBERS[1],
        "points": 5,
    },
    {
        "title": "Odkurzanie salonu",
        "type": "Sprzątanie",
        "icon": "bi-stars",
        "due": "Sob, 25 paź",
        "status": "upcoming",
        "mode": "rotation",
        "assignee": MEMBERS[2],
        "points": 10,
    },
    {
        "title": "Rozmrożenie lodówki",
        "type": "Kuchnia",
        "icon": "bi-snow",
        "due": "Pn, 20 paź",
        "status": "done",
        "mode": "fixed",
        "assignee": MEMBERS[3],
        "points": 20,
    },
]

WEEK: list[dict[str, Any]] = [
    {"day": "Pn", "date": 20, "events": [{"title": "Lodówka", "color": 6}]},
    {"day": "Wt", "date": 21, "events": []},
    {"day": "Śr", "date": 22, "events": [{"title": "Śmieci", "color": 9}], "today": True},
    {"day": "Cz", "date": 23, "events": [{"title": "Łazienka", "color": 0}]},
    {"day": "Pt", "date": 24, "events": [{"title": "Zakupy", "color": None}]},
    {"day": "So", "date": 25, "events": [{"title": "Salon", "color": 3}, {"title": "Pranie", "color": 0}]},
    {"day": "Nd", "date": 26, "events": []},
]
