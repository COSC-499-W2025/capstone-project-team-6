# Mandira Samarasekara

# Aakash Tirithdas

# Mithish Ravisankar Geetha

# Harjot Sahota

## Date Ranges

March 16 - March 29
<img width="1077" height="636" alt="Screenshot 2026-03-28 at 11 59 02 AM" src="https://github.com/user-attachments/assets/223c2d75-8616-44b6-82f8-cebee975cdb0" />

## What went well

these weeks were very busy, and I made several major improvements to the resume page and overall user experience of the application.

I improved the layout of the Resume page to make it easier for users to navigate and use. As part of that work, I added an inline preview section so users can now preview their generated resume before downloading it, which makes the resume generation flow much more convenient and user-friendly.

I also made generated resumes savable, and they can now be viewed later in a stored resumes section. In that section, users can view and delete previous resume generations. This makes the feature much more user-friendly because users can keep the resumes they want instead of losing them after generation. Saving is also optional, so users can choose whether or not they want to store a generated resume.

I updated the Education section to support full CRUD functionality. Users can now save, edit, and delete their education entries, which means they no longer have to re-enter their education information every time they log in and generate a resume. This makes the feature much more practical for repeated use.

In addition, I added a Work Experience section to the Resume page. Users can now enter work experience entries that are automatically displayed in reverse chronological order, and this section also supports full CRUD functionality so users can save their work history for future resume generations.

Outside of the Resume page, I also added a logout button to the navigation bar. Previously, the logout option was only available on the dashboard, which was inconvenient for users. Moving it to the navigation bar makes logging out much easier and more accessible from anywhere in the app.

I also fixed several smaller bugs in the codebase in preparation for the final demo, including UI issues, visibility problems, and other minor fixes that helped make the application feel more polished and stable.

Another thing that went well was that our group met together for the project demo, and we all collaborated to create the demo video. That was a good team effort and helped us prepare our final presentation as a group.

Overall, this week went well because I contributed multiple meaningful frontend improvements that made the application more functional, persistent, and user-friendly, while also helping the team prepare for the final demo.

## What didn’t go well

One thing that did not go well this week was that two of my PRs for the Resume page were very large and closely connected, with a lot of new implementation and changes across the page.

My first PR had a bug where the resume PDF preview would not display correctly, even though the follow-up PR, which depended on the first one, had the preview working properly. After debugging, I realized that I had fixed the issue in the second PR but forgot to apply the same fix back to the first PR. This caused extra confusion and made the review process harder.

This taught me that large connected PRs can be difficult to manage, especially when fixes are made in one branch but not carried back into the earlier dependent branch. It was a good lesson in being more careful when working across stacked or related PRs.

## PRs initiated

Work experience section  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/462

Added logout button to navigation bar  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/458

Improve Resume page layout + add persistent education entries + inline PDF preview  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/460

frontend bug fixes https://github.com/COSC-499-W2025/capstone-project-team-6/pull/477 

Implemeted save resume generation + tests https://github.com/COSC-499-W2025/capstone-project-team-6/pull/479

## PRs reviewed

Job description Matching  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/467

made changes to the database to fix the delete account bug  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/464

Aakash/multiproject bug  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/480

Bug Fixes and Enhancements + Rebranding  https://github.com/COSC-499-W2025/capstone-project-team-6/pull/475

Job Match Page UX Improvements https://github.com/COSC-499-W2025/capstone-project-team-6/pull/473

Portfolio Private Mode and Interactive Portfolio Summary https://github.com/COSC-499-W2025/capstone-project-team-6/pull/471

## Plans for next week

Next week I plan to improve the stored resumes feature by allowing users to download resumes they have saved. Right now, users can only view their stored resumes, so adding download support would make the feature much more useful and complete.

If I have time, I also want to improve the existing feature that lets users update a resume by adding content from their saved projects. Currently, this feature is only available for markdown resumes, so I would like to add support for PDF uploads as well.

# Mohamed Sakr

# Ansh Rastogi

