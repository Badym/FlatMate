# Frontend FlatMate

Warstwa widoku (V w MVC). Strony renderuje Flask po stronie serwera z szablonów Jinja2, więc nie ma osobnego budowania ani npm. Backend (`backend/`) wskazuje ten katalog w `create_app()`.

## Struktura

```
frontend/
├── templates/
│   ├── layouts/        szkielety stron: base.html (wszystko), auth.html (logowanie/rejestracja)
│   ├── components/     komponenty wielokrotnego użytku – makra Jinja2, jeden komponent na plik
│   └── pages/          strony renderowane przez kontrolery, pogrupowane jak blueprinty
└── static/
    ├── css/
    │   ├── main.css    punkt wejścia: @import wszystkich plików w kolejności kaskady
    │   ├── base/       fonty, tokeny (kolory, cienie, tryb ciemny), style globalne, klasy pomocnicze, animacje
    │   ├── components/ style komponentów, nazwy jak w templates/components/
    │   ├── layouts/    style layoutów
    │   └── pages/      style pojedynczych stron
    ├── js/
    │   ├── theme-init.js  ustawia motyw w <head>, zanim strona się narysuje
    │   ├── main.js        punkt wejścia (moduł ES), uruchamia komponenty
    │   └── components/    zachowania komponentów, po jednym module
    ├── img/            favicon i grafiki
    └── vendor/         Bootstrap 5.3.8, Bootstrap Icons 1.13.2, Inter – bez zmian, bajt w bajt
```

## Komponenty

Komponent to makro Jinja2, czyli funkcja z parametrami, która zwraca HTML. Strona importuje go i wywołuje:

```jinja
{% from "components/avatar.html" import avatar %}
{% from "components/task_item.html" import task_item %}

{{ avatar(member, "sm") }}
{% for task in tasks %}{{ task_item(task) }}{% endfor %}
```

Treść do środka komponentu przekazuje się blokiem `call` (odpowiednik `children` w React):

```jinja
{% call empty_state("bi-cup-hot", "Pula jest pusta", "Opis…") %}
  <a class="btn btn-primary" href="…">Nowe zadanie</a>
{% endcall %}
```

Komponenty korzystające z kontekstu żądania (`config`, `request`, `current_user`, `current_year`) importuje się z `with context`, np. `navbar` i `footer` w `layouts/base.html`.

| Komponent | Plik | Styl | JS |
| --- | --- | --- | --- |
| `brand()` | components/brand.html | components/brand.css | – |
| `navbar()` | components/navbar.html | components/navbar.css | – |
| `footer()` | components/footer.html | components/footer.css | – |
| `theme_toggle()` | components/theme_toggle.html | components/theme-toggle.css | components/theme-toggle.js |
| `flash()`, `flash_messages()` | components/flash_messages.html | components/flash.css | components/flash-messages.js |
| `form_field()` | components/form_field.html | components/form-field.css | components/password-toggle.js, password-meter.js |
| `avatar()`, `avatar_stack()` | components/avatar.html | components/avatar.css | – |
| `badge()`, `status_badge()`, `mode_badge()` | components/badge.html | components/badge.css | – |
| `task_item()` | components/task_item.html | components/task-item.css | – |
| `stat_card()` | components/stat_card.html | components/card.css | – |
| `empty_state()` | components/empty_state.html | components/empty-state.css | – |
| `user_menu()` | components/user_menu.html | components/user-menu.css | Bootstrap dropdown |
| `color_picker()` | components/color_picker.html | components/color-picker.css | – |

`avatar` przyjmuje obiekt `User` albo słownik z tymi samymi polami (`display_name`, `initials`, `color_index`, `avatar_filename`), więc ten sam komponent obsługuje prawdziwe ekrany i makiety z `backend/demo_data.py`.

Filtr `plural` odmienia słowa po liczebniku: `{{ n }} {{ n|plural("zadanie", "zadania", "zadań") }}`.

Wszystkie komponenty na przykładowych danych są w bibliotece pod `/_ui/` (tylko tryb deweloperski).

## Zasady

- **Bez inline JS i CSS.** CSP pozwala tylko na pliki z serwera (`script-src 'self'`, `style-src 'self'`), więc w szablonach nie ma `<script>` bez `src`, atrybutów `onclick=` ani `style=`. Pilnuje tego `scripts/check_templates.py` w CI.
- **Bez `|safe` i `Markup()`** na danych użytkownika: Jinja2 sama escapuje treść (ochrona przed XSS).
- **Zachowania przez atrybuty `data-fm-*`.** Moduł w `js/components/` szuka swoich atrybutów, a HTML nie zawiera kodu.
- **Kolory i szerokości jako klasy.** Kolor użytkownika to `.u-color-N` (paleta w `backend/core/constants.py`), szerokość paska to `.fm-w-0` … `.fm-w-100`.
- **Tokeny zamiast wartości na sztywno.** Kolory, cienie i promienie biorą się z `css/base/tokens.css`, dzięki czemu tryb ciemny działa automatycznie.
- **Nowy komponent:** plik w `templates/components/`, styl w `static/css/components/` dopisany do `main.css`, ewentualny moduł w `static/js/components/` uruchomiony w `main.js`, przykład w `/_ui/`. Test `tests/frontend/test_structure.py` sprawdza, że każdy plik CSS jest zaimportowany i każdy szablon się kompiluje.
