"""
blocks_mow.py - Mow N More (Topeka, KS).

No reference site; the design is specified by the logo made for the client
in Canva (2026-10-28), and four devices come straight off it:

  * MOWING STRIPES. The mark's lawn is drawn as curved stripes. On the page
    they become a striped band (two greens in a repeating diagonal) that
    carries the quick facts under the hero and the closing call to action.
  * THE GOLD RULE WITH A CLIPPED END. Under the wordmark sits a gold bar
    whose right end is cut on the diagonal. Every section title gets that
    bar (`_rule`), clip-path and all.
  * GOLD DOTS between words, from "LAWN · LANDSCAPE · TREE SERVICE" - used in
    eyebrows and the service tag lines.
  * HEAVY CONDENSED CAPS (the wordmark) for display type: Barlow Condensed
    800, uppercase, with Barlow for text.

Contrast, measured: gold #CF9700 on white is 2.60:1, so gold is NEVER a text
colour on white and gold buttons carry a near-black label (6.92:1). Gold text
appears only on the green (4.66:1).

Photos are the client's own (Facebook posts and the business's Yelp photos);
galleries open in a lightbox grouped by set and need no Media Library ids.

    mm.topbar  mm.header  mm.footer  mm.mobilebar
    mm.hero  mm.pagehero  mm.stripes  mm.split  mm.services  mm.servicerows
    mm.gallery  mm.reviews  mm.steps  mm.area  mm.cta  mm.faq  mm.form
    mm.contactcards  mm.map
"""
from __future__ import annotations

import re

from .core import (
    container, widget, repeater_item, slider, dims, box, media, link,
    gap, color_ref, typo_ref, icon, css,
)
from .tokens import C, T
from .blocks import (
    block, _row, _col, _tracks, _button, _text, _faq, _hover_lift,
    KIT_CONTAINER, CARD_SHADOW_SOFT,
)

GREEN = "primary"        # #083F18 - logo green
DEEP = "secondary"       # #052A10 - darker green for the footer and stripes
GOLD = "accent"          # #CF9700 - logo gold: rules, dots, button fills
INK = "mmink01"          # #14180F - labels on gold
PALE = C["surface"]      # #F4F6EF
LINE = C["border"]       # #DDE3D6
MUTED = C["muted"]       # #5B6455
MIST = "mmmist1"         # #CFE0D2 - secondary text on green

PAD = dims(92, 0, 92, 0)
PAD_T = dims(68, 24, 68, 24)
PAD_M = dims(54, 18, 54, 18)
R = box(6)
GUT = 24


# ─────────────────────────────── helpers ───────────────────────────────────

def _sec(kids, bg="white", pad=None, anchor=None, extra=None):
    grounds = {"white": C["white"], "pale": PALE, "green": GREEN, "deep": DEEP}
    s = {"content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
         "flex_direction": "column", "flex_gap": gap(32),
         "padding": pad or PAD, "padding_tablet": PAD_T, "padding_mobile": PAD_M,
         "background_background": "classic"}
    if anchor:
        s["_element_id"] = anchor
    if extra:
        s.update(extra)
    return container(kids, s, globals_={"background_color": color_ref(grounds.get(bg, C["white"]))})


def _dark(bg):
    return bg in ("green", "deep")


def _dots(text):
    """'A · B · C' -> the middots in gold, as in the logo's tagline."""
    return text.replace(" · ", ' <span style="color:var(--e-global-color-accent)">&bull;</span> ')


def _h(text, size="h2", token=None, align="left", on_dark=False):
    t = re.sub(r"\[\[(.+?)\]\]",
               r'<span style="color:var(--e-global-color-accent)">\1</span>' if on_dark
               else r'<span style="color:var(--e-global-color-primary)">\1</span>', text)
    return widget("heading", {"title": t, "header_size": size, "align": align},
                  globals_={"title_color": color_ref(C["white"] if on_dark else INK),
                            "typography_typography": typo_ref(token or T["h_large"])})


def _p(html, align="left", on_dark=False, small=False):
    t = _text(html, align, small=small)
    t["settings"]["__globals__"]["text_color"] = color_ref(MIST if on_dark else "text")
    return t


def _eyebrow(text, on_dark=False, align="left"):
    return widget("heading", {"title": _dots(text), "header_size": "div", "align": align},
                  globals_={"title_color": color_ref(GOLD if on_dark else GREEN),
                            "typography_typography": typo_ref(T["eyebrow"])})


