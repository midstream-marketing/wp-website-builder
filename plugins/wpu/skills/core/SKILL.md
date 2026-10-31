---
name: core
description: The working method for ALL WordPress / Elementor / WooCommerce site work in WP Ultimate Build - building, fixing, SEO, posts, speed, security, plugins. Load it before running any wpu script, touching a client site through the WPU Bridge, or answering how the toolkit works. Merged from WP Site Doctor, WP Site Build and the Elementor Forge handbook.
---

# WP Ultimate Build - working method

One toolkit for the whole life of a client site: build it (Elementor Forge + site plan), fix it
(Doctor), optimise it (SEO, posts, speed, security), hand it over. Everything reaches the site
through the **WPU Bridge** plugin. When WordPress itself is down (and the bridge with it), `/wpu:rescue` goes in
through the hosting instead - SFTP/SSH or a cPanel API token.

## Where things are

| | Path |
|---|---|
| This plugin (read-only - never write here) | `${CLAUDE_PLUGIN_ROOT}` |
| Wrappers (PowerShell) | `${CLAUDE_PLUGIN_ROOT}/scripts/*.ps1` |
| Browser audits (Node + Playwright, system Chrome) | `${CLAUDE_PLUGIN_ROOT}/audit/*.mjs` |
| Read-only and dry-runnable PHP scripts | `${CLAUDE_PLUGIN_ROOT}/php/*.php` |
| Site plan engine | `${CLAUDE_PLUGIN_ROOT}/build/apply-plan.php` |
| Elementor Forge (compiler, 38 blocks, registry, validator) | `${CLAUDE_PLUGIN_ROOT}/forge/` |
| SEO / speed / security tools (Python, stdlib) | `${CLAUDE_PLUGIN_ROOT}/tools/` |
| Permanent site mu-plugins | `${CLAUDE_PLUGIN_ROOT}/site-plugins/` |
| Knowledge: traps, playbook, handbook | `${CLAUDE_PLUGIN_ROOT}/knowledge/` |
| **The workspace** (where Claude Code is open) | `sites/<slug>/` - one folder per client |

Per client: `sites/<slug>/site.json` (settings, NO secrets), `SITE-NOTES.md` (what this site has
taught us - read it first), `plan.json`, `intake.json`, `copy.json`, `ir.json`, `design-spec.json`,
`shots/`, `seo/`, `perf/`, `security/`, `scripts/` (one-off fix scripts for this site).

**Pick the site for every command** - there is deliberately no default, because these scripts write to
live client sites:

```powershell
$env:WPU_SITE = 'acme-roofing'
powershell -File "${CLAUDE_PLUGIN_ROOT}/scripts/rdoctor.ps1"
```

(In Bash on Windows: `WPU_SITE=acme-roofing powershell -File ...`.) Node and Python tools read the same variable.

## The one rule

**You cannot fix or build what you cannot see.** Every failure in this work traces back to changing
something and assuming the result. The loop for every change:

1. **Plan** it - in the site plan, a changes file, or a dry-runnable script.
2. **Dry run** - read every line of what will change.
3. **Apply** - the guard hook makes the member approve every live write. Never try to get around it.
4. **See it** - `audit/sweep.mjs` screenshots at 390 / 768 / 1440, then *look at them*.
5. **Assert it** - `audit/audit.mjs`, `audit/fonts.mjs`, `audit/seo.mjs`, or a targeted `audit/probe.mjs`.
6. **Regress** - re-run the full audit. Fixes break other things constantly.

Never report something as done that you have not seen working. A green build is not evidence: grep the
output for the values you believe you set.

## Toolkit

**Bridge wrappers** (`scripts/`): `rdoctor` (preflight - run first on any new host), `rwpphp <script.php> [apply]`,
`rplan <plan.json> [apply]`, `rtemplate <file.json>`, `rmedia <file> [alt]`, `rfile get|put`, `rlog`,
`rinventory` (all public URLs), `rseo list|push|rollback`, `rposts list|push`, `rspeed info|<group> [apply]|restore`.
Local LocalWP twins: `wp`, `wpphp`, `php`, `plan`, `detect`, `push-mu`.

**Audits** (`audit/`): `audit` (status, sideways scroll, broken images, JS errors, thin pages), `sweep` (screenshots),
`fonts`, `probe` (which CSS rule wins), `whichrule`, `align`, `imgres`, `rband`, `hscroll`, `responsive`, `seo`,
`shot`, `shotdiff`, `perf`, `devices`, `install-bridge`, `install-plugin-zip`.

**PHP** (`php/`, run through `rwpphp`): `site-info` (start here), `dead-widgets`, `orphans`, `elementor-info`,
`templates`, `conditions`, `theme-locations`, `security-info`, `speed-info`, `speed-apply`, `hardening-set`,
`url-inventory`, `fatal-tail`, `find-text`, `export-elementor`, `updraft-backup-start|status`, and more.

**Forge** (`forge/forge.py`): intake + copy (+ IR) -> validated Elementor Template Kit. Rules in the `elementor-contract`
skill. **Tools**: `tools/seo/dataforseo.py`, `tools/seo/seo_plan.py`, `tools/perf/psi.py`, `tools/security/outside.py`,
`tools/hosting/sftp.py` and `tools/hosting/cpanel.py` (the back door - see the `rescue` skill).

