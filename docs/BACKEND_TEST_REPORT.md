# Backend Test Report

## 1. Introduction

This report summarizes the backend testing completed for the capstone system. It lists the backend test files currently used in the project, the components and features they cover, and the testing strategies used to verify that the server-side logic behaves as expected.

The backend is built with FastAPI and Python and supports important workflows such as authentication, portfolio management, project analysis, resume generation, LLM integration, curation, and role prediction. Backend testing focuses on confirming that API endpoints, analysis algorithms, database operations, and processing pipelines behave correctly under normal, edge-case, and failure conditions.

---

## 2. Scope of Backend Testing

The backend tests focus on validating:

- REST API endpoint behavior (status codes, response shapes, authentication)
- Core analysis modules (code complexity, OOP pattern detection, git analysis)
- Database read/write operations (user data, analysis results, resume content)
- LLM pipeline integration (mocked Gemini API calls, consent gating)
- Resume and portfolio generation logic
- Project ranking and curation algorithms
- Role prediction using ML techniques
- CLI command workflows
- End-to-end analysis pipelines across multiple components

The testing does not directly validate browser-side rendering or full production network behavior. External services (Google Gemini API, PostgreSQL pgvector) are mocked or conditionally skipped.

---

## 3. Test Environment

The backend test suite uses the following tools and configuration:

- **Framework:** pytest 8.4.2
- **Async support:** pytest-asyncio 0.24.0
- **API testing:** FastAPI `TestClient` (backed by httpx)
- **Configuration file:** `src/tests/pytest.ini`
- **Setup files:** `src/tests/backend_test/conftest.py`, `src/tests/integration_test/conftest.py`
- **Run commands:**

```bash
# From src/ directory with PYTHONPATH set
cd src
PYTHONPATH=/path/to/src/backend python -m pytest tests/backend_test/ -v
PYTHONPATH=/path/to/src/backend python -m pytest tests/api_test/ -v
PYTHONPATH=/path/to/src/backend python -m pytest tests/integration_test/ -v
```

Or from inside Docker (where `pythonpath = /app` is pre-configured):

```bash
pytest tests/ -v
```

### Shared Fixtures (backend_test/conftest.py)

- `temp_db` — Creates an isolated temporary SQLite database for each test
- `test_user` — Creates a test user with a random username and known password
- `fake_session` (autouse) — Simulates a logged-in CLI session for all backend tests
- `setup_vector_db` (session-scoped, autouse) — Initializes pgvector tables if `VECTOR_DB_URL` is set; otherwise skips silently

### Shared Fixtures (integration_test/conftest.py)

- `temp_db` — Temporary database with full initialization
- `temp_session_file` — Isolated session file using monkeypatch
- `cleanup_session` — Clears session state before and after each test
- `isolated_test_env` — Combined fixture providing a clean environment
- `mock_users` — Creates 8 test users (alice, bob, carol, dave, eve, frank, grace, henry)
- `test_directory` — Git-initialized directory with sample code files

---

## 4. Test Files and Coverage

All backend test files are located in `src/tests/`. The current test suite contains **60 test files** and approximately **897 total tests**.

To run all tests:

```bash
cd src
PYTHONPATH=/path/to/src/backend python -m pytest tests/ -v
```

### 4.1 API Tests (`src/tests/api_test/`)

