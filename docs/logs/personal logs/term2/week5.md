# Mandira Samarasekara

# Aakash Tirithdas

# Mithish Ravisankar Geetha

# Ansh Rastogi

# **Harjot Sahota**

## **Date ranges**

January 26th – February 8th

---
## **What went well**

- These 2 weeks I completed two major features: the **Settings consent update UI** and the **Delete All Projects** functionality. Both included full frontend work, backend updates, and database tests.

- In **PR #348**, I added the consent toggle on the Settings page, including loading the user’s consent status, a confirmation modal, and clear success/error feedback. The UI now matches the app’s style, and all related frontend tests are passing.

- In **PR #345**, I added a bulk project deletion flow with a new `DELETE /api/projects` endpoint, full user-scoped backend logic, UI updates, and database tests to verify that only the authenticated user’s projects are removed.

- I also merged **PR #338**, which added per-project deletion with improved Projects page UI and full backend authorization checks. Both manual and automated tests confirmed the end-to-end flow works reliably.

- All PRs passed CI, and manual checks ensured UI updates, confirmation flows, and DB state behaved correctly after deletion and after logout/login. Overall, I shipped multiple stable features and strengthened my understanding of frontend–backend integration and testing.


---
## **What didn’t go well**

- Nothing major went wrong this week, but I did discover an important bug in our system: we were using two different unique identifiers for projects, which caused portfolio_items not to delete when the associated project was deleted. This issue wasn’t obvious at first and took time to trace through the database and backend logic.

- The bug is now fully fixed, but identifying it highlighted how critical consistent IDs are for future features and data integrity. While it didn’t block my work, it added extra debugging time and reminded me to double-check identifier flow across the stack.

---
## **PRs initiated**

- **Add update consent feature in Settings + tests**  
  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/348

- **Add delete all projects functionality (UI + backend + DB tests)**  
  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/345

- **Add per-project delete feature with UI updates and backend cleanup**  
  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/338

---
## **PRs reviewed**

- **Markdown resume preview and resume information bug fixes**  
  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/346

- **Role prediction curation (CLI + database + tests)**  
  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/342

- **Interactive resume generator**  
  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/336

- **Frontend Resume Generator**  
  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/334

- **Role prediction tests**  
  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/330

---

## **Plans for next week**


# Mohamed Sakr

