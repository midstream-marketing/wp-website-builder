"""
blocks_wasatch.py — the Wasatch Unlimited design family.

Client-specific, and deliberately so. Two references were supplied and they
are opposites: big-d.com is dark, industrial and corporate; finegc.com is
light, residential and warm. The client's own written scope bans "overly
corporate design" and "industrial look" outright, so the references could not
both be followed as-is. The split is recorded device by device in
`clients/wasatch-unlimited/design-spec.json`:

    big-d   -> STRUCTURE. Devices that are palette-independent: CTA cards
               straddling the hero's bottom edge, a section heading with its
               button on the same row, an arrow-prefixed capability index,
               figures sitting on hairline rules, ALL-CAPS micro-labels.
    finegc  -> REGISTER. Light ground, photo-led bento with unequal tiles,
               the circular outlined arrow button in a card corner, the
               numbered service-area rail.

What actually distinguishes this design, in the order the eye reads it:

    1. It is a LIGHT design on a WARM ground. Charcoal appears exactly three
       times full-bleed — header, pull-quote band, footer. big-d makes
       charcoal the ground; doing that here rebuilds the industrial look the
       scope spent a paragraph rejecting.
    2. Photographs carry the page. The client has ten real project photos and
       the scope bans stock, so every photo slot is a real one and there are
       no decorative illustrations to pad with.
    3. Headings are sentence case; EYEBROWS AND LABELS ARE CAPS. That single
       contrast is what stops a warm light palette reading soft, and it is
       the cheapest thing to carry across from big-d.
    4. One action, everywhere: a filled bronze rectangle reading REQUEST AN
       ESTIMATE. Scope section 16 bans CTA sprawl, so the only other control
       is a wordless circular arrow.

Colour comes from the Global Kit via `intake.json`. Nothing here names a hex.
"""
from __future__ import annotations

from .core import (
    container, widget, slider, dims, box, media, link, icon, gap,
    color_ref, typo_ref,
)
from .tokens import C, T
from .blocks import (
    block, _row, _col, _tracks, _track, _heading, _text, _button,
    _hover_lift, _faq, CARD_SHADOW_SOFT,
    KIT_CONTAINER, TABLET_CONTAINER,
)

# ─────────────────────────── rhythm and shape ───────────────────────────
#
# big-d runs a tighter vertical rhythm than the trade families and finegc a
# looser one. Splitting the difference at 96 keeps ten pages from feeling
# either cramped or padded, which matters because the scope asks for 8-10
# STRONG pages rather than a large site.

WU_PAD = dims(96, 0, 96, 0)
WU_PAD_T = dims(72, 24, 72, 24)
WU_PAD_M = dims(56, 20, 56, 20)

R_CARD = box(14)          # photo and content cards
R_TILE = box(18)          # the large bento tiles
R_BTN = box(4)            # the primary action: a rectangle, not a pill
R_ROUND = box(999)        # the circular arrow only

GUTTER = 28
HEADER_H = 84

# The hero cards straddle the hero's bottom edge. This is the overlap depth,
# and it is a constant because two blocks have to agree on it: the hero pads
# its own bottom by this much so the cards have somewhere to sit, and the card
# row pulls itself up by the same amount.
OVERLAP = 92


def _wu_section(children, bg="ground", pad=None, extra=None):
    """A page section. `bg` names a ground, never a hex."""
    grounds = {
        "ground": C["surface"],
        "alt": C["surface_alt"],
        "white": C["white"],
        "dark": "secondary",
    }
    s = {
        "content_width": "boxed",
        "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "flex_gap": gap(40),
        "padding": pad or WU_PAD,
        "padding_tablet": WU_PAD_T,
        "padding_mobile": WU_PAD_M,
        "background_background": "classic",
    }
    if extra:
        s.update(extra)
    return container(children, s,
                     globals_={"background_color": color_ref(grounds.get(bg, C["surface"]))})


def _wu_caps(text, on_dark=False, tone="brand"):
    """ALL-CAPS micro-label. The most repeated device in this design.

    Tracking is wide and the size is small — at body size it reads as a
    shouted heading instead of a label, which is the failure mode.
    """
    colour = {
        "brand": C["brand_on_dark"] if on_dark else "primary",
        "muted": C["on_dark"] if on_dark else C["muted"],
    }[tone]
    return widget("heading", {
        "title": text.upper(),
        "header_size": "div",
        "align": "left",
        "__typography__": typo_ref(T["eyebrow"]),
    }, globals_={"title_color": color_ref(colour)})


