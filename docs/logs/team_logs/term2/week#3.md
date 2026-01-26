# Team Log – Team 6

**Work Performed:** **Jan 19th – Jan 25th**

---

## Milestone Goals Recap

### Features in Project Plan for This Milestone

- Deliver **Milestone 2 requirements** and ensure the system is ready for evaluation:
  - **Req 24:** Developer Role Prediction (confidence scoring + reasoning + persistence)
  - **Req 32:** Backend API endpoints for full frontend support (projects, portfolio, resume, consent)
  - Improve **frontend usability and completeness** for peer testing / heuristic evaluation readiness
  - Strengthen **consent + privacy workflows** (revocation and enforce gating rules)
- Improve **system stability + test coverage**
  - Add high-coverage unit/integration tests across backend + frontend workflows
  - Ensure CI stability and consistent local runs across the team

### Associated Tasks / PRs Touched This Week

- **Req 24 — Developer Role Prediction**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/329  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/330  

- **Frontend analysis integration (backend ↔ frontend linking)**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/317  

- **Backend API Endpoints + modular refactor (Req 32)**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/301  

- **Backend unit tests for endpoints**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/318  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/319  

- **Dashboard and project UX enhancements**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/308  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/306  

- **Resume/portfolio storage + Projects page UI**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/311  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/322  

- **Consent + analysis flow improvements**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/313  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/315  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/304  

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

- **Task:** Req 24 — Developer Role Prediction  
  **Description:** Implemented a complete **Developer Role Prediction System** that analyzes project characteristics to predict the most likely developer role with **confidence scoring** and **explainable reasoning**. The solution supports **12 role classifications**, applies a **multi-factor scoring algorithm** (languages, frameworks, testing signals, CI/CD, repo structure, etc.), and integrates with the database + CLI pipeline.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/329  

- **Task:** Req 24 — Role Prediction automated test suite  
  **Description:** Built a full automated test suite for role prediction including **unit, integration, performance, and end-to-end coverage** to ensure reliable predictions and stable persistence across workflows.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/330  

- **Task:** Team coordination + heuristic evaluation preparation  
  **Description:** Attended weekly check-ins and team meetings, aligned milestone progress, prepared for the upcoming in-class heuristic evaluation, and created the **Google survey** to collect structured user feedback.

- **Task:** Reviewed PRs  
  **Links:**
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/322  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/318  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/317  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/313  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/308  

- **Issues:**  
<img width="673" height="191" alt="image" src="https://github.com/user-attachments/assets/9428aa1f-115e-4a69-8fe8-273fc36e9159" />


---

### Aakash Tirathdas (**aakash-tir**)

- **Task:** Frontend analysis workflow connection (backend ↔ frontend)  
  **Description:** Implemented the core connection between backend services and the analysis frontend. This included setting up the majority of the analysis workflow structure and preparing it for final integration and polishing.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/317  

- **Task:** Debugging + test maintenance support  
  **Description:** Debugged failing tests from prior development work and assisted other teammates with implementation tasks where needed. Also contributed to resolving minor issues discovered during integration work.

- **Task:** Reviewed PRs  
  **Links:**
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/298  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/301  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/304  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/315  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/319  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/324  

- **Issues:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/issues/316
  
<img width="821" height="89" alt="image" src="https://github.com/user-attachments/assets/122cfbfa-485a-4774-9161-213b799f77ff" />


---

### Mithish Ravisankar Geetha (**MithishR**)

- **Task:** Req 32 — Full API endpoint implementation + backend refactor  
  **Description:** Implemented all major API endpoints for **projects, resume, portfolio, and privacy consent**, meeting requirement 32 for Milestone 2. Refactored the monolithic API server into a **modular architecture**, improving maintainability and enabling smoother frontend integration.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/301  

- **Task:** Backend unit testing expansion  
  **Description:** Added extensive unit test coverage for analysis, authentication, projects, portfolio, tasks, resume, health, and API server endpoints, validating expected outputs, error handling, and basic security behaviors.  
  **PRs:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/318  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/319  

- **Task:** Reviewed PRs  
  **Links:**
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/290  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/306  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/308  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/311  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/304  

- **Issues:**  

<img width="477" height="199" alt="image" src="https://github.com/user-attachments/assets/7f76f548-6421-4b9f-b514-316cf27a02ef" />

---

### Ansh Rastogi (**anshr18**)

- **Task:** Dashboard redesign + improved UX structure  
  **Description:** Delivered a modern dashboard redesign with navigation, real-time project statistics, and quick action cards for core workflows (upload, view, generate portfolio/resume). Built reusable UI components and placeholder pages for remaining routes.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/308  

- **Task:** Project thumbnail upload system (backend + API integration)  
  **Description:** Implemented a complete project thumbnail workflow including database schema updates, protected API endpoints (POST/GET/DELETE), file validation rules, ownership checks, and file storage handling.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/306  

- **Task:** Bug fixes and integration debugging  
  **Description:** Resolved SQL filtering issues, corrected API response handling, fixed a thumbnail storage edge case (orphaned files), and validated backend/frontend integration with authentication and routing.

- **Task:** Reviewed PRs  
  **Links:**
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/318  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/311  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/313  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/301  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/324  

