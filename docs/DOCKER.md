# Docker Guide

Step-by-step guide to run the app with Docker.

---

## 1. Where to run commands

**All Docker commands must be run from the `scripts/` directory.**

```bash
cd /path/to/capstone-project-team-6/scripts
```

So your prompt should look like: `.../capstone-project-team-6/scripts $`

---

## 2. One-time setup

### 2.1 Create `.env` in the project root

The app reads environment variables from a file named `.env` in the **project root** (one level above `scripts/`).

- **Option A:** If you run `./run.sh` or `run.bat` and `.env` is missing, it will copy `scripts/.env.example` to the project root as `.env`. You still need to edit it (see below).
- **Option B:** Do it yourself:

```bash
# From project root (one level above scripts/)
cp scripts/.env.example .env
```

So the file you edit is: **`capstone-project-team-6/.env`** (not inside `scripts/`).

### 2.2 Variables you should change in `.env`

| Variable | What to do |
|----------|------------|
| `JWT_SECRET` | **Not used.** The app uses in-memory tokens, not JWT. You can leave it as-is or omit it. |
| `GOOGLE_API_KEY` | **Change if you use Google/LLM features.** Replace `your_google_api_key_here` with your key, or leave as-is if you don’t need those features. |
| `GEMINI_API_KEY` | **Change if you use Gemini/LLM features.** Same as above. |

### 2.3 Variables you can leave as-is (Docker defaults)

These are already set in `docker-compose.yml` or match the Postgres container; you usually don’t need to change them in `.env` unless you want different paths or DB credentials:

- `MYAPP_DB_PATH` – set by Compose to `/app/data/myapp.db`
- `ANALYSIS_DB_PATH` – set by Compose to `/app/data/analysis.db`
- `DOCUMENTS_DB_PATH` – set by Compose to `/app/data/documents.db`
- `DATABASE_URL` – set by Compose to `postgresql://postgres:postgres@database:5432/vector_db`
- `POSTGRES_*` – used by the Postgres container; only change if you change the image or need different credentials.

If you **do** put these in `.env`, keep the same values so the app can find the databases and connect to the `database` service.

---

## 3. Build and run

From **`scripts/`**:

**macOS / Linux:**
```bash
./run.sh
```

**Windows (cmd):**
```cmd
run.bat
```

**Or manually (from `scripts/`):**
```bash
docker compose build --no-cache
docker compose up -d
```

---

## 4. Where the app runs (URLs)

After `docker compose up -d` succeeds:

| What | URL |
|------|-----|
| **Main application (frontend + API)** | **http://localhost:8000** |
| **API documentation (Swagger)** | http://localhost:8000/docs |
| **Health check** | http://localhost:8000/api/health |

Open **http://localhost:8000** in your browser to use the app. The frontend is served by the same server on that port.

---

## 5. Useful commands (all from `scripts/`)

```bash
# View app logs
docker compose logs -f app

# Stop the app and database
docker compose down

# Stop and delete database volumes (fresh start)
docker compose down -v
```

---

## 6. If something goes wrong

- **Port 8000 already in use**  
  Edit `scripts/docker-compose.yml`: change `"8000:8000"` to e.g. `"8001:8000"`. Then use **http://localhost:8001** instead of 8000.

- **“.env not found” or variables not applied**  
  `.env` must be in the **project root** (`capstone-project-team-6/.env`), not in `scripts/`. Compose is run from `scripts/` and loads `../.env`.

- **App doesn’t load at http://localhost:8000**  
  Wait 30–60 seconds after `docker compose up -d`, then check logs: `docker compose logs app`. Fix any errors (e.g. DB connection) and restart: `docker compose up -d`.
