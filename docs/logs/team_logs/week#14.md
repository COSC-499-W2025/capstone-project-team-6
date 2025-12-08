# Team Log – Team 6

**Work Performed:** Dec 1st – Dec 7th

---

## Milestone Goals Recap

### Features in Project Plan for This Milestone

- Finalize and strengthen the **non-LLM analysis pipeline**:
  - Refactor project chronology using commit/modified/analysis dates.
  - Improve résumé retrieval and deletion workflows.
  - Extend and refine the portfolio item generator with C/C++ analyzers, optimization scoring, and Git metadata.
- Strengthen the **end-to-end CLI workflow**:
  - Integrate complexity analysis, résumé generation, and portfolio generation into the CLI.
  - Add progress bars and feature-selection flags for LLM analysis.
- Expand **deep semantic analysis capabilities**:
  - Add documentation for Architecture, Complexity, Security, Skills, and Domain lenses.
  - Enhance LLM-based résumé and portfolio narrative generation.
- Support **Milestone 1 presentation & reporting**:
  - Complete demo video, presentation, team contract, and self-reflections.
  - Review other teams’ presentations and finalize all milestone deliverables.

### Associated Tasks / PRs Touched This Week

- Project chronology and timelines  
  - Issue: https://github.com/COSC-499-W2025/capstone-project-team-6/issues/212  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/213  

- Git and system architecture work  
  - PRs:  
    - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/228  
    - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/229  
    - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/227  
    - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/204  

- Non-LLM pipeline (résumé, deletion, retrieval, top projects)  
  - PRs:  
    - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/183  
    - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/201  
    - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/188  
    - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/189  

- Portfolio generator  
  - PRs:  
    - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/211  
    - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/218  

- CLI workflow and LLM integration  
  - PRs:  
    - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/203  
    - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/220  
    - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/206  
    - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/223  
    - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/208  

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

- **Task:** Refactor chronological project & skills timelines  
  **Description:** Implemented a new three-tier date priority system using commit date, file modified date, and analysis timestamp. Added database/migration support for new metadata fields, improved CLI formatting, and fixed a regression involving duplicate table definitions.  
  **Links:**  
  - Issue: https://github.com/COSC-499-W2025/capstone-project-team-6/issues/212  
  - PR: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/213  

- **Task:** Presentation, demo, and team coordination  
  **Description:** Co-created the milestone demo with Aakash, prepared and delivered the presentation, finalized the team contract, and completed the milestone self-reflection.

- **Task:** Code reviews  
  **Links:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/208  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/183  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/189
    
<img width="1248" height="232" alt="Screenshot 2025-12-07 at 11 28 54 PM" src="https://github.com/user-attachments/assets/fba5e35c-f5b3-4b41-b957-f119b86a7d27" />

---

### Aakash Tirathdas (**aakash-tir**)

- **Task:** System architecture & diagrams  
  **Description:** Updated the project’s DFD and system architecture to reflect new analyzers, Git integration, and expanded CLI workflows.

- **Task:** CLI refactor and demo recording  
  **Description:** Refactored CLI components, collaborated on video demo, and fixed areas that delayed expected workflows.

- **Task:** Initiated PRs  
  **Links:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/228  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/229  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/227  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/204  

- **Task:** Reviewed PRs  
  **Links:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/200  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/206  

<img width="1241" height="240" alt="Screenshot 2025-12-07 at 11 30 03 PM" src="https://github.com/user-attachments/assets/33391c3e-64da-4957-afa2-3cc2b3bacbb5" />

---

### Mithish Ravisankar Geetha (**MithishR**)

- **Task:** Strengthened deletion & retrieval workflows  
  **Description:** Refactored the Delete Insights feature after detailed review findings, resolved merge conflicts, and implemented complete résumé item retrieval with caching. Completed all milestone deliverables including contract and self-reflection.

- **Task:** Initiated PRs  
  **Links:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/183  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/184  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/188  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/189  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/201  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/200  

- **Task:** Reviewed PRs  
  **Links:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/211  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/204  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/213
    
<img width="1240" height="430" alt="Screenshot 2025-12-07 at 11 31 03 PM" src="https://github.com/user-attachments/assets/5dbb87d7-1034-4d4d-bfc5-e9f9d8673cbf" />

---

### Ansh Rastogi (**anshr18**)

