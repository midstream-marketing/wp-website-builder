"""
blocks_truair.py — TruAir Heating & Cooling (`tru.*`), single-page landing.

The client picked newgenmechanicaltx.com by name ("i really like this one"),
so that site is the SPEC and this family reproduces its devices — rendered and
inventoried 2026-09-21 (design-spec.json, mode "match"). Its signature moves:

    1. THE DIAGONAL WEDGE HERO. A solid brand-colour hero with a white wedge
       cut across the right-hand side, the artwork sitting inside the wedge.
       Built with clip-path, no image editing.
    2. SOLID-COLOUR BENEFIT CARDS overlapping the foot of the hero — the first
       card in the accent colour, the rest in brand blue, white centred text.
    3. CIRCULAR ICON BADGES everywhere: the phone in the utility bar, the
       icon tile on every service card, the rows in the "why choose" panel.
    4. THE CIRCULAR ARROW BUTTON on the right of each service card.
    5. SQUARE NUMBER BADGES overlapping the top-left corner of each process
       card.
    6. THE WHITE CALL CARD — circular phone icon, CALL OR TEXT TODAY, the
       number, and a button, floated at the foot of the about section.
    7. FULL-BLEED BRAND BANDS carrying a centred white headline and an
       outlined pill button.
    8. THE CLOSING FORM PANEL: a photograph with two translucent panels over
       it — contact details left, the enquiry form right.

Palette is TruAir's, not NewGen's: blue #1C74BC and red #EE1C25 sampled from
the supplied logo (the brand colour rule in the fidelity skill — the client's
logo beats the reference's palette). NewGen's navy/pink becomes TruAir
blue/red, and the darker blue for bands is the logo blue darkened.

Every fact the business has not supplied is rendered as a visible PLACEHOLDER
rather than invented — see the README ask list.
"""
from __future__ import annotations

import re

from .core import (
    container, widget, repeater_item, slider, dims, box, media, link, icon,
    gap, color_ref, typo_ref, css,
)
from .tokens import C, T
from .blocks import (
    block, _row, _col, _tracks, _heading, _text, _button, _faq, _hover_lift,
    KIT_CONTAINER, CARD_SHADOW_SOFT, CARD_SHADOW,
)

BLUE = "primary"          # logo blue — buttons, icons, accents
DEEP = "secondary"        # logo blue darkened — full-bleed bands, footer
RED = "accent"            # logo red — the CTA colour
INK = "truin20"          # near-black heading ink (the reference sets headings near-black)
GROUNDS = {"white": C["white"], "grey": C["surface"], "blue": DEEP}

PAD = dims(92, 0, 92, 0)
PAD_T = dims(72, 24, 72, 24)
PAD_M = dims(56, 18, 56, 18)
R_CARD = box(16)
R_PILL = box(40)
GUTTER = 24
_ENTITY = re.compile(r"&([A-Z]+);")


def _caps(text):
    return _ENTITY.sub(lambda m: "&" + m.group(1).lower() + ";", text.upper())


def _dark(bg):
    return bg == "blue"


def _sec(children, bg="white", pad=None, extra=None, anchor=None):
    s = {"content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
         "flex_direction": "column", "flex_gap": gap(40),
         "padding": pad or PAD, "padding_tablet": PAD_T, "padding_mobile": PAD_M,
         "background_background": "classic"}
    if extra:
        s.update(extra)
    if anchor:
        s["_element_id"] = anchor
    return container(children, s, globals_={
        "background_color": color_ref(GROUNDS.get(bg, C["white"]))})


# ───────────────────────────── shared parts ─────────────────────────────

def _eyebrow(text, on_dark=False, align="center"):
    """Small tracked caps eyebrow — blue on light, white on the bands."""
    return widget("heading", {
        "title": _caps(text), "header_size": "div", "align": align,
    }, globals_={"title_color": color_ref(C["white"] if on_dark else C["ink_primary"]),
                 "typography_typography": typo_ref(T["eyebrow"])})


def _pill_eyebrow(text):
    """The hero's solid red pill eyebrow."""
    lab = widget("heading", {"title": _caps(text), "header_size": "div", "align": "center"},
                 globals_={"title_color": color_ref(C["white"]),
                           "typography_typography": typo_ref(T["eyebrow"])})
    return _row([container([lab], {
        "content_width": "full", "flex_direction": "row",
        "flex_justify_content": "center", "flex_align_items": "center",
        "padding": dims(10, 20, 9, 20), "border_radius": R_PILL, "_flex_grow": 0,
        "width": slider(round(50 + len(text) * 9.2)),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(RED)})], 0, justify="flex-start",
        extra={"flex_direction_mobile": "row"})


