---
name: visual-change
description: The working method for any visual or design change to a WordPress / Elementor site in this toolkit - icons, spacing, alignment, typography, overlays, headers, colours, responsive behaviour. Use it whenever the client says something "looks wrong", "isn't aligned", "doesn't look premium", "is too small/narrow/tight", or asks to match a mockup or screenshot. Also use when editing a page that has been hand-edited in Elementor, when patching _elementor_data, or when a previous visual fix did not land. Not for content changes, plugin work, or WooCommerce configuration.
---

# Visual changes: get it right the first time

This exists because visual fixes on these sites kept taking three or four rounds. Every rule below is
here because skipping it cost a round trip on a real client site. The cost of following it is a few
minutes; the cost of skipping it is the client sending another screenshot.

## The one rule

**Never change a visual property you have not measured, and never report one you have not looked at.**

"The check passed" is not the same as "it looks right". A passing check on the wrong quantity is worse
than no check, because it stops you looking.

## The loop

```
1. MEASURE    what is actually on the page now - geometry, computed styles, the DOM
2. DIAGNOSE   name the mechanism, in numbers, before touching anything
3. CHANGE     the smallest edit that addresses that mechanism
4. RE-MEASURE the same quantities, with a tolerance you stated in advance
5. LOOK       screenshot the region, cropped, at deviceScaleFactor 2, and actually read it
6. REGRESS    the suite, and run the patch twice to prove it is idempotent
```

Do not skip 1 because the cause "is obvious". In the session that produced this skill, the obvious
cause (the icons) was wrong; the real cause was a paragraph's `margin-bottom` inflating a flex row.

## Step 1 - measure first

Write a probe with Playwright against the live page. Report numbers, not booleans:

```js
const page = await browser.newPage({ viewport: { width: 390, height: 900 } });
await page.goto(url + '?nc=' + Date.now(), { waitUntil: 'networkidle' });
// the element, its parent, the computed styles that decide the layout, the boxes
```

For an alignment or spacing complaint, always capture:
- the **row**: `display`, `align-items`, `gap`, height
- the **widget**: `margin`, `align-self`, height
- the **paragraph**: `margin`, `font-size`, `line-height`, height, number of lines
- the **ink**, not the box: `getBBox()` on every shape in an SVG, scaled to screen

### Measure against a stable target

This is where most alignment work goes wrong.

| Target | Stable? | Use it for |
|---|---|---|
| Element bounding box | No - includes leading and margins | nothing, on its own |
| Glyph bounding box (`actualBoundingBoxAscent/Descent`) | **No** - moves with the characters | never for a column of rows |
| Line box (`line-height`) | Yes | rough centring |
| **Cap-height midline** | **Yes** - a font property | **icons beside text** |

`(201) 706-2322` has no descenders; `hello@spabluejerseycity.com` has three. Align to the glyph box and
those two icons sit at different heights. Cap height comes from the font, so it is the same on every
row - which is exactly what makes a column look aligned.

```js
const c = document.createElement('canvas').getContext('2d');
c.font = getComputedStyle(p).font;
const m = c.measureText('H');
const baseline = pBox.top + (lineHeight - fontSize) / 2 + m.fontBoundingBoxAscent;
const capMid   = baseline - m.actualBoundingBoxAscent / 2;   // 'H' ink above baseline == cap height
```

### "Visible" means rendered, not un-hidden

`el.hidden === false` and `getComputedStyle(el).display !== 'none'` both stay true when it is the
element's **parent** that is hidden - the child's own display is untouched and only its box collapses.
A control row with `[hidden]` on the wrapper reported its two buttons as visible. Test the box:

```js
const shown = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
```

`:hover` **cannot be triggered from JavaScript.** `dispatchEvent(new MouseEvent('mouseover'))` does
not make `:hover` match, so a hover check written that way reads the resting styles and passes a
broken state. Use the driver's real `hover()`, and pick an element that is actually hoverable - a
disabled control with `pointer-events:none` never matches, and the probe measures what is underneath.

A check can also go **vacuous** rather than fail. After adding a click test, the hover check read the
"resting" colours with the pointer still parked on the arrow, and passed. Park the mouse first, and
assert the state actually *changed* (`after.bg !== before.bg`) rather than only that the result looks
acceptable.

Likewise, an overlap test must intersect **both** axes. Comparing only horizontal extents called a
control row sitting neatly *below* the cards an overlap, and sent me chasing a layout bug that was not
there.

### Validate the measuring method itself

A probe can be wrong. Sanity-check it before trusting a failure.

- **Counting lines**: divide element height by computed `line-height`. Do **not** count
  `range.getClientRects()` - `<br>` splits the contents into separate text nodes and you get a rect
  per node plus rects for the breaks. A three-line paragraph with two `<br>` reports five.
- If a measured result contradicts what you can see in a screenshot, the probe is wrong until proven
  otherwise.