def _wu_button(label, href, style="primary"):
    """The primary action.

    A filled bronze RECTANGLE with a trailing arrow — big-d's outlined arrow
    button, filled in so it holds its weight on a light warm ground where an
    outline would disappear. Deliberately not a pill: finegc's pills are the
    softer half of that reference and the scope asks for premium, not soft.
    """
    if style == "outline":
        b = _button(label, href, "ghost", "fas fa-arrow-right")
    elif style == "onphoto":
        # Over a photograph the ghost button needs a solid edge to survive a
        # busy image; white border on the scrim rather than a tinted fill.
        b = _button(label, href, "ghost", "fas fa-arrow-right")
        b["settings"]["__globals__"].update({
            "button_text_color": color_ref(C["white"]),
            "border_color": color_ref(C["white"]),
        })
    else:
        b = _button(label, href, "primary", "fas fa-arrow-right")
    b["settings"]["border_radius"] = R_BTN
    b["settings"]["text_padding"] = dims(16, 30, 16, 30)
    b["settings"]["__typography__"] = typo_ref(T["meta"])
    return b


def _wu_arrow_circle(href, on_dark=True):
    """The circular outlined arrow — finegc's signature.

    Icon only and WORDLESS on purpose: scope section 16 bans a second verb
    competing with REQUEST AN ESTIMATE, so this navigates without naming
    itself. It is positioned absolutely into a card's top-right corner by the
    caller, which is the legal Elementor route (`_position` + offsets), not
    CSS.
    """
    ic = widget("icon", {
        "selected_icon": icon("fas fa-arrow-right"),
        "size": slider(14),
        "align": "center",
        "view": "default",
        "link": link(href),
    }, globals_={"primary_color": color_ref(C["white"] if on_dark else "primary")})
    return container([ic], {
        "content_width": "full",
        "flex_direction": "row",
        "flex_justify_content": "center",
        "flex_align_items": "center",
        "width": slider(44),
        "min_height": slider(44),
        "_flex_grow": 0,
        "border_radius": R_ROUND,
        "border_border": "solid",
        "border_width": box(1),
        "_position": "absolute",
        "_offset_orientation_h": "end",
        "_offset_x_end": slider(18),
        "_offset_orientation_v": "start",
        "_offset_y": slider(18),
        "_z_index": 3,
    }, globals_={"border_color": color_ref(
        C["on_dark"] if on_dark else C["border"])})


def _wu_photo(image, height=280, radius=None, ratio=None):
    """A photograph, or an honest empty slot in its place.

    An unfilled slot renders as a fixed-height tinted block rather than
    collapsing, so a page missing photography shows where it goes instead of
    looking like a layout bug. Most slots here are filled — the client's real
    photos are wired in — but the gallery has room for more than they have.
    """
    if image and image.get("url"):
        return widget("image", {
            "image": media(image["url"], image.get("alt", "")),
            "image_size": "full",
            "width": slider(100, "%"),
            "align": "center",
            "image_border_radius": radius or R_CARD,
            "object-fit": "cover",
        })
    return container([], {
        "content_width": "full",
        "min_height": slider(height),
        "min_height_mobile": slider(round(height * 0.62)),
        "border_radius": radius or R_CARD,
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["surface_alt"])})


def _wu_photo_bg(image, height, radius, children, scrim=0.55):
    """A photograph used as a container BACKGROUND with content over it.

    This is how every bento tile and the hero are built. The scrim is an
    overlay rather than a filter so the text on top keeps full contrast — a
    filter would dim the type along with the photo.
    """
    s = {
        "content_width": "full",
        "flex_direction": "column",
        "flex_justify_content": "flex-end",
        "min_height": slider(height),
        "min_height_mobile": slider(round(height * 0.72)),
        "padding": dims(26, 26, 26, 26),
        "border_radius": radius,
        "background_background": "classic",
        "background_position": "center center",
        "background_size": "cover",
        "overlay_background": "classic",
        "overlay_color": "rgba(11,12,15,%.2f)" % scrim,
        "css_filters_css_filter": "custom",
    }
    g = {}
    if image and image.get("url"):
        s["background_image"] = media(image["url"], image.get("alt", ""))
    else:
        g["background_color"] = color_ref(C["surface_alt"])
    return container(children, s, globals_=g)


# ═══════════════════════════════ header ═══════════════════════════════

