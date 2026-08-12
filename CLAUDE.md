# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> Patterns shared across every Mediashock internal tool (notifications, theme toggle, icons,
> auth, Firestore rules gotchas) live in `CLAUDE.md` in the parent `Claude Projects/` folder —
> check there before building something this project's own architecture below doesn't cover.

## What this is

MediaShock APAC's LinkedIn Content Hub — a shared content calendar, planner (kanban for post
ideas), and analytics dashboard. Single client-side HTML file, no build step, backed by Firebase
(Firestore + Google Auth) for live multi-user editing.

Live at https://deane-ms.github.io/MS-linkedin-hub/ (GitHub Pages).

## Critical: canonical source vs. generated file

- **`content-hub-firebase.html` is the canonical source. Always edit this file.**
- **`index.html` is generated — never hand-edit it, never treat a diff in it as the real change.**
  It's `content-hub-firebase.html` wrapped with the DOCTYPE/head/body structure GitHub Pages needs
  (the source file itself starts at a bare `<title>`).
- Regenerate after any edit:
  ```
  python sync_from_scratchpad.py content-hub-firebase.html
  ```
  This also stamps a fresh UTC build version into both `index.html` (`CURRENT_BUILD_VERSION`) and
  `version.txt`, which the deployed page polls to auto-reload clients onto new deploys (never mid-modal
  — see "Live update" in DESIGN.md).
- `<head>`-level additions (meta tags, preload hints, the manifest/favicon links) go in
  `sync_from_scratchpad.py`'s `HEAD_OPEN` template, not in `content-hub-firebase.html` — that file
  has no `<head>` at all.

## Shipping a change

Use the `/ship-content-hub` slash command (`.claude/commands/ship-content-hub.md`) — it drives the
full release loop: sync → `node --check` syntax verification → QA against a real Firebase emulator
via the `content-hub-qa` subagent (`.claude/agents/content-hub-qa.md`) → update `DESIGN.md` if the
change introduced a non-obvious pattern → stage changed files by name. It never commits/pushes
without asking first — that's a standing rule for this project, not a per-change judgment call.

For manual local testing instead of the full flow:
```
firebase emulators:start --project demo-mediashock-hub
python -m http.server 8765   # serve over http:// — Firebase Auth popup needs a real origin, not file://
```
The app auto-detects `localhost`/`127.0.0.1` and points itself at the emulators instead of prod —
no config changes needed.

## Architecture

- **Firestore collections**: `posts`, `buckets`, `ideas`, `notifications`, `suggestions` (one doc
  per item), plus single documents `analytics/current` and `goals/<metric>` (one goal doc per
  metric, capped at 3). Everything reads live via `onSnapshot`. Access control is one blanket rule
  in `firestore.rules` (`match /{document=**} { allow read, write: if isMediashock(); }`,
  `@mediashock.com.sg` only) covering every collection — unlike the sibling Team Project Manager
  app, a brand-new collection here needs no separate rules deploy. `notifications` is queried with
  `where("recipient", "==", ...)` only (sorted client-side) to avoid needing a composite index.
