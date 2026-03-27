# Blume API - Reference

**Base URL:** `http://localhost:8000/api`  
**Version:** 2.0.0

---

## Authentication

- **POST /api/auth/signup**
  - Registers a new user.
  - Request: `{ "username": str, "password": str }`
  - Response: `{ "access_token": str, "token_type": "Bearer", "username": str }`
  - No authentication required.

- **POST /api/auth/login**
  - Logs in a user and returns access token.
  - Request: `{ "username": str, "password": str }`
  - Response: `{ "access_token": str, "token_type": "Bearer", "username": str }`
  - No authentication required.

- **POST /api/auth/logout**
  - Logs out and invalidates token.
  - Auth: Bearer token required.
  - Response: `{ "message": "Successfully logged out" }`

---

## Health & Root

- **GET /api/health**
  - Health check endpoint.
  - Auth: Not required.
  - Response: `{ "status": "healthy", "version": "2.0.0", "timestamp": str }`

- **GET /**
  - Root API information.
  - Auth: Not required.
  - Response: `{ "name": "Blume API", "version": "2.0.0", "docs": "/docs", "health": "/api/health" }`

---

## Portfolios

- **GET /api/portfolios**
  - List all portfolios for authenticated user.
  - Auth: Bearer token required.
  - Response: Array of portfolio summaries (analysis_uuid, zip_file, analysis_timestamp, total_projects, analysis_type).

- **GET /api/portfolios/{portfolio_id}**
  - Get detailed information for a portfolio.
  - Auth: Bearer token required.
  - Response: Complete portfolio details including projects and skills.

- **POST /api/portfolios/upload**
  - Upload new portfolio (ZIP file). Returns task_id for async processing.
  - Auth: Bearer token required.
  - Request: multipart/form-data with `file` (ZIP) and optional `analysis_type` (llm or non_llm, default: llm).
  - Response: `{ "task_id": str, "status": "processing", ... }`
  - Status: 202 Accepted.

- **POST /api/portfolios/{portfolio_id}/add**
  - Incrementally add projects to existing portfolio.
  - Auth: Bearer token required.
  - Request: multipart/form-data with `file` (ZIP).
  - Response: `{ "task_id": str, "status": "processing", ... }`
  - Status: 202 Accepted.

- **DELETE /api/portfolios/{portfolio_id}**
  - Delete a portfolio and all associated data.
  - Auth: Bearer token required.
  - Response: `{ "message": "Portfolio deleted successfully" }`

- **POST /api/portfolio/generate**
  - Generate formatted portfolio document.
  - Auth: Bearer token required.
  - Request: `{ "portfolio_id": str }`
  - Response: Portfolio items with metadata.

---

## Projects

- **GET /api/projects**
  - List all projects across all portfolios.
  - Auth: Bearer token required.
  - Response: `{ "username": str, "total_projects": int, "projects": [...] }`

- **GET /api/projects/{portfolio_uuid}:{project_path}**
  - Get detailed project information.
  - Auth: Bearer token required.
  - Response: Project details with metadata and thumbnail URL.

- **GET /api/skills**
  - Get aggregated skills across all projects.
  - Auth: Bearer token required.
  - Response: `{ "username": str, "total_skills": int, "skills": [...] }` (sorted by count).

- **POST /api/projects/{project_id}/thumbnail**
  - Upload project thumbnail image.
  - Auth: Bearer token required.
  - Request: multipart/form-data with `file` (JPG, PNG, GIF, WebP, max 5MB).
  - Response: `{ "message": "Thumbnail uploaded", "thumbnail_url": str, "project_id": str }`

- **GET /api/projects/{project_id}/thumbnail**
  - Get project thumbnail image.
  - Auth: Bearer token required.
  - Response: Image file.

- **DELETE /api/projects/{project_id}/thumbnail**
  - Delete project thumbnail.
  - Auth: Bearer token required.
  - Response: `{ "message": "Thumbnail deleted successfully" }`

---

## Analysis

- **POST /api/analysis/quick**
  - Quick analysis on ZIP file without storing as portfolio.
  - Auth: Bearer token required.
  - Request: multipart/form-data with `file` (ZIP) and optional `analysis_type`.
  - Response: `{ "status": "completed", "results": {...} }` (synchronous).

- **GET /api/analysis/status**
  - Get analysis pipeline status and statistics.
  - Auth: Bearer token required.
  - Response: `{ "status": "operational", "statistics": { "total_analyses": int, "completed": int, ... } }`

- **POST /api/analysis/portfolios/{portfolio_id}/start**
  - Start/restart analysis on existing portfolio.
  - Auth: Bearer token required.
  - Request: `{ "analysis_type": "llm" or "non_llm" }`
  - Response: `{ "task_id": str, "status": "pending", ... }`
  - Status: 202 Accepted.

- **POST /api/analysis/uploads/{upload_id}/start**
  - Start analysis for specific upload.
  - Auth: Bearer token required.
  - Response: `{ "task_id": str, "status": "pending", ... }`
  - Status: 202 Accepted.

- **POST /api/analysis/uploads/{upload_id}/cleanup**
  - Clean up upload and temporary files.
  - Auth: Bearer token required.
  - Response: `{ "message": "Upload cleaned up successfully" }`

---

## Resume

- **POST /api/resume/generate**
  - Generate resume from selected portfolio(s).
  - Auth: Bearer token required.
  - Request: `{ "portfolio_ids": [str], "format": "markdown|pdf|latex", "include_skills": bool, "include_projects": bool, "max_projects": int, "personal_info": {...} }`
  - Response: `{ "resume_id": str, "format": str, "content": str, "metadata": {...} }`

- **GET /api/resume/personal-info**
  - Get saved personal information.
  - Auth: Bearer token required.
  - Response: `{ "personal_info": {...} }`

- **PUT /api/resume/personal-info**
  - Save or update personal information.
  - Auth: Bearer token required.
  - Request: `{ "personal_info": { "name": str, "email": str, "phone": str, ... } }`
  - Response: `{ "ok": true }`

- **POST /api/resumes**
  - Store a new resume.
  - Auth: Bearer token required.
  - Request: `{ "title": str, "format": "markdown|text", "content": str }`
  - Response: Stored resume object with id, created_at, updated_at.
  - Status: 201 Created.

- **GET /api/resumes**
  - List all stored resumes.
  - Auth: Bearer token required.
  - Response: Array of stored resumes.

- **GET /api/resumes/{resume_id}**
  - Get specific stored resume.
  - Auth: Bearer token required.
  - Response: Resume object with content and metadata.

- **POST /api/resume/{resume_id}/edit**
  - Edit stored resume content.
  - Auth: Bearer token required.
  - Request: `{ "content": str }`
  - Response: Updated resume object.

---

## Curation

- **GET /api/curation/settings**
  - Get user's curation settings.
  - Auth: Bearer token required.
  - Response: `{ "user_id": str, "comparison_attributes": [...], "showcase_project_ids": [...], "custom_project_order": [...], "highlighted_skills": [...] }`

- **GET /api/curation/projects**
  - Get all projects with curation metadata and effective dates.
  - Auth: Bearer token required.
  - Response: Array of projects with languages, frameworks, dates.

- **GET /api/curation/showcase**
  - Get user's showcase projects (typically 3 or fewer).
  - Auth: Bearer token required.
  - Response: Array of selected showcase projects.

- **GET /api/curation/skills**
  - Get all available skills (alphabetically sorted).
  - Auth: Bearer token required.
  - Response: Array of skill strings.

- **GET /api/curation/attributes**
  - Get available comparison attributes.
  - Auth: Bearer token required.
  - Response: Array of `{ "key": str, "description": str, "is_default": bool }`

- **POST /api/curation/chronology**
  - Save project date corrections.
  - Auth: Bearer token required.
  - Request: `{ "project_id": int, "project_start_date": str, "project_end_date": str, ... }` (ISO 8601 format).
  - Response: `{ "message": "Project chronology updated successfully" }`

- **POST /api/curation/showcase**
  - Set showcase projects (max 3).
  - Auth: Bearer token required.
  - Request: `{ "project_ids": [int, ...] }`
  - Response: `{ "message": "Showcase projects set successfully" }`

- **POST /api/curation/attributes**
  - Set comparison attributes.
  - Auth: Bearer token required.
  - Request: `{ "attributes": [str, ...] }` (min 1).
  - Response: `{ "message": "Comparison attributes set successfully" }`

- **POST /api/curation/order**
  - Set custom project display order.
  - Auth: Bearer token required.
  - Request: `{ "project_ids": [int, ...] }`
  - Response: `{ "message": "Project order set successfully" }`

- **POST /api/curation/skills**
  - Set highlighted skills.
  - Auth: Bearer token required.
  - Request: `{ "skills": [str, ...] }`
  - Response: `{ "message": "Highlighted skills set successfully" }`

---

## Tasks

- **GET /api/tasks/{task_id}**
  - Get task status and progress.
  - Auth: Bearer token required.
  - Response: `{ "task_id": str, "status": "pending|running|completed|failed", "progress": 0-100, "error": str or null, ... }`

- **GET /api/tasks**
  - List user's tasks (most recent first).
  - Auth: Bearer token required.
  - Query: `?limit=50` (optional).
  - Response: Array of task status objects.

- **POST /api/admin/cleanup**
  - Admin endpoint to clean up old completed tasks.
  - Auth: Bearer token required.
  - Response: `{ "message": "Cleanup check completed", "total_tasks": int, "completed_tasks": int }`

---

## Consent

- **GET /api/user/consent**
  - Get user consent status.
  - Auth: Bearer token required.
  - Response: `{ "has_consented": bool, "message": str }`

- **POST /api/user/consent**
  - Save user consent.
  - Auth: Bearer token required.
  - Request: `{ "has_consented": bool }`
  - Response: `{ "has_consented": bool, "message": str }`

- **POST /api/privacy-consent**
  - Save privacy consent.
  - Auth: Bearer token required.
  - Request: `{ "has_consented": bool }`
  - Response: `{ "has_consented": bool, "message": str }`

---

## Common Workflows

**Upload & Analyze Portfolio:**
1. `POST /api/portfolios/upload` → Returns `task_id`
2. `GET /api/tasks/{task_id}` → Poll until `complete` or `failed`
3. `GET /api/portfolios/{portfolio_id}` → Access results

**Generate Tailored Resume:**
1. `PUT /api/resume/personal-info` → Save personal details
2. `POST /api/curation/showcase` → Select top 3 projects
3. `POST /api/resume/generate` → Generate resume

**Customize Portfolio:**
1. `GET /api/curation/projects` → List projects
2. `POST /api/curation/showcase` → Select showcase
3. `POST /api/curation/order` → Set order
4. `POST /api/curation/skills` → Highlight skills

---

## HTTP Status Codes

- **200 OK** - Successful request
- **201 Created** - Resource created
- **202 Accepted** - Async operation queued
- **400 Bad Request** - Invalid parameters
- **401 Unauthorized** - Missing/invalid token
- **403 Forbidden** - Consent required or insufficient permissions
- **404 Not Found** - Resource not found
- **409 Conflict** - Resource already exists
- **413 Payload Too Large** - File too large
- **500 Internal Server Error** - Server error

---

## Task Status Values

- `pending` - Task queued, not started
- `running` - Task currently processing
- `completed` - Task finished successfully
- `failed` - Task encountered error

---

## Analysis Types

- `llm` - Uses LLM for detailed analysis (slower, more thorough)
- `non_llm` - Quick analysis without LLM (faster)
