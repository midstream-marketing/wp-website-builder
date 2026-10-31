"""
blocks_desgroup.py — Des Group Property Services (`dg.*`).

The brief: "I need my site to look similar to https://capriplumbing.com/, clean
and simple. No need for fake stock images, just the sale copies and
descriptions of the services." So Capri is the SPEC for layout and treatment
(see reference-vs-similar), and the client's own no-stock instruction narrows
it: every Capri device is matched except its photography.

Capri's devices, rendered and read off the live site (2026-09-12):

    1. Announcement bar over a dark sticky header; nav left, an OUTLINED PHONE
       BOX ("Call Today" over the number) on the right.
    2. Centred hero on a dark navy gradient: breadcrumb, an outlined pill
       eyebrow, a huge Sora 800 headline whose last words are picked out in
       blue, a one-line sub, two buttons, and a row of outlined pill badges.
    3. Tracked blue caps eyebrow over a centred Sora headline, every section.
    4. Bordered dark cards (16px radius, 1px line) with an outlined ICON TILE,
       used for every service grid.
    5. Alternating split: eyebrow + headline one side, prose the other.
    6. A numbered process TIMELINE — number boxes joined by a vertical line.
    7. A mid-page call strip ("No hot water right now?").
    8. FAQ accordion; request form card beside a text column with the phone.
    9. A closing band: headline, tick list, call button.

Dropped from Capri on purpose: its hero photograph and photos (client's
instruction), the testimonial carousel, "4.9 stars", BBB badge and the stat
counters (Des Group has supplied none — they would be invented), and the
emergency POPUP (a modal over the first screen of a four-page site costs more
than it earns; the mobile call bar does the job).

Colour: Capri's navy ground, re-keyed to the Des Group shield blue. Nothing
here names a hex except the roof swatches, which are illustrations of
product colours rather than brand colour.
"""
from __future__ import annotations

import re

from .core import (
    container, widget, repeater_item, slider, dims, box, link, icon, gap,
    color_ref, typo_ref, css,
)
from .tokens import C, T
from .blocks import (
    block, _row, _col, _tracks, _faq, _button, _hover_lift, KIT_CONTAINER,
)

BLUE = "primary"            # shield blue, button fill
GROUND = "secondary"        # navy page ground
HI = "accent"               # light blue highlight
DEEP = "dgdp020"            # logo dark grey (alternate ground, header bar, footer, fields)
HEAD = "dghd021"            # heading white-blue
EDGE = "dgbd022"            # blue hairline on buttons / phone box
LINE = C["border"]
CARD = C["surface"]
TILE = C["surface_alt"]

PAD = dims(100, 0, 100, 0)
PAD_T = dims(76, 24, 76, 24)
PAD_M = dims(58, 20, 58, 20)
R_CARD = box(16)
R_BTN = box(14)
GUTTER = 22

GROUNDS = {"ground": GROUND, "deep": DEEP, "panel": CARD}
_ENTITY = re.compile(r"&([A-Z]+);")


def _caps(text):
    return _ENTITY.sub(lambda m: "&" + m.group(1).lower() + ";", text.upper())


def _sec(children, bg="ground", pad=None, extra=None, anchor=None):
    """Capri separates every section with a 1px top hairline."""
    s = {
        "content_width": "boxed",
        "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "flex_gap": gap(44),
        "padding": pad or PAD,
        "padding_tablet": PAD_T,
        "padding_mobile": PAD_M,
        "background_background": "classic",
        "border_border": "solid",
        "border_width": dims(1, 0, 0, 0),
    }
    if extra:
        s.update(extra)
    if anchor:
        s["_element_id"] = anchor
    return container(children, s, globals_={
        "background_color": color_ref(GROUNDS.get(bg, GROUND)),
        "border_color": color_ref(LINE)})


# ───────────────────────────── type ─────────────────────────────

def _eyebrow(text, align="center"):
    return widget("heading", {
        "title": _caps(text), "header_size": "div", "align": align,
    }, globals_={"title_color": color_ref(HI),
                 "typography_typography": typo_ref(T["eyebrow"])})


