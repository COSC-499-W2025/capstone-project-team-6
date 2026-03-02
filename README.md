# Team Contract
Team Contract can be found [here](docs/Capstone%20Team%206%20Contract.pdf).


Google Docs link to the team contract: https://docs.google.com/document/d/1QnISyjm78uy_NUFr6qpKbF3jwdyAV0nqgGjOC47GHT8/edit?usp=sharing

Google Drive link to the test zip files: https://drive.google.com/drive/folders/1OcQmw6caoHSFL_DtbaS9mrlM4EpTM9vs?usp=drive_link

# Project Work Breakdown Structure 

## Level-1 Overview
- **Project Management**
- **Milestone 1 — Core Parsing & Text Outputs (Oct–Dec 07)**
- **Milestone 2 — Service/API + Human-in-the-Loop (Jan–Mar 01)** *(Subject to change)*
- **Milestone 3 — Front-End (Mar–Apr 05)** *(Subject to change)*
- **Cross-Cutting Quality:** Testing, Security & Privacy, Documentation  
- **Project Closure**

---

## 1. Project Management
### 1.1 Initiation & Scope Control
- Define success metrics.

### 1.2 Planning
- Timeline and task assignments.

### 1.3 Stakeholder & Ethics Review
- Define data-use boundaries and privacy considerations.

### 1.4 Standups & Reviews
- Weekly meetings and milestone demos.

### 1.5 Tracking & Reporting
- Maintain weekly logs.

---

## 2. Milestone 1 — Core Parsing & Text Outputs (Oct–Dec 07)

**Goal:**  
Build the Python core that takes as input a zipped folder, parses artifacts, derives projects/skills/metrics, and produces TXT/CSV/JSON outputs.  
Store results in a local database, enable retrieval and secure deletion, and ensure user data privacy.

### 2.1 System Architecture & Foundations
- **2.1.1** Architecture design (Python backend, module boundaries, DFD)
- **2.1.2** Local DB schema (SQL): projects, artifacts, sessions, skills, summaries
- **2.1.3** Configuration management: user settings stored for reuse

### 2.2 Data Access, Consent & Modes
- **2.2.1** Consent flow: explicit permission before any access
- **2.2.2** Upload Mode: validate zipped folder; return error on wrong format
- **2.2.3** Laptop Scan list: folder allow/deny lists; OS checks (Windows/macOS)

### 2.3 Parsers & Extractors
- **2.3.1 Code Analysis**
  - Language/framework detection  
  - Lines of code  
  - Functions/classes  
  - Repository mining  
  - Individual contribution heuristics
- **2.3.2 Document Parsing**
  - PDF, DOC, DOCX, Text  
  - Metadata extraction
- **2.3.3 Media/Other Artifacts**
  - Basic metadata (created, modified, authorship)

### 2.4 Project & Skill Inference
- **2.4.1** Project grouping: distinguish individual vs. collaborative projects  
- **2.4.2** Contribution inference: commits for collaboration repos  
- **2.4.3** Metrics engine: duration and frequency of activity types (code/test/design/doc)  
- **2.4.4** Skill extraction: keywords and skills developed during project

### 2.5 External Services Policy & Fallbacks
- **2.5.1** Permission prompt for LLM/external calls + privacy implications  
- **2.5.2** Offline/alternative analyses if external use not permitted

### 2.6 Ranking, Summaries & Outputs
- **2.6.1** Project importance ranking (based on contributions/impact)  
- **2.6.2** Summaries for top-ranked projects  
- **2.6.3** Projects timeline and skills progression list  
- **2.6.4** Output generators: CSV/JSON/plain-text for all key info  
- **2.6.5** Store & retrieve:
  - Portfolio items from DB  
  - Résumé items from DB

### 2.7 Secure Data Deletion
- **2.7.1** Delete insights/data with verification

### 2.8 Performance & Resource Control
- **2.8.1** Processing-time: target ~5 minutes ideal time  
- **2.8.2** Memory/permission edge cases: resumable or partial scans

#### Milestone-1 Deliverables
- M1 architecture diagram & DB schema  
- DFD  
- WBS  
- Parsers (code/docs) + metrics/skills extraction  
- Ranking and summaries in chronological lists  
- Text/CSV/JSON outputs  
- Secure deletion function  
- Unit/integration tests for code  

