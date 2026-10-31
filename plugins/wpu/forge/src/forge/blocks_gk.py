"""
blocks_gk.py — GK Exteriors LLC (`gk.*`), Northern Utah.

No reference site was supplied: "clean, modern and professional … using the GK
Exteriors black and gold branding … premium and trustworthy, not overly
crowded." So the LOGO specifies the design (design-spec.json, mode
"specified"), exactly as with Magic Renovations and OnSight.

What the mark and the yard sign give us:

    1. THE GOLD HAIRLINE FRAME. The sign is a black plate with a thin gold
       rounded rectangle inset from its edge. That frame is the signature: it
       insets the hero, the CTA band and the estimate card.
    2. GOLD IS LINE-WORK, NEVER A FIELD. The monogram is drawn in thin gold
       stroke on black. Gold is a 1px rule, an outlined icon, a numeral or a
       button — never a large filled area, which is what makes gold look
       cheap and is the trap in a black-and-gold brand.
    3. WIDE-TRACKED CAPS. "EXTERIORS" is set in wide-letterspaced caps under
       the mark; section labels repeat that exact treatment.
    4. LICENSED & INSURED, small and white, at the foot of the sign — a quiet
       trust line rather than a badge. `gk.trustbar` is that line.

"Not overly crowded" is a layout instruction, so sections are white or warm
off-white by default with generous padding, and black is spent on the header,
one or two feature bands, the CTA and the footer.

The client asked that no street address appear anywhere — the footer and
schema carry the SERVICE AREA instead. Nothing in this family emits an address.

Colour comes from the Global Kit via intake.json; no hex is named here.
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

GOLD = "primary"
INK = "secondary"          # near-black ground
GOLD_DK = "gkgd020"        # gold darkened for small text on white (AA)
BONE = "gkbn021"           # warm off-white alternate ground
GROUNDS = {"white": C["white"], "bone": BONE, "ink": INK}

PAD = dims(104, 0, 104, 0)
PAD_T = dims(78, 24, 78, 24)
PAD_M = dims(60, 20, 60, 20)
R = box(3)
GUTTER = 26
_ENTITY = re.compile(r"&([A-Z]+);")


def _caps(text):
    return _ENTITY.sub(lambda m: "&" + m.group(1).lower() + ";", text.upper())


def _dark(bg):
    return bg == "ink"


def _sec(children, bg="white", pad=None, extra=None, anchor=None):
    s = {"content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
         "flex_direction": "column", "flex_gap": gap(46),
         "padding": pad or PAD, "padding_tablet": PAD_T, "padding_mobile": PAD_M,
         "background_background": "classic"}
    if extra:
        s.update(extra)
    if anchor:
        s["_element_id"] = anchor
    return container(children, s,
                     globals_={"background_color": color_ref(GROUNDS.get(bg, C["white"]))})


def _tracked(size, weight="600", spacing=3.4, colour=None, upper=True):
    s = {"typography_typography": "custom",
         "typography_font_family": "Montserrat",
         "typography_font_weight": weight,
         "typography_font_size": slider(size),
         "typography_letter_spacing": slider(spacing)}
    if upper:
        s["typography_text_transform"] = "uppercase"
    return s


# ───────────────────────────── signature parts ─────────────────────────────

def _frame(children, pad=None, on_dark=True, extra=None):
    """The sign's gold hairline frame, inset from the edge of a black plate."""
    s = {"content_width": "full", "flex_direction": "column", "flex_gap": gap(24),
         "padding": pad or dims(46, 44, 46, 44),
         "padding_mobile": dims(30, 22, 30, 22),
         "border_border": "solid", "border_width": box(1), "border_radius": box(6)}
    if extra:
        s.update(extra)
    return container(children, s, globals_={
        "border_color": color_ref(GOLD if on_dark else GOLD_DK)})


def _label(text, on_dark=False, align="left"):
    """Wide-tracked caps label with a short gold rule — the wordmark treatment."""
    rule = container([], {"content_width": "full", "width": slider(34),
                          "min_height": slider(1), "_flex_grow": 0,
                          "background_background": "classic"},
                     globals_={"background_color": color_ref(GOLD if on_dark else GOLD_DK)})
    lab = widget("heading", {"title": _caps(text), "header_size": "div", "align": "left",
                             **_tracked(12, "600", 3.4)},
                 globals_={"title_color": color_ref(GOLD if on_dark else GOLD_DK)})
    return _row([rule, lab], 12, align="center",
                justify="center" if align == "center" else "flex-start",
                extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})


