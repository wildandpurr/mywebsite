# AGENTS.md — Wild and Purr website

## What this repo is
A **static Framer export** published with GitHub Pages (`CNAME` -> wildandpurr.com).
There is no build step. The deployed files *are* the source.

## Layout
- `index.html` — server-rendered DOM (the Framer export's SSR output) plus all CSS.
- `assets/animate/*.mjs` — the React hydration bundles. `shared-lib.<hash>.mjs` holds
  the page component tree; `script_main.<hash>.mjs` boots it.
- `assets/meta/meta-*.json` — the Framer search index (referenced from `<meta>` tags).
- `assets/fonts/`, `assets/images/` — hashed assets.

## Critical gotchas
1. **Two copies of every string.** `index.html` and `assets/animate/shared-lib.<hash>.mjs`
   both contain the page copy and image `src` values. If you edit only one, React
   hydration overwrites the DOM shortly after load: the update flashes and then reverts.
   Always keep SSR and bundle byte-identical for the affected region.
2. **React hydration deletes foreign DOM inside the Framer root.** Any element added
   inside `<div data-framer-root>` that React does not know about is removed on hydration.
   Markup added *outside* the root survives. Prefer editing the bundle + SSR together
   over injecting extra markup.
3. **Icons are CSS masks.** Framer renders TikTok/YouTube/Ko-fi glyphs as
   `mask-image: url('data:image/svg+xml,...')`, and the Ko-fi heart historically used
   `<use href="#79158532">` pointing at the `#svg-templates` sprite. A `mask-image`
   whose SVG has no opaque pixels makes the element a solid coloured square; keep the
   data-URI self-contained rather than depending on the sprite.
4. **Renaming a chunk busts the cache.** Framer filenames are content-hashed. When the
   bundle changes, rename it and update every reference in `index.html`
   (script `src`, `modulepreload`, and the meta search-index paths) so browsers do not
   serve the old file.
5. `sw.js` and `service-worker.js` only call `self.registration.unregister()` — they do
   not cache anything.

## Links section
The "Find us elsewhere" block lives in `index.html` and in the bundle under the
`framer-1gey6qo` container, between the intro paragraph and the "Our hashtags" block.
Banner labels are kept verbatim; section titles are not added inside the block.

## Regenerating the links block and page text
Do **not** hand-edit the links block or any page copy in `index.html` or the bundle.
Edit `LINKS` (banners), `HASHTAGS` (the hashtags line) or `TEXT` (all other page copy)
in `tools/apply_links.py` and run it:

    python3 tools/apply_links.py

It is the single source of truth. It rewrites the SSR markup, the hydration bundle,
the CSS (banner colours + icon masks) and the Framer search index together, then
renames the bundle to a fresh content hash and repoints every reference. It is
idempotent — running it twice changes nothing — and it fails loudly if a re-export
moves the anchors it relies on.

`TEXT` is keyed by the `framer-XXXX` class of the wrapper element that holds each
string. That class is the join key: it appears as `class="framer-XXXX"` in
`index.html` and as ``className:`framer-XXXX` `` in the bundle, so both copies of a
string can be found and rewritten without matching on the text itself.

## Hand-editing a string by hand (no script)
If you must edit without the script, the same string exists in **three** places and
all three must be changed, or the browser shows your new text and then reverts it on
hydration:

1. `index.html` — the SSR markup (what paints first).
2. `assets/animate/shared-lib.<hash>.mjs` — inside ``children:`...` ``, immediately
   before ``className:`framer-XXXX` ``.
3. `assets/meta/meta-*.json` — both files, in the `"/" -> "p"` array (only for
   strings that appear there; headings usually do not).

Then **rename the bundle** to a new content hash and update the three references to
it in `index.html` (`script src`, `modulepreload`, meta paths) — or just use the
script, which does all of this for you.

Rule of thumb: **colours and CSS are safe to hand-edit** (they live only in
`index.html`). **Any visible text is not** — it is duplicated and will revert.

## Verifying a change
Serve the repo (`python3 -m http.server`) and confirm, in a browser, that the DOM does
not change after hydration. A `MutationObserver` on `.framer-1gey6qo` should report
`mutations=0` and identical content before and after `load`.

## Outstanding work and planning notes
See `docs/outstanding-items.md` for deferred items (meta description wording,
analytics, GSC sitemap, fb:app_id) and `docs/responsive-option-b.md` for the
Framer breakpoint plan and the re-apply checklist that any Framer re-export
requires (a re-export overwrites `index.html` and `assets/`).

The mobile viewport fix (option a) is live: `index.html` sets
`width=device-width` and pins it with a `<script data-viewport-fix>` guard,
because the Framer runtime re-applies `width=1200` on hydration.