def _head(props, on_dark=False, align="center", width=82, size="h2"):
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], on_dark, align))
    if props.get("title"):
        kids.append(_heading(props["title"], props.get("size", size), T["h_large"], align,
                             on_dark=on_dark, tone="dark" if not on_dark else "dark"))
    if props.get("intro"):
        kids.append(_text(props["intro"], align, on_dark=on_dark))
    return container(kids, {
        "content_width": "full", "flex_direction": "column", "flex_gap": gap(14),
        "width": slider(width, "%"), "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"),
        "_flex_align_self": "center" if align == "center" else "flex-start"})


def _btn(label, href, style="red", icon_cls=None):
    """red: the estimate/CTA button. blue: solid brand blue. white: white pill
    on a coloured ground. outline: white hairline pill on a coloured ground."""
    b = _button(label, href, "ghost", icon_cls or "")
    s, g = b["settings"], b["settings"]["__globals__"]
    fills = {
        "red": (C["white"], RED, RED, C["white"], DEEP, DEEP),
        "blue": (C["white"], BLUE, BLUE, C["white"], DEEP, DEEP),
        "white": (DEEP, C["white"], C["white"], C["white"], RED, RED),
        "outline": (C["white"], C["transparent"], C["white"], DEEP, C["white"], C["white"]),
    }[style]
    g.update({"button_text_color": color_ref(fills[0]),
              "background_color": color_ref(fills[1]),
              "border_color": color_ref(fills[2]),
              "hover_color": color_ref(fills[3]),
              "button_background_hover_color": color_ref(fills[4]),
              "button_hover_border_color": color_ref(fills[5]),
              "typography_typography": typo_ref(T["meta"])})
    s.update({"border_radius": R_PILL, "border_width": box(2),
              "text_padding": dims(17, 30, 16, 30),
              "icon_align": "left", "icon_indent": slider(9)})
    return b


def _actions(props, on_dark=False, justify="flex-start"):
    kids = []
    if props.get("phone_display"):
        kids.append(_btn(props["phone_display"], "tel:" + props.get("phone", ""),
                         "white" if on_dark else "red", "fas fa-phone-alt"))
    if props.get("cta_label"):
        kids.append(_btn(props["cta_label"], props.get("cta_url", "#estimate"),
                         "outline" if on_dark else "blue"))
    return _row(kids, 14, align="center", justify=justify,
                extra={"flex_direction_mobile": "column",
                       "flex_align_items_mobile": "stretch"})


def _circle_icon(icon_cls, size=52, icon_size=20, fill=None, on_dark=False):
    """The reference's circular icon badge, used in six places."""
    ic = widget("icon", {"selected_icon": icon(icon_cls), "size": slider(icon_size),
                         "align": "center", "view": "default"},
                globals_={"primary_color": color_ref(C["white"] if not on_dark else DEEP)})
    return container([ic], {
        "content_width": "full", "flex_direction": "row",
        "flex_justify_content": "center", "flex_align_items": "center",
        "width": slider(size), "min_height": slider(size), "_flex_grow": 0,
        "_flex_align_self": "flex-start", "border_radius": box(999),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(fill or (C["white"] if on_dark else BLUE))})


def _arrow_button(href):
    """The circular arrow button on the right of every service card."""
    ic = widget("icon", {"selected_icon": icon("fas fa-arrow-right"), "size": slider(16),
                         "align": "center", "view": "default", "link": link(href)},
                globals_={"primary_color": color_ref(C["white"])})
    return container([ic], {
        "content_width": "full", "flex_direction": "row",
        "flex_justify_content": "center", "flex_align_items": "center",
        "width": slider(52), "min_height": slider(52), "_flex_grow": 0,
        "border_radius": box(999), "background_background": "classic",
    }, globals_={"background_color": color_ref(BLUE)})


