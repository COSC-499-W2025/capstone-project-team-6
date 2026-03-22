# Mandira Samarasekara

# Aakash Tirithdas

# Mithish Ravisankar Geetha

# Harjot Sahota

## Date Ranges

March 16 - March 22

## What went well

This week was very busy, and I made several major improvements to the resume page and overall user experience of the application.

I improved the layout of the Resume page to make it easier for users to navigate and use. As part of that work, I added an inline preview section so users can now preview their generated resume before downloading it, which makes the resume generation flow much more convenient and user-friendly.

I also updated the Education section to support full CRUD functionality. Users can now save, edit, and delete their education entries, which means they no longer have to re-enter their education information every time they log in and generate a resume. This makes the feature much more practical for repeated use.

In addition, I added a Work Experience section to the Resume page. Users can now enter work experience entries that are automatically displayed in reverse chronological order, and this section also supports full CRUD functionality so users can save their work history for future resume generations.

Outside of the Resume page, I also added a logout button to the navigation bar. Previously, the logout option was only available on the dashboard, which was inconvenient for users. Moving it to the navigation bar makes logging out much easier and more accessible from anywhere in the app.

Overall, this week went well because I contributed multiple meaningful frontend improvements that made the application more functional, persistent, and user-friendly.

## What didn’t go well

One thing that did not go well this week was that two of my PRs for the Resume page were very large and closely connected, with a lot of new implementation and changes across the page.

My first PR had a bug where the resume PDF preview would not display correctly, even though the follow-up PR, which depended on the first one, had the preview working properly. After debugging, I realized that I had fixed the issue in the second PR but forgot to apply the same fix back to the first PR. This caused extra confusion and made the review process harder.

This taught me that large connected PRs can be difficult to manage, especially when fixes are made in one branch but not carried back into the earlier dependent branch. It was a good lesson in being more careful when working across stacked or related PRs.

## PRs initiated

Work experience section  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/462

Added logout button to navigation bar  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/458

Improve Resume page layout + add persistent education entries + inline PDF preview  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/460

## PRs reviewed

Job description Matching  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/467

made changes to the database to fix the delete account bug  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/464

## Plans for next week

Next week I plan to continue contributing to the Resume page and make the layout even more user-friendly. There are still some bugs that need to be fixed, such as there being no way to remove the resume preview from the screen after generating it, and a section of words being cut off in the generated resume output. I want to address these issues so the Resume page feels more polished and complete for users.


# Mohamed Sakr

# Ansh Rastogi

