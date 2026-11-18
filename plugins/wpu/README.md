# WP Ultimate Build (`wpu`)

One Claude Code plugin for Midstream Marketing's WordPress work. It merges three earlier toolkits and keeps what they learned:

| Was | Now |
|---|---|
| Elementor Ready To Use Templates (Elementor Forge) | `forge/` compiler, 207-widget registry, validator, block library: `/wpu:build` |
| WP Site Build | `scripts/rplan.ps1`, `build/apply-plan.php`, `audit/`: `/wpu:new-site`, `/wpu:build` |
| WP Site Doctor | the bridge, `php/` scripts, merged `knowledge/GOTCHAS.md`: `/wpu:doctor` |
| SEO Growth OS (Phase 1 parts) | keyword scoring, adapter ideas, honesty rules: `/wpu:seo` |

Everything runs on the team's own **Claude seats** (Team/Enterprise, or Pro/Max) in Claude Code. There is no Anthropic API key anywhere in the system.

## What it does

| Command | Job |
|---|---|
| `/wpu:new-site <slug> <url>` | Set up a site folder, install the WPU Bridge, connect, take a baseline |
| `/wpu:build` | A site in Elementor, Gutenberg, Divi 4, Breakdance or SeedProd from a Claude Design canvas, reference sites, a mockup or a brief |
| `/wpu:doctor` | Find and fix layout, mobile, image, font and plugin problems on an existing site |
| `/wpu:seo` | DataForSEO research, keyword map, then Rank Math or Yoast titles, descriptions, focus keywords and schema, with rollback |
| `/wpu:posts` | Write and publish blog posts (drafts by default) with categories, featured image and SEO fields |
| `/wpu:speed` | PageSpeed medians, one settings group at a time, automatic rollback if worse |
| `/wpu:secure` | Outside scan, inside audit, hardening mu-plugin, plugin code review |
| `/wpu:plugin` | Custom plugins or mu-plugins with the WordPress security gate |
| `/wpu:rescue` | Site down (white screen, critical error, stuck maintenance)? Fix it through the hosting: SFTP/SSH or a cPanel API token |
| `/wpu:handover` | Launch checklist, final backup, bridge removal |
| `/wpu:learn` | Save new lessons into team knowledge (GOTCHAS, validator rules, block factories) |
| `/wpu:theme` | Build a draft block theme (design tokens, templates, CSS) with a private preview link; activate on the go-ahead |
| `/wpu:updates` | Plugin and theme updates on one site or all of them, checked before and after, rolled back if a page breaks |

The `core` skill is the shared working method and loads at the start of every session.

## How it reaches a site: the WPU Bridge

`bridge/wpu-bridge.php` (v2.0) is a temporary plugin installed on the client site. Its REST routes live under `/wp-json/wpu/v1/`.

**One standard zip for every site:** `plugins/wpu/bridge/release/wpu-bridge-2.2.0.zip`, with its SHA-256 checksum beside it. Upload that same file to every client site (Plugins > Add New > Upload Plugin). Nothing in it is specific to a site: each person's access comes from the connection key they make on that site afterwards.

- **One key per team member.** Keys are made in *Tools > WPU Bridge*. Only a SHA-256 hash is stored. Every audit-log entry records which member made the change, and any key can be revoked on its own.
- **It removes itself from use.** The bridge stops answering after 30 days. HTTPS is required. `define('WPU_BRIDGE_DISABLE', true);` turns it off instantly. Deactivating it deletes all keys.
- **Every write is reversible.** SEO, speed and file writes keep a backup first, and `rseo rollback` / `rspeed restore` put the old values back.
- **Two mu-plugins stay after handover:** `wpu-seo-schema.php` (JSON-LD output) and `wpu-hardening.php` (switchable hardening).

## The back door: hosting access

The bridge runs inside WordPress, so when a bad update takes WordPress down, the bridge goes down with it. `/wpu:rescue` gets in through the hosting instead:

- **SFTP/SSH** (`tools/hosting/sftp.py`) works on every host type, including Kinsta, WP Engine and SiteGround. It can read error logs, switch off a broken plugin or theme, clear a stuck maintenance mode, upload a fixed file, fix permissions, and run wp-cli when the account has shell access.
- **cPanel** (`tools/hosting/cpanel.py`) logs in with an **API token**, never the cPanel password. It covers error logs, the PHP version per domain, small text-file fixes, switching plugins off and on, host backups and cron.

**Safeguards:**
- Every write is a dry run until `apply` is added, and the member approves each one.
- A copy of anything changed is saved locally first, and every action is logged with the member's name.
- Writes stay inside the WordPress folder.
- The server's SSH identity is pinned, and a changed identity is refused.
- Folder deletion, `rm -rf`, `chmod -R`/777, destructive wp-cli and SQL are refused outright.
- `wp-config.php` passwords and salts are hidden in any output, and files downloaded from the server can't overwrite anything on your computer.
- Details are in `tools/hosting/SECURITY.md`.

Set it up when you add a site, not during an outage. `/wpu:new-site` asks for it.

## Admin setup (once, by an org owner)