@block("wu.header")
def wu_header(props):
    """Charcoal header, white wordmark, uppercase nav, phone, bronze CTA.

    Charcoal is not a style preference here. The client's only logo asset is a
    PURE WHITE wordmark on transparency — it is invisible on any light ground,
    so a dark header is the one option that works with the file they actually
    have. Recorded in intake.json so nobody 'fixes' it to a white header.
    """
    left = [widget("heading", {
        "title": props.get("brand", ""),
        "header_size": "div",
        "align": "left",
        "link": link(props.get("home", "/")),
        "__typography__": typo_ref(T["wordmark"]),
    }, globals_={"title_color": color_ref(C["white"])})]

    nav = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"),
        "layout": "horizontal",
        # `align_items`, not `align` â€” nav-menu does not observe `align`, and
        # the validator catches it rather than shipping a control Elementor
        # silently ignores.
        "align_items": "right",
        "pointer": "none",
        "menu_space_between": slider(26),
        "toggle_align": "right",
        "submenu_icon": {"value": "fas fa-caret-down", "library": "fa-solid"},
        "__typography__": typo_ref(T["meta"]),
    }, globals_={
        "color_menu_item": color_ref(C["on_dark"]),
        "color_menu_item_hover": color_ref(C["brand_on_dark"]),
        "color_menu_item_active": color_ref(C["white"]),
        "dropdown_background_color": color_ref("secondary"),
        "dropdown_color_menu_item": color_ref(C["on_dark"]),
    })

    phone = props.get("phone_display", "")
    right = [nav]
    if phone:
        right.append(widget("heading", {
            "title": phone,
            "header_size": "div",
            "align": "right",
            "link": link("tel:" + props.get("phone", "")),
            "__typography__": typo_ref(T["meta"]),
        }, globals_={"title_color": color_ref(C["white"])}))
    right.append(_wu_button(props.get("cta_label", "Request an Estimate"),
                            props.get("cta_url", "/contact/")))

    bar = _row([
        _col(left, 26),
        _col([_row(right, 24, align="center", justify="flex-end")], 74),
    ], 24, align="center", justify="space-between", extra={
        "flex_wrap": "nowrap",
        "flex_direction_mobile": "row",
    })

    return container([bar], {
        "content_width": "boxed",
        "boxed_width": slider(KIT_CONTAINER),
        "min_height": slider(HEADER_H),
        "padding": dims(16, 0, 16, 0),
        "padding_mobile": dims(14, 20, 14, 20),
        "flex_direction": "column",
        "flex_justify_content": "center",
        "background_background": "classic",
    }, globals_={"background_color": color_ref("secondary")})


# ═════════════════════════════════ hero ═════════════════════════════════

@block("wu.hero")
def wu_hero(props):
    """Full-bleed photograph, scrim, display heading, one line, two actions.

    Bottom padding reserves OVERLAP px so `wu.herocards` can pull itself up
    into this section without colliding with the buttons. The two blocks are
    a pair; placing the hero without the cards leaves a deliberate-looking
    band of empty photo, which is why the IR always emits them together.
    """
    img = props.get("image") or {}
    inner = [
        _wu_caps(props.get("eyebrow", ""), on_dark=True, tone="muted")
        if props.get("eyebrow") else None,
        _heading(props.get("title", ""), "h1", T["hero"], "left", on_dark=True),
        _text(props.get("intro", ""), "left", on_dark=True) if props.get("intro") else None,
        _row([
            _wu_button(props.get("cta_label", "Request an Estimate"),
                       props.get("cta_url", "/contact/")),
            _wu_button(props.get("cta2_label", "View Our Work"),
                       props.get("cta2_url", "/projects/"), "onphoto"),
        ], 14, align="center"),
    ]
    inner = [x for x in inner if x is not None]

    body = container(inner, {
        "content_width": "full",
        "flex_direction": "column",
        "flex_gap": gap(20),
        "width": slider(60, "%"),
        "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"),
    })

    return _wu_photo_bg(
        img, 660, box(0),
        [container([body], {
            "content_width": "boxed",
            "boxed_width": slider(KIT_CONTAINER),
            "flex_direction": "column",
            "flex_justify_content": "center",
            "padding": dims(0, 0, 0, 0),
        })],
        scrim=0.58,
    ) | {}


@block("wu.herocards")
def wu_herocards(props):
    """Three charcoal cards straddling the hero's bottom edge.

    THE device from big-d, and the one most at risk of being flattened into a
    tidy CTA band below the hero — which is why cta.band is in the spec's
    `never` list. The overlap is a negative top margin plus a z-index; both
    are container controls, so no stylesheet is involved.

    On mobile the cards stack and the overlap is dropped to zero: a 3-high
    stack pulled up 92px would cover the hero headline.
    """
    cards = []
    for c in props.get("cards", [])[:3]:
        inner = [
            _wu_caps(c.get("label", ""), on_dark=True, tone="brand")
            if c.get("label") else None,
            _heading(c.get("title", ""), "h3", T["h_small"], "left", on_dark=True),
            _wu_button(c.get("link_label", "View"), c.get("url", "#"), "onphoto"),
        ]
        inner = [x for x in inner if x is not None]
        cards.append(_col([container(inner, {
            "content_width": "full",
            "flex_direction": "column",
            "flex_gap": gap(14),
            "flex_justify_content": "space-between",
            "padding": dims(28, 26, 28, 26),
            "min_height": slider(184),
            "background_background": "classic",
        }, globals_={"background_color": color_ref("secondary")})],
            _tracks([1, 1, 1], GUTTER)[0]))

    return container([_row(cards, GUTTER, align="stretch")], {
        "content_width": "boxed",
        "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "padding": dims(0, 0, 0, 0),
        "margin": dims(-OVERLAP, 0, 0, 0),
        "margin_mobile": dims(0, 0, 0, 0),
        "z_index": 4,
    })


