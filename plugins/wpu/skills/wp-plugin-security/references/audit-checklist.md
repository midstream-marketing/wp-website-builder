# Audit checklist and known vulnerability patterns

Work through this against the actual code, file by file. Contents:

1. Line-by-line checklist
2. The vulnerability patterns behind real plugin CVEs
3. Escaping and sanitizing quick reference
4. Secure snippets to copy

---

## 1. Line-by-line checklist

### File level
- [ ] `if ( ! defined( 'ABSPATH' ) ) { exit; }` at the top of every PHP file.
- [ ] Unique prefix on every function, class, constant, hook, option key, table name, transient, CSS class, JS global.
- [ ] Plugin header present; `Requires at least` and `Requires PHP` set.
- [ ] No secrets, tokens, licence keys or client credentials in the source.
- [ ] No `error_reporting`/`display_errors` changes, no leftover `var_dump`, `print_r`, `error_log` of user data.
- [ ] No backup, `.zip`, `.sql`, `.log` or editor swap files inside the plugin folder.
- [ ] `index.php` silence stub in any writable directory the plugin creates; `.htaccess` deny where uploads are stored.

### Every request handler (form post, AJAX, REST, admin_post, cron trigger, webhook)
- [ ] Capability check with the narrowest capability that fits.
- [ ] Nonce verified: `check_admin_referer()`, `check_ajax_referer()`, or `wp_verify_nonce()` with an explicit `wp_die` on failure.
- [ ] Object-level authorization: does the ID in the request belong to this user?
- [ ] Each parameter read explicitly from `$_POST` or `$_GET` (never `$_REQUEST`), with `isset`/`wp_unslash` and a type-appropriate sanitizer.
- [ ] Values validated, not just sanitized — allowlist, range, enum, existence check.
- [ ] Response escaped for its context; JSON responses via `wp_send_json_success`/`wp_send_json_error`.
- [ ] Rate limiting or a transient lock on anything expensive or emailing, if reachable by anonymous users.
- [ ] Public webhooks verify a signature (HMAC) with `hash_equals()`, not `==`.

### Data in and out of the database
- [ ] All raw SQL via `$wpdb->prepare()` with `%s`/`%d`/`%f`.
- [ ] Table/column names and `ORDER BY`/`ASC|DESC` come from a hard-coded allowlist, never from the request.
- [ ] `LIKE` values wrapped in `$wpdb->esc_like()`.
- [ ] `register_setting()` has a real `sanitize_callback`; the callback rebuilds the array key by key rather than trusting the submitted shape.
- [ ] No user input reaching `update_option`, `update_user_meta`, `wp_update_user`, `add_role` or `wp_insert_user` without a capability check — role/capability parameters are a privilege-escalation vector.
- [ ] Meta registered with `show_in_rest` has a sanitize and auth callback.
- [ ] Custom tables created with `dbDelta()`, charset from `$wpdb->get_charset_collate()`.

### Output
- [ ] Every echoed variable escaped at the point of output, matched to context.
- [ ] Attribute values in double quotes and `esc_attr()`-wrapped.
- [ ] Data passed to JS via `wp_localize_script` or `wp_json_encode` — never string-built into a `<script>` block.
- [ ] Admin settings values escaped on the settings page too (stored XSS hits the admin first).
- [ ] Any HTML-allowing field goes through `wp_kses_post()` or an explicit allowed-tags array.
- [ ] `esc_html__()` / `esc_attr__()` used for translated strings.

### Files, URLs, external calls
- [ ] No request value inside `include`, `require`, `file_get_contents`, `fopen`, `unlink`, `rename`, `copy`.
- [ ] Uploads through `wp_handle_upload()`; MIME allowlist; `wp_check_filetype_and_ext()`; executable extensions rejected; filename via `sanitize_file_name()`.
- [ ] Downloads/exports check capability and resolve paths with `realpath()` inside an expected base directory.
- [ ] Outbound HTTP via `wp_safe_remote_*` with a timeout, and the response body treated as untrusted input.
- [ ] Redirects use `wp_safe_redirect()`; open-redirect parameters validated against an allowlist.
- [ ] Bundled third-party libraries are current and named in the readme with their version.

