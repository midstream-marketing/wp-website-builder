// Response timing and payload weight.
//
// Runs each URL three times and reports the median — the first request after
// any plugin or theme change is a cold start and can be 30x slower than steady
// state. Reporting that first number as "the site is slow" is a false alarm.
//
//   node audit/perf.mjs            all configured URLs
//   node audit/perf.mjs / /shop/   specific ones
import { launch, cfg, urls, url } from '../lib/lib.mjs';

const conf = cfg();
const rest = process.argv.slice(2);
const targets = rest.length ? rest.map((u) => url(u, conf)) : urls(conf);

const browser = await launch();
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, ignoreHTTPSErrors: true });

console.log('page                                              median   requests   transferred');
console.log('-'.repeat(86));

for (const target of targets) {
	const runs = [];
	let requests = 0;
	let bytes = 0;

	for (let i = 0; i < 3; i++) {
		const page = await ctx.newPage();

		if (i === 2) {
			// Only instrument the last run — listeners add measurable overhead.
			page.on('request', () => requests++);
			page.on('response', async (res) => {
				const len = res.headers()['content-length'];
				if (len) bytes += parseInt(len, 10) || 0;
			});
		}

		const t0 = Date.now();
		try {
			await page.goto(target, { waitUntil: 'domcontentloaded', timeout: 90000 });
			runs.push(Date.now() - t0);
		} catch {
			runs.push(NaN);
		}

		await page.waitForTimeout(300);
		await page.close();
	}

	const valid = runs.filter((n) => !Number.isNaN(n)).sort((a, b) => a - b);
	const median = valid.length ? valid[Math.floor(valid.length / 2)] : NaN;
	const short = target.replace(conf.baseUrl, '') || '/';

	console.log(
		`${short.padEnd(48).slice(0, 48)}  ${String(median).padStart(6)}ms  ${String(requests).padStart(7)}   ${(bytes / 1024).toFixed(0).padStart(8)} KB`
	);

	if (runs[0] > median * 3) {
		console.log(`      note: first run ${runs[0]}ms — cold start, not representative`);
	}
}

await browser.close();
