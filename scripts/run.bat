@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

REM Navigate to the script's directory
cd /d %~dp0

echo Stopping old containers...
docker rm -f capstone_container >nul 2>&1
docker-compose down -v --remove-orphans >nul 2>&1

echo Building and updating Docker images...
docker compose build --no-cache

echo Launching containers...
docker compose up -d

echo Running!
echo  - Backend:  http://localhost:8000/docs
echo  - Frontend: http://localhost:5173