## Step 2 - diagnose in numbers

State the mechanism and the magnitude before changing anything:

> Icons sit 4.2px low on every row and 16.8px low on the address row. The rows are
> `display:flex; align-items:center`, and the `<p>` carries `margin-bottom:14.4px`, so the row is
> taller than its text; the address row compounds it by centring against two lines.

If you cannot write that sentence, you are not ready to edit.

## Step 0 - do what was asked, and only that

The most expensive failure in this project was not a wrong pixel. Asked to *fix the arrows, add the
client's reviews and make the desktop slider three-up*, I replaced the whole section with a design of
my own. It measured well and it was still wrong work, and it had to be reverted.

- A request to fix parts of something is not permission to redesign it. "The design was good, it just
  needs polishing" is the default assumption unless the user says otherwise.
- The client's mock outranks the client's live site, and both outrank your taste.
- If a fix seems to need a redesign, say so in one line and ask - do not deliver the redesign.
- Restoring is cheap when the builders are still in the library. Prefer deleting a section from the
  page assembly over deleting its code.

## Step 3 - change

### Patch, do not rebuild, when a page has hand edits

Dragged values (`width: 17.318999999%`) are the fingerprint of an Elementor hand edit. Re-running a
page builder throws them away. Walk the stored tree and change only the nodes you mean to.

**Always round-trip**: `json_decode` before, `json_encode` after, `json_decode` again to check, and
`wp_slash()` on the way into `update_post_meta`. A failed decode blanks the page. Keep the previous
value in a `_prev_data` meta key.

### Match precisely, never by loose substring

A stylesheet is also an `html` widget. Matching `strpos($html, 'lp-cico')` tagged the page's 10KB
stylesheet as an icon and replaced it with a map pin; it survived only because a later branch
overwrote it back. Match a full opening tag, an exact class, or an id:

```php
const ICON_MARK = '<span class="lp-cico" role="img" aria-label="';
```

Then prove the match: list every node it hits, with its path and settings, before applying.

### Merge classes, never concatenate

`trim($existing . ' new')` appends every run: `lp-crow lp-crow lp-crow`. Split, `array_unique`, join,
and return null when nothing changed.

### Put the rule where the hook is guaranteed to land

Elementor does not render `_css_classes` on every container type. A CSS custom property declared on a
class that never renders is **undefined**, which makes `height: var(--x)` invalid and silently
collapses the box. Two defences:
- hang the rule off a class you have confirmed in the DOM
- always give `var()` a fallback: `var(--lp-crow-lh, 24px)`

## Step 4 - re-measure with a stated tolerance

Say the tolerance before you run it. For icon alignment these have worked:

| Quantity | Tolerance |
|---|---|
| Icon ink centre vs cap midline | ≤ 1px |
| Spread of that offset across rows | ≤ 0.5px (they must all be wrong the same way, or right together) |
| Spread of ink left edges | ≤ 1px |
| Spread of gaps to text | ≤ 1px |

Write it as a script that exits non-zero, and keep it - it becomes the regression test.

## Step 5 - look at it

Screenshot the **region**, not the page, at `deviceScaleFactor: 2`, with overlays removed:

```js
await page.evaluate(() => {
  for (const el of document.querySelectorAll('[class*="cookie"],[id*="cookie"]')) {
    const cs = getComputedStyle(el);
    if (cs.position === 'fixed' || cs.position === 'sticky') el.remove();
  }
});
```

Scroll **first**, wait, **then** measure the clip rectangle. Measuring in the same tick as
`scrollIntoView` returns the pre-scroll rect and the clip lands on empty background.

Beware anchoring a clip on text: `querySelectorAll('h2')` matched a copy of the heading inside a hidden
mobile menu whose rect is 0×0. Anchor on the thing you are changing, and filter to elements with a
non-zero width.

## Step 6 - regress and prove idempotency

- Run the full suite: `audit.mjs`, `fonts.mjs`, and the site's own acceptance script.
- **Run the patch twice.** The second run must report *nothing to change*. A dry run that lists work it
  will not do trains you to stop reading dry runs, which is how both bugs above survived.

## Traps that have already cost a round trip

**Elementor**
- `_elementor_data` is JSON inside a meta value, so URLs are written `https:\/\/…`. A pattern built from
  a plain URL matches **nothing** on a page that visibly shows the image. Allow an optional backslash
  before each separator, and escape the replacement the same way.
- Elementor writes `.elementor-icon svg { fill: <colour> }`. An outline icon with `fill="none"` on the
  `<svg>` gets filled solid. Put `fill="none"` on each shape - a declaration on the element beats an
  inherited value - and use `stroke="currentColor"`, which resolves against the `color` Elementor sets
  on the same wrapper, so the colour control still works.
- Elementor's SVG sanitiser strips `<style>` blocks. Presentation attributes only.
- The kit's widget spacing gives every widget `margin-bottom`. Setting `_margin` to 0 compiles to
  `calc(var(--kit-widget-spacing, 0px) + 0px)`, so it does not zero. Use a class plus `!important`.
