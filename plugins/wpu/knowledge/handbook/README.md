# The Handbook

Everything this system has learned, in a form another system can absorb.

Written 2026-09-09 from 30 memory files, 3 project skills, 25 client builds and
6 WordPress plugins produced in `elementor-forge`. It is not a description of
the forge. It is the **transferable part**: the judgement, the standards, the
failure modes and the two mechanisms that turn judgement into something a
machine can check.

---

## What is in here

| File | What it carries | Portable? |
|---|---|---|
| `00-SOUL.md` | How to work. Voice, honesty discipline, what "done" means, how to handle conflicting instructions. **Start here — this is the part that is actually hard to rebuild.** | Fully |
| `01-DESIGN-METHOD.md` | Reference modes, the device taxonomy, `design-spec.json`, the fidelity gate, logo-as-design-input, palette and ground systems | Fully |
| `02-COPY-AND-SEO.md` | Word floors, what makes copy read human, heading/schema structure, the SEO sheet, placeholder discipline | Fully |
| `03-BUILD-CONTRACT.md` | The Elementor JSON contract and the 13 validator rules | Elementor-specific, but the *shape* of the idea ports to any generator |
| `04-GOTCHAS.md` | 30-odd earned traps: symptom → cause → rule. Most are silent failures | Mixed; each entry is labelled |
| `05-PLAYBOOK.md` | The end-to-end build sequence and the handoff standard | Fully |
| `06-CASE-FILES.md` | Every build compressed to its lesson. The evidence base for everything above | Fully |
| `tools/check_fidelity.py` | Portable design-fidelity gate | Runs anywhere with Python 3.8+ |
| `tools/copy_audit.py` | Portable copy gate — HTML, Markdown or JSON | Runs anywhere with Python 3.8+ |
| `tools/design-spec.schema.json` | Schema for the device inventory | Fully |

---

## How to port it into another system

Three levels, cheapest first. They compose.

### 1. As instructions (30 minutes)

Paste `00-SOUL.md` into the new system's system prompt or top-level agent
instructions. Paste `01-DESIGN-METHOD.md` and `02-COPY-AND-SEO.md` as skills or
reference documents that load when a design or copy task starts.

That alone reproduces most of the behaviour. The principles do the work; the
tooling only stops the principles from being quietly skipped.

### 2. As gates (2 hours)

Copy `tools/` in and wire both scripts into whatever "is this build finished"
check the new system has. Both are dependency-free Python 3.8+, and both were
verified against real builds in this repo:

```bash
# design gate — reads a component tree, a name list, or rendered output
python tools/check_fidelity.py design-spec.json --ir ir.json --brand intake.json
python tools/check_fidelity.py design-spec.json --scan "dist/**/*.html"

# copy gate — HTML, Markdown or JSON documents
python tools/copy_audit.py dist/ --floors floors.json
```

**Calibrate the floors against your own output before trusting them** — the copy
gate counts button and field labels too, so it reads 15–20% higher than a
prose-only counter. Run it on a page you already consider well-written and set
the numbers from that.

This is the half that matters most, and the reason is in `00-SOUL.md`:

> **Everything the pipeline measures comes out right. Everything it does not
> measure drifts.**

Three failed client reviews in a row happened because design was measured by
nothing. Word counts were always fine — because they were audited. The gates
are not bureaucracy; they are the difference between the two outcomes.

### 3. As memory (ongoing)

`06-CASE-FILES.md` is the format to keep writing in: one file per project, with
the *non-obvious* facts only — never what the code already says. The house
style is worth copying exactly:

- Lead with the decision, not the description.
- Every claim traceable to something observed, with the date.
- **Bold the rule**, so the file is skimmable at 2am.
- End with **How to apply**, which is the part future-you actually reads.
- Link related entries with `[[slug]]` so the corpus becomes a graph.

---

## If you only read four paragraphs

**Match devices, not section order.** A design looks like itself because of
floating chips on a photo, labelled tinted cards, a bento grid, circular arrow
buttons, a serif display face. Reproduce the section order without those and
you have built a different website with the same table of contents. Enumerate
the devices in writing *before* composing anything.

**Never invent a fact to fill a slot.** No testimonials, no review counts, no
years-in-business, no licence numbers, no prices. An empty slot with a written
brief is a deliverable; an invented one is a liability that ships. But a
*content* refusal never licenses a *structural* one — refusing to fake reviews
does not permit dropping the bento grid.

**Finish the artifact in the same turn.** The deliverable is the importable
thing, not the analysis of it. Open questions get built on a stated assumption
and flagged alongside the artifact, never used as a reason to stop before it
exists.

**A green build is not evidence.** Grep the compiled output for the values you
believe you set. Half the traps in `04-GOTCHAS.md` pass every validator and
render wrong.
