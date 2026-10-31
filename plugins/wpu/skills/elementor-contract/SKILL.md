---
name: elementor-contract
description: Load before writing, reviewing, or debugging anything that produces Elementor template JSON — block factories, the compiler, the validator, or IR. Contains the settings-channel rules, legal control vocabulary, document types, and the ten validator rules. Use whenever a task mentions Elementor, template JSON, __globals__, __dynamic__, containers, loop items, or a Template Kit.
---

# Elementor JSON Contract

Read `CONTRACT.md` in this directory in full before acting. It is derived from
two shipped commercial kits and is the source of truth for this repo.

## The five things that break builds

1. **Never emit CSS.** No `custom_css`, no `_custom_css`, no `_css_classes`.
   Both reference kits contain zero bytes of CSS across 39 templates.
2. **Never invent a control key.** Check `registry/elementor-registry.json`.
   Elementor silently drops unknown keys, which looks like "the styling
   didn't apply" rather than an error.
3. **Route by channel.** Colour and typography go in `__globals__`. Geometry
   goes in literal `settings`. WP data goes in `__dynamic__`. Never mix.
4. **Never write raw `template_id`.** Use `@loop:<key>` symbolic refs;
   the importer resolves them to real post IDs.
5. **Never hand-author element JSON in an agent.** Agents emit IR. Only
   `src/forge/blocks.py` produces Elementor trees.

## If a design can't be expressed

Add a factory to `blocks.py`. Do not loosen the validator, do not add a
CSS escape hatch, do not reach for a third-party widget. Core + Elementor
Pro only.

## Before you finish any change

```
python3 forge.py examples/intake.example.json -o out --strict
```

A build that prints errors is not done.
