# Mandira Samarasekara

# Aakash Tirithdas

## Date Ranges

March 15 - March 29
![Aakash Week 10](../images/aakasht2w12.png)

## What went well

The presentation went well
majority of bugs were fixed

## Coding tasks

- implemented saving job analysis, can delete and view them

## Testing or debugging tasks

- partially fixed increamental upload. was a deep seeded bug which could not be fixed, small fixes were made
- fixed bugs in portfolio tests
- curate ranking debug to show numbers instead of checks
- fixed small bugs in multi-project analysis
  - loading bar bug
  - error message now more user friendly
- fixed delete account bug

## Document tasks

- finalaized architecture and data flow diagrams for milestone 3

## Reviewing or collaboration tasks

Too many to refer to reviewed PR to find what was reviewed

## Issues / Blockers

No major blockers this week

## PR's initiated

- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/503
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/500
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/496
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/483
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/481
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/480
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/464

## PR's reviewed

- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/494
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/492
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/490
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/489
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/485
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/479
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/470
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/462
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/452
-

## Plan for next week

tie up loose ends and complete the project

# Mithish Ravisankar Geetha

## Date Ranges

March 9 - March 15
![Mithish Week 10](../images/MithishT2W12.png)

## Goals for this week (planned last sprint)

- Finalize Milestone 3 core requirements, including the Portfolio customization system.
- Resolve session persistence issues caused by Docker container restarts.
- Implement visual data representations (Activity Heatmap) for the developer portfolio.
- Execute full project rebranding to "Blume" for consistent UI/UX across the platform.
- Fix critical bugs regarding duplicate project uploads and orphaned portfolio entries.

## What went well

This week marked the successful wrap-up of Milestone 3. The implementation of the **GitHub-style activity heatmap** and the **Smart Role Assessment** significantly enhances the professional utility of the portfolio. A major technical hurdle was cleared by moving authentication tokens from in-memory storage to a persistent SQLite database; this ensures users remain logged in even after server restarts. Additionally, the transition to the "Blume" branding was executed across all UI elements, providing a much cleaner and more professional identity for the application.

## What could have been done better

While the automated portfolio cleanup logic was successfully implemented, the initial logic for "Smart Role Assessment" required several rounds of debugging to ensure it correctly aggregated skills across multiple projects without performance lag. Earlier communication on the rebranding assets could have streamlined the CSS updates, as the process involved touching 16+ frontend files simultaneously to ensure consistency.

## Coding tasks

- **Session Persistence:** Developed a custom class behaving like a dictionary but backed by a SQLite `tokens` table to persist Auth tokens across backend restarts.
- **Portfolio Heatmap:** Created a calendar-style activity grid that visualizes project intensity via dot size and color density, including productivity stats like streaks and total commits.
- **Smart Portfolio Summary:** Built a dynamic branding system and an analyzer that scans all projects to determine primary developer roles and aggregate the top 8 skills.
- **Project Rebranding:** Updated all UI elements and naming conventions from "MDA Portfolio" to "Blume" for a unified brand identity.
- **Duplicate Detection:** Implemented client-side file signature comparison to prevent users from uploading duplicate projects.

## Testing or debugging tasks

- **Persistence Testing:** Verified that restarting Docker containers no longer clears the `tokens` dictionary, allowing sessions to remain active.
- **Portfolio Cleanup Validation:** Confirmed that deleting the last project in a portfolio now triggers an automatic cleanup of orphaned analysis entries.
- **UI Responsiveness:** Tested the new heatmap and portfolio summary sections across desktop, tablet, and mobile views to ensure visual consistency.

## Document tasks

- **Milestone 3 Documentation:** List of any unsolved bugs has been created.

## Reviewing or collaboration tasks