| Test File | Component | Tests | Primary Coverage |
|---|---:|---:|---|
| `test_analysis.py` | Analysis API | 7 | Re-analysis endpoint, consent checks, portfolio validation |
| `test_api_endpoints.py` | All endpoints | 26 | Health, auth, portfolios, analysis, resume, tasks, curation |
| `test_api_server.py` | API server setup | 15 | CORS, routers, docs, tags, versioning, error handling, performance |
| `test_auth.py` | Auth endpoints | 23 | Signup, login, logout, password change, token expiration |
| `test_health.py` | Health endpoints | 7 | Health check, root endpoint, version consistency, no-auth requirements |
| `test_incremental_upload.py` | Incremental upload | 8 | Incremental portfolio uploads, deduplication, missing portfolio handling |
| `test_llm_analysis_endpoint.py` | LLM endpoint | 7 | LLM summaries, error states, missing LLM, access control |
| `test_portfolios.py` | Portfolio endpoints | 14 | List, get, delete portfolios, consent management, upload handling |
| `test_project_thumbnails.py` | Thumbnail endpoints | 9 | Upload, get, delete thumbnails, auth, validation |
| `test_projects.py` | Project endpoints | 11 | List projects, get details, skills aggregation, invalid formats |
| `test_resume.py` | Resume endpoints | 43 | Resume generation, multiple projects, personal info, formatting |
| `test_resume_education.py` | Education endpoints | 5 | Education CRUD, user scoping, personal info seeding |
| `test_resume_generate_bugfix.py` | Resume generation | 19 | Resume generation edge cases and bugfix verification |
| `test_resume_highlighted_skills.py` | Resume skills | 7 | Highlighted skills extraction, forwarding to generator, model validation |
| `test_tasks.py` | Task endpoints | 10 | Task status, user task list, task cancellation |

### 4.2 Backend Tests (`src/tests/backend_test/`)

| Test File | Component | Tests | Primary Coverage |
|---|---:|---:|---|
| `test_analysis_database.py` | `analysis_database.py` | 27 | Analysis storage, retrieval, user scoping |
| `test_analyze.py` | `analyze.py` | 22 | Comprehensive report generation from ZIP projects |
| `test_authentication.py` | `database.py` | 4 | User authentication logic |
| `test_c_analysis.py` | `c_oop_analyzer.py` | 22 | C OOP patterns (structs, inheritance, encapsulation) |
| `test_chronology.py` | `chronology` | 7 | Git activity chronology analysis |
| `test_complexity_analyzer.py` | `complexity_analyzer.py` | 49 | Python and Java cyclomatic complexity detection |
| `test_consent.py` | `consent.py` | 11 | User consent tracking and updates |
| `test_cpp_oop_analyzer.py` | `cpp_oop_analyzer.py` | 20 | C++ OOP analysis (classes, templates, access control) |
| `test_curation.py` | `curation.py` | 19 | Project curation logic |
| `test_curation_api.py` | Curation API | 23 | Curation API endpoints |
| `test_curation_cli.py` | Curation CLI | 20 | Curation CLI commands |
| `test_database.py` | `database.py` | 4 | SQLite user database operations |
| `test_deep_code_analyzer.py` | `deep_code_analyzer.py` | 11 | Deep code complexity analysis |
| `test_documents_database.py` | `documents_database.py` | 2 | Document storage operations |
| `test_enhanced_api.py` | Enhanced API | 15 | Enhanced API features |
| `test_enhanced_ranking.py` | Ranking algorithm | 39 | Project ranking, scoring metrics, contribution weights |
| `test_gemini_file_search.py` | `gemini_file_search.py` | 9 | Google Gemini API integration (mocked) |
| `test_git_analysis.py` | `git_analysis.py` | 42 | Git history, contributors, commit analysis, branch info, export |
| `test_git_analysis_activity.py` | Git activity | 2 | Git activity patterns |
| `test_inc_upload.py` | Incremental upload | 11 | Incremental portfolio upload processing |
| `test_java_oop_analyzer.py` | `java_oop_analyzer.py` | 15 | Java OOP analysis (classes, interfaces, inheritance) |
| `test_llm_summary.py` | LLM summaries | 20 | LLM-generated project summaries |
| `test_metadata_extractor.py` | `metadata_extractor.py` | 29 | Document metadata extraction (PDF, DOCX, TXT) |
| `test_portfolio_item_generator.py` | Portfolio generator | 34 | Portfolio item generation from project analyses |
| `test_project_analyzer.py` | `project_analyzer.py` | 41 | FileClassifier — ignore patterns, test detection, language detection |
| `test_resume_generator.py` | `resume_generator.py` | 16 | Project type detection, architecture items, tech items, formatting |
| `test_resume_generator_highlighted_skills.py` | Resume generator | 13 | Highlighted skills rendering in resume output |
| `test_resume_retrieval.py` | Resume retrieval | 12 | Resume item retrieval and filtering |
| `test_role_curation.py` | Role curation | 19 | Job role curation and matching |
| `test_role_prediction_integration.py` | Role prediction | 8 | Role prediction integration tests |
| `test_role_prediction_runner.py` | Role prediction | 0 | (Empty — placeholder) |
| `test_role_predictor.py` | `role_predictor.py` | 26 | ML-based role prediction across developer profiles |
| `test_session.py` | `session.py` | 4 | Session save, clear, and load |
| `test_task_manager_llm.py` | `task_manager.py` | 4 | LLM task lifecycle and consent gating |
| `test_text_extractor.py` | `text_extractor.py` | 4 | Text extraction from plain text, images, PDF, JSON |
| `test_traversal.py` | `traversal.py` | 2 | Directory traversal |
| `test_user_contribution_scoring.py` | Contribution scoring | 2 | User contribution boost calculations |
| `test_user_scoping.py` | User scoping | 6 | User data isolation in analysis database |
| `test_vector_service.py` | `vector_service.py` | 5 | Vector embedding service |
| `test_zip_traversal.py` | `traversal.py` | 10 | ZIP file traversal and structure validation |

