#!/usr/bin/env python3
"""Check an SEO plan and turn it into the changes file the bridge applies.

    python tools/seo/seo_plan.py            reads  sites/<slug>/seo/plan.json
                                            writes sites/<slug>/seo/changes.json + plan-report.md

plan.json is written by the seo-strategist agent:
  { "pages": [ { "id": 12, "url": "/roof-repair/", "focus_keyword": "roof repair austin",
                 "title": "...", "description": "...", "canonical": null, "noindex": false,
                 "schema": { ... JSON-LD ... } } ] }

Hard errors (exit 1, no changes file):
  - the same focus keyword on two pages (they compete with each other)
  - duplicate titles or descriptions
  - a title or description that is empty
  - ranking or result promises ("guaranteed", "#1 on Google", "rank first")
Warnings (reported, not blocking): length outside the usual range, focus keyword
missing from the title, a page id that is not in seo/current.json.

Lengths are a character proxy - Google truncates on pixel width - so they warn, never block.
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _wpu import site_dir, write_json  # noqa: E402

TITLE = (30, 60)
DESC = (70, 160)
PROMISES = re.compile(r"\b(guarantee[ds]?|#\s?1 on google|rank (?:first|#?1)|top of google|page one guaranteed)\b", re.I)


def main() -> int:
    d = site_dir() / "seo"
    plan_p = d / "plan.json"
    if not plan_p.exists():
        sys.exit(f"{plan_p} not found")
    plan = json.loads(plan_p.read_text(encoding="utf-8-sig"))
    pages = plan.get("pages") or []
    known = set()
    cur_p = d / "current.json"
    if cur_p.exists():
        known = {p["id"] for p in json.loads(cur_p.read_text(encoding="utf-8-sig")).get("pages", [])}

    errors, warns = [], []
    seen = {"focus_keyword": defaultdict(list), "title": defaultdict(list), "description": defaultdict(list)}
    items = []
    for p in pages:
        pid = p.get("id")
        tag = f"#{pid} {p.get('url', '')}"
        if not isinstance(pid, int):
            errors.append(f"{tag}: id must be the WordPress post id (number)")
            continue
        if known and pid not in known:
            warns.append(f"{tag}: not in seo/current.json - run scripts/rseo.ps1 list")
        for f in ("title", "description"):
            v = (p.get(f) or "").strip()
            if f in p and not v:
                errors.append(f"{tag}: empty {f}")
            if v and PROMISES.search(v):
                errors.append(f"{tag}: {f} promises a ranking or result: \"{PROMISES.search(v).group(0)}\"")
            if v:
                lo, hi = TITLE if f == "title" else DESC
                if not lo <= len(v) <= hi:
                    warns.append(f"{tag}: {f} is {len(v)} chars (usual {lo}-{hi})")
                seen[f][v.lower()].append(tag)
        kw = (p.get("focus_keyword") or "").strip()
        if kw:
            seen["focus_keyword"][kw.lower()].append(tag)
            if p.get("title") and kw.lower() not in p["title"].lower():
                warns.append(f"{tag}: focus keyword \"{kw}\" is not in the title")
        item = {"id": pid}
        for f in ("title", "description", "focus_keyword", "canonical", "noindex", "schema"):
            if f in p:
                item[f] = p[f]
        items.append(item)

    for f, label in (("focus_keyword", "focus keyword"), ("title", "title"), ("description", "description")):
        for v, tags in seen[f].items():
            if len(tags) > 1:
                errors.append(f"same {label} on {len(tags)} pages ({', '.join(tags)}): \"{v}\"")

    report = ["# SEO plan check", "", f"{len(items)} page(s), {len(errors)} error(s), {len(warns)} warning(s).", ""]
    report += ["## Errors", *[f"- {e}" for e in errors], ""] if errors else []
    report += ["## Warnings", *[f"- {w}" for w in warns], ""] if warns else []
    (d / "plan-report.md").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))

    if errors:
        print("Not writing changes.json until the errors are fixed.")
        return 1
    out = write_json(d / "changes.json", {"items": items})
    print(f"-> {out}\nNext: powershell -File scripts/rseo.ps1 push {out}   (dry run, then add 'apply')")
    return 0


if __name__ == "__main__":
    sys.exit(main())
