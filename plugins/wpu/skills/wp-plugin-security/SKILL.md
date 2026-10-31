---
name: wp-plugin-security
description: Hardening rules, self-audit checklist and an automated scanner for WordPress code. Use this skill EVERY time you write, edit, extend, review, debug or package a WordPress plugin, mu-plugin, theme function, WooCommerce extension, Elementor widget, custom endpoint, admin settings page, shortcode, or any PHP snippet destined for a WordPress site — even a "quick" 20-line snippet, even when the user only asks for a feature and says nothing about security. Also use it when reviewing third-party or client plugin code for vulnerabilities, when a site has been hacked, or when the user asks whether code is safe. Every delivery must end with the Security review block defined here.
---

# WordPress plugin security

WordPress plugins are the single biggest source of site compromises — not because PHP is unsafe, but because plugin code repeatedly makes the same six or seven mistakes. This skill exists so those mistakes never make it into a delivered file.

Two working rules:

1. **Assume the input is hostile and the visitor is unauthenticated.** Every request parameter, every option value, every uploaded file, every URL, every value coming back from an external API is attacker-controlled until proven otherwise.
2. **Never claim code is unhackable.** Say what was hardened, what the residual risks are, and what the site owner still has to do. Overclaiming is itself a security failure — it stops people from patching.

## The seven rules that prevent almost every real-world plugin CVE

Apply all seven to every file. They are ordered by how often their absence gets sites hacked.

**1. Every state change needs a capability check AND a nonce.**
Capability answers *are you allowed?*; nonce answers *did you mean to?*. Missing either one is broken access control or CSRF — together these are the majority of plugin CVEs.

```php
if ( ! current_user_can( 'manage_options' ) ) { wp_die( esc_html__( 'Not allowed.', 'td' ), 403 ); }
check_admin_referer( 'td_save_settings' );   // admin forms
check_ajax_referer( 'td_ajax', 'nonce' );    // admin-ajax
```
Never use `is_admin()` as a permission check — it only means "this is an admin-side request", not "this user is an admin". Never use `is_user_logged_in()` where a capability is what you mean. Pick the narrowest capability that fits (`edit_posts`, `manage_woocommerce`, `edit_post` with the object ID) rather than defaulting to `manage_options` everywhere.

**2. Sanitize on input, escape on output — late, and matched to context.**
Sanitizing is not escaping. A value can be stored clean and still break out of the context it lands in.

| Where the value lands | Use |
|---|---|
| HTML text | `esc_html()` |
| Attribute | `esc_attr()` |
| URL (`href`, `src`) | `esc_url()` (`esc_url_raw()` when storing) |
| Inside `<script>` / JS var | `wp_json_encode()`, or `esc_js()` for a quoted string |
| Textarea | `esc_textarea()` |
| Rich text the editor allows | `wp_kses_post()` |
| Translated string | `esc_html__()`, `esc_attr_e()` — translations are data too |

Escape at the point of output, not "earlier somewhere". Input side: `sanitize_text_field`, `sanitize_email`, `sanitize_key`, `sanitize_hex_color`, `absint`, `esc_url_raw`, `wp_kses`. **Validate** as well as sanitize: check the value is in an allowlist, in range, or matches an expected ID.

**3. Never build SQL by concatenation.**

```php
$rows = $wpdb->get_results( $wpdb->prepare(
    "SELECT * FROM {$wpdb->prefix}td_leads WHERE status = %s AND id = %d", $status, $id
) );
```
`%s`/`%d`/`%f` only. Placeholders cannot be used for table or column names or for `ORDER BY` direction — allowlist those against a hard-coded array instead. Reach for `WP_Query`, `get_posts`, `get_option` before writing raw SQL at all.

**4. Lock down every endpoint you register.**
- `wp_ajax_nopriv_*` exposes an action to the entire internet. Only register it when anonymous access is genuinely required, and treat that handler as a public API.
- REST routes need a real `permission_callback`. `__return_true` is only acceptable for genuinely public read-only data, and say so in a comment.
- `admin_post_*` and `admin_post_nopriv_*` follow the same rules as AJAX.
- Authorization is per-object, not just per-role: check the requested ID actually belongs to the current user (`current_user_can( 'edit_post', $post_id )`), otherwise you have an IDOR.

