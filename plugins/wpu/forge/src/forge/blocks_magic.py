"""
blocks_magic.py — the Magic Renovations & Repairs design family.

No reference site was supplied for this build. The style brief is verbal —
"professional, modern, clean construction/real-estate look" — so the design
is specified rather than matched, and `clients/magic-renovations/
design-spec.json` writes down what was decided so a later change is a
deliberate revision rather than drift.

The one hard input is the LOGO, and it carries more than a style adjective
could: near-black, a gold gradient, a classical Roman serif, and a five-star
roofline mark. Three rules come straight out of it and govern everything here:

    1. BLACK IS THE SPOTLIGHT, NOT THE GROUND. The logo is ~90% black on
       white, so the site is light with black used full-bleed exactly four
       times: header, one mid-page band, the CTA band, the footer. A dark
       ground would make gold text the norm, and gold reads cheap the moment
       there is a lot of it.
    2. GOLD IS A LINE, A NUMERAL OR A BUTTON — never a fill larger than a
       button. Same reason.
    3. THE EYEBROW SITS OVER A SHORT GOLD RULE. That pairing repeats at the
       top of nearly every section and is the cheapest, most recognisable
       thing in the design. It is why `_mg_head` exists rather than each
       block assembling its own heading.

Colour comes from the Global Kit via `intake.json`. Nothing here names a hex.
"""
from __future__ import annotations

from .core import (
    container, widget, slider, dims, box, media, link, icon, gap,
    color_ref, typo_ref,
)
from .tokens import C, T
from .blocks import (
    block, _row, _col, _tracks, _heading, _text, _button, _faq,
    _hover_lift, KIT_CONTAINER,
)

# ─────────────────────────── rhythm and shape ───────────────────────────

MG_PAD = dims(100, 0, 100, 0)
MG_PAD_T = dims(74, 24, 74, 24)
MG_PAD_M = dims(56, 20, 56, 20)

R_CARD = box(10)          # squarer than a consumer brand, rounder than industrial
R_BTN = box(3)
GUTTER = 26
HEADER_H = 88
RULE_W = 52               # the gold rule under every eyebrow


def _mg_section(children, bg="ground", pad=None, extra=None):
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
        "flex_gap": gap(42),
        "padding": pad or MG_PAD,
        "padding_tablet": MG_PAD_T,
        "padding_mobile": MG_PAD_M,
        "background_background": "classic",
    }
    if extra:
        s.update(extra)
    return container(children, s, globals_={
        "background_color": color_ref(grounds.get(bg, C["surface"]))})


def _mg_rule(width=RULE_W, on_dark=False):
    """The short gold rule. Always gold, on both grounds — it is the one
    element that never changes colour, which is what makes it read as the
    brand rather than as decoration."""
    return container([], {
        "content_width": "full",
        "width": slider(width),
        "min_height": slider(3),
        "_flex_grow": 0,
        "background_background": "classic",
    }, globals_={"background_color": color_ref("primary")})


def _mg_caps(text, on_dark=False, tone="gold"):
    """ALL-CAPS micro-label."""
    colour = {
        "gold": "primary",
        "muted": C["on_dark"] if on_dark else C["muted"],
        "ink": C["white"] if on_dark else C["ink_on_white"],
    }[tone]
    return widget("heading", {
        "title": text.upper(),
        "header_size": "div",
        "align": "left",
        "__typography__": typo_ref(T["eyebrow"]),
    }, globals_={"title_color": color_ref(colour)})


def _mg_head(props, on_dark=False, size="h2"):
    """Eyebrow, gold rule, heading, optional intro — in that order.

    Every section opens with this. Assembling it once rather than per block is
    what keeps the rule the same width and the gap the same everywhere; the
    signature stops being a signature the moment two sections disagree.
    """
    kids = []
    if props.get("eyebrow"):
        kids.append(_mg_caps(props["eyebrow"], on_dark))
        kids.append(_mg_rule(on_dark=on_dark))
    if props.get("title"):
        kids.append(_heading(props["title"], size, T["h_medium"], "left",
                             on_dark=on_dark))
    if props.get("intro"):
        kids.append(_text(props["intro"], "left", on_dark=on_dark))
    return container(kids, {
        "content_width": "full",
        "flex_direction": "column",
        "flex_gap": gap(14),
        "width": slider(props.get("head_width", 72), "%"),
        "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"),
    })


