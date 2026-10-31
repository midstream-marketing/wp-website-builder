"""
blocks_onsight.py — OnSight Window Films LLC (`os.*`), Rochester NY.

No design reference was supplied — "make sure the website looks premium
contractor" — so, as with Magic Renovations, the LOGO specifies the design
(design-spec.json, mode "specified"). The mark gives four rules:

    1. THE LABEL BOX. "SIGHT" is white condensed caps reversed out of a
       solid black box. Every section opens with that box — a short caps
       label in a black block — followed by…
    2. THE BLUE ARROW. The mark ends in a blue right-pointing triangle.
       It is the only colour in the logo, so blue is spent sparingly: the
       arrow after each label, the arrow in each button, list bullets, the
       primary button and a 4px rule along the top of the header (the logo
       artwork carries that blue line too).
    3. TWO WEIGHTS OF TYPE. A heavy wide "ON" against a tall condensed
       "SIGHT". Headings are Barlow Condensed in caps; body is Inter.
    4. BLACK AND WHITE, HARD-EDGED. Square corners (2px), no pastel tints,
       black bands for the moments that matter (why us, the CTA, footer).

Content rules this family enforces:
    * Stock photos illustrate film applications only; the Gallery takes
      real OnSight projects and ships as labelled PLACEHOLDER slots.
    * Safety film copy is written in "does / does not" pairs (`os.honest`),
      because the brief says "without making unsupported guarantees".

Colour comes from the Global Kit via intake.json.
"""
from __future__ import annotations

import re

from .core import (
    container, widget, repeater_item, slider, dims, box, media, link, icon,
    gap, color_ref, typo_ref,
)
from .tokens import C, T
from .blocks import (
    block, _row, _col, _tracks, _heading, _text, _button, _faq, _hover_lift,
    KIT_CONTAINER, CARD_SHADOW_SOFT,
)

BLUE = "primary"
INK = "secondary"
HI = "accent"            # blue lifted for use on black
GROUNDS = {"white": C["white"], "grey": C["surface"], "ink": INK}

PAD = dims(96, 0, 96, 0)
PAD_T = dims(72, 24, 72, 24)
PAD_M = dims(56, 20, 56, 20)
R = box(2)
GUTTER = 26
ARROW = "fas fa-play"
_ENTITY = re.compile(r"&([A-Z]+);")


def _caps(text):
    return _ENTITY.sub(lambda m: "&" + m.group(1).lower() + ";", text.upper())


def _dark(bg):
    return bg == "ink"


def _sec(children, bg="white", pad=None, extra=None, anchor=None):
    s = {"content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
         "flex_direction": "column", "flex_gap": gap(44),
         "padding": pad or PAD, "padding_tablet": PAD_T, "padding_mobile": PAD_M,
         "background_background": "classic"}
    if extra:
        s.update(extra)
    if anchor:
        s["_element_id"] = anchor
    return container(children, s, globals_={
        "background_color": color_ref(GROUNDS.get(bg, C["white"]))})


def _condensed(size, weight="600", spacing=2.0, upper=True):
    """Barlow Condensed set locally for the label box and buttons — small
    tracked caps in the heading face, which no kit typography token offers."""
    s = {"typography_typography": "custom",
         "typography_font_family": "Barlow Condensed",
         "typography_font_weight": weight,
         "typography_font_size": slider(size),
         "typography_letter_spacing": slider(spacing)}
    if upper:
        s["typography_text_transform"] = "uppercase"
    return s


# ───────────────────────────── signature parts ─────────────────────────────

def _arrow(size=11, on_dark=False):
    return widget("icon", {"selected_icon": icon(ARROW), "size": slider(size),
                           "align": "center", "view": "default"},
                  globals_={"primary_color": color_ref(HI if on_dark else BLUE)})


def _label(text, on_dark=False, justify="flex-start"):
    """The SIGHT box: condensed caps reversed out of a solid block, then the
    blue arrow. On black grounds the box inverts to white."""
    lab = widget("heading", {"title": _caps(text), "header_size": "div",
                             "align": "center", **_condensed(15, "600", 2.2)},
                 globals_={"title_color": color_ref(INK if on_dark else C["white"])})
    boxc = container([lab], {
        "content_width": "full", "flex_direction": "row",
        "flex_justify_content": "center", "flex_align_items": "center",
        "padding": dims(6, 12, 5, 12), "_flex_grow": 0,
        "width": slider(round(28 + len(text) * 9.6)),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["white"] if on_dark else INK)})
    return _row([boxc, _arrow(13, on_dark)], 10, align="center", justify=justify,
                extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})


