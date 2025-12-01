# Mandira Samarasekara

# Aakash Tirithdas

# Mithish Ravisankar Geetha

## Date Ranges
November 24-November 30
![Mithish Week 13](images/MithishWeek13.png)

## Weekly recap goals
- Extend Python OOP analysis and design-principles detection
- Refactor and improve résumé generation workflow
- Add resume-related database tables and caching functions
- Implement deletion workflow for previously generated insights
- Generate and test “Top Ranked Projects” feature
- Review teammates’ PRs
- Study for Quiz 2 and complete the quiz

## What went well
Over the past two weeks, I made strong progress across multiple core areas of the non-LLM pipeline. I expanded the Python OOP and design-principles detection, which strengthened the depth of our code-quality analysis. I also refactored the résumé generator to make the output more structured, scalable, and aligned with the new database schema.

Another major step forward was implementing new database tables and caching logic for analysis and résumé retrieval, which improves performance and supports persistent storage. I added full workflows for deleting previously generated insights and implemented (and tested) the “Top Ranked Projects” feature, including code-file filtering and scoring logic.

Overall, this sprint helped solidify several important subsystems: OOP analysis, résumé generation, caching, project ranking, and deletion workflows—all of which strengthened the reliability, usability, and maintainability of the pipeline. I also studied for and completed Quiz 2.

## What didn't go well
Due to time constraints, I couldn’t finish implementing retrieval for previously generated résumé items. This will be completed in the next sprint along with additional refinements after integrating the new caching logic. A few deeper tests for the new resume-retrieval pathways also need to be added..

## PR's initiated
- Further OOP analysis and design principles detection in Python #164:https://github.com/COSC-499-W2025/capstone-project-team-6/pull/164
- Refactored résumé generator #168: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/168
- Unit tests for the résumé generator #169: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/169
- Add Resume Data Tables and Retrieval Functions with Analysis/Resume Caching #175: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/175
- Delete previously generated insights #183: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/183
- Unit tests for deletion workflow #184: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/184
- Summarize the top ranked projects + display only code files #188: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/188 
- Unit testing for top ranked projects #189: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/189

![alt text](image-3.png)
![alt text](image-4.png)
![alt text](image-5.png)
![alt text](image-6.png)
## PR's reviewed
- Git analysis #177: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/177
- Portfolio item generator #187: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/187
- CLI analysis integration #179: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/179

## Plan for next week
- Implement retrieval for previously generated résumé items  
- Refactor and clean up output and caching logic  
- Prepare and finalize Milestone 1 submission  
- Continue refining analysis modules after integration  

# Ansh Rastogi

# Harjot Sahota
<img width="1077" height="632" alt="Screenshot 2025-11-30 at 4 01 01 PM" src="https://github.com/user-attachments/assets/ed0477a7-1cef-48b0-be23-59dd3c715fe7" />

## Date Ranges
November 24-November 30

## Weekly recap goals
- Implemented and integrated the new portfolio item generator into the backend analysis pipeline.
- Ensured portfolio items save to the database alongside resume items.
- Built a full automated test suite for the portfolio generator.

## What went well
- Successfully built the full portfolio_item_generator.py with architecture, contributions, skills, and overview generation.
- Fully integrated portfolio generation into analyze.py without duplicating OOP analysis or breaking existing resume logic.
- Created a comprehensive test suite (quality score, architecture, contributions, skills, and full item generation) — all tests pass.
- Cleanly resolved merge conflicts and ensured compatibility with Development.

## What didn't go well
- Integration required reorganizing parts of analyze.py to avoid duplicated or misplaced logic.
- My portfolio analysis does not yet evaluate C, C++, Git activity, or document files because those analyzers were not integrated or merged into Development in time. This will be completed next sprint alongisde with proper tests for those specific analyzers to ensure full coverage and consistency with the existing pipeline.
  
## PR's initiated
- portfolio item generator #187 https://github.com/COSC-499-W2025/capstone-project-team-6/pull/187
  
<img width="1470" height="956" alt="Screenshot 2025-11-30 at 3 46 23 PM" src="https://github.com/user-attachments/assets/4d243227-cdcb-429d-bb46-0f0b78321e26" />

## PR's reviewed
- Further OOP analysis and design principles detection in Python #164 https://github.com/COSC-499-W2025/capstone-project-team-6/pull/164
- Mithish Week 13 logs #190 https://github.com/COSC-499-W2025/capstone-project-team-6/pull/190
- Unit tests for the resume generator #169 https://github.com/COSC-499-W2025/capstone-project-team-6/pull/169
- Deep Semantic Analysis Core Features #181 https://github.com/COSC-499-W2025/capstone-project-team-6/pull/181
- CLI integration analysis test #182 https://github.com/COSC-499-W2025/capstone-project-team-6/pull/182
- Unit tests for deletion workflow #184 https://github.com/COSC-499-W2025/capstone-project-team-6/pull/184
  
<img width="1221" height="262" alt="Screenshot 2025-11-30 at 3 54 58 PM" src="https://github.com/user-attachments/assets/0078b778-3e30-4442-beb5-e6457f552168" />
<img width="1222" height="137" alt="Screenshot 2025-11-30 at 3 52 11 PM" src="https://github.com/user-attachments/assets/b5aff214-453f-418c-bd8e-eee558d6aafa" />


## Plan for next week
- Extend the portfolio generator to incorporate insights from the new analyzers (C/C++ OOP metrics, Git contribution depth, documentation quality).
- refractor portfolio genereator to produce a cleaner output i.e not including a summary length output, clean up format (i.e 1 class instead of 1 classes)

# Mohamed Sakr
