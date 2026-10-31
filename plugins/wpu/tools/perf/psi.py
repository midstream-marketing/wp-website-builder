#!/usr/bin/env python3
"""PageSpeed Insights runs for the speed loop. Standard library only.

    python tools/perf/psi.py run <label> [/path ...]       mobile run of the site's perf pages (or the paths given)
    python tools/perf/psi.py run <label> --desktop
    python tools/perf/psi.py compare <before-label> <after-label>

Pages: site.json "perf_urls" (default: "/" plus the first url in "urls" that is not "/").
Each URL is run 3 times and the MEDIAN is kept - one lab run varies by 10-20 points.
Saved to sites/<slug>/perf/<label>.json. compare exits 2 when the after run is worse on
mobile LCP (+10%), CLS (+0.02) or TBT (+20%) on any page, so the loop knows to roll back.

Field data (real Chrome users, 28 days) is shown when Google has it; it does not move
within a day, so the loop judges changes on lab metrics and reports field data as context.

Key (optional, raises the quota): scripts/wpu-secret.ps1 set global pagespeed_key
"""
from __future__ import annotations

import json
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _wpu import site_cfg, site_dir, secret, write_json  # noqa: E402

API = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
LAB = {"lcp": "largest-contentful-paint", "cls": "cumulative-layout-shift", "tbt": "total-blocking-time",
       "fcp": "first-contentful-paint", "si": "speed-index", "ttfb": "server-response-time"}


def one(url: str, strategy: str) -> dict:
    q = {"url": url, "strategy": strategy, "category": "performance"}
    key = secret("global", "pagespeed_key")
    if key:
        q["key"] = key
    try:
        with urllib.request.urlopen(API + "?" + urllib.parse.urlencode(q), timeout=180) as r:
            d = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        sys.exit(f"PageSpeed HTTP {e.code} for {url}: {e.read().decode('utf-8', 'replace')[:300]}")
    lh = d["lighthouseResult"]
    a = lh["audits"]
    out = {"score": round((lh["categories"]["performance"]["score"] or 0) * 100)}
    for k, aid in LAB.items():
        out[k] = a.get(aid, {}).get("numericValue")
    opps = []
    for aid, au in a.items():
        sav = (au.get("details") or {}).get("overallSavingsMs")
        if au.get("details", {}).get("type") == "opportunity" and sav and sav > 100:
            opps.append({"id": aid, "title": au.get("title"), "savings_ms": round(sav)})
    out["opportunities"] = sorted(opps, key=lambda o: -o["savings_ms"])[:8]
    fld = (d.get("loadingExperience") or {}).get("metrics") or {}
    out["field"] = {k: (fld.get(m) or {}).get("percentile") for k, m in
                    (("lcp", "LARGEST_CONTENTFUL_PAINT_MS"), ("cls", "CUMULATIVE_LAYOUT_SHIFT_SCORE"),
                     ("inp", "INTERACTION_TO_NEXT_PAINT"))} if fld else None
    return out


def median_run(url: str, strategy: str, n: int = 3) -> dict:
    runs = []
    for i in range(n):
        runs.append(one(url, strategy))
        if i < n - 1:
            time.sleep(2)
    med = {}
    for k in ["score", *LAB]:
        vals = [r[k] for r in runs if r.get(k) is not None]
        med[k] = statistics.median(vals) if vals else None
    med["opportunities"] = runs[-1]["opportunities"]
    med["field"] = runs[-1]["field"]
    med["runs"] = n
    return med


def cmd_run(label: str, paths: list, desktop: bool):
    cfg = site_cfg()
    base = cfg["baseUrl"].rstrip("/")
    if not paths:
        paths = cfg.get("perf_urls") or ["/"] + [u for u in cfg.get("urls", []) if u != "/"][:1]
    strategy = "desktop" if desktop else "mobile"
    res = {"label": label, "strategy": strategy, "at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "pages": {}}
    for p in paths:
        url = p if p.startswith("http") else base + (p if p.startswith("/") else "/" + p)
        r = median_run(url, strategy)
        res["pages"][p] = r
        print(f"{p:<34} score {r['score']:>5}  LCP {fmt_ms(r['lcp'])}  CLS {r['cls'] if r['cls'] is not None else '-':<6}"
              f"  TBT {fmt_ms(r['tbt'])}  TTFB {fmt_ms(r['ttfb'])}")
        for o in r["opportunities"][:4]:
            print(f"      - {o['title']} (~{o['savings_ms']} ms)")
    out = write_json(site_dir() / "perf" / f"{label}.json", res)
    print(f"-> {out}")


def fmt_ms(v):
    return "-" if v is None else f"{v / 1000:.2f}s"


def cmd_compare(a: str, b: str) -> int:
    d = site_dir() / "perf"
    A = json.loads((d / f"{a}.json").read_text(encoding="utf-8"))
    B = json.loads((d / f"{b}.json").read_text(encoding="utf-8"))
    worse = []
    print(f"{'page':<30} {'metric':<6} {a:>12} {b:>12}  change")
    for p, ra in A["pages"].items():
        rb = B["pages"].get(p)
        if not rb:
            continue
        for m, limit in (("lcp", 1.10), ("cls", 0.02), ("tbt", 1.20), ("score", None)):
            va, vb = ra.get(m), rb.get(m)
            if va is None or vb is None:
                print(f"{p:<30} {m:<6} {'-':>12} {'-':>12}  no data")
                continue
            if m == "cls":
                bad = vb > va + limit
                ch = f"{vb - va:+.3f}"
            elif m == "score":
                bad = False
                ch = f"{vb - va:+.0f}"
            else:
                bad = va > 0 and vb > va * limit
                ch = f"{(vb - va) / va * 100:+.0f}%" if va else "n/a"
            if bad:
                worse.append(f"{p} {m}")
            print(f"{p:<30} {m:<6} {va:>12.3f} {vb:>12.3f}  {ch}{'   WORSE' if bad else ''}")
    if worse:
        print("\nWORSE on: " + ", ".join(worse) + "  -> roll this group back (scripts/rspeed.ps1 restore ...)")
        return 2
    print("\nNo regression beyond the thresholds. Keep it.")
    return 0


def main():
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == "run":
        desktop = "--desktop" in a
        cmd_run(a[1], [x for x in a[2:] if x != "--desktop"], desktop)
        return 0
    if len(a) == 3 and a[0] == "compare":
        return cmd_compare(a[1], a[2])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