### Scripts, assets, dependencies
- [ ] Assets enqueued with `wp_enqueue_*` and a version string, conditionally — not on every admin page.
- [ ] No remote script/CSS loaded from a third-party CDN in admin context.
- [ ] Uninstall handled by `uninstall.php` (with `WP_UNINSTALL_PLUGIN` guard) or `register_uninstall_hook`, deleting options and tables cleanly.

---

## 2. Vulnerability patterns behind real plugin CVEs

Check each against the code you just wrote — these are the exact shapes that get plugins mass-exploited.

**Unauthenticated option update.** An AJAX or `admin_post_nopriv` handler that calls `update_option()`. Attackers set `users_can_register` and `default_role=administrator` and register themselves as admin. *Fix:* capability + nonce; never expose option writes to `nopriv`.

**Privilege escalation via user-supplied role.** A registration or profile form that passes `$_POST['role']` into `wp_insert_user`/`wp_update_user`. *Fix:* hard-code the role server-side.

**Missing capability check on an admin action.** Handler protected by a nonce only, or by `is_admin()`. Any logged-in subscriber can call it. *Fix:* both checks, always.

**CSRF on settings save.** Settings form without a nonce, so an admin visiting a hostile page silently rewrites plugin config (including anything that stores JS). *Fix:* Settings API or explicit nonce.

**Stored XSS through settings or a shortcode attribute.** Value stored unescaped, echoed raw on the front end or back in the admin field. *Fix:* sanitize in, escape out, both sides.

**Reflected XSS through a query parameter.** `echo $_GET['s']` or a search term rendered into a heading or a hidden input. *Fix:* `esc_html`/`esc_attr`.

**SQL injection in a "safe-looking" spot.** Interpolation in `ORDER BY`, in a `LIMIT`, in an `IN (...)` list built with `implode`, or inside `prepare()` on a value that was already concatenated. *Fix:* allowlist for identifiers; build `IN` placeholders programmatically and pass the array to `prepare`.

**Local file inclusion via a template or view parameter.** `include $_GET['template'] . '.php'` — traversal reads arbitrary files. *Fix:* map keys to paths.

**Arbitrary file upload.** Extension checked client-side, or a MIME denylist instead of an allowlist. Results in a webshell. *Fix:* allowlist + `wp_handle_upload` + no PHP execution in the upload dir.

**Arbitrary file read/download.** An export or invoice endpoint that takes a path or filename. *Fix:* capability check + `realpath()` inside a fixed base dir + serve by ID, not path.

**IDOR on records.** `?lead_id=123` fetched without checking ownership. *Fix:* per-object capability check.

**Unauthenticated REST write.** `permission_callback => '__return_true'` on a route that creates or modifies data. *Fix:* real callback returning a capability check.

**SSRF in a URL fetcher.** A "check my feed" endpoint that fetches any URL — used to hit `169.254.169.254` or internal services. *Fix:* `wp_safe_remote_get()`, scheme and host allowlist.

**PHP object injection.** `unserialize()` on a cookie, POST field or option written by a lower-privileged user. *Fix:* JSON.

**Sensitive data exposure.** Debug logs written inside the plugin folder, API keys echoed into a data attribute, or a lead-capture endpoint returning the whole table.

---

## 3. Escaping and sanitizing quick reference

| Input type | Sanitize (in) | Escape (out) |
|---|---|---|
| Plain text | `sanitize_text_field()` | `esc_html()` |
| Multiline text | `sanitize_textarea_field()` | `esc_textarea()` |
| Rich text | `wp_kses_post()` | `wp_kses_post()` |
| Email | `sanitize_email()` + `is_email()` | `esc_html()` |
| URL | `esc_url_raw()` + scheme check | `esc_url()` |
| Integer / ID | `absint()`, `intval()` | `esc_attr()` / cast |
| Float | `floatval()` | `esc_attr()` |
| Hex colour | `sanitize_hex_color()` | `esc_attr()` |
| Option/array key, slug | `sanitize_key()`, `sanitize_title()` | `esc_attr()` |
| Filename | `sanitize_file_name()` | `esc_attr()` |
| Enum / select value | `in_array( $v, $allowed, true )` | `esc_attr()` |
| Checkbox | `! empty() ? 1 : 0` | cast to int |
| JSON to JS | `wp_json_encode()` | `wp_json_encode()` |
| SQL value | — | `$wpdb->prepare()` |

