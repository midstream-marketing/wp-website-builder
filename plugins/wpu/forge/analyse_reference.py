#!/usr/bin/env python3
"""analyse_reference.py — turn a reference site or screenshot into a design profile.

A client points at a site and says "like that". This reads the reference and
emits the measurable half of the answer — palette, type, radii, spacing — as a
profile the compiler consumes, so matching a reference stops being me editing
Python by eye and becomes an input to the build.

    python analyse_reference.py --url https://waterlooturf.com/
    python analyse_reference.py --image shot.png
    python analyse_reference.py --url https://x.com --image shot.png -o profiles/x.json

A URL yields exact values because the stylesheet states them. A screenshot
yields measured values, which is weaker: JPEG artefacts shift hues, and a
colour's share of the pixels is not its role in the design. Prefer the URL;
use the image to fill in what the CSS does not reveal.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import ssl
import sys
import urllib.parse
import urllib.request
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

# Colours that carry no brand information.
NEUTRAL = re.compile(r"^#(fff(fff)?|000(000)?|f{3,6}|0{3,6})$", re.I)


def fetch(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.read().decode("utf-8", "ignore")


def hexof(rgb) -> str:
    return "#%02X%02X%02X" % tuple(int(c) for c in rgb[:3])


def luminance(hexcolor: str) -> float:
    h = hexcolor.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4
    return .2126 * f(r) + .7152 * f(g) + .0722 * f(b)


def saturation(hexcolor: str) -> float:
    h = hexcolor.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    mx, mn = max(r, g, b), min(r, g, b)
    return 0.0 if mx == 0 else (mx - mn) / mx


# ───────────────────────────── from a URL ─────────────────────────────

def from_url(base: str) -> dict:
    html = fetch(base)
    css = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S | re.I))
    sheets = []
    for tag in re.findall(r'<link[^>]+rel=["\']stylesheet["\'][^>]*>', html, re.I):
        m = re.search(r'href=["\']([^"\']+)', tag)
        if m:
            sheets.append(urllib.parse.urljoin(base, m.group(1)))
    for href in sheets[:16]:
        try:
            css += "\n" + fetch(href)
        except Exception:
            pass

    hexes = collections.Counter(
        h.lower() for h in re.findall(r"#[0-9a-fA-F]{6}\b", css)
        if not NEUTRAL.match(h))
    brand = [h for h, _ in hexes.most_common(24)
             if saturation(h) > .18][:8]

    fams = collections.Counter()
    for f in re.findall(r"font-family\s*:\s*([^;{}]+)", css):
        first = f.split(",")[0].strip().strip('"\'')
        if first and not re.search(r"awesome|icon|var\(|inherit|eicons", first, re.I):
            fams[first] += 1

    radii = collections.Counter(
        int(x) for x in re.findall(r"border-radius\s*:\s*(\d{1,3})px", css)
        if 2 <= int(x) <= 60)
    pads = collections.Counter(
        int(x) for x in re.findall(r"padding(?:-top|-bottom)?\s*:\s*(\d{2,3})px", css)
        if 40 <= int(x) <= 200)

    return {
        "brand_colours": brand,
        "all_colours": [{"hex": h, "count": n} for h, n in hexes.most_common(12)],
        "fonts": [f for f, _ in fams.most_common(4)],
        "radius_common": [r for r, _ in radii.most_common(4)],
        "section_padding_common": [p for p, _ in pads.most_common(4)],
        "google_fonts": sorted(set(re.findall(
            r"fonts\.googleapis\.com/css2?\?family=([^&\"'>]+)", html)))[:6],
        "has_marquee": bool(re.search(r"@keyframes[^{]*(marquee|ticker|scroll)", css, re.I)),
        "has_clip_path": "clip-path" in css,
        "has_gradient_overlay": bool(re.search(r"linear-gradient\([^)]*rgba\(0,\s*0,\s*0", css)),
    }


# ─────────────────────────── from a screenshot ───────────────────────────

def from_image(path: str, k: int = 12) -> dict:
    from PIL import Image
    import numpy as np

    im = Image.open(path).convert("RGB")
    # Long marketing pages are mostly white body; sample the whole thing but
    # report coverage so a 2%-but-everywhere accent is still visible.
    im.thumbnail((520, 6000))
    arr = np.asarray(im).reshape(-1, 3).astype(float)

    # Bucket to group similar pixels, then report each bucket's *mean* rather
    # than its floor. Reporting the floor shifts every channel down by up to
    # the bucket width, which turned a real #1268A8 into #0060A8.
    q = (arr // 24 * 24).astype(int)
    keys, inverse, counts = np.unique(q, axis=0, return_inverse=True,
                                      return_counts=True)
    sums = np.zeros_like(keys, dtype=float)
    np.add.at(sums, inverse, arr)
    means = sums / counts[:, None]
    order = np.argsort(-counts)
    total = counts.sum()

    swatches = []
    for i in order[:60]:
        hx = hexof(means[i])
        pct = 100.0 * counts[i] / total
        swatches.append({"hex": hx, "pct": round(pct, 2),
                         "sat": round(saturation(hx), 2),
                         "lum": round(luminance(hx), 3)})

    brand = [s for s in swatches if s["sat"] > .25 and .03 < s["lum"] < .75][:6]
    darks = [s for s in swatches if s["lum"] < .08][:3]
    lights = [s for s in swatches if s["lum"] > .85][:3]
    return {
        "brand_candidates": brand,
        "dark_grounds": darks,
        "light_grounds": lights,
        "top_swatches": swatches[:14],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url")
    ap.add_argument("--image")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()
    if not (a.url or a.image):
        sys.exit("give --url and/or --image")

    prof = {}
    if a.url:
        prof["url"] = a.url
        prof["css"] = from_url(a.url)
    if a.image:
        prof["image"] = a.image
        prof["pixels"] = from_image(a.image)

    text = json.dumps(prof, indent=2)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"written -> {a.out}\n")
    print(text)


if __name__ == "__main__":
    main()
