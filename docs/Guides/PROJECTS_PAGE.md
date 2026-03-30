# Projects Page Documentation

## Overview

The Projects page (`/projects`) is the primary interface for viewing, managing, and curating all analyzed projects. It aggregates projects across every uploaded portfolio for the authenticated user, enriches each entry with resume bullets and portfolio summaries, and provides filtering, sorting, role curation, AI analysis viewing, and thumbnail management.

---

## Route & Access

| Property | Value |
|---|---|
| **Route** | `/projects` |
| **Component file** | `src/frontend/src/ProjectsPage.jsx` |
| **Access control** | `ProtectedRoute` — unauthenticated users are redirected to `/login` |
| **Auth context** | `useAuth()` from `AuthContext` |

---

## Features

### 1. Project Listing

On load the page fetches all projects belonging to the authenticated user via `GET /api/projects`. Each project object returned by `get_user_projects()` is normalized:

- If a project is missing `composite_id`, it is derived as `{analysis_uuid}:{project_path}`.
- Two parallel enrichment calls are issued per project: `GET /api/projects/{id}/resume-items` and `GET /api/projects/{id}/portfolio`, attaching `resume_items` and `portfolio` (the `text_summary` field) to each project card.

Each project card displays:

- Project name and path
- Primary programming language
- File count
- Whether the project has tests
- Effective date range (start → end)
- Predicted or curated role with confidence
- Language and framework tag pills
- Resume bullets (expandable)
- Portfolio summary text
- Thumbnail image (if set)
- LLM or static analysis panel

---

### 2. Filtering and Sorting

All filtering and sorting operates entirely on the client side against the loaded project list.

| Control | Behavior |
|---|---|
| **Search box** | Case-insensitive substring match on project name and primary language |
| **Language dropdown** | Filter to a single primary language; populated dynamically from the loaded project list |
| **Has Tests toggle** | Filter to only projects that have detected test files |
| **Sort: Date** | Sort by effective end date, most recent first |
| **Sort: Name** | Alphabetical by project name |
| **Sort: Language** | Alphabetical by primary language |
| **Sort: File Count** | Descending by total file count |
| **Curated Order** | Sort using `custom_project_order` from curation settings (only active when the user has saved a custom order) |

---

### 3. Showcase Mode

When navigating from the Dashboard with a `showcaseProjectId` in router state (`location.state?.showcaseProjectId`), the page enters **Showcase Mode**:

- Only the highlighted project is shown.
- A banner is displayed at the top of the page indicating showcase mode is active.
- A "Show all projects" button is available to exit back to the full list.

Showcase badges (e.g. "Top 1", "Top 2", "Top 3") are displayed on project cards whose `id` is in the `showcase_project_ids` list returned by `GET /api/curation/settings`.

---

### 4. Role Curation

The Projects page integrates role prediction and manual curation per project.

- **Predicted role**: Computed during analysis; stored as `predicted_role` with an associated `predicted_role_confidence` (0–1 float).
- **Curated role**: A user-overridden role label stored as `curated_role`. When set, the curated role is displayed in place of the predicted role without a confidence indicator.
- **Available roles**: Fetched on load via `GET /api/curation/roles`. The dropdown is populated from this list.
- **Saving/clearing**: Selecting a role from the dropdown and confirming calls `POST /api/curation/role` with `{ project_id, curated_role }`. Setting `curated_role` to `null` clears the override and restores the predicted role.

---

### 5. LLM Analysis Panel (`LlmAnalysisPanel`)

Each project card contains a collapsible analysis panel. The panel behaves differently based on the `analysis_type` field of the project.

#### LLM Projects (`analysis_type === 'llm'`)

- The panel header shows **"AI Analysis"** with a robot emoji.
- On expansion, `GET /api/projects/{id}/llm-analysis` is called (using the integer `id`) to retrieve the LLM summary markdown.
- The markdown is parsed into sections by `parseLlmSections()`, which splits on numbered headers (`## 1. Title`) and plain headers (`## Title`).
- Sections are bucketed into analysis modules by `buildModuleSectionMap()`:

| Module Key | Label | Matched by keywords in section title |
|---|---|---|
| `architecture` | Architecture & Patterns | architect, pattern, data flow |
| `complexity` | Complexity & Algorithms | complex, algorithm, concurren |
| `security` | Security & Defensive Coding | secur, defensive |
| `skills` | Soft Skills & Maturity | skill, maturity, soft |
| `domain` | Domain-Specific Competency | domain, competenc |
| `resume` | Resume & Portfolio Artifacts | resume, career, portfolio artifact |