def _h(text, size="h2", token=None, align="center", hl=None):
    """Heading; `hl` picks out one phrase in the highlight blue — Capri's
    '…Solutions You Can Trust'. Colour through the global CSS variable, so
    the kit still re-skins."""
    s = {"title": text, "header_size": size, "align": align}
    if hl and hl in text:
        s["title"] = text.replace(hl, '<span class="dg-hl">' + hl + "</span>", 1)
        s["custom_css"] = css(
            "selector .dg-hl { color: var(--e-global-color-accent); }")
    return widget("heading", s, globals_={
        "title_color": color_ref(HEAD),
        "typography_typography": typo_ref(token or T["h_large"])})


def _p(html, align="left", small=False, muted=False):
    return widget("text-editor", {
        "editor": html if html.strip().startswith("<") else "<p>" + html + "</p>",
        "align": align,
    }, globals_={"text_color": color_ref(C["muted"] if muted else "text"),
                 "typography_typography": typo_ref(T["body_small"] if small else "text")})


def _head(props, align="center", width=76):
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], align))
    if props.get("title"):
        kids.append(_h(props["title"], props.get("size", "h2"), None, align,
                       props.get("hl")))
    if props.get("sub"):
        kids.append(widget("heading", {
            "title": props["sub"], "header_size": "div", "align": align},
            globals_={"title_color": color_ref(HEAD),
                      "typography_typography": typo_ref(T["h_small"])}))
    if props.get("intro"):
        kids.append(_p(props["intro"], align))
    return container(kids, {
        "content_width": "full", "flex_direction": "column", "flex_gap": gap(14),
        "width": slider(width if align == "center" else 100, "%"),
        "width_tablet": slider(100, "%"), "width_mobile": slider(100, "%"),
        "_flex_align_self": "center" if align == "center" else "flex-start",
    })


# ───────────────────────────── controls ─────────────────────────────

def _btn(label, href, style="primary", icon_cls=None):
    """primary: shield-blue fill with a lighter blue hairline (Capri's filled
    button). ghost: transparent with a navy hairline. Sora 700, sentence case."""
    b = _button(label, href, "ghost", icon_cls or "")
    s, g = b["settings"], b["settings"]["__globals__"]
    g.pop("typography_typography", None)
    if style == "primary":
        g.update({"button_text_color": color_ref(C["white"]),
                  "background_color": color_ref(BLUE),
                  "border_color": color_ref(EDGE),
                  "hover_color": color_ref(GROUND),
                  "button_background_hover_color": color_ref(HI),
                  "button_hover_border_color": color_ref(HI)})
    else:
        g.update({"button_text_color": color_ref(HEAD),
                  "background_color": color_ref(C["transparent"]),
                  "border_color": color_ref(LINE),
                  "hover_color": color_ref(HI),
                  "button_background_hover_color": color_ref(CARD),
                  "button_hover_border_color": color_ref(HI)})
    s.update({
        "border_radius": R_BTN, "border_width": box(1),
        "text_padding": dims(17, 30, 17, 30),
        "icon_align": "left", "icon_indent": slider(10),
        "typography_typography": "custom",
        "typography_font_family": "Sora",
        "typography_font_weight": "700",
        "typography_font_size": slider(16),
    })
    return b


def _phone_btn(props, style="primary", label=None):
    return _btn(label or props.get("phone_display", ""),
                "tel:" + props.get("phone", ""), style, "fas fa-phone-alt")


def _actions(props, justify="center"):
    kids = []
    if props.get("cta_label"):
        kids.append(_btn(props["cta_label"], props.get("cta_url", "#request")))
    if props.get("phone_display"):
        kids.append(_phone_btn(props, "ghost"))
    return _row(kids, 14, align="center", justify=justify,
                extra={"flex_direction_mobile": "column",
                       "flex_align_items_mobile": "stretch"})


def _pill(text, icon_cls=None, tone="line"):
    kids = []
    if icon_cls:
        kids.append(widget("icon", {"selected_icon": icon(icon_cls),
                                    "size": slider(13), "align": "center",
                                    "view": "default"},
                           globals_={"primary_color": color_ref(HI)}))
    kids.append(widget("heading", {"title": text, "header_size": "div",
                                   "align": "center"},
                       globals_={"title_color": color_ref(HEAD),
                                 "typography_typography": typo_ref(T["meta"])}))
    return container(kids, {
        "content_width": "full", "flex_direction": "row",
        "flex_align_items": "center", "flex_justify_content": "center",
        "flex_gap": gap(8), "_flex_grow": 0,
        "width": slider(round(62 + len(text) * 7.4)),
        "width_mobile": slider(round(58 + len(text) * 7.0)),
        "padding": dims(9, 16, 9, 16), "border_radius": box(999),
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
    }, globals_={"border_color": color_ref(LINE),
                 "background_color": color_ref(CARD)})


