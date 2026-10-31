#!/usr/bin/env python3
"""
wp_security_scan.py — static security scan for WordPress plugin/theme code.

Usage:
    python3 wp_security_scan.py /path/to/plugin-folder [--json] [--quiet]

No dependencies. Regex-based, so it errs toward reporting: every finding needs
a human decision — fix it, or leave a one-line comment in the code saying why
it is safe. A clean run is not proof of safety; it only means the known-bad
shapes are absent.

Exit codes: 0 = no findings, 1 = findings, 2 = bad usage.
"""

import argparse
import json
import os
import re
import sys

SKIP_DIRS = {".git", "node_modules", "vendor", ".svn", "__pycache__", "dist"}
PHP_EXT = (".php", ".inc", ".phtml")

# (id, severity, compiled pattern, message)
RULES = [
    # --- Output escaping -------------------------------------------------
    ("unescaped-echo", "high",
     r"""echo\s+\$(?!wpdb)[A-Za-z_][\w\['\"\]\->]*\s*[;\.]""",
     "Variable echoed without an escaping function (esc_html/esc_attr/esc_url/wp_kses_post)."),
    ("unescaped-short-echo", "high",
     r"""<\?=\s*\$""",
     "Short echo tag outputs a variable unescaped."),
    ("unescaped-interpolation", "medium",
     r"""echo\s+["'][^"'\n]*\$\{?[A-Za-z_]""",
     "Variable interpolated into an echoed string — escape it in its output context first."),
    ("unescaped-attr", "high",
     r"""=["']\s*<\?php\s+echo\s+\$(?!\w*\s*\?>\s*["']?\s*$)""",
     "Variable echoed into an HTML attribute — needs esc_attr()/esc_url()."),
    ("printf-unescaped", "medium",
     r"""\b(printf|vprintf)\s*\(\s*["'][^"']*%s""",
     "printf outputs a raw %s — escape the argument (esc_html) before printing."),

    # --- Request data ----------------------------------------------------
    ("raw-superglobal", "high",
     r"""\$_(GET|POST|COOKIE|REQUEST)\s*\[[^\]]+\](?!\s*\))""",
     "Request data used directly — wp_unslash() then sanitize/validate before use."),
    ("request-superglobal", "medium",
     r"""\$_REQUEST\s*\[""",
     "$_REQUEST mixes GET/POST/COOKIE — read the specific superglobal instead."),
    ("server-trust", "medium",
     r"""\$_SERVER\s*\[\s*['"](HTTP_HOST|PHP_SELF|HTTP_X_FORWARDED_FOR|HTTP_REFERER|REQUEST_URI)['"]\s*\]""",
     "Client-controlled $_SERVER value — use home_url()/admin_url() or sanitize and validate."),

    # --- SQL --------------------------------------------------------------
    ("sql-concat", "critical",
     r"""\$wpdb->(query|get_results|get_row|get_var|get_col)\s*\(\s*["'][^"']*\$""",
     "SQL built with an interpolated variable — use $wpdb->prepare() with %s/%d."),
    ("sql-concat-dot", "critical",
     r"""\$wpdb->(query|get_results|get_row|get_var|get_col)\s*\(\s*["'][^"']*["']\s*\.\s*\$""",
     "SQL concatenated with a variable — use $wpdb->prepare()."),
    ("prepare-interpolated", "high",
     r"""prepare\s*\(\s*["'][^"']*\{\$(?!wpdb)""",
     "Variable interpolated inside prepare() instead of being passed as a placeholder argument."),
    ("orderby-variable", "high",
     r"""ORDER\s+BY\s+[{\$'"]*\$""",
     "ORDER BY built from a variable — placeholders don't cover identifiers; use an allowlist."),

    # --- Endpoints and authorization -------------------------------------
    ("ajax-nopriv", "high",
     r"""add_action\s*\(\s*['"]wp_ajax_nopriv_""",
     "Unauthenticated AJAX endpoint — confirm anonymous access is required and treat it as a public API (nonce, validation, rate limit)."),
    ("admin-post-nopriv", "high",
     r"""add_action\s*\(\s*['"]admin_post_nopriv_""",
     "Unauthenticated admin-post endpoint — same rules as a public API."),
    ("rest-open", "critical",
     r"""['"]permission_callback['"]\s*=>\s*['"]__return_true['"]""",
     "REST route with no permission check — only acceptable for genuinely public read-only data."),
    ("is-admin-as-auth", "high",
     r"""if\s*\(\s*!?\s*is_admin\s*\(\s*\)\s*\)""",
     "is_admin() is not a permission check — use current_user_can()."),
    ("logged-in-as-auth", "medium",
     r"""if\s*\(\s*!?\s*is_user_logged_in\s*\(\s*\)\s*\)""",
     "Logged-in is not a capability — a subscriber passes this. Use current_user_can()."),

    # --- Privilege / options ---------------------------------------------
    ("role-from-input", "critical",
     r"""(wp_insert_user|wp_update_user|add_role|set_role|add_cap)\s*\([^)]*\$_(GET|POST|REQUEST)""",
     "User role/capability derived from request data — privilege escalation. Hard-code the role."),
    ("option-from-input", "critical",
     r"""update_option\s*\(\s*\$_(GET|POST|REQUEST)""",
     "Option key taken from request data — attackers can rewrite core settings."),
    ("register-setting-no-sanitize", "medium",
     r"""register_setting\s*\(\s*[^,]+,\s*[^,)]+\s*\)\s*;""",
     "register_setting() without a sanitize_callback."),

    # --- Dangerous functions ---------------------------------------------
    ("eval", "critical", r"""(?<![\w>$])eval\s*\(""", "eval() — remove it; there is always another design."),
    ("create-function", "critical", r"""create_function\s*\(""", "create_function() is removed in PHP 8 and unsafe."),
    ("extract", "high", r"""(?<![\w>$])extract\s*\(""", "extract() lets input define variable names."),
    ("unserialize", "critical", r"""(?<![\w>$])unserialize\s*\(""", "unserialize() on untrusted data enables PHP object injection — use json_decode()."),
    ("shell", "critical",
     r"""(?<![\w>$])(exec|shell_exec|system|passthru|popen|proc_open)\s*\(""",
     "Shell execution in a WordPress plugin — remove it."),
    ("assert", "high", r"""(?<![\w>$])assert\s*\(\s*\$""", "assert() with a variable behaves like eval() on older PHP."),
    ("dynamic-call", "high",
     r"""call_user_func(_array)?\s*\(\s*\$_(GET|POST|REQUEST)""",
     "Function name taken from request data."),

    # --- Files and remote ------------------------------------------------
    ("include-variable", "critical",
     r"""(include|include_once|require|require_once)\s*\(?\s*['"]?[^;'"\n]*\$_(GET|POST|REQUEST)""",
     "File inclusion driven by request data — local file inclusion. Map allowlisted keys to paths."),
    ("file-op-input", "critical",
     r"""(file_get_contents|fopen|unlink|rename|copy|file_put_contents|readfile|scandir|rmdir|mkdir)\s*\([^)]*\$_(GET|POST|REQUEST)""",
     "File operation on a request-controlled path — traversal / arbitrary file access."),
    ("move-uploaded", "high",
     r"""move_uploaded_file\s*\(""",
     "Raw upload handling — use wp_handle_upload() with a MIME allowlist and wp_check_filetype_and_ext()."),
    ("remote-get", "medium",
     r"""\bwp_remote_(get|post|request|head)\s*\(""",
     "Use wp_safe_remote_* to block SSRF against internal addresses."),
    ("remote-fetch-input", "critical",
     r"""(file_get_contents|curl_init|wp_remote_get)\s*\(\s*\$_(GET|POST|REQUEST)""",
     "Fetching a request-supplied URL — SSRF. Allowlist scheme and host, use wp_safe_remote_get()."),
    ("unsafe-redirect", "medium",
     r"""wp_redirect\s*\(\s*\$""",
     "wp_redirect() with a variable — use wp_safe_redirect() or validate against an allowlist."),
    ("upload-mimes", "high",
     r"""add_filter\s*\(\s*['"]upload_mimes['"]""",
     "Widening allowed upload types — confirm no executable type is added."),

    # --- Secrets and hygiene ---------------------------------------------
    ("hardcoded-secret", "high",
     r"""(?i)(api[_-]?key|secret|password|passwd|token|bearer|private[_-]?key)\s*['"]?\s*[:=]>?\s*['"][A-Za-z0-9_\-\/\+]{16,}['"]""",
     "Possible hard-coded credential — read it from an option or a wp-config constant."),
    ("weak-compare", "medium",
     r"""(?<![=!<>])==\s*\$?(hash|md5|sha1|signature|token)""",
     "Comparing a secret with == is timing-unsafe — use hash_equals()."),
    ("md5-password", "medium",
     r"""\b(md5|sha1)\s*\(\s*\$(pass|password|pwd)""",
     "md5/sha1 for passwords — use wp_hash_password()/wp_check_password()."),
    ("debug-output", "low",
     r"""(?<![\w>$])(var_dump|print_r|var_export)\s*\(""",
     "Debug output left in the code."),
    ("display-errors", "medium",
     r"""(ini_set\s*\(\s*['"]display_errors|error_reporting\s*\()""",
     "Plugin changing error display — leaks internals."),
]

