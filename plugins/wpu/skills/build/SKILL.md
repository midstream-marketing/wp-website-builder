---
name: build
description: Build or rebuild a site in Elementor or in Gutenberg (WordPress blocks) from a Claude Design canvas, reference websites, an XD/Figma/screenshot mockup, or just a brief - through Elementor Forge and the WPU Bridge; Gutenberg, Divi 4, Breakdance and SeedProd layouts through the bridge's typed tools - with a render-and-compare gate. Use for new sites, page rebuilds and new sections.
argument-hint: "[Claude Design link | reference URLs | brief]"
---

# Build: design to Elementor or Gutenberg

**Pick the builder first.** Elementor when the site runs Elementor or the client wants it (sections 0-6 below).
Gutenberg when the site has no page builder, uses a block theme, or the client asks for blocks (see
"Gutenberg route" at the end). A whole new look without a page builder: build a draft theme with `/wpu:theme`.
Never mix builders on one page.

**Divi sites, version 4 or 5** (Divi theme, Extra or the Divi Builder plugin): build and edit full layouts through
the bridge's typed tools - see "Divi route" at the end.

**Breakdance 3+ / Oxygen 6+ and SeedProd 6.20+ sites**: build and edit full layouts through the builder's own AI
actions, run through the bridge's typed tools - see "Breakdance route" and "SeedProd route" at the end.

Sites built with **Bricks, Beaver Builder, or older Breakdance / SeedProd versions**: keep their builder. Through
the bridge's typed tools, `builder_page_text` reads every visible text on such a page and `builder_replace_text` changes text
safely in the builder's own data (styles, links and ids untouched, cache cleared, undo kept). New layouts in
those builders are made in the builder itself; WPU edits their content.

Load `core`, then `elementor-contract` (Elementor only) and `design-fidelity`. Read `${CLAUDE_PLUGIN_ROOT}/knowledge/BUILD-PLAYBOOK.md`
for the phase gates and `${CLAUDE_PLUGIN_ROOT}/knowledge/handbook/01-DESIGN-METHOD.md` + `02-COPY-AND-SEO.md`.
Input: `$ARGUMENTS`. Site folder: `sites/$WPU_SITE/`.

## 0. Intake

`intake-agent` writes `intake.json` (schema `${CLAUDE_PLUGIN_ROOT}/forge/schemas/intake.schema.json`). A trade preset
(`forge/presets/*.json`: electrician, general-contractor, hvac, landscaping, plumber, roofing, tree-surgeon, turf)
supplies the generic parts. Missing facts become one batch of questions - never invented.

## 1. Design source -> design-spec.json + tokens

- **Claude Design link**: open it (the session is signed in with the org account, so `/artifacts` or the Artifact
  read can reach it). Measure, don't eyeball: colours, fonts, spacing, radii, section devices. 
- **Reference site URL**: `python "${CLAUDE_PLUGIN_ROOT}/forge/analyse_reference.py" <url>` gives the measured palette,
  fonts, radii and techniques. Use structure and feel only - never copy a reference's text, images, logo or brand.
- **Screenshot / XD / Figma**: `design-director-agent`; an XD share link is machine-readable (see GOTCHAS).
- **No reference**: the logo is the brief (handbook 01 section 6).

Write `design-spec.json` (schema `${CLAUDE_PLUGIN_ROOT}/forge/schemas/design-spec.schema.json`): the device
inventory and the `never` list.
**Match devices, not section order.** If a device has no block factory, build the factory in `blocks.py` - never substitute.

## 2. Copy

`seo-copy-agent` -> `copy.json`. If `/wpu:seo` has run, use `seo/plan.json` focus keywords per page. Word floors and
human-copy rules from handbook 02; `copy_audit.py` gates it after compile (step 3).

## 3. Compile and validate

`layout-agent` -> `ir.json`. Then from the site folder:

```
python "${CLAUDE_PLUGIN_ROOT}/forge/forge.py" intake.json --copy copy.json --ir ir.json -o out --strict
python "${CLAUDE_PLUGIN_ROOT}/forge/tools/check_fidelity.py" .        # reads design-spec.json + ir.json here
python "${CLAUDE_PLUGIN_ROOT}/forge/tools/copy_audit.py" out          # word floors, one H1, banned phrases
```

Both must pass. Grep the compiled JSON for the values you believe you set.

## 4. Put it on the site (dry run first, every time)

1. Backup: `rwpphp.ps1 php/updraft-backup-start.php` (check retention - see GOTCHAS).
2. `rplan.ps1 plan.json` -> read -> `apply` (site settings, plugins, theme, Elementor settings, kit). Run again
   after plugins install. **Kit on a non-fresh site restyles live pages** - snapshot and ask first.