**5. Treat files and paths as dangerous.**
No user-controlled value inside `include`/`require`. Never accept an arbitrary path parameter — map a whitelisted key to a path. For uploads use `wp_handle_upload()` with a MIME allowlist and `wp_check_filetype_and_ext()`; never trust the client filename or extension; never allow `.php`, `.phtml`, `.htaccess`. For remote URLs use `wp_safe_remote_get()` (it blocks internal-network SSRF) rather than `wp_remote_get()`/`file_get_contents()`.

**6. Ban the sharp tools outright.**
`eval()`, `create_function()`, `assert()` on strings, `extract()`, `unserialize()` on user data (use `json_decode`), `exec`/`shell_exec`/`system`/`passthru`/`popen`, `$_REQUEST` (be explicit about GET vs POST), `$wpdb->query( $_POST[...] )`, `add_filter('upload_mimes')` widening, and dynamic function calls from request data. If a task seems to need one of these, the design is wrong — say so and propose the alternative.

**7. Fail closed, leak nothing.**
Guard every file with `if ( ! defined( 'ABSPATH' ) ) { exit; }`. Prefix every function, class, constant, option, hook, table and CSS class uniquely. Never hard-code API keys, tokens or passwords — read them from options set by the admin or from `wp-config.php` constants, and never echo them back into HTML or JS. Keep error detail out of front-end output. Don't trust `$_SERVER['HTTP_HOST']`, `HTTP_X_FORWARDED_FOR` or `PHP_SELF`; use `home_url()`, `admin_url()`, `sanitize_url()`.

## Workflow

**When writing new code:** design the permission model before the feature — who may call this, authenticated or not, over which endpoint, on which objects. Then write the code with rules 1–7 applied from the first line rather than bolted on.

**When editing existing or third-party code:** read the file first and note what protections already exist; don't remove a nonce or capability check while adding a feature. If the existing code has vulnerabilities outside the scope of the request, report them — fix them if they're small, flag them clearly if they're not.

**Before delivering anything, always:**
1. Re-read your own code against `references/audit-checklist.md` — line by line, not from memory.
2. Run the scanner over the plugin folder:
   ```bash
   python3 scripts/wp_security_scan.py /path/to/plugin-folder
   ```
   It flags unescaped output, raw superglobals, missing nonce/capability checks, SQL concatenation, dangerous functions, unsafe file and HTTP calls. Fix or consciously justify every finding — a suppressed finding needs a one-line comment in the code explaining why it's safe.
3. Write the Security review block below into the chat response.

## Security review block — required in every delivery

Keep it short and concrete. No boilerplate reassurance.

```markdown
**Security review**

- Attack surface: <endpoints, forms, uploads, shortcodes — and who can reach each>
- Controls: <nonces, capabilities, sanitizers, escapers, prepared statements actually used>
- Scanner: <clean, or the findings and why they're acceptable>
- Residual risk: <what this code cannot defend against — e.g. a compromised admin account, a vulnerable host, supply-chain risk in a bundled library>
- On your side: <what the site owner must do — keep WP/PHP updated, least-privilege admin accounts, backups>
```

If the request itself is the risk — storing card numbers in the database, an unauthenticated endpoint that writes options, disabling nonce checks "to make it work" — say so plainly and offer the safe design instead. Shipping it quietly is not helpfulness.

## Reference files

- `references/audit-checklist.md` — the full line-by-line review checklist, plus the WordPress-specific vulnerability patterns behind real plugin CVEs (unauthenticated option update, privilege escalation via role parameter, stored XSS in settings, LFI via template parameter, arbitrary file download, unauthenticated REST write). Read it before the final review pass on any plugin longer than a single function.
- `scripts/wp_security_scan.py` — static scanner, no dependencies, `python3 scripts/wp_security_scan.py <folder>`. Run it on generated code and on client code being audited.
