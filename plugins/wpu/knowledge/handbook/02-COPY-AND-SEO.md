# 02 — Copy and SEO

Standing requirement on **every** build, not a one-off pass. Audit before the
handoff document is written, and treat a thin page as a build failure the same
way a compile error is.

---

## 1. Word-count floors — measured, not guessed

| Page type | Floor | Target |
|---|---|---|
| Money / service page | 700 | 900–1,200 |
| Location / area page | 700 | 800–1,000 |
| Home | 800 | 900–1,200 |
| About | 600 | 700–900 |
| Hub / index page | 400 | 500–700 |
| Contact / utility | 300 | 400–600 |
| Product / catalogue page | 500 | 600–900 |
| Policy / legal | — | length follows the document |
| Theme Builder templates (archive, single, header, footer) | exempt | their words come from the post being rendered |

Anything under its floor is a **rewrite, not a tweak**. Measured on real builds:
AirFusion shipped 13 of 15 pages thin on the first pass (5,392 → 11,269 words
after the rewrite); alpha-wolf-labs had 4 of 20; magic-renovations 3.

**Padding to hit the number is the failure mode, not the goal.** Depth comes
from `00-SOUL.md` §6 — the domain, never the company.

### Location pages are the standing trap

Four area pages at ~230 words with the city name swapped is the doorway pattern
Google explicitly discounts. Every location page needs something **only true of
that place**: the local trade mix, the climate or building stock, named
neighbourhoods, why demand differs there.

Measure it. AirFusion's rewritten area pages overlap only **5.1–6.0% on 5-gram
shingles**; Falis's 19 service pages max out at **6.7% across all 190 pairs**.
If that cannot be written truthfully, consolidate into one page with anchored
sections rather than shipping near-duplicates — and say so.

---

## 2. What makes copy read as human

- **Lead with the specific, not the category.** "A fryer down mid-service costs
  covers, not parts" beats "we offer quality commercial kitchen repair".
- **Name the real failure modes, numbers and trade-offs** a practitioner would
  know. Concrete detail is the strongest available signal of genuine expertise.
- **Vary sentence length.** Uniform medium-length sentences are the giveaway.
- **Say something falsifiable.** A page that could be about any company in the
  trade is thin regardless of length.
- **Cut the tells.** The banned list is in `00-SOUL.md` §9 and is enforced by
  `copy_audit.py`; add per-client bans from the client's own scope document.
- **Never invent facts to reach depth.** See `00-SOUL.md` §2.

### Two structural moves that create honest depth

**Say what the page does not say.** DualCore's `/we-test/` carries a section
literally headed *"What this page does not yet say"*, naming the laboratory and
the methods as outstanding. It is more credible than the vague version, and it
is a live ask-list for the client.

**Explain the constraint, not the capability.** "In a niche without paid ads,
organic is the channel that decides who wins" does more work than any list of
SEO services.

---

## 3. Structure — verify per page, never assume

- Exactly **one H1**, containing the focus keyword. Verify by counting; do not
  assume the template did it.
- H2/H3 nested properly, no level skipped; the keyword or a variant in some H2s.
- Descriptive internal anchor text — never bare "click here" / "read more".
- FAQ blocks carry FAQ schema **where the Q&A is really on the page**.
- Every page links to at least one of the site's money pages. Internal links are
  load-bearing for the keyword map, not decoration — say so where the copy is
  handed over for editing.
- Every image slot gets alt text written from the photo brief, plus a
  recommended SEO filename (`commercial-hvac-rooftop-orlando.jpg`).

**A dynamic H1 is still an H1.** Theme Builder documents (archive, single post)
carry their H1 as a dynamic widget with no text of its own, so a naive text
scan reports "0 H1s" and fails every template. Count widget types as well as
text, and exempt template documents from the word floor.

---

## 4. The SEO sheet is a default deliverable

One per client, one section per page, shaped so it can be typed straight into
Yoast or Rank Math:

- **Focus keyword** — one per page, and **no two pages competing**. Write down
  how the cannibalisation is avoided (e.g. the hub takes the broad term, the
  children take the modifiers).
