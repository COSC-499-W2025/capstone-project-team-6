# Team Log – Team 6

**Work Performed:** **Mar 2nd – Mar 8th**

---

## Milestone Goals Recap

### Features in Project Plan for This Milestone

- Wrap up and stabilize **Milestone 2** functionality before beginning Milestone 3 work
  - Fix bugs found during milestone wrap-up
  - Improve reliability of **analysis**, **resume generation**, and **duplicate detection** workflows
  - Polish user-facing pages including **Analyze**, **Projects**, and **Settings**
- Improve **setup, deployment, and development workflow**
  - Unify frontend/backend Docker setup
  - Add clearer setup instructions for the TA
  - Verify cross-platform behavior, especially on Windows
- Strengthen **testing and regression protection**
  - Repair stale/broken tests
  - Add targeted regression tests for major bugs
  - Validate key flows through manual and local testing
- Begin planning and preparing for **Milestone 3**
  - Discuss milestone requirements
  - Identify carryover polish and next feature work

### Associated Tasks / PRs Touched This Period

- **Setup, docs, and test stabilization**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/410
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/411
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/412
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/415
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/429

- **Analysis, duplicate detection, and Analyze page improvements**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/414
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/420
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/431

- **Dockerization and account/settings features**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/416
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/418
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/428

- **Projects UI and resume generation reliability**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/423
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/425
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/426

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

- **Task:** Setup fixes, dependency cleanup, and TA onboarding documentation  
  **Description:** Fixed outdated and deprecated dependencies in the root `requirements.txt` and added a detailed `SETUP_INSTRUCTIONS.md` document under `docs` so the TA can set up the project from scratch more reliably.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/411

- **Task:** Analyze page UI redesign + progress bar accuracy improvements  
  **Description:** Restyled the Analyze page to align with the Dashboard and Upload design system, including project name display, project/analysis badges, and hiding the raw task ID. Also improved backend progress reporting by introducing a `progress_callback` in `analyze_folder()` with six real phase-based updates and mapping analysis progress properly in `task_manager.py`, replacing the misleading hardcoded 50% behavior.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/420

- **Task:** Windows validation for unified Docker workflow  
  **Description:** Tested the unified Docker setup on Windows and fixed missing or incompatible setup pieces, including persistent volume handling, `.env` bootstrapping, Docker Compose v2 standardization, CORS environment configuration, and a Windows-specific test script.  
  **PR contribution:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/416

- **Task:** Collaboration + testing support  
  **Description:** Reviewed and locally tested major teammate PRs, including resume generation and Projects page UI changes, and provided approval after verifying expected behavior.  
  **Reviewed PRs:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/423  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/425  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/416  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/412  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/415  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/429

<img width="586" height="81" alt="image" src="https://github.com/user-attachments/assets/39922dbd-e439-455f-80ae-87ce12073665" />
<img width="1259" height="86" alt="image" src="https://github.com/user-attachments/assets/055bde0f-36f8-4b91-89ca-45fa08eed043" />


---

### Aakash Tirithdas (**aakash-tir**)

- **Task:** Multi-project analysis bug fix  
  **Description:** Fixed the multi-project analysis bug by updating the task analysis logic to support multiple task IDs rather than only one. This restored correct handling of extra multi-project analysis flows.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/414

- **Task:** Test stabilization and validation  
  **Description:** Ensured relevant tests passed except for deprecated ones, and validated the multi-project analysis fix through both manual and automated testing. This work also involved recreating fixes in a cleaner branch after merge conflicts made the previous branch difficult to salvage.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/412

- **Task:** Documentation updates  
  **Description:** Updated milestone documentation artifacts including DFD1 and the architecture diagram to reflect the latest system state.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/410

- **Task:** Bug discovery + reviews  
  **Description:** Identified additional bugs remaining in the multi-analysis and duplication logic, and reviewed teammate PRs related to settings, Analyze page improvements, and resume generation fixes.  
  **Reviewed PRs:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/418  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/420  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/425

<img width="425" height="86" alt="image" src="https://github.com/user-attachments/assets/fe3d25b5-b794-450d-90ee-891f6bb722c7" />


