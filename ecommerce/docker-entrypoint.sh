#!/bin/bash
set -e

# If a command is passed, run it as appuser (skip permission fixes)
if [ $# -gt 0 ]; then
    echo "Running custom command: $*"
    exec gosu appuser "$@"
fi

# Fix permissions for bind-mounted directories (runs as root)
# Only needed for the default web process
echo "Setting ownership for staticfiles and media directories..."
chown -R appuser:appuser /app/staticfiles /app/media
find /app/staticfiles /app/media -type d -exec chmod 755 {} \;
find /app/staticfiles /app/media -type f -exec chmod 644 {} \;

# Otherwise, run the default Django setup and start Gunicorn
# Run migrations and collect static files as appuser
echo "Running database migrations..."
gosu appuser python manage.py migrate

echo "Collecting static files..."
gosu appuser python manage.py collectstatic --noinput

# Start the application as appuser (exec replaces shell process)
echo "Starting Gunicorn..."
exec gosu appuser gunicorn ecommerce.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
