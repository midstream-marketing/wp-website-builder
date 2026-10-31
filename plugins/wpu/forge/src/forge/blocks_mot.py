"""
blocks_mot.py — MODELS ON TOUR, a German-language model booking marketplace.

Matched to two supplied mockup sheets covering seven screens. Palette,
grounds, card anatomy and control shapes are read off the pixels.

    #F9046D  hot pink — the accent, as TEXT, rules, icons and eyebrows
    #E31B72  the same pink deepened — BUTTON FILLS only
    #02090D  page ground, near-black
    #0C1016  cards and tiles
    #0A1015  form fields and filter controls
    #1A222B  hairlines

WHY THE PINK IS TWO VALUES. White on the brand pink #F9046D is 3.99:1 —
over the large-text bar, under the 4.5 that the small caps labels on these
buttons actually need. The brand pink as TEXT on the near-black page is
5.03:1 and perfectly fine. So the accent stays #F9046D everywhere it is
type, and button FILLS use #E31B72 where white reaches exactly 4.50:1. The
two are visually near-identical; the design does not change. Same split
economy-roofing made with its orange.

THE REGISTRY CONSTRAINT. loop-grid's query controls and the dynamic tags
are not in this repo's registry, so the model and event cards are built as
STATIC tiles reproducing the mockup exactly rather than as an unverified
loop-item that would risk importing empty. Once the custom post types
exist these become a loop; the tile markup is the design reference for it,
and BUILD-NOTES.md says how.

Everything is in GERMAN, including the umlauts, because the copy is the
client's. The four English script accents are theirs too and are kept.

    mot.header      two-tone wordmark, nav, search, BOOK A MODEL
    mot.hero        full-bleed photo under a directional gradient
    mot.pagehero    the shorter inner-page variant
    mot.script      the handwritten accent, floated       ← device
    mot.citystrip   cities with live model counts
    mot.sectionhead pink caps eyebrow, heading, optional link
    mot.modelgrid   the model tile                        ← signature
    mot.eventgrid   the event tile
    mot.featured    the large featured-event panel
    mot.filterbar   search + two selects + FILTERN
    mot.availability the Verfügbarkeit date row
    mot.booking     Termin auswählen, chips, total, trust
    mot.modelhead   the model detail header and bio
    mot.steps       the four numbered steps with rules
    mot.applyform   the For Models application panel
    mot.cards       photo cards with a pink icon
    mot.stats       the three-up figures band
    mot.split       photo beside copy
    mot.benefits    icon + title + text list
    mot.cta         closing band
    mot.footer      wordmark, columns, legal links
"""
from __future__ import annotations

from .core import (
    container, widget, repeater_item, slider, dims, box, media, link,
    gap, color_ref, typo_ref, icon,
)
from .tokens import C, T
from .blocks import (
    block, _row, _col, _tracks, _button, _heading, _text, _faq, KIT_CONTAINER,
)

PINK = "primary"        # #F9046D — accent as TYPE
PINK_FILL = "secondary"  # #E31B72 — button fills, white label at 4.50
PAGE = C["surface"]      # #02090D
CARD = C["surface_alt"]  # #0C1016
FIELD = "motfld1"       # #0A1015
PINK_DEEP = "motpnk2"   # #C01160 — hover
INK = "motink1"         # #06090D
GREEN = "motgrn1"       # #3DDC6E — the availability dot

MOT_PAD = dims(76, 0, 76, 0)
MOT_PAD_T = dims(56, 22, 56, 22)
MOT_PAD_M = dims(42, 16, 42, 16)
R_CARD = box(10)
R_PILL = box(999)
GUTTER = 18

SHADOW = {
    "box_shadow_box_shadow_type": "yes",
    "box_shadow_box_shadow": {"horizontal": 0, "vertical": 8, "blur": 24,
                              "spread": -8, "color": "rgba(0, 0, 0, 0.6)"},
}
SHADOW_HOVER = {
    "box_shadow_hover_box_shadow_type": "yes",
    "box_shadow_hover_box_shadow": {"horizontal": 0, "vertical": 16,
                                    "blur": 38, "spread": -10,
                                    "color": "rgba(249, 4, 109, 0.30)"},
}
SHADOW_LIFTED = {
    "box_shadow_box_shadow_type": "yes",
    "box_shadow_box_shadow": {"horizontal": 0, "vertical": 22, "blur": 54,
                              "spread": -14, "color": "rgba(0, 0, 0, 0.75)"},
}


# ───────────────────────────────── helpers ─────────────────────────────────

def _sec(children, bg="page", pad=None, anchor=None, extra=None):
    grounds = {"page": PAGE, "card": CARD, "field": FIELD}
    s = {
        "content_width": "boxed",
        "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "flex_gap": gap(22),
        "padding": pad or MOT_PAD,
        "padding_tablet": MOT_PAD_T,
        "padding_mobile": MOT_PAD_M,
        "background_background": "classic",
    }
    if anchor:
        s["_element_id"] = anchor
    if extra:
        s.update(extra)
    return container(children, s, globals_={
        "background_color": color_ref(grounds.get(bg, PAGE))})


def _card(kids, width=None, pad=None, tone=None, hover=True, lifted=False,
          extra=None):
    s = {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(9),
        "padding": pad or dims(16, 16, 18, 16),
        "border_radius": R_CARD,
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
    }
    s.update(SHADOW_LIFTED if lifted else SHADOW)
    if hover:
        s.update(SHADOW_HOVER)
    if width:
        s.update({"width": slider(width, "%"),
                  "width_mobile": slider(100, "%")})
    if extra:
        s.update(extra)
    return container(kids, s, globals_={
        "background_color": color_ref(tone or CARD),
        "border_color": color_ref(C["border"])})


def _h(text, size="h2", token=None, align="left", tone=None):
    return widget("heading", {
        "title": text, "header_size": size, "align": align,
        "__typography__": typo_ref(token or T["h_medium"]),
    }, globals_={"title_color": color_ref(tone or C["white"])})


def _small(text, align="left", tone=None):
    return widget("heading", {
        "title": text, "header_size": "div", "align": align,
        "__typography__": typo_ref(T["body_small"]),
    }, globals_={"title_color": color_ref(tone or C["muted"])})


