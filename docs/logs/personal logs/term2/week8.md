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
<img width="1097" height="643" alt="Screenshot 2026-03-01 at 10 05 33 PM" src="https://github.com/user-attachments/assets/c5bd8ed5-bce4-4df3-aaf6-dcd28d78335c" />

# Mohamed Sakr

## Date Ranges

February 9-March 1
![Mohamed Week 8](mohamedW8T2.png)

## Goals for this week (planned last sprint)

- Continue improving frontend-backend communication using FastAPI
- Fix any additional bugs found during peer testing
- Finalize all API endpoints and fix tests
- Present the milestone 2 requirements in class
- Stabilize Portfolio page end-to-end rendering by aligning backend response contracts with frontend expectations
- Improve Portfolio UI resilience (deduplication, fallback highlighted skills, and clearer available analyses labels)
- Align and expand Portfolio test coverage to prevent regressions after recent UI and API-contract updates
- Expand Milestone 2 README Service/API + Human-in-the-Loop documentation with clear high-level architecture and low-level implementation guidance
- Expanded the architecture and DFD diagrams to reflect the changes in terms of new features, API endpoints, and the frontend.
- Perform detailed code reviews across major curation/portfolio PRs to validate architecture quality, UX behavior, and backend/frontend integration risks.
- Verify that newly added curation features are protected by strong automated tests and call out any remaining regression or usability gaps.

## What went well

This week went well because I was able to fix a full end-to-end Portfolio rendering issue by aligning backend responses with frontend expectations. I updated the portfolio detail response contract so it consistently returns `items` and `portfolio_items`, which allowed the Portfolio page to render portfolio points reliably instead of showing empty states.

I also improved UI resilience by making highlighted skills derive from `portfolio_items[].skills_exercised` whenever `skills` is empty. This prevented missing-skill states when analysis data existed but was shaped differently than older frontend assumptions. In addition, I updated the "Available analyses" cards to use project names from the analysis payload instead of generic analysis type labels (LLM/NON_LLM), which made the page much clearer from a user perspective.

Another major positive was test alignment. I expanded the Portfolio page test suite so it now covers current behavior: portfolio metadata rendering, quality/sophistication display (including `project_statistics` fallback), derived highlighted skills behavior, project-name card titles, and empty-state handling. This gave me stronger confidence that these fixes are stable and less likely to regress.

## What didn't go well

The biggest challenge was debugging root causes that were split across multiple layers. The frontend symptoms looked simple ("No portfolio items", missing highlighted skills), but the real issues involved API response shape mismatches, field availability differences, and stale test expectations after UI changes. Tracing and validating all of these together took longer than expected.

I also had to spend extra effort on duplicate item behavior during reanalysis. To fully resolve it, I implemented both cleanup and fetch-side controls: removing `portfolio_items` on child reanalysis and returning only the latest portfolio item per project during analysis item fetch. This was necessary, but it added complexity and increased implementation/testing time.

## Coding tasks

- **API contract alignment:** Updated portfolio detail responses to include portfolio items in a consistent structure (`items` and `portfolio_items`) for reliable frontend rendering.
- **Deduplication and lifecycle cleanup:** Prevented duplicate portfolio items by cleaning `portfolio_items` on reanalysis and limiting analysis item fetches to the latest item per project.
- **Highlighted skills fallback logic:** Added derivation of highlighted skills from `portfolio_items[].skills_exercised` when `skills` is empty.
- **Available analyses card title fix:** Switched card titles to project names from the analysis payload instead of analysis type labels.
- **Portfolio page product update:** Removed the Summary section from the Portfolio page based on product request.
- **End-to-end rendering stabilization:** Verified that portfolio points now render consistently with real analysis data paths.



## Testing or debugging tasks

- **Portfolio test suite refresh:** Updated tests to match current UI behavior and removed outdated checks tied to the removed Summary section.
- **Metadata rendering coverage:** Added/updated tests for portfolio title, summary, tech stack, and skills rendering behavior.
- **Quality/sophistication fallback coverage:** Added explicit tests for nested `project_statistics` fallback display logic.
- **Derived highlighted skills validation:** Added tests ensuring highlighted skills still populate when `skills` is empty by using portfolio item data.
- **Available analyses labeling checks:** Added assertions that card titles come from `project_names` rather than LLM/NON_LLM labels.
- **Empty-state regression checks:** Added coverage for responses with no portfolio items to ensure graceful and correct empty-state UI.

## Reviewing or collaboration tasks

- **Reviewed comprehensive curation platform PR (backend + frontend + persistence):** Assessed the 8-endpoint FastAPI curation API, JWT-protected routes, Pydantic validation, SQLite persistence, and the full 5-tab React curation experience (showcase, comparison attributes, highlighted skills, chronology correction, custom order). Feedback highlighted strong validation/error handling, good state persistence, and well-scoped tests.
- **Reviewed consent flow bug-fix PR with UX risk callout:** Confirmed backend boolean-consent handling improvements (`save_user_consent(..., False)` default and migration helper) and new tests, while flagging a non-blocking but important UX regression: users who decline consent now enter the app and only encounter downstream 403s without clear guidance. Requested explicit messaging/gating or restoration of the prior logout clarity.
- **Reviewed thumbnail removal + console-noise cleanup PR:** Validated the new remove-thumbnail flow, blob URL revocation to avoid memory leaks, expected 404 handling for "no thumbnail" cases, and cleanup robustness. Provided polish feedback to ensure delete action feedback is visible during async operations.
- **Reviewed curation integration across Portfolio/Resume/Projects/Dashboard PR:** Manually tested curated ranking, ordering, skills/attributes propagation, chronology overrides, showcase filtering/navigation, and dashboard showcase presentation. Confirmed curated behavior works consistently across pages and called out the implementation as production-ready.
- **Reviewed follow-up curation integration test-coverage PR:** Found no blocking issues; verified backend/frontend coverage for highlighted-skills precedence, API forwarding, showcase rendering/navigation, sorting/filter states, and error/empty/loading paths. Confirmed test execution results (20/20 backend pass, 29/29 frontend pass) and noted only minor environment-warning noise with no functional impact.

## Non coding tasks
- **README documentation PR (Milestone 2 Service/API + HITL):** Expanded the README section to clearly describe the FastAPI service as the frontend/backend mediator and added implementation-level details for API contracts/OpenAPI generation, async job lifecycle orchestration, local session/profile isolation, incremental ZIP ingest behavior, deduplication + canonical artifact storage, and Human-in-the-Loop curation workflows (representation overrides, role attribution, evidence linking, thumbnail association, saved showcase/resume wording customization, and portfolio/resume text rendering). Also added a dedicated FastAPI endpoint map covering health checks, portfolio lifecycle, ingest/jobs, curation updates, and text rendering endpoints.
- **Updated our architecture and DFD diagrams:** Expanded the architecture and DFD diagrams to reflect the changes in terms of new features, API endpoints, and the frontend.

## **Issues / Blockers**
-No major blockers this week

## PR's initiated
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/375
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/377
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/403

## PR's reviewed
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/399
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/395
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/389
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/373
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/368
