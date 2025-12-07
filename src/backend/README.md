# Backend Setup - Electron Desktop App

This is the Python FastAPI backend for an Electron-based desktop application.

## Tech Stack

- **Frontend**: React (Electron renderer process)
- **Backend**: FastAPI (Python API server)
- **Database**: SQLite (local database)
- **Desktop**: Electron
- **Containerization**: Docker & Docker Compose

## Prerequisites

- Python 3.13.7
- uv package manager
- Docker & Docker Compose (for full environment setup)

## Setup Instructions

### 1. Create Virtual Environment

```bash
uv venv
```

This creates a `.venv` directory with an isolated Python environment.

### 2. Activate Virtual Environment

```bash
source .venv/bin/activate
```

On Windows:
```bash
source .venv/Scripts/activate
```

### 3. Install Dependencies

```bash
uv pip install -r requirements.txt
```

## Installed Packages

### Core Dependencies
- **FastAPI 0.115.6** - Modern, fast web framework for building APIs
- **Uvicorn 0.34.0** - ASGI server for running FastAPI

### Database
- **SQLAlchemy 2.0.31** - ORM for SQLite database operations
- **SQLite** - Built into Python, no separate installation needed

### Environment Variables
- **python-dotenv 1.0.1** - Load environment variables from .env files

### Testing
- **pytest 8.2.2** - Testing framework
- **pytest-cov 5.0.0** - Code coverage plugin
- **httpx 0.28.1** - Async HTTP client for testing FastAPI endpoints

### Code Quality
- **black 24.4.2** - Code formatter
- **flake8 7.1.0** - Linting tool

## Using the CLI

The project provides a command-line interface (CLI) for interacting with the backend. The CLI tool is named `mda` (Mine Digital Artifacts).

### Installation

The CLI is automatically installed when you install the package:

```bash
pip install -e .
```

### Authentication Commands

```bash
# Login to the system
mda login <username> <password>

# Signing up
mda signup <username> <password>
```

### Analysis Commands

```
# Analyze a directory for projects
mda analyze <path>
```

The analyze command will:

1. Scan the directory structure
2. Identify project boundaries using heuristics
3. Score directories based on project indicators (like .git, package.json, etc.)
4. Display found projects with their scores and indicators

### Common Error Messages

- `Please login first`: You need to log in before using analysis features
- `Invalid credentials`: Username or password is incorrect
- `Path does not exist`: The specified directory path is invalid
- `Already logged in`: A user is already logged in (use logout first)

### Notes

- You must be logged in to use analysis features
- The system maintains a local session
- All commands will provide feedback on success or failure
- Use `mda --help` for command usage details

Other features will be added and updated when implemented.

## Running the Backend

```bash
uvicorn main:app --reload
```

Or specify host and port:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The FastAPI server will start and automatically reload on code changes.

## Dockerized Setup

The project includes Docker support for running both the backend and Electron-based frontend simultaneously.

### 1. Build and Launch Containers (macOS)
```
chmod +x scripts/run.sh
./scripts/run.sh
```
### 2. Build and Launch Containers (Windows)
```
scripts\win_run.bat
```
If this does not work 
```
scripts/run.bat
```
### 3. Access Services
- Backend (FastAPI) → http://localhost:8000/docs
- Frontend (React/Vite) → http://localhost:5173


## Development Workflow

### Running Tests
```bash
pytest
```

### Code Coverage
```bash
pytest --cov=.
```

### Code Formatting
```bash
black .
```

### Linting
```bash
flake8
```

## Environment Variables

Create a `.env` file in the backend directory for environment-specific configuration:

```env
DATABASE_PATH=./data/app.db
SECRET_KEY=your-secret-key
```

## Project Structure

```
backend/
├── .venv/              # Virtual environment (not in git)
├── .gitignore         # Git ignore rules
├── main.py            # FastAPI application entry point
├── requirements.txt   # Python dependencies
├── README.md          # This file
└── data/              # SQLite database storage (not in git)
```

## Integration with Electron

The FastAPI backend runs as a local API server that the Electron app communicates with via HTTP requests. The React frontend (in the Electron renderer process) will make API calls to `http://localhost:8000` (or configured port).
≈≈
### Communication Flow
```
Electron Main Process
    ↓
React Frontend (Renderer) ← HTTP → FastAPI Backend ← SQLAlchemy → SQLite Database
```

## API Documentation

FastAPI automatically generates interactive API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
