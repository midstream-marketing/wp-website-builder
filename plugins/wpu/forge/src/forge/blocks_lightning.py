"""
blocks_lightning.py — Lightning Peptides LLC, homepage.

The client asked for their homepage rebuilt to match https://www.ascend.science/
device for device, in their own brand colours. So this family is a direct
transcription of that reference's vocabulary, with every navy and blue mapped
onto Lightning's black and lightning yellow:

    ascend.science                     Lightning Peptides
    ------------------------------     --------------------------------------
    navy #17233F bands and footer      black #0B0B0B
    blue #2A6AD0 fills and accents     lightning yellow #F5D34C (fills),
                                       gold #D3A32C (tiles, badges, rules)
    pale-blue gradient grounds         cream #FEFCF2
    white cards on the tinted ground   unchanged - white cards
    amber review stars                 gold #D3A32C
    Inter throughout                   Archivo headings over Inter body

One measured adjustment, the same call the TruAir build made: gold TEXT uses
`lpgld1` #A8790F, because the brand gold is 2.6:1 on cream and fails even the
large-type floor. Fills keep the brand gold. The hue does not move.

Devices, in the order the reference runs them:

    lp.ticker      gold offer/trust strip under the header
    lp.hero        two-tone headline, two pills, trust chips, floating vials
    lp.claimbar    the dark full-bleed claim band
    lp.products    Featured Products, WooCommerce grid + "View all"
    lp.verify      "How to verify each product" - image left, numbered right
    lp.quality     "Every batch tested" - stats, numbered card grid, banner
    lp.why         "Why choose ..." - six icon items, three up
    lp.reviews     "Real Researchers, Real Reviews" - carousel on dark
    lp.closer      the closing line with a vial either side

MOTION. The reference's dominant animation is `reveal-rise` (0.8s fade-and-rise
on 51 elements) with a stagger across card rows. That is exactly what this
repo's motion stage emits - `ir["motion"] = {"preset": "reveal"}` gives
fadeInUp on every section after the first, staggered across card rows - so it
is NOT hand-rolled here. The hero's three vials are the one exception: the
first section is deliberately skipped by that stage, so their entrance is set
on the widgets themselves.

Two of the reference's animations are NOT reproducible on core + Pro controls
and are not faked: the continuous `marquee-scroll` ticker, and the two review
rows that scroll in opposite directions (`reviews-left` / `reviews-right`) -
the testimonial carousel has no direction control. Both are recorded as
partials in design-spec.json.
"""
from __future__ import annotations

from .core import (
    container, widget, repeater_item, slider, dims, box, media, link,
    gap, color_ref, typo_ref, icon,
)
from .tokens import C, T
from .blocks import (
    block, _row, _col, _tracks, _button, _text, KIT_CONTAINER,
)

# brand.extra_colors ids from clients/lightning-peptides/intake.json.
GOLD_TEXT = "lpgld01"     # #A8790F - gold that passes on cream
INK_DARK = "lpink01"      # #F7F3E4 - body text on the black bands

LP_PAD = dims(92, 0, 92, 0)
LP_PAD_T = dims(68, 24, 68, 24)
LP_PAD_M = dims(54, 20, 54, 20)
R_CARD = box(14)         # measured off the reference: 14px dominates
R_PANEL = box(18)
R_PILL = box(999)
LP_GUTTER = 22


# ─────────────────────────────── helpers ───────────────────────────────────

def _lp_section(children, bg="cream", pad=None, anchor=None, extra=None):
    grounds = {"cream": C["surface"], "white": C["surface_alt"],
               "dark": "primary", "gold": "secondary"}
    s = {
        "content_width": "boxed",
        "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "flex_gap": gap(34),
        "padding": pad or LP_PAD,
        "padding_tablet": LP_PAD_T,
        "padding_mobile": LP_PAD_M,
        "background_background": "classic",
    }
    if anchor:
        s["_element_id"] = anchor
    if extra:
        s.update(extra)
    return container(children, s, globals_={
        "background_color": color_ref(grounds.get(bg, C["surface"]))})


