# Plan implementacji – FlatMate

Plan opiera się na [README.md](../README.md), [REQUIREMENTS.md](../REQUIREMENTS.md) i diagramach w katalogu `docs/`:

- `diagram_A_architektura.png` – architektura i ścieżka żądania,
- `diagram_B_przeplyw.png` – przepływ działania aplikacji,
- `diagram_C_devsecops.png` – proces DevSecOps,
- `diagram_bazy_danych.png` – model danych.

Oznaczenia: **FR-x** to wymaganie funkcjonalne, **SR-x** to wymaganie bezpieczeństwa, a **T-xx** to zagrożenie z modelu zagrożeń w REQUIREMENTS.md.

---

## 0. Decyzje projektowe

| # | Temat | Decyzja | Uzasadnienie |
| --- | --- | --- | --- |
| D-1 | Minimalna długość hasła | **12 znaków**, ujednolicone w SR-1 i T-03 (zrobione) | ostrzejsza z dwóch wartości |
| D-2 | Flask-Limiter, Pillow | dopisane do listy bibliotek w README (zrobione) | używane w T-03 i T-10 |
| D-3 | Punkty | pole `points` w `task_type` i `task`; punkty dostaje **osoba przypisana** do zadania w chwili wykonania | README, diagram B („oznaczenie + punkty”) |
| D-4 | Prośba o dołączenie | `membership.status`: `pending` / `active` / `rejected` | odrzucenie zostaje w bazie, więc nie da się zasypywać admina prośbami; admin może usunąć odrzucenie i wtedy prośbę można wysłać ponownie |
| D-5 | Brak dostępu | **404** dla osoby spoza mieszkania (T-01), **403** dla członka bez roli admina na trasach admina (T-02) | członek i tak wie, że mieszkanie istnieje; 403 jest czytelniejsze w testach |
| D-6 | Kolor użytkownika | paleta 12 kolorów; w bazie `color_index`, w HTML klasa `.u-color-N` | CSP (`style-src 'self'`) blokuje atrybuty `style=""` |
| D-7 | Zadania cykliczne | szablon serii + wystąpienia wyliczane z numeru wystąpienia (sekcja 3.1) | rotacja nie zatrzymuje się na osobie, która nie wykonała zadania; kalendarz widzi przyszłe terminy |
| D-8 | Przypisywanie | członek tworzy zadania **dla siebie albo do puli**; wskazanie innej osoby (także w rotacji i przy edycji) może zrobić tylko admin | w REQUIREMENTS przypisanie zadania jest uprawnieniem admina |
| D-9 | Wykonanie zadania z puli | najpierw „Biorę”, potem „Wykonane”; zadania bez osoby nie da się oznaczyć jako wykonane | jednoznacznie wiadomo, komu należą się punkty |
| D-10 | Odejście lub usunięcie członka | jego otwarte zadania wracają do puli, a on znika z rotacji (sekcja 3.2) | nic nie zostaje przypisane osobie spoza mieszkania |
| D-11 | Ostatni członek | admin wychodzi dopiero po przekazaniu roli; gdy jest jedynym członkiem, wyjście oznacza usunięcie mieszkania (z potwierdzeniem nazwą) | mieszkanie zawsze ma admina |
| D-12 | Zaproszenia | link wielorazowy, ważny do wygaśnięcia (7 dni) albo unieważnienia | każde dołączenie i tak akceptuje admin |
| D-13 | Sesje | bez opcji „zapamiętaj mnie”; `User.session_token` zwracany przez `get_id()`, zmieniany przy wylogowaniu i zmianie hasła | sesja Flaska jest w ciasteczku po stronie klienta, więc `session.clear()` nie unieważnia skradzionej kopii; ceną jest wylogowanie na wszystkich urządzeniach |
| D-14 | Enumeracja kont | rejestracja ujawnia, że e-mail jest zajęty; **akceptujemy to jako ryzyko szczątkowe**, ograniczone limitem na `/register` i opisane w modelu zagrożeń | bez weryfikacji e-mailem nie da się tego ukryć |
| D-15 | Migracje | bez Flask-Migrate: `flask init-db`; w etapach 3–8 każda zmiana schematu oznacza reset bazy, a dane testowe odtwarza `flask seed-demo` | wystarczy dla projektu bez danych produkcyjnych |
| D-16 | Wdrożenie | obraz Docker (gunicorn: 1 proces, kilka wątków) za reverse proxy z HTTPS; host do potwierdzenia w etapie 9 (np. Render albo VPS z Caddy) | SR-3 wymaga HTTPS (`Secure`, HSTS); jeden proces oznacza wspólne liczniki limitera w pamięci |
| D-17 | Czas | znaczniki czasu w UTC; terminy zadań (`due_date`) jako `Date` | proste porównania wygasania zaproszeń i blokad |

---

## 1. Stack i zależności

`requirements.txt` z przypiętymi wersjami (T-12):