3. Media: `rmedia.ps1 <files>`; put the ids into the IR/templates. Image URLs with query strings never import.
4. Templates: `rtemplate.ps1 out/templates/*.json`; Theme Builder conditions and menus through the plan.
5. Pages from templates through the plan (`elementor_template`), front page, menus.

## 5. See it and judge it

`node audit/sweep.mjs full`, `audit.mjs`, `fonts.mjs`, `imgres.mjs`, `hscroll.mjs 390`. Then the **visual-critic**
agent (blind to the plan) compares the screenshots with the source at 390/768/1440. Up to three fix loops through
IR -> compile -> re-import. Use the `visual-change` skill for every visual fix.

## 6. Hand back

Preview links for the member, a list of what is provisional (internal), and SITE-NOTES updated with template and
page IDs. Nothing goes live without the member's approval; search engines stay discouraged.

## Gutenberg route (WordPress blocks, through the bridge's typed tools)

Needs WPU Bridge 2.1+. Every tool named below is run with `scripts/rtool.ps1` (see `core`): arguments in
`sites/<slug>/work/*.args.json`, and the word `apply` for anything that changes the site. Steps 0-2 (intake, design spec, copy) are the same; after
that:

1. **Learn the site.** `site_overview` (block theme or classic, blocks plugins such as Kadence or Spectra),
   then `theme_design_tokens` (palette, font sizes, spacing, content and wide widths, and the Kadence, Astra
   or GeneratePress global palette when present: Kadence blocks take colours like `"palette1"`) and
   `block_types_list` for any block you plan to use beyond core. Map the design spec onto the theme's
   tokens: use slugs (`"backgroundColor":"contrast"`, `"fontSize":"x-large"`), and only use a custom value
   when no token is close.
2. **Patterns before scratch.** `block_patterns_list` with a search (hero, pricing, testimonials, faq). An
   existing theme pattern restyled beats hand-written markup. Get its markup with `names` and adapt it.
3. **Write block markup per page**: core blocks first (group, columns, cover, heading, paragraph, buttons,
   image, list, details for FAQs), `layout` and `align` from the tokens, real copy from `copy.json`.
   Images: `media_upload` first, then use the returned id and url. Each block's comment attributes must
   match its HTML (class names, levels, alignment), or the editor marks it invalid.
4. **Create as drafts.** `content_create` (page, status draft, template as the theme needs). Read the
   returned `warnings`: unknown blocks, unbalanced comments and loose HTML must be fixed before showing anyone.
5. **See it and judge it** (section 5): open the `preview` link at 390/768/1440 and run the `visual-critic`.
   Fix with `blocks_edit` (targeted replace, insert, remove by path from `content_get`) rather than resending
   the page.
6. **Publish only on the person's go-ahead** (`content_update` status publish). SEO fields: `seo_update`.
   Every step returned a `change_id`; list them in the hand-back.

## Breakdance route (Breakdance 3+ or Oxygen 6+, through the bridge's typed tools)

Needs WPU Bridge 2.1+, WordPress 6.9+, Breakdance > Settings > Agents & MCP: MCP access on, and the site
admin's tick on **Tools > WPU Bridge > Tool switches > Builder AI actions** (off by default; read `bridge/SECURITY.md`,
"builder AI actions guard", before advising a client to switch it on). The actions are Breakdance's own; the
bridge checks every call first. Run them with `rtool.ps1 ability_run_readonly` / `rtool.ps1 ability_run`,
arguments `{ "name": "breakdance/...", "input": { ... } }`.

1. `abilities_list` with `plugin: "breakdance"` (or `oxygen`). Run `breakdance/get-instructions` and follow it;
   `breakdance/get-skill` has Breakdance's own build guides.
2. New page: `breakdance/create-post` (draft), then `breakdance/html-to-page` with the page as clean HTML
   (sections, headings, text, links, images, classes). Styles: `breakdance/insert-stylesheet` and
   `insert-css-variables` are site-wide, so get the member's go-ahead first.
3. Check: `breakdance/preview-post` returns the rendered HTML; then screenshots and `visual-critic` as in section 5.
4. Changes: `breakdance/get-post-tree`, then `breakdance/edit-post` (update, insert, move, delete by element id).
   Never re-run html-to-page to change something; it only adds.
5. Every page change returns a `change_id`; `change_undo` puts the page back exactly.

What the bridge refuses, say it plainly: Code Block, HTML, JavaScript, shortcode, widget and embed elements;
scripts, iframes, forms and event handlers anywhere in the input; dynamic data, PHP conditions and PHP queries
(set those in Breakdance); builder reset/import tools and site-wide code settings.

Go-ahead: any change to a live page, a template, header, footer or popup, publishing, form destinations,
maintenance mode, home page and global styles is refused with a `confirm_token`. Tell the member exactly what
will change; only when they agree, send the same call again with that token. Work on drafts to avoid this.

