#!/usr/bin/env python3
"""Regenerate the "More from Wild and Purr" links section of this site.

Why this exists
---------------
This repo is a static Framer export. Framer keeps TWO copies of every string:
the server-rendered DOM in ``index.html`` and the React component tree inside
``assets/animate/shared-lib.<hash>.mjs``. On load, React hydrates the
``framer-1gey6qo`` container and DELETES any server DOM it does not recognise,
then renders its own copy. If the two copies disagree, the edited text/logo
paints first and is then replaced by the old version: the "flash then revert"
bug.

So the links block must be identical in both files. This script is the single
source of truth for that block: edit ``LINKS`` below and re-run it. It rewrites
the SSR markup, the hydration bundle, the CSS (banner colours + icon masks) and
the Framer search index together, then renames the bundle so browsers cannot
serve a stale copy.

It is idempotent: running it twice changes nothing.

Usage
-----
    python3 tools/apply_links.py

Then serve the repo and confirm the DOM does not change after hydration:

    python3 -m http.server 8000
    # MutationObserver on .framer-1gey6qo should report 0 mutations.
"""

import base64
import hashlib
import html
import json
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# DATA MODEL - edit this, nothing else.
#
# Each entry: (icon, label, aria-label, url, theme)
#   icon  key into ICON_BODIES below
#   label the visible banner text, reproduced verbatim from the brief
#   url   a real link, or '#' when no live URL exists yet (clean placeholder)
#   theme banner background: wp / sofia / studio / kofi
# --------------------------------------------------------------------------
LINKS = [
    ('tiktok',    'TikTok · Wild and Purr',
     'Wild and Purr on TikTok',
     'https://www.tiktok.com/@wildandpurr2026',        'wp'),
    ('tiktok',    'TikTok · Sofia Tina Graf',
     'Sofia Tina Graf on TikTok',
     'https://www.tiktok.com/@sofiatinagraf',          'sofia'),
    ('youtube',   'YouTube · Our music channel',
     'Mirildan Meltem Studio on YouTube',
     'https://www.youtube.com/@MirildanMeltemStudio',  'studio'),
    ('kofi',      'Ko-fi · Support our creative world',
     'Support Wild and Purr on Ko-fi',
     'https://ko-fi.com/wildandpurr',                  'kofi'),
    ('amazon',    'Amazon · Wild and Purr – coming soon',
     'Wild and Purr on Amazon',
     '#',                                              'wp'),
    ('amazon',    "Amazon · Sofia Tina Graf's author page – coming soon",
     'Sofia Tina Graf\u2019s author page on Amazon',
     '#',                                              'sofia'),
    ('bookvaib',  'Bookvaib · Wild and Purr – coming soon',
     'Wild and Purr on Bookvaib',
     '#',                                              'wp'),
    ('bookvaib',  'Bookvaib · Sofia Tina Graf – coming soon',
     'Sofia Tina Graf on Bookvaib',
     '#',                                              'sofia'),
    ('instagram', 'Instagram · Wild and Purr',
     'Wild and Purr on Instagram',
     '#',                                              'wp'),
    ('instagram', 'Instagram · Sofia Tina Graf',
     'Sofia Tina Graf on Instagram',
     '#',                                              'sofia'),
    ('instagram', 'Instagram · Mirildan Meltem Studio',
     'Mirildan Meltem Studio on Instagram',
     '#',                                              'studio'),
    ('pinterest', 'Pinterest · Wild and Purr',
     'Wild and Purr on Pinterest',
     'https://uk.pinterest.com/wildandpurr/',          'wp'),
]

# Banner background per theme. wp/sofia/studio come from the original brief;
# kofi is the pastel coffee tone requested for the Ko-fi banner.
BG = {'wp': '#EFEBE9', 'sofia': '#E1D4F9', 'studio': '#FFF4B5', 'kofi': '#F0DFCD'}

# The hashtags line sits inside the same hydrated container as the banners, so
# it is duplicated in the SSR markup and the bundle and must be kept in sync the
# same way. Edit here, not in the generated files.
HASHTAGS = ('#WildandPurr #SofiaTinaGraf #HiddenInTheEverydayBook '
            '#WordSearchBook #MirildanMeltemStudio')

