# Trade-site composition, derived from 8 agency references

Read from: Chicago Tree Surgeons, Skyline Fence, Lawnx Landscaping, SafeCut Tree,
HighPoint HVAC, AKTA Plumbing, NYC Plumbing, Arctic Flow HVAC.

This is the judgement half of reference-matching. `analyse_reference.py` measures
palette, type, radii and spacing; it cannot read composition. This file is that
reading, and it is deliberately expressed as frequencies rather than a single
"correct" layout — a section present in 8 of 8 is a requirement, one present in
2 of 8 is an option.

---

## 1. The canonical order

Seven of the eight follow this sequence almost exactly. Lawnx is the outlier
(softer, more editorial, blog-led) and is treated as a separate profile.

| # | Section | Freq | Block | Status |
|---|---|---|---|---|
| 0 | Utility bar — hours / area / email / phone | 5/8 | `header.simple` topbar | ✅ |
| 1 | Header — logo, nav, phone, filled CTA | 8/8 | `header.simple` | ✅ |
| 2 | Hero — dark or photo ground, chip, 2-line H1, tick list, dual CTA, **person on the right** | 8/8 | `hero.impact` | ✅ |
| 3 | Quote form — inside the hero or overlapping beneath it | 6/8 | `form.bar` | ✅ |
| 4 | Trust badge strip — Google / Facebook / Yelp / BBB / manufacturer | 5/8 | — | ❌ **missing** |
| 5 | Why-choose — photo + 2 floating badge cards on one side, chip + H2 + ticks + CTA on the other | 8/8 | `why.split` | ✅ |
| 6 | Stats band — `15+ Years · 5 STAR · LICENSED · 24/7` | 6/8 | `stats.band` | ✅ |
| 7 | Services — chip + H2 + photo cards, each with `Read More →` | 8/8 | `services.cards` | ⚠️ no Read-More link |
| 8 | Process — numbered `01→02→03→04`, usually a dark band, often with a connecting path | 6/8 | `process.split` | ✅ |
| 9 | Before / After pairs with corner labels | 4/8 | `gallery.compare` | ✅ |
| 10 | Marquee strip — repeated 1–3× down the page | 3/8 | `marquee.strip` | ✅ |
| 11 | Testimonials — 3 cards, stars, Google mark, carousel arrows | 8/8 | `reviews.embed` | ✅ |
| 12 | Service areas — location chips + map, often a dark card overlapping the map | 8/8 | `areas.chips` | ✅ |
| 13 | Per-area phone cards — one card per county with its own number | 2/8 | — | ❌ **missing** |
| 14 | Work gallery / portfolio grid | 5/8 | `gallery.grid` | ✅ |
| 15 | FAQ — split layout, **one item pre-opened** | 8/8 | `faq.split` | ⚠️ none pre-opened |
| 16 | Blog cards | 2/8 | — | ❌ **missing** |
| 17 | Final CTA — dark or photo band, CTA + phone, person on the right | 8/8 | `cta.panel` | ✅ |
| 18 | Footer — 4–5 columns, embedded map, review badges | 8/8 | `footer.simple` | ⚠️ no map, no badges |

## 2. Details that are doing the heavy lifting

These are what separate the references from a generic build. Each appears in at
least six of the eight.

1. **A person in the hero.** 8/8. Owner or technician, cut out or photographed
   against the ground, on the right. Never a building, never a product shot.
   Faces carry the "you're hiring a human" message the copy claims.
2. **A chip above every H2.** 8/8. Small pill or bracketed label naming the
   section before the headline states it.
3. **Two-line uppercase H2s**, heavy weight, tight leading. 7/8.
4. **The phone number three times minimum** — header, hero, final CTA. 8/8.
   Often a fourth time in the utility bar.
5. **One FAQ item pre-opened**, in the brand colour with reversed text. 6/8.
   Shows the accordion is interactive without requiring a click.
6. **Read More on every service card.** 6/8. Signals depth behind the card.
7. **Google review marks, not just stars.** 8/8. The logo is the proof.
8. **Numbers stated as facts** — years, review count, licence, response window.
   6/8. Every one is a claim the client must supply and verify.

## 3. Section-level structure worth copying exactly

**Why-choose (8/8, the most consistent section in the set)**
Photo one side; on the other a chip, a two-line H2, three-to-six tick items with
bold lead + sentence, and a filled CTA. Two small badge cards float over or
below the photo (`FAST REPAIRS`, `24/7 SUPPORT`). Skyline and HighPoint put a
`25+ Years` / `60+ TRUSTED` badge in the photo corner.

**Services (8/8)**
Three-across photo cards. Photo top, then either a coloured tag ribbon
(Skyline) or a plain bold title, a one-line description, and `Read More →`.
Six cards is the mode; four when the trade has fewer categories. Carousel
arrows top-right in 5/8 — a grid reads fine and avoids a JS dependency.

**Service areas (8/8)**
Two treatments: chips over a map (Skyline, Arctic Flow, Chicago), or a dark card
overlapping the map (HighPoint, NYC). The second reads as more designed. SafeCut
and Chicago add per-county cards with individual phone numbers — strong for
local SEO, and it needs the client to actually have those numbers.

**Final CTA (8/8)**
Dark or photographic band, two-line uppercase headline, filled CTA plus phone,
person or van on the right. Never a bare colour block with centred text.

## 4. What Lawnx does differently

Worth keeping as a second profile for landscaping and turf, where the work is
aspirational rather than urgent:

- Rounded, softer, lighter. Generous white space, no hard dark bands.
- Hero is a full-bleed photo with centred copy and a social-proof badge above it.
- Icon-card row directly under the hero instead of a form.
- Circular progress dial and a play-button badge over imagery.
- Blog section carries real weight.
- Email-capture strip rather than a phone-led CTA.

The urgent trades (plumbing, HVAC, roofing, electrical, tree) lead with a phone
number and a form. The considered trades (landscaping, turf) lead with imagery
and a gallery. That distinction should drive the preset, not the palette.

## 5. Gaps to close

**New blocks:** `badges.strip` (5/8), `areas.cards` (2/8), `blog.cards` (2/8).

**Existing blocks to amend:** `services.cards` needs a Read-More link;
`faq.split` and `faq.accordion` need a pre-opened item; `footer.simple` needs an
optional map column and badge row.