def _eyebrow(text, align="left"):
    return widget("heading", {
        "title": text, "header_size": "div", "align": align,
        "__typography__": typo_ref(T["eyebrow"]),
    }, globals_={"title_color": color_ref(PINK)})


@block("mot.script")
def mot_script(props):
    """The handwritten accent the mockups float over the photography -
    'Deine Vorteile', 'Good Shots Only', 'Your Next Stop',
    'Create Network Shoot'. Set in Caveat; swap the family if the client
    has the real lettering."""
    return _script(props.get("text", ""), props.get("align", "right"))


def _script(text, align="right", size=None):
    return widget("heading", {
        "title": text, "header_size": "div", "align": align,
        "__typography__": typo_ref(size or T["h_medium"]),
    }, globals_={"title_color": color_ref(PINK)})


def _btn(label, href, style="pink", icon_name=None, full=False):
    """Three buttons, all fully rounded pills - there is not a square
    button anywhere in the mockups.

        pink    #E31B72 fill, WHITE label. Deeper than the brand pink
                because white on #F9046D is 3.99:1 and these labels are
                small caps.
        outline white hairline, white label
        ghost   pink hairline, pink label - the BOOK buttons on listing
                cards and DETAILS & BUCHEN
    """
    b = _button(label, href, "primary", icon_name or "")
    b["settings"].update({
        "border_radius": R_PILL,
        "text_padding": dims(13, 26, 13, 26),
        "__typography__": typo_ref(T["meta"]),
        "hover_animation": "grow",
        "button_box_shadow_box_shadow_type": "yes",
        "button_box_shadow_box_shadow": {
            "horizontal": 0, "vertical": 6, "blur": 18, "spread": -6,
            "color": "rgba(249, 4, 109, 0.45)"},
    })
    if full:
        b["settings"]["align"] = "justify"
    g = b["settings"].setdefault("__globals__", {})
    if style == "outline":
        b["settings"].update({"border_border": "solid", "border_width": box(1)})
        g.update({"background_color": color_ref(C["transparent"]),
                  "border_color": color_ref(C["white"]),
                  "button_text_color": color_ref(C["white"]),
                  "button_background_hover_color": color_ref(C["white"]),
                  "button_hover_border_color": color_ref(C["white"]),
                  "hover_color": color_ref(INK)})
    elif style == "ghost":
        b["settings"].update({"border_border": "solid", "border_width": box(1)})
        g.update({"background_color": color_ref(C["transparent"]),
                  "border_color": color_ref(PINK),
                  "button_text_color": color_ref(PINK),
                  "button_background_hover_color": color_ref(PINK_FILL),
                  "button_hover_border_color": color_ref(PINK_FILL),
                  "hover_color": color_ref(C["white"])})
    else:
        g.update({"background_color": color_ref(PINK_FILL),
                  "border_color": color_ref(PINK_FILL),
                  "button_text_color": color_ref(C["white"]),
                  "button_background_hover_color": color_ref(PINK_DEEP),
                  "button_hover_border_color": color_ref(PINK_DEEP),
                  "hover_color": color_ref(C["white"])})
    return b


def _chip(label, active=False, tone_active=None):
    return container([widget("heading", {
        "title": label, "header_size": "div", "align": "center",
        "__typography__": typo_ref(T["body_small"]),
    }, globals_={"title_color": color_ref(
        C["white"] if active else C["muted"])})], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(8, 14, 8, 14), "border_radius": box(6),
        "_flex_shrink": "0",
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
    }, globals_={
        "background_color": color_ref(
            (tone_active or PINK_FILL) if active else FIELD),
        "border_color": color_ref(
            (tone_active or PINK_FILL) if active else C["border"])})


def _tagline(tags):
    """The dot-separated style line: Fashion · Editorial · Lifestyle."""
    return _small(" · ".join(tags), tone=C["muted"])


def _dot(tone=None):
    return container([], {
        "content_width": "full", "min_height": slider(7), "width": slider(7),
        "_flex_shrink": "0", "border_radius": box(999),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(tone or GREEN)})


def _frame(height=220, label=None, radius=box(8)):
    """An empty, styled image frame. NO STOCK AND NO AI FACES anywhere in
    this kit - a booking platform whose product IS the models cannot show
    people who are not on its books."""
    kids = [_small(label, "center")] if label else []
    return container(kids, {
        "content_width": "full", "min_height": slider(height),
        "flex_direction": "column",
        "flex_justify_content": "center", "flex_align_items": "center",
        "border_radius": radius, "border_border": "dashed",
        "border_width": box(1), "background_background": "classic",
    }, globals_={"background_color": color_ref(FIELD),
                 "border_color": color_ref(C["border"])})


def _shot(image, height=220, radius=box(8), label=None):
    if image and image.get("url"):
        return widget("image", {
            "image": media(image["url"], image.get("alt", "")),
            "image_size": "full", "width": slider(100, "%"),
            "height": slider(height), "object-fit": "cover",
            "align": "center", "image_border_radius": radius})
    return _frame(height, label, radius)


