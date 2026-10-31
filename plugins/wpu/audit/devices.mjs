// Device matrix: every page on real device profiles (viewport, pixel density, phone user-agent - image CDNs
// serve per device), checked for the things a visitor would notice:
//   JS errors, failed same-site requests, sideways scroll, broken images, images cut off by a container,
//   low-resolution images, text drawn on top of an image.
// Screenshots of each page's first screen go to shots/devices/<device>/. Read-only.
//   node audit/devices.mjs [pages.json] [deviceNames,comma]     (report also written to shots/devices/report.txt)
import fs from 'node:fs';
import path from 'node:path';
import { launch, url, ensureShots } from '../lib/lib.mjs';

const ANDROID = 'Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Mobile Safari/537.36';
const IPHONE = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1';
const DESKTOP = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36';
const IPAD = 'Mozilla/5.0 (iPad; CPU OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1';
const DEVICES = [
	{ name: 'galaxy-s-360', width: 360, height: 780, dpr: 3, mobile: true, ua: ANDROID },
	{ name: 'iphone-390', width: 390, height: 844, dpr: 3, mobile: true, ua: IPHONE },
	{ name: 'pixel7-412', width: 412, height: 915, dpr: 2.625, mobile: true, ua: ANDROID },
	{ name: 'ipad-768', width: 768, height: 1024, dpr: 2, mobile: true, ua: IPAD },
	{ name: 'ipad-land-1024', width: 1024, height: 768, dpr: 2, mobile: true, ua: IPAD },
	{ name: 'laptop-1366', width: 1366, height: 768, dpr: 1, mobile: false, ua: DESKTOP },
	{ name: 'desktop-1920', width: 1920, height: 1080, dpr: 1, mobile: false, ua: DESKTOP },
];

const [pagesArg, devArg] = process.argv.slice(2);
const pages = pagesArg && fs.existsSync(pagesArg) ? JSON.parse(fs.readFileSync(pagesArg, 'utf8')) : ['/'];
const devices = devArg ? DEVICES.filter((d) => devArg.split(',').includes(d.name)) : DEVICES;
const root = path.join(ensureShots(), 'devices');
fs.mkdirSync(root, { recursive: true });
const host = new URL(url('/')).host;

async function checkPage(ctx, dev, p) {
	const page = await ctx.newPage();
	const errors = [], failed = [];
	page.on('pageerror', (e) => errors.push(e.message.slice(0, 160)));
	page.on('response', (r) => { try { const u = new URL(r.url()); if (u.host === host && r.status() >= 400 && !u.pathname.includes('dit-bestaat-niet') && !(r.status() === 403 && r.request().isNavigationRequest())) failed.push(`${r.status()} ${u.pathname.slice(0, 80)}`); } catch {} });
	let status = 0;
	try {
		const res = await page.goto(url(p), { waitUntil: 'load', timeout: 90000 });
		status = res ? res.status() : 0;
	} catch (e) { await page.close(); return { p, status: 'LOAD FAIL ' + e.message.slice(0, 80), issues: [] }; }
	await page.waitForTimeout(1500);
	// scroll the whole page so lazy images load, then back to the top
	await page.evaluate(async () => { const h = document.documentElement.scrollHeight; for (let y = 0; y < h; y += innerHeight * 0.8) { scrollTo(0, y); await new Promise((r) => setTimeout(r, 120)); } scrollTo(0, 0); });
	await page.waitForTimeout(1200);
	const res = await page.evaluate((dpr) => {
		const out = { overflow: [], broken: [], cropped: [], lowres: [], overlap: [], scrollW: document.documentElement.scrollWidth, vw: innerWidth,
			blocked: /Checking your browser before accessing|Just a moment/i.test(document.title) };
		if (out.blocked) return out;
		const vw = innerWidth;
		const lbl = (e) => `${e.tagName.toLowerCase()}.${[...e.classList].filter((c) => !/^elementor-(element|widget)$/.test(c)).slice(0, 2).join('.')}`;
		const clippedByScroller = (e) => { for (let n = e.parentElement; n; n = n.parentElement) { const s = getComputedStyle(n); if (/(auto|scroll|hidden|clip)/.test(s.overflowX)) return true; } return false; };
		if (out.scrollW > vw + 1) {
			for (const e of document.querySelectorAll('body *')) { const r = e.getBoundingClientRect(); if (r.width && r.right > vw + 1 && getComputedStyle(e).position !== 'fixed' && !clippedByScroller(e)) out.overflow.push(`${lbl(e)} right=${Math.round(r.right)}`); if (out.overflow.length > 5) break; }
		}
		const imgs = [...document.querySelectorAll('img')].filter((i) => { const r = i.getBoundingClientRect(); const s = getComputedStyle(i); return r.width > 24 && r.height > 24 && s.visibility !== 'hidden' && s.display !== 'none' && s.opacity !== '0' && !i.closest('[aria-hidden="true"], .zoomImg, .pswp'); });
		for (const i of imgs) {
			const r = i.getBoundingClientRect(), s = getComputedStyle(i), name = (i.currentSrc || i.src).split('/').pop().slice(0, 48);
			if (i.complete && i.naturalWidth === 0) { out.broken.push(name); continue; }
			if (r.left < -1 || r.right > vw + 1) continue; // off-screen carousel slides are clipped on purpose
			let vis = { t: r.top, b: r.bottom, l: r.left, rr: r.right };
			for (let n = i.parentElement; n && n !== document.body; n = n.parentElement) {
				const cs = getComputedStyle(n);
				if (/(hidden|clip)/.test(cs.overflow + cs.overflowY + cs.overflowX)) { const b = n.getBoundingClientRect(); vis = { t: Math.max(vis.t, b.top), b: Math.min(vis.b, b.bottom), l: Math.max(vis.l, b.left), rr: Math.min(vis.rr, b.right) }; }
			}
			const shown = Math.max(0, vis.b - vis.t) * Math.max(0, vis.rr - vis.l) / (r.width * r.height);
			if (shown > 0.05 && shown < 0.9 && s.objectFit !== 'cover') out.cropped.push(`${name} ${Math.round(shown * 100)}% shown (${Math.round(r.width)}x${Math.round(r.height)})`);
			if (i.naturalWidth && r.width > 120 && i.naturalWidth < r.width * dpr * 0.5 && !/\.svg/i.test(name)) out.lowres.push(`${name} ${i.naturalWidth}px for ${Math.round(r.width)}css@${dpr}x`);
		}
		const texts = [...document.querySelectorAll('h1, h2, h3, h4, .price, .product_title, p, .elementor-button, button')].filter((t) => { const r = t.getBoundingClientRect(); return r.width > 10 && r.height > 8 && getComputedStyle(t).visibility !== 'hidden' && t.textContent.trim(); });
		for (const t of texts) {
			const tr = t.getBoundingClientRect();
			for (const i of imgs) {
				if (i.contains(t) || t.contains(i) || t.closest('a')?.contains(i)) continue;
				const ir = i.getBoundingClientRect();
				const ix = Math.max(0, Math.min(tr.right, ir.right) - Math.max(tr.left, ir.left)), iy = Math.max(0, Math.min(tr.bottom, ir.bottom) - Math.max(tr.top, ir.top));
				if (ix * iy > 0.4 * tr.width * tr.height) { out.overlap.push(`"${t.textContent.trim().slice(0, 30)}" over ${(i.currentSrc || i.src).split('/').pop().slice(0, 36)}`); break; }
			}
			if (out.overlap.length > 4) break;
		}
		return out;
	}, dev.dpr);
	const dir = path.join(root, dev.name);
	fs.mkdirSync(dir, { recursive: true });
	await page.screenshot({ path: path.join(dir, (p.replace(/[^a-z0-9]+/gi, '-').replace(/^-|-$/g, '') || 'home') + '.png') });
	await page.close();
	const issues = [];
	if (errors.length) issues.push(`JS: ${[...new Set(errors)].slice(0, 2).join(' | ')}`);
	if (failed.length) issues.push(`requests: ${[...new Set(failed)].slice(0, 3).join(', ')}`);
	if (res.scrollW > res.vw + 1) issues.push(`sideways scroll ${res.scrollW}/${res.vw}: ${res.overflow.slice(0, 3).join(', ')}`);
	if (res.broken.length) issues.push(`broken img: ${res.broken.slice(0, 3).join(', ')}`);
	if (res.cropped.length) issues.push(`cropped img: ${res.cropped.slice(0, 3).join(' | ')}`);
	if (res.overlap.length) issues.push(`text over image: ${res.overlap.slice(0, 2).join(' | ')}`);
	if (res.blocked) return { p, status: 'BLOCKED by the host browser check - not checked', issues: [], lowres: [] };
	return { p, status, issues, lowres: res.lowres };
}

