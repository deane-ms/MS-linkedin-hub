# Design conventions

Reference for the patterns already established in `content-hub-firebase.html`. Follow these when adding new fields, panels, or icons so the app keeps reading as one system rather than accreting one-off styles. This is documentation only — it doesn't run; edit the source file and regenerate `index.html` as usual.

## Colors

All color is driven by CSS custom properties on `:root`, with dark as the default and explicit overrides for `:root[data-theme="dark"]` / `:root[data-theme="light"]` (set by the manual theme toggle, persisted to localStorage). Never hardcode a hex color in a new rule — use the existing tokens:

- `--brand`, `--brand-soft`, `--brand-gradient-h` — MediaShock orange, used for active states, primary buttons, links, focus rings.
- `--surface`, `--surface-alt` — card/modal background vs. sunken field background.
- `--border` — all hairlines and input borders.
- `--text`, `--text-soft`, `--text-faint` — primary copy, field labels, secondary/meta text (in that descending order of emphasis).
- `--danger`, `--danger-soft`, `--good`, `--bad` — status colors (delete actions, goal pacing, etc.)

## Spacing rhythm

Three tiers, used consistently everywhere a label sits above a field or a group of fields sits above another group:

- **Label → field: `0.35rem`** (`.field-col`, and the gap baked into `#postForm label`/`#ideaForm label`). Never let a label sit as a bare sibling of its field — always wrap it in `.field-col` so it picks up this tight gap instead of a section gap.
- **Within a section: `0.9rem`** (`.form-section`'s own gap) — spacing between fields that belong to the same logical group.
- **Between sections: divider + `1.3rem`** (`.form-section + .form-section`, `.form-section + .modal-actions`) — a hairline `border-top` plus `1.1rem` padding-top, so unrelated groups of fields read as visually distinct blocks instead of one long stack.

## Form sections

The Post and Idea modals are each broken into `.form-section` blocks (currently: Details / Owners / Content for Post; Details / Brief / Stage & Feedback for Idea — the Tasks sections were removed, see below). Sections are separated by whitespace and a hairline divider only (`.form-section + .form-section`) — **no heading text on the section itself.** An earlier version added an uppercase eyebrow label per section, but that was redundant with the fields' own labels and read as clutter; it was removed. When adding a new field, put it in the section it semantically belongs to (or give it its own `.form-section` if none fit), but every field/group still needs its *own* `<label>` — don't rely on the section boundary alone to convey what a block is for. (Fixed one regression from the original section-label removal: Idea's Tasks block had no field label of its own, only the section heading — it now has `<label>Tasks</label>` matching Post's.)

## Icons

All icon-only buttons are inline SVG, not emoji or icon fonts: `stroke="currentColor"`, `fill="none"`, `stroke-width="1.8"` (bump to ~`2.6` only for small badge-style icons that need to read at a glance), `viewBox="0 0 24 24"`, rendered at `16x16`. Wrap them in `.icon-btn` (2.1rem square, 1px border, 8px radius, `--surface` background) for a clickable icon, or a variant like `.emoji-inline-btn` when it needs to sit inside/overlay another field.

## Reusable input patterns

- **Chips-with-add-row**: owners use `createOwnerChipInput(inputEl, chipsEl, onChange)` — a small factory returning `{add, set, get}`. Reuse this factory (don't hand-roll a new chip list) for anything that's "add a short label, show it as a removable pill."
- **Checklist-with-assignee**: tasks use `createTaskListInput(listEl, inputEl, assigneeSelectEl, getOwners)` similarly — checkbox + text + avatar + remove, assignee dropdown synced live to the item's current owners.
- **Emoji picker**: `createEmojiPicker(toggleBtn, pickerEl, tabsEl, gridEl, textarea, onInsert)` — instantiate one per textarea that should support inserting an emoji (Post Copy, Idea/Brief). The trigger button lives inside a `.textarea-emoji-wrap` (position: relative wrapper around the textarea), overlaid bottom-right via `.emoji-inline-btn`, so it reads as part of the text field rather than a separate toolbar action.
- **Avatars**: `avatarHtml(name, sizeClass)` — always derive color and initials from `avatarColorFor(name)` / `getInitials(name)`, both hashing the trimmed/lowercased name, so the same person renders identically everywhere in the app. Never assign an avatar color ad hoc.
- **Image links**: both Post and Idea images are entered as pasted URLs (`.image-link-row` input + Add button, `.image-link-grid` of `.image-thumb` tiles with a `.image-remove` button), not uploaded files — deliberately. Firestore documents have a hard 1MiB limit, and embedding uploaded images as base64 forced heavy compression that was visibly pixelated; a URL is a few bytes regardless of the source image's real quality. A thumb gets `.broken` (via the `<img>`'s `error` event) when its URL doesn't load — note `.image-thumb.broken::after`'s decorative placeholder icon must keep `pointer-events: none`, or it silently eats clicks meant for the remove button underneath it. Thumbs are `draggable="true"` (with `draggable="false"` on the inner `<img>`/`<a>` so the browser doesn't hijack the drag into an image-drag instead) — `dragstart`/`dragover`/`drop` on `.image-thumb` reorder `currentImages` via `.splice()`. (Idea's version of this predates Post's and still uses its own `.idea-image-*` class names with identical rules, and has no drag-reorder — a future cleanup could unify/extend them, but they aren't currently unified.)
- **Post images list doubles as the asset-folder handoff**: there's deliberately no separate "Asset Folder" field anymore (one existed briefly and was merged back in per feedback that two entry points was confusing). A Google Drive link pasted into the *same* Images input is detected by `isDriveFolderLink()` (matches `drive.google.com`) and rendered as a distinct folder-icon chip (`.image-thumb.folder-link`, opens in a new tab) instead of a photo thumbnail — excluded from the LinkedIn preview (`getPreviewImages()` filters it out) and from the photo-count badge, but still picked up by `findAssetFolderUrl()` to drive the calendar card's quick-open folder icon. `post.assetFolderUrl` (the old dedicated field) is kept only as a fallback inside `findAssetFolderUrl()` for any posts saved while that field existed — there's no editor for it anymore, don't resurrect one; new Drive links go in Images.
- **Status select, color-coded only**: `#f-status` keeps the normal select shape/sizing (tried a full pill-badge redesign here first -- rounded, bold, uppercase -- and it was reverted as unwanted; don't redo that). It just gets a `status-draft`/`status-approved`/`status-scheduled` class for a tinted background/text/border matching the calendar's status-pill colors, kept in sync via `updateStatusSelectStyle()` on `change` and whenever the value is set programmatically (modal open/reset).

## Tasks (removed from the UI, kept in the data)

The assignable Tasks checklist (on both Post and Idea) was removed from the form for now, per direct feedback that it added clutter. The `tasks` field is still read on load and passed straight back through on save (`currentPostTasks` / `currentIdeaTasks` — plain variables, not editable) specifically so existing saved tasks aren't lost even though there's no editor for them. The `createTaskListInput()` factory is still defined but unused; re-adding the UI later is mostly restoring the HTML block removed from both forms and re-wiring those two variables back to the controller.

## Schema changes

Any new field on `posts`/`ideas` must be additive and read with a fallback (`post.newField || defaultValue`) — existing documents without it should degrade gracefully, never break. See `normalizedGoal()` for the pattern used when a field's *shape* changes, not just its presence.
