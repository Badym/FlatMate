# Plan implementacji – FlatMate

Plan opiera się na [README.md](../README.md), [REQUIREMENTS.md](../REQUIREMENTS.md) i diagramach w katalogu `docs/`:

- `diagram_A_architektura.png` – architektura i ścieżka żądania,
- `diagram_B_przeplyw.png` – przepływ działania aplikacji,
- `diagram_C_devsecops.png` – proces DevSecOps,
- `diagram_bazy_danych.png` – model danych.

Oznaczenia: **FR-x** to wymaganie funkcjonalne, **SR-x** to wymaganie bezpieczeństwa, a **T-xx** to zagrożenie z modelu zagrożeń w REQUIREMENTS.md.

---

## 0. Decyzje i niespójności do ujednolicenia

| Temat | Stan w dokumentach | Decyzja w planie |
| --- | --- | --- |
| Minimalna długość hasła | SR-1 podawało 12 znaków, T-03 podawało 8 | **12 znaków**, poprawione w T-03 (zrobione) |
| Flask-Limiter, Pillow | wymienione w T-03, T-10 i na diagramie A, ale brakowało ich w README | dopisane do listy bibliotek w README (zrobione) |
| Punkty | README i diagram B („oznaczenie + punkty”) o nich mówią, wymagania FR już nie | pole `points` w `task_type` i `task` oraz suma punktów członka na pulpicie (FR-8) |
| Prośba o dołączenie | diagram B: „wysłanie prośby” → „admin akceptuje?” | `membership.status = pending/active`, bez osobnej tabeli |
| Odpowiedź przy braku dostępu | T-01, diagram A | **404** dla nie-członka, **404** także dla członka bez roli admina na trasach admina (bez zdradzania struktury) |

---

## 1. Stack i zależności

`requirements.txt` z przypiętymi wersjami (T-12):

```
Flask
Flask-SQLAlchemy
Flask-Login
Flask-WTF            # CSRF + WTForms
email-validator      # walidator Email w WTForms
Flask-Limiter        # T-03
Pillow               # T-10
python-dotenv        # SR-10
gunicorn             # serwer produkcyjny (opcjonalnie waitress na Windows)
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
│   ├── __init__.py          # create_app(), rejestracja blueprintów i rozszerzeń
│   ├── config.py            # Config, TestConfig, ProductionConfig
│   ├── extensions.py        # db, login_manager, csrf, limiter
│   ├── models.py            # modele ORM
│   ├── security.py          # nagłówki (CSP itd.), dekoratory dostępu
│   ├── services/
│   │   ├── rotation.py      # logika zadań cyklicznych i rotacji
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
│       ├── css/ js/         # własne pliki, bez inline JS (CSP)
│       ├── vendor/          # Bootstrap 5 lokalnie (CSP bez zewnętrznych CDN)
│       └── uploads/         # awatary, w .gitignore
├── instance/                # flatmate.db, w .gitignore
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_profile.py
│   ├── test_flats.py
│   ├── test_invites.py
│   ├── test_tasks.py
│   ├── test_rotation.py
│   ├── test_access_control.py   # IDOR i eskalacja uprawnień (T-01, T-02)
│   └── test_security_headers.py
├── .github/
│   ├── workflows/ci.yml
│   └── dependabot.yml
├── .env.example             # wzór bez prawdziwych sekretów
├── .gitleaks.toml           # opcjonalnie
├── requirements.txt
├── requirements-dev.txt
├── run.py                   # punkt startowy (dev)
└── wsgi.py                  # punkt startowy (prod)
```

---

## 3. Model danych

Na podstawie `diagram_bazy_danych.png`. Diagram podaje tylko klucze, a poniżej są uzupełnione pola.

### `user`
| Pole | Typ | Uwagi |
| --- | --- | --- |
| id | Integer PK | |
| email | String(254), unique, index | zapisywany małymi literami |
| display_name | String(50) | |
| password_hash | String(255) | `werkzeug.security.generate_password_hash` (scrypt/pbkdf2 z solą), SR-1 |
| color | String(7) | `#RRGGBB`, walidacja regexem |
| avatar_filename | String(64), nullable | losowa nazwa, SR-9 |
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
| user_id | FK → user | |
| flat_id | FK → flat | |
| role | Enum(`admin`, `member`) | |
| status | Enum(`pending`, `active`) | prośba o dołączenie = `pending` |
| joined_at | DateTime | |
| | | `UniqueConstraint(user_id, flat_id)` |

