"""Tests for applypilot.scoring.validator."""

import pytest
from applypilot.scoring.validator import (
    BANNED_WORDS,
    LLM_LEAK_PHRASES,
    sanitize_text,
    validate_cover_letter,
    validate_json_fields,
    validate_tailored_resume,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def minimal_profile():
    """Minimal profile dict with no preserved facts."""
    return {
        "personal": {"full_name": "Jane Doe", "email": "jane@example.com", "phone": "555-1234"},
        "resume_facts": {"preserved_companies": [], "preserved_projects": [], "preserved_school": ""},
        "skills_boundary": {},
    }


@pytest.fixture
def rich_profile():
    """Profile with real companies, school, and projects to preserve."""
    return {
        "personal": {"full_name": "Jane Doe", "email": "jane@example.com", "phone": "555-1234"},
        "resume_facts": {
            "preserved_companies": ["Acme Corp", "StartupXYZ"],
            "preserved_projects": ["PortfolioApp"],
            "preserved_school": "State University",
        },
        "skills_boundary": {
            "languages": ["Python", "JavaScript"],
            "cloud": ["AWS", "GCP"],
        },
    }


# ---------------------------------------------------------------------------
# sanitize_text
# ---------------------------------------------------------------------------

class TestSanitizeText:
    def test_em_dash_replaced_with_comma(self):
        assert sanitize_text("Worked on X \u2014 drove results") == "Worked on X, drove results"

    def test_em_dash_no_spaces(self):
        assert sanitize_text("A\u2014B") == "A, B"

    def test_en_dash_replaced_with_hyphen(self):
        assert sanitize_text("2020\u20132023") == "2020-2023"

    def test_smart_double_quotes_replaced(self):
        assert sanitize_text("\u201cHello\u201d") == '"Hello"'

    def test_smart_single_quotes_replaced(self):
        assert sanitize_text("it\u2019s") == "it's"

    def test_strips_leading_trailing_whitespace(self):
        assert sanitize_text("  hello  ") == "hello"

    def test_plain_text_unchanged(self):
        text = "Built a REST API using Python and FastAPI."
        assert sanitize_text(text) == text


# ---------------------------------------------------------------------------
# validate_json_fields
# ---------------------------------------------------------------------------

def _minimal_json_data(overrides=None):
    data = {
        "title": "Software Engineer",
        "summary": "Experienced engineer with Python skills.",
        "skills": {"languages": ["Python", "SQL"]},
        "experience": [{"header": "Acme Corp — SWE", "bullets": ["Built CI/CD pipelines."]}],
        "projects": [{"header": "PortfolioApp", "bullets": ["Deployed on AWS."]}],
        "education": "B.S. Computer Science, State University",
    }
    if overrides:
        data.update(overrides)
    return data


class TestValidateJsonFields:
    def test_valid_data_passes(self, minimal_profile):
        result = validate_json_fields(_minimal_json_data(), minimal_profile)
        assert result["passed"] is True
        assert result["errors"] == []

    def test_missing_required_field_fails(self, minimal_profile):
        data = _minimal_json_data()
        del data["summary"]
        result = validate_json_fields(data, minimal_profile)
        assert result["passed"] is False
        assert any("summary" in e for e in result["errors"])

    def test_all_missing_fields_reported(self, minimal_profile):
        result = validate_json_fields({}, minimal_profile)
        assert result["passed"] is False
        assert len(result["errors"]) >= 6  # one per required key

    def test_fabricated_skill_rejected(self, minimal_profile):
        data = _minimal_json_data({"skills": {"languages": ["Python", "golang"]}})
        result = validate_json_fields(data, minimal_profile)
        assert result["passed"] is False
        assert any("golang" in e for e in result["errors"])

    def test_llm_self_talk_always_error(self, minimal_profile):
        data = _minimal_json_data({"summary": "I apologize for any confusion in this resume."})
        result = validate_json_fields(data, minimal_profile, mode="lenient")
        assert result["passed"] is False
        assert any("LLM self-talk" in e for e in result["errors"])

    def test_banned_words_strict_mode_error(self, minimal_profile):
        data = _minimal_json_data({"summary": "I am passionate about building software."})
        result = validate_json_fields(data, minimal_profile, mode="strict")
        assert result["passed"] is False
        assert any("passionate" in e for e in result["errors"])

    def test_banned_words_normal_mode_warning(self, minimal_profile):
        data = _minimal_json_data({"summary": "I am passionate about building software."})
        result = validate_json_fields(data, minimal_profile, mode="normal")
        assert result["passed"] is True
        assert any("passionate" in w for w in result["warnings"])

    def test_banned_words_lenient_mode_ignored(self, minimal_profile):
        data = _minimal_json_data({"summary": "I am passionate about building software."})
        result = validate_json_fields(data, minimal_profile, mode="lenient")
        assert result["passed"] is True
        assert result["warnings"] == []

    def test_preserved_company_missing_fails(self, rich_profile):
        data = _minimal_json_data({"experience": [
            {"header": "SomeOtherCompany — SWE", "bullets": ["Did stuff."]}
        ]})
        result = validate_json_fields(data, rich_profile)
        assert result["passed"] is False
        assert any("Acme Corp" in e for e in result["errors"])

    def test_preserved_school_missing_fails(self, rich_profile):
        data = _minimal_json_data({"education": "B.S. CS, Unknown University"})
        result = validate_json_fields(data, rich_profile)
        assert result["passed"] is False
        assert any("State University" in e for e in result["errors"])

    def test_both_companies_present_passes(self, rich_profile):
        data = _minimal_json_data({"experience": [
            {"header": "Acme Corp — SWE", "bullets": ["Built things."]},
            {"header": "StartupXYZ — Engineer", "bullets": ["More things."]},
        ]})
        result = validate_json_fields(data, rich_profile)
        assert result["passed"] is True


# ---------------------------------------------------------------------------
# validate_tailored_resume
# ---------------------------------------------------------------------------

def _good_resume(profile):
    name = profile["personal"]["full_name"]
    companies = profile["resume_facts"].get("preserved_companies", [])
    school = profile["resume_facts"].get("preserved_school", "State University")
    exp_lines = "\n".join(f"{c}\nSoftware Engineer" for c in companies) if companies else "TechCorp\nSoftware Engineer"
    return f"""{name}
jane@example.com | 555-1234

SUMMARY
Experienced software engineer with Python skills.

TECHNICAL SKILLS
Languages: Python, JavaScript
Cloud: AWS, GCP

EXPERIENCE
{exp_lines}
- Built backend APIs using Python and Flask.

PROJECTS
PortfolioApp
- Deployed on AWS with Docker.

EDUCATION
B.S. Computer Science, {school}
"""


class TestValidateTailoredResume:
    def test_valid_resume_passes(self, rich_profile):
        text = _good_resume(rich_profile)
        result = validate_tailored_resume(text, rich_profile)
        assert result["passed"] is True, result["errors"]

    def test_missing_experience_section(self, minimal_profile):
        # Replace EXPERIENCE section header and also remove "Experienced" from
        # summary so "experience" doesn't appear as a substring elsewhere
        text = _good_resume(minimal_profile)
        text = text.replace("EXPERIENCE", "WORK HISTORY")
        text = text.replace("Experienced software engineer", "Senior software engineer")
        result = validate_tailored_resume(text, minimal_profile)
        assert result["passed"] is False
        assert any("EXPERIENCE" in e for e in result["errors"])

    def test_missing_education_section(self, minimal_profile):
        text = _good_resume(minimal_profile).replace("EDUCATION", "DEGREES")
        result = validate_tailored_resume(text, minimal_profile)
        assert result["passed"] is False
        assert any("EDUCATION" in e for e in result["errors"])

    def test_missing_preserved_company_fails(self, rich_profile):
        text = _good_resume(rich_profile).replace("Acme Corp", "RenamedCorp")
        result = validate_tailored_resume(text, rich_profile)
        assert result["passed"] is False
        assert any("Acme Corp" in e for e in result["errors"])

    def test_missing_preserved_school_fails(self, rich_profile):
        text = _good_resume(rich_profile).replace("State University", "Other University")
        result = validate_tailored_resume(text, rich_profile)
        assert result["passed"] is False
        assert any("State University" in e for e in result["errors"])

    def test_em_dash_causes_error(self, rich_profile):
        text = _good_resume(rich_profile) + "\u2014"
        result = validate_tailored_resume(text, rich_profile)
        assert result["passed"] is False
        assert any("em dash" in e for e in result["errors"])

    def test_banned_word_causes_error(self, rich_profile):
        text = _good_resume(rich_profile) + "\nI am passionate about software."
        result = validate_tailored_resume(text, rich_profile)
        assert result["passed"] is False
        assert any("passionate" in e for e in result["errors"])

    def test_llm_self_talk_causes_error(self, rich_profile):
        text = _good_resume(rich_profile) + "\nNote: This resume has been updated."
        result = validate_tailored_resume(text, rich_profile)
        assert result["passed"] is False
        assert any("LLM self-talk" in e for e in result["errors"])

    def test_fabricated_skill_in_technical_skills(self, rich_profile):
        text = _good_resume(rich_profile).replace(
            "Languages: Python, JavaScript", "Languages: Python, golang"
        )
        result = validate_tailored_resume(text, rich_profile)
        assert result["passed"] is False
        assert any("golang" in e for e in result["errors"])

    def test_name_missing_is_warning_not_error(self, rich_profile):
        text = _good_resume(rich_profile).replace("Jane Doe", "")
        result = validate_tailored_resume(text, rich_profile)
        assert any("Jane Doe" in w for w in result["warnings"])

    def test_new_fabricated_tool_flagged_vs_original(self, rich_profile):
        original = _good_resume(rich_profile)
        modified = original.replace("Python, JavaScript", "Python, JavaScript, django")
        result = validate_tailored_resume(modified, rich_profile, original_text=original)
        assert any("django" in w for w in result["warnings"])


# ---------------------------------------------------------------------------
# validate_cover_letter
# ---------------------------------------------------------------------------

def _good_cover_letter(word_count=200):
    words = ["software"] * word_count
    body = " ".join(words)
    return f"Dear Hiring Manager,\n\nI am writing to apply. {body}\n\nSincerely, Jane"


class TestValidateCoverLetter:
    def test_valid_cover_letter_passes(self):
        text = _good_cover_letter(200)
        result = validate_cover_letter(text)
        assert result["passed"] is True

    def test_must_start_with_dear(self):
        text = "Hello Hiring Manager,\n\nI am writing to apply."
        result = validate_cover_letter(text)
        assert result["passed"] is False
        assert any("Dear" in e for e in result["errors"])

    def test_em_dash_always_error(self):
        text = "Dear Hiring Manager,\n\nI built things \u2014 great things."
        result = validate_cover_letter(text)
        assert result["passed"] is False
        assert any("em dash" in e for e in result["errors"])

    def test_llm_self_talk_always_error(self):
        text = "Dear Hiring Manager,\n\nI apologize for the confusion. I am writing to apply."
        result = validate_cover_letter(text)
        assert result["passed"] is False
        assert any("LLM self-talk" in e for e in result["errors"])

    def test_banned_word_strict_mode_error(self):
        text = "Dear Hiring Manager,\n\nI am passionate about this role."
        result = validate_cover_letter(text, mode="strict")
        assert result["passed"] is False
        assert any("passionate" in e for e in result["errors"])

    def test_banned_word_normal_mode_warning(self):
        text = "Dear Hiring Manager,\n\nI am passionate about this role."
        result = validate_cover_letter(text, mode="normal")
        assert result["passed"] is True
        assert any("passionate" in w for w in result["warnings"])

    def test_banned_word_lenient_mode_ignored(self):
        text = "Dear Hiring Manager,\n\nI am passionate about this role."
        result = validate_cover_letter(text, mode="lenient")
        assert result["passed"] is True
        assert result["warnings"] == []

    def test_strict_mode_word_count_limit(self):
        text = _good_cover_letter(260)  # > 250
        result = validate_cover_letter(text, mode="strict")
        assert result["passed"] is False
        assert any("Too long" in e for e in result["errors"])

    def test_normal_mode_soft_word_limit(self):
        text = _good_cover_letter(280)  # > 275
        result = validate_cover_letter(text, mode="normal")
        assert any("Long" in w for w in result["warnings"])

    def test_lenient_mode_no_word_count_check(self):
        text = _good_cover_letter(400)  # way over limit
        result = validate_cover_letter(text, mode="lenient")
        assert result["passed"] is True

    def test_strict_mode_within_limit_passes(self):
        text = _good_cover_letter(200)
        result = validate_cover_letter(text, mode="strict")
        assert result["passed"] is True
