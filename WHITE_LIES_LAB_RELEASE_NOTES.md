# White Lies Lab Release Notes

Public page:

https://b13102033-svg.github.io/b132-public-handouts/ethan-white-lies-writing-speaking-context-lab.html

Latest validated public build in this maintenance pass:

`b34a084`

## What Changed

- Fixed route anchors so Evidence Notebook, Evidence Library, Answer Models, and Draft Builder no longer point to the wrong sections.
- Added a Tone Transformer for turning blunt truth into soft, balanced, or firm feedback.
- Added source reader status chips: focused page slice vs readable source fragment, plus full-source availability.
- Made source reader focus mode clearer and persistent.
- Added a Source-to-answer bridge with source links and Add to draft buttons.
- Added top navigation jumps: Sources, Bridge, Models, Draft.
- Added an answer readiness meter for saved sources, draft length, contrast, and core concept.
- Added a speaking coach timer: 30s prep, 60s answer, 90s challenge.
- Added draft scaffold buttons: Opening, Concession, Source use, Conclusion.
- Added Copy draft.
- Added Evidence Library source search and Reset sources.
- Added Back to top for the long lesson page.
- Compact mobile navigation into a horizontal scroller so the first screen is not consumed by nav buttons.
- Polished the public handouts index and made the White Lies Lab the featured latest page.
- Added a regression validator and documented the QA workflow.

## Public QA Result

Validator:

`tools/validate_white_lies_page.cjs`

Public target tested:

`https://b13102033-svg.github.io/b132-public-handouts/ethan-white-lies-writing-speaking-context-lab.html?qa=public-b34a084`

Result:

`ok: true`

Checks passed:

- Required route anchors exist exactly once.
- Writing filter shows 7 writing-move sources.
- Source search for `gossip` returns 2 sources.
- No-match search gives recovery guidance.
- Reset sources restores 20 source windows.
- Tone Transformer works.
- Source-to-answer bridge inserts draft text.
- Copy draft reports success.
- Readiness meter detects contrast and core concept.
- Speaking timer starts and stops.
- Reader focus mode works.
- Back to top returns to the page top.
- Mobile viewport has no horizontal overflow and a usable source reader.

## Maintenance Rule

Before reporting that this page is ready after future changes, run the validator against the public URL whenever possible. The user has repeatedly asked for public, clickable, student-facing behavior rather than local-only proof.
