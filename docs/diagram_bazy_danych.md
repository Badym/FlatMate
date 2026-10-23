# Diagram bazy danych

Schemat z migracji `backend/migrations/versions/*_schemat_poczatkowy.py`, zgodny z modelami w `backend/models/` (sprawdza to `flask db check` w CI). GitHub rysuje diagram automatycznie. Wcześniejszy `diagram_bazy_danych.png` pokazuje tylko klucze z etapu projektowania.

```mermaid
erDiagram
    users ||--o{ memberships : "należy do"
    flats ||--o{ memberships : "ma członków"
    flats ||--o{ invites : "zaproszenia"
    users ||--o{ invites : "tworzy"
    flats |o--o{ task_types : "własne typy"
    flats ||--o{ tasks : "zadania"
    task_types ||--o{ tasks : "typ"
    users |o--o{ tasks : "przypisany / wykonał / utworzył"
    tasks |o--o{ tasks : "wystąpienia serii"
    tasks ||--o{ rotation_members : "kolejka rotacji"
    users ||--o{ rotation_members : "w kolejce"

    users {
        int id PK
        string email UK "małymi literami"
        string display_name
        string password_hash "scrypt z solą"
        smallint color_index "0-11, paleta USER_COLORS"
        string avatar_filename "losowa nazwa"
        string session_token UK "get_id(), D-13"
        int failed_logins
        timestamptz locked_until
        timestamptz created_at
    }

    flats {
        int id PK
        string name
        timestamptz created_at
    }

    memberships {
        int id PK
        int user_id FK
        int flat_id FK
        string role "admin | member; jeden admin na mieszkanie"
        string status "pending | active | rejected"
        timestamptz joined_at
        timestamptz created_at
    }

    invites {
        int id PK
        int flat_id FK
        int created_by_id FK
        string token_hash UK "SHA-256, sam token tylko w linku"
        timestamptz expires_at "7 dni"
        bool revoked
        timestamptz created_at
    }

    task_types {
        int id PK
        int flat_id FK "NULL = typ globalny"
        string name
        string icon "klasa Bootstrap Icons"
        smallint default_points "1-100"
    }

    tasks {
        int id PK
        int flat_id FK
        int task_type_id FK
        int assignee_id FK "NULL = pula"
        int created_by_id FK
        int parent_task_id FK "szablon serii, SET NULL"
        int occurrence_index "numer wystąpienia"
        string title
        text description
        date due_date
        smallint points "1-100"
        string status "open | done"
        timestamptz done_at
        int done_by_id FK
        string recurrence "none | daily | weekly | monthly"
        string assignment_mode "fixed | rotation | pool"
        timestamptz created_at
    }

    rotation_members {
        int id PK
        int task_id FK
        int user_id FK
        smallint position
    }
```

## Ograniczenia w bazie

| Tabela | Ograniczenie | Po co |
| --- | --- | --- |
| `users` | `email` i `session_token` unikalne; `color_index` 0–11; `failed_logins >= 0` | jedno konto na adres, sesje jednoznaczne |
| `memberships` | unikalna para `(user_id, flat_id)`; indeks częściowy: co najwyżej jeden `admin` w mieszkaniu | brak podwójnych członkostw, niezmiennik roli admina |
| `invites` | `token_hash` unikalny | wyszukiwanie zaproszenia po skrócie tokenu |
| `task_types` | unikalna para `(flat_id, name)`; `icon LIKE 'bi-%'`; punkty 1–100 | ikona trafia do atrybutu `class`, więc tylko klasy Bootstrap Icons |
| `tasks` | unikalna para `(parent_task_id, occurrence_index)`; `status = done` wtedy i tylko wtedy, gdy jest `done_at`; wystąpienie serii nie może się powtarzać; punkty 1–100; opis do 1000 znaków | spójność serii cyklicznych i punktów |
| `rotation_members` | unikalna para `(task_id, user_id)` | osoba raz w kolejce |
| wszystkie | wartości wyliczeniowe jako tekst z `CHECK` (D-22) | nowa wartość to zwykła migracja |

Usunięcie mieszkania kasuje w bazie jego członkostwa, zaproszenia, własne typy i zadania (`ON DELETE CASCADE`). Usunięcie użytkownika zdejmuje go z zadań (`SET NULL`), a usunięcie szablonu serii zostawia wykonane wystąpienia jako historię punktów.
