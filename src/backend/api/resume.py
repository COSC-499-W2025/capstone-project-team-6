"""Resume generation API endpoints."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.analysis.job_match_analyzer import analyze_job_match
from backend.analysis_database import (add_items_to_user_resume,
                                       create_user_education,
                                       create_user_resume,
                                       create_user_work_experience,
                                       delete_user_education,
                                       delete_user_personal_info,
                                       delete_user_resume,
                                       delete_user_work_experience,
                                       get_all_analyses_for_user,
                                       get_analysis_by_uuid, get_connection,
                                       get_portfolio_item_for_project,
                                       get_projects_for_user,
                                       get_resume_items_for_project_id,
                                       get_user_personal_info, get_user_resume,
                                       get_user_resume_items,
                                       list_user_education, list_user_resumes,
                                       list_user_work_experience,
                                       update_user_education,
                                       update_user_resume_content,
                                       update_user_work_experience,
                                       upsert_user_personal_info)
from backend.api.auth import verify_token

router = APIRouter(prefix="/api", tags=["Resume"])


class ResumeRequest(BaseModel):
    """Request to generate a resume."""

    project_ids: List[int] = Field(..., description="List of project DB integer IDs")
    format: str = Field("markdown", description="Output format: markdown, pdf, latex")
    include_skills: bool = Field(True, description="Include skills section")
    include_projects: bool = Field(True, description="Include projects section")
    max_projects: Optional[int] = Field(None, description="Maximum number of projects to include")
    personal_info: Optional[Dict[str, str]] = Field(
        None,
        description="Personal information (name, email, phone, location, linkedIn, github, website, education)",
    )
    stored_resume_id: Optional[int] = Field(None, description="Optional stored resume to use as the base")
    highlighted_skills: Optional[List[str]] = Field(
        None,
        description="Curated highlighted skills to use in the skills section (from curation settings)",
    )


class ResumeResponse(BaseModel):
    """Generated resume response."""

    resume_id: str
    format: str
    content: str
    metadata: Dict[str, Any]


class ResumeEditRequest(BaseModel):
    """Request to edit a resume."""

    content: str
    metadata: Optional[Dict[str, Any]] = None


class StoredResumeCreateRequest(BaseModel):
    title: str
    format: str = Field("markdown", description="markdown or text")
    content: str


class StoredResumeUpdateRequest(BaseModel):
    content: str


class AddResumeItemsRequest(BaseModel):
    resume_item_ids: List[int]


class PersonalInfoSaveRequest(BaseModel):
    personal_info: Dict[str, str] = Field(default_factory=dict)


class StoredResumeResponse(BaseModel):
    id: int
    title: str
    format: str
    content: str
    items: List[Dict[str, Any]]
    created_at: str
    updated_at: str


class JobMatchRequest(BaseModel):
    """Request to match a job description against user's profile."""

    job_description: str = Field(..., min_length=50, description="The job description text to match against")


class JobMatchResponse(BaseModel):
    """Job description match result."""

    overall_score: int
    skills_score: int
    experience_score: int
    matched_skills: List[str]
    missing_skills: List[str]
    matched_requirements: List[str]
    unmet_requirements: List[str]
    recommendations: List[str]
    summary: str


class PersonalInfoUpsertRequest(BaseModel):
    personal_info: Dict[str, str] = Field(
        ...,
        description="Personal information (name, email, phone, location, linkedIn, github, website, education)",
    )


class PersonalInfoResponse(BaseModel):
    personal_info: Optional[Dict[str, str]] = None


class EducationEntrySaveRequest(BaseModel):
    """Request body for creating/updating an education entry."""

    education_text: Optional[str] = None
    university: Optional[str] = None
    location: Optional[str] = None
    degree: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    awards: Optional[str] = None


