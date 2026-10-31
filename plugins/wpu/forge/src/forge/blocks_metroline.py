"""
blocks_metroline.py — the Metroline Plumbing and Mechanical design family.

No competitor site was named, but the client supplied a BRAND BANNER and it is
a design reference in everything but name. Four decisions had already been made
for this brand and are matched rather than replaced:

    1. Near-black ground with desaturated, high-contrast, close-in photography.
    2. Thin CONCENTRIC ARCS bleeding out of the top-left and bottom-right
       corners — the signature graphic, and the thing that makes the banner
       look like this brand rather than any trade brand.
    3. A solid red bar closing the bottom edge.
    4. Red and charcoal, no third colour.

Two more rules come from the trade rather than the brand, and they matter more
than they look:

    RED IS AN ACCENT, NEVER A FIELD. A red band reads as a warning, not as a
    plumber. Red is a rule, an icon chip, a button, a base bar.

    THE PHONE IS A BUTTON, NOT A LINE OF TEXT. Plumbing has two conversion
    paths and the urgent one is the phone. Rendering it as body text in the
    header corner is the most common mistake on contractor sites.

Colour comes from the Global Kit via `intake.json`. Nothing here names a hex.
"""
from __future__ import annotations

import re

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

ML_PAD = dims(94, 0, 94, 0)
ML_PAD_T = dims(70, 24, 70, 24)
ML_PAD_M = dims(54, 20, 54, 20)

R_CARD = box(8)           # trade-appropriate: squarer than a consumer brand
R_CHIP = box(10)
R_BTN = box(4)
GUTTER = 26
HEADER_H = 122   # two rows: logo + call block, then the nav
RULE_W = 48

# Entity names survive .upper() as `&AMP;` and render literally - see _ml_caps.
_ENTITY = re.compile(r"&([A-Z]+);")


def _ml_section(children, bg="ground", pad=None, extra=None, anchor=None):
    """`anchor` puts a CSS id on the section.

    The client's navigation lists every individual service as its own menu
    item, so each service needs somewhere real to land — a menu item that
    drops the visitor at the top of a long page and leaves them to hunt is
    the same as a broken link.
    """
    grounds = {"ground": C["surface"], "alt": C["surface_alt"],
               "white": C["white"], "dark": "secondary"}
    s = {
        "content_width": "boxed",
        "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "flex_gap": gap(40),
        "padding": pad or ML_PAD,
        "padding_tablet": ML_PAD_T,
        "padding_mobile": ML_PAD_M,
        "background_background": "classic",
    }
    if extra:
        s.update(extra)
    if anchor:
        s["_element_id"] = anchor
    return container(children, s, globals_={
        "background_color": color_ref(grounds.get(bg, C["surface"]))})


def _ml_arcs(corner="top-left", rings=5, base=280, step=130):
    """The concentric arc line-work from the brand banner.

    No image and no stylesheet: each ring is a container with a 1px border and
    a 999 radius, sized far larger than it needs to be and pushed most of the
    way off-canvas, so only the arc crosses the corner. The parent section sets
    `overflow: hidden`, which is what turns full circles into arcs.

    Kept behind the content with a negative-free z-index and no pointer events
    of its own — it is decoration, and decoration that intercepts a click on
    the CTA behind it would be a real bug.
    """
    out = []
    for i in range(rings):
        d = base + step * i
        s = {
            "content_width": "full",
            "width": slider(d),
            "min_height": slider(d),
            "border_radius": box(999),
            "border_border": "solid",
            "border_width": box(1),
            "_position": "absolute",
            "_z_index": 0,
            "_element_custom_width": "yes",
        }
        off = round(d * 0.55)
        if corner == "top-left":
            s.update({"_offset_orientation_h": "start", "_offset_x": slider(-off),
                      "_offset_orientation_v": "start", "_offset_y": slider(-off)})
        else:
            s.update({"_offset_orientation_h": "end", "_offset_x_end": slider(-off),
                      "_offset_orientation_v": "end", "_offset_y_end": slider(-off)})
        out.append(container([], s, globals_={
            "border_color": color_ref(C["rule_dark"])}))
    return out


def _ml_rule(width=RULE_W):
    """Short red rule. Always red, on both grounds — the one element that never
    changes colour, which is what makes it read as brand rather than trim."""
    return container([], {
        "content_width": "full",
        "width": slider(width),
        "min_height": slider(3),
        "_flex_grow": 0,
        "background_background": "classic",
    }, globals_={"background_color": color_ref("primary")})


