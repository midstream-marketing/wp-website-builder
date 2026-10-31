"""
blocks_easy.py - Easy Gebäudeservice, Viersen.

No reference site was named. The client pointed at their Facebook page for
the logo and the photographs, so the design is anchored to the CURRENT logo
(profile picture of 21 March 2026), and four things are taken from it:

  * TWO TONES, ONE SPLIT. The wordmark is "EA" in black and "SY" in steel
    blue (#3C88BC, sampled). So headlines carry one phrase in the logo blue
    and the rest in ink - the same split, at display size, where the blue's
    3.86:1 against white is legal (large text). Small blue text and every
    button fill use the deeper #2A6E9F (5.48:1), never the logo blue.
  * THE SLANT. The E and A of the mark are cut on a shared diagonal. That cut
    is the one shape in the identity, and it is used for three things only:
    the left edge of the hero photograph, the small tab before every eyebrow,
    and the bottom edge of the inner-page heroes and the closing band.
  * BLACK LETTERS NEED A LIGHT HEADER. "EA" and "Gebäudeservice" are black,
    so the header is white. The footer is navy and carries a reversed copy of
    the logo made in prep_images.py.
  * A CLEANING COMPANY'S PROOF IS BEFORE AND AFTER. The client's own album is
    four photographs, three of them before/after pairs. `ez.beforeafter`
    exists for those and labels them as the client's own work. Nothing else
    on the site pretends to be theirs.

The client asked for "no unnecessary animations": there is no scroll reveal
here and the IR sets no motion preset. Cards lift 4px on hover, which is
feedback, not animation.

    ez.topbar       navy utility strip
    ez.header       white sticky header, logo, menu, one CTA
    ez.footer       navy, reversed logo, four columns, legal bar
    ez.hero         split hero, slanted photo, chips floating on the photo
    ez.pagehero     inner-page hero, photo under a scrim, slanted bottom edge
    ez.strip        four plain facts in a row, hairline dividers
    ez.split        photo one side, copy and ticks the other
    ez.services     photo cards with a slanted numeral tab on the photo
    ez.beforeafter  the client's own before/after pairs, chips on the photos
    ez.process      three numbered steps
    ez.area         navy band: the 50 km figure and the towns in three rings
    ez.servicerows  services page: one anchored, alternating row per service
    ez.faq          accordion with FAQ schema
    ez.cta          blue closing band with a slanted top edge
    ez.contactcards contact detail cards; placeholders render highlighted
    ez.form         enquiry form card beside a short brief
    ez.notice       amber "complete before publishing" banner
    ez.legal        long-form legal document in a narrow reading column
"""
from __future__ import annotations

import re

from .core import (
    container, widget, repeater_item, slider, dims, box, media, link,
    gap, color_ref, typo_ref, icon, css,
)
from .tokens import C, T
from .blocks import (
    block, _row, _col, _tracks, _button, _text, _faq, _hover_lift, _angle,
    KIT_CONTAINER, CARD_SHADOW, CARD_SHADOW_SOFT,
)

DEEP = "primary"        # #2A6E9F - fills, links, small blue text
NAVY = "secondary"      # #0E1A25 - headings, dark grounds
LOGO_BLUE = "accent"    # #3C88BC - display accents only (large text)
INK = "ezink01"         # #14181D - the logo's black
MIST = "ezsil01"        # #A9BCCB - secondary text on navy (9.0:1)
NAVY_UP = "ezgrp01"     # #16263A - cards and hairlines on navy
AMBER = "ezamb01"       # #FFF3D1 - placeholder highlight ground
AMBER_INK = "ezamb02"   # #7A4E00 - text on the amber

EZ_PAD = dims(96, 0, 96, 0)
EZ_PAD_T = dims(70, 24, 70, 24)
EZ_PAD_M = dims(56, 18, 56, 18)
R_BTN = box(4)
R_CARD = box(6)
GUTTER = 28

# The logo's diagonal. Both letters lean at roughly the same angle; 9% of a
# 520px-tall photo is a ~47px run, which is close to the mark's slope.
SLANT = 9


# ─────────────────────────────── helpers ───────────────────────────────────

def _sec(children, bg="white", pad=None, anchor=None, extra=None):
    grounds = {"white": C["white"], "pale": C["surface"], "mist": C["surface_alt"],
               "navy": NAVY, "deep": DEEP}
    s = {
        "content_width": "boxed",
        "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "flex_gap": gap(34),
        "padding": pad or EZ_PAD,
        "padding_tablet": EZ_PAD_T,
        "padding_mobile": EZ_PAD_M,
        "background_background": "classic",
    }
    if anchor:
        s["_element_id"] = anchor
    if extra:
        s.update(extra)
    return container(children, s, globals_={
        "background_color": color_ref(grounds.get(bg, C["white"]))})


def _dark(bg):
    return bg in ("navy", "deep")


def _accent(text):
    """`Lead [[accent]] tail` -> the accent phrase in the logo blue.

    Only ever used at display size, where 3.86:1 is legal. One heading
    widget with a span keeps the sentence a single heading for crawlers and
    screen readers."""
    return re.sub(r"\[\[(.+?)\]\]",
                  r'<span style="color:var(--e-global-color-accent)">\1</span>',
                  text)


def _h(text, size="h2", token=None, align="left", on_dark=False):
    return widget("heading", {
        "title": _accent(text), "header_size": size, "align": align,
    }, globals_={
        "title_color": color_ref(C["white"] if on_dark else NAVY),
        "typography_typography": typo_ref(token or T["h_large"]),
    })


def _p(html, align="left", on_dark=False, small=False, color=None):
    t = _text(html, align, on_dark=on_dark, small=small)
    if color or on_dark:
        t["settings"]["__globals__"]["text_color"] = color_ref(color or MIST)
    return t


def _tab(on_dark=False, width=22, height=10):
    """The logo's slant as a small parallelogram - the eyebrow marker."""
    s = {
        "content_width": "full", "flex_direction": "column",
        "width": slider(width), "min_height": slider(height),
        "_flex_shrink": "0",
        "background_background": "classic",
        "custom_css": css(
            "selector { clip-path: polygon(35% 0, 100% 0, 65% 100%, 0 100%); }"),
    }
    return container([], s, globals_={
        "background_color": color_ref(LOGO_BLUE if on_dark else DEEP)})


