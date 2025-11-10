# Mandira Samarasekara

![Mandira Week 10](images/MandiraW10.png)

## Date Range  
November 3 - November 9

## Tasks Worked On 
- Attended team meetings.  
- Completed the non-LLM project analysis implementation, which required considerable effort due to its technical complexity.  
- Designed and implemented comprehensive automated tests (29 total) to ensure reliability and maintainability of the metadata extraction system.  
- Created documentation and example scripts (`example_usage.py`) to make the system easier for teammates to understand, integrate, and test.  
- Reviewed, tested, and provided constructive feedback on teammates’ PRs to improve code quality and maintain consistency across the project.  

## Weekly Goals Recap 
- **Features I was responsible for (this milestone):**  
Phase 2 of the project analysis system — a comprehensive metadata extraction module that analyzes software projects without relying on LLMs. It builds upon the Phase 1 FileClassifier (by Aakash) to extract detailed project-level metadata including technology stacks, framework detection, dependency parsing, and project health metrics.  

Files and documentation included:  
- `METADATA_EXTRACTOR_README.md` – full documentation of the module  
- `example_usage.py` – showcases integration and usage for report generation  
- 29 automated unit tests covering all modules  

### What Went Well
- Successfully completed the Analysis Without LLMs module by Friday, enabling my teammate Mithish to proceed with his OOP analysis component, which depends on my implementation.  
- Achieved full test coverage with clean and maintainable code, ensuring the feature is stable and extensible.  

### What Didn’t Go as Planned
- Encountered challenges when implementing git contribution history retrieval. Despite significant effort, the process was more complex than expected since contributor history cannot be extracted without an active Git connection.  
- Temporarily filled this section with placeholder values until a suitable solution is implemented.  

### Looking Ahead
- Focus on implementing the git contributions feature with repository connection capabilities.  
- Add additional analysis metrics to improve report precision and contextual accuracy.  
- Optimize metadata extraction for performance and scalability to handle larger project datasets.  