def _ml_caps(text, on_dark=False, tone="red"):
    colour = {"red": "primary",
              "muted": C["on_dark"] if on_dark else C["muted"],
              "ink": C["white"] if on_dark else C["ink_on_white"]}[tone]
    # .upper() also uppercases HTML entities, and `&AMP;` renders literally.
    # Every label here is authored copy, so any label with an ampersand in it
    # hits this — it showed up as "COMMERCIAL &AMP; COMPANY" in the footer.
    caps = _ENTITY.sub(lambda m: "&" + m.group(1).lower() + ";", text.upper())
    return widget("heading", {
        "title": caps,
        "header_size": "div",
        "align": "left",
        "__typography__": typo_ref(T["eyebrow"]),
    }, globals_={"title_color": color_ref(colour)})


def _ml_head(props, on_dark=False, size="h2", width=74):
    """Eyebrow, red rule, heading, optional intro. Every section opens here so
    the rule width and gaps stay identical — a signature stops being one the
    moment two sections disagree."""
    kids = []
    if props.get("eyebrow"):
        kids += [_ml_caps(props["eyebrow"], on_dark), _ml_rule()]
    if props.get("title"):
        kids.append(_heading(props["title"], size, T["h_medium"], "left",
                             on_dark=on_dark))
    if props.get("intro"):
        kids.append(_text(props["intro"], "left", on_dark=on_dark))
    return container(kids, {
        "content_width": "full",
        "flex_direction": "column",
        "flex_gap": gap(14),
        "width": slider(props.get("head_width", width), "%"),
        "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"),
    })


def _ml_button(label, href, style="primary"):
    if style == "ghost":
        b = _button(label, href, "ghost", "fas fa-arrow-right")
    elif style == "ondark":
        b = _button(label, href, "ghost", "fas fa-arrow-right")
        b["settings"]["__globals__"].update({
            "button_text_color": color_ref(C["white"]),
            "border_color": color_ref(C["white"])})
    elif style == "phone":
        # The phone is a BUTTON. See the module docstring — on a plumbing site
        # this is the urgent conversion path and it does not get to be text.
        b = _button(label, href, "ghost", "fas fa-phone")
        b["settings"]["__globals__"].update({
            "button_text_color": color_ref(C["white"]),
            "border_color": color_ref("primary")})
    else:
        b = _button(label, href, "primary", "fas fa-arrow-right")
        b["settings"]["__globals__"].update({
            "button_background_color": color_ref("primary"),
            "button_text_color": color_ref(C["white"])})
    b["settings"]["border_radius"] = R_BTN
    b["settings"]["text_padding"] = dims(16, 30, 16, 30)
    b["settings"]["__typography__"] = typo_ref(T["meta"])
    return b


def _ml_chip(icon_cls, on_dark=False):
    """Red-tinted rounded-square icon chip, top-LEFT of a card.

    The brief asks for icons by name. Top-left over a left-aligned title, not
    centred over a centred title — the centred version is the stock trade grid
    and is banned in the design-spec.
    """
    ic = widget("icon", {
        "selected_icon": icon(icon_cls),
        "size": slider(22),
        "align": "center",
        "view": "default",
    }, globals_={"primary_color": color_ref("primary")})
    return container([ic], {
        "content_width": "full",
        "flex_direction": "row",
        "flex_justify_content": "center",
        "flex_align_items": "center",
        "width": slider(52),
        "min_height": slider(52),
        "_flex_grow": 0,
        "_flex_align_self": "flex-start",
        "border_radius": R_CHIP,
        "background_background": "classic",
    }, globals_={"background_color": color_ref(
        C["rule_dark"] if on_dark else C["surface_alt"])})


def _ml_photo(image, height=280, radius=None):
    """A photograph, or an honest empty slot. Every slot is empty in this
    build — no photography was supplied — so this has to make a reserved space
    look deliberate rather than broken."""
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
    }, globals_={"background_color": color_ref(C["surface_alt"]),
                 "border_color": color_ref(C["border"])})


# ═══════════════════════════════ header ═══════════════════════════════