Niezmiennik: każde mieszkanie ma dokładnie jednego admina z `status=active`.

### `invite`
| Pole | Typ | Uwagi |
| --- | --- | --- |
| id | Integer PK | |
| flat_id | FK → flat | |
| user_id | FK → user | autor zaproszenia (admin) |
| token_hash | String(64), unique | SHA-256 tokenu; sam token tylko w linku (T-08) |
| expires_at | DateTime | teraz + 7 dni |
| revoked | Boolean | unieważnienie przez admina |
| created_at | DateTime | |

Token: `secrets.token_urlsafe(32)`. W bazie trzymamy tylko jego hash, więc wyciek bazy nie ujawnia działających linków.

### `task_type`
Diagram nie pokazuje `flat_id`, ale typy są definiowane per mieszkanie. Dodajemy `flat_id`, ewentualnie z kilkoma globalnymi typami domyślnymi przy `flat_id = NULL`.
| Pole | Typ | Uwagi |
| --- | --- | --- |
| id | Integer PK | |
| flat_id | FK → flat, nullable | NULL = typ domyślny (sprzątanie, zakupy, śmieci…) |
| name | String(50) | |
| default_points | Integer | |

### `task`
| Pole | Typ | Uwagi |
| --- | --- | --- |
| id | Integer PK | |
| flat_id | FK → flat, index | **każde zapytanie filtrowane po tym polu** (T-01) |
| task_type_id | FK → task_type | |
| assignee_id | FK → user, nullable | NULL = zadanie w puli |
| created_by_id | FK → user | właściciel zadania (edycja własnych zadań) |
| title | String(100) | |
| description | Text(≤1000) | |
| due_date | Date | |
| points | Integer | domyślnie z `task_type` |
| status | Enum(`open`, `done`) | |
| done_at / done_by_id | DateTime / FK → user | do sumowania punktów |
| recurrence | Enum(`none`, `daily`, `weekly`, `monthly`) | FR-7 |
| assignment_mode | Enum(`fixed`, `rotation`, `pool`) | FR-7 |
| series_id | Integer, nullable | wiąże kolejne wystąpienia zadania cyklicznego |

### `rotation_member`
| Pole | Typ | Uwagi |
| --- | --- | --- |
| id | Integer PK | |
| task_id | FK → task | pierwsze zadanie serii (lub `series_id`) |
| user_id | FK → user | |
| position | Integer | kolejność w rotacji |

### Logika zadań cyklicznych (`services/rotation.py`)
- Gdy zadanie cykliczne zostanie oznaczone jako wykonane, tworzone jest kolejne wystąpienie z `due_date` przesuniętym o okres.
- `fixed` – ta sama osoba,
- `rotation` – następna osoba wg `position` (pomijając osoby, które opuściły mieszkanie),
- `pool` – `assignee_id = NULL`, każdy członek może przejąć.
- Bez crona: następne wystąpienie powstaje w chwili wykonania poprzedniego, co jest prostsze i deterministyczne do testów.

---

## 4. Trasy (blueprinty)

Wszystkie trasy zmieniające dane to **POST** z tokenem CSRF (SR-5, T-06). Trasy mieszkań mają dekoratory z sekcji 5.

### auth
| Metoda | URL | Opis | Ochrona |
| --- | --- | --- | --- |
| GET/POST | `/register` | rejestracja | walidacja, hasło ≥ 12 |
| GET/POST | `/login` | logowanie | Flask-Limiter, np. `5/minute;20/hour` na IP; ogólny komunikat (SR-2, T-03) |
| POST | `/logout` | wylogowanie | `session.clear()` (T-07) |

### profile
| Metoda | URL | Opis |
| --- | --- | --- |
| GET/POST | `/profile` | nazwa, kolor |
| POST | `/profile/avatar` | upload awatara (SR-9, T-10) |
| POST | `/profile/password` | zmiana hasła, wymaga starego hasła |