@block("wu.pagehero")
def wu_pagehero(props):
    """Inner-page hero: charcoal band, eyebrow, H1, one line.

    Short on purpose. Ten pages each opening with a 600px photo would bury the
    content the scope asked to be concise, and only the homepage has a
    photograph strong enough to carry that height.
    """
    inner = [
        _wu_caps(props.get("eyebrow", ""), on_dark=True, tone="brand")
        if props.get("eyebrow") else None,
        _heading(props.get("title", ""), "h1", T["h_large"], "left", on_dark=True),
        _text(props.get("intro", ""), "left", on_dark=True) if props.get("intro") else None,
    ]
    inner = [x for x in inner if x is not None]
    return _wu_section([container(inner, {
        "content_width": "full",
        "flex_direction": "column",
        "flex_gap": gap(16),
        "width": slider(74, "%"),
        "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"),
    })], "dark", pad=dims(76, 0, 76, 0))


# ══════════════════════════ section furniture ══════════════════════════

@block("wu.sectionhead")
def wu_sectionhead(props):
    """Heading left, small arrow button right, on ONE row.

    big-d repeats this on every indexed section and it is what makes them read
    as an index rather than decoration. A centred heading with the button
    dropped underneath is a different component — hence heading.centered in
    the spec's `never` list.
    """
    left = [
        _wu_caps(props.get("eyebrow", ""), tone="brand") if props.get("eyebrow") else None,
        _heading(props.get("title", ""), props.get("size", "h2"), T["h_medium"], "left"),
        _text(props.get("intro", ""), "left") if props.get("intro") else None,
    ]
    left = [x for x in left if x is not None]

    kids = [_col(left, 66)]
    if props.get("cta_label"):
        kids.append(_col([_row([
            _wu_button(props["cta_label"], props.get("cta_url", "#"), "outline")
        ], 0, justify="flex-end")], 30))
    return _row(kids, 32, align="flex-end", justify="space-between")


# ═══════════════════════════════ bento ═══════════════════════════════

@block("wu.bento")
def wu_bento(props):
    """Photo tiles on UNEQUAL tracks — two large, then three smaller.

    finegc's service grid. The asymmetry is the device: a uniform 3-up icon
    grid is the default trade-site component and is precisely what both
    references are not, which is why services.grid is banned globally.

    Each tile: photo background, scrim, circular arrow top-right, and
    bottom-left a caps label, a title and one caption line.
    """
    items = props.get("items", [])

    def tile(it, height):
        body = [
            _wu_caps(it.get("label", ""), on_dark=True, tone="brand")
            if it.get("label") else None,
            _heading(it.get("title", ""), "h3", T["h_small"], "left", on_dark=True),
            _text(it.get("text", ""), "left", on_dark=True, small=True)
            if it.get("text") else None,
        ]
        body = [x for x in body if x is not None]
        stack = container(body, {
            "content_width": "full",
            "flex_direction": "column",
            "flex_gap": gap(8),
        })
        t = _wu_photo_bg(it.get("image"), height, R_TILE,
                         [_wu_arrow_circle(it.get("url", "#")), stack], scrim=0.5)
        return _hover_lift(t, 4)

    rows = []
    top, rest = items[:2], items[2:5]
    if top:
        w = _tracks([1, 1], GUTTER)
        rows.append(_row([_col([tile(it, 340)], w[i]) for i, it in enumerate(top)],
                         GUTTER, align="stretch"))
    if rest:
        w = _tracks([1] * len(rest), GUTTER)
        rows.append(_row([_col([tile(it, 260)], w[i]) for i, it in enumerate(rest)],
                         GUTTER, align="stretch"))

    head = [wu_sectionhead(props)] if props.get("title") else []
    return _wu_section(head + rows, props.get("bg", "ground"))


# ══════════════════════════ capability index ══════════════════════════

