---
name: secure
description: Security audit and hardening of a WordPress site - outside scan, inside audit (versions, users, files, settings), every custom plugin re-scanned, and a switchable hardening mu-plugin applied only with approval. Use for security checks, after a hack, and before handover.
---

# Security

Load `core` and `wp-plugin-security`. Read-only first; nothing changes without the member's yes.

## Audit

```
python "${CLAUDE_PLUGIN_ROOT}/tools/security/outside.py"                                        # what anyone can see
powershell -File "${CLAUDE_PLUGIN_ROOT}/scripts/rwpphp.ps1" "${CLAUDE_PLUGIN_ROOT}/php/security-info.php"   # versions, updates, users, files, settings
powershell -File "${CLAUDE_PLUGIN_ROOT}/scripts/rwpphp.ps1" "${CLAUDE_PLUGIN_ROOT}/php/plugin-files.php"
```

Also: abandoned plugins (no update in 2+ years), nulled themes/plugins, admins without 2FA, backups (is one running,
when did it last finish - `php/updraft-backup-status.php`), form spam protection and SMTP (forms that fail silently).
Every custom plugin and mu-plugin on the site: fetch with `rfile get`, run
`python "${CLAUDE_PLUGIN_ROOT}/skills/wp-plugin-security/scripts/wp_security_scan.py" <folder>`, then the
`security-reviewer` agent reviews it without having seen it built.

## Harden (approval required)

Prefer settings in the security plugin the site already has (Wordfence, Solid Security...). The WPU mu-plugin covers
the small things, each switch off until turned on:

```
powershell -File "${CLAUDE_PLUGIN_ROOT}/scripts/rfile.ps1" put "${CLAUDE_PLUGIN_ROOT}/site-plugins/wpu-hardening.php" mu-plugins/wpu-hardening.php
powershell -File "${CLAUDE_PLUGIN_ROOT}/scripts/rwpphp.ps1" "${CLAUDE_PLUGIN_ROOT}/php/hardening-set.php" on=no_file_edit,no_user_listing,no_author_scan,hide_version,headers
...then the same with apply
```

`no_xmlrpc` breaks Jetpack and the WordPress mobile app - ask. Login URL changes, firewalls and malware scanning belong
to the security plugin or host. File permissions (`wp-config.php` 640, folders 755, files 644) can be fixed with
`tools/hosting/sftp.py chmod <mode> <path> apply` when hosting access is set up (see the `rescue` skill). Server
rules and the host firewall stay a written task for the host - not an automated change. Re-run `outside.py` to confirm.

## After a hack

Don't clean first. Preserve: `rlog.ps1`, the bridge audit log, a full backup (`tools/hosting/cpanel.py backup-now` where
there is cPanel), and the server's raw logs (`sftp.py logs`). Then look for PHP in uploads, unknown
admins, modified core files, injected options. Recommend a professional clean-up when the scope is unclear.

## Report

Findings by severity with evidence, what was changed (and how to undo), what the host or client must do.
Never call a site "secure" or "unhackable" - say what was checked and what remains.
