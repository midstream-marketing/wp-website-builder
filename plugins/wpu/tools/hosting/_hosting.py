"""Shared rules for the hosting tools (sftp.py, cpanel.py).

These are the BACK DOOR. The WPU Bridge is the normal route; use these only when the bridge cannot
help: the site shows a white screen or a fatal error (and the bridge died with it), a file the bridge
cannot reach, the PHP version, server error logs, file permissions, host backups.

Rules every command follows:
  - Read commands run straight away. Write commands are a DRY RUN unless the last argument is "apply".
  - Before anything is changed or removed, a copy is saved to sites/<slug>/hosting/backups/<time>/.
  - Writes are confined to the WordPress root from site.json. Reads may go anywhere the account can.
  - Every write is logged to sites/<slug>/hosting/actions.log with the member's name.
  - Credentials come from the member's encrypted store, never from site.json or the command line.
"""
from __future__ import annotations

import getpass
import json
import os
import posixpath
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _wpu import secret, site_cfg, site_dir, site_slug  # noqa: E402

STAMP = datetime.now().strftime("%Y%m%d-%H%M%S")


def hosting_cfg(kind: str) -> dict:
    """The site.json "hosting.<kind>" block (kind = sftp | cpanel). Exits with a how-to if missing."""
    cfg = site_cfg()
    block = (cfg.get("hosting") or {}).get(kind)
    if not block:
        sys.exit(_HOWTO[kind].format(path=site_dir() / "site.json", slug=site_slug()))
    for bad in ("pass", "password", "token", "apiToken", "key", "passphrase"):
        if block.get(bad):
            sys.exit(
                f'site.json hosting.{kind}.{bad} holds a credential in plain text. Remove it and save it with:\n'
                f'  powershell -File scripts/wpu-secret.ps1 set {site_slug()} {kind}_{"token" if kind == "cpanel" else "pass"}'
            )
    return block


def need_secret(name: str) -> str:
    v = secret(site_slug(), name)
    if not v:
        sys.exit(
            f"No '{name}' saved for {site_slug()}. The member saves it in their own terminal (hidden input):\n"
            f"  powershell -File scripts/wpu-secret.ps1 set {site_slug()} {name}\n"
            f"Never paste it into the chat."
        )
    return v


def hosting_dir() -> Path:
    d = site_dir() / "hosting"
    d.mkdir(parents=True, exist_ok=True)
    return d


