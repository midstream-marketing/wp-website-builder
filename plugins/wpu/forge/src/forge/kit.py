"""
kit.py — package compiled documents as an Envato-format Template Kit.

Output is importable by the Envato Template Kit Import plugin and is the
same shape as a marketplace-sold kit, so the same generator can produce
client sites and sellable products.
"""
from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

from .core import REGISTRY

TYPE_TO_CATEGORY = {
    "page": "page", "section": "page", "header": "section", "footer": "section",
    "single-post": "page", "archive": "page", "loop-item": "section",
    "search-results": "page", "error-404": "page", "container": "section",
    "product": "page", "product-archive": "page",
}


IMG_EXT = re.compile(r"\.(jpe?g|png|webp|svg|gif)(\?|$)", re.I)


def _collect_images(doc: dict) -> list[dict]:
    """Media controls are identified by shape, not by file extension — a CDN
    URL can carry its format in the query string and still be an image."""
    out = []

    def walk(els):
        for el in els:
            for v in (el.get("settings") or {}).values():
                if isinstance(v, dict) and "source" in v \
                        and isinstance(v.get("url"), str) and v["url"].startswith("http"):
                    out.append({"url": v["url"], "alt": v.get("alt", "")})
            walk(el.get("elements") or [])

    walk(doc.get("content", []))
    return out


def _filename(url: str) -> str:
    """Elementor's importer keys off a real extension in the path, so a URL
    without one gets a synthesised name rather than an extensionless file."""
    stem = Path(url.split("?")[0]).name or "image"
    return stem if IMG_EXT.search(stem + "?") else f"{stem}.jpg"


ADDON_PLUGINS = {
    "ha-": {"name": "Happy Addons for Elementor", "version": "3.12.0",
            "file": "happy-elementor-addons/happy-elementor-addons.php",
            "author": "Happy Addons"},
    # Plugins that contribute their own widgets through registry/plugin-widgets.json
    # declare themselves there, next to the vocabulary they add, rather than
    # being restated here. A kit that uses a client's booking widgets and does
    # not list the plugin imports as a page full of empty boxes.
    **REGISTRY.plugins,
}

# WooCommerce is not an Elementor addon and contributes no widget prefix — its
# widgets ship inside Elementor Pro. But a `product` document cannot be
# imported at all unless WooCommerce is active, so a kit containing one has a
# hard dependency the manifest has to state.
WOO_PLUGIN = {"name": "WooCommerce", "version": "9.4.2",
              "file": "woocommerce/woocommerce.php", "author": "Automattic"}
WOO_DOC_TYPES = {"product", "product-archive"}


def _required_plugins(docs: dict[str, dict]) -> list[dict]:
    """Declare only the plugins the kit actually uses.

    A kit that lists a dependency it never touches makes the client install
    something for nothing; one that omits a real dependency imports broken.
    """
    req = [
        {"name": "Elementor", "version": "3.34.1",
         "file": "elementor/elementor.php", "author": "Elementor.com"},
        {"name": "Elementor Pro", "version": "3.34.0",
         "file": "elementor-pro/elementor-pro.php", "author": "Elementor.com"},
    ]
    seen = set()

    def walk(els):
        for el in els:
            wt = el.get("widgetType") or ""
            for prefix, plug in ADDON_PLUGINS.items():
                if wt.startswith(prefix):
                    seen.add(prefix)
            walk(el.get("elements") or [])

    # A WooCommerce widget on an ordinary page counts as much as a Single
    # Product document does — a Products grid on the home page needs the
    # plugin too, and it is not covered by the document type.
    needs_woo = False

    def woo_walk(els):
        nonlocal needs_woo
        for el in els:
            if (el.get("widgetType") or "").startswith("woocommerce-"):
                needs_woo = True
            woo_walk(el.get("elements") or [])

    for doc in docs.values():
        walk(doc.get("content", []))
        woo_walk(doc.get("content", []))
        if doc.get("type") in WOO_DOC_TYPES:
            needs_woo = True
    if needs_woo:
        req.append(WOO_PLUGIN)
    for prefix in sorted(seen):
        req.append(ADDON_PLUGINS[prefix])
    return req


