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

## Typed tools (`/tools`, `/tool`) - new in 2.1

The bridge now carries a set of typed tools: page content, Gutenberg blocks, page builders, WooCommerce, ACF,
updates and draft themes. They are run from Claude Code with `scripts/rtool.ps1`.

- **A tool is a fixed, named action with checked arguments. It never runs code it is sent.** That is the
  difference from `/run`, and why the tool routes only need an administrator, not code rights.
- **Same sign-in as the rest of the bridge:** HTTPS, a per-member key (or Application Password), administrator
  capability, the 30-day switch-off, `WPU_BRIDGE_DISABLE`.
- **Nothing changes without "apply".** The site decides this, not the script: "apply" is read only from the
  request address (`?apply=1`), never from the JSON, so nothing inside the arguments can switch it on. Without
  it, a tool that has a dry run is forced into a dry run whatever was sent, and a tool without one is refused.
- **A person approves every apply.** On the team's computers the guard hook asks the member before any
  `rtool.ps1` command runs, unless it is one plain call without the word apply (those cannot change anything).
  Calls built at run time, piped, chained or sent to the bridge route directly are always asked about. The hook
  is a safeguard on Claude, not on a person holding a key: anyone with a key is an administrator.
- **Switches** (Tools > WPU Bridge > Tool switches): read only, updates, order changes, themes, Divi add-on
  modules, builder AI actions (off by default), other plugins' actions.
- **Log and undo.** Every write is in the bridge audit with the member's name, and in the tools' own change
  list with a `change_id`. `rtool.ps1 undo <change_id> apply` puts it back. Undo copies live in a private
  folder (above the web root when possible) and are deleted when the bridge is deactivated.
- **A fresh start each time.** Activating or deactivating the bridge deletes the tools' undo copies, update
  backups, change list, preview links and switches, and undo records from an earlier install no longer verify.
  Draft themes are kept: they are themes on the site, and one may be active.
- **Review.** The tools were built and reviewed as "WPU Connector" (independent reviews at each version) and
  moved into the bridge unchanged apart from names. The move (routes, the apply rule, the switches form, the
  guard-hook rule) had its own independent review: one high finding (a dry run sent as the text "false" ran
  as a real change without apply) and one medium (the hook could be avoided) were fixed, with five low ones.
  Those fixes are tested but have not had a second independent pass. `rtool.ps1` could not be run against a
  live bridge in the build environment (the key store is Windows-only): run `rtool.ps1 list` on the first
  site as its check.

### Tool safeguards

- **HTML filtering:** content, block markup, product descriptions and Elementor replacements go through
  `wp_kses_post` (no scripts or event handlers). Titles and plain fields are sanitized as text.
- **Text replacement** (blocks, search and replace, Elementor) only changes visible text, never block
  attributes, HTML tags, links or class names. So blocks stay valid in the editor.
- **Elementor template import** refuses HTML, shortcode and code widgets, custom code, script, iframes,
  `javascript:` links and event handlers.
- **ACF:**
  - Every value is checked against its field type, including each sub-field inside groups, repeaters and
    flexible content.
  - Links accept only http, https, mailto and tel.
  - Password fields are never read or written.
- **Media:**
  - Downloads go through `wp_safe_remote_get`, so private and local addresses are refused.
  - Only jpg, png, gif, webp, avif and pdf are accepted, and the file contents must match the extension.
  - SVG is refused. The maximum size is 25 MB.
- **Health checks** only load addresses with this site's own scheme, host and port, and never follow
  redirects. That rules out port scanning and redirects that lead elsewhere.
- **Updates:**
  - Item names must be a plugin file or a theme folder name; `..`, backslashes and other characters are
    refused.
  - Before each update, the item is zipped into private storage. A zip cannot run as PHP even if the folder
    is reachable from the web.
  - Restore checks that the backup is ours, that its top folder matches, and that the target's real parent
    folder is the plugins or themes root. It refuses any entry with `..`.
  - Only the newest 10 backups are kept.
