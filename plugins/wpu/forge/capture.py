#!/usr/bin/env python3
"""capture.py — render an imported kit and screenshot it.

BUILD-PLAN step 9. Every other check in this pipeline is arithmetic on JSON;
this is the only one that looks at a rendered page. Desktop shots are written
with the filenames manifest.json already expects, so a captured run also fills
the kit's empty screenshots/ directory.

    python capture.py http://nexgen.local -o clients/nextgen-plumbing/out
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

WIDTHS = {"desktop": 1440, "tablet": 768, "mobile": 390}


def site_pages(base: str) -> list[tuple[str, str]]:
    """(slug, url) for every published page, home first."""
    req = urllib.request.Request(
        base.rstrip("/") + "/wp-json/wp/v2/pages?per_page=100&status=publish",
        headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode("utf-8"))
    pages = [(p["slug"], p["link"]) for p in data]
    pages.sort(key=lambda x: (x[1].rstrip("/") != base.rstrip("/"), x[0]))
    return pages


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base", help="site root, e.g. http://nexgen.local")
    ap.add_argument("-o", "--out", required=True, help="kit output dir")
    ap.add_argument("--only", help="comma-separated slugs")
    ap.add_argument("--full", action="store_true",
                    help="full-page shots (default: viewport only)")
    a = ap.parse_args()

    from playwright.sync_api import sync_playwright

    pages = site_pages(a.base)
    if a.only:
        keep = {s.strip() for s in a.only.split(",")}
        pages = [p for p in pages if p[0] in keep]
    if not pages:
        sys.exit("No published pages found.")

    shots = Path(a.out) / "screenshots"
    shots.mkdir(parents=True, exist_ok=True)
    print(f"{len(pages)} page(s) x {len(WIDTHS)} widths -> {shots}\n")

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for slug, url in pages:
            for label, w in WIDTHS.items():
                ctx = browser.new_context(
                    viewport={"width": w, "height": 1100},
                    device_scale_factor=1,
                    ignore_https_errors=True)
                page = ctx.new_page()
                try:
                    page.goto(url, wait_until="networkidle", timeout=60000)
                except Exception:
                    # networkidle can hang on sites with polling scripts
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)
                # Elementor lazy-loads backgrounds and images on scroll.
                page.evaluate("""() => new Promise(res => {
                    let y = 0;
                    const t = setInterval(() => {
                        window.scrollBy(0, 900); y += 900;
                        if (y >= document.body.scrollHeight) {
                            clearInterval(t); window.scrollTo(0, 0);
                            setTimeout(res, 400);
                        }
                    }, 90);
                })""")
                page.wait_for_timeout(700)

                name = slug if slug else "home"
                fn = shots / (f"{name}.jpg" if label == "desktop"
                              else f"{name}--{label}.jpg")
                page.screenshot(path=str(fn), full_page=a.full,
                                type="jpeg", quality=82)
                kb = fn.stat().st_size / 1024
                print(f"  {name:<26} {label:<8} {w:>5}px  {kb:>6.0f} KB")
                ctx.close()
        browser.close()

    print(f"\n{len(list(shots.glob('*.jpg')))} image(s) in {shots}")


if __name__ == "__main__":
    main()
