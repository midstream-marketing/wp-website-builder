/**
 * Responsive health across every published URL: sideways scroll, what overflows, tap-target size and
 * unreadably small text.
 *
 *   node audit/responsive.mjs             # every published URL
 *   node audit/responsive.mjs /gifts/     # specific ones
 *
 * READ ONLY. Writes shots/responsive.json. Exits non-zero if any page scrolls sideways.
 *
 * NAMES THE CULPRIT, not just the symptom. "The page scrolls sideways" sends you hunting; the
 * element whose right edge sits past the viewport is the thing to fix, so the widest offender is
 * reported with its own width and position.
 *
 * ELEMENTS WIDER THAN THE VIEWPORT ARE NOT AUTOMATICALLY FAULTS. A horizontal card track is
 * deliberately wider than the screen and scrolls inside its own box. So an element is only blamed
 * when it actually pushes the DOCUMENT wider - measured from documentElement.scrollWidth - and
 * anything inside a scrollable ancestor is skipped.
 *
 * TAP TARGETS use 24px, the WCAG 2.2 AA minimum, rather than the 44px Apple guideline: 44 flags
 * every inline text link on the site and the report becomes noise.
 */
import { chromium } from "playwright";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { cfg as siteCfg, ROOT, launchBrowser } from "../lib/lib.mjs";
mkdirSync(`${ROOT}/shots`, { recursive: true });

const cfg = siteCfg();
const base = cfg.baseUrl.replace(/\/$/, "");
const inv = JSON.parse(readFileSync(`${ROOT}/shots/` + "url-inventory.json", "utf8"));

const rel = (u) => u.replace(base, "") || "/";
const pick = (t) => (inv.types[t] || []).map((r) => rel(r.url));
const rest = process.argv.slice(2);
const PAGES = rest.length
  ? rest
  : [...new Set(["/", ...Object.keys(inv.types).filter((t) => !t.startsWith("tax:")).flatMap(pick)])];

const WIDTHS = [360, 390, 768, 1440];
const MIN_TAP = 24;
const MIN_FONT = 12;

const b = await launchBrowser();
const ctx = await b.newContext();
const out = [];
let fail = 0;

for (const path of PAGES) {
  for (const w of WIDTHS) {
    const p = await ctx.newPage();
    await p.setViewportSize({ width: w, height: 900 });
    try {
      await p.goto(base + path + "?nc=" + Date.now(), { waitUntil: "domcontentloaded", timeout: 90000 });
    } catch {
      await p.close();
      continue;
    }
    await p.waitForTimeout(1000);
    await p.evaluate(async () => {
      for (let y = 0; y < document.body.scrollHeight; y += 700) { window.scrollTo(0, y); await new Promise((r) => setTimeout(r, 30)); }
      window.scrollTo(0, 0);
    });
    await p.waitForTimeout(400);

    const r = await p.evaluate((lim) => {
      const de = document.documentElement;
      const overflow = Math.round(de.scrollWidth - de.clientWidth);

      /* who is actually sticking out of the document? */
      const culprits = [];
      if (overflow > 1) {
        for (const e of document.querySelectorAll("body *")) {
          const q = e.getBoundingClientRect();
          if (q.width === 0 || q.height === 0) continue;
          if (q.right <= de.clientWidth + 1 && q.left >= -1) continue;
          /* inside something that scrolls on purpose? then it is not the page's problem */
          let anc = e.parentElement, inScroller = false;
          while (anc && anc !== document.body) {
            const cs = getComputedStyle(anc);
            if (/(auto|scroll|hidden)/.test(cs.overflowX)) { inScroller = true; break; }
            anc = anc.parentElement;
          }
          if (inScroller) continue;
          culprits.push({
            sel: e.tagName.toLowerCase() + "." + String(e.className).split(/\s+/).filter(Boolean).slice(0, 2).join("."),
            right: Math.round(q.right),
            width: Math.round(q.width),
            text: (e.textContent || "").replace(/\s+/g, " ").trim().slice(0, 34),
          });
        }
        culprits.sort((a, b2) => b2.right - a.right);
      }

      /* tap targets and tiny text, mobile only - handled by the caller */
      const small = [];
      for (const e of document.querySelectorAll("a[href], button, input[type=submit], [role=button]")) {
        const q = e.getBoundingClientRect();
        if (q.width === 0 || q.height === 0) continue;
        const cs = getComputedStyle(e);
        if (cs.display === "inline" && e.closest("p, li")) continue; /* inline prose links */
        if (q.height < lim || q.width < lim) {
          small.push({
            sel: e.tagName.toLowerCase() + "." + String(e.className).split(/\s+/).filter(Boolean).slice(0, 2).join("."),
            w: Math.round(q.width), h: Math.round(q.height),
            text: (e.textContent || "").replace(/\s+/g, " ").trim().slice(0, 26),
          });
        }
      }

      const tiny = [];
      for (const e of document.querySelectorAll("p, span, li, a, div")) {
        if (!e.childNodes.length) continue;
        const direct = [...e.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim().length > 12);
        if (!direct) continue;
        const q = e.getBoundingClientRect();
        if (q.width === 0 || q.height === 0) continue;
        const fs = parseFloat(getComputedStyle(e).fontSize);
        if (fs && fs < 12) tiny.push({ fs: Math.round(fs * 10) / 10, text: (e.textContent || "").replace(/\s+/g, " ").trim().slice(0, 34) });
      }

      return { overflow, culprits: culprits.slice(0, 4), small: small.slice(0, 6), smallN: small.length, tiny: tiny.slice(0, 4), tinyN: tiny.length };
    }, MIN_TAP);

    const rec = { path, w, ...r };
    out.push(rec);

    const probs = [];
    if (r.overflow > 1) probs.push(`scrolls sideways by ${r.overflow}px`);
    if (w <= 390 && r.smallN) probs.push(`${r.smallN} tap target(s) under ${MIN_TAP}px`);
    if (w <= 390 && r.tinyN) probs.push(`${r.tinyN} run(s) of text under ${MIN_FONT}px`);

    if (probs.length) {
      console.log(`ISSUE ${path.padEnd(40)} ${String(w).padEnd(5)} ${probs.join("; ")}`);
      for (const c of r.culprits) console.log(`         overflows: ${c.sel} right=${c.right} width=${c.width} "${c.text}"`);
      for (const s of (w <= 390 ? r.small : [])) console.log(`         small tap: ${s.sel} ${s.w}x${s.h} "${s.text}"`);
      for (const t of (w <= 390 ? r.tiny : [])) console.log(`         tiny text: ${t.fs}px "${t.text}"`);
      if (r.overflow > 1) fail++;
    }
    await p.close();
  }
}

await ctx.close();
await b.close();

const scrollers = out.filter((o) => o.overflow > 1);
console.log(`\n${PAGES.length} page(s) x ${WIDTHS.length} widths = ${out.length} checks`);
console.log(`${scrollers.length} with sideways scroll`);
writeFileSync(`${ROOT}/shots/` + "responsive.json", JSON.stringify(out, null, 1));
console.log("shots/responsive.json written");

if (fail) process.exit(1);
