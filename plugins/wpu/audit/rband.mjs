// Viewport-sized bands, so each one is readable at full detail instead of
// being squashed into one enormous full-page image. Also reports every element
// wider than the viewport — use that to *locate* a culprit after hscroll.mjs
// has told you the page genuinely scrolls.
//
//   node audit/rband.mjs /catalog/ cat 390 780 8
import { launch, url, ensureShots, wake } from '../lib/lib.mjs';

const [target, prefix = 'band', w = '1440', bh = '900', count = '10'] = process.argv.slice(2);

if (!target) {
	console.error('usage: node audit/rband.mjs <url-or-path> <prefix> [width] [bandHeight] [count]');
	process.exit(2);
}

const dir = ensureShots();
const browser = await launch();
const ctx = await browser.newContext({
	viewport: { width: +w, height: +bh },
	isMobile: +w < 700,
	hasTouch: +w < 700,
	deviceScaleFactor: 1,
	ignoreHTTPSErrors: true,
});
const page = await ctx.newPage();

await page.goto(url(target), { waitUntil: 'domcontentloaded', timeout: 60000 });
await page.waitForTimeout(700);
await wake(page);

const over = await page.evaluate((vw) => {
	const bad = [];

	for (const el of document.querySelectorAll('body *')) {
		const r = el.getBoundingClientRect();
		if (r.width === 0 || r.height === 0) continue;

		const cs = getComputedStyle(el);
		if (cs.position === 'fixed' || cs.visibility === 'hidden' || cs.display === 'none') continue;

		// Skip-links live off-canvas by design.
		if (r.left < -2000) continue;

		if (r.right > vw + 2 || r.left < -2) {
			const cls = (el.className || '').toString().split(/\s+/).filter(Boolean).slice(0, 2).join('.');
			bad.push(`${el.tagName.toLowerCase()}${cls ? '.' + cls : ''}  [${Math.round(r.left)} → ${Math.round(r.right)}]`);
		}
	}

	return [...new Set(bad)].slice(0, 20);
}, +w);

console.log(over.length ? `elements past the viewport @${w}px:` : `nothing past the viewport @${w}px`);
for (const o of over) console.log('   ', o);

const total = await page.evaluate(() => document.body.scrollHeight);
console.log(`page height ${total}px`);

for (let i = 0; i < +count; i++) {
	const y = i * +bh;
	if (y > total) break;

	await page.evaluate((yy) => window.scrollTo(0, yy), y);
	await page.waitForTimeout(450);

	const name = `${prefix}-${String(i).padStart(2, '0')}.png`;
	await page.screenshot({ path: `${dir}/${name}` });
	console.log('->', name, `y=${y}`);
}

await browser.close();