- **Notifications**: `notifyRecipients` writes a `notifications` doc per recipient.
  `notifyWithMentions` (used by both the feedback-add and feedback-reply handlers on Posts and
  Ideas) wraps it to merge two recipient sets into one notification each: anyone `@Name`-mentioned
  in the text (matched via `parseMentions` against `getKnownNames()` — every name that's ever
  appeared as a post/idea Owner, since there's no fixed team roster) gets type `"mention"`, and
  everyone else in the primary recipient list (the item's Owners for a new feedback item, or the
  original author for a reply) gets `"feedback"`/`"feedback_reply"`. `wireMentionAutocomplete`
  drives the `@`-triggered suggestion menu on both feedback textareas (mirrors Flowboard's
  task-comment mention menu). Assigning/tagging is feedback-only for now — the checklist/assignee
  UI in the Post/Idea modals is dead code (`createTaskListInput` is defined but never wired to any
  DOM elements — see the "Tasks UI is removed for now" comments near `currentPostTasks`/
  `currentIdeaTasks`), so there's no live per-task assignment to notify on.
  - **Desktop popups**: an opt-in toggle in the user menu (`desktopNotifToggleBtn`, `localStorage`
    key `mscontenthub_desktop_notif`) fires a native `Notification` from the `notifications`
    `onSnapshot` listener in `startListeners` for anything added *after* the listener's first
    snapshot (`notifListenerReady` flips true once that first snapshot resolves). Deliberately not
    a timestamp comparison: an earlier version compared each notification's client-generated `at`
    field against this tab's own `Date.now()` at attach time, which silently ate popups whenever
    the notifying user's and the recipient's machine clocks disagreed (the in-app bell has no such
    check, so it kept working — only desktop popups went quiet). Tab-open-somewhere only — no
    service-worker push, no server. Requires the browser's Notification permission to be granted;
    `notifyRecipients` never notifies the person who triggered it, so testing needs a second
    account/tab, not self-feedback/self-mention.
- **Images** are pasted URLs, not uploads — no Firebase Storage (would require the paid Blaze plan)
  and no base64-on-document (hits Firestore's 1MiB limit and looked pixelated). A Drive folder link
  pasted into the same Images field is auto-detected and rendered as a distinct folder chip. Image
  thumbnails are wrapped in a link so they open full-size in a new tab; a thumbnail/preview whose
  URL 404s gets a `.broken`/`.broken-single` placeholder instead of the browser's native broken-
  image icon (see "Icons" in DESIGN.md — this placeholder is drawn with the same masked-SVG
  convention as every other icon, not an emoji).
- **Four tabs**: Calendar (post scheduling by content bucket — shows a trailing-4-week posting
  cadence badge), Content Planner (kanban: New Idea → In Review → Needs Changes → Approved, sending
  an approved idea into the Calendar), Analytics (date-range/granularity-aware performance view —
  opens with sample data until real exported data is imported), Suggestions (comment/reply feature
  board, same embedded-array reply model as Post/Idea feedback). A notification bell (top-right of
  the topbar) surfaces new feedback/replies/suggestions per-user.
  - **Analytics import** (`#importAnalyticsBackdrop`) is JSON-only — a Python script
    (`agent/import_linkedin_xls.py`/`export_analytics.py`, outside this HTML file) converts the
    raw LinkedIn XLS export first; the browser side just parses/validates/writes whatever JSON it's
    given. The file input sits in a `.file-drop-zone` that also accepts a dragged-and-dropped file
    (`loadAnalyticsFileIntoTextarea`, shared by both the `change` handler and the drop handler) —
    this was the first real OS-file drag-and-drop in the app; every other drag-and-drop here moves
    an existing DOM element (image reorder, kanban cards), not a file, so there was no precedent to
    extend. A `window`-level `dragover`/`drop` `preventDefault()` guard stops a file dropped just
    outside the zone from triggering the browser's default "navigate to this file" behavior.
    Numeric `DAY_FIELDS` are coerced with `Number()` (invalid/missing values default to `0`, each
    counted separately) rather than passed through as-is, so a stray non-numeric cell doesn't
    silently corrupt a later sum in the analytics view — the import summary reports how many
    values needed defaulting instead of pretending the file was clean. There is no toast system in
    this app; import feedback is the single inline `#importAnalyticsError` paragraph (red for
    errors, green for success), same as it's always been.
  - **Stale-data reminder**: `updateStaleAnalyticsBanner`, called from `renderAnalytics()`, shows a
    dismissible banner (reusing `.onboarding-banner`'s visual recipe) when the newest day in
    `state.days` is more than `STALE_ANALYTICS_DAYS` (14) old — never for sample data. Unlike the
    onboarding banner's dismiss-forever flag, dismissal here is keyed to the specific stale date
    (`mscontenthub_stale_analytics_dismissed` in `localStorage`), so importing fresher data
    automatically re-arms it the next time *that* data goes stale, rather than staying silently
    dismissed forever after the first click.
- **Mobile (≤720px)**: view-only for Post/Idea editing (creation entry points hidden, existing
  items open read-only with a "View only" badge); everything else stays fully functional, including
  adding (not removing) idea/post feedback comments. Month/week grid becomes an agenda list; the
  Top Posts table collapses to stacked cards.
- **PWA-installable**: `manifest.json`/`sw.js`/icons are hand-maintained, separate from the sync
  pipeline (not derived from `content-hub-firebase.html`). `sw.js` deliberately does no caching.

## Where to look for conventions

**`DESIGN.md` is the authoritative, actively-maintained reference** for this app's established
patterns — color tokens, spacing rhythm, icon conventions, reusable input widgets (chip input,
checklist, emoji picker, avatar coloring, status-picker dropdown), and a long list of specific
gotchas with their history (why they exist, what bug they fixed). Read it before adding new
fields/panels/icons, and read the relevant section before touching an area it documents — don't
duplicate that content here. `/ship-content-hub` updates it automatically when a change introduces
something non-obvious.

## Testing

No unit tests. QA is a real Firebase emulator + Playwright run against the live app, done via the
`content-hub-qa` subagent — see that agent file for emulator setup (Java 21 + Playwright cached
under `.qa-tools/`, gitignored), sign-in flow, and this app's specific selector-scoping gotchas
(near-duplicate Post/Idea modal structures). Don't hand-write a test harness from scratch; delegate
to that agent, briefed with specifics of what changed.

## Automated UI/UX optimization reviews

A scheduled cloud routine (`https://claude.ai/code/routines/trig_01JanYSJWSBVFMmJp9TAekmt`, cron
`16 */5 * * *`, ~5 runs/day) reviews this repo unattended and opens a GitHub issue titled
"UI/UX Optimization Report — <date>" when it finds something concrete — categorized 🔴 Critical /
🟡 Refinement / 🔵 Feature Optimization, citing specific file/function. It skips creating a new
issue if one from the last 24h already exists, and opens nothing at all if it found nothing real.

**Push-notification fallback.** Every run of the sibling Flowboard repo's identical routine found
real things but silently failed to file them — `403 Resource not accessible by integration` on
every issue-creation attempt — worth knowing if this repo's issue tracker looks suspiciously empty
too. The prompt now tries issue creation first and, if it fails for any reason, pushes a mobile
notification with the same categorized report instead (prefixed with the error). **The root cause
isn't fixed by this** — it's a GitHub App permissions gap (`issues:write` missing on the
integration), fixable only from GitHub's UI. See "Scheduled cloud routines" in the parent
`Claude Projects/CLAUDE.md` for the exact fix — same gap, same GitHub App installation, for both
this repo's routine and Flowboard's.

**This is report-only by design, not the original "propose then wait for a reply" spec it was
adapted from.** A cron-fired cloud session runs once, unattended, and finishes — it cannot pause
mid-run and wait days for a human to reply "1, 3, 4" the way an interactive chat can. So the
automated run's tools are deliberately restricted to `Bash`/`Read`/`Grep`/`Glob` (no `Edit`/
`Write`), and its prompt forbids touching code entirely. **Implementing anything from a report is
always a separate, manually-triggered step**: open the GitHub issue, then ask Claude in a normal
interactive session (e.g. "implement items 1 and 3 from issue #N") — that request, in a real
conversation, is the actual approval gate. Manage/disable the schedule at
`https://claude.ai/code/routines`.