@block("wu.linkindex")
def wu_linkindex(props):
    """Three-column index, each row prefixed by a small square outlined arrow.

    big-d's 'WHAT WE BUILD'. The square glyph and the hairline rule under each
    row are the device; a bulleted icon-list is not, which is why icon-list is
    named in the spec.
    """
    items = props.get("items", [])
    cols = props.get("columns", 3)
    on_dark = props.get("bg") == "dark"

    def rowitem(it):
        glyph = container([widget("icon", {
            "selected_icon": icon("fas fa-arrow-right"),
            "size": slider(9),
            "align": "center",
            "view": "default",
        }, globals_={"primary_color": color_ref(
            C["brand_on_dark"] if on_dark else "primary")})], {
            "content_width": "full",
            "flex_direction": "row",
            "flex_justify_content": "center",
            "flex_align_items": "center",
            "width": slider(22),
            "min_height": slider(22),
            "_flex_grow": 0,
            "border_border": "solid",
            "border_width": box(1),
            "border_radius": box(2),
        }, globals_={"border_color": color_ref(
            C["rule_dark"] if on_dark else C["border"])})

        label = widget("heading", {
            "title": it.get("label", ""),
            "header_size": "div",
            "align": "left",
            "link": link(it.get("url", "")) if it.get("url") else None,
            "__typography__": typo_ref(T["body_small"]),
        }, globals_={"title_color": color_ref(
            C["on_dark"] if on_dark else C["ink_on_white"])})

        return container([_row([glyph, label], 12, align="center", extra={
            "flex_wrap": "nowrap", "flex_direction_mobile": "row"})], {
            "content_width": "full",
            "flex_direction": "column",
            "padding": dims(13, 0, 13, 0),
            "border_border": "solid",
            "border_width": dims(0, 0, 1, 0),
        }, globals_={"border_color": color_ref(
            C["rule_dark"] if on_dark else C["border"])})

    per = -(-len(items) // cols) if items else 0
    chunks = [items[i:i + per] for i in range(0, len(items), per)] if per else []
    w = _tracks([1] * max(len(chunks), 1), GUTTER)
    grid = _row([_col([rowitem(x) for x in ch], w[i], extra={"flex_gap": gap(0)})
                 for i, ch in enumerate(chunks)], GUTTER, align="flex-start")

    head = [wu_sectionhead(props)] if props.get("title") else []
    return _wu_section(head + [grid], props.get("bg", "ground"))


# ═══════════════════════════════ stats ═══════════════════════════════

@block("wu.stats")
def wu_stats(props):
    """Figures sitting ON hairline rules — big-d's Quick Facts.

    The DEVICE is required; its CONTENT is where honesty bites. big-d fills it
    with revenue, headcount and a 1967 founding date. Wasatch Unlimited has
    published none of that, so the call sites pass only figures that are
    genuinely evidenced, and anything unverified ships as a visible
    PLACEHOLDER for the client to fill in one field.
    """
    on_dark = props.get("bg") == "dark"
    items = props.get("items", [])
    w = _tracks([1] * min(len(items), 4), GUTTER) if items else []

    def stat(it, width):
        num = widget("heading", {
            "title": it.get("value", ""),
            "header_size": "div",
            "align": "left",
            "__typography__": typo_ref(T["h_medium"]),
        }, globals_={"title_color": color_ref(
            C["white"] if on_dark else C["ink_on_white"])})
        rule = container([], {
            "content_width": "full",
            "min_height": slider(1),
            "margin": dims(12, 0, 12, 0),
            "background_background": "classic",
        }, globals_={"background_color": color_ref(
            C["rule_dark"] if on_dark else C["border"])})
        lab = widget("heading", {
            "title": it.get("label", ""),
            "header_size": "div",
            "align": "left",
            "__typography__": typo_ref(T["body_small"]),
        }, globals_={"title_color": color_ref(
            C["on_dark"] if on_dark else C["muted"])})
        return _col([num, rule, lab], width, extra={"flex_gap": gap(0)})

    grid = _row([stat(it, w[i % len(w)]) for i, it in enumerate(items)],
                GUTTER, align="flex-start")
    head = [wu_sectionhead(props)] if props.get("title") else []
    return _wu_section(head + [grid], props.get("bg", "ground"))


# ═══════════════════════════ project cards ═══════════════════════════

@block("wu.projectcards")
def wu_projectcards(props):
    """Photo, CAPS category, location line, project name, caption.

    Captioned in exactly the shape scope section 9 asks for. The LOCATION line
    ships as PLACEHOLDER on every card: the photo filenames carry street
    addresses but no town, and writing 'Midway' under a project would be
    inventing a fact about where the work was done.
    """
    items = props.get("items", [])
    cols = props.get("columns", 3)
    w = _tracks([1] * cols, GUTTER)

    def card(it):
        photo = container([_wu_photo(it.get("image"), 240, R_CARD),
                           _wu_arrow_circle(it.get("url", "#"))], {
            "content_width": "full",
            "flex_direction": "column",
            "border_radius": R_CARD,
            "overflow": "hidden",
        })
        meta = [
            _wu_caps(it.get("label", ""), tone="brand") if it.get("label") else None,
            _text(it.get("location", ""), "left", small=True) if it.get("location") else None,
            _heading(it.get("title", ""), "h3", T["h_small"], "left"),
            _text(it.get("text", ""), "left", small=True) if it.get("text") else None,
        ]
        meta = [x for x in meta if x is not None]
        body = container(meta, {
            "content_width": "full",
            "flex_direction": "column",
            "flex_gap": gap(6),
            "padding": dims(20, 2, 4, 2),
        })
        return _hover_lift(container([photo, body], {
            "content_width": "full",
            "flex_direction": "column",
            "flex_gap": gap(0),
        }), 4)

    grid = _row([_col([card(it)], w[i % cols]) for i, it in enumerate(items)],
                GUTTER, align="flex-start")
    head = [wu_sectionhead(props)] if props.get("title") else []
    return _wu_section(head + [grid], props.get("bg", "ground"))


# ════════════════════════════ service areas ════════════════════════════

@block("wu.arearail")
def wu_arearail(props):
    """Numbered service-area rail beside body copy — finegc's device.

    The numbering and the rule-per-row are the distinctive half; a plain town
    grid loses both, which is why areas.grid and areas.counties are banned.

    Scope section 13 is explicit that thin duplicate city pages must not be
    created, so this is a rail of NAMES, not of links to nine near-identical
    pages. Each row becomes linkable later if a town ever earns a real page.
    """
    areas = props.get("areas", [])
    rows = []
    for i, a in enumerate(areas, 1):
        n = widget("heading", {
            "title": "%02d" % i,
            "header_size": "div",
            "align": "left",
            "__typography__": typo_ref(T["meta"]),
        }, globals_={"title_color": color_ref("primary")})
        nm = widget("heading", {
            "title": a if isinstance(a, str) else a.get("name", ""),
            "header_size": "div",
            "align": "left",
            "__typography__": typo_ref(T["body_small"]),
        }, globals_={"title_color": color_ref(C["ink_on_white"])})
        rows.append(container([_row([n, nm], 16, align="center", extra={
            "flex_wrap": "nowrap", "flex_direction_mobile": "row"})], {
            "content_width": "full",
            "flex_direction": "column",
            "padding": dims(14, 4, 14, 4),
            "border_border": "solid",
            "border_width": dims(0, 0, 1, 0),
        }, globals_={"border_color": color_ref(C["border"])}))

    rail = container(rows, {
        "content_width": "full",
        "flex_direction": "column",
        "flex_gap": gap(0),
        "padding": dims(10, 22, 10, 22),
        "background_background": "classic",
        "border_radius": R_CARD,
        "border_border": "solid",
        "border_width": box(1),
    }, globals_={
        "background_color": color_ref(C["white"]),
        "border_color": color_ref(C["border"]),
    })

    left = [
        _wu_caps(props.get("eyebrow", ""), tone="brand") if props.get("eyebrow") else None,
        _heading(props.get("title", ""), "h2", T["h_medium"], "left"),
        _text(props.get("intro", ""), "left") if props.get("intro") else None,
    ]
    left = [x for x in left if x is not None]
    if props.get("cta_label"):
        left.append(_wu_button(props["cta_label"], props.get("cta_url", "/contact/")))

    w = _tracks([54, 42], 48)
    return _wu_section([_row([_col(left, w[0]), _col([rail], w[1])], 48,
                             align="flex-start")], props.get("bg", "alt"))


# ═════════════════════════════ process ═════════════════════════════

@block("wu.process")
def wu_process(props):
    """Four flat numbered steps, rule-separated.

    Scope section 12 asks for a simple visual process and says keep it
    concise. Numbers are display-weight text on a rule rather than filled
    circles: circles read as a template component, and the scope names
    'template-heavy appearance' as something to avoid.
    """
    steps = props.get("steps", [])
    on_dark = props.get("bg") == "dark"
    w = _tracks([1] * max(len(steps), 1), GUTTER)

    def step(s, i, width):
        n = widget("heading", {
            "title": "%02d" % (i + 1),
            "header_size": "div",
            "align": "left",
            "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(
            C["brand_on_dark"] if on_dark else "primary")})
        rule = container([], {
            "content_width": "full",
            "min_height": slider(1),
            "margin": dims(14, 0, 16, 0),
            "background_background": "classic",
        }, globals_={"background_color": color_ref(
            C["rule_dark"] if on_dark else C["border"])})
        return _col([
            n, rule,
            _heading(s.get("title", ""), "h3", T["h_small"], "left", on_dark=on_dark),
            _text(s.get("text", ""), "left", on_dark=on_dark, small=True),
        ], width, extra={"flex_gap": gap(8)})

    grid = _row([step(s, i, w[i % len(w)]) for i, s in enumerate(steps)],
                GUTTER, align="flex-start")
    head = [wu_sectionhead(props)] if props.get("title") else []
    return _wu_section(head + [grid], props.get("bg", "ground"))