@block("ml.header")
def ml_header(props):
    """Two-row header, laid out the way the client's deck draws it.

    ROW 1  wordmark left, "Call Us Today" over the number right.
    ROW 2  the six-item nav, with the primary CTA closing the right end.

    The deck puts the phone in the top-right corner as two lines of text. It
    is kept in that position but rendered as a BUTTON, because on a plumbing
    site the phone is the urgent conversion path — see the module docstring.
    The CTA is the one addition to the drawing: the deck has no booking button
    in the chrome, and every page of it ends in a form, so the button that
    reaches those forms belongs in the nav rather than only at the foot of a
    scroll.
    """
    mark = widget("heading", {
        "title": props.get("brand", ""),
        "header_size": "div",
        "align": "left",
        "link": link(props.get("home", "/")),
        "__typography__": typo_ref(T["wordmark"]),
    }, globals_={"title_color": color_ref(C["white"])})

    nav = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"),
        "layout": "horizontal",
        "align_items": "left",
        "pointer": "underline",
        "menu_space_between": slider(22),
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

    # ── row 1: wordmark | "Call Us Today" over the number ──
    call = []
    if props.get("phone_display"):
        call.append(_ml_caps(props.get("call_label", "Call Us Today"),
                             on_dark=True, tone="muted"))
        call.append(_ml_button(props["phone_display"],
                               "tel:" + props.get("phone", ""), "phone"))
    top = _row([
        _col([mark], 46),
        _col([container(call, {
            "content_width": "full",
            "flex_direction": "column",
            "flex_align_items": "flex-end",
            "flex_align_items_mobile": "flex-start",
            "flex_gap": gap(6),
        })], 50),
    ], 20, align="center", justify="space-between", extra={
        "flex_wrap": "nowrap", "flex_direction_mobile": "column"})

    # ── row 2: nav | CTA ──
    bottom_kids = [_col([nav], 76)]
    if props.get("cta_label"):
        bottom_kids.append(_col([_row([
            _ml_button(props["cta_label"], props.get("cta_url", "/contact/"))],
            0, justify="flex-end")], 22))
    rule = container([], {
        "content_width": "full", "min_height": slider(1),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["rule_dark"])})
    bottom = _row(bottom_kids, 20, align="center", justify="space-between",
                  extra={"flex_wrap": "nowrap",
                         "flex_direction_mobile": "column"})

    return container([top, rule, bottom], {
        "content_width": "boxed",
        "boxed_width": slider(KIT_CONTAINER),
        "min_height": slider(HEADER_H),
        "padding": dims(18, 0, 12, 0),
        "padding_mobile": dims(14, 20, 14, 20),
        "flex_direction": "column",
        "flex_gap": gap(12),
        "flex_justify_content": "center",
        "background_background": "classic",
    }, globals_={"background_color": color_ref("secondary")})


# ═════════════════════════════════ hero ═════════════════════════════════

@block("ml.hero")
def ml_hero(props):
    """Photo with scrim (or the brand's near-black when none), arc line-work in
    the corners, and a red bar closing the bottom edge — the banner, rebuilt.

    The arcs and the red bar are why this reads as Metroline rather than as a
    generic dark trade hero, and both cost nothing but containers.
    """
    img = props.get("image") or {}
    has = bool(img.get("url"))

    inner = []
    if props.get("eyebrow"):
        inner += [_ml_caps(props["eyebrow"], on_dark=True), _ml_rule()]
    inner.append(_heading(props.get("title", ""), "h1", T["hero"], "left",
                          on_dark=True))
    if props.get("intro"):
        inner.append(_text(props["intro"], "left", on_dark=True))
    actions = [_ml_button(props.get("cta_label", "Request Service"),
                          props.get("cta_url", "/contact/"))]
    if props.get("phone_display"):
        actions.append(_ml_button(props["phone_display"],
                                  "tel:" + props.get("phone", ""), "phone"))
    inner.append(_row(actions, 14, align="center"))

    body = container(inner, {
        "content_width": "full",
        "flex_direction": "column",
        "flex_gap": gap(18),
        "width": slider(58, "%"),
        "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"),
        "_z_index": 2,
    })

    s = {
        "content_width": "boxed",
        "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "flex_justify_content": "center",
        "min_height": slider(600),
        "min_height_mobile": slider(460),
        "padding": dims(84, 0, 84, 0),
        "padding_mobile": dims(56, 20, 56, 20),
        "background_background": "classic",
        # Turns the oversized rings into corner arcs.
        "overflow": "hidden",
    }
    g = {}
    if has:
        s["background_image"] = media(img["url"], img.get("alt", ""))
        s["background_position"] = "center center"
        s["background_size"] = "cover"
        s["overlay_background"] = "classic"
        s["overlay_color"] = "rgba(20,20,22,0.66)"
        # The banner's photography is desaturated. Doing it here means the
        # client can hand over ordinary colour job photos and still get the
        # brand treatment without editing them.
        s["css_filters_css_filter"] = "custom"
        s["css_filters_saturate"] = slider(15)
    else:
        g["background_color"] = color_ref("secondary")

    bar = container([], {
        "content_width": "full",
        "min_height": slider(10),
        "_position": "absolute",
        "_offset_orientation_v": "end",
        "_offset_y_end": slider(0),
        "_offset_x": slider(0),
        "width": slider(100, "%"),
        "_z_index": 3,
        "background_background": "classic",
    }, globals_={"background_color": color_ref("primary")})

    kids = _ml_arcs("top-left") + _ml_arcs("bottom-right") + [body, bar]
    return container(kids, s, globals_=g)


