# 05 — Playbook

The sequence, the checklist, and what a finished handoff looks like.

---

## The sequence

No step is optional, and the order is the point. Composing before the device
inventory exists is the failure this whole system was rebuilt to prevent.

```
0. GATHER      Read every supplied asset. Crawl the incumbent site.
               Parse the reference's real structure. Decide the MODE.

1. INVENTORY   Write design-spec.json — every visual device, enumerated.
               Ground system, card anatomy, overlays, buttons, type, grid,
               media, proof devices, micro-detail.   [01-DESIGN-METHOD §2]

2. MAP         For each device, name the component that produces it.

3. BUILD GAPS  Any device with no component gets a NEW ONE, in its own
               client module. Substituting the nearest existing component
               is forbidden — that is the failure, not the shortcut.

4. COPY        Write the copy against the floors, from domain knowledge.
               Every unverifiable fact becomes a marked placeholder.

5. COMPOSE     Only now assemble. Structure decisions only; copy lives in
               its own file so it can be edited without touching code.

6. BUILD       Compile with --strict. Errors mean not done.

7. GATE        check_fidelity.py   -> required devices present, no `never`
               copy_audit.py       -> floors, one H1, no banned phrases

8. VERIFY      Grep the COMPILED output for the values you believe you set.
               Render and compare against the reference where possible.

9. HAND OVER   The artifact + the document. Never the document alone.
```

**Everything before step 5 is where the quality is decided.** Steps 6–8 only
prevent regressions.

---

## Where things live

The separation that made every build maintainable:

| File | Holds | Edited by |
|---|---|---|
| `intake.json` | brand, palette, fonts, nav, footer, contact, image briefs, keyword map | you, once |
| `design-spec.json` | the device inventory the gate enforces | you, before composing |
| `copy-pages.json` | **every word on the site**, and every placeholder | the client, later |
| `build_ir.py` | structure only — which device carries which copy, in what order | you |
| `blocks_<client>.py` | the client's own devices | you |

**No hex values in the component code.** Everything routes through tokens, so
the whole site re-skins from one file.

**Copy in JSON, not in Python.** A copy edit must never require touching code —
and keeping markup markers (`**bold**`) in the copy file means a copy edit
cannot silently drop a design device either.

**Placeholders in one place**, so they are filled once and rebuilt.

---

## Per-build checklist

Run before writing the handoff document.

**Design**
- [ ] Mode declared and stated in writing
- [ ] Device inventory written *before* composing
- [ ] Every required device has a real component, not a near-miss
- [ ] `never` entries recorded the moment a fallback was tempting
- [ ] Fidelity gate exits 0
- [ ] Ground rhythm consistent across pages; the accent never fills a section
- [ ] Two button styles, not three

**Copy**
- [ ] Every page at or above its floor, with real material rather than padding
- [ ] Exactly one H1 per document, keyword in it (or the exception flagged)
- [ ] No banned phrases
- [ ] Location/service pages measured for n-gram overlap
- [ ] Nothing invented: reviews, counts, years, prices, licences, labs
- [ ] Placeholders counted, listed, and greppable

**Build**
- [ ] `--strict` green
- [ ] Compiled output grepped for the values you claim
- [ ] IR diffed against the previous build if a shared component changed
- [ ] Output directory cleared if the page set shrank
- [ ] Theme Builder documents carry their display conditions

**Handoff**
- [ ] Ask-list ordered by what blocks launch
- [ ] Import order and pre-import steps stated
- [ ] Every deferred device recorded with its trigger
- [ ] Every conflict between brief, reference and brand named
- [ ] SEO sheet shipped

---

## What ships

1. **The artifact.** The importable, runnable thing.
2. **The handoff document (`README.md`).** Structure below.
3. **The SEO sheet.** One section per page. `02-COPY-AND-SEO.md` §4.
4. **Anything the client must produce**, as a written brief per slot.

### Handoff document structure

Proven across 25 builds. Section 1 is the one clients actually read.

```
1. WHAT I STILL NEED FROM YOU    ordered by what blocks a review-ready site
2. WHAT THE INPUTS WERE          and what followed from them
3. THE DEVICES                   what was built and why each one had to exist
4. DEPARTURES FROM THE BRIEF     each one named, with the reason, reversible
5. FILL BEFORE PUBLISHING        the placeholder inventory + the grep
6. IMPORT NOTES                  order, pre-import steps, slugs, menus
7. WHAT IS DELIBERATELY NOT HERE deferred devices + the trigger for each
8. REBUILDING                    the commands, and which file holds what
9. OPEN QUESTIONS                numbered, answerable in one line each
```

**Section 1 exists because the client's blanks are usually the deliverable.**
When a brief says "let me know if you need anything else", the ordered list of
missing facts *is* the answer.

**Section 4 records decisions you made.** It is never where you excuse ones you
avoided — see `00-SOUL.md` §10.

---

## Reporting back

State the outcome plainly, then the things that need a decision.

- Lead with what was built and the measured numbers: documents, words, errors,
  devices, gates.
- Then the two or three things that are genuinely the client's call.
- Then the open questions, numbered, each answerable in a sentence.
- No hedging on finished work. No inflating unfinished work.

Where you inferred meaning rather than copied it — a garbled figure in a PDF, a
reconstruction of an intended calculation — **say so in one line and point at
it**. That is the sentence that prevents a wrong number going live.

---

## Extension builds

When the site already exists and you are adding to it:

- **Check whether the live site already runs your design tokens.** If the global
  colours and token ids match your intake, new pages inherit the live palette
  with no seam and no re-tinting.
- **Do not re-emit chrome that already works.** Re-importing a header and footer
  gives the site a second set of Theme Builder templates to reconcile.
- Match the *built* pages, not the original comp — they may have diverged, and
  the built site is what a visitor sees.
- Two brief instructions that look contradictory usually are not: check the
  current state before choosing a side. "Move away from blue" and "match the
  existing palette" only conflict if the site is still blue.
