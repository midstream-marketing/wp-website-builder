---
name: layout-agent
description: Merges copy.json, intake.json and the design director's layout intent into ir.json — the intermediate representation the compiler consumes. Use after copy and tokens exist, before compiling.
tools: Read, Write, Glob, Bash
---

> **WP Ultimate Build paths.** Forge lives in `${CLAUDE_PLUGIN_ROOT}/forge/` - run
> `python "${CLAUDE_PLUGIN_ROOT}/forge/forge.py" ...` and read `${CLAUDE_PLUGIN_ROOT}/forge/schemas/`,
> `presets/`, `registry/`, `references/`. This client's files (intake.json, copy.json, ir.json,
> design-spec.json, out/) live in the site folder `sites/<slug>/` - work from there.

You produce `ir.json`. This is the only file an LLM writes that the
compiler reads.

## Shape

```json
{ "site": "Business Name",
  "pages": [
    { "key": "home", "type": "page", "title": "Home",
      "seo": { "target_keyword": "...", "meta_title": "...", "meta_description": "..." },
      "blocks": [
        { "block": "hero.split", "props": { "h1": "...", "intro": "...",
          "cta": { "label": "...", "href": "/contact" },
          "image": { "url": "https://...", "alt": "..." }, "dark": true } }
      ] } ] }
```

## Rules

- `block` must exist in `src/forge/blocks.py`. Run
  `python3 -c "import sys;sys.path.insert(0,'src');from forge.blocks import BLOCKS;print(sorted(BLOCKS))"`
  rather than guessing.
- Props are plain data only — strings, numbers, booleans, lists. Never a
  settings object, never a control key, never a hex colour, never a
  `__globals__` block. If you are typing `unit` or `px`, stop.
- Every string comes from `copy.json` or `intake.json`. You are assembling,
  not authoring. If a slot has no copy, leave it out rather than writing
  filler.
- Every image needs a non-empty `alt`.
- Cross-template references use `@loop:<key>`, never a number.
- Start from `planner.py`'s output and modify it. It already covers the
  common page types correctly; regenerating from scratch loses that.

Verify before finishing:

```
python3 forge.py intake.json --copy copy.json --ir ir.json -o out --strict
```
