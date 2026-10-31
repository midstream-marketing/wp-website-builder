#!/usr/bin/env python3
"""check_fidelity.py — does the composed IR actually contain the reference's
visual devices?

    python tools/check_fidelity.py clients/medlou-health

Reads `design-spec.json` (the device inventory) and `ir.json` (what was
actually composed) from the client directory, and fails when a required device
has no satisfying block, or when a blocklisted fallback has crept in.

This exists because the forge measures JSON validity and copy depth and
nothing at all about whether the output resembles the design the client sent.
Everything the pipeline measures comes out right; everything it does not
measure drifts. Three builds in a row were rejected for the same reason —
section order matched, devices missing — so devices became a measured thing.

Exit codes: 0 pass, 1 fidelity failure, 2 usage/missing files.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def blocks_in(ir: dict) -> set[str]:
    """Every block name used anywhere in the IR."""
    out: set[str] = set()
    for page in ir.get("pages", []):
        for blk in page.get("blocks", []):
            name = blk.get("block")
            if name:
                out.add(name)
    return out


SERIFS = {"newsreader", "fraunces", "lora", "playfair display", "instrument serif",
          "source serif 4", "eb garamond", "libre baskerville", "crimson pro",
          "dm serif display", "cormorant garamond", "spectral", "bitter"}


def global_check(name: str, intake: dict, ir: dict | None = None
                 ) -> tuple[bool, str]:
    """Kit-level devices — type, palette, imagery — are not blocks, so they
    are checked against intake.json and the composed IR rather than against
    a block name."""
    fonts = (intake.get("brand", {}) or {}).get("fonts", {}) or {}
    if name == "heading_font_serif":
        h = str(fonts.get("heading", "")).strip()
        return h.lower() in SERIFS, f"heading font is '{h or '(unset)'}'"
    if name == "heading_body_contrast":
        h, b2 = str(fonts.get("heading", "")), str(fonts.get("body", ""))
        return bool(h) and bool(b2) and h != b2, f"heading '{h}' / body '{b2}'"
    if name == "no_stock_imagery":
        # Every image must come from the client's own domain. Written for
        # the Scottsdale build, where "all photography is theirs" is a real
        # selling point and a stock file slipping in would quietly undo it.
        domain = str((intake.get("business", {}) or {}).get("domain", ""))
        host = domain.split("//")[-1].strip("/").replace("www.", "")
        if not host:
            return False, "business.domain is not set, so origin is uncheckable"
        urls, foreign = set(), set()
        STOCK = ("pexels.", "unsplash.", "pixabay.", "shutterstock.",
                 "istockphoto.", "gettyimages.", "freepik.", "openverse.")
        def walk(n):
            if isinstance(n, dict):
                u = n.get("url")
                if isinstance(u, str) and ("/" in u) and (
                        u.startswith("http") or u.startswith("/wp-content")):
                    urls.add(u)
                    if any(s in u.lower() for s in STOCK):
                        foreign.add(u)
                    elif u.startswith("http") and host not in u:
                        foreign.add(u)
                for v in n.values():
                    walk(v)
            elif isinstance(n, list):
                for v in n:
                    walk(v)
        walk(ir or {})
        if foreign:
            return False, "%d image(s) not from %s: %s" % (
                len(foreign), host, sorted(foreign)[0])
        return True, f"all {len(urls)} image URLs are on {host}"
    if name == "motion_reveal":
        # Entrance animation is a compile stage (motion.py), not a block, so
        # the device is "the IR opted in". Written for Lakes Construction,
        # whose brief lists animations as a required improvement.
        preset = ((ir or {}).get("motion") or {}).get("preset")
        return preset in ("reveal", "fade"), f"motion preset is {preset!r}"
    return False, f"unknown global_check '{name}'"


def load(path: Path, what: str) -> dict:
    if not path.exists():
        sys.exit(f"missing {what}: {path}\n"
                 f"  design-spec.json is written BEFORE build_ir.py — see the "
                 f"design-fidelity skill, step 1.")
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        sys.exit(f"{path} is not valid JSON: {e}")


def main() -> int:
    if len(sys.argv) != 2:
        sys.exit(__doc__)

    root = Path(sys.argv[1])
    spec = load(root / "design-spec.json", "design spec")
    ir = load(root / "ir.json", "IR (run build_ir.py first)")
    intake = load(root / "intake.json", "intake")

    used = blocks_in(ir)
    devices = spec.get("devices", [])
    if not devices:
        sys.exit("design-spec.json lists no devices. An empty inventory is not "
                 "a pass — it means step 1 was skipped.")

    mode = spec.get("mode", "reference")
    print(f"reference : {spec.get('reference', '(unnamed)')}")
    print(f"mode      : {mode}")
    print(f"blocks    : {len(used)} distinct in IR")
    print()

    missing, banned, deferred, ok = [], [], [], []

    for d in devices:
        did = d.get("id", "(unnamed)")
        status = d.get("status", "required")
        satisfied_by = d.get("satisfied_by", [])

        # A fallback the build was previously tempted by. Its presence is a
        # failure even if the required block is also there, because it means
        # the substitution happened somewhere.
        for bad in d.get("never", []):
            if bad in used:
                banned.append((did, bad, d.get("never_reason", "")))

        if status == "deferred":
            deferred.append(did)
            continue

        # Kit-level device (type scale, palette) rather than a block.
        if satisfied_by == ["*global*"] or d.get("global_check"):
            gc = d.get("global_check")
            if not gc:
                missing.append((did, d.get("device", ""),
                                "global device needs a 'global_check' field"))
                continue
            passed, detail = global_check(gc, intake, ir)
            (ok.append((did, status)) if passed
             else missing.append((did, d.get("device", ""), detail)))
            continue

        if not satisfied_by:
            missing.append((did, d.get("device", ""), "no satisfied_by listed"))
            continue

        if any(b in used for b in satisfied_by):
            ok.append((did, status))
        else:
            missing.append((did, d.get("device", ""),
                            "none of " + ", ".join(satisfied_by)))

    for did, status in ok:
        tag = "ok" if status == "required" else "ok (substituted)"
        print(f"  {tag:18} {did}")
    for did in deferred:
        print(f"  {'deferred':18} {did}")
    for did, dev, why in missing:
        print(f"  {'MISSING':18} {did} — {dev}")
        print(f"  {'':18}   {why}")
    for did, bad, why in banned:
        print(f"  {'BANNED BLOCK':18} {did} — '{bad}' is in the IR")
        if why:
            print(f"  {'':18}   {why}")

    total = len(ok) + len(missing)
    print()
    print(f"{len(ok)}/{total} required devices present"
          + (f", {len(deferred)} deferred" if deferred else ""))

    if missing or banned:
        print()
        print("FIDELITY FAIL — the build is not finished.")
        print("Write the missing factories (design-fidelity skill, step 3).")
        print("Substituting the nearest existing block is what this gate exists")
        print("to catch, and documenting the gap in the README is not a fix.")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
