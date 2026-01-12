# Team Log – Team 6

**Work Performed:** **Jan 5th – Jan 11th**

---

## Milestone Goals Recap

### Features in Project Plan for This Milestone

- Stand up the **Milestone 2 backend foundation (REST API)**:
  - Implement FastAPI server structure, authentication, and core endpoint scaffolding.
  - Support user-scoped portfolio operations, background processing, and persistent file handling.
  - Add deduplication + storage groundwork to enable scalable uploads and analysis.
- Strengthen **Git analysis, ranking, and portfolio insights**:
  - Improve contributor-aware project ranking with multi-factor scoring.
  - Expand Git metrics coverage (language detection, ownership, duration, activity types, skills).
  - Improve reporting outputs and reduce “unknown/Other” buckets.
- Improve **testing, stability, and Milestone 2 planning cadence**:
  - Add/extend unit tests (incl. Java complexity + ranking tests).
  - Review pending PRs, resolve regressions early, and align ownership for Milestone 2 requirements.

### Associated Tasks / PRs Touched This Week

- **REST API (Milestone 2) + Authentication**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/265
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/272

- **Contribution ranking / project scoring**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/267
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/268

- **Java complexity + testing**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/262
  - (Winter Break) PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/245

- **Git analysis & metrics features (1–12) + schema foundations**
  - PRs:
    - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/235
    - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/237
    - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/239
    - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/241
    - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/243
    - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/247
    - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/249
    - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/251
    - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/253
    - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/255
    - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/257
    - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/259
    - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/261

- **Weekly logs**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/270

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

- **Task:** Enhanced REST API implementation (Milestone 2)  
  **Description:** Implemented a complete REST API foundation with FastAPI server integration, secure authentication, user-scoped portfolio management, background processing with task status tracking, SHA256-based deduplication with permanent storage, DB extensions for user-scoped operations, and stronger endpoint error handling. Added automated tests and performed end-to-end manual validation of server startup and auth flows.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/272

- **Task:** Team coordination + Milestone 2 alignment  
  **Description:** Attended all team meetings, participated in check-ins, met with Mithish to align REST API architecture and task ownership, and documented weekly progress (team logs).

- **Task:** Reviewed PRs (8 total)  
  **Links:**
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/270
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/268
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/265
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/262
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/257
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/249
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/241
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/237

---

### Aakash Tirithdas (**aakash-tir**)

- 

---

### Mithish Ravisankar Geetha (**MithishR**)

- **Task:** REST API server structure + authentication scaffolding  
  **Description:** Designed and implemented the initial API endpoint structure required for Milestone 2, aligning with existing architecture and enabling smoother future integrations. Coordinated with Mandira to clarify responsibilities and avoid overlap.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/265

- **Task:** Winter break development — Java complexity + unit testing  
  **Description:** Added Java complexity analysis and implemented unit testing to validate complexity behaviors.  
  **PRs:**
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/245
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/262

- **Task:** Reviewed PRs  
  **Links:**
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/237
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/241
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/251
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/259
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/261

---

### Ansh Rastogi (**anshr18**)

- **Task:** Enhanced Contribution Ranking algorithm  
  **Description:** Implemented a multi-factor ranking system to improve project scoring quality in collaborative repos. Added contextual factors (individual contribution weight, recency bonus, project scale, collaboration diversity, activity duration) and a weighted scoring split between technical base scores (45%) and contribution/context factors (55%). Added five-tier project categorization to help users identify high-impact projects.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/267

- **Task:** Testing + stability fixes  
  **Description:** Fixed a contributor lookup bug in `calculate_contribution_score()` after tests failed, and patched a backward-compatibility test break caused by updated ranking output formatting (caught via CI).

- **Task:** Reviewed PRs  
  **Links:**
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/239
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/243
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/247
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/253
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/257

---

### Harjot Sahota (**HarjotSahota**)

- 

---

### Mohamed Sakr (**mgjim101**)

- **Task:** Wrap up + document Git Analysis & Metrics Features (1–12)  
  **Description:** Completed and consolidated Git analysis improvements across insights/ranking, data foundations, schema persistence, and reporting. Key additions included contributor insights (language usage, trivial vs substantial split, ownership signals via blame, noreply filtering), expanded language detection to shrink “Other”, schema extensions for ownership/semantic stats/language breakdowns and skill storage, project duration metrics, activity-type classification (Code/Test/Docs/Design), contribution-aware ranking for single-user + multi-project ranking, and explicit zero-contribution transparency. Improved portfolio summaries and fixed prior “zero contributor/branch count” output bugs.

- **Task:** PRs initiated (winter break through Jan 11 range)  
  **Links:**
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/235
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/237
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/239
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/241
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/243
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/247
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/249
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/251
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/253
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/255
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/257
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/259
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/261

- **Task:** Reviewed PRs  
  **Links:**
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/262
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/269

---

## What Went Well

- **Milestone 2 backend foundation progressed quickly**:
  - REST API structure + authentication landed as a strong base, then was extended into a more complete production-ready implementation with background tasks, deduplication, and persistent storage.
- **Project ranking and Git insights became more meaningful**:
  - Enhanced contribution ranking introduced richer contextual scoring and clearer project categorization.
  - Git analysis improvements reduced “Other/unknown” results and improved clarity via activity mix, ownership signals, and explicit zero-contribution reporting.
- **Strong coordination despite distributed schedules**:
  - Early alignment on API architecture and ownership reduced overlap and helped development move in parallel.
- **Testing + CI caught issues early**:
  - Bugs in contribution scoring and output formatting were surfaced quickly and fixed before they spread.

---

## What Didn’t Go as Planned

- **Coordination friction due to travel/time zones**:
  - Some members were out of town / in different time zones, which made real-time alignment harder (but manageable with proactive communication).
- **Performance + edge cases surfaced in Git-heavy workflows**:
  - Large blame sweeps and multi-project ranking introduced performance hits that need tuning and more load testing.
  - Skill extraction still has edge cases (e.g., sparse histories) that need better fixtures and automated coverage.
- **Extra iteration caused by scoring + formatting regressions**:
  - A contributor lookup bug caused multiple test failures initially.
  - Output format changes broke an existing test and required compatibility patches.

---

## How These Reflections Shape Next Cycle’s Plan

- Continue Milestone 2 execution with focus on:
  - **Req 21:** incremental uploads (add another zipped folder to same portfolio/résumé).
  - **Req 22:** duplicate file recognition + single-instance storage.
  - **Req 23:** allow users to choose which information is represented.
- Add **performance tuning + load testing** for blame-heavy and multi-project ranking workflows.
- Expand automated **test fixtures** for skill extraction and sparse-history repos.
- Improve team sync cadence now that members are returning to regular schedules.

---

## Test Report

- **REST API:** Full suite execution reported passing (e.g., 19/19 tests on the API auth foundation PR), plus manual validation of server startup and health/auth flows.
- **Ranking:** Comprehensive test suite added; CI caught early regressions (contributor lookup bug + output-format assertion) and fixes were applied.
- **Java complexity:** Unit testing work completed to validate analysis correctness.
- **Git analysis:** Functional improvements validated through feature development, but follow-up performance testing and broader fixtures are still needed.

---

## Project Burnup Chart

- 
