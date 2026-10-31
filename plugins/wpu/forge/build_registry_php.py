#!/usr/bin/env python3
"""build_registry_php.py — derive the widget registry from Elementor's source.

The original registry was mined from two shipped kits, so it only knew the
controls those two designers happened to touch: 21 widgets, and none of the
carousels, star ratings, sliders or progress dials a modern lead-gen site is
built from. Reading the plugin source instead yields the complete vocabulary
Elementor actually supports, which is what the contract's V6 rule wants.

    python build_registry_php.py "…/wp-content/plugins" -o registry/elementor-registry.json
    python build_registry_php.py "…/plugins" -o … --addon happy-elementor-addons

Controls are inherited three ways and all three matter: Widget_Button carries
none of its own (they live in Button_Trait), and theme-site-logo extends
Widget_Image. A flat per-file scan misses both, so this indexes every class
and trait first, then resolves each widget through its ancestry.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

# A group control registers several keys under one name, combining as
# f"{group_name}{suffix}". Suffixes are Elementor's own.
GROUPS = {
    "Typography": ["_typography", "_font_family", "_font_size", "_font_weight",
                   "_text_transform", "_font_style", "_text_decoration",
                   "_line_height", "_letter_spacing", "_word_spacing"],
    "Text_Shadow": ["_text_shadow_type", "_text_shadow"],
    "Box_Shadow": ["_box_shadow_type", "_box_shadow", "_box_shadow_position"],
    "Border": ["_border", "_width", "_color"],
    "Background": ["_background", "_color", "_color_b", "_color_stop",
                   "_color_b_stop", "_gradient_type", "_gradient_angle",
                   "_gradient_position", "_image", "_position", "_xpos",
                   "_ypos", "_attachment", "_repeat", "_size", "_bg_width",
                   "_video_link", "_video_start", "_video_end",
                   "_slideshow_gallery", "_video_fallback"],
    "Css_Filter": ["_css_filter", "_blur", "_brightness", "_contrast",
                   "_saturate", "_hue"],
    "Image_Size": ["_size", "_custom_dimension"],
    "Text_Stroke": ["_text_stroke_type", "_text_stroke", "_stroke_color"],
    "Flex_Item": ["_align_self", "_order", "_size", "_grow", "_shrink"],
    "Flex_Container": ["_direction", "_justify_content", "_align_items",
                       "_gap", "_wrap", "_align_content"],
    "Grid_Container": ["_columns_grid", "_rows_grid", "_gaps",
                       "_justify_items", "_align_items"],
    "Mask": ["_switch", "_shape", "_image", "_notice", "_size", "_scale",
             "_position", "_repeat"],
}

RE_CLASS = re.compile(r"^\s*(?:abstract\s+|final\s+)?(?:class|trait)\s+(\w+)"
                      r"(?:\s+extends\s+\\?([\w\\]+))?", re.M)
RE_USE_TRAIT = re.compile(r"^[ \t]+use\s+([\w\\][\w\\,\s]*);", re.M)
RE_NAME = re.compile(r"function\s+get_name\s*\(\s*\)\s*(?::\s*\w+\s*)?\{"
                     r"[^{}]*?return\s*'([^']+)'", re.S)
RE_CTRL = re.compile(r"->add(?:_responsive|_group)?_control\s*\(\s*'([^']+)'")
RE_GROUP = re.compile(
    r"->add_group_control\s*\(\s*(?:\\?[\w\\]*?)Group_Control_(\w+)::get_type"
    r"\s*\(\s*\)\s*,(.*?)(?:\n\s*\);)", re.S)
RE_GROUP_NAME = re.compile(r"'name'\s*=>\s*'([^']+)'")


def controls_in(src: str) -> set[str]:
    out = set(RE_CTRL.findall(src))
    for kind, body in RE_GROUP.findall(src):
        nm = RE_GROUP_NAME.search(body)
        if not nm:
            continue
        base = nm.group(1)
        out.add(base)
        for sfx in GROUPS.get(kind, ["_" + kind.lower()]):
            out.add(base + sfx)
    return out


def index(root: Path, tier: str, classes: dict):
    """Record every class/trait: its parent, its traits, its controls, its name."""
    if not root.exists():
        return
    for php in root.rglob("*.php"):
        if "/vendor/" in php.as_posix() or "/node_modules/" in php.as_posix():
            continue
        try:
            src = php.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        m = RE_CLASS.search(src)
        if not m:
            continue
        cls, parent = m.group(1), (m.group(2) or "").split("\\")[-1]
        traits = []
        for grp in RE_USE_TRAIT.findall(src):
            for t in grp.split(","):
                t = t.strip().split("\\")[-1]
                if t and t[0].isupper():
                    traits.append(t)
        nm = RE_NAME.search(src)
        rec = classes.setdefault(cls, {
            "tier": tier, "parent": "", "traits": [],
            "controls": set(), "widget": None, "file": php.as_posix()})
        rec["parent"] = rec["parent"] or parent
        rec["traits"] = list({*rec["traits"], *traits})
        rec["controls"] |= controls_in(src)
        # Elementor reuses class names across roles — Site_Logo is both a
        # dynamic tag and a Theme Builder widget. The widgets/ copy is the
        # one this registry is about, so let it win.
        in_widget_dir = bool(re.search(r"/(widgets|elements)/", php.as_posix()))
        if in_widget_dir and not re.search(r"/(widgets|elements)/", rec["file"]):
            # The widget copy also has the ancestry we want: Site_Logo the tag
            # extends Pro_Data_Tag, Site_Logo the widget extends Widget_Image.
            rec.update(file=php.as_posix(), widget=None,
                       parent=parent, traits=traits)
        if nm and (rec["widget"] is None or in_widget_dir):
            rec["widget"] = nm.group(1)
        if tier == "core" and rec["tier"] != "core":
            rec["tier"] = tier


def resolve(cls: str, classes: dict, seen=None) -> set[str]:
    """Controls of a class plus everything it inherits or mixes in."""
    seen = seen or set()
    if cls in seen or cls not in classes:
        return set()
    seen.add(cls)
    rec = classes[cls]
    out = set(rec["controls"])
    for nxt in [rec["parent"], *rec["traits"]]:
        if nxt:
            out |= resolve(nxt, classes, seen)
    return out


def widget_name(cls: str, classes: dict, seen=None):
    """get_name() may be declared on a trait or an ancestor."""
    seen = seen or set()
    if cls in seen or cls not in classes:
        return None
    seen.add(cls)
    rec = classes[cls]
    if rec["widget"]:
        return rec["widget"]
    for nxt in [*rec["traits"], rec["parent"]]:
        if nxt:
            got = widget_name(nxt, classes, seen)
            if got:
                return got
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plugins")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--addon", action="append", default=[])
    a = ap.parse_args()

    plugins = Path(a.plugins)
    classes: dict[str, dict] = {}
    index(plugins / "elementor", "core", classes)
    index(plugins / "elementor-pro", "pro", classes)
    for addon in a.addon:
        index(plugins / addon, "addon", classes)
    print(f"indexed {len(classes)} classes/traits")

    # Only classes whose file lives in a widgets/ or elements/ directory are
    # real widgets; dynamic tags and controls also declare get_name().
    widgets: dict[str, dict] = {}
    for cls, rec in classes.items():
        if not re.search(r"/(widgets|elements)/", rec["file"]):
            continue
        name = widget_name(cls, classes)
        if not name:
            continue
        # Addon packs commonly build the slug from the class name:
        # Happy Addons does `return 'ha-' . kebab($class)`, so the literal
        # this scrape captures is only the prefix. Complete it.
        if name.endswith("-") or name.endswith("_"):
            name = name + cls.lower().replace("_", "-")
        ctrls = resolve(cls, classes)
        if not ctrls:
            continue
        cur = widgets.get(name)
        if cur is None or len(ctrls) > len(cur["controls"]):
            widgets[name] = {"tier": rec["tier"], "controls": ctrls}

    common: set[str] = set()
    for c in ("Widget_Base", "Element_Base", "Controls_Stack", "Widget_Common",
              "Widget_Common_Base"):
        common |= resolve(c, classes)

    out_path = Path(a.out)
    prev = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else {}
    data = {
        "source": "elementor plugin source (class + trait resolution)",
        "widgets": {k: {"tier": v["tier"],
                        "controls": sorted(v["controls"] | common)}
                    for k, v in sorted(widgets.items())},
        "common_controls": sorted(common),
        "dynamic_tags": prev.get("dynamic_tags", {}),
        "substitutions": prev.get("substitutions", {}),
        "allowed_breakpoints": prev.get("allowed_breakpoints", ["tablet", "mobile"]),
    }
    out_path.write_text(json.dumps(data, indent=1), encoding="utf-8")

    tiers = defaultdict(int)
    for v in data["widgets"].values():
        tiers[v["tier"]] += 1
    print(f"common inherited controls: {len(common)}")
    print(f"{len(data['widgets'])} widgets {dict(tiers)} -> {out_path}")


if __name__ == "__main__":
    main()