def _field(placeholder, icon_name=None):
    kids = []
    if icon_name:
        kids.append(widget("icon", {
            "selected_icon": icon(icon_name), "size": slider(13),
            "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref(C["muted"])}))
    kids.append(_small(placeholder))
    return container([_row(kids, 9, align="center",
                           extra={"flex_wrap": "nowrap",
                                  "flex_direction_mobile": "row"})], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(12, 14, 12, 14), "border_radius": box(8),
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(FIELD),
                 "border_color": color_ref(C["border"])})


def _select(placeholder, icon_name=None):
    kids = []
    if icon_name:
        kids.append(widget("icon", {
            "selected_icon": icon(icon_name), "size": slider(13),
            "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref(C["muted"])}))
    kids.append(_small(placeholder))
    inner = _row([
        _row(kids, 9, align="center",
             extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"}),
        widget("icon", {
            "selected_icon": icon("fas fa-chevron-down"), "size": slider(10),
            "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref(C["muted"])}),
    ], 8, align="center", justify="space-between",
        extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})
    return container([inner], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(12, 14, 12, 14), "border_radius": box(8),
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(FIELD),
                 "border_color": color_ref(C["border"])})


def _head_stack(props, align="left"):
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], align))
    if props.get("title"):
        kids.append(_h(props["title"], props.get("tag", "h2"),
                       T["h_medium"], align))
    if props.get("intro"):
        kids.append(container([_text(props["intro"], align, on_dark=True,
                                     small=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(props.get("intro_width", 68), "%"),
            "width_mobile": slider(100, "%"),
            "margin": (dims(0, "auto", 0, "auto") if align == "center"
                       else dims(0, 0, 0, 0))}))
    if not kids:
        return []
    return [container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(10),
        "flex_align_items": "center" if align == "center" else "flex-start"})]


# ─────────────────────────────── chrome ────────────────────────────────────

@block("mot.header")
def mot_header(props):
    """MODELS in white, ON TOUR in pink, set as type exactly as the mockup
    draws it."""
    brand = _row([
        widget("heading", {
            "title": props.get("brand_a", "MODELS"), "header_size": "div",
            "align": "left", "link": link("/"),
            "__typography__": typo_ref(T["wordmark"]),
        }, globals_={"title_color": color_ref(C["white"])}),
        widget("heading", {
            "title": props.get("brand_b", "ON TOUR"), "header_size": "div",
            "align": "left", "__typography__": typo_ref(T["wordmark"]),
        }, globals_={"title_color": color_ref(PINK)}),
    ], 7, align="baseline",
        extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})

    nav = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"),
        "layout": "horizontal", "align_items": "center",
        "pointer": "underline", "animation_line": "fade",
        "menu_space_between": slider(props.get("nav_gap", 22)),
        "toggle_align": "right",
        "__typography__": typo_ref(T["meta"]),
    }, globals_={
        "color_menu_item": color_ref(C["white"]),
        "color_menu_item_hover": color_ref(PINK),
        "color_menu_item_active": color_ref(PINK),
        "pointer_color_menu_item_hover": color_ref(PINK),
        "pointer_color_menu_item_active": color_ref(PINK),
        "toggle_color": color_ref(C["white"]),
    })

    actions = [widget("icon", {
        "selected_icon": icon("fas fa-magnifying-glass"), "size": slider(14),
        "align": "center", "view": "default",
        "link": link(props.get("search_url", "/models/")),
    }, globals_={"primary_color": color_ref(C["white"])})]
    if props.get("cta_label"):
        actions.append(_btn(props["cta_label"],
                            props.get("cta_url", "/models/"), "pink"))

    row = _row([
        _col([brand], 26, extra={"flex_justify_content": "center"}),
        _col([nav], 44, extra={"flex_justify_content": "center",
                               "flex_align_items": "center"}),
        _col([_row(actions, 14, align="center", justify="flex-end",
                   extra={"flex_wrap": "nowrap"})], 30,
             extra={"flex_justify_content": "center",
                    "flex_align_items": "flex-end"}),
    ], GUTTER, align="center",
        extra={"flex_wrap": "nowrap", "flex_wrap_tablet": "wrap"})

    return container([row], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "padding": dims(14, 0, 14, 0),
        "padding_mobile": dims(10, 14, 10, 14),
        "background_background": "classic",
        "sticky": "top", "sticky_on": ["desktop", "tablet", "mobile"],
        "sticky_offset": 0,
    }, globals_={"background_color": color_ref(PAGE)})


@block("mot.footer")
def mot_footer(props):
    brand = [_row([
        widget("heading", {
            "title": props.get("brand_a", "MODELS"), "header_size": "div",
            "align": "left", "__typography__": typo_ref(T["wordmark"]),
        }, globals_={"title_color": color_ref(C["white"])}),
        widget("heading", {
            "title": props.get("brand_b", "ON TOUR"), "header_size": "div",
            "align": "left", "__typography__": typo_ref(T["wordmark"]),
        }, globals_={"title_color": color_ref(PINK)}),
    ], 7, align="baseline",
        extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})]
    if props.get("script"):
        brand.append(_script(props["script"], "left"))
    if props.get("blurb"):
        brand.append(_text(props["blurb"], "left", on_dark=True, small=True))

    cols = props.get("columns", [])
    widths = _tracks([1.5] + [1] * len(cols), GUTTER)
    body = [_col(brand, widths[0], extra={"flex_gap": gap(12)})]
    for i, c in enumerate(cols):
        kids = [widget("heading", {
            "title": c.get("title", ""), "header_size": "div", "align": "left",
            "__typography__": typo_ref(T["eyebrow"]),
        }, globals_={"title_color": color_ref(PINK)})]
        for l in c.get("links", []):
            r = []
            if l.get("icon"):
                r.append(widget("icon", {
                    "selected_icon": icon(l["icon"]), "size": slider(12),
                    "align": "center", "view": "default",
                }, globals_={"primary_color": color_ref(PINK)}))
            lab = widget("heading", {
                "title": l.get("label", ""), "header_size": "div",
                "align": "left", "__typography__": typo_ref(T["body_small"]),
            }, globals_={"title_color": color_ref(C["muted"])})
            if l.get("url"):
                lab["settings"]["link"] = link(l["url"])
            r.append(lab)
            kids.append(_row(r, 9, align="center",
                             extra={"flex_wrap": "nowrap",
                                    "flex_direction_mobile": "row",
                                    "padding": dims(4, 0, 4, 0)}))
        body.append(_col(kids, widths[i + 1], extra={"flex_gap": gap(6)}))

    rule = container([], {
        "content_width": "full", "min_height": slider(1),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["border"])})

    return container([
        _row(body, GUTTER, align="flex-start", extra={"flex_wrap": "wrap"}),
        rule,
        _small(props.get("copyright", ""), "center"),
    ], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column", "flex_gap": gap(22),
        "padding": dims(60, 0, 28, 0),
        "padding_mobile": dims(44, 16, 22, 16),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(PAGE)})


# ─────────────────────────────── sections ──────────────────────────────────

