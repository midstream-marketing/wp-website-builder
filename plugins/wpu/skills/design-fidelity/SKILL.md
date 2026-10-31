---
name: design-fidelity
description: "MANDATORY whenever a client supplies a design to match — a Dribbble shot, screenshot, XD/Figma link, mockup, PDF or a competitor URL. Forces the device-level inventory, the missing-factory build and the render-and-compare gate that make output actually resemble the reference instead of merely following its section order. Load BEFORE composing any IR for a build that has a reference attached."
---

# Design Fidelity

Read `METHOD.md` in this directory in full before composing IR. This skill
exists because the same failure happened three times (AirFusion, Falis,
MedLou) and the client's verdict each time was a version of *"this is nowhere
close to the design I sent."*

## The one rule

**Match the DEVICES, not the section order.**

Section order is the cheap half and it is the half that gets done by accident.
A design looks like itself because of its *devices*: chips floating over a
photo, labelled tinted cards, a bento grid, circular arrow buttons, a serif
display face, oval image masks, per-card tints. Reproduce the section order
without the devices and you have built a different website with the same
table of contents.

## Why this keeps failing — the mechanism to interrupt

The forge has 144 block factories. Given a reference, the natural move is to
read its sections, then retrieve *the nearest existing block* for each one.
That is **retrieval, not matching**, and it silently caps the output at
whatever the library already had. The reference gets quietly reduced.

Three specific traps, all observed:

1. **Nearest-block substitution.** "How it works" in the reference is three
   tinted cards each with a LABEL, a heading, an image and a caption. Shipping
   `process.numbered3` — numbered circles on a dark band, no images, no labels
   — is not that section. It is a different component that occupies the same
   slot.
2. **Documenting a gap instead of closing it.** Writing "divergences" in the
   README converts a design failure into prose. The README is where you record
   decisions you *made*, never where you excuse ones you avoided.
3. **Honesty constraints used as cover.** Refusing to invent testimonials or
   metrics is correct and stays correct. It is *not* a licence to also drop the
   bento grid, the arrow buttons and the overlay chips. Separate the two: a
   content refusal never justifies a structural one.

## Mandatory sequence — no step is optional

```
1. INVENTORY   Write clients/<slug>/design-spec.json — every visual device,
               enumerated from the reference. METHOD.md has the taxonomy.
2. MAP         For each device name the block that produces it.
3. BUILD GAPS  Any device with no block gets a NEW FACTORY in
               src/forge/blocks_<client>.py. The contract already requires
               this: "If a design can't be expressed, add a factory."
               Substituting the nearest existing block is forbidden.
4. COMPOSE     Only now write build_ir.py.
5. GATE        python tools/check_fidelity.py clients/<slug>
               Build is NOT done until this exits 0.
6. COMPARE     Render and put it beside the reference. Score it honestly
               against the device list. Anything under 80% is a rebuild.
```

## The gate

`tools/check_fidelity.py` reads `design-spec.json` and `ir.json` and fails when
a required device has no satisfying block in the composed IR, or when a
`never` block appears — the `never` list is where you record the fallback you
were tempted by, so the next run cannot quietly take it.

Treat a fidelity failure exactly like a validator error: **the build is not
finished**, not "finished with notes."

## What still overrides the reference

Unchanged, and stated so nobody has to guess:

- Never invent testimonials, reviews, client logos, press mentions, patient
  quotes, volume figures or outcome claims to fill a slot the reference has.
  Replace the slot with something true, and say so in the README.
- A written client brief beats a named reference where they conflict.
- Brand colour from the client's logo beats the reference's palette.

Every one of those is a *content* substitution. None of them licenses a
*structural* one.
