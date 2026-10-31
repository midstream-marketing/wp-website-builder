#!/usr/bin/env python3
"""cPanel access through cPanel's own API with an API TOKEN (never the cPanel password).

    python tools/hosting/cpanel.py check                    who/where, disk use, PHP version of the site
  Read:
    python tools/hosting/cpanel.py php                      PHP version per domain
    python tools/hosting/cpanel.py ls    [dir]              relative to the WordPress root (or /home/... absolute)
    python tools/hosting/cpanel.py tail  <file> [lines]
    python tools/hosting/cpanel.py get   <file> [local]
    python tools/hosting/cpanel.py logs  [lines]            error_log files and wp-content/debug.log
    python tools/hosting/cpanel.py backups                  host backups the account can see
    python tools/hosting/cpanel.py cron                     cron jobs (read-only)
  Write (DRY RUN unless the last word is "apply"; a copy is saved first):
    python tools/hosting/cpanel.py php-set <ea-phpXX> [domain]      e.g. php-set ea-php82
    python tools/hosting/cpanel.py put  <local-text-file> <remote>  text files up to 2 MB (PHP, .htaccess, .user.ini...)
    python tools/hosting/cpanel.py plugin-off <folder>     /  plugin-on <folder>
    python tools/hosting/cpanel.py theme-off  <folder>     /  theme-on  <folder>
    python tools/hosting/cpanel.py maintenance-off
    python tools/hosting/cpanel.py backup-now               full account backup into the home folder

Token: cPanel > Security > Manage API Tokens. One token per team member, named after them; revoke it there
when the job ends. The member saves it in their own terminal:  wpu-secret.ps1 set <slug> cpanel_token
Deleting files is not offered here - use sftp.py rm (one file, backed up) or the cPanel File Manager.
"""
from __future__ import annotations

import json
import os
import posixpath
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _hosting import (backup_path, dry, hosting_cfg, inside_root, local_download, log_action,  # noqa: E402
                      need_secret, redact, rel_to_root, split_apply)

