#!/bin/sh
set -e

TEMPLATE=/etc/freeradius/sql.template
TARGET=/etc/freeradius/mods-enabled/sql

echo "[entrypoint] Gerando $TARGET a partir do template..."
envsubst '$DB_HOST $DB_PORT $DB_USER $DB_PASSWORD $DB_NAME' \
    < "$TEMPLATE" \
    > "$TARGET"

echo "[entrypoint] Arquivo gerado:"
cat "$TARGET"

echo "[entrypoint] Iniciando FreeRADIUS..."
exec "$@"
