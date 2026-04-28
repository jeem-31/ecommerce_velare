#!/bin/bash
set -e

echo "🚀 Starting Velare Application"
echo "📍 Port: ${PORT:-5000}"
echo "🔑 Supabase URL: ${SUPABASE_URL:0:30}..."

# Run database migrations if needed
# python migrate.py

# Start gunicorn
exec gunicorn \
    --bind 0.0.0.0:${PORT:-5000} \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    app:app
