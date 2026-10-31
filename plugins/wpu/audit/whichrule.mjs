// Which CSS rules declare a given property for an element, in order. Read-only.
//   node audit/whichrule.mjs <path> <selector> <property>
import { launch, url, wake } from '../lib/lib.mjs';
const [target = '/', sel = 'body', prop = 'width'] = process.argv.slice(2);
const browser = await launch();
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, ignoreHTTPSErrors: true });
const page = await ctx.newPage();
await page.goto(url(target), { waitUntil: 'domcontentloaded', timeout: 60000 });
await page.waitForTimeout(1500);
await wake(page);
await page.mouse.move(2, 2);
const out = await page.evaluate(([s, p]) => {
	const el = document.querySelector(s);
	if (!el) return ['element not found'];
	const hits = [];
	const scan = (rules, media) => {
		for (const r of rules) {
			if (r.type === CSSRule.MEDIA_RULE) {
				const applies = window.matchMedia(r.conditionText).matches;
				scan(r.cssRules, `@media ${r.conditionText} [${applies ? 'applies' : 'no'}]`);
			} else if (r.selectorText && r.style && r.style.getPropertyValue(p)) {
				try {
					if (el.matches(r.selectorText)) {
						hits.push(`${media ? media + ' ' : ''}${r.selectorText} { ${p}: ${r.style.getPropertyValue(p)}${r.style.getPropertyPriority(p) ? ' !important' : ''} }`);
					}
				} catch (e) { /* unsupported selector */ }
			}
		}
	};
	for (const sheet of document.styleSheets) {
		try { scan(sheet.cssRules, ''); } catch (e) { hits.push(`(cannot read ${sheet.href})`); }
	}
	hits.push(`COMPUTED ${p} = ${getComputedStyle(el)[p]}  inline="${el.getAttribute('style') || ''}" attr=${el.getAttribute(p) || '-'}`);
	return hits;
}, [sel, prop]);
out.forEach((l) => console.log(l));
await browser.close();