- A multi-select dropdown lets the user choose which module categories to display. Clicking **"Display"** renders the selected sections using the `SimpleMarkdown` renderer.
- The overview section (section number ≤ 1) is always shown above the module picker.

#### Non-LLM Projects

- The panel header shows **"Analysis Output"** with a gear emoji.
- A static key–value grid is rendered from available project fields such as file count, language breakdown, test detection, and complexity scores.
- No API call is made on expansion.

---

### 6. Thumbnail Management

Every project can have a custom thumbnail image associated with it.

- **Display**: On load, `GET /api/projects/{composite_id}/thumbnail` is called. A `204 No Content` response means no thumbnail is set. When a thumbnail exists, the response is a raw image file which is loaded into a blob URL via `URL.createObjectURL`.
- **Upload**: A file picker (accepts `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`) sends a `multipart/form-data` POST to `POST /api/projects/{composite_id}/thumbnail`. The server validates file type, enforces a 5 MB size limit, saves the file to `uploads/project_thumbnails/` under a UUID-based filename, and updates the database record. The previous thumbnail file on disk is deleted atomically.
- **Remove**: A remove button sends `DELETE /api/projects/{composite_id}/thumbnail`. The server deletes the file from disk and clears `thumbnail_image_path` in the database.
- **Blob URL cleanup**: All blob URLs are revoked via `URL.revokeObjectURL` when a thumbnail is updated or removed to prevent memory leaks.

The `composite_id` used for thumbnail routes is URL-encoded and has the format `{analysis_uuid}:{project_path}`. The colon separator is required; requests without it are rejected with `400 Bad Request`.

---

### 7. Project Deletion

Two deletion operations are supported, both triggered through confirmation dialogs.

| Action | API Call | Behavior |
|---|---|---|
| Delete single project | `DELETE /api/projects/{id}` (integer id) | Removes the project and all associated data for the authenticated user |
| Delete all projects | `DELETE /api/projects` | Removes every project for the user; returns a count of deleted projects |

After a successful deletion the project list is refreshed.

---

### 8. Empty and Error States

- **Loading state**: A spinner or loading indicator is shown while the initial project list is being fetched.
- **Global error banner**: If the initial fetch fails, a dismissible error banner is displayed at the top of the page.
- **Empty state**: When the project list is empty (no results, or all deleted), an empty state message is shown with a link back to the Dashboard to upload a new portfolio.

---

## API Endpoints

All requests are made to `baseURL = /api`. Authentication is handled via a JWT bearer token managed by `AuthContext`.

| Method | Path | ID Format | Description |
|---|---|---|---|
| `GET` | `/api/projects` | — | List all projects for authenticated user |
| `GET` | `/api/projects/{id}/resume-items` | integer | Resume bullet points for a project |
| `GET` | `/api/projects/{id}/portfolio` | integer | Portfolio summary (`text_summary`) for a project |
| `GET` | `/api/projects/{id}/llm-analysis` | integer | LLM markdown summary for a project |
| `GET` | `/api/projects/{composite_id}/thumbnail` | `uuid:path` | Retrieve thumbnail image (204 if none) |
| `POST` | `/api/projects/{composite_id}/thumbnail` | `uuid:path` | Upload a new thumbnail (multipart/form-data) |
| `DELETE` | `/api/projects/{composite_id}/thumbnail` | `uuid:path` | Remove thumbnail |
| `DELETE` | `/api/projects/{id}` | integer | Delete a single project |
| `DELETE` | `/api/projects` | — | Delete all projects for authenticated user |
| `GET` | `/api/curation/settings` | — | Retrieve `showcase_project_ids`, `custom_project_order` |
| `GET` | `/api/curation/roles` | — | List available role labels for curation dropdown |
| `POST` | `/api/curation/role` | — | Save or clear a curated role for a project |

> **Note on ID types**: Delete, resume-items, portfolio, and LLM analysis routes use the integer database `id`. Thumbnail routes and the project detail route use the string `composite_id` in the form `{analysis_uuid}:{project_path}`, URL-encoded when embedded in a path segment.

---

## Data Model

### Project Object (frontend runtime shape)

```js
{
  id: number,                        // Integer primary key (DB)
  analysis_id: number,               // FK to analyses table
  analysis_uuid: string,             // UUID of parent portfolio analysis
  composite_id: string,              // "{analysis_uuid}:{project_path}"
  analysis_type: "llm" | "static",   // Determines analysis panel behaviour

  project_name: string,
  project_path: string,
  primary_language: string | null,
  total_files: number,
  has_tests: boolean,

  predicted_role: string | null,
  predicted_role_confidence: number | null,  // 0.0 – 1.0
  curated_role: string | null,

  languages: { [language: string]: number }, // line counts
  frameworks: string[],

  effective_project_start_date: string | null,  // ISO date
  effective_project_end_date: string | null,
  effective_last_commit_date: string | null,
  effective_last_modified_date: string | null,

  // Enriched after load
  resume_items: ResumeItem[],
  portfolio: string | null,          // text_summary from portfolio table
}
```

