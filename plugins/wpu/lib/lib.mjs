// Shared helpers for the WP Ultimate Build browser scripts (merged from WP Site Build + WP Site Doctor).
//
// Uses the system-installed Google Chrome (channel: 'chrome') so there is no
// separate browser download and no version drift against the client's browser.
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

/** Where this plugin's code lives (read-only at runtime - never write here). */
export const PLUGIN_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

/** The workspace: the folder Claude Code was opened in, or WPU_WORKSPACE. */
export const WORKSPACE = process.env.WPU_WORKSPACE || process.cwd();

/**
 * Which client site? WPU_SITE=<slug> picks <workspace>/sites/<slug>/site.json.
 * There is deliberately no fallback to "the last site": these tools write to live
 * client sites. Old wp-site-build / wp-site-doctor configs still work - WPU_SITE
 * (or WPSB_CONFIG / WPSD_CONFIG) may name config.<x>.json in the workspace.
 */
export function siteFile() {
	const wanted = process.env.WPU_SITE || process.env.WPSB_CONFIG || process.env.WPSD_CONFIG;
	if (!wanted) {
		throw new Error(`No site selected. Set WPU_SITE=<slug> (folders in ${path.join(WORKSPACE, 'sites')})`);
	}
	const candidates = [
		path.join(WORKSPACE, 'sites', wanted, 'site.json'),
		path.join(WORKSPACE, wanted),
		path.join(WORKSPACE, `config.${wanted}.json`),
		path.join(WORKSPACE, `${wanted}.json`),
	];
	const picked = candidates.find((f) => fs.existsSync(f) && fs.statSync(f).isFile());
	if (!picked) throw new Error(`WPU_SITE="${wanted}" matched nothing (looked for sites/${wanted}/site.json and config.${wanted}.json in ${WORKSPACE})`);
	return { slug: wanted.replace(/^config\./, '').replace(/\.json$/, '').toLowerCase(), file: picked };
}

/**
 * Output folder for this site (screenshots, reports). Falls back to the
 * workspace when no site is selected, for tools that do not need one.
 */
export const ROOT = (() => {
	try {
		return path.dirname(siteFile().file);
	} catch {
		return WORKSPACE;
	}
})();

/**
 * A secret from the member's own encrypted store (scripts/wpu-secret.ps1), or
 * from WPU_SECRET_<SCOPE>_<NAME> in the environment. Never logged.
 */
export function secret(scope, name) {
	const envName = `WPU_SECRET_${scope}_${name}`.toUpperCase().replace(/[^A-Z0-9_]/g, '_');
	if (process.env[envName]) return process.env[envName];
	if (process.platform !== 'win32') return null;
	const r = spawnSync(
		'powershell',
		['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', path.join(PLUGIN_ROOT, 'scripts', 'wpu-secret.ps1'), 'get', scope, name],
		{ encoding: 'utf8', windowsHide: true }
	);
	return r.status === 0 && r.stdout ? r.stdout : null;
}

/** The selected site's settings, with the admin password filled from the secret store. */
export function cfg() {
	const { slug, file } = siteFile();

	// PowerShell's Set-Content -Encoding utf8 writes a BOM, which JSON.parse
	// rejects. Strip it rather than making every writer remember.
	const raw = fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, '');

	let conf;
	try {
		conf = JSON.parse(raw);
	} catch (e) {
		throw new Error(`${file} is not valid JSON: ${e.message}`);
	}
	conf._slug = slug;
	conf._dir = path.dirname(file);
	if (!conf.pass) {
		Object.defineProperty(conf, 'pass', { enumerable: false, configurable: true, get: () => secret(slug, 'adminpass') });
	}
	return conf;
}