# --------------------------------------------------------------------------
# PAGE TEXT - every visible string on the page, keyed by the framer class of the
# wrapper element that holds it. That class is the same in index.html and in the
# bundle, so it is the join key between the two copies.
#
# Edit the value, re-run the script, and both copies are updated together. Do
# NOT hand-edit index.html for anything in this table: React would overwrite it
# on hydration. Strings not listed here are not managed by this script.
#
# Keys marked "banner label" are owned by LINKS above; leave them alone.
# --------------------------------------------------------------------------
TEXT = {
    'title':        'Wild and Purr',
    'framer-15gmmv0': 'INDEPENDENT BOOKS AND MUSIC',
    'framer-fyhsa4': 'Our home for stories, art, sounds, and everything we are '
                     'creating next. We are just getting started, and much of '
                     'this website is still under construction. More coming '
                     'soon. We hope you will enjoy it.',
    'framer-o8agl2': 'JUST GETTING STARTED',
    'framer-planw1': 'Our first chapter is coming soon.',
    'framer-8pkoyt': 'New books are on their way. This is where you\u2019ll find '
                     'our upcoming titles, cover reveals, and release news.',
    'framer-fefy1v': 'MEET ONE OF OUR AUTHORS',
    'framer-zkgdkh': 'Sofia Tina Graf',
    'framer-15f34k3': 'Sofia Tina Graf is an activity book author. Her first '
                      'book, the beginning of a new collection, is coming soon.',
    'framer-1htb9t2': 'MEET OUR MUSIC STUDIO',
    'framer-gmow2t': 'Mirildan Meltem Studio',
    'framer-17vy7e1': 'The musical side of our creative world. Mirildan Meltem '
                      'Studio is just getting started, with music and more '
                      'about the studio coming soon.',
    'framer-11a7gwn': 'More from Wild and Purr',
    'framer-9yttpo': 'Our social channels are new and mostly empty for now. '
                     'You\u2019re welcome to follow as we begin adding books, '
                     'music, and updates.',
    'framer-1w68hq2': 'Our hashtags',
    'framer-4p7c17':  '\u00a9 2026 Wild and Purr. Made for curious hearts.',
}

