---
name: doctor
description: Audit, debug and fix an existing WordPress/Elementor/WooCommerce site through the WPU Bridge - layout breaks, sideways scroll, broken images, fatals, dead widgets, client revision lists, and WP Site Doctor instruction files. Use when a client reports something broken or "looks wrong", or for a health check.
argument-hint: "[what the client reported | path to an instruction file]"
---

# Doctor: audit and fix

Load `core`; for anything visual also `visual-change`. Input: `$ARGUMENTS`.

## Standard audit (always first)

```
powershell -File "${CLAUDE_PLUGIN_ROOT}/scripts/rdoctor.ps1"
powershell -File "${CLAUDE_PLUGIN_ROOT}/scripts/rwpphp.ps1" "${CLAUDE_PLUGIN_ROOT}/php/site-info.php"
node "${CLAUDE_PLUGIN_ROOT}/audit/audit.mjs"
powershell -File "${CLAUDE_PLUGIN_ROOT}/scripts/rwpphp.ps1" "${CLAUDE_PLUGIN_ROOT}/php/dead-widgets.php"
powershell -File "${CLAUDE_PLUGIN_ROOT}/scripts/rwpphp.ps1" "${CLAUDE_PLUGIN_ROOT}/php/orphans.php"
powershell -File "${CLAUDE_PLUGIN_ROOT}/scripts/rlog.ps1" 300
```

If `rdoctor` cannot reach the bridge, or the site shows a white screen / "critical error" / HTTP 500, stop here and
load the `rescue` skill: the fix goes through the hosting, not the bridge.

**Write the findings down before fixing anything** - fixing as you discover leaves half-finished work in five places.

## Instruction files (from WP Site Doctor)

A client revision list or an instruction file (`sites/<slug>/instructions/*.md`) is worked item by item. Items marked
**"needs client confirmation"** (team members, certifications, prices, permits, structural pivots) are not done - they
are listed back as questions. Each finished item gets its evidence (screenshot or assertion output).

## Per fix

1. Reproduce at the width/state reported (`rband.mjs`, `shot.mjs`).
2. Root cause, not symptom: `probe.mjs` / `whichrule.mjs` for CSS, the log for PHP, `grep -n -i` in
   `${CLAUDE_PLUGIN_ROOT}/knowledge/GOTCHAS.md` for the symptom.
3. Smallest change: a site script in `sites/<slug>/scripts/` with the dry-run/apply convention
   (`$apply = in_array('apply', $argv, true);`), or an mu-plugin via `rfile put`. Security skill for any PHP.
4. Verify: screenshot **and** a scripted assertion.
5. Regress: full `audit.mjs`.

## Report

What was broken, the cause, what changed, the evidence, what is still open - and anything unverified said plainly.
Append site lessons to SITE-NOTES; environment lessons through `/wpu:learn`.
