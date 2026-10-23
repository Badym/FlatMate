"""Stałe domenowe współdzielone przez formularze, serwisy i widoki."""

PASSWORD_MIN_LENGTH = 12  # SR-1, T-03
PASSWORD_MAX_LENGTH = 128
EMAIL_MAX_LENGTH = 254
DISPLAY_NAME_MAX_LENGTH = 50

# Paleta kolorów użytkowników (D-6). Indeks odpowiada klasie CSS ``.u-color-N``
# w frontend/static/css/components/avatar.css, więc obie listy muszą mieć tę samą kolejność.
USER_COLORS: tuple[tuple[str, str], ...] = (
    ("Indygo", "#4f46e5"),
    ("Fiolet", "#7c3aed"),
    ("Fuksja", "#c026d3"),
    ("Róż", "#db2777"),
    ("Czerwień", "#dc2626"),
    ("Pomarańcz", "#ea580c"),
    ("Bursztyn", "#d97706"),
    ("Limonka", "#65a30d"),
    ("Zieleń", "#16a34a"),
    ("Morski", "#0d9488"),
    ("Błękit", "#0284c7"),
    ("Grafit", "#475569"),
)