# Self-contained mask glyphs (no external sprite). Each becomes
# ``.framer-lkic--<name>{mask-image:url('data:image/svg+xml,<svg ...>')}``.
ICON_BODIES = {
    "tiktok": "<svg display=\"block\" role=\"presentation\" viewBox=\"0 0 16 16\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M 7.301 0.013 C 8.174 0 9.041 0.007 9.907 0 C 9.961 1.02 10.327 2.06 11.074 2.78 C 11.821 3.52 12.874 3.86 13.901 3.973 L 13.901 6.66 C 12.941 6.627 11.974 6.427 11.101 6.013 C 10.721 5.84 10.367 5.62 10.021 5.393 C 10.014 7.34 10.027 9.287 10.007 11.227 C 9.954 12.16 9.647 13.087 9.107 13.853 C 8.234 15.133 6.721 15.967 5.167 15.993 C 4.214 16.047 3.261 15.787 2.447 15.307 C 1.101 14.513 0.154 13.06 0.014 11.5 C 0.001 11.167 -0.006 10.833 0.007 10.507 C 0.127 9.24 0.754 8.027 1.727 7.2 C 2.834 6.24 4.381 5.78 5.827 6.053 C 5.841 7.04 5.801 8.027 5.801 9.013 C 5.141 8.8 4.367 8.86 3.787 9.26 C 3.367 9.533 3.047 9.953 2.881 10.427 C 2.741 10.767 2.781 11.14 2.787 11.5 C 2.947 12.593 4.001 13.513 5.121 13.413 C 5.867 13.407 6.581 12.973 6.967 12.34 C 7.094 12.12 7.234 11.893 7.241 11.633 C 7.307 10.44 7.281 9.253 7.287 8.06 C 7.294 5.373 7.281 2.693 7.301 0.013\" fill=\"var(--t829wi, rgb(0,0,0))\"/></svg>",
    "youtube": "<svg display=\"block\" role=\"presentation\" viewBox=\"0 0 16 16\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M 15.665 1.761 C 15.481 1.068 14.942 0.526 14.251 0.337 C 13.003 0 8 0 8 0 C 8 0 2.997 0 1.749 0.337 C 1.058 0.526 0.519 1.068 0.335 1.761 C 0 3.017 0 5.637 0 5.637 C 0 5.637 0 8.257 0.335 9.513 C 0.519 10.205 1.058 10.748 1.749 10.937 C 2.997 11.273 8 11.273 8 11.273 C 8 11.273 13.003 11.273 14.251 10.937 C 14.943 10.748 15.482 10.205 15.666 9.513 C 16 8.257 16 5.637 16 5.637 C 16 5.637 16 3.017 15.665 1.761 M 6.363 8.015 L 6.363 3.258 L 10.545 5.637 Z\" fill=\"var(--t829wi, rgb(0,0,0))\"/></svg>",
    "kofi": "<svg display=\"block\" role=\"presentation\" viewBox=\"0 0 24 24\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M 0 5.516 C 0 3.238 1.404 1.196 3.532 0.381 C 5.659 -0.435 8.068 0.146 9.591 1.84 C 9.697 1.954 9.845 2.018 10 2.018 C 10.155 2.018 10.303 1.954 10.409 1.84 C 11.927 0.135 14.343 -0.453 16.475 0.364 C 18.607 1.181 20.011 3.233 20 5.516 C 20 7.806 18.5 9.516 17 11.016 L 11.508 16.329 C 11.131 16.762 10.586 17.012 10.012 17.016 C 9.438 17.02 8.89 16.776 8.508 16.348 L 3 11.016 C 1.5 9.516 0 7.816 0 5.516\" fill=\"var(--t829wi, rgb(0,0,0))\"/></svg>",
    "amazon": "<svg display=\"block\" role=\"presentation\" viewBox=\"0 0 24 24\" xmlns=\"http://www.w3.org/2000/svg\"><g fill=\"none\" stroke=\"var(--t829wi, rgb(0,0,0))\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M6.5 8h11l.9 11.5H5.6L6.5 8Z\"/><path d=\"M9.5 8V6.2a2.5 2.5 0 0 1 5 0V8\"/></g></svg>",
    "bookvaib": "<svg display=\"block\" role=\"presentation\" viewBox=\"0 0 24 24\" xmlns=\"http://www.w3.org/2000/svg\"><g fill=\"none\" stroke=\"var(--t829wi, rgb(0,0,0))\" stroke-width=\"2\" stroke-linejoin=\"round\"><path d=\"M12 7C9.5 5.2 6.5 4.6 4 5V18c2.5-.4 5.5.2 8 2\"/><path d=\"M12 7c2.5-1.8 5.5-2.4 8-2V18c-2.5-.4-5.5.2-8 2\"/><path d=\"M12 7v13\"/></g></svg>",
    "instagram": "<svg display=\"block\" role=\"presentation\" viewBox=\"0 0 24 24\" xmlns=\"http://www.w3.org/2000/svg\"><g fill=\"none\" stroke=\"var(--t829wi, rgb(0,0,0))\" stroke-width=\"2\"><rect x=\"2\" y=\"2\" width=\"20\" height=\"20\" rx=\"5.5\"/><circle cx=\"12\" cy=\"12\" r=\"4.2\"/></g><circle cx=\"17.4\" cy=\"6.6\" r=\"1.3\" fill=\"var(--t829wi, rgb(0,0,0))\"/></svg>",
    "pinterest": "<svg display=\"block\" role=\"presentation\" viewBox=\"0 0 24 24\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.162-.105-.949-.199-2.403.041-3.439.219-.937 1.406-5.957 1.406-5.957s-.359-.72-.359-1.781c0-1.663.967-2.911 2.168-2.911 1.024 0 1.518.769 1.518 1.688 0 1.029-.653 2.567-.992 3.992-.285 1.193.6 2.165 1.775 2.165 2.128 0 3.768-2.245 3.768-5.487 0-2.861-2.063-4.869-5.008-4.869-3.41 0-5.409 2.562-5.409 5.199 0 1.033.394 2.143.889 2.741.099.12.112.225.085.345-.09.375-.293 1.199-.334 1.363-.053.225-.172.271-.401.165-1.495-.69-2.433-2.878-2.433-4.646 0-3.776 2.748-7.252 7.92-7.252 4.158 0 7.392 2.967 7.392 6.923 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.354-.629-2.758-1.379l-.749 2.848c-.269 1.045-1.004 2.352-1.498 3.146 1.123.345 2.306.535 3.55.535 6.607 0 11.985-5.365 11.985-11.987C23.97 5.39 18.592.026 11.985.026L12.017 0z\" fill=\"var(--t829wi, rgb(0,0,0))\"/></svg>"
}

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / 'index.html'
META = [ROOT / 'assets/meta/meta-d824b18e.json',
        ROOT / 'assets/meta/meta-da3c89c2.json']