```
Flask
Flask-SQLAlchemy
Flask-Login
Flask-WTF            # CSRF + WTForms
email-validator      # walidator Email w WTForms
Flask-Limiter        # T-03, magazyn memory:// (D-16)
Pillow               # T-10
python-dotenv        # SR-10
gunicorn             # serwer produkcyjny (D-16)
```

`requirements-dev.txt`:

```
pytest
pytest-cov
bandit
pip-audit
```

Wersje przypinamy (`==`) przy pierwszej instalacji poleceniem `pip freeze`. Dependabot aktualizuje je później przez PR-y.

---

## 2. Struktura katalogów

```
FlatMate/
├── app/
│   ├── __init__.py          # create_app(), rejestracja blueprintów i rozszerzeń, ProxyFix (prod)
│   ├── config.py            # Config, TestConfig, ProductionConfig
│   ├── extensions.py        # db, login_manager, csrf, limiter
│   ├── models.py            # modele ORM, PRAGMA foreign_keys, kaskady
│   ├── constants.py         # PALETTE (12 kolorów), limity długości pól
│   ├── security.py          # nagłówki (CSP itd.), dekoratory dostępu, is_safe_next()
│   ├── audit.py             # logger zdarzeń bezpieczeństwa
│   ├── cli.py               # flask init-db, flask seed-demo
│   ├── services/
│   │   ├── recurrence.py    # wyliczanie i zapisywanie wystąpień zadań cyklicznych
│   │   ├── membership.py    # odejście/usunięcie członka, przekazanie roli
│   │   ├── tasks.py         # claim/done jako warunkowe UPDATE, punkty
│   │   └── avatars.py       # walidacja i zapis awatarów
│   ├── auth/                # rejestracja, logowanie, wylogowanie
│   │   ├── routes.py
│   │   └── forms.py
│   ├── profile/             # edycja profilu, awatar, hasło
│   ├── flats/               # mieszkania, członkowie, zaproszenia
│   ├── tasks/               # zadania, typy zadań, pula, wykonanie
│   ├── calendar/            # widok kalendarza
│   ├── templates/
│   │   ├── base.html
│   │   ├── auth/ profile/ flats/ tasks/ calendar/ errors/
│   └── static/
│       ├── css/ js/         # własne pliki, bez inline JS i inline stylów (CSP)
│       ├── vendor/          # Bootstrap 5 lokalnie (CSP bez zewnętrznych CDN)
│       └── uploads/         # awatary, w .gitignore
├── instance/                # flatmate.db, w .gitignore
├── scripts/
│   └── check_templates.py   # kontrola szablonów w CI (|safe, Markup, inline JS/style)
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_sessions.py
│   ├── test_profile.py
│   ├── test_flats.py
│   ├── test_membership.py
│   ├── test_invites.py
│   ├── test_tasks.py
│   ├── test_recurrence.py
│   ├── test_access_control.py   # IDOR, eskalacja uprawnień, ID z formularzy (T-01, T-02)
│   ├── test_security_headers.py
│   └── test_audit.py
├── .github/
│   ├── workflows/ci.yml
│   └── dependabot.yml
├── .zap/
│   └── automation.yaml      # plan skanu ZAP z logowaniem (etap 9)
├── .env.example             # wzór bez prawdziwych sekretów
├── Dockerfile               # etap 9
├── requirements.txt
├── requirements-dev.txt
├── run.py                   # punkt startowy (dev)
└── wsgi.py                  # punkt startowy (prod)
```

---

## 3. Model danych

Na podstawie `diagram_bazy_danych.png`. Diagram podaje tylko klucze, a poniżej są uzupełnione pola. W etapie 3 trzeba zaktualizować diagram o `task.parent_task_id` i `task_type.flat_id`.

SQLite domyślnie nie pilnuje kluczy obcych, więc w `models.py` włączamy `PRAGMA foreign_keys=ON` przez event `connect` silnika SQLAlchemy. Relacje `Flat → memberships / invites / tasks / task_types` mają `cascade="all, delete-orphan"`, a klucze obce `ondelete="CASCADE"` (wyjątki opisane przy polach).

### `user`
| Pole | Typ | Uwagi |
| --- | --- | --- |
| id | Integer PK | |
| email | String(254), unique, index | zapisywany małymi literami |
| display_name | String(50) | |
| password_hash | String(255) | `werkzeug.security.generate_password_hash` (scrypt z solą), SR-1 |
| color_index | SmallInteger | 0–11, indeks w `PALETTE` (D-6) |
| avatar_filename | String(64), nullable | losowa nazwa, SR-9 |
| session_token | String(64), unique, index | `secrets.token_hex(32)`; zwracany przez `get_id()`, nowy przy wylogowaniu i zmianie hasła (D-13) |
| failed_logins | Integer, default 0 | licznik nieudanych logowań na konto (sekcja 5) |
| locked_until | DateTime, nullable | czasowa blokada konta |
| created_at | DateTime | |

### `flat`
| Pole | Typ | Uwagi |
| --- | --- | --- |
| id | Integer PK | |
| name | String(80) | |
| created_at | DateTime | |

