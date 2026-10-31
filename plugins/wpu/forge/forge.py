#!/usr/bin/env python3
"""forge.py — CLI. intake.json -> validated, importable Elementor kit."""
import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from forge.tokens import build_kit
from forge.planner import plan
from forge.compiler import compile_site, collect_symbolic_refs
from forge.validator import validate
from forge.kit import write_kit
from forge.reference import load_profile, fold_profile, conformance

PRESETS = Path(__file__).resolve().parent / "presets"


def apply_preset(intake: dict, copy: dict, trade: str) -> tuple[dict, dict]:
    """Fold a trade preset in underneath the client's own answers.

    The client file always wins. A preset supplies the parts that are the same
    for every plumber — service scope, process, the questions homeowners
    actually ask — so an intake only has to carry what is genuinely specific:
    name, area, contact, brand.
    """
    path = PRESETS / f"{trade}.json"
    if not path.exists():
        avail = ", ".join(sorted(p.stem for p in PRESETS.glob("*.json")))
        sys.exit(f"Unknown trade '{trade}'. Available: {avail}")
    p = json.loads(path.read_text(encoding="utf-8"))

    biz = {**p.get("business", {}), **intake.get("business", {})}
    intake["business"] = biz
    intake["seo"] = {**p.get("seo", {}), **intake.get("seo", {})}
    if not intake.get("services"):
        intake["services"] = p.get("services", [])
    if not biz.get("usp") and p.get("trust_items"):
        biz["usp"] = p["trust_items"]

    brand = intake.setdefault("brand", {})
    for key, hint in (("colors", "palette_hint"), ("fonts", "fonts_hint")):
        if not brand.get(key) and p.get(hint):
            brand[key] = {k: v for k, v in p[hint].items() if k != "note"}

    home = copy.setdefault("home", {})
    if not home.get("steps") and p.get("process"):
        home["steps"] = p["process"]
    faq = copy.setdefault("faq", {})
    if not faq.get("faqs") and p.get("faqs"):
        faq["faqs"] = p["faqs"]

    copy.setdefault("_preset", {})["photo_brief"] = p.get("photo_brief", [])
    copy["_preset"]["image_search"] = p.get("image_search", [])
    return intake, copy


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("intake")
    ap.add_argument("-o", "--out", default="out")
    ap.add_argument("--copy", help="copy.json from the SEO agent")
    ap.add_argument("--ir", help="ir.json from the layout agent (skips the planner)")
    ap.add_argument("--trade", help="trade preset to fill the gaps "
                                    "(plumber, roofing, electrician, tree-surgeon, "
                                    "landscaping, turf, general-contractor)")
    ap.add_argument("--profile", help="design profile from analyse_reference.py; "
                                      "fills brand gaps and reports divergence")
    ap.add_argument("--strict", action="store_true", help="V6 control check fails the build")
    ap.add_argument("--no-zip", action="store_true")
    a = ap.parse_args()

    # Explicit UTF-8 both ways. read_text() defaults to the OS locale encoding,
    # which on Windows is cp1252 — every em-dash and curly quote in the copy
    # silently turns into mojibake before it ever reaches the compiler.
    intake = json.loads(Path(a.intake).read_text(encoding="utf-8-sig"))
    copy = json.loads(Path(a.copy).read_text(encoding="utf-8-sig")) if a.copy else {}

    if a.trade:
        intake, copy = apply_preset(intake, copy, a.trade)
        print(f"trade preset: {a.trade}")

    # The reference is folded in after the trade preset and before the kit is
    # built, so it can fill a gap the preset left but never overwrite one the
    # client answered. Both sit underneath the intake for the same reason.
    profile = load_profile(a.profile) if a.profile else None
    if profile:
        print(f"reference: {profile.get('url') or profile.get('image')}")
        for note in fold_profile(intake, profile):
            print(f"  {note}")

    kit_doc = build_kit(intake.get("brand", {}) or {},
                        title=f"{intake['business']['name']} Global Kit")
    ir = json.loads(Path(a.ir).read_text(encoding="utf-8-sig")) if a.ir else plan(intake, copy)
    docs = compile_site(ir)

    report = validate(docs, kit_doc, strict_controls=a.strict)
    print(report.text())

    if profile:
        print("\nreference conformance:")
        print("\n".join(conformance(intake, profile)))

    unresolved = collect_symbolic_refs(docs)
    if unresolved:
        print(f"\n{len(unresolved)} symbolic template ref(s) to resolve at import:")
        for f, r in unresolved:
            print(f"  {f} -> {r}")

    if not report.ok:
        print("\nBuild blocked. Fix errors above.", file=sys.stderr)
        sys.exit(1)

    Path(a.out).mkdir(parents=True, exist_ok=True)
    Path(a.out, "ir.json").write_text(json.dumps(ir, indent=1), encoding="utf-8")
    bundle = None
    if ir.get("bundle_images"):
        # The bundle dir is relative to the intake file's directory.
        bi = ir["bundle_images"]
        bundle = {"dir": Path(a.intake).resolve().parent / bi["dir"],
                  "folder": bi["folder"]}
    result = write_kit(a.out, intake["business"]["name"], kit_doc, docs,
                       zip_it=not a.no_zip, bundle=bundle)
    print(f"\n{len(docs)} template(s) + global kit -> {result}")


if __name__ == "__main__":
    main()