def build_manifest(site_name: str, kit_doc: dict, docs: dict[str, dict],
                   version: str = "1.0.0") -> dict:
    templates = [{
        "name": kit_doc["title"],
        "screenshot": "screenshots/global-kit-styles.jpg",
        "source": "templates/global.json",
        "type": "section",
        "category": "page",
        "metadata": kit_doc["metadata"],
        "elementor_pro_required": True,
    }]

    images: dict[str, dict] = {}
    for fname, doc in docs.items():
        stem = Path(fname).stem
        templates.append({
            "name": doc["title"],
            "screenshot": f"screenshots/{stem}.jpg",
            "source": f"templates/{fname}",
            "type": doc["type"],
            "category": TYPE_TO_CATEGORY.get(doc["type"], "page"),
            "metadata": doc["metadata"],
            "elementor_pro_required": True,
        })
        for img in _collect_images(doc):
            e = images.setdefault(img["url"], {
                "filename": _filename(img["url"]),
                "thumbnail_url": img["url"],
                "templates": [],
                "image_source": "self_created",
                "image_urls": "#",
                "alt": img["alt"],
            })
            ref = {"source": f"templates/{fname}", "name": doc["title"]}
            if ref not in e["templates"]:
                e["templates"].append(ref)

    return {
        "manifest_version": "1.0.23",
        "title": f"{site_name} Template Kit",
        "page_builder": "elementor",
        "kit_version": version,
        "templates": templates,
        "required_plugins": _required_plugins(docs),
        "images": list(images.values()),
    }


def write_kit(outdir: str | Path, site_name: str, kit_doc: dict,
              docs: dict[str, dict], zip_it: bool = True,
              bundle: dict | None = None) -> Path:
    """`bundle` (opt-in): {"dir": Path, "folder": "lakes"}. The images in
    `dir` that the templates reference ship INSIDE the zip under images/, and
    the manifest lists them under forge_images. The Template Kit Importer
    (1.2+) copies them to wp-content/uploads/<folder>/ and registers them in
    the Media Library, so there is no FTP step and Pro widgets that resolve
    images by attachment ID (the gallery) get one."""
    out = Path(outdir)
    (out / "templates").mkdir(parents=True, exist_ok=True)
    (out / "screenshots").mkdir(parents=True, exist_ok=True)

    (out / "templates" / "global.json").write_text(json.dumps(kit_doc, indent=1), encoding="utf-8")
    for fname, doc in docs.items():
        (out / "templates" / fname).write_text(json.dumps(doc, indent=1), encoding="utf-8")

    manifest = build_manifest(site_name, kit_doc, docs)
    bundled = []
    if bundle:
        prefix = "/wp-content/uploads/%s/" % bundle["folder"]
        blob = json.dumps(docs)
        for f in sorted(Path(bundle["dir"]).iterdir()):
            if f.suffix.lower() in (".webp", ".jpg", ".jpeg", ".png") and                     (prefix + f.name) in blob:
                bundled.append(f)
        # Alt text per bundled file, taken from the media values in the
        # templates (the manifest's own `images` list only covers remote
        # URLs). The importer writes it to the attachment.
        alts = {}

        def walk(n):
            if isinstance(n, dict):
                u = n.get("url")
                if isinstance(u, str) and u.startswith(prefix) and n.get("alt"):
                    alts.setdefault(u[len(prefix):], n["alt"])
                for v in n.values():
                    walk(v)
            elif isinstance(n, list):
                for v in n:
                    walk(v)
        walk(docs)
        manifest["forge_images"] = {"folder": bundle["folder"],
                                    "files": [f.name for f in bundled],
                                    "alt": {f.name: alts[f.name] for f in bundled
                                            if f.name in alts}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")

    if zip_it:
        # Transliterate German letters first, or "Gebäudeservice" becomes
        # "geb-udeservice" - the umlaut is dropped as a separator.
        ascii_name = site_name.lower()
        for k, v in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
            ascii_name = ascii_name.replace(k, v)
        slug = re.sub(r"[^a-z0-9]+", "-", ascii_name).strip("-")
        zpath = out / f"{slug}-template-kit.zip"
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(out / "manifest.json", "manifest.json")
            for f in sorted((out / "templates").glob("*.json")):
                z.write(f, f"templates/{f.name}")
            for f in sorted((out / "screenshots").glob("*.jpg")):
                z.write(f, f"screenshots/{f.name}")
            for f in bundled:
                z.write(f, f"images/{f.name}")
        return zpath
    return out
