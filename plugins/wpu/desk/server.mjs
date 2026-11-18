#!/usr/bin/env node
// WPU Desk - a local dashboard for WP Ultimate Build.
//
// It runs the official Claude Code (unmodified, signed in with YOUR own Claude account) with the
// wpu plugin, one job at a time per site, and shows everything in the browser: live progress,
// approvals for live-site changes, replies, results and files. It never sees or stores your Claude
// login, and it only listens on 127.0.0.1.
//
//   node desk/server.mjs [workspace-folder]      (or scripts/wpu-desk.ps1 on Windows)
//
// Env: WPU_WORKSPACE (folder with sites/), WPU_DESK_PORT (default 4977), WPU_DESK_NO_OPEN=1.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import os from 'node:os';
import { spawn, spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { TASKS, NEW_SITE, preface } from './tasks.mjs';

const DESK_DIR = path.dirname(fileURLToPath(import.meta.url));
const PLUGIN_ROOT = path.resolve(DESK_DIR, '..');
const UI_DIR = path.join(DESK_DIR, 'ui');
const WORKSPACE = path.resolve(process.env.WPU_WORKSPACE || process.argv[2] || process.cwd());
const SITES = path.join(WORKSPACE, 'sites');
const DATA = path.join(WORKSPACE, '.desk');
const JOBS_DIR = path.join(DATA, 'jobs');
const WIN = process.platform === 'win32';
const TOKEN = crypto.randomBytes(24).toString('hex');
let PORT = Number(process.env.WPU_DESK_PORT || 4977);

const SLUG = /^[a-z0-9][a-z0-9-]{0,40}$/;
const SECRET_NAMES = ['key', 'apppassword', 'adminpass', 'sftp_pass', 'sftp_keypass', 'cpanel_token', 'dataforseo_login', 'dataforseo_password', 'pagespeed_key'];
const MODELS = ['', 'sonnet', 'opus', 'haiku'];
const SESSION_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
// Tools Claude may use without asking. Live-site writes still stop for approval: the plugin's guard
// hook marks them "ask", and those questions come to this Desk as approval cards. The file-editing
// tools are NOT listed: each edit comes to the Desk, which allows it unless it targets the toolkit,
// the Desk's own data, the secret store or Claude's settings (see fileGate).
const ALLOWED = ['Bash', 'PowerShell', 'Read', 'Glob', 'Grep', 'WebFetch', 'WebSearch', 'Skill', 'Task', 'Agent', 'TodoWrite', 'TaskCreate', 'TaskUpdate', 'TaskList', 'TaskGet', 'ToolSearch', 'BashOutput', 'KillShell'].join(',');
const FILE_TOOLS = ['Write', 'Edit', 'MultiEdit', 'NotebookEdit'];

fs.mkdirSync(SITES, { recursive: true });
fs.mkdirSync(JOBS_DIR, { recursive: true, mode: 0o700 });
if (!WIN) { try { fs.chmodSync(DATA, 0o700); fs.chmodSync(JOBS_DIR, 0o700); } catch { /* not ours */ } }
const PRIVATE = { mode: 0o600 };

// --------------------------------------------------------------------------- Claude Code

// Every program is started by its absolute path with an argument list - never through a shell and
// never by a bare name - so nothing in the workspace folder can stand in for it, and no value can
// break out into a command line.
const SYSROOT = process.env.SystemRoot || 'C:\\Windows';
const SYS = WIN ? {
	powershell: path.join(SYSROOT, 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe'),
	explorer: path.join(SYSROOT, 'explorer.exe'),
	taskkill: path.join(SYSROOT, 'System32', 'taskkill.exe'),
	cmd: path.join(SYSROOT, 'System32', 'cmd.exe'),
} : {};
const CHILD_ENV = WIN ? { NoDefaultCurrentDirectoryInExePath: '1' } : {};

function onPath(names) {
	const dirs = String(process.env.PATH || '').split(path.delimiter).filter((d) => d && path.isAbsolute(d));
	if (WIN && process.env.USERPROFILE) dirs.push(path.join(process.env.USERPROFILE, '.local', 'bin'));
	if (!WIN && process.env.HOME) dirs.push(path.join(process.env.HOME, '.local', 'bin'), path.join(process.env.HOME, '.claude', 'local'));
	for (const d of dirs) for (const n of names) {
		const f = path.join(d, n);
		try { if (fs.statSync(f).isFile()) return f; } catch { /* not here */ }
	}
	return null;
}
// Returns [program, leadingArgs] for Claude Code, or null.
function findClaude() {
	if (!WIN) { const f = onPath(['claude']); return f ? [f, []] : null; }
	const exe = onPath(['claude.exe']);
	if (exe) return [exe, []];
	// npm install: claude.cmd is only a shim. Run the package's own entry point directly instead.
	const shim = onPath(['claude.cmd']);
	if (!shim) return null;
	const pkgDir = path.join(path.dirname(shim), 'node_modules', '@anthropic-ai', 'claude-code');
	const pkg = readJson(path.join(pkgDir, 'package.json'));
	const bin = pkg && (typeof pkg.bin === 'string' ? pkg.bin : pkg.bin?.claude);
	if (!bin) return null;
	const target = path.resolve(pkgDir, bin);
	if (!target.startsWith(pkgDir + path.sep) || !fs.existsSync(target)) return null;
	return /\.(c|m)?js$/i.test(target) ? [process.execPath, [target]] : [target, []];
}
let CLAUDE = null;
function runClaudeSync(args, opts = {}) {
	if (!CLAUDE) return { status: -1, stdout: '' };
	return spawnSync(CLAUDE[0], [...CLAUDE[1], ...args], { encoding: 'utf8', timeout: 30000, windowsHide: true, env: { ...process.env, ...CHILD_ENV }, ...opts });
}

const claude = { found: false, version: '', pluginInstalled: false };
function detectClaude() {
	CLAUDE = findClaude();
	const v = runClaudeSync(['--version']);
	claude.found = v.status === 0;
	claude.version = claude.found ? String(v.stdout).trim() : '';
	if (claude.found) {
		const l = runClaudeSync(['plugin', 'list']);
		claude.pluginInstalled = /\bwpu@/i.test(String(l.stdout || ''));
	}
}
// --------------------------------------------------------------------------- jobs

const jobs = new Map();        // id -> job
const approvals = new Map();   // id -> pending approval (with the helper's held response)

function publicJob(j) {
	const { proc, clients, events, helper, ...rest } = j;
	return rest;
}
function saveJob(j) {
	fs.writeFileSync(path.join(JOBS_DIR, `${j.id}.json`), JSON.stringify(publicJob(j), null, 2), PRIVATE);
}
function loadJobs() {
	for (const f of fs.readdirSync(JOBS_DIR).filter((x) => x.endsWith('.json') && !x.endsWith('.mcp.json'))) {
		try {
			const j = JSON.parse(fs.readFileSync(path.join(JOBS_DIR, f), 'utf8'));
			if (!/^[0-9]{14}-[0-9a-f]{6}$/.test(String(j.id)) || `${j.id}.json` !== f) continue;
			// These files sit where a job's own Claude could edit them: re-check every value used later.
			if (!SESSION_ID.test(String(j.sessionId || ''))) j.sessionId = null;
			if (!MODELS.includes(j.model)) j.model = '';
			if (j.site && !SLUG.test(String(j.site))) j.site = null;
			if (['running', 'needs-approval'].includes(j.status)) j.status = 'stopped';
			j.clients = new Set(); j.events = null; j.proc = null;
			jobs.set(j.id, j);
		} catch { /* skip a broken record */ }
	}
}

function eventsOf(j) {
	if (j.events) return j.events;
	const file = path.join(JOBS_DIR, `${j.id}.jsonl`);
	j.events = fs.existsSync(file) ? fs.readFileSync(file, 'utf8').split('\n').filter(Boolean).map((l) => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean) : [];
	return j.events;
}
function emit(j, ev) {
	ev.at = new Date().toISOString();
	eventsOf(j).push(ev);
	if (j.events.length > 6000) j.events.splice(0, j.events.length - 6000);
	fs.appendFileSync(path.join(JOBS_DIR, `${j.id}.jsonl`), JSON.stringify(ev) + '\n', PRIVATE);
	for (const c of j.clients) c.write(`data: ${JSON.stringify(ev)}\n\n`);
}
function setStatus(j, s) {
	j.status = s; j.updatedAt = new Date().toISOString(); saveJob(j);
	emit(j, { k: 'status', status: s });
}

const REDACT = [/\bwp(?:u|sd)_[A-Za-z0-9]{20,}\b/g, /(Authorization:\s*cpanel\s+\S+:)\S+/gi, /(X-WPU-Key:\s*)\S+/gi, /-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----/g];
function redact(s) {
	let t = String(s ?? '');
	for (const r of REDACT) t = t.replace(r, (m, p1) => (typeof p1 === 'string' && p1 ? `${p1}[hidden]` : '[hidden]'));
	return t;
}
function trunc(s, n = 4000) { s = String(s ?? ''); return s.length > n ? s.slice(0, n) + `\n... (${s.length - n} more characters)` : s; }

function summarize(name, input = {}) {
	const pick = input.command || input.file_path || input.path || input.skill || input.url || input.query || input.pattern || input.description || input.prompt;
	return redact(trunc(pick ? String(pick) : JSON.stringify(input), 600));
}

function handleClaudeEvent(j, e) {
	if (e.type === 'system' && e.subtype === 'init') {
		if (SESSION_ID.test(String(e.session_id || ''))) j.sessionId = e.session_id;
		emit(j, { k: 'info', text: `Claude Code started${e.model ? ` (${e.model})` : ''}` });
		saveJob(j);
	} else if (e.type === 'assistant' && e.message?.content) {
		for (const c of e.message.content) {
			if (c.type === 'text' && c.text?.trim()) emit(j, { k: 'text', text: redact(c.text) });
			else if (c.type === 'tool_use') emit(j, { k: 'tool', id: c.id, name: c.name, summary: summarize(c.name, c.input) });
		}
	} else if (e.type === 'user' && Array.isArray(e.message?.content)) {
		for (const c of e.message.content) {
			if (c.type !== 'tool_result') continue;
			const body = Array.isArray(c.content) ? c.content.map((x) => x.text || (x.type === 'image' ? '[image]' : '')).join('\n') : c.content;
			emit(j, { k: 'result', id: c.tool_use_id, error: !!c.is_error, text: redact(trunc(body, 3000)) });
		}
	} else if (e.type === 'result') {
		if (SESSION_ID.test(String(e.session_id || ''))) j.sessionId = e.session_id;
		if (typeof e.total_cost_usd === 'number') j.usage = (j.usage || 0) + e.total_cost_usd;
		j.lastResult = redact(trunc(e.result || '', 4000));
		j.endedWithQuestion = /\?\s*$/.test((e.result || '').trim());
		emit(j, { k: 'done', ok: !e.is_error, text: j.lastResult, turns: e.num_turns, seconds: Math.round((e.duration_ms || 0) / 1000) });
	}
}

function startRun(j, text, resume) {
	if (!CLAUDE) detectClaude();
	if (!CLAUDE) { emit(j, { k: 'error', text: 'Claude Code was not found. Install it and sign in once, then start the job again.' }); setStatus(j, 'failed'); return; }
	if (resume && !SESSION_ID.test(String(j.sessionId || ''))) { emit(j, { k: 'error', text: 'This job cannot be continued. Start a new one.' }); setStatus(j, 'failed'); return; }
	if (!MODELS.includes(j.model)) j.model = '';
	// A fresh helper key for every run: one job's Claude can't raise approval cards for another job.
	j.helper = crypto.randomBytes(24).toString('hex');
	const mcpFile = path.join(JOBS_DIR, `${j.id}.mcp.json`);
	fs.writeFileSync(mcpFile, JSON.stringify({ mcpServers: { wpu_desk: {
		command: process.execPath,
		args: [path.join(DESK_DIR, 'approval-mcp.mjs')],
		env: { DESK_URL: `http://127.0.0.1:${PORT}`, DESK_HELPER_TOKEN: j.helper, DESK_JOB: j.id },
	} } }), PRIVATE);
	const args = ['-p', '--output-format', 'stream-json', '--verbose', '--mcp-config', mcpFile,
		'--permission-prompt-tool', 'mcp__wpu_desk__approve', '--allowedTools', ALLOWED, '--disallowedTools', 'AskUserQuestion'];
	if (resume) args.push('--resume', j.sessionId);
	if (!claude.pluginInstalled) args.push('--plugin-dir', PLUGIN_ROOT);
	if (j.model) args.push('--model', j.model);
	const env = { ...process.env, ...CHILD_ENV, WPU_SITE: j.site || '', WPU_WORKSPACE: WORKSPACE, MCP_TOOL_TIMEOUT: '86400000' };
	// On Windows secrets live in the encrypted store, so none need to sit in Claude's environment.
	if (WIN) for (const k of Object.keys(env)) if (/^WPU_SECRET_/i.test(k)) delete env[k];
	const proc = spawn(CLAUDE[0], [...CLAUDE[1], ...args], { cwd: WORKSPACE, env, windowsHide: true, detached: !WIN });
	j.proc = proc; j.cancelled = false;
	setStatus(j, 'running');
	emit(j, { k: 'you', text: text });
	proc.stdin.end((resume ? '' : preface(j.site)) + text);
	let buf = '';
	proc.stdout.on('data', (d) => {
		buf += d;
		let i;
		while ((i = buf.indexOf('\n')) >= 0) {
			const line = buf.slice(0, i).trim(); buf = buf.slice(i + 1);
			if (!line) continue;
			try { handleClaudeEvent(j, JSON.parse(line)); } catch { emit(j, { k: 'log', text: redact(trunc(line, 500)) }); }
		}
	});
	let errBuf = '';
	proc.stderr.on('data', (d) => { errBuf = (errBuf + d).slice(-4000); });
	proc.on('error', (err) => emit(j, { k: 'error', text: `Could not start Claude Code: ${err.message}` }));
	proc.on('close', (code) => {
		try { fs.unlinkSync(mcpFile); } catch { /* already gone */ }
		for (const [id, a] of approvals) if (a.job === j.id) decide(id, 'deny', 'The job stopped.');
		j.proc = null;
		if (j.cancelled) setStatus(j, 'cancelled');
		else if (code === 0) setStatus(j, j.endedWithQuestion ? 'needs-reply' : 'done');
		else {
			if (errBuf.trim()) emit(j, { k: 'error', text: redact(trunc(errBuf.trim(), 1500)) });
			if (/log ?in|login|authenticat/i.test(errBuf)) emit(j, { k: 'error', text: 'Claude Code is not signed in. Open a terminal once, run "claude", and sign in with your Claude account. Then try again.' });
			setStatus(j, 'failed');
		}
	});
}

function newJob({ site, task, title, model }) {
	const id = new Date().toISOString().replace(/[-:T.Z]/g, '').slice(0, 14) + '-' + crypto.randomBytes(3).toString('hex');
	const j = { id, site, task, title, model, status: 'new', createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(), sessionId: null, usage: 0, clients: new Set(), events: [], proc: null };
	jobs.set(id, j);
	saveJob(j);
	return j;
}

function cancelJob(j) {
	if (!j.proc) return;
	j.cancelled = true;
	try {
		if (WIN) spawnSync(SYS.taskkill, ['/PID', String(j.proc.pid), '/T', '/F'], { windowsHide: true });
		else {
			// Claude Code runs commands in their own process groups, so collect the whole tree first.
			const kids = new Map();
			for (const line of String(spawnSync('ps', ['-A', '-o', 'pid=,ppid='], { encoding: 'utf8' }).stdout || '').split('\n')) {
				const [pid, ppid] = line.trim().split(/\s+/).map(Number);
				if (pid && ppid) kids.set(ppid, [...(kids.get(ppid) || []), pid]);
			}
			const tree = []; const stack = [j.proc.pid];
			while (stack.length) { const p = stack.pop(); tree.push(p); stack.push(...(kids.get(p) || [])); }
			for (const p of tree.reverse()) { try { process.kill(p, 'SIGTERM'); } catch { /* already gone */ } }
		}
	} catch { try { j.proc.kill(); } catch { /* gone */ } }
}

// --------------------------------------------------------------------------- approvals

function classify(toolName, input, site) {
	// Ask the plugin's own guard why this call needs approval, so the card can say it in plain words.
	try {
		const r = spawnSync(process.execPath, [path.join(PLUGIN_ROOT, 'hooks', 'guard.mjs')], { input: JSON.stringify({ tool_name: toolName, tool_input: input }), encoding: 'utf8', timeout: 10000, env: { ...process.env, ...CHILD_ENV, WPU_SITE: site || '', WPU_WORKSPACE: WORKSPACE } });
		const o = JSON.parse(r.stdout || '{}').hookSpecificOutput || {};
		// "none": the guard has no objection. Callers decide what that means for their tool.
		return { level: o.permissionDecision || 'none', reason: o.permissionDecisionReason || '' };
	} catch { return { level: 'ask', reason: '' }; }
}

// File edits: allowed, except inside the toolkit, the Desk's own data, the secret store or Claude's
// settings. Those would let a job change its own safety rules, so they are refused outright.
const lc = (s) => (WIN ? s.toLowerCase() : s);
function realish(p) {
	// realpath of the nearest folder that exists, plus the rest: catches links on the way.
	let cur = path.resolve(WORKSPACE, p); const rest = [];
	for (let i = 0; i < 64; i++) {
		try { return path.join(fs.realpathSync(cur), ...rest.reverse()); } catch { /* go up */ }
		const up = path.dirname(cur); if (up === cur) break;
		rest.push(path.basename(cur)); cur = up;
	}
	return path.resolve(WORKSPACE, p);
}
const PROTECTED = [PLUGIN_ROOT, DATA, process.env.APPDATA && path.join(process.env.APPDATA, 'WPU'), path.join(os.homedir(), '.claude'), path.join(WORKSPACE, '.claude')]
	.filter(Boolean).map((d) => { try { return fs.realpathSync(d); } catch { return path.resolve(d); } });

function fileGate(input) {
	const targets = [input?.file_path, input?.notebook_path, input?.path].filter((x) => typeof x === 'string' && x);
	if (!targets.length) return 'No file path given.';
	for (const t of targets) {
		const r = lc(realish(t));
		const hit = PROTECTED.find((d) => r === lc(d) || r.startsWith(lc(d) + path.sep));
		if (hit) return `Desk jobs may not change files in ${hit} (the toolkit, the Desk's data, the secret store or Claude's settings). Change the shared plugin through /wpu:learn in Claude Code instead.`;
	}
	return '';
}

function decide(id, decision, message) {
	const a = approvals.get(id);
	if (!a) return false;
	approvals.delete(id);
	const body = decision === 'allow' ? { behavior: 'allow' } : { behavior: 'deny', message: message || 'Rejected by the member in WPU Desk.' };
	try { a.res.writeHead(200, { 'content-type': 'application/json' }); a.res.end(JSON.stringify(body)); } catch { /* helper gone */ }
	const j = jobs.get(a.job);
	if (j) {
		emit(j, { k: 'decision', id, decision, note: message || '' });
		if (j.proc && ![...approvals.values()].some((x) => x.job === j.id)) setStatus(j, 'running');
	}
	return true;
}

// --------------------------------------------------------------------------- sites and files

function readJson(p) { try { return JSON.parse(fs.readFileSync(p, 'utf8').replace(/^﻿/, '')); } catch { return null; } }
function scrub(o) {
	if (Array.isArray(o)) return o.map(scrub);
	if (o && typeof o === 'object') {
		const out = {};
		for (const [k, v] of Object.entries(o)) out[k] = /pass|token|secret|(^|_)key$|apppassword/i.test(k) && typeof v === 'string' && v ? '[hidden]' : scrub(v);
		return out;
	}
	return o;
}
function listSites() {
	if (!fs.existsSync(SITES)) return [];
	return fs.readdirSync(SITES, { withFileTypes: true }).filter((d) => d.isDirectory() && SLUG.test(d.name)).map((d) => {
		const cfg = readJson(path.join(SITES, d.name, 'site.json')) || {};
		const recent = [...jobs.values()].filter((j) => j.site === d.name).sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))[0];
		return { slug: d.name, name: cfg.name || cfg.siteName || d.name, url: cfg.baseUrl || cfg.url || cfg.remote?.url || '', seoPlugin: cfg.seoPlugin || '', lastJob: recent ? { id: recent.id, title: recent.title, status: recent.status, updatedAt: recent.updatedAt } : null };
	}).sort((a, b) => a.slug.localeCompare(b.slug));
}
function siteDir(slug) {
	if (!SLUG.test(slug || '')) return null;
	const d = path.join(SITES, slug);
	return fs.existsSync(d) ? d : null;
}
const BLOCKED_FILES = /(^|\/)(hosting\/(backups|downloads)\/|.*wp-config[^/]*$|.*\.(php|sql|gz|zip)$|known_hosts$)/i;
const relOf = (base, full) => path.relative(base, full).split(path.sep).join('/');
function listFiles(dir) {
	const out = [];
	const walk = (d, rel, depth) => {
		if (depth > 5 || out.length > 800) return;
		for (const e of fs.readdirSync(d, { withFileTypes: true })) {
			if (e.name.startsWith('.') || e.isSymbolicLink()) continue;
			const r = rel ? `${rel}/${e.name}` : e.name;
			if (e.isDirectory()) walk(path.join(d, e.name), r, depth + 1);
			else {
				const st = fs.statSync(path.join(d, e.name));
				out.push({ path: r, size: st.size, mtime: st.mtime.toISOString(), viewable: !BLOCKED_FILES.test(r) });
			}
		}
	};
	walk(dir, '', 0);
	return out.sort((a, b) => b.mtime.localeCompare(a.mtime));
}
const TYPES = { '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.gif': 'image/gif',
	'.json': 'text/plain; charset=utf-8', '.md': 'text/plain; charset=utf-8', '.txt': 'text/plain; charset=utf-8', '.log': 'text/plain; charset=utf-8',
	'.csv': 'text/plain; charset=utf-8', '.html': 'text/plain; charset=utf-8', '.jsonl': 'text/plain; charset=utf-8', '.yml': 'text/plain; charset=utf-8' };