def _photo(image, height=420, radius=R_CARD):
    image = image or {}
    if not image.get("url"):
        return container([widget("heading", {
            "title": "PLACEHOLDER &mdash; " + image.get("slot", "photo"),
            "header_size": "div", "align": "center"},
            globals_={"title_color": color_ref(C["muted"]),
                      "typography_typography": typo_ref(T["meta"])})], {
            "content_width": "full", "flex_direction": "column",
            "flex_justify_content": "center", "flex_align_items": "center",
            "min_height": slider(height), "border_radius": radius,
            "border_border": "dashed", "border_width": box(2),
            "background_background": "classic"},
            globals_={"background_color": color_ref(C["surface_alt"]),
                      "border_color": color_ref(C["border"])})
    return widget("image", {
        "image": media(image["url"], image.get("alt", "")), "image_size": "large",
        "width": slider(100, "%"), "height": slider(height),
        "height_mobile": slider(round(height * 0.68)), "object-fit": "cover",
        "image_border_radius": radius, "align": "center"})


def _grid(cells, cols, gutter=GUTTER, align="stretch"):
    w = _tracks([1] * cols, gutter)
    tab = 48.4 if cols > 1 else 100
    return _row([_col([c], w[i % cols], extra={"width_tablet": slider(tab, "%")})
                 for i, c in enumerate(cells)], gutter, align=align)


def _card(kids, pad=None, bg=None, shadow=True, radius=None):
    s = {"content_width": "full", "flex_direction": "column", "flex_gap": gap(12),
         "padding": pad or dims(28, 26, 30, 26), "border_radius": radius or R_CARD,
         "background_background": "classic"}
    if shadow:
        s.update(CARD_SHADOW_SOFT)
    return container(kids, s, globals_={"background_color": color_ref(bg or C["white"])})


# ═══════════════════════════════ header ═══════════════════════════════

