# Team Log – Team 6

**Work Performed:** **Jan 12th – Jan 18th**

---

## Milestone Goals Recap

### Features in Project Plan for This Milestone

- Implement key **Milestone 2 requirements** for multi-user support and peer evaluation readiness:
  - **Req 21:** Incremental uploads (add another zipped folder to the same portfolio/résumé)
  - **Req 23:** User curation controls (allow users to choose which information is represented)
  - Enforce **user-scoped analysis storage + access** (no cross-user data leakage)
- Improve **user experience + prototype readiness**:
  - Integrate enhanced ranking system into CLI output
  - Stand up authentication frontend for Milestone 2 (login/signup + protected routes + consent)
- Strengthen **testing and stability**:
  - Add high-coverage tests for curation controls, user scoping, and ranking display
  - Address schema/db issues discovered during feature integration and migrations

### Associated Tasks / PRs Touched This Week

- **Req 23 — User curation controls**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/277  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/278  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/288  

- **User-scoped analysis (store + filter by authenticated user)**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/281  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/282  

- **Req 21 — Incremental uploads**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/283  

- **Frontend authentication + consent flow**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/280  

- **Enhanced ranking system surfaced in CLI**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/290  

- **Weekly logs**
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/286  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/291  

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

- **Task:** Req 23 — User curation controls (core implementation)  
  **Description:** Implemented full support for **user-controlled project curation**, allowing users to customize how their portfolio is represented. Added:
  - Manual project timeline corrections to fix inaccurate automated dates  
  - Attribute selection for comparisons (with smart defaults)  
  - Selection of up to 3 showcase projects for highlights/summaries  
  Implemented persistent user-scoped settings and integrated the CLI command: `mda curate`.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/277  

- **Task:** Req 23 — Curation testing suite  
  **Description:** Added **comprehensive automated test coverage** (36 tests) validating curation logic + CLI behavior to ensure correctness and prevent regressions.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/278  

- **Task:** Team coordination + heuristic evaluation preparation  
  **Description:** Scheduled and attended team meetings, aligned the team on the in-class heuristic evaluation plan, assigned responsibilities, and created/owned the **Google survey** to be used during evaluation. Also wrote weekly logs + team log, reviewed incoming PRs, and initiated PRs for progress continuity.

- **Task:** Reviewed PRs  
  **Links:**
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/288  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/283  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/281  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/291  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/286  

<img width="1534" height="105" alt="image" src="https://github.com/user-attachments/assets/54edbd3e-72f1-433a-99a4-fc02ace50cc2" />

---

### Aakash Tirathdas (**aakash-tir**)

- **Task:** Req 23 — Curation enhancements (part 2)  
  **Description:** Extended Mandira’s initial curation implementation by adding:
  - Project re-ranking controls  
  - Skill highlighting (select/pick skills to display)  
  These features complete the user curation workflow (note: not yet attached to resume/portfolio output stage).  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/288  

- **Task:** Milestone 2 alignment + meeting participation  
  **Description:** Participated in Milestone 2 discussions and planning, coordinated implementation expectations with the team, and wrote weekly personal logs.

- **Task:** Reviewed PRs  
  **Links:**
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/281  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/280  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/272  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/265  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/261  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/259  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/255  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/251  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/249  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/239  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/235
 
    
<img width="401" height="86" alt="image" src="https://github.com/user-attachments/assets/bd582b85-7ef2-49ac-98f5-5a2fccee5c18" />
<img width="787" height="80" alt="image" src="https://github.com/user-attachments/assets/7970961d-135a-4e21-88ff-fdc7c13d2b27" />

---

### Mithish Ravisankar Geetha (**MithishR**)

- **Task:** Req 21 — Incremental upload support  
  **Description:** Implemented Milestone 2 support for users to **incrementally upload additional zipped folders** for an existing portfolio/résumé while preserving previously stored data. Ensured this integrates cleanly into the existing REST API + data model flow.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/283  

- **Task:** Testing + debugging for incremental uploads  
  **Description:** Stabilized endpoints after temporary breakage caused by adapting the original API assumptions for multiple uploads per user/portfolio. Performed debugging + refactoring to ensure correct behavior and endpoint stability.

- **Task:** Collaboration + reviews  
  **Description:** Coordinated frontend-backend alignment with Ansh to ensure UI integration requirements match backend capabilities.  
  **PRs reviewed:**
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/278  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/282  

<img width="1751" height="241" alt="image" src="https://github.com/user-attachments/assets/40f963f8-cf09-48b8-8119-33c0f286700e" />

---

### Ansh Rastogi (**anshr18**)