@block("ml.pagehero")
def ml_pagehero(props):
    """Inner-page hero: near-black band, red eyebrow rule, H1, one line."""
    kids = []
    if props.get("eyebrow"):
        kids += [_ml_caps(props["eyebrow"], on_dark=True), _ml_rule()]
    kids.append(_heading(props.get("title", ""), "h1", T["h_large"], "left",
                         on_dark=True))
    if props.get("intro"):
        kids.append(_text(props["intro"], "left", on_dark=True))
    body = container(kids, {
        "content_width": "full",
        "flex_direction": "column",
        "flex_gap": gap(14),
        "width": slider(76, "%"),
        "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"),
    })
    return _ml_section([body], "dark", pad=dims(78, 0, 78, 0))


# ═══════════════════════════ trust / credentials ═══════════════════════════

@block("ml.trustrow")
def ml_trustrow(props):
    """Licensed / Insured / Bonded and the three jurisdictions, right under the
    hero. These are the four facts a homeowner checks before anything else, and
    burying them below three scroll-lengths of marketing is a lost job."""
    items = props.get("items", [])
    w = _tracks([1] * max(len(items), 1), 20)

    def cell(it, width):
        ic = widget("icon", {
            "selected_icon": icon(it.get("icon", "fas fa-check")),
            "size": slider(18), "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref("primary")})
        lab = widget("heading", {
            "title": it.get("label", ""),
            "header_size": "div", "align": "left",
            "__typography__": typo_ref(T["meta"]),
        }, globals_={"title_color": color_ref(C["ink_on_white"])})
        return _col([_row([ic, lab], 10, align="center", extra={
            "flex_wrap": "nowrap", "flex_direction_mobile": "row"})], width)

    return _ml_section([_row([cell(it, w[i % len(w)])
                             for i, it in enumerate(items)], 20, align="center")],
                       "white", pad=dims(26, 0, 26, 0))


# ═══════════════════════════════ services ═══════════════════════════════

@block("ml.services")
def ml_services(props):
    """Icon-chip service cards. The brief asks for 'HD Icons' by name.

    Chip top-LEFT over a left-aligned title. `services.grid` centres the icon
    over a centred title, which is the stock trade component — it is banned in
    the design-spec so nobody quietly swaps back to it.
    """
    items = props.get("items", [])
    cols = props.get("columns", 3)
    w = _tracks([1] * cols, GUTTER)

    def card(it):
        # The deck says "click on bullet points for description". The cards
        # ARE the bullets, so each one links to its own anchored description
        # further down the page.
        title = _heading(it.get("title", ""), "h3", T["h_small"], "left")
        if it.get("url"):
            title["settings"]["link"] = link(it["url"])
        kids = [_ml_chip(it.get("icon", "fas fa-wrench")), title]
        if it.get("sub"):
            kids.append(_ml_caps(it["sub"], tone="muted"))
        if it.get("text"):
            kids.append(_text(it["text"], "left", small=True))
        return _hover_lift(container(kids, {
            "content_width": "full",
            "flex_direction": "column",
            "flex_gap": gap(12),
            "padding": dims(26, 24, 28, 24),
            "border_radius": R_CARD,
            "border_border": "solid",
            "border_width": box(1),
            "background_background": "classic",
        }, globals_={"background_color": color_ref(C["white"]),
                     "border_color": color_ref(C["border"])}), 4)

    grid = _row([_col([card(it)], w[i % cols]) for i, it in enumerate(items)],
                GUTTER, align="stretch")
    head = [_ml_sectionhead(props)] if props.get("title") else []
    return _ml_section(head + [grid], props.get("bg", "ground"))


@block("ml.servicedetail")
def ml_servicedetail(props):
    """One anchored section per service: chip and title left, description right.

    This is the landing site for the service items in the client's dropdown
    menus. Each section carries its own CSS id, so `/residential-plumbing/
    #water-heaters` from the nav or the footer lands on that service rather
    than at the top of the page.

    The descriptions are the client's own copy. They are set as real body text
    on the page rather than hidden inside a collapsed panel: a menu item has
    to lead somewhere a search engine can read and a visitor can link to, and
    an accordion panel that is closed on arrival is neither.
    """
    out = []
    grounds = ("ground", "alt")
    for i, it in enumerate(props.get("items", [])):
        left = _col([
            _ml_chip(it.get("icon", "fas fa-wrench")),
            _heading(it.get("title", ""), "h2", T["h_small"], "left"),
        ] + ([_ml_caps(it["sub"], tone="muted")] if it.get("sub") else []),
            34, extra={"flex_gap": gap(12)})
        body = [_text(p, "left") for p in it.get("paragraphs", [])]
        for b in it.get("bullets", []):
            body.append(_text("&#8212;&nbsp;" + b, "left", small=True))
        right = _col(body, 62, extra={"flex_gap": gap(12)})
        out.append(_ml_section(
            [_row([left, right], GUTTER, align="flex-start")],
            grounds[i % 2] if props.get("alternate", True) else
            props.get("bg", "ground"),
            pad=dims(56, 0, 56, 0),
            anchor=it.get("anchor")))
    return container(out, {"content_width": "full",
                           "flex_direction": "column", "flex_gap": gap(0)})


@block("ml.hours")
def ml_hours(props):
    """Business hours, on the page rather than only in the footer.

    Supplied by the client and stated exactly. It is also the honest answer to
    the emergency question: the hours close on Sunday, so nothing here offers
    round-the-clock cover.
    """
    head = [_ml_head(props)] if props.get("title") else []
    card = container([_ml_hours({"hours_title": props.get("hours_title",
                                                          "Business Hours"),
                                 "hours": props.get("items", [])},
                                on_dark=False)], {
        "content_width": "full", "flex_direction": "column",
        "width": slider(56, "%"),
        "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"),
        "padding": dims(28, 26, 30, 26),
        "border_radius": R_CARD,
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["white"]),
                 "border_color": color_ref(C["border"])})
    return _ml_section(head + [card], props.get("bg", "ground"),
                       anchor=props.get("anchor"))