def _tile(icon_cls):
    """Outlined rounded-square icon tile, top-left of a card."""
    return container([widget("icon", {
        "selected_icon": icon(icon_cls), "size": slider(21),
        "align": "center", "view": "default",
    }, globals_={"primary_color": color_ref(HI)})], {
        "content_width": "full", "flex_direction": "row",
        "flex_justify_content": "center", "flex_align_items": "center",
        "width": slider(52), "min_height": slider(52), "_flex_grow": 0,
        "_flex_align_self": "flex-start",
        "border_radius": box(12), "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(TILE),
                 "border_color": color_ref(EDGE)})


def _card(kids, pad=None, bg=None, edge=None):
    return container(kids, {
        "content_width": "full", "flex_direction": "column", "flex_gap": gap(12),
        "padding": pad or dims(30, 26, 30, 26), "border_radius": R_CARD,
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(bg or CARD),
                 "border_color": color_ref(edge or LINE)})


def _grid(cells, cols, gutter=GUTTER, align="stretch"):
    w = _tracks([1] * cols, gutter)
    tab = 48.4 if cols > 1 else 100
    return _row([_col([c], w[i % cols], extra={"width_tablet": slider(tab, "%")})
                 for i, c in enumerate(cells)], gutter, align=align)


def _ticks(items, inline=False):
    return widget("icon-list", {
        "icon_list": [repeater_item(text=t, selected_icon=icon("fas fa-check"),
                                    link=link("")) for t in items],
        "view": "inline" if inline else "traditional",
        "space_between": slider(18 if inline else 10),
        "icon_size": slider(13),
    }, globals_={"icon_color": color_ref(HI), "text_color": color_ref(HEAD),
                 "icon_typography_typography": typo_ref(T["body_small"])})


def _dots(items):
    return widget("icon-list", {
        "icon_list": [repeater_item(text=t, selected_icon=icon("fas fa-circle"),
                                    link=link("")) for t in items],
        "space_between": slider(8), "icon_size": slider(6),
    }, globals_={"icon_color": color_ref(HI), "text_color": color_ref("text"),
                 "icon_typography_typography": typo_ref(T["body_small"])})


def _rule():
    return container([], {"content_width": "full", "min_height": slider(1),
                          "background_background": "classic"},
                     globals_={"background_color": color_ref(LINE)})


# ═══════════════════════════════ header ═══════════════════════════════

