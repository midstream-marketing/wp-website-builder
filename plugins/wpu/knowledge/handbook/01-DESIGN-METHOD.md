# 01 — Design method

The one rule, the taxonomy that operationalises it, the spec format, the gate,
and what to do when there is no reference at all.

---

## The one rule

> **Match the DEVICES, not the section order.**

Section order is the cheap half and it gets done by accident. A design looks
like itself because of its **devices**: chips floating over a photo, labelled
tinted cards, a bento grid with one large tile, circular arrow buttons, a serif
display face, oval image masks, per-card tints, an inset rounded dark band.

Reproduce the section order without the devices and you have built a different
website with the same table of contents.

### The mechanism to interrupt

With a large block library, the natural move is: read the reference's sections,
retrieve the nearest existing block for each. **That is retrieval, not
matching**, and it silently caps output at whatever the library already had. The
reference gets quietly reduced and nothing reports it.

Three traps, all observed in production:

1. **Nearest-block substitution.** The reference's "how it works" is three
   tinted cards each with a LABEL, a heading, an image and a caption. Shipping
   numbered circles on a dark band is not that section — it is a different
   component occupying the same slot.
2. **Documenting the gap instead of closing it.** A "divergences" section in the
   README converts a design failure into prose.
3. **Honesty constraints used as cover.** A content refusal never justifies a
   structural one. See `00-SOUL.md` §2.

### The failure log that produced this rule

| Build | Supplied | Shipped | Verdict |
|---|---|---|---|
| AirFusion | ameriserve.com, "perfect example", different colours | generic trade page set | *"the design is nowhere close to it"* |
| Falis | imperiare.com + a 45-page written spec | reference devices the spec bans | resolved: written brief wins |
| MedLou | Jelly Health + Forma Health, "follow these examples" | right palette, right serif, generic block rhythm — no overlay chips, no labelled cards, no bento, no arrow buttons | *"I don't think you have followed either of the design screenshot"* |

The common thread is not carelessness. **Section order was matched, devices
were not, and nothing in the pipeline measured the difference.**

---

## 1. Which mode are you in?

Decide before restyling, and say which mode you are working in.

| Wording | Mode | Latitude |
|---|---|---|
| "design it similar to X", "client wants something like X", a supplied mockup to match | **match** | X is the spec. Layout, section order, proportions, type and colour treatment, closely. Do not substitute your own judgement. |
| "use X as a reference", "inspired by" | **reference** | Keep the spirit and structure; improve on it. |
| "perfect example… but different colours" | **match, narrowed** | Everything not excluded is still the spec. Match the layout *harder*. |
| no reference at all | **specified** | Your judgement — but write it down first. See §6. |

**Two references that contradict each other:** split by **layer**, not by
compromise. Wasatch supplied big-d.com (dark, industrial, corporate) and
finegc.com (light, green, residential), with a written scope banning the
corporate/industrial register. Resolution: big-d supplied the *structural
devices* (hero-straddling CTA cards, heading+arrow rows, arrow-prefixed index,
figures on rules, caps micro-labels); finegc supplied the *register* (light warm
ground, unequal photo bento, circular arrow buttons, numbered area rail).

**Structural devices are palette-independent — that is what makes the split
work.** It is the general technique for reconciling references that fight.

### Parse the reference; do not guess it

Most agency sites are built on a known builder, so structure is *readable*:

```bash
# Elementor sites expose their component tree
curl -s https://reference.com | grep -o 'data-widget_type="[^"]*"'
```

That yields the real section rhythm, the widget mix, and the heading-to-prose
ratio. Ameriserve turned out to be **49 headings to 4 text blocks** — the single
fact that most explained why a prose-led build felt wrong. Do this **before**
composing, not after the client pushes back.

Write the section-by-section mapping into the handoff document, so every
divergence is deliberate and reviewable.

---

## 2. The device taxonomy