const browser = await launch();
const report = [];
const log = (s) => { console.log(s); report.push(s); };
let totalIssues = 0;
const lowresAll = new Map();
for (const dev of devices) {
	log(`\n=== ${dev.name} (${dev.width}x${dev.height} @${dev.dpr}x${dev.mobile ? ', touch' : ''})`);
	const queue = [...pages];
	const results = [];
	// One page at a time with a pause (CONC / PAUSE env): Hostinger's firewall answers bursts of automated
	// page loads with 403, which would be reported as site faults.
	const conc = Number(process.env.CONC || 1), pause = Number(process.env.PAUSE || 2500);
	// One context per device: the CDN's hcdn cookie, earned once when its browser check passes, then covers every page.
	const ctx = await browser.newContext({ viewport: { width: dev.width, height: dev.height }, deviceScaleFactor: dev.dpr, isMobile: dev.mobile, hasTouch: dev.mobile, userAgent: dev.ua });
	await Promise.all(Array.from({ length: conc }, async () => { while (queue.length) { const p = queue.shift(); results.push(await checkPage(ctx, dev, p)); await new Promise((r) => setTimeout(r, pause)); } }));
	await ctx.close();
	results.sort((a, b) => pages.indexOf(a.p) - pages.indexOf(b.p));
	for (const r of results) {
		totalIssues += r.issues.length;
		log(`  ${r.issues.length ? 'ISSUE' : 'ok   '} ${String(r.status).padEnd(4)} ${r.p}${r.issues.length ? '\n        - ' + r.issues.join('\n        - ') : ''}`);
		if (r.lowres && r.lowres.length) lowresAll.set(`${dev.name} ${r.p}`, r.lowres.length);
	}
}
await browser.close();
log(`\n${totalIssues ? totalIssues + ' issue(s)' : 'no issues'} across ${devices.length} devices x ${pages.length} pages.`);
if (lowresAll.size) log(`low-resolution images (served below half the screen's pixel density) on ${lowresAll.size} device/page combinations, e.g. ${[...lowresAll.entries()].slice(0, 4).map(([k, v]) => `${k}: ${v}`).join('; ')}`);
fs.writeFileSync(path.join(root, 'report.txt'), report.join('\n'));