@block("dg.header")
def dg_header(props):
    """Announcement bar + dark header with the outlined phone box."""
    tel = "tel:" + props.get("phone", "")
    bar = container([_row([
        widget("heading", {"title": props.get("topline", ""), "header_size": "div",
                           "align": "center"},
               globals_={"title_color": color_ref(HEAD),
                         "typography_typography": typo_ref(T["meta"])}),
        widget("heading", {"title": props.get("topline_link", ""), "header_size": "div",
                           "align": "center", "link": link(tel)},
               globals_={"title_color": color_ref(HI),
                         "typography_typography": typo_ref(T["meta"])}),
    ], 10, align="center", justify="center",
        extra={"flex_direction_mobile": "column", "flex_gap_mobile": gap(2)})], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column", "padding": dims(11, 0, 11, 0),
        "padding_mobile": dims(9, 14, 9, 14),
        "background_background": "classic",
        "border_border": "solid", "border_width": dims(0, 0, 1, 0),
    }, globals_={"background_color": color_ref(TILE),
                 "border_color": color_ref(LINE)})

    logo = widget("theme-site-logo", {"align": "left",
                                      "width": slider(props.get("logo_width", 64)),
                                      "width_mobile": slider(52)})
    nav = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"), "layout": "horizontal",
        "align_items": "left", "pointer": "none",
        "menu_space_between": slider(34), "toggle_align": "right",
    }, globals_={
        "color_menu_item": color_ref("text"),
        "color_menu_item_hover": color_ref(HEAD),
        "color_menu_item_active": color_ref(HEAD),
        "dropdown_background_color": color_ref(CARD),
        "dropdown_color_menu_item": color_ref(HEAD),
        "toggle_color": color_ref(HEAD),
        "menu_typography_typography": typo_ref("text"),
    })
    box_ = container([
        widget("icon", {"selected_icon": icon("fas fa-phone-alt"), "size": slider(16),
                        "align": "center", "view": "default", "link": link(tel)},
               globals_={"primary_color": color_ref(HEAD)}),
        container([
            widget("heading", {"title": props.get("call_label", "Call Today"),
                               "header_size": "div", "align": "left",
                               "link": link(tel)},
                   globals_={"title_color": color_ref(HEAD),
                             "typography_typography": typo_ref(T["meta"])}),
            widget("heading", {"title": props.get("phone_display", ""),
                               "header_size": "div", "align": "left",
                               "link": link(tel)},
                   globals_={"title_color": color_ref(HEAD),
                             "typography_typography": typo_ref(T["h_small"])}),
        ], {"content_width": "full", "flex_direction": "column", "flex_gap": gap(0)}),
    ], {
        "content_width": "full", "flex_direction": "row", "flex_align_items": "center",
        "flex_gap": gap(14), "width": slider(214), "_flex_grow": 0,
        "padding": dims(10, 22, 10, 22), "border_radius": R_BTN,
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
    }, globals_={"border_color": color_ref(EDGE), "background_color": color_ref(TILE)})

    w = _tracks([10, 62, 26], 20)
    main = container([_row([
        _col([logo], w[0], extra={"width_mobile": slider(40, "%")}),
        _col([nav], w[1], extra={"width_mobile": slider(56, "%"),
                                 "flex_align_items_mobile": "flex-end"}),
        _col([box_], w[2], extra={"flex_align_items": "flex-end",
                                  "hide_mobile": "hidden-mobile"}),
    ], 20, align="center", extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column", "padding": dims(12, 0, 12, 0),
        "padding_tablet": dims(12, 24, 12, 24), "padding_mobile": dims(10, 14, 10, 14),
        "background_background": "classic",
        "border_border": "solid", "border_width": dims(0, 0, 1, 0),
    }, globals_={"background_color": color_ref(DEEP), "border_color": color_ref(LINE)})

    return container([bar, main], {
        "content_width": "full", "flex_direction": "column", "flex_gap": gap(0),
        "sticky": "top", "sticky_on": ["desktop", "tablet", "mobile"], "_z_index": 99,
    })


# ═══════════════════════════════ hero ═══════════════════════════════

@block("dg.hero")
def dg_hero(props):
    """Centred hero on a navy gradient — no photograph, per the client."""
    kids = []
    if props.get("breadcrumb"):
        kids.append(widget("text-editor", {
            "editor": "<p>" + " &nbsp;/&nbsp; ".join(
                ('<a href="%s">%s</a>' % (u, t)) if u else t
                for t, u in props["breadcrumb"]) + "</p>",
            "align": "center"},
            globals_={"text_color": color_ref(C["muted"]),
                      "typography_typography": typo_ref(T["meta"])}))
    if props.get("pill"):
        kids.append(_row([_pill(_caps(props["pill"]))], 0, justify="center",
                         extra={"flex_direction_mobile": "row"}))
    kids.append(_h(props.get("title", ""), "h1", T["hero"], "center", props.get("hl")))
    if props.get("intro"):
        kids.append(_p(props["intro"], "center"))
    kids.append(_actions(props))
    if props.get("badges"):
        kids.append(_row([_pill(b["text"], b.get("icon")) for b in props["badges"]],
                         12, align="center", justify="center",
                         extra={"flex_direction_mobile": "row"}))
    body = container(kids, {
        "content_width": "full", "flex_direction": "column", "flex_gap": gap(22),
        "width": slider(84, "%"), "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"), "_flex_align_self": "center"})
    return container([body], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column", "flex_justify_content": "center",
        "min_height": slider(600), "min_height_mobile": slider(0),
        "padding": dims(96, 0, 96, 0), "padding_tablet": dims(80, 24, 80, 24),
        "padding_mobile": dims(56, 18, 56, 18),
        "background_background": "gradient",
        "background_gradient_angle": slider(180, "deg"),
        "background_color_stop": slider(0, "%"),
        "background_color_b_stop": slider(100, "%"),
    }, globals_={"background_color": color_ref(TILE),
                 "background_color_b": color_ref(GROUND)})


# ═══════════════════════════ split / panel / strip ═══════════════════════════