function secretState(scope) {
	const out = {};
	for (const n of SECRET_NAMES) {
		const envName = `WPU_SECRET_${scope.toUpperCase().replace(/-/g, '_')}_${n.toUpperCase()}`;
		if (process.env[envName]) { out[n] = true; continue; }
		if (WIN) {
			const r = spawnSync(SYS.powershell, ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', path.join(PLUGIN_ROOT, 'scripts', 'wpu-secret.ps1'), 'has', scope, n], { encoding: 'utf8', timeout: 15000, windowsHide: true, env: { ...process.env, ...CHILD_ENV } });
			out[n] = String(r.stdout || '').trim() === 'yes';
		} else out[n] = false;
	}
	return out;
}
function saveSecret(scope, name, value) {
	return new Promise((resolve) => {
		if (!WIN) return resolve({ ok: false, error: `The encrypted store needs Windows. Here, set the environment variable WPU_SECRET_${scope.toUpperCase().replace(/-/g, '_')}_${name.toUpperCase()} before starting the Desk.` });
		const p = spawn(SYS.powershell, ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', path.join(PLUGIN_ROOT, 'scripts', 'wpu-secret.ps1'), 'set-stdin', scope, name], { windowsHide: true, env: { ...process.env, ...CHILD_ENV } });
		let out = '';
		p.stdout.on('data', (d) => { out += d; });
		p.stderr.on('data', (d) => { out += d; });
		p.on('close', (code) => resolve(code === 0 ? { ok: true } : { ok: false, error: redact(out.replace(value, '[hidden]')).slice(0, 400) || 'Saving failed.' }));
		p.stdin.end(value + '\n');
	});
}

// --------------------------------------------------------------------------- HTTP

// One-time sign-in links. The browser is opened with a short-lived single-use code, never with the
// session key itself, so the key does not appear on any command line or in the browser history.
const nonces = new Map(); // code -> expiry (ms)
function loginLink() {
	const n = crypto.randomBytes(18).toString('hex');
	for (const [k, exp] of nonces) if (exp < Date.now()) nonces.delete(k);
	nonces.set(n, Date.now() + 10 * 60 * 1000);
	return `http://127.0.0.1:${PORT}/#n=${n}`;
}
function openBrowser(url) {
	if (process.env.WPU_DESK_NO_OPEN) return;
	try {
		// The URL is only digits, letters, ':', '/', '.' and '#', so it is safe on the command line.
		if (!/^http:\/\/127\.0\.0\.1:\d+\/#n=[0-9a-f]+$/.test(url)) return;
		if (WIN) spawn(SYS.cmd, ['/c', 'start', '""', url], { detached: true, stdio: 'ignore', windowsHide: true, env: { ...process.env, ...CHILD_ENV } }).unref();
		else { const o = process.platform === 'darwin' ? '/usr/bin/open' : onPath(['xdg-open']); if (o) spawn(o, [url], { detached: true, stdio: 'ignore' }).unref(); }
	} catch { /* open it by hand */ }
}

const safeEq = (a, b) => { const x = Buffer.from(String(a || '')), y = Buffer.from(String(b || '')); return x.length === y.length && crypto.timingSafeEqual(x, y); };
function send(res, code, body, headers = {}) {
	res.writeHead(code, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', 'x-content-type-options': 'nosniff', ...headers });
	res.end(typeof body === 'string' ? body : JSON.stringify(body));
}
function readBody(req, limit = 2 * 1024 * 1024) {
	return new Promise((resolve, reject) => {
		let n = 0; const chunks = [];
		req.on('data', (c) => { n += c.length; if (n > limit) { reject(new Error('too large')); req.destroy(); } else chunks.push(c); });
		req.on('end', () => { try { resolve(chunks.length ? JSON.parse(Buffer.concat(chunks).toString('utf8')) : {}); } catch { reject(new Error('bad json')); } });
	});
}
const STATIC = { '/': ['index.html', 'text/html; charset=utf-8'], '/app.js': ['app.js', 'text/javascript; charset=utf-8'], '/app.css': ['app.css', 'text/css; charset=utf-8'] };
const CSP = "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'";

const server = http.createServer(async (req, res) => {
	try {
		// Only this machine, only this port: blocks other sites (DNS rebinding) from talking to the Desk.
		const host = String(req.headers.host || '');
		if (host !== `127.0.0.1:${PORT}` && host !== `localhost:${PORT}`) return send(res, 421, { error: 'wrong host' });
		const u = new URL(req.url, `http://${host}`);
		const p = u.pathname;

		if (req.method === 'GET' && STATIC[p]) {
			const [f, type] = STATIC[p];
			res.writeHead(200, { 'content-type': type, 'cache-control': 'no-store', 'x-content-type-options': 'nosniff', 'content-security-policy': CSP, 'referrer-policy': 'no-referrer', 'x-frame-options': 'DENY' });
			return res.end(fs.readFileSync(path.join(UI_DIR, f)));
		}

		// The approval helper (started by Claude Code for a job) - its own token, never the browser's.
		if (p === '/api/internal/approval' && req.method === 'POST') {
			const b = await readBody(req);
			const j = jobs.get(String(b.job || ''));
			if (!j || !j.proc || !j.helper || !safeEq(req.headers['x-desk-helper'], j.helper)) return send(res, 403, { error: 'forbidden' });
			const id = crypto.randomBytes(6).toString('hex');
			const tool = String(b.tool_name || '');
			const c = classify(tool, b.input || {}, j.site);
			if (c.level === 'deny') return send(res, 200, { behavior: 'deny', message: c.reason || 'Blocked by the WPU guard.' });
			if (FILE_TOOLS.includes(tool)) {
				const why = fileGate(b.input);
				if (why) { emit(j, { k: 'info', text: `Refused a file change. ${why}` }); return send(res, 200, { behavior: 'deny', message: why }); }
				if (c.level !== 'ask') return send(res, 200, { behavior: 'allow', updatedInput: b.input });
			}
			const full = JSON.stringify(b.input || {}, null, 2);
			// Never ask the member to approve something they can't see in full.
			if (full.length > 20000) return send(res, 200, { behavior: 'deny', message: 'This call is too long to review in WPU Desk. Split it into smaller steps, or write the script to a file first and run that file.' });
			const a = { id, job: j.id, site: j.site, tool, summary: summarize(tool, b.input), detail: redact(full), reason: c.reason, createdAt: new Date().toISOString(), res };
			approvals.set(id, a);
			// If the helper goes away (Claude Code stopped) before the member decides, drop the card.
			res.on('close', () => {
				if (approvals.get(id) === a && !res.writableEnded) { approvals.delete(id); emit(j, { k: 'decision', id, decision: 'expired', note: 'Claude Code stopped waiting.' }); }
			});
			emit(j, { k: 'approval', id, tool: a.tool, summary: a.summary, detail: a.detail, reason: a.reason });
			setStatus(j, 'needs-approval');
			return; // held open until the member decides
		}

		if (!p.startsWith('/api/')) return send(res, 404, { error: 'not found' });
		if (p === '/api/login' && req.method === 'POST') {
			if (!String(req.headers['content-type'] || '').startsWith('application/json')) return send(res, 415, { error: 'json only' });
			const origin = req.headers.origin;
			if (origin && origin !== `http://127.0.0.1:${PORT}` && origin !== `http://localhost:${PORT}`) return send(res, 403, { error: 'bad origin' });
			const b = await readBody(req, 4096);
			const n = String(b.code || '');
			const exp = nonces.get(n);
			if (!/^[0-9a-f]{36}$/.test(n) || !exp || exp < Date.now()) return send(res, 401, { error: 'This sign-in link was already used or has expired. Press Enter in the WPU Desk window for a new one.' });
			nonces.delete(n);
			return send(res, 200, { token: TOKEN });
		}
		const tok = req.headers['x-desk-token'] || ((p.endsWith('/stream') || p === '/api/file') ? u.searchParams.get('t') : '');
		if (!safeEq(tok, TOKEN)) return send(res, 401, { error: 'Press Enter in the WPU Desk window to get a new sign-in link.' });
		if (req.method === 'POST') {
			if (!String(req.headers['content-type'] || '').startsWith('application/json')) return send(res, 415, { error: 'json only' });
			const origin = req.headers.origin;
			if (origin && origin !== `http://127.0.0.1:${PORT}` && origin !== `http://localhost:${PORT}`) return send(res, 403, { error: 'bad origin' });
		}

		if (req.method === 'GET' && p === '/api/state') {
			const list = [...jobs.values()].sort((a, b) => b.updatedAt.localeCompare(a.updatedAt)).slice(0, 60).map(publicJob);
			const pend = [...approvals.values()].map(({ res: _r, ...a }) => a);
			return send(res, 200, { workspace: WORKSPACE, pluginRoot: PLUGIN_ROOT, windows: WIN, claude, sites: listSites(), jobs: list, approvals: pend, tasks: TASKS.map(({ prompt, ...t }) => t), newSite: { fields: NEW_SITE.fields }, models: MODELS });
		}
		if (req.method === 'POST' && p === '/api/claude/recheck') { detectClaude(); return send(res, 200, { claude }); }

		let m;
		if (req.method === 'GET' && (m = p.match(/^\/api\/site\/([a-z0-9-]+)$/))) {
			const d = siteDir(m[1]); if (!d) return send(res, 404, { error: 'no such site' });
			let notes = '';
			try { notes = fs.readFileSync(path.join(d, 'SITE-NOTES.md'), 'utf8').slice(0, 200000); } catch { /* none */ }
			let actions = [];
			try { actions = fs.readFileSync(path.join(d, 'hosting', 'actions.log'), 'utf8').trim().split('\n').slice(-30).reverse(); } catch { /* none */ }
			return send(res, 200, { slug: m[1], config: scrub(readJson(path.join(d, 'site.json')) || {}), notes, files: listFiles(d), actions: actions.map(redact), jobs: [...jobs.values()].filter((j) => j.site === m[1]).sort((a, b) => b.updatedAt.localeCompare(a.updatedAt)).map(publicJob) });
		}
		if (req.method === 'GET' && p === '/api/file') {
			const d = siteDir(u.searchParams.get('site')); const rel = String(u.searchParams.get('path') || '');
			if (!d || !rel || rel.includes('\0')) return send(res, 403, { error: 'not viewable here' });
			const full = path.resolve(d, rel);
			let real; try { real = fs.realpathSync(full); } catch { return send(res, 404, { error: 'not found' }); }
			const realD = fs.realpathSync(d);
			if (!real.startsWith(realD + path.sep)) return send(res, 403, { error: 'outside the site folder' });
			// Check the block list on the real, normalised path - not on what the browser typed.
			const realRel = relOf(realD, real);
			if (BLOCKED_FILES.test(realRel) || realRel.split('/').some((x) => x.startsWith('.'))) return send(res, 403, { error: 'not viewable here' });
			const type = TYPES[path.extname(real).toLowerCase()];
			if (!type) return send(res, 403, { error: 'file type not shown in the Desk' });
			res.writeHead(200, { 'content-type': type, 'cache-control': 'no-store', 'x-content-type-options': 'nosniff', 'referrer-policy': 'no-referrer', 'content-security-policy': "sandbox; default-src 'none'; img-src 'self'" });
			return fs.createReadStream(real).pipe(res);
		}
		if (req.method === 'GET' && (m = p.match(/^\/api\/secrets\/([a-z0-9-]+)$/))) {
			if (m[1] !== 'global' && !SLUG.test(m[1])) return send(res, 400, { error: 'bad scope' });
			return send(res, 200, { scope: m[1], windows: WIN, saved: secretState(m[1]) });
		}
		if (req.method === 'POST' && p === '/api/secrets') {
			const b = await readBody(req);
			const scope = String(b.scope || ''), name = String(b.name || ''), value = String(b.value || '');
			if ((scope !== 'global' && !SLUG.test(scope)) || !SECRET_NAMES.includes(name)) return send(res, 400, { error: 'Unknown secret name.' });
			if (!value || value.length > 4000 || /[\r\n]/.test(value)) return send(res, 400, { error: 'Enter a single-line value.' });
			const r = await saveSecret(scope, name, value);
			return send(res, r.ok ? 200 : 400, r);
		}
		if (req.method === 'POST' && p === '/api/jobs') {
			const b = await readBody(req);
			const model = MODELS.includes(b.model) ? b.model : '';
			const fields = Object.fromEntries(Object.entries(b.fields || {}).map(([k, v]) => [k, String(v ?? '').slice(0, 20000)]));
			if (b.task === 'new-site') {
				const slug = String(fields.slug || '').toLowerCase();
				if (!SLUG.test(slug)) return send(res, 400, { error: 'Short name: lowercase letters, numbers and dashes only.' });
				if (!/^https?:\/\/[^\s]+$/i.test(fields.url || '')) return send(res, 400, { error: 'Enter the full site URL, starting with https://' });
				if ([...jobs.values()].some((x) => x.site === slug && x.proc)) return send(res, 409, { error: 'A job is already running for this site.' });
				const j = newJob({ site: slug, task: 'new-site', title: `New site: ${slug}`, model });
				startRun(j, NEW_SITE.prompt({ ...fields, slug }), false);
				return send(res, 200, { job: publicJob(j) });
			}
			const t = TASKS.find((x) => x.id === b.task);
			if (!t) return send(res, 400, { error: 'Unknown task.' });
			const site = String(b.site || '');
			if (!siteDir(site)) return send(res, 400, { error: 'Pick a site first.' });
			if ([...jobs.values()].some((x) => x.site === site && x.proc)) return send(res, 409, { error: 'A job is already running for this site. Open it from the list, or cancel it first.' });
			const text = t.prompt(fields, site).trim();
			if (t.id === 'custom' && !fields.text?.trim()) return send(res, 400, { error: 'Type an instruction.' });
			const j = newJob({ site, task: t.id, title: `${t.label}${fields.what ? ': ' + fields.what : ''}`, model });
			startRun(j, text, false);
			return send(res, 200, { job: publicJob(j) });
		}
		if ((m = p.match(/^\/api\/jobs\/([0-9a-f-]+)(?:\/(stream|reply|cancel))?$/))) {
			const j = jobs.get(m[1]); if (!j) return send(res, 404, { error: 'no such job' });
			if (req.method === 'GET' && !m[2]) return send(res, 200, { job: publicJob(j), events: eventsOf(j) });
			if (req.method === 'GET' && m[2] === 'stream') {
				res.writeHead(200, { 'content-type': 'text/event-stream', 'cache-control': 'no-store', connection: 'keep-alive', 'x-content-type-options': 'nosniff' });
				res.write(': connected\n\n');
				// Replay anything that happened after the page loaded the job, then go live.
				const from = Math.max(0, Number(u.searchParams.get('from')) || 0);
				for (const ev of eventsOf(j).slice(from)) res.write(`data: ${JSON.stringify(ev)}\n\n`);
				j.clients.add(res);
				const hb = setInterval(() => res.write(': ping\n\n'), 20000);
				req.on('close', () => { clearInterval(hb); j.clients.delete(res); });
				return;
			}
			if (req.method === 'POST' && m[2] === 'reply') {
				const b = await readBody(req);
				const text = String(b.text || '').trim().slice(0, 20000);
				if (!text) return send(res, 400, { error: 'Type a reply.' });
				if (j.proc) return send(res, 409, { error: 'Claude is still working on this job.' });
				if (!j.sessionId) return send(res, 409, { error: 'This job cannot be continued. Start a new one.' });
				startRun(j, text, true);
				return send(res, 200, { job: publicJob(j) });
			}
			if (req.method === 'POST' && m[2] === 'cancel') { cancelJob(j); return send(res, 200, { ok: true }); }
		}
		if (req.method === 'POST' && (m = p.match(/^\/api\/approvals\/([0-9a-f]+)$/))) {
			const b = await readBody(req);
			const ok = decide(m[1], b.decision === 'allow' ? 'allow' : 'deny', String(b.note || '').slice(0, 1000));
			return send(res, ok ? 200 : 404, ok ? { ok: true } : { error: 'Already decided or expired.' });
		}
		if (req.method === 'POST' && p === '/api/open-folder') {
			const b = await readBody(req);
			const d = b.site ? siteDir(String(b.site)) : WORKSPACE;
			if (!d) return send(res, 404, { error: 'no such site' });
			const opener = WIN ? [SYS.explorer, [d]] : process.platform === 'darwin' ? ['/usr/bin/open', [d]] : [onPath(['xdg-open']), [d]];
			try { if (opener[0]) spawn(opener[0], opener[1], { detached: true, stdio: 'ignore', env: { ...process.env, ...CHILD_ENV } }).unref(); } catch { /* no desktop */ }
			return send(res, 200, { ok: true });
		}
		return send(res, 404, { error: 'not found' });
	} catch (err) {
		const msg = String(err?.message || err);
		if (msg === 'too large' || msg === 'bad json') return send(res, 400, { error: msg });
		console.error(`[desk] ${redact(msg).slice(0, 500)}`);
		return send(res, 500, { error: 'Something went wrong in the Desk. The Desk window shows the details.' });
	}
});

function listen(attempt = 0) {
	server.once('error', (e) => {
		if (e.code === 'EADDRINUSE' && attempt < 10) { PORT += 1; listen(attempt + 1); }
		else { console.error(`WPU Desk could not start: ${e.message}`); process.exit(1); }
	});
	server.listen(PORT, '127.0.0.1', () => {
		const url = loginLink();
		console.log(`\nWPU Desk is running.\n  Workspace : ${WORKSPACE}\n  Claude    : ${claude.found ? claude.version : 'NOT FOUND - install Claude Code and sign in once'}\n  Plugin    : ${claude.pluginInstalled ? 'installed' : 'loaded from ' + PLUGIN_ROOT}\n\n  Open: ${url}\n  (a one-time link, valid 10 minutes - press Enter here for a new one)\n\nKeep this window open while you work. Close it to stop the Desk.\n`);
		openBrowser(url);
	});
}
if (WIN && process.env.USERPROFILE && !lc(WORKSPACE).startsWith(lc(process.env.USERPROFILE) + path.sep)) {
	console.warn(`\nWARNING: the workspace ${WORKSPACE} is outside your user folder. Other Windows users on this PC may be able to read or change it.\nMove it under ${process.env.USERPROFILE} (for example Desktop\\WPU-Work) unless you are the only user of this PC.\n`);
}
loadJobs();
detectClaude();
listen();
// Enter in the Desk window: a fresh sign-in link (opens the browser again).
if (process.stdin.isTTY) {
	process.stdin.setEncoding('utf8');
	process.stdin.on('data', () => { const url = loginLink(); console.log(`  Open: ${url}`); openBrowser(url); });
}
process.on('SIGINT', () => { for (const j of jobs.values()) cancelJob(j); process.exit(0); });
