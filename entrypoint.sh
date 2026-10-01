#!/bin/sh
set -e

echo "=========================================="
echo "  Starting MEMO Production Container     "
echo "=========================================="

# Determine SQLite DB path
TARGET_DB="${DB_PATH:-/app/data/db.sqlite3}"
TARGET_DIR=$(dirname "$TARGET_DB")

mkdir -p "$TARGET_DIR"

# If persistent DB doesn't exist yet, seed from bundled db.sqlite3
if [ ! -f "$TARGET_DB" ] && [ -f "/app/db.sqlite3" ]; then
    echo "==> Initializing persistent database from bundled db.sqlite3..."
    cp /app/db.sqlite3 "$TARGET_DB"
fi

# Populate initial media files if media volume is empty
if [ -d "/app/seed_media" ] && [ -z "$(ls -A /app/media 2>/dev/null)" ]; then
    echo "==> Populating initial media files into persistent volume..."
    cp -r /app/seed_media/* /app/media/ 2>/dev/null || true
fi

# Apply database migrations
echo "==> Running database migrations..."
python manage.py migrate --noinput

# Collect static files into staticfiles directory
echo "==> Collecting static assets..."
python manage.py collectstatic --noinput

# Optionally keep the per-instance Evolution webhook configuration in sync.
# Run this in the background so a temporarily disconnected/unlicensed Evolution
# instance never prevents the storefront from starting. Retrying also covers the
# normal race where Evolution is healthy before the WhatsApp instance is ready.
if [ "${EVOLUTION_AUTO_CONFIGURE_WEBHOOK:-0}" = "1" ]; then
    (
        attempt=1
        while [ "$attempt" -le 20 ]; do
            echo "==> Configuring Evolution API webhook (attempt $attempt/20)..."
            if python manage.py configure_evolution_webhook; then
                exit 0
            fi
            attempt=$((attempt + 1))
            sleep 15
        done
        echo "WARNING: Evolution webhook could not be configured; the storefront will remain available."
    ) &
fi

# Configure Gunicorn workers
WORKERS=${GUNICORN_WORKERS:-3}
THREADS=${GUNICORN_THREADS:-2}
TIMEOUT=${GUNICORN_TIMEOUT:-60}

echo "==> Starting Gunicorn (Workers: $WORKERS, Threads: $THREADS, Timeout: ${TIMEOUT}s)..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "$WORKERS" \
    --threads "$THREADS" \
    --timeout "$TIMEOUT" \
    --access-logfile - \
    --error-logfile -
