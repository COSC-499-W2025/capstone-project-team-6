"""Resume generation API endpoints."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.analysis_database import (add_items_to_user_resume,
                                       create_user_resume,
                                       get_all_analyses_for_user,
                                       get_analysis_by_uuid, get_connection,
                                       get_user_resume, get_user_resume_items,
                                       list_user_resumes,
                                       update_user_resume_content)
from backend.api.auth import verify_token

router = APIRouter(prefix="/api", tags=["Resume"])


class ResumeRequest(BaseModel):
    """Request to generate a resume."""

    portfolio_ids: List[str] = Field(..., description="List of portfolio UUIDs to include")
    format: str = Field("markdown", description="Output format: markdown, pdf, latex")
    include_skills: bool = Field(True, description="Include skills section")
    include_projects: bool = Field(True, description="Include projects section")
    max_projects: Optional[int] = Field(None, description="Maximum number of projects to include")
    personal_info: Optional[Dict[str, str]] = Field(
        None, description="Personal information (name, email, phone, location, linkedIn, github, website)"
    )
    stored_resume_id: Optional[int] = Field(None, description="Optional stored resume to use as the base")


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


class StoredResumeResponse(BaseModel):
    id: int
    title: str
    format: str
    content: str
    items: List[Dict[str, Any]]
    created_at: str
    updated_at: str


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


@router.post("/resume/generate", response_model=ResumeResponse)
async def generate_resume(
    request: ResumeRequest,
    username: str = Depends(verify_token),
):
    """Generate a resume from selected portfolios."""
    try:
        import base64

        from backend.analysis.resume_generator import generate_resume

        # Validate all portfolios exist and belong to user
        portfolios = []
        for portfolio_id in request.portfolio_ids:
            analysis = get_analysis_by_uuid(portfolio_id, username)
            if not analysis:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Portfolio {portfolio_id} not found or access denied",
                )
            portfolios.append(analysis)

        # If a stored resume is provided, use it as the base and append analysis bullets.
        if request.stored_resume_id:
            if request.format != "markdown":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Stored resumes can only be merged into markdown output",
                )
            stored_resume = get_user_resume(request.stored_resume_id, username)
            if not stored_resume:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Stored resume not found",
                )
            if stored_resume["format"] != "markdown":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Stored resume must be markdown to merge",
                )
            generated_content = generate_resume(
                portfolios=portfolios,
                format=request.format,
                include_skills=request.include_skills,
                include_projects=request.include_projects,
                max_projects=request.max_projects,
                personal_info=request.personal_info,
            )
            resume_content = _merge_resume_content(stored_resume["content_text"], generated_content)
        else:
            # Generate a full resume from selected portfolios
            resume_content = generate_resume(
                portfolios=portfolios,
                format=request.format,
                include_skills=request.include_skills,
                include_projects=request.include_projects,
                max_projects=request.max_projects,
                personal_info=request.personal_info,
            )

        # Convert PDF/LaTeX bytes to base64 string for JSON response
        if request.format in ("pdf", "latex") and isinstance(resume_content, bytes):
            resume_content = base64.b64encode(resume_content).decode("utf-8")

        # Generate resume ID (in production, save to database)
        import uuid

        resume_id = str(uuid.uuid4())

        return ResumeResponse(
            resume_id=resume_id,
            format=request.format,
            content=resume_content,
            metadata={
                "username": username,
                "portfolio_count": len(portfolios),
                "total_projects": sum(p["total_projects"] for p in portfolios),
                "generated_at": __import__("datetime").datetime.now().isoformat(),
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
    # This is a stub - in production, fetch from database
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
    # This is a stub - in production, update in database
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Resume editing not yet implemented. Generate a new resume instead.",
    )


@router.post("/resumes", response_model=StoredResumeResponse)
async def create_stored_resume(request: StoredResumeCreateRequest, username: str = Depends(verify_token)):
    if request.format not in ("markdown", "text"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only markdown/text resumes can be stored",
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


@router.post("/resumes/{resume_id}/items", response_model=StoredResumeResponse)
async def add_items_to_stored_resume(resume_id: int, request: AddResumeItemsRequest, username: str = Depends(verify_token)):
    if not request.resume_item_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No resume items selected")

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

    resume = get_user_resume(resume_id, username)
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
