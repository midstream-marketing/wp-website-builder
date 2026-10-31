---
name: speed
description: Make a WordPress/Elementor site faster with a measure-change-remeasure loop - PageSpeed Insights medians, one settings group at a time, automatic rollback when mobile LCP/CLS/TBT gets worse. Use for PageSpeed complaints, Core Web Vitals and slow pages.
---

# Speed

Load `core`. Every group is measured before and after; a group that makes mobile metrics worse is rolled back.

## Measure

```
python "${CLAUDE_PLUGIN_ROOT}/tools/perf/psi.py" run baseline              # mobile, median of 3, perf_urls from site.json
powershell -File "${CLAUDE_PLUGIN_ROOT}/scripts/rspeed.ps1" info           # cache plugin, Elementor options, autoload, revisions
node "${CLAUDE_PLUGIN_ROOT}/audit/perf.mjs"                                # TTFB (median of 3 - the first hit is a cold start)
node "${CLAUDE_PLUGIN_ROOT}/audit/imgres.mjs"                              # oversized / undersized images
```

## Fix, in the order that usually pays most on Elementor sites

| Order | Area | How |
|---|---|---|
| 1 | Server / TTFB | Report hosting region or plan mismatch. Recommend; never migrate on your own |
| 2 | Images | Right-size and WebP the LCP image; hero must not be lazy-loaded; CSS background heroes -> image widget (rebuild via Forge or a site script) |
| 3 | Elementor | `rspeed.ps1 elementor` -> `apply` (performance experiments, optimised loading) |
| 4 | Fonts | `rspeed.ps1 fonts` (local Google Fonts, swap), drop unused weights in the kit |
| 5 | Background images | `rspeed.ps1 lazybg` |
| 6 | Caching | Configure the cache plugin the host already has (LiteSpeed, WP Rocket...), in its own settings - never add a second. See GOTCHAS: WP Rocket RUCSS/delay-JS traps |
| 7 | Third-party JS | Pixel, GTM, chat - delaying them can break tracking: **ask first** |
| 8 | Database | `rspeed.ps1 transients apply`; report big autoloaded options |

After each group:

```
python "${CLAUDE_PLUGIN_ROOT}/tools/perf/psi.py" run after-<group>
python "${CLAUDE_PLUGIN_ROOT}/tools/perf/psi.py" compare baseline after-<group>     # exit 2 = worse
powershell -File "${CLAUDE_PLUGIN_ROOT}/scripts/rspeed.ps1" restore sites/<slug>/perf/rollback/<file>.json   # if worse
node "${CLAUDE_PLUGIN_ROOT}/audit/sweep.mjs"     # speed changes can break layout - look
```

`cssfile` vs `cssinline`: on hosts whose cleanup deletes `uploads/elementor/css`, images and styles vanish after a few
days - use `cssinline` there (GOTCHAS).

## Report

Before/after per page (score, LCP, CLS, TBT), groups kept and rolled back, and what needs the host or the client.
Lab numbers move run to run; field data (28 days) will lag.
