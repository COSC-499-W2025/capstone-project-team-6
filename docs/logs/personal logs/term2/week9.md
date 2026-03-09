# Aakash Tirithdas
## Date Ranges

February 9-March 1
![Aakash Week 9](../images/aakashlogst2w9.png)

## Goals for this week (planned last sprint)
- Discuss milestone 3 requirements
- Fix any bugs found during milestone 2 wrap up.
- Fix the bug from our extra multiproject analysis


## What went well
- all tasks went well.
- all tasks were complete
  
## What could have been done better
- There were no team meetings that occured this week due to everyone being busy


## Coding tasks
- fixed the multi-project analysis bug.
  - the bug stemmed from the task analysis only being able to assign 1 task id. 
  - the code was adjusted to be compatible with multiple task ids fixing the bug
- 2 new bugs were found
  - 1 duplication in mult-analysis is not implemented
  - duplicatio of deleted projects is still found meaning there is a logical error in the duplication identification



## Testing or debugging tasks
- Ensure that all relevet tests passed from the start of the project with the exception of depricated tests. (closed last weeks branch as there were too may merge conflicts causing several new errors, was easier to make the same fixes in a new branch with a few slight changes)
- maually and automatically tests that the multiple analysis fix worked as expected. 

## Document tasks
- updated our DFD1 and architecture diagram


## PR's initiated
- fixed the multiproject bug. #414 https://github.com/COSC-499-W2025/capstone-project-team-6/pull/414
- made changes to the tests so that all tests pass #412 https://github.com/COSC-499-W2025/capstone-project-team-6/pull/412
- updated documentation for milestone2 #410 https://github.com/COSC-499-W2025/capstone-project-team-6/pull/410

## PR's reviewed


## Plan for next week

- fix the 2 new bugs that i found
  - 1 duplication in mult-analysis is not implemented
  - duplicatio of deleted projects is still found meaning there is a logical error in the duplication identification

# Mithish Ravisankar Geetha

## Date Ranges

March 2-March 8
![Mithish Week 8](../images/MithishT2W9.png)

## Goals for this week (planned last sprint)

- Discuss milestone 3 requirements
- Fix any bugs found during milestone 2 wrap up.
- Dockerize the application with a unified frontend/backend script
- Implement the change password feature

## What went well
The transition to a unified Docker environment was a significant success this week, as merging the React frontend and FastAPI backend into a single container has greatly streamlined the local development workflow. This change, along with the implementation of a persistent SQLite database through volume mounting, provides a much more stable foundation for the team. 
On the feature side, the settings page was successfully enhanced with the change password functionality and a direct logout button, which noticeably improves the user experience by centralizing account controls. Additionally, providing detailed architectural feedback on the Milestone 2 documentation helped ensure our system design. The modular connections between the FastAPI server and Gemini AI is accurately represented for future milestones.

## What didn't go well
Despite the progress with containerization, a primary concern remains the lack of verification for Windows environments; since the script was developed on macOS, there may be minor compatibility issues that haven't been surfaced yet. The migration to the new Docker setup constitutes a breaking change regarding local data. Because the application now relies on a new SQLite volume mounting strategy, all previously saved local login credentials will no longer function, requiring all team members and testers to create new accounts.


## Coding tasks

- **Unified Dockerization:** Created a multi-service Docker configuration to run the entire stack on port 8000.
- **User Management Features:** Developed the backend logic and frontend UI for the new password change functionality.
- **Settings Page Enhancements:** Integrated a logout trigger directly into the settings interface.

**PRs:**
- Docker Containerization - Unified Setup [#416](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/416)
- Settings page: change password [#418](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/418)


## Testing or debugging tasks
- **Auth Testing:** Verified password change and logout logic using `pytest src/tests/api_test/test_auth.py`.
- **Persistence Validation:** Tested Docker volume mounting to ensure SQLite data persists across container restarts.
- **Container Health:** Used `test-docker-setup.sh` to verify API and Frontend availability on the new unified port.

**PRs:**
- Fix the multiproject bug [#414](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/414)
- Settings page: change password [#418](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/418)

## Reviewing or collaboration tasks
- **Architecture Guidance:** Requested specific changes to the Milestone 2 documentation to correctly map the relationship between the FastAPI server, Gemini AI, and the independent Task/Project/Portfolio modules.
- **Bug Triaging:** Reviewed and approved fixes for the multiproject bug and general setup issues.

## **Issues / Blockers**

-No major blockers this week

## PR's initiated
- Docker Containerization - Unified Setup #416 (https://github.com/COSC-499-W2025/capstone-project-team-6/pull/416)
- Settings page: change password #418 (https://github.com/COSC-499-W2025/capstone-project-team-6/pull/418)

## PR's reviewed
- fixed the multiproject bug #414: (https://github.com/COSC-499-W2025/capstone-project-team-6/pull/414)
- Setup fix #411 (https://github.com/COSC-499-W2025/capstone-project-team-6/pull/411)
- updated documentation for milestone2 #410 (https://github.com/COSC-499-W2025/capstone-project-team-6/pull/410) (Changes Requested)


## Plan for next week
- Verify Docker functionality on Windows environments.
- Begin implementation of Milestone 3 core requirements based on team discussion.

# Harjot Sahota

## Date Range
March 1 - March 8
<img width="1081" height="634" alt="Screenshot 2026-03-08 at 4 40 47 PM" src="https://github.com/user-attachments/assets/ce3e832c-abab-48b0-8317-45ee252e360c" />

## What went well

This week I completed two meaningful improvements to the application: a Projects page UI cleanup and a full Delete Account feature.

I updated the Projects page UI to make project cards cleaner, more readable, and easier to use. I removed the unused “Select stored resume” / “Add selected bullets” section, removed checkbox selection from resume bullets so they are now displayed as plain bullet points only, and improved the overall card layout and styling. These changes made the page feel more polished and user-friendly without changing the main functionality.
I successfully added a Delete Account feature that allows an authenticated user to permanently remove their account and all associated data from the system through the Settings page. This included adding a new Delete Account section and confirmation modal in the frontend, wiring the frontend API call, creating the backend delete account endpoint, and adding helper logic to remove the user and related stored data. I also added Settings page tests covering the new delete account flow.

Overall, this week went well because I was able to both improve the usability of the app and add a valuable account management feature for users who no longer want to use the system.

## What didn’t go well

While implementing the Delete Account feature, I discovered that some database relationships were not set up with the correct cascading delete behavior. Because of that, deleting an account was not as straightforward as it should have been.

Given the size and scope of the PR, I decided to use a backend helper function to work around the current database relationship issues by deleting dependent data in the correct order before removing the user row. This allowed me to complete the feature without expanding the PR too far, but it also highlighted an area of the database design that still needs improvement.

## PRs initiated

Projects page UI cleanup and card layout improvements  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/423

Add delete account feature with frontend, backend, and tests  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/428

## PRs reviewed

added tests to verify resume bugs are fixed  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/426

fixed the multiproject bug setup fix  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/414

Setup fix https://github.com/COSC-499-W2025/capstone-project-team-6/pull/411

updated documentation for milestone2  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/410


## Plans for next week

Next week I plan to work on a cleanup PR that migrates the remaining relevant foreign key relationships to use `ON DELETE CASCADE` where appropriate. This should simplify the delete-account flow and reduce the need for manual ordered cleanup in backend helper logic.

I also plan to work on a feature that allows users to upload or paste in their own API key in the app so they can use the LLM analysis feature through the frontend.