- **Task:** Git analysis integration  
  **Description:** Integrated commit history, contributor stats, ZIP/directory support, and graceful error handling into the CLI.  

  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/203  

- **Task:** Major CLI enhancements  
  **Description:** Integrated complexity analysis, résumé generation, portfolio generation, and added feature-selection flags and rich UI formatting to the `mda analyze-llm` command.

  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/220  

- **Task:** Reviewed PRs  
  **Links:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/211  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/208  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/204  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/201  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/193  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/214  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/218  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/221  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/223  

<img width="1248" height="297" alt="Screenshot 2025-12-07 at 11 31 36 PM" src="https://github.com/user-attachments/assets/bf556d9d-5a3e-409c-ba9e-0483411e097b" />


---

### Harjot Sahota (**HarjotSahota**)

- **Task:** Portfolio generator extensions  
  **Description:** Integrated full C/C++ OOP analysis, optimization scoring, and Git metadata into the portfolio system. Restored missing logic in `analyze.py` and ensured full end-to-end functionality without regressions.

- **Task:** Initiated PRs  
  **Links:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/211  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/218  

- **Task:** Reviewed PRs  
  **Links:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/201  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/203  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/206  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/213  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/220  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/223  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/230  

<img width="1236" height="309" alt="Screenshot 2025-12-07 at 11 32 11 PM" src="https://github.com/user-attachments/assets/cc952254-a32d-4067-9100-a77cf7f0d090" />

---

### Mohamed Sakr (**mgjim101**)

- **Task:** LLM progress bar  
  **Description:** Implemented rich-progress UI for all phases of LLM analysis and suppressed log noise to prevent bar flickering.  

  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/206  

- **Task:** Deep Semantic documentation  
  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/208  

- **Task:** LLM career artifact generation  
  **Description:** Added résumé and portfolio narrative generation via `--resume` flag.

  **PR:** https://github.com/COSC-499-W2025/capstone-project-team-6/pull/223  

- **Task:** Reviewed PRs  
  **Links:**  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/184  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/218  
  - https://github.com/COSC-499-W2025/capstone-project-team-6/pull/220  

<img width="466" height="205" alt="Screenshot 2025-12-07 at 11 32 51 PM" src="https://github.com/user-attachments/assets/3afa8712-bb7b-4637-a62e-e497cda6a385" />

---

## What Went Well

- The **analysis pipeline** is significantly stronger:  
  - Chronology refactored with accurate metadata.  
  - Resume deletion/retrieval workflows completed and tested.  
  - Portfolio generator now incorporates C/C++, optimization tiers, and Git metadata.  
- The **CLI** gained robust new capabilities:  
  - Full integration of complexity, résumé, and portfolio generation.  
  - LLM analysis greatly improved with richer formatting and feature flags.  
  - Progress bar added for user-friendly LLM analysis.  
- The **Deep Semantic Analysis** subsystem advanced through documentation, clearer structure, and career artifact generation.  
- Strong team communication and collaboration ensured timely completion of Milestone 1 deliverables.

---

## What Didn’t Go as Planned

- Some PRs unintentionally removed or regressed logic, requiring rapid fixes.  
- Merge conflicts slowed progress during periods of high activity.  
- Chronology output still needs formatting polish for readability.  
- Progress bar integration required unexpected refactoring of logging layers.  
- Some CLI workflows required last-minute debugging, especially ZIP handling and import issues.

---

## How These Reflections Shape Next Cycle’s Plan

- Improve formatting & readability of chronology output.  
- Add safeguards against accidental code deletion in PRs.  
- Refine CLI’s input handling and overall user experience.  
- Expand portfolio generator with deeper Git and optimization insights.  
- Begin Milestone 2 planning in January with focus on scalability.

---

## Test Report

- **Chronology:** Unit tests passing for new date-priority logic.  
- **Resume Pipeline:** Deletion and retrieval workflows stable and tested.  
- **Portfolio:** Full C/C++ and optimization scoring tests passing.  
- **CLI:** End-to-end tests verify pipeline integration.  
- **LLM:** Progress bar behavior validated through manual testing.  
- **Deep Semantic:** Documentation validated; additional tests planned.

---

## Project Burnup Chart

<img width="1043" height="663" alt="Screenshot 2025-12-07 at 11 33 36 PM" src="https://github.com/user-attachments/assets/31ce9a00-5120-4baa-a468-0480e5b7b0a5" />

