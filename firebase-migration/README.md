# Firebase migration — work in progress, NOT yet live

This branch (`firebase-migration`) holds a rebuilt version of the Content Hub dashboard
that replaces per-browser `localStorage` with a shared Firebase backend, so anyone with
a `@mediashock.com.sg` Google account can edit it and see everyone else's changes live.

**This is not deployed.** The live site (`index.html` on `master`) is still the original
localStorage-only version. Nothing here goes live until it's manually finished and merged.

## What's done and tested

Built and verified against a local Firebase Emulator Suite (fully offline, no real
project needed for this part):

- Google Sign-In gate, restricted to `@mediashock.com.sg` accounts
- Restriction enforced twice: once in the UI, and independently confirmed at the
  database level via Firestore Security Rules (a non-mediashock account gets a real
  `permission-denied`, not just a UI block)
- Live sync verified across two independent signed-in sessions: calendar posts, planner
  ideas + feedback, and content buckets all propagate to other open sessions without a
  refresh
- Post images upload to Firebase Storage (not embedded as base64) — avoids the real risk
  of image-heavy posts blowing past Firestore's 1MiB per-document limit

## Data model

- `posts` collection — one doc per calendar post, doc ID = post ID
- `buckets` collection — one doc per content bucket, doc ID = bucket key, has an `order` field
- `ideas` collection — one doc per planner idea, doc ID = idea ID, `feedback` is an array field on the doc
- `analytics/current` — single doc holding the shared analytics data (days/topPosts/demographics/follower count).
  Date-range and granularity view preferences stay in each browser's `localStorage`, not Firestore,
  so one person changing their view doesn't change what everyone else sees.

## What's left to ship this for real

1. Create the real Firebase project (Firestore + Authentication with Google provider + Storage,
   all in production mode) — see the setup steps already given in chat, or ask Claude to recap them.
2. Register a Web App in that project and get its `firebaseConfig` object.
3. In `content-hub-firebase.html`, find the block that starts with `var firebaseConfig = {` (search
   for `REPLACE_ME`) and paste in the real values.
4. Update `.firebaserc` in this folder to the real project ID (currently `demo-mediashock-hub`,
   which only exists for local emulator testing).
5. Publish `firestore.rules` and `storage.rules` (copy-paste into the Firebase Console's Rules tabs,
   or `firebase deploy --only firestore:rules,storage` if the Firebase CLI is installed).
6. Add the real GitHub Pages domain to Authentication → Settings → Authorized domains.
7. Wrap `content-hub-firebase.html` with the DOCTYPE/head/body structure (same transformation
   `sync_from_scratchpad.py` in the repo root does for the localStorage version — this file wasn't
   run through it yet since the config isn't real), copy it over `index.html` on `master`, and push.

## Local testing setup (for reference, not needed for production)

Local testing used a portable JRE + `firebase-tools` installed ad hoc in a scratch folder (not part of
this repo) to run `firebase emulators:start --project demo-mediashock-hub`, plus a plain
`python -m http.server` to serve the file over `http://localhost` (Firebase Auth's popup sign-in flow
needs a real http(s) origin, not `file://`). None of that tooling is required for the real deployment —
Firebase Hosting/GitHub Pages + a real project is all that's needed once configured.