# ═══════════════════════════ split / prose ═══════════════════════════

@block("wu.split")
def wu_split(props):
    """Copy one side, photograph the other. The workhorse content section.

    Written rather than reused so the photo corner radius, the caps eyebrow
    and the button shape match the rest of the family — a borrowed split from
    another client's module would import that client's card language.
    """
    flip = props.get("flip", False)
    body = [
        _wu_caps(props.get("eyebrow", ""), tone="brand") if props.get("eyebrow") else None,
        _heading(props.get("title", ""), props.get("size", "h2"), T["h_medium"], "left"),
    ]
    body = [x for x in body if x is not None]
    for para in props.get("paragraphs", []):
        body.append(_text(para, "left"))
    if props.get("bullets"):
        for b in props["bullets"]:
            body.append(_text("&#8212;&nbsp;" + b, "left", small=True))
    if props.get("cta_label"):
        body.append(_wu_button(props["cta_label"], props.get("cta_url", "/contact/")))

    photo = _wu_photo(props.get("image"), 420, R_TILE)
    w = _tracks([52, 44], 56)
    cols = [_col(body, w[0], extra={"flex_gap": gap(16)}), _col([photo], w[1])]
    if flip:
        cols = list(reversed(cols))
    return _wu_section([_row(cols, 56, align="center")], props.get("bg", "ground"))