def _ml_sectionhead(props):
    """Heading left, optional button right, on one row."""
    on_dark = props.get("bg") == "dark"
    kids = [_col([_ml_head(props, on_dark)], 68)]
    if props.get("cta_label"):
        kids.append(_col([_row([
            _ml_button(props["cta_label"], props.get("cta_url", "#"),
                       "ondark" if on_dark else "ghost")], 0,
            justify="flex-end")], 28))
    return _row(kids, 30, align="flex-end", justify="space-between")


@block("ml.sectionhead")
def ml_sectionhead(props):
    return _ml_sectionhead(props)


# ═══════════════════════════ split / prose ═══════════════════════════

@block("ml.split")
def ml_split(props):
    body = []
    if props.get("eyebrow"):
        body += [_ml_caps(props["eyebrow"]), _ml_rule()]
    if props.get("title"):
        body.append(_heading(props["title"], props.get("size", "h2"),
                             T["h_medium"], "left"))
    for para in props.get("paragraphs", []):
        body.append(_text(para, "left"))
    for b in props.get("bullets", []):
        body.append(_text("&#8212;&nbsp;" + b, "left", small=True))
    if props.get("cta_label"):
        body.append(_ml_button(props["cta_label"],
                               props.get("cta_url", "/contact/")))
    photo = _ml_photo(props.get("image"), 420, R_CARD)
    w = _tracks([52, 44], 54)
    cols = [_col(body, w[0], extra={"flex_gap": gap(15)}), _col([photo], w[1])]
    if props.get("flip"):
        cols = list(reversed(cols))
    return _ml_section([_row(cols, 54, align="center")], props.get("bg", "ground"))


