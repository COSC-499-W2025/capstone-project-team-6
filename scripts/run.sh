#!/bin/bash
set -e
cd "$(dirname "$0")"

# Check if .env file exists in project root
if [ ! -f "../.env" ]; then
    echo ".env file not found in project root."
    if [ -f ".env.example" ]; then
        cp .env.example ../.env
        echo "Created ../.env file. Please edit it with your API keys."
    else
        echo ".env.example not found. Please create a .env file in the project root."
        exit 1
    fi
fi

echo "Stopping old containers..."
docker rm -f capstone_container 2>/dev/null || true
docker compose down --remove-orphans || true

echo "Building and updating Docker images..."
docker compose build --no-cache

echo "Launching containers."
docker compose up -d

echo "Running!"
echo " - Application: http://localhost:8000"
echo " - API Docs:    http://localhost:8000/docs"
