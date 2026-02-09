# Team Log – Team 6

**Work Performed:** **Jan 26th – Feb 8th**

---

## Milestone Goals Recap

### Features in Project Plan for This Milestone

- Improve **Milestone 2 readiness** by expanding the end-to-end feature set and polishing the user experience:
  - Strengthen **frontend usability** for peer testing + heuristic evaluation feedback
  - Expand project management UX (upload, analyze, browse, curate)
  - Support richer **portfolio/resume workflows** (stored resumes, portfolio dashboard, generation-ready data)
- Improve **system stability + test coverage**
  - Add/expand backend + frontend tests to prevent regressions
  - Validate flows through manual testing and peer testing sessions
  - Identify and address cross-platform inconsistencies (Mac/Windows)

### Associated Tasks / PRs Touched This Period

- **Portfolio Curation (UI + persistence scaffolding)**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/368

- **Projects Page Filtering / Searching / Sorting**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/362

- **Role Curation (CLI + persistence + tests)**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/342

- **Upload → Analyze workflow integration**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/364

- **Project Thumbnail Upload UI + Upload Page**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/354
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/333

- **Portfolio Page wiring + regression tests**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/340

- **Stored Resume Support + Resume/Portfolio Enhancements**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/352
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/359

- **Consent + Delete workflows + project ID migration**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/348
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/345
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/338
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/350

---

## Team Members

- **maddysam356** → Mandira Samarasekara  
- **aakash-tir** → Aakash Tirathdas  
- **MithishR** → Mithish Ravisankar Geetha  
- **anshr18** → Ansh Rastogi  
- **HarjotSahota** → Harjot Sahota  
- **mgjim101** → Mohamed Sakr  

---

## Completed Tasks

### Mandira Samarasekara (**maddysam356**)

- **Task:** Portfolio Curation infrastructure (Curate page + persistent preferences)
  **Description:** Implemented a dedicated **Curation** page that allows users to customize how their work is presented through a structured 5-tab workflow: selecting **Top 3 showcase projects**, choosing **comparison attributes**, curating **highlighted skills**, correcting **project chronology**, and defining **custom project ordering**. Added validation limits, loading states, and active-tab persistence. Integration into portfolio/resume generation is intentionally deferred.
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/368

- **Task:** Projects page filtering, searching, and sorting
  **Description:** Added full Projects page controls for **search**, **language filtering**, **test status filtering**, and **sorting** (date, name, language, file count), including filtered counts, a clear-filters reset, supporting API helpers, and comprehensive frontend test coverage.
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/362

- **Task:** Role curation workflow (CLI + persistence + tests)
  **Description:** Implemented a role curation system allowing users to override predicted roles through an interactive CLI using preset options or fully custom roles. Ensured user ownership enforcement, DB persistence for curated values, and robust test coverage across edge cases and authorization rules.
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/342

- **Task:** Peer testing + heuristic evaluation participation and synthesis
  **Description:** Participated in peer testing and heuristic evaluation activities, identified UI refinement opportunities, and contributed feedback to guide UX improvements and prioritization. Completed extensive PR review and hands-on validation to reduce integration risk.

- **Task:** Reviewed PRs  
  **Links:**
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/356
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/354
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/348
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/340
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/338
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/322
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/318
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/317
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/313
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/308

- **Issues:**
<img width="642" height="92" alt="image" src="https://github.com/user-attachments/assets/d5c81cfa-adde-47d4-a4e1-f8e238bd1d2c" />
<img width="676" height="427" alt="image" src="https://github.com/user-attachments/assets/b75404b1-597e-4817-9d67-46906b3112aa" />




---

### Aakash Tirathdas (**aakash-tir**)

- **Task:** Upload → Analyze end-to-end integration
  **Description:** Completed major parts of the analysis cycle by connecting upload UI to the analysis backend. Implemented temporary ZIP storage, upload tracking (uuid/uploadid), new DB table persistence, and ensured analysis results are stored in the correct DB tables so project pages can surface outcomes. Began work on consent-update and analysis loading UI improvements.
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/364

- **Task:** Testing and validation of analysis workflow
  **Description:** Performed extensive manual testing across multiple accounts and ZIP inputs to validate both LLM and non-LLM paths, confirm correct DB writes, and ensure the analysis cycle completes reliably.

- **Task:** Reviewed PRs  
  **Links:**
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/350
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/359
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/352
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/342
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/336
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/329

- **Issues:**
<img width="539" height="90" alt="image" src="https://github.com/user-attachments/assets/f0abb98d-9d50-4670-a1e5-9a28948edf0e" />
<img width="822" height="89" alt="image" src="https://github.com/user-attachments/assets/b0e7c6bb-67e7-4bf1-ac64-fc0730944753" />


---

### Mithish Ravisankar Geetha (**MithishR**)

- **Task:** Backend API foundation + resume generation system (Milestone 2 expansion)
  **Description:** Implemented/refactored major API endpoints and built a complete interactive resume generator supporting Markdown, PDF, and LaTeX outputs. Added rendering improvements, resolved authentication token issues, fixed missing resume fields, and enabled personal info customization. Also contributed intelligent incremental upload logic to merge updates without duplication.
  **PRs:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/301  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/334  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/336  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/346  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/356  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/324  

- **Task:** Test expansion for backend endpoints
  **Description:** Wrote and expanded unit tests across analysis/auth/projects/portfolio/tasks/resume/health flows to strengthen CI stability and reduce regressions.
  **PRs:**
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/318
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/319