@block("tru.header")
def tru_header(props):
    """Utility bar (circular phone badge, CALL OR TEXT over the number, email
    and licence right) over a white nav bar with the red CTA — the reference's
    two-tier header."""
    tel = "tel:" + props.get("phone", "")
    call = _row([
        _circle_icon("fas fa-phone-alt", 44, 17),
        container([
            widget("heading", {"title": _caps(props.get("call_label", "Call or Text")),
                               "header_size": "div", "align": "left"},
                   globals_={"title_color": color_ref(INK),
                             "typography_typography": typo_ref(T["eyebrow"])}),
            widget("heading", {"title": props.get("phone_display", ""), "header_size": "div",
                               "align": "left", "link": link(tel)},
                   globals_={"title_color": color_ref(C["ink_primary"]),
                             "typography_typography": typo_ref(T["h_small"])}),
        ], {"content_width": "full", "flex_direction": "column", "flex_gap": gap(0)}),
    ], 12, align="center", extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})

    def meta(text, icon_cls, href=""):
        return _row([
            widget("icon", {"selected_icon": icon(icon_cls), "size": slider(13),
                            "align": "center", "view": "default"},
                   globals_={"primary_color": color_ref(BLUE)}),
            widget("heading", {"title": text, "header_size": "div", "align": "left",
                               **({"link": link(href)} if href else {})},
                   globals_={"title_color": color_ref(INK),
                             "typography_typography": typo_ref(T["meta"])}),
        ], 8, align="center", extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})

    right = []
    if props.get("email"):
        right.append(meta(props["email"], "fas fa-envelope", "mailto:" + props["email"]))
    if props.get("licence"):
        right.append(meta(props["licence"], "fas fa-id-card"))
    w = _tracks([40, 56], 20)
    top = container([_row([
        _col([call], w[0]),
        _col([_row(right, 22, align="center", justify="flex-end",
                   extra={"flex_wrap": "wrap", "flex_direction_mobile": "row"})], w[1],
             extra={"hide_mobile": "hidden-mobile"}),
    ], 20, align="center")], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column", "padding": dims(10, 0, 10, 0),
        "padding_tablet": dims(10, 24, 10, 24), "padding_mobile": dims(8, 14, 8, 14),
        "background_background": "classic",
        "border_border": "solid", "border_width": dims(0, 0, 1, 0),
    }, globals_={"background_color": color_ref(C["white"]),
                 "border_color": color_ref(C["border"])})

    logo = widget("theme-site-logo", {"align": "left",
                                      "width": slider(props.get("logo_width", 190)),
                                      "width_mobile": slider(146)})
    nav = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"), "layout": "horizontal",
        "align_items": "center", "pointer": "underline",
        "menu_space_between": slider(22), "toggle_align": "right",
    }, globals_={"color_menu_item": color_ref(INK),
                 "color_menu_item_hover": color_ref(BLUE),
                 "color_menu_item_active": color_ref(BLUE),
                 "pointer_color_menu_item_hover": color_ref(RED),
                 "pointer_color_menu_item_active": color_ref(RED),
                 "dropdown_background_color": color_ref(C["white"]),
                 "dropdown_color_menu_item": color_ref(INK),
                 "toggle_color": color_ref(BLUE),
                 "menu_typography_typography": typo_ref(T["meta"])})
    w2 = _tracks([24, 52, 22], 20)
    main = container([_row([
        _col([logo], w2[0], extra={"width_mobile": slider(58, "%")}),
        _col([nav], w2[1], extra={"flex_align_items": "center",
                                  "width_mobile": slider(38, "%")}),
        _col([_btn(props.get("cta_label", "Get a Free Estimate"),
                   props.get("cta_url", "#estimate"))], w2[2],
             extra={"flex_align_items": "flex-end", "hide_mobile": "hidden-mobile"}),
    ], 20, align="center", extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column", "padding": dims(14, 0, 14, 0),
        "padding_tablet": dims(12, 24, 12, 24), "padding_mobile": dims(10, 14, 10, 14),
        "background_background": "classic", **CARD_SHADOW_SOFT,
    }, globals_={"background_color": color_ref(C["white"])})
    return container([top, main], {
        "content_width": "full", "flex_direction": "column", "flex_gap": gap(0),
        "sticky": "top", "sticky_on": ["desktop", "tablet", "mobile"], "_z_index": 99})


# ═══════════════════════════════ hero ═══════════════════════════════

@block("tru.hero")
def tru_hero(props):
    """Brand-blue hero with the reference's WHITE DIAGONAL WEDGE on the right,
    the photo inside it. clip-path does the wedge — no image editing, and it
    holds at any width."""
    left = [_pill_eyebrow(props["eyebrow"])] if props.get("eyebrow") else []
    left.append(_heading(props.get("title", ""), "h1", T["hero"], "left", on_dark=True))
    if props.get("intro"):
        left.append(_text(props["intro"], "left", on_dark=True))
    left.append(_actions(props, on_dark=True))
    if props.get("ticks"):
        left.append(widget("icon-list", {
            "icon_list": [repeater_item(text=t, selected_icon=icon("fas fa-check-circle"),
                                        link=link("")) for t in props["ticks"]],
            "view": "inline", "space_between": slider(20), "icon_size": slider(14)},
            globals_={"icon_color": color_ref(C["white"]), "text_color": color_ref(C["white"]),
                      "icon_typography_typography": typo_ref(T["meta"])}))

    photo = _photo(props.get("image"), 520, box(0))
    wedge = container([photo], {
        "content_width": "full", "flex_direction": "column", "flex_justify_content": "center",
        "padding": dims(0, 0, 0, 0), "background_background": "classic",
        "custom_css": css("selector { clip-path: polygon(14% 0, 100% 0, 100% 100%, 0 100%); }"),
    }, globals_={"background_color": color_ref(C["white"])})

    w = _tracks([52, 44], 40)
    row = _row([_col(left, w[0], extra={"flex_gap": gap(20)}),
                _col([wedge], w[1], extra={"hide_mobile": "hidden-mobile"})],
               40, align="center")
    return container([row], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column", "flex_justify_content": "center",
        "min_height": slider(640), "min_height_mobile": slider(0),
        "padding": dims(80, 0, 96, 0), "padding_tablet": dims(64, 24, 72, 24),
        "padding_mobile": dims(48, 18, 56, 18), "background_background": "classic",
    }, globals_={"background_color": color_ref(DEEP)})


@block("tru.cards")
def tru_cards(props):
    """Solid-colour benefit cards straddling the foot of the hero — first card
    in red, the rest brand blue, centred white text. Negative top margin is
    what makes them overlap, exactly as the reference does."""
    cells = []
    for i, it in enumerate(props.get("items", [])):
        fill = RED if i == 0 else BLUE
        kids = [widget("heading", {"title": it["title"], "header_size": "h3", "align": "center"},
                       globals_={"title_color": color_ref(C["white"]),
                                 "typography_typography": typo_ref(T["h_small"])}),
                _text(it["text"], "center", on_dark=True, small=True)]
        cells.append(_card(kids, dims(28, 24, 30, 24), fill, shadow=False))
    sec = _sec([_grid(cells, props.get("columns", 4), 20)], props.get("bg", "grey"),
               pad=dims(0, 0, 84, 0))
    sec["settings"]["margin"] = dims(-64, 0, 0, 0)
    sec["settings"]["margin_mobile"] = dims(-32, 0, 0, 0)
    sec["settings"]["_z_index"] = 2
    return sec


