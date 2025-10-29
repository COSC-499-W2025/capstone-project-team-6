# COSC 499 Project Proposal

## Project Proposal for Mining Digital Artifacts  

**Team Number:** 06  
**Team Members:**  
- Aakash Tirathdas 19000413  
- Mithish Ravisankar Geetha 54389754  
- Ansh Rastogi 17164336  
- Harjot Sahota 97986475  
- Mohamed Sakr 14163851  
- Mandira Samarasekara 34542282  

---

## 1. Project Scope and Usage Scenario  

Our desktop application is designed to provide final-year students and early-career professionals with insights into their work over a specified period. Users grant the application access to their laptops and can specify which folders should be scanned and which should be excluded. The application then analyzes the selected folders, extracts relevant information, and presents it on a dashboard that provides a detailed overview of the user’s work.  

Initially, the project will target Computer Science students and those involved in coding-related activities. Support for students in other disciplines, such as literature or art, may be considered as a secondary feature depending on project scope and time constraints.  

---

## 2. Proposed Solution  

Our solution is to develop a desktop application that mines and analyzes digital work artifacts from a user’s laptop to provide insights into their projects, code contributions and outputs over time.  

By scanning selected folders, the app extracts metadata and content from code repositories, documents and other media. This information is organized and displayed on an interactive dashboard, offering users:  
- An overview of the work they’ve done so far  
- An overview of their productivity  
- Insights into skill development and the projects they’ve worked on  

Our app focuses on **personalized analysis with strict data privacy**, ensuring that all extracted data remains encrypted and is stored only on the user’s machine. We combine detailed code analysis with document and media summaries, allowing deeper and more structured insights than generic productivity apps.  

Users can also generate resumes and dashboards with minimal effort.  

---

## 3. Use Cases  

### Use Case 1: Dashboard Generator  
- **Primary actor:** Student / Professor  
- **Description:** The program generates a dashboard containing project information from a user’s laptop.  
- **Precondition:** User must give the app folder/laptop access.  
- **Postcondition:** Dashboard is displayed and can be interacted with.  

**Main Scenario:**  
1. User clicks “Generate dashboard”  
2. System validates requirements  
3. If valid, dashboard is generated  
4. Dashboard is displayed  

**Extensions:**  
- If invalid data is entered, system notifies user and requests correction  

---

### Use Case 2: Upload Folder  
- **Primary actor:** Student / Professor  
- **Description:** The system accepts a zipped folder for scanning.  
- **Precondition:** User has selected folder upload mode.  
- **Postcondition:** Zipped folder is stored in database (or memory if no database).  

**Main Scenario:**  
1. User selects “Upload folder”  
2. User drags & drops zipped folder  
3. System validates folder  
4. If valid, system confirms  
5. Folder is uploaded  

**Extensions:**  
- Invalid folder format results in error → user must re-upload  

---

### Use Case 3: Scanning and Analyzing Files  
- **Primary actor:** Final-year student / professional  
- **Description:** User selects folders/drives for local scan → app extracts summaries, logs results, and groups related files.  

**Preconditions:**  
- App installed locally  
- User logged in (authentication optional)  
- Folders selected for scan  
- Permissions granted  
- Enough memory available  
- No other scan running  

**Postconditions:**  
- Summaries and logs saved locally (encrypted)  
- Metadata stored in database  
- Scan session entry recorded  

**Main Scenario:**  
1. User clicks “Scan”  
2. System prompts folder/drive selection  
3. Permissions checked → elevated access requested if needed  
4. If granted, scan proceeds  
5. System stores session in database  
6. Resource constraints checked  
7. Files scanned:  
   - **Code:** detect language, count LOC, detect functions/classes, summarize  
   - **Docs:** extract author, headings, text snippets  
8. Summaries stored in database  
9. Stats generated (file counts, timelines, etc.)  
10. Analytics runs → dashboard links provided  