### `membership` (user ↔ flat, N:M)
| Pole | Typ | Uwagi |
| --- | --- | --- |
| id | Integer PK | |
| user_id | FK → user, CASCADE | |
| flat_id | FK → flat, CASCADE | |
| role | Enum(`admin`, `member`) | |
| status | Enum(`pending`, `active`, `rejected`) | D-4 |
| joined_at | DateTime | |
| | | `UniqueConstraint(user_id, flat_id)` |

Niezmiennik: każde mieszkanie ma dokładnie jednego admina ze statusem `active`.

### `invite`
| Pole | Typ | Uwagi |
| --- | --- | --- |
| id | Integer PK | |
| flat_id | FK → flat, CASCADE | |
| user_id | FK → user | autor zaproszenia (admin) |
| token_hash | String(64), unique | SHA-256 tokenu; sam token jest tylko w linku (T-08) |
| expires_at | DateTime | teraz + 7 dni |
| revoked | Boolean | unieważnienie przez admina |
| created_at | DateTime | |

Token: `secrets.token_urlsafe(32)`. W bazie trzymamy tylko jego hash, więc wyciek bazy nie ujawnia działających linków.

### `task_type`
| Pole | Typ | Uwagi |
| --- | --- | --- |
| id | Integer PK | |
| flat_id | FK → flat, nullable, CASCADE | NULL = typ domyślny (sprzątanie, zakupy, śmieci…) |
| name | String(50) | |
| default_points | Integer | |

### `task`
| Pole | Typ | Uwagi |
| --- | --- | --- |
| id | Integer PK | |
| flat_id | FK → flat, CASCADE, index | **każde zapytanie filtrowane po tym polu** (T-01) |
| task_type_id | FK → task_type | |
| assignee_id | FK → user, nullable | NULL = zadanie w puli |
| created_by_id | FK → user | autor (edycja własnych zadań) |
| parent_task_id | FK → task, nullable, **SET NULL** | rodzaj wiersza, patrz niżej |
| occurrence_index | Integer, nullable | numer wystąpienia *k*; `UniqueConstraint(parent_task_id, occurrence_index)` |
| title | String(100) | |
| description | Text (≤ 1000 znaków) | |
| due_date | Date | w szablonie: data pierwszego wystąpienia |
| points | Integer | domyślnie z `task_type` |
| status | Enum(`open`, `done`) | |
| done_at / done_by_id | DateTime / FK → user | kto kliknął „Wykonane”; punkty liczone dla `assignee_id` (D-3) |
| recurrence | Enum(`none`, `daily`, `weekly`, `monthly`) | FR-7 |
| assignment_mode | Enum(`fixed`, `rotation`, `pool`) | FR-7 |

Rodzaj wiersza:
- `parent_task_id IS NULL` i `recurrence = none` → **zadanie jednorazowe**,
- `parent_task_id IS NULL` i `recurrence ≠ none` → **szablon serii** (nie jest wyświetlany jako zadanie do zrobienia),
- `parent_task_id` ustawione → **wystąpienie serii** (`recurrence = none`).

### `rotation_member`
| Pole | Typ | Uwagi |
| --- | --- | --- |
| id | Integer PK | |
| task_id | FK → task (szablon serii), CASCADE | |
| user_id | FK → user, CASCADE | |
| position | Integer | kolejność w rotacji |
| | | `UniqueConstraint(task_id, user_id)` |

### 3.1 Zadania cykliczne (`services/recurrence.py`)

- **Funkcja czysta** `occurrence(template, k, rotation) → (due_date, assignee_id)`:
  - `daily`: start + *k* dni; `weekly`: start + 7·*k* dni;
  - `monthly`: ten sam dzień miesiąca co start, w miesiącu start + *k*, przycięty do ostatniego dnia miesiąca (31 sty → 28/29 lut → 31 mar). Liczony zawsze od startu, a nie od poprzedniego wystąpienia;
  - `fixed` → `template.assignee_id`; `rotation` → `rotation[k mod n]` według `position`; `pool` → `None`.
- `ensure_occurrences(flat, horizon=dziś + 28 dni)` zapisuje brakujące wystąpienia do horyzontu. Wywołują ją pulpit, lista zadań i kalendarz. `UniqueConstraint(parent_task_id, occurrence_index)` chroni przed duplikatami przy równoległych żądaniach (`IntegrityError` jest przechwytywany).
- Kalendarz poza horyzontem pokazuje wystąpienia wyliczone funkcją `occurrence`, ale niezapisane w bazie (oznaczone jako „planowane”).
- Zaległe wystąpienia zostają otwarte i oznaczone jako zaległe. Nie wstrzymują kolejnych, więc rotacja idzie dalej.
- Edycja szablonu usuwa niewykonane wystąpienia z terminem ≥ dziś i generuje je od nowa. Wykonane i zaległe zostają.
- Usunięcie serii usuwa szablon i jego niewykonane wystąpienia. Wykonane zostają z `parent_task_id = NULL`, żeby nie zniknęła historia punktów.

### 3.2 Odejście lub usunięcie członka (`services/membership.py`)