COMPILED = [(rid, sev, re.compile(pat), msg) for rid, sev, pat, msg in RULES]

SEV_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

# File-level checks
ABSPATH_RE = re.compile(r"""defined\s*\(\s*['"]ABSPATH['"]""")
NONCE_RE = re.compile(r"""(check_admin_referer|check_ajax_referer|wp_verify_nonce|wp_nonce_field|settings_fields|WP_REST_Server)""")
CAP_RE = re.compile(r"""(current_user_can|permission_callback|user_can\s*\(|add_options_page|add_menu_page|add_submenu_page)""")
HANDLER_RE = re.compile(r"""add_action\s*\(\s*['"](wp_ajax_|admin_post_|admin_init|wp_loaded)""")
SUPPRESS_RE = re.compile(r"""(phpcs:ignore|wpsec:ignore|@security-reviewed)""", re.I)


def scan_file(path, rel):
    findings = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
    except OSError as exc:
        return [{"file": rel, "line": 0, "id": "read-error", "severity": "low", "message": str(exc), "code": ""}]

    text = "\n".join(lines)

    for num, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith(("//", "#", "*", "/*")):
            continue
        if SUPPRESS_RE.search(line):
            continue
        # Lines that already escape are much less interesting for output rules.
        escaped = re.search(r"""\b(esc_html|esc_attr|esc_url|esc_js|esc_textarea|wp_kses|wp_json_encode|absint|intval|sanitize_)""", line)
        for rid, sev, pattern, msg in COMPILED:
            if escaped and rid.startswith("unescaped"):
                continue
            if pattern.search(line):
                findings.append({
                    "file": rel, "line": num, "id": rid, "severity": sev,
                    "message": msg, "code": stripped[:160],
                })

    if "<?php" in text and not ABSPATH_RE.search(text):
        findings.append({
            "file": rel, "line": 1, "id": "no-abspath-guard", "severity": "medium",
            "message": "No `if ( ! defined( 'ABSPATH' ) ) { exit; }` guard — file can be requested directly.",
            "code": "",
        })

    if HANDLER_RE.search(text):
        if not NONCE_RE.search(text):
            findings.append({
                "file": rel, "line": 1, "id": "handler-no-nonce", "severity": "high",
                "message": "Request handlers registered but no nonce verification found in this file (CSRF).",
                "code": "",
            })
        if not CAP_RE.search(text):
            findings.append({
                "file": rel, "line": 1, "id": "handler-no-capability", "severity": "high",
                "message": "Request handlers registered but no current_user_can() found in this file (broken access control).",
                "code": "",
            })

    return findings