Run Node and Python from the workspace so outputs land in the site folder:
`node "${CLAUDE_PLUGIN_ROOT}/audit/audit.mjs"`, `python "${CLAUDE_PLUGIN_ROOT}/tools/seo/dataforseo.py" ...`.

## Rules for every change

1. **Native Elementor controls before CSS.** Container/flex/grid settings and the kit's global colours and fonts.
   Unavoidable CSS goes in the element's own Custom CSS using `selector`, never a page-wide blob.
2. **Never hand-write Elementor JSON.** Agents emit IR; only `forge/src/forge/blocks.py` authors element trees.
   Round-trip any JSON before writing `_elementor_data` or kit settings - a failed decode blanks the page.
3. **Never edit theme or plugin files.** Site PHP goes in an mu-plugin (`rfile put ... mu-plugins/<site>-*.php`).
4. **Every PHP file you write passes the `wp-plugin-security` skill** - rules, scanner, and the Security review
   block in the delivery. That includes mu-plugins and one-off scripts that write.
5. **Lint after every PHP edit** (`rfile put` refuses unparseable PHP; locally `scripts/php.ps1 -l`).
   Never paste code out of a Grep result - Grep escapes characters for display.
6. **Media only through `rmedia`** - host scanners delete files a script writes into uploads/.
7. **Dry-run everything.** Hosts kill long requests (30-170 s); idempotent steps mean a re-run finishes the job.
8. **Diagnose, don't guess.** CSS "not applying" -> `probe.mjs`/`whichrule.mjs`. A fix that "did not work" is
   usually a stale `?ver=` or a page cache - check before re-diagnosing.
9. **Don't trust one timing.** The first request after a change is a cold start; `perf.mjs` takes a median of 3.
10. **Search engines stay discouraged until launch**, and launch is the client's call.
11. **Report honestly.** Failed test -> say so with the output. Skipped something -> say that. Couldn't verify ->
    say "unverified". A clean summary over broken work is worse than no summary.

## Ask the member first

- Deleting pages, products, plugins, media, users
- Anything touching payments, tax, shipping rules or real prices
- Legal or policy copy (always a template for the client's lawyer)
- Going live: search engines on, domain, removing "coming soon"
- Sending email to real people; buying licences
- Turning off XML-RPC, delaying tracking scripts, changing a security plugin's settings
- Changing the design beyond the reported defect

Fix without asking: broken layouts, sideways scroll, overlapping text, missing fonts, broken images, 404s,
PHP notices/fatals, dangling menu links, clear accessibility failures.

## Never fabricate

Reviews, testimonials, ratings, client logos, stats, awards, years in business, licence numbers, certifications,
lab results, prices, or "trusted by" claims. An empty slot with a written brief is a deliverable; an invented
fact is a liability that ships. A content refusal never licenses a structural one - not faking reviews does not
mean dropping the review section's design.

**Client-facing copy and guides:** never label images as stock, licensed, reference, example, inspiration-only or
placeholder, and no "coming soon / will be added later" lines. Stock images are normal design imagery the client
swaps later. What is still provisional is tracked privately in `SITE-NOTES.md`, never on the site.

## Secrets

Keys, Application Passwords, wp-admin passwords, hosting passwords (`sftp_pass`), cPanel API tokens (`cpanel_token`)
and the DataForSEO login live in each member's encrypted store,
**set by the member in their own terminal**:

```powershell
powershell -File "${CLAUDE_PLUGIN_ROOT}/scripts/wpu-secret.ps1" set <slug> key
powershell -File "${CLAUDE_PLUGIN_ROOT}/scripts/wpu-secret.ps1" set global dataforseo_login
```

Never ask anyone to paste a secret into the chat, never write one into a file, never print one. The guard hook
blocks it; if it fires, tell the member the `set` line to run instead.

## Session ritual

**Start:** set `WPU_SITE`; read `sites/<slug>/SITE-NOTES.md`; `rdoctor.ps1`; `rwpphp.ps1 php/site-info.php`.
State in one line what is broken or what this session will finish.

**End:** `audit.mjs` + `fonts.mjs` + `sweep.mjs` and look at the screenshots. Append what this site taught us to
`sites/<slug>/SITE-NOTES.md` (decisions, template/page IDs, what is provisional). Anything learned about the
*environment* (a host, a plugin, Elementor, Windows) goes through `/wpu:learn` so it reaches the whole team.

## Knowledge - search, don't read whole

- `knowledge/GOTCHAS.md` - ~530 traps from 40+ client sites, symptom -> cause -> rule. `grep -n -i "<symptom>"`.
- `knowledge/BUILD-PLAYBOOK.md` - build phases 0-8, each with a gate.
- `knowledge/CHECKLIST-HANDOVER.md`, `knowledge/CHECKLIST-DOCTOR.md` - QA gates.
- `knowledge/REMOTE.md` - how the bridge works, its safety model, and the eight host traps it handles.
- `knowledge/handbook/00-SOUL.md` ... `06-CASE-FILES.md` - design method, copy and SEO, build contract, case files.
- `knowledge/COMPILER-CONTRACT.md` - the Elementor JSON contract.

## Commands

`/wpu:new-site` set up a client - `/wpu:build` design to Elementor - `/wpu:doctor` audit and fix - `/wpu:seo` -
`/wpu:posts` - `/wpu:speed` - `/wpu:secure` - `/wpu:plugin` custom plugin - `/wpu:rescue` site down / hosting-level fix -
`/wpu:handover` - `/wpu:learn`.
