# Mandira Samarasekara

# Aakash Tirithdas

# Mithish Ravisankar Geetha

## Date Ranges

February 9-March 1
![Mithish Week 8](../images/MithishW8T2.png)

## Goals for this week (planned last sprint)

- Complete frontend integration for incremental upload feature
- Complete the incremental upload feature
- Continue improving frontend-backend communication using FastAPI
- Fix any additional bugs found during peer testing
- Finalize all API endpoints and fix tests
- Present the milestone 2 requirements in class

## What went well

The most significant achievement this sprint was the successful stabilization and delivery of Milestone 2. 
On the technical side, the Incremental Upload system is now fully operational. This was a complex requirement; the system successfully detects if an uploaded project has more than 30% changes compared to the existing version. If it exceeds this threshold, the portfolio and database are updated accordingly. I also built a specialized frontend polling mechanism that tracks the background analysis task. Once complete, it triggers a detailed results modal that gives the user granular feedback on exactly which projects were newly added, which were updated with specific change percentages, and which were skipped to avoid duplicates.

Furthermore, the API documentation was a major success. By adding a comprehensive guide and satisfying all Milestone 2 API requirements, I’ve made the backend significantly more accessible for the frontend team, reducing the time spent on "trial and error" integration.

## What didn't go well
The primary challenge this sprint was technical debt. After refactoring our monolithic server into a modular FastAPI structure, our test suite was breaking. I encountered a significant number of errors in the portfolio tests and incorrect patch paths in the curation tests, where mocks were not targeting the correct functions. 

Specifically, ensuring that all API tests were properly executed over HTTP (rather than direct function calls) required a massive overhaul of our testing infrastructure. While I managed to fix the majority of failing tests for the API server and Projects endpoints, there were some outstanding tasksregarding lingering failures in the resume and tasks endpoints. These required extra debugging time that ate into the schedule for new feature development, highlighting the difficulty of maintaining high test coverage while simultaneously moving the architecture to a modular design.

## Coding tasks
- **Incremental Sync Engine:** Completed the logic to detect >30% project changes and trigger database updates, fulfilling the "later point in time" information requirement.
- **Frontend Feedback Loop:** Developed a new "incremental upload" UI section and result modal with real-time status polling for background tasks.
- **Test Infrastructure:** Migrated legacy backend tests to use `FastAPI.TestClient` for true HTTP-level validation.
- **Milestone 2 Integration:** Performed the final merge of the development branch to main and ensured all features (Resume, Portfolios, Projects) were synced.

**PRs:**
- #372 – Incremental upload detection and frontend sync
- #390 – Fix and update tests for API
- #391 – Fix API Server and projects test + API Documentation
- #392 – Merge Development to Main for milestone 2

## Testing or debugging tasks

- **Portfolios & Curation Tests:** Fixed "id" mismatch errors and corrected mock patching in curation tests to ensure accurate backend simulation.
- **HTTP Validation:** Ensured all main API endpoints have comprehensive test coverage that executes over the network stack via `TestClient`.
- **Project/Resume Regressions:** Identified and addressed failing test cases in the projects endpoints caused by the recent data-model migrations.

**PRs:**
- #390 – Fix and update tests for API
- #391 – Fix API Server and projects test + API Documentation

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
-No major blockers this week

## PR's initiated
- [#372 – Incremental upload detection and frontend sync](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/372)
- [#390 – Fix and update tests for API](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/390)
- [#391 – Fix API Server and projects test + API Documentation](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/391)
- [#392 – Merge Development to Main for milestone 2](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/392)

## PR's reviewed

- [#387 – Added delete all function + updated delete function](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/387)
- [#382 – Analyze bug fix](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/382)
- [#381 – Dashboard Statistics](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/381)
- [#379 – Added save personal information section in settings page + backend support](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/379)
- [#373 – Bug fix consent](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/373)
- [#364 – Upload api](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/364)


## Plan for next week

- Discuss milestone 3 requirements
- Fix any bugs found during milestone 2 wrap up.

# Ansh Rastogi

# Harjot Sahota

## **Date ranges**

February 9 – March 1

---

## **What went well**

- This week I completed all major updates to the Settings page by adding full support for persistent personal information management. This included backend updates, the new `DELETE /api/resume/personal-info` endpoint, improved UI, and full Vitest coverage for loading, saving, deleting, and consent behavior.

- I also helped organize and assign tasks for our team’s video demonstration. I created clear lists of all bugs and remaining todos on our branch, which helped the team stay coordinated and finish recording efficiently.

- I restored the “Delete All Projects” button since it was removed accidentally in a previous PR and fixed the broken single-project deletion flow. After debugging, both delete actions now call the correct project-based API endpoints and work cleanly end-to-end.

- During preparation for the demo, our team found small errors in the app. I helped identify and fix these so our demonstration could run smoothly.

---

## **What didn’t go well**

- My previous delete implementation stopped working because another PR changed how the delete endpoint worked. This caused a lot of debugging before I finally discovered the root cause and fixed it properly.

- While preparing for the video demonstration, we found several small code issues that took extra time to fix. It didn’t block progress, but it slowed things down and added extra stress to the week.

---

## **PRs initiated**

- **Extend Settings page with personal info deletion + full test coverage**  
  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/379  

- **Fix delete buttons + restore Delete All Projects functionality**  
  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/387  

- **Improve Personal Information + Resume workflow (backend + UI integration)**  
  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/402  

---

## **PRs reviewed**

- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/390  
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/398  
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/394  
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/389  
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/382  
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/381  
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/377  
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/373  
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/368  

---

## **Plans for next week**

Next week, I plan to implement an API key input feature in the Settings page so users can enter their own key and enable LLM-based analysis. This will require new UI work, backend support, and updates to the resume/analysis pipeline to allow the system to use the user’s stored key during generation.




# Mohamed Sakr
