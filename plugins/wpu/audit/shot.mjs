// One screenshot.
//
//   node audit/shot.mjs /                home.png
//   node audit/shot.mjs /cart/ cart 390  cart.png at 390px
//   node audit/shot.mjs / home 1440 full full-page rather than viewport
import { launch, url, ensureShots, wake } from '../lib/lib.mjs';

const [target = '/', name = 'shot', w = '1440', mode = 'viewport'] = process.argv.slice(2);

const dir = ensureShots();
const browser = await launch();
const ctx = await browser.newContext({
	viewport: { width: +w, height: 900 },
	isMobile: +w < 700,
	hasTouch: +w < 700,
	ignoreHTTPSErrors: true,
});
const page = await ctx.newPage();

await page.goto(url(target), { waitUntil: 'domcontentloaded', timeout: 60000 });
await page.waitForTimeout(900);
	await wake(page);

const out = `${dir}/${name.replace(/\.png$/, '')}.png`;
await page.screenshot({ path: out, fullPage: mode === 'full' });

console.log('->', out);
await browser.close();
