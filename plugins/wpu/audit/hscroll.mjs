// Does the document actually scroll sideways?
//
// Per-element overflow reports are noisy — marquees and carousels are meant to
// be wider than the screen and are clipped by an ancestor. This checks the one
// thing a visitor can actually feel.
//
//   node audit/hscroll.mjs 390                 all configured URLs
//   node audit/hscroll.mjs 390 /cart/ /shop/   specific ones
import { launch, cfg, urls, url, wake } from '../lib/lib.mjs';

const conf = cfg();
const [w = '390', ...rest] = process.argv.slice(2);
const targets = rest.length ? rest.map((u) => url(u, conf)) : urls(conf);

const browser = await launch();
let failures = 0;

for (const target of targets) {
	const ctx = await browser.newContext({
		viewport: { width: +w, height: 800 },
		isMobile: +w < 700,
		hasTouch: +w < 700,
		ignoreHTTPSErrors: true,
	});
	const page = await ctx.newPage();

	try {
		await page.goto(target, { waitUntil: 'domcontentloaded', timeout: 60000 });
		await page.waitForTimeout(400);
	await wake(page);

		const r = await page.evaluate(() => ({
			scroll: document.documentElement.scrollWidth,
			client: document.documentElement.clientWidth,
		}));

		const diff = r.scroll - r.client;
		if (diff > 1) failures++;
		console.log(`${diff > 1 ? 'SCROLLS +' + String(diff).padEnd(4) : 'ok        '} @${w}  ${target}`);
	} catch (e) {
		failures++;
		console.log(`ERROR      @${w}  ${target}  ${e.message.split('\n')[0]}`);
	}

	await ctx.close();
}

await browser.close();
process.exit(failures ? 1 : 0);