Answer every one of these **in writing**. "It has a hero, a services grid and a
CTA" is a section list, not a device inventory.

### Ground system
- How many distinct section grounds — white, one tint, two tints, a dark band?
- Does the **page itself** sit on a tint with white cards on top? (This alone
  changes the whole read and costs nothing to reproduce.)
- Are dark bands full-bleed, or **inset rounded blocks** with page margin
  visible either side? These are different design systems, not a variant.

### Card anatomy — the highest-value question
- Does a card carry a **label/eyebrow above the title**? In what case?
- Where is the image: top-edge, inset with padding, right-hand side, none?
- Corner radius — small (4–8), medium (12–16), large (20–28), pill?
- Border, shadow, both, neither?
- **Do cards differ from each other** (per-card tints) or are they uniform?

### Overlay elements
- Chips, pills or mini-cards **floating on top of photos**?
- Containing what — an avatar, an icon, a stat, a status?
- Usually the single most identity-defining device in a modern shot, and the one
  most often dropped.

### Button vocabulary
- Pill, rounded-rect or square? Filled / outline / ghost, and which is primary?
- Is there a **circular icon-only arrow button** — card corner, beside a
  heading, as carousel controls?
- How many button styles exist in total? (Answer should usually be two.)

### Type system
- **Serif or sans for display?** A serif display over a sans body is the most
  common reason a shot reads "premium" rather than "template".
- Display size relative to body — 3×, 5×, 8×?
- Sentence case, Title Case or ALL CAPS for headings and eyebrows?
- Mixed weights inside one heading?

### Grid rhythm
- Symmetric N-up, or an **asymmetric bento** with one large tile?
- Does anything overlap, offset or break the grid deliberately?
- Carousel with visible arrows, or a static grid?

### Media treatment
- Rounded rectangles, ovals/pills, circles, hexagons, full-bleed?
- Images inline *inside a sentence*?
- Photos masked, or sitting in tinted frames?
- Does anything **bleed off the page edge**?

### Proof devices
- Star rating with a review count? Press logo strip? Counter row? Named quotes
  with avatars?
- **For each: does the client actually have this?** If not it becomes a truthful
  substitute and is recorded as one — never silently dropped.

### Micro-detail
- Status pills — "In Stock", "Rx", "Shipped"?
- Dividers, rules, dotted rails?
- Icon style — line, solid, duotone, in a circle?

---

## 3. `design-spec.json` — make it machine-checkable

A checklist nobody runs is a checklist nobody follows.

```json
{
  "reference": "reference/jelly-health.png",
  "mode": "match",
  "notes": "Client said 'follow these examples' -> match, not inspiration.",
  "ground_system": "White primary, #F4F7F9 alternate, near-black navy as a full-bleed SPOTLIGHT used at most twice per page.",
  "type_system": "Geometric sans display over Inter body. ALL-CAPS eyebrows in the accent.",
  "button_vocabulary": "Two: filled accent primary, hairline ghost secondary. No third style anywhere.",
  "card_anatomy": "14px radius, hairline border, white fill. Featured card lifted with the brand colour, not a shadow.",
  "devices": [
    {
      "id": "hero-overlay-chips",
      "device": "Chip cards floating over the hero provider photo",
      "satisfied_by": ["hero.chips"],
      "status": "required"
    },
    {
      "id": "labelled-step-cards",
      "device": "Three tinted cards: LABEL, title, image, caption",
      "satisfied_by": ["steps.labeled"],
      "status": "required",
      "never": ["process.numbered3", "process.numbered"],
      "never_reason": "Numbered circles on a dark band is a different component in the same slot — the exact substitution that failed review."
    },
    {
      "id": "press-logos",
      "device": "Press logo strip",
      "status": "substituted",
      "satisfied_by": ["trust.bar"],
      "substitution_reason": "Client has no press coverage; inventing it would be fabrication."
    }
  ]
}
```

`status` values:

