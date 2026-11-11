"""Punkt wejścia WSGI dla gunicorna i polecenia ``flask --app wsgi``."""

from backend import create_app

app = create_app()