def _dark(bg):
    return bg == "dark"


def _head(text, size="h2", token=None, align="left", on_dark=False,
          color=None):
    """A heading in Archivo. Colour is explicit, never inherited.

    `blocks._heading` colours its default headings with the `secondary`
    global, which on most brands is the dark ink. On THIS brand secondary is
    lightning yellow, so every heading here names its own colour.
    """
    return widget("heading", {
        "title": text, "header_size": size, "align": align,
        "__typography__": typo_ref(token or T["h_medium"]),
    }, globals_={"title_color": color_ref(
        color or (C["white"] if on_dark else "primary"))})


def _two_tone(lead, highlight, size="h2", token=None, align="left",
              on_dark=False, tail=""):
    """The reference's signature headline: one word in the accent, the rest in
    ink, on the same line.

    Built as two (or three) heading widgets in a wrapping row rather than one
    heading carrying a coloured `<span>`, because a span means inline CSS and
    this repo emits none. The row wraps exactly where the text would.
    """
    token = token or T["h_large"]
    segs = [(lead, False), (highlight, True)]
    if tail:
        segs.append((tail, False))
    segs = [(t, hl) for t, hl in segs if t]

    # ONE of these widgets carries the real heading tag and the rest are
    # divs, or the page ships three H1s. The tag goes to the LONGEST segment
    # so the heading a screen reader and a crawler read is the sentence, not
    # the one word that happens to be coloured.
    lead_index = max(range(len(segs)), key=lambda i: len(segs[i][0]))
    parts = []
    for i, (text, hl) in enumerate(segs):
        parts.append(_head(text, size if i == lead_index else "div", token,
                           align, on_dark,
                           color=("secondary" if on_dark else GOLD_TEXT)
                           if hl else None))
    return _row(parts, 12, align="baseline", extra={
        "flex_wrap": "wrap",
        "flex_direction_mobile": "row",
        "flex_justify_content": "center" if align == "center" else "flex-start"})


def _pill(text, icon_name="fas fa-circle-check", on_dark=False):
    """The small capsule label above a section heading - VERIFICATION,
    QUALITY CONTROL. White on the tinted grounds, gold-tinted on dark."""
    kids = [widget("icon", {
        "selected_icon": icon(icon_name), "size": slider(13),
        "align": "center", "view": "default",
    }, globals_={"primary_color": color_ref(
        "secondary" if on_dark else GOLD_TEXT)})]
    kids.append(widget("heading", {
        "title": text.upper(), "header_size": "div", "align": "left",
        "__typography__": typo_ref(T["eyebrow"]),
    }, globals_={"title_color": color_ref(
        C["white"] if on_dark else "primary")}))
    return container([_row(kids, 8, align="center", extra={
        "flex_wrap": "nowrap", "flex_direction_mobile": "row"})], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(8, 18, 8, 18),
        "border_radius": R_PILL,
        "border_border": "solid", "border_width": box(1),
        "width": slider(0),
        "width_mobile": slider(100, "%"),
        "background_background": "classic",
    }, globals_={
        "background_color": color_ref(
            C["overlay"] if on_dark else C["surface_alt"]),
        "border_color": color_ref(C["border"] if not on_dark else C["rule_dark"])})


def _lp_button(label, href, style="fill"):
    """Three button shapes, and only three, matching the reference:

        fill     lightning yellow pill, black label - the primary action
        quiet    white pill with a hairline - the secondary beside it
        onDark   yellow pill used on the black bands
    """
    b = _button(label, href, "primary", "")
    b["settings"].update({
        "border_radius": R_PILL,
        "text_padding": dims(15, 30, 15, 30),
        "__typography__": typo_ref(T["meta"]),
    })
    g = b["settings"].setdefault("__globals__", {})
    if style == "quiet":
        g.update({
            "button_background_color": color_ref(C["surface_alt"]),
            "button_text_color": color_ref("primary"),
            "border_color": color_ref(C["border"]),
            "button_background_hover_color": color_ref(C["surface"]),
            "hover_color": color_ref("primary")})
        b["settings"].update({"border_border": "solid",
                              "border_width": box(1)})
    else:
        g.update({
            "button_background_color": color_ref("secondary"),
            "button_text_color": color_ref("primary"),
            "button_background_hover_color": color_ref("accent"),
            "hover_color": color_ref("primary")})
    return b


