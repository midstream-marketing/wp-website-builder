#!/usr/bin/env python3
"""Pick Pexels photos that actually fit a warm-neutral brand.

Taking the first result gave a red gift box, a cold grey salon and a dark
barbershop - fine photographs, wrong palette. This collects every candidate on
the results page, downloads the small preview of each, and SCORES it against
the brand: low saturation, warm hue, mid-to-high brightness. Only the winner
is fetched at full size.

Pexels License: free for commercial use, no attribution required.
"""
from __future__ import annotations

import colorsys
import io
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
OUT = HERE / "stock2"
OUT.mkdir(exist_ok=True)

QUERIES = [
    ("massage", "massage therapist hands on back of client", "landscape"),
    ("styling", "woman hair blowout salon mirror stylist", "portrait"),
]

PREVIOUS = {"8070371", "3921392", "16571739", "14730864", "37240365", "6634828", "17640381", "7446657",
            "6168343", "19085994", "7901232", "6952333", "38167596",
            "9146381", "28743778"}

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/122 Safari/537.36")


def score(data: bytes, want: str):
    """Warm, desaturated and not too dark wins. Returns (score, w, h)."""
    try:
        im = Image.open(io.BytesIO(data)).convert("RGB")
    except Exception:
        return None
    w, h = im.size
    small = im.resize((48, 48), Image.LANCZOS)
    px = list(small.getdata())
    sat = val = warm = 0.0
    for r, g, b in px:
        hh, ss, vv = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        sat += ss
        val += vv
        # warm = hue in the red/orange/yellow band, or nearly neutral
        warm += 1.0 if (hh <= 0.13 or hh >= 0.93 or ss < 0.12) else 0.0
    n = len(px)
    sat /= n
    val /= n
    warm /= n
    s = warm * 2.2 - sat * 2.6 + (1 - abs(val - 0.62) * 2) * 1.1
    if want == "portrait" and h > w:
        s += 0.45
    if want == "landscape" and w > h:
        s += 0.45
    if min(w, h) < 900:
        s -= 1.5
    return (s, w, h, round(sat, 3), round(val, 3), round(warm, 3))


def pick(slug: str, query: str, want: str, used: set):
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1500, "height": 1200}, user_agent=UA)
        try:
            pg.goto("https://www.pexels.com/search/" + urllib.parse.quote(query) + "/",
                    wait_until="domcontentloaded", timeout=60000)
            pg.wait_for_timeout(3200)
            pg.mouse.wheel(0, 2200)
            pg.wait_for_timeout(2200)
            srcs = pg.eval_on_selector_all(
                "img", "els => els.map(e => e.src).filter(s => s && s.includes('images.pexels.com'))")
        except Exception as exc:
            print("  %-9s FAILED %s" % (slug, exc))
            b.close()
            return None
        b.close()

    seen, best = set(), None
    for src in srcs[:26]:
        m = re.search(r"/photos/(\d+)/", src)
        if not m:
            continue
        pid = m.group(1)
        if pid in seen or pid in used:
            continue
        seen.add(pid)
        prev = src.split("?")[0] + "?auto=compress&cs=tinysrgb&w=520"
        try:
            data = urllib.request.urlopen(
                urllib.request.Request(prev, headers={"User-Agent": UA}), timeout=45).read()
        except Exception:
            continue
        sc = score(data, want)
        if sc and (best is None or sc[0] > best[0][0]):
            best = (sc, pid, src)

    if not best:
        print("  %-9s nothing scored" % slug)
        return None
    sc, pid, src = best
    full = src.split("?")[0] + "?auto=compress&cs=tinysrgb&w=1800"
    data = urllib.request.urlopen(
        urllib.request.Request(full, headers={"User-Agent": UA}), timeout=90).read()
    (OUT / (slug + ".jpg")).write_bytes(data)
    used.add(pid)
    print("  %-9s photo %-9s score %.2f  sat %.2f val %.2f warm %.2f  %.0f KB"
          % (slug, pid, sc[0], sc[3], sc[4], sc[5], len(data) / 1024))
    return {"slug": slug, "query": query, "photo_id": pid,
            "page": "https://www.pexels.com/photo/" + pid + "/"}


def main():
    used, got = set(PREVIOUS), []
    for i, (slug, query, want) in enumerate(QUERIES):
        rec = pick(slug, query, want, used)
        if rec:
            got.append(rec)
        if i < len(QUERIES) - 1:
            time.sleep(22)
    (OUT / "credits.json").write_text(json.dumps(got, indent=1), encoding="utf-8")
    print("kept %d of %d" % (len(got), len(QUERIES)))


if __name__ == "__main__":
    main()
