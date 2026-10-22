# FlatMate – menedżer mieszkania współdzielonego

Aplikacja webowa do podziału obowiązków w mieszkaniu współdzielonym: zadania domowe jednorazowe i cykliczne z rotacją osób, punkty za wykonane zadania i kalendarz. Każde mieszkanie to osobna, odizolowana grupa.

Projekt realizowany w ramach przedmiotu **Projektowanie, Bezpieczeństwo i Operacje (DevSecOps)**, Politechnika Śląska.

## Członkowie zespołu

| Imię i nazwisko | 
| --- | 
| Patryk Czakon | 
| Błażej Sztefka | 

## Wybrany język i technologie

- **Backend:** Python + Flask
- **Frontend:** HTML, CSS, Bootstrap 5
- **Baza danych:** SQLite
- **Biblioteki:** Flask-SQLAlchemy, Flask-Login, Flask-WTF, Flask-Limiter, Pillow

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