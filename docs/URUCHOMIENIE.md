# Uruchomienie FlatMate od zera

Instrukcja dla komputera, na którym nie ma jeszcze niczego: ani narzędzi, ani repozytorium. Polecenia są dla Windowsa (PowerShell), różnice dla macOS i Linuksa opisują krótkie uwagi. Aplikacja działa w Dockerze, więc nie trzeba instalować Pythona ani PostgreSQL.

| Etap | Co robisz | Czas |
| --- | --- | --- |
| 1 | Instalujesz Git i Docker Desktop | 15–30 min |
| 2 | Pobierasz repozytorium | 1 min |
| 3 | Tworzysz plik `.env` z hasłami | 5 min |
| 4 | Uruchamiasz aplikację | 3–5 min za pierwszym razem |
| 5 | Tworzysz konta demo i logujesz się | 2 min |
| 6 | Zatrzymujesz i uruchamiasz ponownie | – |

---

## Etap 1. Instalacja narzędzi

Potrzebujesz dwóch programów:

- **Git** pobiera repozytorium z GitHuba.
- **Docker Desktop** uruchamia aplikację i bazę danych w kontenerach. Zawiera `docker compose`.

### 1.1. Otwórz PowerShell

Kliknij **Start**, wpisz `PowerShell` i otwórz **Windows PowerShell**. Wszystkie polecenia z tej instrukcji wpisujesz w tym oknie i zatwierdzasz klawiszem Enter.

### 1.2. Zainstaluj Git

```powershell
winget install --id Git.Git -e
```

Bez `winget`: pobierz instalator z https://git-scm.com/download/win i klikaj **Next** z domyślnymi ustawieniami.

### 1.3. Zainstaluj Docker Desktop

```powershell
winget install --id Docker.DockerDesktop -e
```

Bez `winget`: pobierz instalator z https://www.docker.com/products/docker-desktop/ i zostaw zaznaczoną opcję **Use WSL 2 instead of Hyper-V**.

Po instalacji **uruchom ponownie komputer**. Docker na Windowsie działa na WSL 2, który włącza się dopiero po restarcie.

### 1.4. Uruchom Docker Desktop

1. Kliknij **Start**, wpisz `Docker Desktop` i otwórz program.
2. Zaakceptuj warunki licencji. Logowanie do konta Dockera możesz pominąć (**Skip**).
3. Poczekaj, aż w lewym dolnym rogu okna pojawi się zielone **Engine running**.

Jeśli Docker poprosi o aktualizację WSL, otwórz PowerShell jako administrator (prawy przycisk na PowerShell → **Uruchom jako administrator**) i wpisz `wsl --update`.

### 1.5. Sprawdź instalację

Zamknij PowerShell i otwórz go od nowa, żeby widział nowe programy. Potem wpisz:

```powershell
git --version
docker --version
docker compose version
```

Każde polecenie powinno wypisać numer wersji. Jeśli któreś zwraca błąd, wróć do odpowiedniego kroku.