### flats
| Metoda | URL | Opis | Rola |
| --- | --- | --- | --- |
| GET | `/flats` | „Moje mieszkania” | zalogowany |
| GET/POST | `/flats/new` | utworzenie, twórca = admin (FR-3) | zalogowany |
| GET | `/flats/<id>` | pulpit mieszkania: zadania, punkty | członek |
| POST | `/flats/<id>/leave` | opuszczenie (admin musi najpierw przekazać rolę) | członek |
| GET | `/flats/<id>/members` | lista członków i prośby | członek (akcje: admin) |
| POST | `/flats/<id>/members/<mid>/approve` | akceptacja prośby (FR-4) | admin |
| POST | `/flats/<id>/members/<mid>/reject` | odrzucenie | admin |
| POST | `/flats/<id>/members/<mid>/remove` | usunięcie członka (FR-5) | admin |
| POST | `/flats/<id>/members/<mid>/make-admin` | przekazanie roli (FR-5) | admin |
| POST | `/flats/<id>/delete` | usunięcie mieszkania (z potwierdzeniem nazwą) | admin |
| GET/POST | `/flats/<id>/invites` | lista, tworzenie zaproszeń | admin |
| POST | `/flats/<id>/invites/<iid>/revoke` | unieważnienie | admin |
| GET/POST | `/join/<token>` | podgląd i wysłanie prośby o dołączenie | zalogowany |

### tasks
| Metoda | URL | Opis | Rola |
| --- | --- | --- | --- |
| GET | `/flats/<id>/tasks` | lista z filtrami (moje / pula / wszystkie / wykonane) | członek |
| GET/POST | `/flats/<id>/tasks/new` | nowe zadanie (FR-6, FR-7) | członek; wybór osoby innej niż siebie = admin |
| GET/POST | `/flats/<id>/tasks/<tid>/edit` | edycja | autor lub admin |
| POST | `/flats/<id>/tasks/<tid>/delete` | usunięcie | autor lub admin |
| POST | `/flats/<id>/tasks/<tid>/claim` | „Biorę” z puli (FR-8) | członek; tylko gdy `assignee_id IS NULL` |
| POST | `/flats/<id>/tasks/<tid>/assign` | przypisanie osoby | admin |
| POST | `/flats/<id>/tasks/<tid>/done` | oznaczenie wykonania + punkty + kolejne wystąpienie | przypisany lub admin |
| GET/POST | `/flats/<id>/task-types` | typy zadań mieszkania | admin |

Zadanie pobieramy zawsze zapytaniem `Task.query.filter_by(id=tid, flat_id=id).first_or_404()`, nigdy samym `get(tid)` (T-01).

### calendar
| Metoda | URL | Opis |
| --- | --- | --- |
| GET | `/flats/<id>/calendar?month=YYYY-MM` | siatka miesiąca renderowana po stronie serwera (FR-9); kolor = kolor użytkownika |

Kalendarz robimy bez zewnętrznej biblioteki JS, żeby utrzymać prosty CSP. Siatkę generuje moduł `calendar` z biblioteki standardowej.

---

## 5. Warstwa bezpieczeństwa (mapowanie SR / T → implementacja)