---

### Mithish Ravisankar Geetha (**MithishR**)

- **Task:** Unified Docker environment for local development  
  **Description:** Dockerized the application into a unified frontend/backend workflow, streamlining local setup and improving development consistency. The new setup included persistent local data through mounted storage and health-checked container startup.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/416

- **Task:** Settings page account management improvements  
  **Description:** Implemented the password change feature and added logout support directly into the Settings page, improving account control and user experience.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/418

- **Task:** Testing and validation for auth + Docker  
  **Description:** Verified password change and logout with backend tests, validated persistence across container restarts, and checked API/frontend availability using Docker setup scripts.  
  **Related PRs:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/416  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/418

- **Task:** Collaboration + architecture guidance  
  **Description:** Reviewed setup and multi-project fixes, and provided architectural feedback on milestone documentation to better reflect relationships between FastAPI, Gemini AI, and Task/Project/Portfolio modules.  
  **Reviewed PRs:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/414  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/411  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/410

<img width="948" height="94" alt="image" src="https://github.com/user-attachments/assets/2cfa107a-6641-4185-990a-227a2956f7b7" />


---

### Harjot Sahota (**HarjotSahota**)

- **Task:** Projects page UI cleanup and layout improvements  
  **Description:** Improved the Projects page by removing the unused “Select stored resume” / “Add selected bullets” section, displaying resume bullets as plain bullet points, and cleaning up the project card layout for better readability and usability.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/423

- **Task:** Delete Account feature  
  **Description:** Added a full Delete Account feature spanning frontend, backend, and tests. This included a new Settings page section, confirmation modal, API wiring, backend deletion endpoint, and helper logic to remove associated user data.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/428

- **Task:** Database cleanup insight  
  **Description:** Identified that some database relationships were missing proper cascading delete behavior. Used ordered backend cleanup logic to complete the feature safely while flagging schema cleanup as follow-up technical debt.

- **Task:** Collaboration + reviews  
  **Description:** Reviewed resume generation tests, multiproject/setup work, and milestone documentation updates to support team integration.  
  **Reviewed PRs:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/426  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/414  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/411  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/410

<img width="715" height="199" alt="image" src="https://github.com/user-attachments/assets/ff7f3ed1-cd7c-45a1-9150-e0f5f23eb13f" />


---

### Mohamed Sakr (**mgjim101**)

- **Task:** Resume generation crash fix  
  **Description:** Diagnosed and fixed the broken resume generation workflow that previously caused a white screen. This included correcting the backend/frontend field mismatch (`portfolio_ids` vs `project_ids`), rewriting `generate_resume` to fetch project/resume/portfolio data correctly, removing the single-portfolio restriction, adding a React `ErrorBoundary`, and increasing axios timeout duration.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/425

- **Task:** Resume regression test coverage  
  **Description:** Updated stale tests to match the new request format and mocks, added a new regression test suite for the identified bugs, and created frontend tests covering render behavior, success/error flows, and `ErrorBoundary` fallback behavior. All 85 tests passed locally.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/426

- **Task:** Collaboration + review support  
  **Description:** Reviewed Analyze page changes and the Delete Account feature during early review stages to provide feedback on ongoing Milestone 2 wrap-up work.  
  **Reviewed PRs:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/420  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/428



---

### Ansh Rastogi (**anshr18**)

- **Task:** Duplicate detection bug-fix sweep  
  **Description:** Fixed eight bugs across duplicate detection logic in SQL, backend task handling, and frontend upload/navigation state. Key fixes included preventing deleted projects from blocking re-upload, enabling duplicate detection for LLM uploads, separating duplicates from upload errors in multi-file flows, and correcting redirect/message behavior for mixed duplicate/new upload cases.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/431

- **Task:** Manual debugging and scenario-based validation  
  **Description:** Manually reproduced and verified eight distinct edge cases including deleted-project re-upload, genuine duplicates, mixed-case multi-upload, LLM duplicate handling, runtime error reproduction, message visibility, and navigate-back persistence.