@block("wu.prose")
def wu_prose(props):
    """Headed prose with optional bullets. For FAQ intros and legal-ish copy."""
    kids = []
    if props.get("title"):
        kids.append(_heading(props["title"], props.get("size", "h2"),
                             T["h_medium"], "left"))
    for para in props.get("paragraphs", []):
        kids.append(_text(para, "left"))
    if props.get("bullets"):
        for b in props["bullets"]:
            kids.append(_text("&#8212;&nbsp;" + b, "left", small=True))
    inner = container(kids, {
        "content_width": "full",
        "flex_direction": "column",
        "flex_gap": gap(14),
        "width": slider(props.get("width", 78), "%"),
        "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"),
    })
    return _wu_section([inner], props.get("bg", "ground"))


# ═══════════════════════════ quote band ═══════════════════════════

@block("wu.quoteband")
def wu_quoteband(props):
    """Full-bleed charcoal band with one pull quote and an attribution.

    BUILT BUT NOT PLACED. Scope section 25 bans fake testimonials, placeholder
    testimonials and fake customer names outright, and no real review has been
    supplied. The block exists so that turning it on is one line in
    build_ir.py the day a real review arrives — a deferred device, recorded in
    design-spec.json, not a forgotten one.
    """
    kids = [
        widget("heading", {
            "title": "“",
            "header_size": "div",
            "align": "left",
            "__typography__": typo_ref(T["caps_hero"]),
        }, globals_={"title_color": color_ref(C["brand_on_dark"])}),
        _heading(props.get("quote", ""), "blockquote", T["h_medium"], "left", on_dark=True),
    ]
    if props.get("author"):
        kids.append(_wu_caps(props["author"], on_dark=True, tone="muted"))
    inner = container(kids, {
        "content_width": "full",
        "flex_direction": "column",
        "flex_gap": gap(14),
        "width": slider(74, "%"),
        "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"),
    })
    return _wu_section([inner], "dark")


# ═══════════════════════════ estimate CTA ═══════════════════════════

@block("wu.ctaband")
def wu_ctaband(props):
    """The one conversion band. One verb, everywhere: Request an Estimate."""
    kids = [
        _wu_caps(props.get("eyebrow", ""), on_dark=True, tone="brand")
        if props.get("eyebrow") else None,
        _heading(props.get("title", ""), "h2", T["h_medium"], "left", on_dark=True),
        _text(props.get("text", ""), "left", on_dark=True) if props.get("text") else None,
    ]
    kids = [x for x in kids if x is not None]
    actions = [_wu_button(props.get("cta_label", "Request an Estimate"),
                          props.get("cta_url", "/contact/"))]
    if props.get("phone_display"):
        actions.append(_wu_button(props["phone_display"],
                                  "tel:" + props.get("phone", ""), "onphoto"))
    w = _tracks([60, 36], 40)
    return _wu_section([_row([
        _col(kids, w[0], extra={"flex_gap": gap(14)}),
        _col([_row(actions, 14, align="center")], w[1]),
    ], 40, align="center")], "dark", pad=dims(72, 0, 72, 0))


# ═══════════════════════════ sticky mobile bar ═══════════════════════════