`remove_member(membership)` w jednej transakcji, wspólne dla „opuść mieszkanie” i „usuń członka”:
1. usuwa osobę z `rotation_member`; pusta rotacja zmienia tryb serii na `pool`,
2. szablony `fixed` przypisane do tej osoby przechodzą w tryb `pool`,
3. niewykonane wystąpienia z terminem ≥ dziś w zmienionych seriach są generowane od nowa (przy zmianie *n* kolejka rotacji się przesuwa, co świadomie akceptujemy),
4. pozostałe niewykonane zadania przypisane do tej osoby wracają do puli (`assignee_id = NULL`),
5. usuwa wiersz `membership`. Wykonane zadania i punkty zostają jako historia.

Interfejs `release_member_tasks(flat, user)` z kroków 1–4 ustalamy w etapie 3 jako szkielet. Ścieżka B implementuje go w etapie 7, a ścieżka A wywołuje go w etapie 5.

---

## 4. Trasy (blueprinty)

Wszystkie trasy zmieniające dane to **POST** z tokenem CSRF (SR-5, T-06). Trasy mieszkań mają dekoratory z sekcji 5.

Zasoby mieszkania pobieramy zawsze zapytaniem z `flat_id` z adresu, np. `Task.query.filter_by(id=tid, flat_id=id).first_or_404()`, nigdy samym `get(tid)` (T-01). Dotyczy to też `<mid>` (membership) i `<iid>` (invite).

**ID z formularzy** (`assignee_id`, członkowie rotacji, `task_type_id`) są sprawdzane względem mieszkania. Lista wyboru `SelectField` jest budowana tylko z aktywnych członków tego mieszkania lub z jego typów zadań i typów globalnych, a warstwa `services/` sprawdza to drugi raz. Obca wartość daje błąd walidacji formularza.

### auth
| Metoda | URL | Opis | Ochrona |
| --- | --- | --- | --- |
| GET/POST | `/register` | rejestracja | walidacja, hasło ≥ 12; limit `10/hour` na IP (D-14) |
| GET/POST | `/login` | logowanie; nieudana próba zwraca **401** z formularzem | limit IP liczący tylko nieudane próby + blokada konta; ogólny komunikat (SR-2, T-03); parametr `next` przez `is_safe_next()` |
| POST | `/logout` | wylogowanie | nowy `session_token`, `session.clear()` (T-07, D-13) |

### profile
| Metoda | URL | Opis |
| --- | --- | --- |
| GET/POST | `/profile` | nazwa, kolor z palety (D-6) |
| POST | `/profile/avatar` | upload awatara (SR-9, T-10) |
| POST | `/profile/password` | zmiana hasła, wymaga starego hasła; nowy `session_token`, po czym ponowne zalogowanie bieżącej sesji |

### flats
| Metoda | URL | Opis | Rola |
| --- | --- | --- | --- |
| GET | `/flats` | „Moje mieszkania” | zalogowany |
| GET/POST | `/flats/new` | utworzenie, twórca = admin (FR-3) | zalogowany |
| GET | `/flats/<id>` | pulpit: moje zadania, pula, ranking punktów | członek |
| POST | `/flats/<id>/leave` | opuszczenie; admin dostaje komunikat o przekazaniu roli, a jedyny członek trafia do potwierdzenia usunięcia mieszkania (D-11) | członek |
| GET | `/flats/<id>/members` | lista członków i prośby | członek (akcje: admin) |
| POST | `/flats/<id>/members/<mid>/approve` | akceptacja, tylko `pending` (FR-4) | admin |
| POST | `/flats/<id>/members/<mid>/reject` | odrzucenie, tylko `pending` → `rejected` | admin |
| POST | `/flats/<id>/members/<mid>/remove` | usunięcie członka przez `remove_member` albo usunięcie odrzucenia; nie dotyczy admina (FR-5) | admin |
| POST | `/flats/<id>/members/<mid>/make-admin` | przekazanie roli, tylko `active`, w jednej transakcji (FR-5) | admin |
| POST | `/flats/<id>/delete` | usunięcie mieszkania (z potwierdzeniem nazwą) | admin |
| GET/POST | `/flats/<id>/invites` | lista i tworzenie zaproszeń | admin |
| POST | `/flats/<id>/invites/<iid>/revoke` | unieważnienie | admin |
| GET/POST | `/join/<token>` | podgląd i prośba o dołączenie; istniejący wiersz `pending`/`active`/`rejected` → komunikat bez nowego wiersza | zalogowany |

### tasks
| Metoda | URL | Opis | Rola |
| --- | --- | --- | --- |
| GET | `/flats/<id>/tasks` | lista z filtrami (moje / pula / wszystkie / zaległe / wykonane) | członek |
| GET/POST | `/flats/<id>/tasks/new` | nowe zadanie lub seria (FR-6, FR-7) | członek: dla siebie lub do puli; inna osoba lub rotacja z innymi → admin (D-8) |
| GET/POST | `/flats/<id>/tasks/<tid>/edit` | edycja zadania lub szablonu serii | autor lub admin; zmiana osoby na inną niż autor → admin |
| POST | `/flats/<id>/tasks/<tid>/delete` | usunięcie zadania lub serii (sekcja 3.1) | autor lub admin |
| POST | `/flats/<id>/tasks/<tid>/claim` | „Biorę” z puli (FR-8), warunkowy UPDATE | członek |
| POST | `/flats/<id>/tasks/<tid>/assign` | przypisanie osoby | admin |
| POST | `/flats/<id>/tasks/<tid>/done` | oznaczenie wykonania, warunkowy UPDATE; zadanie bez osoby → komunikat (D-9) | przypisany lub admin |
| GET/POST | `/flats/<id>/task-types` | typy zadań mieszkania | admin |