# Stable anchors. Asserted unique so a re-export that moves things fails loudly
# instead of silently corrupting the page.
SSR_START = '<a aria-label="Wild and Purr on TikTok"'
SSR_END = '<div class="framer-18r5lyp" data-framer-name="Our hashtags">'
BND_FIRST_LABEL = 'Wild and Purr on TikTok'
BND_END = '/*#__PURE__*/ s(`div`,{className:`framer-18r5lyp`'
BND_BANNER_START = '/*#__PURE__*/ c(`a`'
CSS_START = '.framer-lk{'
CSS_END = '</style><!-- Start of headEnd -->'
HASHTAGS_PREFIX = '#WildandPurr'

# Filled by main() with the managed strings as they currently appear on disk.
OLD_TEXT = {}


def bundle_path():
    hits = sorted((ROOT / 'assets' / 'animate').glob('shared-lib.*.mjs'))
    if len(hits) != 1:
        sys.exit('expected exactly one shared-lib bundle, found: %r'
                 % [h.name for h in hits])
    return hits[0]


def mask_uri(body):
    return "url('data:image/svg+xml,%s')" % body


def ssr_banner(icon, label, aria_label, url, theme):
    target = '' if url == '#' else ' target="_blank" rel="noopener noreferrer"'
    return (
        '<a aria-label="%s" class="framer-lk framer-lk--%s" href="%s"%s>'
        '<div class="framer-lkic framer-lkic--%s"></div>'
        '<div class="framer-lkt" data-framer-component-type="RichTextContainer"'
        ' style="transform:none">'
        '<p class="framer-text framer-styles-preset-ett894"'
        ' data-styles-preset="F4MC6C3X_" dir="auto"'
        ' style="--framer-text-alignment:start">%s</p></div></a>'
    ) % (aria_label, theme, url, target, icon, label)


def bundle_banner(icon, label, aria_label, url, theme):
    target = '' if url == '#' else ',target:`_blank`,rel:`noopener noreferrer`'
    return (
        '/*#__PURE__*/ c(`a`,{"aria-label":`%s`,'
        'className:`framer-lk framer-lk--%s`,href:`%s`%s,children:['
        '/*#__PURE__*/ c(`div`,{className:`framer-lkic framer-lkic--%s`}),'
        '/*#__PURE__*/ c(`div`,{className:`framer-lkt`,'
        '"data-framer-component-type":`RichTextContainer`,style:{transform:`none`},'
        'children:/*#__PURE__*/ c(`p`,'
        '{className:`framer-text framer-styles-preset-ett894`,'
        '"data-styles-preset":`F4MC6C3X_`,dir:`auto`,'
        'style:{"--framer-text-alignment":`start`},children:`%s`})})]})'
    ) % (aria_label, theme, url, target, icon, label)


def css_block():
    rules = [
        '.framer-lk{box-sizing:border-box;cursor:pointer;height:min-content;'
        'overflow:var(--overflow-clip-fallback,clip);'
        'will-change:var(--framer-will-change-override,transform);border-radius:16px;'
        'display:flex;flex-flow:row;flex:none;place-content:center flex-start;'
        'align-items:center;gap:20px;width:100%;padding:24px;text-decoration:none;'
        'position:relative}',
    ]
    for theme, colour in BG.items():
        rules.append('.framer-lk--%s{background-color:%s}' % (theme, colour))
    rules.extend([
        '.framer-lkic{flex:none;width:28px;height:28px;aspect-ratio:1;'
        'background-color:#282526;-webkit-mask-repeat:no-repeat;mask-repeat:no-repeat;'
        '-webkit-mask-position:center;mask-position:center;'
        '-webkit-mask-size:contain;mask-size:contain}',
        '.framer-lkt{white-space:pre-wrap;word-break:break-word;word-wrap:break-word;'
        'flex:1 0 0;width:1px;height:auto;position:relative}',
    ])
    for name, body in ICON_BODIES.items():
        uri = mask_uri(body)
        rules.append('.framer-lkic--%s{-webkit-mask-image:%s;mask-image:%s}'
                     % (name, uri, uri))
    return ''.join(rules)


