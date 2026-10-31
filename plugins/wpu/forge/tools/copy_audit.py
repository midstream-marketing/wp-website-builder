#!/usr/bin/env python3
"""
wu_copy_audit.py — measure the built kit against the copy standard.

Runs on the COMPILED templates, not on the copy JSON, so it audits what a
visitor actually gets rather than what the source intended. Three checks:

  1. Word count per page against the floors in copy-and-seo-standard.
  2. Exactly one H1 per page.
  3. The scope's banned vocabulary (section 24) and the usual AI tells.

Usage:  python tools/wu_copy_audit.py clients/wasatch-unlimited/out
Exit 1 if anything fails, so it can gate a build like the validator does.
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

# copy-and-seo-standard, "Word-count floors (measured, not guessed)".
# Keys are document names; anything not listed and not exempt is unchecked.
FLOORS = {
    "home": 800,
    # magic-renovations
    "services": 700,
    "request-an-estimate": 300,
    # metroline-plumbing
    "gallery": 400,
    "service-areas": 700,
    "basement-finishing-remodeling": 700,
    "home-remodeling": 700,
    "additions-adus": 700,
    "service-areas": 700,
    "about": 600,
    # live-fatima
    "ways-to-give": 600,
    "consecration": 700,
    # peptidelaunch. A theme shop's product pages carry less prose than a
    # service page by design - the comparison table and the product cards do
    # the work - so those floors sit lower than /hire-us/, which is the money
    # page and has to argue.
    "themes": 500,
    "themes-free": 500,
    "themes-premium": 600,
    "plugins": 500,
    "hire-us": 800,
    "projects": 400,
    "our-process": 400,
    "faq": 400,
    "contact": 300,
}
# PER-CLIENT OVERRIDES, and the reason they exist.
#
# FLOORS is keyed by document name, which collides the moment two clients ship
# a page with the same stem. That happened on 2026-09-09: peptidelaunch's
# `/resources/` is a hub at 400 and live-fatima's is a 16-item library at 600,
# and because a dict keeps the LAST duplicate key, the second entry silently
# won and live-fatima was audited against the wrong floor. A green audit is not
# evidence when the thing being audited was resolved wrongly.
CLIENT_FLOORS = {
    # Mow N More (Topeka). Four pages by the brief; Services carries all six
    # services as anchored rows and is the money page.
    "mow-n-more": {"home": 800, "services": 700, "contact": 300, "book-an-appointment": 300},
    # Lakes Construction (Windermere). Seven service pages and eight area
    # pages are the money pages and are held to the money-page floor; the
    # area pages carry town-specific planning and building notes so they are
    # not near-duplicates. Legal and utility pages follow their documents.
    "lakes-construction": {
        "home": 800, "services": 400, "areas": 400, "about-us": 450,
        "our-projects": 300, "gallery": 80, "contact-us": 300,
        "schedule-an-appointment": 300,
        "extensions": 700, "eco-extensions": 700, "garden-rooms": 700,
        "new-builds": 700, "planning-and-architectural-drawings": 700,
        "jetties": 700, "commercial-builds": 700,
        "windermere": 650, "bowness-on-windermere": 650, "ambleside": 650,
        "kendal": 650, "grasmere": 650, "hawkshead": 650, "coniston": 650,
        "keswick": 650},
    # Easy Gebäudeservice. Five pages; Services carries all eight services
    # as anchored rows and is the money page. The legal pages follow the
    # documents and carry no floor.
    "easy-gebaeudeservice": {"home": 800, "services": 700, "contact": 300},
    # MODELS ON TOUR. A MARKETPLACE, where the default 800-word home floor
    # is an article floor and wrong - the matched mockups are grids, and
    # padding them would break the match. Home and About carry the real
    # argument and are held to a sensible number; the listing and detail
    # templates are interface fed by custom post types and carry none.
    "models-on-tour": {
        "home": 500, "about": 450, "for-models": 200},
    # VYBE OC Delivery. An ECOMMERCE kit, where the default 800-word home
    # floor is the wrong instrument - the matched mockup is a product grid,
    # and padding it with prose would break the match this build exists to
    # deliver. The floors below are set to what each page type should
    # actually carry: a shop landing with real delivery/ID copy beneath the
    # grid, and genuine content pages held higher. Cart, checkout, product
    # and archive are interface, not prose, and carry no floor at all.
    "vybe-oc": {
        "home": 450, "delivery-areas": 400, "faq": 400},
    # Prolific Roofing. A four-page kit for a company twelve months old, so
    # there is no archive to lean on and every page has to stand up on its
    # own. The Services page carries all five services as anchored bands,
    # which is why its floor is the money-page one.
    "prolific-roofing": {
        "home": 800, "services": 700, "contact-us": 300,
        "schedule-an-appointment": 450},
    # Scottsdale Tree Trimmers. Most pages carry thousands of words of the
    # client's preserved content and clear any floor easily; the floors that
    # matter here are on the NEW pages, which have no preserved half to lean
    # on and must stand up by themselves.
    "scottsdale-tree": {
        "home": 800, "about-us": 700, "services": 700,
        "areas-we-serve": 450, "blog": 450, "contact": 300,
        "book-an-appointment": 450,
        "queen-palm-care": 600, "deep-root-fertilization": 600,
        "commercial-tree-trimming": 700},
    # 6-page build written without a client copy document. The Gallery is a
    # real content page here rather than a grid of captions, so it carries a
    # higher floor than the usual 400.
    "medina-radiant": {
        "home": 800, "about-us": 600, "services": 700, "gallery": 500,
        "contact-us": 350, "book-an-appointment": 400},
    # 13-page build from the client's own copy document. The six sub-service
    # pages are the money pages and carry the local keyword each, so they get
    # the money-page floor rather than being left unchecked - the supplied
    # copy ran about 350 words each, which is under what ranks.
    "ie-homebuilders": {
        "home": 800, "about-us": 600, "services": 700,
        "kitchen-remodeling": 700, "bathroom-remodeling": 700,
        "home-additions": 700, "new-home-construction": 700,
        "whole-home-renovation": 700, "commercial-construction": 700,
        "contact-us": 300, "schedule-an-appointment": 350},
    "live-fatima": {"resources": 600, "apostolates": 500},
    "peptidelaunch": {"resources": 400},
    # Single-page sub-domain sites. The AML page is a long-form money page and
    # carries the whole sales argument, so it is held above the 700 floor.
    "elite-property": {"aml": 900, "aml-worldwide": 900, "join": 300},
    "gene-lee-skin-clinic": {
        "home": 800, "about-dr-gene-lee": 600,
        "advanced-injectables": 700, "laser-rf-remodeling": 700,
        "body-contouring": 700, "medical-weight-loss": 700,
        # A product page argues less than a service page; the product panel
        # and its details do the work.
        "glow-rx": 450, "concierge": 600, "new-patients": 600,
        "contact": 300},
    "edit-by-edita": {"home": 800, "services": 700, "contact": 300},
    # 14-page SEO build. The three service pages are the money pages and are
    # held highest; the four city pages must carry genuinely local copy, not
    # a city name swapped into a template, so they get a real floor too.
    "prorevive-construction": {
        "home": 1000, "about": 650, "services": 650,
        "water-damage-reconstruction": 900, "kitchen-remodeling": 900,
        "bathroom-remodeling": 900, "areas-we-serve": 500,
        "tacoma-wa": 650, "olympia-wa": 650, "puyallup-wa": 650,
        "federal-way-wa": 650, "gallery": 400, "portfolio": 600,
        "contact": 300,
        "book-an-appointment": 350},
    # 4-page trade site built on the client's own copy. The service pages
    # carry long client-written service lists and are held at the money-page
    # floor; home is the hub.
    "des-group": {"home": 800, "hvac": 900, "commercial-hvac": 900,
                  "plumbing": 1000, "roofing": 800},
    # Local-SEO lead-gen site. Four money pages held at the service-page
    # target; the gallery ships as real-project placeholders, so it argues
    # less and is held lower.
    "onsight-window-films": {
        "home": 1100, "commercial-window-film": 1000, "residential-window-film": 1000,
        "safety-security-window-film": 1000, "decorative-privacy-window-film": 900,
        "about": 650, "gallery": 400, "get-a-free-estimate": 450},
    # 3-page starter site. Two money pages carry the whole argument, so
    # both are held at the service-page target; the estimate page is a form.
    "gk-exteriors": {"home": 900, "services": 1100, "free-estimate": 450},
    # Single-page landing site: one page carries everything, so it is held
    # at the money-page target rather than the 800 home floor.
    "truair-hvac": {"home": 900},
    # 25-document roofing kit built from the client's own copy doc.
    # The 18 sub-service pages share one layout, so the floor is what
    # stops them collapsing into eighteen copies of a stub.
    "economy-roofing": {
        "home": 950, "services": 650, "about": 600, "contact": 300,
        "book-an-appointment": 270,
        "rubber-roof-repair": 270, "flat-roof-services": 270, "patching-leaks": 270,
        "metal-roof-repair": 270, "asphalt-shingle-roof-repair": 270, "slate-roof-repair": 270,
        "new-roof-installation": 270, "full-roof-replacement": 270, "slate-roof-replacement": 270,
        "residential-roofing": 270, "new-construction-roofing": 270, "custom-roofing": 270,
        "roof-inspection": 270, "emergency-roofing": 270, "roof-maintenance-gutter-cleaning": 270,
        "skylight-installation-repair": 270, "chimney-flashing": 270, "specialty-services": 270,
    },
    # WooCommerce kit. Only the three CONTENT pages carry a floor; cart,
    # checkout, the single-product and the archive are functional
    # templates whose real words come from the products themselves.
    "black-bear-labs": {"home": 1000, "contact": 320, "shop": 350},
    # 14-page salon. The seven category pages are the money pages and
    # each carries its own treatment list, benefits and FAQs; the floor
    # stops them collapsing into seven copies of a hub page.
    "look-lovely": {
        "home": 850, "about": 640, "services": 700, "prices": 580,
        "gallery": 400, "contact": 330, "book-an-appointment": 480,
        "makeup": 550, "hair": 550, "lashes-brows": 550, "nails": 550,
        "facials-skincare": 550, "body-spa": 550, "cosmetic": 550,
    },
    # 4-page logo-specified build. Home is the hub and carries the whole
    # argument; services is the money page. The contact page is held low on
    # purpose - padding a contact page is how you make it worse.
    "ee-custom-renovation": {
        "home": 1100, "services": 950,
        "contact-us": 330, "schedule-an-appointment": 450},
    # 51-document local-SEO build: 15 service pages and 27 town pages.
    # Both sets are generated from one template each, so the floors are what
    # stop a future edit quietly turning them back into thin doorway pages.
    # Measured floors, set just under what the build actually produces.
    "weather-warrior": {
        "home": 1000, "about": 700, "services": 750, "gallery": 400,
        "areas-we-serve": 500, "contact": 380, "schedule-appointment": 420,
        "roof-repair": 650, "roof-replacement": 650, "new-roof-installation": 650,
        "residential-roofing": 650, "emergency-roofing": 650, "metal-roofing": 650,
        "tile-roofing": 650, "flat-roofing": 650, "gutters": 650,
        "soffit-and-fascia": 650, "siding": 650, "attic-ventilation": 650,
        "exterior-painting": 650, "pressure-washing": 650, "fencing": 650,
        "san-antonio": 520, "new-braunfels": 520, "seguin": 520, "canyon-lake": 520,
        "schertz": 520, "converse": 520, "universal-city": 520, "live-oak": 520,
        "helotes": 520, "bulverde": 520, "spring-branch": 520, "bandera": 520,
        "castroville": 520, "macdona": 520, "von-ormy": 520, "adkins": 520,
        "lytle": 520, "elmendorf": 520, "atascosa": 520, "somerset": 520,
        "st-hedwig": 520, "la-vernia": 520, "fair-oaks-ranch": 520, "timberwood-park": 520,
        "medina-lake": 520, "lake-hills": 520, "kirby": 520,
    },
}


def floor_for(client, key):
    return CLIENT_FLOORS.get(client, {}).get(key, FLOORS.get(key))


# Chrome and utility documents carry no prose target of their own.
EXEMPT = {"header", "footer", "global", "404", "privacy-policy"}

# Theme Builder documents carry no prose of their own - their words come from
# whatever post is being displayed - so a word floor is meaningless for them.
TEMPLATE_DOCS = {"archive", "single-post", "single", "search-results", "loop-item"}

# ...and their H1 is a DYNAMIC widget, not a `heading` with header_size=h1.
# Counting only heading widgets false-failed every theme-builder template.
DYNAMIC_H1 = {"theme-post-title", "theme-archive-title", "theme-page-title",
              # A product template's H1 is the product name, which is as
              # dynamic as a post title and was simply never added here.
              "woocommerce-product-title"}

# Scope section 24, verbatim, plus the tells from the copy standard.
BANNED = [
    "trusted partner", "quality is our top priority", "turning dreams into reality",
    "one-stop shop", "for all your construction needs", "unparalleled craftsmanship",
    "in today's fast-paced world", "we understand that", "look no further",
    "nestled in", "elevate your", "unlock", "seamless", "cutting-edge",
    "delve", "moreover", "in conclusion", "state-of-the-art", "peace of mind",
    "attention to detail", "second to none", "dream home",
]

# A few banned words are marketing filler in one sense and the ordinary name
# of a real thing in another. "Seamless" as an adjective ("a seamless
# experience") is the tell the list is hunting; "seamless gutter" is what the
# product is called, what the manufacturer calls it, and what a homeowner
# types into Google. Banning the noun would cost a roofer their own service
# name to satisfy a lint rule.
#
# So a banned term only counts where it appears OUTSIDE its allowed
# collocations. Add a sense here only when the word is genuinely a term of
# art in that phrase - not to smuggle the filler sense past the check.
SENSES = {
    "seamless": ("seamless gutter",),
}


def banned_hit(term, text):
    """True when `term` occurs in `text` in a sense the list actually bans."""
    total = text.count(term)
    for ok in SENSES.get(term, ()):
        total -= text.count(ok)
    return total > 0


# Documents whose copy is the CLIENT'S OWN PUBLISHED TEXT, reprinted whole.
#
# The banned list hunts marketing tells written by us. It is the wrong
# instrument for a page that reproduces a client's existing article: Live
# Fatima's Sacrament of Penance page is 15,000 words of traditional catechesis
# in which "moreover" is ordinary period prose, and no honest fix exists -
# editing it would be editing the client's doctrine to please a lint rule.
#
# So these documents are exempt from the BANNED check ONLY. Word floors, the
# one-H1 rule and the placeholder count still apply, and the report prints the
# exemption on the row rather than passing them silently.
VERBATIM = {
    "live-fatima": {
        "sacrament-of-penance", "examen-adults", "examen-children",
        "praying-the-rosary", "brown-scapular", "five-first-saturdays",
        "simple-acts-of-penance", "consecration-to-mary", "apparitions",
        "prayer-triumph", "faqs",
    },
    # Scottsdale Tree Trimmers. These pages carry the client's EXISTING
    # article content, reproduced verbatim, because the brief is explicitly
    # about not losing a Page 1 Position 2 ranking that content earns. Their
    # own copy happens to contain "attention to detail", "peace of mind" and
    # "we understand that" - and rewriting a ranking page to satisfy a lint
    # rule is precisely the thing this build must not do.
    #
    # The NEW copy on these same pages is still checked: build_ir.py runs
    # the banned list against copy.json alone, so filler written by us is
    # caught there instead of here.
    "scottsdale-tree": {
        "home", "about-us", "tree-trimming", "tree-removal",
        "cactus-removal", "saguaro-cactus-removal",
        "commercial-tree-trimming", "tree-care-paradise-valley-az",
    },
}

TEXT_KEYS = ("title", "editor", "text", "tab_content", "description_text",
             "field_label", "placeholder", "button_text")


def strings(node, out):
    """Every human-visible string in a compiled document.

    REPEATER ITEMS COUNT TOO (fixed 2026-09-11). This used to read text only
    from an element's own `settings`, so everything inside a list — icon-list
    ticks, pricing features, footer links, accordion titles, form labels — was
    invisible to BOTH the word count and the banned-phrase check. Found when
    an elite-property build carrying "REGULATORY PEACE OF MIND" in a tick list
    passed as "no banned copy". A repeater item is a dict with an `_id` and no
    `elType`; its text keys are harvested directly.
    """
    if isinstance(node, dict):
        wt = node.get("widgetType")
        st = node.get("settings", {}) or {}
        for k in TEXT_KEYS:
            v = st.get(k)
            if isinstance(v, str) and v.strip():
                out.append((wt, st.get("header_size"), v))
        if "_id" in node and "elType" not in node:
            for k in TEXT_KEYS + ("item_title", "tab_title"):
                v = node.get(k)
                if isinstance(v, str) and v.strip():
                    out.append(("repeater", None, v))
        for v in node.values():
            strings(v, out)
    elif isinstance(node, list):
        for v in node:
            strings(v, out)
    return out



def widget_types(node, out):
    """Every widgetType in the document, regardless of whether it carries text.

    Needed because a Theme Builder H1 is a dynamic widget with no text
    setting of its own - the text extractor above never sees it.
    """
    if isinstance(node, dict):
        wt = node.get("widgetType")
        if wt:
            out.append(wt)
        for v in node.values():
            widget_types(v, out)
    elif isinstance(node, list):
        for v in node:
            widget_types(v, out)
    return out


def clean(html):
    t = re.sub(r"<[^>]+>", " ", html)
    t = (t.replace("&mdash;", " ").replace("&nbsp;", " ")
          .replace("&amp;", "&").replace("&#8212;", " "))
    return re.sub(r"\s+", " ", t).strip()


def main(outdir):
    tpl = Path(outdir) / "templates"
    if not tpl.is_dir():
        print("no templates/ in " + str(outdir))
        return 1

    # clients/<slug>/out -> "<slug>"
    parts = Path(outdir).resolve().parts
    client = parts[parts.index("clients") + 1] if "clients" in parts else ""

    fails, rows = [], []
    for f in sorted(tpl.glob("*.json")):
        key = f.stem
        doc = json.loads(io.open(f, encoding="utf-8").read())
        found = strings(doc.get("content", []), [])
        types = widget_types(doc.get("content", []), [])

        words, h1s, blob = 0, 0, []
        for wt, size, raw in found:
            txt = clean(raw)
            if wt == "heading" and size == "h1":
                h1s += 1
            words += len(txt.split())
            blob.append(txt.lower())

        # A Theme Builder document's H1 is a dynamic widget.
        h1s += sum(1 for t in types if t in DYNAMIC_H1)

        joined = " ".join(blob)
        verbatim = key in VERBATIM.get(client, set())
        hits = [] if verbatim else sorted({b for b in BANNED if banned_hit(b, joined)})
        floor = floor_for(client, key)
        placeholders = joined.count("placeholder")

        status = []
        if floor and words < floor:
            status.append("THIN %d<%d" % (words, floor))
            fails.append("%s: %d words, floor %d" % (key, words, floor))
        if key in TEMPLATE_DOCS:
            floor = None
        if key not in EXEMPT and h1s != 1:
            status.append("H1=%d" % h1s)
            fails.append("%s: %d H1s, expected exactly 1" % (key, h1s))
        if hits:
            status.append("BANNED: " + ", ".join(hits))
            fails.append("%s: banned phrase(s) %s" % (key, ", ".join(hits)))
        if verbatim:
            status.append("verbatim (banned check skipped)")

        rows.append((key, words, floor or 0, h1s, placeholders,
                     "; ".join(status) or "ok"))

    print("client: %s" % (client or "(unknown)"))
    print("%-32s %6s %6s %4s %6s  %s" %
          ("page", "words", "floor", "h1", "plchdr", "status"))
    print("-" * 92)
    for key, words, floor, h1s, ph, status in rows:
        print("%-32s %6d %6s %4d %6d  %s" %
              (key, words, floor or "-", h1s, ph, status))

    total = sum(r[1] for r in rows)
    print("-" * 92)
    print("%d documents, %d words total" % (len(rows), total))

    if fails:
        print("\nFAIL")
        for x in fails:
            print("  " + x)
        return 1
    print("\nPASS - every page meets its floor, one H1 each, no banned copy.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1
                  else "clients/wasatch-unlimited/out"))