def _head(props, on_dark=False, align="left", width=78):
    kids = []
    if props.get("label"):
        kids.append(_label(props["label"], on_dark,
                           "center" if align == "center" else "flex-start"))
    if props.get("title"):
        kids.append(_heading(props["title"], props.get("size", "h2"), T["h_large"],
                             align, on_dark=on_dark))
    if props.get("intro"):
        kids.append(_text(props["intro"], align, on_dark=on_dark))
    return container(kids, {
        "content_width": "full", "flex_direction": "column", "flex_gap": gap(16),
        "width": slider(width, "%"), "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"),
        "_flex_align_self": "center" if align == "center" else "flex-start"})


def _btn(label, href, style="blue", icon_cls=ARROW):
    """blue: the primary Get-a-Free-Estimate button. ink: solid black.
    ghost: black hairline on light. outline: white hairline on black/photo."""
    b = _button(label, href, "ghost", icon_cls)
    s, g = b["settings"], b["settings"]["__globals__"]
    g.pop("typography_typography", None)
    fills = {
        "blue": (C["white"], BLUE, BLUE, C["white"], INK, INK),
        "ink": (C["white"], INK, INK, C["white"], BLUE, BLUE),
        "ghost": (INK, C["transparent"], INK, C["white"], INK, INK),
        "outline": (C["white"], C["transparent"], C["white"], INK, C["white"], C["white"]),
    }[style]
    g.update({"button_text_color": color_ref(fills[0]),
              "background_color": color_ref(fills[1]),
              "border_color": color_ref(fills[2]),
              "hover_color": color_ref(fills[3]),
              "button_background_hover_color": color_ref(fills[4]),
              "button_hover_border_color": color_ref(fills[5])})
    s.update({"border_radius": R, "border_width": box(2),
              "text_padding": dims(16, 28, 15, 28),
              "icon_align": "right" if icon_cls == ARROW else "left",
              "icon_indent": slider(10), **_condensed(17, "700", 1.4)})
    return b


def _actions(props, on_dark=False, justify="flex-start"):
    kids = []
    if props.get("cta_label"):
        kids.append(_btn(props["cta_label"], props.get("cta_url", "/get-a-free-estimate/")))
    if props.get("phone_display"):
        kids.append(_btn(props["phone_display"], "tel:" + props.get("phone", ""),
                         "outline" if on_dark else "ghost", "fas fa-phone-alt"))
    return _row(kids, 14, align="center", justify=justify,
                extra={"flex_direction_mobile": "column",
                       "flex_align_items_mobile": "stretch"})


def _slot(label, height=300):
    txt = widget("heading", {"title": "PLACEHOLDER &mdash; " + label,
                             "header_size": "div", "align": "center"},
                 globals_={"title_color": color_ref(C["muted"]),
                           "typography_typography": typo_ref(T["meta"])})
    return container([txt], {
        "content_width": "full", "flex_direction": "column",
        "flex_justify_content": "center", "flex_align_items": "center",
        "min_height": slider(height), "min_height_mobile": slider(round(height * .7)),
        "padding": dims(20, 20, 20, 20), "border_radius": R,
        "border_border": "dashed", "border_width": box(2),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["surface_alt"]),
                 "border_color": color_ref(C["border"])})


def _photo(image, height=340, lightbox=False):
    image = image or {}
    if not image.get("url"):
        return _slot(image.get("slot", "project photo"), height)
    s = {"image": media(image["url"], image.get("alt", "")), "image_size": "large",
         "width": slider(100, "%"), "height": slider(height),
         "height_mobile": slider(round(height * .7)), "object-fit": "cover",
         "image_border_radius": R, "align": "center"}
    if lightbox:
        s.update({"link_to": "file", "open_lightbox": "yes"})
    return widget("image", s)


