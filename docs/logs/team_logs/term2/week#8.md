# Team Log – Team 6

**Work Performed:** **Feb 9th – Mar 1st**

---

## Milestone Goals Recap

### Features in Project Plan for This Milestone

- Deliver and stabilize **Milestone 2** end-to-end functionality and UX polish:
  - Strengthen **frontend usability** based on peer testing feedback
  - Expand core project workflows (upload, analyze, browse, deduplicate, incremental updates)
  - Support richer **portfolio/resume workflows** (rendering correctness, curation integration, generation-ready data)
- Improve **system stability + test coverage**
  - Resolve broken/legacy tests after architecture refactors
  - Expand backend + frontend tests to prevent regressions
  - Validate key flows through manual testing and peer testing sessions

### Associated Tasks / PRs Touched This Period

- **Portfolio Curation (UI + integration + tests)**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/368
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/395
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/399

- **Incremental Upload (detection + frontend sync)**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/372

- **API stabilization + docs + test migrations**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/390
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/391
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/392
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/403

- **Portfolio rendering reliability + regression tests**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/375
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/377

- **Dashboard + thumbnails + duplicate ZIP detection**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/381
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/389
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/398

- **Analyze pipeline fixes + consent/test bug fixes**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/382
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/373
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/385

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

- **Task:** Portfolio curation foundation + full app integration  
  **Description:** Built the end-to-end **curation system** (backend authenticated API + frontend workflow + persistent storage) and integrated curated settings across **Portfolio**, **Resume/Dashboard**, and **Projects** pages. Implemented a structured **5-tab** curation workflow: **Top 3 showcase**, **comparison attributes**, **highlighted skills (max 10)**, **chronology correction**, and **custom project order**. Ensured curated preferences consistently drive UI behavior (ranking badges, ordering, filters, resume forwarding, and dashboard showcase navigation).  
  **PRs:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/368  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/395  

- **Task:** Automated curation integration test coverage  
  **Description:** Added comprehensive backend + frontend tests validating curation behavior and propagation (highlighted skills forwarding + fallback logic, showcase rendering and navigation, projects sorting/filtering states, and error/empty/loading paths).  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/399  

- **Task:** Collaboration + PR reviews  
  **Description:** Reviewed teammate PRs focused on test stability and rendering correctness to reduce integration risk ahead of Milestone 2 stabilization.  
  **Reviewed PRs:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/390  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/385  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/377  

---

### Aakash Tirathdas (**aakash-tir**)

- **Task:** Analysis pipeline completion (LLM + non-LLM)  
  **Description:** Completed the analyze pipeline end-to-end so projects can be analyzed **with or without LLM**, ensuring reliable storage and validation (e.g., preventing analysis without a project title). Began implementation for **multi-project analysis** while maintaining correct persistence and runtime behavior.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/382  

- **Task:** Test stabilization + deprecated/incorrect test cleanup  
  **Description:** Ensured the test suite passes except for explicitly deprecated tests, and validated the analysis pipeline through both manual and automated testing.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/385  

- **Task:** Consent workflow bug fix support  
  **Description:** Contributed bug fixes to consent-related behavior to ensure settings/authorization flows remain stable during Milestone 2 wrap-up.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/373  

- **Task:** Collaboration + PR reviews + demo/presentation support  
  **Description:** Provided feedback on multiple teammate PRs and supported milestone deliverables (demo video and in-class presentation preparation).  
  **Reviewed PRs (selected):**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/403  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/402  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/398  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/394  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/387  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/372  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/391  

---

### Mithish Ravisankar Geetha (**MithishR**)

- **Task:** Incremental upload system (detection + UX feedback loop)  
  **Description:** Delivered a production-ready **Incremental Upload** system that detects when an uploaded project exceeds a **30% change threshold**, then updates the portfolio/database accordingly. Implemented a frontend polling mechanism for background analysis jobs and a detailed result modal describing which projects were **added**, **updated (with change %)**, or **skipped** as duplicates.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/372  

- **Task:** Test infrastructure migration + API stabilization  
  **Description:** Migrated backend tests to use **FastAPI.TestClient** for true HTTP-level validation and fixed widespread failures caused by the refactor to modular FastAPI. Stabilized key endpoints (API server + Projects), corrected mock patch paths and ID mismatch errors, and improved CI reliability.  
  **PRs:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/390  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/391  

- **Task:** Milestone 2 final integration to main  
  **Description:** Completed the final merge of the development branch to main and verified Milestone 2 end-to-end feature sync (Resume, Portfolios, Projects) for submission readiness.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/392  

- **Task:** Collaboration + reviews  
  **Description:** Reviewed a wide range of feature PRs spanning dashboard, uploads, consent, and endpoint changes to identify regressions early and reduce integration risk.  
  **Reviewed PRs (selected):**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/387  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/382  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/381  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/379  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/373  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/364  

---

### Ansh Rastogi (**anshr18**)

- **Task:** Dashboard data correctness + frontend polish  
  **Description:** Fixed user-facing dashboard issues including broken `/api/skills` behavior (incorrect DB import), replaced hardcoded AI analysis counts with live computed values, and corrected misleading labels (changed “Total Lines of Code” to “Total Files” to match stored metrics).  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/381  