def _eyebrow(text, on_dark=False, align="left", color=None):
    lab = widget("heading", {
        "title": text, "header_size": "div", "align": align,
    }, globals_={
        "title_color": color_ref(color or (MIST if on_dark else DEEP)),
        "typography_typography": typo_ref(T["eyebrow"]),
    })
    tab = _tab(on_dark)
    if color:
        tab["settings"]["__globals__"]["background_color"] = color_ref(color)
    return container([tab, lab], {
        "content_width": "full", "flex_direction": "row",
        "flex_direction_mobile": "row", "flex_wrap": "nowrap",
        "flex_gap": gap(10), "flex_align_items": "center",
        "flex_justify_content": "center" if align == "center" else "flex-start",
    })


def _btn(label, href, style="solid", icon_name="fas fa-arrow-right"):
    """Four buttons.

        solid   deep blue fill, white label (5.48:1). The primary.
        light   white fill, deep blue label - on the blue closing band.
        ghost   navy hairline on light grounds.
        ghost_d white hairline on dark grounds and photographs.
    """
    b = _button(label, href, "primary", icon_name or "")
    b["settings"].update({
        "border_radius": R_BTN,
        "text_padding": dims(16, 28, 16, 28),
        "border_border": "solid", "border_width": box(1),
    })
    g = b["settings"].setdefault("__globals__", {})
    if style == "light":
        g.update({"background_color": color_ref(C["white"]),
                  "border_color": color_ref(C["white"]),
                  "button_text_color": color_ref(DEEP),
                  "button_background_hover_color": color_ref(NAVY),
                  "button_hover_border_color": color_ref(NAVY),
                  "hover_color": color_ref(C["white"])})
    elif style == "ghost":
        g.update({"background_color": color_ref(C["transparent"]),
                  "border_color": color_ref(NAVY),
                  "button_text_color": color_ref(NAVY),
                  "button_background_hover_color": color_ref(NAVY),
                  "button_hover_border_color": color_ref(NAVY),
                  "hover_color": color_ref(C["white"])})
    elif style == "ghost_d":
        g.update({"background_color": color_ref(C["transparent"]),
                  "border_color": color_ref(C["white"]),
                  "button_text_color": color_ref(C["white"]),
                  "button_background_hover_color": color_ref(C["white"]),
                  "button_hover_border_color": color_ref(C["white"]),
                  "hover_color": color_ref(NAVY)})
    else:
        g.update({"background_color": color_ref(DEEP),
                  "border_color": color_ref(DEEP),
                  "button_text_color": color_ref(C["white"]),
                  "button_background_hover_color": color_ref(NAVY),
                  "button_hover_border_color": color_ref(NAVY),
                  "hover_color": color_ref(C["white"])})
    return b


def _btn_row(btns, align="flex-start"):
    return _row(btns, 12, align="center", justify=align, extra={
        "flex_wrap": "wrap", "flex_direction_mobile": "column",
        "flex_align_items_mobile": "stretch", "padding": dims(6, 0, 0, 0)})


def _ticks(items, on_dark=False, columns=1, container_px=KIT_CONTAINER):
    rows = []
    for t in items:
        mark = widget("icon", {
            "selected_icon": icon("fas fa-check"), "size": slider(12),
            "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref(LOGO_BLUE if on_dark else DEEP)})
        rows.append(_row([mark, _p(t, on_dark=on_dark, small=True)], 12,
                         align="flex-start",
                         extra={"flex_wrap": "nowrap",
                                "flex_direction_mobile": "row",
                                "padding": dims(5, 0, 5, 0)}))
    if columns == 1:
        return container(rows, {"content_width": "full",
                                "flex_direction": "column", "flex_gap": gap(0)})
    per = -(-len(rows) // columns)
    # container_px is an ESTIMATE of the parent column's width. Size against
    # 90% of it, so a parent a few pixels narrower than estimated still holds
    # the columns on one line (the row-geometry rule, V11).
    w = _tracks([1] * columns, 22, container=container_px * 0.9)[0]
    cols = [_col(rows[i:i + per], w, extra={"flex_gap": gap(0)})
            for i in range(0, len(rows), per)]
    return _row(cols, 22, align="flex-start", extra={"flex_wrap": "wrap"})


def _card(kids, width=None, pad=None, on_dark=False, lift=True, extra=None):
    s = {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(12),
        "padding": pad or dims(28, 26, 30, 26),
        "padding_mobile": dims(22, 18, 24, 18),
        "border_radius": R_CARD,
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
        **(CARD_SHADOW_SOFT if not on_dark else {}),
    }
    if width:
        s.update({"width": slider(width, "%"), "width_mobile": slider(100, "%")})
    if extra:
        s.update(extra)
    el = container(kids, s, globals_={
        "background_color": color_ref(NAVY_UP if on_dark else C["white"]),
        "border_color": color_ref(NAVY_UP if on_dark else C["border"])})
    return _hover_lift(el, 4) if lift else el


def _shot(image, height=240, radius=None, extra_css=None):
    radius = radius or R_CARD
    if image and image.get("url"):
        w = widget("image", {
            "image": media(image["url"], image.get("alt", "")),
            "image_size": "full", "width": slider(100, "%"),
            "height": slider(height), "object-fit": "cover",
            "align": "center", "image_border_radius": radius})
        if extra_css:
            w["settings"]["custom_css"] = css(*extra_css)
        return w
    return container([], {
        "content_width": "full", "min_height": slider(height),
        "border_radius": radius, "border_border": "dashed",
        "border_width": box(1), "background_background": "classic",
    }, globals_={"background_color": color_ref(C["surface"]),
                 "border_color": color_ref(C["border"])})


def _chip(text, icon_name=None, tone="white"):
    """Small pill. tone: white (on photos), deep (Before/After), navy."""
    fills = {"white": C["white"], "deep": DEEP, "navy": NAVY}
    inks = {"white": NAVY, "deep": C["white"], "navy": C["white"]}
    kids = []
    if icon_name:
        kids.append(widget("icon", {
            "selected_icon": icon(icon_name), "size": slider(13),
            "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref(
            DEEP if tone == "white" else C["white"])}))
    kids.append(widget("heading", {
        "title": text, "header_size": "div", "align": "left",
    }, globals_={"title_color": color_ref(inks[tone]),
                 "typography_typography": typo_ref(T["meta"])}))
    # A container defaults to width:100% and has no fit-content option, so
    # the pill is sized from its label: 13px meta runs ~7.4px a character.
    est = 30 + (21 if icon_name else 0) + len(text) * 7.4
    return container(kids, {
        "content_width": "full", "flex_direction": "row",
        "flex_direction_mobile": "row", "flex_wrap": "nowrap",
        "flex_gap": gap(8), "flex_align_items": "center",
        "width": slider(round(est)), "_flex_shrink": "0",
        "padding": dims(8, 14, 8, 14),
        "border_radius": box(999),
        "background_background": "classic",
        **CARD_SHADOW_SOFT,
    }, globals_={"background_color": color_ref(fills[tone])})


def _float(el, h="start", v="start", x=16, y=16, z=3):
    """Pin `el` over its (relative) parent - the overlay-chip device."""
    el["settings"].update({
        "_position": "absolute",
        "_offset_orientation_h": h, "_offset_orientation_v": v,
        "_offset_x": slider(x), "_offset_y": slider(y),
        "_z_index": z,
    })
    return el


def _frame(kids, height, extra=None):
    """A relative box that overlay chips can be pinned inside."""
    s = {"content_width": "full", "flex_direction": "column",
         "position": "relative", "min_height": slider(height),
         "flex_gap": gap(0), "overflow": "hidden", "border_radius": R_CARD}
    if extra:
        s.update(extra)
    return container(kids, s)


def _numeral(n, on_dark=False, token=None):
    return widget("heading", {
        "title": "%02d" % n, "header_size": "div", "align": "left",
    }, globals_={"title_color": color_ref(LOGO_BLUE),
                 "typography_typography": typo_ref(token or T["h_large"])})


def _head(props, on_dark=False, align="left"):
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], on_dark, align))
    if props.get("title"):
        kids.append(_h(props["title"], props.get("tag", "h2"),
                       T["h_large"], align, on_dark))
    if props.get("intro"):
        kids.append(container([_p(props["intro"], align, on_dark)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(props.get("intro_width", 70), "%"),
            "width_mobile": slider(100, "%"),
            "margin": (dims(0, "auto", 0, "auto") if align == "center"
                       else dims(0, 0, 0, 0))}))
    if not kids:
        return []
    return [container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(14),
        "flex_align_items": "center" if align == "center" else "flex-start"})]