def _bullets(items):
    """Bullet points as left-ruled rows — each is a claim the page argues."""
    out = []
    for b in items:
        out.append(container([_p(b, "left")], {
            "content_width": "full", "flex_direction": "column",
            "padding": dims(4, 0, 4, 18),
            "border_border": "solid", "border_width": dims(0, 0, 0, 3),
        }, globals_={"border_color": color_ref(HI)}))
    return container(out, {"content_width": "full", "flex_direction": "column",
                           "flex_gap": gap(16)})


@block("dg.split")
def dg_split(props):
    """Capri's alternating split: eyebrow + headline one side, prose the other."""
    left = []
    if props.get("eyebrow"):
        left.append(_eyebrow(props["eyebrow"], "left"))
    left.append(_h(props.get("title", ""), props.get("size", "h2"), None, "left",
                   props.get("hl")))
    if props.get("cta_label"):
        left.append(_row([_btn(props["cta_label"], props.get("cta_url", "#request"))], 0))
    right = [_p(p, "left") for p in props.get("paragraphs", [])]
    if props.get("bullets"):
        right.append(_bullets(props["bullets"]))
    for p in props.get("after", []):
        right.append(_p(p, "left"))
    w = _tracks([42, 54], 60)
    cols = [_col(left, w[0], extra={"flex_gap": gap(16)}),
            _col(right, w[1], extra={"flex_gap": gap(16)})]
    if props.get("flip"):
        cols.reverse()
    return _sec([_row(cols, 60, align="center")], props.get("bg", "ground"),
                anchor=props.get("anchor"))


@block("dg.panel")
def dg_panel(props):
    """A highlighted panel — 'The Solution', 'The Guarantee'. Blue hairline."""
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], "left"))
    if props.get("title"):
        kids.append(_h(props["title"], "h2", T["h_medium"], "left"))
    for p in props.get("paragraphs", []):
        kids.append(_p(p, "left"))
    if props.get("bullets"):
        if props.get("bullets_title"):
            kids.append(widget("heading", {"title": props["bullets_title"],
                                           "header_size": "h3", "align": "left"},
                               globals_={"title_color": color_ref(HEAD),
                                         "typography_typography": typo_ref(T["h_small"])}))
        kids.append(_bullets(props["bullets"]))
    for p in props.get("after", []):
        kids.append(_p(p, "left"))
    card = _card(kids, dims(44, 44, 44, 44), TILE, EDGE)
    card["settings"]["padding_mobile"] = dims(28, 20, 28, 20)
    card["settings"]["flex_gap"] = gap(18)
    return _sec([container([card], {
        "content_width": "full", "flex_direction": "column",
        "width": slider(88, "%"), "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"), "_flex_align_self": "center"})],
        props.get("bg", "deep"), anchor=props.get("anchor"))


@block("dg.strip")
def dg_strip(props):
    """Mid-page call strip: headline + line left, buttons right."""
    left = [_h(props.get("title", ""), "h2", T["h_medium"], "left")]
    if props.get("text"):
        left.append(_p(props["text"], "left"))
    if props.get("note"):
        left.append(_row([_pill(props["note"], "fas fa-dollar-sign")], 0,
                         extra={"flex_direction_mobile": "row"}))
    w = _tracks([58, 38], 36)
    right = _actions(props, justify="flex-end")
    card = _card([_row([_col(left, w[0], extra={"flex_gap": gap(14)}),
                        _col([right], w[1])], 36, align="center")],
                 dims(40, 40, 40, 40), TILE, EDGE)
    card["settings"]["padding_mobile"] = dims(26, 20, 26, 20)
    return _sec([card], props.get("bg", "ground"), pad=dims(64, 0, 64, 0),
                anchor=props.get("anchor"))


# ═══════════════════════════════ cards ═══════════════════════════════

@block("dg.cards")
def dg_cards(props):
    """Bordered dark cards with an outlined icon tile. Serves the home service
    cards (with a dot list and a link) and every numbered service list."""
    def card(it):
        top = [_tile(it.get("icon", "fas fa-tools"))]
        kids = [_row(top, 0, extra={"flex_direction_mobile": "row"})]
        if it.get("num"):
            kids.append(_eyebrow(it["num"], "left"))
        t = widget("heading", {"title": it.get("title", ""), "header_size": "h3",
                               "align": "left"},
                   globals_={"title_color": color_ref(HEAD),
                             "typography_typography": typo_ref(T["h_small"])})
        if it.get("url"):
            t["settings"]["link"] = link(it["url"])
        kids.append(t)
        if it.get("text"):
            kids.append(_p(it["text"], "left", small=True))
        if it.get("list"):
            kids.append(_rule())
            kids.append(_dots(it["list"]))
        if it.get("url") and it.get("link_label"):
            kids.append(widget("heading", {
                "title": it["link_label"] + " &rarr;", "header_size": "div",
                "align": "left", "link": link(it["url"])},
                globals_={"title_color": color_ref(HI),
                          "typography_typography": typo_ref(T["meta"])}))
        return _hover_lift(_card(kids), 4)

    head = [_head(props)] if (props.get("title") or props.get("eyebrow")) else []
    return _sec(head + [_grid([card(i) for i in props.get("items", [])],
                              props.get("columns", 3))],
                props.get("bg", "ground"), anchor=props.get("anchor"))


