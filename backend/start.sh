#!/bin/bash

# Database initialization
echo "Waiting for database to be ready..."
/opt/venv/bin/python /backend/wait_for_db.py
 

echo "Initializing database..."
/opt/venv/bin/python /backend/db/create_tables.py
/opt/venv/bin/python /backend/check_tables.py
/opt/venv/bin/python /backend/scripts/migrate_add_permission.py || true
/opt/venv/bin/python /backend/scripts/create_test_users.py || true

# Start backend in background
echo "Starting backend server..."
 
/opt/venv/bin/python /backend/start_server.py 


