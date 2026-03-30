#!/bin/bash
cp backend/.env frontend/
docker compose down
docker compose up --build --no-attach server_alvo
