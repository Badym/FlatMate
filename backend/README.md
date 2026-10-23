# Backend FlatMate

Aplikacja Flask w architekturze warstwowej (MVC). Widok, czyli szablony, CSS i JS, jest w [`frontend/`](../frontend/README.md). Backend go renderuje, więc obie części działają jako jedna aplikacja i jeden kontener.

## Struktura

```
backend/
├── __init__.py       create_app(): konfiguracja, rozszerzenia, nagłówki, kontrolery
├── core/
│   ├── config.py     konfiguracje środowisk (development, testing, production) z .env
│   ├── extensions.py instancje rozszerzeń: db, migrate, csrf, limiter, login_manager
│   └── constants.py  stałe domenowe (długości pól, paleta kolorów użytkowników)
├── controllers/      C – endpointy HTTP (blueprinty), *_controller.py
├── services/         logika biznesowa i granice transakcji, *_service.py
├── repositories/     zapytania do bazy (tylko ORM), *_repository.py
├── models/           M – encje ORM, jedna na plik
├── forms/            formularze WTForms: walidacja danych wejściowych i CSRF
├── security/         nagłówki bezpieczeństwa, później dekoratory dostępu
├── migrations/       migracje Alembic (Flask-Migrate)
└── demo_data.py      przykładowe dane do makiet (strona główna, /_ui/)
```

## Przepływ żądania

```
żądanie → controller → form (walidacja) → service → repository → model / baza
                  ↓
        render_template("pages/…") z frontend/templates
```

| Warstwa | Odpowiada za | Nie robi |
| --- | --- | --- |
| controller | odczyt żądania, walidację formularza, wywołanie serwisu, wybór szablonu lub przekierowania | zapytań do bazy, logiki biznesowej |
| service | przypadek użycia (np. „dołącz do mieszkania”), reguły biznesowe, `db.session.commit()` | renderowania HTML, budowania zapytań SQL |
| repository | zapytania ORM do jednej encji | `commit()`; transakcję zamyka serwis |
| model | definicję tabeli i relacji | logiki żądań |

## Zasady

- **Dane mieszkania zawsze przez `FlatScopedRepository`.** Nie ma w nim `get(id)`, tylko `get_in_flat(flat_id, id)`, więc podmiana ID w adresie nie da dostępu do cudzego mieszkania (T-01).
- **Tylko ORM.** Bez SQL sklejanego z tekstu, nawet przez `text()` z f-stringiem (SR-7). Bandit sprawdza to w CI.
- **Sekrety tylko z `.env`.** `core/config.py` w produkcji nie wystartuje bez `SECRET_KEY` (minimum 32 znaki) i `DATABASE_URL` (SR-10).
- **Zmiana modelu oznacza migrację w tym samym PR-ze:** `uv run flask --app wsgi db migrate -m "opis"`, a potem sprawdzenie wygenerowanego pliku w `migrations/versions/`.
- **Nowy moduł funkcji** (np. zadania): `controllers/tasks_controller.py` (blueprint zarejestrowany w `controllers/__init__.py`), `services/task_service.py`, `repositories/task_repository.py`, `models/task.py` (import w `models/__init__.py`), formularze w `forms/`, strony w `frontend/templates/pages/tasks/` i testy w `tests/backend/`.
