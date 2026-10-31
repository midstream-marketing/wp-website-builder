// Install and activate the WP Site Build Bridge through wp-admin.
//
// Why this rather than a file-manager upload: dropping the .zip into
// wp-content/plugins/ does nothing — WordPress only scans for PHP files with a
// plugin header, directly in plugins/ or one directory deep. A zip sitting
// there is invisible, which is the "plugin not found" you get. WordPress's own
// uploader unpacks it to the right shape.
//
//   node audit/install-bridge.mjs            # install + activate
//   node audit/install-bridge.mjs --dry      # log in and report state only
import path from 'node:path';
import fs from 'node:fs';
import { launch, cfg, url, ROOT, WORKSPACE } from '../lib/lib.mjs';

const dry = process.argv.includes('--dry');
const conf = cfg();
const zip = path.join(WORKSPACE, 'dist', 'wpu-bridge.zip'); // made by scripts/build-bridge.ps1

if (!fs.existsSync(zip)) {
	console.error(`missing ${zip} — run: powershell -File scripts/build-bridge.ps1`);
	process.exit(2);
}

const browser = await launch();
const ctx = await browser.newContext({ viewport: { width: 1500, height: 950 }, ignoreHTTPSErrors: true });
const page = await ctx.newPage();

// ---------------------------------------------------------------- log in --

// This host's WAF answers the FIRST hit on wp-login.php with a 403 and an empty
// body. A retry gets a 200 and the real form. Without this the script sees no
// #user_login, silently skips the login and reports a failure that never
// happened.
let formUp = false;

for (let attempt = 1; attempt <= 4 && !formUp; attempt++) {
	const res = await page.goto(url('/wp-login.php'), { waitUntil: 'domcontentloaded', timeout: 60000 });
	await page.waitForTimeout(900);
	formUp = (await page.locator('#user_login').count()) > 0;
	console.log(`login page attempt ${attempt}: HTTP ${res ? res.status() : '?'}, form ${formUp ? 'present' : 'ABSENT'}`);
}

if (!formUp) {
	console.error('login form never appeared — the host is blocking automated requests');
	await page.screenshot({ path: path.join(ROOT, 'shots', 'bridge-login-blocked.png') });
	await browser.close();
	process.exit(1);
}

if (await page.locator('#user_login').count()) {
	await page.fill('#user_login', conf.user);
	await page.fill('#user_pass', conf.pass);
	await Promise.all([
		page.waitForLoadState('domcontentloaded').catch(() => {}),
		page.click('#wp-submit'),
	]);
	// Wait for the admin bar rather than a fixed delay. A managed host with a
	// heavy plugin set (WP Engine, 31 plugins) takes well over 1.5s to paint the
	// dashboard, and the old fixed wait reported "LOGIN FAILED" against a session
	// that had in fact logged in perfectly — the screenshot showed the dashboard.
	await page.waitForSelector('#wpadminbar', { timeout: 30000 }).catch(() => {});
	await page.waitForTimeout(500);
}

const loggedIn = await page.locator('#wpadminbar, body.wp-admin').count();
console.log('logged in:', loggedIn > 0, '->', page.url());

if (!loggedIn) {
	const err = await page.locator('#login_error').innerText().catch(() => '');
	console.error('LOGIN FAILED', err ? '— ' + err.replace(/\s+/g, ' ') : '');
	await page.screenshot({ path: path.join(ROOT, 'shots', 'bridge-login-failed.png') });
	await browser.close();
	process.exit(1);
}

// ------------------------------------------------- already installed? ----

await page.goto(url('/wp-admin/plugins.php'), { waitUntil: 'domcontentloaded', timeout: 60000 });
await page.waitForTimeout(900);

// Match on the plugin FILE, not the slug. A copy extracted into a wrapper
// folder shows up with the same data-slug but a path like
// "wp-site-build/wp-site-build-bridge/wpsb-bridge.php" — nested a level too
// deep. Treating that as "already installed" is what made an earlier run skip
// the upload and do nothing.
const WANT = 'wpu-bridge/wpu-bridge.php';