def backup_path(rel: str) -> Path:
    """Local path a remote file is saved to before it is changed. rel is relative to the WP root."""
    safe = re.sub(r"[^A-Za-z0-9._/-]", "_", rel.lstrip("/")).replace("..", "_")
    p = hosting_dir() / "backups" / STAMP / safe
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def log_action(tool: str, action: str, detail: dict) -> None:
    entry = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "member": _member(),
             "tool": tool, "action": action, **detail}
    with open(hosting_dir() / "actions.log", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _member() -> str:
    try:
        return os.environ.get("WPU_MEMBER") or getpass.getuser()
    except Exception:  # noqa: BLE001
        return "unknown"


def split_apply(args: list[str]) -> tuple[list[str], bool]:
    if args and args[-1].lower() == "apply":
        return args[:-1], True
    return args, False


def inside_root(root: str, path: str) -> str:
    """Resolve path against root (POSIX) and refuse anything that ends up outside it."""
    root = posixpath.normpath("/" + root.strip("/")) if root.startswith("/") else posixpath.normpath(root.strip("/"))
    if len([p for p in root.split("/") if p]) < 2:
        sys.exit(f"refused: the WordPress root '{root}' is too broad. Set it to the folder that holds wp-config.php.")
    if "\x00" in path:
        sys.exit("refused: null byte in path")
    full = path if path.startswith("/") else posixpath.join(root, path)
    full = posixpath.normpath(full)
    if not (full == root or full.startswith(root.rstrip("/") + "/")):
        sys.exit(f"refused: {path} is outside the WordPress root ({root}). Writes stay inside it.")
    return full


def rel_to_root(root: str, full: str) -> str:
    root = posixpath.normpath(root)
    return posixpath.relpath(full, root) if full.startswith(root) else full.lstrip("/")


def dry(msg: str) -> None:
    print(f"  ~ {msg}")
    print("\n(dry run - nothing changed. Add 'apply' to do it.)")


SAFE_MODES = {"400", "440", "444", "600", "604", "640", "644", "700", "705", "710", "711", "750", "755"}

# Shell commands that are never run, with or without apply. Matched on the normalised command.
DENY = [
    (r"\brm\b[^|;&]*\s(-[a-z]*[rf][a-z]*|--recursive|--force|--dir)\b", "recursive or forced rm - remove single files with 'rm <file> apply'"),
    (r"\b(rmdir|unlink|shred)\b", "removing files outside the backed-up path - use 'rm <file> apply'"),
    (r"\b(chmod|chown|chgrp)\b[^|;&]*\s(-[a-z]*r[a-z]*|--recursive)\b", "recursive permission change - fix files one folder at a time with sftp.py chmod"),
    (r"\bfind\b[^|;&]*\s-(delete|exec|execdir|ok|okdir|fprint|fprint0|fprintf|fls)\b", "find that deletes, writes or runs commands"),
    (r"\bgit\s+(clean|reset\s+--hard|checkout\s+--?\s*\.)", "git command that discards files"),
    (r"\bwp\s+search-replace\b(?![^|;&]*--dry-run)", "wp search-replace without --dry-run - run it with --dry-run first, then ask the member"),
    (r"\bwp\s+db\s+(export|cli)\b", "wp db export/cli - an export lands in the web root where anyone can download it; use cpanel.py backup-now or the host's backup"),
    (r"\bwp\s+(plugin|theme)\s+delete\b|\bwp\s+post\s+delete\b[^|;&]*--force", "deleting plugins, themes or posts for good - switch them off instead"),
    (r"\b(mkfs|fdisk|dd)\b", "disk-level command"),
    (r"\b(shutdown|reboot|halt|poweroff|kill\s+-9\s+-1|killall)\b", "server-level command"),
    (r"(curl|wget)[^|;]*\|\s*(ba|z)?sh\b", "piping a download into a shell"),
    (r"\bcrontab\s+-r\b", "deleting all cron jobs"),
    (r">\s*\S*wp-config\.php", "overwriting wp-config.php from the shell - use sftp.py put (it keeps a backup)"),
    (r"\bwp\s+(db\s+(reset|drop|import|query)|site\s+empty|user\s+delete|eval|eval-file|shell)\b", "destructive or arbitrary wp-cli command"),
    (r"\b(drop\s+(database|table)|truncate\s+table|delete\s+from)\b", "destructive SQL"),
    (r":\(\)\s*\{", "fork bomb"),
    (r"\bhistory\s+-c\b|\bunset\s+HISTFILE\b", "hiding shell history"),
]


def denied(command: str) -> str | None:
    c = re.sub(r"\s+", " ", command.strip().lower())
    for m in re.finditer(r"\bchmod\s+((?:-\w+\s+)*)(\S+)", c):
        mode = m.group(2)
        if re.fullmatch(r"[0-7]{3,4}", mode) and mode[-1] in "2367":
            return "world-writable permissions"
        if re.search(r"(^|,)[ao]*\+[rwx]*w|(^|,)[ugo]*[ao][ugo]*[+=][rwxst]*w", mode):
            return "world-writable permissions"
    for pat, why in DENY:
        if re.search(pat, c):
            return why
    return None


# wp-cli subcommands that only read. Anything else needs 'apply'.
WP_READ = (
    "core version", "core verify-checksums", "core check-update", "plugin list", "plugin status",
    "plugin verify-checksums", "theme list", "theme status", "option get", "option list", "user list",
    "cron event list", "cron schedule list", "transient get", "post list", "post get",
    "db size", "db tables", "doctor", "cli info", "site list", "menu list",
    "rewrite list", "cache type", "language core list", "maintenance-mode status",
)


# wp-cli GLOBAL flags that run code, reach other servers or change which site is touched. Never accepted.
WP_FORBIDDEN_FLAGS = ("--exec", "--require", "--ssh", "--http", "--path", "--context", "--user")
SHELL_META = re.compile(r"[;&|<>()$`\\\r\n]")


def wp_args_problem(args: str) -> str | None:
    """Why this wp-cli argument string is refused outright, or None."""
    if SHELL_META.search(args):
        return "shell characters in a wp-cli command"
    low = args.lower()
    for f in WP_FORBIDDEN_FLAGS:
        if re.search(rf"(^|\s){re.escape(f)}(=|\s|$)", low):
            return f"the wp-cli flag {f} (runs code or switches target)"
    return None


def wp_is_read(args: str) -> bool:
    if wp_args_problem(args):
        return False
    a = re.sub(r"\s+", " ", args.strip().lower())
    if a == "db check":
        return True  # bare only: extra flags are passed to mysqlcheck (--repair, --auto-repair)
    return any(a == r or a.startswith(r + " ") for r in WP_READ)


_SECRET_LINE = re.compile(
    r"(?P<head>define\s*\(\s*['\"](?:DB_PASSWORD|DB_USER|AUTH_KEY|SECURE_AUTH_KEY|LOGGED_IN_KEY|NONCE_KEY|AUTH_SALT|"
    r"SECURE_AUTH_SALT|LOGGED_IN_SALT|NONCE_SALT|[A-Z0-9_]*(?:API_KEY|SECRET|TOKEN|PASSWORD|PASS))['\"]\s*,\s*)"
    r"(?P<q>['\"]).*?(?P=q)",
    re.I)


def redact(text: str) -> str:
    """Hide wp-config secrets in anything printed (they would land in the chat transcript)."""
    return _SECRET_LINE.sub(lambda m: f"{m.group('head')}{m.group('q')}[hidden by WPU]{m.group('q')}", text)


def local_download(name: str) -> "Path":
    """Downloads only ever land in sites/<slug>/hosting/downloads/ and never overwrite."""
    base = (hosting_dir() / "downloads").resolve()
    base.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^A-Za-z0-9._-]", "_", posixpath.basename(name)) or "download"
    p = base / stem
    n = 1
    while p.exists():
        p = base / f"{n}-{stem}"
        n += 1
    return p


