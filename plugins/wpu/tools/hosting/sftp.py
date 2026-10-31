#!/usr/bin/env python3
"""SFTP / SSH access to a client's hosting - the way in when WordPress (and so the bridge) is down.

    python tools/hosting/sftp.py trust                      show the server's fingerprint and pin it (once per site)
    python tools/hosting/sftp.py check                      log in, show the account and the WordPress root

  Read (run straight away):
    python tools/hosting/sftp.py ls    [dir]
    python tools/hosting/sftp.py stat  <path>
    python tools/hosting/sftp.py get   <remote> [local]     download (default: sites/<slug>/hosting/downloads/)
    python tools/hosting/sftp.py tail  <file> [lines]
    python tools/hosting/sftp.py find  <name-pattern> [dir] e.g.  find "*.php" wp-content/mu-plugins
    python tools/hosting/sftp.py logs  [lines]              error_log, wp-content/debug.log, ~/logs - newest lines

  Write (DRY RUN unless the last word is "apply"; a backup is saved first):
    python tools/hosting/sftp.py put   <local> <remote>     upload; verified, then swapped in
    python tools/hosting/sftp.py mv    <from> <to>
    python tools/hosting/sftp.py rm    <file>               one file, never a folder; never wp-config.php
    python tools/hosting/sftp.py mkdir <dir>
    python tools/hosting/sftp.py chmod <mode> <path>        644/640/600/755/750/... - never world-writable
    python tools/hosting/sftp.py plugin-off <folder>        rename wp-content/plugins/<folder> so WordPress skips it
    python tools/hosting/sftp.py plugin-on  <folder>        undo plugin-off
    python tools/hosting/sftp.py theme-off  <folder>        same for a theme (WordPress falls back to a default theme)
    python tools/hosting/sftp.py theme-on   <folder>
    python tools/hosting/sftp.py maintenance-off            remove a stuck .maintenance file

  Shell (SSH accounts only):
    python tools/hosting/sftp.py exec "<command>"           read-only commands (ls, tail, grep, df, php -v...) run;
                                                            anything else needs "apply"; dangerous ones never run
    python tools/hosting/sftp.py wp   "<wp-cli args>"       e.g. wp "plugin list"; write commands need "apply"

Paths are relative to the WordPress root from site.json (hosting.sftp.root). Writes must stay inside it.
Credentials: the member's encrypted store (sftp_pass, or sftp_keypass for a key with a passphrase).
"""
from __future__ import annotations

import fnmatch
import hashlib
import base64
import os
import posixpath
import re
import shlex
import stat
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _hosting import (SAFE_MODES, backup_path, denied, dry, hosting_cfg, hosting_dir, inside_root,  # noqa: E402
                      local_download, log_action, need_secret, redact, rel_to_root, split_apply, wp_args_problem,
                      wp_is_read)
from _wpu import secret, site_slug  # noqa: E402

try:
    import paramiko
except ImportError:
    sys.exit("paramiko is not installed. Run:  python -m pip install --user paramiko")

TOOL = "sftp"
READ_SHELL = {"ls", "cat", "tail", "head", "grep", "find", "du", "df", "stat", "wc", "whoami", "pwd", "uptime",
              "free", "ps", "id", "uname", "which", "file", "md5sum", "sha256sum", "php", "date"}


# --------------------------------------------------------------------------- connection

def known_hosts() -> Path:
    return hosting_dir() / "known_hosts"


def fingerprint(key) -> str:
    return "SHA256:" + base64.b64encode(hashlib.sha256(key.asbytes()).digest()).decode().rstrip("=")


def host_id(s: dict) -> str:
    port = int(s.get("port", 22))
    return s["host"] if port == 22 else f"[{s['host']}]:{port}"


def credentials(s: dict) -> dict:
    auth = (s.get("auth") or "password").lower()
    if auth == "key":
        kf = os.path.expanduser(s.get("keyFile") or "")
        if not kf or not os.path.exists(kf):
            sys.exit(f'hosting.sftp.keyFile "{s.get("keyFile")}" not found on this computer.')
        return {"key_filename": kf, "passphrase": secret(site_slug(), "sftp_keypass")}
    return {"password": need_secret("sftp_pass")}


