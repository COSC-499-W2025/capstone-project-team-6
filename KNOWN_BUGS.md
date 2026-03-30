# Known Bugs List

This document tracks specific cases where implemented features do not work as expected.

---

### 1. Hard-coded File Path in Analysis Backend
**File:** `src/backend/api/analysis.py:313`

**Issue:** Analysis endpoint uses Windows-specific hard-coded file path
```python
FIXED_ZIP_PATH = Path(r"C:/Users/aakas/uni/cosc499/Project13_FreeCodeCamp.zip")
```

**How to reproduce:**
1. Deploy application on non-Windows machine or different user account
2. Attempt to start new analysis via `/api/analysis/start`
3. Request fails with "Zip file not found" error

**Expected behavior:** Analysis should use uploaded files from database/storage
**Actual behavior:** Always looks for specific file at hard-coded Windows path

**Impact:** Application cannot be deployed on production servers or different development machines



### 2. Authentication Token Expiry Race Condition 
**File:** `src/frontend/src/contexts/AuthContext.jsx`

**Issue:** Token expiry logic relies on client-side timing, causing premature or late logouts

**How to reproduce:**
1. Login to application
2. Change system clock forward by 30 minutes
3. Continue using application
4. Observe inconsistent authentication state

**Expected behavior:** Server should validate token expiry
**Actual behavior:** Client-side timer controls logout, vulnerable to clock manipulation

**Impact:** Users may be logged out unexpectedly or remain logged in with expired tokens


### 3. Session Storage Race Condition in Analysis 
**File:** `src/frontend/src/pages/AnalyzePage.jsx`

**Issue:** Complex fallback logic for task IDs can fail when multiple tabs or rapid navigation occurs

**How to reproduce:**
1. Start file upload in one tab
2. Open analyze page in second tab during upload
3. Navigate back/forward rapidly between upload and analyze pages
4. May show "Missing task" error despite valid upload

**Expected behavior:** Consistent task tracking across browser sessions
**Actual behavior:** Task IDs occasionally lost due to complex fallback chain

### 4. Memory Leaks in Portfolio Page 
**File:** `src/frontend/src/pages/Portfolio.jsx`

**Issue:** Event listeners and timers not properly cleaned up on component unmount

**How to reproduce:**
1. Navigate to Portfolio page
2. Leave page open and navigate to other pages multiple times
3. Return to Portfolio page repeatedly
4. Observe increasing memory usage in browser dev tools

**Expected behavior:** Memory usage should remain stable
**Actual behavior:** Memory usage increases with each visit to Portfolio page

### 5. Null Pointer Exceptions in Project Loading 
**File:** `src/frontend/src/pages/ProjectsPage.jsx`

**Issue:** Accessing properties on undefined project objects during loading states

**How to reproduce:**
1. Go to Projects page with slow network connection
2. Projects load incrementally
3. Console shows errors like "Cannot read property 'name' of undefined"
4. Some project cards may not render correctly

**Expected behavior:** Graceful loading with proper fallbacks
**Actual behavior:** JavaScript errors during loading states


### 6. Inconsistent API Response Handling 
**File:** `src/frontend/src/services/api.js`

**Issue:** Different endpoints return data in different envelope structures

**Examples:**
- Portfolio settings: `{ settings: {...} }`
- Projects: `{ projects: [...] }` or direct array `[...]`
- Some endpoints: `{ data: {...} }`

**Impact:** Requires complex parsing logic and prone to errors when API changes

### 7. Form Validation Edge Cases 
**File:** `src/frontend/src/pages/auth/LoginPage.jsx`

**Issue:** Username/password validation doesn't handle edge cases

**How to reproduce:**
1. Enter very long username (>1000 chars)
2. Use special characters in password
3. Submit form with whitespace-only inputs
4. Inconsistent error handling

**Expected behavior:** Consistent validation with clear error messages
**Actual behavior:** Some edge cases pass validation but fail at server

### 8. Incremental Upload Adds to Portfolio Items Instead of Projects
**File:** Upload functionality (multiple files involved)

**Issue:** When using incremental upload feature, files are incorrectly added to portfolio items instead of being processed as new projects

**How to reproduce:**
1. Go to Upload page
2. Select "Incremental Upload" option
3. Upload additional files to an existing project
4. Navigate to Portfolio page
5. Observe files appear as portfolio items instead of being integrated into the project

**Additional related issue:**
1. Delete a project from the Projects page
2. Go to Upload page and select "Incremental Upload"  
3. The deleted project still appears in the available projects list
4. This occurs because incremental upload polls available portfolios instead of active projects

**Expected behavior:** Incremental uploads should add files to existing projects and update project analysis. Deleted projects should not appear in the incremental upload options.

**Actual behavior:** Uploaded files are treated as separate portfolio items, and deleted projects remain visible for incremental upload


---
