// Compare two screenshot folders file by file (same names, e.g. a sweep
// before and after a site-wide change) and report how much of each page
// changed. Writes a red-highlighted diff image for every page that moved.
//
//   node audit/shotdiff.mjs shots/nexxus-baseline shots/sweep [thresholdPct]
//
// A page "changed" when more than thresholdPct (default 0.5) of its pixels
// differ by more than a small tolerance (anti-aliasing noise is ignored).
// Height differences are reported separately - content that moved down
// shows as a large diff everywhere below it.

import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';
import { launchBrowser } from '../lib/lib.mjs';

const [a, b, thr = '0.5'] = process.argv.slice(2);
if (!a || !b) {
	console.log('usage: node audit/shotdiff.mjs <folderBefore> <folderAfter> [thresholdPct]');
	process.exit(2);
}
const out = path.join(b, '_diff');
fs.mkdirSync(out, { recursive: true });

const browser = await launchBrowser();
const page = await browser.newPage();
await page.setContent('<canvas id=a></canvas><canvas id=b></canvas><canvas id=d></canvas>');

let changed = 0;
for (const f of fs.readdirSync(a).filter((n) => n.endsWith('.png')).sort()) {
	const pb = path.join(b, f);
	if (!fs.existsSync(pb)) {
		console.log(`  MISSING  ${f}`);
		continue;
	}
	const uri = (p) => 'data:image/png;base64,' + fs.readFileSync(p).toString('base64');
	const r = await page.evaluate(
		async ([ua, ub]) => {
			const load = async (u) => {
				const i = new Image();
				i.src = u;
				await i.decode();
				return i;
			};
			const [ia, ib] = await Promise.all([load(ua), load(ub)]);
			const w = Math.min(ia.width, ib.width);
			const h = Math.min(ia.height, ib.height);
			const px = (img, id) => {
				const c = document.getElementById(id);
				c.width = w;
				c.height = h;
				const x = c.getContext('2d');
				x.drawImage(img, 0, 0);
				return x.getImageData(0, 0, w, h);
			};
			const da = px(ia, 'a');
			const db = px(ib, 'b');
			const c = document.getElementById('d');
			c.width = w;
			c.height = h;
			const x = c.getContext('2d');
			const dd = x.createImageData(w, h);
			let n = 0;
			let firstY = -1;
			for (let i = 0; i < da.data.length; i += 4) {
				const diff =
					Math.abs(da.data[i] - db.data[i]) + Math.abs(da.data[i + 1] - db.data[i + 1]) + Math.abs(da.data[i + 2] - db.data[i + 2]);
				if (diff > 48) {
					n++;
					if (firstY < 0) firstY = Math.floor(i / 4 / w);
					dd.data[i] = 255;
					dd.data[i + 1] = 0;
					dd.data[i + 2] = 0;
					dd.data[i + 3] = 255;
				} else {
					const g = (db.data[i] + db.data[i + 1] + db.data[i + 2]) / 3;
					dd.data[i] = dd.data[i + 1] = dd.data[i + 2] = 200 + g * 0.2;
					dd.data[i + 3] = 255;
				}
			}
			x.putImageData(dd, 0, 0);
			return {
				pct: (100 * n) / (w * h),
				firstY,
				ha: ia.height,
				hb: ib.height,
				png: c.toDataURL('image/png'),
			};
		},
		[uri(path.join(a, f)), uri(pb)]
	);
	const moved = r.pct > Number(thr);
	const hNote = r.ha !== r.hb ? `  height ${r.ha} -> ${r.hb}` : '';
	console.log(`  ${moved ? 'CHANGED ' : 'same    '} ${f.padEnd(34)} ${r.pct.toFixed(2).padStart(6)}%${moved ? `  first diff at y=${r.firstY}` : ''}${hNote}`);
	if (moved) {
		changed++;
		fs.writeFileSync(path.join(out, f), Buffer.from(r.png.split(',')[1], 'base64'));
	}
}
await browser.close();
console.log(`\n${changed} page(s) changed beyond ${thr}%${changed ? ` - highlighted diffs in ${out}` : ''}`);