def _photo_section(kids, props, pad, height, overlay=0.72, anchor=None):
    """A full-bleed photograph under a directional dark gradient, so the
    headline sits on the dark side rather than over the subject. That
    gradient is why the generic heroes are banned."""
    sec = _sec(kids, "page", pad=pad, anchor=anchor,
               extra={"min_height": slider(height),
                      "flex_justify_content": "center"})
    img = props.get("image")
    if img and img.get("url"):
        sec["settings"].update({
            "background_image": media(img["url"], img.get("alt", "")),
            "background_position": props.get("position", "center right"),
            "background_size": "cover", "background_repeat": "no-repeat",
            "background_overlay_background": "gradient",
            "background_overlay_gradient_type": "linear",
            "background_overlay_gradient_angle": slider(90, "deg"),
            "background_overlay_color_stop": slider(10, "%"),
            "background_overlay_color_b_stop": slider(95, "%"),
            "background_overlay_opacity": slider(props.get("overlay",
                                                           overlay)),
        })
        sec["settings"].setdefault("__globals__", {}).update({
            "background_overlay_color": color_ref(PAGE),
            "background_overlay_color_b": color_ref(C["transparent"]),
        })
    else:
        sec["settings"]["border_border"] = "dashed"
        sec["settings"]["border_width"] = box(1)
        sec["settings"].setdefault("__globals__", {})[
            "border_color"] = color_ref(C["border"])
    return sec


@block("mot.hero")
def mot_hero(props):
    kids = []
    if props.get("title"):
        kids.append(_h(props["title"], props.get("tag", "h1"), T["hero"],
                       "left"))
    if props.get("standfirst"):
        kids.append(widget("heading", {
            "title": props["standfirst"], "header_size": "div",
            "align": "left", "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(
            PINK if props.get("standfirst_pink") else C["white"])}))
    if props.get("intro"):
        kids.append(container([_text(props["intro"], "left", on_dark=True,
                                     small=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(props.get("intro_width", 62), "%"),
            "width_mobile": slider(100, "%")}))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"),
                         "pink"))
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props.get("alt_url", "#"),
                         "outline"))
    if btns:
        kids.append(_row(btns, 12, align="center",
                         extra={"flex_wrap": "wrap",
                                "padding": dims(10, 0, 0, 0)}))
    if props.get("script"):
        kids.append(_script(props["script"], "right"))
    col = _col(kids, props.get("width", 58), extra={"flex_gap": gap(16)})
    return _photo_section([_row([col], GUTTER, align="center")], props,
                          dims(props.get("pad_top", 92), 0,
                               props.get("pad_bottom", 92), 0),
                          props.get("height", 460),
                          anchor=props.get("anchor"))


@block("mot.pagehero")
def mot_pagehero(props):
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"]))
    if props.get("title"):
        kids.append(_h(props["title"], props.get("tag", "h1"), T["h_large"],
                       "left"))
    if props.get("intro"):
        kids.append(container([_text(props["intro"], "left", on_dark=True,
                                     small=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(props.get("intro_width", 62), "%"),
            "width_mobile": slider(100, "%")}))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"),
                         "pink"))
    if btns:
        kids.append(_row(btns, 12, align="center",
                         extra={"flex_wrap": "wrap",
                                "padding": dims(8, 0, 0, 0)}))
    if props.get("script"):
        kids.append(_script(props["script"], "right"))
    col = _col(kids, props.get("width", 62), extra={"flex_gap": gap(12)})
    return _photo_section([_row([col], GUTTER, align="center")], props,
                          dims(66, 0, 66, 0), props.get("height", 300),
                          anchor=props.get("anchor"))


