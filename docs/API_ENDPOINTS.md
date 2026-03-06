# API Endpoints Catalog

This document lists backend REST endpoints defined in:

- `src/backend/api/*.py` (modular routers)
- `src/backend/api_server.py` (direct app routes)

---

## Health

| Method | Endpoint |
|---|---|
| GET | `/` |
| GET | `/api/health` |

## Authentication

| Method | Endpoint |
|---|---|
| POST | `/api/auth/signup` |
| POST | `/api/auth/login` |
| POST | `/api/auth/logout` |

## Consent and Privacy

| Method | Endpoint |
|---|---|
| GET | `/api/user/consent` |
| POST | `/api/user/consent` |
| POST | `/api/privacy-consent` |

## Portfolios

| Method | Endpoint |
|---|---|
| GET | `/api/portfolios` |
| GET | `/api/portfolios/{portfolio_id}` |
| GET | `/api/portfolio/{portfolio_id}` |
| POST | `/api/portfolios/upload` |
| POST | `/api/portfolios/{portfolio_id}/add` |
| POST | `/api/portfolio/generate` |
| DELETE | `/api/portfolios/{portfolio_id}` |

## Projects and Skills

| Method | Endpoint |
|---|---|
| GET | `/api/projects` |
| GET | `/api/projects/{project_id}` |
| POST | `/api/projects/upload` |
| GET | `/api/skills` |
| POST | `/api/projects/{project_id}/thumbnail` |
| GET | `/api/projects/{project_id}/thumbnail` |
| DELETE | `/api/projects/{project_id}/thumbnail` |
| GET | `/api/projects/{project_id}/resume-items` |
| GET | `/api/projects/{project_id}/portfolio` |
| DELETE | `/api/projects/{project_id}` |
| DELETE | `/api/projects` |

## Resume

| Method | Endpoint |
|---|---|
| GET | `/api/resume/personal-info` |
| PUT | `/api/resume/personal-info` |
| DELETE | `/api/resume/personal-info` |
| POST | `/api/resume/generate` |
| GET | `/api/resume/{resume_id}` |
| POST | `/api/resume/{resume_id}/edit` |
| POST | `/api/resumes` |
| GET | `/api/resumes` |
| GET | `/api/resumes/{resume_id}` |
| PATCH | `/api/resumes/{resume_id}` |
| POST | `/api/resumes/{resume_id}/items` |

## Tasks and Admin

| Method | Endpoint |
|---|---|
| GET | `/api/tasks` |
| GET | `/api/tasks/{task_id}` |
| GET | `/api/tasks/{task_id}/status` |
| POST | `/api/admin/cleanup` |

## Analysis Pipeline

| Method | Endpoint |
|---|---|
| POST | `/api/analysis/portfolios/{portfolio_id}/reanalyze` |
| POST | `/api/analysis/quick` |
| POST | `/api/analysis/portfolios/upload` |
| GET | `/api/analysis/status` |
| POST | `/api/analysis/portfolios/{portfolio_id}/start` |
| POST | `/api/analysis/start` |
| POST | `/api/analysis/uploads/{upload_id}/start` |
| POST | `/api/analysis/uploads/{upload_id}/cleanup` |

## Curation

| Method | Endpoint |
|---|---|
| GET | `/api/curation/settings` |
| GET | `/api/curation/projects` |
| GET | `/api/curation/showcase` |
| GET | `/api/curation/skills` |
| GET | `/api/curation/attributes` |
| POST | `/api/curation/chronology` |
| POST | `/api/curation/showcase` |
| POST | `/api/curation/attributes` |
| POST | `/api/curation/order` |
| POST | `/api/curation/skills` |

---