- **Task:** Collaboration + reviews  
  **Description:** Reviewed test fixes, settings changes, Projects page cleanup, and resume bugfix tests to reduce regression risk across the codebase.  
  **Reviewed PRs:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/412  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/418  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/423  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/426

<img width="451" height="85" alt="image" src="https://github.com/user-attachments/assets/3cae9fa9-3743-490c-a885-d8fcfe7b931a" />
<img width="469" height="91" alt="image" src="https://github.com/user-attachments/assets/40c64e0e-d8f9-4a92-8adc-c27ab7634920" />


---

## What Went Well

- **Milestone 2 wrap-up produced substantial stability gains**
  - The team fixed several high-impact bugs across multi-project analysis, duplicate detection, Docker setup, and resume generation.
  - Multiple user-facing pages were improved, especially Analyze, Projects, and Settings.

- **Cross-platform setup and onboarding improved**
  - The unified Docker workflow was implemented and then strengthened with Windows verification, setup script fixes, and improved environment handling.
  - TA onboarding was improved through updated setup documentation and dependency cleanup.

- **Core user workflows became more reliable**
  - Resume generation no longer crashes with a white screen.
  - Duplicate detection handles more edge cases correctly.
  - Progress reporting on the Analyze page is more accurate and less misleading.
  - Projects page and account settings are cleaner and more usable.

- **Testing and review effort was strong**
  - Team members combined manual validation, targeted regression tests, and PR review support to reduce integration risk.
  - Multiple key flows were tested locally before approval.

---

## What Didn’t Go as Planned

- **Coordination was weaker this week**
  - No team meetings took place because everyone was busy, which made communication and sync-up harder.

- **Several issues surfaced late in wrap-up**
  - Missing TA setup instructions and deprecated dependencies were only identified after additional setup work.
  - Some duplicate detection and delete-account issues revealed deeper design or schema problems that were not obvious earlier.

- **Cross-platform and data migration concerns added overhead**
  - The Docker workflow was originally created on macOS, so Windows verification had to be done afterward.
  - The new Docker storage strategy also meant previously saved local login credentials no longer worked, requiring new local accounts.

- **Edge-case debugging consumed time**
  - A number of bugs only appeared in specific sequences such as upload → delete → re-upload or mixed duplicate/new multi-file flows, making them harder to isolate and validate.

---

## How These Reflections Shape Next Cycle’s Plan

- Prioritize **Milestone 3 implementation** while continuing targeted Milestone 2 polish.
- Improve **team coordination** and earlier communication around setup, testing, and documentation gaps.
- Continue hardening **multi-project analysis**, **duplicate detection**, and **resume/portfolio integration**.
- Address deeper technical debt areas that were exposed this week, including:
  - remaining duplicate detection issues
  - delete-account cascade cleanup
  - loading/progress behavior for multi-project analysis
  - tighter cross-platform setup consistency
- Extend recently added features into next-step improvements such as:
  - role prediction integration into resume/portfolio generation
  - better multi-project loading animation
  - user-provided API key support for frontend LLM workflows

---

## Test Report

- **Setup and Docker validation**
  - Unified Docker environment verified through build/startup checks, health checks, auth flow testing, persistence validation, and Windows compatibility testing  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/416  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/411

- **Multi-project analysis and Analyze page validation**
  - Manual and automated verification of the multiproject analysis fix  
  - Progress bar and UI behavior improvements validated during Analyze page work  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/414  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/420

- **Resume generation regression coverage**
  - Resume generation flow fixed and validated locally
  - Backend and frontend regression tests added, including `ErrorBoundary` coverage and request format validation  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/425  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/426

- **General test stabilization**
  - Legacy/stale test fixes and broader test-suite cleanup  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/412

- **Auth/settings validation**
  - Password change and logout verified through targeted auth testing  
  - Delete Account flow covered with Settings page tests  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/418  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/428

- **Duplicate detection scenario validation**
  - Eight distinct manual duplicate-detection scenarios tested and confirmed  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/431

---

## Project Burnup Chart

<img width="1787" height="928" alt="image" src="https://github.com/user-attachments/assets/72e4f857-ccb7-4079-8979-22567bfb5a7e" />

