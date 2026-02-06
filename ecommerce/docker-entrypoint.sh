#!/bin/bash
set -e

# Fix permissions for bind-mounted directories (runs as root)
echo "Setting ownership for staticfiles and media directories..."
chown -R appuser:appuser /app/staticfiles /app/media
find /app/staticfiles /app/media -type d -exec chmod 755 {} \;
find /app/staticfiles /app/media -type f -exec chmod 644 {} \;

# Run migrations and collect static files as appuser
echo "Running database migrations..."
gosu appuser python manage.py migrate

echo "Collecting static files..."
gosu appuser python manage.py collectstatic --noinput

# Start the application as appuser (exec replaces shell process)
echo "Starting Gunicorn..."
exec gosu appuser gunicorn ecommerce.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
