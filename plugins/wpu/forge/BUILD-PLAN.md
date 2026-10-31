# Elementor Forge — build & operate

Intake → SEO copy → design tokens → IR → compiled Elementor JSON →
validated → packaged as an importable Template Kit.

Everything in this repo already runs. This document is how to extend it and
how to use it on real client work.

---

## Run it now

```bash
python3 forge.py examples/intake.example.json -o out
```

Produces `out/` with `manifest.json`, `templates/*.json`, `ir.json`, and a
zip you can feed to the Envato Template Kit Import plugin. The example builds
a 13-page HVAC contractor site — header, footer, home, about, services index,
three service pages, areas index, two area pages, FAQ and contact.

With agent output:

```bash
python3 forge.py intake.json --copy copy.json -o out --strict
python3 forge.py intake.json --copy copy.json --ir ir.json -o out --strict
```

`--strict` promotes V6 control warnings to errors. Use it before delivery.

---

## Layout

```
forge.py                        CLI
registry/elementor-registry.json  legal widget + control vocabulary
schemas/intake.schema.json      the questionnaire contract
src/forge/
  core.py       ids, value shapes, globals/dynamic helpers, registry
  tokens.py     brand -> global.json Kit          (the only place colour lives)
  blocks.py     block factories                    (the only place JSON is authored)
  planner.py    intake + copy -> IR                (deterministic floor)
  compiler.py   IR -> Elementor documents, symbolic ref resolution
  validator.py  the ten rules
  kit.py        manifest + zip packaging
.claude/
  skills/elementor-contract/    pinned contract — agents read this first
  agents/                       five subagents
```

---

## The pipeline

| Stage | Who | In | Out |
|---|---|---|---|
| 1 Intake | `intake-agent` | conversation | `intake.json` |
| 2 Design tokens | `design-director-agent` | reference screenshots | patched `brand.colors` / `brand.fonts`, layout intent |
| 3 Copy | `seo-copy-agent` | `intake.json` | `copy.json` |
| 4 Layout | `layout-agent` | intake + copy + intent | `ir.json` |
| 5 Compile | `compiler.py` | `ir.json` | `out/templates/*.json` |
| 6 Validate | `validator.py` | documents + kit | pass/fail report |
| 7 Package | `kit.py` | documents | `manifest.json` + zip |
| 8 QA | `qa-agent` | report + staging import | fixes, screenshots |

Stages 5–7 are deterministic. No model touches them. That is the entire
reason the output imports cleanly without separate CSS.

---

## Importing into WordPress

Order matters. Getting it wrong is the usual cause of "it doesn't look like
the preview":

1. Install Elementor + Elementor Pro. Nothing else.
2. Import the kit zip via the Envato Template Kit Import plugin.
3. **Apply the Global Kit first** — Site Settings → import `global.json`.
   Pages imported before the kit exists render with dangling token
   references and look unstyled.
4. Create the WP menu named in the header block, then assign it.
5. Import loop-item documents, note their post IDs, resolve `@loop:` refs.
6. Import pages last.
7. Assign header/footer display conditions in Theme Builder.

---

## Extending

### Add a block

```python
@block("testimonials.row")
def testimonials_row(props):
    ...
    return _section([...], bg="surface")
```

Rules: colour and typography via `color_ref` / `typo_ref`; geometry via
`dims` / `slider` / `box`; never a hex literal, never a CSS string. Then
rebuild and run `--strict`.

### Add a widget the registry doesn't know

The registry is mined from real kits, so it only knows controls those kits
used. When you need a control it hasn't seen:

1. Build the thing by hand once in Elementor, export the template.
2. Run `build_registry.py` over it together with the existing kits.
3. Commit the updated registry.

Never add a control key by guessing it — that's the failure mode the
registry exists to prevent.

### Add a page type

Extend `DOC_META` in `compiler.py` and add a branch to `planner.py`. Theme
Builder types (`archive`, `single-post`, `loop-item`) take dynamic bindings
rather than literal copy — see `core.dynamic()` and the contract.

---

## Build order, if you're rebuilding this from scratch

Each phase leaves the repo working.

1. **Registry** — `build_registry.py` over two or more kits. Nothing else can
   be trusted until this exists.
2. **Core + tokens** — value-shape helpers and `global.json` generation.
   Test: import the kit alone and check Site Settings shows your palette.
3. **Three blocks** — `hero.split`, `services.grid`, `cta.band`. Compile a
   one-page IR by hand, import it, look at it. This is the moment the whole
   idea is proved or disproved.
4. **Validator** — all ten rules, wired into the CLI as a build gate.
5. **Planner** — the remaining page types.
6. **Kit packaging** — manifest + zip.
7. **Agents** — intake, copy, design, layout, QA. Deliberately last: the
   deterministic pipeline must work end to end before a model is allowed
   near it.
8. **Importer** — WP REST push, `@loop:` resolution, menu creation,
   Theme Builder conditions. Turns a 7-step manual import into one command.
9. **Screenshots** — Playwright capture at three widths, into
   `screenshots/`, which the manifest already expects and the QA agent uses
   for visual diffing.

---

## What this is worth

A 13-page contractor site — structure, copy slots, responsive behaviour,
global kit, importable zip — compiles in under a second. The work that
remains is the work that should remain: choosing the palette, writing the
copy, and looking at the result.

The two limits worth knowing up front. First, block coverage is the ceiling
on design range — the system builds what's in `blocks.py` and nothing else,
so unusual layouts mean writing a factory, not prompting harder. Second,
image URLs must be publicly reachable at import time, because Elementor
downloads by URL; a client who sends photos over WhatsApp needs them hosted
before the build runs.
