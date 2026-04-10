#!/bin/bash

# Function to open a new terminal window with a command
open_terminal() {
    local command="$1"
    local title="$2"

    # Try different terminal emulators in order of preference
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal --title="$title" -- bash -c "$command; exec bash"
    elif command -v konsole &> /dev/null; then
        konsole --new-tab --title="$title" -e bash -c "$command; exec bash"
    elif command -v xfce4-terminal &> /dev/null; then
        xfce4-terminal --title="$title" -e bash -c "$command; exec bash"
    elif command -v mate-terminal &> /dev/null; then
        mate-terminal --title="$title" -e bash -c "$command; exec bash"
    elif command -v terminator &> /dev/null; then
        terminator --title="$title" -e bash -c "$command; exec bash"
    elif command -v xterm &> /dev/null; then
        xterm -title "$title" -e bash -c "$command; exec bash"
    else
        echo "No supported terminal emulator found!"
        return 1
    fi
    return 0
}

# Copy environment file
cp backend/.env frontend/

# Stop existing containers
docker compose down

echo "Opening terminal for uvicorn server..."
open_terminal "cd $(pwd)/server_sse/ && uvicorn server_sse:app --host 0.0.0.0 --port 8001 --reload" "Uvicorn Server"
docker compose up --build



# Open second terminal for uvicorn


# Wait for docker process

