"""Stałe domenowe współdzielone przez formularze, serwisy i widoki."""

PASSWORD_MIN_LENGTH = 12  # SR-1, T-03
PASSWORD_MAX_LENGTH = 128
EMAIL_MAX_LENGTH = 254
DISPLAY_NAME_MAX_LENGTH = 50
FLAT_NAME_MAX_LENGTH = 80
TASK_TYPE_NAME_MAX_LENGTH = 50
TASK_TITLE_MAX_LENGTH = 100
TASK_DESCRIPTION_MAX_LENGTH = 1000

INVITE_VALIDITY_DAYS = 7  # SR-8, T-08

# Logowanie: SR-2, T-03. Limity na adres IP liczą tylko nieudane próby (status 401).
LOGIN_RATE_LIMIT = "5 per minute;20 per hour"
REGISTER_RATE_LIMIT = "10 per hour"
PASSWORD_CHANGE_RATE_LIMIT = "10 per hour"
LOGIN_MAX_FAILURES = 10  # tyle nieudanych prób na konto zakłada blokadę
LOGIN_LOCK_MINUTES = 15

# Awatary: SR-9, T-10
AVATAR_SIZE = 256  # px, dłuższy bok po zmniejszeniu
AVATAR_MAX_PIXELS = 4096 * 4096  # większe obrazy odrzucamy przed dekodowaniem

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
