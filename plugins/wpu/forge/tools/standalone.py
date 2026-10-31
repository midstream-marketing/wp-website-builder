#!/usr/bin/env python3
"""
standalone.py — rebuild a compiled template so it needs no Global Kit.

WHY THIS EXISTS. Every kit this repo ships routes colour and typography
through Elementor globals: a heading carries `globals/colors?id=surf002`
rather than a hex, which is what lets one Global Kit restyle a whole site.
That is the right default for a site being built here, and the wrong one for a
site that already exists: importing the kit would overwrite the client's own
global colours, fonts, button styles and container width, changing every page
they already have.

So this takes the compiled document and resolves every global reference into
the literal value the kit would have supplied:

    settings.__globals__.title_color = "globals/colors?id=surf002"
        ->  settings.title_color = "#FEFCF2"

    settings.__typography__ = "globals/typography?id=typo101"
        ->  settings.typography_typography = "custom"
            settings.typography_font_family = "Archivo"
            settings.typography_font_size = {...}   (and tablet/mobile, weight,
            line height, letter spacing)

    settings.__globals__.content_typography_typography = "globals/typography?id=typo104"
        ->  the same expansion under the widget's own group prefix

The result imports as an ordinary Elementor template. It carries its own
styling, touches nothing global, and applies to exactly the page it is applied
to.

THE TRADE-OFF, stated plainly: a standalone template no longer follows the
site's global colours. Change a brand colour in Site Settings later and this
page keeps the values baked in at build time. That is the price of not
touching the rest of the site, and it is the right trade when the site is
already live.

    python tools/standalone.py clients/<slug>            # uses out/
    python tools/standalone.py clients/<slug> --out-dir out-standalone
"""
from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path

GLOBAL_DOC = "global.json"
COLOR_PREFIX = "globals/colors?id="
TYPO_PREFIX = "globals/typography?id="


def load_kit(path: Path):
    """Colour and typography tables out of the Global Kit document."""
    kit = json.loads(path.read_text(encoding="utf-8"))
    ps = kit.get("page_settings", {})
    colors, typo = {}, {}
    for key in ("system_colors", "custom_colors"):
        for c in ps.get(key, []) or []:
            colors[c["_id"]] = c.get("color", "")
    for key in ("system_typography", "custom_typography"):
        for t in ps.get(key, []) or []:
            typo[t["_id"]] = {k: v for k, v in t.items()
                              if k.startswith("typography_")}
    return colors, typo


def expand_typo(entry: dict, prefix: str) -> dict:
    """Re-key a kit typography entry under one widget's control group.

    The kit stores `typography_font_family`; a widget group called
    `content_typography` wants `content_typography_font_family`. The group's
    own switch (`<prefix>_typography`) must be set to "custom" or Elementor
    ignores every other key in the group - the same trap `_inline_type` exists
    for in the block factories.
    """
    out = {}
    for k, v in entry.items():
        suffix = k[len("typography"):]          # "_font_family", "_typography"
        out[prefix + suffix] = v
    out[prefix + "_typography"] = "custom"
    return out


def flatten(el: dict, colors: dict, typo: dict, misses: list) -> None:
    s = el.get("settings")
    if isinstance(s, dict):
        g = s.get("__globals__")
        if isinstance(g, dict):
            for key, ref in list(g.items()):
                if not isinstance(ref, str):
                    continue
                if ref.startswith(COLOR_PREFIX):
                    ident = ref[len(COLOR_PREFIX):]
                    if ident in colors:
                        s[key] = colors[ident]
                        del g[key]
                    else:
                        misses.append(ref)
                elif ref.startswith(TYPO_PREFIX):
                    ident = ref[len(TYPO_PREFIX):]
                    entry = typo.get(ident)
                    if entry and key.endswith("_typography"):
                        prefix = key[: -len("_typography")]
                        s.update(expand_typo(entry, prefix))
                        del g[key]
                    else:
                        misses.append(ref)
            if not g:
                s.pop("__globals__", None)

        ref = s.pop("__typography__", None)
        if isinstance(ref, str) and ref.startswith(TYPO_PREFIX):
            entry = typo.get(ref[len(TYPO_PREFIX):])
            if entry:
                s.update(expand_typo(entry, "typography"))
            else:
                misses.append(ref)
                s["__typography__"] = ref

    for child in el.get("elements", []) or []:
        flatten(child, colors, typo, misses)


