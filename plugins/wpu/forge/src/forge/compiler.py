"""
compiler.py — IR -> Elementor document JSON.

The IR is the only thing an LLM agent writes. It is deliberately small:
a page key, a document type, and an ordered list of {block, props}.
Everything about how that becomes Elementor JSON lives in blocks.py.
"""
from __future__ import annotations

from .blocks import render, set_primary_style
from .core import reset_ids
from .motion import apply_motion

# The first element is Elementor's own document-type name and is load-bearing:
# the Template Kit importer hands this JSON straight to Elementor's `local`
# source, which looks the type up in the documents manager. The second is the
# Envato category label, which only classifies the entry in the manifest.
#
# `product` / `product-archive` are registered by Elementor Pro's WooCommerce
# module, so those two documents import only when WooCommerce *and* Pro are
# both active. With Pro missing the importer rewrites the type to `page`
# (class-builder-elementor.php:109) and the template lands as an ordinary page
# rather than failing — with WooCommerce missing it errors, which is why the
# README lists it as a prerequisite rather than a nicety.
DOC_META = {
    "page":            ("page",            "single-page"),
    "header":          ("header",          "section-header"),
    "footer":          ("footer",          "section-footer"),
    "single-post":     ("single-post",     "single-post"),
    "archive":         ("archive",         "archive-blog"),
    "product":         ("product",         "single-product"),
    "product-archive": ("product-archive", "archive-product"),
    "loop-item":       ("loop-item",       "section-loop"),
    "error-404":       ("error-404",       "single-404"),
    "container":       ("container",       "section-other"),
}

# Theme Builder documents that are useless until something tells them where to
# render. Same reasoning as the header/footer default below: an imported
# template with no condition is silently never shown, which reads as a broken
# kit. Overridable per page with a `conditions` key on the IR.
DEFAULT_CONDITIONS = {
    "header":          ["include/general"],
    "footer":          ["include/general"],
    "product":         ["include/product"],
    "product-archive": ["include/product_archive"],
    # Elementor Pro: not_found404 is a sub-condition of singular
    # (modules/theme-builder/conditions/singular.php). Added 2026-10-26 - a
    # 404 template with no condition imported and never rendered.
    "error-404":       ["include/singular/not_found404"],
}


def compile_document(page_ir: dict) -> dict:
    """Compile one IR page into an importable Elementor template document."""
    dtype = page_ir.get("type", "page")
    if dtype not in DOC_META:
        raise ValueError(f"Unknown document type '{dtype}'. Legal: {sorted(DOC_META)}")
    el_type, template_type = DOC_META[dtype]

    content = []
    for i, b in enumerate(page_ir["blocks"]):
        try:
            content.append(render(b["block"], b.get("props", {})))
        except Exception as e:
            raise RuntimeError(
                f"{page_ir['key']} block[{i}] '{b.get('block')}': {e}"
            ) from e

    doc = {
        "version": "0.4",
        "title": page_ir.get("title") or page_ir["key"].title(),
        "type": el_type,
        "metadata": {
            "template_type": template_type,
            "include_in_zip": "1",
            "elementor_pro_required": "1",
            # Opt-in per page. Canvas skips get_header()/get_footer(), so a
            # Theme Builder header and footer do NOT render on a Canvas page.
            # A kit whose footer must appear on every page (legal links on a
            # German site) sets "elementor_header_footer" (Full Width), which
            # keeps edge-to-edge sections and renders the theme parts. Absent
            # the key, output is unchanged.
            "wp_page_template": page_ir.get("wp_page_template") or (
                "elementor_canvas" if dtype == "page" else "default"),
        },
        "content": content,
        "page_settings": {
            "hide_title": "yes",
            "background_background": "classic",
        },
    }
    # Theme Builder display conditions. The contract is right that conditions
    # live in `_elementor_conditions` post meta rather than in the document —
    # but the Template Kit Import plugin copies them across from this metadata
    # key on import (vendor/template-kit-import/inc/class-builder-elementor.php),
    # so shipping them here is what turns "now go and assign the header to the
    # whole site" from a manual step into no step at all.
    #
    # A header or footer with no condition is imported and then never rendered,
    # which reads as a broken kit, so site-wide is the default.
    conditions = page_ir.get("conditions")
    if conditions is None:
        conditions = DEFAULT_CONDITIONS.get(dtype)
    if conditions:
        doc["metadata"]["elementor_pro_conditions"] = conditions

    if page_ir.get("seo"):
        doc["metadata"]["forge_seo"] = page_ir["seo"]
    # Opt-in URL path, e.g. "/services/garden-rooms/". The Template Kit
    # Importer (1.2+) sets the page slug and parent page from it, so nested
    # URLs survive import. Absent the key, output is unchanged.
    if page_ir.get("slug") and dtype == "page":
        doc["metadata"]["forge_slug"] = page_ir["slug"]
    return doc


def compile_site(ir: dict) -> dict[str, dict]:
    """Compile every page in the IR. Returns {filename: document}."""
    reset_ids()
    # Kit-wide button treatment, opt-in like `motion`. Set before any block
    # renders, cleared after, so it can never leak into the next build in the
    # same process — which is exactly how the regression suite runs.
    set_primary_style((ir.get("buttons") or {}).get("primary_style"))
    out = {}
    for page in ir["pages"]:
        slug = page["key"].replace(":", "-")
        out[f"{slug}.json"] = compile_document(page)
    # Entrance animation is a whole-document decision — whether a section is
    # the first on its page, and whether a row is a card grid — so it runs
    # here rather than inside a block factory. Absent `ir["motion"]` it is a
    # no-op and the output is unchanged.
    apply_motion(out, ir.get("motion"))
    set_primary_style(None)
    return out


# ───────────────── symbolic template reference resolution ─────────────────

SYMBOLIC_PREFIX = "@loop:"


def collect_symbolic_refs(docs: dict[str, dict]) -> list[tuple[str, str]]:
    """Find every unresolved @loop:<key> reference. (file, ref)"""
    found = []

    def walk(els, fname):
        for el in els:
            for k, v in (el.get("settings") or {}).items():
                if k in ("template_id", "loop_template_id") and \
                        isinstance(v, str) and v.startswith(SYMBOLIC_PREFIX):
                    found.append((fname, v))
            walk(el.get("elements") or [], fname)

    for fname, doc in docs.items():
        walk(doc.get("content", []), fname)
    return found


def resolve_symbolic_refs(docs: dict[str, dict], mapping: dict[str, int]) -> int:
    """
    Rewrite @loop:<key> -> real WordPress post id.
    Run this AFTER importing loop-item documents, never before.
    """
    n = 0

    def walk(els):
        nonlocal n
        for el in els:
            s = el.get("settings") or {}
            for k in ("template_id", "loop_template_id"):
                v = s.get(k)
                if isinstance(v, str) and v.startswith(SYMBOLIC_PREFIX):
                    key = v[len(SYMBOLIC_PREFIX):]
                    if key in mapping:
                        s[k] = str(mapping[key])   # always string
                        n += 1
            walk(el.get("elements") or [])

    for doc in docs.values():
        walk(doc.get("content", []))
    return n