### calendar
| Metoda | URL | Opis |
| --- | --- | --- |
| GET | `/flats/<id>/calendar?month=YYYY-MM` | siatka miesiąca renderowana po stronie serwera (FR-9): zapisane wystąpienia oraz wyliczone „planowane” poza horyzontem; kolor = klasa `.u-color-N` |

Kalendarz robimy bez zewnętrznej biblioteki JS, żeby utrzymać prosty CSP. Siatkę generuje moduł `calendar` z biblioteki standardowej. Parametr `month` przechodzi walidację formatu i zakresu (np. ±24 miesiące), żeby nie generować dowolnie dużych wyliczeń.

---

## 5. Warstwa bezpieczeństwa (mapowanie SR / T → implementacja)

| Kontrola | Implementacja | SR / T |
| --- | --- | --- |
| Hash haseł | `generate_password_hash` / `check_password_hash`, min. 12 znaków, max 128 | SR-1, T-04 |
| Limit logowań na IP | `@limiter.limit("5/minute;20/hour", methods=["POST"], deduct_when=lambda r: r.status_code == 401)`, czyli liczone są tylko nieudane próby; magazyn `memory://` przy jednym procesie gunicorna (D-16) | SR-2, T-03 |
| Blokada konta | `failed_logins` ≥ 10 → `locked_until` = teraz + 15 min; w czasie blokady ten sam ogólny komunikat; sukces zeruje licznik. Ryzyko szczątkowe: atakujący może celowo zablokować cudze konto na 15 min | SR-2, T-03 |
| Komunikat i czas logowania | ten sam komunikat dla złego e-maila, złego hasła i blokady; dla nieistniejącego konta `check_password_hash` na stałym hashu, żeby czas odpowiedzi był podobny | SR-2, T-03 |
| Prawdziwy adres IP | w prod za proxy `ProxyFix(app.wsgi_app, x_for=1, x_proto=1)`, włączane zmienną `TRUST_PROXY=1`; bez tego limiter widziałby wszystkich pod adresem proxy | SR-2, T-03 |
| Sesja | `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SECURE=True` (prod), `SESSION_COOKIE_SAMESITE="Lax"`, `PERMANENT_SESSION_LIFETIME=12h`; po zalogowaniu `session.clear()` + `login_user` (ochrona przed fixation); bez „zapamiętaj mnie” | SR-3, T-07 |
| Unieważnianie sesji | `get_id()` zwraca `session_token`, a `user_loader` szuka po nim; nowy token przy wylogowaniu i zmianie hasła, więc stare ciasteczka przestają działać (D-13) | SR-3, T-07 |
| Członkostwo | dekorator `@flat_member_required` ładuje `Membership(user, flat, status=active)` do `g.membership`, w przeciwnym razie `abort(404)` | SR-4, T-01 |
| Rola admina | dekorator `@flat_admin_required` (wymaga członkostwa) sprawdza `g.membership.role == "admin"`, w przeciwnym razie `abort(403)` (D-5) | SR-4, T-02 |
| ID z URL i formularzy | zapytania filtrowane po `flat_id`; listy wyboru i ponowna kontrola w `services/` (sekcja 4) | SR-4, T-01, T-02 |
| Bezpieczne przekierowanie | `is_safe_next(url)`: tylko ścieżki względne zaczynające się od `/`, bez `//`, `\`, schematu i hosta; w przeciwnym razie przekierowanie na `/flats` | SR-6 |
| Wyścigi „sprawdź i zmień” | „Biorę”: `UPDATE task SET assignee_id=… WHERE id=… AND flat_id=… AND assignee_id IS NULL AND status='open'`; „Wykonane”: `… WHERE status='open'`; `rowcount == 0` → komunikat „zadanie już zajęte / już wykonane”. Brak podwójnych punktów | SR-4 |
| CSRF | `CSRFProtect(app)` globalnie, `{{ form.csrf_token }}` / `csrf_token()` w każdym formularzu, także w przyciskach „Biorę” i „Usuń” | SR-5, T-06 |
| XSS | autoescape Jinja2; **zakaz `|safe` i `Markup()`** na danych użytkownika (kontrola `scripts/check_templates.py` w CI); walidatory `Length`, `Regexp`, `NumberRange` | SR-6, T-05 |
| CSP i nagłówki | `after_request`: `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin`, `X-Frame-Options: DENY`, HSTS w prod. Bez inline JS i atrybutów `style` (kolory przez klasy, D-6) | SR-6, T-05 |
| SQLi | wyłącznie ORM, bez `text()` z f-stringami; Bandit w CI | SR-7, T-09 |
| Integralność bazy | `PRAGMA foreign_keys=ON`, kaskady w relacjach, ograniczenia unikalności (sekcja 3) | SR-4, SR-7 |
| Zaproszenia | `token_urlsafe(32)`, w bazie SHA-256, `expires_at` = +7 dni, `revoked`; wyszukiwanie po hashu tokenu; użycie zaproszenia tworzy tylko `pending` | SR-8, T-08 |
| Awatary | `MAX_CONTENT_LENGTH = 2 MB`; Pillow: `Image.open` + `verify()`, potem **ponowne otwarcie** (po `verify()` obiekt nie nadaje się do użycia); format ∈ {PNG, JPEG} sprawdzany po zawartości; `Image.MAX_IMAGE_PIXELS` ≈ 16 Mpx i `DecompressionBombWarning` traktowane jako błąd; zmniejszenie do 256×256 i ponowny zapis (usuwa metadane i ewentualny payload); nazwa `secrets.token_hex(16) + ext`; usunięcie starego pliku | SR-9, T-10 |
| Logi bezpieczeństwa | `audit.py`, logger `flatmate.security` (JSON na stdout): nieudane i udane logowania, blokady kont, wylogowanie, zmiana hasła, zaproszenia, prośby, akceptacje, odrzucenia, usunięcia członków, przekazanie roli, usunięcie mieszkania, odrzucone uploady, odmowy dostępu 403/404 na trasach mieszkań. Zapisujemy ID użytkownika i IP; **nigdy** haseł, tokenów ani ciasteczek | OWASP A09 |
| Sekrety | `SECRET_KEY` z `.env` (python-dotenv); aplikacja **nie startuje**, gdy w prod brakuje klucza; `DEBUG=False` domyślnie; `.env.example` w repo; gitleaks w CI | SR-10, T-11 |
| Zależności | przypięte wersje, pip-audit w CI, Dependabot co tydzień | T-12 |
| Baza | `instance/flatmate.db` poza `static/` | T-04 |
| Strony błędów | własne 400/403/404/413/429/500 bez stack trace'ów | T-11 |

---

## 6. Szablony i UI

- `base.html`: Bootstrap 5 (lokalnie w `static/vendor`), navbar z wyborem mieszkania, komunikaty `flash`.
- Pulpit mieszkania: „Moje zadania”, „Pula do wzięcia”, zaległe, ranking punktów członków.
- Przyciski akcji („Biorę”, „Wykonane”, „Usuń”) to małe formularze POST z CSRF, bez linków GET.
- Potwierdzenia akcji destrukcyjnych przez osobną stronę lub modal Bootstrapa (JS z pliku, nie inline).
- Kolor użytkownika: `PALETTE` w `constants.py` i odpowiadające mu klasy `.u-color-0` … `.u-color-11` w `static/css`. W formularzu profilu wybór z listy, a `color_index` jest walidowany zakresem 0–11 (D-6).
- Wystąpienia „planowane” w kalendarzu są wyróżnione (np. przerywana ramka), żeby było widać, że nie istnieją jeszcze w bazie.

---

## 7. Testy (pytest)

`conftest.py`:
- fabryka aplikacji z `TestConfig`: SQLite w pamięci, `WTF_CSRF_ENABLED=False` (poza testami CSRF), `RATELIMIT_ENABLED=False` (poza testami limitera, bo inaczej testy logowania losowo dostawałyby 429), `SESSION_COOKIE_SECURE=False`;
- fixture'y `client`, `user_a`, `user_b`, `flat_a` (admin A), `flat_b` (admin B), `member_of_a`;
- helper `login(client, user)` ustawiający `_user_id = user.session_token` przez `client.session_transaction()`. Dzięki temu ścieżka B może testować zadania, zanim powstanie interfejs logowania ze ścieżki A.

Kluczowe scenariusze:

1. **Auth:** rejestracja, odrzucenie hasła < 12 znaków, duplikat e-maila, ogólny komunikat i status 401 przy błędzie, 429 po 5 nieudanych próbach (udane się nie liczą), blokada konta po 10 nieudanych z tym samym komunikatem, flagi ciasteczka.
2. **Sesje (T-07):** ciasteczko zapisane przed wylogowaniem po wylogowaniu nie działa; to samo po zmianie hasła; `next=https://evil.example` i `next=//evil.example` przekierowują na `/flats`.
3. **IDOR (T-01):** użytkownik B próbuje GET/POST na każdą trasę `/flats/<flat_a>/…` → 404; B podstawia ID zadania, członkostwa albo zaproszenia z mieszkania A pod własne mieszkanie → 404.
4. **Eskalacja (T-02):** członek (nie admin) wysyła POST na każdą trasę admina → 403, stan bazy bez zmian. Jeden test sparametryzowany listą tras admina.
5. **ID z formularzy:** członek przypisuje zadanie innej osobie lub tworzy rotację z innymi → odmowa; admin przypisuje osobę z innego mieszkania lub `pending` → błąd walidacji; `task_type_id` z innego mieszkania → błąd walidacji.
6. **CSRF (T-06):** z włączonym CSRF POST bez tokenu → 400.
7. **Zaproszenia (T-08):** wygasły, unieważniony i błędny token → brak dołączenia; poprawny token → `pending`, dopiero akceptacja admina → `active`; ponowne użycie przez członka lub osobę odrzuconą nie tworzy nowego wiersza.
8. **XSS (T-05):** zadanie z tytułem `<script>alert(1)</script>` jest w HTML escapowane; nagłówek CSP jest obecny i ma `style-src 'self'`.
9. **Awatary (T-10):** PNG/JPEG przechodzą i są zmniejszane do ≤ 256×256; SVG, HTML z rozszerzeniem `.png`, „bomba dekompresyjna” i plik > 2 MB (413) są odrzucane; nazwa pliku jest losowa.
10. **Zadania:** podwójne „Biorę” → drugie dostaje komunikat „już zajęte”; podwójne „Wykonane” nie dubluje punktów; zadania z puli bez osoby nie da się oznaczyć jako wykonane; punkty liczone dla osoby przypisanej.
11. **Zadania cykliczne (FR-7):** testy jednostkowe funkcji `occurrence`: `daily` / `weekly` / `monthly` z 31 stycznia, rotacja `k mod n`, `pool` bez osoby; `ensure_occurrences` jest idempotentne; zaległe wystąpienie nie wstrzymuje kolejnych; edycja szablonu przelicza tylko przyszłe niewykonane.
12. **Członkowie:** przekazanie roli zostawia jednego admina; admin nie wychodzi bez przekazania roli; jedyny członek po „Opuść” trafia do usunięcia mieszkania; `remove_member` oddaje zadania do puli i usuwa osobę z rotacji; usunięcie mieszkania kasuje zadania, zaproszenia i członkostwa (kaskady z włączonym `PRAGMA foreign_keys`).
13. **Logi:** nieudane logowanie emituje zdarzenie (`caplog`), a w logach nie ma hasła ani tokenu.

