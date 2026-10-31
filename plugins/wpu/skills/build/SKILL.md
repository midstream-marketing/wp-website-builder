---
name: build
description: Build or rebuild an Elementor site from a Claude Design canvas, reference websites, an XD/Figma/screenshot mockup, or just a brief - through Elementor Forge, the site plan and the WPU Bridge, with a render-and-compare gate. Use for new sites, page rebuilds and new sections.
argument-hint: "[Claude Design link | reference URLs | brief]"
---

# Build: design to Elementor

Load `core`, then `elementor-contract` and `design-fidelity`. Read `${CLAUDE_PLUGIN_ROOT}/knowledge/BUILD-PLAYBOOK.md`
for the phase gates and `${CLAUDE_PLUGIN_ROOT}/knowledge/handbook/01-DESIGN-METHOD.md` + `02-COPY-AND-SEO.md`.
Input: `$ARGUMENTS`. Site folder: `sites/$WPU_SITE/`.

## 0. Intake

`intake-agent` writes `intake.json` (schema `${CLAUDE_PLUGIN_ROOT}/forge/schemas/intake.schema.json`). A trade preset
(`forge/presets/*.json`: electrician, general-contractor, hvac, landscaping, plumber, roofing, tree-surgeon, turf)
supplies the generic parts. Missing facts become one batch of questions - never invented.

## 1. Design source -> design-spec.json + tokens

- **Claude Design link**: open it (the session is signed in with the org account, so `/artifacts` or the Artifact
  read can reach it). Measure, don't eyeball: colours, fonts, spacing, radii, section devices. 
- **Reference site URL**: `python "${CLAUDE_PLUGIN_ROOT}/forge/analyse_reference.py" <url>` gives the measured palette,
  fonts, radii and techniques. Use structure and feel only - never copy a reference's text, images, logo or brand.
- **Screenshot / XD / Figma**: `design-director-agent`; an XD share link is machine-readable (see GOTCHAS).
- **No reference**: the logo is the brief (handbook 01 section 6).

Write `design-spec.json` (schema `${CLAUDE_PLUGIN_ROOT}/forge/schemas/design-spec.schema.json`): the device
inventory and the `never` list.
**Match devices, not section order.** If a device has no block factory, build the factory in `blocks.py` - never substitute.

## 2. Copy

`seo-copy-agent` -> `copy.json`. If `/wpu:seo` has run, use `seo/plan.json` focus keywords per page. Word floors and
human-copy rules from handbook 02; `copy_audit.py` gates it after compile (step 3).

## 3. Compile and validate

`layout-agent` -> `ir.json`. Then from the site folder:

```
python "${CLAUDE_PLUGIN_ROOT}/forge/forge.py" intake.json --copy copy.json --ir ir.json -o out --strict
python "${CLAUDE_PLUGIN_ROOT}/forge/tools/check_fidelity.py" .        # reads design-spec.json + ir.json here
python "${CLAUDE_PLUGIN_ROOT}/forge/tools/copy_audit.py" out          # word floors, one H1, banned phrases
```

Both must pass. Grep the compiled JSON for the values you believe you set.

## 4. Put it on the site (dry run first, every time)

1. Backup: `rwpphp.ps1 php/updraft-backup-start.php` (check retention - see GOTCHAS).
2. `rplan.ps1 plan.json` -> read -> `apply` (site settings, plugins, theme, Elementor settings, kit). Run again
   after plugins install. **Kit on a non-fresh site restyles live pages** - snapshot and ask first.
3. Media: `rmedia.ps1 <files>`; put the ids into the IR/templates. Image URLs with query strings never import.
4. Templates: `rtemplate.ps1 out/templates/*.json`; Theme Builder conditions and menus through the plan.
5. Pages from templates through the plan (`elementor_template`), front page, menus.

## 5. See it and judge it

`node audit/sweep.mjs full`, `audit.mjs`, `fonts.mjs`, `imgres.mjs`, `hscroll.mjs 390`. Then the **visual-critic**
agent (blind to the plan) compares the screenshots with the source at 390/768/1440. Up to three fix loops through
IR -> compile -> re-import. Use the `visual-change` skill for every visual fix.

## 6. Hand back

Preview links for the member, a list of what is provisional (internal), and SITE-NOTES updated with template and
page IDs. Nothing goes live without the member's approval; search engines stay discouraged.