- **Private storage** is a random folder above the web root when the host allows it, otherwise inside
  uploads with deny files. Folders are `0700`. The connection check on the admin page says which one this
  site uses.

### builder AI actions guard (Breakdance, Oxygen, SeedProd)

Breakdance 3 / Oxygen 6 and SeedProd 6.20+ register their own page-building actions with the WordPress
Abilities API. They were written for an administrator at the keyboard: they do not filter input, and the
builders can run PHP and print unescaped markup from ordinary-looking settings (dynamic-data shortcodes,
PHP conditions and queries, element ids, attribute names). The bridge reaches these actions through
`rtool.ps1 ability_run`, so `tools/ability-guard.php` stands in front of them.

**What it does**

- **Off by default.** Until an administrator ticks "Builder AI actions" under Tools > WPU Bridge, only a
  short list of harmless look-ups (page tree, element list, schemas, page list) works. Everything that changes
  something, shows form submissions or builder settings, or renders a page is refused.
- **Allowlist.** Only builder actions on the bridge's own list run. An action a builder adds in a later
  version is blocked until the list is updated. The MCP Adapter's "run any ability" action is blocked.
- **Never run:** Breakdance `run-site-tool`, `set-settings`, WooCommerce template writes, everything that
  fetches or imports a design library, `report-bug`; SeedProd `activate-license` and `import-theme`.