Cel pokrycia: **≥ 80%** (`pytest --cov=app --cov-fail-under=80`).

---

## 8. CI/CD – GitHub Actions (diagram C)

`.github/workflows/ci.yml`, uruchamiany na `pull_request` i `push` do `main`, z równoległymi jobami:

| Job | Polecenie | Blokuje merge |
| --- | --- | --- |
| tests | `pytest --cov=app --cov-fail-under=80` | tak |
| bandit (SAST) | `bandit -r app -ll` | tak |
| pip-audit | `pip-audit -r requirements.txt` | tak |
| gitleaks | `gitleaks/gitleaks-action` | tak |
| templates | `python scripts/check_templates.py`: błąd przy `|safe`, `Markup(`, inline `<script>` bez `src`, atrybutach `on*=` i `style=` w `app/templates` | tak |
| zap (DAST) | po merge do `main`: `flask init-db`, `flask seed-demo` z losowym hasłem konta demo generowanym w jobie, aplikacja w tle przez gunicorn; ZAP Automation Framework (`.zap/automation.yaml`): logowanie formularzem (`csrf_token` dodany do listy tokenów anty-CSRF w ZAP), spider, skan pasywny i baseline; raport HTML jako artefakt | nie (raport) |

Jeśli skan z logowaniem okaże się zbyt kosztowny w konfiguracji, zostaje sam baseline bez logowania. Wtedy w raporcie opisujemy ograniczenie: ZAP widzi tylko strony publiczne (logowanie i rejestrację).

