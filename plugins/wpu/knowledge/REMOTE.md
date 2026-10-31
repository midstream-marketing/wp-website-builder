# Working on a live site without host access

The problem this solves: you are building a client site, but you only ever get
wp-admin on its host — no SSH, no cPanel. Building locally means migrating the
whole site up at the end (and every migration is a chance to lose work — WP Site
Doctor has a script that exists only because a re-import silently reverted
mu-plugins and rolled back a plugin version).

The WP Site Build Bridge lets you build directly on the target host instead:
the same scripts that would run locally run there, plus build routes for media
and Elementor templates. It is derived from the WP Site Doctor Bridge 1.2.0 —
same transport and safety model — under its own namespace (`wpsb/v1`), so both
plugins can be installed on one site without clashing.

---

## What actually changes

Nothing above the wrapper layer.

| Local | Remote | Notes |
|---|---|---|
| `bin/wpphp.ps1 script.php` | `bin/rwpphp.ps1 script.php` | same script, same `$argv`, same output |
| — | `bin/rdoctor.ps1` | preflight the host |
| read `debug.log` by hand | `bin/rlog.ps1` | |
| edit files in `wp-content` | `bin/rfile.ps1 get/put` | parse-checks PHP before writing |

The Playwright tools (`audit.mjs`, `probe.mjs`, `rband.mjs`, …) **already work
remotely** — they only ever needed a URL. Point `baseUrl` at the live site.

Build-specific tools on top of the same transport:

| Tool | Route | Notes |
|---|---|---|
| `bin/rplan.ps1 plan.json [apply]` | `/run` | sends `build/apply-plan.php` + the plan; idempotent |
| `bin/rtemplate.ps1 file.json` | `/template` | Elementor's own importer |
| `bin/rmedia.ps1 file [alt]` | `/media` | real Media Library attachments; re-upload reuses |

Any script written for WP Site Doctor also runs here unchanged — same `$argv`,
same dry-run/apply convention.

---

## Being straight about what this is

The `/run` route executes PHP you send it. That is remote code execution, and it
is deliberate — build steps are scripts and they must run as-is.

It is **not a new privilege**. An administrator can already run arbitrary PHP
through Plugins > Add New > Upload, or the file editor. This is a second door
into a room you already have the key to. So the whole job is making the door as
strong as the front one:

- `manage_options` required on every route
- authenticated with **Application Passwords** — per-user, revocable from
  wp-admin, never the account's real password
- HTTPS enforced; plain HTTP refused unless `WPSB_BRIDGE_ALLOW_HTTP` is defined
- **hard expiry**: after `WPSB_BRIDGE_DAYS` (default 60 — builds run longer than repairs) the routes stop
  existing and the plugin deactivates itself
- every call recorded — user, IP, time, what ran — readable at `/audit`
- kill switch: `define( 'WPSB_BRIDGE_DISABLE', true );` in wp-config.php

The expiry matters more than any of the rest. The realistic failure here is not
an attacker, it is **you forgetting to delete this at handover**. Forgetting now
fails safe.

---

## Setup, per client site

```powershell
powershell -File bin/build-bridge.ps1     # -> remote/wp-site-build-bridge.zip
```

1. **Plugins > Add New > Upload Plugin** — install and activate the zip.
2. **Users > Profile > Application Passwords** — add one named `wp-site-build`.
   Copy it; WordPress shows it once.
3. Add a `remote` block to `config.json`:

```json
"remote": {
  "url":         "https://clientsite.com",
  "user":        "your-admin-login",
  "appPassword": "abcd EFGH ijkl MNOP qrst UVWX"
}
```

4. **Preflight before anything else:**

```powershell
powershell -File bin/rdoctor.ps1
```

`config.json` now holds a live credential for a client site. Keep it out of
version control and off shared drives.

### At handover

Delete the plugin, **then revoke the application password** in the client's
profile. Deleting the plugin alone leaves a working credential behind.

---

## Run it

```powershell
powershell -File bin/rwpphp.ps1 php/site-info.php
powershell -File bin/rplan.ps1 plans/client.plan.json            # dry run
powershell -File bin/rplan.ps1 plans/client.plan.json apply      # apply
powershell -File bin/rtemplate.ps1 templates/header.json
powershell -File bin/rmedia.ps1 assets/logo.svg "Company logo"
powershell -File bin/rlog.ps1 300
powershell -File bin/rfile.ps1 put ./client-tweaks.php mu-plugins/client-tweaks.php
```

---

## What has actually been tested

**This bridge (1.0.0) and `build/apply-plan.php` have been syntax-checked only**
(PHP lint, PowerShell parser, `node --check`, zip structure). The new pieces —
`/media`, `/template`, and every step of the plan engine — have **not yet been
run against a WordPress install**. Test them on a LocalWP or throwaway staging
site (define `WPSB_BRIDGE_ALLOW_HTTP` in an mu-plugin there) before the first
client build, and record the results in this section.

The transport underneath (`/run`, `/file`, `/log`, `/doctor`, the output capture
and the PowerShell client) is unchanged from the WP Site Doctor Bridge 1.2.0,
which was verified end to end against alphawolf.local (WordPress 7.1, PHP 8.2,
Elementor 4.2.3, WooCommerce 11.0.1) and has since run on several live client
hosts:

