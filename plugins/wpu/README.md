# WP Ultimate Build (`wpu`)

One Claude Code plugin for Webelite Digital's WordPress work. It merges three earlier toolkits and keeps what they learned:

| Was | Now |
|---|---|
| Elementor Ready To Use Templates (Elementor Forge) | `forge/` compiler, 207-widget registry, validator, block library: `/wpu:build` |
| WP Site Build | `scripts/rplan.ps1`, `build/apply-plan.php`, `audit/`: `/wpu:new-site`, `/wpu:build` |
| WP Site Doctor | the bridge, `php/` scripts, merged `knowledge/GOTCHAS.md`: `/wpu:doctor` |
| SEO Growth OS (Phase 1 parts) | keyword scoring, adapter ideas, honesty rules: `/wpu:seo` |

Everything runs on the team's **Claude Team/Enterprise seats**. There is no Anthropic API key anywhere in the system.

## What it does

| Command | Job |
|---|---|
| `/wpu:new-site <slug> <url>` | Set up a site folder, install the WPU Bridge, connect, take a baseline |
| `/wpu:build` | Elementor site from a Claude Design canvas, reference sites, a mockup or a brief |
| `/wpu:doctor` | Find and fix layout, mobile, image, font and plugin problems on an existing site |
| `/wpu:seo` | DataForSEO research, keyword map, then Rank Math or Yoast titles, descriptions, focus keywords and schema, with rollback |
| `/wpu:posts` | Write and publish blog posts (drafts by default) with categories, featured image and SEO fields |
| `/wpu:speed` | PageSpeed medians, one settings group at a time, automatic rollback if worse |
| `/wpu:secure` | Outside scan, inside audit, hardening mu-plugin, plugin code review |
| `/wpu:plugin` | Custom plugins or mu-plugins with the WordPress security gate |
| `/wpu:rescue` | Site down (white screen, critical error, stuck maintenance)? Fix it through the hosting: SFTP/SSH or a cPanel API token |
| `/wpu:handover` | Launch checklist, final backup, bridge removal |
| `/wpu:learn` | Save new lessons into team knowledge (GOTCHAS, validator rules, block factories) |

The `core` skill is the shared working method and loads at the start of every session.

## How it reaches a site: the WPU Bridge

`bridge/wpu-bridge.php` (v2.0) is a temporary plugin installed on the client site. Its REST routes live under `/wp-json/wpu/v1/`.

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

1. Push this repository to a **private** GitHub repo in the company org, for example `webelite/wpu-marketplace`.
2. Add these to the organization's **server-managed settings for Claude Code**, set by an owner in the Claude admin settings. If IT manages computers instead, put them in a `managed-settings.json` pushed to each machine:

```json
{
  "extraKnownMarketplaces": {
    "webelite-wpu": {
      "source": { "source": "github", "repo": "webelite/wpu-marketplace" }
    }
  },
  "enabledPlugins": {
    "wpu@webelite-wpu": true
  },
  "forceLoginMethod": "claudeai",
  "forceLoginOrgUUID": "<your organization UUID>"
}
```

`forceLoginMethod` and `forceLoginOrgUUID` keep everyone on the org seat, so nobody can run it on a personal account or an API key.

   A member can also add it by hand (Claude Code 2.1.275 or later):

```text
/plugin install wpu --marketplace webelite/wpu-marketplace
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

## Layout

```text
.claude-plugin/plugin.json   manifest (bump version to release)
skills/        the working methods (core, build, doctor, seo, posts, speed, secure, plugin, rescue, handover, learn, ...)
agents/        visual-critic, security-reviewer, seo-strategist, content-writer, editor, forge agents
hooks/         session-start (site context) and guard (secret and live-write gate)
bridge/        wpu-bridge.php + SECURITY.md
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
```

## Honest limits

- PowerShell wrappers and DPAPI secrets assume Windows. On macOS or Linux, use `pwsh` and set secrets as `WPU_SECRET_<SCOPE>_<NAME>` environment variables.
- Plugin installs from wordpress.org, Elementor Pro features and the Yoast/Rank Math write paths need checking on a real staging site before client use. The local test site had neither Elementor nor a real SEO plugin.
- SEO work does not promise rankings, and the plan checker blocks copy that does.
- The cPanel tool was tested against a mock of cPanel's API, not a real server yet. Run `cpanel.py check` on one real account before relying on it.
- Some budget hosts give SFTP without shell access. There, `sftp.py exec` and `sftp.py wp` won't work; every file command still does.