def _mg_button(label, href, style="primary"):
    """One verb on this site: Request an Estimate.

    Primary is a filled GOLD rectangle with near-black text — the logo's own
    contrast, and the only combination that holds on both the light ground and
    the black bands without needing a second variant.
    """
    if style == "ghost":
        b = _button(label, href, "ghost", "fas fa-arrow-right")
    elif style == "ondark":
        b = _button(label, href, "ghost", "fas fa-arrow-right")
        b["settings"]["__globals__"].update({
            "button_text_color": color_ref(C["white"]),
            "border_color": color_ref(C["white"]),
        })
    else:
        b = _button(label, href, "primary", "fas fa-arrow-right")
        b["settings"]["__globals__"].update({
            "button_background_color": color_ref("primary"),
            "button_text_color": color_ref("secondary"),
        })
    b["settings"]["border_radius"] = R_BTN
    b["settings"]["text_padding"] = dims(17, 32, 17, 32)
    b["settings"]["__typography__"] = typo_ref(T["meta"])
    return b


def _mg_photo(image, height=300, radius=None):
    """A photograph, or an honest empty slot.

    EVERY slot in this build is currently empty — the client has not supplied
    photography yet. That makes this function unusually load-bearing: it has
    to make an unfilled slot look like a reserved space rather than a bug, on
    a site whose entire stated purpose is showcasing project photos.
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
        "min_height_mobile": slider(round(height * 0.64)),
        "border_radius": radius or R_CARD,
        "border_border": "solid",
        "border_width": box(1),
        "background_background": "classic",
    }, globals_={
        "background_color": color_ref(C["surface_alt"]),
        "border_color": color_ref(C["border"]),
    })


# ═══════════════════════════════ header ═══════════════════════════════

@block("mg.header")
def mg_header(props):
    """Near-black header, gold wordmark, caps nav, filled gold CTA.

    The supplied logo is black-on-white, so on this header it needs the
    reversed variant — flagged in intake.json under `logo.note`. Until that
    file arrives the wordmark renders as text, which is also the more robust
    thing for a template kit: it never ships a broken image reference.
    """
    mark = widget("heading", {
        "title": props.get("brand", ""),
        "header_size": "div",
        "align": "left",
        "link": link(props.get("home", "/")),
        "__typography__": typo_ref(T["wordmark"]),
    }, globals_={"title_color": color_ref("primary")})

    nav = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"),
        "layout": "horizontal",
        "align_items": "right",
        "pointer": "underline",
        "menu_space_between": slider(24),
        "toggle_align": "right",
        "submenu_icon": {"value": "fas fa-caret-down", "library": "fa-solid"},
        "__typography__": typo_ref(T["meta"]),
    }, globals_={
        "color_menu_item": color_ref(C["on_dark"]),
        "color_menu_item_hover": color_ref("primary"),
        "color_menu_item_active": color_ref(C["white"]),
        "pointer_color_menu_item_hover": color_ref("primary"),
        "dropdown_background_color": color_ref("secondary"),
        "dropdown_color_menu_item": color_ref(C["on_dark"]),
    })

    right = [nav]
    if props.get("phone_display"):
        right.append(widget("heading", {
            "title": props["phone_display"],
            "header_size": "div",
            "align": "right",
            "link": link("tel:" + props.get("phone", "")),
            "__typography__": typo_ref(T["meta"]),
        }, globals_={"title_color": color_ref(C["white"])}))
    right.append(_mg_button(props.get("cta_label", "Request an Estimate"),
                            props.get("cta_url", "/request-an-estimate/")))

    bar = _row([
        _col([mark], 28),
        _col([_row(right, 22, align="center", justify="flex-end")], 70),
    ], 22, align="center", justify="space-between", extra={
        "flex_wrap": "nowrap", "flex_direction_mobile": "row"})

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

@block("mg.hero")
def mg_hero(props):
    """Photograph with a scrim, or a black ground when there is no photo yet.

    The fallback matters here more than usual. With no photography supplied,
    a hero that expects an image would render as a grey rectangle with white
    text on it — the worst-looking element on the site. Falling back to the
    brand's own black keeps the page deliberate until the photo arrives, and
    the swap is one URL in intake.json.
    """
    img = props.get("image") or {}
    has = bool(img.get("url"))

    inner = []
    if props.get("eyebrow"):
        inner += [_mg_caps(props["eyebrow"], on_dark=True), _mg_rule(on_dark=True)]
    inner.append(_heading(props.get("title", ""), "h1", T["hero"], "left", on_dark=True))
    if props.get("intro"):
        inner.append(_text(props["intro"], "left", on_dark=True))
    inner.append(_row([
        _mg_button(props.get("cta_label", "Request an Estimate"),
                   props.get("cta_url", "/request-an-estimate/")),
        _mg_button(props.get("cta2_label", "View Our Work"),
                   props.get("cta2_url", "/projects/"), "ondark"),
    ], 14, align="center"))

    body = container(inner, {
        "content_width": "full",
        "flex_direction": "column",
        "flex_gap": gap(18),
        "width": slider(58, "%"),
        "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"),
    })

    s = {
        "content_width": "boxed",
        "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "flex_justify_content": "center",
        "min_height": slider(600),
        "min_height_mobile": slider(460),
        "padding": dims(80, 0, 80, 0),
        "padding_mobile": dims(56, 20, 56, 20),
        "background_background": "classic",
    }
    g = {}
    if has:
        s["background_image"] = media(img["url"], img.get("alt", ""))
        s["background_position"] = "center center"
        s["background_size"] = "cover"
        s["overlay_background"] = "classic"
        s["overlay_color"] = "rgba(9,9,11,0.62)"
    else:
        g["background_color"] = color_ref("secondary")
    return container([body], s, globals_=g)


@block("mg.pagehero")
def mg_pagehero(props):
    """Inner-page hero: black band, gold eyebrow over a rule, H1, one line."""
    kids = []
    if props.get("eyebrow"):
        kids += [_mg_caps(props["eyebrow"], on_dark=True), _mg_rule(on_dark=True)]
    kids.append(_heading(props.get("title", ""), "h1", T["h_large"], "left",
                         on_dark=True))
    if props.get("intro"):
        kids.append(_text(props["intro"], "left", on_dark=True))
    body = container(kids, {
        "content_width": "full",
        "flex_direction": "column",
        "flex_gap": gap(14),
        "width": slider(74, "%"),
        "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"),
    })
    return _mg_section([body], "dark", pad=dims(80, 0, 80, 0))


# ══════════════════════════════ section head ══════════════════════════════

@block("mg.sectionhead")
def mg_sectionhead(props):
    """Standalone eyebrow + rule + heading, with an optional button at the
    right on the same row."""
    kids = [_col([_mg_head(props, props.get("bg") == "dark")], 68)]
    if props.get("cta_label"):
        kids.append(_col([_row([
            _mg_button(props["cta_label"], props.get("cta_url", "#"),
                       "ondark" if props.get("bg") == "dark" else "ghost")
        ], 0, justify="flex-end")], 28))
    return _row(kids, 30, align="flex-end", justify="space-between")


# ═══════════════════════════════ services ═══════════════════════════════

@block("mg.services")
def mg_services(props):
    """Service cards led by a large GOLD NUMERAL rather than an icon.

    Deliberate: an icon grid is the default trade-site component and every
    competitor in this market has one. A numbered set reads as a considered
    list of what the business does, which is the "professional, modern"
    register the brief asked for. services.grid and icons.row are both in the
    design-spec's `never` list because reaching for one of them is exactly how
    this would quietly become a generic contractor page.
    """
    items = props.get("items", [])
    cols = props.get("columns", 3)
    w = _tracks([1] * cols, GUTTER)

    def card(it, n):
        num = widget("heading", {
            "title": "%02d" % n,
            "header_size": "div",
            "align": "left",
            "__typography__": typo_ref(T["h_medium"]),
        }, globals_={"title_color": color_ref("primary")})
        kids = [num, _mg_rule(36)]
        if it.get("image") is not None and props.get("photos"):
            kids.append(_mg_photo(it.get("image"), 200))
        kids.append(_heading(it.get("title", ""), "h3", T["h_small"], "left"))
        if it.get("text"):
            kids.append(_text(it["text"], "left", small=True))
        if it.get("url"):
            kids.append(_mg_button(props.get("link_label", "Learn more"),
                                   it["url"], "ghost"))
        return _hover_lift(container(kids, {
            "content_width": "full",
            "flex_direction": "column",
            "flex_gap": gap(12),
            "padding": dims(28, 26, 30, 26),
            "border_radius": R_CARD,
            "border_border": "solid",
            "border_width": box(1),
            "background_background": "classic",
        }, globals_={
            "background_color": color_ref(C["white"]),
            "border_color": color_ref(C["border"]),
        }), 4)

    grid = _row([_col([card(it, i + 1)], w[i % cols])
                 for i, it in enumerate(items)], GUTTER, align="stretch")
    head = [mg_sectionhead(props)] if props.get("title") else []
    return _mg_section(head + [grid], props.get("bg", "ground"))


# ═══════════════════════════ project cards ═══════════════════════════

@block("mg.projectcards")
def mg_projectcards(props):
    """Photo, gold caps category, title, one caption line."""
    items = props.get("items", [])
    cols = props.get("columns", 3)
    w = _tracks([1] * cols, GUTTER)

    def card(it):
        kids = [_mg_photo(it.get("image"), 250, R_CARD)]
        meta = []
        if it.get("label"):
            meta.append(_mg_caps(it["label"]))
        meta.append(_heading(it.get("title", ""), "h3", T["h_small"], "left"))
        if it.get("text"):
            meta.append(_text(it["text"], "left", small=True))
        kids.append(container(meta, {
            "content_width": "full",
            "flex_direction": "column",
            "flex_gap": gap(7),
            "padding": dims(18, 2, 4, 2),
        }))
        return _hover_lift(container(kids, {
            "content_width": "full",
            "flex_direction": "column",
            "flex_gap": gap(0),
        }), 4)

    grid = _row([_col([card(it)], w[i % cols]) for i, it in enumerate(items)],
                GUTTER, align="flex-start")
    head = [mg_sectionhead(props)] if props.get("title") else []
    return _mg_section(head + [grid], props.get("bg", "ground"))


# ═══════════════════════════ split / prose ═══════════════════════════

@block("mg.split")
def mg_split(props):
    """Copy one side, photograph the other."""
    body = [_mg_head(props, head_width=100) if False else None]
    body = []
    if props.get("eyebrow"):
        body += [_mg_caps(props["eyebrow"]), _mg_rule()]
    if props.get("title"):
        body.append(_heading(props["title"], props.get("size", "h2"),
                             T["h_medium"], "left"))
    for para in props.get("paragraphs", []):
        body.append(_text(para, "left"))
    for b in props.get("bullets", []):
        body.append(_text("&#8212;&nbsp;" + b, "left", small=True))
    if props.get("cta_label"):
        body.append(_mg_button(props["cta_label"],
                               props.get("cta_url", "/request-an-estimate/")))

    photo = _mg_photo(props.get("image"), 430, R_CARD)
    w = _tracks([52, 44], 54)
    cols = [_col(body, w[0], extra={"flex_gap": gap(15)}), _col([photo], w[1])]
    if props.get("flip"):
        cols = list(reversed(cols))
    return _mg_section([_row(cols, 54, align="center")], props.get("bg", "ground"))


@block("mg.prose")
def mg_prose(props):
    """Headed prose with optional bullets."""
    kids = []
    if props.get("eyebrow"):
        kids += [_mg_caps(props["eyebrow"]), _mg_rule()]
    if props.get("title"):
        kids.append(_heading(props["title"], props.get("size", "h2"),
                             T["h_medium"], "left"))
    for para in props.get("paragraphs", []):
        kids.append(_text(para, "left"))
    for b in props.get("bullets", []):
        kids.append(_text("&#8212;&nbsp;" + b, "left", small=True))
    inner = container(kids, {
        "content_width": "full",
        "flex_direction": "column",
        "flex_gap": gap(14),
        "width": slider(props.get("width", 80), "%"),
        "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"),
    })
    return _mg_section([inner], props.get("bg", "ground"))


# ═══════════════════════════════ process ═══════════════════════════════

@block("mg.process")
def mg_process(props):
    """Numbered stages in gold numerals on hairline rules.

    The numerals match the service cards on purpose — two different numbering
    styles on one site is the kind of small inconsistency that reads as
    template rather than design.
    """
    steps = props.get("steps", [])
    on_dark = props.get("bg") == "dark"
    w = _tracks([1] * max(len(steps), 1), GUTTER)

    def step(s, i, width):
        num = widget("heading", {
            "title": "%02d" % (i + 1),
            "header_size": "div",
            "align": "left",
            "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref("primary")})
        rule = container([], {
            "content_width": "full",
            "min_height": slider(1),
            "margin": dims(14, 0, 16, 0),
            "background_background": "classic",
        }, globals_={"background_color": color_ref(
            C["rule_dark"] if on_dark else C["border"])})
        return _col([
            num, rule,
            _heading(s.get("title", ""), "h3", T["h_small"], "left", on_dark=on_dark),
            _text(s.get("text", ""), "left", on_dark=on_dark, small=True),
        ], width, extra={"flex_gap": gap(8)})

    grid = _row([step(s, i, w[i % len(w)]) for i, s in enumerate(steps)],
                GUTTER, align="flex-start")
    head = [mg_sectionhead(props)] if props.get("title") else []
    return _mg_section(head + [grid], props.get("bg", "ground"))


# ═══════════════════════════════ stat band ═══════════════════════════════

@block("mg.statband")
def mg_statband(props):
    """Full-bleed black band: statement left, figures on gold rules right.

    Content is constrained by what is actually known. No project counts, years
    trading or crew numbers were supplied, and big round numbers are the
    easiest thing in the world to invent — so the call site passes only what
    the brief states, and anything else ships visibly as PLACEHOLDER.
    """
    items = props.get("items", [])
    left = [_mg_head(props, on_dark=True, size="h2")]

    def stat(it, width):
        return _col([
            widget("heading", {
                "title": it.get("value", ""),
                "header_size": "div",
                "align": "left",
                "__typography__": typo_ref(T["h_medium"]),
            }, globals_={"title_color": color_ref(C["white"])}),
            _mg_rule(40, on_dark=True),
            widget("heading", {
                "title": it.get("label", ""),
                "header_size": "div",
                "align": "left",
                "__typography__": typo_ref(T["body_small"]),
            }, globals_={"title_color": color_ref(C["on_dark"])}),
        ], width, extra={"flex_gap": gap(10)})

    sw = _tracks([1] * max(len(items), 1), 24)
    right = _row([stat(it, sw[i % len(sw)]) for i, it in enumerate(items)],
                 24, align="flex-start")
    w = _tracks([44, 52], 48)
    return _mg_section([_row([_col(left, w[0]), _col([right], w[1])], 48,
                             align="center")], "dark")


# ═══════════════════════════════ reviews ═══════════════════════════════

@block("mg.reviews")
def mg_reviews(props):
    """A framed slot for the client's real Google reviews.

    The brief asks for Google reviews on the homepage rather than a separate
    reviews page. This renders the plugin's shortcode inside the family's card
    frame, so the widget sits in the design rather than on top of it.

    It deliberately does NOT render review cards of its own. reviews.grid,
    testimonials.columns and testimonials.carousel are all banned in the
    design-spec for that reason: they render text somebody types in, which is
    a route to publishing testimonials the business never received.
    """
    head = [mg_sectionhead(props)] if props.get("title") else []
    slot = container([
        widget("text-editor", {
            "editor": props.get("shortcode", ""),
            "align": "center",
        }, globals_={
            "text_color": color_ref("text"),
            "typography_typography": typo_ref("text"),
        }),
    ], {
        "content_width": "full",
        "flex_direction": "column",
        "padding": dims(34, 30, 34, 30),
        "padding_mobile": dims(22, 16, 22, 16),
        "border_radius": R_CARD,
        "border_border": "solid",
        "border_width": box(1),
        "background_background": "classic",
    }, globals_={
        "background_color": color_ref(C["white"]),
        "border_color": color_ref(C["border"]),
    })
    return _mg_section(head + [slot], props.get("bg", "alt"))


# ═══════════════════════════════ faq ═══════════════════════════════

@block("mg.faq")
def mg_faq(props):
    """Accordion with FAQ schema, left-aligned to match the family."""
    acc = _faq(props.get("items", []), props.get("first_open", True))
    acc["settings"]["faq_schema"] = "yes" if props.get("schema", True) else ""
    head = [_mg_head(props)] if props.get("title") else []
    body = container([acc], {
        "content_width": "full",
        "flex_direction": "column",
        "width": slider(82, "%"),
        "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"),
    })
    return _mg_section(head + [body], props.get("bg", "ground"))


# ═══════════════════════════════ CTA band ═══════════════════════════════

@block("mg.ctaband")
def mg_ctaband(props):
    """The one conversion band. One verb: Request an Estimate."""
    kids = []
    if props.get("eyebrow"):
        kids += [_mg_caps(props["eyebrow"], on_dark=True), _mg_rule(on_dark=True)]
    kids.append(_heading(props.get("title", ""), "h2", T["h_medium"], "left",
                         on_dark=True))
    if props.get("text"):
        kids.append(_text(props["text"], "left", on_dark=True))

    actions = [_mg_button(props.get("cta_label", "Request an Estimate"),
                          props.get("cta_url", "/request-an-estimate/"))]
    if props.get("phone_display"):
        actions.append(_mg_button(props["phone_display"],
                                  "tel:" + props.get("phone", ""), "ondark"))
    w = _tracks([58, 38], 40)
    return _mg_section([_row([
        _col(kids, w[0], extra={"flex_gap": gap(14)}),
        _col([_row(actions, 14, align="center")], w[1]),
    ], 40, align="center")], "dark", pad=dims(76, 0, 76, 0))


# ═══════════════════════════ sticky mobile bar ═══════════════════════════

@block("mg.stickybar")
def mg_stickybar(props):
    """CALL / REQUEST AN ESTIMATE, fixed to the bottom on phones only."""
    call = _mg_button("Call", "tel:" + props.get("phone", ""), "ondark")
    est = _mg_button(props.get("cta_label", "Request an Estimate"),
                     props.get("cta_url", "/request-an-estimate/"))
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

@block("mg.footer")
def mg_footer(props):
    """Black footer: wordmark and contact, then link columns."""
    brand = [widget("heading", {
        "title": props.get("brand", ""),
        "header_size": "div",
        "align": "left",
        "__typography__": typo_ref(T["wordmark"]),
    }, globals_={"title_color": color_ref("primary")})]
    if props.get("blurb"):
        brand.append(_text(props["blurb"], "left", on_dark=True, small=True))
    for k, href in (("phone_display", "tel:" + props.get("phone", "")),
                    ("email", "mailto:" + props.get("email", "")),
                    ("instagram", props.get("instagram_url", ""))):
        if props.get(k):
            brand.append(widget("heading", {
                "title": props[k],
                "header_size": "div",
                "align": "left",
                "link": link(href),
                "__typography__": typo_ref(T["body_small"]),
            }, globals_={"title_color": color_ref(C["white"])}))

    widths = _tracks([36, 20, 20, 18], 30)
    cols = [_col(brand, widths[0], extra={"flex_gap": gap(12)})]
    for i, group in enumerate(props.get("columns", [])[:3], start=1):
        kids = [_mg_caps(group.get("title", ""), on_dark=True, tone="muted")]
        for l in group.get("links", []):
            kids.append(widget("heading", {
                "title": l.get("label", ""),
                "header_size": "div",
                "align": "left",
                "link": link(l.get("url", "#")),
                "__typography__": typo_ref(T["body_small"]),
            }, globals_={"title_color": color_ref(C["on_dark"])}))
        cols.append(_col(kids, widths[i], extra={"flex_gap": gap(10)}))

    rule = container([], {
        "content_width": "full",
        "min_height": slider(1),
        "margin": dims(38, 0, 24, 0),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["rule_dark"])})

    return _mg_section([_row(cols, 30, align="flex-start"), rule,
                        _text(props.get("legal", ""), "left", on_dark=True, small=True)],
                       "dark", pad=dims(74, 0, 40, 0))
