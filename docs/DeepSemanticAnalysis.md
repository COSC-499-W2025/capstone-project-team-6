# Deep Semantic Code Analysis with Gemini 1.5

This document details the architecture, features, and usage of the AI-powered **Deep Semantic Analysis** engine included in the backend. This system leverages Google's Gemini Pro/Flash models and their **Long Context** capabilities to analyze entire codebases at once, providing insights that static analysis tools cannot match.

## 1. Architecture Overview

The analysis pipeline combines traditional static analysis with Large Language Model (LLM) reasoning. It is designed to be "context-aware," meaning it ingests the full source code of a project along with pre-computed metadata to generate high-level architectural critiques.

### Core Components

1.  **LLM Pipeline Orchestrator** (`src/backend/analysis/llm_pipeline.py`)
    *   Acts as the central controller.
    *   Integrates the "Offline Analysis" (static parsers for Python/Java/C++) to provide a factual baseline.
    *   Manages file filtering, reading, and preparation for the LLM.
    *   Constructs dynamic prompts based on requested analysis features.

2.  **Gemini File Search Client** (`src/backend/gemini_file_search.py`)
    *   A specialized wrapper around the `google-genai` SDK.
    *   Handles the **File API** interactions: uploading source code files to Google's temporary storage for LLM processing.
    *   Manages the lifecycle of remote files (Upload -> Poll for Active -> Generate -> Delete).
    *   Supports both **AI Studio** (API Key) and **Vertex AI** (Enterprise/GCP) authentication modes.


## 2. Analysis Workflow

When a project is submitted for analysis, the following steps occur:

1.  **Offline Pre-computation**: The system first runs `generate_comprehensive_report` to count lines of code, identify languages, and parse class structures (OOP metrics). This ensures the LLM has hard data to work with.
2.  **File Classification & Filtering**:
    *   The `FileClassifier` iterates through the ZIP.
    *   Binary files, images, and large files (>2MB) are skipped.
    *   Ignored directories (e.g., `node_modules`, `.git`, `venv`) and files (e.g., `.DS_Store`, `.env`) are filtered out to reduce noise and tokens.
3.  **Batch Upload**:
    *   Valid text files are extracted to a temporary directory.
    *   They are uploaded in parallel to the Gemini File API.
    *   The system polls the API until all files reach the `ACTIVE` state.
4.  **Prompt Construction**:
    *   A base prompt ("You are a Senior Principal Software Architect...") is combined with the specific **Feature Modules** requested by the user (see Section 3).
    *   The "Offline Analysis" JSON summary is injected into the context so the LLM knows the project stats.
5.  **Generation**: The model processes the prompt across the entire codebase (up to 2M tokens) and returns a structured Markdown report.
6.  **Cleanup**: Remote files are immediately deleted from Google Cloud to ensure data privacy and prevent storage costs.

## 3. Analysis Features (Modules)

The system is modular. You can enable specific analysis "lenses" to focus the AI's attention.

### Architecture (`--architecture`)
*   **Design Pattern Efficacy**: Identifies patterns (Singleton, Factory, etc.) and critiques if they are used correctly or abused.
*   **Anti-Pattern Detection**: Scans for "God Objects," circular dependencies, and spaghetti code.
*   **Data Flow**: Traces how data moves between layers (API -> Service -> DB) and checks for leakage.

### Complexity (`--complexity`)
*   **Big-O Gap Analysis**: Contrasts the *actual* time complexity of code (e.g., nested loops) against the *theoretical best case*.
*   **Algorithmic Intent**: Deduce what the code *tries* to do vs. how it does it.
*   **Concurrency Audit**: (For C++/Java/Go) Checks for race conditions, thread safety, and locking strategies.

### Security (`--security`)
*   **Logic-Based Security**: Looks beyond simple regex scans. Finds business logic flaws (e.g., "Can a user access another user's data by changing an ID?").
*   **Defensive Coding**: Evaluates input validation strategies and fail-safe logic.
*   **Information Leakage**: Checks if error handling exposes sensitive stack traces.

### Skills & Maturity (`--skills`)
*   **Soft Skills Inference**: Infers the developer's experience level based on folder structure, naming conventions, and refactoring habits.
*   **Testing Psychology**: Critiques whether tests check "happy paths" only or include defensive "failure mode" cases.
*   **Language Fluency**: Determines if the code is "idiomatic" (e.g., Pythonic) or "translated" from another language (e.g., writing C-style loops in Python).

### Domain (`--domain`)
*   **Framework Specifics**: Adapts the review based on detected frameworks (Django, React, Spring).
*   **Idiom Checks**: Ensures framework features are used correctly (e.g., using Dependency Injection in Spring, Hooks in React).
*   **REST Maturity**: Validates API design against standard HTTP conventions.

## 4. Setup & Configuration

### Prerequisites
*   Python 3.10+
*   Google Cloud Project (for Vertex AI) OR Google AI Studio API Key.

### Dependencies
Install the required packages from `src/backend/requirements.txt`:
```bash
pip install google-genai python-dotenv rich
```

### Environment Variables
Create a `.env` file in the root directory:

**Option A: Google AI Studio (Easiest)**
Use this for personal development or testing with the `gemini-2.5-flash` model.
```ini
GOOGLE_API_KEY=your_api_key_here
```

**Option B: Vertex AI (Enterprise)**
Use this for production environments with `gemini-1.5-pro-002`.
```ini
GOOGLE_CLOUD_PROJECT=your_gcp_project_id
GEMINI_LOCATION=us-central1
# Ensure you have authenticated via 'gcloud auth application-default login'
```

## 5. Usage Guide

### Command Line Interface (CLI)

You can run the analysis directly from the terminal using `src/backend/analysis/llm_pipeline.py`.

**Basic Run (General Deep Dive):**
```bash
PYTHONPATH=src python src/backend/analysis/llm_pipeline.py /path/to/project.zip
```

**Run with Specific Features:**
```bash
# Analyze Architecture and Security only
PYTHONPATH=src python src/backend/analysis/llm_pipeline.py /path/to/project.zip --architecture --security
```

**Run Full Analysis (All Modules):**
```bash
PYTHONPATH=src python src/backend/analysis/llm_pipeline.py /path/to/project.zip --all
```

**Output JSON (for API integration):**
```bash
PYTHONPATH=src python src/backend/analysis/llm_pipeline.py /path/to/project.zip --all --json
```

## 6. Troubleshooting

*   **"Google Cloud AI Platform libraries not installed"**: Ensure you installed `google-genai`.
*   **"No valid credentials found"**: Check your `.env` file for `GOOGLE_API_KEY` or ensure `GOOGLE_CLOUD_PROJECT` is set and you are authenticated with GCP.
*   **400 Bad Request / File Too Large**: The system automatically skips files > 2MB. If you have many small files that exceed the context window (1M/2M tokens), try analyzing a smaller subset or ignoring more folders in `IGNORED_PATH_KEYWORDS` inside `llm_pipeline.py`.