| Kontrola | Implementacja | SR / T |
| --- | --- | --- |
| Hash haseł | `generate_password_hash` / `check_password_hash`, min. 12 znaków, max 128 | SR-1, T-04 |
| Limit logowań | `@limiter.limit("5/minute;20/hour", methods=["POST"])` na `/login`; ten sam komunikat dla złego e-maila i hasła; stały czas (sprawdzanie hasha również dla nieistniejącego użytkownika) | SR-2, T-03 |
| Sesja | `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SECURE=True` (prod), `SESSION_COOKIE_SAMESITE="Lax"`, `REMEMBER_COOKIE_*` analogicznie, `PERMANENT_SESSION_LIFETIME`; po zalogowaniu `session.clear()` + `login_user` (ochrona przed fixation), po wylogowaniu `session.clear()` | SR-3, T-07 |
| Członkostwo | dekorator `@flat_member_required` → ładuje `Membership(user, flat, status=active)` do `g.membership`, w przeciwnym razie `abort(404)` | SR-4, T-01 |
| Rola admina | dekorator `@flat_admin_required` (sprawdza `g.membership.role == "admin"`) → `abort(404)` | SR-4, T-02 |
| CSRF | `CSRFProtect(app)` globalnie, `{{ form.csrf_token }}` / `csrf_token()` w każdym formularzu, także w przyciskach „Biorę”, „Usuń” | SR-5, T-06 |
| XSS | autoescape Jinja2; **zakaz `|safe`** na danych użytkownika (sprawdzane w code review / grep w CI); walidatory `Length`, `Regexp` | SR-6, T-05 |
| CSP i nagłówki | `after_request`: `Content-Security-Policy: default-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin`, `X-Frame-Options: DENY`, HSTS w prod | SR-6, T-05 |
| SQLi | wyłącznie ORM, bez `text()` z f-stringami; Bandit w CI | SR-7, T-09 |
| Zaproszenia | `token_urlsafe(32)`, w bazie SHA-256, `expires_at` = +7 dni, `revoked`, porównanie przez `hmac.compare_digest`; użycie zaproszenia tylko tworzy `pending` | SR-8, T-08 |
| Awatary | `MAX_CONTENT_LENGTH = 2 MB`; Pillow `Image.open` + `verify()`, format ∈ {PNG, JPEG} (po zawartości, nie rozszerzeniu); ponowny zapis (`image.save`) usuwa metadane i ewentualny payload; nazwa `secrets.token_hex(16) + ext`; usunięcie starego pliku | SR-9, T-10 |
| Sekrety | `SECRET_KEY` z `.env` (python-dotenv); aplikacja **nie startuje**, gdy w prod brakuje klucza; `DEBUG=False` domyślnie; `.env.example` w repo; gitleaks w CI | SR-10, T-11 |
| Zależności | przypięte wersje, pip-audit w CI, Dependabot co tydzień | T-12 |
| Baza | `instance/flatmate.db` poza `static/` | T-04 |
| Strony błędów | własne 400/404/413/429/500 bez stack trace'ów | T-11 |

---

## 6. Szablony i UI

- `base.html`: Bootstrap 5 (lokalnie w `static/vendor`), navbar z wyborem mieszkania, komunikaty `flash`.
- Pulpit mieszkania: „Moje zadania”, „Pula do wzięcia”, ranking punktów członków.
- Przyciski akcji („Biorę”, „Wykonane”, „Usuń”) to małe formularze POST z CSRF, bez linków GET.
- Potwierdzenia akcji destrukcyjnych przez osobną stronę lub modal Bootstrapa (JS z pliku, nie inline).
- Kolor użytkownika jako znacznik przy zadaniach i w kalendarzu. Wartość przechodzi walidację regexem, zanim trafi do atrybutu `style`.

---

## 7. Testy (pytest)

`conftest.py`: fabryka aplikacji z `TestConfig` (SQLite w pamięci, `WTF_CSRF_ENABLED=False` dla większości testów i osobny zestaw z włączonym CSRF), fixture'y `client`, `user_a`, `user_b`, `flat_a` (admin A), `flat_b` (admin B), helper `login(client, user)`.

Kluczowe scenariusze:

1. **Auth:** rejestracja, odrzucenie hasła < 12 znaków, duplikat e-maila, ogólny komunikat błędu, 429 po przekroczeniu limitu, flagi ciasteczka.
2. **IDOR (T-01):** użytkownik B próbuje GET/POST na każdą trasę `/flats/<flat_a>/…` → 404; B próbuje operować zadaniem z mieszkania A, podstawiając jego ID pod własne mieszkanie → 404.
3. **Eskalacja (T-02):** członek (nie admin) wysyła POST na każdą trasę admina → 404, stan bazy bez zmian. Najlepiej jeden test sparametryzowany listą tras admina.
4. **CSRF (T-06):** z włączonym CSRF POST bez tokenu → 400.
5. **Zaproszenia (T-08):** wygasły token, unieważniony token i błędny token → brak dołączenia; poprawny token → `pending`, a dopiero akceptacja admina → `active`; ponowne użycie przez członka nie tworzy duplikatu.
6. **XSS (T-05):** zadanie z tytułem `<script>alert(1)</script>` jest w HTML escapowane; nagłówek CSP jest obecny.
7. **Awatary (T-10):** PNG/JPEG przechodzą; SVG, HTML z rozszerzeniem `.png` i plik > 2 MB są odrzucane (413); nazwa pliku jest losowa.
8. **Rotacja (FR-7):** po wykonaniu zadania cyklicznego powstaje kolejne z właściwym terminem i osobą; pominięcie osoby, która opuściła mieszkanie; pula → `assignee_id` NULL.
9. **Członkowie:** przekazanie roli zostawia jednego admina; admin nie może opuścić mieszkania bez przekazania roli; usunięcie mieszkania kasuje zadania i zaproszenia.

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
| zap (DAST) | po merge do `main`: uruchomienie aplikacji w kontenerze/tle + `zaproxy/action-baseline` | raport (artefakt), bez blokady |

