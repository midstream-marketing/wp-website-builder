# Design Fidelity — method

## 1. The device taxonomy

Go through the reference and answer every one of these in writing. This is the
step that was being skipped; "it has a hero, a services grid and a CTA" is a
section list, not a device inventory.

### Ground system
- How many distinct section grounds? White, one tint, two tints, a dark band?
- Does the **page itself** sit on a tint with white cards on top? (Jelly does —
  this alone changes the whole read and costs nothing to reproduce.)
- Are dark bands full-bleed, or inset rounded blocks?

### Card anatomy — the highest-value question
- Does a card carry a **label/eyebrow above the title**? In what case?
- Where is the image: top-edge, inset with padding, right-hand side, none?
- Corner radius — small (4–8), medium (12–16), large (20–28), pill?
- Border, shadow, both, neither?
- **Do cards differ from each other** (per-card tints) or are they uniform?

### Overlay elements
- Are there chips, pills or mini-cards **floating on top of photos**?
- What do they contain — an avatar, an icon, a stat, a status?
- This is usually the single most identity-defining device in a modern shot,
  and it is the one most often dropped.

### Button vocabulary
- Pill, rounded-rect or square?
- Is there a **circular icon-only arrow button**? Where — card corner, beside a
  heading, as carousel controls?
- Filled / outline / ghost, and which is primary?

### Type system
- **Serif or sans for display?** A serif display over a sans body is the most
  common reason a shot reads "premium" rather than "template".
- Display size relative to body — 3×, 5×, 8×?
- Sentence case, Title Case or ALL CAPS for headings and eyebrows?
- Mixed weights inside one heading?

### Grid rhythm
- Symmetric N-up grid, or an **asymmetric bento** with one large tile?
- Does anything overlap, offset or break the grid deliberately?
- Carousel with visible arrows, or a static grid?

### Media treatment
- Rounded rectangles, ovals/pills, circles, hexagons, full-bleed?
- Images inline *inside a sentence*? (Forma does this — very distinctive.)
- Are photos masked, or sitting in tinted frames?

### Proof devices
- Star rating with a review count?
- Press logo strip?
- Counter row?
- Named quotes with avatars?

*(For each: does the client actually have this? If not it becomes a truthful
substitute — see SKILL.md — and gets recorded as such, not silently dropped.)*

### Micro-detail
- Status pills — "In Stock", "Rx", "Shipped"?
- Dividers, rules, dotted rails?
- Icon style — line, solid, duotone, in a circle?

---

## 2. Writing `design-spec.json`

Machine-checkable, because a checklist nobody runs is a checklist nobody
follows. Minimum shape:

```json
{
  "reference": "reference/jelly-health.png",
  "mode": "match",
  "notes": "Client said 'follow these examples' -> match, not inspiration.",
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
      "never_reason": "Numbered circles on a dark band is a different component in the same slot — this is the exact substitution that failed review."
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

`status` is one of:

| value | meaning |
|---|---|
| `required` | must appear; build fails without it |
| `substituted` | deliberately replaced for a truth reason; must still appear as its substitute |
| `deferred` | agreed with the client to build later; recorded so it is not forgotten |

`never` is the important field. Put the tempting fallback in it the moment you
notice yourself reaching for it.

---

## 3. Building the missing factories

The Elementor contract already governs this and it is not optional:

> If a design can't be expressed, add a factory to `blocks.py`. Do not loosen
> the validator, do not add a CSS escape hatch, do not reach for a third-party
> widget. Core + Elementor Pro only.

Client-specific families go in their own module — `blocks_fatima.py`,
`blocks_ameri.py` — registered by one import line at the foot of `blocks.py`.

Devices people wrongly assume are impossible without CSS, and the legal
controls that do them:

| Device | Controls (all in the registry) |
|---|---|
| Chips floating over a photo | container `_position: absolute`, `_offset_x`, `_offset_y`, `_offset_orientation_h/v`, `_z_index` |
| Circular arrow button | `border_radius: 999`, fixed `width` + `min_height`, `flex_justify_content/align_items: center` |
| Per-card tints | `background_background: classic` + `__globals__.background_color` per card |
| Bento / asymmetric grid | `_tracks([...])` with unequal ratios, plus `_flex_grow` |
| Oval / pill image mask | `image_border_radius` in `%` |
| Overlap between sections | negative `margin` — literal geometry, allowed |

If a control is not in `registry/elementor-registry.json`, it does not exist.
Check before writing, never after.

---

## 4. Verification

**Structural gate — always:**

```bash
python tools/check_fidelity.py clients/<slug>
```

**Visual comparison — whenever a render is possible:** import the kit, render
the page, and put the screenshot beside the reference at the same width. Score
device by device from `design-spec.json`:

```
devices required : 12
devices present  : 12
visually matched : 10   ->  83%
```

Under 80% is a rebuild, not a note in the README. Record the score.

**The honest limitation:** a kit cannot be rendered without a WordPress import,
so on most builds the structural gate is all that runs before handover. That is
exactly why the device inventory has to be written *first* and has to be
specific — it is the only artefact standing between the reference and a
library-shaped approximation of it.

---

## 5. Failure log

Kept so the pattern stays visible.

| Build | What was sent | What shipped | Verdict |
|---|---|---|---|
| AirFusion | ameriserve.com, "perfect example", different colours | generic trade page set | "the design is nowhere close to it" |
| Falis | imperiare.com + a 45-page written spec | reference devices banned by the spec | resolved: written brief wins |
| MedLou | Jelly Health + Forma Health, "follow these examples" | correct palette and serif, generic block rhythm — no overlay chips, no labelled cards, no bento, no arrow buttons | "I don't think you have followed either of the design screenshot" |

The common thread is not carelessness about the brief. It is that **section
order was matched and devices were not**, and that nothing in the pipeline
measured the difference. Everything the forge measures, it gets right;
everything it does not measure drifts. This skill exists to make design a
measured thing.
