# GOTCHAS - merged knowledge base

Environment and platform traps learned on real client sites. Merged on 2026-10-28 from
wp-site-doctor/knowledge/GOTCHAS.md (all of it) and wp-site-build/knowledge/GOTCHAS.md (the
156 entries the Doctor file did not already have, in Part 2). Nothing was rewritten.

Search it, don't read it whole: it is ~500 KB. `grep -n -i "<symptom words>" knowledge/GOTCHAS.md`.
New traps go through /wpu:learn so the whole team gets them.

---

# Part 1 - from WP Site Doctor


Every entry here cost real time to find. Read before debugging, not after.

---

## LocalWP

### Local's PHP ships without a php.ini

`php.exe` inside Local has **no `php.ini`**, so `mysqli`, `mbstring`, `curl`, `gd` etc. are all unloaded. Any script you run with it dies on a missing function.

`scripts/wp.ps1` and `scripts/wpphp.ps1` pass every extension explicitly with `-d extension=...`. If you invoke Local's PHP directly, you must do the same.

### The DB port is not what wp-config says

`wp-config.php` says `DB_HOST=localhost`, but Local runs each site's MySQL on its **own port** (10011, 10012, …). Connecting on the default port fails with a vague error.

Per-site ports live in `%APPDATA%\Local\sites.json`. `scripts/detect.ps1` reads it. The wrappers pass `-d mysqli.default_port=<port>`.

### `wp eval-file` silently does nothing on larger files

**This is the worst one.** Above roughly 16KB, `wp eval-file` exits **0**, prints nothing, and executes **none** of the file. No error, nothing under `--debug`.

Symptom: your seeding script "runs" and nothing happens. You will suspect your own code for a long time.

Use **`scripts/wpphp.ps1`** instead — the script `require`s `wp-load.php` itself and runs under plain PHP. Reserve `wp.ps1` for short one-liners.

### A warm page cache hijacks `wpphp.ps1`

Symptom: `pwsh scripts/wpphp.ps1 php/site-info.php` worked at the start of the
session and now prints **the site's homepage HTML** instead of your output. The
script itself is fine and unchanged.

The shim used to set `$_SERVER['REQUEST_URI'] = '/'`. Once WP Rocket has cached
the homepage, its output buffer sees a cacheable front-end GET for `/` during
`wp-load`, `readfile()`s the cached page and calls `exit()` — your script never
runs. Nothing warns you; it looks like your code did nothing.

`DONOTCACHEPAGE` does not help, and neither does a query string: with
`advanced-cache.php` absent, WP Rocket's `Buffer\Tests::can_init_process()`
short-circuits to `true` because no tests are registered.

The lever that does work is `Buffer\Tests::is_rejected_extension()` — WP Rocket
refuses any request URI ending in `.php`. `scripts/wpphp.ps1` now sets
`REQUEST_URI = '/wpsd-cli.php'`, which keeps the request an ordinary GET while
making every page cache decline to touch it.

### Sites pulled down from WP Engine fatal on every admin page

A copy taken from WP Engine brings `wp-content/mu-plugins/` with it. Those
plugins reference platform-only constants — `PWP_NAME`, `WPE_APIKEY` — that
exist nowhere but WP Engine. Locally you get, on `init`:

```
PHP Fatal error: Uncaught Error: Undefined constant "PWP_NAME"
  in wp-content/mu-plugins/wpengine-common/plugin.php:525
```

The front end can keep working while **every** `wp-admin` request dies, because
the failing branch is inside `if ( is_admin() )`. "Critical error on wp-admin
only" is the signature.

Fix: rename the directory aside and put an empty one back.

```powershell
Rename-Item "$wc\mu-plugins" "mu-plugins-wpe-disabled"
New-Item -ItemType Directory "$wc\mu-plugins"
```

Never deploy the emptied `mu-plugins` back to WP Engine — the platform supplies
those files itself. Kinsta, Pantheon and Flywheel copies have the same trap with
their own constants.

### Admin pages take 5–10s on a copied production site

UpdraftPlus, Sucuri and WP Engine's Smart Plugin Manager all phone home on admin
requests. On a local copy those calls crawl to their timeouts. Playwright's
30s default fires mid-navigation and looks like a hang.

Set `page.setDefaultNavigationTimeout(180000)` for anything driving wp-admin.
Slow is not the same as broken — check the HTTP status before you go debugging.

### Arguments to `wpphp.ps1` silently arrive one character at a time

`pwsh scripts/wpphp.ps1 myscript.php apply` used to pass `a`, `p`, `p`, `l`, `y` as
five separate arguments. The script sees the wrong `$argv`, takes the wrong
branch, and reports success having done nothing. There is no error.

The cause is PowerShell unrolling a statement's output on assignment:

```powershell
$rest = if ($n -gt 1) { @($args[1..($n-1)]) }   # WRONG - $rest is a String
$rest = @( if ($n -gt 1) { $args[1..($n-1)] } ) # RIGHT - $rest is Object[]
```

A one-element array assigned out of an `if` block collapses back to a bare
String, and splatting a String with `@rest` enumerates its characters. The
`@( )` has to wrap the whole statement, not sit inside it. Fixed in
`scripts/wpphp.ps1`; check for the same shape anywhere else you splat.

Because of this, **any `wpphp.ps1` call that passed a single argument before
2026-08-20 ran with the wrong argv.** Dry-run/apply flags were the usual victim.

### Elementor `_elementor_data` will not re-encode byte-for-byte

Before writing `_elementor_data` back you want to prove you are not corrupting
it. Byte equality is the wrong test — it always fails on floats:

```
stored : "size":1.1799999999999999
PHP    : "size":1.18
```

The stored copy was written by the JS editor with 17-digit precision; PHP's
`serialize_precision=-1` emits the shortest form that round-trips. Same double,
different spelling. Test for **lossless round-trip** instead:

```php
$identity = wp_json_encode( $data );
$ok = ( json_decode( $identity, true ) === $data );   // structural equality
```

Use plain `wp_json_encode()` with **no flags** — that matches how Elementor
writes it (escaped slashes `\/` and escaped unicode `\u2019`). Adding
`JSON_UNESCAPED_SLASHES` or `JSON_UNESCAPED_UNICODE` rewrites every string in
the document, turning a five-value edit into a whole-file diff.

Write with `update_post_meta( $id, '_elementor_data', wp_slash( $json ) )`, then
clear both caches or you will be looking at stale CSS:

```php
\Elementor\Plugin::$instance->files_manager->clear_cache();
rocket_clean_domain();
```

### Elementor library templates are not publicly viewable

`/?p=646` or `/?elementor_library=<slug>` on a saved template silently serves
the **homepage** to a logged-out browser — HTTP 200, no redirect you'd notice.
Automating against it and finding your section missing means "not logged in",
not "not there". Log in first; `?p=<id>` then renders the template properly.

### An Adobe XD share link IS machine-readable - stop eyeballing screenshots

A published `xd.adobe.com/view/<id>/` link looks like an opaque JS viewer, but
it fetches the design's full vector scene graph from Adobe's CDN as JSON, with
no login:

```
application/vnd.adobe.agc.graphicsTree+json      <- the whole design
application/vnd.adobe.uxdesign.globalresources+json
```

Load the link in Playwright and capture the response body:

```js
p.on('response', async r => {
  if (/vnd\.adobe\.(agc|uxdesign)/.test(r.headers()['content-type']||''))
    writeFileSync('xd.json', await r.body());
});
await p.goto(URL, {waitUntil:'domcontentloaded'});
await p.waitForTimeout(20000);   // it arrives late; do not skip the wait
```

Structure: `children[0].artboard.children`, and `artboards` carries the artboard
size. Nodes are `{type: text|shape|group, transform:{tx,ty}, ...}` - accumulate
`tx/ty` down the tree for absolute coordinates, and subtract the artboard's `x`
for artboard-local ones. Useful fields:

- text: `meta.ux.rangedStyles[0]` -> `postscriptName`, `fontSize`;
  `style.textAttributes` -> `paragraphAlign`, `lineHeight`;
  `meta.ux.outlinesLayout.static.paragraphs[].lines[].layoutBounds` gives the
  **measured width of every rendered line** - the ground truth for "does this
  heading fit on one line".
- shape: `shape.type` of `circle|line|path|rect` with `cx/cy/r`, `x1/x2`, or an
  SVG `path` string; `style.stroke.dash` finds dotted rails.

Never infer a design's geometry from a screenshot of unknown scale. The archived
scene graph for Greyson is at `docs/xd-graphicstree.json`.

Fallbacks if a link is ever unpublished: an SVG export of the artboard, or the
`.xd` file itself (a ZIP of JSON).

### Elementor caps inner sections at the GLOBAL content width

A top-level section's "Content Width" setting does **not** reach its inner
sections. Every `.elementor-inner-section > .elementor-container` is capped at
the site-wide content width from Site Settings, so a wide top-level section
still gets narrow rows. Override per-section in CSS:

```css
.my-section .inner-row > .elementor-container{max-width:1339px;}
```

Also budget for `.elementor-widget-wrap.elementor-element-populated`, which
carries **10px of side padding** - 20px off every row, which is exactly the kind
of number that leaves text 9px short and makes a heading wrap.

### Negative margins do not widen an Elementor widget

`.elementor-widget-wrap` is `display:flex`, so a widget with `width:auto` is
sized by the flex container. Adding `margin-left:-42px` **moves** the box
without growing it - the computed width stays at the column width. To let a
widget overhang its column you need an explicit width too:

```css
.widget{width:calc(100% + 42px); margin-left:-42px;}   /* right edge stays put */
```

### An overflow check is not a responsiveness check

`audit.mjs` and the usual `scrollWidth > clientWidth` test only catch elements
crossing the **viewport** edge. They say nothing about elements crossing **each
other**. A section can pass every overflow test at every breakpoint while a
connector line runs 47px through a heading.

If a layout mixes absolute px with percentages - fixed decorative geometry beside
`%` paddings, say - the two scale apart as the container narrows. Measure the
actual gap between the things that must not touch, at a dozen widths, and assert
it stays positive. Deriving a scale from the live container width and clamping
against the neighbour's measured edge is what makes it hold.

### wp-cli can hang

Occasionally a `wp` call hangs indefinitely holding a php.exe process. If a command has not returned in ~60s, it is stuck:

```powershell
Get-Process php | Select-Object Id, StartTime, CPU
Stop-Process -Id <id> -Force
```

Then use `wpphp.ps1` for that operation instead.

---

### PowerShell writes a BOM, and JSON.parse rejects it

`Set-Content -Encoding utf8` and `Out-File -Encoding utf8` both prepend a
byte-order mark. Node then fails with `Unexpected token '﻿'` on a file that
looks perfectly valid in an editor.

Write JSON (and anything PHP will `require`) without a BOM:

```powershell
[System.IO.File]::WriteAllText($path, $text, (New-Object System.Text.UTF8Encoding($false)))
```

### `$host` is a read-only PowerShell built-in

Assigning to it fails with "Cannot overwrite variable Host because it is
read-only or constant". Use `$siteHost` or anything else.

### `Select-Object -First/-Last` on a native command gives exit 255

It closes the pipe early, the process gets a broken-pipe error, and PowerShell
reports 255. The output you saw is still correct — do not go hunting for a bug
that is not there. Capture to a variable first if the exit code matters.

---

## Browser automation

### `networkidle` never fires on sites with a chat widget

Tidio, Intercom, Crisp and friends hold a socket open forever. `waitUntil: 'networkidle'` therefore **never resolves** and every script times out at 60s.

Use `waitUntil: 'domcontentloaded'` plus an explicit `waitForTimeout`. All scripts in this kit already do.

### Per-element overflow reports are noisy

Marquees, carousels and full-bleed rails are *deliberately* wider than the viewport and clipped by an ancestor. Reporting every element wider than the screen produces dozens of false positives.

What actually matters is whether the **document** scrolls:

```js
document.documentElement.scrollWidth > document.documentElement.clientWidth
```

`audit/hscroll.mjs` checks exactly that. Use the per-element report only to locate the culprit *after* hscroll says something is wrong.

### The skip link is always reported

Accessibility skip links sit at `left: -9999px` by design. Every overflow report will list one. Ignore it.

---

## WordPress / theme

### Where the errors actually are

There is often **no `wp-content/debug.log`** unless `WP_DEBUG_LOG` is on. WooCommerce keeps its own, and it catches fatals:

```
wp-content/uploads/wc-logs/fatal-errors-YYYY-MM-DD-<hash>.log
```

Check the timestamp against "now" — most entries are stale. Also check `<site>/logs/php/error.log` in the Local site folder.

### Never paste code out of a Grep result

Grep escapes characters for display. A comment opening `/*` appears as `\*`. Paste that back into a template and PHP dies with `syntax error, unexpected token "\"` — which white-screens the entire site.

**Read the file, then edit it.** This happened twice in the source project.

### Lint after every template edit

```powershell
pwsh scripts/php.ps1 -l path/to/file.php
```

A single bad character in `header.php` takes down every page, and you will not notice if you only reload the one page you were working on.

---

## Page builders

### Elementor renders *nothing* for an unregistered widget

If a theme or plugin that provided widgets is removed, every page built with them keeps its `_elementor_data` but renders **silent empty gaps**. No error, no placeholder — just blank space where a section was.

Symptom: "this page looks broken / has a big gap". Run `php/dead-widgets.php`.

### Writing `_elementor_data` corrupts easily

It is slash-escaped JSON in postmeta. Always:

1. `json_decode` your new value and confirm it is not `null`
2. write with `wp_slash( wp_json_encode( $data ) )`
3. `delete_post_meta( $id, '_elementor_css' )` to clear the stale per-page CSS

A failed decode renders the page completely blank.

### Builder pages must not inherit a narrow content column

If the theme constrains written pages to a reading measure, that will crush any builder-made page into a fraction of its intended width. Detect and exempt:

```php
'builder' === get_post_meta( $id, '_elementor_edit_mode', true )
```

Same applies to WooCommerce cart / checkout / account, whose tables and two-column forms need the full width.

---

## WooCommerce

### It floats the account columns and sets `order`

`.woocommerce-MyAccount-navigation` and `-content` get `float` plus percentage widths, *and* a flex `order`. Dropping a CSS grid on the parent is not enough — the columns land stranded or swapped. Reset all three:

```css
float: none; width: auto;
grid-column: 1; grid-row: 1; order: 0;   /* and 2 / 1 / 0 for the content */
```

### Free shipping does not replace the paid rate

When an order qualifies for free shipping, WooCommerce lists **both** methods and preselects the paid one. A "you qualify for free shipping" message will therefore be contradicted at checkout. Filter `woocommerce_package_rates` to drop the others when free shipping is present.

### Restrict countries properly

Setting up one shipping zone is not enough — a customer elsewhere can still reach checkout and stall with no method. Set `woocommerce_allowed_countries` / `woocommerce_ship_to_countries` to `specific`, and clear the methods from the "rest of world" zone (id 0).

---

## CSS

### Plugin stylesheets outrank yours

Third-party CSS commonly uses **IDs** (`#uap_submit_bttn`) and loads after the theme. Equal-specificity class selectors lose.

Do not guess — measure:

```bash
node audit/probe.mjs <url> '.the-selector'
```

Then match or exceed their specificity. Reach for `!important` only after you have looked.

### A wrapper div may be the styled element

Plugins often wrap a real `<input type="submit">` in a styled `<div>`. Styling both stacks two buttons. Check the markup before writing the rule.

### Percentage `max-height` does not resolve in a grid area

`max-height: 100%` on a grid item silently falls back to the intrinsic size, so images render at full resolution and overflow. Use an absolute value.

### Chrome's password-generation bubble eats the first click on a register button

Filling a field with `autocomplete="new-password"` makes Chrome pop its
"suggest strong password" bubble directly **below** the field — which is exactly
where a signup form's submit button sits. The bubble is browser UI, so nothing in
the page shows it: `elementFromPoint` still returns the BUTTON, `pointer-events`
is `auto`, no `preventDefault` fires, and Playwright's actionability checks pass.
The click simply never reaches the button and **no request is made**. Happens in
headed Chrome too, so it is not a headless artifact.

Symptom: submitting by click does nothing, but `page.press(field,'Enter')`,
`form.requestSubmit()` and a plain `curl` POST all work.

```js
// blur the password field before clicking a submit button under it
await p.evaluate(() => document.activeElement.blur());
await p.keyboard.press('Escape');
```

Before concluding a form is broken, test a **control button on the same page**
(here: the login button, which submitted fine). That is what separated "the site
is broken" from "my harness is being interfered with".

### `is_shop()` is true on the product archive, not just the shop page

If the product archive slug has been changed (here to `our-tours`), then
`is_shop()` is true on `/our-tours/`. A `template_redirect` guarded only by
`is_shop()` will redirect that page **to itself** — an infinite loop. Match the
specific page you mean:

```php
if ( ! is_page() || 'shop' !== get_post_field( 'post_name', get_queried_object_id() ) ) { return; }
```

Always `curl -D -` the redirect target *and* the source after adding a redirect.
I caught this only because I checked both URLs.

### An element hidden by a responsive flag is still in `innerHTML`

Counting text with `document.body.innerText`/`innerHTML` includes containers that
Elementor has hidden with `hide_desktop` / `hide_tablet` / `hide_mobile`. A pair
of responsive variants therefore looks like duplicated content. Filter by real
visibility before calling something a duplicate:

```js
const vis = e => { const r = e.getBoundingClientRect(), c = getComputedStyle(e);
  return r.width > 0 && r.height > 0 && c.display !== 'none' && c.visibility !== 'hidden'; };
```

### UpdraftPlus can be configured database-only — check before trusting a backup

`boot_backup(1, 1, false, true)` honours the saved include options, so if
`updraft_include_plugins` / `themes` / `uploads` / `mu-plugins` are `0`, you get a
DB-only archive and the run still reports **"The backup succeeded and is now
complete"**. The only sign is in `wp-content/updraft/log.*.txt`:

```
No backup of plugins: excluded by user's options
```

Turn them on first, then back up:

```php
foreach ( array('plugins','themes','uploads','mu-plugins','others') as $k ) {
    UpdraftPlus_Options::update_updraft_option( 'updraft_include_' . $k, 1 );
}
```

There is no `wp updraftplus` CLI command — that is a premium add-on. Drive it
through the `$updraftplus` global via `scripts/wpphp.ps1`.

### WooCommerce registration needs *two* switches

`woocommerce_enable_myaccount_registration = yes` renders the form, but if
WordPress's own `users_can_register` is `0` the POST is a **silent no-op** — no
error notice, no PHP warning, no user created. Check both.

### Elementor's kit flattens links: `.elementor a{box-shadow:none}` and a navy colour

Two rules in the Elementor kit quietly beat any single-class rule on an `<a>`:

- `.elementor a{box-shadow:none}` — card shadows vanish, so a white card on a
  white page becomes invisible while `getComputedStyle` cheerfully reports
  `borderRadius` and `background` as applied.
- the kit's link colour — white-on-navy text inside `.elementor` renders navy on
  navy, i.e. invisible.

Both are specificity (0,1,1) and beat `.my-class` (0,1,0). Use two classes:

```css
.hdt-upcoming a.hdt-uc { box-shadow: …; border: 1px solid #E4E0D8; }
.hdt-acct a.hdt-acct__out { color: rgba(255,255,255,.82); }
```

Confirm the winner with CDP rather than reading stylesheets:

```js
const cdp = await ctx.newCDPSession(page); await cdp.send('CSS.enable');
const {nodeId} = await cdp.send('DOM.querySelector', {nodeId: root.nodeId, selector: '.hdt-uc'});
(await cdp.send('CSS.getMatchedStylesForNode', {nodeId})).matchedCSSRules   // in cascade order
```

### The WooCommerce shop page hijacks its own URL

If a designed page is *also* set as the shop page, WordPress resolves that URL to
the **product archive** and the page's Elementor content never renders — you get
the default loop instead, plus the page's `post_content` printed as the archive
description. A page duplicated from another one can therefore leak the original's
heading onto the archive.

Check `wc_get_page_id('shop')`, `get_post_type_object('product')->has_archive`,
and the page's raw `post_content` before assuming a template is at fault.

### WooCommerce dashboard text is in a template, not on a hook

`woocommerce_account_dashboard` fires *inside* `myaccount/dashboard.php`, after
the default greeting and the "shipping and billing addresses" paragraph. So
`remove_action( 'woocommerce_account_dashboard', 'woocommerce_account_content' )`
removes nothing. Override the template instead:

```php
add_filter( 'woocommerce_locate_template', function ( $t, $name ) {
    $ours = MY_PLUGIN_PATH . 'templates/' . $name;
    if ( 'myaccount/dashboard.php' === $name && file_exists( $ours )
        && ! locate_template( array( 'woocommerce/' . $name, $name ) ) ) {
        return $ours;
    }
    return $t;
}, 10, 2 );
```

### Elementor 404 templates live in the `single` location

Document type is `error-404`, the condition is `include/singular/not_found404`,
and the `elementor_pro_theme_builder_conditions` cache entry goes under
**`single`**. Discover this rather than guessing — an invalid condition renders
nothing, silently:

```php
$m = \ElementorPro\Modules\ThemeBuilder\Module::instance();
$m->get_locations_manager()->get_locations();
$m->get_conditions_manager()->get_conditions_config();
```

### A disabled submit button is not always a bug

The tour booking button stays disabled until lead-passenger name/phone/email,
emergency contact and the declaration checkbox are filled — that is the client's
required flow. Check `form.querySelectorAll(':invalid')` and read the
`validationMessage` before hunting for a JS fault.

### Yoast meta survives a rename

Renaming or repurposing a post leaves `_yoast_wpseo_title`, `_yoast_wpseo_metadesc`
and `_yoast_wpseo_focuskw` pointing at the old subject, and Yoast caches the
rendered output in `wp_yoast_indexable`. The page looks completely correct while
serving the previous product's title and description to search engines.

```php
update_post_meta( $id, '_yoast_wpseo_title', '…' );
update_post_meta( $id, '_yoast_wpseo_metadesc', '…' );
update_post_meta( $id, '_yoast_wpseo_focuskw', '…' );
$wpdb->query( "DELETE FROM {$wpdb->prefix}yoast_indexable WHERE object_id = $id AND object_type = 'post'" );
```

Verify in the rendered HTML, not the meta — `curl -s URL | grep -oiE '<title>[^<]*'`.

Grepping `wp_postmeta` for the old name is the quickest way to find every leak;
ignore `_wp_old_slug`, which is what powers WordPress's automatic 301.

### `color` on a container does not reach children that set their own

A "selected" state that flips a background to dark and sets `color:#fff` on the
wrapper leaves every child that declares its own colour completely unchanged. Here
the selected date card rendered its date `#0E2340` on `#0E2340`.

Inherited colour is the weakest thing in the cascade — assume nothing, and read the
computed colour of the **leaf** nodes:

```js
[...card.querySelectorAll('*')].filter(n => !n.children.length && n.textContent.trim())
  .map(n => ({ text: n.textContent.trim(), color: getComputedStyle(n).color }))
```

Do this for every state that inverts a background, not just the default one.

### The Elementor kit rounds every image, and that shows as a line inside rounded containers

`.elementor-kit-12 img { border-radius: 12px 12px 12px 12px }` applies to **every**
image on the site. Drop an image into a container that already rounds and clips
(`border-radius` + `overflow:hidden`) and the image's own inner curve leaves a
sliver of the container's background visible at each corner — it reads as a faint
line or double edge, and it rounds corners that were meant to stay square (e.g.
the bottom of a card image that should meet the card body flush).

Let the container own the shape:

```css
.hdt-uc .hdt-uc__media img { border-radius: 0; }   /* card image  */
.hdt-tp .hdt-gal img       { border-radius: 0; }   /* gallery     */
.hdt-tp .hdt-hero img      { border-radius: 0; }   /* hero        */
```

Two classes are needed — `.hdt-gal img` (0,1,1) only ties with the kit rule and
loses on source order.

### Prefer `aspect-ratio` to a fixed image height in a fluid card

A fixed `height: 265px` looked right on the 396px-wide Our Tours cards (1.49:1)
but came out at 1.10:1 — visibly square — on the homepage, whose column is only
291px wide. `aspect-ratio: 3/2` holds the same shape at every card width and
every breakpoint. Verify by measuring the ratio, not the height:

```js
[...document.querySelectorAll('.hdt-uc__media')]
  .map(m => (m.getBoundingClientRect().width / m.getBoundingClientRect().height).toFixed(2))
```

### Deleting Elementor's CSS files is not enough — and leaves the site with 404 stylesheets

Elementor records each generated file in **`_elementor_css` post meta**. Delete
`uploads/elementor/css/post-*.css` on its own and Elementor still believes the
file is current: it keeps enqueuing `post-57.css`, the browser 404s, and the page
renders with its per-post CSS missing (layout silently reverts to defaults —
here a 3-column card grid jumped from 293px to 463px cards). `files_manager->clear_cache()`
alone did not rewrite them either.

Clear the meta, then hit the pages:

```php
$wpdb->query( "DELETE FROM {$wpdb->postmeta} WHERE meta_key = '_elementor_css'" );
\Elementor\Plugin::$instance->files_manager->clear_cache();
```

```bash
for u in / /our-tours/ /tour/oxford/; do curl -s -o /dev/null "http://heritage.local$u"; done
ls -la wp-content/uploads/elementor/css/   # confirm post-*.css came back
```

**Always confirm the files exist again afterwards.** A missing per-post stylesheet
does not throw anything — the page still returns 200 and the audit still passes.

### Elementor caches a widget's control CSS until the file is rebuilt

Renaming a control (here `media_height` → `media_ratio`) changes nothing on the
front end until the per-post CSS is regenerated, because the old declaration is
baked into `post-<id>.css` and outranks the plugin's own stylesheet by
specificity. After editing a widget's `selectors`, rebuild as above and grep the
generated file to confirm:

```bash
grep -o "elementor-element-<id>[^}]*}" post-57.css
```

### UpdraftPlus is slow on Windows because there is no `zip` binary

A full backup of this site took **20.9 minutes**, and **~19 of those were the
plugins folder alone**. The cause is not disk speed and not total size:

| Entity | Files | Size | Time |
|---|---|---|---|
| plugins | 19,489 | 296 MB | **~19 min** |
| themes | 510 | 15 MB | ~51 s |
| uploads | 937 | 182 MB | ~32 s |

uploads is **larger than plugins in bytes but 20× faster** — the cost is driven by
**file count**, not size.

UpdraftPlus logs `Checking if we have a zip executable available`, finds none
(nothing on PATH, no Git/7-Zip/Local copy), and falls back to PHP `ZipArchive`.
In that mode it closes and reopens the archive every `UPDRAFTPLUS_MAXBATCHFILES`
files — default **1000** — and each reopen rewrites the central directory of a
growing archive, so the cost climbs as the zip fills.

The constant is overridable (`updraftplus.php:62` guards it with `!defined`), so
it can be raised in `wp-config.php`:

```php
if ( ! defined( 'UPDRAFTPLUS_MAXBATCHFILES' ) ) {
	define( 'UPDRAFTPLUS_MAXBATCHFILES', 25000 );
}
```

**20.9 min → 8.6 min**, a 59% cut, same 15 archives, all passing `testzip()`.
Reopens still occur on the other two triggers (25 MB of data, or 2 s since the
last write), which is why it does not go to zero.

Put it in `wp-config.php`, **not** an mu-plugin: UpdraftPlus restores `mu-plugins`
onto the destination, and this is a workaround for one slow local Windows box —
a Linux host with a real `zip` binary does not want it.

Installing a `zip` executable would beat all of this, but that is a machine change
worth asking about first.

### `information_schema.TABLE_ROWS` is an estimate, and wildly so

It reported `wp_postmeta` at 14,508 rows / 67 MB when the table actually held
**1,065** rows. InnoDB also does not hand disk space back after deletes, so the
on-disk figure stays high. Never size a database from it — `SELECT COUNT(*)`.

This matters when judging a backup: a DB dump that suddenly shrinks (here 6.6 MB
→ 0.8 MB gz) may be correct. Verify by **content**, not size — confirm the table
count matches and grep the decompressed dump for things that must be there.

### WordPress 7.1 makes hook callback ids integers — plugins that do string ops on them fatal

`_wp_filter_build_unique_id()` now returns `(string) spl_object_id( $callback )` for
closures and objects. That is a **numeric** string, and PHP casts numeric string
array keys to `int`. So iterating `$wp_filter[$hook]->callbacks[$priority]` can hand
you integer keys where every plugin written before WP 7.1 expects strings:

```php
foreach ( $wp_filter[ $hook ]->callbacks[ $priority ] as $key => $config ) {
    substr( $key, -10 );   // PHP 8 TypeError if $key is an int -> fatal
}
```

On PHP 8 that is an uncaught `TypeError`, and if the code runs on `init` it takes
down **the entire site**, not just admin. Cast before any string operation:

```php
substr( (string) $key, - strlen( $method ) )
```

Using the key purely for `isset()` / `unset()` / array lookup is safe — only string
functions break. When triaging a WP 7.x site, grep for string functions applied to a
callback-iteration key:

```
rg '(substr|strpos|strlen|str_contains|str_(starts|ends)_with)\s*\(\s*\$key' --glob '*.php'
```

Check for a plugin update **before** patching a vendor file — WP Rocket shipped this
exact fix one patch release later, and taking the update left no modified file behind.

### A 500 on every URL is not an "admin" problem — read the log first

`/`, `/wp-admin/` and `/wp-login.php` all returning 500 means something fatals during
bootstrap, so there is no point poking at admin screens. Go straight to
`Local Sites/<site>/logs/php/error.log` and read the newest stack trace: it names the
file, line and the actual argument (`substr(5065, -24)` was the whole diagnosis).

Confirm a fix by **log size and last-entry timestamp**, not by the page loading —
compare bytes before and after, and check the newest entry predates the change.
Grepping the tail of an unchanged log will happily match the *old* errors and make a
working fix look broken.

### A re-import silently reverts your fixes — check file mtimes first

When a bug you already fixed comes back, do not re-debug it from scratch. Compare
timestamps:

```bash
stat -c '%y  %n' wp-content/plugins/<plugin>/<file>.php wp-content/mu-plugins/<file>.php
```

A cluster of files all modified within a few minutes, well after your fix, means the
site was re-imported or restored — and a plugin may have been **rolled back** to an
older version at the same time. Check `wp plugin list --name=<x> --fields=version`
against what you installed.

For a site pulled from managed hosting (WP Engine, Kinsta, Pantheon), host-specific
mu-plugins come back with every pull. Keep the repair in a script rather than doing
it by hand each time.

### Managed-host mu-plugins need the loader moved too

WP Engine's `mu-plugins/mu-plugin.php` is a loader:

```php
require_once __DIR__ . '/wpengine-common/plugin.php';
```

Renaming `wpengine-common/` alone turns "Undefined constant PWP_NAME" into
"Failed opening required ...". Move the loader **and** the directories it pulls in.
Check which root files are platform-bound before moving anything:

```bash
for f in *.php; do printf '%-38s %s\n' "$f" "$(grep -cE '\b(PWP_NAME|WPE_[A-Z_]+)\b' "$f")"; done
```

Files scoring 0 (here `slt-force-strong-passwords.php`, `wpengine-security-auditor.php`)
are ordinary plugins — leave them.

### Elementor's per-element CSS beats your stylesheet

Elementor writes per-widget rules like

```css
.elementor-557 .elementor-element.elementor-element-c118e19 .jet-listing-grid__slider-icon { right: -30px }
```

at specificity (0,3,x). A tidy component selector such as
`.jet-listing-grid__slider-icon.next-arrow` (0,2,0) loses, and the symptom is a fix
that is present in the page source and still does nothing.

Confirm with CDP `CSS.getMatchedStylesForNode` — it lists the rules in cascade order
with their media queries — then either edit the widget setting or override with
`!important`. `!important` is the right call when the value is set per element and
you want one rule to cover them all.

### An absolutely positioned control 30px outside its container overflows on phones

Carousel arrows offset outside the track look fine at desktop width and push the page
sideways at 390px, where the track is nearly the full viewport. Symptom is a small,
constant overflow (+10px here). Find it by listing elements whose right edge exceeds
the viewport **and that no ancestor clips**:

```js
const clipped = e => { let n = e.parentElement;
  while (n && n !== document.documentElement) {
    if (/hidden|clip|auto|scroll/.test(getComputedStyle(n).overflowX)) return true;
    n = n.parentElement; } return false; };
```

Without the clip check you get a long list of elements inside `overflow:hidden`
sliders that are not actually causing the scroll.

### WordPress escapes `>` in Customizer "Additional CSS"

A child combinator written into Customizer CSS is served to the browser as
`&gt;`, so the rule parses as garbage and never matches — while every other rule
in the same block applies normally. That mix is the confusing part: half your
fix works.

```css
.parent > .child { … }   /* served as `.parent &gt; .child` — dead */
.parent .child   { … }   /* works */
```

Check what is actually served, not what you saved:

```bash
curl -s URL | grep -A 8 "my-marker-comment"
```

Use descendant selectors, or put the CSS in a stylesheet file instead.

### Reading an Adobe XD artboard's real coordinates

Artboards are placed on an infinite canvas, so node transforms are canvas-absolute.
`doc.artboards[<uid>]` carries `{width, height, x, y}` — subtract that `x`/`y` while
walking or every coordinate is off by thousands:

```js
const AB = doc.artboards[uid];
walk(doc.children[0].artboard.children, -AB.x, -AB.y);
```

`meta.ux.outlinesLayout.static.paragraphs[].lines[].layoutBounds` gives the measured
width of each rendered line — but it can come back as zeros, so do not depend on it;
`rawText`, `meta.ux.rangedStyles[0].fontSize` and `style.textAttributes.lineHeight`
are reliable.

Derive the layout from the geometry rather than guessing: content inset is the
left-most element `x`; section height is the background rect's `h`; internal spacing
is the gap between successive element `y` values (they are frequently **not** a
uniform flex gap — here 33px then 53px, which needed a gap plus a margin).

### A full-page screenshot can render scroll-animated sections blank

Elementor's entrance animations (`_animation: fadeInUp`) start at `opacity: 0` and
are released by an IntersectionObserver. `page.screenshot({fullPage: true})` resizes
the viewport to the whole document, which can mean those observers never fire — the
capture comes out with entire sections empty, and it looks like the content is
broken when it is not.

Scroll in steps with a pause, then assert nothing is left faded before trusting a
screenshot:

```js
for (let y = 0; y < H; y += 500) { await p.evaluate(v => scrollTo(0, v), y); await p.waitForTimeout(220); }
await p.evaluate(() => [...document.querySelectorAll('h1,h2,h3,p')]
  .filter(e => parseFloat(getComputedStyle(e).opacity) < 0.95).length);   // expect 0
await p.evaluate(() => document.querySelectorAll('.elementor-invisible').length);  // expect 0
```

For a visual record, capture section-by-section in a normal viewport instead.

### Derive section padding from the design's background bands, not heading gaps

Heading-to-heading distance = padding + content, and content height differs whenever
the built copy is not identical to the design's. Matching those gaps with padding
manufactures empty space.

Full-width rects in the scene graph give the true section boundaries:

```js
nodes.filter(o => o.n.shape?.type === 'rect' && o.n.shape.width >= 1700)
```

Padding is then `firstHeading.y - band.y`. Skip sections whose height is set by a
side image — their padding is not inferable from text positions.

### A block-replacing CSS script must not assume its block is last

`grey-bannerfix.php` rebuilt Customizer CSS as *"everything before my marker" + my
new block*. That is correct only while its block is the final one. Once a second
script had appended a rhythm block after it, re-running the first silently deleted
the second — and its own success output looked clean, because it only checked for
the markers it knew about.

Splice on both sides, and verify **every** expected marker after writing:

```php
$before = substr( $css, 0, $pos );
$after  = substr( $css, $pos + strlen( $ownBlock ) );   // not '' 
foreach ( $allKnownMarkers as $m ) {
    echo strpos( $out, $m ) !== false ? "present" : "MISSING";
}
```

A "written N bytes" line proves nothing about what was lost.

### Match a design's grid at the page level, not one section at a time

Pulling a single section onto the design's measurements while the rest of the page
keeps the build's grid looks *worse* than leaving it alone — the mismatch reads as a
mistake even though that section is now the accurate one. Check what the design uses
across the whole artboard (the left-most `x` of every text block) and what the build
uses site-wide before changing one section's width.

Here XD used x=191 throughout while the site was built to 1400 (x=260); moving only
the hero made the banner look broken relative to its own page.

---

## Running scripts over REST (the bridge plugin)

Found while building and testing `remote/wpsd-bridge.php` on alphawolf.local.
Every one of these produced a result that looked like "the tool is broken".

### WordPress flushes your output buffer before your shutdown function runs

`ob_start()` + `register_shutdown_function()` inside a REST callback **loses the
output entirely** on any `exit()`.

WordPress registers `shutdown_action_hook()` at bootstrap, and that calls
`wp_ob_end_flush_all()`. Shutdown functions run in registration order, so core's
runs first, flushes your buffer straight to the client, and by the time yours
runs `ob_get_level()` is already 0. The script's output arrives as loose text
sitting *outside* the JSON, and the response reports an empty result.

Fix: give the buffer a **capturing callback** that stores the chunk and returns
`''`. Then it does not matter who flushes it or when — the content is yours and
nothing leaks into the body.

```php
ob_start( 'wpsd_bridge_ob_capture' );   // callback appends to a global, returns ''
```

This matters because nearly every script here ends `exit( "== DRY RUN ==" )`.

### `ob_get_clean()` invokes the handler *and* returns the buffer

So combining "what the callback captured" with "what `ob_get_clean()` returned"
**duplicates the entire output**. Close down with `ob_end_flush()` instead and
read only the callback's copy:

```php
while ( ob_get_level() > $level_before ) { ob_end_flush(); }
$output = $GLOBALS['...'];
```

### Core's fatal handler answers before yours can

`WP_Fatal_Error_Handler` is registered early, so on a fatal it emits its
"critical error" JSON with a 500 and your response is glued on after it. Filter
`wp_should_handle_php_error` to `false` while your script runs.

Better still, wrap the `include` in `try { } catch ( \Throwable $e )` — that
catches undefined functions, type errors and `ParseError`, which is nearly every
fatal a script here can raise, and lets you build a normal response.

### A UTF-8 BOM in any PHP file corrupts every JSON response

`Set-Content -Encoding utf8` in Windows PowerShell 5.1 **always writes a BOM**.
A BOM before `<?php` is emitted as body bytes on every request, so:

- `Invoke-RestMethod` silently fails to parse and hands back a bare string —
  every field reads empty and it looks like the endpoint returned nothing
- on a real site it causes "headers already sent", breaking redirects and cookies

Use `Set-Content -Encoding utf8NoBOM` (PS 7), or write bytes, or let PHP write
the file. The bridge now strips a leading BOM from any `.php` it is given and
reports `bom_stripped`, and the client shows any stray pre-JSON bytes rather
than hiding them.

It caught `config.json` here too — a BOM'd config still loads in PowerShell but
`json.load()` in Python throws `Unexpected UTF-8 BOM`.

### `catch [RuntimeException]` swallows every HTTP error in PowerShell

PowerShell wraps a cmdlet's terminating error in `ActionPreferenceStopException`,
which derives from `RuntimeException`. A catch clause for that type intercepts
`Invoke-WebRequest`'s 4xx/5xx before the real handler and re-throws it as a raw
stack dump. Catch the specific web exception, or just use one generic `catch`.

### `trap` does not survive dot-sourcing

`trap { }` in a dot-sourced helper does **not** become the caller's trap —
functions and variables transfer, trap handlers do not. Errors surfaced as
PowerShell stack dumps with the `throw` site quoted back. Use an explicit
`Stop-Wpsd`-style function that prints one line and exits.

### `Invoke-RestMethod -Credential` does not authenticate the REST API

It waits for a 401 challenge before sending credentials, and the WordPress REST
API does not issue one — so every call arrives unauthenticated. Build the
`Authorization: Basic` header by hand.

---

## Mutating nested Elementor nodes: iterate the REAL array by reference

A recursive walker that descends with

```php
foreach ( (array) ( $n['elements'] ?? array() ) as &$c ) { walk( $c ); }
```

silently loses every edit made below the top level. Both `(array)` and the
`?? array()` build a **temporary copy**, so `&$c` binds to the copy, not to
`$n['elements']`. The function reports success, the JSON round-trips, the write
"applies" — and the stored data is unchanged. It only bites for *nested*
targets: a top-level edit (`$d[$idx]['settings'] = ...`) writes through fine,
which is why `aw-banner-blue.php` worked and `aw-footer-affiliate.php` (a deep
icon-list) did not, first time.

Descend on the real property instead:

```php
if ( ! empty( $n['elements'] ) && is_array( $n['elements'] ) ) {
    foreach ( $n['elements'] as &$c ) { walk( $c ); }
    unset( $c );
}
```

Always re-read the stored meta after an apply to confirm the change is really in
the DB — "== APPLIED ==" only proves the code ran, not that the tree it edited
was the live one.

## A `LIKE '%2026/07/%'` scan misses Elementor's escaped-slash URLs

When search-replacing upload URLs across the DB (e.g. renaming media), the
obvious `WHERE meta_value LIKE '%2026/07/%'` filter **silently skips every
`_elementor_data` row**, because Elementor stores JSON with escaped slashes —
the path is literally `2026\/07\/file.png`, so `2026/07/` (plain slashes) never
matches. The first pass looked complete (73 postmeta rows changed) but left the
home page's hero reference untouched; the file was already renamed, so it would
have rendered broken. Verification caught it, a second pass with
`LIKE '%uploads%'` (a fragment with no slash, present in both escaped and plain
forms) fixed it.

Do the replacement itself with **slash-anchored tokens** — replace `/2.png`, not
`2.png` — so a numeric name can't match inside a longer one (`/2.png` is not a
substring of `/14.png`, because the char after `/` is `1`). The anchor survives
escaping: `/2.png` is still a substring of `\/2.png`. Use `strtr($s,$pairs)` (not
chained `str_replace`) so a size variant and its base can't double-replace, and
walk serialized values with `maybe_unserialize` → recurse → `maybe_serialize`
while treating Elementor's JSON as a plain string (it is not PHP-serialized, so
`maybe_unserialize` leaves it a string and `strtr` rewrites it in place).

## Two traps when testing a WooCommerce cart with Playwright

**`?add-to-cart=123` is unreliable behind WP Rocket** — the cached copy is served
and the item never lands in the session. Use the Store API
(`POST /wp-json/wc/store/v1/cart/add-item` with the `Nonce` header from a prior
GET), which is what the Cart block itself uses.

**Clicking "Add to cart" on a VARIABLE product does nothing and says nothing.**
The button is a "Select options" link until a variation is chosen. The Store API
is blunter and tells you why: `woocommerce_rest_missing_attributes — Missing
attributes for variable product.` Only simple products get `a.ajax_add_to_cart`;
target that class, or pass a variation ID rather than its parent.

## scrollWidth > clientWidth is not proof of horizontal scroll

On a page with a vertical scrollbar, `document.documentElement.scrollWidth` can
exceed `clientWidth` by exactly the scrollbar width (16px in Chrome) with no
horizontal scrolling at all. A naive check reports a false positive on almost
every page. `audit/hscroll.mjs` tests the thing a visitor can actually feel —
use it rather than rolling the comparison by hand. A real overflow looks like
the 206px the header mini-cart produced, not 16px.

## Finding the CSS rule that actually wins

`audit/whichrule.mjs <url> [width]` lists every loaded rule matching an element
that sets a horizontal margin, with its stylesheet and media query. Two things
it must check, both learned the hard way: the **`margin` shorthand** (the
longhands are empty on the rule's style object) and the **logical properties**
(`margin-inline`). Hello Elementor's `.alignwide{margin-inline:-80px}` was
invisible to the probe until `margin-inline` was added.

---

## PowerShell Compress-Archive makes plugin zips WordPress mis-installs

Symptom: uploading the bridge zip via Plugins > Add New > Upload installs it to
`wp-content/plugins/wp-site-doctor-bridge-1/wp-site-doctor-bridge/wpsd-bridge.php`
(double-nested), so Activate says **"Plugin file does not exist."** Extracting the
same zip by hand in cPanel works, which is the tell: WordPress's own
unzip + "find the single top-level folder" step is what fails.

Cause: Windows PowerShell 5.1 `Compress-Archive` writes entries with backslash
separators and no explicit directory entry. WordPress's `unzip_file()` +
`WP_Upgrader::install_package()` then can't identify the single root folder and
wraps everything in an extra folder named after the zip.

Fix: build the zip by hand with `System.IO.Compression.ZipArchive` (see
`scripts/build-bridge.ps1`), guaranteeing:
- forward-slash entry names,
- an explicit directory entry `wp-site-doctor-bridge/`,
- every file under that one folder, nothing at the archive root, no `__MACOSX`,
- LF line endings and no BOM on the PHP (a BOM breaks the plugin header).

Verify before shipping: extract the zip to a temp dir and confirm the only
top-level item is `wp-site-doctor-bridge/` with `wpsd-bridge.php` inside.

Note also: a plugin that executes PHP (the /run route) legitimately matches the
webshell signature that host malware scanners (ImunifyAV, Wordfence) look for
(`base64_decode` + `file_put_contents` + `include`). On a host that runs one, the
upload can be quarantined regardless of packaging — that is the scanner doing its
job, and the answer is the direct-file upload or host allowlisting, not hiding the
code. When cPanel-extract works but the WP uploader fails, it is packaging (this
gotcha), not a scanner.

### Plugin CSS class collisions are invisible until you probe

`.hdt-facts` in a new checkout stylesheet silently inherited
`display:flex`, a background and a gold left border from `hdt-front.css`, which
already used that class for the tour-page facts list. The symptom was icons that
looked "missing" and text with a mysterious indent — nothing in the new file
explained it, and reading the new CSS again would never have found it.

`audit/probe.mjs` (or `her-probe-el.mjs` on pages needing a cart) shows the
*computed* value and settles it in one run. Before shipping a stylesheet into a
plugin that already has one, diff the class names:

```bash
grep -o "\.hdt-[a-z0-9_-]*" old.css   | sort -u > /tmp/a
grep -o "\.hdt-[a-z0-9_-]*" new.css   | sort -u > /tmp/b
comm -12 /tmp/a /tmp/b        # anything printed is a collision
```

Scoped rules (`.hdt-booking-form .hdt-total`) are safe; bare ones are not.

### WooCommerce address field classes cannot be set from PHP

Filtering `woocommerce_checkout_fields` to drop `form-row-wide` from
`billing_city` / `billing_postcode` / `billing_phone` **does nothing visible**.
WooCommerce's `address-i18n.js` rewrites those classes on the client from the
country locale in `wc_address_i18n_params`, on load and on every country change,
and overwrites whatever PHP set.

Do it in CSS against the row id, which outranks the class and survives the
rewrite:

```css
#billing_city_field, #billing_postcode_field { grid-column: auto; }
```

### A checkbox <label> must not be display:grid

WooCommerce puts the input, the label text and `<abbr class="required">*</abbr>`
inside one `<label>`. As grid items the text and the asterisk land in different
tracks and the `*` drops onto its own line below the checkbox. Use a block label
with `padding-left` and an absolutely-positioned input instead, so the text and
the asterisk stay in one inline flow.

Same family of problem: inlining `dl.variation dt`/`dd` to compact the order
table removes the whitespace between them and renders `Departure:Wednesday`.
Add `dt { margin-right: .35em }`.

### The host answers some asset requests with a bot challenge

On heritagedaytours.co.uk, `/wp-admin/js/password-strength-meter.min.js` returns
**HTTP 200 with an HTML page** titled "Checking your browser…". The browser
parses that HTML as JavaScript, which is the `Unexpected token '<'` console
error on /cart/, /checkout/ and /my-account/.

Two consequences when auditing:

1. Filter that error out of "new JS errors" assertions or every run looks
   broken.
2. **Do not conclude a feature is broken from a headless run alone.** Re-test
   headed (`headless: false`) before reporting a payment or script fault to a
   client — and prove pre-existence by disabling your own code
   (`page.route('**/your.js', r => r.abort())`) rather than by reverting.

### Git Bash rewrites a bare `/` argument into a Windows path

```bash
node audit/shot.mjs / home 1440 full     # requests <site>/C:/Program Files/Git/
```

MSYS path conversion turns the lone `/` into `C:/Program Files/Git/`, so the
script politely screenshots the site's **404 page**. This looked exactly like
"the client's homepage is down" and cost a real detour — the page was fine the
whole time.

Tells: the screenshot is a 404 but `curl`/`fetch` and an in-JS `url('/')` both
return 200 with the right `<body class="home">`.

Fixes, in order of preference:

```bash
node audit/audit.mjs                                   # config urls, no shell involved
MSYS_NO_PATHCONV=1 node audit/shot.mjs / home 1440     # disable conversion
node audit/shot.mjs "https://site.tld/" home 1440      # pass an absolute URL
```

Anything taking a URL **path** as an argv is affected — `shot.mjs`, `hscroll.mjs`,
`rband.mjs`, `probe.mjs`. Paths with more than one segment (`/our-tours/`) are
left alone, so only the bare `/` bites.

### A helper called from two places must live where both can see it

`HDT_Tour_UI` is only `require_once`d inside `HDT_Elementor::widgets()`, on
`elementor/widgets/register`. Putting a shared helper there and calling it from
the checkout produced **no output and no error** — the `method_exists()` guard
just returned false and the row rendered empty.

Before sharing a static helper between two templates, check where its class is
actually loaded, not merely that the plugin is active. Guard-and-continue hides
this failure; assert it in the verification instead (count the rendered nodes,
not just "no fatal").

### Version plugin assets by filemtime, never by a constant

`HDT_Checkout::assets()` originally enqueued its CSS with `HDT_VERSION`:

```php
wp_enqueue_style( 'hdt-checkout', HDT_URL . 'assets/css/hdt-checkout.css', array(), HDT_VERSION );
```

Every redeploy of that file then shipped behind `?ver=1.3.0` — a URL the browser
already had. The site looked right in a fresh automation context and stale to
the client, who spent a round of review looking at the *first* stylesheet while
being told fixes were live. The failure is completely silent.

Use the file's own mtime, as `HDT_Booking::assets()` already did:

```php
$cv = file_exists( $css ) ? (string) filemtime( $css ) : HDT_VERSION;
```

Assert it, because "looks right on my machine" cannot catch it:

```js
const ver = new URL(link.href).searchParams.get('ver');
// fail if ver === the plugin version constant
```

Purging WP-Optimize does **not** help — this is the visitor's browser cache, not
the server's.

### A prepended alert becomes a grid item

Injecting a validation banner with `prependTo($panel)` where the panel is
`display:grid` puts the banner in the *first track*, pushing every sibling one
cell along. The panel silently rearranges the instant someone submits an
incomplete form — the worst possible moment for the layout to move.

Give any injected banner `grid-column: 1 / -1; order: -1` so it spans and stays
first whether the container is flex or grid.

### Judge alignment on stacked blocks only

An alignment sweep that compares every card's left edge will flag deliberate
two-up rows as broken. Separate the two rules: stacked blocks share a left edge
and width; row items share a top edge and each other's width. Otherwise the tool
reports a defect that is actually the design, and real ones get lost in it.

### "Plugin not found" after a file-manager upload

WordPress finds a plugin only by scanning for a PHP file with a plugin header,
either directly in `wp-content/plugins/` or **exactly one directory deep**. Two
uploads that look fine in a file manager and are both invisible to WordPress:

```
wp-content/plugins/my-plugin.zip                          <- a zip is never read
wp-content/plugins/wrapper/my-plugin/my-plugin.php        <- one level too deep
```

The correct shape is `wp-content/plugins/my-plugin/my-plugin.php`.

Diagnosing without shell access, in order:

1. `GET /wp-json/` with an application password — is the plugin's namespace
   registered? (Absent means not active.)
2. `GET /wp-json/wp/v2/plugins` — lists installed plugins and their **plugin
   file paths**. A nested copy shows a give-away path with two segments.
   Note this endpoint silently omits some nested installs, so an empty result
   is not proof of absence — check `plugins.php` too.
3. Request a known file directly (`/wp-content/plugins/<dir>/readme.txt`). A
   `200` proves the files are there; the themed 404 page proves they are not.
   This is how you tell "uploaded to the wrong place" from "not uploaded".

Fix by installing the zip through **Plugins > Add New > Upload**, which unpacks
to the right shape. `node audit/install-bridge.mjs` does this end to end.

Match on the plugin **file path**, never `data-slug`: a nested duplicate carries
the same slug, so slug-matching reports "already installed" and skips the fix.

### Some hosts 403 the first request of every browser context

Hostinger's CDN returns a bare `403` to the first request from a fresh browser
context, then `200` to everything after. Not user-agent detection — a real
Chrome UA changes nothing — and no cookie is required.

Since every tool here opens a context per breakpoint, this made a healthy
10-page site report as entirely `403`. `lib/lib.mjs` now retries `403/429/503`
navigations twice and **logs each retry**, so a real 403 is not hidden. Disable
with `"navRetries": 0`.

Before reporting a site as down from automation, confirm with a plain `fetch`
or `curl` — those get `200` on the first try because the challenge is per
browser context, not per IP.

---

## Age gates record consent in a COOKIE, not localStorage

`config.json` had `localStorageSeed` for getting past overlays. That is not
enough: age/professional-use gates usually set a cookie. alphawolflab.us uses
`acg_verified=1`.

Without it every screenshot is a picture of the interstitial, and — worse — the
audit measures the *gate's* text and reports every gated page as `THIN`. It is
easy to spend a while "fixing" a page that was rendering correctly all along
behind an overlay.

`lib/lib.mjs` now seeds cookies per context. In `config.json`:

```json
"cookieSeed": { "acg_verified": "1" }
```

Sanity check: the DOM behind an overlay is still fully rendered and measurable,
so `getBoundingClientRect()` numbers taken through a gate are *valid* even when
the screenshot shows only the splash. Trust the measurements, distrust the
picture — the reverse of the usual advice.

## `querySelector('a, b, c')` returns document order, NOT selector order

`audit.mjs` used `document.querySelector('main, .site-main, #main, article')`
intending "prefer main, fall back to article". A comma-separated selector
returns the **first element in the document that matches any branch**. On
`/coa/`, which has no `<main>` and 36 `<article class="coam__card">` cards, that
returned the first card: a 36-item archive was reported as 108 chars of content.

Two separate bugs were hiding here, and the first fix only exposed the second:

1. Query each selector in priority order, one at a time.
2. `<article>` is only a meaningful "main content" fallback when there is
   exactly one of them. On an archive, every card is an `<article>` — fall
   through to `body` instead.

Both are fixed in `audit/audit.mjs`. When a "thin content" result disagrees with
what you can see on screen, compare `main.innerText.length` against
`body.innerText.length` before believing the tool.

## Diagnosing a colour that "won't apply": read the cascade, don't guess

CDP gives you the actual matched rules in cascade order, which beats reasoning
about specificity from memory:

```js
const cdp = await ctx.newCDPSession(page);
await cdp.send('DOM.enable'); await cdp.send('CSS.enable');
const { root } = await cdp.send('DOM.getDocument', { depth: -1 });
const { nodeId } = await cdp.send('DOM.querySelector', { nodeId: root.nodeId, selector: '.coam-btn' });
const m = await cdp.send('CSS.getMatchedStylesForNode', { nodeId });
// m.matchedCSSRules is in cascade order — the LAST one setting the property wins
```

This turned "the button label is invisible" into "`.elementor-kit-366 a` (0,1,1)
beats `.coam-btn` (0,1,0)" in one shot, and made it obvious the fix was a
specificity bump rather than `!important`.

**Elementor's global kit stylesheet styles every `a` at specificity 0,1,1.** Any
plugin button styled with a single class will lose its colour on an Elementor
site. Pin the link states (`a.X:link, a.X:visited, ...` = 0,2,1) so the fix wins
on specificity rather than on enqueue order.

## "The fix didn't work" is usually the ?ver= — check before re-diagnosing

Second site this has cost time on (Heritage first, now Alpha Wolf). The pattern:

1. Deploy a CSS change. Verify it with Playwright. It passes.
2. The client refreshes and sees the old rendering.
3. Start re-diagnosing a bug that is already fixed.

Playwright uses a **fresh browser context every run**, so it never has a cached
copy and always fetches the new file. The client's browser does have one, and
plugins almost always enqueue with a hand-maintained constant:

```php
wp_register_style( 'coam', COAM_URL . 'assets/coa.css', array(), COAM_VERSION );
```

`COAM_VERSION` does not change when you edit the CSS, so the URL does not
change, so nothing re-fetches. Fix it at the source rather than telling people
to hard-refresh:

```php
$time = is_readable( $path ) ? filemtime( $path ) : false;
return false === $time ? COAM_VERSION : COAM_VERSION . '.' . $time;
```

**Diagnostic that settles it in one step:** read the `<link>` href off the live
page. If the `?ver=` is unchanged after a deploy, it is a caching problem, not a
CSS problem — stop looking at the stylesheet.

```js
[...document.querySelectorAll('link[rel=stylesheet]')].map(l => l.href)
```

Also: **verify logged-in as well as logged-out.** Page caches usually bypass for
admins, so the two states can render differently and the client is normally
looking at the logged-in one.

### WP Rocket needs more than one purge call

`rocket_clean_domain()` alone leaves minified and "used CSS" copies in place:

```php
rocket_clean_domain(); rocket_clean_minify(); rocket_clean_cache_busting();
if ( function_exists( 'rocket_clean_used_css' ) ) { rocket_clean_used_css(); }
```

Have the purge script *print which functions actually existed and ran* — the
earlier one on this site reported a cheerful "purged" while calling none of the
Rocket functions, which is how the stale file survived.

## A host scanner can delete uploaded brand logos, silently

On alphawolflab.us, an uploaded PNG of the **Cash App logo** was removed from
disk within minutes of every upload. Five other payment logos in the same
directory, uploaded seconds apart, were untouched. There is no security plugin
in WordPress — it is server-side.

What the diagnosis looked like, and the wrong turn in the middle of it:

1. `pay-cashapp.png` uploaded fine, then 404'd. Re-uploaded, gone again.
2. Same bytes as `pay-ca.png` survived the first check → concluded "filename
   trigger". **Wrong.** It was deleted too, just several minutes later.
3. Checked the directory listing again rather than trusting the earlier check.
   Both names gone; the other five present → content signature, not filename.

The lesson is about *timing*: a scanner runs on an interval, so "the file is
still there" a minute after upload proves nothing. Re-check after several
minutes before concluding anything, and confirm against the **directory
listing**, not an HTTP request — a 404 alone cannot distinguish "deleted" from
"cached 404" or "blocked by a WAF rule".

Heavily-impersonated payment brands (Cash App, PayPal, Zelle) are the likely
triggers, since their logos ship inside phishing kits.

**Do not obfuscate the asset to get it past the scanner.** Recompressing,
renaming, or base64-inlining it into a PHP file is evasion, it can escalate to
the whole file being quarantined (a base64 blob in a PHP file is itself a
malware signature), and it leaves a booby trap for the next person. Either get
the host to whitelist the path, or render the payment method as text.

## An Elementor page with no `post_content` is not necessarily empty — check both

`php/orphans.php` measures `post_content`, which is zero for most Elementor
pages because the builder stores its tree in the `_elementor_data` postmeta. So
"EMPTY PUBLISHED PAGES" on an Elementor site is usually noise.

Usually — but not always, and the failure mode is symmetrical:

* Assume it's noise and you miss genuinely blank pages. On the Confraternity
  site all ten flagged pages had `post_content` **and** `_elementor_data` at
  zero bytes. They really were empty.
* Assume it's real and you "fix" pages that were fine all along.

Check both fields before concluding either way:

```php
$content = strlen( $p->post_content );
$builder = strlen( (string) get_post_meta( $p->ID, '_elementor_data', true ) );
```

`audit.mjs` will not save you here: an empty Elementor page still returns 200
and still renders the header and footer templates, which is enough text to clear
the thin-content threshold.

---

## Git Bash rewrites any argument that starts with `/`

Running the audit tools through the Bash tool on Windows, this:

```bash
node audit/rband.mjs "/financial-planning/" out 1440 1050 9
```

screenshots a **404 page**. MSYS path conversion turns the leading-slash argument
into a Windows path, so the script receives:

```
C:/Program Files/Git/financial-planning/
```

Nothing warns you. `rband` reports a page height (1407px — the 404 page), writes
its bands, and says "nothing past the viewport", so it reads as a clean pass on a
page you never looked at. It cost a full diagnostic detour chasing a "collapsing
document" that was only ever a wrong URL.

Two ways out, either is fine:

```bash
MSYS_NO_PATHCONV=1 node audit/rband.mjs "/financial-planning/" out 1440 1050 9
node audit/rband.mjs "https://site.test/financial-planning/" out 1440 1050 9
```

The full URL form is immune. **If a tool's output looks structurally wrong —
wrong page height, no content, unexpected title — print `page.url()` before
believing anything else.**

---

## "Delay JavaScript execution" makes a correct page screenshot as empty voids

WP Rocket's *Delay JavaScript execution* (also LiteSpeed, Perfmatters,
FlyingPress) holds every deferred script until the visitor moves the mouse,
scrolls, touches or presses a key. Headless automation does none of those, so
Elementor's animation JS never boots and every widget carrying an entrance
animation keeps the `.elementor-invisible` class it ships with:
`visibility:hidden`, still occupying its full height.

On greysonprivate that was **26 invisible widgets and ~2000px of apparently
blank page**. It does not look like a bug in the tooling — it looks exactly like
a real layout defect, correctly spaced empty regions where content should be. I
reported an "invisible credentials heading" as a site defect on the strength of
it. It was not; it was this.

`lib.mjs` now exports `wake(page)` and `open()` calls it. It sends a real mouse
move, wheel and keypress, then walks the page slowly enough for Elementor's
intersection observer to fire.

**The dwell time matters.** Scrolling in 110ms steps outran the observer and left
16 of 26 widgets hidden — a partial reveal, which is worse than none because it
looks like it worked. 260ms per step reveals all of them. Anything still hidden
afterwards is forced into its finished state and the count is returned, so a
non-zero return is information, not a finding.

Any new script that builds its own `browser.newContext()` must call `wake()`
itself — `open()` covers the common path, but `audit.mjs`, `rband.mjs`,
`hscroll.mjs` and friends each construct their own.

---

## WP Engine refuses to let PHP write `.php` files anywhere

The toolkit's usual "drop an mu-plugin in" move does not work on WP Engine:

```
ERROR: HTTP 500 - Write failed - check permissions on mu-plugins
```

`file_put_contents()` returns `false` for any path ending in `.php`, in
`mu-plugins`, `plugins` or `uploads` alike. The identical bytes written as
`.css` succeed, and `mu-plugins/` is otherwise writable — so it is the
**extension**, not the directory or the permissions.

Isolate it that way before assuming anything: change one variable at a time
(`.php` into `uploads`, `.css` into `mu-plugins`) and the pattern falls out in
two calls.

Where to put CSS instead, in order of preference:

1. **Elementor page Custom CSS** (`_elementor_page_settings['custom_css']`) —
   page-scoped automatically, and the client can find it at Page Settings →
   Advanced → Custom CSS. Needs Elementor Pro.
2. **Customizer Additional CSS** (`wp_update_custom_css_post()`) — global, but
   discoverable and editable by the client.

Both are database-stored, so neither needs a file write.

---

## A failing remote call reported `HTTP 500 - ` with no message

`scripts/_remote.ps1` read the error body from `$_.Exception.Response`'s stream. On
Windows PowerShell 5.1 that stream has usually already been consumed by the time
the catch block runs, so it returned nothing and the actual reason — *"Write
failed - check permissions on mu-plugins"* — was thrown away. Fixed: read
`$_.ErrorDetails.Message` first and fall back to the stream.

---

## WP Rocket's Remove Unused CSS silently serves a stale stylesheet

Change any CSS — Elementor's generated file, a page's Custom CSS, an mu-plugin —
and the front end may not move at all, because WP Rocket serves
`<style id="wpr-usedcss">`: a single stylesheet built from a saved map of "CSS
this page actually uses". Rules added after that map was built are simply absent
from it.

The tell is that the rule is verifiably **on the page** (`grep` the HTML finds
your selector) while `getComputedStyle` reports the property unset. If you look
for a `post-<id>.css` link tag to check, note there may not be one — RUCSS
inlines everything and drops the link.

`rocket_clean_post()` and `rocket_clean_domain()` do **not** clear it, and
`rocket_clean_used_css()` does not exist in current versions. What works:

```php
$wpdb->query( "TRUNCATE TABLE `{$wpdb->prefix}wpr_rucss_used_css`" );
```

The CSS itself lives in gzipped files under `wp-content/cache/used-css/`, keyed
by the `hash` column, so a raw string search on those files finds nothing until
you `gzdecode()` them. The path is
`used-css/{site}/{hash[0]}/{hash[1]}/{hash[2]}/{substr(hash,3)}.css.gz` — glob
for `substr($hash,3).'.css.gz'` rather than reconstructing it.

After truncating, the first request rebuilds the map, so **load the page twice**
before measuring.

---

## `null - null === 0`, and other ways an alignment probe passes on nothing

Measuring alignment as a difference between two `getBoundingClientRect().top`
values reports a perfect `0` when *both* selectors miss:

```js
const t = id => { const e = document.querySelector(sel); return e ? e.top : null; };
t('a') - t('b')            // null - null === 0  -> "aligned!"
```

A whole 36-width sweep came back clean this way while the page was still visibly
misaligned. Return `NaN` for a miss and assert on it, or check presence
explicitly — a measurement that cannot fail is not a measurement.

The same class of error: identical byte counts across unrelated URLs (an age
gate), and a comma-separated `querySelector` silently returning document order
rather than selector order.

## Elementor container padding lives on `.e-con-inner`, not the section

Setting `padding` on `.elementor-element-<id>` for a boxed container looks like
it works — the rule applies, the computed value is what you set — and the page
does not move. The visible space is on the child `.e-con-inner`:

```
whynow section   pad 6px/0px      <- what I kept setting
whynow inner     pad 96px/96px    <- where the space actually was
```

This cost two failed attempts at the same gap. `padding` on the section is real
but sits *outside* the inner box, so on a boxed container it usually computes to
nothing visible. Target `.elementor-element-<id> > .e-con-inner`.

Corollary: measure `paddingTop`/`paddingBottom`/`rowGap` on **both** the section
and its `.e-con-inner` before writing any spacing rule. `audit/gr-pad.mjs` does
this for a list of selectors.

## Space before a widget can be the parent's `row-gap`, not a margin

A widget that is the *third* flex item in a two-column row inherits the row's
`row-gap` as its top spacing. No margin anywhere reports it, so it reads as
unexplained air, and the instinct is to fix it with a negative margin. Walk the
ancestor chain and print `display` / `rowGap` at each level — `audit/gr-chain.mjs`.

## `<p>&nbsp;</p>` spacers in Elementor text editors

Hand-authored content in these client sites uses empty paragraphs as spacers.
They are invisible in Grep output, survive every CSS fix, and are the usual real
cause of "too much space after the bullets". Strip with:

```php
preg_replace( '~<p>(?:\s|&nbsp;|&#160;|\xc2\xa0)*</p>~u', '', $editor )
```

Found on both `/financial-planning/` and `/retirement-planning/`.

## Inline SVG instead of uploading, for supplied icon artwork

Putting a client-supplied SVG in the media library means enabling SVG uploads
site-wide, which is a standing security trade-off (SVG can carry script) taken
for the sake of two decorative icons. Inlining the markup in an Elementor `html`
widget keeps the exact artwork and its own `fill`, and changes no site setting.

Size it with `height:<n>px; width:auto` and **not** `max-height`: these files
carry explicit `width`/`height` attributes, and `max-height` caps the height
while leaving the attribute width in place, distorting the icon. With a `viewBox`
present, `height` + `width:auto` scales correctly from the aspect ratio.

## Sampling a hover mid-transition reads as a failed fix

A CTA hover check reported one button as FAIL with `bg=rgb(56,60,64)`,
`border=rgb(231,232,233)` — values that are on the path from gold to navy, not a
wrong result. The button was still animating its `.3s` transition when the
assertion sampled it.

Sample at **>= 400ms** after `hover()` for a `.3s` transition, and when something
fails, print the value at several delays before believing it:

```
rest  : bg=rgb(208, 151, 72)
+150ms: bg=rgb(62, 64, 64)     <- would have failed
+400ms: bg=rgb(37, 49, 63)     <- correct
```

Same class of error as the delay-JS `.elementor-invisible` artifact: the page is
mid-flight, not broken.

## Site-wide CSS on a site where you cannot write PHP

WP Engine refuses `.php` writes under `wp-content`, so no mu-plugin. With
Elementor Pro the usable slot is the **active kit's** `_elementor_page_settings`
`custom_css` (`get_option('elementor_active_kit')`), which loads on every page
including header/footer templates. Page-level custom CSS does **not** reach the
header — the header is a separate `elementor_library` template.

Always fence an injected block with a marker comment and replace on the marker,
or repeated runs silently stack duplicates.

## Elementor page Custom CSS is NOT auto-scoped — it leaks into header/footer

A page's Custom CSS is emitted as written. A rule targeting a widget *type*
rather than an element id therefore matches that widget type **anywhere on the
page, including the header and footer templates**, which render inside the same
document.

This shipped a real defect. Bullet-list styling on page #227:

```css
.elementor-widget-icon-list .elementor-icon-list-icon svg{ width:7px; height:7px; }
```

also matched the header's "Client Login" icon list and shrank its 18px account
icon to 7×7 — but only on `/financial-planning/`, the one page where that CSS
loads. It looked like a deformed icon on a single page, which is exactly how it
was reported, and it is easy to misread as a caching artifact.

**Rule: prefix every widget-type selector in page Custom CSS with the page's own
wrapper** — `.elementor-227 .elementor-widget-icon-list …`. Element-id selectors
(`.elementor-element-<id>`) are inherently safe. Elementor's `selector` keyword
also resolves to the page wrapper.

Detect it by measuring the same element across several pages: one page
disagreeing with the rest points at that page's CSS, not at the element.

## Rebuilding a too-faint asset instead of stacking it

`wave-clear.png` was a *palette* PNG, pure white, 8 alpha levels, max 75/255. No
Elementor control can strengthen that — opacity only ever weakens a layer — so
it had been bodged by painting the same image as eight stacked background
layers to reach an effective alpha of 0.94.

Rescaling the alpha channel in the asset itself (75 → 255) is the actual fix and
hits the design's amplitude exactly. Blur the alpha afterwards: 8 levels scaled
by 3.4 leaves ~34-unit steps that band visibly across a soft gradient.

```python
full = alpha.point(lambda v: min(255, int(round(v*255/75))))
smooth = full.filter(ImageFilter.GaussianBlur(radius=2.0))
```

Check the composite before uploading: `alpha_composite` over the section's real
base colour, then read `getextrema()`. Amplitude went 1 → 5, matching the XD
artboard, and the eight layers collapsed to one.

## Two adjacent sections cannot share one `cover` background

Sizing the same image `cover` on two stacked sections gives two unrelated crops
at different scales, so a continuous graphic restarts at the boundary. To span
one image across both, size **both** to the combined height and anchor opposite
edges:

```css
.head { background-size:100% 938px; background-position:center top;    }
.wheel{ background-size:100% 938px; background-position:center bottom; }
```

Measure the combined height per breakpoint across every page using the template
first — here it varied by at most 45px of ~920, invisible at this amplitude.

## Find horizontal overflow by enumerating what crosses the edge, not by guessing

`scrollWidth - clientWidth` tells you there is overflow, not what causes it, and
the obvious suspect is often innocent. A carousel had been blamed for a +10px
scroll for several sessions; the actual culprit was its **navigation arrow**,
positioned 30px outside the slider by the widget's own settings.

```js
for (const e of document.querySelectorAll('body *')) {
  const b = e.getBoundingClientRect();
  if (b.width && b.height && b.right > document.documentElement.clientWidth + 0.5)
    console.log(e.className, b.right);
}
```

Content inside an `overflow:hidden` track will show in that list but does not
scroll the page — confirm against `excess` before acting. Check `b.left < 0`
too: `scrollWidth` does not report content at negative x.

## Marker-fenced CSS blocks need a START and an END marker

Injecting a block that keeps "everything before my marker" and re-appends itself
silently deletes any block written after it. Use a matched pair and splice
between them:

```php
$head = substr( $old, 0, strpos( $old, $MARK ) );
$tail = substr( $old, strpos( $old, $END ) + strlen( $END ) );
$new  = trim( $head . $CSS . $tail );
```

Then assert the *other* blocks survived in the same run.

## A widget you cannot find on the page is probably in a reusable template

Changing a carousel on the page it appears on may not change it, because the
widget can live in an `elementor_library` template the page embeds. Search the
whole `postmeta` table rather than the page you are looking at:

```sql
SELECT post_id FROM wp_postmeta
WHERE meta_key='_elementor_data' AND meta_value LIKE '%jet-listing-grid%'
```

Skip `revision` rows. Then edit the template — that fixes every page embedding it.

Also delete `_elementor_element_cache` on the template after writing. It stores
rendered markup, and `files_manager->clear_cache()` does not clear it, so the old
HTML is served indefinitely.

## Never count carousel slides to learn how many items exist

A Swiper in loop mode injects clones, so `.jet-listing-grid__item` and
`.swiper-slide` both overcount — 3 posts rendered as 9 slides in one place and 5
in another. Count the source instead:

```php
wp_count_posts( 'team-members' )->publish
```

Getting this wrong led me to tell the client a 3-item slider held 5 items and was
therefore justified.

## `ul + p` fails when the paragraph is a separate Elementor widget

Two widgets that look like one block of prose are two DOM subtrees. A sibling
combinator across them matches nothing, and the rule fails **silently** — no
error, no visual change, and a careless check will call it fixed.

Before writing an adjacency rule, confirm both elements share a parent:

```js
document.querySelector('#a').parentElement === document.querySelector('#b').parentElement
```

If they do not, the space is the parent container's `row-gap`, not a margin.

## Reading `::before` colour when the marker is painted with `background`

`getComputedStyle(li,'::before').color` returns the inherited text colour and
tells you nothing about a dot drawn as `content:""` + `background`. Read
`backgroundColor`. Misreading this nearly had me "fix" bullets that were already
the right colour.

## An element screenshot clips anything hanging outside the element

Markers positioned at `left:-18px` hang into the parent's padding. `element
.screenshot()` crops to the element's own box, so they vanish from the image
while being perfectly visible on the page. Verify negative-offset decoration
with a viewport clip, not an element shot.

## `document.styleSheets` under-reports: cross-origin sheets throw

Scanning for your own rules and getting `0` may mean the sheets are unreadable,
not absent — here 33 of 43 were cross-origin (CDN/optimiser). Never conclude
"my CSS is not applying" from a rule scan. Assert on a computed value that only
your CSS could produce.

## Guard `:hover` with `@media (hover:hover)` whenever a click toggle shares the state

iOS applies `:hover` on tap and leaves it applied until the user taps elsewhere.
If the same element also toggles a class on click, the two fight: the first tap
sets both, the second clears the class but leaves the stuck `:hover`, so the
element appears not to respond.

```css
.card.is-on { background: navy; }
@media (hover:hover) { .card:hover { background: navy; } }
```

Touch gets the class, mouse gets hover, neither interferes.

Related: never put `:hover` in the same selector list as a class rule. One
unsupported or invalid selector invalidates the entire list in CSS, silently
dropping the class rule too. Write them as two blocks.

## WooCommerce attribute term order: use `name_num`, not `menu_order`

Setting an attribute's `order_by` to `menu_order` and writing `order_<taxonomy>`
term meta is what the admin UI does, but `wc_get_product_terms()` still returned
terms alphabetically ("10mg, 5mg") on the front end.

`name_num` sorts on the leading number in the term name and needs no per-term
data — correct for any `<number><unit>` naming scheme.

```sql
UPDATE wp_woocommerce_attribute_taxonomies
SET attribute_orderby = 'name_num' WHERE attribute_name = 'strength';
```

Then `delete_transient('wc_attribute_taxonomies')`, invalidate the
`woocommerce-attributes` cache group, and clear each product's transients.

## Hostinger: OPcache holds a just-written mu-plugin for ~2 seconds

`opcache.validate_timestamps=1` with `revalidate_freq=2` means a file written
through the bridge can serve its OLD compiled version for a couple of seconds.
A verification run started immediately after the upload reads stale CSS and looks
like the change did not apply.

Either sleep past the window or invalidate explicitly:

```php
opcache_invalidate( WPMU_PLUGIN_DIR . '/my-plugin.php', true );
```

There is also a CDN in front (`Server: hcdn`, `x-hcdn-cache-status`), so append a
cache-busting query string to every verification request.

## Age gate redirects bare product URLs

`curl` on a DualCore product URL 302s to `/age-verify?return=…`. The browser
tooling is fine because `config.dualcore.json` seeds `acg_verified=1`, but any
raw HTTP check must send that cookie or it measures the gate, not the page.

## An apostrophe inside a single-quoted PHP string terminates it

CSS or JS held in `$css = '…'` cannot contain a bare `'`. A prose comment such as
`/* each item's contribution */` inside that string is a parse error, and
"fixing" it to `''` makes it worse. Reword to avoid the apostrophe, or use a
heredoc. `scripts/php.ps1 -l` catches it; `scripts/rfile.ps1` also parse-checks before
writing, which is what stopped a broken mu-plugin reaching the site.

## Read the label in a product photo; never trust the filename

Client image sets abbreviate and omit. In one batch `CJC1295.png` was the 5mg
vial, `ghkcu.png` the 100mg, `water.png` the 10ml, and `TESSA`/`Reta-3`/`Tirz-2`/
`MT-1` were Tesamorelin/Retatrutide/Tirzepatide/Melanotan. Mapping on filename
alone would have put the wrong strength on several products.

Crop the label band and build a contact sheet — one image read is far cheaper
than a wrong vial on a live shop:

```python
crop = im.crop((int(w*0.18), int(h*0.32), int(w*0.82), int(h*0.74)))
```

## Client PNGs are usually far too heavy to ship as-is

1254x1254 vial renders arrived at ~1.7 MB each, 58 MB for 34 products. WebP q88
took it to 2.35 MB — a 96% cut with mean per-pixel difference under 1/255.
Always measure the difference rather than assuming quality loss:

```python
ImageChops.difference(orig, converted).convert('L').getextrema()
```

Check what the site already serves first; matching the existing format is an
easier sell than introducing one.

## Do not grab the first gallery `img` when verifying product photos

WooCommerce galleries include a zoom control rendered as an emoji SVG
(`1f50d.svg` = magnifier). A naive `.woocommerce-product-gallery img` selector
matched it on every product, so a verification run reported "image never swaps"
for six working products. Filter out `.svg` and take the largest rendered image.

## Localise overflow with scrollWidth vs clientWidth, not the right-edge scan

`getBoundingClientRect()` reports the **unclipped** box, so an element inside an
`overflow:hidden` parent shows up in a right-edge scan while contributing nothing
to the page scroll. That sent me after a decorative SVG for several rounds while
the real cause was a heading two levels up.

Walk containers and compare their own scroll box instead:

```js
const walk = (el, d) => { for (const c of el.children) {
  if (c.scrollWidth - c.clientWidth > 1 && c.clientWidth > 0) {
    console.log('  '.repeat(d), c.tagName, c.className, c.scrollWidth, c.clientWidth);
    walk(c, d + 1); } } };
walk(document.body, 0);
```

This names the culprit in one pass. Confirm by hiding the suspect and re-reading
`excess` — if it does not move, it was never the cause.

## `wp_strip_all_tags()` on block content returns nothing

A WooCommerce block page stores `<!-- wp:woocommerce/checkout /-->` — all HTML
comments. Stripping tags gives an empty string, so a page audit reports "0 chars"
and the page looks broken when it is perfectly fine. Use `has_block()` to test
for block-built pages before concluding anything is missing.

## Missing icons: check the Font Awesome MAJOR VERSION, not just whether it loads

An icon that renders as an empty box with the right `font-family` and
`::before { content: none }` is a **name that does not exist in the loaded
version**, not a loading failure. FA5 and FA6 renamed a large part of the set:

| FA6 (what kits ship) | FA5 (what Elementor bundles) |
|---|---|
| `fa-circle-check` | `fa-check-circle` |
| `fa-shield-halved` | `fa-shield-alt` |
| `fa-magnifying-glass` | `fa-search` |
| `fa-truck-fast` | `fa-shipping-fast` |
| `fa-file-lines` | `fa-file-alt` |
| `fa-vial-circle-check` | *(no equivalent)* |

Grep the stylesheet before assuming which you have:

```php
$c = file_get_contents( $fa_css );
preg_match( '/Font Awesome Free ([0-9.]+)/i', $c, $m );   // version
strpos( $c, 'fa-circle-check' );                          // FA6 marker
```

**Never load FA5 and FA6 together** — both claim `.fas` and point it at their own
family, so the later one wins and codepoints differ between versions. That turns
missing icons into *wrong* icons, which is harder to spot.

Search the whole plugins directory before adding a CDN: a template kit that
authored the icons usually bundles the matching version already.

## Sample a logo for brand colour instead of eyeballing it

Filter to opaque, saturated, mid-bright pixels — a transparent PNG is mostly dark
glow and antialiasing, which drags any naive average toward black:

```python
h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
if a > 220 and s > 0.55 and v > 0.45 and 205 < h*360 < 245:  # the blue letterforms
```

Then check contrast before shipping the change — the more saturated brand colour
is often *darker* and improves contrast rather than harming it (here white-on-blue
went 4.85:1 -> 8.52:1).

## Find out what actually renders an archive before hooking WooCommerce

A WooCommerce archive may be built by an Elementor `product-archive` template, in
which case `woocommerce_before_main_content` and friends do not put markup where
you expect. Walk up from `ul.products` in the rendered DOM:

```js
let e = document.querySelector('ul.products');
while (e && e.tagName !== 'HTML') { console.log(e.tagName, e.className); e = e.parentElement; }
```

A wrapper like `div.elementor.elementor-49.elementor-location-archive` names both
the mechanism and the template id. Searching `elementor_library` by title keyword
can miss it — search by `_elementor_template_type` instead.

## Build WooCommerce filters on WooCommerce's own query vars

No filter plugin is needed for price and attribute filtering, and no custom
`WP_Query` either — WooCommerce already parses these from the URL:

- `min_price` / `max_price` → `WC_Query::price_filter_post_clauses()`
- `filter_<attr>=a,b` plus `query_type_<attr>=or` →
  `WC_Query::get_layered_nav_chosen_attributes()`, mapping to `pa_<attr>`

Emit them as plain links and a small GET form and filtering keeps working through
pagination, sorting and category archives, with JavaScript disabled. Point
categories at their term archives rather than a query param — that is the
canonical WooCommerce URL and stays indexable.

## Moving an Elementor widget beats recreating it

When restructuring a template, splice the existing widget node into its new
parent rather than building a fresh one. Every style setting the client has
applied travels with it, and the diff stays small enough to verify by eye.

## WooCommerce add-to-cart sits at different depths for simple vs variable

```
simple    form.cart > button.single_add_to_cart_button
variable  form.cart > .single_variation_wrap
                    > .woocommerce-variation-add-to-cart
                    > button.single_add_to_cart_button
```

Neither intermediate wrapper stretches, so a width or flex rule on the button
alone silently fails on variable products only — it measured 151px inside a
315px wrapper while the simple product was already correct. Style the wrappers
too, and always test one of each type.

## Split client copy on its own headings rather than rewriting it

When a design wants content reorganised into columns, and the source copy has a
consistent shape, split it instead of authoring new text:

```php
$parts = preg_split( '~<h3[^>]*>\s*Product Details\s*</h3>~i', $content, 2 );
if ( count( $parts ) < 2 ) { return $content; }   // always fall back untouched
```

The client's words are preserved verbatim, nothing is invented, and a product
that does not follow the pattern degrades to the original layout.

## Park the mouse before screenshotting a WooCommerce gallery

The zoom plugin injects `.zoomImg` at full resolution and positions it under the
cursor, so an automated screenshot shows a magnified crop and looks like a broken
image. Enumerate the gallery images before believing it:

```
[0] emoji  1f50d.svg          <- the magnifier control
[1] wp-post-image 600x600     <- the real image, correct
[2] zoomImg 1254x1254         <- the overlay that looked like a crop
```

## Check supplied "certificates" before publishing them

Two sets arrived on the same day from the same client group. One was forged, one
was not, and the difference was visible without any special tooling:

| signal | forged set | genuine set |
|---|---|---|
| filenames | `Create_A4_laboratory_test_report_…`, `Recreate_…` — the generation prompts | product names |
| dimensions | 1792x2400 (a 2K text-to-image output) | 1033x1522 (document aspect) |
| task numbers | **duplicated** — same number on two files generated a minute apart | 10 distinct |
| batch codes | free-varying, unrelated to dates | correlate with the test dates |
| count | 18 near-identical attempts at one document | one per product |

Cheap checks that caught it: read the filenames, compare pixel dimensions, and
tabulate task numbers and batch codes across the whole set looking for repeats.

Never rename or attach a fabricated certificate — renaming to match products is
the step that turns it into a publishable COA.

## Record "See certificate" rather than inventing a missing figure

Two genuine reports had no purity row — one said "peptide purity not included"
in its Tests Requested. Leaving the field blank hides the gap and filling it in
fabricates a result. COA Manager's own field help asks for `See certificate`,
which is the honest third option. Look for that pattern in any plugin before
deciding a field is mandatory.

## A grid that renders as one column is usually a boxed ancestor, not the grid

`.coam` was `display:grid` and still stacked. The grid was fine — an Elementor
container four levels up had `max-width:760px`, so there was never room for a
second track. Walk the ancestors printing width and max-width before touching
`grid-template-columns`:

```js
let e = document.querySelector('.grid');
while (e && e.tagName !== 'BODY') {
  const c = getComputedStyle(e);
  console.log(e.className, Math.round(e.getBoundingClientRect().width), c.maxWidth, c.display);
  e = e.parentElement;
}
```

## `object-fit: contain` is the wrong default for document thumbnails

Fitting a whole A4 page into a 230px card makes it a grey rectangle. `cover` with
`object-position: top` shows the masthead and identifying fields at a readable
size, which is what a preview is for — the full document should be one click
away. Applies to certificates, invoices, spec sheets, any tall document.

## Test dark mode when a plugin ships CSS variables

A plugin can carry its own `prefers-color-scheme: dark` block. On a light-only
site that produces a half-dark component — dark cards in a white page — and any
text colour you hardcoded goes invisible on it. The bug is invisible to you
because headless Chrome defaults to light:

```js
browser.newContext({ colorScheme: 'dark' })
```

Pin the plugin's variables to the light values *inside the same media query*
rather than trying to out-specify each rule.

## `:root` custom properties tie on specificity — use `:root:root`

Overriding a plugin's CSS variables from an inline style fails silently when both
use `:root`: equal specificity, so source order decides, and inline styles
attached to a dummy handle are not reliably last. `:root:root` (0,2,0) wins
deterministically. Same trick as repeating an element-id class.

## Search a site for build/developer text before handover

Internal notes reach the front end. Grep the rendered copy for the toolchain:

```
/COA Manager plugin|included with the build|WordPress admin|this build|plugin included/i
```

Also worth a pass for claims the data contradicts — "every lot", "all
certificates", "every batch" — and compare against what the database actually
holds.

## Windows: `shutil.move("images", "Images/...")` copies a folder into itself

Windows filesystems are case-insensitive, so a folder named `images` and a
destination named `Images` are **the same directory**. Moving one into the other
starts a recursive self-copy: it duplicated 713 files into `Images/images (2)`
before dying on a long path, leaving a half-copy that looked like real content.

Two habits that avoid it:

- Compare destination names **case-insensitively** against what already exists
  before creating them, and fold into the existing folder rather than creating a
  second casing.
- Before deleting anything that looks like a duplicate, prove it: index both
  trees by relative path + size and confirm the copy contributes nothing unique.

```python
missing = [r for r in copy if r not in parent]
mismatch = [r for r in copy if r in parent and parent[r] != copy[r]]
# delete only when both are empty
```

## Bulk file moves need a manifest, not confidence

Write every move to a CSV as it happens (`moved_from,moved_to`). It costs
nothing, turns an irreversible reorganisation into a reversible one, and is the
only way to answer "where did my file go" afterwards.

Also check the date spread before bucketing by date — 93% of that Downloads
folder was a single month, so date folders would have achieved nothing. Group by
whatever the filenames actually cluster on instead.

## Check `woocommerce_permalinks` before testing product URLs

WooCommerce's product base is configurable and `%product_cat%` may be in it:

```json
{"product_base":"\/shop\/%product_cat%","category_base":"product-category"}
```

Two things follow. Testing `/product/<slug>/` on such a site proves nothing - it
404s whatever you did. And **renaming a product category slug silently rewrites
every product URL that sits under it**, which makes a "cosmetic" category rename
a site-wide URL change. Check the base before touching a category slug.

## WordPress redirects old POST slugs, never old TERM slugs

`_wp_old_slug` + `wp_old_slug_redirect()` covers posts and custom post types.
Renaming a category or tag slug just 404s the old URL - there is no built-in
equivalent, and Yoast free has no redirect manager. Ship the redirect yourself:

```php
add_action( 'template_redirect', function () {
    if ( ! is_404() ) { return; }
    // map old term slug -> new, rebuild the path, wp_safe_redirect( $t, 301 )
}, 1 );
```

## On a 30-second host, batch writes or the data ends up half-applied

22 `wp_update_post()` calls with WooCommerce hooks attached exceeded the limit
and returned 503 **after 16 had committed**. The visible failure was not the
problem - the silent one was that a product changed slug without its
`_wp_old_slug` being written, so its old URL 404'd while the rest redirected.

Make the script idempotent so a re-run completes it, then **verify the side
effects separately** rather than assuming a clean re-run repaired everything.

## pepcore.com: the DB prefix is `fanz_`, not `wp_`

Every table is `fanz_*`. A query written against `wp_wc_orders` returns nothing
rather than erroring, so it reads as "no data" instead of "wrong table".
Always take the prefix from `$wpdb->prefix`.

## pepcore.com has an age gate — curl sees 302 on every page

Every front-end URL 302s to `/age-verify?return=<path>`. A `curl` health check
therefore reports 302 everywhere and an empty body, which looks exactly like a
site you have just broken. It is not. Use the Playwright tooling
(`audit/*.mjs`), which carries the gate cookie, or follow redirects and expect
the age-verify page.

## `scripts/rfile.ps1 put` caps at ~512KB and will not create directories

HTTP 413 above roughly 512KB of raw file (base64 adds a third). Probed on
pepcore: 256KB ok, 512KB ok, 1MB 413. Split larger files, upload the parts,
concatenate server-side, and verify with **md5 against the local original** —
matching byte counts do not prove correct ordering.

`put` into a directory that does not exist fails with no useful message; mkdir
server-side first.

## Triggering an UpdraftPlus backup without the UI

Free UpdraftPlus has no `backup` wp-cli subcommand, and
`UpdraftPlus_Commands::backupnow()` needs an admin capability context and calls
`die`. What works:

```sh
cd <ABSPATH> && nohup /usr/bin/wp eval 'do_action("updraft_backupnow_backup_all");' \
  --allow-root > log 2>&1 &
```

Background it. In the foreground the bridge returns **HTTP 524** (Cloudflare)
while the job keeps running — the request timing out does not mean it failed.
Watch `wp-content/updraft/log.<nonce>.txt` for "The backup succeeded".

Check retention first: it is 2 sets here, so a new backup **evicts the oldest**.

## Never trust a 503 from pepcore.com found during parallel automation

Running two Playwright scripts against pepcore at once reliably produces 503s on
subresources that are perfectly healthy. It has now caused a false finding three
separate times. Re-run the single page sequentially, with nothing else touching
the host, before reporting anything.

## `waitUntil: 'networkidle'` never settles on pepcore.com

Analytics/tracker connections stay open, so `page.goto(..., {waitUntil:
'networkidle'})` times out at 60s on a page that actually loads in ~5s. Use
`domcontentloaded` plus an explicit `waitForTimeout`.

## endroid/qr-code v5.1: ErrorCorrectionLevel is an enum, not classes

`\Endroid\QrCode\ErrorCorrectionLevel\ErrorCorrectionLevelQuartile` does **not**
exist in 5.1. It is `\Endroid\QrCode\ErrorCorrectionLevel::Quartile`, and the
constructor default is `::Low`.

A `class_exists()` guard around the old class name therefore skips silently and
you ship codes at ~7% damage tolerance believing they are at 25%. Nothing errors
and the images look fine. Verify by module count for the same data - Quartile is
denser than Low (33x33 vs 29x29 for a 31-char URL).

## WP Rocket delay_js: excluding a script without its dependencies is worse than not excluding it

Excluding `/plugins/affiliate-wp/` alone made its tracking script run before
`jquery.cookie` -> `$.cookie is not a function`. Adding the cookie libraries then
gave `AFFWP is not defined`, because the **inline** block defining `AFFWP` was
still delayed.

Exclusions match inline script CONTENT as well as `src`, so an inline definition
needs its own entry (here, the literal string `AFFWP`). Check the rendered DOM
for `type="text/rocketlazyloadscript"` on the pieces you thought you had
excluded, rather than guessing at the exclusion list.

## Hostinger's edge CDN caches HTML and ignores your cookies

Hostinger fronts these sites with its own CDN (`Server: hcdn`,
`x-hcdn-request-id`, `x-hcdn-cache-status`). It is a **second cache in front of
whatever you configure in WordPress**, and it keys on the URL, not on cookies.

On DualCore this produced a full age-gate bypass. LiteSpeed Cache was configured
correctly — `acg_verified` registered as a vary cookie, the rewrite rule
(`RewriteRule .? - [E="Cache-Vary:acg_verified"]`) present in `.htaccess` — and
LiteSpeed itself behaved perfectly. hcdn did not: it stored the verified 200 and
replayed it to cookieless requests.

It looks **intermittent**, which is the trap. Caching is per edge node, so the
same request alternates:

```
attempt 1  302  x-hcdn-cache-status: MISS   (mum-edge5)  <- correct
attempt 2  200  x-hcdn-cache-status: HIT  Age: 2  (mum-edge9)  <- BYPASS
attempt 3  302  x-hcdn-cache-status: MISS   (mum-edge7)  <- correct
```

Two or three curl requests can easily all land on passthrough nodes and look
clean. **Test any cookie-gated page at least a dozen times**, and read
`x-hcdn-cache-status` and `Age:`, not just the status code.

Fix: mark front-end HTML `Cache-Control: private, no-store, max-age=0`.
`private` is the operative token — it forbids a *shared* cache from storing the
response. LiteSpeed is unaffected because it decides from its own
`X-LiteSpeed-Cache-Control` header, so the page cache still works. See
`mu-plugins/dcp-cdn-guard.php`.

Confirmed working: `x-litespeed-cache: hit` and `x-hcdn-cache-status: MISS` on
the same response, 12/12 cookieless requests correctly gated.

The same CDN also serves `/robots.txt` ahead of WordPress — see SITE-NOTES.

## lib.mjs seeds the age-gate cookie, so you cannot test a gate with it

`launch()` in `lib/lib.mjs` deliberately injects `acg_verified=1` into **every**
new context so screenshots show the page instead of the interstitial. Any script
that tries to test the gate through it will report the gate is broken/bypassed
when it is fine.

Call `await ctx.clearCookies()` immediately after `newContext()` to test a gate.
For proving a cache does not leak past a gate, prefer plain `curl` — no seeding,
no profile, and you can see the CDN headers.

## `scripts/rfile.ps1 put` reports success without the bytes landing

Seen five times now. It prints `wrote <path> (N bytes)` and the file is simply
not there afterwards — sometimes it lands and then disappears a few seconds
later, after WordPress has already generated thumbnails from it.

Always read the size back **server-side** and retry in a loop:

```bash
for i in 1 2 3; do
  pwsh scripts/rfile.ps1 put "$local" "$remote"
  got=$(pwsh scripts/rwpphp.ps1 check-size.php | ...)
  [ "$got" = "$(stat -c%s "$local")" ] && break
done
```

## WordPress attachment lookup by slug will grab the wrong image

`get_posts(['name' => $slug])` matches *any* attachment with that slug. On
DualCore the age-gate vial cut-outs share names with the product photos, so
attaching `dcp-reta-3-30mg` picked up the 320x662 gate graphic instead of the
1200x1200 product shot — silently, and the product then had a tiny image.

Look up by `_wp_attached_file` against the real relative path instead, and give
different-purpose files different prefixes (`dcp-prod-` vs `dcp-`).

## Never embed file bytes as base64 inside a script sent through the bridge

`scripts/rwpphp.ps1` writes your script to a real PHP file on the server before
executing it. A script containing a large base64 literal plus `base64_decode()`
is the canonical webshell signature, and the host's malware scanner reacts to
it: **the files that script writes are deleted within seconds.**

This is genuinely confusing to diagnose, because the write itself succeeds —
`filesize()` inside the same request returns the correct byte count — and the
file is gone by the next request. It looks exactly like a flaky uploader.

Proof (same bytes, same `file_put_contents`, one request apart):

| written from | result |
|---|---|
| base64 literal inside the script | **deleted** |
| bytes read from a file already on the server | kept |
| `copy()` of a file already on the server | kept |
| `fwrite()` of bytes read from the server | kept |

It is not content-specific — a valid image, a truncated 2KB fragment and a
re-encoded PNG were all deleted when they arrived via a base64 literal, and the
*same* image survived when its bytes were read server-side.

**Use `scripts/rfile.ps1 put` for binaries.** It sends the bytes as JSON in the
request body, so nothing webshell-shaped is ever written to disk. Files
uploaded that way persist.

This also retracts the earlier note blaming `rfile.ps1 put` for silently losing
files: every confirmed loss this session traces to a base64-embedded script,
not to the uploader.

## Hostinger intercepts /favicon.ico and /robots.txt before WordPress

Both are answered by the hosting platform, not the site. `/favicon.ico` returns
Hostinger's own 404 page — identifiable by `platform: hostinger`, `panel:
hpanel` and a `last-modified` date long before the site existed — and no
WordPress hook can change it, at any priority. `parse_request`,
`muplugins_loaded` and `do_faviconico` were all tried.

It does not matter in practice: set the WordPress **site icon** and the
`<link rel="icon">` / `apple-touch-icon` tags are emitted correctly, browsers
use those, and they stop requesting `/favicon.ico` at all. The console 404
disappears.

Both are likely artifacts of the temporary `*.hostingersite.com` preview
domain. Re-check after the real domain is connected.

## A single uncached-gate slip poisons the page cache permanently

With a cookie-varied page cache in front of a server-side age gate, the vary
cookie only protects the *cache key*. If the gate fails to apply for even one
request — a mu-plugin caught mid-write, a filter misfiring — that one 200 is
stored under the "no cookie" key, and every later unverified visitor is served
it **without PHP running**. The gate stays bypassed until someone purges, and
nothing logs it.

This happened here while rewriting an mu-plugin: a check that had passed 12/12
minutes earlier came back 0/12.

Belt and braces, in `mu-plugins/dcp-cdn-guard.php`: if the request carries no
`acg_verified` cookie, mark the response uncacheable outright
(`DONOTCACHEPAGE`, `litespeed_control_set_nocache`,
`X-LiteSpeed-Cache-Control: no-cache`). An unverified 200 can then never enter
the cache in the first place. Verified visitors — everyone past the gate, so
effectively all real browsing — still get the full page cache.

Verify with `curl`, repeatedly, **after warming the cache**, not before.

## Never put a template file at the top level of mu-plugins — it takes the site down

WordPress `include_once`s **every `*.php` file at the top level of
`wp-content/mu-plugins`** during `wp-settings.php`, on every request. A page
template placed there runs immediately, before `$wp_query` exists:

```
mu-plugins/dcp-404-template.php(11): get_header()
wp-settings.php(508): include_once(...)
→ Uncaught Error: Call to a member function get_queried_object() on null
   in wp-includes/query.php:45
```

Every page 500s. **And so does the bridge**, because mu-plugins load before
regular plugins — so `scripts/rwpphp.ps1` and `scripts/rfile.ps1` both return HTTP 500
and there is no way back in without FTP, SSH or hPanel File Manager. On a site
reached only through the bridge, this is unrecoverable without the client.

It also looks partly fine at first: LiteSpeed keeps serving already-cached
pages without running PHP, so `/shop/` can return 200 while the homepage,
checkout and wp-admin are all 500. Do not read a 200 as "still up" — always
re-test with a cache-busting query string.

Two rules:

1. **Subdirectories of mu-plugins are NOT scanned.** Put the template in
   `mu-plugins/<name>/` and point `template_include` at it.
2. **Guard the template anyway**, so a future move cannot repeat this:

```php
/* in the loader */
if ( ! defined( 'DCP_404_OK' ) ) { define( 'DCP_404_OK', true ); }
return $own;

/* first lines of the template */
if ( ! defined( 'DCP_404_OK' ) || ! did_action( 'template_redirect' ) ) {
	return;
}
```

Recovery, if it happens: the client deletes or renames the one offending file
in hPanel → File Manager. Nothing else needs touching, provided the loader
checks `file_exists()` before using the template.

## WP Rocket serves a stale inline `<style>` after an mu-plugin edit

Editing a mu-plugin that prints CSS in `wp_head` and then screenshotting the
page will show you the **old** stylesheet. The PHP file on disk is new; the
cached HTML that embeds its output is not, and nothing about the page looks
stale — the heading and markup can be current while the `<style>` block is not.

This cost a wrong conclusion once: the fix was assumed not to match the DOM,
and the selectors were about to be rewritten, when the DOM was already correct
and only the CSS was old.

Assert on the stylesheet itself, not on the rendered result:

```js
const css = document.getElementById('pep-aff-css');
css.textContent.includes('.pep-aff-dash .affwp-notice')   // did my rule ship?
css.textContent.length                                     // 18772 = old, 23349 = new
```

Purge after every CSS-bearing mu-plugin write, and verify the purge ran:
`rocket_clean_domain()`, `rocket_clean_minify()`, `rocket_clean_files([urls])`,
`\LiteSpeed\Purge::purge_all()`, `wp_cache_flush()` — see `pc-purge.php`.

## Your own extraction script will lie to you about dashes

Known trap: the database stores em dashes (`E2 80 94`) where the copy reads as
a hyphen. The new part, and the expensive part:

**A PHP script that echoes the string prints the em dash as `-`.** Through the
terminal, `grep`, and the bridge, `Lot or batch number — must match your vial`
came back as `Lot or batch number - must match your vial`. A replacement map
built by copying that output matched **zero** occurrences, and the dry run still
looked healthy — it simply listed fewer posts, which is easy to read as "those
posts don't contain it."

Two posts and one whole product-page item would have been reported fixed and
silently skipped.

**The tell:** a dry run whose per-post totals do not equal the sum of the lines
it printed, or an expected post missing from the list entirely. Both appeared
here and both were real.

Never build a replacement map by retyping or copy-pasting script output. Either
byte-check first:

```php
$hex = '';
for ( $i = 0; $i < strlen( $snippet ); $i++ ) {
    $o = ord( $snippet[ $i ] );
    $hex .= ( $o >= 32 && $o < 127 ) ? $snippet[ $i ] : sprintf( '[%02X]', $o );
}
// Lot or batch number [E2][80][94] must match your vial
```

...or make every key dash-insensitive and stop thinking about it:

```php
function dcp_dash_rx( $needle ) {
    $q = preg_quote( $needle, '/' );
    $q = str_replace( '\-', '[-\x{2010}\x{2012}\x{2013}\x{2014}]', $q );
    return '/' . $q . '/u';
}
```

Use `preg_replace_callback` to substitute, so `$` and `\` in the replacement copy
are never read as backreferences.

Also print a **per-rule hit table** at the end of any bulk copy change, marking
rules with zero hits as `MISS`. A rule that matches nothing is the failure mode
that looks exactly like success.

## innerText hides collapsed accordion copy

A rendered-text audit built on `innerText` returns `""` for anything inside a
collapsed Elementor accordion. A banned sentence sitting in a FAQ answer
therefore reports **clean** while the client sees it after one click.

This produced a false "clean" on a phrase the client was looking straight at.

Use `textContent` when auditing for prohibited copy — anything a visitor can
reveal with one click is published:

```js
document.querySelectorAll('p, li, h1, h2, h3, h4, span, div, summary').forEach(e => {
  if (e.querySelector('p, li, h1, h2, h3, h4')) return;   // leaves only
  const t = (e.textContent || '').replace(/\s+/g, ' ').trim();
  // e.offsetParent === null  =>  currently collapsed, still published
});
```

## Never delete an edge optimiser's cache files by hand (Airlift / Hostinger)

Hostinger sites run **Airlift** (`airlift/airlift.php`). It rewrites every
stylesheet, script and font to a hashed file under
`wp-content/uploads/al_opt_content/{CSS,SCRIPT,FONT,IMAGE}/`, and it optimises
**at Hostinger's edge**, not in PHP.

Deleting those files to force a rebuild takes the whole site down. The cached
HTML keeps referencing the hashes, every asset 404s, and the browser reports:

```
Refused to apply style from '.../al_opt_content/CSS/<hash>.css'
because its MIME type ('text/html') is not a supported stylesheet MIME type
```

The site then renders unstyled with no JS — and Elementor Pro form widgets
(multi-step forms especially) silently stop working, because Pro's frontend
script never loads. Clearing `wp-content/cache` does **not** fix it; the edge
still serves the stale HTML.

**Purge through Airlift's own API instead:**

```php
$p = WP_PLUGIN_DIR . '/airlift';
require_once "$p/info.php"; require_once "$p/wp_api.php";
require_once "$p/admin/purge_cache_tools.php";
global $bvsettings;
$tools = new ALPurgeCacheTools( new ALInfo( $bvsettings ), new ALWPAPI( $bvsettings ), __FILE__, 65535 );
$tools->submitPurgeCache( array( 'purge_all' => true ) );   // "purged within a minute"
```

If it is already broken, the recovery that works is to clear the per-URL config
table (back it up first — it is regenerable):

```sql
DELETE FROM wp_bv_airlift_config;   -- prefixed, e.g. wpva_bv_airlift_config
DELETE FROM wp_bv_airlift_stats;
```

Then warm each page with a couple of requests. `apply_airlift_optimizations`
(option, `'true'`/`'false'`) is the kill switch if you need the site correct
immediately while you work out the rest.

## Airlift delays JS until the visitor interacts — Playwright sees a different page

With Airlift on, scripts load but do not execute until the first interaction.
Consequences for auditing:

- `waitUntil: 'networkidle'` never settles — it times out even though the page
  returns 200 in 2s. Use `'domcontentloaded'` plus an explicit wait.
- `window.elementorFrontend` is `undefined` and a multi-step form renders as one
  flat list of every field. **This is not a broken form.** Move the mouse,
  scroll, press Tab, then `waitForSelector('.e-form__indicators__indicator')`.

I reported a working step form as "never worked" on the strength of the first
measurement. Interact before concluding anything about Pro widgets.

## Elementor Pro form styling: label colour is per-widget, not per-page

Cloning a form widget clones its `__globals__`, including
`label_color`. A form copied out of a dark section onto a light one renders
**invisible labels** — present in the DOM with correct text, unreadable on
screen. Check `settings.__globals__.label_color` before blaming CSS.

Two forms on one page also collide on `custom_id`: every field emits
`id="form-field-<custom_id>"`, so a cloned form produces duplicate DOM ids and
every `<label for>` resolves to the *first* form's field. Prefix the clone's
`custom_id`s. Check `email_content` for `[field id="..."]` references first —
if any exist, renaming breaks the notification email.

## Airlift: submitPurgeCache() does NOT clear wp-content/cache

`ALPurgeCacheTools::submitPurgeCache(['purge_all' => true])` returns
"Cache will be purged within a minute" and clears the optimiser's asset layer,
but the **page cache under `wp-content/cache` keeps serving the old HTML** —
including the old inline `<style>`. A CSS change can therefore be live at origin
and invisible on the plain URL indefinitely.

Symptom: the same URL returns different HTML with and without a cache-buster.

```bash
curl -s "https://site/page/"            | grep -c 'my-new-rule'   # 0
curl -s "https://site/page/?cb=$RANDOM" | grep -c 'my-new-rule'   # 1
```

Purge **both**: call `submitPurgeCache()` *and* empty `wp-content/cache`.
Verify on the plain URL, never on a cache-busted one — a cache-busted check
proves the origin is right and tells you nothing about what visitors get.

Also: warming a URL immediately after purging can re-cache the stale build
before the purge lands. Purge, wait, then request.

## Never set Action Scheduler concurrent_batches to 1

Capping `action_scheduler_queue_runner_concurrent_batches` looks like the
obvious way to stop a site overloading itself with async jobs. **Do not set it
to 1.**

Action Scheduler counts *outstanding claims* against that limit, and a claim is
only released when its runner finishes cleanly. A runner killed mid-batch — by a
PHP timeout, a worker being reaped, a 503 — leaks its claim permanently. At a
limit of 1, one leaked claim blocks every future runner and the queue stops
forever.

Seen on pepcore 2026-09-06: **26 stale claims**, oldest from 09-04, and the
queue frozen at `pending=79 in-progress=24` with zero movement over two minutes.

Use **2** or more. Check for leaked claims before blaming the limit:

```sql
SELECT claim_id, date_created_gmt FROM wp_actionscheduler_claims
 WHERE date_created_gmt < DATE_SUB(UTC_TIMESTAMP(), INTERVAL 1 HOUR);
```

Release them through Action Scheduler's own cleaner, not hand-rolled SQL:

```php
$cleaner = new ActionScheduler_QueueCleaner( ActionScheduler::store() );
$cleaner->reset_timeouts();   // runner died -> back to pending
$cleaner->mark_failures();    // genuinely failed -> failed
```

A pile of stale claims is itself a symptom: runners are being killed, which
usually means the worker pool is exhausted.

## WP Rocket preload can 503 a shared-hosting site

Every cache purge — including **every content save** — queues one preload job
per URL. Each job makes an HTTP request back to the site to render a full
uncached page. With `DISABLE_WP_CRON` undefined those fire inside visitor
requests, and Action Scheduler's default 5 concurrent batches x 25 actions
multiplies them.

On pepcore this put **72 preload rows into flight in a single second**, failing
7 within 90s and killing other actions at the 300s mark, while real visitors got
intermittent **503 Service Unavailable**. The site was DDoSing itself with its
own cache warmer.

Diagnose:

```sql
SELECT modified, COUNT(*) c FROM wp_wpr_rocket_cache GROUP BY modified ORDER BY c DESC;
-- many rows sharing one timestamp = a burst
SELECT status, COUNT(*) FROM wp_wpr_rocket_cache GROUP BY status;
```

`action started via WP Cron` in the Action Scheduler logs confirms cron is
running in-request.

Mitigate: cap AS concurrency (2, never 1), turn off `preload_links` (hover
prefetch), and lengthen `purge_cron_interval`. The real fix is
`DISABLE_WP_CRON` **plus** a server cron — never the constant alone, or every
scheduled task including order email stops silently.

## Gemini: `thinkingConfig` is not universally accepted

Sending `generationConfig.thinkingConfig` to a **non**-thinking model is not
ignored — `gemini-3.5-flash-lite` answers HTTP 400 *"Request contains an invalid
argument"* and the call fails outright. Use an allowlist of models known to
support it, never a blanket filter.

Conversely, on a thinking model a small `maxOutputTokens` is consumed by
reasoning before any answer appears: the call returns **HTTP 200** with
`finishReason: MAX_TOKENS` and empty text. A success code with no output looks
like a parser bug and is not one. In a usage log the signature is `ok=0 http=200`.

## Gemini free-tier caps vary enormously between models

`gemini-3.8-flash` allows **20 requests per day** on the free tier; flash-lite
allows orders of magnitude more. Benchmarking latency alone will pick the fast
model that stops working by mid-morning. Read the 429 body — it names the exact
quota: `limit: 20, model: gemini-3.8-flash`.

## Hostinger sites are behind Cloudflare: bridge scripts die at ~100 s with a 524

A long `rwpphp.ps1` script (several API calls plus `sleep()`) returns
`ERROR: HTTP 524`. Split long verification runs into separate invocations rather
than batching them into one script.

## Don't benchmark an API you are also rate-limited on

Repeated probing tripped both Google's per-day quota and the plugin's own
10-messages-per-10-minutes limiter, which then looked like fresh failures of the
fix under test. Check the usage log's `http_status` before concluding anything:
a 429 is your own testing, not the site.

## Git Bash rewrites a bare `/` argument into `C:/Program Files/Git/`

This one produces a **convincing false finding**, so it is worth knowing before
it costs an hour.

```bash
node audit/shot.mjs / home 1440        # screenshots a 404, every time
```

MSYS path conversion turns the lone `/` into the Git installation directory, so
the tool politely requests

```
https://<site>/C:/Program%20Files/Git/
```

which is a real 404, served with the real header and nav — it looks exactly like
a broken homepage. `audit.mjs` disagrees (it reads its URLs from `config.json`,
never from `argv`) and hand-written scripts that hardcode `url('/')` disagree
too, which makes it read like an intermittent site fault rather than a quoting
bug.

Fix — prefix the command:

```bash
MSYS_NO_PATHCONV=1 node audit/shot.mjs / home 1440
```

Affects any argument that *looks* like an absolute POSIX path, so it hits
`shot.mjs`, `rband.mjs`, `hscroll.mjs` and `probe.mjs` equally. A path with a
second segment (`/shop/`) is usually left alone; the bare `/` is the dangerous
case. **The tell is the URL, not the picture** — when a screenshot surprises
you, print `location.href` before believing it.

## "Plugin not found": a Windows-made zip becomes ONE file with a backslash in its name

Symptom: the bridge is uploaded, `plugins.php` lists a row for it, activating
gives **"plugin not found"**, and `wp-json/wpsd/v1/*` 404s. The REST plugins
endpoint does not list it at all.

Cause: the zip was built on Windows with a tool that writes zip entries using
**backslash** separators (`Compress-Archive` in Windows PowerShell 5.1 does this,
as does some Explorer/third-party zipping). Linux has no special meaning for
`\`, so the archive extracts as a single file literally named

```
wp-site-doctor-bridge\wpsd-bridge.php
```

sitting inside `plugins/wp-site-doctor-bridge/`. It looks like a nested folder in
any listing and is not one. WordPress indexes the path, cannot load it, and its
own **Delete reports "The selected plugin has been deleted" while removing
nothing** — `dirname()` on that path does not resolve to a real directory.

`scripts/build-bridge.ps1` already avoids this (it writes entries through
`ZipArchive.CreateEntry` with explicit forward slashes) — so `remote/
wp-site-doctor-bridge.zip` is correct. The broken copy came from a zip made some
other way. **Check entry names before uploading a zip you did not build:**

```powershell
Add-Type -AssemblyName System.IO.Compression.FileSystem
([IO.Compression.ZipFile]::OpenRead($zip)).Entries | % { $_.FullName }
```

Any `\` in the output means it will not install on a Linux host.

**Where the broken zip actually came from (found 2026-09-13):** a hand-made
`Desktop\wp-site-doctor-bridge.zip` (v1.1.0, 2026-08-24, single entry
`wp-site-doctor-bridge\wpsd-bridge.php`) was the file being uploaded to client
sites - the project's `remote/wp-site-doctor-bridge.zip` was fine all along. It is
archived as `wp-site-build/backups/old-doctor-bridge/…-BROKEN-…-DO-NOT-USE.zip` and
the Desktop copy is now the output of `scripts/build-bridge.ps1`. Only ever upload a
zip that script produced.

**Recovery when the folder cannot be deleted:** install under a different folder
name. The bridge uses `plugin_basename( __FILE__ )` and namespaced REST routes,
so the directory name is irrelevant — build a zip containing
`wpsd-bridge/wpsd-bridge.php` and upload that. It sidesteps WordPress's
"Destination folder already exists" refusal entirely.

## Bridge /run: a script's variables share the bridge's own local scope

`wpsd_bridge_run()` `include`s the script inside the function, so a script's top-level
variables ARE the bridge's local variables. happyplumbing.net 2026-09-13: an upload script did
`$file = array(...)` for `wp_handle_sideload()`, overwrote the bridge's temp-file path, and the
bridge's own `@unlink( $file )` then fatalled - the caller got a 500 "critical error" although
the script's work had completed (the site itself was fine).

Names to avoid at a script's top level: `$file`, `$name`, `$start`, `$code`, `$b64`, `$args`,
`$dir`, `$parse`, `$fatal`, `$output`, `$ob_level` (`$argv` is provided on purpose). Prefix
script variables, or wrap the script body in a function. Bridge fix (unlink via the stored
`$GLOBALS['wpsd_bridge_running']['file']`, captured before the include) belongs in both the
Doctor and the Build bridge.

## WP Engine silently no-ops file deletes from PHP

On `/nas/content/live/<install>/`, with the file at 0664 and its directory 0775
and both owned by the PHP uid, all of these returned success and changed
nothing:

| attempt | reported | actual |
|---|---|---|
| `unlink()` | Permission denied | not removed |
| `WP_Filesystem->delete()` (method: direct) | ok | not removed |
| `rename()` out of the tree | ok | not removed |
| wp-admin Delete Plugins | "The selected plugin has been deleted." | not removed |

`is_writable()` returns true throughout. Plugin *installs* work fine, so this is
not a blanket read-only mount. Treat file deletion under `wp-content/plugins` on
WP Engine as unavailable from PHP and use SFTP or WP Engine support.

## Six plugins hijack plugins.php, breaking scripted deactivate/delete

On a plugin-heavy site (Elementor, Crocoblock, Converter for Media, Timeline
Widget, and others) each injects its own "Quick Feedback" deactivation modal and
its own `<form>` onto `plugins.php`. A scripted click on Delete, or on the bulk
Apply, is swallowed by whichever modal binds first. Two consequences:

- Target WordPress's own confirmation control **by value** —
  `input[value="Yes, delete these files"]` — never by form index. The real form
  was #2 of 7 on this site.
- `form.submit()` fails with *"f.submit is not a function"* because WordPress's
  form contains `input[name="submit"]`, which shadows the method. Use
  `HTMLFormElement.prototype.submit.call(f)`, or better, click the button.

---

## A script that reports "matches" has told you nothing

`dc-clientfix.php` printed how many times each search string *matched*, and I
read that as how many rows it *changed*. Its `_elementor_data` branch bailed on
a JSON-decode failure — printing a warning that `tail -20` scrolled off — while
the `post_content` branch wrote fine. The run looked completely clean and the
client found the text still on the page.

**Rule: a mutation script prints writes, never matches, and then reads the value
back.** The pattern that works:

```php
$n = 0;
foreach ( $posts as $p ) {
    $new = str_replace( $from, $to, $p->post_content );
    if ( $new === $p->post_content ) { continue; }
    $wpdb->update( $wpdb->posts, array( 'post_content' => $new ), array( 'ID' => $p->ID ) );
    $n++;
}
printf( "wrote %d\n", $n );
/* then, separately: */
printf( "remaining occurrences: %d\n", count_occurrences( $from ) );  // must be 0
```

The final "remaining: 0" line is the only part that constitutes verification.

## Search on the stem, not the phrase

Client-supplied wording is rarely the site's wording. `plain carton` missed
*plain outer carton*; `not a drug` missed *are not drugs* and *None of these
products is a drug*. Both produced confident "0 occurrences — already fixed"
reports on text that was plainly visible on the page.

Search the shortest distinctive stem (`plain`, `drug`, `unedited`) and read
every hit in context. Slower by a minute, and the only way the count means
anything.

## Any content-mutating query must exclude revisions

`dc-recon3.php` matched `post_content` site-wide and wrote to 853 stored
revisions before anyone noticed. Revisions are copies of every past version of
every post, so a bare `SELECT ... FROM wp_posts WHERE post_content LIKE` hits
them many times over. Always:

```sql
WHERE post_type NOT IN ('revision')  AND post_status != 'inherit'
```

Live content is unharmed by this, but the revision history stops matching what
was actually published — and it is not practically reversible.

## Proving a checkout on a live store

Placing a real test order fires the customer email, the admin email, and any
abandoned-cart capture. On a live client store that means a real inbox gets a
real order confirmation for an order that is about to be deleted.

Suppress mail for the duration, in an mu-plugin named so it loads last:

```php
/* zz-dcp-mail-off.php — TEMPORARY */
add_filter( 'woocommerce_mail_callback', function () { return function () { return true; }; }, 99 );
add_filter( 'pre_wp_mail', '__return_true', 99 );
```

Then afterwards, in one scripted pass: delete the order with
`$order->delete( true )` (hard delete — a trashed order still counts), remove
the mu-plugin, clear `ac_sent_history_lite`, and **prove mail works again** by
checking `$wp_filter['pre_wp_mail']` is back to 0 callbacks and sending a live
`wp_mail()` to the store's own address. Leaving that plugin behind silently
stops every order confirmation on a live store, and nothing on the site looks
wrong.

## A 401 tells you almost nothing about *why* auth failed

Diagnosing a dead bridge on FALIS, I compared three REST calls and drew a
confident, wrong conclusion:

| request | response |
|---|---|
| stored app password | `rest_not_logged_in` (401) |
| deliberately wrong password | `rest_not_logged_in` (401) |
| user that does not exist | `rest_not_logged_in` (401) |

The textbook reading is that identical errors mean WordPress never attempted the
authentication, i.e. the `Authorization` header is being stripped. I reported
that. It was false — `rdoctor.ps1` on the very same host reports
`Authorization header  True` and `app passwords  True`, and a **fresh app
password authenticated immediately**. The control test still returns
`rest_not_logged_in` for a junk password.

**On this stack a revoked or wrong application password yields
`rest_not_logged_in`, not `incorrect_password`.** So the three-way comparison
cannot distinguish a stripped header from a bad credential, and any conclusion
drawn from it is guesswork dressed up as evidence.

When an app password stops working, the order is: **ask for a fresh application
password first** (cheap, and it is the usual cause), and only investigate header
stripping if a known-good credential also fails. Do not theorise about the
transport from the shape of a 401.

## The bridge expiry stamp tells you when it was installed

`rdoctor.ps1` prints `expires <date>`, which is install time + 30 days. If that
date is 30 days from *today*, the plugin was installed or refreshed today —
regardless of what the site notes say. On FALIS the notes said "expires 5 Oct"
but the live bridge said 8 Oct, which was the proof that the client had just
reinstalled it, and confirmed the routes really had been absent when I probed
minutes earlier rather than me having mis-tested.

## Git Bash rewrites a leading-slash argument into a Windows path

`node script.mjs /consecration/ out.txt` through the **Bash** tool became:

```
https://host.comc/Program%20Files/Git/consecration/   -> ERR_NAME_NOT_RESOLVED
```

MSYS path conversion treats a leading `/` as a POSIX path and expands it to the
Git install root. It mangles any argument that looks like an absolute path — URL
paths, `tel:` values, `--opt=/foo`.

Run anything taking a URL-path argument through the **PowerShell** tool instead,
or prefix with `MSYS_NO_PATHCONV=1`. The failure is loud here, but a script that
merely *logs* the argument would record the mangled value silently.

## UpdraftPlus "unable to send to backend" is not a failed backup

Triggering a backup through the bridge returns:

```
ERROR: Response was not JSON. Body was: unable to send to backend
```

The job started anyway — UpdraftPlus hands off to a loopback request that
outlives the bridge's own response. Never re-run it on the strength of that
error; you would start a second concurrent backup. Verify instead:

```php
get_option('updraft_jobdata_<nonce>')['jobstatus']   // filescreating, ...
glob(WP_CONTENT_DIR.'/updraft/*.zip')                // archives landing
get_option('updraft_backup_history')                 // set, once complete
```

The nonce is in `updraft_jobdata_%` rows in `wp_options`. Same shape as any
long-running job behind the bridge: the response dying tells you nothing about
whether the work is running.

## Reading a page headless: `wake()` is not optional

A scraper that scrolled and waited reported a fully-built Elementor page as
truncated to a third of its length, with scrambled headings. Two causes, both
in Elementor rather than the page:

1. Entrance animations leave widgets at `visibility:hidden` (`elementor-invisible`)
   until they scroll into view. A filter that skips hidden elements — a
   reasonable thing to write — drops most of the page.
2. DOM order is not visual order. Containers are reordered with flex/CSS, so a
   section heading can sit *after* its cards in the markup and render before
   them.

Use `wake()` from `lib/lib.mjs`, and confirm any "content is missing" finding
against the served HTML (`curl -sL … | grep -c "phrase"`) before acting on it.
Deleting or rebuilding a section on the strength of a bad headless read is how
you destroy work that was already correct.

## Elementor ships Font Awesome 5 names; modern kits use Font Awesome 6

A kit whose icons are `fas fa-circle-check` renders **PHP warnings into the page
HTML**:

```
Warning: Undefined array key "circle-check" in .../font-icon-svg/font-awesome.php on line 45
Warning: Trying to access array offset on value of type null in ... on line 48
```

Elementor's inline-SVG data manager looks the icon up in
`assets/lib/font-awesome/json/{solid,regular,brands}.json`, and those files carry
**FA5** names. FA6 renamed a lot of icons (`check-circle` -> `circle-check`,
`user-md` -> `user-doctor`, `tachometer-alt` -> `gauge-high`). Any FA6-only name
misses, and with `display_errors` on — the LocalWP default — the warning text is
emitted *inside* `<span class="elementor-icon-list-icon">`.

The symptom looks nothing like an icon problem: those warnings contain the full
Windows path in `<b>` tags, so the page gains ~1900px of horizontal scroll and
the layout appears catastrophically broken. One kit did this on 6 of 9 pages.

Audit which names are actually missing rather than fixing them one at a time:

```python
solid = set(json.load(open('.../json/solid.json'))['icons'])
# every "value": "fas fa-x", "library": "fa-solid" in the kit, minus solid
```

Then rewrite the kit JSON before import (75 replacements across 9 files in that
case) and **verify each replacement exists in the map** — a wrong replacement
fails exactly the same way. `display_errors` being on is what makes this visible
rather than silent; do not "fix" it by hiding the warnings.

## Elementor's Site Logo widget needs an explicit dynamic binding

`theme-site-logo` exported from a kit often carries only `align` and `width`. Its
image comes from a dynamic tag whose `dynamic.default` is `site-logo`, but that
default only applies when the widget actually has a `__dynamic__` key. Without
one the Image base class falls through to
`elementor/assets/images/placeholder.png` — a grey box in the header, which
looks like a missing upload rather than a missing binding.

Setting `custom_logo` alone does **not** fix it. Add the binding, building the
tag text with Elementor's own helper rather than hand-writing the shortcode:

```php
$tag = \Elementor\Plugin::$instance->dynamic_tags->tag_data_to_tag_text( null, 'site-logo' );
$widget['settings']['__dynamic__'] = [ 'image' => $tag ];
```

For a logo on a dark footer, bind nothing — set `settings['image']` to a
reversed asset explicitly. It is a different image, not the same one elsewhere.

## Elementor Pro `save_conditions()` takes arrays, not condition strings

```php
$cm->save_conditions( $id, [ 'include/general' ] );
// Fatal: Cannot unset string offsets  (conditions-manager.php:304)
```

It does `unset( $condition['_id'] )` then `implode( '/', $condition )`, so each
condition must be an **array of segments**:

```php
$cm->save_conditions( $id, [ [ 'include', 'general' ] ] );          // include/general
$cm->save_conditions( $id, [ [ 'include', 'singular', 'post' ] ] ); // include/singular/post
```

Prefer it over writing `_elementor_conditions` by hand — it also calls
`$this->cache->regenerate()`, which rebuilds the
`elementor_pro_theme_builder_conditions` option the front end actually reads.

The fatal lands **after** the templates have been created, so the import is
half-applied: templates exist, conditions do not. Make the importer idempotent
(match on title + `_elementor_template_type`) so re-running finishes the job
instead of duplicating everything.

## A page set as `page_for_posts` returns 0 from `url_to_postid()`

Verifying a blog URL with `url_to_postid( home_url('/blog/') )` reports it does
not resolve, because WordPress treats the posts page as an archive rather than a
page. The URL is fine. Check posts-page and archive URLs over HTTP
(`curl -o /dev/null -w '%{http_code}'`), not with `url_to_postid`.

## The host scanner also eats PDFs — and it took the one with a stale revision

Same server-side scanner as the Cash App logo above, on pepcore this time.
Uploading seven Bioviridian COA PDFs to `uploads/2026/09/`: six survived,
**COA8796.pdf was deleted twice**, minutes after a write that had been verified
byte-for-byte with `md5_file()` against the local original.

What was actually different about it — checked, rather than guessed:

```
COA8790  PDF 1.6  xref 40  /JSx1, /OpenActionx1     survived
COA8792  PDF 1.3  xref 91  /OpenActionx3, /AAx1     survived
COA8794  PDF 1.6  xref 36  /JSx1, /OpenActionx1     survived
COA8796  PDF 1.3  xref 69  /JSx1, /OpenActionx2     DELETED
```

`/JS` is a red herring — it appears in three of them and is a coincidental byte
sequence **inside the compressed JPEG stream**, not a JavaScript action. Grep
for a PDF token and you will match image bytes; confirm with a parser
(`pymupdf`) before believing it.

The real difference: COA8796 carried an **incremental update** — two xref
tables and two `/OpenAction` catalogs, because it had been re-saved a day after
creation (`modDate` > `creationDate`). Rewriting it as a single revision with
`doc.save(out, garbage=4, clean=True)` produced a file that survives.

**This is close to the "do not obfuscate" line in the section above, so be
careful how you think about it.** Flattening a redundant document revision is
not the same as recompressing or renaming an asset to sneak it past a signature
— the page renders *pixel-identical* (verified: 0 of 2,103,750 pixels differ at
150dpi), the JPEG streams are untouched, and nothing about the file's identity
is disguised. But the distinction is yours to defend, so:

* Verify the render is unchanged before and after, and say so.
* Tell the client the file was flagged and re-saved, and have them ask the host
  *why* — a passing file is not a diagnosis.
* Re-check after several minutes. The earlier deletions both happened outside a
  10-second window, so an immediate check proves nothing (as with the logos).

## `rfile.ps1 put` on pepcore caps near 512KB — split, concatenate, verify md5

Confirmed again with 1.2MB PDFs: `HTTP 413 - Payload Too Large` on every one.
`post_max_size` is 32M, so this is the host/WAF in front of PHP, not PHP.

Working recipe: split locally at 400KB, `put` the parts into a temp dir under
uploads, concatenate server-side with `sort($parts, SORT_STRING)`, and gate the
write on `md5($buf) === <local md5>`. Matching byte counts do **not** prove
correct ordering; the md5 does. Re-read the written file with `md5_file()`
afterwards — that proves what landed, not what you meant to write.

`put` will not create the parent directory: `wp_mkdir_p()` it first.

## A quoted bash heredoc still lets `\` through — write PHP with the Write tool

Generating a PHP script with `cat > x.php <<'PHP'` and a `str_replace('\','/')`
in it produced `str_replace('\','/')` on disk. The `\'` then escaped the quote,
the string ran on, and the next `/*` twelve lines later opened a comment that
never closed:

```
Parse error: Unterminated comment starting line 10
```

The reported line is where the *comment* opened, not where the string broke —
so it points at innocent code. Suspect an unterminated string above it.

Note this is a **local** authoring bug, not the bridge: `/run` sends base64 and
`wpsd_bridge_lint()` is a real `token_get_all(TOKEN_PARSE)`. It was reporting
the file honestly. Confirm with `scripts/php.ps1 -l` locally before blaming
transport.

Use the Write tool for PHP files rather than a shell heredoc, and lint every one
before sending it.

## Squaring an SVG in place leaves the attachment metadata lying about it

On livefatima, seven icons had been re-wrapped onto a square canvas after upload
(the fix for Elementor drawing tall SVGs at half width). The *files* were
updated; `_wp_attachment_metadata` was not. So the database said

```
Group-556-1.svg   width 46.598  height 89.012      <- the ORIGINAL shape
```

while the file on disk was genuinely `89.012 x 89.012`.

WordPress prints that stored width as the `<img width="47">` attribute. With
`height:auto` and a square SVG the browser then draws a **47x47** icon. Every
icon got a different arbitrary size this way - 47/57/53/53/72/75/58px across one
row of cards - and no CSS rule anywhere explained it, because none was involved.

The tell: `probe.mjs` shows a concrete `width` in the computed styles but lists
**no matching rule that sets width**. That means the HTML attribute, not CSS.

Fix the metadata from the file's own `<svg width= height=>`:

```php
wp_update_attachment_metadata( $id, [ 'width' => $w, 'height' => $h, 'file' => $rel ] + $meta );
```

Then note that correct metadata still does not give you *uniform* icons - each
square canvas is a different pixel size - so a component that wants one optical
size still needs an explicit box.

## Hand-tuned spacing becomes the defect once you fix what it compensated for

Same page: the obligation cards carried `padding-top` of 35/40/50/55px. It looked
arbitrary, and it was - someone had nudged each card so the *old*, unequal icon
heights lined up. Normalising the icons to one size made that padding the thing
throwing the row out.

Before normalising sizes anywhere, check whether the surrounding container has
per-item spacing that exists to cancel the very inconsistency you are removing,
and clear both in the same pass. Measure the offset of the element **relative to
its own card**, not its viewport `y` - viewport coordinates fold in card
position and hide the real variance.

## An alignment assertion that flags responsive behaviour is a broken assertion

The first version of the livefatima checker required equal `cardTop` and
`headTop` across a row, and duly reported "4 ragged rows" after the layout was
correct: cards stack on mobile so their tops *must* differ, and under
`space-between` a four-line heading legitimately starts higher than a two-line
one. Only two things were actually invariant - one icon size, and one icon
offset within its card.

Assert the invariant, print the rest as informational. A check that cries wolf on
correct output gets ignored, or worse, gets "fixed" by damaging the page.

## "Make them all the same size" is often the wrong fix — check the design first

On livefatima's Become A Member cards, seven icons rendered at seven arbitrary
sizes. The obvious fix — one uniform box — was applied, looked tidy in isolation,
and was wrong. The client came back with "some icons look oddly sized".

The XD artboard draws each icon at its **own natural size**, spanning 52.79 to
89.43 units — a deliberate optical range, not an accident. Forcing them to one
box made the small ones (Confession) too big and the tall one too small relative
to each other.

Two different faults were tangled together, and only the first was real:

1. **Arbitrary** sizes from stale attachment metadata — a genuine bug, fix it.
2. **Unequal** sizes — the design's intent, preserve it.

Uniformity is a guess about intent. Before normalising anything visual, pull the
artboard geometry and check whether the variation is the design. The scene-graph
recipe above turns that from an argument into a measurement — group names in the
artboard matched the SVG filenames exactly, so the mapping was free.

When you do implement design ratios, express them as percentages of the largest
icon and pick the base from what fits the *site's* component (its card was
shorter than the design's), rather than copying absolute design pixels.

## Elementor's own rule beats the icon-list `text_indent` control

Setting `text_indent` on an icon-list widget can silently do nothing. Elementor
ships

```css
.elementor-widget .elementor-icon-list-icon + .elementor-icon-list-text{
  padding-inline-start: 5px;
}
```

which wins, so the control writes a value the page never uses. Set the gap in the
widget's own `custom_css` instead and it applies.

## Measure where the glyphs start, not where the span starts

Checking that same gap, the assertion kept reporting 16px against a 31px target
while the CSS was in fact applied. `getBoundingClientRect()` on
`.elementor-icon-list-text` returns the **border box**, whose left edge sits
before the element's own `padding-inline-start`. The text was exactly where it
should be; the check was reading the wrong edge.

Add the padding when what you care about is the visual start of the text:

```js
t.left + parseFloat(getComputedStyle(el).paddingInlineStart || 0)
```

Same class of error as the alignment checker above: a failing assertion is a
claim about your measurement as much as about the page. Confirm the discrepancy
against the computed style before changing anything.

## Inline SVGs sharing an id: every icon after the first is clipped to the FIRST one's clipPath

This is what was actually cutting off the livefatima homepage icons, and it
survived three rounds of "fixing the sizing" because every measurement I took
was of the **box**, not of the artwork inside it.

Illustrator/XD exports name their clip `id="clip-path"` in *every* file. Used as
`<img src>` that is harmless - each file is its own document. But an Elementor
**icon-list with SVG icons inlines them into the page**, so seven icons put seven
`id="clip-path"` into one DOM. `url(#clip-path)` resolves to the *first* match in
document order, so icons 2..n are all clipped by icon 1's rect:

```
0 viewBox=0 0 89.012 89.012  ownClip=46.598x89.012  resolvesToOwn=true
5 viewBox=0 0 74.977 74.977  ownClip=74.977x62.598  resolvesToOwn=FALSE  -> 46.598x89.012
```

Icon 5's artwork is 74.977 wide and got clipped at 46.598 - **38% of it cut
off**. The widest icons look most broken, which reads like a sizing problem and
sends you to the size controls.

**Detect it** (the check that would have caught it on day one - compare the
resolved clipPath against the element's own):

```js
const g = svg.querySelector('g[clip-path]');
const id = g.getAttribute('clip-path').match(/#([^)]+)/)[1];
document.getElementById(id) === svg.querySelector('clipPath')   // false = collision
g.getBBox()                     // artwork extent, vs the clip rect it should have
```

Also worth listing duplicated ids that are *actually referenced* by some
`url(#...)`, rather than every duplicate id on the page - most duplicates are
inert and only the referenced ones can break rendering.

**Fix** at the file, not with CSS: give each SVG a unique id
(`clip-g554-1`) and rewrite its own `url(#...)`. Then re-upload. `overflow` and
`clip-path` CSS cannot undo it, because the clip is applied inside the SVG's own
coordinate system.

Same trap will apply to any set of exported icons dropped into one page - the
site already carries six `SVGRepo_iconCarrier` duplicates from another icon set.

**The wider lesson:** "measure it, don't assume" only works if you measure the
thing the user is complaining about. Box dimensions were right in every check I
ran while the artwork inside was being sliced in half. When a report says
*cut off*, measure the **ink**, not the frame.

## Register an SVG attachment with real width/height at insert time

Following the stale-metadata bug above, when adding an SVG:

```php
$aid = wp_insert_attachment([...], $path, 0, true);
wp_update_attachment_metadata($aid, ['width'=>$w, 'height'=>$h, 'file'=>$rel]);
```

`wp_generate_attachment_metadata()` cannot size an SVG, so without this the
attachment has no dimensions and WordPress prints whatever it can infer, which is
how the arbitrary icon widths appeared in the first place. Take `$w`/`$h` from
the `<svg width= height=>` attributes.

## AIOSEO dynamicOptions do not persist from a script without `save(true)`

`aioseo()->dynamicOptions->searchAppearance->taxonomies->post_tag->advanced->robotsMeta->noindex = true`
reads back as set *in the same request* only sometimes, and never reaches the
database from a bridge/CLI script: AIOSEO defers the write. Holding a
sub-object in a variable and assigning to it is worse — nothing sticks at all.
Plain `aioseo()->options` (sitemap settings) did persist. Fix: assign through
the full chain, then `aioseo()->dynamicOptions->save(true)`, and verify with a
**raw `SELECT option_value`**, not the getter.

Also: AIOSEO 5.x per-post SEO lives in `{prefix}aioseo_posts` (`title`,
`robots_default`, `robots_noindex`). A post with `robots_noindex=1,
robots_default=0` drops out of the AIOSEO sitemap — the clean way to de-sitemap
a published page that a redirect has retired.

## HTML-escaped data inside `<script type="text/plain">` never decodes

Script elements are raw text: the parser does **not** decode entities inside them.
Stashing `esc(JSON.stringify(x))` in a `<script type="text/plain">` and reading it
back with `.textContent` hands `JSON.parse` a literal `[&quot;...` - it throws.
Wrapped in a bare `try{}catch(e){}` this showed as nothing at all: a blank label
canvas on the pepcore calculator, passing a test that only checked the canvas
*existed*. Keep client-rendered data in a JS object instead, never swallow errors
silently (`console.warn` at least), and assert on **ink** (count non-white pixels
via `getImageData`), not on the element.

Related: a canvas that draws a cross-origin image without CORS becomes tainted and
`toDataURL()`/`getImageData()` throw - a "Download" button silently dies. Set
`img.crossOrigin='anonymous'` before `src`; testing from `file://` exposes this.

## PowerShell 5 `Get-Content -Raw | -replace | Set-Content` corrupts UTF-8 files

Windows PowerShell 5.1 reads files with no BOM as ANSI (Windows-1252) and
`Set-Content -Encoding utf8` writes them back as UTF-8 **with a BOM**. So a quick
in-place `-replace` on a PHP file turns every non-ASCII character into mojibake
(`·` -> `Â·`, `—` -> `â€”`) and adds a BOM before `<?php` (which can cause
"headers already sent"). `php -l` passes and the upload's parse check passes -
the damage only shows as garbled text on the page. This shipped once to
pepcore's calculator (vial label text) before it was caught.

Edit files with the Edit tool. If a PowerShell rewrite is unavoidable, use
`[IO.File]::ReadAllText($f,[Text.Encoding]::UTF8)` and
`[IO.File]::WriteAllText($f,$t,(New-Object Text.UTF8Encoding $false))`.
To undo the damage: `UTF8.GetString(GetEncoding(1252).GetBytes($text))`, then
diff against the server's `.wpsd-*.bak` to make sure nothing else changed.

## Test orders and test coupons on a live store leak to third parties

Before creating any order or coupon on a live site, list `{prefix}wc_webhooks`.
Stores wired to an external checkout or shipping app (Tagada, Shippo, ShipStation)
receive every order.created/updated and often coupon.* event - a test coupon
becomes a real promo code in the external checkout, a test order a real shipment
to fulfil. In the test request: `add_filter('woocommerce_webhook_should_deliver',
'__return_false')` (checked BEFORE the async job is queued), `pre_wp_mail` false,
and strip Jetpack Sync / PixelYourSite / push-notification / analytics callbacks
from `$wp_filter`. Pre-set the order data store's stock_reduced / recorded_sales /
recorded_coupon_usage_counts so a real product is not decremented. Afterwards,
check `actionscheduler_actions` for `woocommerce_deliver_webhook_async` rows.
Reference implementation: pepcore `scratch/pc-coupon-test.php`.

## UpdraftPlus job can stall with its resume event gone (pepcore, GoDaddy/LiteSpeed)

Symptom: `jobstatus=filescreating`, log frozen seconds into "Beginning creation
of dump of plugins", and **no** `updraft_backup_resume` in the cron array even
though the log says "Scheduling a resumption (1) after 300 seconds". Seen once
when UpdraftPlus picked the `/usr/bin/zip` binary. Don't start a second backup.
Re-schedule the lost resumption with the job's own nonce and spawn cron:

```php
wp_schedule_single_event(time()+5, 'updraft_backup_resume', [ $resumption+1, $nonce ]);
spawn_cron();
```

It picked up and completed. Script: pepcore `scratch/pc-backup-reschedule.php`.
Poll with a stall detector (log mtime unchanged for 8 min) rather than a plain wait.

## Moving page Custom CSS into Elementor's per-element `selector` CSS

1. **Specificity goes up.** `selector` becomes `.elementor-<post> .elementor-element.elementor-element-<id>`
   (0,3,0). Declarations that were silently LOSING in the page CSS start winning.
   Snapshot computed styles of every element before/after and delete what flips -
   it was never rendering. Screenshots alone miss 3px changes.
2. **Nothing can sit between the page wrapper and `selector`.** `.some-ancestor selector x`
   expands to `.some-ancestor .elementor-<post> ...` and never matches. Use body classes only.
3. **Page-wide type rules** (`.elementor-<post> .elementor-widget-icon-list ...`) also hit
   content from embedded templates (`[elementor-template]` shortcode). Put them on the
   container that embeds the template, not only on the page's own widgets.
4. **Native first, but check the container type and breakpoints.** `flex_*` keys do nothing
   on a grid container (`grid_gaps`, `grid_align_items`). CSS forced with `!important` at
   every width must be set on every responsive variant the element has - including
   custom ones like `padding_laptop`. Boxed containers put vertical padding on `.e-con-inner`.
Reference: Greyson `scratch/gy-css-migrate.php`, `gy-snap.mjs`, `gy-snapdiff.mjs`.

## Building a plugin zip on Windows: Compress-Archive writes backslashes

PowerShell 5.1 `Compress-Archive` stores entries as `plugin\includes\file.php`. WordPress
on Linux unpacks those as files literally named with backslashes. Build zips with
`System.IO.Compression.ZipArchive` + `CreateEntryFromFile($zip, $path, $rel.Replace('\','/'))`
and check `FullName -match '\'` is 0 before uploading.

## WP Engine: bridge can write CSS/JS in plugins but not PHP

`scripts/rfile.ps1 put` to a `.php` file under `plugins/` on WP Engine fails with
"Write failed - check permissions"; a `.css` in the same plugin succeeds. Deploy PHP
changes by uploading the plugin zip in wp-admin (Plugins > Add New > Upload >
Replace current with uploaded) - `scratch/wp-plugin-upload.mjs` automates it.

## Page cache TTL vs nonces in cached forms

A full-page cache (LiteSpeed Cache default TTL 7 days) serves the same HTML - and the
same nonce - to every visitor. WordPress nonces are valid for 12-24 h. Any public form
that calls `wp_verify_nonce()` (custom booking forms, waitlists) silently starts
failing after a day. Before enabling a page cache, grep the site's plugins for
`wp_nonce_field` / `wp_create_nonce` on public templates and cap the public TTL below
12 h (Heritage: 8 h), or exclude those pages, or use ESI for the nonce.

## Finding unused media: database scan alone is not enough

Plugins store image IDs under their own keys in serialized arrays
(heritage-tours: `s:3:"img";i:1801;` in `_hdt_itin`). A scan that only knows
`_thumbnail_id`, gallery keys and Elementor's `"id":N` misses them and would delete
live images. Always pair the DB scan with a crawl of every public URL (desktop + phone,
computed backgrounds included), and quarantine files + manifest before deleting.

## UpdraftPlus: "running" jobs that never finish = WP-Cron is dead

UpdraftPlus does a big site in resumptions, each one a WP-Cron event. If cron is broken, every
"Backup Now" dies after its first chunk and leaves an `updraft_jobdata_*` row plus `.zip.tmp`
files - the UI keeps showing it as in progress. Check `_get_cron_array()` for events overdue by
hours or days before blaming UpdraftPlus (firparkds.ie: 47 hooks stuck for 15 days).

Separately, with `max_execution_time` 0, `request_backupnow()` called from the bridge runs the
job **inside that request**: the HTTP call comes back empty with exit 1, but the job keeps going
on the server. Poll the job log before assuming it failed, and never start a manual resumption
while the log is still advancing - two writers on one zip corrupt it.

## WP Rocket 3.20.x / 3.21.x + Elementor Pro = site-wide 500 on `init`

`inc/ThirdParty/Plugins/CDN/Cloudflare.php:562` (`declare(strict_types=1)`) runs `substr()` over the
keys of `$wp_filter['deleted_post']` inside `unregister_cloudflare_clean_on_post`, hooked on `init`.
Elementor Pro adds a callback whose key is an **integer**, so it throws a TypeError on every request.
Seen on happyplumbing (3.21.0.1) and firparkds (3.20.2 - the reason WP Rocket had been switched off).
The callback only unhooks the official Cloudflare plugin, so removing it is harmless: mu-plugin that
`remove_action`s it at `init` `PHP_INT_MIN` (`build/mu-plugins/*-rocket-cf-guard.php`). Deploy the
guard **before** activating WP Rocket or installing Elementor Pro, and check the guard reports
"removed ... at init priority 10" on the next request.

## Activating WP Rocket from a script can leave it caching nothing

`activate_plugin('wp-rocket/wp-rocket.php')` through the bridge on firparkds wrote `advanced-cache.php` but left
`define( 'WP_CACHE', false )` and never wrote `wp-content/wp-rocket-config/<host>.php`. Without that config file
advanced-cache.php declines every request: 0 cache files, while preload keeps rendering (and failing) every URL.
After a scripted activation check all three: WP_CACHE true, `wp-rocket-config/<host>.php` exists (call
`rocket_generate_config_file()`), and `cache/wp-rocket/<host>/` fills. Then look for the "This website is like a
Rocket" footer on a second logged-out load.

Then check delay_js did not hold the purchase path: on WooCommerce, exclude jQuery, `/woocommerce/assets/js/`,
their inline params (`wc_add_to_cart_params` ...), underscore/wp-util **and `/wp-includes/js/jquery/ui/`** (the
price-filter slider depends on it), plus any inline script of ours by id - WP Rocket ignores `data-no-optimize`.

## Image Optimization (Elementor's plugin) "optimize on upload" re-queues its own output forever

firparkds: 260 attachments queued 35,982 times in 24 h (up to 1,692x each, ~1,000 jobs/h), all
"complete" - so the queue looks healthy once cron runs. The upload hook fires whenever attachment
metadata is saved, including by the optimiser itself. Tell: `SELECT args, COUNT(*) FROM
wp_actionscheduler_actions WHERE hook='image-optimization/optimize/upload' GROUP BY args` - counts in the
hundreds per attachment. Fix: `image_optimizer_optimize_on_upload` = 0; bulk-optimise new images manually.

## Never back up wp-config.php inside public_html

`wp-config.php.bak` (or `.wpsd-*.bak`) in the web root is not executed as PHP - the server hands it
out as plain text, database password and salts included. Write the backup one level up (the account's
domain folder) with mode 0600. Same for `WP_DEBUG_LOG`: give it a path outside public_html rather than
the default `wp-content/debug.log`, which is publicly downloadable.

## A regex "skip the HTML tags" callback can silently delete every word it matches

Falis spelling sweep: `preg_replace_callback( '/(<[^>]*>)|\bcolour\b/', fn($m) => '' !== $m[1] ? $m[1] : 'color', $s )`.
When the WORD branch matches, group 1 did not participate, so `$m[1]` is **undefined** (PHP warning, value null),
`'' !== null` is true, and the callback returns null - the word is replaced with nothing. A dry run that only
counted matches looked perfect; only the flood of "Undefined array key 1" warnings gave it away.
Use `isset( $m[1] ) && '' !== $m[1]`, and make every text-mutation dry run print a before -> after snippet, not a
count (see also "A script that reports matches has told you nothing").

## Image Optimization single jobs: "in-progress for at least 1337 seconds" is a timeout, not a hang

pepcore, 2026-09-15, 32 images queued via `Single_Optimization::optimize_many()` (hook
`image-optimization/optimize/single`). Some jobs logged "was in-progress for at least 1337 seconds without completing
and has been marked as failed" **one minute after starting**, then "action complete", and a new job appeared for the
same attachment. The real cause is in the PHP log: `Single optimization error. Reason: cURL error 28: Operation timed
out after 50002 milliseconds` - the call to Elementor's optimisation service. The WebP was usually written anyway; the
plugin sets `retry_count` 1 and re-queues once. So: read the PHP log, not the AS log line; count jobs per
`args` - x2 is the built-in retry, climbing past that is a loop. Running single jobs created **0**
`optimize/upload` jobs even with optimize-on-upload on (contrast the firparkds loop above). Pace on shared hosting
under pep-load-guard: roughly 1-2 images a minute. Originals and every resized copy stay on disk next to the .webp,
so old URLs keep resolving; purge the page cache afterwards or cached HTML keeps serving the old PNG srcset.

## Moving page Custom CSS onto an element without changing the cascade: `:where(selector)`

Elementor replaces the literal word `selector` with `.elementor-<post> .elementor-element-<id>` - two classes of
specificity. A page rule like `.gr-guide-part h3` (0,1,1) moved to `selector.gr-guide-part h3` becomes (0,3,1) and
starts beating the widgets' own Custom CSS that used to win (Greyson #2929, 2026-09-15). Wrap the keyword instead:
`:where(selector).gr-guide-part h3` - `:where()` contributes zero, so the rule keeps exactly its old (0,1,1). Same
for IDs: `:where(selector)#gr-cred-option-1 ...`. Also: container mobile `width` does NOT inherit from desktop
(its placeholder is 100%), so a desktop-only native width change leaves phones at full width - set `width_mobile`.
And verify a page-CSS migration with a live match test first (`querySelectorAll` per rule): on a duplicated page most
old rules can match nothing at all.

## A Theme Builder template created by script is ignored until the conditions cache is rebuilt in a LATER request

Greyson 2026-09-15: inserted an `elementor_library` post (type single-page, `_elementor_conditions` set) and called
`ThemeBuilder\Module::instance()->get_conditions_manager()->get_cache()->regenerate()` in the same request. The
option `elementor_pro_theme_builder_conditions` came back WITHOUT the new template (the document was not yet
resolvable in that request), so `get_documents_for_location('single')` returned nothing and every page rendered
with the plain page layout - no error anywhere. Calling `regenerate()` again from a separate bridge request fixed it.
Always read the option back (`['single'][<id>]`) after creating a template by script. Also: pages must use the
**default** page template for a single-page Theme Builder template to render (`elementor_header_footer` bypasses the
`single` location).

## A very tall full-page screenshot on mobile emulation can show the page "twice"

Playwright `fullPage` on an iPhone-emulated context produced a 29,190px image of a 9,730px page that looked like the
header and hero repeated mid-way. The DOM had one header, one H1, one template instance. Before reporting duplicated
content from a screenshot, count the elements (`document.querySelectorAll('h1').length`, `scrollHeight`).

## Elementor chips are wrapped one level deep — deleting the chip leaves the divider behind

Wasatch, 2026-09-17. A label chip in an Elementor "what we do" grid is not one
container. The shape is:

```
wrapper container          <- carries the border-bottom (the divider rule)
  chip container
    icon container
      icon widget (arrow)
    heading widget (label)
```

Removing the chip container (the one holding the icon + heading) leaves the wrapper
with `kids=0`. It still has the divider styling, so the row renders with a stray
horizontal line and a gap where the chip was — and `curl | grep` for the label text
reports it gone, so the HTML check passes while the page is visibly wrong.

Delete the **wrapper**, and assert the sibling count afterwards rather than only
grepping for the removed string. Screenshot the region; the string check cannot see this.

## LiteSpeed serves a stale page to the browser after `litespeed_purge_all`

Same session. After writing `_elementor_data` and firing `do_action('litespeed_purge_all')`,
`curl` returned the new markup while Playwright kept rendering the old page —
`X-LiteSpeed-Cache: hit`. The purge does not reliably reach every cached variant.

Append a cache-buster when verifying visually:

```bash
node audit/rband.mjs "https://site/page/?cb=$(date +%s)" out 1440 900 6
```

Otherwise you will "verify" a fix against a screenshot of the version you just replaced,
twice, and start looking for a bug that is not there.

## An Elementor button with no link set renders `href="#"`; a link url of `" "` renders `href=""`

Wasatch, 2026-09-17. Two different causes for what a review will report as "dead links":

- `button` widget, no `link` key at all → Elementor outputs `href="#"`.
- `heading` widget with `settings.link.url = " "` (a single space) → truthy, so Elementor
  builds the anchor, then trims → `href=""`.

Probing for `"url":""` finds the second only if you also check for `" "`. To make a
heading plain text again, `unset( $el['settings']['link'] )` — emptying the url string
still leaves the anchor.

## Trustindex review carousels look "clipped" in a screenshot mid-autoplay

Same session. `rband.mjs` reported `.ti-review-item` boxes at x=1332→1941 on a 1440px
viewport and the screenshot showed a half-hidden review card. Both are normal: the slide
track holds the off-screen next slides and `.ti-reviews-container-wrapper` has
`overflow:hidden`. The capture had simply landed mid-transition.

Before reporting a carousel as broken, re-capture — and check whether the page-level
hscroll check is clean. If `audit.mjs` says clean at every breakpoint, the overflow is
inside a clipping wrapper and is not a defect.

## `json_decode`/`json_encode` round-trip on `_elementor_data` is safe, but do the string surgery server-side

Same session. Shipping `_elementor_data` to disk through a PowerShell redirect lost 2 bytes
on two pages (em-dash, encoding). Decode → edit → `json_encode` → `update_post_meta`
inside one remote script is byte-safe, and Elementor's storage convention matches plain
`json_encode` (slashes and unicode escaped). Back up into a second post meta key, not to a
local file, and assert `get_post_meta()` equals what you wrote.

## Hostinger: a full-size upload can vanish from uploads/ while its derivatives survive

Wasatch, 2026-09-17. Three images were written into `wp-content/uploads` by a
bridge script in one request, each followed by `wp_generate_attachment_metadata()`.
Two survived. The third had its **full-size original deleted within seconds**,
every time, while its `-1024x768`, `-768x576`, `-300x225` and `-150x150`
derivatives stayed and served 200 indefinitely.

Ruled out by testing, not assumption:

- **not the filename** — reproduced under two unrelated names
- **not the bytes** — reproduced with a canvas re-encode (EXIF/ICC stripped, every byte different)
- **not permissions** — mode 644, same uid/gid as the files that serve
- **not caching** — `wp_remote_get()` from the server itself also returned 404, and `file_exists()` said the file was gone
- **not systematic** — two sibling images uploaded in the same request are untouched

The symptom in `audit.mjs` is `BROKEN IMG` plus a 404 JS error, because WordPress
still emits the missing full-size URL in `src` **and** in `srcset`. Pointing the
widget at a derivative is not enough on its own — `srcset` still references the
dead original.

The fix that holds: make a surviving derivative the attachment's canonical file.

```php
update_attached_file( $id, $dir . 'name-1024x768.jpg' );
wp_update_attachment_metadata( $id, [
    'file' => '2026/09/name-1024x768.jpg', 'width' => 1024, 'height' => 768,
    'sizes' => $only_sizes_that_exist_and_are_smaller,
] );
```

WordPress then never emits a URL for the missing file. Verify with a loopback
`wp_remote_get()` inside the same script, not just `file_exists()` — the file can
be present at the end of the request and gone a few seconds later.

**Always re-run `audit/audit.mjs` after uploading images to this host.** A tile
that looks right in a screenshot can still be serving a 404 for its full-size
source, because the browser silently falls back down the `srcset`.

## Instagram/Facebook without a login: what is actually reachable

Same session, sourcing client photos with their written permission.

- A public IG **profile grid** renders ~12 tiles before the login wall stops
  infinite scroll, regardless of how many posts the account has (44 here, 608 on
  another). Grid thumbnails cap at **640px**.
- Individual **post pages do open** logged out and serve up to **1440px** — so
  harvest from the post page, not the grid.
- `meta[property="og:description"]` on a post page carries the **full caption**,
  which is usually the only source of real project location/scope. Without it
  you would be inventing caption text.
- DOM order of a gallery/grid is **not stable between loads**. Read the image
  filename and its caption in the *same* page session or the pairing is wrong.
- Facebook pages resolve (`/share/<id>/` 400s to curl but redirects fine in a
  real browser to `/people/<name>/<id>/`) yet serve only ~6 distinct images at
  **590x443** — too small to use.
- Watch for third-party watermarks: one harvested photo carried `©2024 PCMLS`
  (Park City MLS), i.e. a realtor's listing photo, not the client's own work.

Use `lib.mjs`'s `launch()`/`wake()` — `wake()` replays real input events, which
is what releases JS held back by an optimiser.

## AffiliateWP block forms break if you edit the page content directly
AffiliateWP stores a checksum of every registration/login block form in post meta
`affwp_submission_forms_hashes`, written on `save_post`. Change the form's blocks with `$wpdb` (or anything
that skips `save_post`) and every submission fails with "Something went wrong when submitting this form,
please contact an administrator." After any direct edit, call
`affiliate_wp()->editor->save_submission_form_hashes( $post_id )`.

## Hostinger: Monarx is probably what deletes "our" files
Hostinger sites run `/var/lib/monarx-agent/share/monarx-protect/` (visible as a template_redirect callback). That
malware agent is the likely reason PHP files written by scripts (mu-plugins, re-uploaded originals) vanish on these
hosts. Put code in Code Snippets (DB) instead. Note one mu-plugin (`wu-301-redirects.php`, plain code) did survive.

## Cloudflare managed challenge: a blocked page scan looks like a clean page scan
On zerenclinics.com the bot challenge answers non-browser clients with an interactive HTML page.
A Playwright scan then finds **zero sections** and records **zero findings** - indistinguishable
from a healthy page unless you check. A 191-page sweep came back "all clean" while 11 of every 12
pages were never actually loaded; the giveaway was a defect I had already seen by eye going missing.
Rules: a scanner must record "not measured" separately from "no findings", and a sweep must report
how many pages it actually measured. Headless never passes; a headed browser passes its FIRST page
only, so scan with one fresh browser per page (`scratch/zc-gaps2.mjs`).
For the bridge, `curl.exe` passes where PowerShell's Invoke-WebRequest does not: set
`"useCurl": true` in the config's remote block, and retry challenged calls a few times.

## Polylang: url_to_postid() picks the wrong language when slugs match
`/botox/` (Spanish) and `/en/botox/` both returned the English post id, so a batch edit skipped two
Spanish pages and applied twice to their English twins. Resolve URLs by matching `get_permalink()`
exactly when a site is multilingual.

## WP Rocket's LCP beacon silently refuses most viewport sizes
The beacon that fills `wp_wpr_above_the_fold` (which drives LCP preloading and the
above-the-fold lazy-load exclusions) bails before doing anything unless the window fits
`width_threshold` x `height_threshold` from `rocket_beacon_data` — 1600x700 on Greyson.
Read `_isValidPreconditions` in `wp-rocket/assets/js/wpr-beacon.min.js`:

```
i = !is_mobile && (screenW < width_threshold || screenH < height_threshold)
```

So **desktop must be at least 1600x700 and mobile at most 1600x700**. A 1440x900 window is
rejected, a 390x900 phone window is rejected on height. The only symptom is
`beacon-completed="true"` with no network call and no new row — it looks like it worked.
It also bails if the page has been scrolled, and `is_mobile` comes from the **user agent**,
not the viewport, so a mobile row needs a phone UA as well as a short window.
Working runner: `scratch/gy-beacon.mjs`.

## On WP Engine, WP Rocket's page cache is off — and that hides its own beacon
`WP_ROCKET_CACHE_PATH` held 1 file and `cache/critical-css` was empty while the site still
reported `X-Cache: HIT` — that HIT is **WP Engine's** cache, not Rocket's. Consequences:

- Purging with `rocket_clean_domain()` alone changes nothing a visitor sees. You must also
  call `WpeCommon::purge_varnish_cache()` and `purge_memcached()`. `scratch/gy-purge.php`
  does all layers.
- The beacon script is injected at page-generation time, so while WP Engine serves a cached
  copy generated earlier, the beacon is simply absent from the HTML. I concluded "no beacon"
  twice before realising I was reading a stale page.

## WP Rocket keeps image URLs in tables a media rename never touches
Renaming media and search-replacing `postmeta` + `options` is not enough. WP Rocket also
stores absolute URLs in its own tables:

- `wp_wpr_above_the_fold` — the LCP record. Left stale after a PNG→WebP conversion it
  preloads the **old** `.png` at `fetchpriority=high` while the page loads the new `.webp`,
  so the visitor downloads both copies of the hero. All 47 rows were stale here.
- `wp_wpr_preconnect_external_domains` — emits a `dns-prefetch` per recorded domain. It still
  held 15 rows for `spcdn.shortpixel.ai` months after ShortPixel was uninstalled, so every
  page paid for a DNS lookup to a host it never contacts.

Empty both after any media rename and re-run the beacon. Same trap in a different disguise:
a *removed* optimisation plugin can keep costing bandwidth through another plugin's cache.

## Repoint renamed media by filename, not by URL
`_elementor_data` is JSON, so URLs are stored escaped as `https:\/\/example.com\/...`. A
full-URL search-replace misses every one of them. Replacing the bare basename
(`hero.png` -> `hero.webp`) matches escaped and unescaped forms alike, and the extension
anchors it so `hero.png` cannot match `hero-1.png`. Convert every registered size and the
`original_image` in one go, or `srcset` ends up mixing formats.

## Converting a whole media library in one bridge request times out at the gateway
61 attachments with all their sizes = ~400 Imagick conversions, then a
`LIKE '%filename%'` scan of `postmeta` **per file**. WP Engine answered HTTP 502 partway
through, leaving files and attachment records converted but references not yet repointed —
a half-applied change on a live site (see `docs/REMOTE.md`).
Two lessons: split conversion from repointing into separate scripts, and never loop a
`LIKE` scan per filename — fetch candidate rows once and apply all replacements in PHP with
`strtr()`. That took the repoint stage from a timeout to 2 seconds.

## WP Rocket: setting `async_css` in the options row does nothing on its own
The subscriber that generates critical CSS is registered in **admin** context and fires on
the plugin's own save action. Writing `wp_rocket_settings['async_css'] = 1` directly leaves
`cache/critical-css` empty, and async CSS without critical CSS is inert — the stylesheets
stay render-blocking. Nothing warns you. Log in and save the WP Rocket settings screen
(`scratch/gy-rocket-save.mjs`); generation then runs in the background and takes a few
minutes to appear.

Also note the CSS delivery controls on 3.23 render as **hidden inputs** paired with a visual
toggle, so reading `.checked` on `#async_css` always returns false and tells you nothing.

## Never string-replace inside PHP-serialized data — it silently destroys it
I renamed media to `.webp` and repointed references with `strtr()` across whole `postmeta`
and `options` values. That is safe for `_elementor_data`, which is JSON. It is **destructive**
for anything PHP-serialized, because every string is stored as `s:LEN:"..."`: turning
`hero.png` into `hero.webp` adds a byte while `LEN` still claims the old count, so
`unserialize()` rejects the entire value.

What that cost on classiccomfortair.com, from six corrupted rows:

- `_elementor_page_settings` on the **Elementor kit** stopped unserializing. Elementor found
  no global colour palette and fell back to its factory defaults — `#6EC1E4`, `#7A7A7A`,
  `#61CE70`, Roboto. **1219 global-colour bindings across the site** resolved to nothing, so
  white headings rendered `#333` grey and typography sizes changed. The client saw it before
  I did.
- `wpseo_titles` (all Yoast title/meta templates), `_wp_attachment_metadata`,
  `_wp_attachment_backup_sizes`, `elementor_remote_info_library`.

**The symptom does not look like data corruption.** Nothing errors, nothing 404s, no PHP
notice. `get_post_meta()` just returns a raw string instead of an array and every consumer
quietly uses its default. I spent a while chasing CSS merging and cache layers first.

Rules:
1. Replace only in columns you know are JSON or plain text. For serialized data, unserialize,
   walk the structure, replace, re-serialize — or use `maybe_unserialize()` round-tripping.
   WP-CLI's `search-replace` does this correctly; a raw SQL or `strtr()` replace does not.
2. After **any** bulk replace, check for damage:
   `SELECT ... WHERE meta_value LIKE 'a:%'` and assert `@unserialize()` succeeds on each.
3. Keep the reversal map **off the site**. Mine was written to `wp-content/wpsd-backups/` and
   was gone by the time I needed it — a cache-cleanup cron almost certainly removed it. Write
   backups locally, or somewhere no cleanup job walks.

Repair, when the backup is missing: the corruption is deterministic, so the length prefixes
can be recomputed. `scratch/cc-fix-serialized.php` walks each value, finds where the `";`
terminator actually sits for every `s:LEN:"`, rewrites the prefix, and refuses to write back
unless the result unserializes cleanly. It fixed all six rows with no data loss.

## Elementor: a broken kit degrades silently to factory colours
`elementor_active_kit` points at a kit post whose `_elementor_page_settings` holds
`system_colors` / `custom_colors`. Widgets bind to entries by id
(`__globals__: {"title_color":"globals/colors?id=fff0001"}`), and that binding **overrides**
the literal colour stored next to it in the same settings array. If the palette cannot be
read, Elementor emits **no colour rule at all** for that widget and the element inherits the
body colour.

So a healthy-looking `title_color: #FFFFFF` in the saved data means nothing on its own —
check that the id in `__globals__` exists in the kit. Two quick tells that a kit is not
resolving: the generated `post-<kit>.css` is tiny (1.4KB here) and contains Elementor's stock
`--e-global-color-primary:#6EC1E4`, and Roboto starts loading on a site that does not use it.

## Don't regex phone numbers out of `_elementor_data`

Elementor stores every CSS value in the same JSON blob as the content, so a phone-number
pattern happily matches `0652173913031` (a z-index/opacity string) and `0 0 32 32` (a box
shadow). On Firpark the top three "phone numbers" by frequency were all CSS. Read the
rendered page and take `a[href^="tel:"]` / `a[href^="mailto:"]` instead — that is also what
the customer actually sees, which is the thing you care about.

## `add_query_arg()` url-encodes its own values

So `add_query_arg(['e' => rawurlencode($email)], $url)` double-encodes: the `@` becomes `%2540`
and the resulting link 404s. Pass raw values. Caught on Firpark's unsubscribe links by
rendering the email templates locally before deploying — which is the general lesson: a
template renderer that stubs WP and `require`s the real plugin file lets you read the actual
output with no site access and no risk, and it catches token bugs that are invisible in prose.

## A plugin's tables existing proves nothing about whether its module is on

WooLentor creates `wp_woolentor_abandoned_cart` and friends at activation, whether or not the
abandoned-cart module was ever configured. On Firpark the tables were there, the stock email
templates were there, and the module had never run: 0 carts, 0 sends, and its settings option
did not exist at all. Check the settings option and the row counts, not `SHOW TABLES`.

## An archive can return 200, error-free, and still be hiding 90% of the catalogue

On Firpark every product-category archive passed a normal sweep — HTTP 200, no console errors,
no horizontal scroll — while showing **6 products out of 86**. Nothing in a status/error/scroll
audit can see this. If a page lists things, assert the **count** against the database, not just
that the page loaded.

Two faults stacked, and they are worth recognising separately:

- The Unlimited Elements product grid carries `products_maxitems` (default 6) and **does not
  honour `paged`** — `/page/2/` re-renders page 1 with the same items.
- WooCommerce's main query paginates at `woocommerce_catalog_rows x woocommerce_catalog_columns`
  (7 x 3 = 21 there). A widget that paginates at a *different* number draws page links that
  WordPress then **404s**, because the main query believes there are fewer pages.

So a widget-rendered archive can show pagination that is simultaneously wrong and unreachable.
Check `page/2/` actually returns 200 *and* contains different products.

## `!important` does not beat specificity

`!important` only breaks ties **between important declarations**. Specificity still decides
which important declaration wins. On Classic Comfort, `.elementor-widget .icon::before{...
!important}` is (0,2,0) and beat `.icon-mail:before{... !important}` at (0,1,0). Repeating the
class to reach (0,3,0) is what won. Measure with `audit/probe.mjs` rather than adding more
`!important`.

## A broken Elementor kit degrades silently to factory colours

If the active kit's `_elementor_page_settings` will not unserialize, Elementor does not error —
global colour bindings just fall back to the stock palette. On Classic Comfort that was 1,219
bindings, and it presented to the client as "white text is appearing in grey". Nothing in the
log. If site-wide colours change for no reason, unserialize the kit meta first.

## Deleting a term or page does not update the menus that point at it

Deleting Firpark's "All" product category left the main nav "Shop" item pointing at
`/product-category/all/`, which then 404'd — the site's primary navigation link, broken, for
days. WordPress cleans up menu items for deleted *posts* in some cases; it does not rescue a
**custom-link** menu item, which is just a stored URL string.

After deleting any term, page or product, walk every `nav_menu_item`: resolve
`_menu_item_url` for custom links, and `_menu_item_object` + `_menu_item_object_id` for the
rest. `scratch/fp-fix-nav-shop.php` has a loop that does it.

Related: **a URL sweep cannot catch this.** Sweeps request `/shop/` directly and pass, while
the header link beside it 404s. At least once per site, click the navigation.

## `wc_get_page_id('shop')` can be -1 while /shop/ works perfectly

WooCommerce registers the product post type with `has_archive => 'shop'`, so the catalogue
resolves whether or not a shop page is configured. If `woocommerce_shop_page_id` is empty,
`wc_get_page_permalink('shop')` falls back to **the site home page** — so every "Return to
shop" button, and breadcrumbs, quietly point at the homepage instead of the catalogue.

Check the option, not the URL. Fixing it is safe only if the target page is genuinely empty;
if it has content, setting it as the shop page hides that content behind the product loop.

## Searching `post_content` misses most of the text on an Elementor site

Firpark's dispatch and returns wording is in Elementor data and in a line injected by an
mu-plugin. A `post_content LIKE` search found none of it, and I wrongly reported that the site
publishes no dispatch timeframe. Search `postmeta` (`_elementor_data`) and the mu-plugins too —
or just render the page and read it, which is the only method that sees everything.

Corollary: check cart and checkout wording with **something in the basket**. An empty cart page
shows nothing but "Return to Shop", so an empty-cart check reports every cart feature missing.

## "Defer JS" and "Optimize CSS delivery" can wreck a score, not improve it

Lighthouse flagged render-blocking JS and CSS on Firpark, and WP Rocket's `defer_all_js` and
`async_css` were both off — the textbook fix. Turning them on **halved the score**:

| | before | after | reverted |
|---|---|---|---|
| desktop | 98 | **63** | 100 |
| mobile | 93 | **68** | 92 |
| desktop TBT | 0 ms | **1,150 ms** | 0 ms |
| mobile TBT | 50 ms | **4,660 ms** | 60 ms |
| desktop CLS | 0 | **0.121** | 0 |

Deferring every script on a jQuery-dependent Elementor/WooCommerce stack moves all of that
execution into one burst after parse, and Total Blocking Time is a heavier scoring weight than
render-blocking. Async CSS then added layout shift on top.

Two lessons. **A render-blocking warning is not automatically worth fixing** — check what the
fix does to TBT and CLS before keeping it. And **snapshot the whole settings array before
touching it**, so revert is one command (`scratch/fp-rocket-toggle.php revert apply`).

Related trap: WP Rocket's settings *page* showed "Optimize CSS delivery" unticked while the
database had `async_css = 1`, because the UI gates it behind a master toggle. Pressing Save on
that page can therefore silently write your change back to 0. Verify the option after any
admin save, not just after your own write.

## Critical CSS generation: the cron does work, it is just slow

`async_css` is inert until WP Rocket has critical CSS — it will not load stylesheets
asynchronously without it, which is a safety feature, not a bug. On Firpark the directory held
only an empty 2025 placeholder. Firing `rocket_critical_css_generation_cron` via `do_action`
produced nothing for several minutes and looked like it had failed; it had not — 5 files
(343 KB: front_page, page, product, product_cat, woolentor-template) appeared about 3 minutes
later. Wait and re-check before concluding the trigger did not work.

## On a low-traffic site, WP Rocket preload barely runs

Preload is driven by WP-Cron, and WP-Cron only fires when somebody visits. Firpark sat at
281 pending / 20 cached after a purge, and a cold page costs **~1.8 s median, 7 s worst, and
10.9 s for the very first request** against ~180 ms warm. That gap is large enough to swing a
PageSpeed score by tens of points depending purely on whether the test lands on a cached page.

So: **after any cache purge on a low-traffic site, warm the cache yourself** rather than
waiting for preload. `scratch/fp-warm.mjs` reads the sitemap and requests every URL (291 on
Firpark). A real server cron calling `wp-cron.php` would fix this properly.

## `position:sticky` dies silently under an ancestor with `overflow` set

Sticky needs every ancestor between it and the scroll container to have `overflow: visible`. If
one has `auto`, `hidden`, `scroll` or `clip`, that ancestor *becomes* the scroll container and
the element simply never sticks — no error, no warning, the CSS computes exactly as written.
On Firpark's checkout `position: sticky` and `top: 24px` both computed correctly with 1,315px of
room, and it still did nothing.

Diagnose by walking the parent chain and printing `overflowX`/`overflowY` rather than re-reading
your own CSS. And think before overriding the offender: on a site kept at zero horizontal scroll,
that `overflow-x:hidden` is usually load-bearing.

## Elementor stretches columns to equal height, which shows as an empty bordered box

A row's columns match the tallest one. If the short column has a background or border, it renders
as a tall empty panel beside the long column's content — which reads to a client as "a large
blank area" or "the page looks unfinished". Fix with `align-items:flex-start` on the
`.elementor-container` **and** `align-self:flex-start` on the column; the row rule alone is not
always enough.

Also worth checking: Elementor's `elementor-col-66` / `elementor-col-33` class names do not
guarantee those widths. On Firpark's checkout they rendered roughly 50/50, which is why the
payment form looked cramped. Measure the boxes; do not trust the class name.

## Elementor Pro

### Never `delete_option('elementor_pro_theme_builder_conditions')`

Elementor Pro caches the location -> template map in that option. Deleting it
does **not** trigger a rebuild — it just empties the map, so `get_by_location()`
finds nothing and **every Elementor header and footer on the site disappears**,
falling back to the theme's own. The front end keeps returning 200, so nothing
looks broken until you load a page and find Hello Elementor's bare header.

Cost on livefatima: the new page looked like the CSS had failed, when in fact
no Elementor header existed at all on any page of the site.

Regenerate instead of clearing:

```php
\ElementorPro\Modules\ThemeBuilder\Module::instance()
    ->get_conditions_manager()->get_cache()->regenerate();
```

`Conditions_Cache` also exposes `clear()` — that is the one that causes this.
Use `regenerate()` after any programmatic change to `_elementor_conditions`.

### A copied template must get fresh element ids

Elementor keys its generated CSS on the element id (`.elementor-element-<id>`).
Duplicate a header or footer template by copying its `_elementor_data` verbatim
and both templates emit rules for the *same* selectors; whichever stylesheet
loads last wins, and the copy renders with the original's styling no matter what
you change. Symptom: the new template measures within a few px of the old one
and every edit appears to do nothing.

Rewrite every `id` in the copied tree before saving.

### `boxed_width`, not `width`, sets a boxed container's max width

Container controls:

| content_width | the control that applies |
|---|---|
| `boxed` | **`boxed_width`** |
| `full`  | `width` |

`width` on a boxed container is silently ignored and the container falls back to
the kit's Content Width. Symptom on livefatima: sections built at 1360 rendered
at 1240, so a row of 300px cards wrapped 3+3+1 instead of the intended 4+3.

### The tablet breakpoint is not always 1024

With the extra breakpoints switched on (Greyson: mobile 767, tablet **768**,
tablet_extra **1024**, laptop **1440**), `*_tablet` covers **768 only**.
769-1024 is `*_tablet_extra`, and a control with no value there falls through to
the **desktop** value. A fixed image height set for desktop + tablet + mobile
therefore looked right at 1440, 768 and 390 and was wildly too tall at 1024.

Always read the live list first — do not assume:

```php
foreach (\Elementor\Plugin::$instance->breakpoints->get_breakpoints() as $k=>$b)
    printf("%-14s active=%-3s value=%s\n", $k, $b->is_enabled()?'yes':'no', $b->get_value());
```

### JetEngine listing grids: where the card actually lives

A `jet-listing-grid` widget holds only the query and the column count. The card
markup is a separate JetEngine listing (`jet-engine` CPT) named by the widget's
**`lisitng_id`** setting — note the typo, it is `lisitng_id` in the stored JSON,
not `listing_id`. Grep for the wrong spelling and you will conclude nothing
references the listing.

`jet-listing-dynamic-image` has native `image_width`, `image_height` and
`image_object_fit` controls, which is all you need to force a uniform card image
without writing CSS. There is no object-position control.

### WP Rocket "Delay JavaScript Execution" silently kills DOM-measuring sections

Symptom, and it is a distinctive one: **a section is deformed for visitors but
correct right after the cache is cleared**, and correct for you because you have
been testing with `?nowprocket=1`.

`delay_js = 1` rewrites every `<script>` — including inline ones — to
`type="text/rocketlazyloadscript"` and does not run them until the visitor
interacts. Any section whose layout is *drawn* by JS (measures the DOM, builds
an SVG, positions connectors) therefore renders in its raw, undrawn state on
first paint.

It does not self-heal either, even for scripts that are written defensively.
A script that redraws on `window.load` and `document.fonts.ready` gets no
benefit: by the time Rocket releases the delayed scripts on first interaction,
both events fired long ago and will never fire again. Only `resize` /
`ResizeObserver` can still rescue it, so the section stays broken until the
visitor resizes the window or reloads with a cold cache.

Clearing the cache "fixes" it because the next response is served before the
optimisation is reapplied. That is why the client sees it fixed and you cannot
reproduce it.

**Do not test this with a cache-busting query string.** WP Rocket does not serve
its optimised cached page for URLs carrying a query string, so `?cb=12345`
quietly gives you the *unoptimised* page and the bug vanishes. Request the bare
URL, twice, in a fresh browser context, and **do not move the mouse, scroll or
type** before measuring — any of those releases the delayed scripts.

Diagnosis that actually distinguishes the two states:

```js
// bare URL vs ?nowprocket=1, no interaction either time
script type variants present   // 'text/rocketlazyloadscript' => delay JS is on
document.querySelector('.gw-rail')          // the thing the script builds
```

Fix is a native setting, not a code change — add a token unique to the inline
script to **delay_js_exclusions**:

```php
$s = get_option('wp_rocket_settings');
$s['delay_js_exclusions'] = array_merge($s['delay_js_exclusions'] ?? [], ['gw-rail']);
update_option('wp_rocket_settings', $s);
rocket_generate_config_file();   // Rocket reads a generated config, not just the option
rocket_clean_domain();
```

Rocket matches those patterns against inline script **contents** as well as
`src`, so any identifier that appears in the script works.

An **empty** `delay_js_exclusions` on a site with hand-built interactive
sections should be treated as a bug waiting to happen — audit every custom
component, not just the one that was reported.

### WP Rocket keeps generated output in its own tables — purging the cache does not clear them

`rocket_clean_domain()` clears the **page** cache. It does **not** clear the
tables Rocket generates and stores per URL, and those tables bake asset URLs
into the served HTML. After changing any image, CSS or background, a purge can
therefore look like it did nothing.

On Greyson staging (Rocket 3.23.3.3) the tables are:

| table | holds | symptom when stale |
|---|---|---|
| `wp_wpr_above_the_fold` | the **LCP image URL** per page (`lcp` column) | `<link rel="preload" data-rocket-preload as="image" href="old.png" fetchpriority="high">` — the browser downloads an image the page no longer shows |
| `wp_wpr_rucss_used_css` | Used CSS (Remove Unused CSS) | old `background-image:url(...)` inlined in the page |
| `wp_wpr_lazy_render_content` | below-the-fold HTML | old markup returns after a purge |
| `wp_wpr_preload_fonts`, `wp_wpr_preconnect_external_domains` | per-URL hints | stale hints |
| `wp_wpr_rocket_cache` | ATF job status only (`id,url,status,modified,last_accessed,is_locked`) | jobs stuck `pending` |

This version has **no** `rocket_clean_used_css()` function, and the
`…RUCSS\Database\Queries\UsedCSS` class has no remove-all method — check with
`get_class_methods()` before relying on one. They are all regenerable caches, so
truncating them directly is safe:

```php
foreach ( [ 'wp_wpr_above_the_fold', 'wp_wpr_rucss_used_css', 'wp_wpr_lazy_render_content',
            'wp_wpr_preload_fonts', 'wp_wpr_preconnect_external_domains', 'wp_wpr_rocket_cache' ] as $t ) {
	$wpdb->query( "TRUNCATE TABLE `$t`" );
}
```

`wp_wpr_above_the_fold` is the one that catches you out: it is the *last*
thing still serving the old URL once everything else is clean, and its name does
not appear in any Rocket purge helper.

### On WP Engine, `x-cache: HIT` means you are not testing what you think

WP Engine puts Varnish in front with `cache-control: max-age=600`. A response
header of `x-cache: HIT: 7` (the counter increments per hit) means the HTML came
from the edge, not from WordPress. Check it before concluding a change did not
work:

```js
const res = await p.goto(url); res.headers()['x-cache']
```

`WpeCommon::purge_varnish_cache( null, true )` purges site-wide and
`WpeCommon::purge_varnish_cache( $post_id )` purges one post; after a real purge
the next response shows `x-cache: MISS`. Note `WpeCommon::purge_object_cache()`
is **not** static and throws if called statically — use `purge_memcached()`.

### Percent-encoded image URLs hide from a URL-level find/replace

Elementor dynamic tags store their settings percent-encoded inside
`_elementor_data`, e.g. a JetEngine meta field with an image fallback:

```
%7B%22meta_field%22%3A%22gr_hero_image%22%2C%22fallback%22%3A%7B%22url%22%3A%22https%3A%5C%2F%5C%2F…%5C%2Fhero.png%22…
```

A replace built from full URLs — plain and `\/`-escaped — misses these, so the
old image quietly keeps rendering on every page that uses that template. The
**filename** inside the blob is not encoded (only the slashes and colon are), so
replace at filename level and every encoding is covered at once.

### Elementor containers use `css_classes`, widgets use `_css_classes`

Adding a custom CSS class programmatically to an Elementor **container**
(section) by writing `_css_classes` into its settings does nothing. The value is
stored, survives a re-save, and is silently ignored — the class never reaches
the markup, so any CSS hanging off it appears to "not apply".

| element | control id |
|---|---|
| widget | `_css_classes` |
| **container / section** | **`css_classes`** |

Confirm against the live control list rather than assuming:

```php
$el = \Elementor\Plugin::$instance->elements_manager->get_element_types('container');
foreach ($el->get_controls() as $k => $c) if (stripos($k, 'class') !== false) echo "$k\n";
// -> css_classes
```

The symptom is distinctive: the injected `<style>` is present in the page
(`styleTagHasX: true`), the scope selector matches, but
`document.querySelectorAll('.your-class').length === 0`. Check the rendered
class list on the section before debugging the CSS.

### A CSS marquee needs its track duplicated, and `overflow:hidden` on the wrapper

The two-row review marquee pattern (ascend.science and now Lightning Peptides):

```css
.fade  { overflow:hidden; mask-image:linear-gradient(to right,transparent,#000 22%,#000 78%,transparent) }
.track { display:flex; width:max-content; animation:left 48s linear infinite }
@keyframes left  { to { transform:translateX(-50%) } }
@keyframes right { from { transform:translateX(-50%) } }
```

The `-50%` only looks seamless because the track contains its cards **twice**.
Halve that and the loop jumps. The wrapper's `overflow:hidden` is what stops the
oversized track adding horizontal page scroll — a mask alone does not clip
layout.

When auditing such a page, remember the track legitimately measures far wider
than the viewport. An overflow check must ignore anything with a clipping
ancestor, or it reports thousands of pixels of phantom overflow:

```js
let n = el.parentElement, clipped = false;
while (n && n !== document.body) { const o = getComputedStyle(n).overflowX;
  if (o === 'hidden' || o === 'clip' || o === 'auto' || o === 'scroll') { clipped = true; break; }
  n = n.parentElement; }
```

## Elementor-generated widget CSS beats your page stylesheet

If a control has a `selectors` entry, Elementor writes it as
`{{WRAPPER}} …` where WRAPPER expands to
`.elementor-<page> .elementor-element.elementor-element-<widget>`. That is
three classes plus a descendant chain — a hand-written
`.elementor-<page> .elementor-element-<section> …` rule will lose to it.

Symptom that identifies this exactly: **the rule works at some breakpoints and
not others.** Many third-party controls carry different `laptop_default` /
`tablet_default` values, so Elementor only emits the competing declaration at
the widths where a default exists. On Lightning Peptides, Jeg Kit's
`st_arrow_normal_left_arrow_offset` defaults to `-96` on desktop but `0` on
laptop and tablet, so carousel arrows obeyed my CSS at 768 and 390 and ignored
it at 1440.

Don't escalate with `!important` — find the control and set it. Dump the
widget's settings, then grep the plugin's `class-*-option.php` for the CSS
property:

```php
foreach ($w['settings'] as $k => $v) if (stripos($k,'arrow')!==false) …
```

Use CDP `CSS.getMatchedStylesForNode` to see which rule actually wins, in
order, rather than reasoning about specificity:

```js
const cdp = await ctx.newCDPSession(p);
await cdp.send('DOM.enable'); await cdp.send('CSS.enable');
const { root } = await cdp.send('DOM.getDocument');
const { nodeId } = await cdp.send('DOM.querySelector', { nodeId: root.nodeId, selector });
(await cdp.send('CSS.getMatchedStylesForNode', { nodeId })).matchedCSSRules
```

Last match wins, and it prints the origin, so the answer takes one run.

## Jeg Kit carousels ignore the base "slides to show" value

`sg_carousel_slide_show_responsive` on its own does nothing.
`class-product-carousel-view.php` builds Tiny Slider's map from the
**per-breakpoint** keys `sg_carousel_slide_show_responsive_<breakpoint>`, each
cascading from the previous one. A carousel set to 8 in the base key rendered 4
until every per-breakpoint key was written. Set them all explicitly.

## A transform can cause horizontal scroll with no overflowing element

An overflow finder that walks the DOM for `rect.right > viewport` and skips
anything under a clipping ancestor will report **nothing** while the page still
scrolls sideways. `transform: scale()` does not change the layout box, so the
element's own geometry looks innocent, but the painted result still counts
toward `scrollWidth`.

Walk `scrollWidth > clientWidth` down from `documentElement` instead — that
chain leads straight to the container, and comparing `getBoundingClientRect()`
against computed `width` exposes the scale (110px painted vs 73.6px laid out
= `scale(1.5)`).

Note also that `overflow-x:hidden` on `body` alone does not stop it; the
`html` element still reports the larger `scrollWidth`.

## Read the class off the DOM, never off the setting name

Jeg's card element is configured as `category` in
`sg_content_show_element`, the wrapper class is `jkit-product-category` by
every naming convention in the plugin, and the actual class is
**`jkit-product-categories`** — plural. A stylesheet written against the
singular matched nothing, and because the plugin's own default styling was
still showing, the result looked like a *specificity* problem rather than a
typo. Two rounds were lost to that.

One `getComputedStyle` probe settles it in one run:

```js
[...wrapper.querySelectorAll('*')].filter(e => /categor/i.test(e.className))
```

If a rule appears to have no effect at all — not partially overridden, but
*nothing* — check the selector matches something before reaching for
specificity or `!important`:

```js
document.querySelectorAll('<your selector>').length
```

## Tiny Slider items will not equalise height on their own

`.tns-item` is `inline-block`, so cards in a row end up whatever height their
content dictates and a single wrapped button makes one card taller. There is no
tns option for it. The fix is CSS and it does not disturb the slider, which
positions by transform on `.tns-slider`:

```css
.tns-slider{display:flex;align-items:stretch}
.tns-slider > .tns-item{flex:0 0 auto;height:auto;display:flex}
```

Then make the card a flex column and push the button down with
`margin-top:auto`. Anything above the button that can wrap (title, price,
category) needs an explicit `min-height` matching its real `line-height`, or
the elements below it still sit at different heights from card to card.

## Verify :hover with CDP forcePseudoState, not a synthetic hover

`page.mouse.move()` and `locator.hover()` did not change what
`getComputedStyle` returned for a hovered button in headless Chrome here —
twice, at two viewports — which reads exactly like "the hover CSS did not
apply" when the CSS was fine. Force the state and inspect the cascade instead:

```js
await cdp.send('CSS.forcePseudoState', { nodeId, forcedPseudoClasses: ['hover'] });
const m = await cdp.send('CSS.getMatchedStylesForNode', { nodeId });
// last matching declaration for a property is the one that wins
```

Read the *winning declaration* rather than the computed value: it survives the
forced-state quirks and tells you which selector won, which is the thing you
actually need. And call `getMatchedStylesForNode` while the state is still
forced — resetting it first drops every `:hover` rule from the result.

A hover that recolours only the container is half a fix whenever the visible
glyph is a child element with its own colour rule: gold button + gold icon is
an invisible control, not a styled one. Set both.

## Raising specificity can silently revert a setting you already made

After widening a selector to beat a plugin's CSS, that same selector also
outranks **Elementor's generated rules for the widget's own controls**. A
`left:4px` written months-in-spirit earlier, harmless while it was losing,
started winning and undid an arrow-offset setting without any error.

Rule of thumb: once a selector is strong enough to beat `{{WRAPPER}}`, delete
from it every property that a widget control also owns. Keep the stylesheet for
what has no control (layout, flex, pseudo-states) and leave the rest to
settings. Re-measure the properties the control governs after any specificity
change — they are the ones that break quietly.

## Never run image processing against a live original

On Lightning Peptides a 2048x2048 PNG disappeared from `wp-content/uploads`
during a sequence of `new Imagick($file)` / `trimImage` / `writeImage` calls
against that path. It was the only missing original out of 184 image
attachments, and nothing in the scripts deletes anything. Cause never
established — which is the point.

The URL then 404s while `wp_get_attachment_metadata()` still reports the full
size, so the site looks fine anywhere a generated size is used and breaks only
where the original is requested.

Work on a copy:

```php
$b = file_get_contents(get_attached_file($id));
printf("BYTES:%d\nMD5:%s\nB64START\n%s\nB64END\n", strlen($b), md5($b), base64_encode($b));
```

Process locally, upload the result as a *new* attachment, verify md5 both ways.

Check for missing originals before trusting any image work:

```php
foreach ($attachment_ids as $id) {
  $f = get_attached_file($id);
  if ($f && !file_exists($f)) { /* original gone, sizes may still be there */ }
}
```

Recovery: UpdraftPlus uploads archives are plain zips, and entries are prefixed
`uploads/`, so `locateName('2026/09/file.png')` alone returns false. Try
`'uploads/' . $entry` too.

## You cannot colour-key a white cap off a cream background

Removing a flat background with a distance threshold destroyed the white cap of
a product vial: cap `rgb(255,255,255)` against background `rgb(255,252,241)` is
a distance of **14.3**, so any tolerance loose enough to catch anti-aliased
edge pixels also eats the cap.

Measure the background before choosing a threshold. If it is generated
artwork it is often *perfectly* flat:

```python
d = np.sqrt(((img - img[0,0]) ** 2).sum(axis=2))
print(d[:300,:300].max())   # 0.00 -> threshold of 2 is plenty
```

Then flood fill **from the border only** — connected, not global — so light
pixels enclosed by the subject are never candidates, and feather one pixel on
the silhouette. Always check the result composited on the colour it will sit
on; a halo or a hole is invisible against white.

## Elementor's hide_mobile is not reliable with custom breakpoints

Setting `hide_mobile => 'hidden'` on a widget hid it at **every** viewport
width, 1440 included, on a site with six custom breakpoints active. The class
renders, but which media query `elementor-hidden-mobile` is generated into
depends on breakpoint CSS that a direct DB write does not regenerate.

Use a per-element `custom_css` media query instead — explicit about the width,
and independent of generated breakpoint CSS:

```css
@media (max-width: 767px) { selector { display: none; } }
```

Verify across a spread of widths, not just one: the failure here looked
correct at the one width that was checked first.

## Image widget height comes from the file, not the settings

The Elementor image widget's width is `space` (a px max-width) and its height
is derived from the image's own aspect ratio. Swapping in a file with a
different ratio silently changes every layout it appears in — ar 0.66 to 0.44
is a 50% height increase.

When replacing images in bulk, scale `space` (and `space_tablet`,
`space_mobile`, plus any custom-breakpoint variants) by `newAr / oldAr`, read
from `wp_get_attachment_metadata()` rather than assumed. Widgets that set an
explicit `height` are unaffected and must be skipped, or they get squashed.

Measure `document.documentElement.scrollHeight` on the affected pages before
and after: it should not move.

## WP Rocket Remove Unused CSS outlives a page rebuild

Replace a page's Elementor content and the page can render as unstyled plain
text while the markup is perfectly correct. Symptom: containers carry
`e-con e-flex` but compute `display: inline`, and the page has a `wpr-usedcss`
`<style>` block instead of `elementor-frontend-inline-css`.

WP Rocket saved a used-CSS sheet built from the OLD markup. `rocket_clean_domain()`
clears the page cache and leaves it alone, because it lives in its own table:

```php
$t = $wpdb->prefix . 'wpr_rucss_used_css';
$wpdb->query( $wpdb->prepare( "DELETE FROM `$t` WHERE url LIKE %s", '%become-a-member%' ) );
```

Check `inlineStyleTags` for `wpr-usedcss` before blaming Elementor's own CSS
cache - regenerating `\Elementor\Core\Files\CSS\Post` will not help.

## A template kit's wp_page_template can delete the site header

Envato-style kits export `wp_page_template: "elementor_canvas"` in each
template's metadata. Canvas renders **no header and no footer**. If the kit's
templates do not contain their own nav - and page templates usually do not -
applying that setting strips the site header, nav and footer from every page
imported. Keep the page's existing template (`elementor_header_footer`) and
only take the kit's `content` and `page_settings`.

## Percentage widths cannot share a row with a fixed flex gap

`width: 31.94%` × 3 in a row with `gap: 26px` overflows by 0.17px at a 1240px
container and by ~10px at 1000px, so the last card wraps. Kits ship this
constantly (31.94 for thirds, 23.43 for quarters, 48.95 for halves - all just
under 100/n, which is still too wide once a gap exists).

Use a calc that subtracts the gaps:

```
calc((100% - 52px) / 3)     // 3 across, 26px gap
calc((100% - 78px) / 4)     // 4 across
```

In Elementor set the width control's unit to `custom` and the size to the calc
string. Percentages only work if the gap is also a percentage.

## Screenshotting a site with WP Rocket Delay JS

Elementor entrance animations set `visibility: hidden` via `.elementor-invisible`
and rely on `elementorFrontend` to clear it. WP Rocket's Delay JS holds all
JavaScript until a **real** user interaction, and `page.evaluate(() => window.scrollTo(...))`
is not one - so screenshots show large blank bands and the page looks broken
when it is fine for visitors.

Interact for real before capturing:

```js
await p.mouse.move(400, 400); await p.mouse.wheel(0, 250);
await p.keyboard.press('ArrowDown');
await p.waitForTimeout(2500);
```

Then assert `document.querySelectorAll('.elementor-invisible').length === 0`
before trusting the screenshot.

---

## Elementor 4.x traps when generating `_elementor_data` by script (2026-09-23, Live Fatima)

Found while rebuilding a page natively to match an HTML prototype. Each one produced
a render that *looked* nearly right; only a paired measurement (prototype vs live,
same selectors, `scratch/lf-bam-measure.mjs`) exposed them.

1. **Every flex container becomes `width:100%` on mobile** unless `width_mobile` is
   set. Elementor ships `@media(max-width:767px){.e-con.e-flex{--width:100%}}`. An 8px
   dot, a 48px badge or an `auto`-width row silently goes full width on phones, and a
   wrapping row of chips stacks vertically. Copy `width` into `width_mobile` explicitly.
2. **`_element_custom_width` does nothing without `_element_width: 'initial'`.** The
   width value is stored and shown, but no CSS is emitted. Custom units work
   (`{unit:'custom', size:'min(680px, 100%)'}`), as they do for container `width`,
   `min_height` and typography `font_size`.
3. **Heading widgets rendered as `span`/`p` pick up theme spacing.** A `span` title
   inside the widget div sits in a line box at the *body* line-height (26.4px on Hello +
   a 1.65 kit), so small labels grow 3–6px. A `p` title gets the theme's paragraph
   `margin-bottom`. Use `header_size: 'div'` for labels, and zero `.elementor-heading-title`
   margins.
4. **Inline-block buttons do the same.** `.elementor-button` sits on the baseline of a
   body-line-height line box, so a row of text + button grows ~11px. `vertical-align:top`
   on the button fixes it.
5. **Per-element CSS loses to Elementor's widget selectors** (`.elementor-NNN
   .elementor-element-xxx .elementor-field-group`, 0,3,0). Prefix class rules with
   `.elementor` and chain classes. Form field typography also styles acceptance
   (checkbox) labels, so style those at higher specificity.
6. **Don't set `padding` on nested-accordion content containers.** The accordion's
   `content_padding` is applied through `--padding-*` variables, and the child
   container's own padding setting overrides it.
7. **Never use `?m=` as a cache-buster.** `m` is a WordPress query var (archive month),
   so the page 404s and every selector measures as missing. Use `?nc=`.

### More Elementor 4.x generation traps (2026-09-23, Apostolates rebuild)

8. **Custom background positions reset to `0px 0px` on tablet and phone.** With
   `background_position: 'initial'` plus `background_xpos`/`background_ypos`, Elementor
   also emits `background-position:0px 0px` for tablet and mobile from the responsive x/y
   defaults. Desktop looks right, so a 1440 check won't catch it. Always set
   `background_xpos_tablet/_mobile` and `background_ypos_tablet/_mobile` too (`scratch/lf-el-lib.mjs`
   `con()` now does this automatically).
9. **Icon-list spacing is not what the settings say.** The text span has its own
   `padding-inline-start:5px`, 18px icons carry an extra ~5px, and the `<svg>` gets a
   `7.5px` right margin. The icon slot's width is border-box *including* `text_indent`. Measure
   the glyph position with a Range, not the span box.
10. **SVG icons are sized by height only.** A tall `viewBox` shrinks the glyph (a 30px icon
    rendered 12.5×30). Give the `<svg>` an explicit square width and height, like an inline
    `<svg width="30" height="30">`.
11. **Counter widget:** `number_alignment: 'start'` emits a literal `text-align:{{VALUE}}`
    (dropped by the browser, but it is broken CSS, so leave the setting out). An empty
    prefix/suffix span becomes the number's first baseline and drops baseline-aligned rows
    by 4px, so hide `:empty` prefix/suffix.
12. **Icon widgets and `fill`:** Elementor sets `fill` on the root `<svg>`, which floods
    stroke-only icons. Bake the colour into a `<g fill=… stroke=…>` wrapper inside the file.
13. **Large `/run` bodies get a 502 from WP Engine** before the script runs (a 175KB page
    payload, ~350KB request). Nothing is written. Send the JSON with `scripts/rfile.ps1` and have
    the apply script read and checksum it (`scratch/lf-page-apply.tpl.php`, `FILE:` payloads).
14. **Prototypes don't always render what their CSS says.** A more specific rule can win
    (`.work p` beat `.take`; `.cta-text p` beat `.signoff`). Measure the prototype's
    *computed* style and match that, then say so.

### Traps from the Resources section rebuild (2026-09-24, Live Fatima)

15. **WP Engine answers 429 to bursts.** Checking ~80 links back to back returned `429 Too
    Many Requests` for a third of them. Those are throttled requests, not broken links. Pace
    link checks at about 0.7s each and retry 429s after a pause before reporting anything.
16. **Inline scripts can opt out of WP Rocket's Delay JS** with a `data-nowprocket` attribute
    on the `<script>`. Use it for anything the first paint depends on (opening accordion items,
    wiring a print button); everything else can wait for the first interaction.
17. **A text widget set to "grow" in a flex row does not shrink.** It sizes to its content, so
    a long paragraph beside a label overflows the page at tablet widths. Give the widget an
    explicit custom width (`calc(100% - Npx)`) per breakpoint. The same applies to auto-width
    containers that hold text.
18. **Nested-accordion titles accept inline HTML** (`<span class=…>` renders), so a subtitle
    or a number prefix can be styled inside the title without extra widgets.
19. **Headless screenshots of long Elementor pages need a slow scroll.** At 400px per 100ms,
    entrance animations on a 10,000px page never fired, and whole sections looked blank. 300px
    per ~200ms is reliable; always assert `.elementor-invisible` is 0 before trusting a shot.
20. **`display:flex` on `.elementor-icon-wrapper` drops the widget's own alignment**
    (Elementor aligns icons with `text-align`). Add `justify-content` for centred icons.
21. **Flex children around tables need `min-width:0`.** Without it, a text widget holding a
    wide table grows to the table's width, and the `overflow-x:auto` scroll never kicks in.

### Traps from the speed pass (2026-09-24, Live Fatima)

22. **Converter for Media's WebP does nothing on WP Engine.** Its default `.htaccess` loader is
    ignored by nginx, so the small WebP copies in `uploads-webpc/` are never served. What the
    browser gets instead is Cloudflare Polish converting the original *losslessly*
    (`cf-polished: ok`, `cf-bgj: imgq:100`): a 2.9 MB PNG came out as a 1.2 MB "webp". Check with
    `curl -I -H "Accept: image/webp" <png url>`. The fix that works is new, lossy WebP
    attachments swapped into content (`scratch/lf-imgopt.php`: dry / make / swap / rollback).
23. **Clearing the RUCSS table makes the next measurement look worse.** Until WP Rocket
    regenerates used-CSS, every plugin stylesheet ships in full (CSS per page went 0 → 120 KB).
    Measure page weight again after the cache has warmed up, not straight after a purge.
24. **`shot.mjs` output paths are relative to `shots/`.** Passing `shots/x.png` writes
    `shots/shots/x.png`. For before/after comparisons use full-page captures with the same scroll
    routine (`scratch/lf-fullshot.mjs`) plus `scratch/lf-pixdiff.mjs`. Viewport shots differ by
    tens of percent from scroll offset alone.

### Traps from the Imperia El Nino hubs (2026-09-24)

25. **Elementor containers take `css_classes`; widgets take `_css_classes`.** Put `_css_classes` on a container
    and it is silently ignored, along with every rule that targets the class, including the container's own
    `custom_css` if it keys off that class. Probe for the class before trusting the styles.
26. **Don't `pre('typography', …)` an already-prefixed group.** The button widget's typography prefix *is*
    `typography`, so re-prefixing `typo()` output produced `typography_typography_typography` and the font was
    ignored (Roboto 500 instead of Roboto Condensed 600 uppercase). Pass `...typo(...)` straight in.
27. **Hostinger answers bursts with a JS bot challenge** ("Checking your browser… Just a moment", HTTP 403).
    This is separate from the first-hit 403. Ten cache-busted page loads in a row were enough. Every check
    then "fails" (no title, no ld+json, no links), and it looks like the site is broken. Detect the challenge
    title, wait for it to clear, pace requests about 2.5s apart, and drop `?nc=` on this host.

### Trap from Pepcore (2026-09-24)

28. **Query-string tests bypass WP Rocket, so they can hide a broken optimised page.** After an Elementor/Pro
    auto-update (4.3.x), Pro began calling the `wp` global without declaring the dependency. WP Rocket's Delay JS
    held back `hooks.min.js` and `i18n.min.js` but not Pro, so every *cached* page threw "wp is not defined" and
    Pro widgets (the phone burger menu) died. `?nocache` tests looked perfect.
    - To test what visitors really get, load the WP Rocket-cached page, and if Cloudflare is in front, go to the
      origin: Chrome `--host-resolver-rules="MAP example.com <origin-ip>"`.
    - Fix: add the missing core deps through the `rocket_delay_js_exclusions` filter in an mu-plugin.

### Traps from the Live Fatima forms + review pass (2026-09-25)

- **PowerShell `*>` / `Out-File` truncates `rwpphp.ps1` output at the console width (~120 chars).** A URL list
  saved that way had every long permalink cut off, and the crawl then "found" 17 published pages returning 404.
  They were all 200. To capture long output to a file, call it from Bash:
  `WPSD_CONFIG=x powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/rwpphp.ps1 script.php > out.txt`.
  (`Tee-Object` / `| Out-File` capture nothing at all, because the wrapper writes to the host, not the pipeline.)
- **"Form submitted OK" on screen does not mean mail went out.** Check `wp_e_submissions_actions_log` (Elementor)
  and WP Mail SMTP's `wp_wpmailsmtp_debug_events`. SendGrid's "Authenticated user is not authorized to send mail"
  means the key lacks the `mail.send` scope. SendGrid's retired free plan leaves keys valid (GET /v3/scopes → 200)
  but unable to send. Check with GET /v3/scopes and /v3/user/credits; neither one sends anything.
- **Vimeo 401 in a headless crawl is a false positive.** Vimeo's Cloudflare bot check refuses headless Chrome
  ("We couldn't verify the security of your connection"), and production shows the same. A 403 "This video isn't
  available" is real: the video is deleted or private, and `vimeo.com/api/oembed.json?url=…` returns 404.
- **Setting Elementor form `submit_actions` explicitly replaces the defaults, and the defaults include
  `save-to-database`.** Adding "email2" as `["email","email2"]` silently stopped submissions being stored. Read
  `apply_filters('elementor_pro/forms/default_submit_actions', ['email'])` first and keep what it returns.
- **Before deleting "every trace" of a test email address, check `wp_users`.** The address given for a test can be
  a real admin account's email (it was the bridge login's). Delete the test submission by ID, not by address.

### Traps from the Live Fatima thank-you page (2026-09-25)

25. **Your own `::before` on an Elementor container inherits `width:100%; height:100%`.** Elementor styles every
    `.e-con::before` as its background-overlay layer. A 2px "track line" set with `left`/`right` came out 1312px wide
    and pushed the page sideways by 154px. Set `width:auto` (and `opacity`/`border-radius`) explicitly on any custom
    pseudo-element on a container.
26. **Elementor background overlays default to 50% opacity.** A prototype gradient copied into `background_overlay_*`
    renders half as dark, and white hero text becomes hard to read. Set `background_overlay_opacity: {size: 1}`.
27. **Elementor's form redirect action rejects relative URLs** (`FILTER_VALIDATE_URL`). `redirect_to` must be absolute,
    so it carries the dev domain until the go-live search-replace.
28. **A `cat > file` with no heredoc in a Bash chain waits on stdin forever.** The command looks like a hung browser
    script until it times out.
29. **Git Bash rewrites a leading-slash argument into a Windows path** (`/become-a-member/` →
    `C:/Program Files/Git/become-a-member/`). Pass URL paths without the leading slash, or set `MSYS_NO_PATHCONV=1`.

### Traps from the Pepcore speed pass (2026-09-25)

30. **Check OPcache before blaming plugins or the database.** On shared CloudLinux hosting the per-account OPcache (128 MB)
    fills up with a WooCommerce + Jetpack + Elementor stack. Once it is full, new files are never cached and the hit rate
    sits around 60%. `opcache_get_status(false)`: look at `cache_full`, `opcache_hit_rate` and `interned_strings_usage`. The
    sizes are PHP_INI_SYSTEM, so only the host can raise them.
31. **Measure PHP time from inside the request, not TTFB.** A cookie-gated mu-plugin that logs phase marks against
    `REQUEST_TIME_FLOAT` showed PHP at a steady ~1.8 s while TTFB ranged from 2.6 to 21 s. The difference is queueing before PHP
    starts (LVE throttling), and no amount of plugin tuning inside PHP removes it.
32. **Elementor's "All Singular" condition includes the 404 page.** A Single Post template with Post Content widgets then renders on every 404
    with no post, which means ~10 "Attempt to read property ID on null" warnings per bot hit. Add `exclude/singular/not_found404`.

### Trap from the Wasatch type system (2026-09-26)

33. **Playwright's WebKit on Windows can't render variable fonts.** Google Fonts now serves most families (Inter, Archivo,
    Roboto Condensed…) as variable woff2. In Playwright WebKit (WinCairo) the wdth/wght axes are ignored: condensed text comes
    out as overlapping glyphs, and bold comes out regular. Chromium and Firefox are fine. Real Safari supports variable fonts, but when
    Safari-engine proof is needed, pick a **static** family (Barlow, Barlow Condensed…) or check `scratch/wu-type/fonttest.html` first.
    Also: `mouse.wheel` throws in mobile WebKit, so scroll with `scrollBy` there.
34. **UpdraftPlus "succeeded" can still mean database only.** If `updraft_include_{plugins,themes,uploads,others}` are 0, a
    boot_backup(1,1) writes just the DB set. Check the set's entities before calling it a full backup.

### Trap from the Pepcore malware check (2026-09-27)

35. **The bridge used to leave executable PHP and downloadable source in public folders.** `get_temp_dir()` can be `wp-content/uploads`
    (a host sets WP_TEMP_DIR), and when the host killed a run mid-request, the temp script `wpsd-*.php` stayed there and could be
    executed over HTTP. `scripts/rfile.ps1 put` kept `file.php.wpsd-<ts>.bak` beside the file, and that is served as plain text (full source).
    Bridge 1.2.1 writes both to `<dir above ABSPATH>/wpsd-bridge/{tmp,backups}`. **Sites still on bridge ≤1.2.0 need the same cleanup**:
    delete `uploads/wpsd-*.php`, move `*.wpsd-*.bak` out of the web root (`scratch/pc-mw-cleanup.php`). After replacing a plugin file
    through the bridge, `opcache_invalidate()` it or the old code keeps running.

### Traps from the Wasatch Manrope change (2026-09-27)

36. **`pwsh` is not installed on this machine.** Run the wrappers as `powershell -ExecutionPolicy Bypass -File scripts/rwpphp.ps1 <script> [args]`.
37. **`rband.mjs` output also goes under `shots/`** (like shot.mjs, item 24): the prefix `scratch/wu7/ph` lands at `shots/scratch/wu7/ph-00.png`.
38. **A blanket "everything but icons" font rule must not use `[class*="icon"]`.** It also matches `.elementor-icon-box-title` and
    `.elementor-icon-list-text`. Exclude `i`, `.fa`, `[class^="eicon"]` and `[class^="fa-"]` instead.

### Traps from the Wasatch addendum build (2026-09-27)

39. **The bridge's stdout through PowerShell mangles some non-ASCII** (`·` came back as `�`). Never round-trip code or content you will
    write back through a text dump: fetch it base64 (`scratch/wu8-snipb64.php`) and send it back base64 inside the script.
40. **All-digit Elementor ids become integers as PHP array keys** (`'2214146' => ...` → int), so `=== $eid` lookups miss. Compare ids as strings.
41. **`:has()` eyebrow selectors out-rank component rules.** A step-number heading followed by an h3 matched the eyebrow rule and rendered
    12px; `:not(.wu-step__num)` was needed. Likewise a base `.elementor-widget-button:not(...):not(...) .elementor-button` rule (4 classes)
    beat per-variant colour rules - put only width/style in the base rule, colours in the variants.
42. **`max-width:700px!important` on text widgets broke phones** where a widget had a fixed Elementor width (638px): it replaced Elementor's
    `max-width:100%`. Use `max-width:min(700px,100%)`.
43. **New widgets inserted by script have no colour settings** and inherit the kit text colour (#2A2C31) - invisible on dark sections. Give
    new widgets a class the design system colours, or set a default text colour for the dark sections. Run a contrast check after inserts.
44. **Customizer "Additional CSS" can silently hide output** (here: every project-page shortcode and all card descriptions). Read
    `wp_get_custom_css_post()` before debugging "missing" markup.

### Traps from the Wasatch photo round (2026-09-29)

45. **Uploads can lose the camera's EXIF rotation.** The owner's originals carried orientation 6, but the site copies were stored
    sideways with no flag, so the magnifier showed them on their side. To find every case, compare each attachment's width/height with the
    owner original *after* applying EXIF (`scratch/wu10/owner-orient.json` + `att-dims.txt`). Fix at the source with `wp_save_image()`
    (`history=[{"r":-90}]`, `target=all`: the same as Media > Edit Image > Rotate right + Save). It keeps "Restore original image".
46. **The projects snippet's duplicate check keys on file size + dimensions**, so the same photo uploaded twice (`IMG_0566` / `IMG_0566-1`)
    is not caught and appears twice in a magnifier. Compare pixels (8-bit grey 64x48 mean-abs-diff under 1, against about 60 for different
    photos). Do not dedupe by filename: `unnamed.jpg` / `unnamed-1.jpg` are different Marzelli photos.
47. **Elementor custom background position is per device:** `background_position{,_tablet,_mobile}='initial'` plus
    `background_xpos*/ypos*` in %. It works on the phone/tablet copy of a section even when that copy only has a tablet image. The
    old `background_xpos` of -306px on many containers had no effect until position became `initial`, so always set both X and Y.
48. **Element screenshots at a short landscape viewport (844x390) are garbage** when a sticky header is present: the capture scrolls
    and the header lands on the element. Measure hero contrast with a tall viewport (the hero height is in px, so the layout is the same).
49. **Measure contrast against the real photo:** hide the text (`color:transparent`), screenshot the hero, and take the 95th-percentile
    luminance inside each text line's box (`scratch/wu10-herocontrast.mjs` + `.py`). An eyeball check passed the Contact hero, which was
    at 2.4:1.
50. **`scripts/php.ps1 -l` does not work on this machine** ("phpDir is not set", no local config.json), and `| tail -1` hid that
    error all session. Lint with Local's PHP directly: `"$LOCALAPPDATA/../Roaming/Local/lightning-services/php-8.2.29+0/scripts/win32/php.exe" -l file`.
    Never pipe a lint through `tail`: check for "No syntax errors".
51. **Elementor caches widget HTML per page (`_elementor_element_cache`).** A PHP change to how a widget renders (for example a
    `elementor_pro/forms/render_field/*` hook) does not show until you delete that postmeta for the page. The CSS change showed at
    once, so the page briefly had neither the old nor the new help line.
52. **Bash heredocs in this harness can eat backslashes** (`\` became `\` in generated JS/PHP), even when quoted. Write
    generated code with the Write tool, or avoid backslashes (`pathToFileURL`, `os.sep`).
53. **Cropping/rotating with wp_save_image renames the file** (`-e<timestamp>`). Anything that stores the URL (Elementor
    background_image.url, hard-coded <img src>, Yoast's wp_yoast_indexable og:image) keeps showing the old file until repointed.
    Delete the stale yoast_indexable rows; Yoast rebuilds them on the next visit.
54. **Playwright's WebKit on Windows draws text thinner and greyer than real Safari.** Metrics, colour and weights are identical to
    Chrome (measure them), but do not put its screenshots in client material as "Safari".
55. **During an outage, "rule out my change" steps get executed literally.** On Pepcore the owner deleted the mu-plugin and renamed
    the plugin folder as suggested, even though the cause turned out to be unrelated. After the site is back, re-check every change
    you suggested reverting and put it back.
56. **opcache can hide a deleted PHP file for minutes.** Some workers keep serving, so a fatal looks intermittent and "started later"
    than it did. Read the real error_log timestamps before concluding when something broke.
57. **`add_post_meta()` / `update_post_meta()` unslash their value.** A raw `_elementor_data` backup saved without `wp_slash()`
    loses its backslashes (`\/`, ` `, `\"`) and restores broken. Always `wp_slash()` JSON going into meta, then read it back
    and compare with `===` before relying on it.
58. **A PHP closure cannot hand back an array element by reference** (`$c = &$find(...)` from `function () use (&$find)` returns
    a copy). Edits land on the copy, the JSON is unchanged, and `update_post_meta` quietly returns false. Write in place with a
    recursive `function (&$els, ...)` and read the saved value back to prove the change took.
59. **Elementor builds a new page's CSS file from settings it cached earlier in the same request.** After `wp_insert_post` +
    setting `_elementor_page_settings` (custom CSS), `Post::create($id)->update()` in that request leaves the custom CSS out.
    Regenerate in a separate request and check the file for your rule.
60. **A host migration can quietly roll a site back.** Pepcore's move restored a copy from the night before: removed plugins came
    back, new mu-plugins were gone, and the crontab was empty while a mu-plugin still disabled WP-Cron. After any migration, check
    the Updraft history date, the mu-plugins list, `crontab -l` and the plugin list before assuming today's work is still there.
61. **Large files can't come back through the bridge in one response.** For backups, use `scratch/pc-bk-download.mjs` (chunked
    base64 through /run, 12 MB per request, md5 per file, resumable). UpdraftPlus splits archives at 25 MB anyway.

### Traps from the CAS mobile CLS/LCP pass (2026-10-06)
- **An image inside a `flex-wrap: wrap` column collapses until it loads.** Multi-line flex columns size each item at fit-content
  width; an `<img width=… height=…>` with `width:100%` contributes 0 px before its file arrives, so its widget is a few px tall and
  then jumps (CLS 0.14 on Elementor product galleries). float/flow-root/flex-shrink/min-height don't help - give the item a
  definite width (`width:100%`). Diagnose by blocking images (`page.route(/\.(webp|png|jpe?g)/, r => r.abort())`) and measuring.
- **Font-swap CLS without touching the design**: metric-matched fallback faces - `@font-face{font-family:"x-fb";src:local("Roboto");
  size-adjust:N%;ascent-override:…}` placed right after the web font in the stack. Measure N per weight as (web-font width /
  fallback width) over the site's real UI text with canvas measureText; ascent/descent = web font's metrics / N. Separate families per
  local font (Roboto = Android, Segoe UI = Windows, Arial = Apple) since each needs its own N. Took CAS shop CLS 0.115 -> 0.0003.
- **Seraphinite `img/lazy/load` puts loading="lazy" back on images you made eager** (it keeps `fetchpriority="high"` ones, via its
  default exclusion). Mark yours (`data-x-eager`) and add `.//img[@data-x-eager]` to contPr/img/lazy/excl.
- **Seraphinite sends `Cache-Control: max-age=3600`**, so a Cloudflare in front keeps HTML for up to an hour and a host purge
  (WP Engine) doesn't clear it. Test with a fresh random query string; tell the client changes appear within the hour.
- **Two tool calls in one message run in parallel** - "upload plugin" + "clear cache" side by side can clear before the upload lands.
  Run the cache clear after the upload returns.

### Trap from the Live Fatima cookie-banner fix (2026-10-06)
- **Bridge scripts share the bridge's function scope.** A script that sets `$start` (or other generic names) and returns normally
  overwrote the bridge's timer: the change was applied, then the REST call died with "Unsupported operand types: float - string"
  in wpsd-bridge.php and the output was lost. Prefix script variables (`$lf_*`) or end with `exit;`, then re-check state with a
  read-only mode before re-running.

## WooLentor Pro "Category Layout" silently breaks category pages (2026-10-06, Fir Park)
WooLentor Pro adds a "Category Layout" select to the product-category edit screen (term meta `wooletor_selectcategory_layout` -
note the typo). It has no empty option, so the first Elementor template in the list (often the **Site Header**) is saved
whenever anyone clicks Update on a category. WooLentor then routes the archive through its own `page/default.php` and renders
that template as page content: header twice, no products, HTTP 200, no errors - invisible to status/console sweeps.
Check: `get_term_meta( $id, 'wooletor_selectcategory_layout', true )` for every product_cat; a sweep must count headers and
product cards, not just status codes. Guard with `sanitize_term_meta_wooletor_selectcategory_layout`.

## Elementor 4: per-element render hooks don't fire for theme-builder columns
`elementor/frontend/column/before_render` (and the generic `elementor/frontend/before_render` for sections/columns) never fired
on Fir Park's archive templates (Elementor 4.2.4); widget-level `elementor/frontend/widget/before_render` did. To insert markup
next to a column, edit the finished HTML in an output buffer and fail safe (return unchanged if the anchor isn't found).

## The bridge's rfile put leaves *.wpsd-*.bak beside the file - downloadable in mu-plugins
`scripts/rfile.ps1 put` keeps the previous version as `<file>.wpsd-YYYYMMDD-HHMMSS.bak` in the same folder. In wp-content/mu-plugins
that is web-readable (Fir Park served them as text, 200). Delete them after verifying a deploy, keep the copies locally.

## A new heading can cost ~1 s of first paint if it pulls in an unused web font
Adding an `<h1>` that inherits the theme's h1 font (a webfont nothing else above the fold used) moved observed FCP after the load
event on Fir Park (shop LCP 5.8 -> 7.7 s, Lighthouse A/B). Give injected headings a font the page already loads.

## Seraphinite serves headless browsers a different page - test with a normal userAgent (2026-10-07, Queen East)
Seraphinite Accelerator builds separate optimised variants, and Playwright's default "HeadlessChrome" UA gets one that real visitors
never see. A layout bug (double-stretched Elementor section) was invisible in every headless check for days. On Seraphinite sites,
always add a run with `userAgent` set to a normal desktop/mobile Chrome string (or headed Chrome) before calling layout verified.

## Bridge 1.2.1 prepends a guard line - scripts cannot start with `namespace`
`scripts/rwpphp.ps1` scripts now run as `<?php defined('ABSPATH')||exit; …` + your file, so `namespace x;` is no longer the first
statement -> fatal "Namespace declaration statement has to be the very first statement". Use fully-qualified names instead
(scratch/sa-set-nons.php / sa-cache-nons.php replace cas-sa-set.php / cas-sa-cache.php).

### update_post_meta() on a revision ID writes to the PARENT post
`update_post_meta( $revision_id, ... )` silently redirects to the parent (it calls `wp_is_post_revision()` and swaps the ID).
A bulk search-replace that selects `_elementor_data` rows by meta value and writes each back with `update_post_meta( $row->post_id )`
will therefore overwrite the live page with each old revision's content in turn - whichever revision is processed last wins.
This reverted a client Home page (Black Bear Labs, 2026-10-09). Always JOIN posts and exclude `post_type = 'revision'`,
or use `update_metadata( 'post', ... )` / a direct `$wpdb->update` on the meta row when revisions really must change.

## Additional CSS is printed through strip_tags()
`wp_custom_css_cb()` outputs the Customizer's Additional CSS with `strip_tags()`, so anything that looks like a tag is deleted
on the front end, including inline SVG in `url("data:image/svg+xml,<svg ...>")`. Percent-encode `<` and `>` (`%3C`, `%3E`) in
SVG data URIs that go into Additional CSS. Also: right after `wp_update_custom_css_post()`, `wp_get_custom_css()` in the same
request can still return the old value. Check the live page's `<style id="wp-custom-css">` instead of trusting it.

## The kit background sits on body, and some pages depend on it
Elementor's kit sets `.elementor-kit-N { background-color: ... }` on `<body>`, which beats a plain `body {}` rule. Before you
override it site-wide, look for pages whose text sits straight on that background. Policy pages built from text widgets with
no section background usually do, and they turn into dark-on-black. Scope the override with body classes
(`body.woocommerce-cart`, `body.page-id-N`) instead.

## Removing Elementor Pro blanks theme widgets that share a Pro widget's name
With Elementor Pro absent, free Elementor's promotions module registers an empty `Pro_Widget_Promotion` placeholder for
every Pro widget name (`woocommerce-breadcrumb`, `form`, `posts`…). It registers on `elementor/widgets/register` at priority 10.
Themes that ship their own widget under the same name (Mixxcazt: `woocommerce-breadcrumb`) are overwritten whenever they
register first. The widget renders nothing on the front end, with no error. To diagnose,
`widgets_manager->get_widget_types( $name )` returns `Elementor\Modules\Promotions\Widgets\Pro_Widget_Promotion`. To fix,
re-register the theme's class at priority 20 when `ELEMENTOR_PRO_VERSION` is undefined, then regenerate that document's CSS.
The style controls were missing while the placeholder was registered. Check `recently_activated` for when Pro was switched off.

## WP Engine can empty advanced-cache.php under a page-cache plugin
On WP Engine, a platform action can rewrite `object-cache.php` and truncate `wp-content/advanced-cache.php` to 0 bytes in the
same second. Turning on WP Engine's Object Cache in the portal is the likely trigger. Plugins that serve pages from that drop-in
(Seraphinite, WP Rocket, etc.) then silently stop working. Seraphinite shows "advanced-cache.php has wrong content… save the
plugin settings", but saving can't repair it there: WPE blocks PHP from writing any `.php` file (Permission denied, even
when the file is owned by the PHP user). The file can only be restored over SFTP/SSH or with WPE's file manager. Check
`filemtime()` on both drop-ins to date the event.

## PowerShell `Compress-Archive` writes backslash entry names
A zip built with `Compress-Archive -Path dir` on Windows PowerShell 5.1 stores `dir\file.php`; WordPress' unzip treats that as one
file called `dir\file.php` and the plugin "installs" but is never found. Build plugin zips with .NET and explicit names:
`[IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $path, 'dir/file.php')` (see the qe-site deploy in the transcript),
or let the bridge create the folder (`wp_mkdir_p`) and `rfile.ps1 put` the file - `rfile put` refuses a path whose parent folder
does not exist yet ("outside wp-content").

## LocalWP was uninstalled on this machine (2026-10-11)
`scripts/php.ps1 -l` fails ("phpDir ... does not exist") and there is no other php.exe. For remote sites the bridge parse-checks every
`.php` it writes (`token_get_all(TOKEN_PARSE)`), so deploy with `rfile.ps1 put` and treat "PHP parse check passed" as the lint.

## UpdraftPlus + huge uploads = disk quota
A site with hundreds of thousands of images (Queen East: 449k png/jpg) produces dozens of 400 MB zip parts; on shared hosting
that exhausts the account quota mid-backup and *everything* that writes a file starts failing (bridge tmp, cache, media uploads).
Back up `--no-uploads` (db + plugins + themes + others) unless the uploads really must be included, and check "Web-server disk
space in use by UpdraftPlus" on the Updraft page first.

## Local Lighthouse vs this host
Lantern derives server latency from observed TTFB. From here a static file on Namecheap answers in ~1.1 s (RTT ~380 ms), so every
local Lighthouse run shows TTFB ~1.0-1.4 s and LCP ~2 s worse than PSI will. Compare runs with each other, not with CAS (WP Engine
edge, ~0.6 s).

## Critical-CSS generator: never de-duplicate rules across stylesheets
Header Footer Elementor prints the header template CSS inline *and* Elementor links the same post-8483.css; the two copies differed
slightly (one rule had a `transition`). `accel-critical-gen.mjs` used to drop a rule already seen in another sheet, so the phone
override from copy 1 landed before copy 2's desktop rule and lost: the header was 10 px shorter and the cart icon 15 px left
until the real stylesheets arrived - and a first tap on the icon hit the wrapper, not the link. Dedupe key now includes the sheet
index (2026-10-11). Symptom to look for: pre-/post-interaction geometry diff on header elements (see the probe in
docs/SITE-NOTES-queeneast.md) - any difference means a cascade-order bug in the generated CSS, not a missing rule.

## LCP image preload: put it AFTER `<meta name="viewport">`, and from the outermost buffer
A `<link rel=preload as=image imagesrcset imagesizes>` placed before the viewport meta is evaluated with the default 980 px
viewport, so on phones it fetches a different srcset candidate than the `<img>` later renders - two downloads, no LCP gain.
Insert it right after the viewport meta. Also: when several output buffers edit the HTML (mu-plugin at priority 0, plugin at 0),
the one started LAST runs FIRST and does not see the other's edits; register the accelerator's ob_start earlier (priority -5) so
it processes the final markup.

## Critical-CSS generator: order sheets by DOM position, not by CDP event order
`CSS.styleSheetAdded` events arrive in load-completion order. Using that as "document order" put Elementor's kit (post-7.css,
container 1290 px) before frontend.min.css (1140 px) and a theme reset before the kit button rule - equal-specificity rules then
resolved the wrong way in the inlined CSS (narrow header, wishlist link drawn as a button). accel-critical-gen.mjs now sorts sheets
by the DOM index of their owner <link>/<style> (DOM.querySelectorAll + describeNode -> backendNodeId = header.ownerNode).

## Delaying ALL JavaScript changes the look on JS-shaped themes
Elementor "stretched" sections, WooCommerce gallery thumbnails, price slider, quantity -/+ and wishlist links are built by JS. If
every script waits for interaction, the first screen differs from the design until the visitor scrolls - clients notice. Default to
delaying only third-party/tracking scripts, and prove parity with a pixel diff against ?accel=off before switching a site live.
Never re-fire DOMContentLoaded/load/jQuery-ready when the site's own scripts already ran (init runs twice).

## Inline JS inside PHP single-quoted strings: no regex literals with backslashes
`'...if(/\/jquery\//.test(s.src))...'` in a PHP single-quoted string arrives in the page as `if(//jquery//.test(...))` after the
edit tool / sed / node escaping layers - a `//` comment that swallows the rest of the line -> "Unexpected token" and the whole
loader dies (Queen East, 2026-10-11, live for ~10 min). Use `indexOf("/wp-includes/js/jquery/jquery.")` instead of regex literals,
and ALWAYS syntax-check the served loader (`new Function(text)`) on a test URL before switching a site live.

## Lighthouse/PSI (Lantern) ignores timers - only interaction-gated loading keeps scripts out of the score
Scripts fetched by a loader at `load + 300 ms` are simulated as fetchable as soon as the loader runs (initiator graph), so they still
compete with FCP/LCP in the simulation. Requests only disappear from the score if they start after the trace ends (~1 s after load
quiet) - i.e. on first interaction or a timer of several seconds. Queen East: 3.5 s after load.

## jQuery restored after load fires `ready` immediately - use holdReady
When a delay loader re-inserts jQuery after `load`, jQuery sees readyState 'complete' and queues ready on the next tick, before the
remaining restored scripts have run. Plugins that start on ready and announce it with an event (WooCommerce gallery ->
`wc-product-gallery-after-init`) fire before later scripts (theme) listen. Call `jQuery.holdReady(true)` as soon as the restored
jQuery has executed and `holdReady(false)` after the last restored script.

## Someone else changing caching plugins is the most common "it got slow again"
Check `recently_activated` (deactivation times) and the plugin list before re-tuning anything. Queen East had four caching swaps in
one day. A must-use guard notice (qe-speed-guard.php) makes the consequence visible to whoever swaps.

## WP Engine + Cloudflare: page "slow again after hours" = 10-minute edge TTL
WPE sends `max-age=600`; every Cloudflare POP expires pages after 10 min, and a warmer only refreshes the POP nearest to it.
Send `Cloudflare-CDN-Cache-Control: max-age=N` from PHP (edge-only, CF strips it). A plain `s-maxage` is rewritten by WPE into the
browser `max-age`. WPE mu-plugins dir may not be writable by the bridge (HTTP 500) — ship as a normal plugin zip.

## PowerShell 5.1 `Set-Content -Encoding utf8` adds a BOM
A BOM before `<?php` outputs bytes -> "headers already sent". Edit PHP with Write/Edit or python, never PS 5.1 Set-Content.

## WP Engine: purge_varnish_cache does not clear Cloudflare (Advanced Network / GES)
`WpeCommon::purge_varnish_cache()` clears WPE's page cache only; Cloudflare keeps its copy until its own TTL. Use
`WpeCommon::clear_cdn_cache()` to clear the edge. Matters as soon as the edge TTL is longer than WPE's 10 minutes.
Bridge writes into plugins/ and mu-plugins/ fail on WPE (HTTP 500) - ship plugin updates as zip via wp-admin.
Git Bash rewrites a bare `/` argument into `C:/Program Files/Git/` - prefix with MSYS_NO_PATHCONV=1.

## W3TC minify on WP Engine = one PHP request per file -> 429/504 for uncached visitors
With minify.rewrite off (required on WPE/nginx) each minified asset is `/?w3tc_minify=<id>.js` rendered by PHP. Logged-in users and
WooCommerce session holders bypass WPE's cache, so a checkout with ~100 scripts hits WPE's rate limit (429) and timeouts (504) ->
random JS packages missing ("Stripe is not defined", "createContext is not a function"). Never minify for those visitors
(define DONOTMINIFY), and test checkout logged in AND with a cart, several times in a row - a single cold run can pass.

## Clearing Elementor CSS while a page cache is on = cached pages missing their post-XX.css
Elementor regenerates post CSS on the first render after `files_manager->clear_cache()`. A page cache (Cache Enabler here) can
store that first render without the `<link id="elementor-post-NN-css">`, and LiteSpeed CSS minify can store empty minified copies
of the then-missing files (whole site unstyled). Order: clear Elementor CSS -> request every key page with `?nc=<random>` ->
clear the page cache -> warm. Check with `grep -o "elementor/css/post-[0-9]*"` on the cached HTML per page.

## Elementor responsive background images can silently not print
`background_image_mobile` was saved in `_elementor_data` but never reached post-NN.css (only `background_position_mobile` did).
On sections already hidden on desktop/tablet, set the base `background_image` instead. Always confirm via computed
`background-image` at the target width, not via the saved settings.

## Layout-shift observers in tests: don't drop `hadRecentInput` entries under touch emulation
With Playwright `isMobile/hasTouch`, Chrome marks early layout shifts as `hadRecentInput: true` although nothing was tapped, so
the usual `if (e.hadRecentInput) continue;` reports CLS 0 while Lighthouse (which counts them) reports 0.25. Sum every entry when
comparing with Lighthouse, and read the trace (`lighthouse --save-assets`, events named `LayoutShift`, `impacted_nodes` old/new
rects) to see exactly what moved and when.

## Cache Enabler: query strings bypass the cache - test URLs measure the uncached page
`?accel=test`, `?r=123` etc. are never served from Cache Enabler, so they show 5-13 s server time on slow hosts and can hide
render-timing bugs that only appear when the HTML arrives fast (cached). A/B with two query variants is fair; final numbers and
timing bugs need the plain URL.

## LiteSpeed Cache options with list values are stored as JSON strings
`litespeed.conf.media-lazy_exc`, `media-lazy_cls_exc` (and other list settings) hold text like '["a","b"]', not PHP arrays.
`(array) get_option()` wraps the string; write back `wp_json_encode( array(...) )`.

## WP Rocket delay-JS exclusions are substring matches against the whole tag
An exclusion like `cky-` (meant for CookieYes) also matches `e-sticky-js`, so Elementor's sticky script runs before the
still-delayed jQuery and throws on every cached page. Use long, specific patterns. And test **cached** pages: a
cache-busting `?nc=` param bypasses WP Rocket's optimisation entirely, so it hides exactly this class of bug. Warm the
cache with a plain request, then load the plain URL (and an `?fbclid=`/`?utm_` URL, which WP Rocket serves from cache).

## GTM: consent-blocked tags and "Once per page"
A tag with Additional Consent Checks set to "Once per page" is spent by a consent-blocked attempt on Page View; a later
consent-update event on the same page will not fire it. Use "Unlimited" plus a `window.__x` run-once guard in the script.

## Updating a plugin and re-activating it in the same PHP request can fatal
Plugin_Upgrader replaces the files, but classes from the old version are already loaded; calling activate_plugin() in the
same request mixed old and new WP-Optimize code -> "Call to undefined method" and the plugin stayed deactivated. Activate
in a separate request. Also: activation redirects (Smush) can bounce the bridge to wp-login - check state afterwards.

## PowerShell turns a comma-separated argument into an array
`rwpphp.ps1 script.php a,b,c` delivers "Array" to the PHP script. Quote it: `'a,b,c'`.

## UpdraftPlus "backup now" honours the include_* settings
If updraft_include_plugins/themes/uploads/others are 0, a scheduled or forced backup saves the DB only and still reports
success. For a real pre-change backup pass restrict_files_to_override => [plugins, themes, uploads, mu-plugins, others],
then verify each entity is in UpdraftPlus_Backup_History.

## Host malware scanners leave empty files behind
Imunify-style cleaners truncate infected files to 0 bytes instead of deleting them. Empty non-core .php files in wp-admin /
wp-includes / root are a record of past infections - compare against api.wordpress.org/core/checksums to find them.

## Elementor background image URL comes from id + size, not the stored url
Pointing `background_image.url` at a sized copy (`-1471x2048.webp`) does nothing - Elementor's media control rebuilds the CSS
URL with `wp_get_attachment_image_src( id, size )`, and an empty `size` means full. Set `size` (e.g. `2048x2048`) as well,
then check the URL the browser actually requests. Also: a same-resolution WebP of an already-compressed JPEG can come out
BIGGER - compare before swapping.

## Elementor 4.3.x: v4 "atomic" element styles disappear in theme-builder headers/footers
Atomic (e-flexbox etc.) styles live in uploads/elementor/css/local-<post>-frontend-<bp>.css, generated only for posts that
fired `elementor/post/render` before `elementor/frontend/after_enqueue_post_styles`. Header/footer templates render later, so
after any cache clear (kit save, Regenerate CSS) their file is never rebuilt and the elements lose all styling. Check
`curl .../local-<id>-frontend-desktop.css` (404) and convert the atomic containers to classic containers.

## Elementor Loop Grid: `:first-child` never matches a loop item
The grid outputs a `<style>` element before the items. Use `.e-loop-item:nth-child(1 of .e-loop-item)`.

## PHP heredoc: `{$var` starts complex syntax
Inside a heredoc, `@media (...){$S .x{...}}` is parsed as `{$S ...}` -> parse error, and the whole script silently does nothing if
you only watch the last output line. Write `{ $S` (with a space). Always read the full output of an apply run.

## Removing the bridge at handover: match the plugin FILE, never a name search (2026-10-20)
`GET /wp/v2/plugins?search=Site Doctor` also returns every plugin we wrote for the client, because their Author header is
"WP Site Doctor". A cleanup that deleted every search hit removed BBL Accelerator and Black Bear Labs - Store Rules from the
live store along with the bridge, then revoked the app password, leaving no way back in. Delete only
`wp-site-doctor-bridge/wpsd-bridge` (exact `plugin` field), revoke the password LAST, and check the site still works before
revoking. scratch/bbl/handover-cleanup.mjs now filters by the exact file.

## Git Bash also rewrites ENVIRONMENT VARIABLES that look like paths (2026-10-20)
`U=/some-page/ node script.mjs` reached the script as `C:/Program Files/Git/some-page/`. MSYS_NO_PATHCONV=1 covers arguments;
for env vars also set `MSYS2_ENV_CONV_EXCL='*'` (or pass the path as an argument instead).

## `hscroll.mjs` / `audit.mjs` H-SCROLL can be a false positive under `body { overflow-x: clip }`

They compare `scrollWidth` to `clientWidth`. With `overflow-x: clip` on body (Hello Elementor + some kits), an off-canvas
child (Elementor nav dropdown, a grid wider than its row) still inflates `documentElement.scrollWidth`, but the page cannot
actually be scrolled, and whether the flag fires depends on load timing (Greyson: home flagged, identical header elsewhere
"ok"). Before chasing it, test the real thing: `scrollTo(500, scrollY)` then read `scrollX` - 0 means no sideways scroll.

## Network Solutions can start 403-ing every multipart POST (and switch PHP file_uploads off)

On 2026-10-21 a platform change on Network Solutions (Black Bear Labs) added `file_uploads = Off` through the host's
`php.override.ini` (merged last, so an account php.ini cannot undo it) AND made the openresty front answer every
`multipart/form-data` POST with a bare "403 Forbidden" page. Symptoms: "Please select a file" on plugin upload,
`rest_upload_no_data` on media upload, and **the Forbidden page on WooCommerce add-to-cart** (the single-product form is
multipart by default). Quick test: `curl -X POST -F a=1 https://site/` -> 403 while `-d a=1` -> 200. Workarounds while the
host fixes it: raw-body REST media upload (`Content-Disposition` header), SFTP for files, drop the add-to-cart form's enctype,
send file-less FormData as urlencoded (jQuery ajaxPrefilter).

## Hostinger CDN + LiteSpeed CSS minify = stale styles after Elementor edits

LiteSpeed Cache's CSS minify writes `wp-content/litespeed/css/<hash>.css?ver=<5 chars of hash>` with a name that does
NOT change when the source (e.g. Elementor `post-553.css`) is regenerated. Hostinger's CDN (`server: hcdn`) caches it with
`max-age=31557600`, so after an Elementor edit some edges keep serving the old copy: new sections/elements arrive with no
CSS (Elementor containers fall back to `display: inline`, content jammed at x=0). The server and a US edge served the new
file while an India edge served the old one - so it can look fine for one person and broken for another. Purging LiteSpeed
does not purge the CDN. Fix used on Medina: LiteSpeed CSS minify OFF **and "Remove Query Strings" (optm-qs_rm) OFF** -
with qs_rm on, even Elementor's own `post-*.css` loses its `?ver=<time>` and the CDN serves the old file again
(`x-hcdn-cache-status: HIT`, large `age`). The CDN does key on the query string, so keeping `?ver=` is enough. Diagnose by comparing the CSS the browser received with `file_get_contents` on the server.

## Backslashes vanish twice: wp_insert_post() content and the bridge script transport

1. `wp_insert_post()` / `wp_update_post()` **unslash** their input. Code stored as post content (WPCode snippets, custom
   CSS posts) loses every backslash unless you pass `wp_slash( $postarr )` - a regex like `'/^\s*AND\s*\(/'` became
   `'/^s*ANDs*(/'`, preg_replace() returned NULL and the admin search silently matched nothing.
2. The WP Site Doctor bridge strips backslash escapes from the script you send (`\'` breaks, `'\'` becomes an
   unterminated `'\'`). In rwpphp scripts avoid escapes: use chr(10)/chr(92), double vs single quotes, or a nowdoc
   (<<<'CODE') for code you write into the site.
To debug a filter that only misbehaves inside wp-admin, record what it sees in a global and print it in an
`admin_footer` HTML comment, then read the page source through a logged-in Playwright session.

## A plugin "class not found" fatal can be a single vanished file
GWM 2026-10-23: the whole site 500'd because ONE Elementor Pro file (conditions-manager.php) was gone. The exact error is in the
recovery-mode option `<hash>_paused_extensions` (readable via the bridge once the plugin is paused by renaming its folder over
FTP). Restore that one file from the newest UpdraftPlus plugins zip of the SAME version, then diff the whole plugin folder
against the zip listing (path + size) before re-enabling. Elementor Pro's Conditions_Manager::save_conditions() wants the
editor array format ([type,name,sub_name,sub_id]), not the stored 'include/general' strings.

## WP-Optimize minify keeps a stale copy of Elementor's page CSS
Verdanza 2026-10-24: new Elementor elements rendered unstyled (container default padding) although post-<id>.css on disk had
their rules - the page loaded wpo-minify-header-elementor-post-<id><ver>.min.css, a cached copy without them. Purge with
WP_Optimize_Minify_Cache_Functions::purge() and ::cache_increment(); wpo_cache_flush() only clears the page cache. Check in the
browser which stylesheet actually holds `.elementor-element-<new id>` before blaming the data.

## "Add New Application Password" shows an empty red box
createdequal.org 2026-10-24 (Sucuri firewall, WP Engine, Wordfence): the profile screen creates the password through the core
REST route /wp/v2/users/<id>/application-passwords. Sucuri blocks every /wp/v2/users route with a 403 HTML page, so the screen
gets no JSON error message and shows an empty notice. Test with `curl -s -o /dev/null -w "%{http_code}" <site>/wp-json/wp/v2/users`
- 403 text/html = firewall. Fix: bridge 1.4.0 connection key (Tools > Site Doctor Bridge), which does not use that route.

## A long-lived page cache serves pages pointing at deleted Elementor CSS
createdequal.org 2026-10-24 (WP Engine + Sucuri, X-Cacheable YES:15552000 = 180 days): cached HTML referenced
uploads/elementor/css/post-<id>.css?ver=<old>, which Elementor had since deleted and regenerated under a new ver -> 404 text/html,
"Refused to apply style", page unstyled. Shows only in the sweep as a console error, never in PHP. After anything that regenerates
Elementor CSS on a host with an edge cache, purge the page cache too, and re-sweep for "Refused to apply style".

## WP Rocket "Load JavaScript deferred" breaks third-party donation forms
createdequal.org 2026-10-24: minify_js + defer_all_js with empty exclusions deferred PayPal's donate-sdk.js (also re-hosted under
cache/min/) past inline Bloomerang code -> "PayPal is not defined", captcha missing, form fallback message shown. Always compare a
payment/donation page with ?nowprocket=1 before blaming the form vendor.

## Leftover Code Snippets from our own setup
A snippet given to the client to make an application password stays ACTIVE after it has done its job. Check the snippets list at
the end of setup; remove the snippet, its option and any credential it created.

## Elementor Icon Box puts the icon ON TOP on mobile unless position_mobile is set
Elementor 4.3 icon-box: `position` = inline-start only applies to desktop/tablet inheritance as you'd expect on desktop, but the
mobile default is block-start. Set position_tablet and position_mobile explicitly. Also: uploaded stroke SVG icons need
fill="none" on every shape (Elementor sets `fill` on the svg element), and an attachment can exist with its file missing -
check get_attached_file() is_file() after creating SVG attachments by script.

## Regenerating thumbnails: never delete "old variants" blindly - one can be the main file
Prolific Roofing 2026-10-24: before wp_generate_attachment_metadata() I unlinked every file in the old metadata's `sizes`.
For one PNG a size entry pointed at the MAIN file name, so the original was deleted and the footer logo 404'd. Skip any
size whose file equals basename(get_attached_file($id)), and check is_file() on the main file afterwards.

## Elementor responsive backgrounds ignore the stored URL - set `size`
background_image_tablet / _mobile = {url, id, size}: Elementor builds the CSS url from id + size, and size '' means FULL.
Storing the 768x512 URL with size '' still serves the full file to phones. Set size 'large' / 'medium_large'.
Check with a 390px browser which files are actually requested, not just the saved data.

## Elementor container `padding` is one object - setting top wipes the existing bottom
Setting $settings['padding'] = {top:90, bottom:0...} replaced GWM's original {top:30, bottom:90} and two sections collapsed
together. Read the existing padding first and change only the side you mean.

## Elementor 4 atomic elements: hide per breakpoint, interactions, and checking them
- Hide on mobile: add "display": {"$$type":"string","value":"none"} to the element's style variant with
  meta.breakpoint "mobile". Atomic elements have no `elementor-element-<id>` class - select them by [data-id].
- Scroll animations for atomic elements = element "interactions" (JSON string {version:1, items:[interaction-item...]}).
  Writing it directly works if postmeta `elementor-interactions-cache` is deleted (the front end rebuilds it). Elements stay
  at opacity 1 until the trigger fires, then fade - classic `animation` hides with visibility from the start instead.
  Measure opacity over time while scrolling; a static check proves nothing.

## Infomaniak (GWM preview host) removes some uploaded SVG files
An SVG written to uploads can be gone minutes later while its attachment remains (empty icon, 404 background). Prefer
PNG for decorative tiles; after adding SVG icons, re-check the files a while later.

### Retry loops around remote scripts must only retry when nothing ran
On a flaky host a loop like "run until the output contains X" re-ran an UpdraftPlus "backup now" script six times,
because the success text was not what the loop matched. Retry only on the bridge's own "route not found" /
"Could not reach" errors (the script never executed), never on "the output didn't look right". Pattern:
`scratch/bbl/r.sh`. Same rule for anything with side effects (backups, emails, orders, writes).

## Re-theming an Elementor site dark -> light: you can't just change the kit colours (2026-10-25, BBL)
One kit global is often used in opposite roles (e.g. "Surface" = section background AND the text on gold buttons), so
changing its value - or remapping the CSS variable - breaks one of the two. What worked: resolve every `__globals__` colour
reference to a concrete hex per element, then recolour by setting key (background/overlay -> light map, border ->
hairline, everything else = text -> dark map; dark text on gold buttons is simply not in the map), skip containers with a
background photo. Freeze header/footer/popups the same way (resolve, don't recolour) BEFORE changing the kit, and still add
scoped CSS restoring the old `--e-global-color-*` values + `color` for `.elementor-location-header/-footer`: they inherit
body colour and site-wide rules (`span.amount {color}`), which is how a header cart total went espresso-on-black.
Photo sections that keep global links change with the kit too - freeze them to the OLD values.
Verify with a contrast scan of every visible text against the composited background (gradients included), at 2 widths and in
interactive states (side cart, menus, accordions, cart with items). Eyeballing full-page screenshots misses most of it.
Script: scratch/bbl/light-site.php + light-check.mjs / light-interact.mjs.

## WP Engine: PHP can't write outside uploads, and Sucuri caches static files (2026-10-25, createdequal.org)
- On this WP Engine install, PHP gets "Permission denied" for unlink/write on mu-plugins/*, wp-content/*.php drop-ins,
  wp-config.php and plugin files - while is_writable() returns TRUE. Don't trust is_writable(); check the write result, and
  never delete a component file-by-file (a partial delete of a still-loaded mu-plugin left it half there - restore from your
  zip). Unhook instead (snippet with remove_filter) and hand file removals to SFTP / WP Engine support.
- Sucuri (X-Sucuri-Cache) caches static CSS/JS 24 h by URL. A fixed file under the same ?ver= stays stale: change the version
  (for Elementor local fonts: the 'version' in _elementor_local_google_fonts).
- Bridge script transport: a literal `\'` (two backslashes right before a quote) arrives mangled -> parse error. Use chr(92).

## PHP: `foreach ($a['k'] ?? [] as &$v)` edits a copy
The `??` expression yields a temporary, so by-reference edits inside the loop are silently dropped (the script still "works" and counts its hits). Guard with `if (empty(...)) continue;` and loop over the real array.

## Elementor atomic styles: validate before writing
The front end renders any style JSON, but an editor Save runs `Style_Parser::make(Style_Schema::get())->parse($style)` and silently drops the WHOLE style if one prop is invalid (e.g. font-family as `{"$$type":"string"}` - valid types are `font-family` / `global-font-variable`). Always parse every style you write with that parser in the apply script; refuse to save if invalid.

## WP Engine: delete_plugins() from PHP half-deletes the plugin (2026-10-27, createdequal.org)
- It returns without error but only the non-PHP files go (css/js/images); every .php stays, so the plugin is still listed
  (inactive, now broken if reactivated). Do the DB side from PHP, then hand `rm -r plugins/<slug>` to SFTP/SSH/WPE support -
  and say so in the report. Test first: create+unlink a `.php` and a `.txt` under plugins/ (txt ok, php denied = this lock).

## Elementor font-awesome.php:45-50 warnings are not broken icons when a Font Awesome Pro kit is set
- With the "inline font icons" experiment on, Elementor can't inline Pro icons (fal/far Pro names) and warns; the Pro kit's JS
  then renders them (`svg.svg-inline--fa`). Check `elementor_font_awesome_pro_kit_id` and the rendered page BEFORE swapping
  icons - swapping to free icons changes the design (it did on createdequal, rolled back).

## WP Engine SFTP drops long sessions (2026-10-27, createdequal.org)
- A recursive download of ~2,000 small files over WP Engine SFTP (paramiko) died with "Server connection dropped" after ~1,500
  files. Make transfers resumable (skip files already present with the same size) and reconnect on SSHException/EOFError.
- python -I hides user-site packages (paramiko installed with --user) - run own scripts without -I.

## wp-admin screenshots: autosave drafts and host firewalls (2026-10-28, blackbearlabs1.com)
- Filling a "new" WordPress screen (post-new.php, e.g. a coupon) without saving still lets autosave create a DRAFT. Close the
  page instead of navigating away, and query for drafts afterwards.
- Do not fill/click a WooCommerce date field before a screenshot: the jQuery UI date picker opens and covers the form.
- Shared hosts may firewall the IP after a few scripted logins - batch every admin screenshot into one login session.


---

# Part 2 - only in WP Site Build

## Elementor kit fonts only load on Elementor pages (Doctio / theme-rendered WooCommerce pages)

`kit.extra_fonts` works by adding a custom global typography entry, and Elementor
only prints kit fonts on pages it renders. On nexxuspeptide.eu the shop, product and
my-account pages are rendered by the theme (Doctio), whose own loader (Codestar
`csf-google-web-fonts`) loads Inter + Raleway only - yet its `main.css` styles every
WooCommerce button in Poppins 600. `fonts.mjs` kept reporting Poppins after the kit
had it. Fix: a tiny mu-plugin that enqueues the family unless `elementor-gf-<family>`
is already enqueued (`remote-files/nexxus/mu-plugins/nexxus-fonts.php`).

## Setting kit colours on a site whose kit was EMPTY restyles live pages

An empty kit means `--e-global-color-*` are undefined, so any widget that references
a global colour falls back to inherited text colour and looks "normal". Filling the
kit makes every such reference switch at once. On nexxuspeptide.eu the live Home used
`globals/colors?id=secondary` for all 39 product prices; setting secondary to the CTA
green turned every price green. Before applying a kit to a live site, count the
references per slot in the Elementor export (plain string search for `colors?id=` -
the JSON is double-escaped, regexes on `globals\/` miss it) and take a baseline sweep;
compare with `audit/shotdiff.mjs`.

## Turning off Elementor's default fonts changes widgets that set no font

With `elementor_disable_typography_schemes` unset, font-less widgets render in
Elementor's default Roboto; with it on they inherit the theme font. Line breaks move
and fixed-width rows can wrap (nexxus newsletter: Submit dropped under the email
field on phones). Same remedy: baseline sweep, diff, fix what moved.

## MetForm forms are built with Elementor's atomic containers

The field grid in a MetForm form is an `e-grid` container: its spacing is
`grid_gaps`, not `flex_gap`. Copied forms also carry the source's negative widget
margins and button colours; the page's own Custom CSS loses to the form's
`post-<formId>.css` at equal specificity. Change the copy's data (labels off via
`mf_input_label_status`, margins zeroed, button styles removed) before reaching for
`!important`.

## `rfile.ps1 get` reports a missing file as "route not found"

A 404 for a file that does not exist yet prints "HTTP 404 - route not found. Is the
WP Site Build Bridge plugin installed". The bridge is fine - the file is absent.

## `powershell -File scripts/*.ps1` from Git Bash is blocked by the execution policy

The PowerShell tool runs the scripts/ scripts fine, but the same command launched from a
bash loop (e.g. a background poller) fails with "running scripts is disabled on this
system" - exit 1, no bridge call made. A poller that only greps for success then loops
silently until its timeout. Always pass `-ExecutionPolicy Bypass`, and make the loop
bail out when the status command itself fails (check `$?` and that a known line such
as `history (` is present) instead of treating "no match" as "not finished yet".

## UpdraftPlus on max_execution_time 0: one wp-cron request can hold a backup hostage

editbyedita.com (LiteSpeed, `max_execution_time 0`): resumption 1 of a full backup never
ended - `lsphp:.../wp-cron.php` ran 44+ minutes at ~37 % CPU, touching
`*-plugins.zip.tmp` every few seconds while growing it by only KB. Every later resumption
logs "Terminate: ...zip.tmp exists with activity within the last 30 seconds" and backs off
with an ever longer interval, so the job never completes - and the stuck request slowed
page loads to 20+ s and coincided with an outage. `php/proc-check.php php` shows it
(PID, elapsed, %CPU) when exec is allowed. Diagnose with that before waiting on
resumptions; stopping it is the client's call on a live host.

## Windows PowerShell 5 `Get-Content -Raw` / `Set-Content` corrupts UTF-8 PHP
Reading a BOM-less UTF-8 file with `Get-Content -Raw` decodes it as ANSI (cp1252); writing it back
double-encodes every non-ASCII char ("categorieÃ«n", "â€”") and `-Encoding utf8` adds a BOM that PHP
prints before `<?php`. Edit with the Edit tool, or use `[IO.File]::ReadAllText/WriteAllText` with
`New-Object Text.UTF8Encoding $false`. Repair: `UTF8.GetString(GetEncoding(1252).GetBytes($s))`.

## WooCommerce: `.woocommerce::after` is a clearfix (display:table)
An absolutely positioned `::after` panel (top/bottom 0) on `.woocommerce` renders 0px tall because
the clearfix makes it `display:table`. Force `display:block !important; height:auto !important`.

## WooCommerce Cart block: never put borders/overflow on `.wc-block-cart__sidebar > *`
The sidebar IS the totals block; `overflow:hidden` on its submit wrapper collapsed "Proceed to
Checkout" to 0px. On mobile (.is-mobile) rows are a CSS grid with a ~58px total column; cell
padding there clips the price — scope desktop cell padding to `.wc-block-cart.is-large`.

## Nexxus: site custom CSS beats mu-plugin CSS on shop cards
The site's own custom CSS prints `.woocommerce-shop ul.products li.product { background/border … !important }`
AFTER mu-plugin inline styles, so equal-specificity `!important` rules lose. Prefix with `body` to win.
Find stray shapes with `node audit/borders.mjs <path> <container>` (includes ::before/::after, pointer-events:none)
and `node audit/at.mjs <path> x y` (element stack at a point; uses an instant scroll — smooth scrolling
otherwise leaves the point off-screen and returns nothing).

## Elementor containers: % widths + gap overflow on tablet
Two children at 48% + 52% with a 56px gap pushed 768px screens 23px sideways. Stack on tablet
(`flex_direction_tablet` column) or keep widths + gap under 100%.

## `display: contents` silently kills `overflow: hidden`
A hover zoom (`transform: scale()`) needs a clipping box. If a flattening rule anywhere - often one of our
own, written to unwrap a slider or a row wrapper - gives that box `display: contents`, `overflow: hidden`
computes but clips nothing and the zoomed image spills over the text below it. Check the computed `display`
of the wrapper (`audit/whichrule.mjs <url> <selector> display`), not just its `overflow`. Scope flattening
rules tightly (e.g. `> div:not([class])`) so they only hit the wrapper they were written for.

## Code Snippets plugin: markup that exists in no file
A string rendered on the page that `grep` cannot find in wp-content may live in the `wp_snippets` table
(Code Snippets plugin) or a similar plugin-owned table. Grep the non-core tables before concluding a theme
or plugin prints it (`php/nexxus-find-snippets.php`). Filter the same hook at a later priority rather than
editing the client's snippet - the snippet keeps working, and the change is visible in our own files.

## WooCommerce ships "coming soon" mode enabled on a fresh install
WooCommerce 9+ sets `woocommerce_coming_soon = yes` during activation. Every shop, category and product URL
renders "Great things are on the horizon" instead of the template you just built, while wp-admin looks
perfectly healthy. Turn it off as part of store setup:
`wp option update woocommerce_coming_soon no` (and `woocommerce_store_pages_only no`).

## Elementor: save() does nothing on a document created in the same request
`\Elementor\Plugin::$instance->documents->get( $id, false )->save( [ 'elements' => ... ] )` is the right call
for an EXISTING document. On a post created moments earlier in the same request the documents manager has no
type registered for it yet, so the save silently stores nothing - the template renders blank while its
conditions, type meta and taxonomy term all look correct. For new documents write the meta directly:
`update_post_meta( $id, '_elementor_data', wp_slash( wp_json_encode( $elements ) ) )`, plus
`_elementor_edit_mode = builder` and `_elementor_version`, then read it back before reporting success.

## remove_action fires too late if it runs inside the same hook
Removing `woocommerce_catalog_ordering` (on `woocommerce_before_shop_loop`, priority 30) from a callback on
that same hook at priority 100 does nothing - priority 30 has already run, and the control prints twice. Do
the removals in `template_redirect` (or any hook that runs earlier than the one you are editing).

## A wrapper div does not turn a Woo loop into a grid
`<div class="grid"><ul class="products">…` with `display:grid` on the div lays out the single `ul`, not the
`li`s inside it. Put the grid on `ul.products` itself and clear Woo's floats/clearfix pseudo-elements on
`li.product`.

## Elementor containers ignore `_css_classes` (2026-09-18, CAS)
Widgets store Advanced > CSS Classes as `_css_classes`; **containers store it as `css_classes`**. A generated
container with `_css_classes` saves fine, round-trips fine and renders with no class at all - every style
scoped to that class silently disappears. Check a built template with a DOM query for the class, not by
reading the JSON back.

## Floated elements ignore `margin: auto` (2026-09-18, CAS)
WooCommerce's `.col2-set` is `float:left` at >=768px; `margin:0 auto !important` computed to 0 and the
My Account cards sat left of centre. `audit/rules-at.mjs <url> <sel> 1440 margin-left,float` showed it.

## Git Bash rewrites "/path/" arguments (2026-09-18)
`node x.mjs /product-category/tools/` from Git Bash receives `C:/Program Files/Git/product-category/tools/`
-> the page 404s. Prefix `MSYS_NO_PATHCONV=1` for scripts that take site paths.

## Theme ajax add-to-cart doubles quantities (2026-09-18, CAS / Mixxcazt)
Mixxcazt posts `?wc-ajax=mixxcazt_add_to_cart` from a document-level click handler. With our own ajax add on
the same form both requests succeed intermittently (qty 2 -> cart +4). Handle the button click in the
capture phase on the form and stopPropagation. Count POSTs per click when testing add to cart.

## Script handles registered from Elementor widget files never enqueue (2026-09-18, CAS)
Widget class files are required inside `elementor/widgets/register`, which runs after `wp_enqueue_scripts`.
`wp_register_script()` placed in such a file is never called in time, so `get_script_depends()` and
`wp_enqueue_script()` in render() silently do nothing (Leaflet map stayed grey). Register assets from a file the
plugin loads up front.

## Mixxcazt ?layout=list replaces the product loop (2026-09-18, CAS)
`inc/woocommerce/class-woocommerce.php` swaps `content-product` for `content-product-list` when `?layout=list`
is present, bypassing a custom card template; old links keep it alive after hiding the toggle. Redirect it away.

## Elementor 4 editor "loading" check (2026-09-18)
`#elementor-loading` is not a reliable "ready" signal in Elementor 4 - wait for `#elementor-panel` to have width.

## Windows caps a command line at 32 KB - big JSON cannot be a script argument
`rwpphp.ps1 script.php spec_b64=<base64>` fails with "The filename or extension is too long" once the JSON is
~24 KB+. Put the file under wp-content with `rfile.ps1 put` (plain files are allowed even on WP Engine), pass its
name (`spec_file=name.json`), read it from WP_CONTENT_DIR, and delete it afterwards - it is publicly reachable.

## Openverse: long queries return nothing, and titles lie
Multi-word searches ("brake disc rotor car") often return 0 results; 1-2 words work. Every download needs a visual
review: "air filter" returned face masks, "jumper cables" network cables, "fuse" 18th-century engravings.

## Old build scripts can silently revert live data
A settings script written for an earlier phase (store address, catalogue tree) will happily put the old values back
when re-run for an unrelated reason (e.g. "purge caches"). When data changes, update or retire every script that
writes it, and grep build/ for the old values.

## PowerShell Set-Content adds a BOM and double-encodes UTF-8 (2026-09-19)
`(Get-Content f -Raw).Replace(...) | Set-Content -Encoding utf8 f` in Windows PowerShell 5.1 reads a BOM-less UTF-8
file as ANSI (so "−" becomes "âˆ’") and writes it back WITH a UTF-8 BOM. A BOM before `<?php` is output before
headers. Check: `head -c 3 f | od -An -tx1` (efbbbf). Edit PHP with python (encoding='utf-8') or the Edit tool.

## wp_insert_post with a "future" date silently schedules instead of publishing (2026-09-19)
A build script set `post_date` from a UTC clock; the site runs on Pacific time, so the newest posts were dated in the
future and WordPress saved them as `future` (scheduled) even though `post_status` was `publish`. Queries then found
nothing. Date posts from `current_time( 'timestamp' )` minus an offset, and set `post_date_gmt` with
`get_gmt_from_date()`.

## A grid rule beats the `hidden` attribute (2026-09-19)
`.pane { display: grid }` overrides the browser's `[hidden] { display: none }`, so tab panes toggled with `hidden`
all stay visible. Add `.pane[hidden] { display: none !important; }` wherever a pane class sets display.

## A link inside a product card's link silently rebuilds the card (2026-09-27)
WooCommerce wraps the whole loop card in `a.woocommerce-LoopProduct-link`. Adding a hover "Add to cart" `<a>`
inside it is a parse error: the HTML adoption-agency algorithm closes the outer anchor, clones it several times
and re-parents everything after the inner link, so the title, blurb and price end up *outside* the card link and
stop being clickable. The served HTML looks perfectly correct - only the parsed DOM shows it. Use `<button>` for
in-card actions (WooCommerce's AJAX handler works on a button and calls `preventDefault`, so the card link is not
followed; a button with no handler lets the click bubble to the card link). Check the parsed tree, not the source:
`document.querySelector('li.product')` walked in Playwright.

## remove_action from an mu-plugin's file scope runs too early for WooCommerce (2026-09-27)
mu-plugins load before regular plugins, so `remove_action( 'woocommerce_after_shop_loop_item',
'woocommerce_template_loop_add_to_cart', 10 )` at file scope removes a callback WooCommerce has not registered yet
and does nothing - the default button keeps rendering. Wrap it in `add_action( 'init', ... )`.

## A theme folder name can collide with a wordpress.org theme slug (2026-09-28)
Deploying a custom theme into `wp-content/themes/aura/` on a host that already had the wp.org theme
"Aura" installed overwrote that theme's files - and WordPress's theme auto-updater then reinstalled the
original **on top of ours**. The site kept rendering the other theme's footer with our `front-page.php`
"missing". Before choosing a theme folder name, check it is not a slug wordpress.org can claim; prefix
it with the client name (`myhouseaura`, not `aura`).

## WooCommerce ships with coming-soon mode ON (2026-09-28)
A fresh WooCommerce sets `woocommerce_coming_soon` and `woocommerce_store_pages_only` to `yes`. The
shop, every category archive and the cart render a near-empty page (112 characters) with no error
anywhere. `audit.mjs` catches it as THIN. Set both to `no`.

## Do not strip trailing digits from attachment file stems (2026-09-28)
A regex written to collapse WordPress's `-1`/`-2` duplicate-upload suffixes (`preg_replace('/-\d+$/')`)
also eats meaningful numbers: `hero-1 … hero-4` all collapsed onto `hero`, and 48 SKUs `AURA-001 …`
onto `AURA`, so one image was assigned and the rest silently dropped. Uploads with unique names need
no stripping at all.

## WP_Site_Icon's size filter REPLACES the size list - never aim it at an in-use image (2026-09-28)
To generate the `site_icon-32/180/192/270` sizes from a script you have to load
`wp-admin/includes/class-wp-site-icon.php` and add `WP_Site_Icon::additional_sizes()` to
`intermediate_image_sizes_advanced`, because those sizes only exist inside wp-admin. That callback does
not *add* the icon sizes - it **returns only them**. Running `wp_generate_attachment_metadata()` with it
attached rewrote the client's logo (an attachment the header uses) to have `sizes` of just
`site_icon-32, site_icon-64`, destroying its real sizes; the original file went missing in the same
window and the header image 404'd on the live site. A site icon gets **its own attachment** - upload a
separate copy, which is exactly what the wp-admin cropper does. Never point a regenerate at an image
the pages already render.

## Elementor stores its JSON with escaped slashes, so URL patterns silently match nothing (2026-09-28)
`_elementor_data` is JSON *inside* a meta value, so every URL in it is written
`https:\/\/site.com\/wp-content\/...`. A `preg_match` built from the plain URL returns **zero matches**
on a page that visibly renders that image - which reads as "the reference is somewhere else" and sends
you hunting. Build the pattern with an optional backslash before each separator (`'\\?/'` in a PHP
single-quoted string) and escape the replacement the same way, or the JSON stops parsing. Always
`json_decode()` before and after, and `wp_slash()` on the way into `update_post_meta`.

## A host security layer can eat or block individual uploads (2026-09-28, webelitelawncare)
Three 512x512 icons (twice PNG, once JPEG) each had their **original** removed from `uploads/` within
about two minutes, while the 150x150/300x300 thumbnails the server itself re-encoded were left in place
and every original from earlier the same day survived. Then the source logo began having its
**connection dropped** on every request - no status code at all - while its own 32x32 derivative and
every sibling image served 200, and PHP confirmed the file was on disk. No plugin explains it: no image
optimiser, no webp conversion, nothing on `wp_handle_upload`/`wp_generate_attachment_metadata`, and the
bridge's upload is a plain `wp_handle_sideload()`. The stack runs Softaculous SoftWP and JetBackup, both
of which scan. **Symptom to recognise:** `file_exists()` says yes, HTTP says no - that is the web server
refusing, not WordPress. **Workaround:** re-encode under a new filename; the new bytes serve normally.
Tell the client, because it is their host quarantining their media.

## rmedia.ps1 re-upload gets a -1 suffix even when the file is gone (2026-09-28)
WordPress 5.8+ `wp_unique_filename()` checks the **database** as well as the filesystem, so re-uploading
after a file has been deleted from disk still produces `name-1.jpg` - the attachment row is enough to
reserve the name. Do not read the `-1` as proof the original file is still there.

## A <br> hidden with display:none also removes the space around it (2026-09-28)
Giving a phone-only line break its own class and hiding it above a breakpoint
(`.lp-mbr{display:none}`) works for the break, but the element is removed from layout completely - so
the text nodes either side end up touching and desktop renders "Jersey Cityfor hair, skin". Put a real
space before each break (`...Jersey City <br class="lp-mbr">for hair...`); at the narrow width the
trailing space collapses at the end of the line, so nothing is lost either way.

## Counting rendered lines: use height, not Range.getClientRects() (2026-09-28)
`range.selectNodeContents(p)` then counting `getClientRects()` over-counts as soon as the paragraph
contains `<br>`: the breaks split the contents into separate text nodes and the API returns a rect per
node plus rects for the breaks themselves. A three-line paragraph with two `<br>` reported five. Divide
the element's height by its computed `line-height` instead.

## Elementor colours SVG icons with a CSS rule, which fills outline icons solid (2026-09-28)
Elementor's icon widget writes `{{WRAPPER}} .elementor-icon svg { fill: <colour> }`. An outline icon
whose `<svg>` carries `fill="none"` is filled in solid, because that rule targets the `<svg>` and the
shapes inherit from it. Put `fill="none"` on each `<path>`/`<rect>`/`<circle>` instead - a declaration
on the element itself beats an inherited value - and use `stroke="currentColor"`, which resolves against
the `color` Elementor sets on the same wrapper, so the icon colour control still works. Use plain
presentation attributes: Elementor's SVG sanitiser strips `<style>` blocks and may strip `style=`.

## Elementor's per-element rule beats a single class - and it uses the logical property (2026-09-28)
`.my-class{margin-bottom:8px}` on an Elementor widget does nothing. Elementor emits
`.elementor-NNN .elementor-element.elementor-element-NNN{...}` (specificity 0,3,0 against your 0,1,0)
and sets `margin-block-end`, not `margin-bottom`. The class lands, the rule is in the stylesheet, and
the computed value is still 0 - which reads as "the class did not apply". Use `!important` and set
both property names.

## An <img>-only image audit reports a page full of photos as fine (2026-09-28)
Elementor sets section and tile artwork as CSS `background-image`, so a probe that walks `<img>`
misses almost everything - on the Spa Blue homepage it found 3 images and passed, while two visibly
pixelated tiles went unmeasured. Walk every element's computed `backgroundImage`, pull the url, load it
to get its natural size, and compare against `rect.width * devicePixelRatio`. `audit/imgres.mjs` does
both. Retina is where this hides: a 768px file in a 768px slot is perfect at 1x and soft everywhere else.

## WordPress "medium_large" is 768px, which is half a retina tile (2026-09-28)
`wp_get_attachment_image_url( $id, 'medium_large' )` is a tempting default for background art, but at
768px it is half what a 730px-wide tile needs on a 2x screen. For anything displayed larger than about
380px CSS, ask for `full` or register a size that matches the slot.

## The Elementor kit styles bare `button`, and beats your class (2026-09-28)
The kit emits `.elementor-kit-N button, … { border-radius: 0 }` - specificity 0,2,0. A rule written as
`.my-arrow { border-radius: 50% }` is 0,1,0 and loses, so circular buttons render as squares while
*other* round buttons on the same page look fine (a selector like `.my-dots button` ties on
specificity and wins on order). Put `!important` on every property the kit touches - radius, padding,
border, background, colour - not just the ones you noticed.

## "Hidden" on a parent leaves the child's computed display alone (2026-09-28)
Checking `el.hidden` or `getComputedStyle(el).display !== 'none'` to decide whether something is on
screen fails when the *wrapper* carries `[hidden]`: the child's own display is still `grid`, only its
box collapses. A check reported two arrows as visible inside a hidden control row. Measure the box -
`rect.width > 0 && rect.height > 0`. For the same reason, an overlap test must intersect both axes;
comparing only horizontal extents flags a row sitting below the cards as overlapping them.

## Elementor carousels: the control is `slides_per_view`, not `slides_to_show` (2026-09-28)
Setting `slides_to_show` on `testimonial-carousel` does nothing and reports no error - the carousel
just stays at one slide per view, which reads as "my change did not save". The live control names are
`slides_per_view`, `slides_per_view_tablet`, `slides_per_view_mobile`, `slides_to_scroll` and `loop`.
Ask the widget rather than guessing:
`\Elementor\Plugin::$instance->widgets_manager->get_widget_types( 'testimonial-carousel' )->get_controls()`.

## Elementor swiper arrows need !important on every positioning property (2026-09-28)
Elementor pins `.elementor-swiper-button` at `top:50%; transform:translateY(-50%)` with a selector that
ties your own on specificity, so source order decides and it is not reliably yours. The symptom is
partial: `width`/`height` applied and the thing resized, while `top`/`left`/`right` silently did not
and it stayed where Elementor put it. Put `!important` on top, bottom, left, right and transform.
Also: Swiper adds `swiper-button-lock` when the whole set already fits - hide those, or you ship two
permanently dead buttons.

## An Elementor arrow icon does not follow `currentColor` (2026-09-28)
The chevron inside `.elementor-swiper-button` is an SVG whose `fill` comes from the widget's
`arrows_color` control. Styling only the button's `color` on hover gives a black circle with a black
arrow inside it - a solid disc. Set `svg { fill }` (and `i { color }` for the font-icon skin)
explicitly for both the resting and hover states.

## :hover cannot be triggered from JavaScript (2026-09-28)
`el.dispatchEvent(new MouseEvent('mouseover'))` does not make `:hover` match, so a check written that
way reads the resting styles and passes a broken hover state. Use the driver's real hover
(`await locator.hover()`), and pick an element that is actually hoverable - a disabled control with
`pointer-events:none` never matches `:hover`, and the probe silently measures whatever is underneath.

## `place-items: center` does nothing horizontally in flexbox (2026-09-28)
`place-items` is shorthand for `align-items` + `justify-items`, and **`justify-items` has no effect on
flex containers**. Write `display:grid;place-items:center` on an element something else forces to
`display:flex`, and you get vertical centring only - the content packs to the left and looks subtly
wrong rather than obviously broken. An Elementor swiper arrow's chevron sat 10.5px left of centre this
way. Use `justify-content:center` explicitly, and remember the forced `display` wins.

## A full-width pagination strip swallows the clicks meant for carousel arrows (2026-09-28)
`.swiper-pagination` is positioned `left:0;right:0`. Move the arrows onto the same line as the dots and
the strip now lies across the arrow circles, intercepting the pointer exactly at their centres - the
natural click target - while the arrows still look and hover fine. Playwright reports it as
"…swiper-pagination… intercepts pointer events". Fix with `pointer-events:none` on the strip and
`pointer-events:auto` on the bullets, and assert that an arrow click actually advances the track.

## sprintf format strings: never mix `%s` with `%1$d`

PHP's sprintf treats sequential and positional specifiers independently. This:

```php
sprintf( '<svg class="i--%s" width="%1$d" height="%1$d">%s</svg>', $name, $size, $path );
```

gives `width="0" height="0"` and prints `$size` as the element's text content — `%1$d` is argument
ONE (the name string, cast to int = 0), while the two `%s` take arguments one and two in order. On
My House Aura this made **every icon on the site** a zero-sized box: no star ratings on any product
card, no chevrons anywhere. Nothing looked broken; the icons were just absent, and it survived
several rounds of visual review. If one specifier is positional, make them all positional.

## A theme's `button` rules will beat yours

mixxcazt sets `min-width: 100px` on every `button` and `button::after { display: none }`. Effects
seen on one page: a drawer title truncated to "Kitchen & D..." because the 40px close button was
really 100px, a 32px circular icon button rendered as a 100x32 ellipse, and every "goes deeper"
chevron silently missing. `width` alone does not win against `min-width` — set `min-width` and
`max-width` as well, and raise specificity for the `::after`.

## Term names are stored kses-normalised — decode on output, never "repair" the database

`wp_update_term()` runs the name through `wp_kses_normalize_entities()`, which turns a bare `&` back
into `&amp;`. So "Kitchen & Dining" is genuinely stored as "Kitchen &amp; Dining" and a script that
"repairs" it reports success and changes nothing, every time. Decode when printing
(`html_entity_decode( $name, ENT_QUOTES, 'UTF-8' )`), and put that behind one helper so no output
path misses it.

## `scripts/rfile.ps1 put` does not purge LiteSpeed

Deploying an mu-plugin or a stylesheet leaves the page cache serving the old HTML. A verified fix can
appear not to work through two full check runs while the PHP is live and opcache is clear. Purge after
any deploy that changes front-end output — `do_action( 'litespeed_purge_all' )` plus
`LiteSpeed\Purge::purge_all()`. The `build/*.php` scripts do this at the end; `rfile.ps1` does not.

## Assertions that are too weak pass while the feature is broken

A mega-menu check that hovered the first department and asserted "3 or more links" passed while
eleven of thirteen panels were rows of bare headings. A price-sort check asserted ascending order over
a two-product filtered set, which can never demonstrate an ordering, and its price extractor
concatenated a struck-through price with a sale price into `39.4256`. Assert the thing that would
actually be wrong: per-column counts, not "some links"; and check ordering on a full page.

## Sweeping a hook removes your own callbacks too

The pattern "remove every string callback from this hook, keep the closures" works only while your
own renderer is a closure. On My House Aura's product page the replacements were named functions
registered at file scope, so the `init` sweep removed the theme's summary *and* ours — brand, rating,
price, swatches, add-ons and delivery block all vanished, while every section below the summary still
rendered, which made it look like a CSS problem. Register replacements inside the sweep callback,
after the removals, not at file scope.

## Check a term's slug, never assume it

"Sales & Deals" is stored as `sales-deals`, not `sales-and-deals` — WordPress drops the ampersand
rather than expanding it, even though "Kitchen & Dining" became `kitchen-and-dining` because its
source string used the word "and". Two build scripts assumed the wrong one. Nothing errored: the
"skip these departments" list simply never matched, so 40 demo products were generated onto deal
shelves and a later script named them after those shelves ("Minimalist Metal Under $100"). One
`get_term_by` call would have shown it.

## An idempotency key that is too loose rewrites the wrong rows

`^AURA-` plus "ends in digits" was meant to select generated SKUs (`AURA-COOKWARE-1`). It also matched
the hand-written `AURA-018`, so a bulk rename overwrote the 48 real products — the only ones with real
photography and real names. Make the key match the generated form exactly
(`^AURA-[A-Z0-9]+-\d+$`), and prefer a key that cannot collide with hand-authored data at all.

## Playwright's check() cannot tick a visually hidden checkbox

A custom checkbox is usually a hidden `<input>` plus a styled `<span>`, with a `<label>` wrapping
both. `page.check()` times out on "element is not visible", and `{force: true}` tests something no
visitor does. Click the label — that is the real interaction, and it proves the label is wired up.

## Capture the reference before rebuilding against it

"Match the reference exactly" is not answerable from memory. Screenshot the real site and measure it:
`scratch-nexxus/bbb-reference.mjs` records header geometry, band order, footer columns and link text
into JSON, and `bbb-slices.mjs` slices the page so each band can be looked at. That turned "the header
is different" into a list — six utility items at measured positions, a shipping bar, a 13-item nav —
and turned "the mega menu design is different" into "it is 975px wide, anchored to the department's
edge, on a cream ground, with a promo column", none of which was guessable.

Two things to expect: an email-capture modal covers the hero (dismiss it, then re-scroll), and product
pages may be bot-blocked by Akamai even when the home page loads. Say which parts you could not
capture rather than inventing them.

## A flex container drops whitespace-only text nodes

`<a style="display:flex">Find your store <span>&rarr;</span></a>` renders as "Find your store→". The
space between the text and the span is a whitespace-only text node, and those are not laid out as flex
items. Use `gap` on the container; adding `&nbsp;` works but hides the real cause.

## WooCommerce's block cart is not the classic cart

A cart page containing `<!-- wp:woocommerce/cart -->` renders React components —
`.wc-block-cart-items__row`, `.wc-block-components-totals-item` — hydrated asynchronously, with an
`.is-loading` class until ready. `.cart_item` and `.woocommerce-cart-form` never appear. A check
written for the classic markup can silently match a mini-cart widget in the header instead and report
plausible numbers from the wrong element; it only fails when that widget is removed. Wait for
`.wc-block-cart-items__row` and assert against the page you meant.

## Measure at the width the client reviews at

A parity pass done at 1440 missed a white-vs-cream header and a container 240px too narrow, because
neither is obvious until there is room to spare. The client's screenshots were 1920. Capture the
reference and the build at the same viewport, and compare numbers, not impressions.

## Find the element that sets the width by printing the chain

Three attempts to widen a page targeted `.container`, `.content-area` and `.site-main`. None of them
sets the width — mixxcazt caps content at `div.col-full { max-width: 1320px }`. Walking from the
target element up to `<html>` and printing each ancestor's width, `max-width`, padding and margin
finds it in one run and shows which single place to change. Guessing at plausible selector names does
not.

## offsetWidth on a display:none element is 0

Positioning logic that measures a hidden panel gets zero and computes a zero offset, which looks like
"the code ran and decided nothing was needed". If the size is fixed by the stylesheet, compute it
(`Math.min(975, clientWidth - 48)`) instead of measuring; otherwise measure on the event that reveals
it.

## Clamp, do not flip

A dropdown near the right edge is usually fixed by shifting it left by the overflow amount. Flipping
it to `right: 0` instead moves it by however far the trigger happens to be from the right edge — for
a mid-row item that was 880px, putting the panel nowhere near the menu that opened it.

## Never nest a form inside WooCommerce's cart form

`<form class="woocommerce-cart-form">` wraps every cart line. A `<form>` inside it is invalid HTML:
the parser **drops the inner start tag**, and the inner `</form>` then closes the outer cart form
early. On My House Aura that meant the first per-item control silently lost its form and did nothing,
while everything after that point — Frequently Bought Together, Save for later — submitted the wrong
form. Three broken features, one cause, no error in any log.

Use a nonced GET link instead, which is what WooCommerce's own "remove item" control is. Assert it:
`document.querySelector('form.woocommerce-cart-form').querySelectorAll('form').length === 0`.

## A theme can delete core WooCommerce handlers

mixxcazt removes `WC_Form_Handler::add_to_cart_action` from `wp_loaded` so its AJAX add-to-cart cannot
double-add — which kills every plain `?add-to-cart=ID` URL on the site. Nothing errors; the link just
does nothing.

When a WooCommerce interface that has worked for a decade appears not to, check the hook is still
registered before suspecting your own code:
`has_action('wp_loaded', array('WC_Form_Handler','add_to_cart_action'))`. Then grep wp-content for the
handler name to find what removed it, and restore it from an mu-plugin rather than editing the theme.

## Never test only with a cache-buster

Every check in this toolkit appended `?nc=<timestamp>`, which bypasses the page cache. That hid a
LiteSpeed-cached page serving a 404 combined stylesheet — an unstyled site for every real visitor,
for days, while the checks passed. Test the plain URL at least once per session, and compare it with
the cache-busted one:

```
plain  litespeed=hit   stylesheets=1   bytes=192203
fresh  litespeed=none  stylesheets=41  bytes=246737
```

## LiteSpeed's page cache is not in wp-content

`LiteSpeed\Purge::purge_all()` called from a REST request does not reach it: the cache lives in the
web server and is evicted by an `X-LiteSpeed-Purge` header on a response the server actually sees.
Deleting `wp-content/litespeed/*` does not evict it either. Expose a front-end URL that emits the
header and hit that instead.

Do not leave CSS Combine on while a site's stylesheets change daily: the combined file is regenerated
under a new name on every deploy, while already-cached HTML keeps pointing at the old one.

## Ask Chrome which rules match, do not walk the stylesheets

Two hand-rolled passes over `document.styleSheets` reported "no rule sets this property" while the
computed value was plainly set. CDP's `CSS.getMatchedStylesForNode` — what the DevTools Styles pane
uses — named the winner immediately: an Elementor element-scoped rule five classes deep. See
`scratch-nexxus/aura-matched.mjs`.

## Check an Elementor control's TYPE before writing its value

`border_radius` on the Search Form widget is a `slider` (`{unit, size}`). Writing the dimensions shape
`{top,right,bottom,left}` is silently ignored and the control falls back to its default — which then
beats any stylesheet, because Elementor's generated selector is far more specific than anything
reasonable you will write. Dump `$widget->get_controls()` and read `type` first.

## Measure responsive layout across widths, not at one

A header that is clean at 1920 had 49px of overlap at 1280, because a flex child was being squeezed
below its content width and overflowed backwards. One screenshot at one width proves nothing about a
fluid row.

## A line you can see but cannot find in the DOM — sample the pixels

A 1px separator on the reference's footer belonged to no element: neither the row above nor the block
below had a border, and a sweep for short wide elements found only an unrelated rule further down.
Screenshot a narrow vertical slice through the boundary and walk the pixel rows looking for one whose
averaged colour differs from its neighbours. That named it immediately — `rgb(98,102,105)`, one row
tall, at the row's bottom edge.

## Outline icon sets do not pass for brand marks

Facebook, Instagram, X, Pinterest, YouTube, Apple and Android are drawn as solid shapes everywhere
they appear. Rendering them with a general-purpose outline stroke set makes them visibly lighter and
thinner than every other logo a visitor has seen that day, which reads as "wrong icons" even when the
shapes are right. Keep a filled variant and a predicate saying which names use it — check the
reference's computed `fill` and `stroke` on the path rather than assuming.

## Cream is not white

A footer using a warm off-white for text looked, against a dark brown ground, as though two adjacent
links were different colours. They were identical — the tint was the cream. Measure the reference's
actual value (`rgb(255,255,255)` here) instead of picking a near-neighbour from the palette.

## Generated boxes are grid items

A clearfix `::before`/`::after` on a container you turn into `display: grid` becomes a **grid item**.
On My House Aura's checkout the theme's clearfix took the first cell, pushing the form into column 2
and the rail onto a second row — with `grid-column: auto` on both real children and no placement rule
anywhere to blame. `getComputedStyle(el, '::before')` shows it: `content: "" display: table`.

Remove it with enough specificity to beat the theme (`form.checkout.aura-checkout::before { content:
none !important }`) — a single-class rule loses.

## WooCommerce only refreshes the fragment it owns

The checkout's order summary must be rendered from `checkout/review-order.php`, because the AJAX that
runs on every address, shipping or fee change replaces the element carrying
`woocommerce-checkout-review-order-table` and nothing else. A summary hand-rolled into the page
template is written once and then lies: ticking a fee charged the extra while the displayed total
kept the old figure.

Likewise `woocommerce_checkout_order_review` renders the payment box as well as the review — calling
it alongside `woocommerce_checkout_payment()` yields two of every gateway field under the same names.

## A check that asserts a placeholder exists will fail when you remove it

Two checks asserted that "note for the client" boxes were present, as a guard that the build was
honest about its gaps. When the gaps moved into a handover document the checks failed on work that
was correct. Assertions about scaffolding need inverting, not deleting — the useful check afterwards
is that the scaffolding has not crept back.

## Elementor does not render CSS Classes on containers

`_css_classes` is a widget control. Writing it onto a **container** stores it — it reads back from
`_elementor_data` and shows in the editor's Advanced tab — and it never reaches the markup. A build
script that adds semantic classes to three header columns looked like it had silently done nothing.

Either use the `elementor-element-<id>` class Elementor does print, and make the build script refuse
to run when that id has gone (so the selector cannot rot unnoticed), or style through a wrapper you
own. `build/aura-headrow.php` and the header block of `aura-css/tokens.css` do both: each rule names
the semantic class *and* the element id, so it keeps working if a later Elementor renders the first.

## Elementor caches the rendered HTML, not just the CSS

`Plugin::$instance->files_manager->clear_cache()` clears the generated stylesheets. It does not clear
`_elementor_element_cache`, a post meta holding the element's rendered markup with a 24-hour timeout.
Settings written to `_elementor_data` were in the meta and absent from every page for that reason.
Delete the meta as well after writing a template:

    delete_post_meta( $template_id, '_elementor_element_cache' );

## An Elementor container's align-items is its HORIZONTAL axis

Containers default to `flex-direction: column`. A blanket
`.elementor-location-header .e-con-full { align-items: center }` — added to put the logo, search and
utilities on one centre line — centred the **logo inside its own column** instead, pushing it 78px in
from the row's left edge. Vertical centring belongs on the row, which is the one container with
`flex-direction: row`; Elementor's own `flex_align_items` control sets it.

## A wrapping flex row breaks on flex-basis, before it shrinks

The header's search column had `flex: 1 1 auto`. At 1920 it filled the gap correctly; at 768 the row
wrapped and the utility cluster dropped onto a second line, left-aligned. A wrapping container places
items using their hypothetical main size — `auto` means the search form's content width — and only
shrinks what is already on the line. `flex: 1 1 0` with `min-width: 0` takes exactly what is left
over and never causes the break.

## wp_footer priority 20 is when scripts print

`wp_print_footer_scripts` is on `wp_footer` at priority 20, registered by `default-filters.php`
before any mu-plugin loads. Markup added at the same priority therefore renders **after** the inline
scripts that look for it: the offer tab drew perfectly and did nothing when clicked, because its
driver had already run against a document without it and returned at the null check. Print footer
markup at a lower priority — 5 is clear of everything.

## A stray `*/` turns the next rules into a comment's selector

A scripted edit left a comment closed twice, so the prose between the two `*/` parsed as a selector
and swallowed the declarations after it. The visible symptom was a search field stuck at the wrong
height with **no rule declaring it** — CDP's matched-styles agreed there was none, because there
genuinely was none. After any scripted CSS edit, check braces and comment nesting before deploying;
`node -e` over the file catches it in a second.

## Not every difference is in the DOM

A probe for dashed borders reported zero on the reference's entire home page, which nearly justified
deleting the coupon tickets from ours. The reference draws that artwork as a **background image** —
no rule mentions it, and no DOM query can find it. The screenshot showed it immediately. When a probe
says a visible thing is not there, the probe is wrong: look at the picture.

## The arrows were right and invisible

Every assertion about the hero's arrows passed - 70x70, white, 50% radius, 15px from each edge,
opacity 0 at rest and .4 on hover, all matching the reference to the pixel - and a visitor could not
see them. They are white discs at 40% opacity, and every slide was a pale photograph that ran to
near-white at both edges. White on white.

The reference's arrows read because its banners are saturated corner to corner: they are single
full-bleed 1920x530 images with the colour panel, the headline and the button baked in. Nothing about
the arrow was wrong; the thing behind it was.

Two lessons. Sample what is BEHIND a control, not just the control - and when the probe samples the
same point the control occupies, it reads the control's own colour and reports everything as fine.
And an element's `opacity` fades its contents with it: putting the translucency in
`background: rgba(...)` instead keeps the chevron readable whatever it lands on.

## Dequeue the handle that is actually loading

98 KB of Roboto was being requested on every page. The theme had a `mixxcazt-fonts` handle building a
Google Fonts URL, so that was dequeued - and nothing changed, because the request came from
ELEMENTOR: `elementor-gf-roboto` and `elementor-gf-robotoslab`, its default kit's faces for any
typography slot with no face set. It was also asking for Jost in all eighteen weights under
`elementor-gf-jost`, duplicating the four-weight request the site makes for itself.

Read the handle off the rendered HTML - WordPress prints it as the link's `id`:

    curl -s https://site/ | grep -oE "<link[^>]*fonts\.googleapis[^>]*>"

## A dequeue can be too early, never too late

`tooltipster` survived `wp_enqueue_scripts` at 99, `wp_print_styles` at 0, `wp_print_scripts` at 0 and
`wp_print_footer_scripts` at 0, because the theme enqueues it while a template renders - after every
one of those has finished. The last point at which an asset can be removed is the filter that writes
its tag:

    add_filter( 'script_loader_tag', fn( $tag, $handle ) => 'tooltipster' === $handle ? '' : $tag, 10, 2 );

## WPSB_CONFIG is not set for you

`node audit/audit.mjs` with no `WPSB_CONFIG` falls back to the example configuration and audits
`clientsite.com`. It does not warn; it reports failures for a site that has nothing to do with this
one, and two runs were spent on connection timeouts against a domain that does not resolve. The
tools under `scratch-nexxus/` read `config.myhouseaura.json` directly and are not affected, which is
what made the difference hard to spot.

## The theme hides every button's ::after

Mixxcazt carries a blanket

    button::after, input[type="button"]::after, input[type="reset"]::after, … { display: none }

The hero's arrows draw their chevron from borders on `::after`. The content, the border colours and
the 45-degree rotation were all applying correctly - CDP confirmed all three of our rules matched and
won - to a box that was never drawn. The result was two empty circles, and every assertion about the
arrows passed, because they were all about the button and none about the mark inside it.

Anything drawn with `::before`/`::after` inside a `button` on this site has to state `display`
explicitly. `getComputedStyle(el, '::after').display` is the one-line check.

## A flex item is not a superscript

`.aura-hero__off` is a flex row holding "Up to", the figure, and a `<sup>` for the asterisk. Being a
flex item, the `sup` is blockified: `vertical-align: super` stops meaning anything, the container's
`gap` pushes it clear of the figure, and `align-items: center` puts it halfway down an 84px number.
It read as a stray mark floating beside the price.

Put the spacing on the other children (`gap: 0` plus a margin on the label) and raise it with
`align-self: flex-start` and a small `margin-top` - the properties that do work on a flex item.

## Clearing a control that only appears on hover

The previous-slide arrow is a 70px circle 15px from the edge, so it ends at x=85 and sat on top of
the hero's subheading - but only while the hero was hovered, which is why it survived every
screenshot taken at rest. The reference starts its panel copy at about 100px for exactly this reason.
The clearance belongs only where the control exists: the arrows are hidden below 900px, and a 100px
gutter on a 36% panel at tablet width crowds the copy for nothing.

## "Borrow the first product image" turns into a lucky dip

Two bands took their picture from the first product photograph in a category: the home page's Featured
Brands tiles, and the mega menu's promo column. That looked deliberate while the catalogue had no
photography, because both fell through to a chosen image instead. The moment products started getting
photographs, both swapped their room scenes for whatever product happened to come first - a single
wine glass on white standing in for the brand "Aura Bloom", and a fire pit letterboxed from a square
shot into a 232x150 promo slot, losing its legs and its rim.

Where a chosen picture exists it has to WIN, with the product photograph as the fallback, not the
other way round. Both now read from a named art slot (`brand-<slug>`, `mega-<slug>`) first.

It is worth grepping for `get_image_id()` after any change that adds product photography: anything
borrowing an arbitrary product image is a latent version of this.

## Clear the cache AFTER the code, not before

The mega panels cache their HTML in `aura_mega_promo_<term_id>` for an hour. Clearing those transients
and then uploading the new PHP fixed nothing: a page view in the gap between the two rebuilt the cache
from the old code, and the check reported the old images as if the edit had never applied. Deploy
first, clear second - or clear twice.

## A smaller `sizes` makes the browser pick a smaller image

Trinity's card was still soft on a phone: the browser chose the 390-wide srcset candidate for a slot
that needs 506 real pixels, because WordPress writes `sizes="100vw"`. Stating the real slot width
(`sizes="(max-width: 767px) 290px, 300px"`) made it **worse** — x0.45 against x0.77 — because `sizes`
tells the browser how many CSS pixels the image occupies, and a smaller figure means a smaller
candidate satisfies it. To force a larger file you have to state a larger `sizes`, or register an
image size that matches the slot. Measured, reverted.

## The overflow probe must measure what the audit measures

`audit.mjs` reported +36px of sideways scroll that three hand-written probes could not reproduce. They
compared `scrollWidth` against the viewport width passed to Playwright; the audit compares it against
`document.documentElement.clientWidth`, which excludes the scrollbar. Matching the formula still did
not reproduce it — the remaining difference was the context: the audit builds one with
`newContext({ isMobile, hasTouch, ignoreHTTPSErrors })` and navigates, and replicating that exactly
reproduced +36px on the first try and named the element.

Two lessons. Copy the failing check's own setup before doubting it — `lib.mjs` exports `open()` and
`wake()` for exactly this. And a probe that "proves" a reported fault does not exist is the probe to
distrust first.

## A stylesheet-presence check that matches the framework's own rules

To confirm a rule had shipped, a probe searched every stylesheet for the element id `1291d88`. It
reported `true` while the rule was not deployed at all — Elementor emits its own rules for that same
element id, so the string was always present. Search for something only your rule contains.

## A `cat >>` inside a command that gets refused never runs

An append-then-deploy command was rejected by the sandbox classifier. The rejection read like a
transient failure, and re-running only the deploy half "succeeded" — so the plugin was redeployed
unchanged and the fix appeared not to work. After any refused compound command, check the file
actually changed (`grep -c` for the new text) before re-running the half that reported success.

## A meta box's inline script runs before the meta box

A `<script>` printed at the top of an `add_meta_box` callback executes the moment the parser reaches it
— which is **before** the rest of the callback's own markup exists. `document.getElementById()` on
anything further down the box returns `null`, the handler binds to nothing, and the feature fails
silently with no console error. "Add row" did nothing on Trinity's Lab Reports box for exactly this
reason, while every other assertion about that box passed.

Either print the script last, or guard it:

```js
if ( 'loading' === document.readyState ) { document.addEventListener( 'DOMContentLoaded', init ); }
else { init(); }
```

Same trap, different shape, as "clear the cache AFTER the code, not before": the order things run in is
not the order you wrote them.

## `??` only catches null, so `''` falls through

`$t['spec'] ?? '—'` prints the em-dash for a missing key or a `null`, and the **empty string** for `''`.
That matters the moment two writers disagree: Trinity's seeded COA rows stored `"spec":null`, the new
admin form writes `""`, and a client pressing Update without changing anything would have turned a
column of dashes into blank cells. Nothing in the form was wrong — the reader was.

When a value can be absent in more than one way, test the value, not its presence:

```php
$spec = isset( $t['spec'] ) ? trim( (string) $t['spec'] ) : '';
echo esc_html( '' !== $spec ? $spec : '—' );
```

Found it by md5-ing the stored meta either side of a no-op save (`php/trinity-coa-snapshot.php`) and
chasing the one hash that moved. A diff of rendered text would have shown nothing on that report,
because the report that broke was a different one.

## `sanitize_text_field()` eats a bare `<`

It calls `strip_tags()`, and PHP's `strip_tags()` discards everything from an unclosed `<` to the end of
the string. So the lab notation `< 0.5%` sanitises to the **empty string**, silently, on save. Any field
that legitimately holds a comparison operator — specifications, tolerances, ranges, measurements — needs
a sanitiser that removes real markup only:

```php
$v = preg_replace( '#</?[a-zA-Z][^<>]*>#', '', $v );   // tags, not stray operators
```

Safe to store as text as long as every reader escapes with `esc_html()` at the point of output — which
is the rule anyway.

## A staged `.php` inside mu-plugins is loaded immediately, and that is a fatal

**This one took the site down.** The deploy routine was: write the new file to
`wp-content/mu-plugins/<name>.staged.php`, then have a promote script swap it over the live file after
checking it. The staged copy never got as far as being promoted, because WordPress loads **every**
`.php` in `mu-plugins/` — there is no activation step and no naming convention it respects. The moment
the staged file landed, every class and function in it was declared a second time, PHP fatalled, and
the whole site returned 500.

It is worse than an ordinary fatal: the bridge plugin is part of that same site, so the promote script
could not run, could not check anything, and could not roll itself back. The only way in was SFTP.

The recovery is to delete the staged file; nothing else is wrong.

```bash
python tools/hosting/sftp.py rm wp-content/mu-plugins/<name>.staged.php apply
```

A staging copy must live somewhere nothing auto-loads. `scripts/spa-deploy-mu.ps1` now parse-checks by
writing to `wp-content/upgrade/` — WordPress's own scratch directory, which already exists (the bridge
refuses a path whose parent does not) and is never scanned — and then writes straight over the live
file via SFTP, with a verified backup and an HTTP check that restores the backup if the page does not
come back healthy.

Note that a `.bak` or `.old` suffix *after* `.php` is safe: `wp_get_mu_plugins()` globs `*.php`, so
`spa-service-widgets.php.wpsb-20261003-001104.bak` is inert. Only a name **ending** in `.php` is loaded.

## `wp_kses_post()` silently deletes inline SVG

`<svg>` and `<path>` are not in its allowlist, so `wp_kses_post( '<span class="disc"><svg>…</svg></span>' )`
returns the span with nothing inside it. Nothing errors and nothing is logged.

This is invisible until you look: the site had 26 arrow discs rendering as empty 40px circles. It only
appeared when the arrows were changed from the character `&rarr;` — which sailed through kses — to a
drawn SVG. A probe caught it by reporting `no-svg` where it expected a stroke width.

Filter with an allowlist that includes the shapes:

```php
$allowed = wp_kses_allowed_html( 'post' );
$allowed['svg']  = array( 'viewbox' => true, 'width' => true, 'height' => true, 'fill' => true,
                          'stroke' => true, 'stroke-width' => true, 'stroke-linecap' => true,
                          'stroke-linejoin' => true, 'class' => true, 'aria-hidden' => true );
$allowed['path'] = array( 'd' => true, 'fill' => true, 'stroke' => true, 'stroke-width' => true );
echo wp_kses( $html, $allowed );
```

Attribute names must be **lowercase** in the allowlist — kses lowercases before comparing, so `viewBox`
as a key never matches.

## Three ways Elementor's own CSS quietly wins a tie

All three cost a deploy each on this site. The pattern is always the same: a rule that looks like it
should apply has the *same* specificity as one of Elementor's, and Elementor's stylesheet loads later.

1. **`.elementor img { height:auto; border-radius:0 }`** — beats `.spa-cat__img img` (both 0,1,1). Card
   images came out letterboxed at 126×84 with square corners instead of 126×126 rounded. Fix:
   `.spa-cats .spa-cat__img img` (0,2,1).

2. **`.elementor-element:where(.e-con-full,.elementor-widget){ align-self:var(--align-self) }`** —
   `:where()` contributes **zero** specificity, so that selector is only (0,1,0), a tie with
   `.elementor-widget-<name>`. A widget in a `flex-direction:column; align-items:center` container then
   shrink-wraps: a one-column grid collapsed to 578px inside a 1280px band. Fix: `.e-con .elementor-widget-<name>`
   (0,2,0), and set `--align-self` as well so Elementor's own rule agrees rather than competes.

3. **The theme's `button`** — `.elementor button` (0,1,1) beats `.spa-caro__btn` (0,1,0), so slider
   arrows that were `display:none` on desktop rendered as pink-bordered boxes under the grid. Fix:
   `.spa-caro .spa-caro__btn`, plus an explicit reset (`appearance:none; border:0; background:none;
   padding:0`) because a `<button>` arrives wearing the theme.

When a rule does not apply, enumerate the rules that actually match the element rather than adding
`!important` — `!important` would also have beaten this file's own responsive rules.

## An apostrophe in a comment inside a single-quoted CSS string

The widget stylesheet lives in `$css = ' … ';`. A possessive in a prose comment inside it — "the
client's", "one card's worth", "its neighbour's" — closes the string, and the file stops parsing. It
has happened four times on this site.

`scripts/rfile.ps1 put` catches it, but only after an upload. `scripts/spa-deploy-mu.ps1` now scans the lines
between `= '` and the closing `';` locally and refuses before anything leaves the machine. Writing
"the client" instead of "the client's" costs nothing; a 500 costs a rollback.

## `$array[] = &$variable` overwrites what you already appended

Appending a reference and then reassigning the variable writes through that reference, mutating the
element already in the array. Building a list this way gives the right number of items, all of them
equal to the last one:

```php
$product = array( 'name' => $name );
$out[]   = &$product;        // WRONG - every row ends up as the final product
```

On this site it produced three product lines holding the correct count of products, every one of them
named "IS CLINICAL" with the same description. Nothing errors; the counts look right, so a summary
line that only reports totals will not catch it.

Track an index instead:

```php
$out[] = array( 'name' => $name );
$i     = count( $out ) - 1;
$out[ $i ]['why'] = $text;
```

## A scrape must be reconciled against a count the page itself gives you

Parsing the client's Booker menu with a regex that required one duration and one price silently
dropped three real services — the ones priced as ranges (`45 min - 1 hr $65.00 - $80.00`). The output
looked complete and plausible.

It was caught by counting the page's own "Book" buttons (63) against parsed prices (59) and chasing
the four-item gap. Any scrape of a list should assert against something the source counts for you —
buttons, "N results", pagination — rather than trusting that the pattern matched everything.

## Elementor caches rendered HTML, so regenerating the CSS is not enough

After writing `_elementor_data`, the usual

```php
\Elementor\Core\Files\CSS\Post::create( $post_id )->update();
```

rebuilds that post's **stylesheet** and nothing else. Elementor also caches rendered element markup,
so the page can keep serving the old band from a database row that plainly contains the new one. The
symptom is maddening: a probe reports the widget missing while a PHP dump of the same post shows it
present, and a cache-busting query string changes nothing because the cache is server-side and keyed
on the post, not the URL.

Finish any script that rewrites page data with:

```php
\Elementor\Plugin::$instance->files_manager->clear_cache();
```

`build/spa-clear-elementor-cache.php` also flushes the object cache and deletes `_transient_elementor%`
rows, which is what finally made a swapped home-page band appear.

## Nine Elementor document saves exhaust 256MB in one request

`\Elementor\Plugin::$instance->documents->get( $id )->save()` holds the whole document tree in memory
and does not release it between posts. A site-wide rewrite across nine pages and templates died with
`Allowed memory size of 268435456 bytes exhausted` after five of them — leaving four unwritten, with no
error visible on the site itself.

Make the script idempotent and give it an explicit batch size (three documents per run has been
comfortable here), rather than discovering the ceiling when half the job is done.

## Specificity in a selector LIST is judged per matching selector

A rule written as

```css
.cs-slider .cs-arrow,
.cs-slider .cs-arrow:hover,
.cs-slider .cs-arrow:disabled { background: #FFF6E9 !important }
```

is **0,2,0 against an ordinary arrow and 0,3,0 against a disabled one** — the whole declaration block
inherits whichever selector matched. So an override at 0,3,0 fixes the Next button and leaves Previous
untouched while the carousel is on its first slide.

The symptom is the worst kind: two identical-looking elements on the same page, one correct and one
not, which reads like a caching problem and is not. It cost three deploys here.

Enumerate the matching selectors rather than reading the rule as a whole:

```js
r.selectorText.split(',').map(s => s.trim()).filter(s => el.matches(s))
```

Then outrank the **highest** of them. Repeating a class (`.cs-arrow.cs-arrow.cs-arrow`) is the cheapest
way up and does not require `!important`.

## Elementor's per-element rule beats anything sane, for images too

`.elementor img { border-radius: 0 }` is 0,1,1 — a tie with `.elementor-widget-image img`, which it
then wins on load order. Leading with `.elementor` gets to 0,2,1 and fixes most of it.

But where a page author set a radius in the editor, Elementor writes

```css
.elementor-1247 .elementor-element.elementor-element-18b4e704 img { border-radius: 0 }
```

at **0,3,1**, which no reasonable stylesheet selector beats. Rounding every image site-wide needs
`!important`, and the cost is that the per-image control in Elementor stops working. That is a real
trade, not a free win — say so when you make it.

## One stray `</div>` in a widget breaks every band BELOW it

A widget that closes more divs than it opens closes Elementor's own `.elementor` wrapper early. Every
section after it becomes a sibling of `<body>` instead of a descendant, so none of the per-element CSS
matches any more — because that CSS is written as `.elementor-9 .elementor-element-XXXX { … }`.

What it looks like, and why it is so confusing:

- containers collapse to `display:inline`, because `.e-con{display:var(--display)}` and `--display`
  comes from the per-element rule that no longer matches. An invalid `var()` falls back to `inline`.
- sections set to hide on all breakpoints **reappear**, for the same reason.
- icons lose their size, columns lose their widths, spacing vanishes.

Nothing errors. The HTML validates as far as the browser is concerned — it just auto-closed a div.
`post-N.css` is present and full of the right rules, which sends you looking at caching.

The tell is in the DOM, not the CSS: walk the broken element's ancestors and see whether
`.elementor .elementor-N` is among them. A working sibling will have it and the broken one will not.

```js
let x = el.parentElement, chain = [];
while (x) { chain.push(x.className); x = x.parentElement; }
```

Count the `echo` statements in any widget that opens a wrapper. `$this->open()` emits one div; count
it.

## A CSS custom property is scoped to where it was declared

`--spa-display` and friends are declared on `.spa-sv, .spa-cards, .spa-cats …`. Used from a selector
that is not inside one of those — an Elementor image box, say — `var(--spa-display)` resolves to
nothing, the whole `font-family` declaration becomes invalid, and the element silently keeps the
inherited face. The `font-size` beside it applies normally, so a serif heading turns sans with
everything else looking right.

Outside the widget markup, name the kit variable directly:

```css
font-family: var(--e-global-typography-primary-font-family, "Playfair Display"), Georgia, serif;
```

## An inverted `:has()` guard hides everything it was never aimed at

A rule meant to collapse *empty* bands was written as "hide any band that does **not** contain one of
our components":

```css
/* WRONG - this is a rule about everything, not about empty bands */
body.single-spa_service .elementor-location-single > .e-con:not(:has(.spa-cards,.spa-cats,…)){display:none!important}
```

It behaved perfectly while the single template was built from `spa-*` widgets. The template was later
replaced by a clone of a hand-built page, which contains **no spa widget at all** — so every band
matched `:not(:has(…))` and all 35 service detail pages rendered a header, a footer and nothing in
between, for weeks. The markup and the dynamic data were present and correct the whole time, at
`height: 0`.

An inverted selector describes the entire rest of the document. Give it a positive precondition so it
can only ever fire on the case it was written for:

```css
/* RIGHT - the band must CONTAIN one of our widgets before it can be hidden for that widget being empty */
… > .e-con:has(.elementor-widget[data-widget_type^="spa-"]):not(:has(.spa-cards,.spa-cats,…)){display:none!important}
```

The tell is specific and cheap to check: `getComputedStyle(el).display === 'none'` on a container
whose descendants all have the right text. Count visible vs total widgets on any page built from a
template you did not write:

```js
const all=[...document.querySelectorAll("[data-widget_type]")];
all.length - all.filter(w=>w.getBoundingClientRect().height>2).length   // 232 of 255 hidden
```

## Two probe false negatives that make a working widget look broken

Both cost a round trip on the team band:

- `querySelector(".spa-team")` finds nothing — the wrapper is `.spa-sv.spa-sv--spa-team`; the row is
  `.spa-team__row`. Match the class the widget actually emits, not the one named after it.
- `querySelectorAll("img")` returns `[]` — portraits are `style="background-image:url(…)"`. Read
  `getComputedStyle(el).backgroundImage` as well as `<img>`, which is what `audit/imgres.mjs` does.

Also: `waitUntil:"networkidle"` times out on these pages because a missing `hair-video.mp4` never
settles. Use `"load"` plus an explicit wait.

## A global colour pick beats the plain value, and lives in `__globals__`

Rewriting `settings['background_color']` on an Elementor widget changed its border and text and left the
background exactly as it was. The element also carried:

```json
"__globals__": { "background_color": "globals/colors?id=spacream2" }
```

Elementor writes the per-element CSS from the GLOBAL reference when one exists, so the plain value is
dead weight. The symptom is maddening because the other keys in the same edit do apply — you get a
half-changed button and start suspecting caches.

When normalising any colour in page data, clear the matching `__globals__` entry as well, and copy the
reference element's `__globals__` if it has one:

```php
unset( $n['settings'][ $key ], $n['settings']['__globals__'][ $key ] );
```

## `update_post_meta()` unslashes, so raw JSON must be `wp_slash()`ed going in

`update_metadata()` runs `wp_unslash()` on the value. Storing `_elementor_data` or a `_prev_data`
backup without `wp_slash()` strips the escapes out of the JSON, and it will not decode when you read it
back. This was discovered the worst way: a `_prev_data` safety net written for a risky patch turned out
to be unreadable at the exact moment it was needed, and the fix had to go forwards instead of back.

```php
update_post_meta( $id, '_prev_data', wp_slash( $raw ) );          // both of them
update_post_meta( $id, '_elementor_data', wp_slash( $out ) );
```

Verify a backup by decoding it, not by checking it is non-empty.

## Elementor containers default to `flex-wrap: wrap`

Growing an icon from 21px to 40px inside a 148px row pushed the total to exactly the row width, and the
icon silently dropped onto a second line — reading as "the arrow moved below the text" rather than as a
wrap. Any row where an element is being resized needs `flex-wrap: nowrap` and `min-width: 0` on the
text beside it, or the growth shows up as a reflow somewhere else.

## `:has()` cannot contain another `:has()` — the whole selector is dropped, silently

Nested `:has()` is invalid CSS. The browser discards the **entire selector**, with no console warning
and no sign in devtools that a rule was ever intended. Twelve selectors on this site were written that
way:

```css
/* INVALID - the inner :has() kills the rule */
.e-con:has(> .elementor-widget-button + .e-con:has(.elementor-widget-html svg)) { align-items:flex-start }
```

The symptom is maddening because the *valid* rules around it work. The membership drawer opened and
closed correctly - its own selector has only one `:has()` - while the card alignment and the arrow
rotation did nothing, which reads as a specificity or caching problem and sends you looking in the
wrong place.

Two sibling `:has()` are fine (`.x:has(> a):has(> b)`); one inside another is not.

Where a script already stamps state on an element, key off that instead and drop `:has()` entirely:

```css
.elementor-widget-button[data-spa-open="1"] .elementor-button-icon { transform:rotate(90deg) }
```

Check before deploying:

```bash
grep -c ':has([^)]*:has(' file.php     # must be 0
```

## Selector depth is worth counting, not guessing

`row > card > inner > (button + panel)` needs three child steps. Written with two it matched the CARD
instead of the row, so `align-items` landed on the wrong element and the cards went on stretching -
again looking like the rule had not loaded. Print the ancestor chain and count it before writing the
selector.

## Elementor: a template can silently revert to an old revision

Symptom: template 2623 came back with a VIDEO hero, the pre-alternation background colours and 128
widgets, when the work in this session had left it on a static hero, strict A/B backgrounds and 115
widgets. Nothing in the build scripts had written it since.

It was not corruption - it was an older copy of the document being restored wholesale, most likely an
Elementor editor autosave for that template being saved over the top. The giveaway is that unrelated
properties changed together and the widget COUNT went up: a buggy script loses or duplicates nodes, it
does not put a video background and old colours back at the same time.

Defences that worked:
- Every script that writes `_elementor_data` keeps a named copy first (`_prev_data_<change>`). That is
  what made this one-command recoverable - `_prev_data_predept` still held the good document.
- Compare band-by-band, not byte counts: print each band's background and the widget count for the
  stored copy and the backup side by side before restoring.
- Re-run the audits (`heroes.mjs`, `altbg.mjs`, `deptlink.mjs`) after ANY template write. The revert
  was caught by the hero audit, not by the script that wrote.

If a template keeps reverting, check whether the Elementor editor is open on it in a browser tab.

## PHP: `foreach ( $nodes as &$n )` plus recursion corrupts the tree

Walking `_elementor_data` to patch one node is the standard job in this repo. Done with a reference
and recursion it is a trap: the reference left dangling after each loop means later iterations write
through it and overwrite earlier entries, and the script then saves that tree.

Use the index instead - it has no dangling reference and propagates into nested arrays correctly:

```php
foreach ( $nodes as $i => $unused ) {
    if ( '97f0652' === (string) ( $nodes[ $i ]['id'] ?? '' ) ) { $nodes[ $i ]['widgetType'] = '...'; return; }
    if ( ! empty( $nodes[ $i ]['elements'] ) ) { $walk( $nodes[ $i ]['elements'] ); }
}
```

The symptom was quiet: the script printed the change it intended and reported "written", and the node
was unchanged on the next read. Always read the value back in the SAME request after writing it.

## Elementor caches rendered widget HTML, so a render filter looks dead

`elementor/widget/render_content` never ran for a plain button in a shared template: Elementor 4.x
stores rendered widget HTML in `_elementor_element_cache` post meta. Worse, when the filter did run,
the cache pinned whichever department rendered FIRST onto all 47 services.

The experiment option `elementor_experiment-e_element_cache` set to `inactive` does NOT stop it; the
rows came straight back. Do not vary a plain Elementor widget per request in a template shared by many
posts. Register a widget instead - Elementor does not cache those the same way, and the rest of this
template already works that way.

## A hidden element still matches `textContent`

Finding the button to patch with `[...document.querySelectorAll("a")].find(a => /view the hair/i.test(a.textContent))`
returned a copy inside a band that is `display:none`, so every later measurement described the wrong
element and the "fix" landed on something nobody can see. Filter to a real box first:

```js
const shown = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
```

Related: the band-hiding guard in spa-service-widgets.php hides any top-level band that contains a
`spa-` widget but none of the known spa content classes. A NEW widget whose markup carries no `spa-*`
class makes its whole band disappear - add the class to that `:not(:has(...))` list when adding a
widget.

## A widget that renders nothing can hide the whole band

Adding `spa-service-faqs` to the FAQ band made the band vanish on 55 of 56 services. The band-hiding
guard in spa-service-widgets.php hides a top-level band that contains a `spa-` widget but none of the
known spa content classes - and a per-service widget with no data outputs nothing, so the band matched
the rule and took the generic accordion down with it.

Whenever a widget is added to a band that also holds hand-built content, add that content's class to
the `:not(:has(...))` allow-list. `.elementor-accordion` is in it now for exactly this reason.

## Not every spa widget extends the shared base class

`$this->style_controls()` added to `Spa_Widget_Book` was an immediate FATAL: that one extends
`\Elementor\Widget_Base` directly, not `Spa_Svc_Widget`. Check the `extends` clause before calling a
base-class method on a widget - the class list is not uniform:

```bash
grep -n "^class Spa_Widget_" remote-files/spa-blue/mu-plugins/spa-service-widgets.php
```

The site stayed up because the fatal only fires where controls are registered, but the Elementor editor
would have been broken.

## A numeric-looking Elementor id becomes an INT array key in PHP

`const BANDS = array( '2890132' => ... )` silently stores an integer key, so `$band_id === (string) $band['id']`
never matches and the script reports "band not found" for exactly the one band whose id has no letters
in it. Cast the key back: `$band_id = (string) $band_id;`.

## `closest('.e-con')` is not the band

Used twice now to find "the section" and wrong both times: on this template it returns the heading's own
column, so a sibling accordion or a card row sitting beside it is outside the result. A check written
that way called a full band empty, and a screenshot of a section captured only its title. Walk up to the
child of the location root instead:

```js
const root = document.querySelector('.elementor-location-single');
let band = el; while (band && band.parentElement !== root) band = band.parentElement;
```

## `.spa-cats` is two-up by default; the main pages only look single-column because of a widget override

The product-lines block on the landing pages renders one card per row, so a new widget reusing that
markup looks like it will too. It will not: `.spa-cats` is `repeat(2, minmax(0,1fr))` above 880px, and
that block is single-column only because its widget instance carries a columns control that writes a
per-element rule. Reusing the markup without the override gave two 300px cards in a 615px column, with
the titles wrapping one word per line.

Measure `getComputedStyle(el).gridTemplateColumns` on BOTH the page you are copying and the page you
are building before assuming a layout carries over:

```
main page   .spa-cats--drawer  cols="593.125px"      <- one track
service     .spa-cats--cards   cols="299px 299px"    <- two
```

## Page-level Elementor CSS does not travel to the template

The products list on /hair-salon/ keeps a fixed height and scrolls inside its column. Nothing in the
widget's settings says so and nothing in the mu-plugin stylesheet did either - it was custom CSS saved
on that PAGE, scoped `.elementor-867 ...`, so rebuilding the same block on the service template got
none of it.

When a block "looks different on the template", check for page-scoped rules before assuming the widget
differs. The quickest way is to ask the browser which rules actually match the element:

```js
for (const sh of document.styleSheets) for (const r of sh.cssRules || [])
  if (r.selectorText && el.matches(r.selectorText) && /height|overflow/.test(r.cssText)) console.log(r.cssText);
```

Behaviour that belongs to a widget should live in the widget's own stylesheet, keyed on
`.elementor-widget-<name>`, not on one page.

## A flex item will not shrink below its longest word without `min-width:0`

Good to Know on a phone: two rows kept their arrow inline and two pushed it onto its own line. The
difference was only the heading text. A flex item's automatic minimum size is its content, so a column
holding "Before your appointment" refuses to go narrower than the longest word plus padding and shoves
its sibling out of the row.

`flex:1 1 auto` alone does not fix it - add `min-width:0`. The symptom is a layout that works on some
rows and not others with identical markup, which reads as random until you compare the text lengths.

## Measure alignment between SIBLINGS, not against the heading element

Checking "is the picture aligned with the heading" by comparing the picture container's top against the
`<h3>` reported a 30px error on a layout that was correct: the heading element sits below its own widget
wrapper because of margin. Compare the two sibling containers the flex row actually aligns, and the
number means something.

Related: when a band is centred by design on desktop and top-aligned on mobile, assert only the
breakpoint you changed and print the other, or the audit fails on behaviour nobody asked you to change.

## Making template copy per-service: use a dynamic tag, not a widget swap

The instinct is to replace the heading with a field widget. Do not. A heading's look comes from
per-element CSS that Elementor generates FOR A HEADING WIDGET; change the widget type and that CSS is
regenerated for the new type and the styling is gone. That is what happened to the hero button.

A dynamic tag changes only the content, so the widget - and every typography, spacing and colour
control the client can see - stays exactly as it was. Elementor stores it on the widget as:

```php
$settings['__dynamic__']['title'] =
  '[elementor-tag id="abc1234" name="spa-service-field-tag" settings="' . rawurlencode( wp_json_encode( array(
      'key' => 'gtk_1_title', 'fallback' => 'Before your appointment' ) ) ) . '"]';
```

Give the tag a `fallback` control and seed it with the wording already in the widget, or every service
that has not filled the field in goes blank. On this site that is 55 of 56.

## `defer_to` is only safe where something else renders in its place

The spa-team widget was given `defer_to = providers` during the CPT pass so it would stand aside for a
per-service widget - but none was added, because the team widget already prefers the people a service
names. The result: the band was fine on 55 services and EMPTY on the one service that had the data,
which is the exact opposite of the intent and the hardest case to notice.

Before setting `defer_to`, check the band actually contains the replacement widget. A deferring widget
with no partner is a silent hole that only opens on the pages carrying real data.

## One predicate, two meanings, two bugs

`spa_svc_addon_groups()` was written to answer "should this be hidden from the department menus?" and
later reused to answer "is this an add-on?". The two questions have different answers for the
experiences, and the result was an experience card with no badge AND a Most Loved band full of add-ons.

When a second caller wants an existing list "but slightly different", add the narrower function rather
than widening the first. Name both after the QUESTION they answer, not the data they hold.

## go.booker.com renders only in a browser

A plain fetch of the client's Booker service menu returns no services - it is a JavaScript app. Loading
it in Playwright with `waitUntil: "domcontentloaded"` plus a 12s settle gives the full menu as text,
59 services with durations and prices. `networkidle` never fires on it and times out.

## A flash shorter than a frame cannot be measured by sampling frames

The pink-menu flash lasts less than 16ms, so a `requestAnimationFrame` loop reading
`getComputedStyle` never catches it. The first version of `audit/noflash.mjs` did exactly that and
passed - and still passed with the fix REMOVED from the response, which is worse than having no check
at all. Two separate self-tests were needed before that became obvious:

1. forcing the colour with an injected `!important` rule proved nothing, because the injection was
   itself being overridden;
2. serving the page with the fix stripped out still reported zero hits.

For a streaming-paint problem, measure DOCUMENT ORDER in the served HTML - which stylesheet and which
markup come first - because that is what actually decides whether the browser can paint the unstyled
state. It is exact, repeatable, and fails loudly when someone moves the rule.

Related trap from the same hunt: an element can compute to a colour it never paints. `.lp-hdr__brand`
(wraps the logo image) and `button.lp-burger` (zero-width border, no text) both compute to #cc3366 and
always have. A check that flags "computed colour is pink" reports them forever. Test for painted text
by walking TEXT NODES and reading their parent's colour, and for borders by requiring a non-zero width.

## Elementor theme-builder conditions (2026-10-05)

Three traps, found while binding a preview template to two specific services. All three fail
**silently** — the condition is stored, reads back correctly, and is simply never matched.

1. **The `include/` prefix is required.** `singular/spa_service/3150` does nothing;
   `include/singular/spa_service/3150` works. Copy the shape from a template that already works.
2. **The string is `type/name/sub_name/sub_id`** — see `Conditions_Manager::parse_condition()`.
   A single post of a CPT is `include/singular/spa_service/<id>`. There is **no `post` segment**
   in between, which is the obvious guess and is wrong.
3. **`save_conditions()` takes arrays, not strings.** It does `unset($c['_id'])` then
   `implode('/', $c)`, so passing strings gives `Cannot unset string offsets`. Pass
   `array('type'=>'include','name'=>'singular','sub_name'=>'spa_service','sub_id'=>'3150')`.
   Prefer it over writing the meta directly: it also calls `$this->cache->regenerate()`, and the
   conditions cache is otherwise left stale.

**Do not verify which template won from inside one PHP request.**
`get_documents_for_location()` memoises into `$this->location_cache[$location]`, so the *first*
service checked returns its answer for every service checked afterwards. My probe reported that all
four services — including the untouched live ones — had switched to the preview template, which was
alarming and wrong. The ground truth is an HTTP request: the rendered page carries
`elementor-page-<template id>`.

```bash
curl -s "$BASE/services/<slug>/" | grep -oE 'elementor-page-[0-9]+' | sort -u
```

## `_spa_tags` splits on commas (2026-10-05, seen twice now)

A product chip is one entry in a comma-separated string, so a tag written as
`Stronger, healthier hair` renders as two chips: "Stronger" and "healthier hair". Olaplex shipped
that way and it survived a rebuild of the block, because the fill script never overwrites a value
that is already there.

It **cannot be detected automatically** — `Repairs damage, Reduces breakage` is two legitimate tags
and looks identical to the parser. `build/spa-fix-chip-commas.php` lists repairs explicitly and then
prints every chip starting with a lowercase letter, which is the usable heuristic for a human.

The same trap is why `_spa_best_for` has its own meta key rather than living in `_spa_tags`.

## Canva: `create-design` ignores `asset_ids` and regenerates

Passing an existing generated image's `asset_ids` to `create-design` does not place that image —
Canva generates a fresh one from the brief, so the exported file is **not** the image that was
approved from `generate-image`. Check the export before using it.

Also: the `thumbnail.url` from `get-assets` is signature-locked to its 200px dimensions. Editing
`height:` / `width:` in that URL returns **HTTP 403**, not a larger image. Full resolution only
comes from `export-design` on a real design.

## `_prev_data_*` backups must be `wp_slash()`ed, or they are not restorable (2026-10-06)

Every "keep the previous value" backup written like this is **corrupt**:

```php
$raw = get_post_meta( $id, '_elementor_data', true );   // valid JSON
update_post_meta( $id, '_prev_data_x', $raw );          // WRONG
```

`update_metadata()` runs the value through `wp_unslash()`, so the escaping is stripped on the way
in. Elementor data is full of `\"` inside HTML attributes, and those become bare `"` — the JSON no
longer parses. `_elementor_data` itself was always written with `wp_slash()`; the *backup* beside it
was not.

Eleven backups on the preview template read back at ~145KB each and **not one decoded**. The safety
net looked present in every dry-run listing and would have failed the moment it was needed.

```php
update_post_meta( $id, '_prev_data_x', wp_slash( $raw ) );   // right
```

Check a backup by decoding it, not by checking it exists:
`is_array( json_decode( get_post_meta( $id, '_prev_data_x', true ), true ) )`.

## Finding a row of tiles in Elementor data: "2+ container children" is not enough

Looking for a tile row with *"a container with two or more container children that contains <marker>"*
also matches the **whole band**, whose two children are the heading block and the tile row. The
harvest then read the section heading as tile 0 and merged every tile into tile 1.

Require that **every** child container has a picture of its own — only the tile row does:

```php
foreach ( $kids as $kid ) {
    if ( false === strpos( wp_json_encode( $kid ), '"widgetType":"image"' ) ) { $ok = false; break; }
}
```

Or scope the search to the band's own children rather than the whole tree, which is what made the
first version of the same search work and the second one fail.

## A regression check must not write to the client's content (2026-10-06)

`audit/offers.mjs` tested the "no offers" state by stashing and clearing `_spa_offers` on the very
service the client had filled in by hand, then restoring it in a `finally`. It worked, but it is a
risk taken for nothing: a crash, a timeout or a killed process between the two leaves their content
in a side meta key.

It now drives the **spare** preview service (#3151, which has no offers of its own) for the hide and
empty states, and only ever **reads** the one the client edits. The PHP helper refuses outright if
it is ever pointed at the client's service.

## Do not assert the client's content, only the behaviour

The same check asserted that the offer tiles must have **distinct titles**. That was added to catch
a bug of mine, and it then failed on the client's own data — they legitimately had three rows
carrying the same offer with different pictures, and later edited one to read "…blowouts test".

A check that fails because the client wrote something reasonable is worse than no check: it trains
you to ignore a red line. Assert that the tiles render, that the pictures are there, that hiding
works. Leave the words to them.

## An Elementor theme-builder template needs to be in the CONDITION INDEX, not just its own meta

`_elementor_conditions` on the template can read exactly like a working template's and still never
render. Elementor consults a site-wide option:

```
elementor_pro_theme_builder_conditions
  => [ 'single' => [ '<template id>' => [ 'include/singular/spa_provider' ], ... ], ... ]
```

A template missing from that index simply never matches. `$document->save_conditions()` is supposed
to add the row and did not here, so `build/spa-team-cond-fix.php` writes the index directly after
trying the API.

The diagnosis only came from comparing the index against a template that DOES work - the meta looked
perfect throughout. **HTTP is the ground truth**: fetch the URL and look for a marker class from the
template.

## A dynamic tag must not wpautop() everything it returns

`wpautop()` on every field put a `<p>` inside an Elementor button and inside every heading. The Book
button grew from 50px to 64px - the client spotted it as odd padding, though the padding was
identical at 18px 32px; it was the TEXT BOX that went from 12px to 26px. A `<p>` inside an `<h2>` is
invalid markup besides.

Paragraph-wrap only when the value actually holds a blank line.

## An empty dynamic URL makes Elementor render href="http://Array"

When a URL tag returns nothing, Elementor falls back to the widget's static `link` setting - which is
an **array** - and stringifies it. Every team member without a booking link of their own got
`href="http://Array"`.

A URL tag for a button must always resolve to something. `spa_booking_url_site()` reads the salon's
Booker link off the services so the button can never be dead.

## A script sent through the bridge shares the bridge's variable scope

`scripts/rwpphp.ps1` includes the script inside a bridge function, so a local called `$name`, `$title` or
`$out` CLOBBERS the bridge's own. The symptom was a PHP warning emitted before the response headers -
which breaks redirects and cookies site-wide.

Prefix locals in build scripts (`$tm_name`, `$tm_title`).

## PowerShell `Set-Content -Encoding utf8` writes a BOM (Windows PowerShell 5.1)
A plugin's main PHP file rewritten that way made WordPress send U+FEFF before every page and REST response
(pop.org dev, 2026-10-27): JSON parsers failed, and headers/cookies are at risk. Write PHP with Python
(`open(p,'w',encoding='utf-8',newline='\n')`) or `-Encoding Ascii`, and after any upload check the first bytes of
the home page are `3c 21 64` (`<!d`).

## WP Engine CDN caches plugin assets by ?ver=
Re-uploading a plugin with the same version left the old `fsi.css?ver=0.4.0` served from the CDN - PHP changes were live,
CSS changes were not. Bump the plugin version (the asset `ver`) on every CSS/JS change.

## A stylesheet enqueued during shortcode rendering prints in the footer
`wp_enqueue_style()` called inside a shortcode/widget render runs after `wp_head`, so the CSS arrives at the end of the
body and the page paints unstyled first (a visible "glitch" on load). Enqueue it on `wp_enqueue_scripts` for the pages
that need it.
