#!/bin/bash

 
# Start frontend in background
echo "Starting frontend server..."
npm run dev &

# Wait for any process to exit
wait -n
