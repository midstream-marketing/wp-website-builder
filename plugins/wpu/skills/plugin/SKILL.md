---
name: plugin
description: Build a custom WordPress plugin or mu-plugin for a client site - calculators, custom post types, Elementor widgets with real controls, shortcodes, WooCommerce tweaks - spec first, hardened, tested, security-reviewed, then installed through the bridge. Use whenever a site needs custom functionality.
argument-hint: "<what the plugin should do>"
---

# Custom plugin

Load `core` and `wp-plugin-security` (mandatory - every rule, the scanner, and the Security review block). Input: `$ARGUMENTS`.
Work in `sites/<slug>/plugins/<plugin-slug>/` (site-specific) or the team's shared plugins repo (reusable).

1. **Spec** - `SPEC.md`: purpose, every input and output, data stored (options/meta/tables), capabilities, nonces,
   REST/AJAX endpoints, uninstall behaviour. The member confirms it before code.
2. **Build** - unique prefix, namespaced, Settings API, `uninstall.php`, no inline script built from data. Elementor
   widgets get full controls so the client edits them in the panel, never a hard-coded HTML embed. Mobile Safari
   quirks from past plugins: flex-shrink, `-webkit-sticky`, hover-only behaviour on touch, reduced motion as an option.
3. **Test** - `php -l` every file, then exercise it: LocalWP (`scripts/wp.ps1`, `wpphp.ps1`) or a staging site.
   Every form, every endpoint, logged out and logged in, PHP 8.1-8.3 deprecations.
4. **Security gate** - `python "${CLAUDE_PLUGIN_ROOT}/skills/wp-plugin-security/scripts/wp_security_scan.py" <folder>`
   clean of high findings; then the `security-reviewer` agent (fresh context) reviews it. Write `SECURITY.md`.
5. **Package** - `scripts/build-plugin.ps1 <slug> <main.php> <includes-folder>` (forward-slash zip; never
   Compress-Archive). WP Engine refuses PHP-written .php files - install the zip through wp-admin
   (`audit/install-plugin-zip.mjs`) there.
6. **Install on staging first**, verify with the audits, then live with the member's approval.

Deliver: the zip, `SPEC.md`, `SECURITY.md` (the Security review block), and how to configure it.