`.github/dependabot.yml`: ekosystemy `pip` i `github-actions`, co tydzień.

Ochrona gałęzi `main` w ustawieniach repo: wymagane zielone checki i PR (ustawia właściciel repozytorium ręcznie).

Opcjonalnie dochodzi `Dockerfile` (python-slim, gunicorn, użytkownik bez roota), przydatny dla ZAP i wdrożenia.

---

## 9. Etapy realizacji

Każdy etap to osobna gałąź i PR przechodzący przez CI.

| Etap | Zakres | Rezultat |
| --- | --- | --- |
| **1** (zrobione) | README, REQUIREMENTS, diagramy | zrobione |
| **2. Szkielet + CI** | struktura katalogów, `create_app`, config z `.env`, rozszerzenia, `base.html`, strony błędów, nagłówki bezpieczeństwa, `requirements*.txt`, workflow CI (testy, Bandit, pip-audit, gitleaks), Dependabot | pusta aplikacja startuje, CI zielone |
| **3. Modele** | wszystkie modele z sekcji 3, inicjalizacja bazy (`flask init-db`), seed typów domyślnych | tabele w SQLite, testy modeli |
| **4. Auth + profil** | rejestracja, logowanie z limiterem, wylogowanie, profil, zmiana hasła, awatary | FR-1, FR-2; SR-1, 2, 3, 9 |
| **5. Mieszkania i członkowie** | tworzenie, pulpit, dekoratory dostępu, zaproszenia, prośby, akceptacja, usuwanie, przekazanie roli, opuszczenie, usunięcie mieszkania | FR-3, 4, 5; SR-4, 8; testy IDOR i eskalacji |
| **6. Zadania** | CRUD zadań jednorazowych, typy, pula, „Biorę”, przypisanie, wykonanie, punkty | FR-6, FR-8 |
| **7. Zadania cykliczne** | `services/rotation.py`, tryby fixed / rotation / pool, rotation_member | FR-7, testy rotacji |
| **8. Kalendarz** | widok miesiąca, nawigacja, kolory użytkowników | FR-9 |
| **9. Utwardzenie i DAST** | przegląd `|safe`, CSP bez wyjątków, ZAP baseline, poprawki z raportu, pokrycie ≥ 80% | raport ZAP, raport Bandit |
| **10. Dokumentacja końcowa** | instrukcja uruchomienia w README, zrzuty ekranu, opis wyników skanów, aktualizacja modelu zagrożeń (status kontroli) | gotowe do oddania |

### Propozycja podziału pracy (do ustalenia w zespole)
- **Osoba A:** etapy 2, 4, 9 (szkielet, CI, auth, utwardzenie),
- **Osoba B:** etapy 3, 6, 7, 8 (modele, zadania, rotacja, kalendarz),
- **Wspólnie:** etap 5 (najbardziej krytyczny dla bezpieczeństwa, review krzyżowe) i 10.

---

## 10. Uruchomienie lokalne (docelowo w README)

```bash
python -m venv .venv
source .venv/Scripts/activate      # Windows Git Bash; Linux/macOS: .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env               # uzupełnić SECRET_KEY: python -c "import secrets; print(secrets.token_hex(32))"
flask --app run init-db
flask --app run run
pytest
```

---

## 11. Definition of Done dla każdego PR

- [ ] CI zielone (testy, Bandit, pip-audit, gitleaks),
- [ ] nowe trasy mieszkania mają `@flat_member_required` / `@flat_admin_required` i test dostępu z obcego konta,
- [ ] zapytania o zasoby mieszkania filtrowane po `flat_id`,
- [ ] formularze zmieniające dane mają CSRF i używają POST,
- [ ] brak `|safe` na danych użytkownika, brak inline JS,
- [ ] brak sekretów w kodzie,
- [ ] review drugiej osoby z zespołu.
