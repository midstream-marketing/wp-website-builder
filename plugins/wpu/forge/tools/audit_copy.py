#!/usr/bin/env python3
"""
audit_copy.py — rendered word count per page, against the copy standard.

    python tools/audit_copy.py <client-slug>

Counts the words a visitor actually sees by walking the *compiled* templates
rather than the copy files, so nested repeaters, FAQ answers and icon-box
descriptions are all included — and anything the IR silently failed to pass
through is correctly counted as absent, which is the whole point.

Floors come from the standing copy standard. A page under its floor is a build
failure, not a nice-to-have. Thin near-duplicate location pages are the usual
offender; the fix is real local substance, or consolidation into one page with
anchored sections. Never padding — a 1,200-word page that could be about any
company in the trade is still thin.
"""
import io
import json
import os
import re
import sys

# Only fields a visitor actually reads. Placeholders and admin-only strings
# (form field labels, button text) are deliberately excluded — they inflate the
# count without being content.
TEXT_KEYS = (
    'editor', 'title', 'title_text', 'description_text', 'text', 'tab_content',
    'item_title', 'acceptance_text', 'nothing_found_message',
)
NESTED_KEYS = TEXT_KEYS + ('tab_title',)

# Floors by page TYPE, not by page. A hub page's job is to route; a
# conversion page's job is to convert. Holding either to a money-page floor
# would reward padding, which the standard explicitly calls a failure.
FLOORS = {
    # Money pages inherit DEFAULT_FLOOR. Everything below is a deliberate
    # page-type classification.
    'home': 800,
    'about': 600,
    # Hubs — route to the money pages rather than rank alone.
    'services': 400,
    'areas-we-serve': 400,
    'service-areas': 400,
    'projects-inspiration': 400,
    # Conversion pages — focused by design; padding actively hurts them.
    'contact': 300,
    'book-service': 300,
    'request-estimate': 300,
}
DEFAULT_FLOOR = 700          # money pages: service and location


def words(doc: dict) -> int:
    total = 0

    def walk(elements):
        nonlocal total
        for el in elements:
            settings = el.get('settings') or {}
            for key, value in settings.items():
                if key in TEXT_KEYS and isinstance(value, str):
                    total += len(re.sub('<[^>]+>', ' ', value).split())
                elif isinstance(value, list):
                    for item in value:
                        if not isinstance(item, dict):
                            continue
                        for k, v in item.items():
                            if k in NESTED_KEYS and isinstance(v, str):
                                total += len(re.sub('<[^>]+>', ' ', v).split())
            walk(el.get('elements') or [])

    walk(doc.get('content', []))
    return total


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__.strip())
        return 2
    slug = sys.argv[1]
    root = os.path.join('clients', slug, 'out', 'templates')
    if not os.path.isdir(root):
        print('no compiled templates at ' + root + ' — run forge.py first')
        return 2

    total = thin = pages = 0
    print('word count vs copy standard — ' + slug)
    for name in sorted(os.listdir(root)):
        doc = json.load(io.open(os.path.join(root, name), encoding='utf-8'))
        if doc.get('type') != 'page':
            continue
        key = name[:-5]
        count = words(doc)
        floor = FLOORS.get(key, DEFAULT_FLOOR)
        ok = count >= floor
        pages += 1
        total += count
        thin += (not ok)
        print('   %-34s %5d   floor %4d   %s'
              % (key, count, floor, 'ok' if ok else 'THIN'))

    print('   %-34s %5d across %d pages' % ('TOTAL', total, pages))
    if thin:
        print('\n   %d page(s) under floor — see the copy standard.' % thin)
    return 1 if thin else 0


if __name__ == '__main__':
    raise SystemExit(main())