# ═══════════════════════════════ about ═══════════════════════════════

@block("tru.about")
def tru_about(props):
    """Centred eyebrow + big heading, photo left, prose right, and the WHITE
    CALL CARD floated at the foot — circular phone icon, CALL OR TEXT TODAY,
    the number, and a button."""
    prose = [_text(p, "left") for p in props.get("paragraphs", [])]
    if props.get("bullets"):
        prose.append(widget("icon-list", {
            "icon_list": [repeater_item(text=t, selected_icon=icon("fas fa-check-circle"),
                                        link=link("")) for t in props["bullets"]],
            "space_between": slider(12), "icon_size": slider(15)},
            globals_={"icon_color": color_ref(BLUE), "text_color": color_ref("text"),
                      "icon_typography_typography": typo_ref("text")}))
    tel = "tel:" + props.get("phone", "")
    call_card = _card([_row([
        _row([_circle_icon("fas fa-phone-alt", 52, 19),
              container([
                  widget("heading", {"title": _caps(props.get("call_label", "Call or text today!")),
                                     "header_size": "div", "align": "left"},
                         globals_={"title_color": color_ref(INK),
                                   "typography_typography": typo_ref(T["eyebrow"])}),
                  widget("heading", {"title": props.get("phone_display", ""), "header_size": "div",
                                     "align": "left", "link": link(tel)},
                         globals_={"title_color": color_ref(C["ink_primary"]),
                                   "typography_typography": typo_ref(T["h_medium"])}),
              ], {"content_width": "full", "flex_direction": "column", "flex_gap": gap(2)}),
              ], 14, align="center", extra={"flex_wrap": "nowrap",
                                            "flex_direction_mobile": "row"}),
        _btn(props.get("cta_label", "Get a Free Estimate"), props.get("cta_url", "#estimate")),
    ], 20, align="center", justify="space-between")], dims(22, 24, 22, 24))
    if props.get("show_call", True) and props.get("phone_display"):
        prose.append(call_card)

    w = _tracks([46, 50], 48)
    cols = [_col([_photo(props.get("image"), 460)], w[0]),
            _col(prose, w[1], extra={"flex_gap": gap(16)})]
    if props.get("flip"):
        cols.reverse()
    return _sec([_head(props), _row(cols, 48, align="center")],
                props.get("bg", "grey"), anchor=props.get("anchor"))


@block("tru.band")
def tru_band(props):
    """Full-bleed brand band: centred white headline and an outlined pill."""
    kids = [_heading(props.get("title", ""), "h2", T["h_large"], "center", on_dark=True)]
    if props.get("text"):
        kids.append(_text(props["text"], "center", on_dark=True))
    if props.get("cta_label"):
        kids.append(_row([_btn(props["cta_label"], props.get("cta_url", "#estimate"), "outline")],
                         0, justify="center"))
    inner = container(kids, {"content_width": "full", "flex_direction": "column",
                             "flex_gap": gap(20), "width": slider(80, "%"),
                             "width_tablet": slider(100, "%"), "width_mobile": slider(100, "%"),
                             "_flex_align_self": "center"})
    return _sec([inner], "blue", pad=dims(72, 0, 72, 0), anchor=props.get("anchor"))


# ═══════════════════════════════ services ═══════════════════════════════

@block("tru.services")
def tru_services(props):
    """Two-up white cards: circular icon tile, title, one line, and the
    CIRCULAR ARROW BUTTON on the right."""
    def card(it):
        body = container([
            widget("heading", {"title": it["title"], "header_size": "h3", "align": "left"},
                   globals_={"title_color": color_ref(INK),
                             "typography_typography": typo_ref(T["h_medium"])}),
            _text(it.get("text", ""), "left", small=True),
        ], {"content_width": "full", "flex_direction": "column", "flex_gap": gap(6)})
        w = _tracks([14, 66, 14], 12)
        inner = _row([
            _col([_circle_icon(it.get("icon", "fas fa-snowflake"), 56, 22)], w[0]),
            _col([body], w[1]),
            _col([_arrow_button(it.get("url", props.get("cta_url", "#estimate")))], w[2],
                 extra={"flex_align_items": "flex-end", "flex_justify_content": "center"}),
        ], 12, align="center", extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})
        return _hover_lift(_card([inner], dims(22, 22, 22, 22)), 4)

    kids = [_head(props)] if props.get("title") else []
    kids.append(_grid([card(i) for i in props.get("items", [])], props.get("columns", 2), 22))
    if props.get("phone_display") or props.get("cta_label"):
        kids.append(_actions(props, justify="center"))
    if props.get("note"):
        kids.append(_text(props["note"], "center", small=True))
    return _sec(kids, props.get("bg", "grey"), anchor=props.get("anchor"))