- **Issues:**  
<img width="646" height="199" alt="image" src="https://github.com/user-attachments/assets/92c66f68-3b2d-4230-bf22-55077e995d61" />

---

### Harjot Sahota (**HarjotSahota**)

- **Task:** Resume/portfolio item storage + Projects page rendering  
  **Description:** Implemented end-to-end support for storing and displaying **resume_items** and **portfolio_items**, including schema updates, DB helpers, protected API endpoints, and frontend rendering for project summaries and bullet lists.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/311  

- **Task:** Fix duplicate analysis persistence bug  
  **Description:** Fixed a critical analysis flow issue preventing duplicate LLM-consented analysis rows from being saved incorrectly, improving consistency across LLM and non-LLM paths.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/304  

- **Task:** Frontend testing configuration + ProjectsPage tests  
  **Description:** Added frontend test infrastructure and implemented ProjectsPage-focused tests, improving confidence in UI correctness after rapid feature changes.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/322  

- **Task:** CI stabilization and merge conflict resolution  
  **Description:** Resolved CI failures by updating unit tests, fixing import issues, addressing cache problems, and cleaning merge conflicts to ensure builds remain green.

- **Task:** Reviewed PRs  
  **Links:**
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/315  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/319  

- **Issues:**  
<img width="806" height="392" alt="image" src="https://github.com/user-attachments/assets/af29a9aa-095a-441b-b533-5a84a4247f09" />


---

### Mohamed Sakr (**mgjim101**)

- **Task:** Consent revocation + enforce gating rules across workflows  
  **Description:** Implemented consent revocation support and enforced consent requirements before login and analysis runs. Hardened CLI prompts to prevent stdin capture failures and ensured revoked users are blocked from AI-powered features.  
  **PRs:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/315  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/313  

- **Task:** Owner-scoped deduplication improvements + testing  
  **Description:** Improved reanalysis behavior with owner-scoped dedup rules and overwrite semantics so the latest run cleanly replaces child tables and avoids cross-user collisions. Added high-coverage tests to prevent regressions and validated safer migrations for legacy DB states.

- **Task:** Reviewed PRs + validation testing  
  **Description:** Reviewed the thumbnail workflow for safety and correctness, identified edge cases related to file cleanup and path validation, and ran the thumbnail test suite successfully.

- **Task:** Reviewed PRs  
  **Links:**
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/306  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/317  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/322  

- **Issues:**
  
<img width="616" height="201" alt="image" src="https://github.com/user-attachments/assets/18ac95ed-f5cc-47e2-b62a-5f11cc46b105" />

---

## What Went Well

- **Major Milestone 2 deliverables progressed quickly**
  - Role Prediction (Req 24) shipped end-to-end with persistence, confidence scoring, and full automated testing.
  - Backend API endpoints (Req 32) were completed and refactored into a modular structure, improving maintainability.
- **Frontend became significantly more presentable**
  - Dashboard redesign and improved navigation created a more polished prototype experience.
  - Thumbnail support enhanced project UX and portfolio readability.
- **System reliability improved through testing**
  - Strong coverage was added across role prediction, backend endpoints, consent workflows, and Projects page UI.
  - CI stability improved after resolving failing tests and merge issues.

---

## What Didn’t Go as Planned

- **Time estimation issues and delayed test work**
  - Some tasks took longer than expected, and test writing was pushed later in the week for a few components.
- **Coordination challenges**
  - One planned meeting was missed due to scheduling conflicts, requiring async follow-ups.
- **Large PR workflow overhead**
  - Some PRs were naturally large due to refactors and broad endpoint coverage, requiring additional coordination and follow-up PRs for testing.

---

## How These Reflections Shape Next Cycle’s Plan

- Prioritize **heuristic/peer evaluation readiness**
  - Ensure the system is stable, demo-friendly, and consistently runnable across team environments.
  - Use evaluation feedback to guide UI polish and workflow clarity improvements.
- Focus on **end-to-end integration and refinement**
  - Complete remaining frontend integration for analysis + curation flows.
  - Add curation support for role prediction when default classification is inaccurate.
- Continue improving **documentation + reliability**
  - Document consent edge cases, dedup behaviors, and migration expectations.
  - Add additional regression tests for integration workflows where needed.

---

## Test Report

- **Req 24 — Role Prediction:** Comprehensive suite added validating scenarios, integration, edge cases, and performance  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/330  
- **Backend endpoint tests:** Expanded unit tests across analysis/auth/projects/portfolio/tasks/resume/health APIs  
  - PRs: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/318  
         https://github.com/COSC-499-W2025/capstone-project-team-6/pull/319  
- **Frontend Projects page tests + test configuration:** Improved UI confidence and stability  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/322  
- **Consent gating + dedup regression testing:** Updated/extended tests to match consent workflow behavior and multi-user overwrite rules  
  - PRs: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/313  
         https://github.com/COSC-499-W2025/capstone-project-team-6/pull/315  

---

## Project Burnup Chart

<img width="1813" height="946" alt="image" src="https://github.com/user-attachments/assets/6795877c-1f1f-4334-a2e1-55ae91b1b220" />