def _chip(text, icon_name="fas fa-bolt"):
    """The trust capsules under the hero copy: outline pill, icon, one line."""
    ic = widget("icon", {
        "selected_icon": icon(icon_name), "size": slider(13),
        "align": "center", "view": "default",
    }, globals_={"primary_color": color_ref(GOLD_TEXT)})
    tx = widget("heading", {
        "title": text, "header_size": "div", "align": "left",
        "__typography__": typo_ref(T["meta"]),
    }, globals_={"title_color": color_ref("primary")})
    return container([_row([ic, tx], 8, align="center", extra={
        "flex_wrap": "nowrap", "flex_direction_mobile": "row"})], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(9, 16, 9, 16),
        "border_radius": R_PILL,
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["surface_alt"]),
                 "border_color": color_ref(C["border"])})


def _card(kids, width=None, pad=None, on_dark=False, extra=None):
    s = {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(10),
        "padding": pad or dims(24, 24, 26, 24),
        "padding_mobile": dims(20, 18, 22, 18),
        "border_radius": R_CARD,
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
    }
    if width:
        s.update({"width": slider(width, "%"), "width_mobile": slider(100, "%")})
    if extra:
        s.update(extra)
    return container(kids, s, globals_={
        "background_color": color_ref(
            C["overlay"] if on_dark else C["surface_alt"]),
        "border_color": color_ref(C["rule_dark"] if on_dark else C["border"])})


def _numbadge(n):
    """The small numbered disc that sits on each quality card in the
    reference - gold fill, black numeral."""
    return container([widget("heading", {
        "title": str(n), "header_size": "div", "align": "center",
        "__typography__": typo_ref(T["eyebrow"]),
    }, globals_={"title_color": color_ref("primary")})], {
        "content_width": "full", "flex_direction": "column",
        "flex_justify_content": "center", "flex_align_items": "center",
        "width": slider(22), "min_height": slider(22),
        "_flex_shrink": "0",
        "border_radius": R_PILL,
        "background_background": "classic",
    }, globals_={"background_color": color_ref("secondary")})


def _icontile(icon_name, size=44, tone="gold"):
    """The rounded icon tile: gold ground, black glyph on the light sections;
    yellow glyph on a hairline tile where the ground is black."""
    dark = tone == "dark"
    return container([widget("icon", {
        "selected_icon": icon(icon_name), "size": slider(round(size * 0.45)),
        "align": "center", "view": "default",
    }, globals_={"primary_color": color_ref(
        "secondary" if dark else "primary")})], {
        "content_width": "full", "flex_direction": "column",
        "flex_justify_content": "center", "flex_align_items": "center",
        "width": slider(size), "min_height": slider(size),
        "_flex_shrink": "0",
        "border_radius": box(12),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(
        C["overlay"] if dark else "accent")})


def _photo(image, height=None, animation=None, delay=None):
    if not (image and image.get("url")):
        return container([], {
            "content_width": "full", "min_height": slider(height or 260),
            "border_radius": R_PANEL, "border_border": "dashed",
            "border_width": box(1), "background_background": "classic",
        }, globals_={"background_color": color_ref(C["surface"]),
                     "border_color": color_ref(C["border"])})
    s = {"image": media(image["url"], image.get("alt", "")),
         "image_size": "full", "align": "center",
         "width": slider(100, "%")}
    if height:
        s.update({"height": slider(height), "object-fit": "contain"})
    if animation:
        s["_animation"] = animation
        if delay:
            s["_animation_delay"] = delay
    return widget("image", s)


