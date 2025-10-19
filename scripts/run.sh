#!/bin/bash
set -e
cd "$(dirname "$0")"
echo "Stopping old containers..."
docker rm -f capstone_container 2>/dev/null || true
docker-compose down -v --remove-orphans || true

echo "Building and updating Docker images..."
docker compose build --no-cache

echo "Launching containers."
docker compose up -d

echo "Running!"
echo " - Backend:  http://localhost:8000/docs"
echo " - Frontend: http://localhost:5173"