- **UI Layout Review:** Reviewed PR #460 to ensure the new persistent education entries and inline PDF preview matched the updated resume layout.
- **Bug Validation:** Collaborated with team members on fixing frontend bugs and multi-project upload issues (PR #477, #480).
- **Public Mode Strategy:** Reviewed the implementation of the Portfolio public mode (PR #494) to ensure data privacy and customization settings are respected.

## Issues / Blockers

No major blockers this week

## PR's initiated

- **Bug Fix: Persist Auth tokens across backend restarts #465** (https://github.com/COSC-499-W2025/capstone-project-team-6/pull/465)
- **Portfolio heatmap #468** (https://github.com/COSC-499-W2025/capstone-project-team-6/pull/468)
- **Bug Fixes and Enhancements + Rebranding #475** -https://github.com/COSC-499-W2025/capstone-project-team-6/pull/475
- **Merge Branch Development to Main for milestone - Project Wrap up #488** -https://github.com/COSC-499-W2025/capstone-project-team-6/pull/488

## PR's reviewed

- **Improve Resume page layout + persistent education entries #460** (https://github.com/COSC-499-W2025/capstone-project-team-6/pull/460)
- **Frontend bug fixes #477** (https://github.com/COSC-499-W2025/capstone-project-team-6/pull/477)
- **Aakash/multiproject bug #480** (https://github.com/COSC-499-W2025/capstone-project-team-6/pull/480)
- **Added Initialisation Document #489** (https://github.com/COSC-499-W2025/capstone-project-team-6/pull/489)
- **Portfolio public mode #494** (https://github.com/COSC-499-W2025/capstone-project-team-6/pull/494)

## Plan for next week

- Fix any other bugs found during testing
- Milestone complete.

# Harjot Sahota

## Date Ranges

March 16 - March 29
<img width="1077" height="636" alt="Screenshot 2026-03-28 at 11 59 02 AM" src="https://github.com/user-attachments/assets/223c2d75-8616-44b6-82f8-cebee975cdb0" />

## What went well

these weeks were very busy, and I made several major improvements to the resume page and overall user experience of the application.

I improved the layout of the Resume page to make it easier for users to navigate and use. As part of that work, I added an inline preview section so users can now preview their generated resume before downloading it, which makes the resume generation flow much more convenient and user-friendly.

I also made generated resumes savable, and they can now be viewed later in a stored resumes section. In that section, users can view and delete previous resume generations. This makes the feature much more user-friendly because users can keep the resumes they want instead of losing them after generation. Saving is also optional, so users can choose whether or not they want to store a generated resume.

I updated the Education section to support full CRUD functionality. Users can now save, edit, and delete their education entries, which means they no longer have to re-enter their education information every time they log in and generate a resume. This makes the feature much more practical for repeated use.

In addition, I added a Work Experience section to the Resume page. Users can now enter work experience entries that are automatically displayed in reverse chronological order, and this section also supports full CRUD functionality so users can save their work history for future resume generations.

Outside of the Resume page, I also added a logout button to the navigation bar. Previously, the logout option was only available on the dashboard, which was inconvenient for users. Moving it to the navigation bar makes logging out much easier and more accessible from anywhere in the app.

I also fixed several smaller bugs in the codebase in preparation for the final demo, including UI issues, visibility problems, and other minor fixes that helped make the application feel more polished and stable.

Another thing that went well was that our group met together for the project demo, and we all collaborated to create the demo video. That was a good team effort and helped us prepare our final presentation as a group.

Overall, this week went well because I contributed multiple meaningful frontend improvements that made the application more functional, persistent, and user-friendly, while also helping the team prepare for the final demo.

## What didn’t go well

One thing that did not go well this week was that two of my PRs for the Resume page were very large and closely connected, with a lot of new implementation and changes across the page.

My first PR had a bug where the resume PDF preview would not display correctly, even though the follow-up PR, which depended on the first one, had the preview working properly. After debugging, I realized that I had fixed the issue in the second PR but forgot to apply the same fix back to the first PR. This caused extra confusion and made the review process harder.

This taught me that large connected PRs can be difficult to manage, especially when fixes are made in one branch but not carried back into the earlier dependent branch. It was a good lesson in being more careful when working across stacked or related PRs.

## PRs initiated

Work experience section https://github.com/COSC-499-W2025/capstone-project-team-6/pull/462

Added logout button to navigation bar https://github.com/COSC-499-W2025/capstone-project-team-6/pull/458

Improve Resume page layout + add persistent education entries + inline PDF preview https://github.com/COSC-499-W2025/capstone-project-team-6/pull/460

frontend bug fixes https://github.com/COSC-499-W2025/capstone-project-team-6/pull/477

Implemeted save resume generation + tests https://github.com/COSC-499-W2025/capstone-project-team-6/pull/479

## PRs reviewed

Job description Matching https://github.com/COSC-499-W2025/capstone-project-team-6/pull/467

made changes to the database to fix the delete account bug https://github.com/COSC-499-W2025/capstone-project-team-6/pull/464

Aakash/multiproject bug https://github.com/COSC-499-W2025/capstone-project-team-6/pull/480

Bug Fixes and Enhancements + Rebranding https://github.com/COSC-499-W2025/capstone-project-team-6/pull/475

Job Match Page UX Improvements https://github.com/COSC-499-W2025/capstone-project-team-6/pull/473

Portfolio Private Mode and Interactive Portfolio Summary https://github.com/COSC-499-W2025/capstone-project-team-6/pull/471

## Plans for next week

Next week I plan to improve the stored resumes feature by allowing users to download resumes they have saved. Right now, users can only view their stored resumes, so adding download support would make the feature much more useful and complete.

If I have time, I also want to improve the existing feature that lets users update a resume by adding content from their saved projects. Currently, this feature is only available for markdown resumes, so I would like to add support for PDF uploads as well.

# Mohamed Sakr

![Mithish Week 10](../term2/mohamedt2w12.png)

## Date Range

March 16 - 29

## Goals for this week (planned last sprint)

- Finalize Milestone 3 core requirements, including analysis bugs and documentation.
- Fix Bugs with LLM analysis
- Construction of a Fully Autonomous Job Application AI Agent

## What went well

Successfuly fixed issues related to retrying analysis in the event of failure. Prior, when an analysis fails, the retry button us not functional. Now the button restarts the analysis project. Also, we were able to fix all bugs with LLM analysis.

## Coding tasks

- **Gate LLM execution on explicit user opt-in** (`task_manager.py`): Add a condition so LLM analysis only runs when both user consent is present **and** `analysis_type == "llm"`, preventing LLM from running for consented users who didn't check the LLM checkbox.

- **Expose `analysis_type` through the projects API** (`curation.py` + `ProjectsPage.jsx`): Include `analysis_type` in the `GET /api/projects` SQL query response, then conditionally render `LlmAnalysisPanel` in the frontend only when `p.analysis_type === 'llm'`.

- **Fix loading screen phase messaging and upload state passing** (`AnalyzePage.jsx` + `Upload.jsx`): Update phase message logic to check both `analysisPhase` and `analysisType` so the correct label ("LLM" vs "Non-LLM") always displays, and ensure `effectiveAnalysisType` is consistently passed via navigation state and `sessionStorage` for multi-file uploads.

- Fix "Retry" button to navigate to /upload instead of re-polling (AnalyzePage.jsx): Replace the beginPolling() call with a navigation to /upload, since failed tasks are in a terminal backend state and cannot be restarted — and rename the button label from "Retry" to "Try Again" to accurately reflect the behavior.

- Document/stub the non-functional reanalyze endpoint (portfolios.py or equivalent): Note that /api/analysis/portfolios/{id}/reanalyze remains 501 Not Implemented and does not retain original files, so re-upload is the only valid recovery path until a true restart mechanism is built.

- • **Build `applypilot`, a 6-stage autonomous job application CLI** (`cli.py`, `pipeline.py`, `discovery/`, `llm.py`, `database.py`, `scoring/validator.py`, `apply/launcher.py`, `config.py`): Implement the full pipeline — scraping 80+ job sources, enriching descriptions via a 3-tier cascade, LLM scoring against a user profile, per-job resume/cover letter tailoring with fabrication detection, and Claude Code + Playwright MCP-driven form submission — orchestrated via Typer CLI with SQLite-backed resumable state, a live Rich dashboard, and a dependency-gated tier system.

**IMPORTANT: The AI agent feature was an experimentation. The agent is full functional (tested by applying to 200+ jobs in 2 days). Yet due to time constraint, we were not able to integrate it into the complete application. All that's left is include it in the frontend and connect API endpoints. The PR is open if needed for future development.**

## Testing or debugging tasks

- Verified that the retry button works for all types of failed analysis.
- Verified that llm analysis only runs when consented and selected per project

## Document tasks

- **Milestone 3 Documentation:** Projects page.

## Reviewing or collaboration tasks

- Approved PR moving logout button into the shared Navigation component (accessible from any page), removing redundant logout logic from `Dashboard.jsx`.
- Approved PR fixing account deletion in Docker by splitting the `delete_user_account` function to use separate DB connections for `analysis.db` (analyses, uploads, user_profile, user_resumes) and `myapp.db` (users, user_consent), resolving a `no such table` error caused by the two databases being at different paths in Docker but the same path locally.
- Approved PR improving the Curate page UX: clearer language, renamed "Comparison Attributes" to "Project Comparison Fields", added guidance text and a "Go to Portfolio" shortcut, removed the confusing Project Order section, and cleaned up Portfolio comparison table behavior.
- Approved PR adding a frontend test report to the docs folder.
- Approved PR updating architecture and data flow diagrams.

## Issues / Blockers

No major blockers this week

## PR's initiated

- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/506
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/498
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/474 (**IMPORTANT: The AI agent feature was an experimentation. The agent is full functional (tested by applying to 200+ jobs in 2 days). Yet due to time constraint, we were not able to integrate it into the complete application. All that's left is include it in the frontend and connect API endpoints. The PR is open if needed for future development.**)
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/470

## PR's reviewed

- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/496
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/495
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/492
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/464
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/458

## Plan for next week

- Fix any other bugs found during testing
- Milestone complete.

# Ansh Rastogi

## Date Ranges

March 15 – March 29
![Ansh Week 12 Term 2](../images/AnshRastogi_PeerEval_SS_W12T2.png)

## Goals for this week (planned last sprint)

- Begin working on the assigned Milestone 3 feature task
- Continue supporting teammates with frontend integration and review work

## What went well

This two-week sprint went well overall. The main highlight was delivering the **Job Description Matching** feature end-to-end — building the Gemini AI backend integration, writing the match scoring logic against a user's projects and skills, and wiring it up to a new `JobMatchPage.jsx` in the frontend. After that shipped, I followed up with a UX pass that added an animated loading progress bar and dynamic circular score rings to make the results feel more polished and responsive.

On the bug-fixing side, I addressed several issues across different layers of the stack. The JSX syntax errors in `Resume.jsx` were blocking the Vite dev server entirely, so those were a quick but important fix. The frontend cleanup PR caught a few categories of low-level noise — a controlled/uncontrolled input warning on the Settings page, unstable list keys on the Projects page, and leftover debug logs and console errors from tests. The backend test fix was more involved: 14 tests were failing due to two missing API endpoints and stale schema expectations, so I implemented the missing routes and updated the schemas to match the current API.

## What could have been done better

- The 14 failing backend tests pointed to missing endpoints that should have been caught earlier. A shared API contract or a brief check against the test suite at the start of implementation would have surfaced these gaps before they accumulated.
- The job matching feature and the Job Match page UX improvement were closely related enough that they could have shipped as one PR. Splitting them added review overhead and a short window where the feature existed without the polished UI.

## Coding tasks

- Implemented the **Job Description Matching feature**
  - Integrated Google Gemini AI to analyze a user's uploaded projects and skills against a pasted job description
  - Built a match scoring system that returns an overall score plus per-category breakdowns
  - Added `GET /api/job-match` endpoint in the backend to serve match results
  - Created `JobMatchPage.jsx` in the frontend to collect job description input and display analysis output
- Implemented **Job Match Page UX improvements**
  - Added an animated loading progress bar shown while Gemini analysis is running
  - Added dynamic circular score rings to visualize match scores per category
- Fixed **three JSX syntax errors in `Resume.jsx`** that were preventing the Vite dev server from starting
- Fixed **multiple frontend issues**
  - Resolved controlled/uncontrolled input warning on the Settings page
  - Fixed unstable list keys on ProjectsPage causing React reconciliation noise
  - Removed debug logs from `Upload.jsx` and suppressed console error noise in tests
- Fixed **14 failing backend tests**
  - Implemented the missing `GET /` root endpoint
  - Implemented the missing `POST /api/tasks/{task_id}/cancel` endpoint
  - Updated stale test schemas to match the current API response shapes

## Testing or debugging tasks

- Tested the job match scoring flow end-to-end across several project and job description combinations, verifying that scores reflected realistic skill alignment
- Confirmed the Vite build succeeds after the JSX syntax fixes and that the Resume page loads cleanly
- Ran the full backend test suite after adding the missing endpoints and schema updates, confirming all 14 previously failing tests pass

## Document tasks

- Wrote a comprehensive **INITIALISATION.md** setup guide covering both the Docker path and local development path for new contributors, including prerequisites, environment configuration, and first-run steps
- Documented the missing backend API endpoints including descriptions for `GET /` and `POST /api/tasks/{task_id}/cancel`, and documented the schema changes required to bring tests in line with the current API

## Reviewing or collaboration tasks

- Reviewed **Projects page LLM analysis integration**
  - Verified the Gemini analysis display panel renders correctly per project
  - Confirmed the `sqlite3.Row` operator fix and LLM summary persistence are working
- Reviewed **updated resume page to include specified showcase projects**
  - Confirmed the showcase project selection controls work correctly
  - Verified the filter for showcase-only projects functions as expected
- Reviewed **Improve Resume page layout + persistent education entries + inline PDF preview**
  - Verified the inline PDF preview renders generated resumes correctly
  - Confirmed education entries persist across sessions
- Reviewed **Bug Fix: Persist Auth tokens across backend restarts**
  - Confirmed that restarting the Docker container no longer clears user sessions
- Reviewed **Portfolio heatmap**
  - Verified the calendar-style activity heatmap renders correctly and productivity stats are accurate
- Reviewed **Bug Fixes and Enhancements + Rebranding**
  - Confirmed duplicate project upload prevention works
  - Verified "MDA Portfolio" → "Blume" rebrand is consistent across all UI elements
- Reviewed **Implemented save resume generation + tests**
  - Verified saved resumes appear in the stored resumes section
  - Confirmed delete functionality removes entries correctly
- Reviewed **made the fix to show numbers**
  - Confirmed that project curation rankings now display as 1st, 2nd, 3rd instead of tick indicators
- Reviewed **implemented saving job analysis, with delete and view**
  - Verified saved job analyses persist correctly and can be viewed and deleted
- Reviewed **Fixed frontend test bugs**
  - Confirmed corrected mock implementations in Upload, Resume, and Portfolio tests make the full test suite pass
- Reviewed **Add Frontend Test Report documentation**
  - Confirmed the test strategy summary is accurate and complete

## Issues / Blockers

No major blockers this sprint.

## PR's initiated

- #451: Added week 10 log – https://github.com/COSC-499-W2025/capstone-project-team-6/pull/451
- #456: Fix JSX syntax errors in Resume.jsx – https://github.com/COSC-499-W2025/capstone-project-team-6/pull/456
- #467: Job description matching – https://github.com/COSC-499-W2025/capstone-project-team-6/pull/467
- #473: Job Match Page UX improvements – https://github.com/COSC-499-W2025/capstone-project-team-6/pull/473
- #489: Added Initialisation Document – https://github.com/COSC-499-W2025/capstone-project-team-6/pull/489
- #490: Backend test bug fix and documentation – https://github.com/COSC-499-W2025/capstone-project-team-6/pull/490
- #501: Bug fixes in frontend – https://github.com/COSC-499-W2025/capstone-project-team-6/pull/501

## PR's reviewed

- #446: Projects page LLM analysis integration – https://github.com/COSC-499-W2025/capstone-project-team-6/pull/446
- #452: Updated resume page to include specified showcase projects – https://github.com/COSC-499-W2025/capstone-project-team-6/pull/452
- #460: Improve Resume page layout + persistent education entries + inline PDF preview – https://github.com/COSC-499-W2025/capstone-project-team-6/pull/460
- #465: Bug Fix: Persist Auth tokens across backend restarts – https://github.com/COSC-499-W2025/capstone-project-team-6/pull/465
- #468: Portfolio heatmap – https://github.com/COSC-499-W2025/capstone-project-team-6/pull/468
- #475: Bug Fixes and Enhancements + Rebranding – https://github.com/COSC-499-W2025/capstone-project-team-6/pull/475
- #479: Implemented save resume generation + tests – https://github.com/COSC-499-W2025/capstone-project-team-6/pull/479
- #481: Made the fix to show numbers – https://github.com/COSC-499-W2025/capstone-project-team-6/pull/481
- #483: Implemented saving job analysis, with delete and view – https://github.com/COSC-499-W2025/capstone-project-team-6/pull/483
- #485: Fixed frontend test bugs – https://github.com/COSC-499-W2025/capstone-project-team-6/pull/485
- #495: Add Frontend Test Report documentation – https://github.com/COSC-499-W2025/capstone-project-team-6/pull/495

## Plan for next week

- Project is complete. No planned work beyond any last-minute fixes identified during final review.
