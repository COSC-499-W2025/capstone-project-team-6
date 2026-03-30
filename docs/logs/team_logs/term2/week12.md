# Team Log – Team 6

**Work Performed:** **Mar 15th – Mar 29th**

---

## Milestone Goals Recap

### Features in Project Plan for This Milestone

- **Milestone 3 implementation** – Begin core M3 features and frontend integration
  - Role prediction integration into resume and portfolio generation
  - LLM analysis display on Projects page
  - Education and Awards section for Resume
  - Resume showcase projects feature
  - Heatmap generation planning
- **Milestone 2 polish and stability**
  - Fix remaining bugs (duplicate detection, project deletion, CORS, thumbnail 500)
  - Personal information validation on Resume and Settings pages
  - Syntax and build stability fixes
- **Setup and documentation**
  - Docker documentation for unified environment
  - TA onboarding and verification guides
  - Cross-platform (Windows) validation

### Associated Tasks / PRs Touched This Period

- **Role prediction and curation**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/444

- **LLM analysis display and pipeline fixes**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/446

- **Resume enhancements**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/440
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/452

- **Personal information validation**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/443

- **CORS and thumbnail fixes**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/450

- **Syntax errors and build stability**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/439

- **Docker documentation**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/441

- **Duplicate detection (carryover)**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/431

---

## Team Members

- **maddysam356** → Mandira Samarasekara
- **aakash-tir** → Aakash Tirithdas
- **MithishR** → Mithish Ravisankar Geetha
- **anshr18** → Ansh Rastogi
- **HarjotSahota** → Harjot Sahota
- **mgjim101** → Mohamed Sakr

---

## Completed Tasks

### Mandira Samarasekara (**maddysam356**)

- **Task:** Role prediction frontend feature  
  **Description:** Implemented the role prediction feature end-to-end across all three project-facing pages (Projects, Resume, Portfolio). Surfaced `predicted_role`, `predicted_role_confidence`, and `curated_role` through enriched backend query paths. Added `GET /api/curation/roles` and `POST /api/curation/role` endpoints. Built an interactive role pill on the Projects page with inline editing, dropdown of predefined roles plus Custom role option, and Save/Reset/Cancel controls. Added role badges to Resume selection list and Portfolio project views with distinct visual states for curated, predicted, and unset roles.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/444

- **Task:** TA verification guide  
  **Description:** Wrote a detailed guide for the TA to verify the role prediction feature on the backend.

