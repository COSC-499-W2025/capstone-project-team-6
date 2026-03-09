@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

REM Docker Setup Test Script for Windows

REM Check if we're in the scripts directory
IF NOT EXIST "docker-compose.yml" (
    echo Please run this script from the scripts\ directory
    echo    cd scripts ^&^& test-docker-setup.bat
    exit /b 1
)

REM Check if Docker is installed
docker --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Docker is not installed. Please install Docker Desktop first.
    exit /b 1
)
echo Docker is installed

REM Check if Docker Compose is installed
docker compose version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Docker Compose is not installed. Please install Docker Desktop first.
    exit /b 1
)
echo Docker Compose is installed
echo.

REM Check if .env file exists in project root
IF NOT EXIST "..\.env" (
    echo .env file not found in project root. Creating from .env.example...
    IF EXIST ".env.example" (
        copy /Y ".env.example" "..\.env" >nul
        echo Created ..\.env file. Please edit it with your API keys.
    ) ELSE (
        echo .env.example not found
        exit /b 1
    )
) ELSE (
    echo .env file exists in project root
)
echo.

REM Check if Dockerfile exists
IF NOT EXIST "Dockerfile" (
    echo Dockerfile not found
    exit /b 1
)
echo Dockerfile exists

REM Check if docker-compose.yml exists
IF NOT EXIST "docker-compose.yml" (
    echo docker-compose.yml not found
    exit /b 1
)
echo docker-compose.yml exists
echo.

echo Ready to build! Run:
echo    docker compose up --build
echo.
echo Or run in detached mode:
echo    docker compose up -d --build
echo.