def connect(s: dict):
    for k in ("host", "user", "root"):
        if not s.get(k):
            sys.exit(f'site.json hosting.sftp.{k} is empty.')
    client = paramiko.SSHClient()
    kh = known_hosts()
    if kh.exists():
        client.load_host_keys(str(kh))
    # Pinned identity: an unknown or changed key is refused. A man-in-the-middle would get the
    # hosting password, and that is the keys to the whole site.
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    try:
        client.connect(hostname=s["host"], port=int(s.get("port", 22)), username=s["user"], timeout=30,
                       allow_agent=False, look_for_keys=False, banner_timeout=30, auth_timeout=30,
                       **credentials(s))
    except paramiko.BadHostKeyException as e:
        sys.exit(
            f"STOP: the server's identity CHANGED for {host_id(s)}.\n"
            f"  pinned : {fingerprint(e.expected_key)}\n  now    : {fingerprint(e.key)}\n"
            "This happens after a server migration - or when someone is intercepting the connection.\n"
            "Confirm the new fingerprint with the host (control panel or support) before you run 'trust' again."
        )
    except paramiko.PasswordRequiredException:
        sys.exit(f"The key file needs its passphrase. Save it with:  wpu-secret.ps1 set {site_slug()} sftp_keypass")
    except paramiko.SSHException as e:
        if (s.get("auth") or "").lower() == "key" and ("key" in str(e).lower() and "known_hosts" not in str(e)):
            sys.exit(f"Could not open the key file {s.get('keyFile')}: {e}\nIf the key has a passphrase, save it with:  "
                     f"wpu-secret.ps1 set {site_slug()} sftp_keypass   (and check the file is a private key, not the .pub).")
        if "not found in known_hosts" in str(e):
            sys.exit(f"The server {host_id(s)} is not pinned yet. Run:  python tools/hosting/sftp.py trust")
        sys.exit(f"SSH error: {e}")
    except paramiko.AuthenticationException:
        sys.exit("Login refused. Check hosting.sftp.user, and the saved sftp_pass / key (wpu-secret.ps1 set ...).")
    except OSError as e:
        sys.exit(f"Could not reach {s['host']}:{s.get('port', 22)} - {e}")
    return client


# --------------------------------------------------------------------------- helpers

def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def rpath(s: dict, p: str) -> str:
    """Path for reading: relative to root, or absolute as given."""
    return posixpath.normpath(p if p.startswith("/") else posixpath.join(s["root"], p or "."))


def confine(sftp, root: str, path: str) -> str:
    """Write target inside the WordPress root - checked on the server's REAL paths, so a symlink inside
    the root that points elsewhere (hosts often symlink uploads/ or public_html) cannot be used to
    write outside it. The target itself must not be a symlink."""
    full = inside_root(root, path)
    try:
        real_root = sftp.normalize(root)
    except IOError:
        sys.exit(f"The WordPress root {root} does not exist on the server - check hosting.sftp.root.")
    parent = posixpath.dirname(full)
    while True:  # nearest existing ancestor (mkdir and new files have no parent yet)
        try:
            real_parent = sftp.normalize(parent)
            break
        except IOError:
            if parent in ("/", "", root):
                real_parent = real_root
                break
            parent = posixpath.dirname(parent)
    if not (real_parent == real_root or real_parent.startswith(real_root.rstrip("/") + "/")):
        sys.exit(f"refused: {path} resolves outside the WordPress root (through a symlink: {real_parent}).")
    st = exists(sftp, full)
    if st and stat.S_ISLNK(st.st_mode) and full != posixpath.normpath(root):
        sys.exit(f"refused: {full} is a symlink. Change the file it points to directly, inside the root.")
    return full


def exists(sftp, p: str):
    try:
        return sftp.lstat(p)
    except IOError:
        return None


def save_backup(sftp, s: dict, full: str) -> Path | None:
    st = exists(sftp, full)
    if not st or stat.S_ISDIR(st.st_mode):
        return None
    dst = backup_path(rel_to_root(s["root"], full))
    sftp.get(full, str(dst))
    return dst