- **The Elementor kit styles bare elements, and beats a single class.** The kit ships
  `.elementor-kit-N button { border-radius: 0 }` - specificity 0,2,0 against a class's 0,1,0 - so
  round buttons render square. A selector like `.my-dots button` ties and wins on order; a bare
  `.my-arrow` does not. Use `!important` on every property the kit touches (radius, padding, border,
  background, colour), not just the ones you happened to think of.
- **A single class loses to Elementor's per-element rule, and Elementor uses the logical property.**
  It emits `.elementor-NNN .elementor-element.elementor-element-NNN { margin-block-end: … }` -
  specificity 0,3,0 against your 0,1,0. So `.my-class{margin-bottom:8px}` lands in the DOM, appears in
  the stylesheet, and computes to 0, which reads as "the class did not apply". Use `!important` **and**
  set both `margin-bottom` and `margin-block-end`.

**Elementor widgets**
- **Ask the widget for its control names.** `slides_to_show` on a carousel does nothing and reports
  nothing; the live control is `slides_per_view`. `get_widget_types( 'name' )->get_controls()` is the
  source of truth, and guessing costs a full apply-and-measure cycle.
- **Swiper arrows need `!important` on every positioning property** - top, bottom, left, right,
  transform. Elementor's rule ties on specificity, so the failure is partial and confusing: the size
  applies and the position does not.
- **An Elementor arrow icon does not follow `currentColor`.** Its `fill` comes from the widget's
  colour control, so a hover that only changes the button's `color` gives a black circle with a black
  arrow in it. Set `svg { fill }` explicitly for both states.
- Swiper adds `swiper-button-lock` when everything already fits - hide those, or ship dead buttons.
- **`place-items:center` centres nothing horizontally in flexbox.** It is shorthand for `align-items`
  + `justify-items`, and `justify-items` has no effect on a flex container. Elementor forces
  `display:flex` on its buttons, so `display:grid;place-items:center` gives vertical centring only and
  the icon packs left - subtly wrong rather than obviously broken. Use `justify-content:center`.
- **A full-width `.swiper-pagination` swallows the arrows' clicks.** Put the arrows on the dots' line
  and the strip lies across the circles, intercepting the pointer at their centres while they still
  look and hover correctly. `pointer-events:none` on the strip, `auto` on the bullets - and assert
  that clicking an arrow actually advances the track.

**Images**
- **Measure CSS backgrounds, not just `<img>`.** Elementor sets section and tile artwork as
  `background-image`. An `<img>`-only probe reported a page full of photographs as "3 images, all fine"
  while two visibly pixelated tiles went unmeasured. `audit/imgres.mjs` walks both.
- An image is pixelated when `naturalWidth < cssWidth * devicePixelRatio`. Retina is where it hides: a
  768px file in a 768px slot is perfect on a 1x monitor and soft on every phone.
- WordPress's `medium_large` is **768px** - half what a 730px tile needs at 2x. For anything displayed
  wider than roughly 380px CSS, ask for `full` or register a size that matches the slot.
- When the source file is smaller than the slot, say so and stop. No processing adds detail that is not
  in the file, and swapping a client's own photograph for stock is a content decision, not a fix.
- A zero-height widget's collapsed margins propagate through `<body>` and shift the whole page.

**CSS**
- A `<br>` hidden with `display:none` removes the break *and* the space around it: "Jersey Cityfor
  hair". Keep a real space before each break.

**WordPress / host**
- Never run `wp_generate_attachment_metadata()` on an attachment the pages already use.
  `WP_Site_Icon::additional_sizes()` **replaces** the size list rather than adding to it - it destroyed
  the client's logo on a live site. A site icon gets its own attachment.
- Uploads can vanish. On one host the original file was removed from `uploads/` within two minutes
  while the server-generated thumbnails survived. Symptom: `file_exists()` true, HTTP request dies with
  no status code. Re-encode under a new filename, and tell the client it is their host.
- SVG upload may be refused. Inline SVG in the page data needs no file, no request, and cannot be
  quarantined.
- `wp_unique_filename()` checks the database as well as the disk, so a re-upload gets `-1` even when the
  original file is gone. The suffix is not proof the file is there.

**This repo's tooling**
- `bin/rwpphp.ps1` sends **one file**. Bundle libraries with `python bin/spa-build.py <entry>`.
- Writing a script with a heredoc mangles backslashes - regexes, `\d`, `\n`, `%1$s`. Use the Write
  tool for any file containing them. This has cost time repeatedly; do not try once more.
- Playwright scripts must live in the project directory to resolve `playwright`.

## Reporting back

Say what you measured, what the mechanism was, and what it is now - in numbers. Show the screenshot.
If something is still out of tolerance, say so plainly rather than describing the change as done.