_HOWTO = {
    "sftp": """{path} has no "hosting.sftp" block. Add one (NO password in it):

  "hosting": {{
    "sftp": {{
      "host": "ssh.clienthost.com",
      "port": 22,
      "user": "sftp-username",
      "root": "/home/user/public_html",
      "auth": "password",
      "keyFile": ""
    }}
  }}

root = the folder that holds wp-config.php. For key login set "auth": "key" and "keyFile" to the
private key's path on your computer. Then save the password (or the key's passphrase) in your own
terminal:
  powershell -File scripts/wpu-secret.ps1 set {slug} sftp_pass
Then pin the server's identity once:  python tools/hosting/sftp.py trust""",
    "cpanel": """{path} has no "hosting.cpanel" block. Add one (NO password or token in it):

  "hosting": {{
    "cpanel": {{
      "host": "server123.clienthost.com",
      "port": 2083,
      "user": "cpanel-username",
      "wpRoot": "public_html",
      "domain": "clientsite.com"
    }}
  }}

wpRoot = the folder under the cPanel home that holds wp-config.php.
Make an API token in cPanel > Security > Manage API Tokens (name it after yourself, e.g. "wpu-ashish"),
then save it in your own terminal:
  powershell -File scripts/wpu-secret.ps1 set {slug} cpanel_token
Revoke the token in the same screen when the job is done.""",
}