def _rule(align="left", width=96):
    """The logo's gold bar, right end clipped on the diagonal."""
    return container([], {
        "content_width": "full", "width": slider(width), "min_height": slider(6),
        "_flex_shrink": "0", "background_background": "classic",
        "margin": dims(0, "auto", 0, "auto") if align == "center" else dims(0, 0, 0, 0),
        "custom_css": css("selector { clip-path: polygon(0 0, 100% 0, calc(100% - 6px) 100%, 0 100%); }"),
    }, globals_={"background_color": color_ref(GOLD)})


def _head(props, on_dark=False, align="left"):
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], on_dark, align))
    if props.get("title"):
        kids.append(_h(props["title"], props.get("tag", "h2"), T["h_large"], align, on_dark))
        kids.append(_rule(align))
    if props.get("intro"):
        kids.append(container([_p(props["intro"], align, on_dark)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(props.get("intro_width", 66), "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto") if align == "center" else dims(0, 0, 0, 0)}))
    if not kids:
        return []
    return [container(kids, {"content_width": "full", "flex_direction": "column", "flex_gap": gap(12),
                              "flex_align_items": "center" if align == "center" else "flex-start"})]


def _btn(label, href, style="gold", icon_name="", tel=False):
    """gold: gold fill, near-black label (6.92:1). green: green fill, white.
    ghost: white hairline, for photographs and green grounds."""
    b = _button(label, href, "primary", icon_name)
    b["settings"].update({"border_radius": box(4), "text_padding": dims(15, 26, 15, 26),
                          "border_border": "solid", "border_width": box(2)})
    g = b["settings"].setdefault("__globals__", {})
    fill, ink, hov, hov_ink, edge = {
        "gold": (GOLD, INK, GREEN, C["white"], GOLD),
        "green": (GREEN, C["white"], GOLD, INK, GREEN),
        "ghost": (C["transparent"], C["white"], C["white"], GREEN, C["white"]),
        "outline": (C["transparent"], GREEN, GREEN, C["white"], GREEN),
    }[style]
    g.update({"background_color": color_ref(fill), "border_color": color_ref(edge),
              "button_text_color": color_ref(ink), "button_background_hover_color": color_ref(hov),
              "button_hover_border_color": color_ref(hov), "hover_color": color_ref(hov_ink),
              "typography_typography": typo_ref(T["meta"])})
    return b


def _btns(btns, justify="flex-start"):
    return _row(btns, 12, align="center", justify=justify, extra={
        "flex_wrap": "wrap", "flex_direction_mobile": "column",
        "flex_align_items_mobile": "stretch", "padding": dims(6, 0, 0, 0)})


