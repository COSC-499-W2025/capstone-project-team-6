from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import aiofiles
import uuid
from datetime import datetime
from typing import List

app = FastAPI(title="Desktop App Backend", version="0.1.0")

# Configuration
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {".txt", ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".doc", ".docx", ".csv", ".json", ".xml"}

# Configure CORS for Electron app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify Electron app's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    """Health check endpoint"""
    return {"status": "ok", "message": "Backend is running"}


@app.get("/api/health")
def health_check():
    """API health check"""
    return {"status": "healthy"}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file to the server

    Args:
        file: The file to upload

    Returns:
        Dictionary with upload status and file information
    """
    try:
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # Read file content
        content = await file.read()
        file_size = len(content)

        # Validate file size
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
            )

        # Generate unique filename
        unique_id = uuid.uuid4().hex[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_name = Path(file.filename).stem
        unique_filename = f"{original_name}_{timestamp}_{unique_id}{file_ext}"
        file_path = UPLOAD_DIR / unique_filename

        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)

        return {
            "status": "success",
            "message": "File uploaded successfully",
            "filename": unique_filename,
            "original_filename": file.filename,
            "size": file_size,
            "size_mb": round(file_size / 1024 / 1024, 2),
            "path": str(file_path)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@app.post("/api/upload/multiple")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    """
    Upload multiple files to the server

    Args:
        files: List of files to upload

    Returns:
        Dictionary with upload results for each file
    """
    results = []

    for file in files:
        try:
            # Validate file extension
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in ALLOWED_EXTENSIONS:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": f"File type {file_ext} not allowed"
                })
                continue

            # Read file content
            content = await file.read()
            file_size = len(content)

            # Validate file size
            if file_size > MAX_FILE_SIZE:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": f"File too large (max {MAX_FILE_SIZE / 1024 / 1024}MB)"
                })
                continue

            # Generate unique filename
            unique_id = uuid.uuid4().hex[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_name = Path(file.filename).stem
            unique_filename = f"{original_name}_{timestamp}_{unique_id}{file_ext}"
            file_path = UPLOAD_DIR / unique_filename

            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)

            results.append({
                "filename": unique_filename,
                "original_filename": file.filename,
                "status": "success",
                "size": file_size,
                "size_mb": round(file_size / 1024 / 1024, 2)
            })

        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": str(e)
            })

    return {
        "status": "completed",
        "total": len(files),
        "successful": len([r for r in results if r["status"] == "success"]),
        "failed": len([r for r in results if r["status"] == "error"]),
        "results": results
    }
