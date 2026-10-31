#!/usr/bin/env python3
"""images.py - resolve every image a kit needs, from the best available source.

Sourcing has been the weakest part of this pipeline: hand-picked URLs, verified
one at a time, and twice the cause of an import that silently replaced every
photo with a placeholder. This makes it a build step with the failure modes
encoded as rules rather than as things I have to remember.

    python images.py clients/nextgen-plumbing/intake.json --preset plumber --dry-run
    python images.py clients/nextgen-plumbing/intake.json --preset plumber --write

Resolution order per slot:
  1. client-supplied  - a local file or a URL already in the intake, always wins
  2. generated        - cached output from generate_images.py
  3. stock            - searched via the Pexels API
  4. empty            - Elementor shows its own placeholder, which is the
                        honest signal that a photo is still owed

Every candidate must pass the same gate before it is written:
  - an image extension in the URL *path*, not the query string
  - no query string at all (WordPress derives the filename with basename())
  - reachable, returning image/*
  - at least MIN_W wide
  - the right orientation for the slot
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

PEXELS_SEARCH = "https://api.pexels.com/v1/search"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
MIN_W = 1200
RELEVANCE_POOL = 6      # rank by relevance first, then weight within this
MAX_BYTES = 6_000_000     # skip anything heavier; --max-mb overrides
IMG_EXT = re.compile(r"\.(jpe?g|png|webp)$", re.I)

# Orientation each role needs. A portrait hero in a landscape slot is the
# difference between a designed page and a stretched one.
ROLE_SHAPE = {
    "hero": "landscape",
    "team": "portrait",
    "about": "landscape",
    "service": "landscape",
    "background": "landscape",
    "gallery": "landscape",
    "cta": "landscape",
}


# ─────────────────────────────── validation ───────────────────────────────

def normalise(url: str) -> str:
    """Strip the query string. Pexels' API hands back sized URLs like
    `...jpeg?auto=compress&w=940`; WordPress turns that whole tail into the
    destination filename, fails wp_check_filetype, and drops the image."""
    return url.split("?")[0]


def check(url: str, timeout: int = 20) -> tuple[bool, str, int]:
    """Returns (ok, reason, bytes). Size comes free with the HEAD request.

    Only Pexels' `original` variant has a clean URL, and originals run
    2-7 MB. WordPress generates its own sized variants on upload so the
    served page is unaffected, but the import downloads every byte — so
    among candidates that pass, prefer the lighter file.
    """
    if "?" in url:
        return False, "query string", 0
    if not IMG_EXT.search(urllib.parse.urlparse(url).path):
        return False, "no image extension in path", 0
    try:
        req = urllib.request.Request(url, method="HEAD", headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            if r.status != 200:
                return False, f"HTTP {r.status}", 0
            ctype = (r.headers.get("Content-Type") or "")
            if not ctype.startswith("image/"):
                return False, f"content-type {ctype}", 0
            size = int(r.headers.get("Content-Length") or 0)
            if MAX_BYTES and size > MAX_BYTES:
                return False, f"{size/1e6:.1f} MB over cap", size
            return True, ctype, size
    except Exception as e:
        return False, str(e)[:48], 0


# ───────────────────────────────── sources ─────────────────────────────────

def pexels(query: str, shape: str, per_page: int = 20) -> list[dict]:
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        raise RuntimeError(
            "PEXELS_API_KEY is not set. Get a free key at "
            "https://www.pexels.com/api/ and set it in your environment.")
    qs = urllib.parse.urlencode({
        "query": query, "per_page": per_page,
        "orientation": shape, "size": "large",
    })
    req = urllib.request.Request(f"{PEXELS_SEARCH}?{qs}",
                                 headers={**UA, "Authorization": key})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode("utf-8"))
    out = []
    for p in data.get("photos", []):
        if p.get("width", 0) < MIN_W:
            continue
        # `src.original` is the only variant without a query string.
        url = normalise(p["src"]["original"])
        out.append({
            "url": url,
            "alt": (p.get("alt") or "").strip(),
            "w": p.get("width"), "h": p.get("height"),
            "credit": p.get("photographer"),
            "source": "pexels",
            "id": p.get("id"),
        })
    return out


def generated(cache: Path, role: str) -> list[dict]:
    """Anything generate_images.py has already produced for this role."""
    d = cache / "generated"
    if not d.exists():
        return []
    return [{"url": p.as_uri(), "alt": "", "source": "generated", "local": str(p)}
            for p in sorted(d.glob(f"{role}*")) if IMG_EXT.search(p.name)]


# ───────────────────────────────── resolve ─────────────────────────────────

def resolve_slot(role: str, queries: list[str], want: int, cache: Path,
                 taken: set[str]) -> list[dict]:
    shape = ROLE_SHAPE.get(role, "landscape")
    picked: list[dict] = []

    for cand in generated(cache, role):
        if len(picked) >= want:
            break
        picked.append(cand)

    for q in queries:
        if len(picked) >= want:
            break
        try:
            cands = pexels(q, shape)
        except RuntimeError:
            raise
        except Exception as e:
            print(f"    ! search failed for {q!r}: {str(e)[:60]}")
            continue
        with cf.ThreadPoolExecutor(8) as ex:
            results = list(ex.map(lambda c: (c, *check(c["url"])), cands))
        # Relevance first, weight second. Sorting the whole result set by size
        # picks light-but-wrong images — a mossy-shingle close-up instead of a
        # crew replacing a roof. So keep Pexels' relevance order, take the top
        # of it, and let file size decide only within that shortlist.
        passing = [(c, s) for c, ok, _why, s in results
                   if ok and c["url"] not in taken]
        shortlist = passing[:max(want * 3, RELEVANCE_POOL)]
        shortlist.sort(key=lambda t: t[1])
        passing = shortlist + passing[len(shortlist):]
        for cand, size in passing:
            if len(picked) >= want:
                break
            taken.add(cand["url"])
            cand["query"] = q
            cand["bytes"] = size
            picked.append(cand)
    return picked


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("intake")
    ap.add_argument("--preset", help="presets/<name>.json for search terms")
    ap.add_argument("--write", action="store_true", help="update the intake file")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--gallery", type=int, default=6)
    ap.add_argument("--terms", help="explicit search phrases, role=phrase;role=phrase (roles: hero, team, about, service, background, gallery). Overrides the preset.")
    ap.add_argument("--max-mb", type=float, default=6.0,
                    help="skip candidates heavier than this (default 6)")
    a = ap.parse_args()

    global MAX_BYTES
    MAX_BYTES = int(a.max_mb * 1_000_000)

    intake_path = Path(a.intake)
    intake = json.loads(intake_path.read_text(encoding="utf-8-sig"))
    cache = intake_path.parent / "assets"
    brand = intake.setdefault("brand", {})
    biz = intake.get("business", {})

    preset = {}
    if a.preset:
        p = Path("presets") / f"{a.preset}.json"
        if p.exists():
            preset = json.loads(p.read_text(encoding="utf-8-sig"))

    terms = preset.get("image_search", []) or [biz.get("type", "contractor")]
    trade = biz.get("type", "contractor")

    # One search phrase per role. Roles differ in what they must show, so a
    # single query for the whole site is what produces interchangeable stock.
    plan = {
        "hero":       ([f"{trade} worker portrait", f"{trade} technician"], 1),
        "team":       ([f"{trade} team", f"two {trade} workers"], 1),
        "about":      ([f"{trade} working", terms[0] if terms else trade], 1),
        "service":    ([terms[1] if len(terms) > 1 else trade], 1),
        "background": ([f"{trade} site", terms[0] if terms else trade], 1),
        "gallery":    (terms or [trade], a.gallery),
    }
    if a.terms:
        for pair in a.terms.split(";"):
            if "=" not in pair:
                continue
            role, phrase = pair.split("=", 1)
            role, phrase = role.strip(), phrase.strip()
            if role in plan:
                plan[role] = ([q.strip() for q in phrase.split("|")], plan[role][1])

    print(f"resolving images for {biz.get('name','?')}  (trade: {trade})\n")
    taken = {i["url"] for i in brand.get("images", []) if i.get("url")}
    existing_roles = {i.get("role") for i in brand.get("images", [])}
    resolved: list[dict] = []

    for role, (queries, want) in plan.items():
        have = sum(1 for i in brand.get("images", []) if i.get("role") == role)
        need = max(0, want - have)
        if not need:
            print(f"  {role:<11} {have} already supplied - keeping")
            continue
        try:
            got = resolve_slot(role, queries, need, cache, taken)
        except RuntimeError as e:
            print(f"\n{e}\n")
            print("Slots still needing a photo:")
            for r, (_, wnt) in plan.items():
                h = sum(1 for i in brand.get("images", []) if i.get("role") == r)
                if h < wnt:
                    print(f"  {r:<11} needs {wnt - h}")
            sys.exit(1)
        print(f"  {role:<11} found {len(got)}/{need}")
        for g in got:
            mb = g.get("bytes", 0) / 1e6
            print(f"      {g['url'][:66]}  {mb:.1f} MB")
            if g.get("alt"):
                print(f"        alt: {g['alt'][:70]}")
            resolved.append({
                "url": g["url"],
                "role": role,
                "subject": g.get("alt") or f"{trade} work",
                "_source": g.get("source"),
                "_credit": g.get("credit"),
            })

    print(f"\n{len(resolved)} new image(s) resolved")
    if not resolved:
        return

    if a.write and not a.dry_run:
        brand.setdefault("images", []).extend(
            {k: v for k, v in r.items() if not k.startswith("_")}
            for r in resolved)
        intake_path.write_text(json.dumps(intake, indent=2, ensure_ascii=False),
                               encoding="utf-8")
        print(f"written -> {intake_path}")
        credits = {r["_credit"] for r in resolved if r.get("_credit")}
        if credits:
            (intake_path.parent / "IMAGE-CREDITS.txt").write_text(
                "Stock photography via Pexels (pexels.com/license).\n"
                "Photographers: " + ", ".join(sorted(credits)) + "\n",
                encoding="utf-8")
            print("credits  -> IMAGE-CREDITS.txt")
    else:
        print("(dry run - nothing written; pass --write to apply)")


if __name__ == "__main__":
    main()
