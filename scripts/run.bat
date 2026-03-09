@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

REM Navigate to the script's directory
cd /d %~dp0

REM Check if .env file exists in project root
IF NOT EXIST "..\.env" (
    echo .env file not found in project root.
    IF EXIST ".env.example" (
        echo Creating .env from .env.example...
        copy /Y ".env.example" "..\.env" >nul
        echo Created ..\.env file. Please edit it with your API keys.
    ) ELSE (
        echo .env.example not found. Please create a .env file in the project root.
        exit /b 1
    )
)

echo Stopping old containers...
docker rm -f capstone_container >nul 2>&1
docker compose down --remove-orphans >nul 2>&1

echo Building and updating Docker images...
docker compose build --no-cache

echo Launching containers...
docker compose up -d

echo Running!
echo  - Application: http://localhost:8000
echo  - API Docs:    http://localhost:8000/docs