| Behaviour | Result |
|---|---|
| Application Password auth over the wire | authenticated as the admin user |
| `php/site-info.php` unmodified | 104 lines, full output, exit 0 |
| `aw-blank.php` unmodified | correct page/template report, exit 0 |
| `$argv` passing | `["script.php","apply"]` — not split into characters |
| `exit("== DRY RUN ==")` | output returned, exit 0 |
| Uncaught fatal | reported as `FATAL:` with file and line, exit 1 |
| UTF-8 output (em-dash, accents) | intact |
| `rfile.ps1 put` valid PHP | written, parse check passed, `.bak` kept |
| `rfile.ps1 put` broken PHP | **refused** with the syntax error and line |
| `rfile.ps1 get ../wp-config.php` | **refused**, traversal blocked |
| Wrong application password | clean `HTTP 401`, exit 1 |
| Unreachable host | clean "could not reach", exit 1 |

**Not tested, and untestable locally** — LocalWP has none of these conditions:
stripped `Authorization` headers, mod_security, a low `max_execution_time`, or a
security plugin. `rdoctor.ps1` exists to report on all four the first time you
point this at a real host.

Three real bugs were found by running it that code review had missed — a lost
output buffer, a duplicated one, and a BOM corrupting every response. They are
written up in `docs/GOTCHAS.md`; the short version is that testing this on
LocalWP first was not optional.

## The traps, and why each one is handled

These are the ones that will actually bite on a client host. `rdoctor.ps1`
reports on all of them, because from the outside every one of them looks
identical — "it doesn't work".

### 1. The host strips the `Authorization` header

Common under CGI/FastCGI. Application Passwords then fail with no useful signal.
The plugin recovers the header from `REDIRECT_HTTP_AUTHORIZATION`,
`HTTP_X_AUTHORIZATION` and `apache_request_headers()`. If `rdoctor` still says
`Authorization header  False`, add to `.htaccess`:

```apache
SetEnvIf Authorization "(.*)" HTTP_AUTHORIZATION=$1
```

### 2. mod_security eats the request body

Many hosts block POST bodies containing `<?php` or `eval`. The payload is
**base64-encoded** for exactly this reason. That is a transport workaround, not
a security measure — nothing relies on it being opaque.

### 3. `max_execution_time` kills a script part way through

**The most dangerous one.** Shared hosting often caps at 30s and blocks
`set_time_limit()`. A script rewriting 42 links across six documents that dies
at link 20 leaves the site in a state that is *worse than before you started*,
and there is no local copy to diff against.

`rdoctor` warns when the limit is low and `set_time_limit()` is blocked. When it
does: dry-run everything, and split large jobs. The dry-run/apply convention
stops being good practice and becomes the thing keeping you out of trouble.

### 4. A security plugin blocks REST auth

Wordfence and Solid Security both do this by default, and both rate-limit
repeated POSTs. `rdoctor` names any it detects. Intermittent failures point here
first.

### 5. Application Passwords are refused over plain HTTP

Core behaviour, and correct — Basic auth over http sends the credential in
clear. For testing against LocalWP, define `WPSB_BRIDGE_ALLOW_HTTP` in an
mu-plugin. **Never define it on a live site.**

### 6. A script calls `exit()` and the response vanishes

Nearly every toolkit script ends `exit( "== DRY RUN ==" )`. `exit()` inside a
REST callback kills the request before a response is built — which from the
client looks exactly like a crash.

Worse, a plain `ob_start()` does not save you: WordPress registers
`shutdown_action_hook()` at bootstrap, which calls `wp_ob_end_flush_all()` and
**flushes your buffer to the client before any shutdown function you registered
later can run**. The first build of this plugin did exactly that, and the
symptom was the script's output arriving as loose text outside the JSON with an
empty result reported.

So the buffer takes a **capturing callback** that stores each chunk and returns
`''`. It no longer matters who flushes it or when. A shutdown handler then owns
the response whenever the callback does not finish normally, so **you get the
script's output back instead of a white screen**.

Without this the whole thing is unusable, and it is the part most worth
understanding if you ever modify the plugin. Two related traps — `ob_get_clean()`
duplicating output, and core's fatal handler answering first — are in
`docs/GOTCHAS.md`.

### 7. A bad mu-plugin white-screens the site

If that happens through `/run`, the bridge goes down with the site and you have
no way back in except wp-admin (which is also down). So `rfile.ps1 put`
**parse-checks PHP server-side before writing**, using `token_get_all()` with
`TOKEN_PARSE` — `php -l` is not available because `exec()` is disabled on most
shared hosting. It also keeps a timestamped `.bak` of whatever it replaced.

### 8. A UTF-8 BOM in a PHP file corrupts every response

`Set-Content -Encoding utf8` in Windows PowerShell 5.1 **always writes a BOM**,
and a BOM before `<?php` is emitted as body bytes on every request. That both
breaks JSON parsing on this end and causes "headers already sent" on the site.

`rfile.ps1 put` strips a leading BOM from `.php` files and tells you it did. The
client also detects any stray bytes before the JSON and prints them as a warning
rather than hiding them — if you see that warning, something on the site is
emitting output before headers and it is worth chasing down.

---

## Still true, and still the point

Everything in `CLAUDE.md` §1 applies harder here, not less. You are now editing a
live site with real visitors and no local copy to fall back on. Dry run, apply,
screenshot, assert. "It looks right" was never verification; against production
it is negligence.

## Bridge 2.0 security rules (added 28 Oct 2026)

- `/run` and `/file` need `install_plugins` (a super admin on multisite) and are refused when the site sets
  `DISALLOW_FILE_MODS`. On such a site, use the typed routes (`/seo`, `/posts`, `/media`, `/template`) or ask the
  owner to lift it for the job. Don't try to work around it.
- `/file` refuses symlinks and anything whose real path is outside wp-content.
- Backups and temp scripts live outside the web root when possible. Otherwise they go in a random-named folder with
  deny-all files. Backup names carry a random suffix.
- Every activation wipes the keys and the audit log, so a re-installed bridge needs new keys from each member.
