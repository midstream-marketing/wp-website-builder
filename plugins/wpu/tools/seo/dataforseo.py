#!/usr/bin/env python3
"""DataForSEO client for WP Ultimate Build. Standard library only.

    python tools/seo/dataforseo.py overview  "roof repair" "roof replacement" --loc "Austin,Texas,United States"
    python tools/seo/dataforseo.py ideas     "roof repair" --limit 100
    python tools/seo/dataforseo.py serp      "roof repair austin" --depth 20
    python tools/seo/dataforseo.py ranked    competitor.com --limit 200
    python tools/seo/dataforseo.py gap       competitor.com --mine clientsite.com --limit 300
    python tools/seo/dataforseo.py score                     # scores sites/<slug>/seo/keywords.json in place
    python tools/seo/dataforseo.py locations "Austin"        # find the exact location_name

Everything lands in sites/<slug>/seo/ (keywords.json, serp/<kw>.json, ranked/<domain>.json).
Results are cached for 7 days in sites/<slug>/seo/cache/ so re-running costs nothing.

Rules (from SEO Growth OS, kept):
  - No key set => exits non-zero with a clear message. It never returns fake data.
  - Missing metrics stay null. They are never coerced to 0.
  - Every call prints its DataForSEO cost; --budget (USD, default 2.00 per run) stops the run
    before a call that would go over it.

Credentials: scripts/wpu-secret.ps1 set global dataforseo_login / dataforseo_password
(or WPU_SECRET_GLOBAL_DATAFORSEO_LOGIN / _PASSWORD in the environment).
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _wpu import site_dir, site_cfg, secret, write_json  # noqa: E402
from seo.keyword_score import KeywordScoreInput, score_keyword  # noqa: E402

API = os.environ.get("WPU_DATAFORSEO_API", "https://api.dataforseo.com/v3/")  # override only for tests
CACHE_DAYS = 7
SPENT = {"usd": 0.0}


class Budget(Exception):
    pass


def auth_header() -> str:
    login = secret("global", "dataforseo_login")
    pw = secret("global", "dataforseo_password")
    if not (login and pw):
        sys.exit("DataForSEO login not set. In your own terminal run:\n"
                 "  powershell -File scripts/wpu-secret.ps1 set global dataforseo_login\n"
                 "  powershell -File scripts/wpu-secret.ps1 set global dataforseo_password")
    return "Basic " + base64.b64encode(f"{login}:{pw}".encode()).decode()


def call(endpoint: str, payload: list, out_dir: Path, budget: float, est: float) -> dict:
    """POST one task. Cached by endpoint+payload. est = worst-case cost in USD, checked before calling."""
    key = hashlib.sha256((endpoint + json.dumps(payload, sort_keys=True)).encode()).hexdigest()[:24]
    cache = out_dir / "cache" / f"{key}.json"
    if cache.exists() and (time.time() - cache.stat().st_mtime) < CACHE_DAYS * 86400:
        print(f"  [cache] {endpoint}", file=sys.stderr)
        return json.loads(cache.read_text(encoding="utf-8"))

    if SPENT["usd"] + est > budget:
        raise Budget(f"stopping: this call could cost ~${est:.3f} and ${SPENT['usd']:.3f} of the ${budget:.2f} budget is spent (raise --budget)")

    req = urllib.request.Request(API + endpoint, data=json.dumps(payload).encode(), method="POST",
                                 headers={"Authorization": auth_header(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        sys.exit(f"DataForSEO HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}")
    except urllib.error.URLError as e:
        sys.exit(f"Could not reach DataForSEO: {e.reason}")

    if data.get("status_code") != 20000:
        sys.exit(f"DataForSEO error {data.get('status_code')}: {data.get('status_message')}")
    task = (data.get("tasks") or [{}])[0]
    if task.get("status_code") != 20000:
        sys.exit(f"DataForSEO task error {task.get('status_code')}: {task.get('status_message')}")

    cost = float(data.get("cost") or 0)
    SPENT["usd"] += cost
    print(f"  ${cost:.4f}  {endpoint}   (run total ${SPENT['usd']:.4f})", file=sys.stderr)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(data), encoding="utf-8")
    return data


def result(data: dict) -> list:
    return ((data.get("tasks") or [{}])[0].get("result")) or []


def loc_lang(args, cfg):
    seo = cfg.get("seo", {})
    return args.loc or seo.get("location") or "United States", args.lang or seo.get("language") or "en"


def kw_row(kw: str, info: dict, props: dict, intent: dict | None, fetched: str) -> dict:
    """One keyword, every metric nullable."""
    return {
        "keyword": kw,
        "search_volume": info.get("search_volume"),
        "cpc": info.get("cpc"),
        "competition": info.get("competition"),
        "difficulty": props.get("keyword_difficulty"),
        "intent": (intent or {}).get("main_intent"),
        "secondary_intents": (intent or {}).get("foreign_intent"),
        "monthly_searches": info.get("monthly_searches"),
        "provider": "dataforseo",
        "fetched_at": fetched,
    }


def merge_keywords(out_dir: Path, rows: list) -> Path:
    path = out_dir / "keywords.json"
    have = {}
    if path.exists():
        for r in json.loads(path.read_text(encoding="utf-8")).get("keywords", []):
            have[r["keyword"].lower()] = r
    for r in rows:
        old = have.get(r["keyword"].lower(), {})
        # keep the strategist's own fields (relevance, cluster, page) when metrics refresh
        keep = {k: old[k] for k in ("businessRelevance", "cluster", "target_page", "strategic") if k in old}
        have[r["keyword"].lower()] = {**r, **keep}
    data = {"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "keywords": sorted(have.values(), key=lambda r: -(r.get("search_volume") or 0))}
    return write_json(path, data)


def cmd_overview(args, cfg, out_dir):
    loc, lang = loc_lang(args, cfg)
    rows, now = [], datetime.now(timezone.utc).isoformat(timespec="seconds")
    for i in range(0, len(args.terms), 700):
        chunk = args.terms[i:i + 700]
        d = call("dataforseo_labs/google/keyword_overview/live",
                 [{"keywords": chunk, "location_name": loc, "language_code": lang, "include_serp_info": False}],
                 out_dir, args.budget, est=0.01 + 0.0001 * len(chunk))
        for res in result(d):
            for it in res.get("items") or []:
                rows.append(kw_row(it["keyword"], it.get("keyword_info") or {}, it.get("keyword_properties") or {},
                                   it.get("search_intent_info"), now))
    found = {r["keyword"].lower() for r in rows}
    for t in args.terms:
        if t.lower() not in found:   # no data is a row with nulls, not a missing row
            rows.append(kw_row(t, {}, {}, None, now))
    print(merge_keywords(out_dir, rows))


def cmd_ideas(args, cfg, out_dir):
    loc, lang = loc_lang(args, cfg)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    d = call("dataforseo_labs/google/keyword_ideas/live",
             [{"keywords": args.terms[:200], "location_name": loc, "language_code": lang, "limit": args.limit,
               "include_serp_info": False}],
             out_dir, args.budget, est=0.01 + 0.0001 * args.limit)
    rows = []
    for res in result(d):
        for it in res.get("items") or []:
            rows.append(kw_row(it["keyword"], it.get("keyword_info") or {}, it.get("keyword_properties") or {},
                               it.get("search_intent_info"), now))
    print(f"{len(rows)} ideas")
    print(merge_keywords(out_dir, rows))


def cmd_serp(args, cfg, out_dir):
    loc, lang = loc_lang(args, cfg)
    for kw in args.terms:
        d = call("serp/google/organic/live/advanced",
                 [{"keyword": kw, "location_name": loc, "language_code": lang, "device": args.device, "depth": args.depth}],
                 out_dir, args.budget, est=0.004 * max(1, args.depth // 10))
        res = (result(d) or [{}])[0]
        organic, features = [], []
        for it in res.get("items") or []:
            t = it.get("type")
            if t == "organic":
                organic.append({"position": it.get("rank_absolute"), "url": it.get("url"), "domain": it.get("domain"),
                                "title": it.get("title"), "description": it.get("description")})
            elif t and t not in features:
                features.append(t)
        safe = "".join(c if c.isalnum() else "_" for c in kw)[:80]
        p = write_json(out_dir / "serp" / f"{safe}.json",
                       {"keyword": kw, "location": loc, "device": args.device,
                        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        "features": features, "organic": organic})
        print(f"{kw}: {len(organic)} results, features: {', '.join(features) or 'none'}  -> {p}")


def ranked(domain, args, loc, lang, out_dir):
    d = call("dataforseo_labs/google/ranked_keywords/live",
             [{"target": domain, "location_name": loc, "language_code": lang, "limit": args.limit,
               "order_by": ["keyword_data.keyword_info.search_volume,desc"]}],
             out_dir, args.budget, est=0.01 + 0.0001 * args.limit)
    rows = []
    for res in result(d):
        for it in res.get("items") or []:
            kd = it.get("keyword_data") or {}
            se = (it.get("ranked_serp_element") or {}).get("serp_item") or {}
            rows.append({"keyword": kd.get("keyword"), "position": se.get("rank_absolute"), "url": se.get("url"),
                         "search_volume": (kd.get("keyword_info") or {}).get("search_volume"),
                         "difficulty": (kd.get("keyword_properties") or {}).get("keyword_difficulty"),
                         "intent": (kd.get("search_intent_info") or {}).get("main_intent")})
    write_json(out_dir / "ranked" / f"{domain}.json", {"domain": domain, "keywords": rows})
    return rows


def cmd_ranked(args, cfg, out_dir):
    loc, lang = loc_lang(args, cfg)
    for dom in args.terms:
        rows = ranked(dom, args, loc, lang, out_dir)
        print(f"{dom}: {len(rows)} ranked keywords -> {out_dir / 'ranked' / (dom + '.json')}")


def cmd_gap(args, cfg, out_dir):
    loc, lang = loc_lang(args, cfg)
    mine = args.mine or (cfg.get("baseUrl", "").split("//")[-1].split("/")[0])
    if not mine:
        sys.exit("--mine <domain> needed (no baseUrl in site.json)")
    have = {r["keyword"] for r in ranked(mine, args, loc, lang, out_dir)}
    gap = {}
    for dom in args.terms:
        for r in ranked(dom, args, loc, lang, out_dir):
            if r["keyword"] and r["keyword"] not in have and (r["position"] or 99) <= 20:
                g = gap.setdefault(r["keyword"], {**r, "competitors": []})
                g["competitors"].append({"domain": dom, "position": r["position"], "url": r["url"]})
    rows = sorted(gap.values(), key=lambda r: (-len(r["competitors"]), -(r["search_volume"] or 0)))
    p = write_json(out_dir / "gap.json", {"mine": mine, "competitors": args.terms, "keywords": rows})
    print(f"{len(rows)} keywords competitors rank top-20 for and {mine} does not -> {p}")


def cmd_score(args, cfg, out_dir):
    path = out_dir / "keywords.json"
    if not path.exists():
        sys.exit(f"{path} not found - run overview or ideas first")
    data = json.loads(path.read_text(encoding="utf-8"))
    site_type = cfg.get("seo", {}).get("site_type", "local_service")
    now = datetime.now(timezone.utc)
    for r in data["keywords"]:
        age = None
        if r.get("fetched_at"):
            age = (now - datetime.fromisoformat(r["fetched_at"])).days
        intents = ",".join(i for i in [r.get("intent"), *(r.get("secondary_intents") or [])] if i) or None
        r["score"] = score_keyword(KeywordScoreInput(
            searchVolume=r.get("search_volume"), difficulty=r.get("difficulty"), provider="dataforseo",
            metricAgeDays=age, intent=intents, businessRelevance=r.get("businessRelevance"), cpc=r.get("cpc"),
            strategicCluster=r.get("strategic"), siteType=site_type))
    # Rank by opportunity, discounted by how much of it is backed by data: a keyword
    # with no volume data should not outrank a measured one on the strength of a guess.
    def rank(r):
        s = r.get("score") or {}
        return -((s.get("score") or 0) * (0.5 + 0.5 * (s.get("confidence") or 0)))
    data["keywords"].sort(key=rank)
    write_json(path, data)
    for r in data["keywords"][:25]:
        s = r["score"]
        print(f"{(s['score'] if s['score'] is not None else '-'):>5}  conf {s['confidence']:.2f}  "
              f"vol {r.get('search_volume') if r.get('search_volume') is not None else '-':>6}  "
              f"kd {r.get('difficulty') if r.get('difficulty') is not None else '-':>4}  {r['keyword']}")


def cmd_locations(args, cfg, out_dir):
    d = call("dataforseo_labs/locations_and_languages", [], out_dir, args.budget, est=0)
    q = " ".join(args.terms).lower()
    for loc in result(d):
        if q in (loc.get("location_name") or "").lower():
            print(loc.get("location_name"), "|", ", ".join(l.get("language_code", "") for l in loc.get("available_languages") or []))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["overview", "ideas", "serp", "ranked", "gap", "score", "locations"])
    ap.add_argument("terms", nargs="*")
    ap.add_argument("--loc", help="location_name, e.g. 'Austin,Texas,United States' (default: site.json seo.location)")
    ap.add_argument("--lang", help="language_code (default: site.json seo.language or en)")
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--depth", type=int, default=20)
    ap.add_argument("--device", default="mobile", choices=["mobile", "desktop"])
    ap.add_argument("--mine", help="the client's domain for gap analysis")
    ap.add_argument("--budget", type=float, default=2.0, help="max USD this run may spend (default 2.00)")
    args = ap.parse_args()

    cfg = site_cfg()
    out_dir = site_dir() / "seo"
    if args.cmd not in ("score", "locations") and not args.terms:
        sys.exit(f"{args.cmd} needs at least one keyword or domain")
    try:
        globals()["cmd_" + args.cmd](args, cfg, out_dir)
    except Budget as b:
        sys.exit(str(b))
    if SPENT["usd"]:
        print(f"DataForSEO spend this run: ${SPENT['usd']:.4f}", file=sys.stderr)


if __name__ == "__main__":
    main()