@block("ml.prose")
def ml_prose(props):
    kids = []
    if props.get("eyebrow"):
        kids += [_ml_caps(props["eyebrow"]), _ml_rule()]
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
    return _ml_section([inner], props.get("bg", "ground"))


# ═══════════════════════════════ process ═══════════════════════════════

@block("ml.process")
def ml_process(props):
    steps = props.get("steps", [])
    on_dark = props.get("bg") == "dark"
    w = _tracks([1] * max(len(steps), 1), GUTTER)

    def step(s, i, width):
        num = widget("heading", {
            "title": "%02d" % (i + 1), "header_size": "div", "align": "left",
            "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref("primary")})
        rule = container([], {
            "content_width": "full", "min_height": slider(1),
            "margin": dims(13, 0, 15, 0), "background_background": "classic",
        }, globals_={"background_color": color_ref(
            C["rule_dark"] if on_dark else C["border"])})
        return _col([num, rule,
                     _heading(s.get("title", ""), "h3", T["h_small"], "left",
                              on_dark=on_dark),
                     _text(s.get("text", ""), "left", on_dark=on_dark, small=True)],
                    width, extra={"flex_gap": gap(8)})

    grid = _row([step(s, i, w[i % len(w)]) for i, s in enumerate(steps)],
                GUTTER, align="flex-start")
    head = [_ml_sectionhead(props)] if props.get("title") else []
    return _ml_section(head + [grid], props.get("bg", "ground"))


# ═══════════════════════════════ areas ═══════════════════════════════

@block("ml.areas")
def ml_areas(props):
    """DC / Maryland / Virginia as three cards that each say something true and
    different. A chip row of place names is the doorway-page pattern in
    miniature, which is why areas.grid and areas.chips are banned."""
    items = props.get("items", [])
    w = _tracks([1] * max(len(items), 1), GUTTER)

    def card(it):
        kids = [_ml_chip(it.get("icon", "fas fa-location-dot")),
                _heading(it.get("title", ""), "h3", T["h_small"], "left")]
        for p in it.get("paragraphs", []):
            kids.append(_text(p, "left", small=True))
        if it.get("towns"):
            kids.append(_ml_rule(32))
            kids.append(_text(it["towns"], "left", small=True))
        return container(kids, {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(11),
            "padding": dims(28, 26, 30, 26),
            "border_radius": R_CARD,
            "border_border": "solid", "border_width": box(1),
            "background_background": "classic",
        }, globals_={"background_color": color_ref(C["white"]),
                     "border_color": color_ref(C["border"])})

    grid = _row([_col([card(it)], w[i % len(w)])
                 for i, it in enumerate(items)], GUTTER, align="stretch")
    head = [_ml_sectionhead(props)] if props.get("title") else []
    return _ml_section(head + [grid], props.get("bg", "ground"))


# ═══════════════════════════════ gallery ═══════════════════════════════

@block("ml.gallery")
def ml_gallery(props):
    """Project grid with a caption per tile. The brief lists Gallery as its own
    page; every slot is currently an empty reserved space."""
    items = props.get("items", [])
    cols = props.get("columns", 3)
    w = _tracks([1] * cols, GUTTER)

    def tile(it):
        kids = [_ml_photo(it.get("image"), 250, R_CARD)]
        meta = []
        if it.get("label"):
            meta.append(_ml_caps(it["label"]))
        if it.get("title"):
            meta.append(_heading(it["title"], "h3", T["h_small"], "left"))
        if it.get("text"):
            meta.append(_text(it["text"], "left", small=True))
        kids.append(container(meta, {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(6), "padding": dims(16, 2, 4, 2)}))
        return _hover_lift(container(kids, {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(0)}), 4)

    grid = _row([_col([tile(it)], w[i % cols]) for i, it in enumerate(items)],
                GUTTER, align="flex-start")
    head = [_ml_sectionhead(props)] if props.get("title") else []
    return _ml_section(head + [grid], props.get("bg", "ground"))


# ═══════════════════════════════ reviews ═══════════════════════════════

@block("ml.reviews")
def ml_reviews(props):
    """Framed slot for the client's real Google reviews.

    Renders a plugin shortcode and deliberately renders NO review cards of its
    own. The three testimonial blocks that could fill this space are banned in
    the design-spec for a truth reason: they render text somebody types in,
    which is a route to publishing reviews the business never received.
    """
    head = [_ml_sectionhead(props)] if props.get("title") else []
    slot = container([widget("text-editor", {
        "editor": props.get("shortcode", ""), "align": "center",
    }, globals_={"text_color": color_ref("text"),
                 "typography_typography": typo_ref("text")})], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(32, 28, 32, 28),
        "padding_mobile": dims(22, 16, 22, 16),
        "border_radius": R_CARD,
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["white"]),
                 "border_color": color_ref(C["border"])})
    return _ml_section(head + [slot], props.get("bg", "alt"))