TOOL = "cpanel"
MAX_PUT = 2 * 1024 * 1024


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """urllib would re-send the Authorization header (the token) to wherever a redirect points."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, f"redirect to {newurl} refused", headers, fp)


_OPENER = urllib.request.build_opener(_NoRedirect, urllib.request.HTTPSHandler(context=ssl.create_default_context()))


class CP:
    def __init__(self, c: dict):
        for k in ("host", "user"):
            if not c.get(k):
                sys.exit(f"site.json hosting.cpanel.{k} is empty.")
        self.c = c
        self.user = c["user"]
        self.base = f"https://{c['host']}:{int(c.get('port', 2083))}"
        test = os.environ.get("WPU_CPANEL_BASE", "")
        if test:
            # Test hook for a local mock only. Any other value could send the token to someone else's server.
            u = urllib.parse.urlparse(test)
            if u.hostname not in ("127.0.0.1", "localhost"):
                sys.exit("WPU_CPANEL_BASE is only for a local test server (127.0.0.1). Unset it.")
            self.base = test.rstrip("/")
        self.home = posixpath.normpath(c.get("home") or f"/home/{self.user}")
        self.root = posixpath.normpath(posixpath.join(self.home, c.get("wpRoot") or "public_html"))
        self.domain = c.get("domain") or ""
        self.token = need_secret("cpanel_token")

    def _call(self, url: str, params: dict, post: bool):
        data = urllib.parse.urlencode(params, doseq=True)
        req = urllib.request.Request(url if post else f"{url}?{data}", data=data.encode() if post else None,
                                     headers={"Authorization": f"cpanel {self.user}:{self.token}"})
        try:
            with _OPENER.open(req, timeout=120) as r:
                body = r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if 300 <= e.code < 400:
                sys.exit(f"cPanel answered with a redirect ({e.msg}). Not followed, so the token stays put. "
                         "Use the server hostname and port 2083 exactly as cPanel shows them.")
            if e.code in (401, 403):
                sys.exit("cPanel refused the token (HTTP %d). Check hosting.cpanel.user, and that the token "
                         "still exists in cPanel > Manage API Tokens." % e.code)
            sys.exit(f"cPanel HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}")
        except urllib.error.URLError as e:
            if "CERTIFICATE" in str(e).upper():
                sys.exit(f"TLS certificate check failed for {self.c['host']}. Use the server's HOSTNAME "
                         "(shown in cPanel's sidebar, e.g. server123.host.com), not an IP or the site domain.")
            sys.exit(f"Could not reach {self.base}: {e.reason}")
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            sys.exit("cPanel answered with a non-JSON page - usually a login page (wrong port/host) or a "
                     "security challenge.")

    def uapi(self, module: str, func: str, post: bool = False, **params):
        j = self._call(f"{self.base}/execute/{module}/{func}", params, post)
        r = j.get("result", j)  # /execute returns the result object itself; WHM wraps it in "result"
        if not r.get("status"):
            sys.exit(f"cPanel {module}::{func} failed: {'; '.join(r.get('errors') or ['no detail'])}")
        return r.get("data")

    def api2(self, module: str, func: str, **params):
        p = {"cpanel_jsonapi_user": self.user, "cpanel_jsonapi_apiversion": 2,
             "cpanel_jsonapi_module": module, "cpanel_jsonapi_func": func, **params}
        j = self._call(f"{self.base}/json-api/cpanel", p, True)
        r = j.get("cpanelresult") or {}
        if r.get("error") or not (r.get("event") or {}).get("result", 0):
            sys.exit(f"cPanel {module}::{func} failed: {r.get('error') or 'no detail'}")
        return r.get("data") or []

    # paths
    def rpath(self, p: str) -> str:
        return posixpath.normpath(p if p.startswith("/") else posixpath.join(self.root, p or "."))

    def read(self, full: str) -> str:
        d = self.uapi("Fileman", "get_file_content", dir=posixpath.dirname(full), file=posixpath.basename(full),
                      from_charset="_DETECT_", to_charset="UTF-8")
        return (d or {}).get("content", "")

    def exists(self, full: str) -> dict | None:
        for e in self.list(posixpath.dirname(full)):
            if e.get("file") == posixpath.basename(full):
                return e
        return None

    def list(self, d: str) -> list:
        data = self.uapi("Fileman", "list_files", dir=d, show_hidden=1, include_permissions=1)
        if isinstance(data, dict):  # newer servers split dirs and files
            return list(data.get("dirs") or []) + list(data.get("files") or [])
        return list(data or [])

    def backup(self, full: str) -> Path | None:
        e = self.exists(full)
        if not e or e.get("type") == "dir":
            return None
        dst = backup_path(rel_to_root(self.root, full))
        dst.write_text(self.read(full), encoding="utf-8")
        return dst

    def not_link(self, full: str) -> None:
        e = self.exists(full)
        if e and e.get("type") == "link":
            sys.exit(f"refused: {full} is a symlink. Change the file it points to directly, inside the root.")

    def rename(self, a: str, b: str) -> None:
        # API2 Fileman::fileop is the long-standing rename call and works on every cPanel version.
        self.api2("Fileman", "fileop", op="rename", sourcefiles=a, destfiles=b, doubledecode=0)


def human(n) -> str:
    try:
        n = float(n)
    except (TypeError, ValueError):
        return str(n)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def tail_text(text: str, n: int) -> None:
    for line in text.splitlines()[-n:]:
        print("  " + redact(line))


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(__doc__)
        return 2
    cmd = sys.argv[1].lower()
    args, apply = split_apply(sys.argv[2:])
    cp = CP(hosting_cfg("cpanel"))

    if cmd == "check":
        q = cp.uapi("Quota", "get_quota_info") or {}
        used = q.get("megabytes_used")
        limit = q.get("megabyte_limit")
        print(f"cPanel user {cp.user} on {cp.c['host']}")
        print(f"disk: {used} MB used of {limit or 'unlimited'} MB" if used is not None else "disk: (not reported)")
        e = cp.exists(posixpath.join(cp.root, "wp-config.php"))
        print(f"WordPress root {cp.root}: {'wp-config.php found' if e else 'NO wp-config.php here - check hosting.cpanel.wpRoot'}")
        show_php(cp)
        return 0

    if cmd == "php":
        show_php(cp)
        return 0

    if cmd == "ls":
        d = cp.rpath(args[0] if args else "")
        rows = sorted(cp.list(d), key=lambda e: str(e.get("file", "")).lower())
        print(f"{d}\n")
        for e in rows:
            kind = "d" if e.get("type") == "dir" else "-"
            print(f"  {kind} {str(e.get('nicemode', '')):>4} {human(e.get('size', 0)):>9}  {e.get('file')}")
        print(f"\n{len(rows)} entr{'y' if len(rows) == 1 else 'ies'}")
        return 0

    if cmd in ("tail", "get"):
        full = cp.rpath(args[0])
        text = cp.read(full)
        if cmd == "tail":
            n = int(args[1]) if len(args) > 1 else 60
            print(f"{full}  (last {n} lines)\n")
            tail_text(text, n)
        else:
            dst = local_download(args[1] if len(args) > 1 else full)  # never outside hosting/downloads
            dst.write_text(text, encoding="utf-8")
            print(f"{full}\n  -> {dst}")
        return 0

    if cmd == "logs":
        n = int(args[0]) if args else 40
        cands = [posixpath.join(cp.root, "error_log"), posixpath.join(cp.root, "wp-content/debug.log"),
                 posixpath.join(cp.root, "wp-admin/error_log")]
        shown = 0
        for c in cands:
            e = cp.exists(c)
            if e and e.get("type") != "dir":
                print(f"\n=== {c}  ({human(e.get('size', 0))})")
                tail_text(cp.read(c), n)
                shown += 1
        if not shown:
            print("No error_log or debug.log found. cPanel > Metrics > Errors shows the server's own error log.")
        return 0

    if cmd == "backups":
        data = cp.uapi("Backup", "list_backups") or []
        if not data:
            print("No host backups listed for this account (many hosts keep backups outside cPanel's view).")
        for b in data:
            print(f"  {b}")
        return 0

    if cmd == "cron":
        rows = cp.api2("Cron", "listcron")
        rows = [r for r in rows if r.get("command")]
        for r in rows:
            print(f"  {r.get('minute')} {r.get('hour')} {r.get('day')} {r.get('month')} {r.get('weekday')}  {r.get('command')}")
        print(f"\n{len(rows)} cron job(s)")
        return 0

    # ------------------------------------------------------------------- writes

    if cmd == "php-set":
        if not args:
            sys.exit("php-set <version> [domain]   e.g. php-set ea-php82   (see 'php' for what is installed)")
        version = args[0]
        vhost = args[1] if len(args) > 1 else cp.domain
        if not vhost:
            sys.exit("Which domain? Pass it, or set hosting.cpanel.domain in site.json.")
        cur = cp.uapi("LangPHP", "php_get_vhost_versions", vhost=vhost) or {}
        before = cur.get("version") if isinstance(cur, dict) else None
        if not apply:
            dry(f"{vhost}: PHP {before} -> {version}   (undo: php-set {before} {vhost} apply)")
            return 0
        cp.uapi("LangPHP", "php_set_vhost_versions", version=version, vhost=vhost)
        print(f"{vhost}: PHP {before} -> {version}\nUndo: python tools/hosting/cpanel.py php-set {before} {vhost} apply")
        log_action(TOOL, "php-set", {"vhost": vhost, "before": before, "after": version})
        return 0

    if cmd == "put":
        if len(args) < 2:
            sys.exit("put <local-text-file> <remote-path>")
        src, full = Path(args[0]), inside_root(cp.root, args[1])
        if not src.is_file():
            sys.exit(f"local file not found: {src}")
        raw = src.read_bytes()
        if len(raw) > MAX_PUT or b"\x00" in raw:
            sys.exit("cpanel.py put is for text files up to 2 MB. Use sftp.py for images, zips or big files.")
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            sys.exit("Not UTF-8 text. Use sftp.py put for this file.")
        text = text.lstrip("﻿")  # a BOM in front of <?php breaks redirects site-wide
        cp.not_link(full)
        old = cp.exists(full)
        if not apply:
            dry(f"write {src} ({human(len(raw))}) -> {full}" + (" (replaces it; a copy is kept)" if old else " (new file)"))
            return 0
        bak = cp.backup(full) if old else None
        cp.uapi("Fileman", "save_file_content", post=True, dir=posixpath.dirname(full),
                file=posixpath.basename(full), content=text, from_charset="UTF-8", to_charset="UTF-8", fallback=1)
        back = cp.read(full)
        if back.rstrip("\r\n") != text.rstrip("\r\n"):
            sys.exit(f"!! the saved file does not match what was sent. Previous version: {bak}")
        print(f"{src}\n  -> {full}  (verified)")
        if bak:
            print(f"  previous version saved: {bak}")
        log_action(TOOL, "put", {"path": full, "bytes": len(raw), "backup": str(bak) if bak else None})
        return 0

    if cmd in ("plugin-off", "plugin-on", "theme-off", "theme-on"):
        kind = "plugins" if cmd.startswith("plugin") else "themes"
        name = args[0].strip("/") if args else ""
        if not name or "/" in name or name.startswith("."):
            sys.exit(f"{cmd} <folder-name>")
        base = inside_root(cp.root, f"wp-content/{kind}")
        a, b = (f"{base}/{name}", f"{base}/{name}.wpu-off") if cmd.endswith("-off") else (f"{base}/{name}.wpu-off", f"{base}/{name}")
        if not cp.exists(a):
            sys.exit(f"{a} does not exist")
        cp.not_link(a)
        if cp.exists(b):
            sys.exit(f"{b} already exists")
        if not apply:
            dry(f"rename {a} -> {b}")
            return 0
        cp.rename(a, b)
        print(f"{a}\n  -> {b}")
        log_action(TOOL, cmd, {"from": a, "to": b})
        return 0

    if cmd == "maintenance-off":
        p = inside_root(cp.root, ".maintenance")
        if not cp.exists(p):
            print("No .maintenance file - the site is not stuck in maintenance mode.")
            return 0
        if not apply:
            dry(f"move {p} aside (a stuck update leaves it behind)")
            return 0
        cp.rename(p, p + ".wpu-off")
        print(f"{p} -> {p}.wpu-off")
        log_action(TOOL, "maintenance-off", {"path": p})
        return 0

    if cmd == "backup-now":
        if not apply:
            dry("start a full account backup into the cPanel home folder (counts toward disk quota; takes minutes)")
            return 0
        cp.uapi("Backup", "fullbackup_to_homedir")
        print("Full backup started. It appears in the home folder as backup-<date>_<user>.tar.gz when finished.\n"
              "Download it, then delete it from the server - a backup in the home folder uses the disk quota.")
        log_action(TOOL, "backup-now", {})
        return 0

    sys.exit(f"unknown command: {cmd}\n{__doc__}")


def show_php(cp: CP) -> None:
    data = cp.uapi("LangPHP", "php_get_vhost_versions") or []
    if isinstance(data, dict):
        data = [data]
    for v in data:
        print(f"  PHP {v.get('version')}  {v.get('vhost')}  ({v.get('documentroot')})"
              f"{'  [php-fpm]' if str(v.get('php_fpm')) == '1' else ''}")


if __name__ == "__main__":
    sys.exit(main())