- Secondary keywords
- **SEO title**, ≤60 characters — measured, with the count shown
- **Meta description**, 120–155 characters — measured, active, with the CTA
- Slug · H1 · schema types · word count against floor
- The alt-text + filename table for every image slot
- A deploy checklist: which schema goes where, and what must **not** be marked
  up yet

**Measure the lengths, do not estimate them.** A supplied set of six meta
descriptions ran 156–164 characters; Google truncates around 155 and what gets
cut is the end, which is where the call to action lives.

**Flag, do not silently rewrite, a client's H1.** Where the focus keyword is not
in the client's own H1, say so, explain why it might be deliberate (a brand or
entity page is doing a different job), and offer the alternative wording.

### Schema discipline

- **No `AggregateRating` until real reviews exist.** Marking up ratings you do
  not have is a manual-action risk.
- **No `Product` schema with a placeholder price.** Worse than none.
- `Organization` with `parentOrganization` is the link that makes two brands one
  entity to a search engine — use it wherever there is a parent company.
- A canonical **entity line** (one sentence describing what the business is)
  goes in the footer, the About page, and every external profile — **verbatim,
  never paraphrased**. That consistency is the whole point.

---

## 5. Placeholder discipline

Every unverifiable fact ships as a visible, greppable marker. Then the marker
list goes in the handoff document, ordered by what blocks launch.

**Conventions that worked:**

- `PLACEHOLDER` as a bare token, or `_PLACEHOLDER_PHONE` for a keyed value.
- If the client's own brief uses a convention (`$[X]`), **keep theirs** — do not
  invent a parallel one. Inventing a price would be worse than showing a blank.
- Reserved fictional numbers for phones where one is structurally required:
  US `555-01xx`, UK Ofcom drama range `020 7946 0958`.
- Count them and publish the count: *"64 visible placeholders"*, *"114 in the
  kit and every one deliberate"*, *"50, inventoried by token and document"*.
- Ship the grep so they can re-check after editing:

```bash
grep -o '\[[^]]\{1,24\}\]' out/templates/*.json | sort | uniq -c | sort -rn
grep -rn 'PLACEHOLDER' out/
```

**Keep them all in one source file** so they are filled once and rebuilt, never
edited across dozens of compiled outputs.

**The dangerous ones**, in order: a licence number on a licensed trade,
invented testimonials, a business address that feeds schema and maps, legally
operative policy text, and any loyalty or refund term (a financial promise).

---

## 6. Images

**An empty slot with a written brief beats a wrong image**, and the reason is
mechanical: *a URL that 404s at import makes the builder substitute its own
placeholder, which is indistinguishable from an unfilled slot.* So a broken
stock URL is strictly worse than nothing.

- Ship every slot with **real alt text** even when the URL is empty. Nothing is
  lost when the file arrives — you replace the file, not the metadata.
- Put the subject brief for each slot in the intake file, and the sourcing route
  in the handoff document.
- Where the client hosts images themselves, the upload must happen **before**
  the import, and month-based upload paths break every URL if the upload slips
  into a different month.
- Normalise supplied camera rolls first: files named `.jpeg` that are really
  HEIC are rejected outright by WordPress; files named `.png` that are really
  JPEG are common. Convert, resize, rename descriptively, leave originals alone.
- **Filter stock out of a client's own media library** before reusing it, and
  exclude anything that would misrepresent the work.
- Where a device needs matched pairs (before/after), build it and switch it
  **off** behind a flag — a comparison slider with two empty frames is a
  *broken* widget, not an empty one.
- Photo advice worth repeating to any trade client: **the persuasive photos are
  the rough-in before it is covered**, not the finished fixture. It is the only
  proof of the half of the job nobody sees, and it cannot be recreated later.
- Where a brief bans AI imagery of a subject, that ban survives contact with an
  empty slot. Ship the slot empty with a sourcing plan — own photography, the
  subject's own comms office, licensed stock with the right catalogue, or
  genuinely public-domain work.