- **Issues:**
<img width="498" height="207" alt="image" src="https://github.com/user-attachments/assets/00042fe5-d0b8-492a-a453-595b01fc74b0" />


---

### Ansh Rastogi (**anshr18**)

- **Task:** Project thumbnail upload UI
  **Description:** Implemented the full thumbnail upload experience in the frontend, including image preview, upload progress feedback, and error handling. Addressed multipart/form-data handling issues and updated CSP to support blob URLs for previews.
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/354

- **Task:** ZIP upload page for projects
  **Description:** Built a ZIP upload page with drag-and-drop, tab-based single/multi upload selection, file validation, and API integration. Fixed a critical routing issue in `App.jsx` and validated user workflows through manual testing.
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/333

- **Issues:**
<img width="462" height="99" alt="image" src="https://github.com/user-attachments/assets/9fc5e102-8dd2-4a9e-a85b-8b7d1bef2454" />
<img width="653" height="558" alt="image" src="https://github.com/user-attachments/assets/f6fe9420-4b6e-49cd-9cb7-4c814038d33a" />

---

### Harjot Sahota (**HarjotSahota**)

- **Task:** Settings consent update workflow
  **Description:** Added a consent toggle in Settings with a confirmation modal, success/error feedback, and frontend tests. Ensured the UI matches existing app styling and consent state loads correctly.
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/348

- **Task:** Delete workflows (single + bulk) + backend authorization + DB tests
  **Description:** Implemented per-project deletion and bulk deletion, including new API routes, strict user-scoped enforcement, UI confirmation flows, and database tests to verify correct deletion behavior.
  **PRs:**
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/338
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/345

- **Task:** Project-ID alignment in resume generation
  **Description:** Fixed a critical modeling issue where resume generation incorrectly relied on portfolio IDs instead of project IDs, refactoring backend and frontend generation flows to align with the project ownership model and prevent missing/duplicated resume items.
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/350

- **Issues:**
<img width="965" height="213" alt="image" src="https://github.com/user-attachments/assets/a49bf7fa-285f-4e85-8ab1-e90412e1b5e0" />
<img width="1001" height="539" alt="image" src="https://github.com/user-attachments/assets/b4779784-0b2e-445b-8d00-658b5325a984" />



---

### Mohamed Sakr (**mgjim101**)

- **Task:** Resume API test suite + stored resume workflow + portfolio dashboard wiring
  **Description:** Built a comprehensive resume API test suite covering auth, generation outputs (Markdown/PDF/LaTeX), stored resume CRUD, merge behavior, and error/ownership cases. Implemented stored resume support (DB + API + UI wiring), and replaced the Portfolio page placeholder with a data-driven dashboard connected to `portfoliosAPI`. Added frontend regression tests to ensure stability of the new portfolio flows and fixed Resume page API wiring to restore build correctness.
  **PRs:**
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/359
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/352
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/340

- **Task:** Reviewed PRs + integration feedback
  **Description:** Reviewed thumbnail, role prediction, and filtering/sorting PRs with a focus on stability, missing imports, cleanup tasks, and edge-case resilience.
  **PR reviews:**
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/354
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/333
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/330
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/362
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/364

- **Issues:**



---

## What Went Well

- **User-facing functionality expanded significantly**
  - New Projects filtering/sorting controls and a full upload experience improved navigation and project management.
  - Portfolio curation infrastructure introduced meaningful user customization for presentation workflows.
  - Portfolio dashboard wiring and stored resume workflows made portfolio/resume features closer to production readiness.

- **Testing and reliability improved**
  - Resume API test coverage grew substantially (including failure paths and access control).
  - Filtering/sorting and portfolio page changes were protected with frontend regression tests.
  - Manual testing across upload/analyze flows improved confidence in integration correctness.

- **Strong collaboration through reviews**
  - Multiple teammates performed high-volume PR reviews and validation testing, reducing integration risk and raising code quality.


---

## What Didn’t Go as Planned

- **Cross-platform environment inconsistencies**
  - Differences between macOS/Windows behavior highlighted the need for stronger container parity, better mocks, and more consistent dev environment replication.

- **Scheduling/coordination friction**
  - At least one missed meeting due to conflicting schedules required asynchronous coordination and contributed to slower alignment on dependencies.

- **Large-scope PR overhead**
  - Several major features required broad refactors or multi-layer changes (frontend + backend + DB + tests), increasing review/merge coordination costs.


---

## How These Reflections Shape Next Cycle’s Plan

- Prioritize **end-to-end integration and polish**
  - Integrate curation preferences into portfolio and resume generation outputs.
  - Complete multi-upload compatibility and tighten the upload/analyze experience.
  - Ensure Projects, Portfolio, and Resume pages remain consistent as APIs evolve.

- Strengthen **environment parity + stability**
  - Improve Docker/containerization alignment and test mocks for localStorage/auth/runtime differences.
  - Add targeted regression tests for cross-platform edge cases and key user flows.

- Continue improving **workflow clarity**
  - Address CLI usability findings from peer testing (menus and guidance).
  - Reduce UX friction using heuristic evaluation feedback as a prioritized roadmap.


---

## Test Report

- **Projects filtering/sorting + UI behavior tests**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/362

- **Resume API high-coverage tests + stored resume behaviors**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/359
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/352

- **Portfolio wiring + regression tests**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/340

- **Role curation tests (authorization + edge cases)**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/342

- **Upload/analyze manual validation**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/364


---

## Project Burnup Chart

<img width="1652" height="936" alt="image" src="https://github.com/user-attachments/assets/c137fc58-1615-4985-9ad9-ad94fc836db5" />