class EducationEntryResponse(BaseModel):
    """Response model for an education entry."""

    id: int
    education_text: Optional[str] = None
    university: Optional[str] = None
    location: Optional[str] = None
    degree: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    awards: Optional[str] = None
    updated_at: Optional[str] = None


class WorkExperienceEntrySaveRequest(BaseModel):
    """Request body for creating/updating a work experience entry."""

    company: Optional[str] = None
    job_title: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    responsibilities_text: Optional[str] = None


class WorkExperienceEntryResponse(BaseModel):
    """Response model for a work experience entry."""

    id: int
    company: Optional[str] = None
    job_title: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    responsibilities_text: Optional[str] = None
    updated_at: Optional[str] = None


def _append_markdown_bullets(content: str, bullets: List[str]) -> str:
    if not bullets:
        return content

    section = "## Projects"
    bullet_block = "\n".join(f"- {bullet}" for bullet in bullets)

    if section in content:
        parts = content.split(section, 1)
        return f"{parts[0]}{section}\n{bullet_block}\n{parts[1]}"

    return f"{content.rstrip()}\n\n{section}\n{bullet_block}\n"


def _find_projects_heading_index(lines: List[str]) -> Optional[int]:
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped == "Projects":
            return idx
        if stripped.startswith("#") and stripped.lstrip("#").strip().lower() == "projects":
            return idx
    return None


def _extract_projects_section(markdown: str) -> str:
    lines = markdown.splitlines()
    start_idx = _find_projects_heading_index(lines)
    if start_idx is None:
        return markdown.strip()

    end_idx = len(lines)
    for idx in range(start_idx + 1, len(lines)):
        stripped = lines[idx].strip()
        if stripped.startswith("#") and stripped.lstrip("#").strip():
            end_idx = idx
            break

    section_lines = lines[start_idx + 1 : end_idx]
    return "\n".join(section_lines).strip()


def _extract_header_section(markdown: str) -> str:
    lines = markdown.splitlines()
    start_idx = _find_projects_heading_index(lines)
    if start_idx is None:
        return markdown.strip()

    header_lines = lines[:start_idx]
    return "\n".join(header_lines).strip()


def _merge_resume_content(base_content: str, generated_content: str) -> str:
    if not base_content:
        return generated_content
    if not generated_content:
        return base_content

    generated_header = _extract_header_section(generated_content)
    generated_projects = _extract_projects_section(generated_content)
    if not generated_projects:
        return base_content

    base_lines = base_content.splitlines()
    header_idx = _find_projects_heading_index(base_lines)
    merged_base = base_content.rstrip()
    if generated_header:
        if not merged_base.startswith(generated_header):
            merged_base = f"{generated_header}\n\n{merged_base}"

    if header_idx is None:
        return f"{merged_base}\n\n## Projects\n{generated_projects}\n"

    base_lines = merged_base.splitlines()
    header_idx = _find_projects_heading_index(base_lines)
    insert_idx = header_idx + 1
    while insert_idx < len(base_lines) and not base_lines[insert_idx].strip():
        insert_idx += 1

    merged_lines = base_lines[:insert_idx] + [generated_projects, ""] + base_lines[insert_idx:]
    return "\n".join(merged_lines).rstrip() + "\n"


