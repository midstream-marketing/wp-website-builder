/**
 * On-page SEO across every published URL: titles, descriptions, headings, images, canonicals,
 * social cards, structured data and indexability.
 *
 *   node audit/seo.mjs              # every published URL from shots/url-inventory.json
 *   node audit/seo.mjs / /gifts/    # specific ones
 *
 * READ ONLY. Writes shots/seo.json.
 *
 * REPORTED AGAINST THE RENDERED PAGE, not the stored post data: a title or description can be
 * filtered, templated or overwritten by a plugin, and only the served HTML says what a crawler sees.
 *
 * SITE-WIDE noindex IS REPORTED ONCE, NOT PER PAGE. Search engines are deliberately discouraged
 * until launch on this build, so flagging it 124 times would bury everything else and train us to
 * skim the output. It is called out separately as a launch item.
 *
 * TITLE AND DESCRIPTION LENGTHS are measured in characters as a practical proxy. Google truncates on
 * pixel width, not characters, so these bounds are advisory - a 62-character title is not a defect.
 * Only missing, empty or duplicated values are treated as real findings.
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

const TITLE_MIN = 15, TITLE_MAX = 65;
const DESC_MIN = 70, DESC_MAX = 165;

const b = await launchBrowser();
const ctx = await b.newContext({ viewport: { width: 1440, height: 1000 } });
const rows = [];

for (const path of PAGES) {
  const p = await ctx.newPage();
  let status = 0;
  try {
    const r = await p.goto(base + path + "?nc=" + Date.now(), { waitUntil: "domcontentloaded", timeout: 90000 });
    status = r ? r.status() : 0;
  } catch {
    rows.push({ path, status: 0, err: "navigation failed" });
    await p.close();
    continue;
  }
  await p.waitForTimeout(900);
  /* lazy sections carry headings and images too */
  await p.evaluate(async () => {
    for (let y = 0; y < document.body.scrollHeight; y += 700) { window.scrollTo(0, y); await new Promise((r) => setTimeout(r, 30)); }
    window.scrollTo(0, 0);
  });
  await p.waitForTimeout(300);

  const d = await p.evaluate(() => {
    const txt = (e) => (e ? (e.textContent || "").replace(/\s+/g, " ").trim() : "");
    const attr = (sel, a) => document.querySelector(sel)?.getAttribute(a) || "";

    const h1 = [...document.querySelectorAll("h1")].map(txt).filter(Boolean);
    const hs = [...document.querySelectorAll("h1,h2,h3,h4,h5,h6")].map((e) => ({ t: e.tagName, x: txt(e) })).filter((x) => x.x);

    /* images: count the ones a crawler would expect alt text on */
    const imgs = [...document.querySelectorAll("img")].filter((i) => {
      const r = i.getBoundingClientRect();
      return (r.width > 1 && r.height > 1) || i.loading === "lazy";
    });
    const noAlt = imgs.filter((i) => !i.hasAttribute("alt") || !i.getAttribute("alt").trim());

    /* visible body text, for thin-content detection */
    const main = document.querySelector("main, .elementor-location-single, .site-main") || document.body;
    const clone = main.cloneNode(true);
    for (const n of clone.querySelectorAll("script,style,nav,header,footer")) n.remove();
    const words = (clone.textContent || "").replace(/\s+/g, " ").trim().split(" ").filter(Boolean).length;

    const ld = [...document.querySelectorAll('script[type="application/ld+json"]')].map((s) => {
      try {
        const j = JSON.parse(s.textContent || "{}");
        const g = j["@graph"] || (Array.isArray(j) ? j : [j]);
        return g.map((x) => x["@type"]).flat().filter(Boolean).join(",");
      } catch {
        return "INVALID JSON";
      }
    });

    return {
      title: txt(document.querySelector("title")) || document.title || "",
      desc: attr('meta[name="description"]', "content"),
      robots: attr('meta[name="robots"]', "content"),
      canonical: attr('link[rel="canonical"]', "href"),
      ogTitle: attr('meta[property="og:title"]', "content"),
      ogImage: attr('meta[property="og:image"]', "content"),
      ogDesc: attr('meta[property="og:description"]', "content"),
      twCard: attr('meta[name="twitter:card"]', "content"),
      lang: document.documentElement.getAttribute("lang") || "",
      viewport: attr('meta[name="viewport"]', "content"),
      h1, hs,
      imgCount: imgs.length,
      noAlt: noAlt.length,
      noAltSrc: noAlt.slice(0, 3).map((i) => (i.currentSrc || i.src || "").split("/").pop()),
      words,
      ld,
    };
  });

  rows.push({ path, status, ...d });
  await p.close();
}