# ═══════════════════════════════ map ═══════════════════════════════

@block("ml.map")
def ml_map(props):
    """Map, framed to match the card language.

    Centred on the SERVICE AREA rather than a street pin, because no business
    address was supplied and a guessed pin on a contractor's contact page is
    worse than an honest regional view. One field in intake.json re-centres it.
    """
    m = widget("google_maps", {
        "address": props.get("address", "Washington, DC"),
        "zoom": slider(props.get("zoom", 9)),
        "height": slider(props.get("height", 420)),
    })
    frame = container([m], {
        "content_width": "full", "flex_direction": "column",
        "border_radius": R_CARD, "overflow": "hidden",
        "border_border": "solid", "border_width": box(1),
    }, globals_={"border_color": color_ref(C["border"])})
    head = [_ml_sectionhead(props)] if props.get("title") else []
    return _ml_section(head + [frame], props.get("bg", "ground"))


# ═══════════════════════════════ faq ═══════════════════════════════

@block("ml.faq")
def ml_faq(props):
    acc = _faq(props.get("items", []), props.get("first_open", True))
    acc["settings"]["faq_schema"] = "yes" if props.get("schema", True) else ""
    head = [_ml_head(props)] if props.get("title") else []
    body = container([acc], {
        "content_width": "full", "flex_direction": "column",
        "width": slider(82, "%"),
        "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%")})
    return _ml_section(head + [body], props.get("bg", "ground"))


# ═══════════════════════════════ CTA band ═══════════════════════════════

@block("ml.ctaband")
def ml_ctaband(props):
    """Near-black conversion band with the arc motif, phone and form side by
    side. Both paths are offered because plumbing has two: the emergency call
    and the planned quote."""
    kids = []
    if props.get("eyebrow"):
        kids += [_ml_caps(props["eyebrow"], on_dark=True), _ml_rule()]
    kids.append(_heading(props.get("title", ""), "h2", T["h_medium"], "left",
                         on_dark=True))
    if props.get("text"):
        kids.append(_text(props["text"], "left", on_dark=True))
    body = container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(14), "_z_index": 2})

    actions = [_ml_button(props.get("cta_label", "Request Service"),
                          props.get("cta_url", "/contact/"))]
    if props.get("phone_display"):
        actions.append(_ml_button(props["phone_display"],
                                  "tel:" + props.get("phone", ""), "phone"))
    act = container([_row(actions, 14, align="center")], {
        "content_width": "full", "flex_direction": "column", "_z_index": 2})

    w = _tracks([58, 38], 40)
    row = _row([_col([body], w[0]), _col([act], w[1])], 40, align="center")
    return _ml_section(_ml_arcs("bottom-right", rings=4) + [row], "dark",
                       pad=dims(74, 0, 74, 0), extra={"overflow": "hidden"})


# ═══════════════════════════ sticky mobile bar ═══════════════════════════

