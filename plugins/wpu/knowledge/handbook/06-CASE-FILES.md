# 06 — Case files

The evidence base. Every build compressed to the thing it taught, so a rule is
never just an opinion.

Ordered roughly by date. `→` marks the transferable lesson.

---

## Design-decision cases

**Primetime Turf** · Houston turf installer · waterlooturf.com in *match* mode
The reference's forest green fought the client's black/silver/lime logo.
→ **Where a reference and the client's brand pull apart, that is the client's
decision to make, not yours to assume.** Match structure, spacing and type;
treat the palette as a separate, named question.

**Heritage Day Tours** · UK over-60s day tours · a finished homepage mockup
The client's written notes contradicted the approved mockup twice — nav items,
and price wording (`ONLY £99 pp`, never `FROM £99 PP`).
→ **Written notes beat the mockup.** They are the later, more specific
instruction. 47 image slots deliberately empty.

**OD Electric** · California electrician · primalelectric.com, "exactly similar"
Palette taken from the logo instead, resolved up front.
→ Client images hosted on their own domain must be **uploaded before the
import**, and month-based upload paths break every URL if the upload slips.
7 files named `.jpeg` were really HEIC (rejected outright by WordPress).

**Greyson Private Wealth** · Columbus OH wealth firm · XD-exact
LPL/FINRA disclosures cannot be written or "finished" by anyone but the CCO.
→ **Match it exactly and flag what looks wrong** beats correcting quietly. The
brand's own gold fails its own brand guide's AA rule; built as drawn, with three
one-line fixes written up. Converting a bespoke HTML widget into a real
component also removes a private font `@import` — and the old widget must be
deleted from the live page or the section renders twice.

**Classic Comfort** · Bristol TN HVAC · two stock-Elementor references
→ **The badge logo won the palette** over both references. Client gave
positioning and services but no facts, photos or contact details, so the entire
risk was a placeholder shipping as real: 12 survive into the templates by
design.

**AirFusion HVACR** · Central Florida · ameriserve.com, "perfect example but
different colours" — **the first design rejection**
→ *"The design is nowhere close to it."* Rejecting the palette **narrows** what
to copy; it does not downgrade the brief to inspiration. Parsing ameriserve
showed **49 headings to 4 text blocks** — the fact that explained why a
prose-led build felt wrong. The interior-page rebuild then found their Services
pages were a *different system* from the homepage: dark top to bottom.
→ **A `bg="dark"` flag does not work.** Existing light-family components resolve
headings and body through light tokens and render invisible copy on a dark
ground. Dark grounds need dark-native components.

**Falis Construction** · Twin Cities, brand-new company · imperiare.com **plus a
45-page written spec that banned the reference's four credibility devices**
→ **The written brief wins.** Kept the reference's *conversion architecture*
(persistent CTA, mega-menu, early estimate route, photo service grid); dropped
its counters, ratings, testimonials and badges — which a new company cannot fill
without fabricating anyway. 27 pages, 21,464 words, max 5-gram overlap 6.7%
across 190 page pairs. Pro forms do multi-step natively but **not per-answer
branching** — said so plainly rather than pretending otherwise.

**MedLou Health** · Jelly Health + Forma Health, "follow these examples" — **the
third rejection, and the one that built the gate**
→ Palette right, serif right, **every device wrong**. Overlay chips on the
photo, labelled tinted cards, a bento with a large tile, circular arrow
buttons — none of them shipped. The root cause was that **nothing measured
design**. `design-spec.json` + `check_fidelity.py` exist because of this build.

**Alpha Wolf Labs** · RUO peptide store · silverstatebiolabs.com in structure
mode, brand colours from the logo, "don't make it completely dark"
→ 26 templates. **114 deliberate placeholders.** Eight policy pages written to
the right shape (~6,600 words) with every jurisdiction, window, carrier and
processor left blank — never guessed. `/testing-process/` never names the
testing laboratory, because that is the most load-bearing unverified claim on
the site and the entire proposition follows from it.

**DualCore Peptides** · Shopify→Woo migration · alphahealthco.com, "the design I
like but in client branding colours"
→ The existing store family was **dark**; this reference is **light with every
dark block inset and rounded**. Reusing it would have shipped the wrong design
in the right colours, so a new 11-component family was written.
→ **The judgement call worth re-reading:** the reference's CTA pill is warm
amber precisely so it separates from the teal. A blue accent inside a blue brand
merges with the primary and the device dies — so the accent became the logo's
brightest cyan, flagged as a one-hex change.
→ **The gate earned its keep here:** a `--strict`-green build still failed
because a banned component had leaked into four inner pages.

**Wasatch Unlimited** · Utah remodeler · **two references that contradict each
other and the written scope**
→ Split by **layer, not compromise**: one supplied the structural devices, the
other the register. Structural devices are palette-independent — that is what
makes it work.
→ A **pure-white wordmark on transparency** forced both the palette and a dark
header. Crawling the live site produced the real contact details, the 301 map,
two HTTP 500 service URLs still linked from their homepage, and no H1 anywhere.

