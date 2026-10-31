"""Read-only: are __globals__ control names real for the widget they sit on?

V6 validates `settings` keys against the registry but the __globals__ loop
only checks that the ref RESOLVES - so a colour aimed at a control the widget
does not have passes every gate and silently does nothing.
"""
import json, re, collections
from pathlib import Path

R = json.load(open("registry/elementor-registry.json", encoding="utf-8"))
try: ADD = json.load(open("registry/additions.json", encoding="utf-8"))
except Exception: ADD = {}
SUFFIX_OK = ("_color", "_typography", "_background_color")

def controls(w):
    for src in (R.get("widgets", {}), ADD.get("widgets", {}), ADD):
        if isinstance(src, dict) and w in src:
            v = src[w]
            return set(v if isinstance(v, list) else list(v.get("controls", v)))
    return set()

bad = collections.Counter()
seen_widgets = collections.Counter()

def walk(n, wt=None):
    if isinstance(n, dict):
        et, w = n.get("elType"), n.get("widgetType")
        here = w if et == "widget" else wt
        g = (n.get("settings") or {}).get("__globals__") or {}
        if et == "widget" and w:
            known = controls(w)
            if known:
                seen_widgets[w] += 1
                for k in g:
                    if k not in known:
                        bad[(w, k)] += 1
        for v in n.values(): walk(v, here)
    elif isinstance(n, list):
        for v in n: walk(v, wt)

files = sorted(Path("clients").glob("*/out/templates/*.json"))
for f in files:
    try: walk(json.load(open(f, encoding="utf-8")))
    except Exception: pass
print("scanned %d compiled templates across %d clients\n" %
      (len(files), len({f.parts[1] for f in files})))
print("%-34s %-34s %s" % ("widget", "globals key (not a control)", "count"))
print("-"*86)
for (w, k), n in bad.most_common(25):
    print("%-34s %-34s %5d" % (w, k, n))
print("\ntotal mismatched global entries:", sum(bad.values()))
