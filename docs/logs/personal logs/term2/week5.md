# Mandira Samarasekara

# Aakash Tirithdas


# Mithish Ravisankar Geetha

## Date Ranges

January 26-February 8
![Mithish Week 3](../images/MithishW4W5T2.png)

## Goals for this week (planned last sprint)

- Attend peer testing session and gather feedback
- Provide feedback for other teams during peer testing
- Fix any bugs identified during peer testing
- Continue polishing frontend UI based on user feedback
- Integrate remaining frontend components with backend API endpoints
- Create interactive resume generator module including pdf and mark generaation
- Expand on the incremental upload feature.  

## What went well

On the backend, I implemented all major API endpoints for projects, resume, portfolio, privacy consent, tasks, analysis, authentication, and health, fulfilling the Milestone 2 requirements. I also refactored the original monolithic api_server.py into a modular structure, which greatly improved maintainability, readability, and scalability. Comprehensive unit tests were added across these services to ensure correct functionality, error handling, and security.

On the frontend and feature side, I built a complete interactive resume generation system that allows users to create professional resumes in Markdown, PDF, and LaTeX (Jake’s Resume template) formats directly from their portfolio and project data. This included proper markdown resume preview rendering, fixes for missing resume information (such as location and website links), token storage fixes to resolve authentication issues between endpoints, PDF generation using reportlab, LaTeX generation using pdflatex, and support for personal information customization.

I also implemented intelligent incremental upload handling to detect project changes and merge updates without creating duplicates, improving overall portfolio data consistency.

The peer testing session went well and provided useful, actionable feedback. We identified a security issue where passwords were visible in the CLI and learned that, while the system functioned correctly, the CLI was not intuitive due to the lack of menu guidance. It was also helpful to see how different teams interpreted the CLI requirements. Additionally, I reviewed several PRs from teammates and other groups, contributing to collaboration and code quality.

## What didn't go well

The initial API PR was very large due to the scope of work, which required unit tests to be split into separate follow-up PRs. While the refactor was beneficial long-term, it required extra coordination and time.

Peer testing also highlighted that although the system functioned correctly, the CLI lacked intuitiveness due to the absence of menu guidance, which will need to be addressed in future iterations.
## Coding tasks
- Implemented and refactored all major API endpoints into a modular architecture
- Built a complete interactive resume generator (Markdown, PDF, LaTeX)
- Implemented markdown resume preview rendering
- Fixed resume information bugs (location, website, formatting)
- Implemented incremental project upload intelligence with change detection
- Implemented token storage module to fix authentication issues
- Integrated resume generation APIs with frontend interface

**PRs:**
- #301 – API Endpoints  
- #324 – Fix consent form bug  
- #334 – Frontend Resume Generator  
- #336 – Interactive Resume Generator  
- #346 – Markdown resume preview and resume information bug fixes  
- #356 – Incremental Information Upload (Updated)  

## Testing or debugging tasks


- Wrote unit tests for:
  - analysis, auth, portfolios, projects
  - tasks, resume, health, API server
- Tested resume generation across Markdown, PDF, and LaTeX outputs  
- Debugged authentication token recognition across endpoints  
- Fixed resume rendering and missing information bugs  
- Identified and documented security issue from peer testing (password visibility in CLI)  

**PRs:**
- #318 – Unit tests for analysis, auth, portfolios, projects  
- #319 – Unit tests for tasks, resume, health, API server  

## Reviewing or collaboration tasks

- #290 – Enhanced Contribution Ranking Integration  
- #306 – Project thumbnail  
- #308 – Updated Dashboard  
- #311 – Resume/portfolio items display on Projects page  
- #304 – Prevent Duplicate LLM Saves During Analysis  
- #350 – Migrate resume generation from portfolio IDs to project IDs  
- #348 – Update consent feature in settings + tests  
- #345 – Delete button functionality + UI + tests  
- #333 – Upload zip file page  

## **Issues / Blockers**

- No major blockers this week.

## PR's initiated

