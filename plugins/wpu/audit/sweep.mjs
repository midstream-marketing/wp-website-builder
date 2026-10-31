// Screenshot every configured page at every breakpoint, for review.
//
//   node audit/sweep.mjs                  all urls x all breakpoints, viewport shots
//   node audit/sweep.mjs full             full-page shots instead
//   node audit/sweep.mjs full / /about/   just these pages
//
// Output: shots/sweep/<page>-<width>.png, plus an index of every file written.
// This is the "look at it" step of a build: after each phase, open the shots and
// check them against the design before moving on. It does not judge anything -
// audit/audit.mjs does the pass/fail checks.
import fs from 'node:fs';
import path from 'node:path';
import { launch, cfg, urls, url, ensureShots, wake } from '../lib/lib.mjs';

const conf = cfg();
const argv = process.argv.slice(2);
const full = argv[0] === 'full';
const only = full ? argv.slice(1) : argv;
const targets = only.length ? only.map((u) => url(u, conf)) : urls(conf);
const widths = conf.breakpoints || [390, 768, 1440];

const dir = path.join(ensureShots(), 'sweep');
fs.mkdirSync(dir, { recursive: true });

const slug = (u) => (new URL(u).pathname.split('/').filter(Boolean).join('-') || 'home').slice(0, 60);

const browser = await launch();
const written = [];

for (const w of widths) {
	const ctx = await browser.newContext({ viewport: { width: w, height: 900 }, isMobile: w < 700, hasTouch: w < 700, ignoreHTTPSErrors: true });
	const page = await ctx.newPage();

	for (const target of targets) {
		const file = path.join(dir, `${slug(target)}-${w}.png`);
		try {
			await page.goto(target, { waitUntil: 'domcontentloaded', timeout: 60000 });
			await page.waitForTimeout(900);
			await wake(page);
			await page.screenshot({ path: file, fullPage: full });
			written.push(path.relative(process.cwd(), file));
			console.log(`  ${String(w).padStart(4)}px  ${target}`);
		} catch (e) {
			console.log(`  FAIL ${w}px ${target}: ${e.message.split('\n')[0]}`);
		}
	}
	await ctx.close();
}

await browser.close();
console.log(`\n${written.length} screenshot(s) in ${path.relative(process.cwd(), dir)}\n`);