@block("wu.stickybar")
def wu_stickybar(props):
    """CALL / REQUEST ESTIMATE, fixed to the bottom on phones only.

    Scope section 17 asks for this explicitly. Hidden on desktop and tablet:
    a bar pinned over a wide layout covers content for no gain, and the header
    already carries both actions there.
    """
    call = _wu_button("Call", "tel:" + props.get("phone", ""), "onphoto")
    est = _wu_button(props.get("cta_label", "Request an Estimate"),
                     props.get("cta_url", "/contact/"))
    return container([_row([call, est], 10, align="center", extra={
        "flex_wrap": "nowrap", "flex_direction_mobile": "row"})], {
        "content_width": "full",
        "flex_direction": "column",
        "padding": dims(10, 14, 10, 14),
        "background_background": "classic",
        "hide_desktop": "hidden-desktop",
        "hide_tablet": "hidden-tablet",
        "_position": "fixed",
        "_offset_orientation_v": "end",
        "_offset_y_end": slider(0),
        "_offset_x": slider(0),
        "width": slider(100, "%"),
        "_z_index": 998,
    }, globals_={"background_color": color_ref("secondary")})


# ═══════════════════════════════ footer ═══════════════════════════════

@block("wu.footer")
def wu_footer(props):
    """Charcoal footer: wordmark and contact, then link columns.

    Carries the service index rather than a logo strip. big-d ends on a
    family-of-companies strip and finegc on award badges; Wasatch Unlimited
    has neither, and inventing association badges is what scope section 32
    bans. The index is real, and it does the internal-linking job section 18
    asks for.
    """
    brand = [
        widget("heading", {
            "title": props.get("brand", ""),
            "header_size": "div",
            "align": "left",
            "__typography__": typo_ref(T["wordmark"]),
        }, globals_={"title_color": color_ref(C["white"])}),
        _text(props.get("blurb", ""), "left", on_dark=True, small=True)
        if props.get("blurb") else None,
    ]
    brand = [x for x in brand if x is not None]
    for k in ("phone_display", "email"):
        if props.get(k):
            href = ("tel:" + props.get("phone", "")) if k == "phone_display" \
                else ("mailto:" + props["email"])
            brand.append(widget("heading", {
                "title": props[k],
                "header_size": "div",
                "align": "left",
                "link": link(href),
                "__typography__": typo_ref(T["body_small"]),
            }, globals_={"title_color": color_ref(C["white"])}))

    cols = [_col(brand, _tracks([34, 20, 20, 20], 32)[0], extra={"flex_gap": gap(12)})]
    widths = _tracks([34, 20, 20, 20], 32)
    for i, group in enumerate(props.get("columns", [])[:3], start=1):
        kids = [_wu_caps(group.get("title", ""), on_dark=True, tone="muted")]
        for l in group.get("links", []):
            kids.append(widget("heading", {
                "title": l.get("label", ""),
                "header_size": "div",
                "align": "left",
                "link": link(l.get("url", "#")),
                "__typography__": typo_ref(T["body_small"]),
            }, globals_={"title_color": color_ref(C["on_dark"])}))
        cols.append(_col(kids, widths[i], extra={"flex_gap": gap(10)}))

    legal = _text(props.get("legal", ""), "left", on_dark=True, small=True)
    rule = container([], {
        "content_width": "full",
        "min_height": slider(1),
        "margin": dims(36, 0, 24, 0),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["rule_dark"])})

    return _wu_section([_row(cols, 32, align="flex-start"), rule, legal],
                       "dark", pad=dims(72, 0, 40, 0))


# ═══════════════════════════════ faq ═══════════════════════════════

@block("wu.faq")
def wu_faq(props):
    """Accordion with FAQ schema, left-aligned to match the family.

    Written rather than reusing `faq.accordion` for two reasons, both real:

    1. That block centres its heading, and every other heading in this design
       is left-aligned with its button on the same row. A centred heading in
       the middle of the page is the one place the family would break.
    2. It does not set `faq_schema`, and scope section 18 asks for schema
       where it applies. The Q&A really is on the page, so the markup is
       earned rather than stuffed.
    """
    acc = _faq(props.get("items", []), props.get("first_open", True))
    acc["settings"]["faq_schema"] = "yes" if props.get("schema", True) else ""

    head = []
    if props.get("eyebrow"):
        head.append(_wu_caps(props["eyebrow"], tone="brand"))
    if props.get("title"):
        head.append(_heading(props["title"], "h2", T["h_medium"], "left"))
    if props.get("intro"):
        head.append(_text(props["intro"], "left"))

    body = container([acc], {
        "content_width": "full",
        "flex_direction": "column",
        "width": slider(props.get("width", 82), "%"),
        "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"),
    })
    return _wu_section(head + [body], props.get("bg", "ground"))