def unique(haystack, needle, what):
    n = haystack.count(needle)
    if n != 1:
        sys.exit('anchor %r (%s) found %d times, expected 1' % (needle, what, n))


def read_text_on_disk(index, script):
    """Read back the current value of each managed string from index.html, so a
    rename can be traced in the meta index (old value -> new value)."""
    found = {}
    for key in TEXT:
        if key == 'title':
            t = re.search(r'<title[^>]*>(.*?)</title>', index, re.S)
            if t:
                found[key] = t.group(1)
            continue
        pat = re.compile(r'<div class="%s"[^>]*><[ph][0-9]?[^>]*>(.*?)'
                         r'</[ph][0-9]?>' % re.escape(key), re.S)
        m = pat.search(index)
        if m:
            found[key] = html.unescape(m.group(1)).strip()
    return found


def _escape_html(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def apply_text_ssr(s):
    """Rewrite the server-rendered copy of each managed string, matched by the
    class of its wrapper div so we never touch an unrelated element."""
    t = re.search(r'(<title[^>]*>)(.*?)(</title>)', s, re.S)
    if not t:
        sys.exit('index.html: <title> not found')
    s = s[:t.start()] + t.group(1) + TEXT['title'] + t.group(3) + s[t.end():]

    for key, value in TEXT.items():
        if key == 'title':
            continue
        pat = re.compile(r'(<div class="%s"[^>]*>)(<[ph][0-9]?[^>]*>)(.*?)(</[ph][0-9]?>)'
                         % re.escape(key), re.S)
        hits = pat.findall(s)
        if len(hits) != 1:
            sys.exit('index.html: expected one text node under .%s, found %d'
                     % (key, len(hits)))
        s = pat.sub(lambda m: m.group(1) + m.group(2) + _escape_html(value)
                    + m.group(4), s, count=1)
    return s


def apply_text_bundle(s):
    """Rewrite the bundle's copy. Each string sits in children:`...` directly
    before className:`<key>`, which is what makes it identifiable."""
    for key, value in TEXT.items():
        if key == 'title':
            continue
        anchor = 'className:`%s`' % key
        if s.count(anchor) != 1:
            sys.exit('bundle: className:`%s` found %d times, expected 1'
                     % (key, s.count(anchor)))
        at = s.index(anchor)
        open_at = s.rfind('children:`', 0, at)
        if open_at < 0:
            sys.exit('bundle: no children:` before className:`%s`' % key)
        close_at = s.index('`', open_at + len('children:`'))
        if close_at > at:
            sys.exit('bundle: children string for %s is not closed before '
                     'className' % key)
        s = s[:open_at] + 'children:`' + value + '`' + s[close_at + 1:]
    return s


def replace_hashtags_ssr(s):
    """The hashtags paragraph sits inside the hydrated container, so it too
    exists twice. Match the whole <p> by its prefix and rewrite its text."""
    pat = re.compile(r'(<p class="framer-text framer-styles-preset-ett894"'
                     r' data-styles-preset="F4MC6C3X_" dir="auto">)'
                     r'#WildandPurr[^<]*(</p>)')
    if len(pat.findall(s)) != 1:
        sys.exit('SSR: expected exactly one hashtags paragraph, found %d'
                 % len(pat.findall(s)))
    return pat.sub(lambda m: m.group(1) + HASHTAGS + m.group(2), s)


def replace_hashtags_bundle(s):
    pat = re.compile(r'(children:`)#WildandPurr[^`]*(`)')
    if len(pat.findall(s)) != 1:
        sys.exit('bundle: expected exactly one hashtags string, found %d'
                 % len(pat.findall(s)))
    return pat.sub(lambda m: m.group(1) + HASHTAGS + m.group(2), s)


def replace_ssr(s):
    unique(s, SSR_START, 'SSR first banner')
    unique(s, SSR_END, 'SSR hashtags block')
    start, end = s.index(SSR_START), s.index(SSR_END)
    return s[:start] + ''.join(ssr_banner(*l) for l in LINKS) + s[end:]


def replace_css(s):
    unique(s, CSS_START, 'CSS block start')
    unique(s, CSS_END, 'CSS block end')
    start, end = s.index(CSS_START), s.index(CSS_END)
    if start > end:
        sys.exit('CSS anchors are out of order')
    return s[:start] + css_block() + s[end:]


def replace_bundle(s):
    if BND_FIRST_LABEL not in s:
        sys.exit('bundle: first banner label not found')
    unique(s, BND_END, 'bundle hashtags block')
    end = s.index(BND_END)
    start = s.rfind(BND_BANNER_START, 0, s.index(BND_FIRST_LABEL))
    if not (0 <= start < end):
        sys.exit('bundle: could not locate first banner')
    body = ','.join(bundle_banner(*l) for l in LINKS)
    return s[:start] + body + ',' + s[end:]


def update_meta():
    labels = [l[1] for l in LINKS]
    wanted = set(labels)
    # Map every managed string to its current on-disk value, so the search index
    # can be moved from old -> new without inventing or dropping entries.
    managed = {k: v for k, v in TEXT.items() if k != 'title'}
    for path in META:
        data = json.loads(path.read_text(encoding='utf-8'))
        paras = data['/']['p']
        anchor = next((n for n, p in enumerate(paras)
                       if p.startswith(HASHTAGS_PREFIX)), None)
        if anchor is None:
            sys.exit('meta %s: hashtags paragraph not found' % path.name)
        # Drop every current banner label, then splice the list back in just
        # before the hashtags line. Keeps the rest of the index untouched.
        out = [p for p in paras if p not in wanted]
        anchor = next(n for n, p in enumerate(out)
                      if p.startswith(HASHTAGS_PREFIX))
        out = [HASHTAGS if p.startswith(HASHTAGS_PREFIX) else p for p in out]
        data['/']['p'] = out[:anchor] + labels + out[anchor:]

        # Refresh managed strings in place, matching on the previous value so a
        # renamed string is found and updated rather than duplicated.
        old_to_new = {}
        for key, new in managed.items():
            old = OLD_TEXT.get(key)
            if old and old != new:
                old_to_new[old] = new
        if old_to_new:
            data['/']['p'] = [old_to_new.get(p, p) for p in data['/']['p']]
        path.write_text(json.dumps(data, ensure_ascii=False,
                                   separators=(',', ':')), encoding='utf-8')


def rename_bundle(old):
    """Content-hash the bundle and repoint every reference, so browsers that
    cached the old URL cannot keep serving stale banners."""
    text = old.read_text(encoding='utf-8')
    text = re.sub(r'shared-lib\.[A-Za-z0-9_-]+\.mjs\.map', 'MAPREF', text)
    digest = base64.urlsafe_b64encode(
        hashlib.sha256(text.encode('utf-8')).digest()).decode().rstrip('=')[:8]
    new_name = 'shared-lib.%s.mjs' % digest
    for path in [INDEX] + sorted((ROOT / 'assets' / 'animate').glob('*.mjs')):
        body = path.read_text(encoding='utf-8', newline='')
        if old.name in body:
            path.write_text(body.replace(old.name, new_name),
                            encoding='utf-8', newline='')
    new = old.with_name(new_name)
    new.write_text(text.replace('MAPREF', new_name + '.map'), encoding='utf-8')
    if new != old:
        old.unlink()
    return new


def main():
    # Fail early on a typo in a theme or icon name rather than emitting a banner
    # with no background colour or a blank icon.
    for icon, label, _aria, _url, theme in LINKS:
        if theme not in BG:
            sys.exit('unknown theme %r on %r' % (theme, label))
        if icon not in ICON_BODIES:
            sys.exit('unknown icon %r on %r' % (icon, label))

    bundle = bundle_path()
    index = INDEX.read_text(encoding='utf-8', newline='')
    script = bundle.read_text(encoding='utf-8')

    # Snapshot the strings as they currently are on disk, so update_meta() can
    # follow a rename from the old value to the new one.
    global OLD_TEXT
    OLD_TEXT = read_text_on_disk(index, script)

    index = replace_ssr(index)
    index = replace_css(index)
    index = replace_hashtags_ssr(index)
    index = apply_text_ssr(index)
    script = replace_bundle(script)
    script = replace_hashtags_bundle(script)
    script = apply_text_bundle(script)

    INDEX.write_text(index, encoding='utf-8', newline='')
    bundle.write_text(script, encoding='utf-8')
    update_meta()
    new_bundle = rename_bundle(bundle)
    print('banners: %d | bundle: %s' % (len(LINKS), new_bundle.name))


if __name__ == '__main__':
    main()