def _ticks(items, on_dark=False, columns=1, px=KIT_CONTAINER):
    rows = []
    for t in items:
        mark = widget("icon", {"selected_icon": icon("fas fa-check"), "size": slider(13),
                               "align": "center", "view": "default"},
                      globals_={"primary_color": color_ref(GOLD if on_dark else GREEN)})
        rows.append(_row([mark, _p(t, on_dark=on_dark, small=True)], 12, align="flex-start",
                         extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row",
                                "padding": dims(4, 0, 4, 0)}))
    if columns == 1:
        return container(rows, {"content_width": "full", "flex_direction": "column", "flex_gap": gap(0)})
    per = -(-len(rows) // columns)
    w = _tracks([1] * columns, 22, container=px * 0.9)[0]
    return _row([_col(rows[i:i + per], w, extra={"flex_gap": gap(0)}) for i in range(0, len(rows), per)],
                22, align="flex-start", extra={"flex_wrap": "wrap"})


def _card(kids, width=None, pad=None, bg=C["white"], lift=True, extra=None):
    s = {"content_width": "full", "flex_direction": "column", "flex_gap": gap(12),
         "padding": pad if pad is not None else dims(24, 22, 26, 22),
         "padding_mobile": dims(20, 18, 22, 18), "border_radius": R,
         "border_border": "solid", "border_width": box(1),
         "background_background": "classic", **CARD_SHADOW_SOFT}
    if width:
        s.update({"width": slider(width, "%"), "width_mobile": slider(100, "%")})
    if extra:
        s.update(extra)
    el = container(kids, s, globals_={"background_color": color_ref(bg), "border_color": color_ref(LINE)})
    return _hover_lift(el, 4) if lift else el


def _img(image, height=260, radius=None, group=None, zoom=False):
    radius = radius if radius is not None else R
    s = {"image": media(image["url"], image.get("alt", "")), "image_size": "full",
         "width": slider(100, "%"), "height": slider(height), "object-fit": "cover",
         "align": "center", "image_border_radius": radius}
    if group:
        l = link(image["url"])
        l["custom_attributes"] = "data-elementor-open-lightbox|yes,data-elementor-lightbox-slideshow|" + group
        s.update({"link_to": "custom", "link": l, "open_lightbox": "yes"})
    w = widget("image", s)
    rules = []
    if zoom:
        rules += ["selector { overflow: hidden; border-radius: inherit; }",
                  "selector img { transition: transform .9s ease; }",
                  "selector:hover img { transform: scale(1.05); }"]
    if group:
        rules.append("selector a { cursor: zoom-in; }")
    if rules:
        w["settings"]["custom_css"] = css(*rules)
    return w


def _stripes(sec):
    """The mowing-stripe ground: two greens in wide diagonal bands, as the
    lawn in the mark. Colours come from the kit's global variables."""
    prev = sec["settings"].get("custom_css", "")
    sec["settings"]["custom_css"] = (prev + "\n" if prev else "") + css(
        "selector { background-image: repeating-linear-gradient(115deg, "
        "var(--e-global-color-primary) 0 90px, var(--e-global-color-secondary) 90px 180px) !important; }")
    return sec


def _tel(phone_tel):
    return "tel:" + phone_tel


# ─────────────────────────────── chrome ────────────────────────────────────

@block("mm.topbar")
def mm_topbar(props):
    left = widget("heading", {"title": _dots(props["text"]), "header_size": "div", "align": "left"},
                  globals_={"title_color": color_ref(C["white"]), "typography_typography": typo_ref(T["meta"])})
    phone = widget("heading", {"title": "Call " + props["phone"], "header_size": "div", "align": "right",
                               "link": link(_tel(props["phone_tel"]))},
                   globals_={"title_color": color_ref(GOLD), "typography_typography": typo_ref(T["meta"])})
    row = _row([left, phone], 20, align="center", justify="space-between",
               extra={"flex_wrap": "nowrap", "flex_wrap_tablet": "wrap"})
    return container([row], {"content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
                             "flex_direction": "column", "padding": dims(8, 0, 8, 0),
                             "padding_tablet": dims(8, 20, 8, 20), "background_background": "classic",
                             "hide_mobile": "hidden-mobile"},
                     globals_={"background_color": color_ref(DEEP)})


@block("mm.header")
def mm_header(props):
    logo = widget("theme-site-logo", {"align": "left", "width": slider(props.get("logo_width", 230)),
                                      "width_mobile": slider(170), "image_size": "full",
                                      "image": media(props["logo"], "Mow N More")})
    nav = widget("nav-menu", {"menu": props.get("menu", "main-menu"), "layout": "horizontal",
                              "align_items": "flex-end", "pointer": "underline", "animation_line": "fade",
                              "menu_space_between": slider(6), "padding_horizontal_menu_item": slider(12),
                              "toggle_align": "right", "full_width": "stretch"},
                 globals_={"menu_typography_typography": typo_ref(T["meta"]),
                           "color_menu_item": color_ref(INK), "color_menu_item_hover": color_ref(GREEN),
                           "color_menu_item_active": color_ref(GREEN),
                           "pointer_color_menu_item_hover": color_ref(GOLD),
                           "pointer_color_menu_item_active": color_ref(GOLD),
                           "color_dropdown_item": color_ref(INK),
                           "background_color_dropdown_item": color_ref(C["white"]),
                           "color_dropdown_item_hover": color_ref(C["white"]),
                           "background_color_dropdown_item_hover": color_ref(GREEN),
                           "toggle_color": color_ref(GREEN)})
    cta = _btn(props.get("cta_label", "Book an Appointment"), props["cta_url"], "gold")
    cta["settings"]["text_padding"] = dims(12, 20, 12, 20)
    right = _row([cta], 12, align="center", justify="flex-end",
                 extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row",
                        "hide_mobile": "hidden-mobile", "hide_tablet": "hidden-tablet"})
    row = _row([_col([logo], 26, extra={"width_tablet": slider(50, "%"), "width_mobile": slider(62, "%")}),
                _col([nav], 52, extra={"flex_align_items": "flex-end", "width_tablet": slider(50, "%"),
                                       "width_mobile": slider(38, "%")}),
                _col([right], 22, extra={"flex_align_items": "flex-end"})],
               16, align="center", extra={"flex_wrap": "nowrap", "flex_wrap_tablet": "nowrap",
                                          "flex_direction_mobile": "row", "flex_wrap_mobile": "nowrap"})
    return container([row], {"content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
                             "flex_direction": "column", "padding": dims(12, 0, 12, 0),
                             "padding_tablet": dims(10, 20, 10, 20), "padding_mobile": dims(8, 16, 8, 16),
                             "background_background": "classic", "border_border": "solid",
                             "border_width": dims(0, 0, 3, 0), "sticky": "top",
                             "sticky_on": ["desktop", "tablet", "mobile"], "sticky_offset": 0,
                             **CARD_SHADOW_SOFT},
                     globals_={"background_color": color_ref(C["white"]), "border_color": color_ref(GOLD)})


