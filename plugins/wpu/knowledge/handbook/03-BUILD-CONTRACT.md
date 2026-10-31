# 03 — The build contract

Elementor-specific in its details. Read it for the **shape of the idea**: a
generator that emits a proprietary format needs a written contract, a mined
registry of what is legal, and a validator that fails the build. Everything else
here is a worked example of that.

Derived from two shipped commercial Envato kits — Saira (Elementor 3.24.4) and
Scoop (3.34.1, Pro-only) — 39 templates, 515 containers, 765 widgets, **0 bytes
of CSS**.

---

## 1. Non-negotiables

1. **No CSS.** Never emit `custom_css`, `_custom_css` or `_css_classes`. Both
   reference kits contain zero bytes of either. If a design cannot be expressed
   in control values, **the component is wrong, not the platform**.
2. **No `section` / `column`.** Containers only. Both kits are 100% container.
3. **Core + Pro widgets only.** Any widget outside the registry with
   `tier != "third-party"` is a build failure, not a warning.
4. **The model never writes the output JSON.** Agents emit IR; the compiler
   emits JSON. This is the rule that makes everything else enforceable.
5. **Never invent a control key.** Elementor silently drops unknown keys, which
   presents as "the styling didn't apply" rather than as an error.

**If a design cannot be expressed: add a factory.** Do not loosen the validator,
do not add a CSS escape hatch, do not reach for a third-party widget.

---

## 2. The three settings channels

Every element's `settings` carries up to three parallel channels, and getting
the boundary right is the whole job. Measured across both kits: **2,568 global
refs vs 15,535 literals.**

```jsonc
"settings": {
  "padding": { "unit": "px", "top": "32", … },        // 1. literal  — geometry
  "__globals__": {                                     // 2. globals — theme
    "title_color": "globals/colors?id=primary"
  },
  "__dynamic__": {                                     // 3. dynamic — WP data
    "background_image": "[elementor-tag id=\"6f4e2b6\" name=\"post-featured-image\" settings=\"%7B%7D\"]"
  }
}
```

| Property class | Channel |
|---|---|
| colour, typography | `__globals__` — **always** |
| padding, margin, gap, width, min-height, radius, flex-*, position, z-index, filters | literal — **always** |
| content on `page` documents | literal |
| content on `loop-item` / `archive` / `single-post` documents | `__dynamic__` |

Globalising geometry breaks maintainability. Hardcoding colour breaks
re-skinning. There is no third option.

Dynamic tag encoding:
`[elementor-tag id="<7-8 hex>" name="<tag-name>" settings="<urlencoded JSON>"]`,
with `%7B%7D` as the empty case. **Always set `fallback`** — it is what renders
in the editor preview and in a QA screenshot before real content exists.

---

## 3. Document types

The output artifact is a **site**, not a page set.

| `type` | `metadata.template_type` | Notes |
|---|---|---|
| `page` | `single-page` | literal copy |
| `section` | `global-styles` | the Kit — exactly one per site, imports first |
| `header` / `footer` | `section-header` / `section-footer` | Theme Builder |
| `single-post` | `single-post` | dynamic |
| `archive` | `archive-blog` / `archive-category` / `archive-search` | dynamic |
| `loop-item` | `section-loop` | dynamic, referenced by `loop-grid` |
| `error-404` | `single-404` | |

**One archive document serves every archive.** `theme-archive-title` and
`archive-posts` inherit whatever query WordPress resolved, so
`/category/feast-days/` renders itself correctly. Building a page per category
is six near-duplicates and is the wrong shape.

Display conditions live in post meta, not in the template JSON — but emit them
in the IR (`conditions: ["include/archive"]`) so the importer can set them and
the template arrives already assigned. Note the compiler writes them out under
`elementor_pro_conditions`, which is not the key you would grep for first.

---

## 4. Portability hazards

`loop-grid`, `loop-carousel` and `template` widgets reference other templates by
**raw WordPress post ID**. Scoop ships 19 of these pointing at IDs on the
author's server. The compiler must emit **symbolic refs** (`"@loop:hero-big"`)
and resolve them at import time. Coerce to string — Scoop stores them
inconsistently as both `"1157"` and `1157`.

Import order: loop items first, capture the new IDs, rewrite the refs, pages
last.

---

## 5. Design tokens

`global.json` → `page_settings`: 4 system colours + N custom, 4 system
typography steps + N custom named steps.

- System `_id`s are the fixed strings `primary` / `secondary` / `text` /
  `accent`. **Never invent others.**
- Custom `_id`s are stable 7-char slugs, so regenerating a site does not
  invalidate previously exported templates. **Do not renumber them** — every
  shipped template references them.
