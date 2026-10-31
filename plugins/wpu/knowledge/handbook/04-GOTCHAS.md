# 04 — Gotchas

Symptom → cause → rule. Almost every entry is a **silent** failure: the build is
green, nothing logs an error, and the output is wrong.

Tagged `[universal]`, `[elementor]`, `[wordpress]` or `[css]` so you can take
what applies.

---

## Layout and geometry

### A row wraps into misalignment on some pages but not others `[universal]`

**Symptom:** "the templates look messed up / not aligned" — intermittently, and
only on some pages. Halves keep their width and drop under one another, leaving
a ragged right edge.

**Cause:** column widths were percentages computed with room reserved for the
gap against the *page* container — but **a percentage width survives nesting and
a pixel gap does not.** The same row inside a padded panel or a half-width
column gets less width than it was promised, exceeds 100%, and wraps. Every
instance measured 100.1%–101.6%, which is why it read as flakiness.

**Rules:**
- Set `flex-wrap: nowrap` whenever the children were sized for a single line.
  Flexbox then shrinks them to whatever width is really there and the arithmetic
  stops mattering at any nesting depth. Restore wrapping at tablet.
- **Wrapping is not stacking.** A row that no longer fits must set every child
  to full width, or you get the ragged-edge rendering rather than a stack.
- Compute the tablet container as `breakpoint − 2 × section padding`. Using 760
  instead of 720 was 8px of optimism, enough to push a 2-up grid to 100.17%.
- Validate it: measure each row's real width after nesting and padding, at
  desktop **and** tablet.

### A container style has no effect `[elementor]`

`max_width` and `height` are **not container controls** and are silently
ignored. Use `content_width: boxed` + `boxed_width`, and `min_height`.
`flex_align_self` is not one either — `_flex_align_self` is.

The trap that let this survive: a generic leniency rule excused anything ending
in `_width`. **Check the dead list first, unconditionally.**

To cap a text measure on a container, pad the outer edge instead.

### An overlay panel is invisible `[universal]`

A translucent "overlay" token painted over **its own ground** resolves to
1.00:1. Use a contrasting low-alpha token (white at low alpha on a dark ground).
Measure contrast; do not eyeball it.

---

## Silent content loss

### A form ships the wrong fields `[universal]`

**Symptom:** the page renders a working form — just not the one specified. On
the one page whose entire purpose is the form.

**Cause:** one branch of the planner built the block without passing `fields` or
`success_message`, so the custom form was discarded and replaced by the generic
fallback. Nothing in the build output flagged it.

**Rule:** after any planner change, rebuild every client into a temp dir and
diff the fresh IR against each committed IR. Compiled output is useless for this
— ids are randomised.

### A deleted page keeps shipping `[universal]`

When a rebuild shrinks the page set, the stale compiled template survives in the
output directory and is still counted by audits and still zipped. **Clear the
output directory when a build's page set shrinks.**

### An audit that cannot see inside lists passes banned copy `[universal]`

**Symptom:** a build carrying "REGULATORY PEACE OF MIND" — a banned phrase — in
a tick list passed the copy gate as "no banned copy".

**Cause:** the audit read text only from an element's own settings. Everything
inside a repeater — icon-list ticks, pricing features, footer links, accordion
titles, form labels — was invisible to both the word count and the
banned-phrase check, on every client, for weeks.

**Rule:** a gate that reads a tree must walk *every* node type that can hold
text, including repeater items. Test it against a known-bad fixture — one that
*must* fail — not only against builds you expect to pass. A gate that has never
been seen to fail has not been shown to work.

### Geolocation-swapping content hides it from Google `[universal]`

**Symptom:** a brief asks for one page that swaps currency, wording and
regulator names by visitor IP (Australia vs worldwide).

**Cause:** Googlebot crawls overwhelmingly from US IP addresses. An IP swap
shows Google only the default/worldwide variant, so every market-specific
keyword — the ones the client explicitly asked to rank for — never gets
indexed. It also fights page caching (one stored copy served to every country).

**Rule:** one URL per market, joined by **hreflang**. Build the variants from a
single composer so they cannot drift. A visitor-level redirect can sit on top;
the content itself must live at crawlable URLs.

### A nested `{label, href}` renders a card with no button `[universal]`

Some components want a bare label plus a separate `href`. Passing the nested
shape produces no button and **no error**. Four prop-shape traps like this cost
real time on one build; each is now documented per component. When a component's
output is missing an element, check the prop shape before checking the renderer.

---

## Text and markup

### `.upper()` uppercases HTML entities `[universal]`

`&amp;` becomes `&AMP;`, which renders literally: **"COMMERCIAL &AMP; COMPANY"**
shipped to a footer. Any caps/eyebrow helper needs a regex that lowercases
entity names after the upper — check *every* block family for it, not just the
one where you found it.

### A helper clobbers the caller's styles `[universal]`

A card helper that assigns a `globals` dict wholesale overwrites whatever the
caller passed in `extra`. The symptom is an unstyled panel, not an error.
**Merge, and let the caller win.**

---

## CSS and theming

### Plugin text is invisible inside a themed page `[css]`

**Symptom:** a heading renders near-black on a near-black panel. Shipped live.

**Cause:** a page builder's global kit styles headings, links and buttons with a
body-class-scoped selector — specificity **(0,1,1)**. That beats a plugin's bare
`.acg__title` at (0,1,0), so `color: inherit` there resolves to the *brand's*
heading colour.

**Rules:**
- **Never `color: inherit` inside markup that lands in a themed page.** State
  the colour at (0,2,0) — `.acg .acg__title`.