1. Push this repository to a **private** GitHub repo in the company org, for example `midstream-marketing/wp-website-builder`.
2. Add these to the organization's **server-managed settings for Claude Code**, set by an owner in the Claude admin settings. If IT manages computers instead, put them in a `managed-settings.json` pushed to each machine:

```json
{
  "extraKnownMarketplaces": {
    "wp-website-builder": {
      "source": { "source": "github", "repo": "midstream-marketing/wp-website-builder" }
    }
  },
  "enabledPlugins": {
    "wpu@wp-website-builder": true
  },
  "forceLoginMethod": "claudeai",
  "forceLoginOrgUUID": "<your organization UUID>"
}
```

`forceLoginMethod` and `forceLoginOrgUUID` keep everyone on the org seat, so nobody can run it on a personal account or an API key.

   A member can also add it by hand (Claude Code 2.1.275 or later):

```text
/plugin install wpu --marketplace midstream-marketing/wp-website-builder
```

3. Give each member read access to the GitHub repo. Claude Code uses their own git credentials to fetch it.
4. **Release an update:** change the code, bump `version` in `plugins/wpu/.claude-plugin/plugin.json` and in `.claude-plugin/marketplace.json`, then push. Members get it on their next start.

## Member setup (once per computer)

Requirements: Windows 10/11 with PowerShell 5.1+ (or pwsh 7), Node 18+, Python 3.10+, Google Chrome.

1. Install Claude Code and log in with your **company Claude account**.
2. Start Claude Code in an empty working folder, for example `C:\WPU`. That folder becomes your workspace: `sites/<slug>/` lives there. The plugin is already enabled.
3. Save your shared secrets **in your own terminal, not in the chat**:

Ask Claude *"show me the secret setup commands"*. It knows where the plugin is installed and prints lines like these, with the real path filled in:

```powershell
powershell -File "<plugin folder>\scripts\wpu-secret.ps1" set global dataforseo_login
powershell -File "<plugin folder>\scripts\wpu-secret.ps1" set global dataforseo_password
powershell -File "<plugin folder>\scripts\wpu-secret.ps1" set global pagespeed_key      # optional
```

Per client site, when needed: `set <slug> key` (bridge), `set <slug> sftp_pass`, and `set <slug> cpanel_token`.

Each one asks for the value with hidden typing.