@block("mm.footer")
def mm_footer(props):
    brand = [widget("image", {"image": media(props["logo"], "Mow N More"), "image_size": "full",
                              "width": slider(240), "align": "left"}),
             _p(props["blurb"], on_dark=True, small=True)]
    if props.get("facebook"):
        brand.append(widget("icon", {"selected_icon": icon("fab fa-facebook-f"), "size": slider(16),
                                     "align": "left", "view": "stacked", "shape": "circle",
                                     "icon_padding": slider(10), "link": link(props["facebook"], external=True)},
                            globals_={"primary_color": color_ref(GOLD), "secondary_color": color_ref(INK)}))
    cols = props["columns"]
    widths = _tracks([1.3] + [1] * len(cols), GUT)
    body = [_col(brand, widths[0], extra={"flex_gap": gap(14), "width_tablet": slider(100, "%")})]
    for i, c in enumerate(cols):
        kids = [_h(c["title"], "h3", T["h_small"], on_dark=True)]
        for l in c["links"]:
            kids.append(widget("heading", {"title": l["label"], "header_size": "div", "align": "left",
                                           **({"link": link(l["url"])} if l.get("url") else {})},
                               globals_={"title_color": color_ref(MIST),
                                         "typography_typography": typo_ref(T["body_small"])}))
        body.append(_col(kids, widths[i + 1], extra={"flex_gap": gap(6), "width_tablet": slider(47, "%")}))
    bar = widget("heading", {"title": props["legal"], "header_size": "div", "align": "left"},
                 globals_={"title_color": color_ref(MIST), "typography_typography": typo_ref(T["meta"])})
    barbox = container([bar], {"content_width": "full", "flex_direction": "column",
                               "padding": dims(20, 0, 0, 0), "border_border": "solid",
                               "border_width": dims(1, 0, 0, 0)},
                       globals_={"border_color": color_ref(GREEN)})
    return container([_row(body, GUT, align="flex-start", extra={"flex_wrap": "nowrap", "flex_wrap_tablet": "wrap"}),
                      barbox],
                     {"content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
                      "flex_direction": "column", "flex_gap": gap(36),
                      "padding": dims(70, 0, 30, 0), "padding_tablet": dims(56, 24, 90, 24),
                      "padding_mobile": dims(48, 18, 96, 18), "background_background": "classic"},
                     globals_={"background_color": color_ref(DEEP)})


@block("mm.mobilebar")
def mm_mobilebar(props):
    call = _btn("Call", _tel(props["phone_tel"]), "green", "fas fa-phone")
    book = _btn("Book", props["book_url"], "gold", "fas fa-calendar-check")
    for b in (call, book):
        b["settings"].update({"text_padding": dims(14, 10, 14, 10), "align": "justify", "border_radius": box(0)})
    return container([_col([call], 50, extra={"width_mobile": slider(50, "%")}),
                      _col([book], 50, extra={"width_mobile": slider(50, "%")})],
                     {"content_width": "full", "flex_direction": "row", "flex_direction_mobile": "row",
                      "flex_wrap": "nowrap", "flex_gap": gap(0), "padding": dims(0, 0, 0, 0),
                      "width": slider(100, "%"), "_position": "fixed", "_offset_orientation_h": "start",
                      "_offset_orientation_v": "end", "_offset_x": slider(0), "_offset_y": slider(0),
                      "_z_index": 9990, "hide_desktop": "hidden-desktop", "hide_tablet": "hidden-tablet",
                      "background_background": "classic"},
                     globals_={"background_color": color_ref(DEEP)})


# ─────────────────────────────── heroes ────────────────────────────────────

def _hero_copy(props):
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], True))
    kids.append(_h(props["title"], "h1", T["hero"], on_dark=True))
    kids.append(_rule())
    if props.get("intro"):
        kids.append(_p(props["intro"], on_dark=True))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props["cta_url"], "gold"))
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props["alt_url"], "ghost"))
    if btns:
        kids.append(_btns(btns))
    return kids


def _photo_ground(sec, image, overlay=0.72, position="center center"):
    sec["settings"].update({"background_image": media(image["url"], image.get("alt", "")),
                            "background_position": position, "background_size": "cover",
                            "background_repeat": "no-repeat", "background_overlay_background": "classic",
                            "background_overlay_opacity": slider(overlay)})
    sec["settings"]["__globals__"]["background_overlay_color"] = color_ref(DEEP)
    return sec