- **Task:** Enhanced ranking integration into CLI  
  **Description:** Integrated the full **Enhanced Contribution Ranking** system into the CLI’s `analyze` output so users can view:
  - Composite score + project category  
  - Base factors (45%) + enhanced/context factors (55%)  
  - Detailed scoring breakdown and justifications for all 9 ranking factors  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/290  

- **Task:** Authentication frontend + consent flow  
  **Description:** Built the complete authentication frontend and hooked it into the FastAPI backend:
  - Login + signup pages  
  - AuthContext global state  
  - Protected routes (React Router)  
  - Consent flow persisted through backend API  
  - Token expiry tracking with automatic logout after 24 hours  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/280  

- **Task:** Test suite for ranking output  
  **Description:** Added integration testing (5 tests) validating ranking factor display correctness, weights breakdown, category visibility, and enhanced ranking justifications.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/290  

- **Task:** Reviewed PRs  
  **Links:**
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/282  

<img width="679" height="206" alt="image" src="https://github.com/user-attachments/assets/a4ce8d47-0979-4f34-8942-5ff71dd30d83" />
<img width="465" height="92" alt="image" src="https://github.com/user-attachments/assets/4e55b44e-b397-4cde-9af2-b8bacd7a2e7f" />

---

### Harjot Sahota (**HarjotSahota**)



---

### Mohamed Sakr (**mgjim101**)

- **Task:** User-scoped analysis storage + isolation enforcement  
  **Description:** Implemented full **user ownership** enforcement for analyses by:
  - Persisting `username` ownership on analysis records  
  - Filtering list/get/delete queries by authenticated owner  
  - Supporting backward-compatible DB migration (inject column safely without dropping data)  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/281  

- **Task:** High-coverage tests for user isolation + migrations  
  **Description:** Created a complete testing suite ensuring:
  - Ownership persistence on analysis  
  - Filtered listings and scoped fetch/delete  
  - NULL-username compatibility  
  - Legacy schema migration behavior  
  Fixed fixtures to initialize user + analysis DBs together and seed users to satisfy FK constraints.  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/282  

- **Task:** Reviewed PRs  
  **Links:**
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/278  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/280  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/283  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/288  

<img width="803" height="429" alt="image" src="https://github.com/user-attachments/assets/0cfe11d6-e3f9-4c75-8e77-95bbfb7042d5" />


---

## What Went Well

- **Major Milestone 2 requirements landed quickly and cleanly**
  - Req 23 user curation controls now provide meaningful user-level customization (re-ranking, skill highlighting, showcase selection, manual timeline fixes).
  - Req 21 incremental uploads enable real-world portfolio iteration without forcing a full re-upload workflow.
- **Multi-user isolation matured significantly**
  - User ownership is now enforced end-to-end for analysis records, removing cross-user leakage risks.
  - Backward-compatible migrations + strong test coverage improved stability.
- **Prototype usability improved**
  - Enhanced ranking became user-visible in the CLI with full scoring factor transparency.
  - Auth frontend (login/signup + consent + protected routes) enabled Milestone 2 multi-user workflows.

---

## What Didn’t Go as Planned

- **Database/schema issues discovered mid-week**
  - While implementing Req 23, the team discovered analyses were not properly separated per user, requiring fixes and follow-up work.
- **Endpoint stability friction during incremental upload support**
  - Adding multi-upload support exposed assumptions in the original API flow that caused temporary breaks and required extra debugging/refactoring.
- **Timezone/travel coordination overhead**
  - A few meetings were missed due to travel and time zone differences, slightly slowing synchronous alignment (still manageable via async updates).

---

## How These Reflections Shape Next Cycle’s Plan

- Prioritize **heuristic evaluation readiness**
  - Ensure every team member can run the system locally and consistently execute the evaluation tasks.
  - Finalize and polish the Google survey workflow.
- Continue Milestone 2 delivery with focus on:
  - Integration work across backend + CLI + frontend so features surface cleanly end-to-end
  - Performance checks for multi-user storage and query patterns (consider indexing if needed)
- Merge development into `main` once stability is confirmed, then begin **Req 24** if bandwidth allows.

---

## Test Report

- **Req 23 (Curation):** 36 automated tests added verifying both core logic + CLI behavior (PR #278)  
- **User isolation:** Dedicated user-scoping test suite validating ownership persistence, filtered listing, scoped delete/get, and legacy migration behavior (PR #282)  
- **Incremental upload:** Endpoint behavior validated through testing and debugging after integration changes (PR #283)  
- **Enhanced ranking visibility:** 5 integration tests added verifying CLI ranking output displays correctly and includes factor breakdown + weight split (PR #290)

---

## Project Burnup Chart

<img width="1784" height="939" alt="image" src="https://github.com/user-attachments/assets/abb9b3b4-9c38-4ae1-b82f-7eca06a980b1" />