@block("ml.stickybar")
def ml_stickybar(props):
    call = _ml_button(props.get("call_label", "Call Now"),
                      "tel:" + props.get("phone", ""), "phone")
    req = _ml_button(props.get("cta_label", "Request Service"),
                     props.get("cta_url", "/contact/"))
    return container([_row([call, req], 10, align="center", extra={
        "flex_wrap": "nowrap", "flex_direction_mobile": "row"})], {
        "content_width": "full", "flex_direction": "column",
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

def _ml_hours(props, on_dark=True):
    """Business hours as a days/time table rather than a run-on sentence.

    The deck puts the hours in the footer and they are the answer to "can I
    get somebody today", so they are set as rows a visitor can scan in one
    look. Nothing here or anywhere else on the site claims 24/7 cover: the
    supplied hours close on Sunday, and a plumbing site that implies
    round-the-clock service it does not run generates the worst call a
    contractor can get.
    """
    rows = [_ml_caps(props.get("hours_title", "Business Hours"),
                     on_dark=on_dark, tone="muted")]
    for h in props.get("hours", []):
        rows.append(_row([
            widget("heading", {
                "title": h.get("days", ""), "header_size": "div",
                "align": "left",
                "__typography__": typo_ref(T["body_small"]),
            }, globals_={"title_color": color_ref(
                C["white"] if on_dark else C["ink_on_white"])}),
            widget("heading", {
                "title": h.get("time", ""), "header_size": "div",
                "align": "right",
                "__typography__": typo_ref(T["body_small"]),
            }, globals_={"title_color": color_ref(
                C["on_dark"] if on_dark else "text")}),
        ], 12, align="center", justify="space-between",
            extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"}))
    return container(rows, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(9)})


def _ml_social(props, on_dark=True):
    """Facebook / Instagram / Yelp, as icon buttons.

    The deck asks for social WIDGETS. Icon links are what that means in a
    footer: an embedded feed in a footer is weight nobody scrolls to, and
    Yelp in particular has no embeddable feed — it has a listing you link to.
    """
    items = props.get("social", [])
    if not items:
        return None
    icons = []
    for s in items:
        icons.append(container([widget("icon", {
            "selected_icon": icon(s.get("icon", "fas fa-link")),
            "size": slider(16), "align": "center", "view": "default",
            "link": link(s.get("url", "#")),
        }, globals_={"primary_color": color_ref(
            C["white"] if on_dark else C["ink_on_white"])})], {
            "content_width": "full",
            "flex_direction": "row",
            "flex_justify_content": "center",
            "flex_align_items": "center",
            "width": slider(40), "min_height": slider(40),
            "_flex_grow": 0,
            "border_radius": box(999),
            "border_border": "solid", "border_width": box(1),
        }, globals_={"border_color": color_ref(
            C["rule_dark"] if on_dark else C["border"])}))
    return container([
        _ml_caps(props.get("social_title", "Follow us"), on_dark=on_dark,
                 tone="muted"),
        _row(icons, 10, align="center",
             extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"}),
    ], {"content_width": "full", "flex_direction": "column",
        "flex_gap": gap(10)})


@block("ml.footer")
def ml_footer(props):
    brand = [widget("heading", {
        "title": props.get("brand", ""), "header_size": "div", "align": "left",
        "__typography__": typo_ref(T["wordmark"]),
    }, globals_={"title_color": color_ref(C["white"])})]
    if props.get("blurb"):
        brand.append(_text(props["blurb"], "left", on_dark=True, small=True))
    for k, href in (("phone_display", "tel:" + props.get("phone", "")),
                    ("email", "mailto:" + props.get("email", "")),
                    ("instagram", props.get("instagram_url", ""))):
        if props.get(k):
            brand.append(widget("heading", {
                "title": props[k], "header_size": "div", "align": "left",
                "link": link(href),
                "__typography__": typo_ref(T["body_small"]),
            }, globals_={"title_color": color_ref(C["white"])}))

    if props.get("hours"):
        brand.append(_ml_hours(props))
    soc = _ml_social(props)
    if soc is not None:
        brand.append(soc)

    widths = _tracks([34, 22, 22, 18], 30)
    cols = [_col(brand, widths[0], extra={"flex_gap": gap(18)})]
    for i, group in enumerate(props.get("columns", [])[:3], start=1):
        kids = [_ml_caps(group.get("title", ""), on_dark=True, tone="muted")]
        for l in group.get("links", []):
            kids.append(widget("heading", {
                "title": l.get("label", ""), "header_size": "div",
                "align": "left", "link": link(l.get("url", "#")),
                "__typography__": typo_ref(T["body_small"]),
            }, globals_={"title_color": color_ref(C["on_dark"])}))
        cols.append(_col(kids, widths[i], extra={"flex_gap": gap(10)}))

    rule = container([], {
        "content_width": "full", "min_height": slider(1),
        "margin": dims(36, 0, 22, 0), "background_background": "classic",
    }, globals_={"background_color": color_ref(C["rule_dark"])})

    return _ml_section([_row(cols, 30, align="flex-start"), rule,
                        _text(props.get("legal", ""), "left", on_dark=True,
                              small=True)],
                       "dark", pad=dims(72, 0, 38, 0))