### 4.3 Integration Tests (`src/tests/integration_test/`)

| Test File | Component | Tests | Primary Coverage |
|---|---:|---:|---|
| `test_analysis_integration.py` | Full pipeline | 19 | End-to-end analysis: upload → analyze → retrieve, LLM pipeline |
| `test_auth_session_integration.py` | Auth + session | 10 | Auth flow with session management, multi-user isolation |
| `test_cli_integration.py` | CLI workflows | 27 | CLI signup, login, consent, analyze commands end-to-end |
| `test_upload_analysis_cycle.py` | Upload + analysis | 8 | Full upload-to-analysis cycle |

---

## 5. Detailed Test Coverage

### 5.1 `test_api_server.py`
**Component under test:** `api_server.py`
**Total tests:** 15

Tests the FastAPI application setup. Verifies that the app has correct metadata (title, version), CORS middleware is configured, all routers are registered (including `/`, `/api/health`, `/api/auth/login`, `/api/projects`, `/api/resume/generate`, etc.), and that OpenAPI documentation is available at `/docs`, `/redoc`, and `/openapi.json`. Also tests 404/405/422 error handling, CORS headers, and response time under concurrent load.

### 5.2 `test_auth.py`
**Component under test:** Auth API endpoints
**Total tests:** 23

Tests the full authentication lifecycle. Covers successful signup, duplicate username rejection, short username/password validation, login success and failure paths, logout (with token removal), token expiration behavior, and password change flows. Confirms that endpoints that require authentication reject unauthenticated requests.

### 5.3 `test_health.py`
**Component under test:** `api/health.py`
**Total tests:** 7

Tests the health check endpoint (`/api/health`) and root endpoint (`/`). Verifies status, version, timestamp format, no-auth access, and that both endpoints return a consistent version string.

### 5.4 `test_resume.py`
**Component under test:** Resume API endpoints
**Total tests:** 43

Tests resume generation across a wide range of inputs. Covers single and multi-project resumes, personal info inclusion, format selection, missing project IDs, unauthorized access, and integration with the resume generator. Also validates stored resume creation, listing, retrieval, and item attachment.

### 5.5 `test_tasks.py`
**Component under test:** `api/tasks.py`
**Total tests:** 10

Tests the task management endpoints. Verifies task status retrieval for valid, missing, and wrong-user tasks, listing all user tasks, task cancellation (success and not-found cases), and error state handling.