@router.post("/resume/job-match", response_model=JobMatchResponse)
async def job_match(request: JobMatchRequest, username: str = Depends(verify_token)):
    """Match a job description against the user's skills, portfolio, and resume bullets."""
    import json as _json

    try:
        user_projects = get_projects_for_user(username)
        project_ids = [p["id"] for p in user_projects]

        user_skills: list[str] = []
        project_summaries: list[dict] = []

        if project_ids:
            placeholders = ",".join("?" for _ in project_ids)
            with get_connection() as conn:
                skill_rows = conn.execute(
                    f"SELECT DISTINCT skill FROM project_skills WHERE project_id IN ({placeholders})",
                    tuple(project_ids),
                ).fetchall()
                user_skills = [row["skill"] for row in skill_rows]

                framework_rows = conn.execute(
                    f"SELECT project_id, framework FROM project_frameworks WHERE project_id IN ({placeholders})",
                    tuple(project_ids),
                ).fetchall()

            frameworks_by_project: dict[int, list[str]] = {}
            for row in framework_rows:
                frameworks_by_project.setdefault(row["project_id"], []).append(row["framework"])

            for p in user_projects:
                pid = p["id"]

                # Portfolio item: richer LLM-generated description + skills
                portfolio = get_portfolio_item_for_project(pid) or {}
                portfolio_skills: list[str] = []
                portfolio_tech: list[str] = []
                for key, target in (("skills_exercised", portfolio_skills), ("tech_stack", portfolio_tech)):
                    raw = portfolio.get(key)
                    if isinstance(raw, str):
                        try:
                            parsed = _json.loads(raw)
                            target.extend(parsed if isinstance(parsed, list) else [])
                        except (_json.JSONDecodeError, TypeError):
                            pass
                    elif isinstance(raw, list):
                        target.extend(raw)

                # Merge portfolio skills into the global skill set
                user_skills = list(dict.fromkeys(user_skills + portfolio_skills))

                # Resume bullets for this project
                bullets = [row["resume_text"] for row in get_resume_items_for_project_id(pid)]

                project_summaries.append(
                    {
                        "name": p.get("project_name", "Unknown"),
                        "primary_language": p.get("primary_language", "unknown"),
                        "predicted_role": p.get("predicted_role", "unknown"),
                        "frameworks": frameworks_by_project.get(pid, []) + portfolio_tech,
                        "portfolio_summary": portfolio.get("text_summary") or "",
                        "resume_bullets": bullets,
                    }
                )

        # Stored resumes (user-uploaded or saved markdown/text)
        stored_resumes = [
            {"title": r["title"], "content": r["content_text"]} for r in list_user_resumes(username) if r["content_text"]
        ]

        result = analyze_job_match(
            job_description=request.job_description,
            user_skills=user_skills,
            project_summaries=project_summaries,
            stored_resumes=stored_resumes,
        )
        return JobMatchResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Job match analysis failed: {str(e)}",
        )


@router.get("/resume/personal-info")
async def get_personal_info(username: str = Depends(verify_token)):
    return {"personal_info": get_user_personal_info(username)}


@router.put("/resume/personal-info")
async def save_personal_info(request: PersonalInfoSaveRequest, username: str = Depends(verify_token)):
    upsert_user_personal_info(username, request.personal_info)
    return {"ok": True}


@router.delete("/resume/personal-info")
async def delete_personal_info(username: str = Depends(verify_token)):
    deleted = delete_user_personal_info(username)
    return {
        "ok": True,
        "deleted": deleted,
        "message": "Personal info removed" if deleted else "No personal info to remove",
    }


def _seed_education_from_personal_info(username: str) -> None:
    """One-time migration from legacy `personal_info.education_*` into `user_education`."""
    personal_info = get_user_personal_info(username) or {}

    # Prefer explicit education text if present.
    education_text = (personal_info.get("education") or "").strip()

    university = (personal_info.get("education_university") or personal_info.get("university") or "").strip()
    location = (personal_info.get("education_location") or personal_info.get("location") or "").strip()
    degree = (personal_info.get("education_degree") or personal_info.get("degree") or "").strip()
    start_date = (personal_info.get("education_start_date") or personal_info.get("start_date") or "").strip()
    end_date = (
        personal_info.get("education_end_date") or personal_info.get("grad_date") or personal_info.get("end_date") or ""
    ).strip()
    awards = (personal_info.get("education_awards") or "").strip()

    if not any([education_text, university, location, degree, start_date, end_date, awards]):
        return

    create_user_education(
        username,
        {
            "education_text": education_text or None,
            "university": university or None,
            "location": location or None,
            "degree": degree or None,
            "start_date": start_date or None,
            "end_date": end_date or None,
            "awards": awards or None,
        },
    )


