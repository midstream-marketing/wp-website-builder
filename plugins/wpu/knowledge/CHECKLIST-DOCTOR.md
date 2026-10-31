# Pre-handover checklist

Run this before telling a client anything is finished. Every item is something
that has actually shipped broken at least once.

---

## Automated gate

```bash
node audit/audit.mjs                 # must exit 0
pwsh bin/php.ps1 --lint-theme        # must be clean
pwsh bin/wpphp.ps1 php/dead-widgets.php
pwsh bin/wpphp.ps1 php/orphans.php
```

---

## Every page

- [ ] Returns 200 — including cart, checkout, account, search, and a 404
- [ ] No horizontal scroll at 360 / 390 / 768 / 1024 / 1440 / 1920
- [ ] No text overlapping other text or artwork at any of those widths
- [ ] Content is not stranded in one half of the screen with a void beside it
- [ ] Tables scroll inside their own box rather than pushing the page sideways
- [ ] No broken images, no console errors that are ours
- [ ] Every page has a `<title>` and is not "thin" (an empty section is a bug)

## Layout traps worth checking by eye

- [ ] Artwork **reflows** on mobile rather than being `display:none`-d away
- [ ] Long-form pages use a readable measure, and builder pages are exempt
- [ ] Cart / checkout / account keep the full width
- [ ] Sticky headers do not cover anchored content
- [ ] Logos are visible against whatever background they sit on — check both

## WooCommerce

- [ ] **At least one payment gateway is enabled** (otherwise checkout dead-ends)
- [ ] Add to cart works from every place it appears — carousel, archive, single
- [ ] Cart quantity, remove and coupon all work
- [ ] Shipping: a qualifying order is not still offered the paid rate
- [ ] Countries you do not ship to cannot start a checkout at all
- [ ] Order emails have somewhere real to go
- [ ] Prices, thresholds and shipping copy on content pages match the actual
      WooCommerce settings — these drift constantly

## Content

- [ ] No placeholder text, lorem ipsum, or demo-import leftovers
- [ ] No references to a previous theme or agency anywhere on the front end
- [ ] Every email address and phone number is the client's real one
- [ ] Policy pages are flagged to the client as templates needing legal review
- [ ] Menus contain no links to trashed or draft pages

## Accessibility

- [ ] Every interactive control is reachable by keyboard and shows focus
- [ ] Tabs, drawers and accordions carry correct ARIA state
- [ ] Decorative overlays do not swallow clicks (`pointer-events: none`)
- [ ] Images have alt text; decorative ones have empty alt

## Before you say it is done

- [ ] The fatal-error log has nothing recent — check the timestamp, not just
      the file
- [ ] Re-ran the full audit **after** the last change, not before
- [ ] Anything you could not verify is stated plainly as unverified
- [ ] Anything left undone is listed, with why
