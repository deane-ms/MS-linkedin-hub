---
description: Ship a change to the MediaShock LinkedIn Content Hub -- sync from the canonical source, verify syntax, QA it against a real Firebase emulator via the content-hub-qa agent, update DESIGN.md if needed, and stage everything for review. Never pushes without explicit confirmation.
argument-hint: [brief description of what changed, e.g. "added a delete-feedback button"]
allowed-tools: Bash, PowerShell, Read, Edit, Write, Grep, Glob, Agent
---

You are running the release workflow for the MediaShock APAC LinkedIn Content Hub at
`C:\Users\user\Desktop\mediashock-linkedin-hub`. The canonical source is
`content-hub-firebase.html`; `index.html` is a generated artifact (GitHub Pages needs a real
`<head>`/`<body>`, which the canonical source deliberately doesn't have) — never hand-edit
`index.html` directly, and never treat a diff in it as the real change to review.

What changed in this run, if given: $ARGUMENTS

## Step 0 — Orient

- `git status` and `git diff -- content-hub-firebase.html` in that repo to see what's actually
  changed. If nothing changed in `content-hub-firebase.html` (or `sync_from_scratchpad.py`,
  `manifest.json`, `sw.js`, or the icon assets), stop and say so rather than inventing work.

## Step 1 — Sync

From the repo directory:
```
python sync_from_scratchpad.py content-hub-firebase.html
```
This also stamps a fresh build version into `index.html` and `version.txt` (see the "Live
update" section of `DESIGN.md`) — that's expected on every run, not a bug.

## Step 2 — Syntax check

Extract the `<script type="module">` body from `content-hub-firebase.html` to a scratch `.mjs`
file and run `node --check` on it (`node --check` needs a real file, not stdin, and the extension
matters — `.mjs` so `import`/top-level syntax doesn't error). Fix any reported syntax error before
moving on; don't proceed to QA on a file that doesn't parse.

## Step 3 — QA against a real emulator

Delegate to the `content-hub-qa` agent (`~/.claude/agents/content-hub-qa.md`) rather than
reimplementing the emulator/Playwright setup here. Brief it with concrete specifics: what changed,
which selectors/elements are involved, what the expected before/after behavior is, and whether
mobile behavior is relevant. A vague "test my changes" prompt gets a shallow pass — give it the
same level of detail you'd want if you were about to hand this off to a QA engineer who's never
seen the diff.

If the agent reports a failure, fix the underlying issue in `content-hub-firebase.html` (never in
`index.html`), then repeat from Step 1.

## Step 4 — Documentation

Check whether this change introduced a pattern, gotcha, or deliberate exception that isn't obvious
from reading the code alone (a new CSS scoping rule, a derived/computed value that looks like it
should come from stored data but doesn't, a platform-specific branch, an intentional exception to
an existing rule). If so, add a bullet to the relevant section of `DESIGN.md` — follow its existing
style: lead with what the rule is, then *why*, in the voice of someone leaving a note for the next
person touching this code. Skip it if the change is purely cosmetic/self-evident.

## Step 5 — Clean up and stage

Confirm no stray `firestore-debug.log`/`ui-debug.log` got left in the repo root (the QA agent
should have handled this, but verify). Run `git status` and stage the actual changed files by name
— never `git add -A`/`.` — matching whatever `git status` actually shows changed.

## Step 6 — Report and stop

Summarize what changed and what QA confirmed, in plain terms a non-engineer can follow (this
project's owner is not a developer). **Do not commit or push.** Ask whether to commit and push,
the same way every change in this project has shipped so far — this is a standing rule, not a
per-change judgment call. If told to proceed, write the commit message in this repo's established
style (concise summary line, a body explaining *why* not just *what*, ending with
`Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`), then `git push origin master`.
