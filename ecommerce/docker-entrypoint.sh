#!/bin/bash
set -e

# Ensure proper permissions for bind-mounted directories
echo "Setting permissions for staticfiles and media directories..."
chmod -R 755 /app/staticfiles /app/media 2>/dev/null || true

# Run migrations and collect static files
echo "Running database migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the application
echo "Starting Gunicorn..."
exec gunicorn ecommerce.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
