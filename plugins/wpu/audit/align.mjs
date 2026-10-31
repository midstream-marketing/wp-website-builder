/**
 * Icon / text alignment checker.
 *
 *   node audit/align.mjs <url-path> <icon-selector> [text-selector] [--tol=1] [--w=1440,768,390]
 *   node audit/align.mjs / .lp-cico
 *
 * Answers the question "is this icon actually aligned with the text beside it", in numbers, so a
 * design complaint can be diagnosed instead of guessed at. Exits non-zero when anything is out of
 * tolerance, so it doubles as a regression test once a fix is in.
 *
 * WHAT IT MEASURES, AND WHY THOSE THINGS
 *
 * - The icon's INK, not its box. An SVG has padding inside its viewBox that the eye does not see, and
 *   it differs per glyph: a map pin is narrower than an envelope, so two icons centred in identical
 *   boxes still look out of line.
 *
 * - The text's CAP-HEIGHT midline, not its bounding box and not its glyph box. The bounding box
 *   includes leading. The glyph box moves with the characters - "(201) 706-2322" has no descenders,
 *   "hello@spabluejerseycity.com" has three - so aligning to it puts every row at a different height.
 *   Cap height is a property of the font, so it is the same target on every row, which is what makes
 *   a column of icons read as aligned.
 *
 * - The SPREAD across rows as well as the absolute offset. Three icons all 2px low looks deliberate;
 *   one icon 2px low looks broken. Consistency matters more than perfection.
 */
import { chromium } from 'playwright';
import fs from 'node:fs';
import { cfg as siteCfg, launchBrowser } from '../lib/lib.mjs';

const args = process.argv.slice(2);
const flags = Object.fromEntries(args.filter(a => a.startsWith('--')).map(a => a.replace(/^--/, '').split('=')));
const pos = args.filter(a => !a.startsWith('--'));

const urlPath = pos[0] || '/';
const iconSel = pos[1] || '.lp-cico';
const textSel = pos[2] || 'p';
const TOL = parseFloat(flags.tol ?? '1');
const widths = (flags.w ?? '1440,768,390').split(',').map(Number);

const cfg = siteCfg();
const base = cfg.baseUrl.replace(/\/$/, '');
const url = base + (urlPath.startsWith('/') ? urlPath : '/' + urlPath);

const spread = a => (a.length ? Math.max(...a) - Math.min(...a) : 0);
let fails = 0;
const ok = (c, m) => { console.log(`  ${c ? 'PASS' : 'FAIL'}  ${m}`); if (!c) fails++; };

const browser = await launchBrowser();

for (const w of widths) {
  const page = await browser.newPage({ viewport: { width: w, height: 900 } });
  await page.goto(url + (url.includes('?') ? '&' : '?') + 'nc=' + Date.now(), { waitUntil: 'networkidle', timeout: 90000 });
  // Scroll first and let it settle; measuring in the same tick as scrollIntoView returns the
  // pre-scroll rectangle.
  await page.evaluate(sel => { const i = document.querySelector(sel); if (i) i.scrollIntoView({ block: 'center', behavior: 'instant' }); }, iconSel);
  await page.waitForTimeout(800);

  const rows = await page.evaluate(([iconSel, textSel]) => {
    const out = [];
    for (const ico of document.querySelectorAll(iconSel)) {
      const ib = ico.getBoundingClientRect();
      if (!ib.width) continue;                       // hidden copies, e.g. inside a closed mobile menu
      const widget = ico.closest('.elementor-widget') || ico.parentElement;
      const row = widget && widget.parentElement;
      const p = row && row.querySelector(textSel);
      if (!p) continue;

      const pcs = getComputedStyle(p);
      const pb = p.getBoundingClientRect();
      const fontSize = parseFloat(pcs.fontSize);
      const lineHeight = parseFloat(pcs.lineHeight) || fontSize * 1.6;

      const c = document.createElement('canvas').getContext('2d');
      c.font = pcs.font;
      const m = c.measureText('H');
      const baseline1 = pb.top + (lineHeight - fontSize) / 2 + m.fontBoundingBoxAscent;
      const capMid = baseline1 - m.actualBoundingBoxAscent / 2;

      // ink of the icon: union of the shapes, scaled from viewBox units to screen px
      let inkLeft = ib.left, inkRight = ib.right, inkMid = (ib.top + ib.bottom) / 2;
      const svg = ico.tagName.toLowerCase() === 'svg' ? ico : ico.querySelector('svg');
      if (svg && svg.viewBox && svg.viewBox.baseVal && svg.viewBox.baseVal.width) {
        const sb = svg.getBoundingClientRect();
        const scale = sb.width / svg.viewBox.baseVal.width;
        let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
        for (const sh of svg.querySelectorAll('path,rect,circle,ellipse,line,polyline,polygon')) {
          const bb = sh.getBBox();
          x0 = Math.min(x0, bb.x); x1 = Math.max(x1, bb.x + bb.width);
          y0 = Math.min(y0, bb.y); y1 = Math.max(y1, bb.y + bb.height);
        }
        if (Number.isFinite(x0)) {
          inkLeft = sb.left + x0 * scale;
          inkRight = sb.left + x1 * scale;
          inkMid = sb.top + ((y0 + y1) / 2) * scale;
        }
      }

      out.push({
        text: p.textContent.trim().replace(/\s+/g, ' ').slice(0, 26),
        lines: Math.round(pb.height / lineHeight),
        delta: inkMid - capMid,
        inkLeft, gap: pb.left - inkRight,
        boxH: ico.getBoundingClientRect().height,
        lineHeight,
        pMarginBottom: parseFloat(pcs.marginBottom) || 0,
      });
    }
    return out;
  }, [iconSel, textSel]);

  console.log(`\n================ ${w}px ================`);
  if (!rows.length) {
    console.log(`  no "${iconSel}" found beside a "${textSel}"`);
    fails++;
    await page.close();
    continue;
  }
  for (const r of rows) {
    const d = r.delta;
    console.log(`  "${r.text}" (${r.lines}ln)  box ${r.boxH.toFixed(0)}px / line ${r.lineHeight}px   ${d >= 0 ? '+' : ''}${d.toFixed(2)}px vs cap midline`);
  }
  const deltas = rows.map(r => Math.abs(r.delta));
  ok(Math.max(...deltas) <= TOL, `every icon within ${TOL}px of the cap midline (worst ${Math.max(...deltas).toFixed(2)}px)`);
  ok(spread(rows.map(r => r.delta)) <= 0.5, `all rows share one offset (spread ${spread(rows.map(r => r.delta)).toFixed(2)}px)`);
  ok(spread(rows.map(r => r.inkLeft)) <= TOL, `ink left edges line up (spread ${spread(rows.map(r => r.inkLeft)).toFixed(2)}px)`);
  ok(spread(rows.map(r => r.gap)) <= TOL, `gaps to text match (spread ${spread(rows.map(r => r.gap)).toFixed(2)}px)`);
  ok(rows.every(r => r.pMarginBottom === 0), `no stray paragraph margin inflating the rows (${rows.map(r => r.pMarginBottom).join('/')}px)`);
  await page.close();
}

await browser.close();
console.log(fails ? `\n${fails} FAILED` : '\nalignment good at every width');
process.exit(fails ? 1 : 0);