@block("dg.trust")
def dg_trust(props):
    """'Why Homeowners Trust Our Team' — three cards, tile + bold lead-in."""
    def card(it):
        return _card([_tile(it.get("icon", "fas fa-check")),
                      widget("heading", {"title": it["title"], "header_size": "h3",
                                         "align": "left"},
                             globals_={"title_color": color_ref(HEAD),
                                       "typography_typography": typo_ref(T["h_small"])}),
                      _p(it["text"], "left", small=True)])
    return _sec([_head(props), _grid([card(i) for i in props.get("items", [])], 3)],
                props.get("bg", "deep"), anchor=props.get("anchor"))


# ═══════════════════════════════ timeline ═══════════════════════════════

@block("dg.timeline")
def dg_timeline(props):
    """Numbered boxes joined by a vertical line, a card beside each."""
    steps = props.get("steps", [])
    rows = []
    for i, s in enumerate(steps):
        num = container([widget("heading", {
            "title": str(i + 1), "header_size": "div", "align": "center"},
            globals_={"title_color": color_ref(HEAD),
                      "typography_typography": typo_ref(T["h_small"])})], {
            "content_width": "full", "flex_direction": "row",
            "flex_justify_content": "center", "flex_align_items": "center",
            "width": slider(56), "min_height": slider(56), "_flex_grow": 0,
            "border_radius": box(12), "border_border": "solid", "border_width": box(1),
            "background_background": "classic",
        }, globals_={"background_color": color_ref(TILE), "border_color": color_ref(EDGE)})
        rail = [num]
        if i < len(steps) - 1:
            rail.append(container([], {
                "content_width": "full", "width": slider(2), "min_height": slider(80),
                "_flex_grow": 1, "background_background": "classic"},
                globals_={"background_color": color_ref(EDGE)}))
        rail_col = container(rail, {
            "content_width": "full", "flex_direction": "column",
            "flex_align_items": "center", "flex_gap": gap(0),
            "width": slider(56), "_flex_grow": 0})
        body = _card([widget("heading", {"title": s["title"], "header_size": "h3",
                                         "align": "left"},
                             globals_={"title_color": color_ref(HEAD),
                                       "typography_typography": typo_ref(T["h_medium"])}),
                      _p(s["text"], "left")], dims(28, 30, 28, 30))
        body["settings"]["margin"] = dims(0, 0, 26, 0)
        rows.append(_row([rail_col, body], 26, align="stretch",
                         extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"}))
    col = container(rows, {"content_width": "full", "flex_direction": "column",
                           "flex_gap": gap(0), "width": slider(82, "%"),
                           "width_tablet": slider(100, "%"),
                           "width_mobile": slider(100, "%"),
                           "_flex_align_self": "center"})
    return _sec([_head(props), col], props.get("bg", "deep"),
                anchor=props.get("anchor"))


# ═══════════════════════════════ roofing materials ═══════════════════════════════

def _swatches(colours):
    """Overlapping product-colour discs, as in the client's own document. The
    colours illustrate the range and are captioned as illustrative."""
    discs = []
    for i, hx in enumerate(colours):
        discs.append(container([], {
            "content_width": "full", "width": slider(118), "min_height": slider(118),
            "width_mobile": slider(78), "min_height_mobile": slider(78),
            "_flex_grow": 0, "border_radius": box(999),
            "border_border": "solid", "border_width": box(3),
            "margin": dims(0, 0, 0, 0 if i == 0 else -26),
            "margin_mobile": dims(0, 0, 0, 0 if i == 0 else -18),
            "background_background": "classic", "background_color": hx,
        }, globals_={"border_color": color_ref(GROUND)}))
    return _row(discs, 0, align="center", justify="center",
                extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})


@block("dg.materials")
def dg_materials(props):
    groups = []
    for g in props.get("groups", []):
        feats = []
        for j, f in enumerate(g.get("features", [])):
            if j:
                feats.append(_rule())
            feats.append(_row([
                _tile(f.get("icon", "fas fa-check")),
                container([widget("heading", {"title": f["title"], "header_size": "h4",
                                              "align": "left"},
                                  globals_={"title_color": color_ref(HEAD),
                                            "typography_typography": typo_ref(T["h_small"])}),
                           _p(f["text"], "left", small=True)],
                          {"content_width": "full", "flex_direction": "column",
                           "flex_gap": gap(4)}),
            ], 18, align="center", extra={"flex_wrap": "nowrap",
                                          "flex_direction_mobile": "row"}))
        kids = [_h(g["name"], "h3", T["h_medium"], "center")]
        if g.get("swatches"):
            kids.append(_swatches(g["swatches"]))
        kids.append(_card(feats, dims(26, 28, 26, 28)))
        groups.append(container(kids, {"content_width": "full",
                                       "flex_direction": "column", "flex_gap": gap(22)}))
    w = _tracks([1] * max(len(groups), 1), 40)
    kids = [_head(props), _row([_col([g], w[i]) for i, g in enumerate(groups)], 40,
                               align="flex-start")]
    if props.get("note"):
        kids.append(_p(props["note"], "center", small=True, muted=True))
    return _sec(kids, props.get("bg", "ground"), anchor=props.get("anchor"))


# ═══════════════════════════════ faq ═══════════════════════════════

@block("dg.faq")
def dg_faq(props):
    acc = _faq(props.get("items", []), props.get("first_open", False))
    acc["settings"]["faq_schema"] = "yes"
    acc["settings"]["__globals__"].update({
        "accordion_item_title_color": color_ref(HEAD),
        "accordion_item_title_icon_color": color_ref(HI),
    })
    body = container([acc], {
        "content_width": "full", "flex_direction": "column",
        "width": slider(78, "%"), "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"), "_flex_align_self": "center"})
    return _sec([_head(props), body], props.get("bg", "ground"),
                anchor=props.get("anchor"))