def _head(props, on_dark=False, align="left", width=76):
    kids = []
    if props.get("label"):
        kids.append(_label(props["label"], on_dark, align))
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


def _btn(label, href, style="gold", icon_cls="fas fa-arrow-right"):
    """gold: filled gold with black label — the Free Estimate button.
    ink: solid black. outline: gold hairline on black. ghost: black hairline."""
    b = _button(label, href, "ghost", icon_cls)
    s, g = b["settings"], b["settings"]["__globals__"]
    g.pop("typography_typography", None)
    fills = {
        "gold": (INK, GOLD, GOLD, INK, C["white"], C["white"]),
        "ink": (C["white"], INK, INK, INK, GOLD, GOLD),
        "outline": (C["white"], C["transparent"], GOLD, INK, GOLD, GOLD),
        "ghost": (INK, C["transparent"], INK, C["white"], INK, INK),
    }[style]
    g.update({"button_text_color": color_ref(fills[0]),
              "background_color": color_ref(fills[1]),
              "border_color": color_ref(fills[2]),
              "hover_color": color_ref(fills[3]),
              "button_background_hover_color": color_ref(fills[4]),
              "button_hover_border_color": color_ref(fills[5])})
    s.update({"border_radius": R, "border_width": box(1),
              "text_padding": dims(17, 32, 16, 32),
              "icon_align": "left" if "phone" in (icon_cls or "") else "right",
              "icon_indent": slider(10), **_tracked(13, "700", 1.8)})
    return b


def _actions(props, on_dark=False, justify="flex-start"):
    kids = []
    if props.get("cta_label"):
        kids.append(_btn(props["cta_label"], props.get("cta_url", "/free-estimate/")))
    if props.get("phone_display"):
        kids.append(_btn(props["phone_display"], "tel:" + props.get("phone", ""),
                         "outline" if on_dark else "ghost", "fas fa-phone-alt"))
    return _row(kids, 14, align="center", justify=justify,
                extra={"flex_direction_mobile": "column",
                       "flex_align_items_mobile": "stretch"})


