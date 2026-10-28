# FlatMate – menedżer mieszkania współdzielonego

Aplikacja webowa do podziału obowiązków w mieszkaniu współdzielonym: zadania domowe jednorazowe i cykliczne z rotacją osób, punkty za wykonane zadania i kalendarz. Każde mieszkanie to osobna, odizolowana grupa.

Projekt realizowany w ramach przedmiotu **Projektowanie, Bezpieczeństwo i Operacje (DevSecOps)**, Politechnika Śląska.

## Członkowie zespołu

| Imię i nazwisko | 
| --- | 
| Patryk Czakon | 
| Błażej Sztefka | 

## Wybrany język i technologie

- **Backend:** katalog `backend/` – Python 3.13 + Flask, architektura warstwowa MVC (kontrolery, serwisy, repozytoria, modele) ([zasady](backend/README.md))
- **Frontend:** katalog `frontend/` – szablony Jinja2 podzielone na layouty, komponenty i strony, Bootstrap 5.3, Bootstrap Icons, własny motyw z trybem jasnym i ciemnym ([zasady](frontend/README.md))
- **Baza danych:** PostgreSQL 17 w Dockerze, migracje Alembic (Flask-Migrate)
- **Biblioteki:** Flask-SQLAlchemy, Flask-Login, Flask-WTF, Flask-Limiter, Pillow
- **Narzędzia:** uv (zależności), Docker Compose, GitHub Actions (pytest, Bandit, pip-audit, gitleaks)

## Krótki opis

**Jaki problem rozwiązuje?** W mieszkaniach współdzielonych obowiązki domowe są dzielone nierówno, ustalenia giną w czatach, a nikt nie pamięta, czyja jest kolej na sprzątanie łazienki ani kto ostatnio kupował środki czystości.

**Kto będzie z niej korzystał?** Osoby mieszkające razem: studenci w akademikach i wynajmowanych mieszkaniach, współlokatorzy, pary i rodziny.

**Dlaczego jest potrzebna?** Daje jedno wspólne miejsce z jasnym podziałem obowiązków. Zadania cykliczne same przechodzą na kolejną osobę. Każde mieszkanie widzi wyłącznie własne dane.

**Jaką podstawową czynność umożliwia?** Zalogowany użytkownik tworzy mieszkanie lub do niego dołącza, a następnie dodaje, przypisuje, przejmuje i oznacza jako wykonane zadania domowe swojego mieszkania.

## Główne funkcje

- rejestracja, logowanie i edycja profilu,
- mieszkania z rolą admina; dołączanie przez link zaproszenia z akceptacją admina,
- zadania jednorazowe i cykliczne z typami, terminami; rotacja, stała osoba lub pula „do wzięcia”,
- kalendarz zadań mieszkania.

## Uruchomienie

Wymagania: [Docker](https://docs.docker.com/get-docker/) z Docker Compose oraz [uv](https://docs.astral.sh/uv/) (do pracy poza kontenerami).

1. Skopiuj `.env.example` do `.env` i uzupełnij `SECRET_KEY` oraz `POSTGRES_PASSWORD`. Wartości wygenerujesz poleceniem `uv run python -c "import secrets; print(secrets.token_hex(32))"`.
2. Uruchom aplikację z bazą:

   ```bash
   docker compose up --build
   ```

   Aplikacja: http://localhost:8000. Przy starcie kontener wykonuje migracje bazy, a stan aplikacji widać pod `/health`.

3. Tryb deweloperski z automatycznym przeładowaniem kodu:

   ```bash
   docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
   ```

   W tym trybie pod http://localhost:8000/_ui/ jest biblioteka komponentów interfejsu.

4. Dane demonstracyjne: 3 konta `@flatmate.example`, mieszkanie i zadania. Hasło do kont to wartość `DEMO_PASSWORD` z `.env`:

   ```bash
   docker compose exec web flask --app wsgi seed-demo           # w działającym kontenerze
   uv run flask --app wsgi seed-demo --reset                    # poza Dockerem, od nowa
   ```

   W środowisku produkcyjnym polecenie odmawia działania.

5. Testy:

   ```bash
   docker compose --profile test run --rm tests   # na PostgreSQL, tak jak w CI
   docker compose up -d db-test && uv run pytest  # lokalnie, na tej samej bazie testowej PostgreSQL
   ```

6. Zmiana modeli wymaga migracji w tym samym PR-ze:

   ```bash
   uv run flask --app wsgi db migrate -m "opis zmiany"
   uv run flask --app wsgi db upgrade
   ```

Gdy porty 8000 lub 5432 są zajęte, zmień `WEB_PORT` i `POSTGRES_PORT` w `.env`.

Szczegóły architektury i etapy prac: [docs/PLAN_IMPLEMENTACJI.md](docs/PLAN_IMPLEMENTACJI.md). Model danych: [docs/diagram_bazy_danych.md](docs/diagram_bazy_danych.md).