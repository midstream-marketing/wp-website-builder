---
name: handover
description: Pre-launch and handover - the QA checklist, launch steps with the client's go-ahead, final backup, bridge removal and credential cleanup. Use when a build or a round of work is finished and the client is about to receive it.
---

# Handover

Load `core`. Work through `${CLAUDE_PLUGIN_ROOT}/knowledge/CHECKLIST-HANDOVER.md` item by item, with evidence.

1. Automated gate: `audit.mjs` (exit 0), `fonts.mjs`, `sweep.mjs full` (look at every screenshot), `responsive.mjs`,
   `seo.mjs`, `dead-widgets.php`, `orphans.php`, `rlog.ps1` (nothing recent - check timestamps).
2. Content: no lorem ipsum or demo leftovers, no previous theme/agency names, real emails and phones, policy pages
   flagged to the client as templates for their lawyer. Search the site for developer text (GOTCHAS).
3. WooCommerce (if it sells): a payment gateway on, a test order through to the email, shipping thresholds match the copy.
4. Launch - **only with the client's go-ahead**: search engines on (plan `site.discourage_search_engines: false`),
   caches purged, `outside.py` clean of high findings.
5. Final backup, copied off the server.
6. Keep the permanent mu-plugins the site uses (`wpu-seo-schema.php`, `wpu-hardening.php`). **Delete the WPU Bridge**
   (this deletes every connection key) and revoke any Application Password made for the toolkit.
7. Members remove the site's secrets: `scripts/wpu-secret.ps1 rm <slug>` (in their own terminal). If hosting access
   was used: the client (or member) revokes the cPanel API token and removes any SFTP user made for us.
8. SITE-NOTES: final state, what is provisional, open questions - it stays in the workspace for aftercare.

Report: what passed (with evidence), what is unverified, what the client must do.