@block("mot.citystrip")
def mot_citystrip(props):
    """Cities with live model counts, closing with the pink live marker."""
    cells = []
    for it in props.get("items", []):
        cells.append(_row([
            widget("icon", {
                "selected_icon": icon(it.get("icon", "fas fa-location-dot")),
                "size": slider(13), "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref(PINK)}),
            container([
                widget("heading", {
                    "title": it.get("label", ""), "header_size": "div",
                    "align": "left", "__typography__": typo_ref(T["meta"]),
                }, globals_={"title_color": color_ref(C["white"])}),
                _small(it.get("note", "")),
            ], {"content_width": "full", "flex_direction": "column",
                "flex_gap": gap(2)}),
        ], 9, align="center",
            extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"}))
    if props.get("live_label"):
        cells.append(_row([
            _dot(PINK),
            container([
                widget("heading", {
                    "title": props["live_label"], "header_size": "div",
                    "align": "left", "__typography__": typo_ref(T["meta"]),
                }, globals_={"title_color": color_ref(PINK)}),
                _small(props.get("live_note", "")),
            ], {"content_width": "full", "flex_direction": "column",
                "flex_gap": gap(2)}),
        ], 9, align="center",
            extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"}))
    strip = container([_row(cells, 26, align="center", justify="space-between",
                            extra={"flex_wrap": "wrap"})], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(16, 18, 16, 18), "border_radius": R_CARD,
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic", **SHADOW,
    }, globals_={"background_color": color_ref(CARD),
                 "border_color": color_ref(C["border"])})
    return _sec([strip], "page", pad=dims(0, 0, 30, 0),
                anchor=props.get("anchor"))


@block("mot.sectionhead")
def mot_sectionhead(props):
    left = _head_stack(props, props.get("align", "left"))
    if props.get("link_label"):
        lab = widget("heading", {
            "title": props["link_label"], "header_size": "div",
            "align": "right", "__typography__": typo_ref(T["meta"]),
            "link": link(props.get("link_url", "#")),
        }, globals_={"title_color": color_ref(PINK)})
        wl, wr = _tracks([1, 0.34], GUTTER)
        row = _row([_col(left, wl), _col([lab], wr,
                                         extra={"flex_justify_content":
                                                "flex-end"})],
                   GUTTER, align="flex-end", extra={"flex_wrap": "wrap"})
        kids = [row]
    else:
        kids = left
    for p in props.get("paragraphs", []):
        kids.append(_text(p, props.get("align", "left"), on_dark=True,
                          small=True))
    return _sec(kids, props.get("bg", "page"),
                pad=props.get("tight") and dims(50, 0, 18, 0) or
                dims(60, 0, 20, 0), anchor=props.get("anchor"))


@block("mot.modelgrid")
def mot_modelgrid(props):
    """THE SIGNATURE TILE. Portrait, a city pill OR a green-dot availability
    row with a date range, a heart top-right, the name, a dot-separated
    style line, a price and a BOOK button.

    Static, because the registry has no dynamic tags for a custom post type
    - an unverified loop-item would risk importing empty, which on a
    marketplace reads as "no models" rather than as a template bug.
    """
    kids = _head_stack(props, props.get("align", "left")) \
        if props.get("title") else []
    per = props.get("columns", 4)
    w = _tracks([1] * per, GUTTER)[0]
    cells = []
    for it in props.get("items", []):
        top = []
        if it.get("available"):
            top.append(_row([
                _dot(), _small(it["available"], tone=C["white"]),
            ], 7, align="center",
                extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"}))
        elif it.get("city"):
            top.append(container([_row([
                widget("icon", {
                    "selected_icon": icon("fas fa-location-dot"),
                    "size": slider(10), "align": "center", "view": "default",
                }, globals_={"primary_color": color_ref(PINK)}),
                widget("heading", {
                    "title": it["city"], "header_size": "div",
                    "align": "left", "__typography__": typo_ref(T["eyebrow"]),
                }, globals_={"title_color": color_ref(C["white"])}),
            ], 6, align="center",
                extra={"flex_wrap": "nowrap",
                       "flex_direction_mobile": "row"})], {
                "content_width": "full", "flex_direction": "column",
                "padding": dims(4, 9, 4, 9), "border_radius": box(4),
                "_flex_shrink": "0", "background_background": "classic",
            }, globals_={"background_color": color_ref(PAGE)}))
        heart = widget("icon", {
            "selected_icon": icon("far fa-heart"), "size": slider(13),
            "align": "right", "view": "default",
        }, globals_={"primary_color": color_ref(C["white"])})
        if top:
            head = _row([top[0], heart], 8, align="center",
                        justify="space-between",
                        extra={"flex_wrap": "nowrap",
                               "flex_direction_mobile": "row"})
        else:
            head = _row([heart], 8, align="center", justify="flex-end",
                        extra={"flex_wrap": "nowrap"})

        body = [head, _shot(it.get("image"), props.get("shot", 230),
                            label=it.get("frame_label"))]
        body.append(widget("heading", {
            "title": it.get("name", ""), "header_size": "h3", "align": "left",
            "__typography__": typo_ref(T["h_small"]),
            "link": link(it.get("url", "#")),
        }, globals_={"title_color": color_ref(C["white"])}))
        if it.get("tags"):
            body.append(_tagline(it["tags"]))
        actions = []
        if it.get("price"):
            actions.append(widget("heading", {
                "title": it["price"], "header_size": "div", "align": "left",
                "__typography__": typo_ref(T["meta"]),
            }, globals_={"title_color": color_ref(C["white"])}))
        if it.get("cta_label"):
            actions.append(_btn(it["cta_label"], it.get("url", "#"),
                                it.get("cta_style", "pink")))
        if actions:
            body.append(_row(actions, 8, align="center",
                             justify="space-between",
                             extra={"flex_wrap": "wrap",
                                    "flex_direction_mobile": "row"}))
        cells.append(_card(body, w, pad=dims(12, 12, 14, 12)))
    kids.append(_row(cells, GUTTER, align="stretch",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "page"), pad=dims(0, 0, 40, 0),
                anchor=props.get("anchor"))


@block("mot.eventgrid")
def mot_eventgrid(props):
    kids = _head_stack(props, props.get("align", "left")) \
        if props.get("title") else []
    per = props.get("columns", 3)
    w = _tracks([1] * per, GUTTER)[0]
    cells = []
    for it in props.get("items", []):
        body = [_shot(it.get("image"), props.get("shot", 150),
                      label=it.get("frame_label"))]
        if it.get("when"):
            body.append(_small(it["when"], tone=PINK))
        body.append(widget("heading", {
            "title": it.get("title", ""), "header_size": "h3", "align": "left",
            "__typography__": typo_ref(T["h_small"]),
            "link": link(it.get("url", "#")),
        }, globals_={"title_color": color_ref(C["white"])}))
        if it.get("meta"):
            body.append(_small(it["meta"]))
        foot = []
        if it.get("price"):
            foot.append(widget("heading", {
                "title": it["price"], "header_size": "div", "align": "left",
                "__typography__": typo_ref(T["meta"]),
            }, globals_={"title_color": color_ref(C["white"])}))
        foot.append(widget("icon", {
            "selected_icon": icon("fas fa-chevron-right"), "size": slider(11),
            "align": "right", "view": "default",
            "link": link(it.get("url", "#")),
        }, globals_={"primary_color": color_ref(PINK)}))
        body.append(_row(foot, 8, align="center", justify="space-between",
                         extra={"flex_wrap": "nowrap",
                                "flex_direction_mobile": "row"}))
        cells.append(_card(body, w, pad=dims(12, 12, 14, 12)))
    kids.append(_row(cells, GUTTER, align="stretch",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "page"), pad=dims(0, 0, 40, 0),
                anchor=props.get("anchor"))


@block("mot.featured")
def mot_featured(props):
    """The large featured-event panel: photo left, pink date pill, title,
    meta, body, Ab-price and a ghost button."""
    right = []
    if props.get("when"):
        right.append(container([widget("heading", {
            "title": props["when"], "header_size": "div", "align": "center",
            "__typography__": typo_ref(T["eyebrow"]),
        }, globals_={"title_color": color_ref(C["white"])})], {
            "content_width": "full", "flex_direction": "column",
            "padding": dims(5, 11, 5, 11), "border_radius": box(4),
            "_flex_shrink": "0", "background_background": "classic",
        }, globals_={"background_color": color_ref(PINK_FILL)}))
    if props.get("title"):
        right.append(_h(props["title"], "h3", T["h_medium"], "left"))
    if props.get("meta"):
        right.append(_small(props["meta"], tone=PINK))
    if props.get("intro"):
        right.append(_text(props["intro"], "left", on_dark=True, small=True))
    foot = []
    if props.get("price"):
        foot.append(widget("heading", {
            "title": props["price"], "header_size": "div", "align": "left",
            "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(C["white"])}))
    if props.get("cta_label"):
        foot.append(_btn(props["cta_label"], props.get("cta_url", "#"),
                         "ghost"))
    if foot:
        right.append(_row(foot, 12, align="center",
                          extra={"flex_wrap": "wrap",
                                 "padding": dims(6, 0, 0, 0)}))
    wl, wr = _tracks([1, 1.15], GUTTER, container=KIT_CONTAINER - 28)
    panel = _card([_row([
        _col([_shot(props.get("image"), props.get("shot", 250),
                    label=props.get("frame_label"))], wl),
        _col(right, wr, extra={"flex_gap": gap(10)}),
    ], GUTTER, align="center", extra={"flex_wrap": "wrap"})],
        pad=dims(14, 14, 16, 14))
    return _sec([panel], "page", pad=dims(0, 0, 34, 0),
                anchor=props.get("anchor"))


@block("mot.filterbar")
def mot_filterbar(props):
    cells = []
    for f in props.get("fields", []):
        if f.get("select"):
            cells.append(_select(f["label"], f.get("icon")))
        else:
            cells.append(_field(f["label"], f.get("icon")))
    widths = _tracks([1.6] + [1] * (len(cells) - 1) + [0.9], GUTTER) \
        if cells else []
    cols = [_col([c], widths[i]) for i, c in enumerate(cells)]
    if props.get("cta_label"):
        cols.append(_col([_btn(props["cta_label"],
                               props.get("cta_url", "#"), "pink", full=True)],
                         widths[-1] if widths else 20))
    return _sec([_row(cols, GUTTER, align="center",
                      extra={"flex_wrap": "wrap"})],
                "page", pad=dims(0, 0, 26, 0), anchor=props.get("anchor"))


@block("mot.modelhead")
def mot_modelhead(props):
    """The Model detail header: back link, name, location, style tags,
    price, bio, socials and a thumbnail strip."""
    kids = []
    if props.get("back_label"):
        kids.append(_row([
            widget("icon", {
                "selected_icon": icon("fas fa-arrow-left"), "size": slider(11),
                "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref(C["muted"])}),
            _small(props["back_label"]),
        ], 7, align="center",
            extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"}))
    if props.get("name"):
        kids.append(_h(props["name"], "h1", T["h_large"], "left"))
    if props.get("location"):
        kids.append(_row([
            widget("icon", {
                "selected_icon": icon("fas fa-location-dot"),
                "size": slider(12), "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref(PINK)}),
            _small(props["location"], tone=C["white"]),
        ], 7, align="center",
            extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"}))
    if props.get("tags"):
        kids.append(_row([_chip(t) for t in props["tags"]], 7, align="center",
                         extra={"flex_wrap": "wrap"}))
    if props.get("price"):
        kids.append(widget("heading", {
            "title": props["price"], "header_size": "div", "align": "left",
            "__typography__": typo_ref(T["h_medium"]),
        }, globals_={"title_color": color_ref(PINK)}))
    if props.get("bio"):
        kids.append(_text(props["bio"], "left", on_dark=True, small=True))
    if props.get("socials"):
        kids.append(_row([widget("icon", {
            "selected_icon": icon(s.get("icon", "fab fa-instagram")),
            "size": slider(15), "align": "center", "view": "default",
            "link": link(s.get("url", "#")),
        }, globals_={"primary_color": color_ref(C["white"])})
            for s in props["socials"]], 14, align="center",
            extra={"flex_wrap": "wrap", "flex_direction_mobile": "row"}))
    thumbs = props.get("thumbs", [])
    if thumbs:
        tw = _tracks([1] * len(thumbs), 8, container=460)[0]
        kids.append(_row([_col([_shot(t.get("image"), 78, box(6),
                                      label=t.get("frame_label"))], tw)
                          for t in thumbs], 8, align="stretch",
                         extra={"flex_wrap": "wrap"}))
    wl, wr = _tracks([1, 1], GUTTER)
    return _sec([_row([
        _col([_shot(props.get("image"), props.get("shot", 400),
                    label=props.get("frame_label"))], wl),
        _col(kids, wr, extra={"flex_gap": gap(11)}),
    ], GUTTER, align="flex-start", extra={"flex_wrap": "wrap"})],
        "page", pad=dims(44, 0, 26, 0), anchor=props.get("anchor"))


@block("mot.availability")
def mot_availability(props):
    """The Verfügbarkeit row: month label with arrows, then date cards each
    showing weekday, number and a slot count."""
    head = _row([
        widget("heading", {
            "title": props.get("title", ""), "header_size": "h3",
            "align": "left", "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(C["white"])}),
        _row([
            widget("icon", {
                "selected_icon": icon("fas fa-chevron-left"),
                "size": slider(11), "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref(C["muted"])}),
            _small(props.get("month", ""), tone=C["white"]),
            widget("icon", {
                "selected_icon": icon("fas fa-chevron-right"),
                "size": slider(11), "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref(C["muted"])}),
        ], 10, align="center",
            extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"}),
    ], 12, align="center", justify="space-between",
        extra={"flex_wrap": "wrap", "flex_direction_mobile": "row"})

    days = props.get("days", [])
    w = _tracks([1] * max(len(days), 1), 8, container=KIT_CONTAINER - 60)[0]
    cells = []
    for d in days:
        active = d.get("active")
        cells.append(_col([container([
            _small(d.get("weekday", ""), "center",
                   tone=C["white"] if active else C["muted"]),
            widget("heading", {
                "title": d.get("day", ""), "header_size": "div",
                "align": "center", "__typography__": typo_ref(T["h_small"]),
            }, globals_={"title_color": color_ref(C["white"])}),
            _small(d.get("slots", ""), "center",
                   tone=PINK if active else C["muted"]),
        ], {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(3), "flex_align_items": "center",
            "padding": dims(11, 8, 11, 8), "border_radius": box(8),
            "border_border": "solid", "border_width": box(1),
            "background_background": "classic",
        }, globals_={
            "background_color": color_ref(FIELD),
            "border_color": color_ref(PINK if active else C["border"])})], w)
                     )
    panel = _card([head, _row(cells, 8, align="stretch",
                              extra={"flex_wrap": "wrap"})],
                  pad=dims(14, 14, 16, 14), hover=False)
    return _sec([panel], "page", pad=dims(0, 0, 30, 0),
                anchor=props.get("anchor"))


@block("mot.booking")
def mot_booking(props):
    """Termin auswählen: date chips, time chips, a running total, the pink
    JETZT BUCHEN, and three trust items underneath."""
    kids = [_row([
        container([
            widget("heading", {
                "title": props.get("title", ""), "header_size": "h3",
                "align": "left", "__typography__": typo_ref(T["h_small"]),
            }, globals_={"title_color": color_ref(C["white"])}),
            _small(props.get("subtitle", "")),
        ], {"content_width": "full", "flex_direction": "column",
            "flex_gap": gap(2)}),
        widget("icon", {
            "selected_icon": icon("fas fa-xmark"), "size": slider(14),
            "align": "right", "view": "default",
            "link": link(props.get("close_url", "/models/")),
        }, globals_={"primary_color": color_ref(C["muted"])}),
    ], 10, align="flex-start", justify="space-between",
        extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})]

    for grp in props.get("groups", []):
        kids.append(_small(grp.get("label", ""), tone=C["white"]))
        kids.append(_row([_chip(c.get("label", ""), c.get("active"))
                          for c in grp.get("chips", [])], 7, align="center",
                         extra={"flex_wrap": "wrap"}))

    if props.get("total_label"):
        kids.append(_row([
            _small(props["total_label"], tone=C["white"]),
            widget("heading", {
                "title": props.get("total_value", ""), "header_size": "div",
                "align": "right", "__typography__": typo_ref(T["h_small"]),
            }, globals_={"title_color": color_ref(PINK)}),
        ], 10, align="center", justify="space-between",
            extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row",
                   "padding": dims(6, 0, 2, 0)}))
    if props.get("cta_label"):
        kids.append(_btn(props["cta_label"], props.get("cta_url", "#"),
                         "pink", full=True))

    trust = props.get("trust", [])
    if trust:
        tw = _tracks([1] * len(trust), 10, container=KIT_CONTAINER // 2)[0]
        kids.append(_row([_col([container([
            widget("icon", {
                "selected_icon": icon(t.get("icon", "fas fa-shield-halved")),
                "size": slider(15), "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref(C["muted"])}),
            _small(t.get("title", ""), "center", tone=C["white"]),
            _small(t.get("note", ""), "center"),
        ], {"content_width": "full", "flex_direction": "column",
            "flex_gap": gap(4), "flex_align_items": "center"})], tw)
            for t in trust], 10, align="flex-start",
            extra={"flex_wrap": "wrap", "padding": dims(8, 0, 0, 0)}))

    panel = _card(kids, pad=dims(16, 16, 18, 16), lifted=True, hover=False)
    return _sec([panel], "page", pad=dims(0, 0, 34, 0),
                anchor=props.get("anchor", "booking"))


@block("mot.steps")
def mot_steps(props):
    """Four numbered steps with pink line icons, separated by vertical
    rules - the For Models row."""
    items = props.get("items", [])
    per = props.get("columns", min(len(items), 4)) or 1
    w = _tracks([1] * per, GUTTER)[0]
    cells = []
    for n, it in enumerate(items, 1):
        cell = _col([
            widget("icon", {
                "selected_icon": icon(it.get("icon", "far fa-user")),
                "size": slider(24), "align": "left", "view": "default",
            }, globals_={"primary_color": color_ref(PINK)}),
            widget("heading", {
                "title": "%d. %s" % (n, it.get("title", "")),
                "header_size": "h3", "align": "left",
                "__typography__": typo_ref(T["h_small"]),
            }, globals_={"title_color": color_ref(C["white"])}),
            _small(it.get("text", "")),
        ], w, extra={"flex_gap": gap(9)})
        if n > 1:
            cell["settings"].update({
                "border_border": "solid",
                "border_width": {"unit": "px", "top": "0", "right": "0",
                                 "bottom": "0", "left": "1",
                                 "isLinked": ""},
                "padding": dims(0, 0, 0, 20),
            })
            cell.setdefault("settings", {}).setdefault("__globals__", {})[
                "border_color"] = color_ref(C["border"])
        cells.append(cell)
    return _sec([_row(cells, GUTTER, align="flex-start",
                      extra={"flex_wrap": "wrap"})],
                props.get("bg", "page"), pad=dims(40, 0, 40, 0),
                anchor=props.get("anchor"))


@block("mot.applyform")
def mot_applyform(props):
    """The For Models panel: icon-prefixed fields in two columns, a dashed
    upload zone with its limits, the 18+ and privacy checkbox, and the pink
    submit - beside a photo column carrying the script accent and three
    benefits."""
    left = _head_stack(props, "left")
    f = props.get("form", {})
    rows = f.get("rows", [])
    for r in rows:
        cols = []
        wds = _tracks([1] * len(r), 12, container=640)
        for i, fl in enumerate(r):
            ctl = (_select(fl["label"], fl.get("icon")) if fl.get("select")
                   else _field(fl["label"], fl.get("icon")))
            cols.append(_col([ctl], wds[i]))
        left.append(_row(cols, 12, align="center",
                         extra={"flex_wrap": "wrap"}))

    up = f.get("upload")
    if up:
        left.append(container([
            widget("icon", {
                "selected_icon": icon("fas fa-cloud-arrow-up"),
                "size": slider(20), "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref(C["muted"])}),
            widget("heading", {
                "title": up.get("title", ""), "header_size": "div",
                "align": "center", "__typography__": typo_ref(T["meta"]),
            }, globals_={"title_color": color_ref(C["white"])}),
            _small(up.get("text", ""), "center"),
            _small(up.get("limits", ""), "center"),
        ], {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(6), "flex_align_items": "center",
            "padding": dims(20, 16, 22, 16), "border_radius": box(8),
            "border_border": "dashed", "border_width": box(1),
            "background_background": "classic",
        }, globals_={"background_color": color_ref(FIELD),
                     "border_color": color_ref(C["border"])}))

    if f.get("consent"):
        left.append(_row([
            container([], {
                "content_width": "full", "width": slider(15),
                "min_height": slider(15), "_flex_shrink": "0",
                "border_radius": box(3), "border_border": "solid",
                "border_width": box(1),
            }, globals_={"border_color": color_ref(C["muted"])}),
            _small(f["consent"]),
        ], 9, align="flex-start",
            extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"}))
    if f.get("submit"):
        left.append(_btn(f["submit"], f.get("submit_url", "#"), "pink"))

    right = [_shot(props.get("image"), props.get("shot", 230),
                   label=props.get("frame_label"))]
    if props.get("script"):
        right.append(_script(props["script"], "left"))
    for bn in props.get("benefits", []):
        right.append(_row([
            widget("icon", {
                "selected_icon": icon(bn.get("icon", "fas fa-star")),
                "size": slider(18), "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref(PINK)}),
            container([
                widget("heading", {
                    "title": bn.get("title", ""), "header_size": "div",
                    "align": "left", "__typography__": typo_ref(T["meta"]),
                }, globals_={"title_color": color_ref(C["white"])}),
                _small(bn.get("text", "")),
            ], {"content_width": "full", "flex_direction": "column",
                "flex_gap": gap(2)}),
        ], 11, align="flex-start",
            extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row",
                   "padding": dims(4, 0, 4, 0)}))

    # Inside a card padded 22 each side, so the real container is narrower.
    wl, wr = _tracks([1.5, 1], GUTTER, container=KIT_CONTAINER - 44)
    panel = _card([_row([
        _col(left, wl, extra={"flex_gap": gap(12)}),
        _col(right, wr, extra={"flex_gap": gap(10)}),
    ], GUTTER, align="flex-start", extra={"flex_wrap": "wrap"})],
        pad=dims(22, 22, 24, 22), hover=False)
    return _sec([panel], "page", anchor=props.get("anchor", "bewerbung"))


@block("mot.cards")
def mot_cards(props):
    kids = _head_stack(props, props.get("align", "left"))
    per = props.get("columns", 3)
    w = _tracks([1] * per, GUTTER)[0]
    cells = []
    for it in props.get("items", []):
        body = [_shot(it.get("image"), props.get("shot", 120),
                      label=it.get("frame_label"))]
        if it.get("icon"):
            body.append(widget("icon", {
                "selected_icon": icon(it["icon"]), "size": slider(18),
                "align": "left", "view": "default",
            }, globals_={"primary_color": color_ref(PINK)}))
        body.append(widget("heading", {
            "title": it.get("title", ""), "header_size": "h3", "align": "left",
            "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(C["white"])}))
        if it.get("text"):
            body.append(_small(it["text"]))
        cells.append(_card(body, w, pad=dims(12, 12, 14, 12)))
    kids.append(_row(cells, GUTTER, align="stretch",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "page"), anchor=props.get("anchor"))


@block("mot.stats")
def mot_stats(props):
    items = props.get("items", [])
    w = _tracks([1] * max(len(items), 1), GUTTER)[0]
    cells = []
    for it in items:
        cells.append(_col([_row([
            widget("icon", {
                "selected_icon": icon(it.get("icon", "fas fa-city")),
                "size": slider(24), "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref(PINK)}),
            container([
                widget("heading", {
                    "title": it.get("value", ""), "header_size": "div",
                    "align": "left", "__typography__": typo_ref(T["h_medium"]),
                }, globals_={"title_color": color_ref(
                    PINK if it.get("pink") else C["white"])}),
                _small(it.get("label", ""), tone=C["white"]),
                _small(it.get("note", "")),
            ], {"content_width": "full", "flex_direction": "column",
                "flex_gap": gap(2)}),
        ], 12, align="center",
            extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})], w))
    return _photo_section([_row(cells, GUTTER, align="center",
                                extra={"flex_wrap": "wrap"})],
                          props, dims(34, 0, 34, 0),
                          props.get("height", 120), overlay=0.86,
                          anchor=props.get("anchor"))


@block("mot.split")
def mot_split(props):
    right = _head_stack(props, "left")
    for p in props.get("paragraphs", []):
        right.append(_text(p, "left", on_dark=True, small=True))
    if props.get("cta_label"):
        right.append(_row([_btn(props["cta_label"],
                                props.get("cta_url", "#"),
                                props.get("cta_style", "outline"))], 12,
                          align="center", extra={"flex_wrap": "wrap",
                                                 "padding": dims(6, 0, 0, 0)}))
    wl, wr = _tracks([1, 1], GUTTER)
    body = [_col([_shot(props.get("image"), props.get("shot", 280),
                        label=props.get("frame_label"))], wl),
            _col(right, wr, extra={"flex_gap": gap(11)})]
    if props.get("flip"):
        body.reverse()
    return _sec([_row(body, GUTTER, align="center",
                      extra={"flex_wrap": "wrap"})],
                props.get("bg", "page"), anchor=props.get("anchor"))


@block("mot.benefits")
def mot_benefits(props):
    kids = _head_stack(props, props.get("align", "left"))
    for it in props.get("items", []):
        kids.append(_row([
            widget("icon", {
                "selected_icon": icon(it.get("icon", "fas fa-star")),
                "size": slider(18), "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref(PINK)}),
            container([
                widget("heading", {
                    "title": it.get("title", ""), "header_size": "div",
                    "align": "left", "__typography__": typo_ref(T["meta"]),
                }, globals_={"title_color": color_ref(C["white"])}),
                _small(it.get("text", "")),
            ], {"content_width": "full", "flex_direction": "column",
                "flex_gap": gap(2)}),
        ], 11, align="flex-start",
            extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row",
                   "padding": dims(5, 0, 5, 0)}))
    return _sec(kids, props.get("bg", "page"), anchor=props.get("anchor"))


@block("mot.cta")
def mot_cta(props):
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], "center"))
    if props.get("title"):
        kids.append(_h(props["title"], props.get("tag", "h2"), T["h_large"],
                       "center"))
    if props.get("intro"):
        kids.append(container([_text(props["intro"], "center", on_dark=True,
                                     small=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(66, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"),
                         "pink"))
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props.get("alt_url", "#"),
                         "outline"))
    if btns:
        kids.append(_row(btns, 12, align="center", justify="center",
                         extra={"flex_wrap": "wrap",
                                "padding": dims(8, 0, 0, 0)}))
    return _photo_section(kids, props, dims(70, 0, 70, 0),
                          props.get("height", 220), overlay=0.84,
                          anchor=props.get("anchor"))