## SeedProd route (SeedProd 6.20+, through the bridge's typed tools)

Needs WPU Bridge 2.1+, WordPress 6.9+ and the site admin's tick on **Tools > WPU Bridge > Tool switches >
Builder AI actions** (off by default). The actions are SeedProd's own.

1. `abilities_list` with `plugin: "seedprod"`. `seedprod/list-pages` and `seedprod/get-page`
   (`include_sections: true`) show what exists.
2. Build with `seedprod/save-page`: `type` (landing-page, coming-soon, maintenance, ...), `title`, and
   `sections[] > rows[] > cols[] > blocks[]`. Every node needs a unique `id`; blocks need `type`,
   `elType: "block"` and `settings` (header: `headerTxt`, `tag`; text: `txt`; button: `btnTxt`, `link`).
   For other blocks, copy the settings names from an existing page (`get-page`); SeedProd fills in defaults.
3. **A person must open the page in SeedProd and click Save.** SeedProd creates the page's HTML in its builder;
   until then the page is empty on the front end. Give the member the `edit_url` and tell them.
4. `change_undo` restores the page as it was.

Refused: Custom HTML, shortcode and template-tag blocks, scripts, event handlers, licence activation, theme
import. Coming soon / maintenance switches, the theme builder switch, global CSS, theme templates, publishing
and changes to a live page need the member's go-ahead (`confirm_token`, as in the Breakdance route).

## Divi route (Divi 4 and Divi 5, through the bridge's typed tools)

Needs WPU Bridge 2.2+ on the site (2.1 covers Divi 4 only) and Divi active with its licence (updates and the
Divi library need the client's own Elegant Themes account; WPU never ships or licenses Divi).

1. `site_overview`, then `divi_modules` (the modules on this site, including ones other plugins add). For each
   module you plan to use, `divi_modules` with `names` gives its settings; add `design: true` for design settings.
2. Intake, design source and copy are the same as sections 0-2 above. Turn the design tokens into Divi settings:
   colours and fonts on modules (`header_text_color`, `body_font_size`, `background_color`), spacing as
   `custom_padding` / `custom_margin` (`top|right|bottom|left`), responsive values with `_tablet` and `_phone`.
3. Send the page as a layout tree with `divi_page_build` (`dry_run: true` first). Shape:
   `sections[] > rows[] (columns "1_2,1_2", cols[]) > modules[] (type, attrs, content, children[])`.
   Fullwidth sections (`"fullwidth": true`) take fullwidth modules directly. Modules with items take `children`.
   Pages are created as drafts.
4. Read the result: warnings name any setting Divi does not know (fix the name, do not ignore it). Open the
   `preview` link, screenshot at 390/768/1440 and run `visual-critic` against the design, as in section 5.
5. Fix with `divi_page_edit` by path (`divi_page_get` gives paths): `set_attrs`, `set_content`, `insert`,
   `replace`, `remove`, `duplicate`, `move`. Elements you do not touch stay exactly as Divi saved them.
6. Tell the member the page also opens in Divi's Visual Builder (`edit_in_divi` link) for hand edits.

**Divi 5.** The same four tools and the same layout shape work on a Divi 5 site. You still use the Divi 4
module and setting names from `divi_modules` (`text`, `blurb`, `button_text`, `background_color`, ...): the bridge
checks the layout, hands it to Divi 5's own converter and saves only the Divi 5 blocks it returns. Differences:
- `divi_page_get` shows Divi 5 names (`divi/text`) and, with `path`, Divi 5's stored settings. Read them to
  understand a page; change things with the Divi 4 names.
- A setting cannot be removed by name on Divi 5 (`null` is refused); set the value you want.
- Modules that exist only in Divi 5 (group, icon list, and so on) can be moved, duplicated and removed, but
  not created or changed here. Pages built here use Divi's "block" row layout, as migrated Divi 4 pages do.
- A page still in Divi 4 form on a Divi 5 site must be opened and saved in Divi once before it can be edited.
- No shortcodes in content on Divi 5 (a contact-form or gallery shortcode is added in Divi by hand), no Divi
  global colours (`gcid-...`; send the colour value), and no `%22` / `%92` in content.
- If the bridge says Divi 5 has not finished its first-time setup, open any page in the Divi builder once.
- `set_attrs` answers with `stored_values_set`: the Divi 5 values that one setting changed. Divi decides this
  (a menu's background colour also sets its dropdown colour), so read the list and re-set what you did not mean.

Limits, say them plainly: the Code module is never written (raw HTML and scripts are added by hand in Divi);
modules that other plugins add to Divi need the site admin to tick "Divi modules from other plugins" under
Tools > WPU Bridge; dynamic content fields are set in Divi;
specialty sections and Divi library/global items can be edited but not created; Theme Builder templates and
Divi 5's block format are not built yet (text edits work on Divi 5 pages).
