---
name: new-site
description: Set up a client site in the WP Ultimate Build workspace - site folder, site.json, notes, the WPU Bridge, the member's connection key, preflight and a baseline audit. Use when starting work on a site that has no sites/<slug>/ folder yet, or to import sites from the old wp-site-build / wp-site-doctor folders.
argument-hint: "<slug> <https://site-url>"
---

# New site

Load the `core` skill first if it is not loaded. Arguments: `$ARGUMENTS`.

## 1. Facts (ask only for what is missing, in one batch)

Slug (lowercase-hyphen), live or staging URL, host, whether it is a new build or an existing site,
SEO plugin (Rank Math / Yoast / none yet), target location for SEO (city, state, country), 2-4 competitors,
and **hosting access for emergencies**: does the host give SFTP/SSH (host, port, username, WordPress folder) and/or
cPanel (server hostname, cPanel username)? Ask for the details, never for the passwords - those go in the member's store.

## 2. Folder

Create `sites/<slug>/` with:
- `site.json` from `${CLAUDE_PLUGIN_ROOT}/templates/site.json` - fill name, baseUrl, remote.url, host, seoPlugin,
  seo.location / competitors, urls. **No secrets.**
- `SITE-NOTES.md` from `${CLAUDE_PLUGIN_ROOT}/templates/SITE-NOTES.md`.
- For a build: `plan.json` from `${CLAUDE_PLUGIN_ROOT}/templates/plan.example.json`.

Old toolkit sites: the member runs, in their own terminal,
`powershell -File "${CLAUDE_PLUGIN_ROOT}/scripts/migrate-legacy.ps1" -From "<old folder>"` (dry run), then with `-Apply`.
It moves credentials into their encrypted store and copies each site's notes and plan.

## 3. Bridge

1. `powershell -File "${CLAUDE_PLUGIN_ROOT}/scripts/build-bridge.ps1"` -> `dist/wpu-bridge.zip`.
2. The member installs it: Plugins > Add New > Upload > Activate. (Or `node "${CLAUDE_PLUGIN_ROOT}/audit/install-bridge.mjs"`
   after they saved the wp-admin password with `wpu-secret.ps1 set <slug> adminpass` - the guard will ask them to approve.)
3. The member makes their key: **Tools > WPU Bridge > their name > Make a connection key**, then in their own terminal:
   `powershell -File "${CLAUDE_PLUGIN_ROOT}/scripts/wpu-secret.ps1" set <slug> key`. Never ask for the key in chat.
4. `$env:WPU_SITE='<slug>'; powershell -File "${CLAUDE_PLUGIN_ROOT}/scripts/rdoctor.ps1"` - read every warning
   (stripped Authorization header, low max_execution_time, security plugin, WAF). Record host quirks in SITE-NOTES.

## 3b. Hosting back door (recommended - it is the only way in when the site is down)

Add the `hosting` block to `site.json` (see `${CLAUDE_PLUGIN_ROOT}/templates/site.json`). The member saves
`sftp_pass` (or uses an SSH key) and/or `cpanel_token` with `wpu-secret.ps1 set`. Then:
`python "${CLAUDE_PLUGIN_ROOT}/tools/hosting/sftp.py" trust` (show the member the fingerprint), `sftp.py check`,
`cpanel.py check`. Setting this up on a calm day is what makes `/wpu:rescue` take minutes instead of a support ticket.

## 4. Baseline (existing sites)

`rwpphp.ps1 php/site-info.php`, `rinventory.ps1`, `node audit/audit.mjs`, `node audit/sweep.mjs`, `rseo.ps1 list`,
`python tools/perf/psi.py run baseline`. Note the starting state in SITE-NOTES so later work can show its effect.

## 5. Report

One short summary: what the site is, bridge status and expiry date, the three most important problems found,
and the suggested next command (`/wpu:build`, `/wpu:doctor`, `/wpu:seo`...).