- **Task:** Collaboration + testing support  
  **Description:** Manually tested the full role prediction stack locally. Reviewed and approved duplicate file analysis detection bug fix (#431) and Fixed syntax errors (#439) after verifying both sets of fixes worked as expected.  
  **Reviewed PRs:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/431  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/439

---

### Aakash Tirithdas (**aakash-tir**)


- **Task:** Personal information validation  
  **Description:** Implemented validation for personal information on both the Resume page and Settings page. Only expected input can be saved; changes on the Resume page do not overwrite Settings page saved information.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/443

- **Task:** Test updates for settings and resume  
  **Description:** Updated and created tests for the Settings and Resume pages in relation to personal information validation.

- **Task:** Docker and documentation validation  
  **Description:** Verified Docker worked correctly on Windows laptop and that documentation was up to date.

- **Task:** Collaboration + reviews  
  **Description:** Reviewed Projects page LLM analysis integration, CORS/thumbnail fixes, updated resume page with showcase projects, and Docker documentation.  
  **Reviewed PRs:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/446  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/450  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/452  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/441

---

### Mithish Ravisankar Geetha (**MithishR**)


- **Task:** Delete project bug fix and Education section for Resume  
  **Description:** Fixed a critical bug in the project deletion flow so deleted projects are fully cleared from the database, enabling clean re-analysis of previously deleted projects without stale data errors. Implemented the Education and Awards section on the Resume page to support detailed academic credentials.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/440

- **Task:** Docker documentation  
  **Description:** Authored detailed instructions for setting up and running containers, including environment-specific configurations.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/441

- **Task:** System stability fixes  
  **Description:** Resolved various JSX and API service syntax errors on the Settings page to restore successful frontend compilation.

- **Task:** Collaboration + reviews  
  **Description:** Verified project deletion clears all associated artifacts and allows fresh re-import. Reviewed role prediction frontend, personal information validation logic, and syntax error fixes.  
  **Reviewed PRs:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/439  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/444  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/443

---

### Harjot Sahota (**HarjotSahota**)

- **Task:** Updated resume page with specified showcase projects  
  **Description:** Implemented the showcase feature on the Resume page so users can clearly display and access their top projects.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/452

- **Task:** Fixed syntax errors  
  **Description:** Resolved frontend build issues including Settings page JSX problems and missing `deleteAccount` API method. Restored successful app compilation and Docker build.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/439

- **Task:** Docker bug fix  
  **Description:** Found and fixed a bug early in the week that was preventing Docker from running properly, unblocking the team for the rest of the week.

- **Task:** Task list and team coordination  
  **Description:** Created the task list and had all teammates review and suggest changes to ensure alignment on priorities.

- **Task:** Collaboration + reviews  
  **Description:** Reviewed duplicate file analysis detection bug fix and Delete project bug fix with Education section.  
  **Reviewed PRs:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/431  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/440

---

### Mohamed Sakr (**mgjim101**)

- **Task:** LLM analysis display panel and pipeline fixes  
  **Description:** Implemented the LLM analysis display panel on the Projects page with base prompt output, category dropdown (architecture, security, complexity, skills, domain, resume), and `parseLlmSections` for rendered React subsections. Added `GET /api/projects/{project_id}/llm-analysis` endpoint. Fixed LLM summary not being persisted (root cause: `sqlite3.Row` does not support `in` operator, so `analysis_uuid` was always `None`). Fixed silently suppressed LLM errors in `llm_pipeline.py` by removing `progress_callback` guards on `logger.error`. Fixed frontend dropdown scrolling for analysis categories. Added diagnostic logging across the LLM pipeline.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/446

- **Task:** Comprehensive test coverage for LLM pipeline  
  **Description:** Created `test_llm_summary.py` (18 unit tests) and `test_llm_analysis_endpoint.py` (6 integration tests). Updated `test_task_manager_llm.py` with new behavior tests. Documented `sqlite3.Row` regression and verified fixes.

- **Task:** Collaboration + reviews  
  **Description:** Reviewed role prediction frontend, validation settings, and Docker documentation.  
  **Reviewed PRs:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/444  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/443  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/441

---

### Ansh Rastogi (**anshr18**)


- **Task:** CORS and thumbnail 500 error fixes  
  **Description:** Fixed CORS errors on the thumbnail endpoint by changing axios `baseURL` from `http://localhost:8000/api` to `/api`, routing requests through the Vite dev proxy and improving production behavior. Fixed 500 Internal Server Error on thumbnail GET endpoint by adding missing `Response` import in `projects.py`.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/450

- **Task:** Manual debugging and validation  
  **Description:** Reproduced CORS failure and 500 error in browser, confirmed fixes for projects with and without thumbnails. Verified Delete project bug fix and Education section locally.

- **Task:** Collaboration + reviews  
  **Description:** Reviewed Delete project bug fix and Education section for Resume; confirmed project deletion and Education section work correctly end-to-end.  
  **Reviewed PRs:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/440

---

## What Went Well

- **Milestone 3 features moved forward**
  - Role prediction is now surfaced across Projects, Resume, and Portfolio with curation support.
  - LLM analysis is fully end-to-end functional on the Projects page.
  - Resume gained Education/Awards and showcase project features.

- **Critical bugs were fixed**
  - Project deletion now fully clears associated data, enabling clean re-analysis.
  - CORS and thumbnail 500 errors were resolved, restoring project thumbnails.
  - Syntax and build issues were fixed, restoring frontend compilation.

- **Strong testing and documentation**
  - LLM pipeline received 24+ new tests covering persistence, API, and regression scenarios.
  - Docker documentation was completed for the unified environment.
  - TA verification guides were added for new features.

- **Team coordination improved**
  - Task list creation and review helped align priorities.
  - Early Docker bug fix unblocked the team for the week.

---

## What Didn't Go as Planned

- **Task overlap**
  - A teammate and Harjot accidentally worked on the same task; discovered when the other opened a PR. Highlighted the need for clearer task ownership and communication.

- **Some planned work deferred**
  - Analyze page loading animation update for multi-project analysis was pushed to next week due to role prediction coordination.
  - Milestone 3 feature task (Ansh) was deferred in favor of CORS/thumbnail debugging.
  - Windows Docker verification remains ongoing; cross-platform edge cases need more testing.

- **Subtle bugs required extensive debugging**
  - `sqlite3.Row` not supporting `in` operator was only found after diagnostic logging.
  - Database corruption from prior partial runs masked whether fixes were working until test data was cleaned.

- **Hardcoded configuration caused silent failures**
  - Axios `baseURL` hardcoded to backend port bypassed Vite proxy and caused CORS issues in some configurations.

---

## How These Reflections Shape Next Cycle's Plan

- Prioritize **Milestone 3 core features** including heatmap generation and peer testing feedback.
- Improve **task ownership and communication** to avoid duplicate work; check task assignments before starting.
- Return to **Analyze page loading animation** for multi-project analysis.
- Run **full system test** and fix remaining bugs before focusing on selling points and excess features.
- Continue **frontend/backend integration** support and related PR reviews.
- Address **output quality** improvements for Gemini analysis sections.

---

## Test Report

- **LLM pipeline and analysis endpoint**
  - 18 unit tests in `test_llm_summary.py` for `update_llm_summary`, `record_analysis`, `sqlite3.Row` regression, and `_process_new_portfolio` behavior  
  - 6 integration tests in `test_llm_analysis_endpoint.py` for authenticated/unauthenticated access, 404 cases, and response structure  
  - Updated `test_task_manager_llm.py` for current architecture  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/446

- **Personal information validation**
  - Tests for Settings and Resume page validation logic  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/443

- **Project deletion and Education section**
  - Verified project deletion clears all artifacts and allows clean re-import  
  - Confirmed Education section renders correctly on Resume page  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/440

- **CORS and thumbnail fixes**
  - Manual verification of thumbnail loading for projects with and without thumbnails  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/450

- **Role prediction**
  - Full-stack manual testing of predicted roles, curation flow, and persistence across Projects, Resume, and Portfolio  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/444

## Project Burnup Chart


