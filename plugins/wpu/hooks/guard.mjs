// PreToolUse guard for WP Ultimate Build.
//
// 1. Secrets never go into files or commands. A bridge key, an Application
//    Password or a DataForSEO login written into a project file or a command
//    line ends up in git, in a transcript, or on a shared drive. Those live in
//    each member's encrypted store (scripts/wpu-secret.ps1) - set by the member
//    in their own terminal, never through Claude.
// 2. A person approves every write to a LIVE site. Dry runs pass silently;
//    the same command with "apply" / "publish" makes Claude Code ask the
//    member, even in auto-accept modes. This is the approval gate the toolkit's
//    rules talk about - enforced here, not left to prose.
//
// Fails open on its own errors (a broken guard must not stop all work), but
// prints why to stderr.
import { readFileSync } from 'node:fs';

let input;
try {
	input = JSON.parse(readFileSync(0, 'utf8'));
} catch {
	process.exit(0);
}

const tool = input.tool_name || '';
const ti = input.tool_input || {};
const text = [ti.content, ti.new_string, ti.command, ...(Array.isArray(ti.edits) ? ti.edits.map((e) => e.new_string) : [])]
	.filter((v) => typeof v === 'string')
	.join('\n');

const decide = (decision, reason) => {
	process.stdout.write(JSON.stringify({ hookSpecificOutput: { hookEventName: 'PreToolUse', permissionDecision: decision, permissionDecisionReason: reason } }));
	process.exit(0);
};