---

## 3. Milestone 2 — Service/API + Human-in-the-Loop (Jan–Mar 01)

**Goal:**  
Run as a service (API). Add human-in-the-loop curation: incremental ingest, deduplication, selection, corrections, and customizable résumé/portfolio text.
Milestone 2 uses a **FastAPI** backend service to facilitate communication between the front-end and back-end through documented REST endpoints and contracts.

### 3.1 Service Enablement
- **3.1.1** API design & contracts: define request/response schemas for ingest, curation, and text rendering workflows. Low-level: Pydantic models validate payload fields and FastAPI auto-generates OpenAPI docs from these schemas.  
- **3.1.2** Orchestration & jobs: async processing for ingest/parse/analyze so users can submit uploads and poll job status. Low-level: upload requests enqueue a background job record, and workers update a persisted job state machine (`queued` -> `running` -> `done`/`failed`).  
- **3.1.3** Auth/session model (local profile): local user profile/session context used to isolate and persist each user’s portfolio state. Low-level: each request carries a session/profile identifier used as a partition key in database reads/writes.

### 3.2 Incremental & Deduplicated Ingest
- **3.2.1** Add new zipped folders into existing portfolio: allow incremental ingestion by uploading additional ZIP folders later to enrich the same portfolio/résumé record. Low-level: new artifacts are extracted, normalized, and merged into the existing portfolio graph without overwriting curated fields unless explicitly requested.  
- **3.2.2** Duplicate detection & single-instance storage: detect duplicate files (e.g., hash/signature checks) and keep one canonical stored copy while linking it to all relevant projects. Low-level: a content hash index maps identical files to one artifact ID, and project records store references to that shared artifact.

### 3.3 Human-in-the-Loop Curation
- **3.3.1** User controls: choose information to represent, including project re-ranking, chronology corrections, project-comparison attributes, skills to highlight, and projects selected for showcase. Low-level: curation updates are stored as explicit override fields layered on top of auto-extracted data.  
- **3.3.2** Role attribution: capture and persist the user’s key role for each project. Low-level: role data is stored in a dedicated project-role field and exposed through project read/write APIs.  
- **3.3.3** Evidence linking: attach evidence of success (metrics, feedback, evaluations) to specific projects for transparent justification. Low-level: evidence entries are stored as typed child records linked by `project_id` with optional source metadata.  
- **3.3.4** Project thumbnail association: allow users to assign a portfolio image to a project as its thumbnail. Low-level: uploaded image metadata is validated and the selected image URI/artifact ID is saved on the project record.  
- **3.3.5** Save customizations: persist curated showcase-project settings and customized résumé-item wording per project. Low-level: showcase flags and résumé text variants are versioned in curation tables so they survive re-ingest.  
- **3.3.6** Display textual views: render project text in two contexts—portfolio showcase view and résumé-item view. Low-level: renderer endpoints compose structured project fields with curation overrides into deterministic text templates for each output mode.

### 3.4 FastAPI APIs & Endpoints (High-Level)
- `GET /health` — service health check.
- `POST /api/v1/portfolios` — create a new portfolio/résumé workspace.
- `GET /api/v1/portfolios/{portfolio_id}` — retrieve portfolio metadata and current curation state.
- `POST /api/v1/portfolios/{portfolio_id}/ingest` — upload initial ZIP or incremental ZIP for additional information.
- `GET /api/v1/jobs/{job_id}` — check async ingest/parse/analyze job status.
- `GET /api/v1/portfolios/{portfolio_id}/projects` — list projects extracted for the portfolio.
- `PATCH /api/v1/projects/{project_id}/ranking` — update project ordering/rank.
- `PATCH /api/v1/projects/{project_id}/chronology` — correct project timeline/chronology fields.
- `PATCH /api/v1/projects/{project_id}/comparison-attributes` — update attributes used for project comparison.
- `PATCH /api/v1/projects/{project_id}/skills` — select and highlight skills for the project.
- `PATCH /api/v1/projects/{project_id}/role` — set user role attribution for the project.
- `PATCH /api/v1/projects/{project_id}/evidence` — attach/update success evidence (metrics/feedback/evaluation).
- `PATCH /api/v1/projects/{project_id}/thumbnail` — associate a portfolio image thumbnail with a project.
- `PATCH /api/v1/portfolios/{portfolio_id}/showcase` — choose and save showcase-project customization.
- `PATCH /api/v1/projects/{project_id}/resume-wording` — customize and save résumé-item wording.
- `GET /api/v1/projects/{project_id}/render/portfolio-text` — get textual portfolio showcase rendering.
- `GET /api/v1/projects/{project_id}/render/resume-text` — get textual résumé-item rendering.

