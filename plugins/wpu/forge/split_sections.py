#!/usr/bin/env python3
"""split_sections.py — one importable template per top-level section.

Some hosts cannot ingest a whole page in one request. CloudLinux LVE, in
particular, kills the PHP worker on CPU or memory and the edge returns a terse
503, which the Elementor UI surfaces as a JSON parse error. The threshold is
per-request, so the fix is smaller requests rather than a smaller site.

This emits each top-level container of a page as its own `section` template.
Import them individually, then drop them into the page in order.

    python split_sections.py clients/<name>/import-no-kit -o clients/<name>/import-sections

Header and footer documents are copied through unchanged — they are already
small and must stay whole to work in Theme Builder.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

WHOLE = {"header", "footer"}          # must import as one document


def count(el: dict) -> int:
    return 1 + sum(count(c) for c in el.get("elements") or [])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="directory of flattened template JSON")
    ap.add_argument("-o", "--dest", required=True)
    ap.add_argument("--max-kb", type=float, default=30.0,
                    help="split pages larger than this (default 30)")
    a = ap.parse_args()

    src, dest = Path(a.src), Path(a.dest)
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    order = []
    for f in sorted(src.glob("*.json")):
        doc = json.loads(f.read_text(encoding="utf-8"))
        stem, dtype = f.stem, doc.get("type", "page")
        size_kb = f.stat().st_size / 1024

        if dtype in WHOLE or size_kb <= a.max_kb:
            shutil.copy(f, dest / f.name)
            order.append((f.name, dtype, round(size_kb, 1), "whole"))
            continue

        for i, block in enumerate(doc.get("content", []), 1):
            part = {
                "version": doc.get("version", "0.4"),
                "title": f"{doc.get('title', stem)} — {i:02d}",
                "type": "section",
                "metadata": {"template_type": "section",
                             "include_in_zip": "1",
                             "elementor_pro_required": "1",
                             "wp_page_template": "default"},
                "content": [block],
                "page_settings": {},
            }
            name = f"{stem}-{i:02d}.json"
            (dest / name).write_text(json.dumps(part, indent=1), encoding="utf-8")
            kb = (dest / name).stat().st_size / 1024
            order.append((name, "section", round(kb, 1), f"{count(block)} elements"))

    print(f"{'file':30} {'type':9} {'KB':>6}  note")
    for n, t, kb, note in order:
        flag = "  <-- still large" if kb > a.max_kb else ""
        print(f"{n:30} {t:9} {kb:>6}  {note}{flag}")
    biggest = max(o[2] for o in order)
    print(f"\n{len(order)} files, largest {biggest} KB "
          f"(was {max((f.stat().st_size / 1024) for f in src.glob('*.json')):.1f} KB)")
    print(f"-> {dest}")


if __name__ == "__main__":
    main()
