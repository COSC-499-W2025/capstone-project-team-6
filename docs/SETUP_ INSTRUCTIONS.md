# Setup Instructions — MDA Portfolio & Resume Generator

This guide walks you through setting up and running the project from scratch.

## Prerequisites

Make sure you have the following installed on your machine before continuing:

| Tool | Minimum Version | Download Link |
|------|----------------|---------------|
| **Python** | 3.9+ | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 18+ | [nodejs.org](https://nodejs.org/) |

---

## Clone the Repository

If you haven't already, clone the project to your local machine:

```bash
git clone <repository-url>
cd capstone-project-team-6
```

---

## Install Python Dependencies

All Python packages required by the project are listed in the `requirements.txt` file at the project root.

### 1. Create a virtual environment (recommended)

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

> You should see `(venv)` at the beginning of your terminal prompt, confirming the virtual environment is active.

### 2. Install the dependencies

```bash
pip install -r requirements.txt
```

This will install all backend dependencies including FastAPI, SQLAlchemy, pytest, and others.

### 3. Install the project in editable mode

This lets Python find the `src/backend` modules correctly:

```bash
pip install -e .
```

---

## Install Frontend Dependencies

The frontend is a React application located in `src/frontend/`.

```bash
cd src/frontend
npm install
```

This reads `package.json` and downloads all required JavaScript packages into `node_modules/`.

Once done, navigate back to the project root:

```bash
cd ../..
```

---

## Environment Variables

The backend uses a `.env` file for configuration (database URLs, API keys, etc.). Create one at `src/backend/.env`.

A minimal `.env` file looks like this:

```env
# Vector database (only needed if using pgvector features)
VECTOR_DB_URL=postgresql://postgres:postgres@localhost:5432/vector_db

# Google Gemini (only needed if using AI-powered file search)
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_CLOUD_PROJECT=your_project_id_here
GEMINI_LOCATION=us-central1
```

> **Note:** The core functionality (authentication, project analysis, portfolio/resume generation) works with SQLite out of the box and does **not** require these variables. You only need to configure them if you want to use the vector database or Gemini AI features.

---

## Start the Backend Server

The backend is a FastAPI application. The code uses imports like `from backend.xxx import ...`, so you must run from the `src/` directory (not from inside `src/backend/`).

```bash
cd src
python -m uvicorn backend.api_server:app --host 0.0.0.0 --port 8000 --reload
```

The server will start on **http://localhost:8000**.

- **API Docs (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative API Docs (ReDoc):** [http://localhost:8000/redoc](http://localhost:8000/redoc)

> The `--reload` flag enables auto-restart on code changes, which is useful during development.
>
> **Common mistake:** Running `python api_server.py` from inside `src/backend/` will fail with `ModuleNotFoundError: No module named 'backend'`. Always run from the `src/` directory.

---

## Start the Frontend Server

Open a **new/separate terminal** (keep the backend running in the first one).

```bash
cd src/frontend
npm run dev
```

The frontend development server will start on **http://localhost:5173**.

Open your browser and go to [http://localhost:5173](http://localhost:5173) to see the application.

> The frontend is configured to proxy API requests (any request to `/api`) to the backend at `http://localhost:8000`, so both servers need to be running at the same time.

---

## Running Tests

### Backend Tests (Python)

Backend tests use **pytest** and are located in `src/tests/`. From the **project root**, run:

```bash
# Run all backend tests
pytest src/tests/

# Run only unit tests
pytest src/tests/backend_test/

# Run only API tests
pytest src/tests/api_test/

# Run only integration tests
pytest src/tests/integration_test/

# Run a specific test file
pytest src/tests/backend_test/test_authentication.py

# Run tests with verbose output
pytest src/tests/ -v

# Run tests with coverage report
pytest src/tests/ --cov=src/backend --cov-report=term-missing
```

### Frontend Tests (JavaScript)

Frontend tests use **Vitest** and are located inside `src/frontend/src/`. From the `src/frontend/` directory:

```bash
cd src/frontend

# Run all frontend tests
npm run test

# Run tests with UI
npm run test:ui
```