def _link_line(label, href, on_dark=False):
    w = widget("heading", {
        "title": label + " &rarr;", "header_size": "div", "align": "left",
        "link": link(href),
    }, globals_={"title_color": color_ref(LOGO_BLUE if on_dark else DEEP),
                 "typography_typography": typo_ref(T["meta"])})
    return w


# ─────────────────────────────── chrome ────────────────────────────────────

@block("ez.topbar")
def ez_topbar(props):
    items = []
    for it in props.get("items", []):
        kids = []
        if it.get("icon"):
            kids.append(widget("icon", {
                "selected_icon": icon(it["icon"]), "size": slider(12),
                "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref(LOGO_BLUE)}))
        lab = widget("heading", {
            "title": it.get("label", ""), "header_size": "div", "align": "left",
        }, globals_={"title_color": color_ref(MIST),
                     "typography_typography": typo_ref(T["meta"])})
        if it.get("href"):
            lab["settings"]["link"] = link(it["href"], external=it["href"].startswith("http"))
        kids.append(lab)
        items.append(_row(kids, 8, align="center",
                          extra={"flex_wrap": "nowrap",
                                 "flex_direction_mobile": "row"}))
    bar = _row(items, 28, align="center", justify="space-between",
               extra={"flex_wrap": "wrap",
                      "flex_justify_content_mobile": "center"})
    return container([bar], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "padding": dims(9, 0, 9, 0),
        "padding_mobile": dims(8, 16, 8, 16),
        "background_background": "classic",
        "hide_mobile": "hidden-mobile",
    }, globals_={"background_color": color_ref(NAVY)})


@block("ez.header")
def ez_header(props):
    """White header: the logo's black letters need a light ground."""
    logo = widget("theme-site-logo", {
        "align": "left", "width": slider(props.get("logo_width", 168)),
        "width_mobile": slider(132),
        "image_size": "full",
        **({"image": media(props["logo"], props.get("business", ""))}
           if props.get("logo") else {}),
    })
    nav = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"),
        "layout": "horizontal", "align_items": "flex-end",
        "pointer": "underline", "animation_line": "fade",
        "menu_space_between": slider(30),
        "toggle_align": "right",
    }, globals_={
        "menu_typography_typography": typo_ref(T["meta"]),
        "color_menu_item": color_ref(NAVY),
        "color_menu_item_hover": color_ref(DEEP),
        "color_menu_item_active": color_ref(DEEP),
        "pointer_color_menu_item_hover": color_ref(LOGO_BLUE),
        "pointer_color_menu_item_active": color_ref(LOGO_BLUE),
        "toggle_color": color_ref(NAVY),
    })
    cta = _btn(props.get("cta_label", "Get a Quote"),
               props.get("cta_url", "/contact/"), "solid", "")
    cta["settings"]["text_padding"] = dims(13, 22, 13, 22)
    row = _row([
        _col([logo], 24, extra={"flex_justify_content": "center",
                                "width_tablet": slider(40, "%"),
                                "width_mobile": slider(60, "%")}),
        _col([nav], 54, extra={"flex_justify_content": "center",
                               "flex_align_items": "flex-end",
                               "width_tablet": slider(30, "%"),
                               "width_mobile": slider(36, "%")}),
        _col([cta], 18, extra={"flex_justify_content": "center",
                               "flex_align_items": "flex-end",
                               "width_tablet": slider(26, "%"),
                               "hide_mobile": "hidden-mobile"}),
    ], 20, align="center", extra={
        "flex_wrap": "nowrap", "flex_wrap_tablet": "nowrap",
        "flex_direction_mobile": "row", "flex_wrap_mobile": "nowrap"})
    return container([row], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "padding": dims(14, 0, 14, 0),
        "padding_tablet": dims(12, 20, 12, 20),
        "padding_mobile": dims(10, 16, 10, 16),
        "border_border": "solid", "border_width": dims(0, 0, 1, 0),
        "background_background": "classic",
        "sticky": "top", "sticky_on": ["desktop", "tablet", "mobile"],
        "sticky_offset": 0,
        **CARD_SHADOW_SOFT,
    }, globals_={"background_color": color_ref(C["white"]),
                 "border_color": color_ref(C["border"])})


