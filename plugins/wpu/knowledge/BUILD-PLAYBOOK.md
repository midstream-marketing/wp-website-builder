# Build playbook

The order a site gets built in. Each phase ends with a **gate** — do not start the
next phase until the gate passes, because every later phase builds on the earlier
ones (a wrong kit font means re-checking every page; a wrong page slug breaks
every menu that links to it).

Commands assume `$env:WPSB_CONFIG = '<site>'` is set.

---

## Phase 0 — Brief and plan

**Inputs to collect:** sitemap (pages + hierarchy), brand colours and fonts,
logo files, design references (Figma/XD/screenshots), content per page, whether
it sells (WooCommerce), payment and shipping details, legal pages, domain and
launch date.

1. Copy `plans/example.plan.json` to `plans/<site>.plan.json`.
2. Fill `site`, `pages`, `menus` from the sitemap; `kit` from the brand.
3. Create `docs/SITE-NOTES-<site>.md` from `docs/SITE-NOTES.md`.
4. List everything missing from the client as questions — do not invent it.

**Gate:** the plan reads as the agreed sitemap; open questions are sent to the client.

---

## Phase 1 — Foundation

```powershell
powershell -File bin/rdoctor.ps1                 # host preflight - read the warnings
powershell -File bin/rwpphp.ps1 php/site-info.php
# UpdraftPlus backup (even on a fresh install - it is the rollback point)
powershell -File bin/rplan.ps1 plans/<site>.plan.json          # dry run
powershell -File bin/rplan.ps1 plans/<site>.plan.json apply    # site, plugins, theme
powershell -File bin/rplan.ps1 plans/<site>.plan.json          # run again: plugin-dependent steps now show
```

Plugins listed under `plugins.install` come from wordpress.org. Premium plugins
(Elementor Pro, etc.) are uploaded through wp-admin with the client's licence,
then listed under `plugins.activate`.

**Gate:** second dry run shows only design/content changes left; `site-info.php`
shows the right theme, plugins, permalinks, and search engines *discouraged*.

---

## Phase 2 — Design system

1. `kit.colors` and `kit.fonts` in the plan → apply.
2. Elementor settings: default colours/fonts disabled, container on.
3. Build one test page with headings, text, buttons in each style; sweep it.
4. `node audit/fonts.mjs` — add any family it reports to `kit.extra_fonts`.

**Gate:** `fonts.mjs` passes; buttons/headings match the design at 390 and 1440.

---

## Phase 3 — Templates

1. Export or receive Elementor templates (header, footer, page layouts, single
   product, archives) as `.json`.
2. `powershell -File bin/rtemplate.ps1 templates/*.json`
3. Header/footer/archive display conditions → `theme_builder` in the plan → apply.
4. Media for the templates: `powershell -File bin/rmedia.ps1 assets/*` — then
   replace template image IDs where they point at the source site's library.

Template rules:
- Layout with containers and native flex/grid controls; responsive values set in
  Elementor per breakpoint, not with media-query CSS.
- Unavoidable CSS goes in the element's Custom CSS with `selector`.
- Global colours/fonts only — no hard-coded hex or font families in widgets.

**Gate:** header and footer render on every page type; `audit.mjs` clean; sweep
screenshots checked at all three widths.

---

## Phase 4 — Pages and content

1. `pages[]` with `elementor_template` → apply (copies layout into each page).
2. Replace placeholder text and images with the client's content.
3. `front_page`, `posts_page` → apply.
4. Every placeholder that must stay (awaiting client) goes in SITE-NOTES.

**Gate:** no lorem ipsum outside what SITE-NOTES lists; `audit.mjs` shows no THIN
or EMPTY SECTIONS; sweep checked.

---

## Phase 5 — Navigation

1. `menus[]` → apply. Themes built on Elementor headers usually register no menu
   locations; the header's Nav Menu widget picks the menu by name instead.
2. Footer links, legal links, 404 page (Elementor Pro `single` / not_found404).
3. `php/orphans.php` — no menu item points at a draft or trashed page.

**Gate:** every menu link returns 200; mobile menu opens and closes.

---

## Phase 6 — Commerce (only if it sells)

1. `woocommerce` in the plan: pages, currency, store country, tax entry mode.
2. **Ask first:** payment gateways, shipping zones and rates, tax rates, prices.
3. Products: import (CSV) or create; images via `rmedia.ps1`.
4. Test the flow: add to cart → cart → checkout → order, in test mode, with the
   confirmation email going only to the client's own inbox.

**Gate:** a test order completes; the cart's "Proceed to checkout" lands on the
real checkout page (not a template preview); mobile checkout total is on screen.

---

## Phase 7 — Responsive and polish pass

```powershell
node audit/sweep.mjs full
node audit/audit.mjs
node audit/fonts.mjs
node audit/hscroll.mjs 390
node audit/perf.mjs
```

Fix with native controls first; use `audit/probe.mjs` to see which rule wins
before writing any CSS. Check phones for: buttons overlapping text, sticky/floating
elements covering controls, hover-only effects, tap targets, pinch-zoom allowed.

**Gate:** all audits pass; screenshots reviewed page by page.

---

## Phase 8 — Launch and handover

1. `docs/CHECKLIST-HANDOVER.md`, every item.
2. With the client's go-ahead: `site.discourage_search_engines: false` → apply.
3. Final UpdraftPlus backup; copy it off the server.
4. Delete the WP Site Build Bridge plugin, **revoke the application password**.
5. Move `docs/SITE-NOTES-<site>.md` to WP Site Doctor for aftercare.

**Gate:** the checklist is complete, and anything unverified is stated as such.