@router.get("/resume/education", response_model=List[EducationEntryResponse])
async def list_education(username: str = Depends(verify_token)):
    entries = list_user_education(username)
    if not entries:
        _seed_education_from_personal_info(username)
        entries = list_user_education(username)
    return entries


@router.post("/resume/education", response_model=EducationEntryResponse)
async def create_education(request: EducationEntrySaveRequest, username: str = Depends(verify_token)):
    edu_id = create_user_education(username, request.model_dump())
    entries = list_user_education(username)
    # Fetch the created entry by id for a stable response shape.
    created = next((e for e in entries if e.get("id") == edu_id), None)
    if not created:
        # Fallback: return minimal
        return EducationEntryResponse(id=edu_id, updated_at=None)
    return created


@router.patch("/resume/education/{education_id}", response_model=EducationEntryResponse)
async def update_education(
    education_id: int,
    request: EducationEntrySaveRequest,
    username: str = Depends(verify_token),
):
    ok = update_user_education(username, education_id, request.model_dump())
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Education entry not found")
    entries = list_user_education(username)
    updated = next((e for e in entries if e.get("id") == education_id), None)
    if not updated:
        return EducationEntryResponse(id=education_id, updated_at=None)
    return updated


@router.delete("/resume/education/{education_id}")
async def delete_education(education_id: int, username: str = Depends(verify_token)):
    ok = delete_user_education(username, education_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Education entry not found")
    return {"ok": True, "deleted": True}


def _seed_work_experience_from_personal_info(username: str) -> None:
    """One-time migration from legacy `personal_info.work_*` into `user_work_experience`."""
    personal_info = get_user_personal_info(username) or {}

    company = (personal_info.get("work_company") or personal_info.get("company") or "").strip()
    job_title = (personal_info.get("work_job_title") or personal_info.get("job_title") or "").strip()
    location = (personal_info.get("work_location") or personal_info.get("location") or "").strip()
    start_date = (personal_info.get("work_start_date") or "").strip()
    end_date = (personal_info.get("work_end_date") or "").strip()
    responsibilities_text = (
        personal_info.get("work_responsibilities_text")
        or personal_info.get("work_responsibilities")
        or personal_info.get("responsibilities_text")
        or ""
    ).strip()

    if not any([company, job_title, location, start_date, end_date, responsibilities_text]):
        return

    create_user_work_experience(
        username,
        {
            "company": company or None,
            "job_title": job_title or None,
            "location": location or None,
            "start_date": start_date or None,
            "end_date": end_date or None,
            "responsibilities_text": responsibilities_text or None,
        },
    )


@router.get("/resume/work-experience", response_model=List[WorkExperienceEntryResponse])
async def list_work_experience(username: str = Depends(verify_token)):
    entries = list_user_work_experience(username)
    if not entries:
        _seed_work_experience_from_personal_info(username)
        entries = list_user_work_experience(username)
    return entries


@router.post("/resume/work-experience", response_model=WorkExperienceEntryResponse)
async def create_work_experience(
    request: WorkExperienceEntrySaveRequest,
    username: str = Depends(verify_token),
):
    work_id = create_user_work_experience(username, request.model_dump())
    entries = list_user_work_experience(username)
    created = next((e for e in entries if e.get("id") == work_id), None)
    if not created:
        return WorkExperienceEntryResponse(id=work_id, updated_at=None)
    return created


@router.patch("/resume/work-experience/{work_id}", response_model=WorkExperienceEntryResponse)
async def update_work_experience(
    work_id: int,
    request: WorkExperienceEntrySaveRequest,
    username: str = Depends(verify_token),
):
    ok = update_user_work_experience(username, work_id, request.model_dump())
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work experience entry not found")
    entries = list_user_work_experience(username)
    updated = next((e for e in entries if e.get("id") == work_id), None)
    if not updated:
        return WorkExperienceEntryResponse(id=work_id, updated_at=None)
    return updated


@router.delete("/resume/work-experience/{work_id}")
async def delete_work_experience(work_id: int, username: str = Depends(verify_token)):
    ok = delete_user_work_experience(username, work_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work experience entry not found")
    return {"ok": True, "deleted": True}


@router.post("/resume/generate", response_model=ResumeResponse)
async def generate_resume(
    request: ResumeRequest,
    username: str = Depends(verify_token),
):
    """Generate a resume from selected projects."""
    try:
        import base64
        import json
        import uuid
        from datetime import datetime

        from backend.analysis.resume_generator import \
            generate_resume as generate_resume_impl

        if not request.project_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No project IDs provided",
            )

        # Validate stored_resume_id early so we fail fast before hitting the DB
        stored_resume = None
        if request.stored_resume_id is not None:
            stored_resume = get_user_resume(request.stored_resume_id, username)
            if not stored_resume:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Stored resume not found",
                )
            if request.format != "markdown":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Merging with a stored resume requires markdown output format",
                )
            if stored_resume["format"] != "markdown":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Stored resume must be in markdown format to merge",
                )

        # Fetch all projects belonging to the user and build a lookup map
        user_projects = get_projects_for_user(username)
        user_project_map = {p["id"]: p for p in user_projects}

        # Build project bundles for the resume generator
        bundles = []
        for pid in request.project_ids:
            project = user_project_map.get(pid)
            if not project:
                # Skip project IDs that don't belong to this user
                continue

            resume_items = [dict(r) for r in get_resume_items_for_project_id(pid)]

            # Fetch portfolio item and parse its JSON fields
            portfolio_item = get_portfolio_item_for_project(pid) or {}
            for key in ("tech_stack", "skills_exercised"):
                raw = portfolio_item.get(key)
                if not raw:
                    portfolio_item[key] = []
                elif isinstance(raw, str):
                    try:
                        parsed = json.loads(raw)
                        portfolio_item[key] = parsed if isinstance(parsed, list) else []
                    except (TypeError, json.JSONDecodeError):
                        portfolio_item[key] = []

            # The resume generator looks for portfolio["skills"]
            portfolio_item["skills"] = portfolio_item.get("skills_exercised") or []

            bundles.append(
                {
                    "project": project,
                    "resume_items": resume_items,
                    "portfolio": portfolio_item,
                }
            )

        if not bundles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No valid projects found for the provided IDs",
            )

        education_entries = list_user_education(username)
        if not education_entries:
            _seed_education_from_personal_info(username)
            education_entries = list_user_education(username)

        # Pass education entries to the resume generator. We keep personal_info as provided
        # but augment it with `education_entries` so the generator can render multiple schools.
        personal_info_for_gen: Dict[str, Any] = dict(request.personal_info or {})
        personal_info_for_gen["education_entries"] = education_entries or []
        if education_entries:
            first = education_entries[0] or {}
            # Backward-compat fields (in case the generator falls back to legacy keys).
            personal_info_for_gen.setdefault(
                "education_university",
                first.get("university")
                or personal_info_for_gen.get("education_university")
                or personal_info_for_gen.get("university"),
            )
            personal_info_for_gen.setdefault(
                "education_location",
                first.get("location") or personal_info_for_gen.get("education_location") or personal_info_for_gen.get("location"),
            )
            personal_info_for_gen.setdefault(
                "education_degree",
                first.get("degree") or personal_info_for_gen.get("education_degree") or personal_info_for_gen.get("degree"),
            )
            personal_info_for_gen.setdefault(
                "education_start_date",
                first.get("start_date")
                or personal_info_for_gen.get("education_start_date")
                or personal_info_for_gen.get("start_date"),
            )
            personal_info_for_gen.setdefault(
                "education_end_date",
                first.get("end_date")
                or personal_info_for_gen.get("education_end_date")
                or personal_info_for_gen.get("grad_date"),
            )
            personal_info_for_gen.setdefault(
                "education_awards",
                first.get("awards") or personal_info_for_gen.get("education_awards"),
            )
            personal_info_for_gen.setdefault(
                "education",
                first.get("education_text") or personal_info_for_gen.get("education"),
            )

        work_entries = list_user_work_experience(username)
        if not work_entries:
            _seed_work_experience_from_personal_info(username)
            work_entries = list_user_work_experience(username)

        personal_info_for_gen["work_experience_entries"] = work_entries or []

        # Backward-compat fields (if generator falls back to legacy keys).
        if work_entries:
            first_w = work_entries[0] or {}
            personal_info_for_gen.setdefault(
                "work_company",
                first_w.get("company") or personal_info_for_gen.get("work_company") or personal_info_for_gen.get("company"),
            )
            personal_info_for_gen.setdefault(
                "work_job_title",
                first_w.get("job_title") or personal_info_for_gen.get("work_job_title") or personal_info_for_gen.get("job_title"),
            )
            personal_info_for_gen.setdefault(
                "work_location",
                first_w.get("location") or personal_info_for_gen.get("work_location") or personal_info_for_gen.get("location"),
            )
            personal_info_for_gen.setdefault(
                "work_start_date",
                first_w.get("start_date")
                or personal_info_for_gen.get("work_start_date")
                or personal_info_for_gen.get("start_date"),
            )
            personal_info_for_gen.setdefault(
                "work_end_date",
                first_w.get("end_date") or personal_info_for_gen.get("work_end_date") or personal_info_for_gen.get("end_date"),
            )
            personal_info_for_gen.setdefault(
                "work_responsibilities_text",
                first_w.get("responsibilities_text")
                or personal_info_for_gen.get("work_responsibilities_text")
                or personal_info_for_gen.get("responsibilities_text"),
            )

        # Generate the resume content
        resume_content = generate_resume_impl(
            projects=bundles,
            format=request.format,
            include_skills=request.include_skills,
            include_projects=request.include_projects,
            max_projects=request.max_projects,
            personal_info=personal_info_for_gen,
            highlighted_skills=request.highlighted_skills,
        )

        # Encode binary formats (pdf / latex) as base64 for JSON transport
        if request.format in ("pdf", "latex") and isinstance(resume_content, bytes):
            resume_content = base64.b64encode(resume_content).decode("utf-8")

        # Merge generated content into the stored resume when requested
        if stored_resume is not None and isinstance(resume_content, str):
            resume_content = _merge_resume_content(stored_resume["content_text"], resume_content)

        return ResumeResponse(
            resume_id=str(uuid.uuid4()),
            format=request.format,
            content=resume_content,
            metadata={
                "username": username,
                "project_count": len(bundles),
                "total_projects": len(bundles),
                "generated_at": datetime.now().isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate resume: {str(e)}",
        )


@router.get("/resume/{resume_id}", response_model=ResumeResponse)
async def get_resume(resume_id: str, username: str = Depends(verify_token)):
    """Get a previously generated resume by ID (stub - needs database implementation)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Resume retrieval not yet implemented. Resumes are currently ephemeral.",
    )


@router.post("/resume/{resume_id}/edit", response_model=ResumeResponse)
async def edit_resume(
    resume_id: str,
    edit_request: ResumeEditRequest,
    username: str = Depends(verify_token),
):
    """Edit a previously generated resume (stub - needs database implementation)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Resume editing not yet implemented. Generate a new resume instead.",
    )


