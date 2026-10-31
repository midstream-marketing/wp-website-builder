# Elementor Forge — build status

What exists, what changed, and what is still unverified.

---

## 1. What the system is

A deterministic compiler. Client facts and copy go in as JSON; validated,
importable Elementor Template Kits come out. No model writes Elementor JSON —
agents produce intake and copy, Python produces the templates. That separation
is why the output imports cleanly with zero stylesheets to reconcile.

```
intake.json  ─┐
copy.json    ─┼─> planner ─> IR ─> compiler ─> validator ─> kit.zip
preset.json  ─┘                                    │
profile.json ─┘                                    └─> capture.py ─> screenshots
```

| Module | Lines | Role |
|---|---|---|
| `blocks.py` | 1795 | 38 block factories — the only place JSON is authored |
| `planner.py` | 750 | intake + copy → IR, three layout variants, 12 page types |
| `tokens.py` | 265 | brand → Global Kit; all colour and type lives here |
| `validator.py` | 223 | 12 rules, build gate |
| `core.py` | 170 | value shapes, id generation, registry access |
| `kit.py` | 129 | manifest + zip packaging |
| `compiler.py` | 96 | IR → Elementor documents |
| `forge.py` | 84 | CLI |
| **`build_registry_php.py`** | 193 | **new** — mines the registry from Elementor's source |
| **`capture.py`** | 81 | **new** — renders a live site and screenshots it |
| **`analyse_reference.py`** | 146 | **new** — reference site/screenshot → design profile |

---

## 2. How far it has moved

| | Start | Now |
|---|---|---|
| Block factories | 12 | **38** |
| Registry widgets | 21 | **207** (47 core, 106 Pro, 54 addon) |
| Registry control entries | ~1,900 | **47,775** |
| Registry source | 2 sample kits, mined 2024 | **Elementor's own PHP source** |
| Validator rules | 10 | **12** |
| Page types | 8 | 12 |
| Layout variants | 1 | 3 (`default`, `feature`, `impact`) |
| Trade presets | 0 | **7** |
| Rendering / visual QA | none | **Playwright, 3 breakpoints** |
| Reference matching | by hand, in Python | **measured extraction** |
| Kit size | 42 KB, no previews | **1.07 MB with 21 previews** |

### Registry: the biggest single unlock

The original registry was mined from a personal-portfolio kit and a news-magazine
kit, so it only knew controls those two designers happened to touch. It was
missing `image-carousel`, `testimonial-carousel`, `star-rating`, `slides`,
`flip-box`, `progress`, `shortcode`, `html` — **all core or Pro**. They were
never forbidden by the contract; they were invisible to it.

Mining Elementor's source instead required resolving three things a flat file
scan gets wrong:

- `Widget_Button` declares none of its own controls — they live in `Button_Trait`
- `theme-site-logo` extends `Widget_Image`
- Elementor reuses class names across roles: `Site_Logo` is both a dynamic tag
  and a Theme Builder widget, and the tag's ancestry was poisoning the widget's

---

## 3. Bugs found — and how each was found

Every one of these was shipping silently before it was caught.

| Bug | Impact | Found by |
|---|---|---|
| **30 of 33 flex rows overflowed** | heroes stacked instead of splitting; 3-up grids rendered 2-up; footers broke apart | arithmetic audit |
| **Image URLs with query strings never imported** | every image in all 3 kits replaced by Elementor's placeholder | **rendering** |
| **UTF-8 read as cp1252** | every em-dash became `â€”` in 3 delivered kits | inspecting stored bytes |
| **White label on lime button** | 2.3:1, effectively unreadable | contrast audit |
| **Ghost button invisible on dark hero** | button rendered as an empty outline | **rendering** |
| **Dividers black-on-black** | 1.00:1, literally invisible, footer + pricing card | contrast audit |
| **Header overlap sliced the nav in half** | every page, every kit | **rendering** |
| **Chips stretched full width** | pills spanning the whole column | **rendering** |
| **Brand colour unreadable on dark grounds** | 2.97:1 icons | contrast audit |
| **Manifest listed 0 images** | extension-only detection missed CDN URLs | manifest inspection |
| **My own contrast auditor was wrong twice** | scored labels against the wrong background; treated `#FFFFFF00` as opaque white | cross-checking a "pass" |

