# Mandira Samarasekara
## Date Ranges
November 10 - November 23
![Mandira Week 11 and 12](images/MandiraWeek12.png)

## Tasks Worked On 
- Developed a Python complexity analyzer that evaluates whether code demonstrates awareness of algorithmic complexity and optimization practices, such as reducing runtime from O(n²) to O(n log n) through efficient algorithms and optimization techniques.
- Implemented detection for efficient data structures that improve performance, including the use of hash maps over lists for enhanced lookup efficiency.
- Created comprehensive test coverage for the Python complexity analyzer with 29 passing tests.
- Authored detailed documentation for the Python complexity analyzer feature.

### What Went Well

- All tests passed successfully, and I completed the implementation while addressing any bugs efficiently.
- The changes I made did not break any existing tests, ensuring backward compatibility.

### What Didn't Go as Planned

- Encountered a few minor merge conflicts due to working from an outdated branch that had undergone several merges. These conflicts were straightforward and resolved quickly.

### Looking Ahead

- I plan to extend the complexity analyzer to support additional programming languages beyond Python, beginning with Java.
- Will continue expanding language support based on project requirements.

## PR's initiated

Python complexity analysis #152

Implemented a Python time-complexity analysis feature that inspects Python files within projects to detect algorithmic complexity patterns and optimization awareness. The analyzer identifies inefficient patterns such as nested loops and suboptimal membership tests, while recognizing positive optimizations including memoization, set/dictionary usage, binary search implementations, and list comprehensions. Outputs include a per-project Optimization Awareness Score (0–100) with optional detailed findings. Includes comprehensive test suite and complete documentation.

## PR's reviewed

Add Fixes to Java analysis pipeline #140
Added CLI workflow integration tests #132
Non LLM analysis: Generate Resume items #146
Unit testing for generation of resume items #147
Mithish logs W11+W12 #149

Conducted thorough testing and code review for all PRs listed above, providing constructive feedback with actionable suggestions for improvement while highlighting strengths and effective implementations. 

# Aakash Tirithdas


# Mithish Ravisankar Geetha  

## Date Ranges
November 10 - Novemeber 23
![Mithish Week 11 and 12](images/MithishWeek12.png)
Over the past two weeks, I made solid progress strengthening the non-LLM analysis pipeline. Building the Java OOP analysis helped me translate high-level design principles into practical code checks, and integrating it into the main pipeline showed me how each component contributes to the overall workflow.

Fixing bugs and adding project-size adaptations improved the accuracy and reliability of the analysis. Implementing database storage and résumé item generation also gave me a better sense of how our results will be used and how to present them meaningfully to users.

Overall, these weeks helped me improve both the technical quality of the analysis pipeline and my ability to think about how the system works end-to-end.## PR's initiated

## PR's initiated
-  Complete Java OOP Analysis #128:  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/128
- Integrated Java nalysis to the main analysis pipeline #130: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/130
- Add fixes to Java analysis pipeline #140: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/140
- Modify java analysis to account for project size #144: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/144
- Store project information in the database #145: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/145
- Non LLM Analysis generate resume items #146: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/146
- Unit testing for generation of resume items #147: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/147
![alt text](image-2.png)
![alt text](image-1.png)



## PR's reviewed
- Integrating analysis pipeline with CLI: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/146


## Plan for next week
-  Retrieve previously generated portfolio information 
-  Retrieve previously generated résumé item 
-  Study for the quiz
- Prepare milestone presentation
- Refactor code after integration

# Ansh Rastogi

# Harjot Sahota

## Date Ranges
November 16 - Novemeber 23
<img width="1076" height="636" alt="Screenshot 2025-11-23 at 9 08 23 PM" src="https://github.com/user-attachments/assets/fec58f9d-4c4c-4bbd-85ec-f3b96557d34f" />

## Tasks Worked On
- [x] Implemented the C++ OOP Analyzer for Phase 3
- [x] Wrote a full test suite for the analyzer
- [x] Added documentation for C++ analysis in Phase 3
- [x] Added libclang dependency and created a samplecpp.cpp test file
- [x] Debugged import issues, AST issues, and test failures
- [x] Prepared and opened PR #157 (C++ OOP Analyzer)

## Weekly Goals Recap
- [x] Finished the working version of the C++ OOP analysis module
- [x] Create a complete test suite 
- [x] Add the analyzer to the documentation & requirements

### What Was Accomplished
- [x] Implemented the entire C++ OOP analyzer using Clang’s AST
- [x] Created a comprehensive PyTest test suite
- [x] Added samplecpp.cpp so teammates can run real tests
- [x] Updated documentation:
Added “Phase 3: C++ OOP Detection” to MetadataExtractor README
Added installation & usage instructions
Added example output
Added known limitations section
- [x] Updated requirements.txt with libclang
- [x] Verified the analyzer works both when libclang is installed or missing (fallback mode)

### What Didn’t Go as Planned
- [x] libclang caused unexpected issues:
AST parsing fails silently if libclang is missing or incorrectly installed

- [x] Tests repeatedly failed until adjustments were made
- [x] Had to adjust imports to match the project structure.

### Looking Ahead
- [x] I plan to expand the detection system to include more patterns like Adapter, Decorator, and Bridge, while reducing false positives.

## PR's initiated
- https://github.com/COSC-499-W2025/capstone-project-team-6/issues/156 
<img width="1470" height="956" alt="Screenshot 2025-11-23 at 9 20 44 PM" src="https://github.com/user-attachments/assets/ea82cacd-9780-4148-980c-cfa4ba9e933a" />

## PR's reviewed
- https://github.com/COSC-499-W2025/capstone-project-team-6/issues/141
<img width="1470" height="956" alt="Screenshot 2025-11-23 at 9 21 50 PM" src="https://github.com/user-attachments/assets/b15bba05-0e85-42c3-8ca7-9e0769c78746" />
- https://github.com/COSC-499-W2025/capstone-project-team-6/issues/139
<img width="1470" height="956" alt="Screenshot 2025-11-23 at 9 22 43 PM" src="https://github.com/user-attachments/assets/13b61854-b815-482c-bba2-890073878241" />
- https://github.com/COSC-499-W2025/capstone-project-team-6/issues/148
<img width="1470" height="956" alt="Screenshot 2025-11-23 at 9 23 09 PM" src="https://github.com/user-attachments/assets/04523fec-2904-4585-86ed-7d92ce91522c" />

















# Mohamed Sakr
