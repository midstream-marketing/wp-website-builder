#!/usr/bin/env node
// Strip inline base64 data-URIs out of an exported HTML file so it can be
// attached to a prompt without blowing the context window.
// Usage: node bin/slim-html.mjs <file.html> [more.html ...]
// Writes <name>.slim.html + <name>-assets/ next to the source.

import fs from "node:fs";
import path from "node:path";

const EXT = {
  "image/jpeg": "jpg", "image/jpg": "jpg", "image/png": "png",
  "image/webp": "webp", "image/gif": "gif", "image/svg+xml": "svg",
  "font/woff2": "woff2", "font/woff": "woff", "application/font-woff": "woff",
};
const RE = /data:([\w.+-]+\/[\w.+-]+);base64,([A-Za-z0-9+/=]+)/g;
const est = (s) => Math.round(s / 3.3); // rough chars -> tokens

const files = process.argv.slice(2);
if (!files.length) {
  console.error("usage: node bin/slim-html.mjs <file.html> [...]");
  process.exit(1);
}

for (const src of files) {
  if (!fs.existsSync(src)) { console.error(`skip (missing): ${src}`); continue; }
  const html = fs.readFileSync(src, "utf8");
  const dir = path.dirname(src);
  const base = path.basename(src).replace(/\.html?$/i, "");
  const assetDir = path.join(dir, `${base}-assets`);

  const seen = new Map(); // dedupe identical payloads
  let n = 0, saved = 0;
  const slim = html.replace(RE, (whole, mime, data) => {
    if (seen.has(data)) { saved += whole.length; return seen.get(data); }
    n += 1;
    const name = `asset${String(n).padStart(2, "0")}.${EXT[mime] ?? "bin"}`;
    fs.mkdirSync(assetDir, { recursive: true });
    fs.writeFileSync(path.join(assetDir, name), Buffer.from(data, "base64"));
    const rel = `${base}-assets/${name}`;
    seen.set(data, rel);
    saved += whole.length - rel.length;
    return rel;
  });

  const out = path.join(dir, `${base}.slim.html`);
  fs.writeFileSync(out, slim, "utf8");
  console.log(
    `${path.basename(src)}\n` +
    `  ${html.length.toLocaleString()} -> ${slim.length.toLocaleString()} chars ` +
    `(~${est(html.length).toLocaleString()} -> ~${est(slim.length).toLocaleString()} tokens)\n` +
    `  ${n} asset(s) extracted to ${base}-assets/\n` +
    `  attach: ${out}`
  );
}
