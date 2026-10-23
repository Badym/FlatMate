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
├── security/         nagłówki, dekoratory dostępu, hasła, tokeny, ładowanie sesji
├── migrations/       migracje Alembic (Flask-Migrate)
├── audit.py          dziennik zdarzeń bezpieczeństwa (JSON na stdout)
├── cli.py            polecenia flask, np. seed-demo
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

- **Każda trasa mieszkania ma `<int:flat_id>` i dekorator** `@flat_member_required` albo `@flat_admin_required` (`security/access.py`). Dekorator wymaga zalogowania, ładuje `g.flat` i `g.membership`, zwraca 404 osobie spoza mieszkania i 403 członkowi bez roli admina.
- **ID z formularzy sprawdzaj względem mieszkania:** osobę przez `MembershipService.is_active_member` (lista wyboru: `member_choices`), typ zadania przez `TaskTypeRepository.get_available`.
- **Zdarzenia bezpieczeństwa przez `audit_event("nazwa", pole=…)`** (`audit.py`). IP, ścieżka i ID użytkownika dochodzą same, a pola z „password”, „token” czy „secret” w nazwie są ukrywane.
- **Hasła tylko przez `security/passwords.py`:** `hash_password` i `verify_password` (stały czas także dla nieistniejącego konta).
- **Dane mieszkania zawsze przez `FlatScopedRepository`.** Nie ma w nim `get(id)`, tylko `get_in_flat(flat_id, id)`, więc podmiana ID w adresie nie da dostępu do cudzego mieszkania (T-01).
- **Tylko ORM.** Bez SQL sklejanego z tekstu, nawet przez `text()` z f-stringiem (SR-7). Bandit sprawdza to w CI.
- **Sekrety tylko z `.env`.** `core/config.py` w produkcji nie wystartuje bez `SECRET_KEY` (minimum 32 znaki) i `DATABASE_URL` (SR-10).
- **Zmiana modelu oznacza migrację w tym samym PR-ze:** `uv run flask --app wsgi db migrate -m "opis"`, a potem sprawdzenie wygenerowanego pliku w `migrations/versions/`.
- **Nowy moduł funkcji** (np. zadania): `controllers/tasks_controller.py` (blueprint zarejestrowany w `controllers/__init__.py`), `services/task_service.py`, `repositories/task_repository.py`, `models/task.py` (import w `models/__init__.py`), formularze w `forms/`, strony w `frontend/templates/pages/tasks/` i testy w `tests/backend/`.
