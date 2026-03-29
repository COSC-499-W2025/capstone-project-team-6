# Frontend Test Report

## 1. Introduction

This report summarizes the frontend testing completed for the capstone system. It lists the frontend test files currently used in the project, the components and features they cover, and the testing strategies used to verify that the user interface behaves as expected.

The frontend is the main user interaction layer of the system. It supports important workflows such as authentication, consent management, project upload and analysis, showcase curation, resume generation, portfolio viewing, and account settings. Because of this, frontend testing focused on confirming that these user-facing features render correctly, respond properly to user actions, and handle success, loading, and error states reliably.

---

## 2. Scope of Frontend Testing

The frontend tests focus on validating the behavior of the React user interface. This includes:

- page and component rendering
- user interaction with forms, buttons, filters, and modals
- conditional rendering based on user state or API data
- loading and error handling
- navigation between pages
- localStorage and sessionStorage behavior
- mocked API integration

The testing does not directly validate backend implementation details or full production end-to-end browser execution. Instead, it verifies that the frontend behaves correctly when interacting with mocked backend responses.

---

## 3. Test Environment

The frontend test suite uses the following tools and configuration:

- **Framework:** Vitest v3 with `@testing-library/react` v16
- **Test environment:** `jsdom` for browser DOM simulation
- **Configuration file:** `src/frontend/vite.config.js`
- **Setup file:** `src/frontend/src/tests/setup.js`
- **Run commands:** `npm test` for watch mode or `npx vitest run` for a single run

The setup file imports `@testing-library/jest-dom` matchers and provides a spec-compliant `localStorage` mock so tests run consistently across environments.

---

## 4. Test Files and Coverage

All frontend test files are located in `src/frontend/src/tests/`. The current test suite contains 10 test files and 181 total tests.

To run these tests:
```
    cd src/frontend
    npx vitest run
```

| Test File | Component | Tests | Primary Coverage |
|---|---:|---:|---|
| `App.test.jsx` | ErrorBoundary | 7 | Crash recovery, fallback UI, error logging |
| `AnalyzePage.test.jsx` | AnalyzePage | 22 | Async polling, progress updates, multi-task analysis flow |
| `Upload.test.jsx` | Upload | 9 | File upload flow, task ID extraction, LLM consent gating |
| `Resume.test.jsx` | Resume | 24 | Resume generation, validation, selection logic, showcase integration |
| `ProjectsPage.test.jsx` | ProjectsPage | 26 | Authentication, loading, filtering, sorting, LLM analysis panel |
| `Settings.test.jsx` | Settings | 27 | Consent toggle, personal info CRUD, delete account flow |
| `Dashboard.test.jsx` | Dashboard | 18 | Showcase cards, navigation, quick actions, error handling |
| `CuratePage.test.jsx` | CuratePage | 27 | All curation tabs, save flows, loading and error states |
| `ProjectsPageShowcase.test.jsx` | ProjectsPage | 10 | Showcase filtering, curated sorting, rank badges |
| `pages/Portfolio.test.jsx` | Portfolio | 11 | Portfolio list/detail rendering, auth redirect, empty/error states |

---

## 5. Detailed Test Coverage

### 5.1 `App.test.jsx`
**Component under test:** `ErrorBoundary` inside `App.jsx`  
**Total tests:** 7

This file tests the app’s error boundary. It checks that the page renders normally when there is no error, and that a fallback message appears instead of a blank screen when an error happens. It also checks that the reload button appears and that errors are logged properly.

### 5.2 `AnalyzePage.test.jsx`
**Component under test:** `src/frontend/src/pages/AnalyzePage.jsx`  
**Total tests:** 22

This file tests the analysis progress page. It covers missing task IDs, missing auth tokens, polling progress, failed analysis states, and successful navigation to the projects page when analysis is complete.

It also checks multi-task analysis, average progress calculation, phase messages, and storing important values in `sessionStorage`.

### 5.3 `Upload.test.jsx`
**Component under test:** `src/frontend/src/pages/Upload.jsx`  
**Total tests:** 9

This file tests the upload page. It checks that uploaded projects return task IDs correctly, that errors are shown if task IDs are missing, and that users can continue to the analysis step.

It also tests multi-project uploads and makes sure LLM analysis is only used when the user has consented.

### 5.4 `Resume.test.jsx`
**Component under test:** `src/frontend/src/pages/Resume.jsx`  
**Total tests:** 24

This file tests the resume page. It checks that projects load properly, that the Generate button works correctly, and that resumes are generated and displayed when the API succeeds.

It also tests validation for personal info, error messages when generation fails, project selection features like Select All, and showcase-related selection options.

### 5.5 `ProjectsPage.test.jsx`
**Component under test:** `src/frontend/src/ProjectsPage.jsx`  
**Total tests:** 26

This file tests the projects page. It checks authentication redirects, loading states, API errors, empty states, and normal project rendering.

It also covers searching, filtering, sorting, dashboard navigation, and whether the AI analysis panel only appears for LLM projects.

### 5.6 `Settings.test.jsx`
**Component under test:** `src/frontend/src/pages/Settings.jsx`  
**Total tests:** 27

This file tests the settings page. It checks the page header, dashboard navigation, loading states, consent display, and the consent toggle modal.

