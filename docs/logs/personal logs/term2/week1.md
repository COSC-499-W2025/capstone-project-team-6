# Mandira Samarasekara

# Aakash Tirithdas

# Mithish Ravisankar Geetha

## Date Ranges

January 5-January 11
![Mithish Week 1](../images/Mithishweek1term2.png)

## Weekly recap goals

- Create API endpoints structure for milestone 2 requirements
- Attend the team meetings
- Meet with Mandira to discuss the API set up
- Review all pending PRs

Winter break activities:

- Added java complexity analysis and unit testing

## What went well

The basic API endpoint structure required for Milestone 2 was successfully designed and implemented, providing a clear and scalable foundation for upcoming features. The structure aligns well with the project’s existing architecture and will make future integrations smoother.

I attended all scheduled team meetings and had a focused discussion with Mandira to align on the API setup, responsibilities, and next steps. This helped clarify expectations early and avoid overlapping work.

Additionally, I reviewed and completed all pending pull requests, ensuring the codebase remained stable and up to date. Addressing these reviews promptly helped close open loops before moving forward into Milestone 2 development.

## What didn't go well

I was out of Kelowna during this period, so I was unable to attend class in person. I will also be unable to attend the Week 2 Monday class on January 12, which made real-time coordination slightly more challenging.

However, this was communicated to the team in advance, and we discussed expectations early on. Tasks were assigned accordingly to ensure progress was not blocked. Once everyone is back in Week 2, we plan to meet again to realign and continue coordination more smoothly.

## PR's initiated

Created during the winter break

- Java complexity analysis #245: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/245
- Unit testing for java complexity #262: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/262

Created during week 1:

- Add REST API Server structure with Authentication (Milestone 2) #265: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/265

## PR's reviewed

- Git language breakdown #237 : https://github.com/COSC-499-W2025/capstone-project-team-6/pull/237
- Added project specific duration analysis features #241: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/241
- Zero Project Contribution Detection #251 : https://github.com/COSC-499-W2025/capstone-project-team-6/pull/251
- Multi-Project Skill Chronological Listing #259 : https://github.com/COSC-499-W2025/capstone-project-team-6/pull/259
- Updated Analysis Database Projects Table to Reflect Skill Analysis Updates #261: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/261

## Issue board

![alt text](image-1.png)
![alt text](image-2.png)

## Plan for next week

- Discuss milestone 2 requirements with the team
- Complete requirement 21 (Allow incremental information by adding another zipped folder of files for the same portfolio or résumé)
- Clean up API endpoints structure if anything is missing

# Ansh Rastogi

## Date Ranges

January 5-January 11
![Ansh Week 1 Term 2](../images/AnshRastogi_PeerEval_SS_W1T2.png)

## Weekly recap goals

- Implement Enhanced Contribution Ranking algorithm for project scoring
- Add multi-factor ranking system with configurable weights
- Create comprehensive test suite for ranking functionality
- Review teammates' PRs and provide constructive feedback
- Attend team meetings and coordinate on Milestone 2 planning

## What went well

This week was highly productive in strengthening our project ranking system. I successfully implemented the Enhanced Contribution Ranking algorithm, which expands our basic composite scoring with five new contextual factors: individual contribution weight, recency bonus, project scale, collaboration diversity, and activity duration.

The implementation introduced a weighted algorithm that combines base technical scores (45%) with contribution and context factors (55%), providing more nuanced project rankings that better reflect individual contributions in collaborative environments. The system also includes a five-tier project categorization (Flagship/Major/Significant/Supporting/Minor) to help users quickly identify their most impactful work.

## What didn't go well

The implementation initially had a bug in the `calculate_contribution_score()` function where the user email lookup wasn't properly searching the contributors list. This caused three test failures on the first run, requiring a bug fix commit. The issue was identified quickly through the test suite, but it added an extra iteration to the development cycle.

Additionally, the enhanced ranking output format change (`"ENHANCED RANKING BREAKDOWN:"` instead of `"Score Breakdown"`) broke an existing test in `test_analyze.py`. This required a patch to update the test assertion to accept either format for backward compatibility, which was caught by the GitHub Actions CI/CD pipeline.

## PR's initiated

- Enhanced Contribution Ranking #267: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/267