@block("tru.why")
def tru_why(props):
    """Brand band: copy and buttons left, bordered rows with circular icons
    right — the reference's 'why choose us' panel."""
    left = [_eyebrow(props.get("eyebrow", ""), True, "left"),
            _heading(props.get("title", ""), "h2", T["h_large"], "left", on_dark=True)]
    for p in props.get("paragraphs", []):
        left.append(_text(p, "left", on_dark=True))
    left.append(_actions(props, on_dark=True))

    rows = []
    for it in props.get("items", []):
        rows.append(container([_row([
            _circle_icon(it.get("icon", "fas fa-check"), 54, 20, fill=C["overlay"]),
            container([
                widget("heading", {"title": it["title"], "header_size": "h3", "align": "left"},
                       globals_={"title_color": color_ref(C["white"]),
                                 "typography_typography": typo_ref(T["h_small"])}),
                *([_text(it["text"], "left", on_dark=True, small=True)] if it.get("text") else []),
            ], {"content_width": "full", "flex_direction": "column", "flex_gap": gap(4)}),
        ], 16, align="center", extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})], {
            "content_width": "full", "flex_direction": "column",
            "padding": dims(18, 20, 18, 20), "border_radius": box(12),
            "border_border": "solid", "border_width": box(1)},
            globals_={"border_color": color_ref(C["rule_dark"])}))
    right = container(rows, {"content_width": "full", "flex_direction": "column",
                             "flex_gap": gap(14)})
    w = _tracks([46, 50], 48)
    return _sec([_row([_col(left, w[0], extra={"flex_gap": gap(18)}), _col([right], w[1])],
                      48, align="center")], "blue", anchor=props.get("anchor"))


@block("tru.process")
def tru_process(props):
    """Four white cards, each with a SQUARE NUMBER BADGE overlapping the
    top-left corner and a circular icon — the reference's process row."""
    def step(s, i):
        badge = container([widget("heading", {
            "title": str(i + 1), "header_size": "div", "align": "center"},
            globals_={"title_color": color_ref(C["white"]),
                      "typography_typography": typo_ref(T["h_small"])})], {
            "content_width": "full", "flex_direction": "row",
            "flex_justify_content": "center", "flex_align_items": "center",
            "width": slider(52), "min_height": slider(52), "_flex_grow": 0,
            "border_radius": box(10), "background_background": "classic",
            "_position": "absolute", "_offset_orientation_h": "start",
            "_offset_x": slider(-10), "_offset_orientation_v": "start",
            "_offset_y": slider(-18), "_z_index": 3,
        }, globals_={"background_color": color_ref(BLUE)})
        card = _card([
            _row([_circle_icon(s.get("icon", "fas fa-comments"), 60, 23)], 0, justify="center"),
            widget("heading", {"title": s["title"], "header_size": "h3", "align": "center"},
                   globals_={"title_color": color_ref(INK),
                             "typography_typography": typo_ref(T["h_small"])}),
            _text(s["text"], "center", small=True),
        ], dims(38, 24, 30, 24))
        card["settings"]["flex_align_items"] = "center"
        return container([badge, card], {"content_width": "full", "flex_direction": "column",
                                         "margin": dims(20, 0, 0, 0)})

    steps = props.get("steps", [])
    return _sec([_head(props), _grid([step(s, i) for i, s in enumerate(steps)],
                                     len(steps) or 4, 24, "stretch")],
                props.get("bg", "white"), anchor=props.get("anchor"))


# ═══════════════════════════════ closing form ═══════════════════════════════