## PRs initiated  
- [#105 – Analysis without LLMs](https://github.com/COSC-499-W2025/capstone-project-team-6/pull/105)  
- Completed issue #104  

## PRs reviewed  
- Constructed the Output Database – #115  
- Python OOP Code Analysis – #108  
- Mohamed W10 Logs – #121  
- Harjot’s Updated Logs (added reviewed & initiated PRs) – #117  


# Mithish Ravisankar Geetha  

## Date Range  

November 3 - November 9
![Mithish Week 9](images/Week10screenshotMithish.png)


## Tasks Worked On 
- Assisted Mandira for the non-LLM analysis by analyzing OOP principles in Python code files.
- Created an unified analysis script to run both Mandira's and my scripts together for the analysis.
- Reviewed pull requests and provided insights for the same.
- Created unit tests for my code.
- Attended team meetings and assigned teammates to tasks. 
## Weekly Goals Recap 
- **Features I was responsible for (this milestone):** 
1. OOP Code analysis for python

All of my goals this week have been met successfully. I have created detailed analysis for python OOP principles and the program gives a comprehensive report ranking the user's ability to design and apply object oriented programming principles. This week was busy due to midterms, hence I created only one PR which is slightly fewer than the usual. 


## PR's initiated
- Python OOP code analysis

## PR's reviewed
- Analysis without LLM




# Aakash  



## Date Range  
November 3 - November 9
![aakash Week 9=10](images/aakashlogs10.png)

## Tasks Worked On  
- llama stack initialization


## Weekly Goals Recap  
- finish the llama stack initialization with ollama and llama stack working in docker successfully 
- combining the docker contanarization of vector database, CLI, and llama stack together so that analysis with LLM's could work

### what was accomplished
- worked on llama stack initialization in the llama-stack-initialization branch
- got a working version of it on docker but a model we did not want to use was substituted as a default
- currently do not have a working version of docker with successful llama stack setup

### What Didn’t Go as Planned
- the docker steup for llama stack had so many small issues i could not get it out this week
- caused Mohammed to not be able to complete the task he was given as it required a working version of llama stack in docker. This made him need to pick up a last minute feature that needed implementing
- Due to llama stack and ollama complications new models where research we had not done on had to be selected
- ALthough the vector database works in a seperate docker it does not work with llama stack as of yet.

### What needs to be done
- I might need to resart the code on the docker as it has gotten extremely messy and solving thi sissues might not work out
- take a different approch to the dockerization of llama stack which moght work better
- better plan my timing as was busy during the week with tests and didnt give myself enough time to get the code working causing a backlog in progress for the team


## PR's initiated/gave input to
- llama-stack-initialization (not merged)

## PR's reviewed
- Analysis-without-LLM
- local embedding model
- refactor-vector-db-local

# Ansh Rastogi

## Date Range


## Tasks Worked On


## Weekly Goals Recap


# Harjot Sahota  


## Date Range  
November 3 - November 9
<img width="764" height="555" alt="Screenshot 2025-11-09 at 8 45 35 PM" src="https://github.com/user-attachments/assets/3d058f6b-9c32-47af-8fd0-edc60f7dba05" />


## Tasks Worked On  
- Researched the differences between local and cloud-based databases, comparing options like Supabase, PostgreSQL with pgvector, and other vector database alternatives.
- Refactored the vector database setup from Supabase (cloud) to a local pgvector instance using Docker Compose, finalizing the backend’s local embedding infrastructure.
- Updated `docker-compose.yml` to include a new `local_pgvector` service and ensured container-level database initialization worked through python -m backend.database_vector.
- Added fixtures and automated tests for vector database setup and document chunk embeddings.
- Integrated the local Ollama nomic-embed-text (768-dim) model to replace the JinaAI embedding model (which i also created).
- Verified end-to-end embedding generation, storage, and retrieval from the pgvector database.
- Reviewed teammate PRs, provided testing feedback, and helped resolve merge issues.
- Attended weekly meetings and coordinated backend integration tasks across the team.

## Weekly Goals Recap  
Transitioned to a fully local embedding setup and ensure backend database integration works end-to-end in Docker. The backend now supports offline embeddings using the Ollama model, ensuring faster performance and complete local control.
What didn’t go as planned:
- my initial PR https://github.com/COSC-499-W2025/capstone-project-team-6/issues/106 did not pass the GitHub CI pipeline due to dependency issues and incompatibility with the workflow environment. I resolved this by updating PostgreSQL drivers and Python versions in the CI setup.
- After completing the first embedding integration using the JinaAI model, we decided to switch to the local Ollama nomic-embed-text model, requiring additional refactoring and testing to ensure compatibility with the pgvector backend.
  

## PR's initiated
- local-embedding-model https://github.com/COSC-499-W2025/capstone-project-team-6/issues/112
- refactor-vector-db-local https://github.com/COSC-499-W2025/capstone-project-team-6/issues/106

## PR's reviewed
- OutputDatabase
- ansh/logs
- mithish-logs-w10

# Mohamed Sakr  
![Mohamed Week 10](images/MohamedW10.png)
## Date Range  
November 3 - November 9

## PRs
115: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/115
120: https://github.com/COSC-499-W2025/capstone-project-team-6/pull/120

## Tasks Worked On 
- Implemented the new SQLite-backed `analysis.db`, covering schema design for analyses, projects, languages, frameworks, dependencies, contributors, and largest-file metadata. Added helper APIs (`record_analysis`, `get_analysis`, `get_projects_for_analysis`) plus fixtures so tests spin up isolated databases.
- Built a standalone `documents.db` helper that persists uploaded artefacts with per-category counts (code/docs/tests/config/other) and added alias handling so downstream code can pass either friendly keys or column names. Wrote a focused pytest module verifying schema creation, inserts, and alias mapping.

## Weekly Goals Recap  
**Features I was responsible for (this milestone):**
- Delivered the persistence layer for both analysis outputs and document uploads, complete with initialization helpers, migration-safe defaults, and repeatable tests. This sets the foundation for exposing the data to the UI/dashboard next cycle.
- **What went well:** The schema work landed smoothly, and the modular DB helpers made it easy to plug tests into temporary paths. The SQLite fallback for vector embeddings significantly improved local reliability.
- **What didn’t go as planned:** Initial test runs failed because of environment gaps . I patched these during the week via fixtures and fallbacks, but they ate time intended for wiring the DBs into the analysis pipeline.
- **Looking ahead:** Priority for the next cycle is to integrate these databases directly into the app flow (triggering `record_analysis`/`save_document` from the analyzer).

**Progress in the last 2 weeks:** 
- Built a database for uploaded file with catgories
- Constructed a database to capture the outputs post-analysis
- Defined the tasks that will be done by the LLM and prompt engineered templates based on them.
- Researched models for the LLM-based Analysis both local & cloud based.