@block("ez.footer")
def ez_footer(props):
    brand = []
    if props.get("logo"):
        brand.append(widget("image", {
            "image": media(props["logo"], props.get("business", "Logo")),
            "image_size": "full", "width": slider(170), "align": "left"}))
    if props.get("blurb"):
        brand.append(_p(props["blurb"], on_dark=True, small=True))
    if props.get("social"):
        icons = [widget("icon", {
            "selected_icon": icon(s.get("icon", "fab fa-facebook-f")),
            "size": slider(15), "align": "center", "view": "stacked",
            "shape": "circle", "icon_padding": slider(10),
            "link": link(s.get("url", "#"), external=True),
        }, globals_={"primary_color": color_ref(NAVY_UP),
                     "secondary_color": color_ref(C["white"])})
            for s in props["social"]]
        brand.append(_row(icons, 10, align="center",
                          extra={"flex_wrap": "wrap",
                                 "flex_direction_mobile": "row"}))

    cols = props.get("columns", [])
    widths = _tracks([1.45] + [1] * len(cols), GUTTER)
    body = [_col(brand, widths[0], extra={"flex_gap": gap(18),
                                          "width_tablet": slider(100, "%")})]
    for i, c in enumerate(cols):
        kids = [container([_tab(True, 16, 8), widget("heading", {
            "title": c.get("title", ""), "header_size": "div", "align": "left",
        }, globals_={"title_color": color_ref(C["white"]),
                     "typography_typography": typo_ref(T["eyebrow"])})], {
            "content_width": "full", "flex_direction": "row",
            "flex_direction_mobile": "row", "flex_wrap": "nowrap",
            "flex_gap": gap(8), "flex_align_items": "center",
            "padding": dims(0, 0, 6, 0)})]
        for l in c.get("links", []):
            row = []
            if l.get("icon"):
                row.append(widget("icon", {
                    "selected_icon": icon(l["icon"]), "size": slider(12),
                    "align": "center", "view": "default",
                }, globals_={"primary_color": color_ref(LOGO_BLUE)}))
            lab = widget("heading", {
                "title": l.get("label", ""), "header_size": "div",
                "align": "left",
            }, globals_={"title_color": color_ref(MIST),
                         "typography_typography": typo_ref(T["body_small"])})
            if l.get("url"):
                lab["settings"]["link"] = link(l["url"])
            row.append(lab)
            kids.append(_row(row, 9, align="flex-start",
                             extra={"flex_wrap": "nowrap",
                                    "flex_direction_mobile": "row",
                                    "padding": dims(3, 0, 3, 0)}))
        body.append(_col(kids, widths[i + 1], extra={
            "flex_gap": gap(4), "width_tablet": slider(31, "%")}))

    legal_links = []
    for l in props.get("legal_links", []):
        legal_links.append(widget("heading", {
            "title": l["label"], "header_size": "div", "align": "left",
            "link": link(l["url"]),
        }, globals_={"title_color": color_ref(C["white"]),
                     "typography_typography": typo_ref(T["meta"])}))
    legal = _row([
        widget("heading", {
            "title": props.get("legal", ""), "header_size": "div",
            "align": "left",
        }, globals_={"title_color": color_ref(MIST),
                     "typography_typography": typo_ref(T["meta"])}),
        _row(legal_links, 22, align="center", justify="flex-end",
             extra={"flex_wrap": "wrap", "flex_direction_mobile": "row",
                    "width": slider(50, "%"), "width_mobile": slider(100, "%"),
                    "flex_justify_content_mobile": "flex-start"}),
    ], 16, align="center", justify="space-between",
        extra={"flex_wrap": "wrap", "padding": dims(22, 0, 0, 0),
               "border_border": "solid", "border_width": dims(1, 0, 0, 0),
               "flex_align_items_mobile": "flex-start"})
    legal["settings"].setdefault("__globals__", {})["border_color"] = \
        color_ref(NAVY_UP)

    return container([
        _row(body, GUTTER, align="flex-start",
             extra={"flex_wrap": "nowrap", "flex_wrap_tablet": "wrap"}),
        legal,
    ], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column", "flex_gap": gap(44),
        "padding": dims(76, 0, 30, 0),
        "padding_tablet": dims(60, 24, 30, 24),
        "padding_mobile": dims(52, 18, 28, 18),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(NAVY)})


# ─────────────────────────────── sections ──────────────────────────────────

