# Elementor Compiler Contract v1

Derived from two shipped Envato kits:

| Kit | Elementor | Profile |
|---|---|---|
| Saira – Personal Portfolio | 3.24.4 | free + 4 third-party plugins |
| Scoop – News & Magazine | 3.34.1 | **Elementor Pro only** ← target profile |

Combined: 39 templates, 515 containers, 765 widgets, **0 bytes of CSS**.

---

## 1. Non-negotiables

1. **No CSS.** Never emit `custom_css`, `_custom_css`, or `_css_classes`.
   Neither kit contains a single byte of either. If a design can't be
   expressed in control values, the block factory is wrong — not Elementor.
2. **No `section` / `column`.** Containers only. Both kits are 100% container.
3. **Core + Pro widgets only.** Any `widgetType` outside `registry.widgets`
   with `tier != "third-party"` is a build failure, not a warning.
4. **The LLM never writes this JSON.** Agents emit IR; the compiler emits JSON.

---

## 2. The three settings axes

Every element's `settings` object carries up to three parallel channels.
Getting these boundaries right is the whole job.

```jsonc
"settings": {
  "padding": { "unit": "px", "top": "32", … },          // 1. literal  — geometry
  "__globals__": {                                       // 2. globals — theme
    "background_overlay_color": "globals/colors?id=0e78c35",
    "title_color":              "globals/colors?id=primary"
  },
  "__dynamic__": {                                       // 3. dynamic — WP data
    "background_image": "[elementor-tag id=\"6f4e2b6\" name=\"post-featured-image\" settings=\"%7B%7D\"]"
  }
}
```

**Routing rule, measured across both kits (2,568 globals refs vs 15,535 literals):**

| Property class | Channel |
|---|---|
| color, typography | `__globals__` — always |
| padding, margin, gap, width, min-height, radius, flex-*, position, z-index, filters | literal — always |
| content on `page` documents | literal |
| content on `loop-item` / `archive` / `single-post` documents | `__dynamic__` |

Globalising geometry breaks maintainability. Hardcoding colour breaks re-skinning.
There is no third option.

### Dynamic tag encoding

```
[elementor-tag id="<7-8 hex>" name="<tag-name>" settings="<urlencoded JSON>"]
```

`settings="%7B%7D"` is the empty case. Tags observed and their payload keys:

| Tag | Bound controls | Settings keys |
|---|---|---|
| `post-featured-image` | `image`, `background_image`, `background_hover_image` | `fallback` |
| `post-title` | `title` | `before`, `after`, `fallback` |
| `archive-title` | `title` | `include_context`, `fallback` |
| `archive-description` | `editor` | — |
| `post-url`, `site-url` | `link` | — |
| `site-logo` | `image` | — |

Always set `fallback` — it's what renders in the editor preview and in the
QA screenshot before real content exists.

---

## 3. Document types

The output artifact is a **site**, not a page set. `type` at the JSON root:

| `type` | `metadata.template_type` | Notes |
|---|---|---|
| `page` | `single-page` | literal copy |
| `section` | `global-styles` | the Kit — exactly one per site |
| `header` / `footer` | `section-header` / `section-footer` | Theme Builder |
| `single-post` | `single-post` | dynamic |
| `archive` | `archive-blog`, `archive-category`, `archive-search` | dynamic |
| `loop-item` | `section-loop` | dynamic, referenced by `loop-grid` |
| `search-results` | `archive-search` | dynamic |
| `error-404` | `single-404` | |
| `container` | `section-other` | reusable global block |

Display conditions are **not** in the template JSON — they live in
`_elementor_conditions` post meta. The importer sets them.

---

## 4. Portability hazards (the #1 cause of a broken import)

`loop-grid`, `loop-carousel`, and `template` widgets reference other templates
by **raw WordPress post ID**:

```json
{ "widgetType": "loop-grid", "settings": { "template_id": "1367" } }
```

Scoop ships 19 of these pointing at IDs 528 / 1157 / 1261 / 1367 — post IDs on
the author's server that will not exist on yours. Import order matters:

1. Import `loop-item` documents first, capture the new post IDs.
2. Rewrite every `template_id` in dependent templates to the new IDs.
3. Import pages last.

The compiler must emit symbolic refs (`"template_id": "@loop:hero-big"`) and
resolve them at import time. Note Scoop stores these inconsistently as both
string `"1157"` and int `1157` — always coerce to string.

---

## 5. Design tokens (the design agent's output contract)

`global.json` → `page_settings`. 4 system colours + N custom, 4 system
typography + N custom named steps:

```jsonc
"system_colors":   [{ "_id": "primary", "title": "Primary", "color": "#004CFF" }, …],
"custom_colors":   [{ "_id": "cb2acc7", "title": "Full White", "color": "#FFFFFF" }, …],
"system_typography": [{ "_id": "primary", "title": "Extra Large Heading",
  "typography_typography": "custom", "typography_font_family": "Inter",
  "typography_font_weight": "700",
  "typography_font_size": { "unit": "px", "size": 40, "sizes": [] },
  "typography_line_height": { "unit": "em", "size": 1.2, "sizes": [] },
  "typography_font_size_mobile": { "unit": "px", "size": 32, "sizes": [] } }, …]
```

Custom `_id` values are 7-char hex, generated. System `_id`s are the fixed
strings `primary` / `secondary` / `text` / `accent` — never invent others.

Conventions both kits follow: line-heights in `em`, font sizes in `px`,
1–2 font families max, opacity baked into 8-digit hex (`#02081752`) rather
than a separate opacity control.

Kit-level layout settings worth setting: `container_width` (Scoop: 1280px),
`container_padding`, `space_between_widgets`, `paragraph_spacing`,
`viewport_md: 768`, `viewport_lg: 1025`.

---

## 6. Value shapes

| Shape | Form |
|---|---|
| slider | `{ "unit": "px\|%\|em\|vh\|rem", "size": 40, "sizes": [] }` |
| dimensions | `{ "unit": "px", "top": "32", "right": "32", "bottom": "32", "left": "32", "isLinked": true }` |
| media | `{ "url": "https://…", "id": 244, "size": "", "alt": "", "source": "library" }` |

Dimension values are **strings**; slider `size` is a **number**. Mixing them
is silently dropped on render.

---

## 7. Responsive

Only two breakpoints are used across 39 templates: `_tablet` and `_mobile`
(1,589 overrides). Do not emit `_widescreen`, `_laptop`, `_tablet_extra`, or
`_mobile_extra` — they require custom breakpoints enabled in Site Settings and
will no-op otherwise.

Emit `_mobile` for every type size and every container padding. Emit `_tablet`
only where the layout actually changes.

---

## 8. Validator rules (all earned from real defects in these kits)

| # | Rule | Evidence |
|---|---|---|
| V1 | Every `globals/colors?id=X` resolves in `global.json` | Saira ships 3 dangling refs |
| V2 | Every `globals/typography?id=X` resolves | clean in both |
| V3 | No `widgetType` outside the allowed registry | Saira: 18% third-party |
| V4 | No `custom_css` / `_css_classes` anywhere | both clean |
| V5 | Every element `id` unique within the document, 7–8 lowercase hex | Saira mixes 5/6/7/8 |
| V6 | Every control key exists in `registry.widgets[type].controls` | catches hallucination |
| V7 | Every `template_id` is a symbolic ref, never a raw integer | Scoop: 19 raw IDs |
| V8 | Every image has non-empty `alt` | Saira: 84/84 empty |
| V9 | Dimension values are strings; slider `size` numeric | — |
| V10 | Every `__dynamic__` tag name is in `registry.dynamic_tags` | — |
| V11 | A flex row's children + gaps fit one line, at desktop **and** tablet, measured against the row's real width after nesting and padding | 63 desktop + 313 tablet overflows across 11 shipped kits |
| V12 | Media URLs have no query string and carry an image extension | — |
| V13 | Every container setting is a real container control | 103 `max_width` + 13 `height` doing nothing |

V8 is worth stressing: both commercial kits ship with zero alt text. Filling
it from the copy agent's page context is free SEO differentiation.

---

## 9. Pro block backlog, evidence-ranked

How often a professional Pro kit actually reaches for each widget — build the
factories in this order:

```
32  posts             118 controls
29  call-to-action     41
16  post-info          13
 8  loop-grid          21
 7  loop-carousel      27
 5  archive-posts      76
 5  theme-post-title    4
 4  author-box         45
 4  share-buttons       7
 4  template            1
 4  theme-archive-title 6
 3  form               40
 3  search-form        29
 3  post-comments       -
 2  nav-menu           55
 2  gallery            14
```

`call-to-action` at 29 uses is the sleeper: it's a single Pro widget that
replaces a whole hand-built container + image + heading + text + button stack,
which is why the kit leans on it so hard. Wrap it first.

---

## 10. Third-party substitution map

Applied when ingesting a non-Pro kit as a layout reference:

```
elementskit-progressbar   → progress
elementskit-heading       → heading
elementskit-blog-posts    → posts
elementskit-social-share  → share-buttons
elementskit-client-logo   → image-carousel
elementskit-category-list → post-info
ekit-nav-menu             → nav-menu
jkit_testimonials         → testimonial-carousel
jkit_gallery              → gallery
jkit_search               → search-form
jkit_post_comment         → post-comments
metform, mf-*             → form
```
