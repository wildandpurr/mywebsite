# Analytics & Consent — Implementation Plan (PROPOSAL, not implemented)

Status: **Draft for review.** No site files are changed by this document.
Branch: `plan/analytics-and-consent` (independent of `main`).

## 1. Goal

Measure where visitors to `https://wildandpurr.com/` come from — including
social platforms (Facebook, Instagram, TikTok, Pinterest, YouTube) — and, only
if advertising starts later, attribute ad conversions.

## 2. Scope decision (recommended)

| Phase | What | Why |
|---|---|---|
| Phase 1 (recommended now) | GA4 + consent + privacy policy | Measures traffic from *all* social sources. ~90% of the value. |
| Phase 2 (defer) | Meta Pixel | Only useful if advertising on Facebook/Instagram. |
| Phase 3 (defer) | TikTok Pixel / Pinterest Tag | Only if advertising on those platforms. |

Rationale: pixels are for advertising attribution and retargeting. GA4 already
shows `facebook.com`, `tiktok.com`, `pinterest.*` etc. as referral sources, so a
per-platform pixel is not needed to *see* social traffic.

## 3. Technical facts about this repository (verified)

- Static **Framer code export** hosted on **GitHub Pages** (`main:/`, custom
  domain via `CNAME`).
- `index.html` contains four custom-code slots, already present:
  - `<!-- Start of headStart -->` / `<!-- End of headStart -->` (line ~45)
  - `<!-- Start of headEnd -->` / `<!-- End of headEnd -->`
  - `<!-- Start of bodyStart -->` / `<!-- End of bodyStart -->`
  - `<!-- Start of bodyEnd -->` / `<!-- End of bodyEnd -->`
- **No analytics or tag manager is currently installed** (verified: no
  `gtag`, `googletagmanager`, `fbq`, `connect.facebook`, or similar).
- The Framer runtime applies `document.title`, `robots` and `viewport` on
  hydration but does **not** remove injected `<script>` tags, so a script added
  to a custom-code slot will run and persist across hydration.

## 4. Implementation options

### Option A — Framer custom-code settings (PREFERRED)

Add the tags through the Framer project's site settings (custom code). On
re-export, Framer re-emits them into the slots, so they survive.

- Pros: survives Framer re-export; single source of truth; matches how the
  export is meant to be extended.
- Cons: requires access to the Framer project and a re-export + redeploy.

### Option B — Hand-edit the exported `index.html`

Insert the tags directly between the marker comments.

- Pros: no Framer access needed; immediate.
- Cons: a future Framer re-export will **overwrite** the hand-added tags unless
  they are re-applied. Must be recorded in `AGENTS.md` and re-applied after any
  re-export.

Recommendation: use **Option A** if the Framer project is accessible; otherwise
Option B with a documented re-apply step.

## 5. Tag placement (for either option)

- **GA4 / consent defaults** → `headStart` (must load before other tags).
- **Meta Pixel / TikTok / Pinterest** → `bodyStart`.

### GA4 (Google Analytics 4)

```html
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

### Meta Pixel (Phase 2 only)

```html
<!-- Meta Pixel Code -->
<script>
  !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?
  n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;
  n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
  t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,
  document,'script','https://connect.facebook.net/en_US/fbevents.js');
  fbq('init', 'YOUR_PIXEL_ID');
  fbq('track', 'PageView');
</script>
<noscript><img height="1" width="1" style="display:none"
  src="https://www.facebook.com/tr?id=YOUR_PIXEL_ID&ev=PageView&noscript=1"/></noscript>
```

IDs come from: GA4 property (analytics.google.com) and Meta Events Manager.
Both are free and can only be created by the site owner.

## 6. Consent (required before any tag goes live)

The audience is UK/EU-oriented, so UK PECR / GDPR require **prior consent**
before analytics or advertising cookies are set.

- Choose a consent mechanism: a hosted CMP (e.g. a free tier) or a lightweight
  self-hosted banner.
- Implement **Google Consent Mode v2** with denied defaults, then update on
  user choice:

```html
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('consent', 'default', {
    'ad_storage': 'denied',
    'ad_user_data': 'denied',
    'ad_personalization': 'denied',
    'analytics_storage': 'denied'
  });
</script>
```

- Do not fire GA4/Meta tags until consent is granted.

## 7. Privacy policy (required)

Both Google and Meta require a linked privacy policy that discloses analytics
and advertising cookies. The site has **no privacy policy page** today.

Outline (to be drafted and reviewed before publication):

1. Who we are and how to contact us.
2. What data we collect (analytics identifiers, IP, device/browser, referrer).
3. Cookies and similar technologies (which ones, purpose, duration).
4. Legal basis and consent, and how to withdraw it.
5. Third parties (Google Analytics; Meta/TikTok/Pinterest if used).
6. Data retention and international transfers.
7. User rights (access, deletion, objection) and how to exercise them.
8. Changes to the policy and effective date.

The policy must be reachable from the site (footer link) and referenced by the
consent banner.

## 8. Risks

| Risk | Mitigation |
|---|---|
| Framer re-export overwrites hand-added tags (Option B) | Prefer Option A; document a re-apply checklist in `AGENTS.md`. |
| Non-compliant tracking without consent | Do not deploy tags until consent + privacy policy are live. |
| Scope creep into advertising pixels | Keep Phase 1 to GA4 only; add pixels per-platform only when advertising. |
| Performance | Tags are async (~30 KB GA4, ~20 KB pixel); negligible but measurable. |
| Data accuracy | GA4 sampling/consent gaps can undercount; document expectations. |

## 9. Verification plan (once implemented, on a preview before production)

1. Serve the branch locally; confirm tags are present in raw HTML.
2. Load in a headless browser; confirm network requests to
   `googletagmanager.com` (and pixel host, if Phase 2) fire **only after**
   consent is granted.
3. Confirm no tags fire when consent is denied (test both states).
4. Confirm GA4 Realtime / DebugView shows the pageview after consent.
5. Confirm no console errors and no layout change (screenshot compare).
6. Confirm the privacy policy page loads and is linked.

## 10. Milestones

1. **M1** — Owner decisions: choose Option A or B; choose consent mechanism;
   approve privacy-policy outline.
2. **M2** — Owner provides GA4 measurement ID (and pixel ID if Phase 2).
3. **M3** — Draft implementation on an isolated branch (tags + consent +
   privacy page).
4. **M4** — Verification per section 9, with before/after evidence.
5. **M5** — Owner review and explicit approval; only then merge and deploy.

## 11. Open questions for the owner

1. Is the Framer project accessible (Option A), or must this be Option B?
2. Is a hosted consent CMP acceptable, or is a self-hosted banner preferred?
3. Is there an existing privacy policy, or should one be drafted from scratch?
4. Do you intend to run paid ads on any platform in the next 6–12 months?
   (Determines whether Phase 2/3 are needed at all.)
