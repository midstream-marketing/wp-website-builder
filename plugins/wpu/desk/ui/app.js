// WPU Desk - browser side. No frameworks; every element is built with the DOM (no innerHTML),
// so text from Claude, websites or files can never run as code here.
(() => {
	'use strict';

	// ------------------------------------------------------------------ token + api
	// The Desk opens this page with a one-time code (#n=...). Swap it for the session key once, then
	// clear it from the address bar. The key stays in this tab only.
	const code = new URLSearchParams(location.hash.slice(1)).get('n');
	if (location.hash) history.replaceState(null, '', location.pathname);
	let TOKEN = null;
	try { TOKEN = sessionStorage.getItem('deskToken'); } catch { /* none */ }
	let loginError = '';
	async function login() {
		if (!code) return;
		try {
			const r = await fetch('/api/login', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ code }) });
			const d = await r.json().catch(() => ({}));
			if (r.ok && d.token) { TOKEN = d.token; try { sessionStorage.setItem('deskToken', TOKEN); } catch { /* private mode */ } }
			else if (!TOKEN) loginError = d.error || 'Sign-in failed.';
		} catch { loginError = 'The Desk is not running. Start it from the WPU Desk shortcut.'; }
	}

	async function api(path, opts = {}) {
		const r = await fetch(path, { ...opts, headers: { 'x-desk-token': TOKEN || '', ...(opts.body ? { 'content-type': 'application/json' } : {}), ...(opts.headers || {}) } });
		const data = await r.json().catch(() => ({}));
		if (!r.ok) throw new Error(data.error || `Request failed (${r.status})`);
		return data;
	}
	const post = (path, body) => api(path, { method: 'POST', body: JSON.stringify(body || {}) });

	// ------------------------------------------------------------------ dom helpers
	function h(tag, attrs, ...kids) {
		const el = document.createElement(tag);
		for (const [k, v] of Object.entries(attrs || {})) {
			if (v === undefined || v === null || v === false) continue;
			if (k === 'class') el.className = v;
			else if (k === 'text') el.textContent = v;
			else if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
			else el.setAttribute(k, v === true ? '' : String(v));
		}
		for (const kid of kids.flat()) if (kid !== null && kid !== undefined && kid !== false) el.append(kid instanceof Node ? kid : document.createTextNode(String(kid)));
		return el;
	}
	const $ = (id) => document.getElementById(id);
	const fmtTime = (iso) => { try { return new Date(iso).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }); } catch { return iso; } };
	const STATUS = { new: 'Starting', running: 'Working', 'needs-approval': 'Needs your approval', 'needs-reply': 'Waiting for your reply', done: 'Done', failed: 'Failed', cancelled: 'Cancelled', stopped: 'Stopped' };
	const pill = (s) => h('span', { class: `pill ${s}` }, STATUS[s] || s);
	function toast(msg) { const t = $('toast'); t.textContent = msg; t.hidden = false; clearTimeout(toast.tm); toast.tm = setTimeout(() => { t.hidden = true; }, 4500); }

	// Tiny, safe markdown: paragraphs, lists, code blocks, inline code, bold. Builds DOM nodes only.
	function md(text) {
		const box = h('div');
		const lines = String(text || '').split('\n');
		let i = 0;
		const inline = (s) => {
			const out = []; const re = /(`[^`]+`|\*\*[^*]+\*\*)/g; let last = 0, m;
			while ((m = re.exec(s))) {
				if (m.index > last) out.push(s.slice(last, m.index));
				out.push(m[0].startsWith('`') ? h('code', { text: m[0].slice(1, -1) }) : h('strong', { text: m[0].slice(2, -2) }));
				last = m.index + m[0].length;
			}
			if (last < s.length) out.push(s.slice(last));
			return out;
		};
		while (i < lines.length) {
			const l = lines[i];
			if (/^```/.test(l)) { const buf = []; i++; while (i < lines.length && !/^```/.test(lines[i])) buf.push(lines[i++]); i++; box.append(h('pre', { text: buf.join('\n') })); continue; }
			if (/^\s*([-*]|\d+\.)\s+/.test(l)) {
				const ordered = /^\s*\d+\./.test(l); const list = h(ordered ? 'ol' : 'ul');
				while (i < lines.length && /^\s*([-*]|\d+\.)\s+/.test(lines[i])) list.append(h('li', null, inline(lines[i++].replace(/^\s*([-*]|\d+\.)\s+/, ''))));
				box.append(list); continue;
			}
			if (!l.trim()) { i++; continue; }
			const buf = [];
			while (i < lines.length && lines[i].trim() && !/^```/.test(lines[i]) && !/^\s*([-*]|\d+\.)\s+/.test(lines[i])) buf.push(lines[i++].replace(/^#+\s*/, ''));
			box.append(h('p', null, inline(buf.join(' '))));
		}
		return box;
	}

	// ------------------------------------------------------------------ state + routing
	let S = null;
	let view = { name: 'home' };
	let stream = null;

	async function refresh() {
		try {
			S = await api('/api/state');
		} catch (e) {
			$('main').replaceChildren(h('div', { class: 'wrap' }, h('div', { class: 'notice' }, loginError || (TOKEN ? e.message : 'Press Enter in the WPU Desk window to get a sign-in link.'))));
			return;
		}
		renderTop(); renderSites();
		if (view.name === 'home') renderHome();
	}
	setInterval(() => { if (!document.hidden) refresh(); }, 4000);

	function go(v) {
		view = v;
		if (stream) { stream.close(); stream = null; }
		if (v.name === 'home') renderHome();
		else if (v.name === 'site') renderSite(v.slug, v.tab || 'tasks');
		else if (v.name === 'job') renderJob(v.id);
		renderSites();
		$('main').focus();
	}

	// ------------------------------------------------------------------ chrome
	function renderTop() {
		const c = S.claude;
		$('topMeta').replaceChildren(
			h('span', null, 'Workspace: ', h('span', { class: 'mono' }, S.workspace)), '  ·  ',
			c.found ? `Claude Code ${c.version.replace(/\(.*\)/, '').trim()} · plugin ${c.pluginInstalled ? 'installed' : 'loaded from Desk folder'}` : 'Claude Code not found');
		const n = S.approvals.length;
		const b = $('apprCount'); b.textContent = String(n); b.className = n ? 'badge' : 'badge zero';
		document.title = n ? `(${n}) WPU Desk` : 'WPU Desk';
	}
	function renderSites() {
		if (!S) return;
		const qy = $('siteSearch').value.toLowerCase();
		const items = S.sites.filter((s) => !qy || s.slug.includes(qy) || (s.name || '').toLowerCase().includes(qy) || (s.url || '').toLowerCase().includes(qy));
		$('siteList').replaceChildren(...(items.length ? items.map((s) => h('button', {
			class: `site-item${view.name === 'site' && view.slug === s.slug ? ' active' : ''}`, type: 'button', onclick: () => go({ name: 'site', slug: s.slug }),
		}, h('span', { class: 'name' }, h('span', { class: `dot ${s.lastJob ? s.lastJob.status : ''}` }), s.name || s.slug), h('span', { class: 'url' }, s.url || s.slug))) : [h('p', { class: 'muted' }, S.sites.length ? 'No match.' : 'No sites yet.')]));
	}
	$('siteSearch').addEventListener('input', renderSites);
	$('btnHome').addEventListener('click', () => go({ name: 'home' }));
	$('btnNewSite').addEventListener('click', openNewSite);
	$('btnSecrets').addEventListener('click', () => openSecrets(view.slug || 'global'));
	$('btnApprovals').addEventListener('click', openApprovals);

	// ------------------------------------------------------------------ modal
	function modal(title, body) {
		$('modalTitle').textContent = title;
		$('modalBody').replaceChildren(...[body].flat());
		$('modalBack').hidden = false;
		const first = $('modalBody').querySelector('input, select, textarea, button');
		if (first) first.focus();
	}
	function closeModal() { $('modalBack').hidden = true; $('modalBody').replaceChildren(); }
	$('modalClose').addEventListener('click', closeModal);
	$('modalBack').addEventListener('click', (e) => { if (e.target === $('modalBack')) closeModal(); });
	document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !$('modalBack').hidden) closeModal(); });

	function fieldEl(f) {
		const id = `f-${f.id}`;
		let input;
		if (f.type === 'textarea') input = h('textarea', { id, name: f.id });
		else if (f.type === 'select') input = h('select', { id, name: f.id }, f.options.map((o) => h('option', { value: o, text: o })));
		else input = h('input', { id, name: f.id, type: 'text', autocomplete: 'off' });
		return h('div', { class: 'field' }, h('label', { for: id, text: f.label }), input);
	}
	function modelEl() {
		return h('div', { class: 'field' }, h('label', { for: 'f-model', text: 'Model' }),
			h('select', { id: 'f-model' }, S.models.map((m) => h('option', { value: m, text: m ? m[0].toUpperCase() + m.slice(1) : 'Default (your Claude Code setting)' }))),
			h('span', { class: 'hint', text: 'Uses your own Claude subscription through Claude Code. Opus for design-heavy builds; Haiku for quick checks.' }));
	}
	function collect(fields) { return Object.fromEntries(fields.map((f) => [f.id, ($(`f-${f.id}`) || {}).value || ''])); }

	// ------------------------------------------------------------------ home
	function renderHome() {
		if (!S) return;
		const main = $('main');
		const wrap = h('div', { class: 'wrap' });
		if (!S.claude.found) wrap.append(h('div', { class: 'notice' }, 'Claude Code was not found on this computer. Install it, open a terminal once, run "claude" and sign in with your Claude account, then click ', h('button', { class: 'btn', type: 'button', onclick: async () => { await post('/api/claude/recheck'); refresh(); } }, 'Check again'), '.'));
		wrap.append(h('div', { class: 'site-head' }, h('div', null, h('h1', { text: 'Recent jobs' }), h('p', { class: 'muted', text: 'Every task you start here runs Claude Code with the WP Ultimate Build plugin, signed in with your own Claude account.' }))));
		if (!S.sites.length) {
			wrap.append(h('div', { class: 'card empty' }, h('h2', { text: 'Add your first client site' }), h('p', { text: 'Give it a short name and the site URL. Claude sets up the folder, the bridge plugin and a baseline audit.' }), h('button', { class: 'btn primary', type: 'button', onclick: openNewSite }, '+ New site')));
		}
		wrap.append(jobsTable(S.jobs, true));
		main.replaceChildren(wrap);
	}
	function jobsTable(list, withSite) {
		if (!list.length) return h('div', { class: 'card empty', text: 'No jobs yet.' });
		return h('div', { class: 'card' }, h('table', { class: 'list' },
			h('thead', null, h('tr', null, withSite ? h('th', { text: 'Site' }) : null, h('th', { text: 'Job' }), h('th', { text: 'Status' }), h('th', { text: 'Updated' }))),
			h('tbody', null, list.map((j) => h('tr', { class: 'click', onclick: () => go({ name: 'job', id: j.id }) },
				withSite ? h('td', { text: j.site || '-' }) : null, h('td', { text: j.title }), h('td', null, pill(j.status)), h('td', { class: 'muted', text: fmtTime(j.updatedAt) }))))));
	}

	// ------------------------------------------------------------------ site
	async function renderSite(slug, tab) {
		const main = $('main');
		let d;
		try { d = await api(`/api/site/${encodeURIComponent(slug)}`); } catch (e) { main.replaceChildren(h('div', { class: 'wrap' }, h('div', { class: 'notice', text: e.message }))); return; }
		const info = (S.sites || []).find((s) => s.slug === slug) || { slug };
		const url = /^https?:\/\//i.test(info.url || '') ? info.url : '';
		const head = h('div', { class: 'site-head' },
			h('div', null, h('h1', { text: info.name || slug }), h('p', { class: 'muted mono', text: url || slug })),
			h('div', { class: 'links' },
				url ? h('a', { class: 'btn', href: url, target: '_blank', rel: 'noopener noreferrer' }, 'Open site') : null,
				url ? h('a', { class: 'btn', href: url.replace(/\/$/, '') + '/wp-admin/', target: '_blank', rel: 'noopener noreferrer' }, 'wp-admin') : null,
				h('button', { class: 'btn', type: 'button', onclick: () => post('/api/open-folder', { site: slug }).catch((e) => toast(e.message)) }, 'Open folder'),
				h('button', { class: 'btn', type: 'button', onclick: () => openSecrets(slug) }, 'Secrets')));
		const tabs = [['tasks', 'Tasks'], ['jobs', `Jobs (${d.jobs.length})`], ['files', 'Results & files'], ['notes', 'Site notes'], ['history', 'Change log']];
		const tabBar = h('div', { class: 'tabs', role: 'tablist' }, tabs.map(([id, label]) => h('button', { class: `tab${tab === id ? ' active' : ''}`, type: 'button', role: 'tab', 'aria-selected': tab === id ? 'true' : 'false', onclick: () => go({ name: 'site', slug, tab: id }) }, label)));
		let body;
		if (tab === 'tasks') {
			const groups = {};
			for (const t of S.tasks) (groups[t.group] = groups[t.group] || []).push(t);
			body = h('div', { class: 'wrap' }, Object.entries(groups).map(([g, list]) => h('div', { class: 'task-group' }, h('h3', { text: g }),
				h('div', { class: 'task-grid' }, list.map((t) => h('button', { class: 'task', type: 'button', onclick: () => openTask(slug, t) }, h('strong', { text: t.label }), h('span', { text: t.desc })))))));
		} else if (tab === 'jobs') body = jobsTable(d.jobs, false);
		else if (tab === 'files') body = filesView(slug, d.files);
		else if (tab === 'notes') body = h('div', { class: 'card' }, d.notes ? md(d.notes) : h('p', { class: 'muted', text: 'No SITE-NOTES.md yet. Claude writes one during "New site".' }));
		else body = historyView(d);
		main.replaceChildren(h('div', { class: 'wrap' }, head, tabBar, body));
	}

	function filesView(slug, files) {
		const imgs = files.filter((f) => f.viewable && /\.(png|jpe?g|webp|gif)$/i.test(f.path)).slice(0, 60);
		const docs = files.filter((f) => !/\.(png|jpe?g|webp|gif)$/i.test(f.path)).slice(0, 300);
		const fileUrl = (p) => `/api/file?site=${encodeURIComponent(slug)}&path=${encodeURIComponent(p)}&t=${encodeURIComponent(TOKEN)}`;
		return h('div', { class: 'wrap' },
			h('div', { class: 'card' }, h('h2', { text: 'Screenshots' }), h('p', { class: 'hint', text: 'Newest first. Audits, builds and visual checks save their screenshots here.' }),
				imgs.length ? h('div', { class: 'gallery' }, imgs.map((f) => h('button', { class: 'thumb', type: 'button', onclick: () => modal(f.path, h('img', { class: 'viewer', src: fileUrl(f.path), alt: f.path })) },
					h('img', { src: fileUrl(f.path), alt: f.path, loading: 'lazy' }), h('div', { text: f.path })))) : h('p', { class: 'muted', text: 'No screenshots yet.' })),
			h('div', { class: 'card' }, h('h2', { text: 'Reports and files' }),
				docs.length ? h('table', { class: 'list' }, h('thead', null, h('tr', null, h('th', { text: 'File' }), h('th', { text: 'Size' }), h('th', { text: 'Changed' }))),
					h('tbody', null, docs.map((f) => h('tr', { class: f.viewable ? 'click' : '', onclick: f.viewable ? () => viewText(slug, f.path) : undefined },
						h('td', { class: 'mono' }, f.path, f.viewable ? '' : h('span', { class: 'muted', text: '  (open the folder to view)' })), h('td', { class: 'muted', text: `${Math.max(1, Math.round(f.size / 1024))} KB` }), h('td', { class: 'muted', text: fmtTime(f.mtime) })))))
					: h('p', { class: 'muted', text: 'Nothing yet.' })));
	}
	async function viewText(slug, p) {
		try {
			const r = await fetch(`/api/file?site=${encodeURIComponent(slug)}&path=${encodeURIComponent(p)}`, { headers: { 'x-desk-token': TOKEN } });
			if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || 'Cannot open this file.');
			let text = await r.text();
			if (/\.json$/i.test(p)) { try { text = JSON.stringify(JSON.parse(text), null, 2); } catch { /* keep raw */ } }
			modal(p, h('pre', { class: 'viewer', text: text.slice(0, 400000) }));
		} catch (e) { toast(e.message); }
	}
	function historyView(d) {
		return h('div', { class: 'wrap' },
			h('div', { class: 'card' }, h('h2', { text: 'Hosting changes (SFTP / cPanel)' }),
				d.actions.length ? h('pre', { class: 'viewer', text: d.actions.join('\n') }) : h('p', { class: 'muted', text: 'No hosting changes logged.' })),
			h('div', { class: 'card' }, h('h2', { text: 'Site changes through the bridge' }),
				h('p', { class: 'hint', text: 'The full audit log of bridge changes, with who made each one, is on the site: wp-admin → Tools → WPU Bridge. Ask "show the bridge audit log" in Ask anything to pull it here.' })));
	}

	// ------------------------------------------------------------------ tasks
	function openTask(slug, t) {
		const start = h('button', { class: 'btn primary', type: 'button' }, 'Start');
		start.addEventListener('click', async () => {
			start.disabled = true;
			try {
				const r = await post('/api/jobs', { site: slug, task: t.id, fields: collect(t.fields), model: $('f-model').value });
				closeModal(); await refresh(); go({ name: 'job', id: r.job.id });
			} catch (e) { toast(e.message); start.disabled = false; }
		});
		modal(`${t.label} · ${slug}`, [h('p', { class: 'muted', text: t.desc }), ...t.fields.map(fieldEl), modelEl(), h('div', { class: 'row-end' }, h('button', { class: 'btn', type: 'button', onclick: closeModal }, 'Cancel'), start)]);
	}
	function openNewSite() {
		if (!S) return;
		const start = h('button', { class: 'btn primary', type: 'button' }, 'Set up site');
		start.addEventListener('click', async () => {
			start.disabled = true;
			try {
				const r = await post('/api/jobs', { task: 'new-site', fields: collect(S.newSite.fields), model: $('f-model').value });
				closeModal(); await refresh(); go({ name: 'job', id: r.job.id });
			} catch (e) { toast(e.message); start.disabled = false; }
		});
		modal('New client site', [h('p', { class: 'muted', text: 'Claude creates the site folder and notes, gives you the bridge plugin to install, then checks the connection and runs a baseline audit.' }), ...S.newSite.fields.map(fieldEl), modelEl(), h('div', { class: 'row-end' }, h('button', { class: 'btn', type: 'button', onclick: closeModal }, 'Cancel'), start)]);
	}

	// ------------------------------------------------------------------ secrets
	const SECRET_LABELS = {
		key: 'Bridge connection key', apppassword: 'Application Password', adminpass: 'wp-admin password', sftp_pass: 'SFTP / SSH password', sftp_keypass: 'SSH key passphrase', cpanel_token: 'cPanel API token',
		dataforseo_login: 'DataForSEO login', dataforseo_password: 'DataForSEO password', pagespeed_key: 'PageSpeed API key',
	};
	async function openSecrets(scope) {
		const scopes = ['global', ...((S && S.sites) || []).map((s) => s.slug)];
		const sel = h('select', { id: 'sec-scope' }, scopes.map((s) => h('option', { value: s, text: s === 'global' ? 'Global (all sites)' : s, selected: s === scope })));
		const list = h('div', { class: 'wrap' });
		const load = async () => {
			const sc = sel.value;
			list.replaceChildren(h('p', { class: 'muted', text: 'Checking…' }));
			let st;
			try { st = await api(`/api/secrets/${encodeURIComponent(sc)}`); } catch (e) { list.replaceChildren(h('div', { class: 'notice', text: e.message })); return; }
			const names = sc === 'global' ? ['dataforseo_login', 'dataforseo_password', 'pagespeed_key'] : ['key', 'apppassword', 'adminpass', 'sftp_pass', 'sftp_keypass', 'cpanel_token'];
			list.replaceChildren(
				st.windows ? h('p', { class: 'hint', text: 'Saved encrypted for your Windows user only. Values are never shown again, and never go into the Claude conversation.' }) : h('div', { class: 'notice', text: 'The encrypted store needs Windows. On this computer, set WPU_SECRET_<SCOPE>_<NAME> environment variables before starting the Desk.' }),
				...names.map((n) => {
					const inp = h('input', { type: 'password', autocomplete: 'new-password', placeholder: st.saved[n] ? 'Saved - type to replace' : 'Not saved', 'aria-label': SECRET_LABELS[n] });
					const btn = h('button', { class: 'btn', type: 'button' }, 'Save');
					btn.addEventListener('click', async () => {
						if (!inp.value) return toast('Type the value first.');
						btn.disabled = true;
						try { await post('/api/secrets', { scope: sc, name: n, value: inp.value }); inp.value = ''; toast(`Saved ${SECRET_LABELS[n]}.`); load(); } catch (e) { toast(e.message); btn.disabled = false; }
					});
					return h('div', { class: 'secret-row' }, h('strong', { text: SECRET_LABELS[n] }), inp, btn, h('span', { class: `pill ${st.saved[n] ? 'done' : ''}`, text: st.saved[n] ? 'Saved' : 'Missing' }));
				}));
		};
		sel.addEventListener('change', load);
		modal('Secrets', [h('div', { class: 'field' }, h('label', { for: 'sec-scope', text: 'For' }), sel), list]);
		load();
	}

	// ------------------------------------------------------------------ approvals list
	function openApprovals() {
		if (!S) return;
		modal('Waiting for your approval', S.approvals.length ? S.approvals.map((a) => h('div', { class: 'approval' },
			h('strong', null, `${a.site || ''} · ${a.tool}`), a.reason ? h('span', { text: a.reason.replace(/^WP Ultimate Build:\s*/, '') }) : null, h('div', { class: 'what', text: a.summary }),
			h('div', { class: 'row' }, h('button', { class: 'btn primary', type: 'button', onclick: () => { closeModal(); go({ name: 'job', id: a.job }); } }, 'Open job')))) : [h('p', { class: 'muted', text: 'Nothing is waiting for you.' })]);
	}

	// ------------------------------------------------------------------ job view
	async function renderJob(id) {
		const main = $('main');
		let d;
		try { d = await api(`/api/jobs/${encodeURIComponent(id)}`); } catch (e) { main.replaceChildren(h('div', { class: 'wrap' }, h('div', { class: 'notice', text: e.message }))); return; }
		let job = d.job;
		const st = h('span', null, pill(job.status));
		const cancelBtn = h('button', { class: 'btn bad', type: 'button' }, 'Stop job');
		cancelBtn.addEventListener('click', async () => { if (confirmStop()) { await post(`/api/jobs/${id}/cancel`).catch((e) => toast(e.message)); } });
		const head = h('div', { class: 'job-head' },
			h('div', null, h('h1', { text: job.title }), h('p', { class: 'muted' }, job.site ? h('button', { class: 'btn ghost', type: 'button', onclick: () => go({ name: 'site', slug: job.site }) }, `← ${job.site}`) : null, ' ', st, ' ', h('span', { class: 'mono', text: fmtTime(job.createdAt) }))),
			cancelBtn);
		const box = h('div', { class: 'stream', 'aria-live': 'polite' });
		const toolEls = {};
		const text = h('textarea', { placeholder: 'Reply to Claude, answer its question, or give the next instruction…', 'aria-label': 'Reply' });
		const sendBtn = h('button', { class: 'btn primary', type: 'button' }, 'Send');
		const composer = h('div', { class: 'composer' }, text, sendBtn);
		sendBtn.addEventListener('click', async () => {
			if (!text.value.trim()) return;
			sendBtn.disabled = true;
			try { await post(`/api/jobs/${id}/reply`, { text: text.value }); text.value = ''; } catch (e) { toast(e.message); }
			sendBtn.disabled = false;
		});
		text.addEventListener('keydown', (e) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) sendBtn.click(); });
		const setState = (s) => {
			job.status = s; st.replaceChildren(pill(s));
			const live = ['running', 'needs-approval', 'new'].includes(s);
			cancelBtn.hidden = !live; sendBtn.disabled = live; text.disabled = live;
			text.placeholder = live ? 'Claude is working… you can reply when it finishes.' : 'Reply to Claude, answer its question, or give the next instruction…';
		};
		setState(job.status);
		const atBottom = () => box.scrollHeight - box.scrollTop - box.clientHeight < 80;
		const add = (el) => { const stick = atBottom(); box.append(el); if (stick) box.scrollTop = box.scrollHeight; };
		const approvalEls = {};
		function render(ev) {
			if (ev.k === 'you') add(h('div', { class: 'msg you', text: ev.text.replace(/^You are running inside WPU Desk[\s\S]*?\n\n/, '') }));
			else if (ev.k === 'text') add(h('div', { class: 'msg claude' }, md(ev.text)));
			else if (ev.k === 'tool') {
				const pre = h('pre', { hidden: true });
				const el = h('div', { class: 'tool' }, h('button', { type: 'button', onclick: () => { pre.hidden = !pre.hidden; } }, `▸ ${ev.name}: ${ev.summary}`), pre);
				toolEls[ev.id] = { el, pre }; add(el);
			} else if (ev.k === 'result') {
				const t = toolEls[ev.id];
				if (t) { t.pre.textContent = ev.text || '(no output)'; if (ev.error) t.el.classList.add('err'); }
			} else if (ev.k === 'approval') {
				const note = h('input', { type: 'text', placeholder: 'Optional note for Claude (why you rejected, what to change)', 'aria-label': 'Note' });
				const yes = h('button', { class: 'btn ok', type: 'button' }, 'Approve');
				const no = h('button', { class: 'btn bad', type: 'button' }, 'Reject');
				const card = h('div', { class: 'approval' },
					h('strong', { text: 'Approval needed before Claude continues' }),
					ev.reason ? h('span', { text: ev.reason.replace(/^WP Ultimate Build:\s*/, '') }) : h('span', { text: `Claude wants to use ${ev.tool}.` }),
					h('div', { class: 'what', text: ev.summary }),
					h('details', null, h('summary', { text: 'Full details' }), h('pre', { text: ev.detail })),
					h('p', { class: 'hint', text: 'Read the dry run above this card before approving. Approving runs exactly this, once.' }),
					h('div', { class: 'row' }, note, no, yes));
				const decideNow = async (decision) => {
					yes.disabled = no.disabled = true;
					try { await post(`/api/approvals/${ev.id}`, { decision, note: note.value }); } catch (e) { toast(e.message); yes.disabled = no.disabled = false; }
				};
				yes.addEventListener('click', () => decideNow('allow'));
				no.addEventListener('click', () => decideNow('deny'));
				approvalEls[ev.id] = card; add(card);
			} else if (ev.k === 'decision') {
				const card = approvalEls[ev.id];
				if (card) { card.classList.add('decided'); card.querySelector('.row')?.replaceChildren(h('strong', { text: ev.decision === 'allow' ? 'Approved' : ev.decision === 'expired' ? 'Expired' : `Rejected${ev.note ? ': ' + ev.note : ''}` })); }
			} else if (ev.k === 'done') add(h('div', { class: 'done-box', text: `Finished${ev.seconds ? ` in ${Math.round(ev.seconds / 60) || '<1'} min` : ''}${ev.turns ? `, ${ev.turns} steps` : ''}.` }));
			else if (ev.k === 'error') add(h('div', { class: 'error-box', text: ev.text }));
			else if (ev.k === 'info') add(h('div', { class: 'info', text: ev.text }));
			else if (ev.k === 'status') setState(ev.status);
		}
		const pendingIds = new Set((S && S.approvals || []).map((a) => a.id));
		for (const ev of d.events) {
			render(ev);
			if (ev.k === 'approval' && !pendingIds.has(ev.id) && !d.events.some((x) => x.k === 'decision' && x.id === ev.id)) render({ k: 'decision', id: ev.id, decision: 'expired' });
		}
		main.replaceChildren(h('div', { class: 'job' }, head, box, composer));
		box.scrollTop = box.scrollHeight;
		let seen = d.events.length;
		const connect = () => {
			stream = new EventSource(`/api/jobs/${encodeURIComponent(id)}/stream?t=${encodeURIComponent(TOKEN)}&from=${seen}`);
			stream.onmessage = (m) => { try { const ev = JSON.parse(m.data); seen++; render(ev); if (ev.k === 'approval' || ev.k === 'status') refresh(); } catch { /* skip */ } };
			stream.onerror = () => { if (stream) { stream.close(); setTimeout(() => { if (view.name === 'job' && view.id === id) connect(); }, 2000); } };
		};
		connect();
	}
	function confirmStop() { return window.confirm('Stop this job? Claude stops at once; changes already approved stay as they are.'); }

	// ------------------------------------------------------------------ start
	login().then(refresh).then(() => { if (S) go({ name: 'home' }); });
})();
