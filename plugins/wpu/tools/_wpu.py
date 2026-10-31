"""Shared helpers for the Python tools: which site, where its folder is, secrets.

Same rules as scripts/_site.ps1 and lib/lib.mjs:
  workspace = $WPU_WORKSPACE or the current folder
  site      = $WPU_SITE  ->  <workspace>/sites/<slug>/site.json
Secrets come from the member's encrypted store (scripts/wpu-secret.ps1) or from
WPU_SECRET_<SCOPE>_<NAME>. They are never printed.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = Path(os.environ.get("WPU_WORKSPACE") or os.getcwd())


def site_slug(required: bool = True) -> str | None:
    s = os.environ.get("WPU_SITE") or os.environ.get("WPSB_CONFIG") or os.environ.get("WPSD_CONFIG")
    if not s and required:
        sys.exit(f"No site selected. Set WPU_SITE=<slug> (folders in {WORKSPACE / 'sites'})")
    return re.sub(r"^config\.|\.json$", "", s).lower() if s else None


def site_dir(required: bool = True) -> Path | None:
    slug = site_slug(required)
    if not slug:
        return None
    d = WORKSPACE / "sites" / slug
    if required and not (d / "site.json").exists():
        sys.exit(f"{d / 'site.json'} not found. Create the site with /wpu:new-site first.")
    return d


def site_cfg() -> dict:
    p = site_dir() / "site.json"
    return json.loads(p.read_text(encoding="utf-8-sig"))


def secret(scope: str, name: str) -> str | None:
    env = re.sub(r"[^A-Z0-9_]", "_", f"WPU_SECRET_{scope}_{name}".upper())
    if os.environ.get(env):
        return os.environ[env]
    if sys.platform != "win32":
        return None
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
             str(PLUGIN_ROOT / "scripts" / "wpu-secret.ps1"), "get", scope, name],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.returncode == 0 and r.stdout else None


def write_json(path: Path, data) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
