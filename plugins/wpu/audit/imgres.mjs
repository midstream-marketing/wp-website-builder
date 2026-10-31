/**
 * Image resolution audit - <img> AND CSS background images.
 *
 *   node audit/imgres.mjs [path] [--w=1440,390] [--dpr=2]
 *
 * An image looks pixelated when its natural pixel width is less than the width it is displayed at
 * multiplied by the device pixel ratio. Retina is where this hides: a 768px file in a 768px slot is
 * perfect on a 1x monitor and visibly soft on every phone and every modern laptop.
 *
 * CSS backgrounds are the blind spot. A probe that only walks <img> reports a page full of photographs
 * as "3 images, all fine", which is how a pixelated hero tile passes an audit. Elementor sets section
 * and tile art as background-image, so both have to be measured.
 */
import { chromium } from 'playwright';
import fs from 'node:fs';
import { cfg as siteCfg, launchBrowser } from '../lib/lib.mjs';

const args = process.argv.slice(2);
const flags = Object.fromEntries(args.filter(a => a.startsWith('--')).map(a => a.replace(/^--/, '').split('=')));
const urlPath = args.find(a => !a.startsWith('--')) || '/';
const widths = (flags.w ?? '1440,390').split(',').map(Number);
const dpr = Number(flags.dpr ?? 2);

const cfg = siteCfg();
const url = cfg.baseUrl.replace(/\/$/, '') + (urlPath.startsWith('/') ? urlPath : '/' + urlPath);

const browser = await launchBrowser();
let under = 0;

for (const w of widths) {
  const page = await browser.newPage({ viewport: { width: w, height: 1000 }, deviceScaleFactor: dpr });
  await page.goto(url + (url.includes('?') ? '&' : '?') + 'nc=' + Date.now(), { waitUntil: 'networkidle', timeout: 90000 });
  await page.evaluate(async () => {
    for (let y = 0; y < document.body.scrollHeight; y += 600) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 90)); }
    window.scrollTo(0, 0);
  });
  await page.waitForTimeout(1500);

  const rows = await page.evaluate(async () => {
    const dpr = window.devicePixelRatio;
    const out = [];

    const natural = src => new Promise(res => {
      const i = new Image();
      i.onload = () => res([i.naturalWidth, i.naturalHeight]);
      i.onerror = () => res([0, 0]);
      i.src = src;
    });

    for (const img of document.querySelectorAll('img')) {
      const r = img.getBoundingClientRect();
      if (!r.width || !img.naturalWidth) continue;
      out.push({ kind: 'img', src: img.currentSrc || img.src, nw: img.naturalWidth, nh: img.naturalHeight,
                 cw: r.width, ch: r.height, label: (img.alt || '').slice(0, 24) });
    }

    for (const el of document.querySelectorAll('*')) {
      const bg = getComputedStyle(el).backgroundImage;
      if (!bg || bg === 'none' || !bg.includes('url(')) continue;
      const m = bg.match(/url\(["']?(.*?)["']?\)/);
      if (!m || m[1].startsWith('data:')) continue;
      const r = el.getBoundingClientRect();
      if (r.width < 40 || r.height < 40) continue;
      const [nw, nh] = await natural(m[1]);
      if (!nw) continue;
      const label = (el.querySelector('h1,h2,h3,h4') || {}).textContent || el.id || '';
      out.push({ kind: 'bg', src: m[1], nw, nh, cw: r.width, ch: r.height, label: label.trim().slice(0, 24) });
    }
    return out.map(o => ({ ...o, needW: Math.round(o.cw * dpr), needH: Math.round(o.ch * dpr), dpr }));
  });

  console.log(`\n=========== ${w}px viewport, dpr ${dpr} ===========`);
  const seen = new Set();
  const uniq = rows.filter(r => { const k = r.src + r.cw; if (seen.has(k)) return false; seen.add(k); return true; });
  uniq.sort((a, b) => (a.nw / a.needW) - (b.nw / b.needW));
  for (const r of uniq) {
    const ratio = r.nw / r.needW;
    const flag = ratio < 0.95 ? 'UNDER' : '  ok ';
    if (ratio < 0.95) under++;
    console.log(`  ${flag} x${ratio.toFixed(2)}  ${r.kind}  natural ${r.nw}x${r.nh}  shown ${Math.round(r.cw)}x${Math.round(r.ch)}  needs ${r.needW}px  ${r.label ? '[' + r.label + ']' : ''}`);
    if (ratio < 0.95) console.log(`         ${r.src.split('/').pop()}`);
  }
  await page.close();
}

await browser.close();
console.log(under ? `\n${under} under-resolved image slot(s)` : '\nevery image has the pixels it needs');
process.exit(under ? 1 : 0);