Secrets are encrypted with Windows DPAPI for your Windows user, in `%APPDATA%\WPU\secrets\`. They never go into `site.json`, the chat or git. A safety hook blocks Claude from writing anything that looks like a key or password.

4. Install the one Python package the hosting tools need: `python -m pip install --user -r "<plugin folder>\tools\requirements.txt"`.
5. Moving from the old toolkits? Run `scripts\migrate-legacy.ps1 -From "C:\path\to\wp-site-doctor"`, check the dry run, then add `-Apply`.

## Daily use

```text
/wpu:new-site acme-dental https://staging.acmedental.ie
/wpu:build        (attach the Claude Design link or reference URLs)
/wpu:seo
/wpu:posts
/wpu:speed
/wpu:secure
/wpu:rescue       (only when the site is down or the fix needs the hosting)
/wpu:handover
```

Choose the site for a session with `$env:WPU_SITE = 'acme-dental'` before starting Claude, or just tell Claude which site. There is no default site, on purpose: a wrong guess would mean a change on the wrong client's site.

**Approvals:** anything that changes a live site or its hosting (`apply`, `push ... apply`, `publish`, file, template and media uploads, bridge installs, every hosting command except plain reads, raw `ssh`/`scp`) shows an approval prompt first. Read the dry run above it before approving.

## Typed tools: Gutenberg, page builders, shop, updates, themes

Since Bridge 2.1 (2.2 for Divi 5) the bridge also carries **typed tools**: fixed, named actions with checked arguments. No script
is sent, every change is logged with the member's name, and almost every change has an undo. They are run with
`scripts/rtool.ps1` (`list`, `info <tool>`, `<tool> args.json [apply]`, `undo <change_id> apply`).

| Area | What the tools do |
|---|---|
| Content | Pages, posts and custom post types; search and replace; media and alt text; terms |
| Gutenberg | Block-by-block editing, block types, patterns, the theme's design tokens (Kadence, Spectra, Astra, GeneratePress palettes) |
| Elementor | Page text, text replace, template import (Forge and `rtemplate` stay the build route) |
| Divi 4 and Divi 5 | Build whole pages (sections, rows, columns, modules, items, design and responsive settings) as drafts; edit existing pages element by element. On Divi 5 the checked layout goes through Divi's own converter and is saved as Divi 5 blocks |
| Breakdance 3 / Oxygen 6, SeedProd 6.20+ | Full layouts through the builder's own AI actions, behind the "Builder AI actions" switch (off by default), with a code check, a go-ahead for live changes and undo |
| Bricks, Beaver Builder, older Breakdance and SeedProd | Read and replace page text safely in the builder's own data |
| Theme builder | Draft block themes (theme.json, templates, parts, CSS; no PHP) with a private preview link; live on the go-ahead (`/wpu:theme`) |
| SEO | Rank Math and Yoast fields, JSON-LD schema |
| Updates | Plugin and theme updates with a dry run, a check of live pages before and after, automatic rollback (`/wpu:updates`) |
| WooCommerce | Products, variations, orders, coupons, store summary |
| ACF | Field groups; values on posts, terms, users and options |
| Other plugins | Actions offered through the WordPress Abilities API (WP 6.9+) |

Switches for these are in wp-admin under Tools > WPU Bridge > Tool switches. Details: `bridge/SECURITY.md`.

There is no MCP connector in this version: everything runs from Claude Code through the bridge.

## WPU Desk: the same work without a terminal

WPU Desk is a dashboard in your browser that runs the same `/wpu:` skills for you. It has a site list, a task button per job, a form for the details, live progress, **Approve / Reject** cards for live-site changes, replies when Claude asks a question, results and files, and a Secrets panel.

How it works: a small local server (`desk/server.mjs`, Node.js, no extra packages) starts the official Claude Code (`claude -p`) with this plugin. Claude Code uses **your own** Claude sign-in, exactly as in a terminal. The Desk never sees your Claude login, and nothing goes to any server other than Anthropic and the client's site.

**Set up once** (on Windows):
1. Install Node.js (LTS) from nodejs.org.
2. Sign in to Claude Code once: open a terminal, run `claude`, and log in.
3. Create the Desktop shortcut:
   ```text
   powershell -ExecutionPolicy Bypass -File "<plugin folder>\scripts\wpu-desk.ps1" -InstallShortcut -Workspace "C:\Users\<you>\Desktop\WPU-Work"
   ```
   Or ask Claude: `/wpu:desk`.

**Every day:** double-click **WPU Desk** on the Desktop. A window opens; keep it open while you work. Your browser opens the dashboard with a one-time sign-in link. Need another tab or a fresh link? Press **Enter** in the Desk window. Close the window to stop the Desk.

- **+ New site** runs `/wpu:new-site`. Then pick the site and click a task (Build, Doctor, SEO, Posts, Speed, Secure, Rescue, Plugin, Handover, Learn, or Custom).
- **Approvals** show the exact command and why it needs approval. Reject with a note to tell Claude what to do instead.
- **Secrets** saves keys and passwords straight into the encrypted Windows store (same as `wpu-secret.ps1`). They never go into a chat.
- Each job keeps its full log under `<workspace>\.desk\jobs\`, so you can reopen it later.

**Limits**
- The Desk is for one person on their own PC with their own Claude seat. It only listens on `127.0.0.1`. Don't share one Desk or one Claude login between people, and don't put it on a server.
- Jobs use your Claude plan's normal usage limits, exactly like Claude Code in a terminal.
- One running job per site at a time. The Desk window must stay open while jobs run.
- Desk jobs can't edit the plugin itself. Use `/wpu:learn` in Claude Code to change shared team knowledge.
- Keep the workspace inside your Windows user folder (the default `Desktop\WPU-Work` is), so other users of the PC can't read job logs.
- The Secrets panel saves secrets only on Windows. Elsewhere, use `WPU_SECRET_<SCOPE>_<NAME>` environment variables.

See `desk/SECURITY.md` for how the Desk is protected.

## Layout

```text
.claude-plugin/plugin.json   manifest (bump version to release)
skills/        the working methods (core, build, doctor, seo, posts, speed, secure, plugin, rescue, handover, learn, ...)
agents/        visual-critic, security-reviewer, seo-strategist, content-writer, editor, forge agents
hooks/         session-start (site context) and guard (secret and live-write gate)
bridge/        wpu-bridge.php, SECURITY.md, release/ (the standard installable zip + SHA-256)
site-plugins/  mu-plugins that stay on the site (schema, hardening)
scripts/       PowerShell wrappers (r*.ps1 talk to the bridge)
php/           read-only and dry-run/apply scripts sent through the bridge
build/         apply-plan.php (idempotent site builder)
forge/         Elementor compiler, registry, validator, blocks, presets
audit/         Playwright audits (layout, responsive, SEO, fonts, screenshots)
tools/         Python: DataForSEO client, keyword scoring, SEO plan checks, PageSpeed, outside security scan,
               hosting/ (sftp.py, cpanel.py - the back door)
knowledge/     GOTCHAS.md (532 traps), handbooks, checklists
templates/     site.json, SITE-NOTES.md, plan.example.json
desk/          WPU Desk: server.mjs, approval-mcp.mjs, tasks.mjs, ui/, SECURITY.md
```

## Honest limits

- PowerShell wrappers and DPAPI secrets assume Windows. On macOS or Linux, use `pwsh` and set secrets as `WPU_SECRET_<SCOPE>_<NAME>` environment variables.
- Plugin installs from wordpress.org, Elementor Pro features and the Yoast/Rank Math write paths need checking on a real staging site before client use. The local test site had neither Elementor nor a real SEO plugin.
- SEO work does not promise rankings, and the plan checker blocks copy that does.
- The cPanel tool was tested against a mock of cPanel's API, not a real server yet. Run `cpanel.py check` on one real account before relying on it.
- Some budget hosts give SFTP without shell access. There, `sftp.py exec` and `sftp.py wp` won't work; every file command still does.
