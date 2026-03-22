"""Job description match analyzer using Gemini."""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

JOB_MATCH_PROMPT = """You are an expert career advisor and technical recruiter. Analyze how well a candidate's profile matches a job description.

## Candidate Profile

**Skills & Technologies:** {skills}

**Projects:**
{projects}

**Uploaded Resumes:**
{resumes}

## Job Description

{job_description}

---

Return ONLY a valid JSON object (no markdown, no explanation) with this exact structure:
{{
  "overall_score": <integer 0-100>,
  "skills_score": <integer 0-100>,
  "experience_score": <integer 0-100>,
  "matched_skills": [<list of skills the candidate has that match the JD>],
  "missing_skills": [<list of skills mentioned in JD that the candidate lacks>],
  "matched_requirements": [<list of JD requirements the candidate meets, as short phrases>],
  "unmet_requirements": [<list of JD requirements the candidate does not meet, as short phrases>],
  "recommendations": [<list of 2-4 actionable tips for the candidate to improve their match>],
  "summary": "<2-3 sentence overall assessment>"
}}

Scoring guidelines:
- overall_score: weighted average (skills 50%, experience 50%)
- skills_score: percentage of required/preferred skills the candidate has
- experience_score: how well their project descriptions, portfolio summaries, and resume bullets map to the role requirements
"""


def _strip_json_fences(text: str) -> str:
    """Remove markdown code fences from a Gemini response if present."""
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ```
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def analyze_job_match(
    job_description: str,
    user_skills: List[str],
    project_summaries: List[Dict[str, Any]],
    stored_resumes: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Compare a job description against the user's skills and projects.

    Args:
        job_description: The raw job description text.
        user_skills: Aggregated list of unique skills from the user's projects.
        project_summaries: List of dicts with keys: name, primary_language, predicted_role, frameworks.

    Returns:
        Dict with overall_score, skills_score, experience_score, matched_skills,
        missing_skills, matched_requirements, unmet_requirements, recommendations, summary.
    """
    from backend.gemini_file_search import GeminiFileSearchClient

    client_wrapper = GeminiFileSearchClient()

    skills_str = ", ".join(user_skills) if user_skills else "No skills detected yet"

    projects_lines = []
    for p in project_summaries:
        frameworks = ", ".join(p.get("frameworks", [])) or "none"
        lines = [
            f"- **{p['name']}** ({p.get('primary_language', 'unknown')}): "
            f"role={p.get('predicted_role', 'unknown')}, tech=[{frameworks}]"
        ]
        if p.get("portfolio_summary"):
            lines.append(f"  Summary: {p['portfolio_summary']}")
        if p.get("resume_bullets"):
            for bullet in p["resume_bullets"]:
                lines.append(f"  • {bullet}")
        projects_lines.append("\n".join(lines))
    projects_str = "\n".join(projects_lines) if projects_lines else "No projects uploaded yet."

    if stored_resumes:
        resume_parts = []
        for r in stored_resumes:
            resume_parts.append(f"### {r['title']}\n{r['content']}")
        resumes_str = "\n\n".join(resume_parts)
    else:
        resumes_str = "No resumes uploaded."

    prompt = JOB_MATCH_PROMPT.format(
        skills=skills_str,
        projects=projects_str,
        resumes=resumes_str,
        job_description=job_description,
    )

    response = client_wrapper.client.models.generate_content(
        model=client_wrapper.model_name,
        contents=prompt,
        config={"temperature": 0.2},
    )

    raw_text = response.text
    clean_text = _strip_json_fences(raw_text)

    try:
        result = json.loads(clean_text)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse Gemini response as JSON: %s\nRaw: %s", e, raw_text)
        raise ValueError(f"Gemini returned invalid JSON: {e}") from e

    # Ensure all expected keys are present with defaults
    defaults: Dict[str, Any] = {
        "overall_score": 0,
        "skills_score": 0,
        "experience_score": 0,
        "matched_skills": [],
        "missing_skills": [],
        "matched_requirements": [],
        "unmet_requirements": [],
        "recommendations": [],
        "summary": "",
    }
    for key, default in defaults.items():
        result.setdefault(key, default)

    # Clamp scores to 0-100
    for score_key in ("overall_score", "skills_score", "experience_score"):
        result[score_key] = max(0, min(100, int(result[score_key])))

    return result