def _fields(fields):
    out = []
    for f in fields:
        item = {"custom_id": f["id"], "field_type": f.get("type", "text"),
                "field_label": f.get("label", ""), "placeholder": f.get("placeholder", ""),
                "required": "true" if f.get("required") else "",
                "width": str(f.get("width", 100))}
        if f.get("options"):
            item["field_options"] = "\n".join(f["options"])
        if f.get("rows"):
            item["rows"] = f["rows"]
        out.append(repeater_item(**item))
    return out


@block("tru.estimate")
def tru_estimate(props):
    """The closing panel: a photograph with two translucent panels over it —
    contact details left, the enquiry form right. The client asked for one
    simple form; this is it, and it is the only form on the page."""
    f = props.get("form", {})
    tel = "tel:" + props.get("phone", "")

    def detail_row(label, value, icon_cls, href=""):
        return _row([
            _circle_icon(icon_cls, 50, 18),
            container([
                widget("heading", {"title": _caps(label), "header_size": "div", "align": "left"},
                       globals_={"title_color": color_ref(C["on_dark"]),
                                 "typography_typography": typo_ref(T["eyebrow"])}),
                widget("heading", {"title": value, "header_size": "div", "align": "left",
                                   **({"link": link(href)} if href else {})},
                       globals_={"title_color": color_ref(C["white"]),
                                 "typography_typography": typo_ref(T["h_small"])}),
            ], {"content_width": "full", "flex_direction": "column", "flex_gap": gap(2)}),
        ], 14, align="center", extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})

    left = [_heading(props.get("title", ""), "h2", T["h_large"], "left", on_dark=True)]
    if props.get("text"):
        left.append(_text(props["text"], "left", on_dark=True))
    if props.get("phone_display"):
        left.append(detail_row(props.get("call_label", "Call or text today"),
                               props["phone_display"], "fas fa-phone-alt", tel))
    if props.get("email"):
        left.append(detail_row("Email", props["email"], "fas fa-envelope",
                               "mailto:" + props["email"]))
    if props.get("area"):
        left.append(detail_row("Service area", props["area"], "fas fa-map-marker-alt"))
    left_panel = container(left, {
        "content_width": "full", "flex_direction": "column", "flex_gap": gap(18),
        "padding": dims(40, 36, 40, 36), "padding_mobile": dims(26, 20, 26, 20),
        "border_radius": R_CARD, "background_background": "classic",
    }, globals_={"background_color": color_ref(C["overlay"])})

    form = widget("form", {
        "form_name": f.get("form_name", "Free Estimate Request"),
        "form_fields": _fields(f["fields"]),
        "submit_actions": ["email"],
        "email_to": f.get("email", ""),
        "email_subject": "New website enquiry - TruAir Heating & Cooling",
        "button_text": f.get("submit", "Send Request"),
        "button_size": "md", "button_width": "100", "input_size": "md",
        "show_labels": "yes", "mark_required": "yes",
        "row_gap": slider(14), "column_gap": slider(14),
        "success_message": f.get("success", ""),
        "field_border_radius": box(6), "field_border_width": box(1),
        "button_border_radius": R_PILL,
    }, globals_={"button_background_color": color_ref(RED),
                 "button_background_hover_color": color_ref(BLUE),
                 "button_text_color": color_ref(C["white"]),
                 "field_background_color": color_ref(C["white"]),
                 "field_text_color": color_ref(INK),
                 "field_border_color": color_ref(C["border"]),
                 "label_color": color_ref(C["white"]),
                 "mark_required_color": color_ref(C["white"]),
                 "button_typography_typography": typo_ref(T["meta"])})
    form_panel = container([form], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(36, 34, 38, 34), "padding_mobile": dims(24, 18, 26, 18),
        "border_radius": R_CARD, "background_background": "classic",
    }, globals_={"background_color": color_ref(C["overlay"])})

    w = _tracks([46, 50], 34)
    s = {"content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
         "flex_direction": "column", "padding": dims(84, 0, 84, 0),
         "padding_tablet": dims(66, 24, 66, 24), "padding_mobile": dims(48, 16, 48, 16),
         "background_background": "classic",
         "_element_id": props.get("anchor", "estimate")}
    img = props.get("image") or {}
    g = {}
    if img.get("url"):
        s.update({"background_image": media(img["url"], img.get("alt", "")),
                  "background_position": "center center", "background_size": "cover",
                  "background_overlay_background": "classic",
                  "background_overlay_color": "rgba(10, 32, 54, 0.72)"})
    else:
        g["background_color"] = color_ref(DEEP)
    return container([_row([_col([left_panel], w[0]), _col([form_panel], w[1])],
                           34, align="stretch")], s, globals_=g)