# ═══════════════════════════════ request form ═══════════════════════════════

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
                         "file_types": f.get("file_types", "jpg,jpeg,png,heic,webp"),
                         "allow_multiple_upload": "yes",
                         "max_files": str(f.get("max_files", 5))})
        out.append(repeater_item(**item))
    return out


@block("dg.request")
def dg_request(props):
    """Capri's 'Send Request Form' split — plus the client's one functional ask:
    the prospect can UPLOAD PHOTOS of the problem."""
    f = props.get("form", {})
    left = [_eyebrow(props.get("eyebrow", "Request Service"), "left"),
            _h(props.get("title", ""), "h2", None, "left")]
    for p in props.get("paragraphs", []):
        left.append(_p(p, "left"))
    if props.get("ticks"):
        left.append(_ticks(props["ticks"]))
    if props.get("phone_display"):
        left.append(_row([_phone_btn(props)], 0))
    form = widget("form", {
        "form_name": f.get("form_name", "Service Request"),
        "form_fields": _fields(f["fields"]),
        "submit_actions": ["email"],
        "email_to": f.get("email", ""),
        "email_subject": "New service request - Des Group website",
        "button_text": f.get("submit", "Send Request"),
        "button_size": "md", "button_width": "100", "input_size": "md",
        "show_labels": "yes", "mark_required": "yes",
        "row_gap": slider(16), "column_gap": slider(14),
        "success_message": f.get("success", ""),
        "field_border_radius": box(10), "field_border_width": box(1),
        "button_border_radius": R_BTN,
    }, globals_={
        "button_background_color": color_ref(BLUE),
        "button_background_hover_color": color_ref(HI),
        "button_text_color": color_ref(C["white"]),
        "field_background_color": color_ref(DEEP),
        "field_text_color": color_ref(HEAD),
        "field_border_color": color_ref(LINE),
        "label_color": color_ref(HEAD),
        "mark_required_color": color_ref(HI),
    })
    card = _card([_h(f.get("title", "Send Request Form"), "h3", T["h_medium"], "left"),
                  form], dims(34, 34, 34, 34))
    card["settings"]["padding_mobile"] = dims(24, 18, 24, 18)
    w = _tracks([46, 50], 52)
    return _sec([_row([_col(left, w[0], extra={"flex_gap": gap(18)}),
                       _col([card], w[1])], 52, align="flex-start")],
                props.get("bg", "deep"), anchor=props.get("anchor", "request"))