## PR's reviewed

- Updated Analysis DB for new git analysis features #239: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/239
- Activity-type contribution frequency #243: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/243
- Add User-Aware Contribution Ranking and Storage #247: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/247
- Fixed DB Duplication Bug #253: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/253
- Include detailed portfolio skills in chronological timeline #257: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/257

## Plan for next week

- Discuss Milestone 2 requirements with the team
- Continue refining ranking algorithm based on user feedback
- Collaborate on Milestone 2 planning and task assignment

# Harjot Sahota

# Mohamed Sakr
## Date Ranges
December 22 - January 11
 ![Mohamed Week 1](../term2/mohamedw1.png)

## Weekly recap goals
- Attend the team meetings
- Review all pending PRs
- Wrap up and document Git Analysis & Metrics Features 1–12:
  - Insights/ranking: contributor insights (per-user language, trivial vs substantial, ownership), single-user hybrid ranking, multi-project ranking, zero-contribution transparency.
  - Data foundations: expanded language detection, project duration metrics, activity-type classification, schema expansions for ownership/semantic stats/language breakdowns and skills storage.
  - Reporting/skills: comprehensive summaries (semantic + activity mix), granular skill extraction (concepts), chronological skill progression, persisted `project_skills` for fast timelines.

Winter break activities:
- Enhanced Contributor Insights: per-user language usage, trivial vs. substantial commit split, total lines changed, surviving-line ownership (file-level dominance), aggregated blame summaries, and noreply-email filtering for accurate identity.
- Expanded Language Detection: broader extension map (TypeScript, Rust, Dockerfile, Swift, config formats, etc.) to shrink the “Other” bucket and improve repo language breakdowns.
- Database Schema Expansion: new tables to persist ownership, semantic stats, and language breakdowns so downstream tools query DB directly instead of parsing raw JSON.
- Project Duration Metrics: derive start/end dates and total active days from git history for portfolio timeline displays.
- Activity Type Classification: categorize contributions as Code, Test, Docs, or Design for contributor-level activity mix.
- Contribution-Aware Ranking (Single User): hybrid boost score for a target email using commit share, recency, and surviving lines to adjust project rank.
- Multi-Project Ranking: iterate top-level projects, apply user-contribution scoring, and produce an aggregated ranked list.
- Zero-Contribution Transparency: explicitly report when the target user has zero detected contributions in a project.
- Comprehensive Summary Outputs: CLI/portfolio summaries now surface semantic summaries, activity breakdowns, and fix the zero contributor/branch count bugs.
- Granular Skill Extraction: detect technical concepts (e.g., OOP, Singleton Pattern, CI/CD, TDD) beyond languages/frameworks.
- Chronological Skill Progression: flat, date-ordered skill list based on first-use timestamps across projects to show learning trajectory.
- Database Storage for Skills: persist extracted skills into a dedicated `project_skills` table during analysis to avoid regenerating timelines.

## What went well
- The expanded language detection and activity-type classification removed most “Other” and “unknown” buckets, producing clear contributor breakdowns and ownership signals.
- Database schema changes landed cleanly, enabling downstream tools to query ownership, semantic stats, and skills without re-parsing raw JSON.
- Ranking outputs now reflect real user impact; zero-contribution cases are explicit, reducing confusion in multi-project reports.
- Portfolio summaries now display the richer metrics (semantic summaries, branch/contributor counts, activity mix) without the prior zero-count bugs.

## What didn't go well
- Initial runs surfaced performance hits during large blame sweeps and multi-project rankings; still need follow-up tuning and more load testing.
- Skill extraction edge cases remain (e.g., sparse commit histories), and coverage could improve with additional fixtures and automated tests.

## PR's initiated
Created during the winter break
-  #235: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/235
-  #237: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/237
-  #239: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/239
-  #241: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/241
-  #243: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/243
-  #247: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/247
-  #249: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/249
-  #251: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/251
-  #253: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/253
-  #255: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/255
-  #257: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/257
-  #259: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/259
-  #261: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/261

## PR's reviewed
-  #262: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/262
-  #269: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/269

## Plan for next week
- Discuss milestone 2 requirements with the team
- Complete requirement 23 allowing users to choose which information is represented