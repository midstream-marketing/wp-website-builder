---
name: theme
description: Build a custom WordPress block theme as a draft through the WPU Bridge's typed tools - design tokens in theme.json, header/footer parts, page templates, optional Tailwind-style CSS - share a private preview link, revise, and activate only on the go-ahead. Use when a client wants a new theme, a full redesign without a page builder, or "a theme like WPVibe makes".
argument-hint: "[site slug] [design source: Claude Design link | reference URLs | brief]"
---

# Theme builder (draft block theme with a preview link)

Needs WPU Bridge 2.1+ on the site with the themes switch on (Tools > WPU Bridge > Tool switches). The tools
(`theme_draft_save`, `theme_preview_link`, `theme_activate`, ...) are run with `scripts/rtool.ps1` (see `core`). The draft is a **block theme
made only of data**: `theme.json` (tokens, global styles and the CSS), `templates/*.html` and `parts/*.html`
block markup. No PHP is written, so a draft can never run code. It is installed but **not active** until
`theme_activate`.

Load `design-fidelity` when a design or reference is supplied.

## 1. Design system first

From the intake and design source, write the design tokens as theme.json `settings`:
- `color.palette`: brand, accent, base (background), contrast (text), plus 2-4 neutrals; slugs are what
  blocks use (`"backgroundColor":"brand"`).
- `typography.fontFamilies`: system stacks or Google fonts. Self-host font files only through the client's own
  process; the bridge tools write no font files. `fontSizes` uses fluid sizes (`"fluid":{"min":..,"max":..}`).
- `spacing.spacingSizes`, `layout.contentSize` (720-760px) and `wideSize` (1200-1280px).
- `styles`: elements (link, button, h1-h6), blocks (core/button, core/navigation), and `styles.css` for the
  rest (passed as `css`).

**Tailwind:** WordPress does not compile Tailwind. In Claude Code, compile the utility classes the templates
use (`npx tailwindcss -i in.css -o out.css --minify` with `content` pointing at the template files), then
send the result as `css` (max 300 KB, no `@import`). Utility classes go in
each block's `className`.

## 2. Parts and templates

- Parts: `header` (site logo/title, navigation, a button) and `footer`. Use them as
  `<!-- wp:template-part {"slug":"header","tagName":"header"} /-->`.
- Templates: `index` (required fallback), `front-page`, `page`, `single`, `archive`, `search`, `404`. Dynamic
  blocks do the content: `post-title`, `post-content`, `query` + `post-template`, `query-pagination`,
  `post-featured-image`, `post-date`.
- Check blocks with `block_types_list` and patterns with `block_patterns_list`. Read every `warnings` line
  `theme_draft_save` returns and fix it.

## 3. Save, preview, judge

1. `theme_draft_save` with `name`, `theme_json`, `css`, `templates`, `parts`. It returns `preview_url` (a
   private link that works for anyone who has it, logged in or not, for 7 days by default) and
   `site_editor_url` (for admins: edit visually in the Site Editor without activating).
2. Open the preview at 390 / 768 / 1440 and run the `visual-critic` against the design source.
3. Revise with `theme_draft_save` again: only the files you send change (each save has a change_id for undo).
   `theme_draft_get` returns the current files.
4. Send the client the preview link (`theme_preview_link` makes a fresh one, 1-30 days).

## 4. Go live, only on the go-ahead

- Check plugins that depend on the old theme (page builders, theme-specific widgets) before switching.
- `theme_activate` the draft. It checks the home page right away; then check the key pages with
  `site_health_check`. The change_id switches back with `change_undo` if anything is wrong.
- Menus: a block theme uses Navigation blocks; check the header part's navigation menu.

## Rules

- Never activate without the person's explicit go-ahead. Activation changes the whole site for every visitor.
- Keep the preview link private: anyone holding it can browse the site in the draft theme (content is the
  same public content).
- Old drafts can stay; they are inactive. Remove unwanted ones from Appearance > Themes.