| value | meaning |
|---|---|
| `required` | must appear; the build fails without it |
| `substituted` | deliberately replaced for a truth reason; must still appear as its substitute |
| `deferred` | agreed to build later; recorded so it is not forgotten, with the trigger |

### `never` is the important field

Put the tempting fallback in it **the moment you notice yourself reaching for
it**. Then the gate fails if it ever appears.

**A `never` entry is evaluated GLOBALLY across the whole build, not scoped to
its device — and that is correct**, because a block that is merely discouraged
gets reached for elsewhere. Two consequences:

- On DualCore, the first `--strict`-green build still failed the gate:
  `store.split` had leaked into four inner pages while the spec banned it.
- On Live Fatima, a `never` entry was written for a block that had a legitimate
  use on another page in the same kit; the gate correctly rejected it. **Only
  list a block that has no honest use anywhere in the build.** Otherwise express
  the constraint as a `_why` note on the device.

### Give a replacement factory the displaced block's prop signature

When you write a new component to displace a banned one, match the old prop
shape. The swap becomes one word per call site instead of a rewrite. That is the
difference between closing a fidelity gap and arguing with the gate.

---

## 4. Build the missing components — never substitute

> If a design cannot be expressed, **add a factory**. Do not loosen the
> validator, do not add a CSS escape hatch, do not reach for a third-party
> widget.

Devices people wrongly assume need custom CSS, and the legal controls that do
them (Elementor names; the *principle* is what ports):

| Device | Controls |
|---|---|
| Chips floating over a photo | container `_position: absolute`, `_offset_x/_offset_y`, `_offset_orientation_h/v`, `_z_index` |
| Circular arrow button | `border_radius: 999`, fixed `width` + `min_height`, centre both flex axes |
| Per-card tints | `background_background: classic` + a per-card global colour ref |
| Bento / asymmetric grid | unequal track ratios + `_flex_grow` |
| Oval / pill image mask | `image_border_radius` in **%** |
| Overlap between sections | negative `margin` — literal geometry, allowed |
| Card strip straddling two sections | transparent section, negative top margin, `z_index: 5`, zero padding |
| Inset rounded dark band | filled container, `border_radius: 20`, **`overflow: hidden`**, inside a normally padded boxed section — the overflow is what lets a photo column reach the panel edge without square corners |
| Photo bleeding off the page edge | section `content_width: full` with zero side padding; the *copy* column re-establishes the page margin with its own asymmetric padding. Doing it on a boxed section is the mistake |
| Corner arc / ring line-work | oversized containers, `border_radius: 999`, 1px border, pushed off-canvas by absolute offsets, inside a section with `overflow: hidden` — the clipping turns circles into corner arcs. 14 rings on one homepage; recolours with the palette and never ships as a fuzzy JPEG |
| Mixed-weight display heading | keep `**markers**` in the copy file and convert to `<b>` at render — a copy edit then cannot silently drop the device |

**Client-specific families get their own module**, registered by one import
line. Do not bend a shared component with more flags.

**Dark grounds need dark-native components.** A `bg="dark"` flag does not work
if the existing blocks resolve headings through a brand tone and body through a
light text token — a dark ground renders invisible copy. This was learned twice
(AirFusion's `blocks_ameri.py`, DualCore's `dc.*` vs the dark `store.*`). If the
reference's whole register is opposite to the existing family, the answer is a
new family, not a flag.

---

## 5. The gate

```bash
python tools/check_fidelity.py <spec.json> --ir <ir.json>
```

Reads the spec and what was actually composed. Exits 1 when a required device
has no satisfying component, or when a `never` component appears anywhere.

**Treat a fidelity failure exactly like a compile error: the build is not
finished** — not "finished with notes."

A directory with no `design-spec.json` also exits 1, so the gate cannot be
passed by skipping the inventory.

