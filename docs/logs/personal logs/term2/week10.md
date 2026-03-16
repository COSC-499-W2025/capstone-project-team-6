# Mandira Samarasekara

## Date Ranges
March 9 - March 15
![Maddy Week 10](../images/MaddyW10T2.png)


## Goals for this week (planned last sprint)
- Incorporated role prediction into resume and portfolio generation
- Change the loading animation in the Analyze page to better account for multi-project analysis

## What went well
This week went well overall because I was able to complete the role prediction frontend feature end-to-end across all three project-facing pages. One of the more satisfying parts was tracing the existing backend role data through multiple query paths and getting it to flow consistently to the frontend, so users can now see predicted roles on the Projects, Resume, and Portfolio pages and override them directly from the Projects page. Manual testing went smoothly across the full stack and I was also able to review and test two teammate PRs and confirm both sets of fixes were working.

## What could have been done better
- The role data already existed in parts of the backend but was not flowing consistently through every query path the frontend needed. It would have been more efficient to map all affected paths before starting the UI work rather than discovering gaps during development.
- I did not get to the Analyze page loading animation update this week. The role prediction curation flow ended up requiring more backend and frontend coordination than anticipated, which pushed that task to next week.

## Coding tasks
- Implemented the **role prediction frontend feature** in PR [#444](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/444)
  - Surfaced role prediction across all three project-facing pages: **Projects**, **Resume**, and **Portfolio**
  - Enriched backend query paths so `predicted_role`, `predicted_role_confidence`, and `curated_role` are included where needed for frontend rendering
  - Added `GET /api/curation/roles` endpoint returning the 12 available developer roles
  - Added `POST /api/curation/role` endpoint to save or clear a curated role for a project
  - Added an interactive role pill on the Projects page with inline editing
  - Added a dropdown of predefined roles plus a **Custom role...** free-text option
  - Added **Save**, **Reset**, and **Cancel** controls for role curation
  - Added role badges to the Resume selection list and Portfolio project views
  - Used distinct visual states for curated roles, predicted roles, and projects with no role data

## Testing or debugging tasks
- Manually tested the full stack locally for PR [#444](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/444)
  - Verified predicted roles display on Projects, Resume, and Portfolio pages after analysis
  - Verified clicking the role pill on the Projects page opens the inline editor
  - Verified selecting a predefined role from the dropdown and saving persists to the database
  - Verified entering a custom role and saving persists to the database
  - Verified **Reset** clears the curated role and reverts to the predicted role
  - Verified **Cancel** closes the editor without saving
  - Verified curated role changes are reflected on Resume and Portfolio after navigation
  - Verified projects with no role prediction display **Not set** gracefully

## Document tasks
- Wrote a detailed guide for the TA so she can veriy the role prediction feature on the backend
## Reviewing or collaboration tasks
- Reviewed **duplicate file analysis detection bug fix** PR [#431](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/431)
  - Verified that the deleted-project re-upload fix works correctly
  - Confirmed deduplication is now analysis-type agnostic
  - Confirmed duplicate handling and messaging are more reliable in single and multi-upload flows
  - Approved the PR after testing and noted a small possible improvement for preserving skipped-duplicate messaging through polling
- Reviewed **Fixed syntax errors** PR [#439](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/439)
  - Verified the frontend build succeeds again
  - Confirmed the Settings page JSX issues were resolved
  - Confirmed the missing `deleteAccount` API method was added correctly
  - Approved the PR after verifying the app compiles and runs successfully

## Issues / Blockers
No major blockers this week.

## PR's initiated
- Feature/role prediction frontend [#444](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/444)

## PR's reviewed
- duplicate file analysis detection bug fix [#431](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/431) : approved after testing duplicate handling scenarios and confirming the major fixes worked as expected
- Fixed syntax errors [#439](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/439) : approved after verifying the frontend and Docker build issues were resolved

## Plan for next week
- Continue milestone 3 frontend integration work
- Return to the Analyze page loading animation update for multi-project analysis
- Support testing and review for related frontend/backend integration PRs

# Aakash Tirithdas

## Date Ranges
March 9 - March 15

## Goals for this week (planned last sprint)

## What went well

## What could have been done better

## Coding tasks

## Testing or debugging tasks

## Document tasks

## Reviewing or collaboration tasks

## Issues / Blockers

## PR's initiated

## PR's reviewed

## Plan for next week

# Mithish Ravisankar Geetha

## Date Ranges
March 9 - March 15

## Goals for this week (planned last sprint)

## What went well

## What could have been done better

## Coding tasks

## Testing or debugging tasks

## Document tasks

## Reviewing or collaboration tasks

## Issues / Blockers

## PR's initiated

## PR's reviewed

## Plan for next week

# Harjot Sahota

## Date Ranges
March 9 - March 15

## Goals for this week (planned last sprint)

## What went well

## What could have been done better

## Coding tasks

## Testing or debugging tasks

## Document tasks

## Reviewing or collaboration tasks

## Issues / Blockers

## PR's initiated

## PR's reviewed

## Plan for next week

# Mohamed Sakr

## Date Ranges
March 9 - March 15
![Mohamed Week 10](../term2/mohamedw10t2.png)
## Goals for this week (planned last sprint)

- Continue working on Milestone 3 features
- Look into further improvements to the resume generation output quality

## What went well

The LLM analysis feature is now fully end-to-end functional. After a methodical debugging process involving backend logging, direct database inspection, and tracing through the full task pipeline, I was able to pinpoint all root causes blocking the analysis from displaying. The frontend panel I built to surface the Gemini output turned out to be solid, the issues were all in the data pipeline, not the UI. Writing focused automated tests for each bug site made the fixes verifiable and should prevent silent regressions.

## What could have been done better

- The root cause of the most critical bug (`sqlite3.Row` not supporting the `in` operator) was subtle and only found after adding extensive diagnostic logging. Knowing the quirks of `sqlite3.Row` upfront would have saved significant debugging time.
- The database ended up in a corrupted state (analyses with `total_projects = 0` and no project rows) from prior partial runs during development, which masked whether fixes were working. It would have been better to clean the test database earlier in the process rather than late in debugging.

## Coding tasks

- Implemented the **LLM analysis display panel** on the Projects page (`ProjectsPage.jsx`)
  - The base prompt output section is always shown for each project
  - A side dropdown lets users select and toggle additional categories from `PROMPT_MODULES` (architecture, security, complexity, skills, domain, resume)
  - Added `parseLlmSections` to transform the Gemini markdown output into rendered React subsections
  - Added `GET /api/projects/{project_id}/llm-analysis` endpoint in `projects.py` to serve `llm_summary` per project
  - Fixed a `NameError` in `projects.py` caused by a missing `Response` import
- Fixed the **LLM summary not being persisted** despite the pipeline running successfully
  - Root cause: `"analysis_uuid" in row` always returned `False` for `sqlite3.Row` objects, so `analysis_uuid` was always set to `None` and the `update_llm_summary` call was skipped
  - Fix: removed the `in row` guard — `analysis_uuid = row["analysis_uuid"] if row else None`
- Fixed **silently suppressed LLM errors** in `llm_pipeline.py`
  - All `logger.error` calls were guarded by `if not progress_callback:`, meaning errors from the Gemini API were never logged when a callback was active
  - Removed all such guards so errors are always logged
- Fixed **frontend dropdown scrolling** for analysis categories in `ProjectsPage.jsx`
  - Changed the dropdown container from `overflow: hidden` to `maxHeight: 320px, overflowY: auto`
  - Removed `overflow: hidden` from the parent panel container which was clipping the absolute-positioned dropdown
- Added **diagnostic logging** to `task_manager.py`, `llm_pipeline.py`, and `analysis_database.py` to track the full LLM pipeline flow: API key presence, pipeline result content, `analysis_uuid` value at save time, and project row counts after `record_analysis`

## Testing or debugging tasks

- Created `tests/backend_test/test_llm_summary.py` with 18 unit tests covering:
  - `update_llm_summary` and `get_llm_summary_for_analysis` round-trip correctness
  - `record_analysis` project row persistence and `total_projects` count accuracy
  - `sqlite3.Row` `in` operator regression (documents the bug and verifies the fix)
  - `_process_new_portfolio` in `task_manager`: LLM summary saved when UUID is available, not saved when UUID is `None`, skipped without consent, and does not crash on Gemini errors
- Created `tests/api_test/test_llm_analysis_endpoint.py` with 6 integration tests covering:
  - Returns `llm_summary` when present for an authenticated user's project
  - Returns `null` summary when LLM has not run
  - Returns 404 for non-existent or other users' projects
  - Rejects unauthenticated requests
  - Response always contains `project_id` and `llm_summary` keys
- Updated `tests/backend_test/test_task_manager_llm.py` to replace the stale test (which tested the old `record_analysis("llm", ...)` architecture) with two new tests verifying the current behavior:
  - `update_llm_summary` is called once with the correct UUID and summary text
  - `record_analysis` is called exactly once (not a second time for the LLM result)
- Diagnosed database corruption by running direct SQL queries confirming `total_projects = 0` and empty `projects` table; cleared corrupted rows and re-ran a clean upload to verify the full pipeline end-to-end

## Reviewing or collaboration tasks
- Reviewed role prediciton frontend edits, validation settings, and docker documentation

## Issues / Blockers
- No blockers
## PR's initiated
-https://github.com/COSC-499-W2025/capstone-project-team-6/pull/446

## PR's reviewed
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/444 (first review)
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/443
- https://github.com/COSC-499-W2025/capstone-project-team-6/pull/441

## Plan for next week

- Continue Milestone 3 frontend integration work
- Look into further output quality improvements for the Gemini analysis sections
- Support review of related frontend/backend integration PRs from teammates

# Ansh Rastogi

## Date Ranges
March 9 - March 15

## Goals for this week (planned last sprint)

## What went well

## What could have been done better

## Coding tasks

## Testing or debugging tasks

## Document tasks

## Reviewing or collaboration tasks

## Issues / Blockers

## PR's initiated

## PR's reviewed

## Plan for next week