**Magic Renovations** · New Orleans contractor · **no design reference at all**
→ `mode: "specified"` — the spec *states* the device system instead of
extracting one, so the gate still means something. **The logo did the design
work:** black is a spotlight not a ground, gold only ever a rule/numeral/button,
a caps eyebrow over a short gold rule as the signature.
→ **The client's blanks became the deliverable** — README §1 retitled *"What I
still need from you"*.
→ Google reviews are a **shortcode slot, never authored cards**; every
review-rendering component is banned globally for a truth reason, not a design
one.

**Metroline Plumbing** · DC/MD/VA plumber · **a brand banner as the reference**
→ **Look at every supplied brand asset before concluding there is no
reference.** The banner had already decided the ground, the photography, the
corner arcs and the red bar. The arcs were rebuilt from containers — 14 rings,
clipped by `overflow: hidden` — so they recolour with the palette.
→ A late layout deck **overrode delivered work**, including deleting a page.
→ **The client's service list is the whole service list.** Five invented
services were removed. **Supplied hours can retire a positioning:** Mon–Fri 8–6
means nothing on the site may claim 24/7.
→ **Red is an accent, never a field**, and **the phone is a button, not header
text** — two rules for any plumbing/HVAC build.

**Live Fatima** · Confraternity of Our Lady of Fatima · extension build onto a
live dev site
→ The dev site already ran the forge's own global kit — same colours, same token
ids — so new pages inherited the live palette with no seam. **Check this on
every extension build.**
→ The brief's hard constraint (no AI imagery of sacred subjects) was being
breached by their own live homepage. Flagged; their call, made knowingly.
→ The Consecration page later arrived as **finished copy with no layout at
all** — the right move was to inherit the shape from the two built pages rather
than invent one, and to add exactly one new device (the thirty-three days as
day-range stages) because the existing numbered component would have run a
second numbering system beside the copy's own.

**PeptideLaunch** · the studio's own peptide theme shop · **a logo and a
publish-ready copy document, no reference**
→ **A copy document can be a design brief.** Three devices existed because the
copy asked for a *shape* prose cannot carry: a real comparison matrix, product
cards with two CTAs (demo and buy are different intents), and an ROI block with
the arithmetic left in.
→ The logo's one-solid-node-in-four became the palette rule.
→ **Kept the client's own `$[X]` convention** rather than inventing prices — 50
placeholders, inventoried by token and document.

---

## Toolchain cases

**Row geometry** — percentage widths survive nesting, pixel gaps do not. 63
desktop + 313 tablet overflows across 11 shipped kits, all marginal (100.1–101.6%),
which is why it read as flakiness. Fixed with `nowrap` when the children were
sized for one line, real tablet stacking, and a validator rule that measures the
row's true width after nesting.

**Container controls** — `max_width` and `height` are silently ignored on
containers and had never applied on 103 + 13 call sites. The validator only
checked widgets. → **Validate every element type, not the interesting one.**

**Motion as a compile stage** — entrance animations cannot live in a component
factory: a factory sees one section and cannot know whether it is first on the
page, and stagger is a property of a row's children as a set. Rules that each
encode a way it goes wrong: exempt the first section (an animation starts at
opacity 0 — above the fold that is a flash of empty page), exempt header and
footer (they replay on every navigation), one animation per branch (a fading
section full of fading cards double-fades), stagger only rows of 3+.

**The schedule-fields bug** — a planner branch built a booking form without
passing its fields. Silent: the page rendered a working form, just the wrong
one. → Diff the IR, not the compiled output; element ids are randomised.

**The store family** — 33 components split by template area rather than more
lines in a 6,000-line file. `store.prose` renders eight legal pages from JSON
with no code per page, plus a sticky table of contents built from its own
headings — long-form prose is normally where a template kit gives up.

**Registry gaps** — per-skin controls are invisible to a PHP scrape (76
recovered by mining a real shipped kit); WooCommerce dynamic tags are absent
entirely, so a custom product card **cannot be verified** and guessing produces
a grid that imports empty — which reads as the client's data entry, not as a
template bug.

---

## Plugin cases

**COA Manager** — one extra bracket inside a `var()` fallback painted three
brand elements with no background at all, silently, across releases. → Count
parens as well as braces on any CSS edit.

**Age Compliance Gate** — the overlay is the stronger mechanism (it never sends
gated content to the browser); the interstitial exists because a confirmation
URL can be linked and screenshotted for a compliance file. Neither is age
*verification*, and saying so is part of the deliverable. Four non-guessable
requirements in `04-GOTCHAS.md`.

**P2P Payments / Cash Pay** — Zelle has no e-commerce API at all; Venmo permits
selling only through a Business Profile; Cash App Pay runs through processors
**whose prohibited-business lists are the live risk** for a research-chemical
store. So these can only ever be manual/offline gateways, and the consequence to
keep raising is that stock is reduced at checkout while nothing authorises
payment. → **Block checkout support is mandatory, not a nicety.**
→ Shipping its own pure-PHP QR encoder was the point: the alternatives leak
every customer's payment details to a third-party image service, or cannot
render in the order email — which is exactly where someone paying by bank
transfer looks an hour later.