### SQLite Tables (backend)

| Table | Purpose |
|---|---|
| `analyses` | Parent portfolio/upload records, keyed by `analysis_uuid` |
| `projects` | One row per project; includes all stat fields and `thumbnail_image_path` |
| `project_languages` | Per-project language breakdown (language, line count) |
| `project_frameworks` | Per-project detected frameworks |
| `project_skills` | Per-project extracted skills |
| `resume_items` | Generated resume bullet points linked to a project |
| `user_curation_settings` | Per-user `showcase_project_ids`, `custom_project_order`, `highlighted_skills` |
| `project_chronology_corrections` | User-overridden date fields per project |

---

## Frontend Architecture

### State Management

The page uses **React local state only** — no Redux, Zustand, or React Query.

| State variable | Purpose |
|---|---|
| `projects` | Full loaded project list (enriched) |
| `filteredProjects` | Derived from `projects` after applying search, language, test, and sort controls |
| `loading` | Boolean — controls initial loading indicator |
| `error` | Global fetch error message string |
| `showcaseMode` / `showcaseProjectId` | Showcase filter driven by router state |

### Key Hooks

- `useAuth()` — provides the authenticated username and token.
- `useNavigate()` / `useLocation()` — routing and showcase state extraction.
- `useRef()` — dropdown close-on-outside-click for the analysis module selector.

### Internal Components

| Component | Location | Purpose |
|---|---|---|
| `SimpleMarkdown` | Inline in `ProjectsPage.jsx` | Lightweight markdown renderer supporting headings (h1–h4), bold, inline code, fenced code blocks, ordered and unordered lists |
| `LlmAnalysisPanel` | Inline in `ProjectsPage.jsx` | Collapsible panel; lazy-loads LLM data on first expand; multi-select module picker |
| `Navigation` | `src/frontend/src/components/Navigation.jsx` | App shell navigation bar |

### Service Layer

API calls are made through two objects from `src/frontend/src/services/api.js`:

- **`projectsAPI`**: `getProjects`, `getProjectById`, `getResumeItems`, `getPortfolioItem`, `getLlmAnalysis`, `getThumbnail`, `uploadThumbnail`, `deleteThumbnail`, `deleteProject`, `deleteAllProjects`
- **`curationAPI`**: `getSettings`, `getAvailableRoles`, `saveRole`

---

## Backend Architecture

### Router Registration

The projects router is registered in `api_server.py`:

```python
from backend.api.projects import router as projects_router
app.include_router(projects_router)
```

Additional project-related endpoints (resume-items, portfolio, delete single, delete all) are registered directly on the `app` instance in `api_server.py` rather than on the router.

### Authentication

All endpoints use `Depends(verify_token)` from `backend.api.auth`, which validates the JWT and returns the `username` claim. All database queries are scoped to that username, preventing cross-user data access.

### Thumbnail File Handling

- Storage path: `src/backend/uploads/project_thumbnails/`
- Filenames: UUID v4 + original extension (e.g. `3f1a2b4c-....png`)
- Allowed types: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`
- Max size: **5 MB**
- Path traversal protection: resolved paths are validated to remain within `THUMBNAIL_UPLOAD_DIR` before any read, write, or delete operation.
- Old thumbnail cleanup: when a new thumbnail is uploaded, the previous file is deleted from disk immediately after the database record is updated successfully.

### Curation Logic

The `get_user_projects()` function in `src/backend/curation.py` is responsible for assembling the enriched project list returned by `GET /api/projects`. It:

1. Queries the `projects` table joined with `analyses` for the given username.
2. Attaches language, framework, and skill data from their respective junction tables.
3. Applies chronology corrections from `project_chronology_corrections` to compute effective dates.
4. Merges `curated_role` over `predicted_role` where set.
5. Returns the ordered list respecting `custom_project_order` from `user_curation_settings` when that setting is non-empty.

---

## Testing

| Test file | Coverage |
|---|---|
| `src/frontend/src/tests/ProjectsPage.test.jsx` | Unit tests for core page rendering, filtering, and deletion flows |
| `src/frontend/src/tests/ProjectsPageShowcase.test.jsx` | Showcase mode rendering and banner display |
| `src/tests/api_test/test_projects.py` | Backend endpoint tests for list, detail, delete, and upload |
| `src/tests/api_test/test_project_thumbnails.py` | Thumbnail upload, retrieval, replacement, and deletion |