# ─────────────────────────────── devices ───────────────────────────────────

@block("lp.ticker")
def lp_ticker(props):
    """The strip directly under the header.

    On the reference this is a continuously scrolling promo band; the client's
    current site already runs a static gold version of it. A true marquee is a
    CSS animation, which this repo does not emit, so the items are laid out as
    one wrapping row across the full width - the same content, holding still.
    Recorded as a partial on the device, not passed off as the animation.
    """
    items = props.get("items", [])
    marks = []
    for it in items:
        ic = widget("icon", {
            "selected_icon": icon(it.get("icon", "fas fa-circle-check")),
            "size": slider(13), "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref("primary")})
        tx = widget("heading", {
            "title": it.get("label", "").upper(), "header_size": "div",
            "align": "left", "__typography__": typo_ref(T["eyebrow"]),
        }, globals_={"title_color": color_ref("primary")})
        marks.append(_row([ic, tx], 8, align="center", extra={
            "flex_wrap": "nowrap", "flex_direction_mobile": "row"}))

    strip = _row(marks, 34, align="center", extra={
        "flex_wrap": "wrap", "flex_direction_mobile": "row",
        "flex_justify_content": "center",
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "margin": dims(0, "auto", 0, "auto")})

    return container([strip], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(13, 20, 13, 20),
        "background_background": "classic",
    }, globals_={"background_color": color_ref("secondary")})


@block("lp.hero")
def lp_hero(props):
    """The opening screen: two-tone headline left, floating vials right.

    Everything about the reference's hero is here except the ambient drift of
    the background sparkles: the headline splits at one accent word, the body
    paragraph sits under it, two pills follow, then a row of outline trust
    chips. The vials enter on a staggered fadeInUp - set on the widgets
    because the motion stage deliberately skips the first section of a page.
    """
    copy = [_two_tone(props.get("lead", ""), props.get("highlight", ""),
                      "h1", T["hero"], "left", tail=props.get("tail", ""))]
    if props.get("intro"):
        copy.append(_text(props["intro"], "left"))
    acts = []
    if props.get("cta_label"):
        acts.append(_lp_button(props["cta_label"],
                               props.get("cta_url", "/shop/")))
    if props.get("cta2_label"):
        acts.append(_lp_button(props["cta2_label"],
                               props.get("cta2_url", "#"), "quiet"))
    if acts:
        copy.append(_row(acts, 14, align="center", extra={
            "flex_wrap": "wrap", "flex_direction_mobile": "row",
            "padding": dims(6, 0, 0, 0)}))
    if props.get("chips"):
        copy.append(_row([_chip(c.get("label", ""), c.get("icon", "fas fa-bolt"))
                          for c in props["chips"]], 10, align="center",
                         extra={"flex_wrap": "wrap",
                                "flex_direction_mobile": "row"}))

    vials = props.get("vials", [])
    shots = []
    for i, v in enumerate(vials[:3]):
        # The middle vial sits proud of the other two, as on the reference.
        lift = dims(0, 0, 44, 0) if i == 1 else dims(30, 0, 0, 0)
        shots.append(container([_photo(v, props.get("vial_height", 300),
                                       "fadeInUp", 200 + i * 160)], {
            "content_width": "full", "flex_direction": "column",
            "flex_justify_content": "center",
            "width": slider(32, "%"), "width_mobile": slider(32, "%"),
            "margin": lift}))

    w = _tracks([52, 44], 40)
    cols = [_col(copy, w[0], extra={"flex_gap": gap(20)}),
            _col([_row(shots, 10, align="center",
                       extra={"flex_wrap": "nowrap",
                              "flex_direction_mobile": "row"})], w[1])]
    return _lp_section([_row(cols, 40, align="center")],
                       props.get("bg", "cream"),
                       pad=dims(84, 0, 84, 0), anchor=props.get("anchor"))


@block("lp.claimbar")
def lp_claimbar(props):
    """The full-bleed dark band of shipping and testing claims.

    The reference scrolls these; see the module docstring. Three claims, laid
    out evenly across the band, in the reference's own rhythm.
    """
    items = props.get("items", [])
    cells = []
    for it in items:
        kids = []
        if it.get("icon"):
            kids.append(widget("icon", {
                "selected_icon": icon(it["icon"]), "size": slider(15),
                "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref("secondary")}))
        kids.append(widget("heading", {
            "title": it.get("label", ""), "header_size": "div",
            "align": "center", "__typography__": typo_ref(T["meta"]),
        }, globals_={"title_color": color_ref(C["white"])}))
        cells.append(_row(kids, 10, align="center", extra={
            "flex_wrap": "nowrap", "flex_direction_mobile": "row",
            "flex_justify_content": "center"}))

    strip = _row(cells, 40, align="center", extra={
        "flex_wrap": "wrap", "flex_direction_mobile": "row",
        "flex_justify_content": "space-between",
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "margin": dims(0, "auto", 0, "auto")})
    return container([strip], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(18, 20, 18, 20),
        "background_background": "classic",
    }, globals_={"background_color": color_ref("primary")})


@block("lp.products")
def lp_products(props):
    """Featured Products.

    The reference runs a horizontal carousel with arrow buttons over its own
    product cards. This ships Elementor Pro's WooCommerce Products grid
    instead, styled to that card - image tile, title, price, category line,
    filled Add to cart pill - because the grid binds to the client's REAL
    catalogue, prices and cart, and a loop carousel would need WooCommerce
    dynamic tags that are not in this repo's control registry. The carousel
    motion is the one thing lost; it is recorded as a substitution in
    design-spec.json and the README says what it would take to add it.
    """
    head = [_two_tone(props.get("lead", "Featured"),
                      props.get("highlight", "Products"), "h2", T["h_medium"])]
    if props.get("intro"):
        head.append(_text(props["intro"], "left", small=True))
    head_col = _col(head, _tracks([70, 26], 24)[0], extra={"flex_gap": gap(6)})
    act = _col([_lp_button(props.get("cta_label", "View all products"),
                           props.get("cta_url", "/shop/"), "quiet")],
               _tracks([70, 26], 24)[1],
               extra={"flex_align_items": "flex-end",
                      "flex_justify_content": "center"})

    grid = widget("woocommerce-products", {
        "columns": str(props.get("columns", 4)),
        "columns_tablet": "2",
        "columns_mobile": "1",
        "paginate": "",
        "show_result_count": "",
        "column_gap": slider(LP_GUTTER),
        "row_gap": slider(30),
        "align": "left",
        "automatically_align_buttons": "yes",
        "box_padding": dims(16, 16, 20, 16),
        "box_border_width": slider(1),
        "box_border_radius": slider(14),
        "image_spacing": slider(14),
        "title_spacing": slider(6),
        "button_spacing": slider(16),
        "button_text_padding": dims(13, 22, 13, 22),
        "button_border_radius": slider(999),
        "show_onsale_flash": "yes",
        "star_size": slider(13),
    }, globals_={
        "products_title_color": color_ref("primary"),
        "products_title_typography_typography": typo_ref(T["h_small"]),
        "price_color": color_ref("primary"),
        "price_typography_typography": typo_ref(T["h_small"]),
        "old_price_color": color_ref(C["muted"]),
        "box_bg_color": color_ref(C["surface_alt"]),
        "box_border_color": color_ref(C["border"]),
        "button_background_color": color_ref("secondary"),
        "button_text_color": color_ref("primary"),
        "button_hover_background_color": color_ref("accent"),
        "button_hover_color": color_ref("primary"),
        "star_color": color_ref("accent"),
        "empty_star_color": color_ref(C["border"]),
    })

    return _lp_section([_row([head_col, act], 24, align="center"), grid],
                       props.get("bg", "white"), anchor=props.get("anchor"))


@block("lp.verify")
def lp_verify(props):
    """"How to verify each product" - the reference's trust device.

    A labelled pill, a two-tone heading, one photograph of a real vial with
    its batch label on the left, and the verification steps as numbered cards
    on the right, closing on one action. The reference's steps describe a QR
    code; these describe what THIS client actually publishes, read off their
    own /quality-standards/ and /coa/ pages.
    """
    left = [_photo(props.get("image"), props.get("image_height", 420))]
    if props.get("caption"):
        left.append(_text(props["caption"], "center", small=True))

    right = []
    if props.get("pill"):
        right.append(_pill(props["pill"], props.get("pill_icon",
                                                    "fas fa-shield-alt")))
    right.append(_two_tone(props.get("lead", ""), props.get("highlight", ""),
                           "h2", T["h_medium"]))
    if props.get("intro"):
        right.append(_text(props["intro"], "left"))
    for i, st in enumerate(props.get("steps", []), 1):
        body = [_head(st.get("title", ""), "h3", T["h_small"])]
        if st.get("text"):
            body.append(_text(st["text"], "left", small=True))
        right.append(_card([_row([_numbadge(i),
                                  _col(body, None, extra={"flex_gap": gap(6)})],
                                 14, align="flex-start",
                                 extra={"flex_wrap": "nowrap",
                                        "flex_direction_mobile": "row"})],
                           pad=dims(20, 22, 22, 22)))
    if props.get("cta_label"):
        right.append(_lp_button(props["cta_label"],
                                props.get("cta_url", "/coa/")))

    w = _tracks([34, 62], 48)
    return _lp_section([_row([_col(left, w[0], extra={"flex_gap": gap(10)}),
                              _col(right, w[1], extra={"flex_gap": gap(14)})],
                             48, align="center")],
                       props.get("bg", "cream"), anchor=props.get("anchor"))


@block("lp.quality")
def lp_quality(props):
    """"Every batch tested" - pill, two-tone heading, three counters, the
    checks as numbered cards two-up, then the proof banner.

    The counters are real `counter` widgets rather than typeset numerals, so
    they count up as the section arrives - the reference animates these too.
    The banner at the foot is its own strip inside the section: gold ground,
    icon, a label line over a statement, and one white action.
    """
    kids = []
    if props.get("pill"):
        kids.append(container([_pill(props["pill"],
                                     props.get("pill_icon", "fas fa-flask"))], {
            "content_width": "full", "flex_direction": "column",
            "flex_align_items": "center"}))
    kids.append(_two_tone(props.get("lead", ""), props.get("highlight", ""),
                          "h2", T["h_medium"], align="center"))
    if props.get("intro"):
        kids.append(container([_text(props["intro"], "center")], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(70, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))

    stats = []
    for st in props.get("stats", []):
        stats.append(_col([widget("counter", {
            "starting_number": st.get("from", 0),
            "ending_number": st.get("to", 0),
            "prefix": st.get("prefix", ""),
            "suffix": st.get("suffix", ""),
            "title": st.get("label", ""),
            "duration": 1600,
            "thousand_separator": "",
        }, globals_={
            "number_color": color_ref(GOLD_TEXT),
            "typography_number_typography": typo_ref(T["h_medium"]),
            "title_color": color_ref(C["muted"]),
            "typography_title_typography": typo_ref(T["meta"]),
        })], _tracks([1] * max(len(props.get("stats", [])), 1), 20)[0]))
    if stats:
        kids.append(_row(stats, 20, align="flex-start",
                         extra={"flex_wrap": "wrap"}))

    checks = props.get("checks", [])
    cols = props.get("columns", 2)
    w = _tracks([1] * cols, LP_GUTTER)[0]
    cards = []
    for i, ch in enumerate(checks, 1):
        body = [_head(ch.get("title", ""), "h3", T["h_small"])]
        if ch.get("text"):
            body.append(_text(ch["text"], "left", small=True))
        cards.append(_card([_row([
            container([_icontile(ch.get("icon", "fas fa-vial"), 42),
                       container([_numbadge(i)], {
                           "content_width": "full", "flex_direction": "column",
                           "_position": "absolute",
                           "_offset_orientation_h": "end", "_offset_x": slider(-6),
                           "_offset_orientation_v": "start", "_offset_y": slider(-6),
                           "_z_index": 3})], {
                "content_width": "full", "flex_direction": "column",
                "width": slider(42), "_flex_shrink": "0"}),
            _col(body, None, extra={"flex_gap": gap(6)})], 14,
            align="flex-start", extra={"flex_wrap": "nowrap",
                                       "flex_direction_mobile": "row"})],
            w, pad=dims(20, 22, 22, 22)))
    if cards:
        kids.append(_row(cards, LP_GUTTER, align="stretch",
                         extra={"flex_wrap": "wrap"}))

    banner = props.get("banner")
    if banner:
        left = [widget("heading", {
            "title": banner.get("label", "").upper(), "header_size": "div",
            "align": "left", "__typography__": typo_ref(T["eyebrow"]),
        }, globals_={"title_color": color_ref("primary")}),
            _head(banner.get("title", ""), "h3", T["h_small"], "left")]
        row = [_icontile(banner.get("icon", "fas fa-certificate"), 46),
               _col(left, None, extra={"flex_gap": gap(4)})]
        act = _lp_button(banner.get("cta_label", "View COAs"),
                         banner.get("cta_url", "/coa/"), "quiet")
        kids.append(container([_row([
            _row(row, 16, align="center", extra={"flex_wrap": "nowrap",
                                                 "flex_direction_mobile": "row"}),
            act], 24, align="center",
            extra={"flex_wrap": "wrap",
                   "flex_justify_content": "space-between"})], {
            "content_width": "full", "flex_direction": "column",
            "padding": dims(22, 26, 22, 26),
            "border_radius": R_PANEL,
            "background_background": "classic",
        }, globals_={"background_color": color_ref("secondary")}))

    return _lp_section(kids, props.get("bg", "cream"),
                       anchor=props.get("anchor"))


@block("lp.why")
def lp_why(props):
    """"Why choose ...?" - six reasons, three up, icon tile centred over each.

    No cards: the reference sets these as plain columns on the page ground,
    which is what keeps a six-item grid from reading as another wall of
    boxes. The client's current site puts all six in solid gold panels, and
    that is the single loudest difference between the two pages.
    """
    items = props.get("items", [])
    cols = props.get("columns", 3)
    w = _tracks([1] * cols, 30)[0]
    cells = []
    for it in items:
        cells.append(_col([
            container([_icontile(it.get("icon", "fas fa-bolt"), 52)], {
                "content_width": "full", "flex_direction": "column",
                "flex_align_items": "center"}),
            _head(it.get("title", ""), "h3", T["h_small"], "center"),
            _text(it.get("text", ""), "center", small=True),
        ], w, extra={"flex_gap": gap(12), "flex_align_items": "center"}))

    kids = [_two_tone(props.get("lead", ""), props.get("highlight", ""),
                      "h2", T["h_medium"], align="center")]
    if props.get("intro"):
        kids.append(container([_text(props["intro"], "center")], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(66, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    kids.append(_row(cells, 30, align="flex-start",
                     extra={"flex_wrap": "wrap"}))
    return _lp_section(kids, props.get("bg", "white"),
                       anchor=props.get("anchor"))


@block("lp.reviews")
def lp_reviews(props):
    """"Real Researchers, Real Reviews" on the black ground.

    The reference runs two rows of review cards scrolling in opposite
    directions. `testimonial-carousel` has no direction control, so this is
    one autoplaying row - the content and the card are matched, the opposing
    drift is not, and design-spec.json says so rather than the README
    claiming a match.

    Nothing here is invented: the reviews are the ones already published on
    the client's own homepage.
    """
    items = props.get("items", [])
    slides = []
    for it in items:
        slides.append(repeater_item(
            content=it.get("text", ""),
            name=it.get("name", ""),
            title=it.get("role", "Verified buyer"),
        ))
    car = widget("testimonial-carousel", {
        "slides": slides,
        "slides_per_view": str(props.get("per_view", 3)),
        "slides_per_view_tablet": "2",
        "slides_per_view_mobile": "1",
        "space_between": slider(20),
        "autoplay": "yes",
        "autoplay_speed": props.get("autoplay_speed", 4200),
        "speed": props.get("speed", 900),
        "loop": "yes",
        "pause_on_hover": "yes",
        "show_arrows": "",
        "content_padding": dims(24, 24, 24, 24),
        "content_border_radius": slider(14),
    }, globals_={
        "content_background_color": color_ref(C["surface_alt"]),
        "content_color": color_ref("text"),
        "content_typography_typography": typo_ref(T["body_small"]),
        "name_color": color_ref("primary"),
        "name_typography_typography": typo_ref(T["h_small"]),
        "title_color": color_ref(C["muted"]),
        "title_typography_typography": typo_ref(T["meta"]),
    })

    kids = [_two_tone(props.get("lead", ""), props.get("highlight", ""),
                      "h2", T["h_medium"], align="center", on_dark=True)]
    if props.get("intro"):
        kids.append(container([_text(props["intro"], "center", on_dark=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(64, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    kids.append(car)
    if props.get("note"):
        kids.append(_text(props["note"], "center", on_dark=True, small=True))
    return _lp_section(kids, "dark", anchor=props.get("anchor"))


@block("lp.closer")
def lp_closer(props):
    """The closing line, a vial standing either side of it.

    The reference's last section before the footer: one sentence at display
    size, centred, one pill under it, and a product shot flanking each margin.
    """
    mid = [_head(props.get("title", ""), "h2", T["h_medium"], "center")]
    if props.get("text"):
        mid.append(container([_text(props["text"], "center")], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(80, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    if props.get("cta_label"):
        mid.append(container([_lp_button(props["cta_label"],
                                         props.get("cta_url", "/shop/"))], {
            "content_width": "full", "flex_direction": "column",
            "flex_align_items": "center"}))

    vials = props.get("vials", [])
    side_w, mid_w = 18, 60
    left = _col([_photo(vials[0] if vials else None, 230)], side_w,
                extra={"flex_justify_content": "center"})
    right = _col([_photo(vials[1] if len(vials) > 1 else None, 230)], side_w,
                 extra={"flex_justify_content": "center"})
    centre = _col(mid, mid_w, extra={"flex_gap": gap(18),
                                     "flex_justify_content": "center"})
    return _lp_section([_row([left, centre, right], 20, align="center",
                             extra={"flex_wrap": "wrap"})],
                       props.get("bg", "cream"), anchor=props.get("anchor"))


@block("lp.compliance")
def lp_compliance(props):
    """The research-use-only notice.

    The reference states this under its age gate and again in its footer. This
    kit emits neither - the client's site already has both - so the notice
    lands at the foot of the page instead, where it also does the job the
    reference's footer disclaimer does: it is the last thing read before the
    catalogue link. The text is the client's own RUO policy, not the
    reference's wording.
    """
    body = [_head(props.get("title", ""), "h3", T["h_small"], "left")]
    for para in props.get("paragraphs", []):
        body.append(_text(para, "left", small=True))
    row = _row([_icontile(props.get("icon", "fas fa-microscope"), 46),
                _col(body, None, extra={"flex_gap": gap(8)})], 18,
               align="flex-start", extra={"flex_wrap": "nowrap",
                                          "flex_direction_mobile": "row"})
    panel = container([row], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(26, 28, 28, 28),
        "border_radius": R_PANEL,
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["surface_alt"]),
                 "border_color": color_ref(C["border"])})
    return _lp_section([panel], props.get("bg", "cream"),
                       pad=dims(56, 0, 56, 0), anchor=props.get("anchor"))
