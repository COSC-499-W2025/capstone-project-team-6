# Initialisation Guide: MDA Portfolio & Resume Generator

This document gets you from zero to a running application as quickly as possible. Choose the setup path that suits you best.

---

## What is this project?

The **MDA Portfolio & Resume Generator** analyses your digital work artifacts (code repositories, documents, media) and automatically generates a curated portfolio and one-page resume. It extracts projects, skills, and contributions from uploaded ZIP archives, then lets you customise the output through a web interface.

- **Backend:** Python / FastAPI
- **Frontend:** React / Vite
- **Database:** SQLite (default) + optional PostgreSQL with pgvector

---

## Prerequisites

| Path   | Tool               | Minimum Version | Download                                                      |
| ------ | ------------------ | --------------- | ------------------------------------------------------------- |
| Docker | **Docker Desktop** | 24+             | [docker.com](https://www.docker.com/products/docker-desktop/) |
| Local  | **Python**         | 3.9+            | [python.org](https://www.python.org/downloads/)               |
| Local  | **Node.js**        | 18+             | [nodejs.org](https://nodejs.org/)                             |

> You only need **one** of the two paths below.

---

## Option A — Docker (Recommended for first-timers)

The fastest way to get the full app running with a single command.

### 1. Clone the repository

```bash
git clone <repository-url>
cd capstone-project-team-6
```

### 2. Create the environment file

```bash
cp scripts/.env.example .env
```

The defaults work out of the box. If you want AI-powered analysis features, open `.env` and fill in your API key:

```env
GOOGLE_API_KEY=your_key_here
```

### 3. Build and start

**macOS / Linux:**

```bash
cd scripts
./run.sh
```

**Windows (Command Prompt):**

```cmd
cd scripts
run.bat
```

**Or manually:**

```bash
cd scripts
docker compose build --no-cache
docker compose up -d
```

### 4. Open the app

Wait ~30 seconds for the app to initialise, then open:

| What               | URL                              |
| ------------------ | -------------------------------- |
| Application        | http://localhost:8000            |
| API docs (Swagger) | http://localhost:8000/docs       |
| Health check       | http://localhost:8000/api/health |

### Stop the app

```bash
# From the scripts/ directory
docker compose down          # stop containers
docker compose down -v       # stop + delete database volumes (fresh start)
```

---

## Option B — Local Development

Run the backend and frontend as separate processes. Requires Python and Node.js installed.

### 1. Clone the repository

```bash
git clone <repository-url>
cd capstone-project-team-6
```

### 2. Set up the Python backend

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

You should see `(venv)` in your prompt. Then install dependencies:

```bash
pip install -r requirements.txt
pip install -e .
```

### 3. Set up the frontend

```bash
cd src/frontend
npm install
cd ../..
```

### 4. Configure environment variables (optional)

Create a file at `src/backend/.env`. The app works with SQLite out of the box — you only need this file if you want vector search or AI features:

```env
# Only needed for AI-powered file search
GOOGLE_API_KEY=your_key_here

# Only needed for vector database (pgvector)
VECTOR_DB_URL=postgresql://postgres:postgres@localhost:5432/vector_db
```

### 5. Start the backend

> **Important:** Run from the `src/` directory, not from `src/backend/`. The import paths require this.

```bash
cd src
python -m uvicorn backend.api_server:app --host 0.0.0.0 --port 8000 --reload
```

The backend starts at **http://localhost:8000**. The `--reload` flag restarts the server automatically on code changes.

### 6. Start the frontend (new terminal)

Keep the backend running and open a second terminal:

```bash
cd src/frontend
npm run dev
```

The frontend starts at **http://localhost:5173** and proxies all `/api` requests to the backend at port 8000.

---

## Default Login Credentials

The database is pre-seeded with a test account so you can log in immediately:

| Username   | Password      |
| ---------- | ------------- |
| `testuser` | `password123` |

---

## Environment Variables

| Variable               | Required          | Description                                    |
| ---------------------- | ----------------- | ---------------------------------------------- |
| `GOOGLE_API_KEY`       | Optional          | Enables Google Gemini AI-powered analysis      |
| `GEMINI_API_KEY`       | Optional          | Alternative key for Gemini features            |
| `VECTOR_DB_URL`        | Optional          | PostgreSQL connection string for vector search |
| `DATABASE_URL`         | Optional (Docker) | Set automatically by Docker Compose            |
| `GOOGLE_CLOUD_PROJECT` | Optional          | Google Cloud project ID for Gemini             |

> All variables are optional for basic usage. Core features (upload, analysis, portfolio, resume generation) work with SQLite and no API keys.

---

## Running Tests

### Backend tests (Python)

Run from the **project root** with the virtual environment active:

```bash
# All tests
pytest src/tests/

# By category
pytest src/tests/backend_test/      # unit tests
pytest src/tests/api_test/          # API tests
pytest src/tests/integration_test/  # integration tests

# With coverage report
pytest src/tests/ --cov=src/backend --cov-report=term-missing
```

### Frontend tests (JavaScript)

```bash
cd src/frontend
npm run test          # run all tests
npm run test:ui       # run with interactive UI
```

---

## Project Structure

```
capstone-project-team-6/
├── src/
│   ├── backend/          # Python FastAPI application
│   │   ├── api_server.py     # App entry point
│   │   ├── api/              # Route handlers (auth, analysis, portfolio, resume…)
│   │   ├── analysis/         # Code & document analyzers
│   │   └── database.py       # SQLite user/session management
│   ├── frontend/         # React + Vite application
│   │   └── src/
│   │       ├── pages/        # Page components
│   │       ├── components/   # Reusable UI components
│   │       └── services/     # API client services
│   └── tests/            # All test suites
│       ├── backend_test/
│       ├── api_test/
│       └── integration_test/
├── scripts/              # Docker Compose files and run scripts
├── docs/                 # Detailed documentation
├── requirements.txt      # Python dependencies
└── INITIALISATION.md     # This file
```

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'backend'`**
You ran uvicorn from the wrong directory. Always run from `src/`, not from `src/backend/`:

```bash
cd src
python -m uvicorn backend.api_server:app ...
```

**Port 8000 is already in use**

- Docker: edit `scripts/docker-compose.yml` and change `"8000:8000"` to e.g. `"8001:8000"`, then use http://localhost:8001
- Local: add `--port 8001` to the uvicorn command

**`.env` not found when using Docker**
The file must be at the **project root** (`capstone-project-team-6/.env`), not inside `scripts/`. Docker Compose loads it from one level above `scripts/`.

**App not loading after `docker compose up`**
Wait 30–60 seconds for the health check to pass, then run:

```bash
docker compose logs app
```

---

## Further Reading

| Document                                                      | Description                             |
| ------------------------------------------------------------- | --------------------------------------- |
| [docs/DOCKER.md](docs/DOCKER.md)                              | Detailed Docker guide with all commands |
| [docs/SETUP\_ INSTRUCTIONS.md](docs/SETUP_%20INSTRUCTIONS.md) | Full local development setup guide      |
| [docs/API_REFERENCE.md](docs/API_REFERENCE.md)                | REST API endpoint documentation         |
