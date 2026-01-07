#!/bin/bash
set -e

echo "Waiting for database to be ready..."

# Set Python path to include the backend directory
export PYTHONPATH="/API_IoT_EDU/backend:$PYTHONPATH"

# Check if database is available (modify with your actual DB credentials)
if [ -n "$DB_HOST" ]; then
    echo "Checking database connection to $DB_HOST..."
    # You can add a database connection check here
    # For example, using wait-for-it or similar tool
fi

echo "Running database migrations..."
cd /API_IoT_EDU/backend

# Run migrations with error handling
python scripts/migrate_add_permission.py || echo "Migration failed or already applied - continuing..."
python scripts/create_test_users.py || echo "User creation failed or already done - continuing..."

echo "Starting application..."
exec "$@"