const rows = await page.evaluate(() =>
	[...document.querySelectorAll('#the-list tr[data-plugin]')]
		.filter((tr) => /wpu-bridge\.php$/.test(tr.getAttribute('data-plugin')))
		.map((tr) => ({ plugin: tr.getAttribute('data-plugin'), cls: tr.className }))
);

console.log('bridge copies found on plugins.php:');
for (const r of rows) console.log(`   ${r.cls.padEnd(10)} ${r.plugin}${r.plugin === WANT ? '   <- correct location' : '   <- NESTED, wrong level'}`);

const present = rows.some((r) => r.plugin === WANT);
console.log('correctly-placed copy present:', present);

if (dry) {
	await page.screenshot({ path: path.join(ROOT, 'shots', 'bridge-plugins.png'), fullPage: true });
	console.log('dry run — nothing changed');
	await browser.close();
	process.exit(0);
}

// ------------------------------------------------------------- upload ----

if (!present) {
	await page.goto(url('/wp-admin/plugin-install.php?tab=upload'), { waitUntil: 'domcontentloaded', timeout: 60000 });
	await page.waitForTimeout(800);

	await page.setInputFiles('#pluginzip', zip);
	console.log('selected', path.basename(zip));

	await Promise.all([
		page.waitForLoadState('domcontentloaded').catch(() => {}),
		page.click('#install-plugin-submit'),
	]);
	// Unpacking on a slow host takes a moment.
	await page.waitForTimeout(6000);

	const body = (await page.locator('body').innerText().catch(() => '')).replace(/\s+/g, ' ');
	console.log('installer said:', body.slice(0, 400));

	await page.screenshot({ path: path.join(ROOT, 'shots', 'bridge-install.png'), fullPage: true });

	// "Plugin installed successfully" offers an Activate link right there.
	const activate = page.locator('a:has-text("Activate Plugin"), a.activate-now').first();
	if (await activate.count()) {
		await Promise.all([
			page.waitForLoadState('domcontentloaded').catch(() => {}),
			activate.click(),
		]);
		await page.waitForTimeout(2500);
		console.log('clicked Activate Plugin');
	}
}

// ----------------------------------------------------------- activate ----

await page.goto(url('/wp-admin/plugins.php'), { waitUntil: 'domcontentloaded', timeout: 60000 });
await page.waitForTimeout(1000);

const row = page.locator(`tr[data-plugin="${WANT}"]`).first();
if (await row.count()) {
	const cls = (await row.getAttribute('class')) || '';
	console.log('plugin row class:', cls);

	if (/\binactive\b/.test(cls)) {
		const link = row.locator('a:has-text("Activate")').first();
		if (await link.count()) {
			await Promise.all([
				page.waitForLoadState('domcontentloaded').catch(() => {}),
				link.click(),
			]);
			await page.waitForTimeout(2500);
			console.log('activated from plugins.php');
		}
	}
} else {
	console.log('WARNING: no bridge row found on plugins.php');
}

await page.goto(url('/wp-admin/plugins.php'), { waitUntil: 'domcontentloaded', timeout: 60000 });
await page.waitForTimeout(900);

const final = await page.evaluate((want) => {
	const tr = document.querySelector(`tr[data-plugin="${want}"]`);
	if (!tr) return null;
	return {
		plugin: tr.getAttribute('data-plugin'),
		cls: tr.className,
		text: tr.innerText.replace(/\s+/g, ' ').slice(0, 200),
	};
}, WANT);

console.log('\nFINAL PLUGIN ROW:', final ? JSON.stringify(final, null, 2) : 'NOT FOUND');
await page.screenshot({ path: path.join(ROOT, 'shots', 'bridge-final.png'), fullPage: true });

await browser.close();
