#!/bin/bash
set -e

# Run migrations and collect static files as root (before switching user)
echo "Running database migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the application
echo "Starting Gunicorn..."
exec gunicorn ecommerce.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