### 5.6 `test_complexity_analyzer.py`
**Component under test:** `analysis/complexity_analyzer.py`
**Total tests:** 49

Tests Python and Java code complexity analysis. Covers detection of nested loops (O(n²) and O(n³)), efficient patterns (sets, dicts, generators, binary search, memoization), inefficient patterns (list membership in loops, string concatenation), Java-specific patterns (Stream API, StringBuilder, ConcurrentHashMap, TreeSet), mixed-language project analysis, score clamping, and edge cases like empty files, unicode content, and very large files.

### 5.7 `test_git_analysis.py`
**Component under test:** `analysis/git_analysis.py`
**Total tests:** 42

Tests git repository analysis using real temporary git repos. Covers solo and collaborative project detection, contribution percentage calculation, contributor sorting, target user detection (exact, case-insensitive, and partial email matching), branch and remote information extraction, edge cases (zero commits, invalid paths, corrupted repos, special characters, GitHub noreply email normalization), JSON export, language breakdown and role inference, semantic contribution split, and code ownership analysis.

### 5.8 `test_enhanced_ranking.py`
**Component under test:** Ranking algorithm
**Total tests:** 39

Tests the project scoring and ranking system. Covers date helper functions (days since, duration), score categorization into tiers (Flagship, Major, Significant, Supporting, Minor), contribution score calculation by contribution percentage, recency scoring by last-activity date, project scale scoring by commit count, collaboration scoring by contributor count, duration scoring, and the full composite score calculation with all weighted breakdown factors.

### 5.9 `test_project_analyzer.py`
**Component under test:** `analysis/project_analyzer.py`
**Total tests:** 41

Tests the `FileClassifier` module that categorizes files in a ZIP project. Covers initialization, context manager usage, directory ignore patterns (node_modules, __pycache__, .venv, build, .git), test file detection (test_ prefix, _test suffix, tests/ directory, spec files), language detection by extension (Python, JavaScript, TypeScript, Java, C++, Go, Rust), individual file classification (type, language, path, is_test, is_readme flags), full project classification results (file counts, code organization by language, metadata completeness), and error handling for nonexistent ZIPs or project paths.

### 5.10 `test_portfolio_item_generator.py`
**Component under test:** `analysis/portfolio_item_generator.py`
**Total tests:** 34

Tests the generation of portfolio items from project analysis results. Covers construction of portfolio summaries, skills extraction, tech stack identification, description generation, and edge cases with missing or incomplete analysis data.

### 5.11 `test_metadata_extractor.py`
**Component under test:** `analysis/metadata_extractor.py`
**Total tests:** 29

Tests document metadata extraction from multiple file formats (PDF, DOCX, TXT). Covers title extraction, author detection, date parsing, keyword extraction, and fallback behavior when metadata fields are missing or malformed.

### 5.12 `test_analysis_integration.py`
**Component under test:** Full analysis pipeline
**Total tests:** 19

End-to-end integration tests that exercise the full analysis workflow: uploading a ZIP, triggering analysis, and retrieving results. Also covers C++/Java OOP analysis, resume generation through the CLI, database storage, and the LLM analysis pipeline with mocked Gemini responses.

### 5.13 `test_cli_integration.py`
**Component under test:** CLI commands
**Total tests:** 27

Tests the CLI interface end-to-end. Covers signup with consent acceptance and denial, duplicate username handling, login flows (first-time with consent, returning user, invalid credentials), consent status check and update commands, analyze command with valid and invalid paths, and confirmation that unauthenticated users are blocked.

---

## 6. Test Strategies Used

The backend test suite uses several strategies to ensure correctness across normal, edge-case, and failure scenarios.

### 6.1 Unit Testing of Analysis Modules
Core analysis modules are tested in isolation by feeding in controlled inputs (code strings, ZIP files, git repos, documents) and asserting expected outputs. This confirms that algorithms behave correctly independently of the API layer.