#### Milestone-2 Deliverables
- Running local service with documented API  
- Incremental ingest + deduplication  
- Full HIL curation flows & saved states  
- Textual display endpoints for portfolio/résumé items  
- API/integration/UX validation tests  

---

## 4. Milestone 3 — Front-End (Mar–Apr 05)

**Goal:**  
Build the UI to consume the service. Generate one-page résumé and web-portfolio views with private/public modes.

### 4.1 Front-End Foundations
- **4.1.1** Tech selection (Electron+React or web stack)  
- **4.1.2** UI kit, routing, state, theming  

### 4.2 Résumé Generator (One-Pager)
- **4.2.1** Education/Awards section  
- **4.2.2** Skills by expertise level  
- **4.2.3** Projects highlighting contributions/impact  
- **4.2.4** Export (PDF/HTML)

### 4.3 Web Portfolio
- **4.3.1** Skills timeline (learning progression)  
- **4.3.2** Activity heatmap (productivity over time)  
- **4.3.3** Top-3 project showcases (process & evolution)  
- **4.3.4** Dashboard modes:  
  - Private (interactive customization)  
  - Public (search/filter only)

#### Milestone-3 Deliverables
- Front-end app integrated with API  
- One-page résumé generator  
- Portfolio with timeline, heatmap, showcases  
- Private/public dashboard modes  
- UI tests & demo  

---

## 5. Cross-Cutting Quality

### 5.1 Testing & QA
- **5.1.1** Unit tests (pytest)  
- **5.1.2** Integration & contract tests (API)  
- **5.1.3** Parser correctness suites (golden files)  
- **5.1.4** Performance tests (processing time)  
- **5.1.5** Security/privacy tests (consent, data at rest)

### 5.2 Security & Privacy
- **5.2.1** Local-only encrypted storage  
- **5.2.2** Permission gating & audit logs for deletion  
- **5.2.3** External-service consent & redaction paths  

### 5.3 Documentation & DevEx
- **5.3.1** Developer guide: setup, scripts, data contracts  
- **5.3.2** User guide: consent, modes, exports, deletion  
- **5.3.3** Architecture & ADRs  
- **5.3.4** Demo scripts & milestone readouts  

---

## 6. Project Closure
- **6.1** Final acceptance & rubric mapping  
- **6.2** Post-mortem & lessons learned  
- **6.3** Handover: code, docs, demo assets  

---

## Assumptions
- Milestone dates are hard boundaries for acceptance demos.  
- Python is mandated for M1 & M2 core; stack may expand in M3.  
- No cloud persistence required; local-first with encryption.  
- Linux desktop support is out of scope initially (per proposal).





 # Data Flow Diagram (DFD Level 1)

## Overview
This DFD shows how data flows between the user, system processes, local storage, and output in the **Mining Digital Work Artifacts** system.

![Data Flow Diagram](docs/Images/DFD1.png)

## Entities
- **User** – logs in, uploads files, views dashboard, and can request data deletion or exports.  
- **Export Destination** – receives final exported outputs.

---

## Processes
- **P1 – Login**  
  Load user configurations and start session.

- **P2 – Upload**  
  Upload zipped folder and give consent; store data in local encrypted DB.

- **P3 – File Sorting**  
  Discard irrelevant files and pass relevant ones for analysis.

- **P4 – Analysis**  
  Analyze files (code or non-code), extract metadata, optionally use LLM, and prepare summaries for storage.

- **P5 – Data Deletion**  
  Handle user’s data wipe requests and remove logs and stored data.

- **P4 (continued) – Display Dashboard Output**  
  Present analyzed results, logs, and visualizations; allow export.

---

## Data Stores
- **D1 – Local Encrypted DB**  
  Stores user data, uploaded files, and analysis results.  

- **D2 – Logs and Scan Receipts**  
  Stores logs, receipts, and deletion confirmations.







