"""
core.py — the primitives every block factory uses.

Nothing else in the codebase is allowed to hand-write an Elementor
settings value. If you find yourself typing {"unit": "px", ...} outside
this module, use the helper instead.
"""
from __future__ import annotations

import json
import random
import string
import urllib.parse
from pathlib import Path

REGISTRY_PATH = Path(__file__).resolve().parents[2] / "registry" / "elementor-registry.json"

_HEX = "0123456789abcdef"
_seen_ids: set[str] = set()


# ─────────────────────────── ids ───────────────────────────

def eid() -> str:
    """8-char lowercase hex, unique within this process."""
    while True:
        v = "".join(random.choice(_HEX) for _ in range(8))
        if v not in _seen_ids:
            _seen_ids.add(v)
            return v


def tid() -> str:
    """7-char id used for token _id and dynamic-tag id."""
    while True:
        v = "".join(random.choice(_HEX) for _ in range(7))
        if v not in _seen_ids:
            _seen_ids.add(v)
            return v


def reset_ids() -> None:
    _seen_ids.clear()


# ───────────────────── value shape helpers ─────────────────────

def slider(size, unit: str = "px") -> dict:
    """Slider control. `size` stays numeric."""
    return {"unit": unit, "size": size, "sizes": []}


def dims(top, right, bottom, left, unit: str = "px", linked: bool = False) -> dict:
    """Dimensions control. Values are STRINGS — Elementor drops numbers here."""
    return {
        "unit": unit,
        "top": str(top), "right": str(right),
        "bottom": str(bottom), "left": str(left),
        "isLinked": linked,
    }


def box(v, unit: str = "px") -> dict:
    return dims(v, v, v, v, unit=unit, linked=True)


def media(url: str, alt: str = "") -> dict:
    """Media control. id="" makes Elementor import the remote file.

    The URL is stripped of its query string. WordPress derives the destination
    filename with basename(), so `photo.jpeg?w=1600` yields the invalid
    filename `photo.jpeg?w=1600`, wp_check_filetype rejects it, the download
    is abandoned and Elementor silently substitutes its own placeholder.
    Measured across both reference kits: 143 media URLs, zero query strings.
    """
    return {"url": url.split("?")[0], "id": "", "size": "", "alt": alt,
            "source": "library"}


def link(url: str, external: bool = False, nofollow: bool = False) -> dict:
    return {
        "url": url,
        "is_external": "on" if external else "",
        "nofollow": "nofollow" if nofollow else "",
    }


def icon(cls: str) -> dict:
    """Font Awesome 5 icon control. Library is inferred from the prefix."""
    prefix = cls.split()[0] if cls else "fas"
    lib = {"fas": "fa-solid", "far": "fa-regular", "fab": "fa-brands"}.get(prefix, "fa-solid")
    return {"value": cls, "library": lib}


def gap(column, row=None) -> dict:
    row = column if row is None else row
    return {"unit": "px", "size": column, "column": str(column), "row": str(row), "isLinked": column == row}


# ─────────────────── globals / dynamic channels ───────────────────

def css(*rules: str) -> str:
    """Element-scoped CSS for effects Elementor controls cannot express.

    Contract v2 relaxes the original "no CSS at all" rule to "no CSS outside a
    block factory". The reason the ban existed was hand-written per-page CSS,
    which is unmaintainable and re-skin-hostile. Effects like clip-path,
    gradient scrims and keyframes have no control equivalent, and the eight
    reference designs are built on them.

    Rules must be written against `selector`, Elementor's placeholder for the
    element itself, so nothing leaks outside the element it is attached to.
    Colour still belongs in __globals__ wherever a control exists for it;
    this is for geometry and effects only.
    """
    out = []
    for r in rules:
        r = " ".join(r.split())
        if not r:
            continue
        # @keyframes is inherently global — it declares a name, not a target —
        # so it cannot be scoped. Names are prefixed `forge-` to keep them from
        # colliding with the theme or another plugin.
        if r.startswith("@keyframes"):
            if not r.startswith("@keyframes forge-"):
                raise ValueError(
                    f"@keyframes names must start with `forge-`, got: {r[:60]}")
        elif "selector" not in r:
            raise ValueError(
                f"CSS must be scoped to `selector`, got: {r[:70]}")
        out.append(r)
    return "\n".join(out)


