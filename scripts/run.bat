@echo off
echo Stopping old containers...
docker rm -f capstone_container 2>/dev/null || true
docker-compose down -v --remove-orphans || true

echo Building new Docker images...
docker-compose build

echo Launching containers...
docker-compose up -d

echo Running services:
echo  - FastAPI: http://localhost:8000/docs
echo  - Frontend: http://localhost:5173

pause
