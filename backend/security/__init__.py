"""Mechanizmy bezpieczeństwa wspólne dla całej aplikacji.

- ``headers`` – CSP i nagłówki bezpieczeństwa,
- ``access`` – dekoratory ``flat_member_required`` i ``flat_admin_required``,
- ``passwords`` – hashowanie i weryfikacja haseł,
- ``tokens`` – tokeny sesji i zaproszeń,
- ``session`` – ładowanie użytkownika z sesji.

W etapie 4 dochodzi ``is_safe_next`` (bezpieczne przekierowania).
"""