- **Input check** on every action that writes, on the text as given and in decoded form:
  - HTML is parsed with WordPress's HTML reader, not matched with patterns. Refused: script, iframe, object,
    embed, form, link, meta and base tags; any `on...` attribute, `srcdoc`, `formaction`; `javascript:` and
    non-image `data:` addresses; PHP tags; an unfinished tag at the end.
  - Code, HTML, JavaScript, shortcode, widget, embed and term-loop elements; SeedProd Custom HTML, shortcode
    and template-tag blocks.
  - Builder dynamic-data shortcodes and markers, PHP conditions, PHP queries, JavaScript and set-attribute
    interactions.
  - Settings whose name marks them as code; ids, tag names and class names that are not plain; attribute
    names that are not plain or that run script; `@import` and script inside CSS.
  - CDATA markers and doctypes (a builder's own HTML reader could join pieces the check saw separately), and
    a second, deliberately loose look for dangerous tag names and handlers.
  - Quotes, backslashes and angle brackets in addresses, ids, colours and sizes, which some elements print
    inside inline scripts.
  - Input too large or too deeply nested to check.
- **Go-ahead code.** A change to a live page, a template, header, footer or popup, a publish, a form's
  destination, or any site-wide setting is refused with a one-time code tied to the person, the action and the
  exact input, valid about ten minutes. Claude is told to ask the person and resend with the code. This makes
  Claude come back to the person; it is not a lock, because Claude holds the code.
- **Undo.** The page's content and the builder's data on that page are saved first; if they cannot be saved
  (too large), the change is refused. Global changes (styles, CSS variables, classes a builder creates) are
  not covered by undo.
- A page someone else has open for editing is not changed. The activity log records which action ran and
  whether a go-ahead code was used.

**What it cannot promise**

The check is a list of the ways we know these builders run code or print raw markup. A builder can read some
other setting in a way that list does not cover, now or after an update. Treat the switch as giving the
connected AI the builder's own power, with strong checks in front. Leave it off on sites where people you do
not fully trust can add text (comments, form entries, guest posts) that Claude might read. SeedProd pages
built this way are empty on the front end until a person saves them once in SeedProd's builder, which also
means SeedProd's builder shows the content to that person first.

Other plugins' abilities are passed through as before; the bridge cannot know what they do.

### Divi 5 layouts (2.2)

- A layout for a Divi 5 site goes through exactly the same checks as a Divi 4 one (below). The checked layout
  is written as Divi 4 shortcodes in memory only and handed to Divi 5's own converter
  (`Conversion::maybeConvertContent`, the code Divi uses to migrate sites). Only the Divi 5 blocks it returns
  are saved. If any part comes back unconverted, nothing is saved.
- Settings live inside each block's JSON, where `--`, `<`, `>`, `&` and quotes are escaped, so text cannot end
  a block or start a new one.
- Editing an existing Divi 5 page: the page must read back exactly as stored before anything is changed;
  untouched blocks keep their stored text; what is about to be saved must parse as a clean Divi 5 layout.
- Code modules are not created, changed or copied. Elements using Divi dynamic content are changed in Divi.
- **Checked twice.** Divi's converter decodes and reshapes values, so what it returns is checked again, on the
  form that will be stored: every text value (and setting name) in every block is refused if it holds script
  or other unsafe markup, a `javascript:` or `data:` address, a shortcode, or a Divi dynamic-content token
  (`$variable(...)$`), including one split up by tags, brackets or spaces.
- **No shortcodes in content on Divi 5.** Divi 5 runs shortcodes inside content and then reads the result
  again for its own tokens. So content holding any shortcode registered on the site is refused; add those in
  Divi itself. Plain square brackets in text ("[24/7]") are fine. `%22`, `%92` and `%5c` in content are
  refused, because Divi 5 turns them back into quotes and backslashes after the content filter has run.
  (On Divi 4, content may hold the site's ordinary shortcodes, as before; Divi's own are refused.)
- Display conditions and the global-colour map are never written by the bridge. Option lists of form fields
  must be plain JSON lists with the known keys, holding text and numbers only.
- **A preview writes nothing.** Divi's converter saves to Divi's own settings in two cases: its first run on a
  site, and a layout that names a Divi global colour (`gcid-...`). The bridge refuses both before converting:
  it asks for Divi to be opened once, and for colours to be sent as values.
- A setting change applies only what the change adds. Divi's converter also writes defaults of its own; those
  are subtracted first. Divi decides what one Divi setting means, and one setting can set several stored
  values (a menu's background colour also sets its dropdown colour); the result lists every stored value an
  operation set, and says so when nothing changed.
- Elements using Divi dynamic content are not changed or copied; only the exact token Divi writes for a plain
  global colour is treated as not dynamic. A page with an element whose settings cannot be read is not edited.
- Changed blocks are written with WordPress's own block serialiser. A copied element is a full copy.
- Limits: 90 conversions per request, 2 MB and 4000 elements per layout, also when appending.
- What remains: these checks run before Divi renders the page, and a Divi update can change how it reads
  stored values, so re-test after a Divi 5 update. A shortcode registered later by a new plugin is not known
  at check time. A copied element keeps the display conditions it already had. Custom CSS settings can style
  the whole page. The Divi 5 visual builder (JavaScript) was tested by opening and saving pages, not reviewed
  line by line.

### Divi 4 layouts

- Layouts arrive as a typed tree, never as shortcode text. The bridge writes the shortcodes itself.
- Every module name is checked against Divi's own registry on the site; where it may sit (fullwidth or not,
  item of which parent) is enforced; column widths must be Divi fractions that add up to one row.
- **Which modules:** Divi's own modules are allowed, except the Code modules (raw HTML and script), which are
  never written, changed or copied. Modules that other plugins add to Divi are refused unless an administrator
  ticks "Divi modules from other plugins" (off by default), and raw-code modules are refused even then.
- Setting names must be ones Divi knows for that module; unknown ones are dropped with a warning.
- Values are filtered like post content, then encoded the way Divi stores them, so a value cannot close its
  quotes or its tag. Web addresses allow http, https, mailto and tel only; custom CSS refuses `<`, `@import`,
  `javascript:` and `expression()`.
- **Checks run on the decoded form.** Divi decodes its own escapes and HTML entities when a page renders, and
  runs shortcodes inside the tablet, phone and hover versions of text settings. So every value and all content
  is decoded repeatedly (Divi escapes, entities, percent-encoding) before it is checked for the tag of any Divi
  element and for `javascript:` / `data:` addresses. Callers may not send Divi's bracket escapes themselves, and
  the tablet, phone and hover versions of text settings may not contain square brackets at all.
- Divi dynamic content cannot be written in any form (its `@ET-DC@` wrapper or bare JSON), and an element
  that already uses dynamic content is changed in Divi only.
- Divi's editor decodes entities before showing settings. A setting whose decoded form holds markup the
  content filter would not allow (script written as `&lt;script&gt;`, for example) is refused.
- Works on pages, posts and ordinary custom post types the person can edit. Not on revisions, the Divi
  library, Theme Builder templates or products. A page someone has open for editing is not overwritten.
- Edits keep untouched elements as stored, including their stored setting values. An element whose settings
  are not plain `name="value"` pairs is left for Divi. A page with content outside its Divi layout is refused
  rather than rewritten. Pages are capped at 2 MB and 4000 elements.
- The normal content filter is switched back on in every case after a save, even if another plugin fails.
- Undo restores the exact content and Divi's page settings. New pages are drafts.
- Divi's own files are only read (to load its module list); nothing in Divi is changed.
- Left to the people using it: Claude can set a contact form's recipient address and redirect, and can place
  any ordinary shortcode or allowed HTML (including iframes for administrators) in text, as an editor could.
  Read drafts before publishing.

### Page-builder text, draft themes, other plugins' actions

- **Page builders** (Divi 4/5, Bricks, Beaver Builder, Breakdance, SeedProd):
  - Only visible text changes. Comments, whole `<script>`, `<style>` and `<textarea>` elements, and HTML tags
    (parsed with their quoted attributes) are never touched; nor are styling, link and id keys in builder data.
  - Divi replacements may not contain quotes, `[ ]` or `< >`.
  - Undo restores the exact stored bytes, for allowlisted builder fields only.
- **Theme builder:**
  - Draft themes contain only `style.css` (a header), `theme.json` and `.html` block templates and parts.
    File paths come from a fixed pattern; no `.php` can be written.
  - Theme names become `wpu-` plus lowercase letters, numbers and dashes. Only folders marked as WPU drafts
    are ever written or removed, and never one that is live.
  - Markup is filtered like post content, and CSS refuses `<`, `@import`, `javascript:` and `expression()`.
  - Saving a draft that has become the live theme needs an explicit confirmation.
  - `theme_activate` accepts only a plain folder name of an installed theme.
- **Preview links:**
  - Random 32-character key, stored hashed, expiring after 1-30 days. Anyone holding the link sees the site
    in the draft theme.
  - Front end only: never wp-admin, cron or REST (checked on the decoded request, again when the request is
    parsed).
  - `noindex`, `no-store` and `DONOTCACHEPAGE`. A CDN set to ignore those headers is the one way a preview
    could be cached.
- **Abilities API** (WordPress 6.9+):
  - Only abilities a plugin exposed (`show_in_rest` or `mcp.public`) are listed or run.
  - Each run goes through `WP_Ability::execute()`, which checks the input against the ability's schema and runs
    the ability's own permission check as the signed-in person.
  - A separate read-only tool runs only abilities annotated read-only. The admin switch can allow all, allow
    only read-only, or turn abilities off.
  - Other plugins' actions cannot be undone by the bridge, and the consent screen says so.
- **Change files are signed** (HMAC with the site's auth salt). A change file altered on disk is refused
  instead of being written back into the site. Changes saved by version 1.0 (unsigned) can no longer be
  undone automatically.

## Residual risk

- `/run` is arbitrary PHP **by design**. Anyone holding a key (or an admin Application Password made for another tool, while the bridge is active) can do anything that admin could. That is why keys are per member and revocable, the bridge expires after 30 days, and handover removes it.
- A compromised admin account, a compromised member computer (DPAPI protects secrets at rest, not from malware running as that user), or a vulnerable host are outside what the plugin can defend against.
- The public `/wp-json/` index shows that `wpu/v1` exists while the bridge is active.
- On nginx, the `.htaccess` deny files do nothing. The random folder names and the ABSPATH guard are the protection there.

## On the site owner's side

- Keep WordPress, PHP and plugins updated, and use least-privilege admin accounts.
- Keep backups (UpdraftPlus or the host's) independent of the bridge.
- Remove the bridge at handover (`/wpu:handover`). Revoke a member's key the day they leave the team.