`.github/dependabot.yml`: ekosystemy `pip` i `github-actions`, co tydzień.

Ochrona gałęzi `main` w ustawieniach repo: wymagane zielone checki i PR. Ustawia ją właściciel repozytorium ręcznie.

`Dockerfile` (etap 9): `python:3.x-slim`, użytkownik bez roota, `gunicorn --workers 1 --threads 4 wsgi:app` (D-16).

---

## 9. Etapy realizacji

Każdy etap to osobna gałąź i PR przechodzący przez CI. Po wspólnym etapie 3 praca idzie dwiema równoległymi ścieżkami.

| Etap | Kto | Zakres | Rezultat |
| --- | --- | --- | --- |
| **1** (zrobione) | razem | README, REQUIREMENTS, diagramy, plan | zrobione |
| **2. Szkielet + CI** | A | struktura katalogów, `create_app`, config z `.env`, rozszerzenia, `base.html`, strony błędów, nagłówki bezpieczeństwa, `requirements*.txt`, workflow CI (testy, Bandit, pip-audit, gitleaks, kontrola szablonów), Dependabot | pusta aplikacja startuje, CI zielone |
| **3. Fundament** | razem, krótko | wszystkie modele z sekcji 3 (PRAGMA, kaskady, ograniczenia), `flask init-db`, `flask seed-demo`, typy domyślne, dekoratory `@flat_member_required` / `@flat_admin_required`, helpery walidacji przynależności, `audit.py`, fixture'y testowe z logowaniem przez sesję, szkielet `release_member_tasks`, aktualizacja diagramu bazy | obie ścieżki mogą pracować niezależnie |
| **4. Auth + profil** | A | rejestracja, logowanie z limiterem i blokadą konta, `session_token`, wylogowanie, `is_safe_next`, profil z paletą kolorów, zmiana hasła, awatary | FR-1, FR-2; SR-1, 2, 3, 9 |
| **5. Mieszkania i członkowie** | A | tworzenie, pulpit, zaproszenia, prośby, akceptacja, odrzucenie, usuwanie, przekazanie roli, opuszczenie, usunięcie mieszkania, `remove_member` | FR-3, 4, 5; SR-4, 8; testy IDOR i eskalacji |
| **6. Zadania** | B | CRUD zadań jednorazowych, typy, pula, „Biorę”, przypisanie, wykonanie (warunkowe UPDATE), punkty, walidacja ID z formularzy | FR-6, FR-8 |
| **7. Zadania cykliczne** | B | `services/recurrence.py`, szablony i wystąpienia, tryby fixed / rotation / pool, `rotation_member`, implementacja `release_member_tasks` | FR-7, testy rotacji |
| **8. Kalendarz** | B | widok miesiąca, nawigacja, wystąpienia planowane, kolory użytkowników | FR-9 |
| **9. Utwardzenie, DAST, wdrożenie** | A (review B) | przegląd CSP i szablonów, `Dockerfile`, `ProxyFix`, wybór hosta z HTTPS (D-16), ZAP z logowaniem, poprawki z raportu, pokrycie ≥ 80% | raport ZAP, raport Bandit, działająca instancja |
| **10. Dokumentacja końcowa** | razem | instrukcja uruchomienia w README, zrzuty ekranu, opis wyników skanów, aktualizacja modelu zagrożeń: status kontroli i ryzyka szczątkowe (enumeracja przy rejestracji, celowa blokada cudzego konta, wylogowanie na wszystkich urządzeniach, przesuwanie kolejki rotacji) | gotowe do oddania |