> **macOS:** Docker Desktop z https://www.docker.com/products/docker-desktop/, Git przez `xcode-select --install`. Polecenia wpisujesz w aplikacji Terminal.
> **Linux:** Docker Engine z wtyczką Compose (https://docs.docker.com/engine/install/) i `git` z menedżera pakietów, np. `sudo apt install git`.

---

## Etap 2. Pobranie repozytorium

```powershell
cd $HOME\Documents
git clone https://github.com/Badym/FlatMate.git
cd FlatMate
git switch develop
```

Repozytorium trafi do folderu `Dokumenty\FlatMate`. Gałąź `main` zawiera wersje oddane po kolejnych etapach, a `develop` bieżącą wersję zespołu.

Sprawdź, czy na tej gałęzi jest już logowanie i konta demo:

```powershell
Test-Path backend\cli.py
```

Jeśli wynik to `False`, ta gałąź ma jeszcze tylko szkielet aplikacji. Przełącz się wtedy na gałąź z najnowszym kodem (listę pokazuje `git branch -r`), na przykład:

```powershell
git switch feat/etap-3-fundament
```

Wszystkie dalsze polecenia wpisujesz w folderze `FlatMate`. Jeśli zamkniesz okno, po ponownym otwarciu PowerShella wpisz najpierw `cd $HOME\Documents\FlatMate`.

---

## Etap 3. Konfiguracja: plik `.env`

Aplikacja czyta hasła i ustawienia z pliku `.env`. Ten plik nie trafia do repozytorium, więc każdy tworzy własny na podstawie wzoru `.env.example`.

### 3.1. Skopiuj wzór

```powershell
Copy-Item .env.example .env
```

### 3.2. Wygeneruj dwa losowe sekrety

Polecenie korzysta z Pythona w kontenerze Dockera, więc nie musisz instalować Pythona. Pierwsze uruchomienie pobiera obraz, co trwa chwilę.

Klucz aplikacji (`SECRET_KEY`, 64 znaki):

```powershell
docker run --rm python:3.13-slim python -c "import secrets; print(secrets.token_hex(32))"
```

Hasło do bazy (`POSTGRES_PASSWORD`, 32 znaki):

```powershell
docker run --rm python:3.13-slim python -c "import secrets; print(secrets.token_hex(16))"
```

Każde polecenie wypisuje jeden ciąg liter i cyfr. Skopiuj go: zaznacz myszą i naciśnij Enter albo Ctrl+C.

### 3.3. Uzupełnij `.env`

```powershell
notepad .env
```

W Notatniku zmień te linie (wartości wpisuj bez cudzysłowów i bez spacji wokół `=`):

| Linia | Co wpisać |
| --- | --- |
| `SECRET_KEY=` | pierwszy wygenerowany ciąg (64 znaki) |
| `POSTGRES_PASSWORD=` | drugi wygenerowany ciąg (32 znaki) |
| `DATABASE_URL=` | w środku adresu zamień `HASLO_Z_POSTGRES_PASSWORD` na ten sam drugi ciąg; potrzebne tylko przy pracy bez Dockera |
| `DEMO_PASSWORD=` | wymyślone przez ciebie hasło do kont demo, **co najmniej 12 znaków** |
| `APP_ENV=` | zostaw `development` |

Zapisz plik (Ctrl+S) i zamknij Notatnik.

Uwagi:

- `APP_ENV=production` zakłada HTTPS za reverse proxy. Na własnym komputerze zostaw `development`.
- Hasło do bazy ustaw raz, przed pierwszym uruchomieniem. Baza zapamiętuje je przy tworzeniu, a późniejsza zmiana w `.env` jej nie zmienia (zobacz „Najczęstsze problemy”).

---

## Etap 4. Uruchomienie aplikacji

Upewnij się, że Docker Desktop działa (**Engine running**), i wpisz:

```powershell
docker compose up --build
```

Za pierwszym razem Docker pobiera obrazy i buduje aplikację, co zajmuje kilka minut. Potem kontener sam przygotowuje bazę (migracje) i uruchamia serwer. Aplikacja jest gotowa, gdy w logach pojawi się linia podobna do tej:

```text
web-1  | [2026-10-28 18:30:00 +0000] [1] [INFO] Listening at: http://0.0.0.0:8000 (1)
```

**Zostaw to okno otwarte**, bo zamknięcie go zatrzymuje aplikację.

Otwórz w przeglądarce **http://localhost:8000**. Zobaczysz stronę główną FlatMate. Pod adresem http://localhost:8000/health aplikacja zgłasza swój stan.

---

## Etap 5. Konta demo i logowanie

### 5.1. Utwórz dane demonstracyjne

Otwórz **drugie** okno PowerShella (pierwsze jest zajęte przez serwer) i wpisz:

```powershell
cd $HOME\Documents\FlatMate
docker compose exec web flask --app wsgi seed-demo
```

Polecenie tworzy mieszkanie „Mickiewicza 12/4 (demo)”, kilka zadań i trzy konta:

| E-mail | Rola w mieszkaniu demo |
| --- | --- |
| `ola@flatmate.example` | admin |
| `kuba@flatmate.example` | członek |
| `marta@flatmate.example` | członek |

Hasło do wszystkich trzech kont to wartość `DEMO_PASSWORD` z twojego pliku `.env`.

### 5.2. Zaloguj się

1. Na stronie http://localhost:8000 kliknij **Zaloguj się** w prawym górnym rogu.
2. W polu **Adres e-mail** wpisz `ola@flatmate.example`.
3. W polu **Hasło** wpisz wartość `DEMO_PASSWORD` z `.env`.
4. Kliknij **Zaloguj się**.

Po zalogowaniu zobaczysz stronę **Moje mieszkania** z mieszkaniem demo.

### 5.3. Co możesz teraz zrobić

- **Profil:** kliknij swój awatar z nazwą w prawym górnym rogu i wybierz **Profil**. Tam zmienisz nazwę, kolor, zdjęcie (PNG lub JPEG, do 2 MB) i hasło.
- **Wylogowanie:** w tym samym menu wybierz **Wyloguj się**.
- **Własne konto:** po wylogowaniu kliknij **Załóż konto** i wypełnij formularz: nazwę, e-mail i dwa razy hasło (co najmniej 12 znaków).

Na tym etapie projektu działają konta, profil i lista mieszkań. Tworzenie mieszkań, zaproszenia, zadania i kalendarz dochodzą w kolejnych etapach.

---

## Etap 6. Zatrzymanie i ponowne uruchomienie

| Chcesz | Polecenie |
| --- | --- |
| zatrzymać aplikację | w oknie z serwerem naciśnij **Ctrl+C** albo w drugim oknie wpisz `docker compose down` |
| uruchomić ją ponownie | `docker compose up` |
| uruchomić w tle, bez zajmowania okna | `docker compose up -d`, a logi zobaczysz przez `docker compose logs -f web` |
| pobrać najnowszy kod i uruchomić | `git pull`, potem `docker compose up --build` |
| odtworzyć dane demo od nowa | `docker compose exec web flask --app wsgi seed-demo --reset` |
| usunąć **wszystkie** dane (bazę i zdjęcia) | `docker compose down -v` |

Konta, mieszkania i zdjęcia przetrwają `docker compose down` i restart komputera, bo Docker trzyma je w wolumenach. Kasuje je dopiero `docker compose down -v`.

---

## Dodatkowo: tryb deweloperski i testy

Tryb z automatycznym przeładowaniem kodu po każdej zmianie pliku. Pod http://localhost:8000/_ui/ jest wtedy biblioteka komponentów interfejsu.

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Testy na osobnej, tymczasowej bazie PostgreSQL, tak jak w CI:

```powershell
docker compose --profile test run --rm --build tests
```

Praca bez kontenera aplikacji (wymaga [uv](https://docs.astral.sh/uv/): `winget install --id astral-sh.uv -e`) jest opisana w sekcji „Uruchomienie” w [README](../README.md).

---

## Najczęstsze problemy

| Objaw | Przyczyna i rozwiązanie |
| --- | --- |
| `error during connect` albo `Cannot connect to the Docker daemon` | Docker Desktop nie działa. Uruchom go i poczekaj na **Engine running**. |
| `Ustaw SECRET_KEY w pliku .env` albo `Ustaw POSTGRES_PASSWORD w pliku .env` | Brak pliku `.env` albo pusta wartość. Plik musi się nazywać dokładnie `.env`: sprawdź poleceniem `Get-ChildItem -Force .env*`, czy Notatnik nie zapisał go jako `.env.txt`. |
| `port is already allocated` albo `Bind for 127.0.0.1:8000 failed` | Port zajęty przez inny program. W `.env` zmień `WEB_PORT=8000` na np. `8001` (a przy błędzie z portem 5432 `POSTGRES_PORT=5432` na `5433`) i otwórz http://localhost:8001. |
| `password authentication failed for user "flatmate"` | `POSTGRES_PASSWORD` zmieniono po pierwszym uruchomieniu. Przywróć poprzednie hasło albo usuń bazę poleceniem `docker compose down -v` (traci dane) i uruchom aplikację ponownie. |
| `Ustaw DEMO_PASSWORD (co najmniej 12 znaków)` | Uzupełnij `DEMO_PASSWORD` w `.env`, wpisz `docker compose up -d`, żeby kontener wczytał nową wartość, i powtórz `seed-demo`. |
| `Dane demo już istnieją` | Konta demo już są, możesz się logować. Żeby utworzyć je od nowa, dodaj `--reset`. |
| `service "web" is not running` przy `seed-demo` | Aplikacja nie działa. Uruchom ją (etap 4) i dopiero potem `seed-demo`. |
| Strona http://localhost:8000 się nie otwiera | Sprawdź, czy w oknie z serwerem jest linia `Listening at`. Spróbuj adresu http://127.0.0.1:8000. |
| „Nieprawidłowy e-mail lub hasło” przy koncie demo | Hasło to wartość `DEMO_PASSWORD` z `.env` z chwili uruchomienia `seed-demo`. Po zmianie hasła w `.env` wpisz `docker compose up -d`, a potem `seed-demo --reset`. Po 10 nieudanych próbach konto blokuje się na 15 minut. |
