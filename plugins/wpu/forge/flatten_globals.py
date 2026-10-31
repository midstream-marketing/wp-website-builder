#!/usr/bin/env python3
"""flatten_globals.py — resolve __globals__ into literal values.

The kit's whole design is that colour and typography live once, in global.json,
and every template points at it. That is right until the importer that applies
global.json is unavailable — a broken Template Kit plugin, a host blocking the
API, a client on a locked-down install. Then every template renders unstyled,
because `globals/colors?id=surf002` resolves to nothing.

This produces a second, dependency-free copy: the same documents with the
tokens resolved in place, importable one at a time through
Elementor > Templates > Saved Templates > Import Templates.

    python flatten_globals.py clients/<name>/out -o clients/<name>/out-flat

The trade-off is stated plainly because it is real: flattened templates cannot
be re-skinned by editing one file. Ship the kit build when the importer works;
ship this when it does not.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

REF = re.compile(r"globals/(colors|typography)\?id=([\w-]+)")


def load_tokens(kit: dict) -> tuple[dict, dict]:
    ps = kit.get("page_settings", {})
    colors = {c["_id"]: c["color"]
              for c in ps.get("system_colors", []) + ps.get("custom_colors", [])}
    typos = {t["_id"]: t
             for t in ps.get("system_typography", []) + ps.get("custom_typography", [])}
    return colors, typos


def flatten_element(el: dict, colors: dict, typos: dict, report: dict) -> None:
    s = el.get("settings") or {}
    g = s.pop("__globals__", None)
    if g:
        for control, ref in g.items():
            m = REF.search(ref or "")
            if not m:
                report["malformed"] += 1
                continue
            kind, tok = m.groups()

            if kind == "colors":
                hexval = colors.get(tok)
                if hexval is None:
                    report["dangling"].append(f"{control}={tok}")
                    continue
                s[control] = hexval
                report["colors"] += 1
            else:
                token = typos.get(tok)
                if token is None:
                    report["dangling"].append(f"{control}={tok}")
                    continue
                # `title_typography_typography` -> prefix `title_typography`.
                # The token stores its own keys under a plain `typography_`
                # prefix, so each suffix is re-hung off the widget's prefix.
                if not control.endswith("_typography"):
                    report["malformed"] += 1
                    continue
                prefix = control[: -len("_typography")]
                for k, v in token.items():
                    if not k.startswith("typography_"):
                        continue
                    s[prefix + k[len("typography"):]] = v
                s[control] = "custom"
                report["typography"] += 1

    for child in el.get("elements") or []:
        flatten_element(child, colors, typos, report)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir", help="a built kit directory (contains templates/)")
    ap.add_argument("-o", "--dest", required=True)
    a = ap.parse_args()

    src = Path(a.outdir) / "templates"
    kit = json.loads((src / "global.json").read_text(encoding="utf-8"))
    colors, typos = load_tokens(kit)
    print(f"kit tokens: {len(colors)} colours, {len(typos)} typography steps")

    dest = Path(a.dest)
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    total = {"colors": 0, "typography": 0, "malformed": 0, "dangling": []}
    for f in sorted(src.glob("*.json")):
        if f.name == "global.json":
            continue
        doc = json.loads(f.read_text(encoding="utf-8"))
        report = {"colors": 0, "typography": 0, "malformed": 0, "dangling": []}
        for el in doc.get("content", []):
            flatten_element(el, colors, typos, report)
        # Kit-level page settings the document relied on the kit to supply.
        doc.setdefault("page_settings", {})
        (dest / f.name).write_text(json.dumps(doc, indent=1), encoding="utf-8")
        print(f"  {f.name:22} {report['colors']:>4} colour  "
              f"{report['typography']:>3} type"
              + (f"  DANGLING {report['dangling']}" if report["dangling"] else ""))
        for k in ("colors", "typography", "malformed"):
            total[k] += report[k]
        total["dangling"] += report["dangling"]

    print(f"\nresolved {total['colors']} colour + {total['typography']} typography refs")
    if total["malformed"]:
        print(f"WARNING {total['malformed']} malformed ref(s)")
    if total["dangling"]:
        print(f"ERROR {len(total['dangling'])} dangling: {total['dangling'][:6]}")
    else:
        print("no dangling references — these templates need no global kit")

    # Nothing may still point at a global after flattening.
    leftover = sum(1 for f in dest.glob("*.json")
                   if "__globals__" in f.read_text(encoding="utf-8"))
    print(f"templates still carrying __globals__: {leftover}")
    print(f"-> {dest}")


if __name__ == "__main__":
    main()