// ---- 1. secrets ------------------------------------------------------------
const SECRET_PATTERNS = [
	[/\bwpu_[A-Za-z0-9]{40}\b/, 'a WPU Bridge connection key'],
	[/\bwpsd_[A-Za-z0-9]{40}\b/, 'a Site Doctor Bridge connection key'],
	[/"appPassword"\s*:\s*"[A-Za-z0-9]{4}( ?[A-Za-z0-9]{4}){5}"/, 'an Application Password'],
	[/"(?:pass|password|adminpass|dataforseo_password)"\s*:\s*"[^"]{6,}"/i, 'a password'],
	[/X-WPU-Key:\s*\S{20,}/i, 'a bridge key in a request header'],
	[/"(?:token|apiToken|cpanel_token|sftp_pass|sftp_keypass|passphrase)"\s*:\s*"[^"]{6,}"/i, 'a hosting password or API token'],
	[/Authorization:\s*cpanel\s+\S+:\S{16,}/i, 'a cPanel API token in a request header'],
	[/\bsshpass\s+-p\s*\S+/i, 'an SSH password on a command line'],
	[/-----BEGIN [A-Z ]*PRIVATE KEY-----/, 'a private key'],
	[/\bWPU_SECRET_[A-Z0-9_]+\b/, 'a stored secret (WPU_SECRET_ variable)'],
	[/\bsecret\s*\(\s*['"]/, 'a call that reads a stored secret'],
];
for (const [re, what] of SECRET_PATTERNS) {
	if (re.test(text)) {
		decide(
			'deny',
			`Blocked: this would put ${what} into a file or command. Secrets live in each member's encrypted store. Ask the member to run, in their own terminal:  powershell -File <plugin>/scripts/wpu-secret.ps1 set <site> key   (or apppassword / adminpass / sftp_pass / cpanel_token / global dataforseo_password). Then reference nothing - the scripts read it themselves.`
		);
	}
}

// Where hosting credentials are SENT is decided by site.json (host) and the pinned known_hosts.
// Changing either quietly would redirect a password or token, so a person confirms it.
const fp = String(ti.file_path || ti.path || '');
if (/(Write|Edit|MultiEdit)/.test(tool) && /sites[\\/][^\\/]+[\\/](site\.json|hosting[\\/]known_hosts)$/i.test(fp)) {
	if (/known_hosts$/i.test(fp) || /"(host|port|url|user|root|wpRoot|keyFile)"\s*:/.test(text) || /"hosting"\s*:/.test(text)) {
		decide('ask', `WP Ultimate Build: this changes where this site's hosting or bridge credentials are sent (${fp}). Approve only if the member gave these details.`);
	}
}

if (/(Bash|PowerShell)/.test(tool) && typeof ti.command === 'string') {
	const cmd = ti.command;

	if (/wpu-secret\.ps1['"]?\s+(get|set)\b/i.test(cmd)) {
		decide(
			'deny',
			'Blocked: secrets are read by the scripts themselves and set by the member in their own terminal (the prompt is hidden input). Do not print or set them through Claude. Tell the member the exact `wpu-secret.ps1 set ...` line to run.'
		);
	}

	// ---- 2. live writes need a person -------------------------------------
	const LIVE_WRITE = [
		[/r(plan|wpphp|speed)\.ps1\b[^\n]*\bapply\b/i, 'applies changes to the live site'],
		[/rseo\.ps1['"]?\s+(push\b[^\n]*\bapply\b|rollback\b)/i, 'writes SEO fields on the live site'],
		[/rposts\.ps1['"]?\s+push\b[^\n]*\bpublish\b/i, 'PUBLISHES a post on the live site'],
		[/rfile\.ps1['"]?\s+put\b/i, 'writes a file into wp-content on the live site'],
		[/rtemplate\.ps1\b/i, 'imports Elementor templates into the live site'],
		[/rmedia\.ps1\b/i, 'uploads files to the live Media Library'],
		[/install-(bridge|plugin-zip)\.mjs\b/i, 'installs a plugin on the live site'],
	];
	// Hosting tools: ASK unless the whole command is one plain read. Matching "apply" was not enough -
	// it can be built at run time ($(echo apply), quotes, line continuations), so the rule is inverted:
	// only an exact, metacharacter-free read form passes without a person.
	if (/(sftp|cpanel)\.py\b/i.test(cmd)) {
		const PY = String.raw`^\s*(?:\$env:WPU_SITE\s*=\s*['"]?[a-z0-9_-]+['"]?\s*;\s*|WPU_SITE=[a-z0-9_-]+\s+)?(?:python3?|py)(?:\.exe)?\s+(?:-3\s+)?["']?[^\s"';&|<>$\`]*tools[\\/]hosting[\\/]`;
		const ARG = String.raw`(?:\s+(?:[\w./*@:=+,-]+|"[\w./* @:=+,-]*"))`;
		const READ_SFTP = new RegExp(PY + String.raw`sftp\.py["']?\s+(?:check|ls|stat|tail|find|logs|get|help)` + ARG + `{0,3}\\s*$`, 'i');
		const READ_CP = new RegExp(PY + String.raw`cpanel\.py["']?\s+(?:check|php|ls|tail|get|logs|backups|cron|help)` + ARG + `{0,3}\\s*$`, 'i');
		// exec / wp read forms: one double-quoted argument of plain characters, nothing after it.
		const READ_SH = new RegExp(PY + String.raw`sftp\.py["']?\s+(?:exec|wp)\s+"[\w ./*:=,@+|-]*"\s*$`, 'i');
		// The PowerShell site prefix ($env:WPU_SITE = "slug"; ...) is the one allowed use of $ and ;.
		const body = cmd.replace(/^\s*\$env:WPU_SITE\s*=\s*['"]?[a-z0-9_-]+['"]?\s*;\s*/i, '');
		const plain = !/apply/i.test(body) && !/[\r\n;&<>$`\\]/.test(body.replace(/\\(?=[\w.-])/g, '/'));
		if (!(plain && (READ_SFTP.test(cmd) || READ_CP.test(cmd) || READ_SH.test(cmd)))) {
			const what = /\btrust\b/i.test(cmd)
				? "pins this server's SSH identity - compare the fingerprint it prints with the host's, if they publish one"
				: "may change files or settings on the client's HOSTING (writes keep a backup; read the dry run first)";
			decide('ask', `WP Ultimate Build: this hosting command ${what}.`);
		}
	}

	// Raw ssh/scp/sftp/rsync skips the backups, the root confinement and the command denylist that
	// tools/hosting/sftp.py enforces - with or without user@host (an ssh config alias needs no @).
	if (/(^|[;&|(\n]\s*|\s)(ssh|scp|sftp|rsync|sshpass|plink|pscp)(\.exe)?\s+\S/i.test(cmd) && !/^\s*[^;&|]*tools[\\/]hosting[\\/](sftp|cpanel)\.py\b[^;&|]*$/i.test(cmd)) {
		decide('ask', 'WP Ultimate Build: this is a raw SSH/SFTP command to a server. Prefer python tools/hosting/sftp.py, which keeps backups, stays inside the WordPress root and blocks destructive commands. Approve only if the tool cannot do this.');
	}

	for (const [re, what] of LIVE_WRITE) {
		if (re.test(cmd)) {
			const site = process.env.WPU_SITE || (cmd.match(/WPU_SITE\s*=\s*['"]?([a-z0-9_-]+)/i) || [])[1] || '(see WPU_SITE)';
			decide('ask', `WP Ultimate Build: this command ${what} (site: ${site}). Approve only if you have read the dry run.`);
		}
	}
}

process.exit(0);
