// Open a URL in a FRESH context per attempt. Some hosts (Hostinger/Namecheap from this machine, 2026-10-11) drop ~1 in 3 TCP
// connects; a reused Chrome context keeps failing after the first timeout, a new one gets through.
export async function openFresh(browser, href, ctxOpts = {}, tries = 8) {
  let last;
  for (let i = 0; i < tries; i++) {
    const ctx = await browser.newContext(ctxOpts); const p = await ctx.newPage();
    try { const r = await p.goto(href, { waitUntil: 'load', timeout: 60000 }); if (r && !p.url().startsWith('chrome-error')) return { ctx, page: p }; } catch (e) { last = e; }
    await ctx.close(); await new Promise((res) => setTimeout(res, 3000));
  }
  throw last || new Error('could not open ' + href);
}