Zasady współpracy:
- każdy PR recenzuje druga osoba;
- PR-y z etapów 5 i 7 (uprawnienia, przypisania, odejście członka) muszą zawierać testy dostępu z obcego konta i z konta członka;
- zmiany w modelach po etapie 3 uzgadniamy wspólnie, bo wymagają resetu bazy u obu osób (D-15).

---

## 10. Uruchomienie lokalne (docelowo w README)

```bash
python -m venv .venv
source .venv/Scripts/activate      # Windows Git Bash; Linux/macOS: .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env               # uzupełnić SECRET_KEY: python -c "import secrets; print(secrets.token_hex(32))"
flask --app run init-db
flask --app run seed-demo          # opcjonalnie: przykładowe konta, mieszkanie i zadania
flask --app run run
pytest
```

---

## 11. Definition of Done dla każdego PR

- [ ] CI zielone (testy, Bandit, pip-audit, gitleaks, kontrola szablonów),
- [ ] nowe trasy mieszkania mają `@flat_member_required` / `@flat_admin_required` i testy: obce konto → 404, członek na trasie admina → 403,
- [ ] zasoby mieszkania pobierane z filtrem `flat_id`, a ID z formularzy sprawdzane względem mieszkania,
- [ ] formularze zmieniające dane mają CSRF i używają POST,
- [ ] brak `|safe` i `Markup()` na danych użytkownika, brak inline JS i atrybutów `style`,
- [ ] operacje typu „sprawdź i zmień” (np. „Biorę”, „Wykonane”) zrobione jako warunkowy UPDATE,
- [ ] zdarzenia bezpieczeństwa logowane przez `audit.py`, bez haseł i tokenów w logach,
- [ ] brak sekretów w kodzie,
- [ ] review drugiej osoby z zespołu.

---

## 12. Historia zmian planu

- **v1 (2026-10-22):** pierwsza wersja.
- **v2 (2026-10-22):** poprawki po przeglądzie planu:
  - kolor użytkownika z palety zamiast atrybutu `style`, zgodnie z CSP (D-6),
  - zadania cykliczne jako szablon i wystąpienia wyliczane z numeru (sekcja 3.1),
  - limiter liczy tylko nieudane próby, do tego blokada konta i `ProxyFix`,
  - unieważnianie sesji przez `session_token` (D-13),
  - walidacja ID z formularzy względem mieszkania,
  - `PRAGMA foreign_keys` i kaskady w SQLite,
  - ochrona parametru `next`, warunkowe UPDATE, logi bezpieczeństwa,
  - zabezpieczenia awatarów przed „bombą dekompresyjną”,
  - 403 dla członka na trasach admina (D-5),
  - nowe decyzje D-8 … D-17: przypisywanie, pula, odejście członka, ostatni członek, zaproszenia, enumeracja, migracje, wdrożenie, czas,
  - nowy podział pracy z wspólnym etapem 3 i dwiema równoległymi ścieżkami,
  - ZAP z logowaniem i kontrola szablonów w CI.
