#!/bin/sh
# Start kontenera aplikacji: migracje schematu bazy, potem serwer (CMD).
set -eu

flask --app wsgi db upgrade

exec "$@"