It also covers personal info loading, saving, deleting, validation, cancel changes, and the delete account flow, including clearing tokens and redirecting the user after success.

### 5.7 `Dashboard.test.jsx`
**Component under test:** `src/frontend/src/pages/Dashboard.jsx`  
**Total tests:** 18

This file tests the dashboard page. It checks the showcase section, empty states, project cards, ranking badges, metadata display, and fallback values for missing data.

It also tests navigation from showcase cards and confirms that quick action cards still appear.

### 5.8 `CuratePage.test.jsx`
**Component under test:** `src/frontend/src/pages/CuratePage.jsx`  
**Total tests:** 27

This file tests the curation page. It checks page rendering, loading projects and settings, navigation back to the dashboard, and switching between all five tabs.

It also tests save actions and error handling in the showcase, attributes, skills, chronology, and project order sections.

### 5.9 `ProjectsPageShowcase.test.jsx`
**Component under test:** `src/frontend/src/ProjectsPage.jsx`  
**Total tests:** 10

This file focuses on showcase behavior in the projects page. It checks that showcase filters work correctly, that the banner appears when filtering is active, and that users can return to showing all projects.

It also checks curated sort options and top-rank badges for showcase projects.

### 5.10 `pages/Portfolio.test.jsx`
**Component under test:** `src/frontend/src/pages/Portfolio.jsx`  
**Total tests:** 11

This file tests the portfolio page. It checks authentication redirects, loading states, API errors, and portfolio item rendering after data loads.

It also tests switching between portfolio items, handling missing skills data, and showing an empty state when no items are available.

---

## 6. Test Strategies Used

The frontend test suite uses several strategies to ensure the system behaves correctly across normal, loading, failure, and edge-case scenarios.

### 6.1 Rendering Verification
Rendering tests verify that expected UI elements appear after the component is mounted or after data finishes loading. These checks confirm that the JSX output matches the intended frontend design.

Examples include:
- confirming page headings and buttons exist
- confirming project cards render after API data loads
- confirming empty-state messages appear when lists are empty

### 6.2 User Interaction Simulation
User interaction tests simulate real frontend behavior by triggering clicks, input changes, modal confirmations, and selection toggles. These tests confirm that the correct state changes happen after user actions.

Examples include:
- clicking Generate on the Resume page
- toggling consent in Settings
- selecting showcase projects
- changing filters and sort settings on Projects

### 6.3 Async State Testing
Async tests verify the transition between loading, success, and error states when promises resolve or reject. `waitFor` is used to confirm that the frontend updates correctly after asynchronous operations complete.

Examples include:
- loading indicators disappearing after API responses
- progress bars updating during analysis polling
- error messages showing after rejected requests

### 6.4 API Mock Isolation
All API modules are mocked with `vi.mock(...)` and `vi.fn()` so that each test runs deterministically without real network activity. `mockResolvedValue`, `mockRejectedValue`, and `mockImplementation` are used to simulate different backend outcomes.

This strategy ensures that frontend behavior can be tested independently of backend availability. It also makes tests faster and more reliable.

### 6.5 Router Mocking
Navigation behavior is tested by mocking `useNavigate` and providing router context through `MemoryRouter` or `BrowserRouter`. This allows the test suite to confirm redirect and navigation behavior without using a real browser history.

Examples include:
- redirecting unauthenticated users to `/login`
- navigating to `/projects` after analysis completion
- moving from the dashboard to curation or project pages

### 6.6 Auth Context Mocking
Authentication-dependent pages are tested by mocking the authentication context. This allows both authenticated and unauthenticated scenarios to be tested without a live auth provider.

Examples include:
- authenticated access to protected pages
- unauthenticated redirects
- clearing stored auth tokens after delete account

### 6.7 Error Path Testing
The suite deliberately tests API failures and unexpected data shapes to verify that the frontend does not crash and instead displays useful fallback behavior.

Examples include:
- structured API errors using `response.data.detail`
- generic `Error` objects
- invalid or non-array API responses
- empty or missing fields in project metadata

### 6.8 Boundary and Edge Case Testing
Boundary testing checks how the frontend behaves when it receives incomplete, null, empty, or unexpected values.

Examples include:
- null `project_name`
- missing `primary_language`
- empty project arrays
- non-existent showcase IDs
- invalid phone numbers or empty names in forms

### 6.9 Storage Assertions
Some tests verify correct frontend use of `localStorage` and `sessionStorage`. This is important for preserving analysis task IDs, tokens, selected analysis type, and other temporary UI state.

Examples include:
- storing `analysisType`
- reading fallback task IDs from session storage
- removing auth tokens after account deletion

### 6.10 Pending-Promise Loading State Testing
Some tests use promises that never resolve in order to freeze a component in its loading state. This makes it possible to assert loading indicators and disabled buttons independently from success or failure transitions.

---

## 7. Conclusion

The frontend test suite provides broad coverage of the capstone system’s main user-facing features. Across 10 test files and 181 tests, it verifies critical workflows including authentication handling, upload and analysis progression, project viewing, showcase curation, resume generation, settings management, portfolio access, and crash recovery.

By combining rendering checks, interaction testing, async state verification, mocked API isolation, router and auth mocking, and edge-case validation, the frontend tests help ensure that the application behaves consistently and safely under both normal and failure conditions. This provides confidence that the frontend system works as expected for users interacting with the application.
