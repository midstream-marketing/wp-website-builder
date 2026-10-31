// The full sweep. Run at the start and end of every session.
//
//   node audit/audit.mjs              all configured URLs, all breakpoints
//   node audit/audit.mjs /cart/       just one page
//
// Checks per page: HTTP status, horizontal scroll at every breakpoint, broken
// images, JS console errors, missing page title, and empty content.
import { launch, cfg, urls, url, ensureShots, wake } from '../lib/lib.mjs';

const conf = cfg();
const only = process.argv.slice(2);
const targets = only.length ? only.map((u) => url(u, conf)) : urls(conf);
const widths = conf.breakpoints || [390, 768, 1440];

ensureShots();

const browser = await launch();
const problems = [];
const notes = [];

function report(page, kind, detail) {
	problems.push({ page, kind, detail });
}

/* ---------------- status + content + images + JS errors ---------------- */

console.log(`\n=== Pages (${targets.length}) ===`);

for (const target of targets) {
	const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, ignoreHTTPSErrors: true });
	const page = await ctx.newPage();
	const jsErrors = [];

	page.on('pageerror', (e) => jsErrors.push(String(e.message)));
	page.on('console', (m) => {
		if (m.type() === 'error') jsErrors.push(m.text());
	});
	// "Failed to load resource: 404" never says WHICH file - record the URL of every failed sub-request.
	page.on('response', (r) => {
		if (r.status() >= 400 && r.url() !== target) jsErrors.push(`HTTP ${r.status()} ${r.url()}`);
	});

	let status = 0;

	try {
		const res = await page.goto(target, { waitUntil: 'domcontentloaded', timeout: 60000 });
		status = res ? res.status() : 0;
		await page.waitForTimeout(900);
		// Fire delayed JS so entrance-animated widgets are actually visible;
		// without this the overflow and image checks below skip them.
		await wake(page);
	} catch (e) {
		report(target, 'LOAD', e.message.split('\n')[0]);
		await ctx.close();
		console.log(`  FAIL  ${target}`);
		continue;
	}

	if (status !== 200) report(target, 'STATUS', String(status));

	// Lazy-loading has to be resolved BEFORE the image check, or it reports phantom failures.
	//
	// LiteSpeed (and WP core's loading="lazy") leave an untriggered image holding a tiny placeholder
	// in src. That placeholder IS complete, so `complete && naturalWidth === 0` is false for some and
	// true for others depending purely on scroll timing. This reported five broken images on a shop
	// page whose files all served HTTP 200 as valid WebP. Swap data-src in, then wait for real
	// decodes, and only then decide what is broken.
	await page.evaluate(() => {
		for (const i of document.querySelectorAll('img[data-src], img[data-lazyloaded]')) {
			const real = i.getAttribute('data-src');
			if (real) i.setAttribute('src', real);
			const set = i.getAttribute('data-srcset');
			// srcset beats src: overriding src while a placeholder srcset remains keeps the
			// placeholder on screen, which reads as a blank or broken image.
			if (set) i.setAttribute('srcset', set);
			else if (real) i.removeAttribute('srcset');
			i.removeAttribute('loading');
		}
	});
	await page
		.waitForFunction(() => [...document.images].every((i) => i.complete), null, { timeout: 30000 })
		.catch(() => {});

	const info = await page.evaluate(() => {
		const broken = [...document.images]
			.filter((i) => i.complete && i.naturalWidth === 0 && i.currentSrc)
			.map((i) => i.currentSrc.split('/').pop())
			.slice(0, 8);

		// One selector per query, in priority order.
		//
		// A comma-separated querySelector returns the first match in DOCUMENT
		// order, not selector order. On an archive whose theme emits no <main>,
		// 'main, .site-main, #main, article' therefore matched the first
		// <article> -- a single result card -- and the thin-content check
		// measured that one card instead of the whole listing, reporting a full
		// page of results as 108 chars of content.
		let main = null;

		for (const sel of ['main', '.site-main', '#main']) {
			main = document.querySelector(sel);
			if (main) break;
		}

		// <article> is a last resort, and only when there is exactly one.
		//
		// On an archive every result card is its own <article>, so falling back
		// to the first one measures a single card and reports a full listing as
		// thin. alphawolflab.us/coa/ emits no <main> at all and 36 article cards:
		// that read as 108 chars of content against 5,509 in the body.
		if (!main) {
			const articles = document.querySelectorAll('article');
			if (articles.length === 1) main = articles[0];
		}

		// A cart with nothing in it, or a search with no results, is short by
		// design — that is a state, not a defect. Detect it so the thin-content
		// check does not cry wolf on every run.
		const emptyState = !!document.querySelector(
			'.cart-empty, .wc-empty-cart-message, .woocommerce-info, .no-results, .woocommerce-no-products-found'
		);

		return {
			title: document.title,
			broken,
			emptyState,
			textLength: (main ? main.innerText : document.body.innerText).trim().length,
			// A common page-builder failure: the container renders but is empty.
			emptyBuilderSections: document.querySelectorAll(
				'.elementor-section:empty, .elementor-widget:empty, .elementor-container:empty'
			).length,
		};
	});

	if (info.broken.length) report(target, 'BROKEN IMG', info.broken.join(', '));
	if (!info.title || /^\s*$/.test(info.title)) report(target, 'NO TITLE', '(empty <title>)');
	if (info.emptyBuilderSections) report(target, 'EMPTY SECTIONS', `${info.emptyBuilderSections} (dead widgets?)`);

	if (info.textLength < 120) {
		if (info.emptyState) {
			notes.push(`${target} — short, but it is showing an empty/no-results state (fine)`);
		} else {
			report(target, 'THIN', `${info.textLength} chars of visible text`);
		}
	}

	// Ignore noise from third-party widgets we cannot fix.
	const ours = jsErrors.filter((e) => !/tidio|intercom|crisp|hotjar|gtag|facebook/i.test(e));
	if (ours.length) report(target, 'JS ERROR', ours.slice(0, 3).join(' | '));

	const flag = problems.some((p) => p.page === target) ? 'ISSUES' : 'ok    ';
	console.log(`  ${flag}  ${status}  ${target}`);

	await ctx.close();
}