def scan(target):
    findings, files = [], 0
    if os.path.isfile(target):
        findings += scan_file(target, os.path.basename(target))
        return findings, 1
    for root, dirs, names in os.walk(target):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in names:
            if not name.endswith(PHP_EXT):
                continue
            full = os.path.join(root, name)
            files += 1
            findings += scan_file(full, os.path.relpath(full, target))
    return findings, files


def main():
    ap = argparse.ArgumentParser(description="Static security scan for WordPress plugin code.")
    ap.add_argument("path", help="Plugin folder or PHP file")
    ap.add_argument("--json", action="store_true", help="Machine-readable output")
    ap.add_argument("--quiet", action="store_true", help="Only critical and high findings")
    args = ap.parse_args()

    if not os.path.exists(args.path):
        print(f"Path not found: {args.path}", file=sys.stderr)
        return 2

    findings, files = scan(args.path)
    if args.quiet:
        findings = [f for f in findings if f["severity"] in ("critical", "high")]
    findings.sort(key=lambda f: (SEV_ORDER.get(f["severity"], 9), f["file"], f["line"]))

    if args.json:
        print(json.dumps({"scanned_files": files, "findings": findings}, indent=2))
        return 1 if findings else 0

    print(f"Scanned {files} PHP file(s) in {args.path}\n")
    if not findings:
        print("No known-bad patterns found.")
        print("Still complete the manual checklist — a clean scan is not proof of safety.")
        return 0

    counts = {}
    current_file = None
    for f in findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
        if f["file"] != current_file:
            current_file = f["file"]
            print(f"\n{current_file}")
        print(f"  [{f['severity'].upper():8}] line {f['line']:>4}  {f['id']}")
        print(f"             {f['message']}")
        if f["code"]:
            print(f"             > {f['code']}")

    summary = ", ".join(f"{counts[s]} {s}" for s in ("critical", "high", "medium", "low") if s in counts)
    print(f"\n{len(findings)} finding(s): {summary}")
    print("Fix each one, or add a `// wpsec:ignore` comment on the line explaining why it is safe.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
