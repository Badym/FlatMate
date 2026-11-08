# FlatMate – menedżer mieszkania współdzielonego

Aplikacja webowa do podziału obowiązków w mieszkaniu współdzielonym: zadania domowe jednorazowe i cykliczne z rotacją osób, pula zadań do wzięcia i wspólny kalendarz. Każde mieszkanie to osobna, odizolowana grupa.

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
- tworzenie, edycja i usuwanie zadań jednorazowych z typem, terminem i przypisaniem; przegląd z filtrami: moje, pula, wszystkie, zaległe i wykonane,
- zadania jednorazowe i cykliczne z typami, terminami; rotacja, stała osoba lub pula „do wzięcia”,
- kalendarz zadań mieszkania.

## Uruchomienie

Wymagania: Windows 10/11, Git, [Docker Desktop](https://docs.docker.com/get-docker/) z uruchomionym Docker Engine oraz PowerShell. Python, PostgreSQL ani `uv` nie są potrzebne do uruchomienia aplikacji.

Jeśli Git i Docker Desktop nie są zainstalowane, możesz zainstalować je przez `winget`:

```powershell
winget install --id Git.Git -e
winget install --id Docker.DockerDesktop -e
```

Po instalacji uruchom Docker Desktop i poczekaj, aż Docker Engine będzie działał.

Sklonuj repozytorium, przejdź do jego katalogu i uruchom aplikację:

```powershell
git clone https://github.com/Badym/FlatMate.git
cd FlatMate
git switch develop
.\start.ps1
```

Przy pierwszym uruchomieniu skrypt tworzy z `.env.example` lokalny plik `.env` z losowym kluczem aplikacji oraz hasłami bazy i kont demo (plik jest ignorowany przez Git). Przy kolejnych uruchomieniach zachowuje te hasła i synchronizuje hasło roli PostgreSQL z `.env`, bez usuwania danych. Migracje bazy wykonują się automatycznie. Domyślny adres aplikacji to http://localhost:8000; jeśli zmieniono `WEB_PORT`, użyj ustawionego portu.

### Sprawdzenie stanu

- `GET /health` — liveness aplikacji, publiczny i niezależny od bazy danych. Przykład:

  ```powershell
  Invoke-RestMethod http://localhost:8000/health
  ```

  Odpowiedź HTTP 200:

  ```json
  {"status": "ok"}
  ```

- `GET /ready` — gotowość aplikacji do obsługi żądań, w tym dostępność bazy. Przykład:

  ```powershell
  Invoke-RestMethod http://localhost:8000/ready
  ```

  Przy działającej bazie zwraca HTTP 200 i `{"status":"ok","database":"ok"}`. Jeśli baza jest niedostępna, zwraca HTTP 503 i `{"status":"degraded","database":"error"}`.

### Dane demo i tryb deweloperski

Dane demonstracyjne można utworzyć poleceniem `docker compose exec web flask --app wsgi seed-demo`. Wygenerowane hasło znajduje się w `.env` w polu `DEMO_PASSWORD`; zaloguj się np. jako `ola@flatmate.example`. Polecenie seedowania jest wyłączone w środowisku produkcyjnym.

Tryb deweloperski z automatycznym przeładowaniem kodu i biblioteką komponentów pod `/_ui/`:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Porty można zmienić w `.env` (`WEB_PORT`, `POSTGRES_PORT`). Szczegółowa instrukcja instalacji Dockera i rozwiązywania problemów: [docs/URUCHOMIENIE.md](docs/URUCHOMIENIE.md).

Testy wymagają `uv` i są uruchamiane w kontenerze na PostgreSQL:

```powershell
docker compose --profile test run --rm --build tests
```

Szczegóły architektury i etapy prac: [docs/PLAN_IMPLEMENTACJI.md](docs/PLAN_IMPLEMENTACJI.md). Model danych: [docs/diagram_bazy_danych.md](docs/diagram_bazy_danych.md).