- Line-heights in `em`, font sizes in `px`, 1–2 font families maximum.
- Opacity baked into 8-digit hex (`#02081752`), never a separate control.
- Kit-level settings worth setting: `container_width` (1240), `container_padding`,
  `space_between_widgets`, `paragraph_spacing`, `viewport_md: 768`,
  `viewport_lg: 1025`.

---

## 6. Value shapes

| Shape | Form |
|---|---|
| slider | `{ "unit": "px\|%\|em\|vh\|rem", "size": 40, "sizes": [] }` |
| dimensions | `{ "unit": "px", "top": "32", …, "isLinked": true }` |
| media | `{ "url": "…", "id": "", "size": "", "alt": "…", "source": "library" }` |

**Dimension values are strings; slider `size` is a number.** Mixing them is
silently dropped on render.

Media URLs are stripped of their query string: WordPress derives the filename
with `basename()`, so `photo.jpeg?w=1600` yields an invalid filename, the
download is abandoned, and Elementor silently substitutes a placeholder.
Measured across both kits: 143 media URLs, zero query strings.

---

## 7. Responsive

Only two breakpoints are used across all 39 reference templates: `_tablet` and
`_mobile` (1,589 overrides). Do **not** emit `_widescreen`, `_laptop`,
`_tablet_extra` or `_mobile_extra` — they need custom breakpoints enabled in
Site Settings and no-op otherwise.

Emit `_mobile` for every type size and every container padding. Emit `_tablet`
only where the layout actually changes.

---

## 8. The validator rules

Every one earned from a real defect.

| # | Rule | Evidence |
|---|---|---|
| V1 | Every colour global ref resolves in `global.json` | Saira ships 3 dangling refs |
| V2 | Every typography global ref resolves | clean in both |
| V3 | No widget type outside the allowed registry | Saira: 18% third-party |
| V4 | No `custom_css` / `_css_classes` anywhere | both clean |
| V5 | Every element `id` unique in the document, 7–8 lowercase hex | Saira mixes 5/6/7/8 |
| V6 | Every control key exists in the registry for that widget | catches hallucination |
| V7 | Every `template_id` is symbolic, never a raw integer | Scoop: 19 raw IDs |
| V8 | Every image has non-empty `alt` | Saira: 84/84 empty |
| V9 | Dimension values are strings; slider `size` numeric | — |
| V10 | Every dynamic tag name is in the registry | — |
| V11 | A flex row's children + gaps fit one line, at desktop **and** tablet, measured against the row's real width after nesting and padding | 63 desktop + 313 tablet overflows across 11 shipped kits |
| V12 | Media URLs have no query string and carry an image extension | — |
| V13 | Every **container** setting is a real container control | 103 `max_width` + 13 `height` doing nothing |

V8 is worth stressing: both commercial kits ship with zero alt text. Filling it
from the copy context is free differentiation.

V13 exists because V6 only validated widgets. **A whole class of settings was
silently ignored for months and every build was green.**

---

## 9. The registry is the source of truth

If a control is not in the registry, it does not exist. Check **before** writing,
never after.

```bash
python -c "import json,io;print('max_width' in json.load(io.open('registry/elementor-registry.json',encoding='utf-8'))['widgets']['container']['controls'])"
```

Two known mining gaps, and how they were closed:

- **Per-skin controls are invisible to a PHP scrape.** The `posts` widget
  registers controls per skin, so only the skin-agnostic base was captured;
  every styled Posts widget silently failed V6 and fell back to default card
  styling. Fixed by mining **76 controls from the shipped Scoop kit's 32 real
  Posts widgets** — traceable evidence, which is what an additions file demands.
  (Note `cards_card_bg_color`, not the `cards_bg_color` you would guess.)
- **WooCommerce dynamic tags are absent.** The registry holds 7 generic tags —
  no product price, SKU or batch tag. So a custom product `loop-item` **cannot
  be verified before shipping**, and guessing produces a grid that **imports
  empty** — the worst failure mode, because it reads as the client's data entry
  rather than as a template bug. Use the verified widgets instead
  (`wc-products`, `woocommerce-archive-products`) and put per-card badges in a
  theme hook snippet, not in a template.

**Mining a control name from a real shipped kit is the cheapest way to settle
"is this control real"** without standing up WordPress — the exports are real
builder output.

---

## 10. Finishing

```bash
python forge.py <intake> --ir <ir.json> -o out --strict
```

A build that prints errors is not done. And a build that prints no errors is not
proof either — see `04-GOTCHAS.md`.

**Element ids are randomised per build**, so diffing compiled output between two
builds always reports differences and proves nothing. **Diff the IR instead** —
it is deterministic, and it is what a planner change actually affects.
