"""Punkt wejścia WSGI dla gunicorna i polecenia ``flask --app wsgi``."""

from app import create_app

app = create_app()
