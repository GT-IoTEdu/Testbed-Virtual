#!/bin/bash
if docker info >/dev/null 2>&1; then
    DIR=$(readlink -f Scripts)
    
    # Ensure scripts have proper permissions on host
    if [ -z "$(docker images -q api/iotedu:latest 2> /dev/null)" ]; then
        docker build -t api/iotedu:latest .
    fi
    
else
    echo "Docker permission error. Run this command and restart your machine:"
    echo "sudo usermod -aG docker $USER"
fi