await ctx.close();
await b.close();

/* ------------------------------------------------------------------ findings ------------------- */
const F = [];
const add = (sev, area, path, msg) => F.push({ sev, area, path, msg });

const byTitle = new Map();
const byDesc = new Map();

for (const r of rows) {
  if (r.err || r.status !== 200) {
    add("high", "status", r.path, `HTTP ${r.status || "error"}`);
    continue;
  }
  const t = (r.title || "").trim();
  const d = (r.desc || "").trim();

  if (!t) add("high", "title", r.path, "no <title>");
  else {
    if (t.length < TITLE_MIN) add("med", "title", r.path, `title very short (${t.length} chars): "${t}"`);
    if (t.length > TITLE_MAX) add("low", "title", r.path, `title ${t.length} chars, may truncate: "${t.slice(0, 70)}…"`);
    byTitle.set(t, [...(byTitle.get(t) || []), r.path]);
  }

  if (!d) add("high", "description", r.path, "no meta description");
  else {
    if (d.length < DESC_MIN) add("low", "description", r.path, `description short (${d.length} chars)`);
    if (d.length > DESC_MAX) add("low", "description", r.path, `description ${d.length} chars, will truncate`);
    byDesc.set(d, [...(byDesc.get(d) || []), r.path]);
  }

  if (!r.h1.length) add("high", "headings", r.path, "no H1");
  else if (r.h1.length > 1) add("med", "headings", r.path, `${r.h1.length} H1s: ${r.h1.slice(0, 3).map((x) => `"${x.slice(0, 28)}"`).join(", ")}`);

  if (!r.canonical) add("med", "canonical", r.path, "no canonical link");

  if (r.noAlt) add("med", "images", r.path, `${r.noAlt}/${r.imgCount} images with no alt text (${r.noAltSrc.join(", ")})`);

  if (!r.ogImage) add("low", "social", r.path, "no og:image - link previews will be blank");
  if (!r.ogTitle) add("low", "social", r.path, "no og:title");

  if (r.words < 120) add("med", "content", r.path, `thin: ~${r.words} words of body copy`);

  if (r.ld.some((x) => x === "INVALID JSON")) add("high", "schema", r.path, "structured data does not parse");
  if (!r.ld.length) add("low", "schema", r.path, "no structured data");

  if (!r.viewport) add("high", "responsive", r.path, "no viewport meta - the page will not scale on a phone");
  if (!r.lang) add("low", "a11y", r.path, "no lang attribute on <html>");
}

for (const [t, ps] of byTitle) if (ps.length > 1) add("med", "duplicate", ps[0], `${ps.length} pages share the title "${t.slice(0, 54)}": ${ps.slice(0, 4).join(", ")}${ps.length > 4 ? ", …" : ""}`);
for (const [d, ps] of byDesc) if (ps.length > 1) add("med", "duplicate", ps[0], `${ps.length} pages share one meta description: ${ps.slice(0, 4).join(", ")}${ps.length > 4 ? ", …" : ""}`);

/* site-wide noindex once, not per page */
const noindexed = rows.filter((r) => /noindex/i.test(r.robots || ""));
if (noindexed.length) {
  console.log(`\nNOTE  ${noindexed.length}/${rows.length} pages carry noindex - search engines are discouraged until launch (expected on this build).`);
}

const order = { high: 0, med: 1, low: 2 };
F.sort((a, b2) => order[a.sev] - order[b2.sev] || a.area.localeCompare(b2.area) || a.path.localeCompare(b2.path));

console.log(`\n=== SEO findings across ${rows.length} URLs ===\n`);
let last = "";
for (const f of F) {
  if (f.sev !== last) {
    console.log(`\n--- ${f.sev.toUpperCase()} ---`);
    last = f.sev;
  }
  console.log(`  [${f.area}] ${f.path.padEnd(44)} ${f.msg}`);
}

const counts = F.reduce((m, f) => ((m[f.sev] = (m[f.sev] || 0) + 1), m), {});
console.log(`\n${F.length} finding(s): ${counts.high || 0} high, ${counts.med || 0} medium, ${counts.low || 0} low`);

writeFileSync(`${ROOT}/shots/` + "seo.json", JSON.stringify({ rows, findings: F }, null, 1));
console.log("shots/seo.json written");