@block("ez.hero")
def ez_hero(props):
    """Copy on white, the photograph cut on the logo's diagonal, and chips
    pinned over the photo. The slant is dropped below tablet, where a
    stacked photo with a sloped edge just looks broken."""
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"]))
    kids.append(_h(props["title"], "h1", T["hero"]))
    if props.get("intro"):
        kids.append(_p(props["intro"]))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"), "solid"))
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props.get("alt_url", "#"), "ghost", ""))
    if btns:
        kids.append(_btn_row(btns))
    if props.get("ticks"):
        kids.append(_ticks(props["ticks"], columns=2,
                           container_px=KIT_CONTAINER * 0.5))

    h = props.get("height", 560)
    photo = _shot(props.get("image"), h, radius=box(0), extra_css=[
        "selector img { clip-path: polygon(%d%% 0, 100%% 0, 100%% 100%%, 0 100%%); }" % SLANT,
        "@media (max-width: 1024px) { selector img { clip-path: none; "
        "border-radius: 6px; } }",
    ])
    if photo["elType"] == "widget":
        photo["settings"]["height_tablet"] = slider(420)
        photo["settings"]["height_mobile"] = slider(300)
    chips = [_float(_chip(c["label"], c.get("icon"), c.get("tone", "white")),
                    h="start" if i == 0 else "end", v="end",
                    x=64 if i == 0 else 22, y=28 + 0 * i, z=3 + i)
             for i, c in enumerate(props.get("chips", [])[:2])]
    frame = _frame([photo] + chips, h, extra={
        "border_radius": box(0), "min_height_tablet": slider(420),
        "min_height_mobile": slider(300)})

    w = _tracks([1.02, 1], 56)
    row = _row([_col(kids, w[0], extra={"flex_gap": gap(20),
                                         "padding": dims(10, 0, 10, 0)}),
                _col([frame], w[1])], 56, align="center")
    return _sec([row], "white", pad=dims(64, 0, 72, 0),
                anchor=props.get("anchor"),
                extra={"padding_tablet": dims(44, 24, 56, 24),
                       "padding_mobile": dims(34, 18, 46, 18)})


@block("ez.pagehero")
def ez_pagehero(props):
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], True))
    kids.append(_h(props["title"], "h1", T["hero"], on_dark=True))
    if props.get("intro"):
        kids.append(_p(props["intro"], on_dark=True))
    if props.get("cta_label"):
        kids.append(_btn_row([_btn(props["cta_label"],
                                   props.get("cta_url", "#"), "solid")]))
    col = _col(kids, props.get("width", 62), extra={"flex_gap": gap(18)})
    sec = _sec([_row([col], GUTTER)], "navy",
               pad=dims(96, 0, 118, 0), anchor=props.get("anchor"),
               extra={"min_height": slider(props.get("height", 400)),
                      "flex_justify_content": "center",
                      "padding_tablet": dims(70, 24, 92, 24),
                      "padding_mobile": dims(54, 18, 76, 18)})
    img = props.get("image")
    if img and img.get("url"):
        sec["settings"].update({
            "background_image": media(img["url"], img.get("alt", "")),
            "background_position": props.get("position", "center center"),
            "background_size": "cover", "background_repeat": "no-repeat",
            "background_overlay_background": "classic",
            "background_overlay_opacity": slider(0.8),
        })
        sec["settings"]["__globals__"]["background_overlay_color"] = \
            color_ref(NAVY)
    return _angle(sec, "bottom", 44)


@block("ez.strip")
def ez_strip(props):
    """Four plain, true facts. Not a stats row: there are no numbers here
    because none were supplied."""
    items = props.get("items", [])
    w = _tracks([1] * len(items), 0)[0]
    cells = []
    for i, it in enumerate(items):
        kids = [widget("icon", {
            "selected_icon": icon(it.get("icon", "fas fa-check")),
            "size": slider(22), "align": "left", "view": "default",
        }, globals_={"primary_color": color_ref(DEEP)}),
            _h(it["title"], "h3", T["h_small"]),
            _p(it.get("text", ""), small=True)]
        cells.append(_col(kids, w, extra={
            "flex_gap": gap(8), "padding": dims(6, 28, 6, 28),
            "padding_mobile": dims(18, 0, 18, 0),
            "width_tablet": slider(50, "%"),
            "border_border": "solid",
            "border_width": dims(0, 0, 0, 0 if i == 0 else 1),
            "border_width_mobile": dims(1 if i else 0, 0, 0, 0),
            "__globals__": {"border_color": color_ref(C["border"])},
        }))
    row = _row(cells, 0, align="stretch",
               extra={"flex_wrap": "nowrap", "flex_wrap_tablet": "wrap"})
    return _sec([row], props.get("bg", "pale"), pad=dims(44, 0, 44, 0),
                extra={"padding_tablet": dims(36, 24, 36, 24)})


@block("ez.split")
def ez_split(props):
    bg = props.get("bg", "white")
    on_dark = _dark(bg)
    copy = _head({k: props.get(k) for k in ("eyebrow", "title")}, on_dark)
    for p in props.get("paragraphs", []):
        copy.append(_p(p, on_dark=on_dark))
    if props.get("list_title"):
        copy.append(_h(props["list_title"], "h3", T["h_small"], on_dark=on_dark))
    if props.get("ticks"):
        copy.append(_ticks(props["ticks"], on_dark, props.get("tick_columns", 1),
                           container_px=KIT_CONTAINER * 0.5))
    if props.get("cta_label"):
        copy.append(_btn_row([_btn(props["cta_label"], props.get("cta_url", "#"),
                                   "ghost_d" if on_dark else "solid")]))
    h = props.get("image_height", 480)
    kids = [_shot(props.get("image"), h)]
    if props.get("chip"):
        kids.append(_float(_chip(props["chip"], props.get("chip_icon")),
                           "start", "end", 18, 18))
    frame = _frame(kids, h)
    w = _tracks([1, 1.05], 56)
    pair = [_col([frame], w[0]), _col(copy, w[1], extra={"flex_gap": gap(16)})]
    if props.get("flip"):
        pair.reverse()
    return _sec([_row(pair, 56, align="center")], bg, anchor=props.get("anchor"))