def _ticks(items, on_dark=False, cols=1):
    per = max(1, -(-len(items) // cols))
    chunks = [items[i:i + per] for i in range(0, len(items), per)]
    lists = [widget("icon-list", {
        "icon_list": [repeater_item(text=t, selected_icon=icon(ARROW), link=link(""))
                      for t in ch],
        "space_between": slider(12), "icon_size": slider(10),
    }, globals_={"icon_color": color_ref(HI if on_dark else BLUE),
                 "text_color": color_ref(C["white"] if on_dark else "text"),
                 "icon_typography_typography": typo_ref("text")}) for ch in chunks]
    if len(lists) == 1:
        return lists[0]
    w = _tracks([1] * len(lists), 30)
    return _row([_col([l], w[i]) for i, l in enumerate(lists)], 30, align="flex-start")


def _grid(cells, cols, gutter=GUTTER, align="stretch"):
    w = _tracks([1] * cols, gutter)
    tab = 48.4 if cols > 1 else 100
    return _row([_col([c], w[i % cols], extra={"width_tablet": slider(tab, "%")})
                 for i, c in enumerate(cells)], gutter, align=align)


def _card(kids, pad=None, bg=None, shadow=True):
    s = {"content_width": "full", "flex_direction": "column", "flex_gap": gap(12),
         "padding": pad or dims(28, 26, 28, 26), "border_radius": R,
         "border_border": "solid", "border_width": box(1),
         "background_background": "classic"}
    if shadow:
        s.update(CARD_SHADOW_SOFT)
    return container(kids, s, globals_={"background_color": color_ref(bg or C["white"]),
                                        "border_color": color_ref(C["border"])})


def _title(text, size="h3", on_dark=False, token=None):
    return _heading(text, size, token or T["h_medium"], "left", on_dark=on_dark)


def _icon_tile(icon_cls, on_dark=False):
    return container([widget("icon", {"selected_icon": icon(icon_cls), "size": slider(22),
                                      "align": "center", "view": "default"},
                             globals_={"primary_color": color_ref(C["white"])})], {
        "content_width": "full", "flex_direction": "row",
        "flex_justify_content": "center", "flex_align_items": "center",
        "width": slider(52), "min_height": slider(52), "_flex_grow": 0,
        "_flex_align_self": "flex-start", "border_radius": R,
        "background_background": "classic",
    }, globals_={"background_color": color_ref(BLUE)})


# ═══════════════════════════════ header ═══════════════════════════════

@block("os.header")
def os_header(props):
    """Blue 4px rule, black utility bar (service area · phones · email), white
    main bar with the logo, nav and the blue estimate button. Sticky."""
    def meta(text, icon_cls, href=""):
        kids = [widget("icon", {"selected_icon": icon(icon_cls), "size": slider(12),
                                "align": "center", "view": "default"},
                       globals_={"primary_color": color_ref(HI)}),
                widget("heading", {"title": text, "header_size": "div", "align": "left",
                                   **({"link": link(href)} if href else {})},
                       globals_={"title_color": color_ref(C["white"]),
                                 "typography_typography": typo_ref(T["meta"])})]
        return _row(kids, 8, align="center", extra={"flex_wrap": "nowrap",
                                                    "flex_direction_mobile": "row"})

    rule = container([], {"content_width": "full", "min_height": slider(4),
                          "background_background": "classic"},
                     globals_={"background_color": color_ref(BLUE)})
    right = [meta(p["display"], "fas fa-phone-alt", "tel:" + p["tel"])
             for p in props.get("phones", [])]
    if props.get("email"):
        right.append(meta(props["email"], "fas fa-envelope", "mailto:" + props["email"]))
    w = _tracks([40, 56], 20)
    top = container([_row([
        _col([meta(props.get("area_line", ""), "fas fa-map-marker-alt")], w[0],
             extra={"hide_mobile": "hidden-mobile"}),
        _col([_row(right, 22, align="center", justify="flex-end",
                   extra={"flex_direction_mobile": "row", "flex_wrap": "wrap",
                          "flex_justify_content_mobile": "center"})], w[1]),
    ], 20, align="center")], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column", "padding": dims(8, 0, 8, 0),
        "padding_tablet": dims(8, 24, 8, 24), "padding_mobile": dims(8, 14, 8, 14),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(INK)})

    logo = widget("theme-site-logo", {"align": "left", "width": slider(210),
                                      "width_tablet": slider(190), "width_mobile": slider(160)})
    nav = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"), "layout": "horizontal",
        "align_items": "center", "pointer": "underline",
        "menu_space_between": slider(20), "toggle_align": "right",
        "submenu_icon": {"value": "fas fa-caret-down", "library": "fa-solid"},
    }, globals_={"color_menu_item": color_ref(INK), "color_menu_item_hover": color_ref(BLUE),
                 "color_menu_item_active": color_ref(INK),
                 "pointer_color_menu_item_hover": color_ref(BLUE),
                 "pointer_color_menu_item_active": color_ref(BLUE),
                 "dropdown_background_color": color_ref(C["white"]),
                 "dropdown_color_menu_item": color_ref(INK),
                 "toggle_color": color_ref(INK),
                 "menu_typography_typography": typo_ref(T["meta"])})
    w2 = _tracks([20, 58, 20], 20)
    main = container([_row([
        _col([logo], w2[0], extra={"width_mobile": slider(62, "%")}),
        _col([nav], w2[1], extra={"flex_align_items": "center",
                                  "width_mobile": slider(34, "%")}),
        _col([_btn(props.get("cta_label", "Get a Free Estimate"),
                   props.get("cta_url", "/get-a-free-estimate/"))], w2[2],
             extra={"flex_align_items": "flex-end", "hide_mobile": "hidden-mobile"}),
    ], 20, align="center", extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column", "padding": dims(14, 0, 14, 0),
        "padding_tablet": dims(12, 24, 12, 24), "padding_mobile": dims(10, 14, 10, 14),
        "background_background": "classic", **CARD_SHADOW_SOFT,
    }, globals_={"background_color": color_ref(C["white"])})
    return container([rule, top, main], {
        "content_width": "full", "flex_direction": "column", "flex_gap": gap(0),
        "sticky": "top", "sticky_on": ["desktop", "tablet", "mobile"], "_z_index": 99})


# ═══════════════════════════════ heroes ═══════════════════════════════

def _photo_bg(s, image, strength):
    if image and image.get("url"):
        s.update({"background_image": media(image["url"], image.get("alt", "")),
                  "background_position": "center center", "background_size": "cover",
                  "background_overlay_background": "classic",
                  "background_overlay_color": "rgba(14, 15, 17, %.2f)" % strength})
        return {}
    return {"background_color": color_ref(INK)}


def _trust(items):
    cells = []
    for it in items:
        cells.append(_row([_arrow(12, True),
                           widget("heading", {"title": it, "header_size": "div",
                                              "align": "left", **_condensed(17, "600", 1.2)},
                                  globals_={"title_color": color_ref(C["white"])})],
                          10, align="center", extra={"flex_wrap": "nowrap",
                                                     "flex_direction_mobile": "row"}))
    return _row(cells, 28, align="center", extra={"flex_direction_mobile": "column",
                                                  "flex_align_items_mobile": "flex-start"})


@block("os.hero")
def os_hero(props):
    """Full-bleed photo under a black wash; label box, condensed H1, sub, the
    two actions, and a trust line of arrow-led facts along the bottom."""
    kids = []
    if props.get("label"):
        kids.append(_label(props["label"], True))
    kids.append(_heading(props.get("title", ""), "h1", T["hero"], "left", on_dark=True))
    if props.get("intro"):
        kids.append(_text(props["intro"], "left", on_dark=True))
    kids.append(_actions(props, True))
    body = container(kids, {"content_width": "full", "flex_direction": "column",
                            "flex_gap": gap(22), "width": slider(64, "%"),
                            "width_tablet": slider(100, "%"), "width_mobile": slider(100, "%")})
    parts = [body]
    if props.get("trust"):
        rule = container([], {"content_width": "full", "min_height": slider(1),
                              "margin": dims(26, 0, 6, 0), "background_background": "classic"},
                         globals_={"background_color": color_ref(C["rule_dark"])})
        parts += [rule, _trust(props["trust"])]
    s = {"content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
         "flex_direction": "column", "flex_justify_content": "center",
         "min_height": slider(700), "min_height_mobile": slider(0),
         "padding": dims(110, 0, 64, 0), "padding_tablet": dims(84, 24, 56, 24),
         "padding_mobile": dims(60, 18, 44, 18), "background_background": "classic"}
    return container(parts, s, globals_=_photo_bg(s, props.get("image"), .70))


@block("os.pagehero")
def os_pagehero(props):
    kids = []
    if props.get("label"):
        kids.append(_label(props["label"], True))
    kids.append(_heading(props.get("title", ""), "h1", T["hero"], "left", on_dark=True))
    if props.get("intro"):
        kids.append(_text(props["intro"], "left", on_dark=True))
    if props.get("cta_label") or props.get("phone_display"):
        kids.append(_actions(props, True))
    body = container(kids, {"content_width": "full", "flex_direction": "column",
                            "flex_gap": gap(20), "width": slider(70, "%"),
                            "width_tablet": slider(100, "%"), "width_mobile": slider(100, "%")})
    s = {"content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
         "flex_direction": "column", "flex_justify_content": "center",
         "min_height": slider(480), "min_height_mobile": slider(0),
         "padding": dims(90, 0, 90, 0), "padding_tablet": dims(70, 24, 70, 24),
         "padding_mobile": dims(52, 18, 52, 18), "background_background": "classic"}
    return container([body], s, globals_=_photo_bg(s, props.get("image"), .72))


# ═══════════════════════════════ content ═══════════════════════════════

@block("os.split")
def os_split(props):
    bg = props.get("bg", "white")
    on_dark = _dark(bg)
    body = [_head(dict(props, intro=""), on_dark, width=100)]
    for p in props.get("paragraphs", []):
        body.append(_text(p, "left", on_dark=on_dark))
    if props.get("bullets"):
        body.append(_ticks(props["bullets"], on_dark, props.get("bullet_cols", 1)))
    if props.get("cta_label") or props.get("phone_display"):
        body.append(_actions(props, on_dark))
    img = props.get("image") or {}
    ph = [_photo(img, props.get("height", 480))]
    w = _tracks([50, 46], 56)
    cols = [_col(body, w[0], extra={"flex_gap": gap(18)}), _col(ph, w[1])]
    if props.get("flip"):
        cols.reverse()
    return _sec([_row(cols, 56, align="center")], bg, anchor=props.get("anchor"))


@block("os.prose")
def os_prose(props):
    bg = props.get("bg", "white")
    on_dark = _dark(bg)
    kids = [_head(dict(props, intro=""), on_dark, width=100)]
    for p in props.get("paragraphs", []):
        kids.append(_text(p, "left", on_dark=on_dark))
    if props.get("bullets"):
        kids.append(_ticks(props["bullets"], on_dark, props.get("bullet_cols", 1)))
    inner = container(kids, {"content_width": "full", "flex_direction": "column",
                             "flex_gap": gap(18), "width": slider(props.get("width", 80), "%"),
                             "width_tablet": slider(100, "%"), "width_mobile": slider(100, "%")})
    return _sec([inner], bg, anchor=props.get("anchor"))


@block("os.services")
def os_services(props):
    """Photo-topped service cards: condensed title, text, 'Learn more ▶'."""
    bg = props.get("bg", "grey")

    def card(it):
        kids = [_photo(it.get("image"), 230)]
        t = _title(it["title"])
        if it.get("url"):
            t["settings"]["link"] = link(it["url"])
        body = [t, _text(it.get("text", ""), "left", small=True)]
        if it.get("url"):
            body.append(_row([_btn(it.get("link_label", "Learn More"), it["url"], "ghost")], 0))
        kids.append(container(body, {"content_width": "full", "flex_direction": "column",
                                     "flex_gap": gap(12), "padding": dims(22, 22, 24, 22)}))
        c = _card(kids, dims(0, 0, 0, 0))
        c["settings"]["flex_gap"] = gap(0)
        return _hover_lift(c, 5)

    head = [_head(props, _dark(bg))] if props.get("title") else []
    return _sec(head + [_grid([card(i) for i in props.get("items", [])],
                              props.get("columns", 4), 22)], bg, anchor=props.get("anchor"))


@block("os.benefits")
def os_benefits(props):
    """Blue square icon tile, condensed title, short text — on white or black."""
    bg = props.get("bg", "white")
    on_dark = _dark(bg)

    def cell(it):
        kids = [_icon_tile(it.get("icon", "fas fa-check")),
                _title(it["title"], "h3", on_dark),
                _text(it.get("text", ""), "left", on_dark=on_dark, small=True)]
        if on_dark:
            return container(kids, {"content_width": "full", "flex_direction": "column",
                                    "flex_gap": gap(12), "padding": dims(28, 24, 28, 24),
                                    "border_border": "solid", "border_width": box(1)},
                             globals_={"border_color": color_ref(C["rule_dark"])})
        return _card(kids, shadow=False)

    head = [_head(props, on_dark)] if props.get("title") else []
    return _sec(head + [_grid([cell(i) for i in props.get("items", [])],
                              props.get("columns", 3), 22)], bg, anchor=props.get("anchor"))


@block("os.process")
def os_process(props):
    """Big blue condensed numerals over a black rule — four steps."""
    bg = props.get("bg", "grey")
    on_dark = _dark(bg)

    def step(s, i):
        num = widget("heading", {"title": "%02d" % (i + 1), "header_size": "div",
                                 "align": "left", **_condensed(64, "700", 0, False)},
                     globals_={"title_color": color_ref(HI if on_dark else BLUE)})
        rule = container([], {"content_width": "full", "min_height": slider(3),
                              "width": slider(48), "_flex_grow": 0,
                              "background_background": "classic"},
                         globals_={"background_color": color_ref(C["white"] if on_dark else INK)})
        return container([num, rule, _title(s["title"], "h3", on_dark),
                          _text(s["text"], "left", on_dark=on_dark, small=True)],
                         {"content_width": "full", "flex_direction": "column", "flex_gap": gap(12)})

    steps = props.get("steps", [])
    return _sec([_head(props, on_dark),
                 _grid([step(s, i) for i, s in enumerate(steps)], len(steps), 30, "flex-start")],
                bg, anchor=props.get("anchor"))


@block("os.films")
def os_films(props):
    """The manufacturer's film families, grouped by job. Names and short
    descriptions only — sourced from the manufacturer's own pages."""
    bg = props.get("bg", "white")

    def group(g):
        rows = [_label(g["group"])]
        for f in g["films"]:
            rows.append(container([
                widget("heading", {"title": f["name"], "header_size": "h3", "align": "left",
                                   **_condensed(22, "700", 0.6)},
                       globals_={"title_color": color_ref(INK)}),
                _text(f["text"], "left", small=True)],
                {"content_width": "full", "flex_direction": "column", "flex_gap": gap(4),
                 "padding": dims(14, 0, 14, 0), "border_border": "solid",
                 "border_width": dims(1, 0, 0, 0)},
                globals_={"border_color": color_ref(C["border"])}))
        return container(rows, {"content_width": "full", "flex_direction": "column",
                                "flex_gap": gap(8)})

    kids = [_head(props)]
    kids.append(_grid([group(g) for g in props.get("groups", [])],
                      props.get("columns", 3), 36, "flex-start"))
    if props.get("note"):
        kids.append(_text(props["note"], "left", small=True))
    return _sec(kids, bg, anchor=props.get("anchor"))


@block("os.honest")
def os_honest(props):
    """'What it does / what it does not' — two black-headed columns. Built
    for safety film, where a brochure line like 'burglar-proof glass' is
    exactly the unsupported guarantee the brief rules out."""
    bg = props.get("bg", "grey")

    def col(title, items, icon_cls, colour):
        rows = [widget("heading", {"title": _caps(title), "header_size": "h3",
                                   "align": "left", **_condensed(20, "700", 1.6)},
                       globals_={"title_color": color_ref(C["white"])})]
        head = container(rows, {"content_width": "full", "flex_direction": "column",
                                "padding": dims(14, 22, 12, 22),
                                "background_background": "classic"},
                         globals_={"background_color": color_ref(INK)})
        lst = widget("icon-list", {
            "icon_list": [repeater_item(text=t, selected_icon=icon(icon_cls), link=link(""))
                          for t in items],
            "space_between": slider(14), "icon_size": slider(15)},
            globals_={"icon_color": color_ref(colour), "text_color": color_ref("text"),
                      "icon_typography_typography": typo_ref("text")})
        c = _card([head, container([lst], {"content_width": "full",
                                           "flex_direction": "column",
                                           "padding": dims(22, 22, 24, 22)})],
                  dims(0, 0, 0, 0))
        c["settings"]["flex_gap"] = gap(0)
        return c

    w = _tracks([1, 1], 26)
    return _sec([_head(props), _row([
        _col([col(props.get("does_title", "What it does"), props.get("does", []),
                  "fas fa-check-circle", BLUE)], w[0]),
        _col([col(props.get("not_title", "What it does not do"), props.get("does_not", []),
                  "fas fa-times-circle", C["muted"])], w[1]),
    ], 26, align="stretch")] + ([_text(props["note"], "left", small=True)]
                                if props.get("note") else []),
        bg, anchor=props.get("anchor"))


@block("os.areas")
def os_areas(props):
    """Service area by REGION — each region a label box, one true line, and
    its towns. One page listing real regions beats a page per town (the
    doorway-page pattern Google discounts)."""
    bg = props.get("bg", "ink")
    on_dark = _dark(bg)

    def region(r):
        kids = [_label(r["name"], on_dark)]
        if r.get("text"):
            kids.append(_text(r["text"], "left", on_dark=on_dark, small=True))
        kids.append(_ticks(r["towns"], on_dark, r.get("cols", 2)))
        return container(kids, {"content_width": "full", "flex_direction": "column",
                                "flex_gap": gap(14)})

    kids = [_head(props, on_dark)]
    kids.append(_grid([region(r) for r in props.get("regions", [])],
                      props.get("columns", 3), 40, "flex-start"))
    if props.get("note"):
        kids.append(_text(props["note"], "left", on_dark=on_dark, small=True))
    return _sec(kids, bg, anchor=props.get("anchor"))


@block("os.faq")
def os_faq(props):
    bg = props.get("bg", "white")
    acc = _faq(props.get("items", []), True)
    acc["settings"]["faq_schema"] = "yes"
    acc["settings"]["__globals__"]["accordion_item_title_icon_color"] = color_ref(BLUE)
    w = _tracks([34, 62], 44)
    return _sec([_row([_col([_head(props, width=100)], w[0]), _col([acc], w[1])],
                      44, align="flex-start")], bg, anchor=props.get("anchor"))


@block("os.cta")
def os_cta(props):
    """Black band: label box, condensed headline, both actions, blue rule."""
    left = [_label(props.get("label", "Free Estimates"), True),
            _heading(props.get("title", ""), "h2", T["h_large"], "left", on_dark=True)]
    if props.get("text"):
        left.append(_text(props["text"], "left", on_dark=True))
    w = _tracks([60, 36], 40)
    right = _actions(props, True, "flex-end")
    return _sec([_row([_col(left, w[0], extra={"flex_gap": gap(16)}), _col([right], w[1])],
                      40, align="center")], "ink", pad=dims(80, 0, 80, 0),
                extra={"border_border": "solid", "border_width": dims(0, 0, 4, 0)})


# ═══════════════════════════════ estimate form ═══════════════════════════════

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
        if f.get("acceptance_text"):
            item["acceptance_text"] = f["acceptance_text"]
        if f.get("type") == "upload":
            item.update({"file_sizes": str(f.get("max_mb", 10)),
                         "file_types": f.get("file_types", "jpg,jpeg,png,heic,webp,pdf"),
                         "allow_multiple_upload": "yes",
                         "max_files": str(f.get("max_files", 6))})
        out.append(repeater_item(**item))
    return out


def _form(f):
    return widget("form", {
        "form_name": f.get("form_name", "Free Estimate Request"),
        "form_fields": _fields(f["fields"]),
        "submit_actions": ["email"],
        "email_to": f.get("email", ""),
        "email_subject": "New estimate request - OnSight Window Films website",
        "button_text": f.get("submit", "Request My Free Estimate"),
        "button_size": "md", "button_width": "100", "input_size": "md",
        "show_labels": "yes", "mark_required": "yes",
        "row_gap": slider(16), "column_gap": slider(14),
        "success_message": f.get("success", ""),
        "field_border_radius": R, "field_border_width": box(1),
        "button_border_radius": R,
        **{"button_" + k: v for k, v in _condensed(18, "700", 1.4).items()},
    }, globals_={"button_background_color": color_ref(BLUE),
                 "button_background_hover_color": color_ref(INK),
                 "button_text_color": color_ref(C["white"]),
                 "field_background_color": color_ref(C["white"]),
                 "field_text_color": color_ref(INK),
                 "field_border_color": color_ref(C["border"]),
                 "label_color": color_ref(INK),
                 "mark_required_color": color_ref(BLUE)})


@block("os.estimate")
def os_estimate(props):
    """The quote form in a card, beside what-happens-next and the contact
    details. Uploads go with the email so the estimate can start from photos."""
    bg = props.get("bg", "grey")
    f = props.get("form", {})
    card = _card([_label(f.get("title", "Free Estimate")),
                  _heading(f.get("heading", "Tell Us About Your Glass"), "h2",
                           T["h_medium"], "left"),
                  *([_text(f["intro"], "left", small=True)] if f.get("intro") else []),
                  _form(f)], dims(36, 34, 36, 34))
    card["settings"]["padding_mobile"] = dims(24, 18, 24, 18)
    aside = [_head(dict(props, intro=""), width=100)]
    for p in props.get("paragraphs", []):
        aside.append(_text(p, "left"))
    for i, st in enumerate(props.get("next", [])):
        aside.append(_row([
            widget("heading", {"title": "%02d" % (i + 1), "header_size": "div",
                               "align": "left", **_condensed(34, "700", 0, False)},
                   globals_={"title_color": color_ref(BLUE)}),
            container([_title(st["title"], "h3", token=T["h_small"]),
                       _text(st["text"], "left", small=True)],
                      {"content_width": "full", "flex_direction": "column", "flex_gap": gap(4)}),
        ], 16, align="flex-start", extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"}))
    if props.get("details"):
        aside.append(widget("icon-list", {
            "icon_list": [repeater_item(text=d["text"], selected_icon=icon(d.get("icon", ARROW)),
                                        link=link(d.get("href", ""))) for d in props["details"]],
            "space_between": slider(12), "icon_size": slider(16)},
            globals_={"icon_color": color_ref(BLUE), "text_color": color_ref(INK),
                      "icon_typography_typography": typo_ref("text")}))
    w = _tracks([40, 56], 44)
    cols = [_col(aside, w[0], extra={"flex_gap": gap(20)}), _col([card], w[1])]
    return _sec([_row(cols, 44, align="flex-start")], bg,
                anchor=props.get("anchor", "estimate"))


# ═══════════════════════════════ gallery / map ═══════════════════════════════

@block("os.gallery")
def os_gallery(props):
    """Real projects only. Until photos exist each slot is a visible,
    greppable PLACEHOLDER with its category — never a stock photo."""
    bg = props.get("bg", "white")

    def tile(it):
        kids = [_photo(it.get("image"), props.get("height", 300), lightbox=True),
                _label(it.get("category", "Project")),
                _title(it.get("title", ""), "h3", token=T["h_small"])]
        if it.get("text"):
            kids.append(_text(it["text"], "left", small=True))
        return container(kids, {"content_width": "full", "flex_direction": "column",
                                "flex_gap": gap(10)})

    kids = [_head(props)] if props.get("title") else []
    kids.append(_grid([tile(i) for i in props.get("items", [])], props.get("columns", 3), 26,
                      "flex-start"))
    if props.get("note"):
        kids.append(_text(props["note"], "left", small=True))
    return _sec(kids, bg, anchor=props.get("anchor"))


@block("os.map")
def os_map(props):
    bg = props.get("bg", "white")
    m = widget("google_maps", {"address": props.get("address", "Rochester, NY"),
                               "zoom": slider(props.get("zoom", 8)),
                               "height": slider(props.get("height", 440)),
                               "height_mobile": slider(320)})
    frame = container([m], {"content_width": "full", "flex_direction": "column",
                            "border_radius": R, "overflow": "hidden",
                            "border_border": "solid", "border_width": box(1)},
                      globals_={"border_color": color_ref(C["border"])})
    return _sec(([_head(props)] if props.get("title") else []) + [frame], bg,
                anchor=props.get("anchor"))


# ═══════════════════════════════ footer / sticky ═══════════════════════════════

@block("os.footer")
def os_footer(props):
    brand = [widget("theme-site-logo", {"align": "left", "width": slider(210)})]
    if props.get("blurb"):
        brand.append(_text(props["blurb"], "left", on_dark=True, small=True))
    brand.append(_row([_btn(props.get("cta_label", "Get a Free Estimate"),
                            props.get("cta_url", "/get-a-free-estimate/"))], 0))

    def links(items, icon_cls="fas fa-play"):
        return widget("icon-list", {
            "icon_list": [repeater_item(text=i["label"], selected_icon=icon(i.get("icon", icon_cls)),
                                        link=link(i.get("url", ""))) for i in items],
            "space_between": slider(10), "icon_size": slider(9)},
            globals_={"icon_color": color_ref(HI), "text_color": color_ref(C["white"]),
                      "icon_typography_typography": typo_ref(T["body_small"])})

    w = _tracks([34, 20, 20, 22], 30)
    cols = [_col(brand, w[0], extra={"flex_gap": gap(18)})]
    for i, g in enumerate(props.get("columns", [])[:3], start=1):
        cols.append(_col([_label(g["title"], True), links(g["links"])], w[i],
                         extra={"flex_gap": gap(16)}))
    rule = container([], {"content_width": "full", "min_height": slider(1),
                          "margin": dims(40, 0, 22, 0), "background_background": "classic"},
                     globals_={"background_color": color_ref(C["rule_dark"])})
    return _sec([_row(cols, 30, align="flex-start"), rule,
                 _text(props.get("legal", ""), "left", on_dark=True, small=True)],
                "ink", pad=dims(76, 0, 36, 0),
                extra={"border_border": "solid", "border_width": dims(4, 0, 0, 0)})


@block("os.stickybar")
def os_stickybar(props):
    call = _btn(props.get("call_label", "Call"), "tel:" + props.get("phone", ""),
                "outline", "fas fa-phone-alt")
    est = _btn(props.get("cta_label", "Free Estimate"),
               props.get("cta_url", "/get-a-free-estimate/"))
    return container([_row([call, est], 10, align="center", justify="center",
                           extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(10, 12, 10, 12), "background_background": "classic",
        "hide_desktop": "hidden-desktop", "hide_tablet": "hidden-tablet",
        "_position": "fixed", "_offset_orientation_v": "end",
        "_offset_y_end": slider(0), "_offset_x": slider(0),
        "width": slider(100, "%"), "_z_index": 998,
    }, globals_={"background_color": color_ref(INK)})