/* ---------------- horizontal scroll matrix ---------------- */

console.log(`\n=== Horizontal scroll (${widths.join(' / ')}) ===`);

for (const w of widths) {
	const ctx = await browser.newContext({
		viewport: { width: w, height: 900 },
		isMobile: w < 700,
		hasTouch: w < 700,
		ignoreHTTPSErrors: true,
	});
	const page = await ctx.newPage();
	let bad = 0;

	for (const target of targets) {
		try {
			await page.goto(target, { waitUntil: 'domcontentloaded', timeout: 60000 });
			await page.waitForTimeout(400);

			const measure = () =>
				page.evaluate(
					() => document.documentElement.scrollWidth - document.documentElement.clientWidth
				);

			// Before and after the deferred scripts run. On a site with "delay
			// JavaScript execution" the first reading catches widgets that are
			// still in their pre-init position - Elementor's mobile dropdown menu
			// sits off-canvas to the right until its JS hides it, which reads as
			// a 330px overflow that no visitor who has touched the screen ever
			// sees. Reporting only the settled figure as a defect keeps that out
			// of the results, and the pre-boot figure is reported separately so a
			// genuine flash of sideways scroll is still visible.
			const before = await measure();
			await wake(page);
			const diff = await measure();

			if (diff > 1) {
				report(target, 'H-SCROLL', `+${diff}px at ${w}`);
				bad++;
			} else if (before > 1) {
				report(target, 'H-SCROLL-PREBOOT', `+${before}px at ${w} before deferred JS runs (settles to 0)`);
			}
		} catch {
			/* already reported above */
		}
	}

	console.log(`  ${w.toString().padStart(4)}px  ${bad ? `${bad} page(s) scroll sideways` : 'clean'}`);
	await ctx.close();
}

await browser.close();

/* ---------------- verdict ---------------- */

console.log('\n=== Result ===');

if (notes.length) {
	console.log('\nnotes (not failures):');
	for (const n of notes) console.log(`   ${n}`);
}

if (!problems.length) {
	console.log(`\nPASS — ${targets.length} pages, ${widths.length} breakpoints, nothing found.\n`);
	process.exit(0);
}

const byPage = new Map();
for (const p of problems) {
	if (!byPage.has(p.page)) byPage.set(p.page, []);
	byPage.get(p.page).push(p);
}

for (const [page, list] of byPage) {
	console.log(`\n${page}`);
	for (const p of list) console.log(`   ${p.kind.padEnd(15)} ${p.detail}`);
}

console.log(`\nFAIL — ${problems.length} issue(s) across ${byPage.size} page(s).\n`);
process.exit(1);
