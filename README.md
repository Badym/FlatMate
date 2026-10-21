# FlatMate – menedżer mieszkania współdzielonego

Aplikacja webowa do podziału obowiązków w mieszkaniu współdzielonym: zadania domowe jednorazowe i cykliczne z rotacją osób, punkty za wykonane zadania i kalendarz. Każde mieszkanie to osobna, odizolowana grupa.

Projekt realizowany w ramach przedmiotu **Projektowanie, Bezpieczeństwo i Operacje (DevSecOps)**, Wydział Matematyki Stosowanej, Politechnika Śląska.

## Członkowie zespołu

| Imię i nazwisko | Rola w projekcie |
| --- | --- |
| [Imię Nazwisko] | [np. backend, bezpieczeństwo] |
| [Imię Nazwisko] | [np. frontend, testy, dokumentacja] |

## Wybrany język i technologie

- **Backend:** Python + Flask
- **Frontend:** HTML, CSS, Bootstrap 5
- **Baza danych:** SQLite
- **Biblioteki:** Flask-SQLAlchemy, Flask-Login, Flask-WTF

## Krótki opis

**Jaki problem rozwiązuje?** W mieszkaniach współdzielonych obowiązki domowe są dzielone nierówno, ustalenia giną w czatach, a nikt nie pamięta, czyja jest kolej na sprzątanie łazienki ani kto ostatnio kupował środki czystości.

**Kto będzie z niej korzystał?** Osoby mieszkające razem: studenci w akademikach i wynajmowanych mieszkaniach, współlokatorzy, pary i rodziny.

**Dlaczego jest potrzebna?** Daje jedno wspólne miejsce z jasnym podziałem obowiązków. Zadania cykliczne same przechodzą na kolejną osobę, a punkty pokazują, kto ile robi. Każde mieszkanie widzi wyłącznie własne dane.

**Jaką podstawową czynność umożliwia?** Zalogowany użytkownik tworzy mieszkanie lub do niego dołącza, a następnie dodaje, przypisuje, przejmuje i oznacza jako wykonane zadania domowe swojego mieszkania.

## Główne funkcje

- rejestracja, logowanie i profil (kolor, awatar),
- mieszkania z rolą admina; dołączanie przez link zaproszenia z akceptacją admina,
- zadania jednorazowe i cykliczne z typami, terminami i punktami; rotacja, stała osoba lub pula „do wzięcia”,
- kalendarz zadań mieszkania.

Planowane później (poza zakresem projektu): wydatki, lista zakupów, tablica ogłoszeń, rezerwacje wspólnych zasobów.

## Dokumentacja

- [REQUIREMENTS.md](REQUIREMENTS.md) – cel, użytkownicy, wymagania funkcjonalne i bezpieczeństwa, model zagrożeń
- [docs/diagram.pdf](docs/diagram.pdf) – diagram działania aplikacji (3 strony):
  - [A. Architektura i obsługa żądania](docs/diagram_A_architektura.png)
  - [B. Przepływ działania z perspektywy użytkownika](docs/diagram_B_przeplyw.png)
  - [C. Proces wytwarzania (DevSecOps)](docs/diagram_C_devsecops.png)
- [docs/diagram_bazy_danych.png](docs/diagram_bazy_danych.png) – diagram bazy danych (tabele i relacje między nimi)

## Status

Etap 1: planowanie, wymagania i model zagrożeń.