@block("ez.services")
def ez_services(props):
    """Photo cards. The numeral sits on the photo in a slanted blue tab -
    the logo's diagonal again - so the eight services read as a set."""
    bg = props.get("bg", "pale")
    kids = _head(props, False, props.get("align", "left"))
    cols = props.get("columns", 4)
    w = _tracks([1] * cols, 24)[0]
    cards = []
    for n, it in enumerate(props.get("items", []), 1):
        th = props.get("thumb_height", 200)
        tab = container([widget("heading", {
            "title": "%02d" % n, "header_size": "div", "align": "left",
        }, globals_={"title_color": color_ref(C["white"]),
                     "typography_typography": typo_ref(T["eyebrow"])})], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(58),
            "padding": dims(7, 18, 7, 14),
            "background_background": "classic",
            "custom_css": css(
                "selector { clip-path: polygon(0 0, 100% 0, 84% 100%, 0 100%); }"),
        }, globals_={"background_color": color_ref(DEEP)})
        photo = _frame([_shot(it.get("image"), th, radius=dims(6, 6, 0, 0)),
                        _float(tab, "start", "end", 0, 0)], th,
                       extra={"border_radius": dims(6, 6, 0, 0)})
        body = [_h(it["title"], "h3", T["h_small"])]
        if it.get("label"):
            body.insert(0, widget("heading", {
                "title": it["label"], "header_size": "div", "align": "left",
            }, globals_={"title_color": color_ref(C["muted"]),
                         "typography_typography": typo_ref(T["meta"])}))
        if it.get("text"):
            body.append(_p(it["text"], small=True))
        if it.get("href"):
            body.append(_link_line(props.get("action_label", "Details"),
                                   it["href"]))
        inner = container(body, {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(8), "padding": dims(20, 20, 24, 20),
            "_flex_grow": 1})
        cards.append(_card([photo, inner], w, pad=dims(0, 0, 0, 0), extra={
            "flex_gap": gap(0), "overflow": "hidden",
            "width_tablet": slider(_tracks([1, 1], 24, 720)[0], "%")}))
    kids.append(_row(cards, 24, align="stretch", extra={"flex_wrap": "wrap"}))
    if props.get("footer_cta"):
        f = props["footer_cta"]
        kids.append(_btn_row([_btn(f["label"], f["url"], "ghost")],
                             "center"))
    return _sec(kids, bg, anchor=props.get("anchor"))


@block("ez.beforeafter")
def ez_beforeafter(props):
    """The client's own work. Two photos per pair, each labelled with a chip
    on the photo, a caption under the pair. Built for the four photographs
    in the client's 'Kunden Aufträge' album and nothing else."""
    bg = props.get("bg", "white")
    kids = _head(props, False, "left")
    pairs = props.get("pairs", [])
    cols = props.get("columns", len(pairs) or 1)
    w = _tracks([1] * cols, 24)[0]
    cards = []
    for p in pairs:
        h = p.get("height", props.get("photo_height", 300))
        half = _tracks([1, 1], 8, container=KIT_CONTAINER * w / 100)
        shots = []
        for side, img in (("before", p["before"]), ("after", p["after"])):
            shots.append(_col([_frame([
                _shot(img, h, radius=box(4)),
                _float(_chip(props.get(side + "_label", side.title()),
                             tone="navy" if side == "before" else "deep"),
                       "start", "start", 10, 10),
            ], h, extra={"border_radius": box(4)})],
                half[0], extra={"width_tablet": slider(half[0], "%"),
                                "width_mobile": slider(half[0], "%")}))
        pair_row = _row(shots, 8, align="stretch", extra={
            "flex_wrap": "nowrap", "flex_wrap_tablet": "nowrap",
            "flex_direction_mobile": "row"})
        body = [pair_row, _h(p["title"], "h3", T["h_small"])]
        if p.get("text"):
            body.append(_p(p["text"], small=True))
        cards.append(_card(body, w, pad=dims(12, 12, 22, 12),
                           extra={"width_tablet": slider(100, "%")}))
    kids.append(_row(cards, 24, align="stretch", extra={"flex_wrap": "wrap"}))
    if props.get("note"):
        kids.append(_p(props["note"], small=True))
    return _sec(kids, bg, anchor=props.get("anchor"))


@block("ez.process")
def ez_process(props):
    bg = props.get("bg", "white")
    on_dark = _dark(bg)
    kids = _head(props, on_dark, "left")
    items = props.get("items", [])
    w = _tracks([1] * len(items), GUTTER)[0]
    cells = []
    for i, it in enumerate(items, 1):
        cells.append(_col([
            _row([_numeral(i, on_dark), _tab(on_dark, 30, 12)], 12,
                 align="center", extra={"flex_wrap": "nowrap",
                                        "flex_direction_mobile": "row"}),
            _h(it["title"], "h3", T["h_medium"], on_dark=on_dark),
            _p(it.get("text", ""), on_dark=on_dark, small=True),
        ], w, extra={"flex_gap": gap(12), "padding": dims(26, 0, 0, 0),
                     "border_border": "solid", "border_width": dims(2, 0, 0, 0),
                     "__globals__": {"border_color": color_ref(
                         NAVY_UP if on_dark else C["border"])}}))
    kids.append(_row(cells, GUTTER, align="flex-start"))
    return _sec(kids, bg, anchor=props.get("anchor"))


@block("ez.area")
def ez_area(props):
    """The service radius as a figure, and the towns in three rings by
    distance. No embedded Google Map: on a German site it loads Google before
    consent, which is a GDPR problem a static list does not have."""
    left = [_eyebrow(props.get("eyebrow", ""), True)]
    left.append(container([
        widget("heading", {"title": props.get("figure", "50"),
                           "header_size": "div", "align": "left"},
               globals_={"title_color": color_ref(C["white"]),
                         "typography_typography": typo_ref(T["wordmark"])}),
        widget("heading", {"title": props.get("unit", "km"),
                           "header_size": "div", "align": "left"},
               globals_={"title_color": color_ref(LOGO_BLUE),
                         "typography_typography": typo_ref(T["h_large"])}),
    ], {"content_width": "full", "flex_direction": "row",
        "flex_direction_mobile": "row", "flex_wrap": "nowrap",
        "flex_gap": gap(10), "flex_align_items": "flex-end"}))
    left.append(_h(props["title"], "h2", T["h_large"], on_dark=True))
    for p in props.get("paragraphs", []):
        left.append(_p(p, on_dark=True))
    if props.get("cta_label"):
        left.append(_btn_row([_btn(props["cta_label"], props.get("cta_url", "#"),
                                   "solid")]))

    rings = []
    for r in props.get("rings", []):
        chips = [_chip(t, None, "white") for t in r["towns"]]
        for c in chips:
            c["settings"].pop("box_shadow_box_shadow_type", None)
            c["settings"].pop("box_shadow_box_shadow", None)
        rings.append(_card([
            container([_tab(True, 18, 9), widget("heading", {
                "title": r["label"], "header_size": "div", "align": "left",
            }, globals_={"title_color": color_ref(C["white"]),
                         "typography_typography": typo_ref(T["eyebrow"])})], {
                "content_width": "full", "flex_direction": "row",
                "flex_direction_mobile": "row", "flex_wrap": "nowrap",
                "flex_gap": gap(8), "flex_align_items": "center"}),
            _p(r.get("note", ""), on_dark=True, small=True),
            _row(chips, 8, align="center",
                 extra={"flex_wrap": "wrap", "flex_direction_mobile": "row"}),
        ], on_dark=True, lift=False, pad=dims(22, 22, 24, 22)))
    w = _tracks([1, 1.15], 56)
    row = _row([_col(left, w[0], extra={"flex_gap": gap(18)}),
                _col(rings, w[1], extra={"flex_gap": gap(14)})], 56,
               align="flex-start")
    return _sec([row], "navy", anchor=props.get("anchor", "service-area"))