def shell(client, s: dict, command: str, timeout: int = 180) -> int:
    full = f"cd {shlex.quote(s['root'])} && {command}"
    _in, out, err = client.exec_command(full, timeout=timeout)
    o = out.read().decode("utf-8", "replace")
    e = err.read().decode("utf-8", "replace")
    if o:
        print(redact(o.rstrip()))
    if e:
        print("stderr:\n" + redact(e.rstrip()))
    return out.channel.recv_exit_status()


def shell_is_read(command: str) -> bool:
    """True only for a plain read-only command. Anything doubtful returns False, so it needs 'apply'
    (and with it, the member's approval)."""
    # Pipes between read commands are fine; every other shell operator is not.
    if re.search(r"[;&<>()$`\\\r\n{}]", command):
        return False
    try:
        parts = [shlex.split(seg) for seg in command.split("|")]
    except ValueError:
        return False
    for p in parts:
        if not p or "/" in p[0] or p[0] not in READ_SHELL:
            return False  # a bare command name only: "/usr/bin/find" would slip past the flag checks
        name, rest = p[0], p[1:]
        if name == "find" and any(x.startswith(("-f", "-ok", "-exec", "-delete")) and x != "-follow" for x in rest):
            return False
        if name == "tail" and any(x.startswith(("-f", "-F", "--follow", "--retry")) for x in rest):
            return False  # follows forever
        if name == "date" and any(x.startswith(("-s", "--set")) for x in rest):
            return False
        if name == "du" and any(x.startswith("--files0-from") for x in rest):
            return False
        if name == "php" and rest not in (["-v"], ["-m"], ["--version"]):
            return False
    return True


# --------------------------------------------------------------------------- commands

