// Every font a page ASKS for that never LOADS.
//
//   node audit/fonts.mjs                 all configured URLs, desktop + phone
//   node audit/fonts.mjs / /shop/        specific pages
//
// Why this exists: theme and widget CSS routinely name a font ("Quicksand",
// "Nunito") that nothing enqueues. The browser silently falls back to its
// default serif - Times - and the page "looks off" without any error anywhere.
// document.fonts.check() does NOT catch it: it returns true for a family that
// was never declared at all. This checks the loaded FontFace set instead.
//
// Fix for anything reported: add the family as a global font in the Elementor
// kit (build/apply-plan.php "kit.fonts"), so Elementor hosts and loads it.
import { launch, cfg, urls, url, wake } from '../lib/lib.mjs';

const conf = cfg();
const only = process.argv.slice(2);
const targets = only.length ? only.map((u) => url(u, conf)) : urls(conf);

const browser = await launch();
const missing = new Map();
const used = new Map();

for (const [label, vp] of [['desktop', { width: 1440, height: 900 }], ['phone', { width: 390, height: 844 }]]) {
	const ctx = await browser.newContext({ viewport: vp, isMobile: vp.width < 700, hasTouch: vp.width < 700, ignoreHTTPSErrors: true });
	const page = await ctx.newPage();

	for (const target of targets) {
		try {
			await page.goto(target, { waitUntil: 'domcontentloaded', timeout: 60000 });
			await page.waitForTimeout(900);
			await wake(page);
			await page.evaluate(() => document.fonts.ready);
		} catch (e) {
			console.log(`  LOAD FAIL ${target}: ${e.message.split('\n')[0]}`);
			continue;
		}

		const found = await page.evaluate(() => {
			const loaded = new Set([...document.fonts].filter((f) => f.status === 'loaded').map((f) => f.family.replace(/["']/g, '')));
			const generic = /^(serif|sans-serif|monospace|cursive|fantasy|system-ui|ui-sans-serif|ui-serif|inherit|initial|-apple-system|BlinkMacSystemFont)$/i;
			const system = /^(Arial|Helvetica|Helvetica Neue|Segoe UI|Times New Roman|Times|Georgia|Verdana|Tahoma|Courier New|Apple Color Emoji|Segoe UI Emoji)$/i;
			const icon = /awesome|icon|eicons|auxin-front|simple-line|dashicons|Woo-Side-Cart|star|slick|swiper/i;
			const out = {};
			for (const el of document.querySelectorAll('body *')) {
				if (!el.offsetParent) continue;
				if (![...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim().length > 1)) continue;
				const first = getComputedStyle(el).fontFamily.split(',')[0].trim().replace(/["']/g, '');
				if (!first || generic.test(first) || icon.test(first)) continue;
				const ok = loaded.has(first) || system.test(first);
				const key = `${first}|${ok ? 1 : 0}`;
				if (!out[key]) {
					const cls = (el.className || '').toString().trim().split(/\s+/)[0];
					out[key] = { n: 0, sample: `${el.tagName.toLowerCase()}${cls ? '.' + cls : ''} "${el.textContent.trim().slice(0, 30)}"`, weight: getComputedStyle(el).fontWeight };
				}
				out[key].n++;
			}
			return out;
		});

		for (const [key, v] of Object.entries(found)) {
			const [fam, ok] = key.split('|');
			used.set(fam, (used.get(fam) || 0) + v.n);
			if (ok === '0') {
				if (!missing.has(fam)) missing.set(fam, []);
				missing.get(fam).push(`${label} ${target.replace(conf.baseUrl, '') || '/'}  x${v.n}  w${v.weight}  e.g. ${v.sample}`);
			}
		}
	}
	await ctx.close();
}

await browser.close();

console.log('\nfonts in use (text elements): ' + [...used].sort((a, b) => b[1] - a[1]).map(([f, n]) => `${f}=${n}`).join(' | '));

if (!missing.size) {
	console.log('\nPASS - every font the pages ask for is loaded.\n');
	process.exit(0);
}

console.log('\nNOT LOADED (text falls back to the browser default):');
for (const [fam, where] of missing) {
	console.log(`\n  ${fam}  (${where.length} page view${where.length === 1 ? '' : 's'})`);
	where.slice(0, 6).forEach((w) => console.log(`     ${w}`));
}
console.log('\nFix: add each family under "kit" -> "fonts" in the plan and re-run scripts/rplan.ps1.\n');
process.exit(1);
