# Responsive fix (option b) — logistics and re-apply checklist

Status: planning note. Option (a) is live (see below); this describes the durable
fix and everything that must be re-applied when it is done.

## Where we are

- **Option (a) — shipped.** `index.html` carries `<meta name="viewport"
  content="width=device-width, initial-scale=1">` plus a small guard script
  (`<script data-viewport-fix>`) that pins the value against the Framer runtime.
  Merged to `main` in `8069dda`; live at https://wildandpurr.com/.
- **Option (b) — this document.** Set the viewport at the source in the Framer
  project so a re-export emits a correct responsive site and the guard is no
  longer needed.

## Why the guard exists (the problem option b solves)

The exported layout is already fluid: the Framer root tracks the viewport width
from 320px up, with no horizontal overflow. The only thing that breaks phones is
the authored viewport value `width=1200`, which makes mobile browsers scale the
whole desktop layout down to about one third size (effective body text ~6px).

That value is not hand-written in the HTML. It is generated from the project's
page metadata. In the export it appears as:

- `assets/animate/shared-lib.<hash>.mjs` — `viewport:`width=1200`` inside the page
  metadata function, and `breakpoints:[{hash:`72rtr7`}]`, `framerIntrinsicWidth:1200`,
  `framerResponsiveScreen:true`.
- `index.html` — the `<meta name="viewport">` tag.

The runtime re-applies `width=1200` on hydration, which is why the static meta
alone is not enough and the guard exists. The call site is
`meta[name="viewport"].setAttribute(...)` in `nocodexport.<hash>.mjs`.

## How to do (b)

Prerequisite: access to the original Framer project (or a duplicate). Whoever
exported the site via NocodeXport has it.

1. Open the breakpoint bar at the top of the Framer canvas.
2. Add a **Phone** breakpoint (~390px); optionally a **Tablet** breakpoint
   (~810px). Framer creates new layouts that inherit from the primary
   breakpoint. The width shown on the canvas is the minimum viewport width at
   which that breakpoint becomes active.
3. Adjust only what the narrower layout needs — type size, Stack direction, gap,
   padding, width, visibility. Keep overrides focused; add a breakpoint when the
   layout starts to fail, not by habit.
4. Preview across breakpoints inside Framer.
5. Re-export via NocodeXport and replace `index.html` and `assets/` in the repo.

## Reference values from the CSS prototype (branch `proto/mobile-responsive`, deleted)

A throwaway CSS prototype once existed on branch `proto/mobile-responsive`. It is
gone, but its **tuned values** are worth keeping as a starting point for the
breakpoints above. It targeted Framer's generated class hashes, which change on
every export, so the selectors themselves were not reusable — only the numbers.

| Element | ≤768px | ≤400px |
| --- | --- | --- |
| Heading (`framer-styles-preset-hw1bwg`) | 26px | 23px |
| Body (`framer-styles-preset-ett894`) | 17px | 16px |
| Root padding | 24px 16px | — |
| Link cards | 18px padding, 14px gap | — |
| Content blocks | 20–24px padding | — |

## Re-apply checklist after any Framer re-export

A re-export regenerates `index.html` and `assets/` wholesale. Everything applied
directly to those files is lost. After each export, re-apply and verify:

1. **Viewport** — either confirm the export now emits `width=device-width`, or
   re-add the option (a) meta + guard. Do not leave both.
2. **Canonical + hreflang** (from PR #6): self-referencing
   `<link rel="canonical" href="https://wildandpurr.com/">` and the `en` +
   `x-default` alternates.
3. **Open Graph / Twitter tags** — `og:title`, `og:description`, `og:image`
   (`/assets/images/og-wild-and-purr-1200x630.png`), `twitter:card`.
4. **Meta description** — must match the intended copy (see the
   moments/discoveries note below).
5. **`lang` attribute** on `<html>`.
6. **Bundled page text** — any copy edited via `tools/apply_links.py` must be
   re-applied by running that script; it is the single source of truth for links
   and page text.
7. **Files that survive a re-export** (repo-level, not part of the export):
   `robots.txt`, `sitemap.xml`, `CNAME`, `404.html`, `docs/`.

After re-applying, run the standard verification: canonical present and
self-referencing, no staging domain references, viewport correct, desktop
rendering unchanged, and no hydration reversion.

## Verification commands

```
# viewport and guard
curl -s https://wildandpurr.com/ | grep -o 'name="viewport" content="[^"]*"'

# canonical + hreflang
curl -s https://wildandpurr.com/ | grep -oE 'rel="canonical"[^>]*|hreflang="[^"]*"'

# supporting files
for u in /robots.txt /sitemap.xml; do
  curl -s -o /dev/null -w "%{http_code} $u\n" "https://wildandpurr.com$u"
done
```

## Open questions

1. Is the original Framer project available, and who holds it?
2. Do we want a purpose-built phone layout (stacked columns, larger type), or is
   the current fluid layout at native width sufficient? The live option (a)
   already makes the fluid layout usable; option (b) is only required for a
   bespoke mobile design.
3. After a re-export, who runs the re-apply checklist and how is it verified?