**The gate reads component *names*.** A device rendered inside a shared helper
function reads as MISSING even though it is on the page. The fix is naming the
components that actually emit it — **after verifying in the compiled output** —
never loosening the gate.

**Visual comparison, whenever a render is possible:** put the render beside the
reference at the same width and score device by device.

```
devices required : 12
devices present  : 12
visually matched : 10   ->  83%
```

Under 80% is a rebuild, not a note. The honest limitation: most builds cannot be
rendered before handover, which is *why* the inventory has to be written first
and has to be specific. It is the only artefact standing between the reference
and a library-shaped approximation of it.

---

## 6. When there is no reference: the logo is the brief

Two builds had no reference site, screenshot or comp. Both worked, and the
method is reusable.

**Write the spec in `mode: "specified"`.** It *states* the device system rather
than extracting one. That keeps the gate meaningful and makes a later change a
deliberate revision against a written spec instead of drift.

**Then read the logo for actual rules, not adjectives.**

- *Magic Renovations:* black + gold gradient + classical Roman serif + a
  five-star roofline mark. Three rules fell out: black is a **spotlight, not a
  ground** (the mark is ~90% black on white, so a dark site would make gold text
  the norm and gold reads cheap in quantity); gold is only ever a rule, a
  numeral or a button; every section opens with a caps eyebrow over a short gold
  rule, which becomes the signature. Type: Cinzel — the closest Google face to
  the wordmark.
- *PeptideLaunch:* a rising chain of four nodes, three navy outlines and **one
  solid teal-to-cyan node**. That 1-in-4 ratio became the palette rule — the
  accent fills a button, a numeral, a tick, one featured border, and never a
  section ground. The dashed trajectory arc gave a direction of travel, so
  numbered devices run left-to-right and nothing is a centred stack.

**Look at every supplied brand asset before concluding there is no reference.**
Metroline supplied no competitor URL, but the brand *banner* had already decided
four things: near-black ground, desaturated close-in photography, thin
concentric corner arcs, and a red base bar.

---

## 7. Palette and type derivation

- **The client's logo beats the reference's palette.** Consistently, across
  Primetime Turf, OD Electric, Classic Comfort, Alpha Wolf, DualCore, AirFusion.
  Say the conflict out loud before restyling.
- **A logo gradient cannot become a flat token.** It survives as the neutral
  border/muted pair, or as a two-stop gradient on the one control that accepts
  one (a button background). Do not average it into a solid.
- **Type can be kept from the reference even when the palette is rejected.**
  DualCore kept Montserrat + Inter because the client rejected the colour, not
  the typography. Confirm faces from the reference's own stylesheet — a scrape's
  colour extraction returning framework defaults is a signal to discard the
  colour half and keep the type half.
- **Derive the readable variants; do not pick them.** A brand colour is chosen
  to look right, not to be readable. Lime on white is 2.4:1. Compute:
  `ink_primary` (darkened until ≥4.5:1 on white), `brand_on_dark` (lightened
  until ≥4.5:1 on the dark ground), `on_accent` / `on_primary` (whichever of
  black/white passes on that fill). Allow a per-client override behind a 4.5:1
  guard — lifting a near-black navy or a near-black bronze mathematically yields
  grey, which is correct arithmetic and wrong branding.
- **A white-only logo forces the palette open.** A pure-white wordmark on
  transparency is invisible on any light ground, so a dark header is the only
  ground the existing asset works on. That is a constraint, not a style choice.
- **A dark logo on white needs a reversed asset for a dark header or footer.**
  A `brightness(0) invert(1)` filter whitens every opaque pixel — right for a
  transparent PNG, and it renders as a **solid white block** for a logo exported
  flat on its own background card. Ask for the transparent asset.
- **Check whether the live site already runs your design tokens.** On an
  extension build, the dev site's global colours matched the client's own
  intake exactly, token ids included — so new pages inherited the live palette
  with no seam and no re-tinting. One check, worth doing on every extension.
