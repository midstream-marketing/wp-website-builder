"""
reference.py — make a design reference an input to the build.

`analyse_reference.py` has always been able to read a reference site or
screenshot and report its palette, type and rhythm. Nothing consumed that
report: it was printed, a person read it, and typed four hex values into an
intake by hand. Every measurement that was not retyped was lost, and nothing
afterwards checked the built kit against the thing it was supposed to match —
so "the template doesn't follow the reference" had no build step that could
catch it.

This module closes that loop:

  fold_profile()  fills the gaps in intake.brand from the reference, without
                  ever overriding an answer the client actually gave.
  conformance()   reports, per token, whether the kit took the reference's
                  value, the client's, or a stock default — so a deviation is
                  something you decided rather than something you discover on
                  the rendered page.

The client always wins. A reference is evidence about intent, not authority
over the brand: when a client states their own logo colour, that is the brand
and the reference is wrong. Making that precedence explicit here is what keeps
"use X as a reference" and "match X" from being the same build.
"""
from __future__ import annotations

import json
from pathlib import Path

from .tokens import DEFAULTS, contrast

# Faces that appear in a stylesheet but are not the design's type. Icon fonts,
# system stacks and Elementor's own defaults all show up in a scrape.
_NOT_TYPE = {
    "inherit", "initial", "sans-serif", "serif", "monospace", "system-ui",
    "-apple-system", "blinkmacsystemfont", "segoe ui", "helvetica", "arial",
    "roboto", "times new roman", "georgia", "courier new", "eicons",
    "font awesome 5 free", "font awesome 5 brands", "fontawesome",
}

TRACKED = ("primary", "secondary", "accent", "text")


def load_profile(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def _hue(hexcolor: str) -> float:
    h = hexcolor.lstrip("#")[:6]
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    mx, mn = max(r, g, b), min(r, g, b)
    if mx == mn:
        return 0.0
    d = mx - mn
    if mx == r:
        return (60 * ((g - b) / d) + 360) % 360
    if mx == g:
        return 60 * ((b - r) / d) + 120
    return 60 * ((r - g) / d) + 240


def palette(profile: dict) -> dict:
    """Best guess at primary / secondary / accent from a profile.

    A URL profile states its colours, so it is preferred. A screenshot only
    measures them — coverage is not role, and compression shifts hue — so it
    is a fallback rather than a second opinion.
    """
    css = profile.get("css") or {}
    brand = [c.upper() for c in (css.get("brand_colours") or [])]
    darks = []
    if not brand:
        px = profile.get("pixels") or {}
        brand = [s["hex"] for s in (px.get("brand_candidates") or [])]
        darks = [s["hex"] for s in (px.get("dark_grounds") or [])]
    if not brand:
        return {}

    out = {"primary": brand[0]}
    # The accent is the first colour far enough round the wheel to read as a
    # different colour rather than a shade of the primary.
    for c in brand[1:]:
        if min(abs(_hue(c) - _hue(brand[0])),
               360 - abs(_hue(c) - _hue(brand[0]))) > 40:
            out["accent"] = c
            break
    if darks:
        out["secondary"] = darks[0]
    return out


def fonts(profile: dict) -> dict:
    """Heading and body face from a profile, if it named any worth using."""
    css = profile.get("css") or {}
    named = []
    for f in (css.get("google_fonts") or []) + (css.get("fonts") or []):
        f = f.replace("+", " ").split(":")[0].strip()
        if f and f.lower() not in _NOT_TYPE and f not in named:
            named.append(f)
    if not named:
        return {}
    return {"heading": named[0], "body": named[1] if len(named) > 1 else named[0]}


def fold_profile(intake: dict, profile: dict) -> list[str]:
    """Fill the gaps in intake.brand from the reference. Returns a log.

    Mirrors how `apply_preset` folds a trade in: the profile sits underneath
    the client's own answers and is only ever consulted where the client left
    a field empty.
    """
    brand = intake.setdefault("brand", {})
    colors = brand.setdefault("colors", {})
    bfonts = brand.setdefault("fonts", {})
    notes = []

    for key, value in palette(profile).items():
        if colors.get(key):
            if colors[key].upper() != value.upper():
                notes.append(f"colors.{key}: kept client {colors[key]} "
                             f"(reference has {value})")
        else:
            colors[key] = value
            notes.append(f"colors.{key}: {value} from reference")

    for key, value in fonts(profile).items():
        if bfonts.get(key):
            if bfonts[key] != value:
                notes.append(f"fonts.{key}: kept client {bfonts[key]} "
                             f"(reference has {value})")
        else:
            bfonts[key] = value
            notes.append(f"fonts.{key}: {value} from reference")

    brand.setdefault("_reference", {})["source"] = \
        profile.get("url") or profile.get("image") or "profile"
    return notes


def conformance(intake: dict, profile: dict) -> list[str]:
    """Per-token account of where each brand value came from.

    Printed after the build so that a template diverging from its reference is
    a line in the build output, not a surprise on the page.
    """
    brand = intake.get("brand") or {}
    colors = brand.get("colors") or {}
    bfonts = brand.get("fonts") or {}
    ref_c, ref_f = palette(profile), fonts(profile)

    rows = []
    for key in TRACKED:
        rows.append((f"colors.{key}", colors.get(key), DEFAULTS[key],
                     ref_c.get(key)))
    for key in ("heading", "body"):
        rows.append((f"fonts.{key}", bfonts.get(key), DEFAULTS[f"{key}_font"],
                     ref_f.get(key)))

    out = []
    for name, given, default, want in rows:
        have = given or default
        if want and have.upper() == want.upper():
            note = "matches reference"
        elif want:
            note = f"DIVERGES — reference has {want}"
        else:
            note = ("client's own" if given else "stock default") +                    ", reference is silent"
        out.append(f"  {name:<18} {have:<22} ({note})")
    return out