def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(__doc__)
        return 2
    cmd = sys.argv[1].lower()
    args, apply = split_apply(sys.argv[2:])
    s = hosting_cfg("sftp")
    s["root"] = posixpath.normpath(s["root"])

    if cmd == "trust":
        # Fetch the server's key WITHOUT logging in: the password must never go to a server the member has
        # not confirmed yet.
        try:
            t = paramiko.Transport((s["host"], int(s.get("port", 22))))
            t.banner_timeout = 30
            t.start_client(timeout=30)
            key = t.get_remote_server_key()
            t.close()
        except (paramiko.SSHException, OSError) as e:
            sys.exit(f"Could not reach {s['host']}:{s.get('port', 22)} - {e}")
        hk = paramiko.HostKeys()
        if known_hosts().exists():
            hk.load(str(known_hosts()))
        hk.add(host_id(s), key.get_name(), key)
        hk.save(str(known_hosts()))
        print(f"{host_id(s)}  {key.get_name()}  {fingerprint(key)}")
        print(f"pinned in {known_hosts()}")
        print("If the host shows its SSH fingerprint (control panel or support), check it matches the line above.")
        log_action(TOOL, "trust", {"host": host_id(s), "fingerprint": fingerprint(key)})
        return 0

    client = connect(s)
    try:
        sftp = client.open_sftp()
        root = s["root"]

        if cmd == "check":
            print(f"logged in as {s['user']} on {host_id(s)}")
            st = exists(sftp, posixpath.join(root, "wp-config.php"))
            print(f"WordPress root {root}: {'wp-config.php found' if st else 'NO wp-config.php here - check hosting.sftp.root'}")
            for p in ("wp-content/plugins", "wp-content/themes", "wp-content/mu-plugins", ".maintenance",
                      "error_log", "wp-content/debug.log"):
                st = exists(sftp, posixpath.join(root, p))
                if st:
                    print(f"  {p:<24} {'folder' if stat.S_ISDIR(st.st_mode) else human(st.st_size)}")
            try:
                _i, o, _e = client.exec_command("echo shell-ok", timeout=20)
                print("shell access: " + ("yes" if o.read().decode().strip() == "shell-ok" else "no"))
            except paramiko.SSHException:
                print("shell access: no (SFTP only)")
            return 0

        if cmd == "ls":
            p = rpath(s, args[0] if args else "")
            rows = sorted(sftp.listdir_attr(p), key=lambda a: a.filename.lower())
            print(f"{p}\n")
            for a in rows:
                kind = "l" if stat.S_ISLNK(a.st_mode) else "d" if stat.S_ISDIR(a.st_mode) else "-"
                when = datetime.fromtimestamp(a.st_mtime).strftime("%Y-%m-%d %H:%M")
                print(f"  {kind} {oct(a.st_mode & 0o777)[2:]:>4} {human(a.st_size):>9}  {when}  {a.filename}")
            print(f"\n{len(rows)} entr{'y' if len(rows) == 1 else 'ies'}")
            return 0

        if cmd == "stat":
            p = rpath(s, args[0])
            st = exists(sftp, p)
            if not st:
                print(f"{p}: does not exist")
                return 1
            kind = "symlink" if stat.S_ISLNK(st.st_mode) else "folder" if stat.S_ISDIR(st.st_mode) else "file"
            print(f"{p}\n  {kind}, mode {oct(st.st_mode & 0o777)[2:]}, {human(st.st_size)}, "
                  f"modified {datetime.fromtimestamp(st.st_mtime):%Y-%m-%d %H:%M}, uid {st.st_uid}")
            return 0

        if cmd == "get":
            src = rpath(s, args[0])
            # Always into sites/<slug>/hosting/downloads/, never over an existing file: a file from a
            # possibly hacked server must not be able to land on the plugin, a hook or a settings file.
            dst = local_download(args[1] if len(args) > 1 else src)
            sftp.get(src, str(dst))
            print(f"{src}\n  -> {dst}  {human(dst.stat().st_size)}")
            return 0

        if cmd == "tail":
            p = rpath(s, args[0])
            n = int(args[1]) if len(args) > 1 else 60
            print_tail(sftp, p, n)
            return 0

        if cmd == "logs":
            n = int(args[0]) if args else 40
            home = posixpath.dirname(root)
            cands = [posixpath.join(root, "error_log"), posixpath.join(root, "wp-content/debug.log"),
                     posixpath.join(root, "wp-admin/error_log"), posixpath.join(root, "php_errorlog")]
            for d in (posixpath.join(home, "logs"), posixpath.join(posixpath.dirname(home), "logs")):
                try:
                    cands += [posixpath.join(d, f) for f in sftp.listdir(d) if "error" in f.lower()]
                except IOError:
                    pass
            found = [(c, st) for c in cands if (st := exists(sftp, c)) and not stat.S_ISDIR(st.st_mode)]
            if not found:
                print("No error logs found. WP_DEBUG_LOG may be off; check the host panel for logs.")
                return 0
            for c, st in sorted(found, key=lambda x: -x[1].st_mtime):
                print(f"\n=== {c}  ({human(st.st_size)}, modified {datetime.fromtimestamp(st.st_mtime):%Y-%m-%d %H:%M})")
                print_tail(sftp, c, n, header=False)
            return 0

        if cmd == "find":
            pat = args[0]
            start = rpath(s, args[1] if len(args) > 1 else "")
            hits = []
            walk(sftp, start, pat, hits, depth=0)
            for h, st in hits[:300]:
                print(f"  {datetime.fromtimestamp(st.st_mtime):%Y-%m-%d %H:%M}  {human(st.st_size):>9}  {h}")
            print(f"\n{len(hits)} match(es){' (first 300 shown)' if len(hits) > 300 else ''}")
            return 0

        # ----------------------------------------------------------------- writes

        if cmd == "put":
            if len(args) < 2:
                sys.exit("put <local-file> <remote-path>")
            src, dst = Path(args[0]), confine(sftp, root, args[1])
            if not src.is_file():
                sys.exit(f"local file not found: {src}")
            old = exists(sftp, dst)
            if old and stat.S_ISDIR(old.st_mode):
                sys.exit(f"{dst} is a folder - give the full file path")
            if not apply:
                dry(f"upload {src} ({human(src.stat().st_size)}) -> {dst}" + (" (replaces the current file; a backup is kept)" if old else " (new file)"))
                return 0
            bak = save_backup(sftp, s, dst)
            tmp = dst + ".wpu-uploading"
            sftp.put(str(src), tmp)
            size = sftp.stat(tmp).st_size
            if size != src.stat().st_size:
                sftp.remove(tmp)
                sys.exit(f"size mismatch {size} != {src.stat().st_size} - upload discarded, nothing changed")
            if old:
                sftp.chmod(tmp, old.st_mode & 0o777)
                try:
                    sftp.posix_rename(tmp, dst)  # atomic swap where the server supports it
                except IOError:
                    sftp.remove(dst)
                    sftp.rename(tmp, dst)
            else:
                sftp.rename(tmp, dst)
            print(f"{src}\n  -> {dst}  {human(size)}  (verified)")
            if bak:
                print(f"  previous version saved: {bak}")
            log_action(TOOL, "put", {"path": dst, "bytes": size, "backup": str(bak) if bak else None})
            return 0

        if cmd == "mv":
            a, b = confine(sftp, root, args[0]), confine(sftp, root, args[1])
            if not exists(sftp, a):
                sys.exit(f"{a} does not exist")
            if exists(sftp, b):
                sys.exit(f"{b} already exists - move or remove it first")
            if not apply:
                dry(f"rename {a} -> {b}")
                return 0
            sftp.rename(a, b)
            print(f"{a}\n  -> {b}")
            log_action(TOOL, "mv", {"from": a, "to": b})
            return 0

        if cmd in ("plugin-off", "plugin-on", "theme-off", "theme-on"):
            kind = "plugins" if cmd.startswith("plugin") else "themes"
            name = args[0].strip("/") if args else ""
            if not name or "/" in name or name.startswith("."):
                sys.exit(f"{cmd} <folder-name>   e.g. {cmd} elementor-pro")
            base = confine(sftp, root, f"wp-content/{kind}")
            if cmd.endswith("-off"):
                a, b = f"{base}/{name}", f"{base}/{name}.wpu-off"
            else:
                a, b = f"{base}/{name}.wpu-off", f"{base}/{name}"
            if not exists(sftp, a):
                sys.exit(f"{a} does not exist" + (" (was it turned off with sftp.py?)" if cmd.endswith("-on") else ""))
            if exists(sftp, b):
                sys.exit(f"{b} already exists")
            what = "WordPress will skip it on the next request" if cmd.endswith("-off") else "it can be activated again in wp-admin"
            if not apply:
                dry(f"rename {a} -> {b}  ({what})")
                return 0
            sftp.rename(a, b)
            print(f"{a}\n  -> {b}\n{what}.")
            if cmd == "plugin-on":
                print("Note: WordPress deactivated it while it was missing - reactivate it in wp-admin (or wp \"plugin activate ...\" apply).")
            log_action(TOOL, cmd, {"from": a, "to": b})
            return 0

        if cmd == "maintenance-off":
            p = confine(sftp, root, ".maintenance")
            if not exists(sftp, p):
                print("No .maintenance file - the site is not stuck in maintenance mode.")
                return 0
            if not apply:
                dry(f"remove {p} (a stuck update leaves it behind; it shows 'Briefly unavailable for scheduled maintenance')")
                return 0
            bak = save_backup(sftp, s, p)
            sftp.remove(p)
            print(f"removed {p} (backup {bak})")
            log_action(TOOL, "maintenance-off", {"path": p, "backup": str(bak)})
            return 0

        if cmd == "rm":
            p = confine(sftp, root, args[0])
            st = exists(sftp, p)
            if not st:
                sys.exit(f"{p} does not exist")
            if stat.S_ISDIR(st.st_mode):
                sys.exit("rm removes single files only. To switch off a plugin or theme use plugin-off / theme-off.")
            if posixpath.basename(p) == "wp-config.php" and posixpath.dirname(p) in (root, posixpath.dirname(root)):
                sys.exit("refused: removing wp-config.php takes the site down. Replace it with 'put' instead (a backup is kept).")
            if not apply:
                dry(f"remove {p} ({human(st.st_size)}; a backup is kept)")
                return 0
            bak = save_backup(sftp, s, p)
            sftp.remove(p)
            print(f"removed {p}\n  backup: {bak}")
            log_action(TOOL, "rm", {"path": p, "backup": str(bak)})
            return 0

        if cmd == "mkdir":
            p = confine(sftp, root, args[0])
            if exists(sftp, p):
                print(f"{p} already exists")
                return 0
            if not apply:
                dry(f"create folder {p}")
                return 0
            sftp.mkdir(p, 0o755)
            print(f"created {p}")
            log_action(TOOL, "mkdir", {"path": p})
            return 0

        if cmd == "chmod":
            if len(args) < 2:
                sys.exit("chmod <mode> <path>   e.g. chmod 644 wp-config.php")
            mode, p = args[0].lstrip("0") or "0", confine(sftp, root, args[1])
            mode = mode.zfill(3)
            if mode not in SAFE_MODES:
                sys.exit(f"refused: mode {mode}. Allowed: {', '.join(sorted(SAFE_MODES))} (never world-writable).")
            st = exists(sftp, p)
            if not st:
                sys.exit(f"{p} does not exist")
            before = oct(st.st_mode & 0o777)[2:]
            if not apply:
                dry(f"chmod {p}: {before} -> {mode}")
                return 0
            sftp.chmod(p, int(mode, 8))
            print(f"{p}: {before} -> {mode}")
            log_action(TOOL, "chmod", {"path": p, "before": before, "after": mode})
            return 0

        if cmd in ("exec", "wp"):
            if not args:
                sys.exit(f'{cmd} "<command>"')
            line = " ".join(args)
            if cmd == "wp":
                bad = wp_args_problem(line)
                if bad:
                    sys.exit(f"refused ({bad}). Pass plain wp-cli arguments, e.g.  wp \"plugin list\"")
                try:
                    wp_argv = shlex.split(line)
                except ValueError as e:
                    sys.exit(f"could not parse the wp-cli arguments: {e}")
                # Rebuilt from parsed words, each quoted: nothing in them can act as shell syntax.
                command = shlex.join(["wp", *wp_argv, f"--path={root}"]
                                     + (["--skip-themes", "--skip-plugins"] if needs_safe_mode(line) else []))
            else:
                command = line
            why = denied(command)
            if why:
                sys.exit(f"refused ({why}). This command is never run through WP Ultimate Build.")
            read = wp_is_read(line) if cmd == "wp" else shell_is_read(line)
            if not read and not apply:
                dry(f"run on {host_id(s)} in {root}:\n      {command}")
                return 0
            print(f"$ {command}\n")
            code = shell(client, s, command)
            if not read:
                log_action(TOOL, cmd, {"command": command, "exit": code})
            return code

        sys.exit(f"unknown command: {cmd}\n{__doc__}")
    finally:
        client.close()