@block("mm.hero")
def mm_hero(props):
    col = _col(_hero_copy(props), props.get("width", 60), extra={"flex_gap": gap(16)})
    sec = _sec([_row([col], GUT)], "deep", pad=dims(120, 0, 120, 0),
               extra={"min_height": slider(props.get("height", 640)), "flex_justify_content": "center",
                      "padding_tablet": dims(90, 24, 90, 24), "padding_mobile": dims(70, 18, 70, 18)})
    return _photo_ground(sec, props["image"], props.get("overlay", 0.7), props.get("position", "center center"))


@block("mm.pagehero")
def mm_pagehero(props):
    col = _col(_hero_copy(props), props.get("width", 64), extra={"flex_gap": gap(14)})
    sec = _sec([_row([col], GUT)], "deep", pad=dims(96, 0, 90, 0),
               extra={"min_height": slider(props.get("height", 400)), "flex_justify_content": "center",
                      "padding_tablet": dims(76, 24, 70, 24), "padding_mobile": dims(60, 18, 56, 18)})
    return _photo_ground(sec, props["image"], props.get("overlay", 0.74), props.get("position", "center center"))


# ─────────────────────────────── sections ──────────────────────────────────

@block("mm.stripes")
def mm_stripes(props):
    """The mowing-stripe band carrying quick facts."""
    items = props["items"]
    w = _tracks([1] * len(items), GUT)[0]
    cells = []
    for it in items:
        cells.append(_col([
            widget("icon", {"selected_icon": icon(it["icon"]), "size": slider(24), "align": "center",
                            "view": "default"}, globals_={"primary_color": color_ref(GOLD)}),
            _h(it["title"], "h3", T["h_small"], "center", True),
            _p(it["text"], "center", True, True)], w,
            extra={"flex_gap": gap(6), "flex_align_items": "center", "width_tablet": slider(48, "%")}))
    sec = _sec([_row(cells, GUT, align="flex-start", extra={"flex_wrap": "nowrap", "flex_wrap_tablet": "wrap"})],
               "green", pad=dims(38, 0, 38, 0), extra={"padding_tablet": dims(32, 24, 32, 24)})
    return _stripes(sec)


@block("mm.split")
def mm_split(props):
    bg = props.get("bg", "white")
    dk = _dark(bg)
    copy = _head({k: props.get(k) for k in ("eyebrow", "title")}, dk)
    for p in props.get("paragraphs", []):
        copy.append(_p(p, on_dark=dk))
    if props.get("ticks"):
        copy.append(_ticks(props["ticks"], dk, props.get("tick_columns", 1), KIT_CONTAINER * 0.5))
    if props.get("cta_label"):
        copy.append(_btns([_btn(props["cta_label"], props["cta_url"], "gold" if dk else "green")]))
    photo = _img(props["image"], props.get("image_height", 460), group=props.get("group"))
    w = _tracks([1, 1.05], 52)
    pair = [_col([photo], w[0]), _col(copy, w[1], extra={"flex_gap": gap(14)})]
    if props.get("flip"):
        pair.reverse()
    return _sec([_row(pair, 52, align="center")], bg, anchor=props.get("anchor"))


@block("mm.services")
def mm_services(props):
    """Photo cards: the client's own job photo on top, a green title bar
    with the gold rule, the line, and a link."""
    kids = _head(props, False, props.get("align", "left"))
    cols = props.get("columns", 3)
    w = _tracks([1] * cols, GUT)[0]
    cards = []
    for it in props["items"]:
        body = [_h(it["title"], "h3", T["h_medium"]), _rule(width=48)]
        if it.get("text"):
            body.append(_p(it["text"], small=True))
        if it.get("href"):
            body.append(widget("heading", {"title": it.get("link_label", "Learn more") + " &rarr;",
                                           "header_size": "div", "align": "left", "link": link(it["href"])},
                               globals_={"title_color": color_ref(GREEN), "typography_typography": typo_ref(T["meta"])}))
        inner = container(body, {"content_width": "full", "flex_direction": "column", "flex_gap": gap(10),
                                 "padding": dims(20, 20, 22, 20), "_flex_grow": 1})
        cards.append(_card([_img(it["image"], props.get("thumb_height", 220), radius=dims(6, 6, 0, 0), zoom=True), inner],
                           w, pad=dims(0, 0, 0, 0),
                           extra={"flex_gap": gap(0), "overflow": "hidden",
                                  "width_tablet": slider(_tracks([1, 1], GUT, 720)[0], "%")}))
    kids.append(_row(cards, GUT, align="stretch", extra={"flex_wrap": "wrap"}))
    if props.get("footer_cta"):
        f = props["footer_cta"]
        kids.append(_btns([_btn(f["label"], f["url"], "outline")]))
    return _sec(kids, props.get("bg", "pale"), anchor=props.get("anchor"))


