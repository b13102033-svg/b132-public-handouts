# B132 Public Handouts Deployment Status

Last deployed: 2026-06-29

Repository:
https://github.com/b13102033-svg/b132-public-handouts

GitHub Pages:
https://b13102033-svg.github.io/b132-public-handouts/

Current student page:
https://b13102033-svg.github.io/b132-public-handouts/longteng-vocab-king-unit50-54-review.html

Ethan GEPT writing/speaking pages:
- https://b13102033-svg.github.io/b132-public-handouts/ethan-gept-writing-speaking.html
- https://b13102033-svg.github.io/b132-public-handouts/ethan-white-lies-writing-speaking-context-lab.html
- https://b13102033-svg.github.io/b132-public-handouts/ethan-gept-second-stage-materials.html

Status:
- GitHub Pages status: built
- HTTPS enforced: true
- Source: main branch, root path
- Current public pages are standalone HTML with no local asset dependencies.

Validation:
- Home page returned HTTP 200.
- Student review page returned HTTP 200.
- Student review page contains the Longteng Unit 50-54 title.
- Student review page contains at least 90 input fields and 90 buttons.
- Ethan GEPT pages were exported as public student versions with local B132 source links disabled rather than broken.

Update workflow:
1. Edit or replace `longteng-vocab-king-unit50-54-review.html`.
2. Commit the change.
3. Push to `origin main`.
4. GitHub Pages will rebuild from the repository root.