Four of the eleven were only findable by looking at a rendered page. That is the
argument for `capture.py` in one line.

### Rules added to prevent recurrence

- **V11** — a flex row's children plus gaps must fit one line. Verified it fires
  on every previously-broken shape.
- **V12** — media URLs must carry a real image extension and no query string.
  Both historical import failures now blocked at build time.

---

## 4. Derived design tokens

Colour is computed, not chosen. `tokens.py` derives four tokens per brand so a
palette cannot ship unreadable:

| Token | Derivation | Why |
|---|---|---|
| `on_accent` / `on_primary` | whichever of dark/white wins on the fill | lime takes a black label at 11:1; navy takes white at 14:1 |
| `ink_primary` | darken brand until ≥4.5:1 on the darkest light surface | brand colours are picked to look right, not to be read |
| `brand_on_dark` | lighten brand until ≥4.5:1 on the dark ground | a navy brand becomes `#728190`; lime and blue pass unchanged |
| `rule_dark` | white at 16% | a dark rule on a dark panel is invisible |

Verified across three unrelated palettes — lime/black, navy/yellow, blue/navy —
all pass with no hand-tuning.

---

## 5. Reference matching

`analyse_reference.py` measures what a reference states, tested against a render
whose palette was already known:

| Input | Accuracy |
|---|---|
| **Website URL** | Exact. Stylesheet states every token. Pulled Waterloo's full palette, Raleway+Inter, radii and padding in one pass. |
| **Screenshot** | Dark ground `#0E1A2B` → `#0D192A` (error 3). Accent `#1268A8` → `#1267AB` (error 4). **Blind to colours with little screen area** — a sparingly-used brand colour was missed entirely. |

It also detects whether the reference uses clip-paths, gradient overlays or
marquee keyframes, which tells the build which techniques to reach for.

`references/COMPOSITION.md` holds the judgement half: the canonical 19-section
order derived from 8 agency references, with frequencies, plus the eight details
doing the heavy lifting.

---

## 6. Trade presets

Seven trades: `plumber`, `electrician`, `roofing`, `tree-surgeon`, `landscaping`,
`turf`, `general-contractor`. Each carries default services, trust items,
process steps, FAQs, a photo brief, palette and font hints, and image search
terms — all overridable per client.

Composition analysis produced one structural finding worth keeping: **urgent
trades** (plumbing, HVAC, roofing, electrical, tree) lead with a phone number
and a form; **considered trades** (landscaping, turf) lead with imagery and a
gallery. That should drive the preset, not the palette.

---

## 7. Kits built

| Client | Templates | Kit | Notes |
|---|---|---|---|
| NextGen Plumbing | 10 | 1.07 MB | 7 pages, Trustindex slot, rendered and captured |
| Primetime Turf | 12 | 60 KB | 11 pages, Waterloo-matched styling |
| South Jersey Install | 6 | 35 KB | 3 pages, built to a client PDF brief |

All build `--strict` with 0 errors. Contrast: 0 failures except one decorative
hairline in Primetime.

---

## 8. Honest status

**Verified by rendering:** the header overlap, invisible button, stretched chips
and missing images were all seen on screen and diagnosed from the real page.

**Not yet verified:** every fix made after the last capture — the image URL fix,
the ghost-button variant, chip widths, nav width, scrims, marquee, hover lift,
and all 54 addon widgets. The kit rebuilds cleanly and the audits pass, but
nothing since that capture has been looked at.

**Next:** re-import and re-capture before adding anything further. Then amend the
blocks against `COMPOSITION.md` — hero person-photo, `Read More` on service
cards, `nested-accordion` for the pre-opened FAQ, and swap in `ha-step-flow`,
`ha-image-compare`, `ha-news-ticker`, `ha-logo-grid`.

**Known ceiling:** section composition still needs a human to read the reference.
Extraction handles palette, type, spacing and effects; it cannot infer section
order, and a reference using a section the library lacks still needs a new
factory.
