# REQUIREMENTS – FlatMate

## 1. Cel aplikacji

FlatMate pozwala współlokatorom uczciwie dzielić obowiązki domowe. Użytkownik tworzy mieszkanie lub do niego dołącza, a następnie członkowie planują zadania jednorazowe i cykliczne, przejmują je i zbierają punkty za ich wykonanie. Dane każdego mieszkania widzą wyłącznie jego członkowie.

## 2. Użytkownicy i ich możliwości

| Użytkownik | Możliwości |
| --- | --- |
| Gość | rejestracja, logowanie |
| Członek mieszkania | tworzenie, przejmowanie i wykonywanie zadań, kalendarz, edycja własnego profilu i własnych zadań, opuszczenie mieszkania |
| Admin mieszkania | to co członek oraz zaproszenia, akceptacja nowych osób, usuwanie członków, przekazanie roli admina, usunięcie mieszkania |

## 3. Wymagania funkcjonalne

1. Rejestracja i logowanie użytkownika; funkcje mieszkań są dostępne tylko po zalogowaniu.
2. Edycja profilu: nazwa, kolor, awatar, hasło.
3. Utworzenie mieszkania; twórca zostaje jego adminem.
4. Dołączanie do mieszkania przez link zaproszenia, po akceptacji admina.
5. Zarządzanie członkami przez admina: usuwanie członków i przekazanie roli admina.
6. Tworzenie, edycja i usuwanie zadań jednorazowych z typem, terminem i punktami.
7. Zadania cykliczne z rotacją osób, stałą osobą lub pulą „do wzięcia”.
8. Przejmowanie zadań z puli i oznaczanie wykonania; wykonujący dostaje punkty.
9. Kalendarz zadań mieszkania.

## 4. Wymagania bezpieczeństwa

1. Hasła przechowywane jako hash z solą, minimum 8 znaków.
2. Limit nieudanych prób logowania i ogólny komunikat błędu.
3. Bezpieczna sesja: ciasteczko `HttpOnly`, `Secure`, `SameSite=Lax`.
4. Kontrola dostępu po stronie serwera: użytkownik widzi tylko swoje mieszkania, akcje admina wymagają roli admina.
5. Token CSRF w każdym formularzu zmieniającym dane.
6. Walidacja danych wejściowych i escapowanie treści w szablonach (ochrona przed XSS).
7. Dostęp do bazy tylko przez ORM (ochrona przed SQL injection).
8. Losowe, wygasające tokeny zaproszeń.
9. Kontrola przesyłanych awatarów: tylko PNG/JPEG, limit rozmiaru, losowa nazwa pliku.
10. Sekrety (`SECRET_KEY`) w pliku `.env` poza repozytorium, tryb debug wyłączony.

**Wrażliwe elementy:** hasła, sesje, `SECRET_KEY`, tokeny zaproszeń, dane mieszkań i adresy e-mail, plik bazy danych.

## 5. Model zagrożeń

Model obejmuje zagrożenia dla kont użytkowników, izolacji mieszkań, danych w bazie i samego serwera. Ryzyko oceniono jako połączenie prawdopodobieństwa i skutków.