def kit_defaults(kit_path: Path) -> dict:
    """The handful of page-level settings the kit would otherwise supply.

    Only the ones a single page actually depends on: the content width its
    boxed containers measure against, and the default button geometry. Left on
    the DOCUMENT, so it applies to this page and no other.
    """
    ps = json.loads(kit_path.read_text(encoding="utf-8")).get("page_settings", {})
    keep = {}
    for k in ("container_width", "button_border_radius", "button_padding",
              "image_border_radius"):
        if k in ps:
            keep[k] = ps[k]
    return keep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("client")
    ap.add_argument("--in-dir", default="out")
    ap.add_argument("--out-dir", default="out-standalone")
    ap.add_argument("--title", default=None)
    ap.add_argument("--only", default=None,
                    help="one document key - export just that page, which is "
                         "what an extension build on a live site needs")
    args = ap.parse_args()

    client = Path(args.client)
    src = client / args.in_dir / "templates"
    dst = client / args.out_dir
    if not (src / GLOBAL_DOC).exists():
        raise SystemExit("no Global Kit at %s - nothing to resolve against"
                         % (src / GLOBAL_DOC))

    colors, typo = load_kit(src / GLOBAL_DOC)
    defaults = kit_defaults(src / GLOBAL_DOC)
    if dst.exists():
        shutil.rmtree(dst)
    (dst / "templates").mkdir(parents=True)

    manifest_templates = []
    made = []
    for doc_path in sorted(src.glob("*.json")):
        if doc_path.name == GLOBAL_DOC:
            continue
        if args.only and doc_path.stem != args.only:
            continue
        doc = json.loads(doc_path.read_text(encoding="utf-8"))
        misses: list = []
        for el in doc.get("content", []) or []:
            flatten(el, colors, typo, misses)

        page_settings = doc.get("page_settings") or {}
        page_settings.update(defaults)
        doc["page_settings"] = page_settings

        out_path = dst / "templates" / doc_path.name
        out_path.write_text(json.dumps(doc, indent=1), encoding="utf-8")

        blob = out_path.read_text(encoding="utf-8")
        left = blob.count("globals/")
        made.append((doc_path.name, left, len(set(misses))))
        manifest_templates.append({
            "name": doc.get("title", doc_path.stem.title()),
            "source": "templates/" + doc_path.name,
            "type": "page",
            "category": "page",
            "metadata": {
                "template_type": "single-page",
                "include_in_zip": "1",
                "elementor_pro_required": "1",
                "wp_page_template": "elementor_header_footer",
                "additional_template_information": [
                    "Standalone: this template carries its own colours and "
                    "type. It does NOT import a Global Kit and does not "
                    "change any other page."
                ],
            },
            "elementor_pro_required": True,
        })

    if not manifest_templates:
        raise SystemExit("nothing matched --only %r" % args.only)
    title = args.title or (client.name.replace("-", " ").title() +
                           " - Standalone Templates")
    manifest = {
        "manifest_version": "1.0.23",
        "title": title,
        "page_builder": "elementor",
        "kit_version": "1.0.0",
        "templates": manifest_templates,
    }
    (dst / "manifest.json").write_text(json.dumps(manifest, indent=1),
                                       encoding="utf-8")

    zip_path = dst / ((args.only or client.name) + "-standalone.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(dst / "manifest.json", "manifest.json")
        for t in manifest_templates:
            z.write(dst / t["source"], t["source"])

    print("colours resolved: %d   typography sets resolved: %d"
          % (len(colors), len(typo)))
    for name, left, miss in made:
        status = "clean" if left == 0 else "%d UNRESOLVED" % left
        print("  %-28s %s%s" % (name, status,
                                "  (%d distinct)" % miss if miss else ""))
    print("wrote %s" % zip_path)
    if any(left for _, left, _ in made):
        raise SystemExit("unresolved global references remain - see above")


if __name__ == "__main__":
    main()