@router.post("/resumes", response_model=StoredResumeResponse)
async def create_stored_resume(request: StoredResumeCreateRequest, username: str = Depends(verify_token)):
    if request.format not in ("markdown", "text", "pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only markdown/text/pdf resumes can be stored",
        )

    resume_id = create_user_resume(
        username=username,
        title=request.title,
        format=request.format,
        content_text=request.content,
    )
    row = get_user_resume(resume_id, username)
    return StoredResumeResponse(
        id=row["id"],
        title=row["title"],
        format=row["format"],
        content=row["content_text"],
        items=[],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.get("/resumes", response_model=List[StoredResumeResponse])
async def list_stored_resumes(username: str = Depends(verify_token)):
    rows = list_user_resumes(username)
    return [
        StoredResumeResponse(
            id=row["id"],
            title=row["title"],
            format=row["format"],
            content=row["content_text"],
            items=[],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]


@router.get("/resume/personal-info", response_model=PersonalInfoResponse)
async def get_personal_info_v2(username: str = Depends(verify_token)):
    info = get_user_personal_info(username)
    return PersonalInfoResponse(personal_info=info or None)


@router.put("/resume/personal-info", response_model=PersonalInfoResponse)
async def upsert_personal_info(
    request: PersonalInfoUpsertRequest,
    username: str = Depends(verify_token),
):
    upsert_user_personal_info(username, request.personal_info)
    saved = get_user_personal_info(username)
    return PersonalInfoResponse(personal_info=saved or None)


@router.get("/resumes/{resume_id}", response_model=StoredResumeResponse)
async def get_stored_resume(resume_id: int, username: str = Depends(verify_token)):
    row = get_user_resume(resume_id, username)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    items = get_user_resume_items(resume_id, username)
    return StoredResumeResponse(
        id=row["id"],
        title=row["title"],
        format=row["format"],
        content=row["content_text"],
        items=[dict(item) for item in items],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.patch("/resumes/{resume_id}", response_model=StoredResumeResponse)
async def update_stored_resume(resume_id: int, request: StoredResumeUpdateRequest, username: str = Depends(verify_token)):
    update_user_resume_content(resume_id, username, request.content)
    row = get_user_resume(resume_id, username)
    items = get_user_resume_items(resume_id, username)
    return StoredResumeResponse(
        id=row["id"],
        title=row["title"],
        format=row["format"],
        content=row["content_text"],
        items=[dict(item) for item in items],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.delete("/resumes/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stored_resume_endpoint(resume_id: int, username: str = Depends(verify_token)):
    deleted = delete_user_resume(resume_id, username)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")


@router.post("/resumes/{resume_id}/items", response_model=StoredResumeResponse)
async def add_items_to_stored_resume(resume_id: int, request: AddResumeItemsRequest, username: str = Depends(verify_token)):
    if not request.resume_item_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No resume items selected")

    resume = get_user_resume(resume_id, username)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    with get_connection() as conn:
        placeholders = ",".join("?" for _ in request.resume_item_ids)
        rows = conn.execute(
            f"""
            SELECT id, analysis_id, project_id, resume_text
            FROM resume_items
            WHERE id IN ({placeholders})
            """,
            tuple(request.resume_item_ids),
        ).fetchall()

    if not rows:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid resume items found")

    items = [
        {
            "resume_item_id": row["id"],
            "analysis_id": row["analysis_id"],
            "project_id": row["project_id"],
            "bullet_text": row["resume_text"],
            "bullet_order": idx,
        }
        for idx, row in enumerate(rows)
    ]
    add_items_to_user_resume(resume_id, username, items)

    merged_content = _append_markdown_bullets(resume["content_text"], [row["resume_text"] for row in rows])
    update_user_resume_content(resume_id, username, merged_content)

    updated = get_user_resume(resume_id, username)
    stored_items = get_user_resume_items(resume_id, username)
    return StoredResumeResponse(
        id=updated["id"],
        title=updated["title"],
        format=updated["format"],
        content=updated["content_text"],
        items=[dict(item) for item in stored_items],
        created_at=updated["created_at"],
        updated_at=updated["updated_at"],
    )
