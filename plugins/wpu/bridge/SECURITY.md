# WPU Bridge 2.0: security review

Reviewed 28 Oct 2026 by:

1. A line-by-line pass against the wp-plugin-security checklist.
2. The static scanner, run on `bridge/`, `site-plugins/`, `php/` and `build/`.
3. A separate reviewer who had not seen the build. They read the code and probed the local test site without a key.

## Attack surface

| Route (`/wp-json/wpu/v1/`) | Who can reach it | What it does |
|---|---|---|
| `/doctor`, `/log`, `/audit` (GET) | key or admin Application Password + `manage_options` | read-only status |
| `/seo` GET/POST, `/seo/rollback` | same | SEO meta read/write, backup first, rollback by validated ref |
| `/posts` GET/POST | same | posts; `wp_kses_post` on content; publishing needs `confirm_publish` |
| `/media`, `/template` | same | uploads through WordPress's own type checks (no URL fetching, 25 MB cap); Elementor JSON import |
| `/run`, `/file` | same **+ `install_plugins`**, **super admin on multisite**, refused when `DISALLOW_FILE_MODS` | operator PHP; read/write inside wp-content |
| Tools > WPU Bridge (wp-admin) | `manage_options` + nonce | make/revoke per-member keys (max 20) |

Unauthenticated callers get a generic 401 on every route. Once the bridge expires (30 days) or `WPU_BRIDGE_DISABLE` is set, the routes are not registered at all. Plain HTTP is refused unless `WPU_BRIDGE_ALLOW_HTTP` is set (local testing only). Spoofed `X-Forwarded-Proto` headers don't count as HTTPS.

## Controls

- **Keys:** a SHA-256 hash is stored, compared with `hash_equals`. A key works only while its creator is still an admin. Keys are wiped on every activation and deactivation, and each audit entry carries the member's name.
- **`/file`:** refuses `..` and null bytes; checks the real path of the nearest existing parent; refuses symlinks and any target whose real path leaves wp-content; parse-checks PHP before writing; strips a BOM.
- **Backups and `/run` temp scripts:**
  - Kept above ABSPATH only when that folder is outside the document root.
  - Otherwise a 0700 temp folder this PHP user owns, with a random name.
  - Otherwise `uploads/wpu-bridge-<random>/`.
  - Every one of these folders gets a deny-all `.htaccess` and an `index.php`.
  - Backup names have a random suffix, and temp scripts start with an ABSPATH guard and are swept after an hour.
- **Output:** admin page output escaped; JSON-LD printed with `JSON_HEX_TAG|AMP|APOS|QUOT` (no `</script>` breakout, tested); `_wpu_schema` is protected meta.
- **SQL:** `$wpdb->prepare` wherever a value enters a query.

## Scanner

- **`bridge/wpu-bridge.php`, `site-plugins/*`:** clean.
- **`plugin-src/index.php`:** "no ABSPATH guard". It is an empty directory index that outputs nothing.
- **`php/*`:** these are one-shot scripts. They are never installed on the site; the bridge runs each one for a key holder and returns its plain-text output to the terminal. The findings and how each was settled:

| Finding | Verdict |
|---|---|
| `printf`/`echo` | Plain text, not HTML, so not exploitable |
| SQL concatenation | Only `{$wpdb->options}`/`{$wpdb->posts}` table names, with no outside input |
| Shell calls in `db-dump.php` and `proc-check.php` | Every argument goes through `escapeshellarg`; DB credentials pass through a 0600 temp file, never the command line |
| DB dump names | Now carry a random suffix |
| `server-timing.php` using `wp_remote_get` | Fetches only `home_url()` pages, with redirects off |

## Fixed in this review

| # | Severity | Issue | Fix |
|---|---|---|---|
| 1 | Medium | On multisite, a single-site admin could use `/run` to take over the network; `/run` and `/file` ignored `DISALLOW_FILE_MODS` | New `wpu_bridge_permission_code`: `install_plugins`, super admin on multisite, honours `DISALLOW_FILE_MODS` |
| 2 | Medium | Backups could land in a web-served folder (Bedrock, subfolder installs) under guessable names | Document-root check, deny files, random names |
| 3 | Low-Med | A predictable `/tmp` folder on shared hosting could be pre-created by another account | Random name, 0700, owner must be this PHP user |
| 4 | Low | Keys survived an FTP delete and came back on re-install | Keys and audit wiped on activation |
| 5 | Low | A symlink as the last path segment escaped wp-content | `is_link` refusal and real-path check |
| 6 | Low | Hardening `no_user_listing` broke the block editor's author picker for Editors | Users route kept for `edit_posts` |

## Residual risk

- `/run` is arbitrary PHP **by design**. Anyone holding a key (or an admin Application Password made for another tool, while the bridge is active) can do anything that admin could. That is why keys are per member and revocable, the bridge expires after 30 days, and handover removes it.
- A compromised admin account, a compromised member computer (DPAPI protects secrets at rest, not from malware running as that user), or a vulnerable host are outside what the plugin can defend against.
- The public `/wp-json/` index shows that `wpu/v1` exists while the bridge is active.
- On nginx, the `.htaccess` deny files do nothing. The random folder names and the ABSPATH guard are the protection there.

## On the site owner's side

- Keep WordPress, PHP and plugins updated, and use least-privilege admin accounts.
- Keep backups (UpdraftPlus or the host's) independent of the bridge.
- Remove the bridge at handover (`/wpu:handover`). Revoke a member's key the day they leave the team.