def color_ref(token: str) -> str:
    return f"globals/colors?id={token}"


def typo_ref(token: str) -> str:
    return f"globals/typography?id={token}"


def dynamic(name: str, **settings) -> str:
    """Build an [elementor-tag] payload for the __dynamic__ channel."""
    encoded = urllib.parse.quote(json.dumps(settings, separators=(",", ":")))
    return f'[elementor-tag id="{tid()}" name="{name}" settings="{encoded}"]'


# ───────────────────────── element builders ─────────────────────────

def container(children: list | None = None, settings: dict | None = None,
              globals_: dict | None = None, dynamic_: dict | None = None) -> dict:
    s = dict(settings or {})
    if globals_:
        s["__globals__"] = globals_
    if dynamic_:
        s["__dynamic__"] = dynamic_
    return {
        "id": eid(),
        "elType": "container",
        "settings": s,
        "elements": children or [],
        "isInner": False,
    }


def widget(widget_type: str, settings: dict | None = None,
           globals_: dict | None = None, dynamic_: dict | None = None,
           children: list | None = None) -> dict:
    """Build a widget element.

    `children` is for Elementor's nested widgets (nested-accordion,
    nested-tabs, nested-carousel). Those keep their panel content as real
    child containers rather than as an HTML string in a repeater field, so
    each panel can hold any block content — which is the whole reason to
    prefer them over the flat `accordion` widget.
    """
    s = dict(settings or {})
    if globals_:
        s["__globals__"] = globals_
    if dynamic_:
        s["__dynamic__"] = dynamic_
    return {
        "id": eid(),
        "elType": "widget",
        "settings": s,
        "elements": children or [],
        "widgetType": widget_type,
    }


def repeater_item(**fields) -> dict:
    return {"_id": tid(), **fields}


# ───────────────────────────── registry ─────────────────────────────

class Registry:
    """Ground truth for legal widget types and control keys."""

    def __init__(self, path: Path | str = REGISTRY_PATH):
        self.data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.widgets = self.data["widgets"]
        # Curated additions: valid controls the mined kits never exercised.
        add_path = Path(path).with_name("additions.json")
        self.additions = {}
        if add_path.exists():
            self.additions = {
                k: set(v["controls"])
                for k, v in json.loads(add_path.read_text(encoding="utf-8")).items()
                if not k.startswith("_")
            }
        self.substitutions = self.data.get("substitutions", {})
        self.dynamic_tags = set(self.data.get("dynamic_tags", {}))
        self.breakpoints = set(self.data.get("allowed_breakpoints", ["tablet", "mobile"]))
        self.plugins = {}
        self._load_plugin_widgets(Path(path).with_name("plugin-widgets.json"))

    def _load_plugin_widgets(self, path: Path) -> None:
        """Merge in widgets a client's own WordPress plugin registers.

        These cannot live in elementor-registry.json: that file is regenerated
        wholesale by build_registry_php.py from the Elementor source tree, so a
        hand-added entry survives only until the next remine. The merge is
        additive and never overwrites a mined name — if Elementor later ships a
        widget under the same slug, the mined definition is the true one.
        """
        if not path.exists():
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        self.plugins = {k: v for k, v in data.get("_plugins", {}).items()
                        if not k.startswith("_")}
        common = self.data.get("common_controls", [])
        for name, spec in (data.get("widgets") or {}).items():
            if name.startswith("_") or name in self.widgets:
                continue
            controls = [c for c in spec["controls"] if c != "_common"]
            if "_common" in spec["controls"]:
                controls += common
            self.widgets[name] = {"tier": spec.get("tier", "addon"),
                                  "controls": sorted(set(controls))}
        self.dynamic_tags |= {k for k in (data.get("dynamic_tags") or {})
                              if not k.startswith("_")}

    def allowed(self, wtype: str) -> bool:
        w = self.widgets.get(wtype)
        return bool(w) and w["tier"] != "third-party"

    def tier(self, wtype: str) -> str | None:
        w = self.widgets.get(wtype)
        return w["tier"] if w else None

    def controls(self, wtype: str) -> set[str]:
        w = self.widgets.get(wtype)
        base = set(w["controls"]) if w else set()
        return base | self.additions.get(wtype, set())

    def substitute(self, wtype: str) -> str:
        return self.substitutions.get(wtype, wtype)


REGISTRY = Registry()
