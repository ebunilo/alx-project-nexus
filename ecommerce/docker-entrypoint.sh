#!/bin/bash
set -e

# If this is a celery worker, skip permission fixes for faster startup
if [ $# -gt 0 ] && [ "$1" = "celery" ] && echo "$*" | grep -q "worker"; then
    echo "Running celery worker: $*"
    exec gosu appuser "$@"
fi

# Fix permissions for bind-mounted directories (runs as root)
# Needed for the default web process and other commands that may write to these dirs
echo "Setting ownership for staticfiles and media directories..."
chown -R appuser:appuser /app/staticfiles /app/media
find /app/staticfiles /app/media -type d -exec chmod 755 {} \;
find /app/staticfiles /app/media -type f -exec chmod 644 {} \;

# If a command is passed (other than celery worker), run it as appuser after permission fixes
if [ $# -gt 0 ]; then
    echo "Running custom command: $*"
    exec gosu appuser "$@"
fi

# Otherwise, run the default Django setup and start Gunicorn
# Run migrations and collect static files as appuser
echo "Running database migrations..."
gosu appuser python manage.py migrate

echo "Collecting static files..."
gosu appuser python manage.py collectstatic --noinput

# Start the application as appuser (exec replaces shell process)
echo "Starting Gunicorn..."
exec gosu appuser gunicorn ecommerce.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
