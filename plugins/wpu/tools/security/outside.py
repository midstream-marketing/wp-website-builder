#!/usr/bin/env python3
"""What an anonymous visitor (or a scanner) can learn about the site - checked from outside.

    python tools/security/outside.py            writes sites/<slug>/security/outside.json

Checks: HTTPS redirect, security headers, WordPress version leaks, REST user listing,
?author=N login enumeration, XML-RPC, exposed files (readme.html, debug.log, wp-config backups,
.git), directory listing on uploads. READ ONLY - plain GET/POST requests a browser could make.
Findings say what was seen, not what it means for a specific attack.
"""
from __future__ import annotations

import json
import re
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _wpu import site_cfg, site_dir, write_json  # noqa: E402

UA = "WP Ultimate Build security check (authorised)"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def fetch(url, method="GET", data=None, follow=True):
    opener = urllib.request.build_opener() if follow else urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(url, data=data, method=method, headers={"User-Agent": UA, "Content-Type": "text/xml"} if data else {"User-Agent": UA})
    try:
        with opener.open(req, timeout=30) as r:
            return r.status, dict(r.headers), r.read(200_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), (e.read(20_000) or b"").decode("utf-8", "replace")
    except (urllib.error.URLError, ssl.SSLError, TimeoutError) as e:
        return 0, {}, str(e)


def main():
    cfg = site_cfg()
    base = cfg["baseUrl"].rstrip("/")
    F = []

    def add(level, check, detail):
        F.append({"level": level, "check": check, "detail": detail})

    if base.startswith("https://"):
        st, hd, _ = fetch("http://" + base[8:] + "/", follow=False)
        loc = {k.lower(): v for k, v in hd.items()}.get("location", "")
        if st in (301, 308) and loc.startswith("https://"):
            add("ok", "https", "http:// redirects permanently to https://")
        else:
            add("high", "https", f"http:// answers {st} {('-> ' + loc) if loc else ''} instead of a 301 to https://")

    st, hd, body = fetch(base + "/")
    h = {k.lower(): v for k, v in hd.items()}
    for name, want in (("strict-transport-security", "high"), ("x-content-type-options", "med"),
                       ("referrer-policy", "low"), ("x-frame-options", "med"), ("content-security-policy", "low")):
        if name in h or (name == "x-frame-options" and "frame-ancestors" in h.get("content-security-policy", "")):
            add("ok", "header", f"{name} present")
        else:
            add(want if base.startswith("https") or name != "strict-transport-security" else "low", "header", f"{name} missing")
    m = re.search(r'<meta name="generator" content="WordPress ([\d.]+)', body)
    if m:
        add("low", "version", f"WordPress {m.group(1)} shown in the page <head>")
    if "x-powered-by" in h:
        add("low", "version", f"X-Powered-By: {h['x-powered-by']}")

    st, _, body = fetch(base + "/wp-json/wp/v2/users")
    if st == 200 and body.strip().startswith("["):
        try:
            users = [u.get("slug") for u in json.loads(body)]
        except ValueError:
            users = []
        add("med", "users", f"/wp-json/wp/v2/users lists {len(users)} user(s) to anyone: {', '.join(filter(None, users))[:120]}")
    else:
        add("ok", "users", f"/wp-json/wp/v2/users not public ({st})")

    st, hd, _ = fetch(base + "/?author=1", follow=False)
    loc = {k.lower(): v for k, v in hd.items()}.get("location", "")
    if "/author/" in loc:
        add("med", "users", f"?author=1 reveals a login name: {loc}")
    else:
        add("ok", "users", "?author=1 does not reveal a login name")

    st, _, body = fetch(base + "/xmlrpc.php", method="POST",
                        data=b"<?xml version='1.0'?><methodCall><methodName>system.listMethods</methodName></methodCall>")
    if st == 200 and "<methodResponse>" in body and "faultCode" not in body:
        add("med", "xmlrpc", "XML-RPC answers (used for brute-force login attempts; Jetpack and the mobile app need it)")
    else:
        add("ok", "xmlrpc", f"XML-RPC off or blocked ({st})")

    for path, level in (("/readme.html", "low"), ("/wp-content/debug.log", "high"), ("/debug.log", "high"),
                        ("/wp-config.php.bak", "high"), ("/wp-config.php~", "high"), ("/wp-config.bak", "high"),
                        ("/.git/HEAD", "high"), ("/.env", "high"), ("/wp-content/uploads/", "med")):
        st, _, body = fetch(base + path)
        if st == 200:
            if path.endswith("uploads/") and "Index of" not in body:
                continue
            if path == "/.env" and "=" not in body:
                continue
            add(level, "exposed", f"{path} is readable ({len(body)} bytes)")

    order = {"high": 0, "med": 1, "low": 2, "ok": 3}
    F.sort(key=lambda f: order[f["level"]])
    for f in F:
        print(f"  {f['level'].upper():<5} {f['check']:<8} {f['detail']}")
    out = write_json(site_dir() / "security" / "outside.json", {"site": base, "findings": F})
    print(f"-> {out}")
    return 1 if any(f["level"] == "high" for f in F) else 0


if __name__ == "__main__":
    sys.exit(main())
