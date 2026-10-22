"""Przykładowe dane do makiet: podgląd na stronie głównej i w /_ui.

To wyłącznie treść prezentacyjna; nie trafia do bazy i zniknie z makiet,
gdy pulpit mieszkania zacznie korzystać z prawdziwych danych.
"""

from __future__ import annotations

from typing import Any

MEMBERS: list[dict[str, Any]] = [
    {"name": "Ola Nowak", "initials": "ON", "color": 0, "points": 64, "role": "admin"},
    {"name": "Kuba Wiśniewski", "initials": "KW", "color": 9, "points": 51, "role": "member"},
    {"name": "Marta Zając", "initials": "MZ", "color": 3, "points": 38, "role": "member"},
    {"name": "Piotr Lis", "initials": "PL", "color": 6, "points": 22, "role": "member"},
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