Examples include:
- Feeding specific Python code to the complexity analyzer and checking detected patterns
- Running git analysis on a temporary repo with known commit history
- Extracting metadata from a mock PDF

### 6.2 API Endpoint Testing with TestClient
All REST API endpoints are tested using FastAPI's `TestClient`, which runs the ASGI app in-process without a real network. This allows accurate simulation of the full request/response lifecycle including middleware, authentication, and validation.

Examples include:
- Signing up a user and verifying the token
- Calling `/api/resume/generate` with valid and invalid payloads
- Confirming 401/403 responses for unauthenticated and unauthorized requests

### 6.3 Database Isolation with Temporary Fixtures
Each test that touches the database receives its own isolated SQLite database file via the `temp_db` fixture. This prevents test interference and ensures that no leftover state from one test affects another.

Examples include:
- Auth tests that create users, then log in with those users
- Analysis storage tests that write and re-read records
- User scoping tests that confirm records from one user are invisible to another

### 6.4 Mocking External Services
All external dependencies (Google Gemini API, vector database, file system paths) are mocked with `unittest.mock` so that tests run deterministically without internet access or infrastructure setup.

Examples include:
- Mocking `google.generativeai` to return fixed summaries
- Mocking `get_projects_for_user` to return a controlled project list
- Patching `Path.home()` to redirect session files to a temp directory

### 6.5 Session Simulation
The `fake_session` autouse fixture in `backend_test/conftest.py` automatically simulates a logged-in CLI session for all backend tests. This eliminates the need for each test to manually create a session and ensures test isolation from the real user's session file.

### 6.6 Integration Testing with Real Git Repos
Git analysis tests create real temporary git repositories using subprocess calls, add actual commits with known authors and messages, and then run the analysis module against them. This ensures the git analysis module works correctly with actual git output rather than mocked strings.

Examples include:
- A solo-author repo with 5 commits testing 100% contribution
- A three-author repo testing percentage calculation and contributor sorting
- A repo with GitHub noreply emails testing normalization

### 6.7 CLI Workflow Testing
Integration tests invoke the CLI functions directly (not via subprocess) and assert on return values, stdout output, and resulting database state. This validates that user-facing commands behave correctly across multi-step flows.

Examples include:
- Full signup → login → consent → analyze workflow
- Consent revocation for an already-consented user
- Analyzing a path that does not exist

### 6.8 Edge Case and Error Path Testing
Tests deliberately feed invalid, empty, null, or malformed inputs to verify that the backend does not crash and instead returns appropriate errors or fallback values.

Examples include:
- ZIP files with no Python or Java content
- Corrupted git repositories
- Resuming with project IDs that don't belong to the user
- Resume generation with no project IDs

### 6.9 Score and Algorithm Validation
Ranking, scoring, and ML prediction modules are tested with controlled inputs to verify that numerical outputs stay within expected ranges and that categorical outputs match expected tiers.

Examples include:
- Confirming a score of 80+ maps to "Flagship Project"
- Verifying that a solo contributor receives 30.0 contribution points
- Checking that very recent activity returns the maximum recency score

### 6.10 Async Task Testing
Task manager and LLM pipeline tests use `pytest-asyncio` and mocks to verify that asynchronous analysis tasks transition correctly through pending, running, and completed states, and that LLM processing is skipped when consent has not been granted.

---

## 7. Conclusion

The backend test suite provides broad and deep coverage of the capstone system's server-side logic. Across 60 test files and approximately 897 tests, it verifies critical workflows including authentication, portfolio and project management, code and git analysis, resume generation, LLM integration, role prediction, project ranking, curation, and CLI command workflows.

By combining unit tests for analysis algorithms, API endpoint tests with an in-process test client, database isolation via temporary fixtures, mocking of external services, real git repository fixtures for git analysis, and end-to-end integration tests for full workflows, the backend tests provide confidence that the system behaves correctly and safely across both normal and failure conditions.