@block("mm.servicerows")
def mm_servicerows(props):
    """Services page: one anchored, alternating row per service, each with a
    small lightbox strip of the client's photos for that kind of work."""
    rows = []
    for n, it in enumerate(props["items"]):
        bg = "white" if n % 2 == 0 else "pale"
        copy = [_eyebrow(it.get("tag", ""))] if it.get("tag") else []
        copy += [_h(it["title"], "h2", T["h_large"]), _rule()]
        for p in it["paragraphs"]:
            copy.append(_p(p))
        if it.get("ticks"):
            copy.append(_ticks(it["ticks"], columns=2 if len(it["ticks"]) > 4 else 1, px=KIT_CONTAINER * 0.52))
        copy.append(_btns([_btn(props.get("cta_label", "Book this service"), props["cta_url"], "green")]))
        imgs = it["images"]
        if not imgs:
            # No photo of this kind of work exists (drains end up buried). A
            # branded stripe panel, not a stock photo of someone else's job.
            panel = container([
                widget("icon", {"selected_icon": icon(it.get("panel_icon", "fas fa-water")), "size": slider(54),
                                "align": "center", "view": "default"},
                       globals_={"primary_color": color_ref(GOLD)}),
                _h(it["title"], "div", T["h_medium"], "center", True),
                _p(it.get("panel_text", ""), "center", True, True)],
                {"content_width": "full", "flex_direction": "column", "flex_gap": gap(12),
                 "flex_justify_content": "center", "flex_align_items": "center", "min_height": slider(400),
                 "min_height_mobile": slider(260), "padding": dims(30, 30, 30, 30), "border_radius": R,
                 "background_background": "classic"},
                globals_={"background_color": color_ref(GREEN)})
            media_kids = [_stripes(panel)]
        else:
            media_kids = [_img(imgs[0], 400, group="svc-" + it["slug"])]
        if len(imgs) > 1:
            tw = _tracks([1] * min(3, len(imgs) - 1), 10, container=KIT_CONTAINER * 0.46)[0]
            media_kids.append(_row([_col([_img(i, 110, group="svc-" + it["slug"])], tw,
                                         extra={"width_tablet": slider(tw, "%"), "width_mobile": slider(tw, "%")})
                                    for i in imgs[1:4]],
                                   10, align="stretch", extra={"flex_wrap": "nowrap", "flex_wrap_tablet": "nowrap",
                                                               "flex_direction_mobile": "row"}))
        w = _tracks([1, 1.08], 52)
        pair = [_col(media_kids, w[0], extra={"flex_gap": gap(10)}), _col(copy, w[1], extra={"flex_gap": gap(14)})]
        if n % 2:
            pair.reverse()
        rows.append(_sec([_row(pair, 52, align="center")], bg, anchor=it["slug"]))
    return container(rows, {"content_width": "full", "flex_direction": "column", "flex_gap": gap(0),
                            "padding": dims(0, 0, 0, 0)})


@block("mm.gallery")
def mm_gallery(props):
    """The client's own job photos in a grid; every photo opens in a
    lightbox that steps through the set."""
    kids = _head(props, False, props.get("align", "left"))
    cols = props.get("columns", 4)
    w = _tracks([1] * cols, 12)[0]
    cells = [_col([_img(i, props.get("height", 230), radius=box(4), group=props.get("group", "work"), zoom=True)], w,
                  extra={"width_tablet": slider(_tracks([1, 1], 12, 720)[0], "%"),
                         "width_mobile": slider(_tracks([1, 1], 10, 360)[0], "%")})
             for i in props["images"]]
    kids.append(_row(cells, 12, align="stretch", extra={"flex_wrap": "wrap", "flex_direction_mobile": "row"}))
    if props.get("note"):
        kids.append(_p(props["note"], small=True))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor", "work"))