# ═══════════════════════════════ faq / footer ═══════════════════════════════

@block("tru.faq")
def tru_faq(props):
    acc = _faq(props.get("items", []), True)
    acc["settings"]["faq_schema"] = "yes"
    acc["settings"]["__globals__"]["accordion_item_title_icon_color"] = color_ref(RED)
    body = container([acc], {"content_width": "full", "flex_direction": "column",
                             "width": slider(84, "%"), "width_tablet": slider(100, "%"),
                             "width_mobile": slider(100, "%"), "_flex_align_self": "center"})
    return _sec([_head(props), body], props.get("bg", "white"), anchor=props.get("anchor"))


@block("tru.footer")
def tru_footer(props):
    # The footer is deep blue, and the client's logo is blue type on white, so
    # the Site Logo widget is wrong here. `logo` takes the reversed (white)
    # version prepared by prepare-logos.py; without it we fall back to the
    # theme logo rather than shipping a blue-on-blue wordmark.
    brand = [widget("image", {"image": media(props["logo"], props.get("logo_alt", "")),
                              "image_size": "full", "width": slider(210), "align": "left"})
             if props.get("logo") else
             widget("theme-site-logo", {"align": "left", "width": slider(200)})]
    if props.get("blurb"):
        brand.append(_text(props["blurb"], "left", on_dark=True, small=True))
    if props.get("social"):
        icons = [widget("icon", {"selected_icon": icon(s.get("icon", "fas fa-link")),
                                 "size": slider(16), "align": "center", "view": "default",
                                 "link": link(s.get("url", "#"), external=True)},
                        globals_={"primary_color": color_ref(C["white"])})
                 for s in props["social"]]
        brand.append(_row(icons, 16, align="center", extra={"flex_wrap": "nowrap",
                                                            "flex_direction_mobile": "row"}))

    def title(t):
        return widget("heading", {"title": t, "header_size": "h3", "align": "left"},
                      globals_={"title_color": color_ref(C["white"]),
                                "typography_typography": typo_ref(T["h_small"])})

    def links(items, icon_cls="fas fa-arrow-right"):
        return widget("icon-list", {
            "icon_list": [repeater_item(text=i["label"], selected_icon=icon(i.get("icon", icon_cls)),
                                        link=link(i.get("url", ""))) for i in items],
            "space_between": slider(11), "icon_size": slider(12)},
            globals_={"icon_color": color_ref(C["white"]), "text_color": color_ref(C["on_dark"]),
                      "icon_typography_typography": typo_ref(T["body_small"])})

    w = _tracks([34, 22, 24, 20], 30)
    cols = [_col(brand, w[0], extra={"flex_gap": gap(18)})]
    for i, g in enumerate(props.get("columns", [])[:3], start=1):
        cols.append(_col([title(g["title"]), links(g["links"], g.get("icon", "fas fa-arrow-right"))],
                         w[i], extra={"flex_gap": gap(14)}))
    rule = container([], {"content_width": "full", "min_height": slider(1),
                          "margin": dims(40, 0, 22, 0), "background_background": "classic"},
                     globals_={"background_color": color_ref(C["rule_dark"])})
    return _sec([_row(cols, 30, align="flex-start"), rule,
                 _text(props.get("legal", ""), "left", on_dark=True, small=True)],
                "blue", pad=dims(74, 0, 34, 0))


@block("tru.stickybar")
def tru_stickybar(props):
    call = _btn(props.get("call_label", "Call Now"), "tel:" + props.get("phone", ""),
                "blue", "fas fa-phone-alt")
    est = _btn(props.get("cta_label", "Free Estimate"), props.get("cta_url", "#estimate"))
    return container([_row([call, est], 10, align="center", justify="center",
                           extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(10, 12, 10, 12), "background_background": "classic",
        "hide_desktop": "hidden-desktop", "hide_tablet": "hidden-tablet",
        "_position": "fixed", "_offset_orientation_v": "end",
        "_offset_y_end": slider(0), "_offset_x": slider(0),
        "width": slider(100, "%"), "_z_index": 998,
        "border_border": "solid", "border_width": dims(1, 0, 0, 0),
    }, globals_={"background_color": color_ref(C["white"]),
                 "border_color": color_ref(C["border"])})
