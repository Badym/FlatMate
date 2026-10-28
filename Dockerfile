# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Etap bazowy: zależności produkcyjne z uv.lock (powtarzalne wersje, T-12)
# ---------------------------------------------------------------------------
FROM python:3.13-slim AS base

COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN groupadd --system flatmate \
    && useradd --system --gid flatmate --no-create-home --shell /usr/sbin/nologin flatmate

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

# ---------------------------------------------------------------------------
# Etap testów: zależności deweloperskie + testy (docker compose run tests)
# ---------------------------------------------------------------------------
FROM base AS test

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

COPY . .
RUN chown -R flatmate:flatmate /app
USER flatmate

CMD ["pytest", "--cov=backend", "--cov-report=term-missing", "--cov-fail-under=80"]

# ---------------------------------------------------------------------------
# Etap produkcyjny: tylko kod aplikacji, użytkownik bez uprawnień roota
# ---------------------------------------------------------------------------
FROM base AS runtime

COPY backend ./backend
COPY frontend ./frontend
# Jedyny zapisywalny katalog aplikacji: awatary (w docker-compose osobny wolumen).
RUN mkdir -p frontend/static/uploads/avatars && chown -R flatmate:flatmate frontend/static/uploads
COPY wsgi.py ./
COPY --chmod=755 docker/entrypoint.sh /usr/local/bin/entrypoint.sh

USER flatmate
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).status == 200 else 1)"]

ENTRYPOINT ["entrypoint.sh"]
# Jeden proces z wątkami: wspólne liczniki limitera w pamięci (D-16).
# Bez gniazda sterującego: system plików kontenera jest tylko do odczytu.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "--worker-tmp-dir", "/tmp", "--no-control-socket", "--access-logfile", "-", "wsgi:app"]