`wp_unslash()` before sanitizing values read from `$_POST`/`$_GET`, since WordPress adds slashes.

---

## 4. Secure snippets

**Settings page save (Settings API does the nonce for you):**
```php
register_setting( 'td_group', 'td_options', array(
    'type'              => 'array',
    'sanitize_callback' => 'td_sanitize_options',
) );

function td_sanitize_options( $input ) {
    $out = array();
    $out['enabled'] = empty( $input['enabled'] ) ? 0 : 1;
    $out['label']   = sanitize_text_field( $input['label'] ?? '' );
    $color          = sanitize_hex_color( $input['color'] ?? '' );
    $out['color']   = $color ? $color : '#2d95b8';
    $out['mode']    = in_array( $input['mode'] ?? '', array( 'a', 'b' ), true ) ? $input['mode'] : 'a';
    return $out; // rebuilt key by key — unknown keys are dropped
}
```

**Authenticated AJAX handler:**
```php
add_action( 'wp_ajax_td_save_lead', 'td_save_lead' );
function td_save_lead() {
    check_ajax_referer( 'td_ajax', 'nonce' );
    if ( ! current_user_can( 'edit_posts' ) ) {
        wp_send_json_error( array( 'message' => __( 'Not allowed.', 'td' ) ), 403 );
    }
    $id    = absint( $_POST['id'] ?? 0 );
    $email = sanitize_email( wp_unslash( $_POST['email'] ?? '' ) );
    if ( ! $id || ! is_email( $email ) ) {
        wp_send_json_error( array( 'message' => __( 'Invalid data.', 'td' ) ), 400 );
    }
    // ... prepared query here
    wp_send_json_success();
}
```

**Public form endpoint (anonymous, so treat as a public API):**
```php
add_action( 'wp_ajax_nopriv_td_contact', 'td_contact' );
add_action( 'wp_ajax_td_contact', 'td_contact' );
function td_contact() {
    check_ajax_referer( 'td_contact', 'nonce' );          // nonce still helps against drive-by posting
    $ip  = isset( $_SERVER['REMOTE_ADDR'] ) ? sanitize_text_field( wp_unslash( $_SERVER['REMOTE_ADDR'] ) ) : '';
    $key = 'td_rl_' . md5( $ip );
    if ( get_transient( $key ) ) {
        wp_send_json_error( array( 'message' => __( 'Please wait a moment.', 'td' ) ), 429 );
    }
    set_transient( $key, 1, 30 );
    // sanitize + validate every field, then store/send
}
```

**REST route:**
```php
register_rest_route( 'td/v1', '/leads', array(
    'methods'             => WP_REST_Server::CREATABLE,
    'callback'            => 'td_rest_create_lead',
    'permission_callback' => function () {
        return current_user_can( 'edit_posts' );
    },
    'args'                => array(
        'email' => array(
            'required'          => true,
            'sanitize_callback' => 'sanitize_email',
            'validate_callback' => 'is_email',
        ),
    ),
) );
```

**IN clause with placeholders:**
```php
$ids          = array_map( 'absint', (array) $raw_ids );
$placeholders = implode( ',', array_fill( 0, count( $ids ), '%d' ) );
$rows         = $wpdb->get_results( $wpdb->prepare(
    "SELECT * FROM {$wpdb->prefix}td_leads WHERE id IN ($placeholders)", $ids
) );
```

**Allowlisted ORDER BY:**
```php
$columns = array( 'id', 'created_at', 'email' );
$orderby = in_array( $_GET['orderby'] ?? '', $columns, true ) ? $_GET['orderby'] : 'id';
$order   = ( 'asc' === strtolower( $_GET['order'] ?? '' ) ) ? 'ASC' : 'DESC';
$sql     = "SELECT * FROM {$wpdb->prefix}td_leads ORDER BY {$orderby} {$order} LIMIT %d";
```

**Serving a file safely:**
```php
if ( ! current_user_can( 'manage_options' ) ) { wp_die( '', 403 ); }
$base = realpath( wp_upload_dir()['basedir'] . '/td-exports' );
$file = realpath( $base . '/' . sanitize_file_name( wp_unslash( $_GET['file'] ?? '' ) ) );
if ( ! $file || ! $base || 0 !== strpos( $file, $base ) || ! is_file( $file ) ) { wp_die( '', 404 ); }
```
