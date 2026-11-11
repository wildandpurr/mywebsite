# Outstanding items

Running list of known, deliberately-deferred items. Nothing here is urgent unless
noted.

## 1. Meta description wording: "creative moments" vs "creative discoveries"

**Status: paused, awaiting a decision. No changes made.**

### Origin of the discrepancy (traced 2026-11-11)

- The copy has read **"creative moments"** since the **very first commit**
  (`121dd3b`, "Add files via upload", 2026-10-28, by wildandpurr). It is the
  authored Framer text, not something introduced later.
- **"creative discoveries" never appears anywhere in git history.** It was never
  in the repo.
- The wording difference came up in conversation on **2026-11-11 ~10:37**, when
  the user shared a screenshot of **LinkedIn's link preview** of the site and
  said: *"It should say creative discoveries, not moments."* So the source of
  "discoveries" was the user's own intent at that moment — not a prior edit, a
  merge, or a Framer re-export. Nothing was changed at the time; the request was
  paused ("Stop. Leave it").

### Where the string lives (6 occurrences, 4 files)

Changing it is not a one-line edit. The string is duplicated:

| File | Location |
| --- | --- |
| `index.html` | `meta name="description"` |
| `index.html` | `meta property="og:description"` |
| `index.html` | `meta name="twitter:description"` |
| `assets/animate/shared-lib.<hash>.mjs` | page metadata function `So()` |
| `assets/meta/meta-d824b18e.json` | `"/" -> description` |
| `assets/meta/meta-da3c89c2.json` | `"/" -> description` |

Note: the description is **metadata**, not visible page text, so it is **not**
covered by `tools/apply_links.py` (which handles visible copy). It must be edited
in all six places, and the bundle renamed to a fresh content hash with every
reference in `index.html` updated — or the change will revert/desync.

### To resolve

Confirm which wording is wanted, then apply to all six locations (or extend
`tools/apply_links.py` to own metadata too) and verify in the rendered DOM that
the description does not revert after hydration.

## 2. Analytics and tracking

**Status: deferred by the user (2026-11-11).**

Decision: no tracking and no privacy policy for now. To be revisited when a
newsletter / email-capture is set up. A draft plan exists on branch
`plan/analytics-and-consent` (`docs/analytics-consent-plan.md`) and can be picked
up then. The live site currently has no analytics installed.

## 3. Google Search Console: sitemap "Couldn't fetch"

**Status: awaiting the user's re-check in GSC.**

Investigated 2026-11-11. The live sitemap is healthy on every axis: HTTP 200,
`application/xml`, valid XML, no redirects, referenced in `robots.txt`, no
`X-Robots-Tag`, accessible to Googlebot. `www` 301-redirects to the apex;
`sitemap_index.xml` does not exist (404) but was never submitted. Most likely
causes are GSC-side: timing (the sitemap only went live 2026-11-11 09:46) or the
wrong URL submitted. Recommended: delete and re-add `sitemap.xml` under the
`https://wildandpurr.com` property, then wait 24–48h. No site change needed.

## 4. `fb:app_id` warning

**Status: no action (advisory given).**

Facebook's debugger notes a missing `fb:app_id`. This is a warning, not an error,
and does not affect link previews. Implementing it only matters if we later need
Facebook Analytics or the Facebook app tooling. Recommend leaving it.

## 5. Mobile responsiveness

**Status: option (a) shipped; option (b) pending.**

Option (a) (device-width viewport + guard) is live. Option (b) — a proper Framer
breakpoint layout — is described in `docs/responsive-option-b.md`, including the
re-apply checklist needed because a Framer re-export overwrites `index.html` and
`assets/`.
