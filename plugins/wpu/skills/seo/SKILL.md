---
name: seo
description: On-page SEO for a WordPress site with Rank Math or Yoast, driven by DataForSEO data - keyword research, SERP checks, competitor gaps, a keyword-to-page map, titles, descriptions, focus keywords, schema and internal links, written through the bridge with backup and rollback. Use for SEO setup, audits and keyword work.
argument-hint: "[seed keywords | competitor domains]"
---

# SEO: DataForSEO -> keyword map -> Rank Math / Yoast

Load `core`; read `${CLAUDE_PLUGIN_ROOT}/knowledge/handbook/02-COPY-AND-SEO.md`. Input: `$ARGUMENTS`.
Every tool below writes into `sites/<slug>/seo/`. DataForSEO costs money: say the budget before big pulls
(`--budget`, default $2 per run); cached results are free for 7 days.

## 1. Where the site stands

```
powershell -File "${CLAUDE_PLUGIN_ROOT}/scripts/rseo.ps1" list page,post      # current fields -> seo/current.json
powershell -File "${CLAUDE_PLUGIN_ROOT}/scripts/rinventory.ps1"
node "${CLAUDE_PLUGIN_ROOT}/audit/seo.mjs"                                     # what the RENDERED pages serve
```

No Rank Math or Yoast active -> ask which; install through the site plan (`plugins.install`), then continue.

## 2. Data

```
python "${CLAUDE_PLUGIN_ROOT}/tools/seo/dataforseo.py" ideas "<seed 1>" "<seed 2>" --limit 150
python "${CLAUDE_PLUGIN_ROOT}/tools/seo/dataforseo.py" overview "<exact service + city terms>"
python "${CLAUDE_PLUGIN_ROOT}/tools/seo/dataforseo.py" gap <competitor1> <competitor2>
python "${CLAUDE_PLUGIN_ROOT}/tools/seo/dataforseo.py" serp "<top 5 money keywords>"
python "${CLAUDE_PLUGIN_ROOT}/tools/seo/dataforseo.py" score
```

Location comes from `site.json seo.location` (find exact names with `dataforseo.py locations <city>`).
Missing metrics stay null - never fill them in.

## 3. The map (seo-strategist agent)

The `seo-strategist` agent sets `businessRelevance` on keywords, re-scores, groups them into clusters and writes
`seo/plan.json`: one primary focus keyword per page, title, description, schema per page type
(LocalBusiness/Service/FAQPage/Article/Product), internal links to add, and pages that are missing (a gap keyword
with no page -> propose it, don't create it). Location pages only with genuinely local content - no doorway pages.

```
python "${CLAUDE_PLUGIN_ROOT}/tools/seo/seo_plan.py"     # blocks duplicate focus keywords/titles and ranking promises
```

## 4. Write it (dry run, read, apply)

```
powershell -File "${CLAUDE_PLUGIN_ROOT}/scripts/rseo.ps1" push sites/<slug>/seo/changes.json
powershell -File "${CLAUDE_PLUGIN_ROOT}/scripts/rseo.ps1" push sites/<slug>/seo/changes.json apply
```

Schema needs the permanent mu-plugin once per site (it outlives the bridge):
`rfile.ps1 put "${CLAUDE_PLUGIN_ROOT}/site-plugins/wpu-seo-schema.php" mu-plugins/wpu-seo-schema.php`.
Do not add schema types the SEO plugin already prints (check the rendered page first) - duplicates are errors in Google.

## 5. Verify on the rendered page

`node audit/seo.mjs` again: titles, descriptions, canonicals, one H1, schema present and parseable. A stored value a
cache or the plugin is not serving is not done. Undo: `rseo.ps1 rollback <backup_ref>` (the ref is in `seo/receipts/`).

## 6. Report

Pages changed, keyword per page with volume/difficulty, gaps that need new pages, schema added, the backup ref, and
DataForSEO spend. Observations, estimates and recommendations are labelled as such. **No ranking promises.**