/** Absolute URL from a path or a full URL. */
export function url(pathOrUrl, conf = cfg()) {
	if (/^https?:\/\//i.test(pathOrUrl)) return pathOrUrl;
	return conf.baseUrl.replace(/\/$/, '') + (pathOrUrl.startsWith('/') ? pathOrUrl : `/${pathOrUrl}`);
}

/** Every URL to audit, as absolute URLs. */
export function urls(conf = cfg()) {
	return (conf.urls || ['/']).map((u) => url(u, conf));
}

/**
 * Chrome as installed on the member's machine (channel 'chrome', no download). If it is
 * missing, fall back to Playwright's own Chromium so the audit still runs, and say so.
 * WPU_BROWSER_CHANNEL overrides ('msedge', or '' for Playwright's Chromium).
 */
export async function launchBrowser(opts = {}) {
	const channel = process.env.WPU_BROWSER_CHANNEL ?? 'chrome';
	try {
		return await chromium.launch({ ...(channel ? { channel } : {}), headless: true, ...opts });
	} catch (e) {
		if (!channel) throw e;
		console.warn(`  [browser] ${channel} not found - using Playwright's Chromium instead`);
		return chromium.launch({ headless: true, ...opts });
	}
}

export async function launch() {
	const browser = await launchBrowser({ args: ['--no-sandbox', '--disable-gpu'] });

	// Any init script the site needs to get past a gate/overlay is applied to
	// every context, so screenshots show the page rather than the interstitial.
	const conf = cfg();
	const orig = browser.newContext.bind(browser);

	// Some hosts challenge the FIRST request from a new browser context and
	// answer it with a bare 403, then serve every later request normally
	// (Hostinger's CDN on imperiare.com does exactly this). Every tool here
	// makes a fresh context per breakpoint, so without this each one reports a
	// site-wide outage that does not exist.
	//
	// Retries are logged rather than swallowed: a genuine 403 must not be
	// hidden. Set "navRetries": 0 in config.json to turn this off.
	const retries = conf.navRetries === undefined ? 2 : Number(conf.navRetries);
	const RETRYABLE = new Set([403, 429, 503]);

	browser.newContext = async (opts) => {
		const ctx = await orig(opts);

		// Age gates and "confirm you are a professional" splashes usually record
		// consent in a COOKIE, not localStorage (alphawolflab.us uses
		// acg_verified=1). Seeding it means every screenshot shows the page
		// instead of the interstitial, and the audit measures real content --
		// otherwise every gated page reports as THIN and looks like a defect.
		//
		//   "cookieSeed": { "acg_verified": "1" }
		//
		const cookieSeed = Object.entries(conf.cookieSeed || {});

		if (cookieSeed.length) {
			const { hostname } = new URL(conf.baseUrl);

			await ctx.addCookies(
				cookieSeed.map(([name, value]) => ({
					name,
					value: String(value),
					domain: hostname,
					path: '/',
				}))
			);
		}

		for (const [key, value] of Object.entries(conf.localStorageSeed || {})) {
			await ctx.addInitScript(
				([k, v]) => {
					try {
						localStorage.setItem(k, v);
					} catch {
						/* private mode */
					}
				},
				[key, value]
			);
		}

		if (retries > 0) {
			const newPage = ctx.newPage.bind(ctx);

			ctx.newPage = async (...pageArgs) => {
				const page = await newPage(...pageArgs);
				const goto = page.goto.bind(page);

				page.navRetries = 0;

				page.goto = async (target, options) => {
					let res = await goto(target, options);

					for (let i = 0; i < retries; i++) {
						if (!res || !RETRYABLE.has(res.status())) break;
						// Hostinger's hcdn now serves its browser check with a 403. Reloading it is another
						// hit that keeps the IP challenged - wait it out below instead.
						const isCheck = await page
							.evaluate(() => /Checking your browser before accessing|Just a moment/i.test(document.title + ' ' + (document.body ? document.body.innerText.slice(0, 300) : '')))
							.catch(() => false);
						if (isCheck) break;
						page.navRetries++;
						console.warn(`  [retry ${i + 1}/${retries}] ${res.status()} on ${target}`);
						await page.waitForTimeout(900);
						res = await goto(target, options);
					}

					// Hostinger's hcdn answers the first page of a fresh context with a 200
					// "Checking your browser before accessing ..." JS challenge that reloads
					// into the real page after ~4 s (nexxuspeptide.eu). Measuring it reports an
					// empty site. Wait it out; the hcdn cookie it sets covers the whole context.
					const challenged = () =>
						page
							.evaluate(() => /Checking your browser before accessing|Just a moment/i.test(document.title + ' ' + (document.body ? document.body.innerText.slice(0, 300) : '')))
							.catch(() => true);
					if (await challenged()) {
						for (let s = 0; s < 20 && (await challenged()); s++) await page.waitForTimeout(1000);
						await page.waitForLoadState('domcontentloaded').catch(() => {});
						await page.waitForTimeout(800);
						if (await challenged()) console.warn(`  [hcdn] still on the browser check after 20 s: ${target}`);
					}

					return res;
				};

				return page;
			};
		}

		return ctx;
	};

	return browser;
}

/**
 * Trigger "delay JavaScript execution" optimisers.
 *
 * WP Rocket (and LiteSpeed, Perfmatters, FlyingPress) hold every deferred script
 * back until the visitor moves the mouse, scrolls, touches or presses a key. A
 * headless run does none of those, so Elementor's animation JS never boots and
 * every widget carrying an entrance animation keeps the `.elementor-invisible`
 * class it ships with - `visibility:hidden`, but still occupying its full
 * height. The page then screenshots as correctly-spaced voids, which reads
 * exactly like a real layout bug and is not one.
 *
 * On greysonprivate this was 26 invisible widgets and ~2000px of apparently
 * empty page. After this call: 0. See docs/GOTCHAS.md.
 */
export async function wake(page) {
	// The optimiser only releases its scripts on a genuine input event.
	await page.mouse.move(120, 160);
	await page.mouse.move(640, 420);
	await page.mouse.wheel(0, 100);
	await page.keyboard.press('Shift');
	await page.waitForTimeout(900);

	// Elementor reveals a widget when it scrolls into view, so walk the page.
	// Dwell long enough for the observer to fire - a fast scroll outruns it and
	// leaves widgets behind (26 -> 16 rather than 26 -> 0 when this was 110ms).
	await page.evaluate(async () => {
		const step = Math.round(window.innerHeight * 0.5);
		for (let y = 0; y < document.body.scrollHeight; y += step) {
			window.scrollTo(0, y);
			await new Promise((r) => setTimeout(r, 260));
		}
		window.scrollTo(0, 0);
	});
	await page.waitForTimeout(700);

	// Whatever is still hidden gets put into its finished state by hand. The
	// resting layout after every animation has run is what we are measuring;
	// leaving stragglers hidden makes them invisible to the overflow and image
	// checks and silently understates the page. Returns how many needed forcing
	// - a non-zero count is normal, not a finding.
	return page.evaluate(() => {
		const left = document.querySelectorAll('.elementor-invisible');
		left.forEach((el) => {
			el.classList.remove('elementor-invisible');
			el.style.visibility = 'visible';
			el.style.opacity = '1';
		});
		return left.length;
	});
}

/**
 * A page ready to inspect.
 *
 * Deliberately `domcontentloaded`, never `networkidle` — live-chat widgets hold
 * a socket open forever and networkidle would never resolve. See docs/GOTCHAS.
 */
export async function open(browser, target, { width = 1440, height = 900, settle = 700 } = {}) {
	const ctx = await browser.newContext({
		viewport: { width, height },
		isMobile: width < 700,
		hasTouch: width < 700,
		deviceScaleFactor: 1,
		ignoreHTTPSErrors: true,
	});

	const page = await ctx.newPage();
	const errors = [];

	page.on('pageerror', (e) => errors.push(String(e.message)));
	page.on('console', (m) => {
		if (m.type() === 'error') errors.push(m.text());
	});

	await page.goto(url(target), { waitUntil: 'domcontentloaded', timeout: 60000 });
	await page.waitForTimeout(settle);
	await wake(page);

	page.collectedErrors = errors;
	return { ctx, page, errors };
}

/** Log in to wp-admin and keep the session on the context. */
export async function login(page, conf = cfg()) {
	await page.goto(url('/wp-login.php', conf), { waitUntil: 'domcontentloaded', timeout: 60000 });

	if (!(await page.locator('#user_login').count())) return false;

	// Up to three passes: Jetpack Protect answers a correct login with a maths
	// captcha and the message "Once you solve it, you will need to log in again",
	// so the credentials have to be submitted a second time after solving. A
	// single fill-and-click silently lands back on wp-login.php with no error box,
	// which reads like a wrong password and is not one.
	for (let attempt = 0; attempt < 3; attempt++) {
		if (await page.locator('#user_login').count()) {
			await page.fill('#user_login', conf.user);
			await page.fill('#user_pass', conf.pass);
		}

		const mathField = page.locator('input[name="jetpack_protect_num"]');
		if (await mathField.count()) {
			const question = await page.evaluate(() => document.body.innerText);
			const m = question.match(/(\d+)\s*([+\-*x×])\s*(\d+)\s*=/);
			if (m) {
				const [, a, op, b] = m;
				const x = Number(a);
				const y = Number(b);
				const answer = op === '+' ? x + y : op === '-' ? x - y : x * y;
				await mathField.fill(String(answer));
			}
		}

		const submit = page.locator('#wp-submit');
		if (!(await submit.count())) break;
		await submit.click();
		await page.waitForLoadState('domcontentloaded').catch(() => {});
		await page.waitForTimeout(1200);

		if (!(await page.locator('#user_login').count()) && !(await page.locator('input[name="jetpack_protect_num"]').count())) {
			return true;
		}
	}

	return !(await page.locator('#user_login').count());
}

export function ensureShots() {
	const dir = path.join(ROOT, 'shots');
	fs.mkdirSync(dir, { recursive: true });
	return dir;
}