@block("mm.reviews")
def mm_reviews(props):
    """REAL reviews only, quoted word for word with the reviewer's name as the
    platform shows it and a link to the source."""
    kids = _head(props, False, "left")
    items = props["items"]
    w = _tracks([1] * len(items), GUT)[0]
    cards = []
    for r in items:
        cards.append(_card([
            widget("icon", {"selected_icon": icon("fas fa-quote-left"), "size": slider(24), "align": "left",
                            "view": "default"}, globals_={"primary_color": color_ref(GOLD)}),
            _p("&ldquo;" + r["text"] + "&rdquo;"),
            widget("heading", {"title": r["name"] + " &middot; " + r["source"], "header_size": "div", "align": "left",
                               "link": link(r["url"], external=True)},
                   globals_={"title_color": color_ref(GREEN), "typography_typography": typo_ref(T["meta"])}),
        ], w, lift=False, extra={"width_tablet": slider(100, "%"), "border_border": "solid",
                                 "border_width": dims(0, 0, 0, 4)}))
        cards[-1]["settings"]["__globals__"]["border_color"] = color_ref(GOLD)
    kids.append(_row(cards, GUT, align="stretch", extra={"flex_wrap": "wrap"}))
    if props.get("note"):
        kids.append(_p(props["note"], small=True))
    return _sec(kids, props.get("bg", "pale"), anchor=props.get("anchor", "reviews"))


@block("mm.steps")
def mm_steps(props):
    bg = props.get("bg", "white")
    dk = _dark(bg)
    kids = _head(props, dk, "left")
    items = props["items"]
    w = _tracks([1] * len(items), GUT)[0]
    cells = []
    for n, it in enumerate(items, 1):
        cells.append(_col([
            widget("heading", {"title": "%02d" % n, "header_size": "div", "align": "left"},
                   globals_={"title_color": color_ref(GOLD), "typography_typography": typo_ref(T["h_large"])}),
            _h(it["title"], "h3", T["h_small"], on_dark=dk),
            _p(it["text"], on_dark=dk, small=True)], w,
            extra={"flex_gap": gap(8), "width_tablet": slider(100, "%"), "padding": dims(18, 0, 0, 0),
                   "border_border": "solid", "border_width": dims(3, 0, 0, 0),
                   "__globals__": {"border_color": color_ref(GOLD)}}))
    kids.append(_row(cells, GUT, align="flex-start"))
    return _sec(kids, bg, anchor=props.get("anchor"))


@block("mm.area")
def mm_area(props):
    """Service area: the towns as pills on green, plus a map of the base."""
    kids = _head({k: props.get(k) for k in ("eyebrow", "title", "intro")}, True)
    pills = []
    for t in props["towns"]:
        pills.append(container([widget("heading", {"title": t, "header_size": "div", "align": "center"},
                                        globals_={"title_color": color_ref(INK),
                                                  "typography_typography": typo_ref(T["meta"])})],
                               {"content_width": "full", "flex_direction": "row", "flex_direction_mobile": "row",
                                "width": slider(round(28 + len(t) * 8.6)), "_flex_shrink": "0",
                                "padding": dims(8, 14, 8, 14), "border_radius": box(999),
                                "flex_justify_content": "center", "background_background": "classic"},
                               globals_={"background_color": color_ref(GOLD)}))
    kids.append(_row(pills, 10, align="center", extra={"flex_wrap": "wrap", "flex_direction_mobile": "row"}))
    for p in props.get("paragraphs", []):
        kids.append(_p(p, on_dark=True))
    left = _col(kids, _tracks([1, 1], 48)[0], extra={"flex_gap": gap(16)})
    mapw = widget("google_maps", {"address": props["map_address"], "zoom": slider(props.get("zoom", 10)),
                                  "height": slider(380)})
    right = _col([mapw], _tracks([1, 1], 48)[1], extra={"border_radius": R, "overflow": "hidden"})
    return _sec([_row([left, right], 48, align="center")], "green", anchor=props.get("anchor", "service-area"))


@block("mm.cta")
def mm_cta(props):
    kids = [_eyebrow(props["eyebrow"], True, "center")] if props.get("eyebrow") else []
    kids += [_h(props["title"], "h2", T["h_large"], "center", True), _rule("center")]
    if props.get("text"):
        kids.append(container([_p(props["text"], "center", True)], {
            "content_width": "full", "flex_direction": "column", "width": slider(62, "%"),
            "width_mobile": slider(100, "%"), "margin": dims(0, "auto", 0, "auto")}))
    btns = [_btn(props["cta_label"], props["cta_url"], "gold")]
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props["alt_url"], "ghost", "fas fa-phone"))
    kids.append(_btns(btns, "center"))
    sec = _sec(kids, "green", pad=dims(80, 0, 80, 0), extra={"flex_align_items": "center"})
    return _stripes(sec)