# ═══════════════════════════════ closing band / footer ═══════════════════════════════

@block("dg.band")
def dg_band(props):
    """Capri's closing band: headline, tick list, call button — here carrying
    the client's own 'Ready to Protect Your Investment?' close."""
    left = [_h(props.get("title", ""), "h2", T["h_large"], "left")]
    if props.get("text"):
        left.append(_p(props["text"], "left"))
    if props.get("ticks"):
        left.append(_ticks(props["ticks"], inline=True))
    right = container([
        widget("heading", {"title": props.get("call_label", "Call Us Direct"),
                           "header_size": "div", "align": "left"},
               globals_={"title_color": color_ref(C["muted"]),
                         "typography_typography": typo_ref(T["eyebrow"])}),
        _phone_btn(props),
        widget("heading", {"title": props.get("book_label", "Online Booking"),
                           "header_size": "div", "align": "left"},
               globals_={"title_color": color_ref(C["muted"]),
                         "typography_typography": typo_ref(T["eyebrow"])}),
        _btn(props.get("cta_label", "Schedule Service Online"),
             props.get("cta_url", "#request"), "ghost", "far fa-calendar-alt"),
    ], {"content_width": "full", "flex_direction": "column", "flex_gap": gap(12)})
    w = _tracks([60, 34], 40)
    sec = _sec([_row([_col(left, w[0], extra={"flex_gap": gap(16)}),
                      _col([right], w[1])], 40, align="center")], "ground",
               pad=dims(80, 0, 80, 0),
               extra={"background_background": "gradient",
                      "background_gradient_angle": slider(135, "deg"),
                      "background_color_stop": slider(0, "%"),
                      "background_color_b_stop": slider(100, "%")})
    # Both stops must be set: Elementor's default second stop is #F2295B
    # (pink), so a gradient with only `background_color` renders navy-to-pink.
    # Navy into the logo grey — the brand's two colours in one band.
    sec["settings"]["__globals__"]["background_color_b"] = color_ref(DEEP)
    return sec


@block("dg.footer")
def dg_footer(props):
    brand = [widget("theme-site-logo", {"align": "left", "width": slider(84)})]
    if props.get("blurb"):
        brand.append(_p(props["blurb"], "left", small=True))

    def title(t):
        return _eyebrow(t, "left")

    def links(items):
        return widget("icon-list", {
            "icon_list": [repeater_item(text=i["label"], selected_icon=icon(i.get("icon", "fas fa-angle-right")),
                                        link=link(i.get("url", ""))) for i in items],
            "space_between": slider(10), "icon_size": slider(12),
        }, globals_={"icon_color": color_ref(HI), "text_color": color_ref("text"),
                     "icon_typography_typography": typo_ref(T["body_small"])})

    w = _tracks([38, 26, 30], 30)
    cols = [_col(brand, w[0], extra={"flex_gap": gap(16)})]
    for i, grp in enumerate(props.get("columns", [])[:2], start=1):
        cols.append(_col([title(grp["title"]), links(grp["links"])], w[i],
                         extra={"flex_gap": gap(14)}))
    legal = _p(props.get("legal", ""), "left", small=True, muted=True)
    return _sec([_row(cols, 30, align="flex-start"), _rule(), legal], "deep",
                pad=dims(70, 0, 34, 0))


@block("dg.stickybar")
def dg_stickybar(props):
    call = _phone_btn(props, "primary", props.get("call_label", "Call Now"))
    req = _btn(props.get("cta_label", "Request"), props.get("cta_url", "#request"), "ghost")
    return container([_row([call, req], 10, align="center", justify="center",
                           extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(10, 12, 10, 12), "background_background": "classic",
        "hide_desktop": "hidden-desktop", "hide_tablet": "hidden-tablet",
        "_position": "fixed", "_offset_orientation_v": "end",
        "_offset_y_end": slider(0), "_offset_x": slider(0),
        "width": slider(100, "%"), "_z_index": 998,
        "border_border": "solid", "border_width": dims(1, 0, 0, 0),
    }, globals_={"background_color": color_ref(DEEP), "border_color": color_ref(LINE)})