- [#301 – API Endpoints](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/301)  
- [#318 – Unit tests (analysis, auth, portfolios, projects)](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/318)  
- [#319 – Unit tests (tasks, resume, health, API server)](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/319)  
- [#324 – Fix consent form bug](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/324)  
- [#334 – Frontend Resume Generator](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/334)  
- [#336 – Interactive Resume Generator](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/336)  
- [#346 – Markdown resume preview and resume information bug fixes](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/346)  
- [#356 – Incremental Information Upload (Updated)](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/356)  
- [#318 – Unit tests for analysis, auth, portfolios, projects](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/318)  
- [#319 – Unit tests for tasks, resume, health, API server](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/319)  


## PR's reviewed

- [#290 – Enhanced Contribution Ranking Integration](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/290)  
- [#306 – Project thumbnail](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/306)  
- [#308 – Updated Dashboard](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/308)  
- [#311 – Resume/portfolio items display on Projects page](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/311)  
- [#304 – Prevent Duplicate LLM Saves During Analysis](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/304)  
- [#350 – Migrate resume generation from portfolio IDs to project IDs](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/350)  
- [#348 – Update consent feature in settings + tests](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/348)  
- [#345 – Delete button functionality + UI + tests](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/345)  
- [#333 – Upload zip file page](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/333)  

## Plan for next week

- Complete frontend integration for incremental upload feature  
- Continue improving frontend-backend communication using FastAPI  
- Fix any additional bugs found during peer testing  

# Ansh Rastogi

# **Harjot Sahota**

## **Date ranges**

January 26th – February 8th
<img width="1078" height="633" alt="Screenshot 2026-02-07 at 7 47 28 PM" src="https://github.com/user-attachments/assets/184e0af3-a46c-4ee7-ab85-72dc6b934df0" />

---
## **What went well**

- These 2 weeks I completed two major features: the **Settings consent update UI** and the **Delete All Projects** functionality. Both included full frontend work, backend updates, and database tests.

- In **PR #348**, I added the consent toggle on the Settings page, including loading the user’s consent status, a confirmation modal, and clear success/error feedback. The UI now matches the app’s style, and all related frontend tests are passing.

- In **PR #345**, I added a bulk project deletion flow with a new `DELETE /api/projects` endpoint, full user-scoped backend logic, UI updates, and database tests to verify that only the authenticated user’s projects are removed.

- I also merged **PR #338**, which added per-project deletion with improved Projects page UI and full backend authorization checks. Both manual and automated tests confirmed the end-to-end flow works reliably.

- All PRs passed CI, and manual checks ensured UI updates, confirmation flows, and DB state behaved correctly after deletion and after logout/login. Overall, I shipped multiple stable features and strengthened my understanding of frontend–backend integration and testing.

- I identified and fixed a critical data-model bug in the resume generation flow where portfolio (analysis) IDs were incorrectly used instead of project IDs. I refactored the backend resume API, resume generator, and frontend resume page to be fully project-based, ensuring resume bullets are correctly sourced per project and that project deletion now cascades cleanly without breaking resume generation. This resolved duplicated/missing resume entries and aligned the feature with the database ownership model.


---
## **What didn’t go well**

- Nothing major went wrong this week, but I did discover an important bug in our system: we were using two different unique identifiers for projects, which caused portfolio_items not to delete when the associated project was deleted. This issue wasn’t obvious at first and took time to trace through the database and backend logic.

- The bug is now fully fixed, but identifying it highlighted how critical consistent IDs are for future features and data integrity. While it didn’t block my work, it added extra debugging time and reminded me to double-check identifier flow across the stack.

---
## **PRs initiated**

- **Add update consent feature in Settings + tests**  
  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/348

- **Add delete all projects functionality (UI + backend + DB tests)**  
  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/345

- **Add per-project delete feature with UI updates and backend cleanup**  
  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/338

- **Migrate resume generation from portfolio IDs to project IDs**    
https://github.com/COSC-499-W2025/capstone-project-team-6/pull/350

---
## **PRs reviewed**

- **Markdown resume preview and resume information bug fixes**  
  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/346

- **Role prediction curation (CLI + database + tests)**  
  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/342

- **Interactive resume generator**  
  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/336

- **Frontend Resume Generator**  
  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/334

- **Role prediction tests**  
  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/330

---

## **Plans for next week**

Next week I will work on removing portfolio_id usage end-to-end (it still exists in the database + tests + function calls). This will require refactoring backend endpoints and database access patterns that still depend on portfolio UUIDs, updating frontend flows (Upload/Analyze/Curate), and rewriting/adjusting related tests to match the new project-based model.


# Mohamed Sakr