def _photo(image, height=420, radius=R, lightbox=False):
    image = image or {}
    if not image.get("url"):
        return container([widget("heading", {
            "title": "PLACEHOLDER &mdash; " + image.get("slot", "project photo"),
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
    s = {"image": media(image["url"], image.get("alt", "")), "image_size": "large",
         "width": slider(100, "%"), "height": slider(height),
         "height_mobile": slider(round(height * 0.68)), "object-fit": "cover",
         "image_border_radius": radius, "align": "center"}
    if lightbox:
        s.update({"link_to": "file", "open_lightbox": "yes"})
    return widget("image", s)


def _gold_icon(icon_cls, size=26, on_dark=False):
    return widget("icon", {"selected_icon": icon(icon_cls), "size": slider(size),
                           "align": "left", "view": "default"},
                  globals_={"primary_color": color_ref(GOLD if on_dark else GOLD_DK)})


def _ticks(items, on_dark=False, cols=1):
    per = max(1, -(-len(items) // cols))
    chunks = [items[i:i + per] for i in range(0, len(items), per)]
    lists = [widget("icon-list", {
        "icon_list": [repeater_item(text=t, selected_icon=icon("fas fa-check"), link=link(""))
                      for t in ch],
        "space_between": slider(12), "icon_size": slider(13)},
        globals_={"icon_color": color_ref(GOLD if on_dark else GOLD_DK),
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


def _card(kids, pad=None, on_dark=False):
    return container(kids, {
        "content_width": "full", "flex_direction": "column", "flex_gap": gap(14),
        "padding": pad or dims(30, 28, 32, 28), "border_radius": R,
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
        **({} if on_dark else CARD_SHADOW_SOFT)},
        globals_={"background_color": color_ref(INK if on_dark else C["white"]),
                  "border_color": color_ref(GOLD if on_dark else C["border"])})


# ═══════════════════════════════ header ═══════════════════════════════

@block("gk.header")
def gk_header(props):
    """Black header, gold hairline under it: service area strip, then logo,
    nav, phone and the gold Free Estimate button. Sticky on every device."""
    def meta(text, icon_cls, href=""):
        return _row([
            widget("icon", {"selected_icon": icon(icon_cls), "size": slider(12),
                            "align": "center", "view": "default"},
                   globals_={"primary_color": color_ref(GOLD)}),
            widget("heading", {"title": text, "header_size": "div", "align": "left",
                               **({"link": link(href)} if href else {})},
                   globals_={"title_color": color_ref(C["on_dark"]),
                             "typography_typography": typo_ref(T["meta"])}),
        ], 8, align="center", extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})

    right = [meta(p["display"], "fas fa-phone-alt", "tel:" + p["tel"])
             for p in props.get("phones", [])]
    if props.get("email"):
        right.append(meta(props["email"], "fas fa-envelope", "mailto:" + props["email"]))
    w = _tracks([44, 52], 20)
    strip = container([_row([
        _col([meta(props.get("area_line", ""), "fas fa-map-marker-alt")], w[0],
             extra={"hide_mobile": "hidden-mobile"}),
        _col([_row(right, 24, align="center", justify="flex-end",
                   extra={"flex_direction_mobile": "row", "flex_wrap": "wrap"})], w[1]),
    ], 20, align="center")], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column", "padding": dims(9, 0, 9, 0),
        "padding_tablet": dims(9, 24, 9, 24), "padding_mobile": dims(8, 14, 8, 14),
        "background_background": "classic",
        "border_border": "solid", "border_width": dims(0, 0, 1, 0),
    }, globals_={"background_color": color_ref(INK),
                 "border_color": color_ref(C["rule_dark"])})

    logo = widget("theme-site-logo", {"align": "left",
                                      "width": slider(props.get("logo_width", 150)),
                                      "width_mobile": slider(108)})
    nav = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"), "layout": "horizontal",
        "align_items": "center", "pointer": "underline",
        "menu_space_between": slider(26), "toggle_align": "right",
    }, globals_={"color_menu_item": color_ref(C["white"]),
                 "color_menu_item_hover": color_ref(GOLD),
                 "color_menu_item_active": color_ref(GOLD),
                 "pointer_color_menu_item_hover": color_ref(GOLD),
                 "pointer_color_menu_item_active": color_ref(GOLD),
                 "dropdown_background_color": color_ref(INK),
                 "dropdown_color_menu_item": color_ref(C["white"]),
                 "toggle_color": color_ref(GOLD),
                 "menu_typography_typography": typo_ref(T["meta"])})
    w2 = _tracks([22, 52, 24], 20)
    main = container([_row([
        _col([logo], w2[0], extra={"width_mobile": slider(54, "%")}),
        _col([nav], w2[1], extra={"flex_align_items": "center",
                                  "width_mobile": slider(42, "%")}),
        _col([_btn(props.get("cta_label", "Free Estimate"),
                   props.get("cta_url", "/free-estimate/"))], w2[2],
             extra={"flex_align_items": "flex-end", "hide_mobile": "hidden-mobile"}),
    ], 20, align="center", extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column", "padding": dims(16, 0, 16, 0),
        "padding_tablet": dims(14, 24, 14, 24), "padding_mobile": dims(12, 14, 12, 14),
        "background_background": "classic",
        "border_border": "solid", "border_width": dims(0, 0, 2, 0),
    }, globals_={"background_color": color_ref(INK), "border_color": color_ref(GOLD)})
    return container([strip, main], {
        "content_width": "full", "flex_direction": "column", "flex_gap": gap(0),
        "sticky": "top", "sticky_on": ["desktop", "tablet", "mobile"], "_z_index": 99})


# ═══════════════════════════════ heroes ═══════════════════════════════

def _photo_bg(s, image, strength):
    if image and image.get("url"):
        s.update({"background_image": media(image["url"], image.get("alt", "")),
                  "background_position": "center center", "background_size": "cover",
                  "background_overlay_background": "classic",
                  "background_overlay_color": "rgba(10, 10, 10, %.2f)" % strength})
        return {}
    return {"background_color": color_ref(INK)}


@block("gk.hero")
def gk_hero(props):
    """Project photo under a black wash, with the gold frame inset over it."""
    kids = []
    if props.get("label"):
        kids.append(_label(props["label"], True))
    kids.append(_heading(props.get("title", ""), "h1", T["hero"], "left", on_dark=True))
    if props.get("intro"):
        kids.append(_text(props["intro"], "left", on_dark=True))
    kids.append(_actions(props, True))
    if props.get("ticks"):
        kids.append(_ticks(props["ticks"], True, min(len(props["ticks"]), 3)))
    inner = _frame(kids, dims(46, 44, 46, 44))
    inner["settings"]["width"] = slider(70, "%")
    inner["settings"]["width_tablet"] = slider(100, "%")
    inner["settings"]["width_mobile"] = slider(100, "%")
    s = {"content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
         "flex_direction": "column", "flex_justify_content": "center",
         "min_height": slider(720), "min_height_mobile": slider(0),
         "padding": dims(96, 0, 96, 0), "padding_tablet": dims(76, 24, 76, 24),
         "padding_mobile": dims(52, 16, 52, 16), "background_background": "classic"}
    return container([inner], s, globals_=_photo_bg(s, props.get("image"), .62))


@block("gk.pagehero")
def gk_pagehero(props):
    kids = []
    if props.get("label"):
        kids.append(_label(props["label"], True))
    kids.append(_heading(props.get("title", ""), "h1", T["h_large"], "left", on_dark=True))
    if props.get("intro"):
        kids.append(_text(props["intro"], "left", on_dark=True))
    if props.get("cta_label") or props.get("phone_display"):
        kids.append(_actions(props, True))
    body = container(kids, {"content_width": "full", "flex_direction": "column",
                            "flex_gap": gap(18), "width": slider(72, "%"),
                            "width_tablet": slider(100, "%"), "width_mobile": slider(100, "%")})
    s = {"content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
         "flex_direction": "column", "flex_justify_content": "center",
         "min_height": slider(460), "min_height_mobile": slider(0),
         "padding": dims(86, 0, 86, 0), "padding_tablet": dims(68, 24, 68, 24),
         "padding_mobile": dims(50, 18, 50, 18), "background_background": "classic"}
    return container([body], s, globals_=_photo_bg(s, props.get("image"), .68))


@block("gk.trustbar")
def gk_trustbar(props):
    """The sign's LICENSED & INSURED line, as a quiet strip under the hero."""
    cells = []
    for it in props.get("items", []):
        cells.append(_row([
            _gold_icon(it.get("icon", "fas fa-check"), 17, on_dark=_dark(props.get("bg", "ink"))),
            widget("heading", {"title": _caps(it["text"]), "header_size": "div",
                               "align": "left", **_tracked(12, "600", 2.4)},
                   globals_={"title_color": color_ref(
                       C["white"] if _dark(props.get("bg", "ink")) else INK)}),
        ], 10, align="center", extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"}))
    w = _tracks([1] * max(len(cells), 1), 20)
    return _sec([_row([_col([c], w[i]) for i, c in enumerate(cells)], 20, align="center")],
                props.get("bg", "ink"), pad=dims(22, 0, 22, 0))


# ═══════════════════════════════ content ═══════════════════════════════

@block("gk.split")
def gk_split(props):
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
    photo = [_photo(img, props.get("height", 480))]
    if img.get("caption"):
        photo.append(widget("heading", {"title": _caps(img["caption"]), "header_size": "div",
                                        "align": "left", **_tracked(11, "500", 2.0)},
                            globals_={"title_color": color_ref(C["muted"])}))
    w = _tracks([48, 48], 56)
    cols = [_col(body, w[0], extra={"flex_gap": gap(18)}),
            _col(photo, w[1], extra={"flex_gap": gap(10)})]
    if props.get("flip"):
        cols.reverse()
    return _sec([_row(cols, 56, align="center")], bg, anchor=props.get("anchor"))


@block("gk.services")
def gk_services(props):
    """Photo-topped service cards with a gold outline icon."""
    bg = props.get("bg", "bone")

    def card(it):
        kids = []
        if it.get("image") is not None:
            kids.append(_photo(it["image"], 236))
        body = [_gold_icon(it.get("icon", "fas fa-home"), 24)]
        t = _heading(it["title"], "h3", T["h_medium"], "left")
        if it.get("url"):
            t["settings"]["link"] = link(it["url"])
        body.append(t)
        body.append(_text(it.get("text", ""), "left", small=True))
        if it.get("url"):
            body.append(widget("heading", {
                "title": _caps(it.get("link_label", "See details")) + " &rarr;",
                "header_size": "div", "align": "left", "link": link(it["url"]),
                **_tracked(11, "700", 2.2)},
                globals_={"title_color": color_ref(GOLD_DK)}))
        kids.append(container(body, {"content_width": "full", "flex_direction": "column",
                                     "flex_gap": gap(12), "padding": dims(24, 24, 26, 24)}))
        c = _card(kids, dims(0, 0, 0, 0))
        c["settings"]["flex_gap"] = gap(0)
        return _hover_lift(c, 5)

    head = [_head(props, _dark(bg))] if props.get("title") else []
    return _sec(head + [_grid([card(i) for i in props.get("items", [])],
                              props.get("columns", 3), 24)], bg, anchor=props.get("anchor"))


@block("gk.servicedetail")
def gk_servicedetail(props):
    """One anchored alternating section per service — the Services page body."""
    out = []
    for i, it in enumerate(props.get("items", [])):
        body = [_label(it.get("label", "Service")),
                _heading(it["title"], "h2", T["h_large"], "left")]
        for p in it.get("paragraphs", []):
            body.append(_text(p, "left"))
        if it.get("bullets"):
            body.append(_ticks(it["bullets"], False, 2))
        if it.get("cta_label"):
            body.append(_row([_btn(it["cta_label"], it.get("cta_url", "/free-estimate/"))], 0))
        img = it.get("image") or {}
        photo = [_photo(img, 460)]
        if img.get("caption"):
            photo.append(widget("heading", {"title": _caps(img["caption"]), "header_size": "div",
                                            "align": "left", **_tracked(11, "500", 2.0)},
                                globals_={"title_color": color_ref(C["muted"])}))
        w = _tracks([50, 46], 56)
        cols = [_col(body, w[0], extra={"flex_gap": gap(18)}),
                _col(photo, w[1], extra={"flex_gap": gap(10)})]
        if i % 2:
            cols.reverse()
        out.append(_sec([_row(cols, 56, align="center")],
                        "white" if i % 2 == 0 else "bone", anchor=it.get("anchor")))
    return container(out, {"content_width": "full", "flex_direction": "column",
                           "flex_gap": gap(0)})


@block("gk.why")
def gk_why(props):
    """Gold outline icons on black — the reasons to trust a new contractor."""
    bg = props.get("bg", "ink")
    on_dark = _dark(bg)

    def cell(it):
        return container([_gold_icon(it.get("icon", "fas fa-check"), 26, on_dark),
                          _heading(it["title"], "h3", T["h_small"], "left", on_dark=on_dark),
                          _text(it.get("text", ""), "left", on_dark=on_dark, small=True)],
                         {"content_width": "full", "flex_direction": "column",
                          "flex_gap": gap(12), "padding": dims(28, 26, 28, 26),
                          "border_border": "solid", "border_width": box(1)},
                         globals_={"border_color": color_ref(
                             C["rule_dark"] if on_dark else C["border"])})

    return _sec([_head(props, on_dark),
                 _grid([cell(i) for i in props.get("items", [])], props.get("columns", 3), 24)],
                bg, anchor=props.get("anchor"))


@block("gk.process")
def gk_process(props):
    """Gold numerals over a hairline — four steps, generously spaced."""
    bg = props.get("bg", "white")
    on_dark = _dark(bg)

    def step(s, i):
        num = widget("heading", {"title": "%02d" % (i + 1), "header_size": "div",
                                 "align": "left", **_tracked(40, "300", 1.0, upper=False)},
                     globals_={"title_color": color_ref(GOLD if on_dark else GOLD_DK)})
        rule = container([], {"content_width": "full", "min_height": slider(1),
                              "margin": dims(14, 0, 16, 0),
                              "background_background": "classic"},
                         globals_={"background_color": color_ref(
                             C["rule_dark"] if on_dark else C["border"])})
        return container([num, rule,
                          _heading(s["title"], "h3", T["h_small"], "left", on_dark=on_dark),
                          _text(s["text"], "left", on_dark=on_dark, small=True)],
                         {"content_width": "full", "flex_direction": "column",
                          "flex_gap": gap(8)})

    steps = props.get("steps", [])
    return _sec([_head(props, on_dark),
                 _grid([step(s, i) for i, s in enumerate(steps)], len(steps), 32, "flex-start")],
                bg, anchor=props.get("anchor"))


@block("gk.gallery")
def gk_gallery(props):
    """Real GK project photos with honest captions, tap to enlarge."""
    bg = props.get("bg", "white")

    def tile(it):
        kids = [_photo(it.get("image"), props.get("height", 290), lightbox=True)]
        if it.get("caption"):
            kids.append(widget("heading", {"title": _caps(it["caption"]), "header_size": "div",
                                           "align": "left", **_tracked(11, "500", 2.0)},
                               globals_={"title_color": color_ref(C["muted"])}))
        return container(kids, {"content_width": "full", "flex_direction": "column",
                                "flex_gap": gap(10)})

    kids = [_head(props, _dark(bg))] if props.get("title") else []
    kids.append(_grid([tile(i) for i in props.get("items", [])],
                      props.get("columns", 3), 20, "flex-start"))
    if props.get("note"):
        kids.append(_text(props["note"], "left", small=True))
    return _sec(kids, bg, anchor=props.get("anchor"))


@block("gk.areas")
def gk_areas(props):
    """Service area as towns, on black. No street address anywhere — the
    client asked for the service area instead, and this is it."""
    bg = props.get("bg", "ink")
    on_dark = _dark(bg)
    towns = props.get("towns", [])
    body = [_ticks(towns, on_dark, props.get("columns", 3))]
    if props.get("note"):
        body.append(_text(props["note"], "left", on_dark=on_dark, small=True))
    w = _tracks([40, 54], 48)
    return _sec([_row([_col([_head(props, on_dark, width=100)], w[0]),
                       _col(body, w[1], extra={"flex_gap": gap(16)})], 48, align="flex-start")],
                bg, anchor=props.get("anchor"))


@block("gk.faq")
def gk_faq(props):
    bg = props.get("bg", "white")
    acc = _faq(props.get("items", []), True)
    acc["settings"]["faq_schema"] = "yes"
    acc["settings"]["__globals__"]["accordion_item_title_icon_color"] = color_ref(GOLD_DK)
    w = _tracks([36, 60], 44)
    return _sec([_row([_col([_head(props, width=100)], w[0]), _col([acc], w[1])],
                      44, align="flex-start")], bg, anchor=props.get("anchor"))


@block("gk.cta")
def gk_cta(props):
    """Black band, gold frame, one clear ask."""
    kids = [_label(props.get("label", "Free Estimates"), True),
            _heading(props.get("title", ""), "h2", T["h_large"], "left", on_dark=True)]
    if props.get("text"):
        kids.append(_text(props["text"], "left", on_dark=True))
    w = _tracks([58, 38], 40)
    row = _row([_col(kids, w[0], extra={"flex_gap": gap(16)}),
                _col([_actions(props, True, "flex-end")], w[1])], 40, align="center")
    return _sec([_frame([row], dims(52, 48, 52, 48))], "ink", pad=dims(80, 0, 80, 0))


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
        if f.get("type") == "upload":
            item.update({"file_sizes": str(f.get("max_mb", 10)),
                         "file_types": f.get("file_types", "jpg,jpeg,png,heic,webp,pdf"),
                         "allow_multiple_upload": "yes",
                         "max_files": str(f.get("max_files", 6))})
        out.append(repeater_item(**item))
    return out


@block("gk.estimate")
def gk_estimate(props):
    """Free-estimate form in a card beside the contact details. Every request
    goes to the business email — the client's one delivery requirement."""
    bg = props.get("bg", "bone")
    f = props.get("form", {})
    form = widget("form", {
        "form_name": f.get("form_name", "Free Estimate Request"),
        "form_fields": _fields(f["fields"]),
        "submit_actions": ["email"],
        "email_to": f.get("email", ""),
        "email_subject": "New free estimate request - GK Exteriors website",
        "button_text": f.get("submit", "Request My Free Estimate"),
        "button_size": "md", "button_width": "100", "input_size": "md",
        "show_labels": "yes", "mark_required": "yes",
        "row_gap": slider(16), "column_gap": slider(14),
        "success_message": f.get("success", ""),
        "field_border_radius": R, "field_border_width": box(1),
        "button_border_radius": R,
        **{"button_" + k: v for k, v in _tracked(13, "700", 1.8).items()},
    }, globals_={"button_background_color": color_ref(GOLD),
                 "button_background_hover_color": color_ref(INK),
                 "button_text_color": color_ref(INK),
                 "field_background_color": color_ref(C["white"]),
                 "field_text_color": color_ref(INK),
                 "field_border_color": color_ref(C["border"]),
                 "label_color": color_ref(INK),
                 "mark_required_color": color_ref(GOLD_DK)})
    card = _card([_label(f.get("label", "Free Estimate")),
                  _heading(f.get("heading", "Request Your Free Estimate"), "h2",
                           T["h_medium"], "left"),
                  *([_text(f["intro"], "left", small=True)] if f.get("intro") else []),
                  form], dims(36, 34, 38, 34))
    aside = [_head(dict(props, intro=""), width=100)]
    for p in props.get("paragraphs", []):
        aside.append(_text(p, "left"))
    if props.get("details"):
        aside.append(widget("icon-list", {
            "icon_list": [repeater_item(text=d["text"],
                                        selected_icon=icon(d.get("icon", "fas fa-check")),
                                        link=link(d.get("href", ""))) for d in props["details"]],
            "space_between": slider(14), "icon_size": slider(17)},
            globals_={"icon_color": color_ref(GOLD_DK), "text_color": color_ref(INK),
                      "icon_typography_typography": typo_ref("text")}))
    if props.get("ticks"):
        aside.append(_ticks(props["ticks"]))
    if props.get("phone_display"):
        aside.append(_actions({"phone_display": props["phone_display"],
                               "phone": props.get("phone", "")}))
    w = _tracks([42, 54], 48)
    return _sec([_row([_col(aside, w[0], extra={"flex_gap": gap(20)}), _col([card], w[1])],
                      48, align="flex-start")], bg, anchor=props.get("anchor", "estimate"))


# ═══════════════════════════════ footer ═══════════════════════════════

@block("gk.footer")
def gk_footer(props):
    brand = [widget("theme-site-logo", {"align": "left", "width": slider(160)})]
    if props.get("blurb"):
        brand.append(_text(props["blurb"], "left", on_dark=True, small=True))
    if props.get("licence"):
        brand.append(widget("heading", {"title": _caps(props["licence"]), "header_size": "div",
                                        "align": "left", **_tracked(11, "600", 2.2)},
                            globals_={"title_color": color_ref(GOLD)}))

    def links(items):
        return widget("icon-list", {
            "icon_list": [repeater_item(text=i["label"],
                                        selected_icon=icon(i.get("icon", "fas fa-angle-right")),
                                        link=link(i.get("url", ""))) for i in items],
            "space_between": slider(10), "icon_size": slider(12)},
            globals_={"icon_color": color_ref(GOLD), "text_color": color_ref(C["on_dark"]),
                      "icon_typography_typography": typo_ref(T["body_small"])})

    w = _tracks([34, 22, 22, 18], 30)
    cols = [_col(brand, w[0], extra={"flex_gap": gap(18)})]
    for i, g in enumerate(props.get("columns", [])[:3], start=1):
        cols.append(_col([_label(g["title"], True), links(g["links"])], w[i],
                         extra={"flex_gap": gap(16)}))
    rule = container([], {"content_width": "full", "min_height": slider(1),
                          "margin": dims(42, 0, 24, 0), "background_background": "classic"},
                     globals_={"background_color": color_ref(C["rule_dark"])})
    return _sec([_row(cols, 30, align="flex-start"), rule,
                 _text(props.get("legal", ""), "left", on_dark=True, small=True)],
                "ink", pad=dims(78, 0, 38, 0),
                extra={"border_border": "solid", "border_width": dims(2, 0, 0, 0)})


@block("gk.stickybar")
def gk_stickybar(props):
    call = _btn(props.get("call_label", "Call Now"), "tel:" + props.get("phone", ""),
                "outline", "fas fa-phone-alt")
    est = _btn(props.get("cta_label", "Free Estimate"),
               props.get("cta_url", "/free-estimate/"))
    return container([_row([call, est], 10, align="center", justify="center",
                           extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(10, 12, 10, 12), "background_background": "classic",
        "hide_desktop": "hidden-desktop", "hide_tablet": "hidden-tablet",
        "_position": "fixed", "_offset_orientation_v": "end",
        "_offset_y_end": slider(0), "_offset_x": slider(0),
        "width": slider(100, "%"), "_z_index": 998,
        "border_border": "solid", "border_width": dims(2, 0, 0, 0),
    }, globals_={"background_color": color_ref(INK), "border_color": color_ref(GOLD)})