| ID | Zagrożenie | Czego dotyczy | Możliwe konsekwencje | Ryzyko | Planowana kontrola / działanie |
| --- | --- | --- | --- | --- | --- |
| T-01 | **Dostęp do cudzego mieszkania (IDOR).** Atakujący zmienia ID mieszkania lub zadania w adresie URL, np. `/flats/5/tasks` na `/flats/6/tasks`. | dane mieszkań: członkowie, zadania, punkty | odczyt, zmiana lub usunięcie danych mieszkania, do którego atakujący nie należy | wysokie | dekorator sprawdzający członkostwo na każdej trasie mieszkania; każde zapytanie do bazy filtrowane po `flat_id`; odpowiedź 404 zamiast 403, żeby nie zdradzać istnienia mieszkania; testy z dwoma kontami |
| T-02 | **Eskalacja uprawnień.** Zwykły członek wysyła ręcznie żądanie przeznaczone dla admina, np. usunięcie członka albo przekazanie roli. | role, lista członków, ustawienia mieszkania | usunięcie współlokatorów, przejęcie roli admina, usunięcie całego mieszkania | wysokie | sprawdzanie roli po stronie serwera dla każdej akcji admina, a nie tylko ukrywanie przycisków w interfejsie; testy autoryzacji dla każdej trasy admina |
| T-03 | **Zgadywanie hasła (brute force, credential stuffing).** Automatyczne próby logowania z listą popularnych lub wyciekniętych haseł. | konta użytkowników | przejęcie konta i dostęp do wszystkich mieszkań ofiary | średnie | limit nieudanych prób logowania na adres IP (Flask-Limiter); ogólny komunikat „nieprawidłowy e-mail lub hasło”; minimalna długość hasła 8 znaków |
| T-04 | **Wyciek bazy i odczytanie haseł.** Atakujący zdobywa plik SQLite, np. przez błędną konfigurację serwera. | hasła i adresy e-mail | odzyskanie haseł i użycie ich w innych serwisach | średnie | hasła przechowywane tylko jako hash z solą (`werkzeug.security`); plik bazy poza katalogiem publicznym `static/` |
| T-05 | **Stored XSS.** Użytkownik wpisuje kod JavaScript w tytule lub opisie zadania albo w nazwie mieszkania. | przeglądarki pozostałych członków mieszkania | wykonanie skryptu u ofiary: działania w jej imieniu, podmiana treści, wyłudzenie danych | wysokie | automatyczne escapowanie w szablonach Jinja2; zakaz filtra `|safe` na danych użytkownika; walidacja długości i typu pól; nagłówek Content-Security-Policy |
| T-06 | **Cross-Site Request Forgery (CSRF).** Zalogowany admin odwiedza złośliwą stronę, która w tle wysyła formularz do aplikacji. | operacje zmieniające dane | np. usunięcie członka lub mieszkania bez wiedzy admina | średnie | token CSRF w każdym formularzu (Flask-WTF); zmiany danych tylko metodą POST; ciasteczko sesji z `SameSite=Lax` |
| T-07 | **Przejęcie sesji.** Kradzież ciasteczka sesji przez skrypt (XSS) lub nieszyfrowane połączenie. | sesja zalogowanego użytkownika | atakujący działa jako ofiara bez znajomości hasła | średnie | ciasteczko z flagami `HttpOnly` i `Secure`; HTTPS; odnowienie sesji po zalogowaniu i jej usunięcie przy wylogowaniu |
| T-08 | **Wyciek lub odgadnięcie linku zaproszenia.** Link trafia do niepowołanej osoby albo atakujący próbuje odgadnąć token. | dostęp do mieszkania | obca osoba dołącza do mieszkania i widzi jego dane | średnie | losowy token o długości 256 bitów (`secrets.token_urlsafe(32)`); ważność 7 dni; możliwość unieważnienia linku; dołączenie wymaga akceptacji admina |
| T-09 | **SQL injection.** Złośliwe dane w formularzu lub adresie URL zmieniają treść zapytania do bazy. | baza danych | odczyt, zmiana lub usunięcie wszystkich danych w bazie | niskie | dostęp do bazy wyłącznie przez ORM (Flask-SQLAlchemy) i zapytania parametryzowane; skanowanie kodu narzędziem Bandit |
| T-10 | **Złośliwy plik jako awatar.** Przesłanie pliku SVG z JavaScriptem, HTML udającego obrazek albo bardzo dużego pliku. | serwer, przeglądarki innych użytkowników | XSS, zapełnienie dysku serwera | średnie | akceptowane tylko PNG i JPEG, sprawdzane po zawartości pliku; limit 2 MB; losowa nazwa pliku; ponowne zapisanie obrazu przez bibliotekę Pillow |
| T-11 | **Wyciek `SECRET_KEY` lub uruchomienie w trybie debug.** Klucz trafia do publicznego repozytorium albo aplikacja działa z włączonym debuggerem. | sesje wszystkich użytkowników, serwer | podrabianie sesji dowolnego użytkownika; zdalne wykonanie kodu przez debugger Werkzeug | wysokie | sekrety w pliku `.env` dodanym do `.gitignore`; skanowanie repozytorium narzędziem gitleaks; `DEBUG=False` w konfiguracji produkcyjnej |
| T-12 | **Podatne biblioteki zewnętrzne.** Użyta wersja Flaska lub innej biblioteki ma znaną podatność (CVE). | cała aplikacja | wykorzystanie gotowego exploita | średnie | przypięte wersje w `requirements.txt`; regularne skanowanie zależności (pip-audit, Dependabot) i aktualizacje |
| T-13 | **Samodzielne zatwierdzenie prośby o dołączenie.** Osoba z linkiem wysyła bezpośrednio żądanie `POST /flats/6/requests/12/accept`, z pominięciem admina. | proces dołączania do mieszkania | wejście do mieszkania bez zgody admina | wysokie | akceptację prośby może wykonać tylko admin danego mieszkania (sprawdzenie roli i `flat_id`); prośba musi mieć status „oczekuje” |
| T-14 | **Manipulacja punktami.** Członek zmienia w formularzu wartość `points` na 9999 albo oznacza jako wykonane cudze zadanie, żeby zebrać punkty. | punkty i statystyki członków | nieuczciwe wyniki, konflikty między współlokatorami | niskie | walidacja zakresu punktów po stronie serwera (np. 0–100); punkty za zadanie cykliczne brane z szablonu, a nie z formularza; zapis, kto i kiedy oznaczył wykonanie |
| T-15 | **Mass assignment.** Atakujący dopisuje do formularza profilu lub rejestracji ukryte pole, np. `role=admin` albo `user_id=1`. | konta i role | nadanie sobie uprawnień admina lub zmiana cudzego konta | średnie | formularze WTForms z jawnie zdefiniowanymi polami; serwer nigdy nie przepisuje całego `request.form` do modelu; rola zmieniana tylko przez osobną akcję admina |
| T-16 | **Enumeracja kont.** Formularz rejestracji odpowiada „ten e-mail jest już zajęty”, a formularz logowania inaczej reaguje dla istniejących kont. | adresy e-mail użytkowników | zebranie listy kont do ataków na hasła i phishingu | niskie | jednakowe komunikaty i czas odpowiedzi przy logowaniu; limit żądań na formularzu rejestracji |
| T-17 | **Open redirect.** Link logowania z parametrem `?next=https://zla-strona.pl` przekierowuje po zalogowaniu na stronę atakującego, np. fałszywy formularz logowania. | użytkownicy klikający w linki | phishing i kradzież hasła | niskie | parametr `next` akceptowany tylko, jeśli jest ścieżką wewnątrz aplikacji (zaczyna się od `/`, bez domeny) |
| T-18 | **Przeciążenie aplikacji (DoS).** Utworzenie tysięcy zadań albo zadania cyklicznego „co 1 dzień” bez daty końca, generującego ogromną liczbę wystąpień. | serwer i baza danych | spowolnienie lub zatrzymanie aplikacji dla wszystkich mieszkań | średnie | generowanie wystąpień tylko na najbliższe 4 tygodnie; limit liczby zadań na mieszkanie; limit żądań na użytkownika |
| T-19 | **Clickjacking.** Złośliwa strona osadza aplikację w niewidocznej ramce (`iframe`) i nakłania admina do kliknięcia „Usuń członka”. | akcje admina | wykonanie akcji bez świadomości użytkownika | niskie | nagłówek `X-Frame-Options: DENY` i `frame-ancestors 'none'` w CSP |
| T-20 | **Ujawnienie informacji w błędach.** Komunikat błędu pokazuje stack trace, ścieżki plików lub zapytania SQL. | konfiguracja i kod serwera | ułatwienie ataku przez poznanie budowy aplikacji | niskie | własne strony błędów 404 i 500 bez szczegółów technicznych; szczegóły tylko w logach serwera |
| T-21 | **Brak śladu działań (zaprzeczenie).** Admin usuwa członka albo ktoś cofa wykonanie zadania, a potem twierdzi, że tego nie zrobił. | historia zmian w mieszkaniu | brak możliwości wyjaśnienia sporu lub incydentu | niskie | logowanie zdarzeń: logowania, zmiany ról, usunięcia członków, zmiany statusu zadań (kto, co, kiedy), bez haseł i tokenów |
| T-22 | **Mieszkanie bez admina.** Ostatni admin usuwa swoje konto lub opuszcza mieszkanie. | zarządzanie mieszkaniem | nikt nie może przyjmować nowych osób ani usuwać członków | niskie | admin nie może opuścić mieszkania bez przekazania roli; przy usuwaniu konta rola przechodzi na najdłużej należącego członka |