@block("ez.servicerows")
def ez_servicerows(props):
    """One row per service on the Services page, alternating sides, each
    with its own anchor so the home cards and the footer can deep-link."""
    rows = []
    items = props.get("items", [])
    for n, it in enumerate(items, 1):
        copy = [_row([_numeral(n, token=T["h_medium"]),
                      widget("heading", {
                          "title": it.get("label", ""), "header_size": "div",
                          "align": "left"},
                          globals_={"title_color": color_ref(C["muted"]),
                                    "typography_typography": typo_ref(T["meta"])})],
                     12, align="center",
                     extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"}),
                _h(it["title"], "h2", T["h_large"])]
        for p in it.get("paragraphs", []):
            copy.append(_p(p))
        if it.get("ticks"):
            copy.append(_h(props.get("list_title", "Typically included"),
                           "h3", T["h_small"]))
            copy.append(_ticks(it["ticks"], columns=2 if len(it["ticks"]) > 4 else 1,
                               container_px=KIT_CONTAINER * 0.52))
        copy.append(_btn_row([_btn(props.get("cta_label", "Ask for a quote"),
                                   props.get("cta_url", "/contact/"), "solid")]))
        h = it.get("image_height", 440)
        kids = [_shot(it.get("image"), h)]
        if it.get("chip"):
            kids.append(_float(_chip(it["chip"], it.get("chip_icon"),
                                     it.get("chip_tone", "white")),
                               "start", "end", 16, 16))
        frame = _frame(kids, h, extra={"min_height_tablet": slider(340),
                                        "min_height_mobile": slider(260)})
        w = _tracks([1, 1.1], 56)
        pair = [_col([frame], w[0]), _col(copy, w[1], extra={"flex_gap": gap(14)})]
        if n % 2 == 0:
            pair.reverse()
        rows.append(_sec([_row(pair, 56, align="center")],
                         "pale" if n % 2 == 0 else "white",
                         anchor=it.get("slug")))
    return container(rows, {"content_width": "full", "flex_direction": "column",
                            "flex_gap": gap(0), "padding": dims(0, 0, 0, 0)})


@block("ez.faq")
def ez_faq(props):
    bg = props.get("bg", "white")
    acc = _faq(props.get("items", []), True)
    acc["settings"]["faq_schema"] = "yes"
    head = _head({**{k: props.get(k) for k in ("eyebrow", "title", "intro")},
                  "intro_width": 100}, False, "left")
    w = _tracks([0.8, 1.2], 56)
    row = _row([_col(head, w[0]), _col([acc], w[1])], 56, align="flex-start")
    return _sec([row], bg, anchor=props.get("anchor", "faq"))


@block("ez.cta")
def ez_cta(props):
    # On the deep blue the mist grey drops to ~2.3:1, so the eyebrow, its tab
    # and the paragraph go white.
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], True, "center", color=C["white"]))
    kids.append(_h(props["title"], "h2", T["h_large"], "center", True))
    if props.get("text"):
        kids.append(container([_p(props["text"], "center", True,
                                  color=C["white"])], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(64, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    btns = [_btn(props.get("cta_label", "Get a Quote"),
                 props.get("cta_url", "/contact/"), "light")]
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props.get("alt_url", "#"),
                         "ghost_d", ""))
    kids.append(_btn_row(btns, "center"))
    sec = _sec(kids, "deep", pad=dims(118, 0, 96, 0),
               extra={"flex_align_items": "center",
                      "padding_tablet": dims(92, 24, 72, 24),
                      "padding_mobile": dims(78, 18, 60, 18)})
    return _angle(sec, "top", 44)


def _is_placeholder(v):
    return isinstance(v, str) and v.strip().startswith("[")


@block("ez.contactcards")
def ez_contactcards(props):
    kids = _head(props, False, "left")
    items = props.get("items", [])
    cols = props.get("columns", len(items) or 1)
    w = _tracks([1] * cols, 24)[0]
    cards = []
    for it in items:
        body = [widget("icon", {
            "selected_icon": icon(it.get("icon", "fas fa-circle")),
            "size": slider(20), "align": "left", "view": "stacked",
            "shape": "square", "icon_padding": slider(12),
        }, globals_={"primary_color": color_ref(C["surface_alt"]),
                     "secondary_color": color_ref(DEEP)}),
            widget("heading", {
                "title": it.get("label", ""), "header_size": "div",
                "align": "left"},
                globals_={"title_color": color_ref(C["muted"]),
                          "typography_typography": typo_ref(T["eyebrow"])})]
        val = it.get("value", "")
        if _is_placeholder(val):
            body.append(container([widget("heading", {
                "title": val, "header_size": "div", "align": "left"},
                globals_={"title_color": color_ref(AMBER_INK),
                          "typography_typography": typo_ref(T["meta"])})], {
                "content_width": "full", "flex_direction": "column",
                "padding": dims(8, 10, 8, 10), "border_radius": box(4),
                "background_background": "classic"},
                globals_={"background_color": color_ref(AMBER)}))
        else:
            v = widget("heading", {
                "title": val, "header_size": "div", "align": "left"},
                globals_={"title_color": color_ref(NAVY),
                          "typography_typography": typo_ref(T["h_small"])})
            if it.get("href"):
                v["settings"]["link"] = link(it["href"],
                                             external=it["href"].startswith("http"))
            body.append(v)
        if it.get("text"):
            body.append(_p(it["text"], small=True))
        cards.append(_card(body, w, extra={
            "width_tablet": slider(_tracks([1, 1], 24, 720)[0], "%")}))
    kids.append(_row(cards, 24, align="stretch", extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "pale"), anchor=props.get("anchor"))


@block("ez.form")
def ez_form(props):
    f = props.get("form", {})
    fields = []
    for fl in f.get("fields", []):
        item = {"custom_id": fl.get("id", "field"),
                "field_type": fl.get("type", "text"),
                "field_label": fl.get("label", ""),
                "placeholder": fl.get("placeholder", ""),
                "required": "true" if fl.get("required") else "",
                "width": str(fl.get("width", 100))}
        if fl.get("options"):
            item["field_options"] = chr(10).join(fl["options"])
        if fl.get("rows"):
            item["rows"] = fl["rows"]
        if fl.get("acceptance_text"):
            item["acceptance_text"] = fl["acceptance_text"]
        fields.append(repeater_item(**item))

    form = widget("form", {
        "form_name": f.get("form_name", "Quote request"),
        "form_fields": fields,
        "submit_actions": ["email"],
        # Left EMPTY on purpose. No business email was supplied, and an
        # Elementor form with an empty "To" falls back to the WordPress
        # admin address - a working inbox - where a placeholder string would
        # make every enquiry fail silently.
        "email_to": f.get("email", ""),
        "email_subject": f.get("subject", "New quote request"),
        "button_text": f.get("submit", "Send"),
        "button_size": "md", "button_width": "100", "input_size": "md",
        "show_labels": "yes", "mark_required": "yes",
        "row_gap": slider(14), "column_gap": slider(12),
        "success_message": f.get("success", ""),
        "error_message": f.get("error", ""),
        "required_field_message": f.get("required", ""),
        "field_border_radius": box(4), "field_border_width": box(1),
        "button_border_radius": R_BTN,
    }, globals_={
        "button_background_color": color_ref(DEEP),
        "button_text_color": color_ref(C["white"]),
        "button_background_hover_color": color_ref(NAVY),
        "button_hover_color": color_ref(C["white"]),
        "field_background_color": color_ref(C["white"]),
        "field_text_color": color_ref(NAVY),
        "field_border_color": color_ref(C["border"]),
        "label_color": color_ref(NAVY),
        "mark_required_color": color_ref(DEEP),
    })

    card_kids = [_h(props.get("title", ""), "h2", T["h_medium"])]
    if props.get("intro"):
        card_kids.append(_p(props["intro"], small=True))
    card_kids.append(form)
    if props.get("privacy_note"):
        card_kids.append(_p(props["privacy_note"], small=True))
    card = _card(card_kids, lift=False, pad=dims(36, 34, 38, 34),
                 extra={"flex_gap": gap(16), **CARD_SHADOW})

    side = props.get("side")
    if side:
        sk = _head({k: side.get(k) for k in ("eyebrow", "title")})
        for p in side.get("paragraphs", []):
            sk.append(_p(p))
        if side.get("list_title"):
            sk.append(_h(side["list_title"], "h3", T["h_small"]))
        if side.get("ticks"):
            sk.append(_ticks(side["ticks"], container_px=KIT_CONTAINER * 0.45))
        w = _tracks([0.9, 1.1], 56)
        body = _row([_col(sk, w[0], extra={"flex_gap": gap(16)}),
                     _col([card], w[1])], 56, align="flex-start")
    else:
        body = container([card], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(72, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")})
    return _sec([body], props.get("bg", "white"),
                anchor=props.get("anchor", "quote"))


@block("ez.notice")
def ez_notice(props):
    """The amber 'complete before publishing' banner on the legal pages.
    It is its own section so it can be deleted in one click once the
    placeholders are filled."""
    box_ = container([
        widget("icon", {"selected_icon": icon("fas fa-triangle-exclamation"),
                        "size": slider(20), "align": "left", "view": "default"},
               globals_={"primary_color": color_ref(AMBER_INK)}),
        container([
            widget("heading", {"title": props["title"], "header_size": "div",
                               "align": "left"},
                   globals_={"title_color": color_ref(AMBER_INK),
                             "typography_typography": typo_ref(T["h_small"])}),
            _text(props["text"], small=True),
        ], {"content_width": "full", "flex_direction": "column",
            "flex_gap": gap(6)}),
    ], {"content_width": "full", "flex_direction": "row",
        "flex_direction_mobile": "row", "flex_wrap": "nowrap",
        "flex_gap": gap(14), "flex_align_items": "flex-start",
        "padding": dims(20, 22, 20, 22), "border_radius": R_CARD,
        "border_border": "solid", "border_width": dims(0, 0, 0, 4),
        "background_background": "classic"},
        globals_={"background_color": color_ref(AMBER),
                  "border_color": color_ref(AMBER_INK)})
    box_["elements"][1]["elements"][1]["settings"]["__globals__"]["text_color"] = \
        color_ref(AMBER_INK)
    return _sec([container([box_], {
        "content_width": "full", "flex_direction": "column",
        "width": slider(78, "%"), "width_tablet": slider(100, "%"),
        "margin": dims(0, "auto", 0, "auto")})], "white",
        pad=dims(48, 0, 0, 0), extra={"padding_tablet": dims(36, 24, 0, 24),
                                       "padding_mobile": dims(28, 18, 0, 18)})


@block("ez.legal")
def ez_legal(props):
    """A legal document in a narrow reading column. Placeholders are written
    as <mark>[...]</mark> in the copy so they show up highlighted on the page
    and cannot be mistaken for finished text."""
    kids = []
    if props.get("lead"):
        kids.append(_p(props["lead"]))
    for s in props.get("sections", []):
        kids.append(_h(s["title"], "h2", T["h_medium"]))
        for p in s.get("paragraphs", []):
            kids.append(_p(p))
    if props.get("updated"):
        kids.append(_p(props["updated"], small=True))
    col = container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(14),
        "width": slider(78, "%"), "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"),
        "margin": dims(0, "auto", 0, "auto")})
    return _sec([col], "white", pad=dims(56, 0, 96, 0))
