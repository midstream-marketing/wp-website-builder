// Why isn't my CSS applying? Measure, don't guess.
//
//   node audit/probe.mjs /my-account/ ".woocommerce-MyAccount-navigation"
//   node audit/probe.mjs / ".header" 1440
//
// Prints box geometry, the computed values that usually matter, the ancestor
// chain (with each ancestor's display/position), and every stylesheet rule
// that matches the element — so you can see which one is actually winning.
import { launch, url, wake } from '../lib/lib.mjs';

const [target, selector, width = '1440'] = process.argv.slice(2);

if (!target || !selector) {
	console.error('usage: node audit/probe.mjs <url-or-path> <selector> [width]');
	process.exit(2);
}

const browser = await launch();
const ctx = await browser.newContext({
	viewport: { width: +width, height: 900 },
	isMobile: +width < 700,
	ignoreHTTPSErrors: true,
});
const page = await ctx.newPage();

await page.goto(url(target), { waitUntil: 'domcontentloaded', timeout: 60000 });
await page.waitForTimeout(800);
	await wake(page);

const out = await page.evaluate((sel) => {
	const el = document.querySelector(sel);
	if (!el) return { error: `no element matches ${sel}` };

	const cs = getComputedStyle(el);
	const r = el.getBoundingClientRect();

	const interesting = [
		'display', 'position', 'float', 'order', 'zIndex', 'visibility', 'opacity',
		'width', 'maxWidth', 'height', 'maxHeight', 'overflow', 'overflowX',
		'gridTemplateColumns', 'gridColumn', 'gridRow', 'flexDirection',
		'margin', 'padding', 'border', 'borderRadius',
		'background', 'backgroundColor', 'backgroundImage', 'color',
		'fontSize', 'fontFamily', 'lineHeight', 'transform',
	];

	const computed = {};
	for (const k of interesting) {
		const v = cs[k];
		if (v && v !== 'none' && v !== 'normal' && v !== 'auto' && v !== '0px') computed[k] = v;
	}

	// Which rules actually match, and from which stylesheet.
	const rules = [];
	for (const sheet of document.styleSheets) {
		let list;
		try {
			list = sheet.cssRules;
		} catch {
			continue; // cross-origin
		}
		for (const rule of list) {
			if (!rule.selectorText) continue;
			try {
				if (!el.matches(rule.selectorText)) continue;
			} catch {
				continue;
			}
			rules.push({
				selector: rule.selectorText,
				from: (sheet.href || 'inline').split('/').slice(-1)[0].split('?')[0],
				css: rule.style.cssText.slice(0, 200),
			});
		}
	}

	const chain = [];
	let p = el.parentElement;
	while (p && p !== document.documentElement) {
		const pcs = getComputedStyle(p);
		chain.push(
			`${p.tagName.toLowerCase()}.${(p.className || '').toString().trim().split(/\s+/).slice(0, 3).join('.')}` +
				`  [display:${pcs.display} position:${pcs.position} overflow:${pcs.overflow}]`
		);
		p = p.parentElement;
	}

	return {
		tag: el.tagName.toLowerCase(),
		classes: (el.className || '').toString(),
		box: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
		computed,
		matchingRules: rules,
		ancestors: chain,
		siblings: [...(el.parentElement?.children || [])].map(
			(n) => `${n.tagName.toLowerCase()}.${(n.className || '').toString().trim().split(/\s+/)[0]}`
		),
	};
}, selector);

if (out.error) {
	console.error(out.error);
	await browser.close();
	process.exit(1);
}

console.log(`\n${out.tag}  ${selector}   @${width}px`);
console.log(`classes: ${out.classes}\n`);
console.log(`box: x=${out.box.x} y=${out.box.y} w=${out.box.w} h=${out.box.h}\n`);

console.log('computed:');
for (const [k, v] of Object.entries(out.computed)) console.log(`   ${k.padEnd(20)} ${v}`);

console.log(`\nmatching rules (last one wins on equal specificity):`);
for (const r of out.matchingRules) {
	console.log(`   [${r.from}]  ${r.selector}`);
	console.log(`       ${r.css}`);
}

console.log('\nancestors:');
for (const a of out.ancestors) console.log(`   ${a}`);

console.log(`\nsiblings: ${out.siblings.join(', ')}\n`);

await browser.close();
