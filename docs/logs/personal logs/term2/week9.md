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