@block("mm.faq")
def mm_faq(props):
    acc = _faq(props["items"], True)
    acc["settings"]["faq_schema"] = "yes"
    g = acc["settings"]["__globals__"]
    for k in ("accordion_item_title_color", "accordion_item_title_icon_color"):
        g.pop(k, None)
    # Real nested-accordion colour controls (see forge-dark-kit-defaults).
    g.update({"normal_title_color": color_ref(INK), "hover_title_color": color_ref(GREEN),
              "active_title_color": color_ref(GREEN), "normal_icon_color": color_ref(GREEN),
              "hover_icon_color": color_ref(GREEN), "active_icon_color": color_ref(GREEN)})
    head = _head({**{k: props.get(k) for k in ("eyebrow", "title", "intro")}, "intro_width": 100})
    w = _tracks([0.8, 1.2], 52)
    return _sec([_row([_col(head, w[0]), _col([acc], w[1])], 52, align="flex-start")],
                props.get("bg", "white"), anchor="faq")


@block("mm.form")
def mm_form(props):
    f = props["form"]
    fields = []
    for fl in f["fields"]:
        item = {"custom_id": fl["id"], "field_type": fl.get("type", "text"), "field_label": fl["label"],
                "placeholder": fl.get("placeholder", ""), "required": "true" if fl.get("required") else "",
                "width": str(fl.get("width", 100))}
        if fl.get("options"):
            item["field_options"] = chr(10).join(fl["options"])
        if fl.get("rows"):
            item["rows"] = fl["rows"]
        fields.append(repeater_item(**item))
    form = widget("form", {
        "form_name": f["form_name"], "form_fields": fields, "submit_actions": ["email"],
        "email_to": f.get("email", ""), "email_subject": f["subject"], "button_text": f["submit"],
        "button_size": "md", "button_width": "100", "input_size": "md", "show_labels": "yes",
        "mark_required": "yes", "row_gap": slider(14), "column_gap": slider(12),
        "success_message": f["success"], "field_border_radius": box(4), "field_border_width": box(1),
        "button_border_radius": box(4)},
        globals_={"button_background_color": color_ref(GOLD), "button_text_color": color_ref(INK),
                  "button_background_hover_color": color_ref(GREEN), "button_hover_color": color_ref(C["white"]),
                  "field_background_color": color_ref(C["white"]), "field_text_color": color_ref(INK),
                  "field_border_color": color_ref(LINE), "label_color": color_ref(INK),
                  "mark_required_color": color_ref(GREEN)})
    card = _card([_h(props["title"], "h2", T["h_medium"]), _rule(width=60),
                  *([_p(props["intro"], small=True)] if props.get("intro") else []), form],
                 lift=False, pad=dims(32, 30, 34, 30), extra={"flex_gap": gap(14), "border_border": "solid",
                                                              "border_width": dims(4, 1, 1, 1)})
    card["settings"]["__globals__"]["border_color"] = color_ref(GOLD)
    side = props.get("side")
    if side:
        sk = _head({k: side.get(k) for k in ("eyebrow", "title")})
        for p in side.get("paragraphs", []):
            sk.append(_p(p))
        if side.get("ticks"):
            sk.append(_ticks(side["ticks"], px=KIT_CONTAINER * 0.4))
        if side.get("phone"):
            sk.append(_btns([_btn("Call " + side["phone"], _tel(side["phone_tel"]), "green", "fas fa-phone")]))
        w = _tracks([0.9, 1.1], 52)
        body = _row([_col(sk, w[0], extra={"flex_gap": gap(14)}), _col([card], w[1])], 52, align="flex-start")
    else:
        body = card
    return _sec([body], props.get("bg", "pale"), anchor=props.get("anchor", "book"))


@block("mm.contactcards")
def mm_contactcards(props):
    kids = _head(props, False, "left")
    items = props["items"]
    w = _tracks([1] * len(items), GUT)[0]
    cards = []
    for it in items:
        val = widget("heading", {"title": it["value"], "header_size": "div", "align": "left",
                                 **({"link": link(it["href"])} if it.get("href") else {})},
                     globals_={"title_color": color_ref(INK), "typography_typography": typo_ref(T["h_small"])})
        cards.append(_card([
            widget("icon", {"selected_icon": icon(it["icon"]), "size": slider(18), "align": "left", "view": "stacked",
                            "shape": "circle", "icon_padding": slider(12)},
                   globals_={"primary_color": color_ref(GREEN), "secondary_color": color_ref(C["white"])}),
            widget("heading", {"title": it["label"], "header_size": "div", "align": "left"},
                   globals_={"title_color": color_ref(GREEN), "typography_typography": typo_ref(T["eyebrow"])}),
            val, *([_p(it["text"], small=True)] if it.get("text") else [])],
            w, extra={"width_tablet": slider(_tracks([1, 1], GUT, 720)[0], "%")}))
    kids.append(_row(cards, GUT, align="stretch", extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))