**Extensions:**  
- Permission denied → skip file  
- Memory exceeded → pause/terminate scan, save partial results  
- Cancel mid-scan → partial results saved  
- DB write failure → log + notify user  

---

### Use Case 4: Laptop Scanner Mode  
- **Primary actor:** Student / Professor  
- **Description:** Scans laptop for relevant projects, excluding user-specified/private folders.  

**Preconditions:**  
- User selects “Laptop scan” mode  
- OS must be Windows or Mac (Linux not supported)  

**Postcondition:**  
- Layout of scan generated (excluding prohibited folders)  

**Main Scenario:**  
1. User selects scan laptop  
2. User specifies folders to avoid  
3. Validation of inputs & OS compatibility  
4. If valid, scan layout is created & confirmation page shown  

**Extensions:**  
- Invalid folder/file inputs → error message  
- Unsupported OS → error, only upload mode available  

---

### Use Case 5: Mode Selection  
- **Primary actor:** Student / Professor  
- **Description:** User chooses between folder upload or laptop scanner mode.  

**Preconditions:**  
- Application downloaded successfully  
- No scan currently underway  

**Postcondition:**  
- User proceeds to upload or grant folder scan permissions  

**Main Scenario:**  
1. Open application  
2. System validates installation  
3. User selects mode  
4. System checks no scan is running  
5. If valid, user proceeds  

**Extensions:**  
- If a scan is running → system waits  

---

### Use Case 6: Secure Data Deletion  
- **Primary actor:** Student / Professor (Admin role optional)  
- **Description:** User deletes stored artifacts, summaries, metadata, and logs securely.  

**Preconditions:**  
- App installed and running  
- Prior scans exist  
- No active job  
- User authenticated  

**Postcondition:**  
- Selected data irreversibly deleted  
- Indexes updated  
- Deletion receipt generated  

**Main Scenario:**  
1. Open Privacy & Data Controls → Delete Data  
2. Choose deletion scope  
3. System verifies permissions  
4. Confirm deletion (e.g., type “DELETE”)  
5. System deletes data + rebuilds indexes  
6. Show deletion receipt  

**Extensions:**  
- Active job → block and retry later  
- Insufficient permissions → require Admin  
- Partial failure → rollback and retry  
- External exports → user advised to manually delete  
- Compliance mode → dual confirmation required  

---

## 4. Requirements, Testing, and Requirement Verification  

### Technology Stack & Test Framework  
- **Desktop Framework & UI:** Electron + React OR PyQt6  
- **Backend:** Python  
- **Database:** SQLite  
- **File Analysis:** GitPython, OpenCV, PyPDF2, python-docx, pytesseract, PyDriller  
- **Data Analysis & Visualization:** Pandas, Matplotlib, Seaborn, Plotly  
- **Testing:** Pytest  

---

### Requirement Table  

| Requirement | Description | Test Cases | Difficulty | Assigned To |
|-------------|-------------|------------|------------|-------------|
| **Multi-OS support** | App runs on Mac & Windows, handling OS-specific paths & permissions | Run app on both OS → error on unsupported OS | M | Mohamed Sakr |
| **Elevated Privilege Consent** | Prompt user when scanning privileged files | If granted → scan proceeds; else skip/halt | M | Harjot |
| **Folder Selection** | User selects folders to scan, system validates | Valid → scan starts; invalid → error | M | Aakash |
| **Code Analysis** | Detect language, functions, classes, LOC, contributions | Scan file → detect functions/classes; error if crash | H | Mandira |
| **Document Parsing** | Parse DOC/DOCX/PDF, extract data | Parse doc successfully; error otherwise | H | Mithish |
| **Laptop Scan Mode** | Full laptop scan, excluding prohibited/system files | Verify exclusions | H | Ansh |
| **Upload Folder Mode** | Upload zipped folder for scan | Valid zip → scan; else error | H | Harjot |
| **Processing Time** | Time from scan start to dashboard display | Ideally ≤ 5 minutes | E | Aakash |

---