- **Task:** Thumbnail lifecycle improvements (remove + UX resilience)  
  **Description:** Implemented thumbnail removal support with proper UI state clearing, blob URL revocation to prevent memory leaks, and graceful handling of missing thumbnail states to suppress console noise.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/389  

- **Task:** Duplicate ZIP detection (API + task-level)  
  **Description:** Added SHA-256 hashing to track uploaded ZIPs and implemented duplicate detection at both API and task levels to avoid re-analysis and wasted compute. Added an informational banner and improved runtime stability by deferring LLM pipeline imports to avoid startup dependency errors.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/398  

- **Task:** Collaboration + PR reviews  
  **Description:** Reviewed major Milestone 2 PRs across tests, incremental upload, portfolio rendering, personal info, and curation integration to validate integration quality and UX behavior.  
  **Reviewed PRs (selected):**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/385  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/391  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/372  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/375  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/399  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/402  

---

### Harjot Sahota (**HarjotSahota**)

- **Task:** No team log submitted for this period  
  **Description:** No personal log content was provided for Feb 9th – Mar 1st, so team-level work for this member cannot be summarized in the standardized format.  

---

### Mohamed Sakr (**mgjim101**)

- **Task:** Portfolio end-to-end rendering stabilization (API contract + UI resilience)  
  **Description:** Fixed Portfolio rendering issues by aligning backend response contracts with frontend expectations (ensuring consistent `items` / `portfolio_items` shapes). Improved UI resilience via highlighted-skills fallback derivation from `portfolio_items[].skills_exercised`, and made “Available analyses” cards more user-friendly by using project names instead of generic analysis type labels. Removed the Portfolio Summary section per product direction and verified consistent rendering with real analysis data.  
  **PRs:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/375  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/377  

- **Task:** Portfolio deduplication + reanalysis lifecycle cleanup  
  **Description:** Addressed duplicate portfolio item behavior during reanalysis by implementing cleanup controls (removing stale `portfolio_items` on child reanalysis) and fetch-side dedupe (returning only the latest portfolio item per project during analysis item fetch).  

- **Task:** Test suite alignment for Portfolio regressions  
  **Description:** Expanded and updated Portfolio page tests to match current UI behavior: metadata rendering, quality/sophistication display including `project_statistics` fallback, derived highlighted skills behavior, project-name card titles, and empty-state handling.  
  **PRs:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/375  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/377  

- **Task:** Documentation + architecture artifacts  
  **Description:** Expanded the Milestone 2 README with clearer service/API + Human-in-the-Loop documentation and updated architecture/DFD diagrams to reflect new features, endpoints, and frontend integration changes.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/403  

- **Task:** Collaboration + PR reviews  
  **Description:** Conducted detailed reviews across major curation/portfolio changes and related UX-risk callouts (consent gating clarity), validating architecture quality and integration behavior across the app.  
  **Reviewed PRs (selected):**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/399  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/395  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/389  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/373  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/368  

---

## What Went Well

- **Milestone 2 stabilization and delivery**
  - The team successfully wrapped Milestone 2 with key flows functioning end-to-end (upload/analyze variants, incremental updates, deduplication, portfolio rendering correctness, and curation propagation).
- **User-facing feature maturity increased**
  - Curation now drives portfolio/resume/projects/dashboard behavior.
  - Incremental upload and duplicate ZIP detection reduce wasted compute and improve user clarity.
  - Portfolio UI now renders reliably with improved labeling and fallback behavior.
- **Testing and reliability improved despite refactors**
  - Backend tests were migrated to HTTP-level validation, reducing false confidence from direct function calls.
  - Targeted frontend regression tests were expanded for curation and portfolio behavior.

---

## What Didn’t Go as Planned

- **Presentation/demo execution issues**
  - The Milestone 2 in-class presentation ran over time and had clarity gaps (missing/late architecture diagram, time lost to technical issues, and slides that could have been more concise).
- **Coordination + merge latency**
  - Waiting for PR approvals/merge windows slowed progress and created last-minute pressure (especially for bug fixes and polish).
- **Technical debt from architecture refactors**
  - Modularization and contract shifts caused widespread test breakage and multi-layer debugging overhead, consuming time intended for feature work.

---

## How These Reflections Shape Next Cycle’s Plan

- Prioritize **Milestone 3 planning + clearer delivery execution**
  - Lock slide structure earlier (including architecture visuals) and rehearse timing to avoid overruns.
  - Improve demo/presentation reliability (tech checks + explicit backups).
- Focus on **bug burn-down + polish after Milestone 2**
  - Triage remaining issues from peer testing and Milestone 2 wrap-up.
  - Address the underlying dependency/import issues (e.g., LLM pipeline dependency stability) rather than workarounds.
- Continue strengthening **integration + test stability**
  - Expand regression coverage on reanalysis/deduplication/incremental flows and cross-layer API contract checks.

---

## Test Report

- **Curation integration tests (backend + frontend)**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/399

- **API server + projects endpoint test stabilization / HTTP-level migration**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/390  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/391  

- **Portfolio rendering regression tests + contract alignment**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/375  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/377  

- **Analysis pipeline validation + test fixes**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/382  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/385  

- **Incremental upload (feature + frontend sync verification)**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/372  

---

## Project Burnup Chart

*(Not included for this period — burnup image not provided in the personal logs.)*
