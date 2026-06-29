# White Lies Lab QA Tools

This folder contains regression checks for the public student-facing page:

`ethan-white-lies-writing-speaking-context-lab.html`

The validator is intentionally interaction-focused. It does not only check that files exist; it opens the page in Chrome and tests the behaviors the student actually uses.

## Validator

Script:

`tools/validate_white_lies_page.cjs`

It checks:

- Required route anchors exist exactly once: Evidence Library, Source-to-answer bridge, Answer models, Draft builder.
- Evidence Library filter works and shows 7 writing-move sources.
- Source search works for `gossip`.
- No-match source search gives recovery guidance.
- Tone Transformer produces firm feedback from a blunt sentence.
- Source-to-answer bridge can insert a sentence into the draft.
- Copy draft reports success.
- Readiness meter detects contrast and core concepts.
- Speaking timer starts and stops.
- Source reader focus mode works without horizontal overflow.
- Mobile viewport has no horizontal overflow and keeps a usable source reader.

## Local Check

From the public handouts repository root:

```bash
NODE_PATH=/Users/qyjun/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules \
/Users/qyjun/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node \
tools/validate_white_lies_page.cjs \
'http://127.0.0.1:8134/ethan-white-lies-writing-speaking-context-lab.html'
```

## Public Check

After pushing to GitHub Pages and waiting for refresh:

```bash
NODE_PATH=/Users/qyjun/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules \
/Users/qyjun/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node \
tools/validate_white_lies_page.cjs \
'https://b13102033-svg.github.io/b132-public-handouts/ethan-white-lies-writing-speaking-context-lab.html'
```

## Maintenance Rule

Before telling the user the page is ready, run the validator against the public URL whenever possible. If it fails, fix the page or the test before reporting success.
