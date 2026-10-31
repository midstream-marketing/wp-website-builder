# Hosting tools (`sftp.py`, `cpanel.py`): security notes

Reviewed 31 Oct 2026 by a separate reviewer who had not seen them built. Every finding was fixed and re-tested.

## Model

- The bridge is the normal route. These tools are the back door for when WordPress is down.
- **Credentials:**
  - They live only in the member's encrypted store (DPAPI on Windows), or in a `WPU_SECRET_*` variable on macOS or Linux.
  - `site.json` holds no secrets, and the tools refuse to run if it does.
  - The guard hook blocks passwords, tokens, private keys, `WPU_SECRET_*` and `secret(` in files and commands.
- **SFTP host identity:**
  - It is pinned per site in `sites/<slug>/hosting/known_hosts`.
  - `trust` fetches the server key **without logging in**, so the password is never sent to an unconfirmed server.
  - A changed key stops the tool, showing both fingerprints.
- **cPanel:**
  - Uses a per-member API token over verified TLS (`Authorization: cpanel user:token`).
  - Redirects are refused, so the token can't be forwarded.
  - The test override `WPU_CPANEL_BASE` only accepts 127.0.0.1 or localhost.
- **Approval:**
  - Only exact plain-read command lines pass the hook silently. Every other `sftp.py` or `cpanel.py` invocation asks the member, dry runs included.
  - The rule is inverted on purpose: matching the word `apply` was bypassable with `$(echo apply)`, quote splitting, line continuations and `python -c`.
- **Writes:**
  - They stay inside the WordPress root, checked on the server's *real* paths, so a symlinked folder can't be used to escape. Symlink targets are refused.
  - A root of `/` or one with fewer than two components is refused.
  - A copy is saved before every change, and every write is logged with the member's name.
- **Shell (`exec`):**
  - Runs without `apply` only for bare allow-listed read commands (`ls`, `cat`, `tail`, `grep`, `find`, `du`, `df`, `php -v`…), optionally piped, with no other shell operators.
  - Not allowed without `apply`: `find -delete/-exec/-fprint*/-ok*`, `tail -f`, `date -s`, `du --files0-from`.
  - A denylist blocks destructive commands even with `apply`: recursive or forced `rm`, `rmdir`, `chmod -R`, world-writable modes, `find -delete`, `git clean`/`reset --hard`, `wp db export|cli|reset|drop|import|query`, `wp search-replace` without `--dry-run`, `wp plugin|theme delete`, `wp eval`, and destructive SQL.
- **wp-cli:**
  - Arguments are parsed and rebuilt with `shlex.join`.
  - Shell characters and the global flags `--exec`, `--require`, `--ssh`, `--http`, `--path`, `--context` and `--user` are refused.
  - `config get/list` and `db check` with flags are not treated as reads.
- **Output:** `DB_PASSWORD`, `DB_USER`, salts and `*_KEY/SECRET/TOKEN/PASSWORD` defines are hidden in everything printed.
- **Downloads:** they land only in `sites/<slug>/hosting/downloads/` and never overwrite, so a file from a hacked server can't replace a hook or settings file.

## Residual risk

- A member can approve something they didn't read. The dry run is shown, but the decision is theirs.
- A Bash command that rewrites `site.json` (for example `python -c`) isn't caught by the Write/Edit check. Changing where credentials go that way needs a deliberately crafted command.
- Trust on first use: if the very first connection is intercepted, the wrong key is pinned. The fingerprint is shown, so compare it with the host's when they publish one.
- A full-account API token can do more than these tools expose. Make one token per member, and revoke it when the job ends.
- cPanel was tested against a mock of its API. Check it once against a real account.
