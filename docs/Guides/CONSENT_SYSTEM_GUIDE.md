# Consent System Documentation

## Overview

The application implements a **two-tier consent system** to ensure compliance with privacy requirements and user awareness of data handling practices.

## Consent Tiers

### 1. Basic Consent (Local Analysis)
- **Required for**: All application usage
- **Covers**: Local file analysis without external data transmission
- **Function**: `ask_for_consent()`
- **Stored in**: `user_consent` table in SQLite database

### 2. External Service Consent (AI-Enhanced Analysis)
- **Required for**: Using Google Gemini API (`analyze-llm` command)
- **Covers**: Uploading code to external cloud services
- **Function**: `ask_for_external_service_consent()`
- **Per-session**: Asked each time before uploading to external service

---

## Consent Flow Diagram

```
User Signup/Login
    ↓
Basic Consent Required
    ↓
[User Reviews Local Analysis Terms]
    ↓
Accept → Stored in Database
    ↓
User Can Use:
  - mda analyze (local)
  - mda analyze-essay (local)
  - mda timeline (local)
    ↓
User Runs: mda analyze-llm
    ↓
External Service Consent Required
    ↓
[User Reviews Google Gemini Terms]
    ↓
Accept → Temporary (this session)
    ↓
Data Uploaded to Google Cloud
    ↓
Analysis Results Returned
    ↓
Remote Files Deleted
```

---

## Implementation Details

### Basic Consent

**Location**: `src/backend/consent.py` - `ask_for_consent()`

**Key Points**:
- Displayed on first login or signup
- Explains local analysis capabilities
- Stored permanently in database
- Can be updated via `mda consent --update`

**Covers**:
- Local file parsing and metadata extraction
- OOP analysis (Python, Java, C++, C)
- Complexity analysis
- Git history analysis
- Database storage of results

**Does NOT cover**:
- External API calls
- Cloud-based AI analysis
- Data transmission over internet

### External Service Consent

**Location**: `src/backend/consent.py` - `ask_for_external_service_consent()`

**Key Points**:
- Displayed before EACH `analyze-llm` execution
- Explicit warning about data leaving device
- Lists exactly what data will be sent
- Explains Google's privacy policy applies
- Offers alternative (local analysis)

**Covers**:
- Uploading source code to Google Cloud
- Processing by Gemini AI models
- Temporary storage on Google servers
- Data deletion after analysis

**Privacy Warnings Include**:
- ⚠️ Data transmitted over internet
- ⚠️ Google's privacy policy applies
- ⚠️ Don't use for proprietary/confidential code
- ⚠️ Employer permission may be required

---

## Usage Examples

### Command Line

#### Check Consent Status
```bash
mda consent --status
```

#### Update Consent
```bash
mda consent --update
```

#### Local Analysis (No External Consent Required)
```bash
mda analyze project.zip
```

#### AI-Enhanced Analysis (External Consent Required)
```bash
mda analyze-llm project.zip
# → System will prompt for external service consent
# → User must explicitly agree before data upload
```

### Programmatic Usage

```python
from backend.consent import ask_for_consent, ask_for_external_service_consent

# Basic consent
if ask_for_consent():
    print("User can use local analysis")
else:
    print("User declined, cannot proceed")

# External service consent
if ask_for_external_service_consent("Google Gemini API"):
    # Proceed with external API call
    upload_to_gemini(project_data)
else:
    print("User declined external service")
    print("Falling back to local analysis")
    run_local_analysis(project_data)
```

---

## Database Schema

### user_consent Table
```sql
CREATE TABLE user_consent (
    username TEXT PRIMARY KEY,
    has_consented INTEGER NOT NULL CHECK(has_consented IN (0, 1)),
    consented_at TEXT,
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
);
```

**Fields**:
- `username`: User identifier (foreign key)
- `has_consented`: Boolean (0=no, 1=yes)
- `consented_at`: ISO timestamp of consent

---

## Privacy Guarantees

### Local Analysis (`mda analyze`)
✅ **All data stays on device**
- No internet connection required
- No external API calls
- All analysis using Python AST and static tools
- Results stored in local SQLite database
- Complete user control over data

### AI-Enhanced Analysis (`mda analyze-llm`)
⚠️ **Data transmitted to external service**
- Requires explicit per-use consent
- Source code uploaded to Google Cloud
- Processed by Gemini AI models
- Files deleted after analysis
- Subject to Google's privacy policy

---

## Testing

### Unit Tests
Located in: `src/tests/backend_test/test_consent.py`

**Coverage includes**:
- Basic consent form display
- Yes/no/invalid input handling
- EOF handling (Ctrl-D)
- Database integration
- Session integration
- External service consent
- Custom service names
- Retry logic

**Run tests**:
```bash
pytest src/tests/backend_test/test_consent.py -v
```

### Manual Testing
```bash
python test_consent_flow.py
```

This interactive script tests:
1. Basic consent prompt
2. External service consent prompt
3. Summary of consent decisions

---

## Compliance Requirements Met

✅ **Milestone Requirement #1**: User consent for data access
✅ **Milestone Requirement #4**: External service permission with privacy implications

### Before Fix (Non-Compliant)
- ❌ No separate Gemini consent
- ❌ No privacy implications explained
- ❌ Users unaware data would leave device

### After Fix (Compliant)
- ✅ Two-tier consent system
- ✅ Explicit external service warning
- ✅ Privacy implications clearly stated
- ✅ Alternative (local analysis) offered
- ✅ Per-use consent for external services

---

## Future Enhancements

### Persistent External Consent (Optional)
Add a database flag to remember external service consent:

```python
def check_external_consent(username):
    """Check if user has persistent external service consent."""
    with get_connection() as conn:
        result = conn.execute(
            "SELECT gemini_consent FROM user_consent WHERE username = ?",
            (username,)
        ).fetchone()
    return result and result[0] == 1

def save_external_consent(username, consented):
    """Save persistent external service consent preference."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE user_consent SET gemini_consent = ? WHERE username = ?",
            (1 if consented else 0, username)
        )
        conn.commit()
```

### Consent Audit Log
Track all consent decisions for audit purposes:

```sql
CREATE TABLE consent_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    consent_type TEXT NOT NULL, -- 'basic' or 'external'
    decision INTEGER NOT NULL, -- 0 or 1
    timestamp TEXT NOT NULL,
    FOREIGN KEY (username) REFERENCES users(username)
);
```

---

## Troubleshooting

### "Please provide consent before analyzing files"
**Solution**: Run `mda consent --update` to view and accept consent form

### External consent prompt appears every time
**Expected behavior**: External consent is per-session for maximum privacy awareness

### Want to skip external consent prompt
**Not recommended**: This would violate privacy requirements. Use local analysis instead:
```bash
mda analyze project.zip  # No external consent required
```

---

## References

- **Consent Module**: `src/backend/consent.py`
- **CLI Integration**: `src/backend/cli.py` (lines 18, 934-942)
- **Tests**: `src/tests/backend_test/test_consent.py`
- **Database**: `src/backend/database.py`
- **Google Privacy Policy**: https://cloud.google.com/terms/cloud-privacy-notice