- Reset `-webkit-text-fill-color: currentColor` alongside it, because a
  gradient-text theme paints straight over `color`.
- **Bump the plugin's version constant** — it is the stylesheet cache-buster.
  Without it the browser serves the old CSS and the fix looks like it failed.

### One extra bracket paints nothing `[css]`

```css
background-image: var(--coam-brand, linear-gradient(90deg, #2b6bff, #7b3ff2)));
```

One closing bracket too many, on the **fallback inside `var()`**. CSS discards a
malformed declaration silently, so the brand bar, the amount chip and the active
tab painted with **no background at all** — on any theme that had not set the
token. It looks like a styling choice, which is why it survived releases.

**The check, worth running on any CSS edit:** strip comments, then count `{`/`}`
and `(`/`)` separately. That file scored parens **−3** while braces balanced —
the exact signature. Braces alone look clean.

### Re-skinning a plugin by editing its CSS is not upgrade-safe `[wordpress]`

Colour tokens in `assets/*.css` are reverted by any reinstall. Settings survive;
stylesheets do not. Ship a reinstall-proof Additional CSS block alongside.

---

## Platform behaviour

### Every request fatals because of a missing constant `[wordpress]`

A site copied from a managed host carries that host's mu-plugins, which
reference constants that exist only on their servers. An unguarded
`hash(… . WPE_APIKEY)` raises a fatal on PHP 8; a caller guarding with
`method_exists()` does not help — **the method exists, its dependency does not.**

Only top-level `.php` files in `mu-plugins/` auto-load, so moving the loaders
into a subdirectory disables them without touching the vendor directory. The
host re-adds them on deploy, so nothing needs restoring.

**And the knock-on:** the same fatal killed the migration plugin's own
background chunk requests, leaving a half-imported database — 11 published pages
with zero layout data while 4.1 MB of it sat on revisions and trashed posts. The
one query that settled it compared **what pages have** against **what the
database contains**. Always check where the data *is*.

### A cached page never runs your PHP `[wordpress]`

A page cache serves stored HTML before PHP runs, so a server-side redirect never
fires on a cached hit. Four things make a redirect gate actually work, none of
them guessable:

1. **Two layers** — the server-side check, plus a copy baked into the cached
   HTML as a `<head>` script.
2. **The bot test goes in the JS, not the PHP** — one cached page is shared
   between humans and crawlers, so deciding server-side bakes one audience's
   answer into the other's page. Crawlers must be let through or the gate gets
   indexed in place of every product.
3. **`data-cfasync="false" data-no-optimize data-no-minify data-no-defer`** on
   that script. Every JS optimiser defers inline scripts by default; deferred,
   the gate runs after paint — the exact flash it exists to prevent.
4. **Never gate loopback IPs.** The cache preloader fetches the site from the
   server itself with no bot UA, gets redirected, and the cache can then never
   repopulate after a purge. Presented as 6–10s TTFB with an empty cache dir and
   took a separate debugging session to find.

### A gateway is silently absent from the new checkout `[wordpress]`

WooCommerce's **block** checkout does not read classic gateways. A gateway
without a block integration works in the shortcode checkout and is invisible in
the block one — the default on new installs — so it reads as a broken plugin.
Also: `wc-settings` must be a script dependency or `getSetting()` is undefined.

### `add_query_arg()` encodes for you `[wordpress]`

Pre-encoding a value double-encodes it. And `#` as a `preg_match` delimiter
collides with a literal `#` inside a character class — use `~`. And
`wp_kses_post()` strips `<svg>`, which silently drops every inline QR code.

---

## Verification

### A green build is not evidence `[universal]`

Grep the compiled output for the values you believe you set, rather than
trusting that the component did what it looks like it does. Half the entries
above pass every validator.

### Lint proves nothing — execute the code `[universal]`

Stub the platform and **run** the classes. 33 / 72 / 82 / 102 executing
assertions on four plugins caught return-shape, order-status, stock, reference
stability and every panel rendering. Split a function that ends in `exit()` into
a decision function and an effect function, or a test can only ever check one
case per process.

### A wrong output can look perfect `[universal]`

A QR encoder with an inverted format strip produces a symbol indistinguishable
by eye that decodes as noise. What caught it: a matrix diff against a reference
implementation (60/61 bit-for-bit) **plus** a round-trip decode (65/65). Two
real bugs — the format strip is written MSB-first, and mask selection must score
the matrix *before* the format bits are written.

**Where the failure mode is silent and visual inspection is useless, build the
comparison rig.** It is cheaper than the support ticket.

### Fetch the URL with the parameter present `[universal]`

A live page was reported as having an unrendered template placeholder. It did
not — it had been fetched without the parameter that fills it. Reproduce the
exact request before calling something a bug.

### Test the preview, not just the editor `[wordpress]`

An editor stuck on its spinner is usually the *preview iframe* failing. Fetch
the preview URL directly and check the status and title.

---

## Retrieval

### A Google Doc `/edit` URL is not fetchable — `export?format=txt` is `[universal]`

Fetching the edit URL returns only the app chrome. `export?format=txt` on a
public doc returns the full text — and for a **multi-tab** document, one export
returns every tab concatenated, so the `?tab=` fragment can be ignored. `/pub`
401s. Try the export endpoint before telling anyone a document is inaccessible.

### Crawl the incumbent before composing anything `[universal]`

One hour on the client's existing site produced the real phone number, the real
email, the URL set for the 301 map, **two service URLs returning HTTP 500 that
were still linked from their own homepage**, and **no H1 anywhere on the
homepage**. Those findings are the concrete form of a scope document's vague
"broken links" complaint — and they are the difference between a redesign
proposal and a diagnosis.
