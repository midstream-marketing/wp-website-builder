"""
validator.py — the ten rules, all earned from real defects in shipped
commercial kits. Failures block the build; warnings don't.

The QA agent reads this report BEFORE it looks at a screenshot. Most
"the import looks broken" bugs are caught here, deterministically, for
free — no vision pass needed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .core import REGISTRY
from .tokens import token_ids

HEXID = re.compile(r"^[0-9a-f]{7,8}$")
GLOBAL_REF = re.compile(r"globals/(colors|typography)\?id=([\w-]+)")
TAG_NAME = re.compile(r'name="([^"]+)"')
RESP = re.compile(r"_(widescreen|laptop|tablet_extra|tablet|mobile_extra|mobile)$")

# Contract v2: element-scoped CSS is permitted, because clip-paths, gradient
# scrims and keyframes have no control equivalent. Hand-authored class names
# stay banned — they are the part that made CSS unmaintainable, since a class
# implies a stylesheet living somewhere outside the template.
BANNED_KEYS = {"_css_classes"}
CSS_KEYS = {"custom_css", "_custom_css"}
# Anything that could reach outside the element it is attached to.
CSS_FORBIDDEN = re.compile(
    r"@import|</?script|javascript:|expression\s*\(|url\s*\(\s*['\"]?\s*data:text/html",
    re.I)
ALLOWED_BP = {"tablet", "mobile"}

# Style controls that are legal on any widget but may not appear in the
# mined registry, because the reference kits routed them through globals.
STYLE_SUFFIXES = (
    "_color", "_typography", "_typography_typography", "_background",
    "_border_color", "_box_shadow", "_padding", "_margin", "_radius",
    "_spacing", "_size", "_width", "_height", "_align", "_gap",
)


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def err(self, rule, where, msg):
        self.errors.append(f"[{rule}] {where}: {msg}")

    def warn(self, rule, where, msg):
        self.warnings.append(f"[{rule}] {where}: {msg}")

    def text(self) -> str:
        lines = []
        if self.errors:
            lines.append(f"FAIL — {len(self.errors)} error(s)")
            lines += ["  " + e for e in self.errors]
        else:
            lines.append("PASS — 0 errors")
        if self.warnings:
            lines.append(f"{len(self.warnings)} warning(s)")
            lines += ["  " + w for w in self.warnings]
        return "\n".join(lines)


# Container settings that read as real but are not container controls at all,
# with the control that actually does the job. Every one of these was found in
# shipped output, silently doing nothing. Checked before the generic
# "unobserved control" leniency, which would otherwise excuse them.
CONTAINER_DEAD = {
    "max_width": " — cap the measure with `boxed_width` (content_width: boxed) "
                 "or by padding the outer container instead",
    "height": " — use `min_height`",
    "flex_align_content": " — use `align_content`",
}

# Viewport width Elementor lays a full-width container out against, per
# breakpoint. Boxed containers use the kit's container_width instead.
VIEWPORT = {None: 1440, "tablet": 768}


def _bp(settings: dict, key: str, bp: str | None):
    """Value of `key` at breakpoint `bp`, falling back to the desktop value.

    Elementor's responsive controls are inherit-down: a container with only
    `width` set is that width at every breakpoint, and `width_tablet` overrides
    it from the tablet breakpoint down. Reading only the suffixed key would
    report every unsuffixed row as unchecked at tablet.
    """
    if bp:
        v = settings.get(f"{key}_{bp}")
        if v not in (None, "", {}):
            return v
    return settings.get(key)


def _px(v) -> float | None:
    """Numeric px size out of a slider control, or None."""
    if isinstance(v, dict) and v.get("unit") == "px" and             isinstance(v.get("size"), (int, float)):
        return float(v["size"])
    return None


def _side_padding(settings: dict, bp: str | None) -> float:
    pad = _bp(settings, "padding", bp)
    if not isinstance(pad, dict) or pad.get("unit") != "px":
        return 0.0
    out = 0.0
    for side in ("left", "right"):
        try:
            out += float(pad.get(side) or 0)
        except (TypeError, ValueError):
            pass
    return out


def content_width(el: dict, parent_px: float | None, kit_px: float,
                  bp: str | None, parent_direction: str = "column") -> float | None:
    """Inner width in px that this container's children resolve against.

    None means "not statically knowable" — an auto-sized child of a flex row,
    or a width in a unit that depends on the viewport. Callers must skip the
    geometry checks rather than guess, because guessing 1240 is the bug this
    function exists to fix: a row nested two containers deep was measured
    against the full page width, so the gap it reserved was less than half of
    what the gap actually costs there, and the row silently wrapped.
    """
    if el.get("elType") != "container":
        return parent_px
    s = el.get("settings") or {}

    w = _bp(s, "width", bp)
    if isinstance(w, dict) and w.get("unit") == "%" and             isinstance(w.get("size"), (int, float)):
        own = None if parent_px is None else parent_px * float(w["size"]) / 100
    elif (px := _px(w)) is not None:
        own = px
    elif w not in (None, "", {}):
        own = None                                  # vw/em/custom
    elif parent_px is None:
        own = None
    elif parent_direction == "row":
        own = None                                  # auto-sized flex child
    else:
        own = parent_px

    # A boxed container centres a fixed measure inside itself regardless of
    # how wide it is; everything below it resolves against that, not the page.
    if _bp(s, "content_width", bp) == "boxed":
        boxed = _px(_bp(s, "boxed_width", bp)) or kit_px
        own = boxed if own is None else min(own, boxed)

    return None if own is None else max(0.0, own - _side_padding(s, bp))


def _row_overflow(el: dict, avail_px: float | None, bp: str | None) -> str | None:
    """V11 — do a flex row's children plus their gaps fit on one line?

    A wrapping flex row breaks a line as soon as the children's widths plus
    the gaps exceed 100%; it does not shrink them. Computing a column as
    100/n and then adding a gap silently drops the last item onto its own
    line, which is how a 3-up grid renders 2-up and a split hero stacks.

    The gap is the part that has to be measured in context. A percentage width
    is relative and survives being nested; a px gap is absolute, so the
    narrower the real container, the larger a share of it the same gap eats.
    That is why `avail_px` is threaded down the tree rather than assumed.
    """
    s = el.get("settings") or {}
    if _bp(s, "flex_direction", bp) != "row":
        return None
    # Mobile stacks these outright, so a row that only overflows below tablet
    # is not a defect. Anything wider is laid out side by side for real.
    if _bp(s, "flex_wrap", bp) == "nowrap":
        return None                       # flexbox shrinks instead of wrapping
    kids = el.get("elements") or []
    if len(kids) < 2:
        return None
    if avail_px is None or avail_px <= 0:
        return None

    widths = []
    for k in kids:
        w = _bp(k.get("settings") or {}, "width", bp)
        if not (isinstance(w, dict) and w.get("unit") == "%"
                and isinstance(w.get("size"), (int, float))):
            return None                       # auto-sized: nothing to check
        widths.append(float(w["size"]))

    gap_px = _px(_bp(s, "flex_gap", bp))
    if gap_px is None:
        g = _bp(s, "flex_gap", bp) or {}
        gap_px = float(g.get("size") or 0) if g.get("unit") in (None, "px") else None
        if gap_px is None:
            return None
    gap = gap_px / avail_px * 100

    at = f" at {bp}" if bp else ""
    if len(set(widths)) == 1:
        # Even grid: check one full line, not the whole (wrapping) row.
        #
        # Recovering the intended column count from the width has to account
        # for the gaps the width was computed against. A correct k-column
        # width satisfies w = (100 - gap*(k-1))/k, so k = (100+gap)/(w+gap).
        # Using round(100/w) instead ignores the gap and over-estimates as k
        # grows — at k=6 it guesses 7 and reports a fitting row as broken.
        w = widths[0]
        per_line = max(1, round((100 + gap) / (w + gap))) if w else 1
        used = per_line * w + (per_line - 1) * gap
        if used > 100.05:
            return (f"{per_line}x{w:g}% + {per_line - 1} gaps of {gap_px:g}px "
                    f"in a {avail_px:.0f}px container = {used:.2f}%{at} "
                    f"— only {per_line - 1} will fit per line")
    else:
        used = sum(widths) + (len(widths) - 1) * gap
        if used > 100.05:
            return (f"widths {'+'.join(f'{w:g}' for w in widths)}% + "
                    f"{len(widths) - 1} gaps of {gap_px:g}px in a "
                    f"{avail_px:.0f}px container = {used:.2f}%{at} "
                    f"— the row will wrap")
    return None


def validate(docs: dict[str, dict], kit: dict, strict_controls: bool = False) -> Report:
    r = Report()
    colors, typos = token_ids(kit)
    cw = (kit.get("page_settings", {}).get("container_width") or {}).get("size") or 1240

    for fname, doc in docs.items():
        seen_ids: set[str] = set()

        def walk(els, path, avail: dict, parent_direction: str = "column"):
            for idx, el in enumerate(els):
                et = el.get("elType")
                wt = el.get("widgetType")
                key = wt or et
                where = f"{fname}:{path}[{idx}]:{key}"
                s = el.get("settings") or {}

                # V5 — unique, well-formed ids
                _id = el.get("id", "")
                if not HEXID.match(str(_id)):
                    r.err("V5", where, f"bad element id {_id!r} (need 7-8 lowercase hex)")
                elif _id in seen_ids:
                    r.err("V5", where, f"duplicate element id {_id}")
                else:
                    seen_ids.add(_id)

                # V3 — widget vocabulary
                if et == "widget":
                    if not REGISTRY.allowed(wt):
                        sub = REGISTRY.substitute(wt)
                        hint = f" — substitute '{sub}'" if sub != wt else ""
                        r.err("V3", where, f"widget '{wt}' is not core/Pro{hint}")
                elif et in ("section", "column"):
                    r.err("V3", where, f"legacy elType '{et}' — containers only")

                # V11 — flex rows fit on one line, at every breakpoint that
                # still lays them out side by side. Mobile is exempt: the row
                # helper stacks there, so a mobile "overflow" is not a defect.
                #
                # V13 — container settings exist. V6 only looks at widgets, so
                # a setting that is not a container control (max_width, height)
                # is written, imported, and silently does nothing — the measure
                # is never capped and the shape is never sized, which reads as
                # a layout bug with no failing build to point at.
                if et == "container":
                    for bp in (None, "tablet"):
                        msg = _row_overflow(el, avail.get(bp), bp)
                        if msg:
                            r.err("V11", where, msg)
                            break
                    known = REGISTRY.controls("container")
                    for k in s:
                        if k.startswith("__") or k in CSS_KEYS:
                            continue
                        m = RESP.search(k)
                        base = k[: m.start()] if m else k
                        # The dead list is checked first and unconditionally.
                        # These read as real settings and pass every other
                        # rule, but they are not container controls at all —
                        # `_width`/`_height` are in STYLE_SUFFIXES, so the
                        # generic leniency below would wave `max_width`
                        # through, which is exactly how it survived.
                        if base in CONTAINER_DEAD:
                            r.err("V13", where,
                                  f"'{base}' is not a container control — "
                                  f"Elementor ignores it{CONTAINER_DEAD[base]}")
                        elif known and base not in known and                                 not any(base.endswith(sfx) for sfx in STYLE_SUFFIXES):
                            # Merely unobserved. The registry is mined from two
                            # kits, so absence is weak evidence — same standing
                            # as V6, and curated into additions.json once a
                            # control is confirmed real.
                            (r.err if strict_controls else r.warn)(
                                "V13", where,
                                f"control '{base}' not observed for a container")

                # V4 — CSS is scoped, or it is not allowed
                for bad in BANNED_KEYS & set(s):
                    r.err("V4", where, f"CSS escape hatch '{bad}' present")
                for ck in CSS_KEYS & set(s):
                    blob = s.get(ck) or ""
                    if not isinstance(blob, str) or not blob.strip():
                        continue
                    if CSS_FORBIDDEN.search(blob):
                        r.err("V4", where, f"{ck} contains a disallowed construct")
                    for line in blob.splitlines():
                        line = line.strip()
                        if not line or "selector" in line:
                            continue
                        # @keyframes declares a name rather than targeting an
                        # element, so it cannot be scoped; the `forge-` prefix
                        # is what keeps it from colliding.
                        if line.startswith("@keyframes forge-"):
                            continue
                        r.err("V4", where,
                              f"{ck} rule is not scoped to `selector`: {line[:60]}")

                for k, v in s.items():
                    if k.startswith("__"):
                        continue

                    # V7 — no raw template ids
                    if k in ("template_id", "loop_template_id"):
                        if not (isinstance(v, str) and v.startswith("@")):
                            r.err("V7", where,
                                  f"{k}={v!r} is a raw id — use a symbolic @loop:<key> ref")

                    m = RESP.search(k)
                    base = k[: m.start()] if m else k
                    if m and m.group(1) not in ALLOWED_BP:
                        r.err("V?", where,
                              f"breakpoint '_{m.group(1)}' requires custom breakpoints")

                    # V9 — value shapes
                    if isinstance(v, dict):
                        if {"unit", "top", "right", "bottom", "left"} <= v.keys():
                            for side in ("top", "right", "bottom", "left"):
                                if not isinstance(v[side], str):
                                    r.err("V9", where,
                                          f"{k}.{side} must be a string, got {type(v[side]).__name__}")
                        elif {"unit", "size"} <= v.keys() and "column" not in v:
                            if not isinstance(v["size"], (int, float)) and v["size"] != "":
                                r.err("V9", where, f"{k}.size must be numeric")

                        # V8 — alt text on media
                        if "url" in v and "source" in v and v.get("url"):
                            if not v.get("alt"):
                                r.warn("V8", where, f"{k} has empty alt text")

                            # V12 — importable media URL. WordPress builds the
                            # destination filename with basename(), so a query
                            # string produces an invalid name and the image is
                            # silently replaced with a placeholder.
                            u = v["url"]
                            if "?" in u:
                                r.err("V12", where,
                                      f"{k} url has a query string — "
                                      f"basename() yields '{u.split('/')[-1][:48]}', "
                                      f"which WordPress will reject")
                            elif not re.search(r"\.(jpe?g|png|webp|svg|gif)$", u, re.I):
                                r.err("V12", where,
                                      f"{k} url has no image extension in its "
                                      f"path — Elementor will not import it")

                    # V6 — control vocabulary. CSS keys are injected into every
                    # element by a Pro module rather than declared on a widget,
                    # so they never appear in a source scrape; V4 owns them.
                    if et == "widget" and REGISTRY.allowed(wt) and base not in CSS_KEYS:
                        known = REGISTRY.controls(wt)
                        if known and base not in known and \
                                not any(base.endswith(sfx) for sfx in STYLE_SUFFIXES):
                            (r.err if strict_controls else r.warn)(
                                "V6", where, f"control '{base}' not observed for '{wt}'")

                # V1 / V2 — globals resolve
                for ctrl, ref in (s.get("__globals__") or {}).items():
                    mm = GLOBAL_REF.search(ref or "")
                    if not mm:
                        r.err("V1", where, f"malformed global ref on '{ctrl}': {ref!r}")
                        continue
                    kind, tok = mm.groups()
                    pool = colors if kind == "colors" else typos
                    rule = "V1" if kind == "colors" else "V2"
                    if tok not in pool:
                        r.err(rule, where, f"dangling {kind} token '{tok}' on '{ctrl}'")

                # V10 — dynamic tags known
                for ctrl, raw in (s.get("__dynamic__") or {}).items():
                    tm = TAG_NAME.search(raw or "")
                    if not tm:
                        r.err("V10", where, f"malformed dynamic tag on '{ctrl}'")
                    elif tm.group(1) not in REGISTRY.dynamic_tags:
                        r.warn("V10", where, f"dynamic tag '{tm.group(1)}' not in registry")

                if et == "container":
                    child_avail = {
                        bp: content_width(el, avail.get(bp), cw, bp, parent_direction)
                        for bp in (None, "tablet")
                    }
                    direction = s.get("flex_direction") or "column"
                else:
                    child_avail, direction = avail, "column"
                walk(el.get("elements") or [], f"{path}/{key}", child_avail, direction)

        walk(doc.get("content", []), "root",
             {None: cw, "tablet": min(cw, VIEWPORT["tablet"])})

        if doc.get("type") not in {
            "page", "section", "header", "footer", "single-post",
            "archive", "product", "product-archive", "loop-item",
            "search-results", "error-404", "container"
        }:
            r.err("V-doc", fname, f"unknown document type {doc.get('type')!r}")

    return r
