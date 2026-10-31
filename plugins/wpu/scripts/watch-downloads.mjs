#!/usr/bin/env node
// Watch a folder for exported HTML with inlined base64 and slim it automatically,
// so an oversized export can never be attached to a prompt by accident.
//
//   node bin/watch-downloads.mjs [folder]   # default: %USERPROFILE%\Downloads
//   node bin/watch-downloads.mjs --once     # sweep existing files and exit
//
// On hit: original -> <folder>/_raw-html-originals/, slim version takes its name.

import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { execFileSync } from "node:child_process";

const args = process.argv.slice(2);
const once = args.includes("--once");
const DIR = args.find((a) => !a.startsWith("--")) ?? path.join(os.homedir(), "Downloads");
const ARCHIVE = path.join(DIR, "_raw-html-originals");
const SLIM = path.join(import.meta.dirname, "slim-html.mjs");
const MIN = 200 * 1024; // ignore anything already small
const LOG = path.join(import.meta.dirname, "..", "scratch", "slim-watch.log");

const log = (m) => {
  const line = `${new Date().toISOString()} ${m}`;
  console.log(line);
  try { fs.appendFileSync(LOG, line + "\n"); } catch {}
};

function settled(p) {
  // wait until the file stops growing (browser still writing it)
  let last = -1;
  for (let i = 0; i < 30; i++) {
    let s;
    try { s = fs.statSync(p).size; } catch { return false; }
    if (s === last && s > 0) return true;
    last = s;
    Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 300);
  }
  return false;
}

function process_(file) {
  const p = path.join(DIR, file);
  if (!/\.html?$/i.test(file) || file.endsWith(".slim.html")) return;
  let st;
  try { st = fs.statSync(p); } catch { return; }
  if (!st.isFile() || st.size < MIN) return;
  if (!settled(p)) return;

  let head;
  try { head = fs.readFileSync(p, "utf8"); } catch { return; }
  if (!head.includes("base64,")) return;

  const base = file.replace(/\.html?$/i, "");
  try {
    execFileSync(process.execPath, [SLIM, p], { stdio: "pipe" });
    const slim = path.join(DIR, `${base}.slim.html`);
    if (!fs.existsSync(slim)) return log(`FAILED (no slim produced): ${file}`);
    fs.mkdirSync(ARCHIVE, { recursive: true });
    fs.renameSync(p, path.join(ARCHIVE, file));
    fs.renameSync(slim, p);
    const after = fs.statSync(p).size;
    log(`slimmed ${file}: ${st.size.toLocaleString()} -> ${after.toLocaleString()} bytes`);
  } catch (e) {
    log(`ERROR ${file}: ${e.message}`);
  }
}

fs.mkdirSync(path.dirname(LOG), { recursive: true });
for (const f of fs.readdirSync(DIR)) process_(f);
if (once) { log("sweep complete"); process.exit(0); }

log(`watching ${DIR}`);
const pending = new Map();
fs.watch(DIR, (_e, file) => {
  if (!file || !/\.html?$/i.test(file)) return;
  clearTimeout(pending.get(file));
  pending.set(file, setTimeout(() => { pending.delete(file); process_(file); }, 1500));
});
