# WPU Desk: security notes

WPU Desk starts Claude Code with command access on your PC. Anyone who can drive the Desk can run commands as you, so it is locked down as follows.

## Who can reach it

- **Only this PC.** The server listens on `127.0.0.1`, never on the network. The `Host` header must be exactly `127.0.0.1:<port>` or `localhost:<port>`, which blocks DNS-rebinding attacks from web pages.
- **A session key for every API call.** The key is 48 random hex characters, made fresh each time the Desk starts, and compared in constant time. Browsers can't add the `x-desk-token` header across sites, so a malicious page you visit can't start jobs or approve anything (no CSRF). POST requests must also be `application/json` from the Desk's own origin.
- **One-time sign-in links.** The browser is opened with a single-use code that expires after 10 minutes (`#n=...`), never with the key itself. The page swaps the code for the key, removes it from the address bar, and keeps the key in that tab only. Press **Enter** in the Desk window for a new link.
- **Strict page policy.** CSP is `default-src 'self'`, with no inline script, no framing and `no-referrer`. The UI builds everything with DOM calls, never `innerHTML`, so text from Claude, websites or files can't run as code. Site links must start with `http(s)://`.

## How programs are started

- **No shell, no bare names.** Claude Code, PowerShell, Explorer, taskkill and cmd are started by absolute path with an argument list. Nothing typed in the Desk, and nothing in job files, can become part of a command line. On Windows, an npm-installed Claude is run through its package entry point rather than the `claude.cmd` shim.
- **The workspace is never searched for programs.** `NoDefaultCurrentDirectoryInExePath=1` is set for child processes, and the launcher runs from `%APPDATA%\WPU`, not from the workspace.
- **Saved jobs are re-checked on load.** The session ID must be a UUID, the model one of the known names, and the site a valid short name, before any of them is used again.

## Approvals and guardrails

- Live-site writes, hosting commands and bridge installs are marked "ask" by the plugin's guard hook and come to the Desk as **Approve / Reject** cards. The guard's "deny" rules (secrets, dangerous commands) are refused automatically.
- Every job run gets **its own helper key**, so one job can't raise cards for another. If the Desk stops, the helper denies everything.
- A call too long to show in full (over 20,000 characters) is refused rather than shown cut short.
- **File edits** (Write, Edit, MultiEdit, NotebookEdit) go through the Desk. They are allowed in the workspace, but refused inside the plugin, the Desk's own `.desk` folder, `%APPDATA%\WPU` (the secret store) and Claude's settings folders, so a job can't rewrite its own safety rules.
- On Windows, `WPU_SECRET_*` variables are removed from Claude's environment; secrets come from the encrypted store when a script needs them.

**What approvals are not:** a security boundary against a Claude session that has already been misled, for example by instructions hidden in a client's web page. Claude can still run ordinary shell commands without asking. The guard and the Desk catch the known dangerous patterns, but they can't see everything a script does. Read the dry run before you approve, and stop any job that behaves oddly.

## Files and secrets

- Files are shown only from `sites/<slug>/`, after a realpath check. The block list (hosting backups and downloads, `wp-config*`, `.php`, `.sql`, archives, `known_hosts`, dot-folders) is checked on the real, normalised path. Symlinks are not listed. Files are sent as plain text or images with `nosniff` and a sandbox CSP. `site.json` is shown with passwords, tokens and keys hidden.
- Secrets typed into the Secrets panel go straight to `wpu-secret.ps1` on stdin. They are never put on a command line, in a log, in a job file or in a reply. Only "saved / not saved" is ever shown.
- Job logs and output are redacted for bridge keys, cPanel auth headers and private keys. On macOS and Linux, `.desk/` is `0700` and job files are `0600`.

## Known limits

- The session key is used in the `t=` query string for live updates and images, because `EventSource` and `<img>` can't send headers. It can end up in the browser history if you open an image in its own tab. It stops working when the Desk restarts.
- On Windows, `.desk/` gets the workspace folder's permissions. Keep the workspace inside your user folder (the default `Desktop\WPU-Work` is). The Desk and the launcher warn you when it isn't.
- One person, one PC, one Claude seat. Don't run the Desk on a shared server or expose its port.
