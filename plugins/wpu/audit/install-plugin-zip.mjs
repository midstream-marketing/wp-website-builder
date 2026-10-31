// Install (or update) any plugin zip through wp-admin's own uploader, then make sure it is active.
// For hosts that refuse PHP-created .php files (WP Engine): the uploader is the one route they allow.
// An already-installed plugin is replaced via WordPress's "Replace current with uploaded" step.
//
//   node audit/install-plugin-zip.mjs remote/cas-store.zip cas-store/cas-store.php
import path from 'node:path';
import fs from 'node:fs';
import { launch, cfg, url, ROOT } from '../lib/lib.mjs';

const [zipArg, want] = process.argv.slice(2);
if (!zipArg || !want) { console.error('usage: node audit/install-plugin-zip.mjs <zip> <folder/main.php>'); process.exit(2); }
const zip = path.resolve(process.cwd(), zipArg);
if (!fs.existsSync(zip)) { console.error(`missing ${zip}`); process.exit(2); }
const conf = cfg();

const browser = await launch();
const page = await (await browser.newContext({ viewport: { width: 1500, height: 950 }, ignoreHTTPSErrors: true })).newPage();

// log in (the first hit on wp-login.php can be answered 403 by a WAF - retry)
let formUp = false;
for (let i = 1; i <= 4 && !formUp; i++) {
	await page.goto(url('/wp-login.php'), { waitUntil: 'domcontentloaded', timeout: 60000 });
	await page.waitForTimeout(800);
	formUp = (await page.locator('#user_login').count()) > 0;
}
if (!formUp) { console.error('login form never appeared'); await browser.close(); process.exit(1); }
await page.fill('#user_login', conf.user);
await page.fill('#user_pass', conf.pass);
await Promise.all([page.waitForLoadState('domcontentloaded').catch(() => {}), page.click('#wp-submit')]);
await page.waitForSelector('#wpadminbar', { timeout: 30000 }).catch(() => {});
if (!(await page.locator('#wpadminbar, body.wp-admin').count())) { console.error('LOGIN FAILED'); await browser.close(); process.exit(1); }
console.log('logged in');

// upload
await page.goto(url('/wp-admin/plugin-install.php?tab=upload'), { waitUntil: 'domcontentloaded', timeout: 60000 });
await page.waitForTimeout(700);
await page.setInputFiles('#pluginzip', zip);
await Promise.all([page.waitForLoadState('domcontentloaded').catch(() => {}), page.click('#install-plugin-submit')]);
await page.waitForTimeout(5000);

// already installed -> WordPress shows a comparison with "Replace current with uploaded"
const replace = page.locator('a.update-from-upload-overwrite, a:has-text("Replace current with uploaded")').first();
if (await replace.count()) {
	console.log('plugin exists - replacing with the uploaded version');
	await Promise.all([page.waitForLoadState('domcontentloaded').catch(() => {}), replace.click()]);
	await page.waitForTimeout(5000);
}
const said = (await page.locator('.wrap').first().innerText().catch(() => '')).replace(/\s+/g, ' ');
console.log('installer:', said.slice(0, 260));
if (/error|failed|could not/i.test(said) && !/successfully/i.test(said)) {
	await page.screenshot({ path: path.join(ROOT, 'shots', 'plugin-install-error.png'), fullPage: true });
}

// activate if needed
await page.goto(url('/wp-admin/plugins.php'), { waitUntil: 'domcontentloaded', timeout: 60000 });
await page.waitForTimeout(900);
const row = page.locator(`tr[data-plugin="${want}"]`).first();
if (!(await row.count())) { console.error(`no plugin row for ${want}`); await browser.close(); process.exit(1); }
if (/\binactive\b/.test((await row.getAttribute('class')) || '')) {
	const link = row.locator('span.activate a').first();
	await Promise.all([page.waitForLoadState('domcontentloaded').catch(() => {}), link.click()]);
	await page.waitForTimeout(2500);
	console.log('activated');
}
await page.goto(url('/wp-admin/plugins.php'), { waitUntil: 'domcontentloaded', timeout: 60000 });
const final = await page.locator(`tr[data-plugin="${want}"]`).first().evaluate((tr) => ({ cls: tr.className, text: tr.innerText.replace(/\s+/g, ' ').slice(0, 140) })).catch(() => null);
const fatal = (await page.locator('.notice-error, #message.error').allInnerTexts().catch(() => [])).join(' | ');
console.log('final:', JSON.stringify(final));
if (fatal) console.log('admin notice:', fatal.slice(0, 300));
await browser.close();
process.exit(final && /\bactive\b/.test(final.cls) && !/\binactive\b/.test(final.cls) ? 0 : 1);