def needs_safe_mode(line: str) -> bool:
    """wp-cli loads every plugin, so on a site with a fatal error even 'plugin list' dies. The read
    commands run with plugins and themes skipped; that is exactly the state a rescue needs."""
    return wp_is_read(line) or line.strip().lower().startswith(("plugin deactivate", "plugin activate", "theme activate"))


def print_tail(sftp, p: str, n: int, header: bool = True) -> None:
    st = sftp.stat(p)
    with sftp.open(p, "r") as fh:
        # Logs can be hundreds of MB; read only the last ~256 KB.
        start = max(0, st.st_size - 262144)
        fh.seek(start)
        lines = fh.read().decode("utf-8", "replace").splitlines()
    if start and lines:
        lines = lines[1:]
    if header:
        print(f"{p}  ({human(st.st_size)}, last {n} lines)\n")
    for line in lines[-n:]:
        print("  " + redact(line))


def walk(sftp, d: str, pat: str, hits: list, depth: int) -> None:
    if depth > 8 or len(hits) > 2000:
        return
    try:
        rows = sftp.listdir_attr(d)
    except IOError:
        return
    for a in rows:
        p = posixpath.join(d, a.filename)
        if fnmatch.fnmatch(a.filename, pat):
            hits.append((p + ("/" if stat.S_ISDIR(a.st_mode) else ""), a))
        if stat.S_ISDIR(a.st_mode) and not stat.S_ISLNK(a.st_mode) and a.filename not in ("node_modules", ".git", "cache"):
            walk(sftp, p, pat, hits, depth + 1)


if __name__ == "__main__":
    sys.exit(main())
