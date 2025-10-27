# File Upload Testing Guide

## Quick Start

### Terminal 1: Start the Server
```bash
cd src/backend
source .venv/bin/activate
uvicorn main:app --reload
```

**What you'll see:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

### Terminal 2: Upload Files
```bash
cd src/backend
source .venv/bin/activate

# Upload a single file
python upload_cli.py upload test_file.txt
```

---

## Testing Methods

### Method 1: CLI Tool (Recommended)

#### Single File Upload
```bash
python upload_cli.py upload test_file.txt
```

**Output:**
```
Uploading: test_file.txt
Size: 0.08 KB

✓ Upload successful!
  Original: test_file.txt
  Saved as: test_file_20251019_143022_a1b2c3d4.txt
  Size: 0.0 MB
  Path: /path/to/uploads/test_file_20251019_143022_a1b2c3d4.txt
```

**Where files go:** `src/backend/uploads/` directory

#### Multiple Files Upload
```bash
python upload_cli.py upload file1.txt file2.pdf file3.jpg
```

**Output:**
```
Uploading 3 files...

✓ Upload completed!
  Total: 3
  Successful: 3
  Failed: 0

Results:
  ✓ file1.txt
    Saved as: file1_20251019_143022_a1b2c3d4.txt (0.0 MB)
  ✓ file2.pdf
    Saved as: file2_20251019_143030_b2c3d4e5.pdf (0.1 MB)
  ✓ file3.jpg
    Saved as: file3_20251019_143035_c3d4e5f6.jpg (0.5 MB)
```

#### Check Server Health
```bash
python upload_cli.py health
```

**Output:**
```
✓ Backend is healthy at http://localhost:8000
```

---

### Method 2: Using curl

```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@test_file.txt"
```

**Output (JSON):**
```json
{
  "status": "success",
  "message": "File uploaded successfully",
  "filename": "test_file_20251019_143022_a1b2c3d4.txt",
  "original_filename": "test_file.txt",
  "size": 81,
  "size_mb": 0.0,
  "path": "/full/path/to/uploads/test_file_20251019_143022_a1b2c3d4.txt"
}
```

---

### Method 3: Browser (Interactive API Docs)

1. Make sure server is running
2. Open browser to: **http://localhost:8000/docs**
3. Click on **POST /api/upload**
4. Click **"Try it out"**
5. Click **"Choose File"** button
6. Select your file
7. Click **"Execute"**
8. See the response below

**Screenshots:**
- You'll see a Swagger UI interface
- File upload button to select files
- Response shows the JSON output

---

### Method 4: Automated Test Script

Run the complete test:
```bash
./test_upload.sh
```

This will:
1. Check if server is running
2. Create test files
3. Upload single file
4. Upload multiple files
5. Show uploaded files in the directory

---

## What Happens During Upload?

### Input:
- **File:** Any file from your computer (must be allowed type)
- **Location:** Anywhere on your filesystem
- **Command:** `python upload_cli.py upload /path/to/your/file.txt`

### Processing:
1. CLI reads your file
2. Sends it to `http://localhost:8000/api/upload`
3. Backend validates file type and size
4. Generates unique filename with timestamp
5. Saves to `uploads/` directory

### Output:
1. **Terminal:** Success message with file details
2. **File System:** File saved in `src/backend/uploads/`
3. **Filename:** `originalname_YYYYMMDD_HHMMSS_uniqueid.ext`

---

## File Constraints

### Allowed File Types:
- `.txt` - Text files
- `.pdf` - PDF documents
- `.jpg`, `.jpeg`, `.png`, `.gif` - Images
- `.doc`, `.docx` - Word documents
- `.csv` - CSV files
- `.json` - JSON files
- `.xml` - XML files

### File Size Limit:
- Maximum: **100 MB** per file

### Error Examples:

**Wrong file type:**
```
✗ Upload failed: File type .exe not allowed. Allowed types: .txt, .pdf, .jpg, ...
```

**File too large:**
```
✗ Upload failed: File too large. Maximum size: 100.0MB
```

**Server not running:**
```
✗ Error: Could not connect to http://localhost:8000
Make sure the backend server is running:
  cd src/backend
  uvicorn main:app --reload
```

---

## Checking Uploaded Files

```bash
# List all uploaded files
ls -lh uploads/

# Count uploaded files
ls uploads/ | wc -l

# View file contents
cat uploads/test_file_20251019_143022_a1b2c3d4.txt
```

---

## Cleanup

```bash
# Remove all uploaded files (be careful!)
rm uploads/*

# Remove specific test files
rm test_file_1.txt test_file_2.txt
```

---

## Troubleshooting

### Server won't start
```bash
# Check if port 8000 is already in use
lsof -i :8000

# Kill existing process if needed
kill -9 <PID>
```

### Can't connect to server
- Make sure Terminal 1 has the server running
- Check for errors in the server terminal
- Verify URL is `http://localhost:8000`

### Import errors
```bash
# Reinstall dependencies
cd src/backend
source .venv/bin/activate
uv pip install -r requirements.txt
```

---

## API Endpoints

- **POST /api/upload** - Upload single file
- **POST /api/upload/multiple** - Upload multiple files
- **GET /api/health** - Check server health
- **GET /** - Root endpoint (health check)
- **GET /docs** - Interactive API documentation
- **GET /redoc** - Alternative API documentation
