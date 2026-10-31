"""
blocks_edit.py — EDIT by Edita: the printed menu, made into a website.

Built 2026-09-11. The design reference is the client's own price menu (see
clients/edit-by-edita/design-spec.json). It already speaks the register the
brief asks for — "a high end aesthetic clinic" — in five devices, and this
family reproduces each one rather than reaching for med-spa defaults:

    ed.hero        the masthead: huge Didone EDIT, tracked AESTHETIC INJECTOR,
                   the tagline between two hairlines
    ed.menu        hairline-ruled price columns: tracked serif caps header, a
                   (SMALL-CAPS NOTE), name left / price right, a Book action
    ed.packages    bordered package cells closed by a solid taupe SAVE bar
    ed.society     the EDIT Society membership band with its icon row
    ed.footer      the ruled sign-off line and the black consultation-fee bar

plus the connective tissue a site needs and a printed menu does not:
ed.header, ed.pagehead, ed.statement, ed.portrait, ed.highlights, ed.steps,
ed.faq, ed.contact, ed.cta, ed.bar.

Rules the menu sets and every factory follows: zero corner radius anywhere,
no shadows, 1px rules in the light taupe, paper-cream ground, black only for
the fee bar and the primary button. The three faces are the menu's three
voices — Bodoni Moda for the wordmark only, Cormorant Garamond for tracked
serif capitals and prices, Jost for tracked sub-lines and body.
"""
from __future__ import annotations

from .core import (
    container, widget, repeater_item, slider, dims, box, media, link,
    gap, color_ref, typo_ref, icon,
)
from .tokens import C, T
from .blocks import block, _row, _col, _tracks, _button, _heading, _text

# From clients/edit-by-edita/intake.json -> brand.extra_colors
TAUPE_LT = "tplt026"   # the menu's own taupe: rules and line icons only
PAPER = "papr027"

DIDONE = "Bodoni Moda"
SERIF = "Cormorant Garamond"
SANS = "Jost"
SCRIPT = "Pinyon Script"

GROUND = {"paper": C["surface"], "deep": C["surface_alt"], "dark": "secondary"}
PAD = dims(96, 20, 96, 20)
PAD_T = dims(72, 24, 72, 24)
PAD_M = dims(56, 18, 56, 18)


# ───────────────────────────── primitives ─────────────────────────────

def _sec(children, bg="paper", pad=None, extra=None, anchor=None, gap_px=36):
    s = {"content_width": "boxed", "boxed_width": slider(1240),
         "flex_direction": "column", "flex_gap": gap(gap_px),
         "padding": pad or PAD, "padding_tablet": PAD_T, "padding_mobile": PAD_M,
         "background_background": "classic"}
    if anchor:
        s["_element_id"] = anchor
    if extra:
        s.update(extra)
    return container(children, s, globals_={
        "background_color": color_ref(GROUND.get(bg, C["surface"]))})


def _type(family, size, weight="400", spacing=0.0, transform="none",
          line=1.3, size_t=None, size_m=None, spacing_m=None):
    """Inline typography for the menu's display voices. The kit's scale holds
    the heading and body steps; these are the one-off masthead and label
    settings that exist only because the printed menu sets them."""
    t = {"typography_typography": "custom",
         "typography_font_family": family,
         "typography_font_size": slider(size),
         "typography_font_weight": weight,
         "typography_letter_spacing": slider(spacing),
         "typography_text_transform": transform,
         "typography_line_height": slider(line, "em")}
    if size_t:
        t["typography_font_size_tablet"] = slider(size_t)
    if size_m:
        t["typography_font_size_mobile"] = slider(size_m)
    if spacing_m is not None:
        t["typography_letter_spacing_mobile"] = slider(spacing_m)
    return t


def _line(text, color="secondary", align="center", tag="div", **kw):
    return widget("heading", {"title": text, "header_size": tag,
                              "align": align, **_type(**kw)},
                  globals_={"title_color": color_ref(color)})


def _caps(text, size="h2", align="center", color="secondary"):
    """Tracked serif capitals — WRINKLE RELAXERS. The kit's section-title
    token, set uppercase for this brand."""
    return widget("heading", {"title": text, "header_size": size,
                              "align": align},
                  globals_={"title_color": color_ref(color),
                            "typography_typography": typo_ref(T["h_large"])})


def _note(text, align="center", color=None):
    """The parenthetical small-caps note — (PRICED PER UNIT)."""
    return _line(text, color or C["muted"], align, family=SANS, size=11,
                 weight="500", spacing=2.2, transform="uppercase")


def _rule(width=90, color=TAUPE_LT):
    return container([], {"content_width": "full", "flex_direction": "column",
                          "width": slider(width, "px"),
                          "min_height": slider(1),
                          "background_background": "classic"},
                     globals_={"background_color": color_ref(color)})


def _ruled(text, width=110, **kw):
    """Text between two hairlines — the menu's tagline and sign-off device."""
    return _row([_rule(width), _line(text, **kw), _rule(width)], 22,
                align="center", justify="center",
                extra={"flex_direction_mobile": "row", "flex_wrap": "nowrap"})


def _btn(label, href, outline=False, small=False):
    """Square, thin, tracked — the menu has no rounded corner anywhere."""
    b = _button(label, href, "ghost" if outline else "accent", None)
    s = b["settings"]
    s["border_radius"] = box(0)
    s["text_padding"] = dims(12 if small else 16, 26 if small else 36,
                             12 if small else 16, 26 if small else 36)
    if outline:
        s["__globals__"].update({"button_text_color": color_ref("secondary"),
                                 "border_color": color_ref("secondary")})
    return b


def _buttons(items, align="center"):
    out = [_btn(i["label"], i["href"], i.get("outline", False))
           for i in items if i]
    return _row(out, 14, align="center",
                justify="center" if align == "center" else "flex-start",
                extra={"flex_direction_mobile": "row", "flex_wrap": "wrap"})


def _ico(cls, size=26, color=None):
    return widget("icon", {"selected_icon": icon(cls), "size": slider(size),
                           "align": "center", "view": "default"},
                  globals_={"primary_color": color_ref(color or C["ink_primary"])})


def _cell(children, width, borders=(0, 0, 0, 0), pad=None, extra=None,
          width_t=None):
    s = {"content_width": "full", "flex_direction": "column",
         "flex_gap": gap(14), "width": slider(width, "%"),
         "width_tablet": slider(width_t or 100, "%"),
         "width_mobile": slider(100, "%"),
         "padding": pad or dims(34, 34, 34, 34),
         "padding_mobile": dims(28, 6, 28, 6),
         "border_border": "solid", "border_width": dims(*borders)}
    if extra:
        s.update(extra)
    return container(children, s, globals_={"border_color": color_ref(TAUPE_LT)})


def _wordmark(size, spacing, size_t=None, size_m=None, spacing_m=None,
              tag="div", color="secondary", href=None):
    s = {"title": "EDIT", "header_size": tag, "align": "center",
         **_type(DIDONE, size, "400", spacing, line=1.0, size_t=size_t,
                 size_m=size_m, spacing_m=spacing_m)}
    if href:
        s["link"] = link(href)
    return widget("heading", s, globals_={"title_color": color_ref(color)})


# ─────────────────────────────── chrome ───────────────────────────────

@block("ed.header")
def ed_header(props):
    mark = container([
        _wordmark(30, 9, size_m=24, spacing_m=6, href="/"),
        _line("AESTHETIC INJECTOR", family=SANS, size=8, weight="500",
              spacing=4.4),
    ], {"content_width": "full", "flex_direction": "column",
        "flex_align_items": "flex-start", "flex_gap": gap(4)})
    mark["elements"][0]["settings"]["align"] = "left"
    mark["elements"][1]["settings"]["align"] = "left"
    nav = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"), "layout": "horizontal",
        "align_items": "center", "pointer": "underline",
        "menu_space_between": slider(40), "toggle_align": "right",
        "dropdown": "mobile",
    }, globals_={"color_menu_item": color_ref("secondary"),
                 "color_menu_item_hover": color_ref(C["ink_primary"]),
                 "pointer_color_menu_item_hover": color_ref(C["ink_primary"]),
                 "menu_typography_typography": typo_ref("accent")})
    book = _btn(props["cta"]["label"], props["cta"]["href"], small=True)
    w = _tracks([30, 50, 20], 20)
    row = _row([
        _col([mark], w[0], extra={"flex_justify_content": "center",
                                  "width_mobile": slider(46, "%")}),
        _col([nav], w[1], extra={"flex_align_items": "center",
                                 "flex_justify_content": "center",
                                 "width_mobile": slider(14, "%")}),
        _col([book], w[2], extra={"flex_align_items": "flex-end",
                                  "flex_justify_content": "center",
                                  "width_mobile": slider(40, "%")}),
    ], 20, align="center", extra={"flex_direction_mobile": "row",
                                  "flex_wrap": "nowrap"})
    return container([row], {
        "content_width": "boxed", "boxed_width": slider(1240),
        "flex_direction": "column",
        "padding": dims(20, 20, 20, 20), "padding_mobile": dims(14, 16, 14, 16),
        "border_border": "solid", "border_width": dims(0, 0, 1, 0),
        "background_background": "classic",
        "sticky": "top", "sticky_on": ["desktop", "tablet", "mobile"],
        "_z_index": 99,
    }, globals_={"background_color": color_ref(C["surface"]),
                 "border_color": color_ref(TAUPE_LT)})


@block("ed.bar")
def ed_bar(props):
    """The black consultation-fee bar from the foot of the menu."""
    return container([
        _line(props["title"], C["surface"], family=SANS, size=14, weight="500",
              spacing=4.2, transform="uppercase", size_m=12, spacing_m=2.4),
        _line(props.get("sub", ""), C["surface"], family=SERIF, size=17,
              weight="400", spacing=0.2),
    ], {"content_width": "full", "flex_direction": "column",
        "flex_gap": gap(6), "padding": dims(22, 20, 22, 20),
        "background_background": "classic"},
        globals_={"background_color": color_ref("secondary")})


@block("ed.footer")
def ed_footer(props):
    links = widget("icon-list", {
        "icon_list": [repeater_item(text=i["text"], link=link(i["href"]),
                                    selected_icon={"value": "", "library": ""})
                      for i in props.get("links", [])],
        "view": "inline", "space_between": slider(34),
    }, globals_={"text_color": color_ref("secondary"),
                 "icon_typography_typography": typo_ref("accent")})
    top = _sec([
        _wordmark(56, 20, size_m=40, spacing_m=12),
        _line("AESTHETIC INJECTOR", family=SANS, size=11, weight="500",
              spacing=6.5, size_m=9, spacing_m=4),
        _line(props["practitioner"], C["muted"], family=SERIF, size=18,
              weight="500"),
        container([links], {"content_width": "full", "flex_direction": "column",
                            "flex_align_items": "center",
                            "margin": dims(10, 0, 6, 0)}),
        _ruled(props["sign_off"], 90, color=C["muted"], family=SANS, size=11,
               weight="500", spacing=3.2, transform="uppercase", size_m=9,
               spacing_m=1.6),
        _line(props["legal"], C["muted"], family=SANS, size=12, weight="400",
              spacing=0.3),
    ], "paper", pad=dims(80, 20, 44, 20), gap_px=14,
        extra={"flex_align_items": "center", "border_border": "solid",
               "border_width": dims(1, 0, 0, 0)})
    top["settings"]["__globals__"]["border_color"] = color_ref(TAUPE_LT)
    return container([top, ed_bar(props["bar"])],
                     {"content_width": "full", "flex_direction": "column",
                      "flex_gap": gap(0)})


# ─────────────────────────────── openers ──────────────────────────────

@block("ed.hero")
def ed_hero(props):
    """The menu masthead, at web scale. No photograph: the typographic lockup
    is the most expensive-looking thing the brand owns, and it does not wait
    for a photoshoot."""
    kids = [
        _wordmark(168, 34, size_t=118, size_m=76, spacing_m=12),
        # The SEO H1 is the tracked line under the wordmark — it carries the
        # focus keyword, where the four-letter wordmark cannot.
        widget("heading", {"title": props["h1"], "header_size": "h1",
                           "align": "center",
                           **_type(SANS, 24, "400", 13, "uppercase",
                                   size_t=20, size_m=14, spacing_m=5.5)},
               globals_={"title_color": color_ref("secondary")}),
        container([_ruled(props["tagline"], 120, family=SERIF, size=19,
                          weight="500", spacing=6, transform="uppercase",
                          size_m=13, spacing_m=3)],
                  {"content_width": "full", "flex_direction": "column",
                   "margin": dims(14, 0, 8, 0)}),
    ]
    if props.get("intro"):
        kids.append(container([_text(props["intro"], "center")],
                              {"content_width": "full",
                               "flex_direction": "column",
                               "width": slider(640, "px"),
                               "width_mobile": slider(100, "%")}))
    if props.get("practitioner"):
        kids.append(_line(props["practitioner"], C["muted"], family=SERIF,
                          size=18, weight="500", spacing=1))
    kids.append(container([_buttons(props.get("buttons", []))],
                          {"content_width": "full", "flex_direction": "column",
                           "margin": dims(12, 0, 0, 0)}))
    return _sec(kids, "paper", pad=dims(120, 20, 112, 20), gap_px=16,
                extra={"flex_align_items": "center"})


@block("ed.pagehead")
def ed_pagehead(props):
    kids = [_note(props.get("note", "")),
            widget("heading", {"title": props["h1"], "header_size": "h1",
                               "align": "center"},
                   globals_={"title_color": color_ref("secondary"),
                             "typography_typography": typo_ref(T["hero"])}),
            _ruled(props.get("tagline", "Not changed. Edited."), 80,
                   family=SERIF, size=16, weight="500", spacing=5,
                   transform="uppercase", size_m=12, spacing_m=2.4)]
    if props.get("intro"):
        kids.append(container([_text(props["intro"], "center")],
                              {"content_width": "full",
                               "flex_direction": "column",
                               "width": slider(660, "px"),
                               "width_mobile": slider(100, "%")}))
    if props.get("buttons"):
        kids.append(_buttons(props["buttons"]))
    return _sec(kids, "paper", pad=dims(96, 20, 72, 20), gap_px=18,
                extra={"flex_align_items": "center"})


@block("ed.statement")
def ed_statement(props):
    kids = []
    if props.get("note"):
        kids.append(_note(props["note"]))
    kids.append(_caps(props["title"]))
    kids.append(_rule(60))
    for p in props.get("paras", []):
        kids.append(_text(p, "center"))
    if props.get("buttons"):
        kids.append(_buttons(props["buttons"]))
    inner = container(kids, {"content_width": "full", "flex_direction": "column",
                             "flex_align_items": "center", "flex_gap": gap(18),
                             "width": slider(760, "px"),
                             "width_mobile": slider(100, "%")})
    return _sec([inner], props.get("bg", "paper"),
                extra={"flex_align_items": "center"})


@block("ed.portrait")
def ed_portrait(props):
    img = widget("image", {
        "image": media(props.get("image", {}).get("url", ""),
                       props.get("image", {}).get("alt", props["name"])),
        "image_size": "full", "width": slider(100, "%"), "height": slider(560),
        "height_mobile": slider(380), "object-fit": "cover",
        "image_border_radius": box(0)})
    body = [_note(props.get("note", ""), "left"),
            widget("heading", {"title": props["name"], "header_size": "h2",
                               "align": "left"},
                   globals_={"title_color": color_ref("secondary"),
                             "typography_typography": typo_ref(T["h_large"])}),
            _line(props.get("credentials", ""), C["ink_primary"], "left",
                  family=SANS, size=12, weight="500", spacing=3,
                  transform="uppercase"),
            _rule(60)]
    body += [_text(p, "left") for p in props.get("paras", [])]
    if props.get("buttons"):
        body.append(_buttons(props["buttons"], "left"))
    w = _tracks([44, 52], 56)
    return _sec([_row([_col([img], w[0]),
                       _col(body, w[1], extra={"flex_gap": gap(16),
                                               "flex_justify_content": "center"})],
                      56, align="center")], props.get("bg", "deep"))


# ─────────────────────────────── the menu ─────────────────────────────

def _price_row(name, price, size=20):
    return _row([
        _line(name, "secondary", "left", family=SERIF, size=size, weight="500",
              size_m=size - 2),
        _line(price, "secondary", "right", family=SERIF, size=size,
              weight="500", size_m=size - 2),
    ], 16, align="baseline", justify="space-between",
        extra={"flex_direction_mobile": "row", "flex_wrap": "nowrap"})


def _category(c):
    kids = [_caps(c["title"], "h2"),
            _note(c["note"]) if c.get("note") else None]
    kids = [k for k in kids if k]
    if c.get("desc"):
        kids.append(_text(c["desc"], "center", small=True))
    kids.append(container([_price_row(r["name"], r["price"])
                           for r in c.get("rows", [])],
                          {"content_width": "full", "flex_direction": "column",
                           "flex_gap": gap(10), "margin": dims(6, 0, 0, 0)}))
    if c.get("areas"):
        a = c["areas"]
        kids.append(_rule(220))
        kids.append(_note(a["title"]))
        kids.append(container([_price_row("·  " + r["name"], r["units"], 16)
                               for r in a["rows"]],
                              {"content_width": "full",
                               "flex_direction": "column", "flex_gap": gap(6)}))
    if c.get("footnote"):
        kids.append(_line(c["footnote"], "secondary", family=SERIF, size=19,
                          weight="400"))
        kids[-1]["settings"]["title"] = f"<em>{c['footnote']}</em>"
    if c.get("book"):
        kids.append(container([_btn(c["book"]["label"], c["book"]["href"],
                                    outline=True, small=True)],
                              {"content_width": "full",
                               "flex_direction": "column",
                               "flex_align_items": "center",
                               "margin": dims(10, 0, 0, 0)}))
    return kids


@block("ed.menu")
def ed_menu(props):
    """The price menu. Categories in pairs, each pair one row split by a
    vertical hairline, rows separated by a horizontal hairline — the menu's
    ruled columns at a width a phone can read. Every category ends with its
    own Book action (the IC Beauty model, and the brief's 'booking option')."""
    cats = props.get("categories", [])
    w = _tracks([1, 1], 0)
    rows = []
    for i in range(0, len(cats), 2):
        pair = cats[i:i + 2]
        last = i + 2 >= len(cats)
        cells = []
        for j, c in enumerate(pair):
            cell = _cell(_category(c), w[j] if len(pair) == 2 else 100,
                         borders=(0, 1 if (j == 0 and len(pair) == 2) else 0,
                                  0 if last else 1, 0),
                         pad=dims(44, 44, 44, 44),
                         extra={"flex_align_items": "stretch",
                                **({"_element_id": c["anchor"]}
                                   if c.get("anchor") else {})})
            cell["settings"]["border_width_mobile"] = dims(0, 0, 1, 0)
            cells.append(cell)
        rows.append(_row(cells, 0, align="stretch"))
    head = []
    if props.get("title"):
        head = [_note(props.get("note", "")), _caps(props["title"]), _rule(60)]
    return _sec(head + [container(rows, {"content_width": "full",
                                         "flex_direction": "column",
                                         "flex_gap": gap(0)})],
                props.get("bg", "paper"), anchor=props.get("anchor"),
                extra={"flex_align_items": "center"}, gap_px=18)


@block("ed.packages")
def ed_packages(props):
    """SIGNATURE EDIT PACKAGES — bordered cells, each closed by the solid
    taupe SAVE bar where the menu has one."""
    pk = props.get("items", [])
    w = _tracks([1] * len(pk), 0)[0]
    cells = []
    for n, p in enumerate(pk):
        bullets = "<ul>" + "".join(f"<li>{b}</li>" for b in p.get("items", [])) + "</ul>"
        body = [_ico(p.get("icon", "far fa-star"), 30, TAUPE_LT),
                _line(p["name"], "secondary", family=SERIF, size=17,
                      weight="600", spacing=1.2, transform="uppercase"),
                _line(p["price"], "secondary", family=SERIF, size=30,
                      weight="500")]
        if p.get("lede"):
            body.append(_text(p["lede"], "center", small=True))
        body.append(_text(bullets, "left", small=True))
        inner = container(body, {"content_width": "full",
                                 "flex_direction": "column",
                                 "flex_align_items": "center",
                                 "flex_gap": gap(10), "_flex_grow": 1,
                                 "padding": dims(28, 16, 22, 16)})
        kids = [inner]
        if p.get("save"):
            kids.append(container([_line(p["save"], C["surface"], family=SANS,
                                         size=12, weight="500", spacing=2.6,
                                         transform="uppercase")],
                                  {"content_width": "full",
                                   "flex_direction": "column",
                                   "padding": dims(10, 8, 10, 8),
                                   "background_background": "classic"},
                                  globals_={"background_color": color_ref("primary")}))
        cells.append(container(kids, {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(0), "flex_justify_content": "space-between",
            "width": slider(w, "%"), "width_tablet": slider(33.33, "%"),
            "width_mobile": slider(100, "%"),
            "border_border": "solid",
            "border_width": dims(1, 1, 1, 1 if n == 0 else 0),
            "border_width_mobile": dims(1, 1, 1, 1),
            "background_background": "classic",
        }, globals_={"background_color": color_ref(C["surface"]),
                     "border_color": color_ref(TAUPE_LT)}))
    head = [_ruled(props["title"], 120, family=SERIF, size=30, weight="500",
                   spacing=5, transform="uppercase", size_m=19, spacing_m=2)]
    if props.get("intro"):
        head.append(container([_text(props["intro"], "center")],
                              {"content_width": "full",
                               "flex_direction": "column",
                               "width": slider(700, "px"),
                               "width_mobile": slider(100, "%")}))
    row = _row(cells, 0, align="stretch", extra={"flex_wrap": "wrap"})
    kids = head + [row]
    if props.get("buttons"):
        kids.append(_buttons(props["buttons"]))
    return _sec(kids, props.get("bg", "paper"), anchor=props.get("anchor"),
                extra={"flex_align_items": "center"}, gap_px=26)


@block("ed.society")
def ed_society(props):
    """The EDIT Society band — lockup | membership | six benefits."""
    lock = container([
        _wordmark(46, 12),
        widget("heading", {"title": "Society", "header_size": "div",
                           "align": "center",
                           **_type(SCRIPT, 40, "400", 0, line=0.9)},
               globals_={"title_color": color_ref("secondary")}),
    ], {"content_width": "full", "flex_direction": "column",
        "flex_gap": gap(0), "flex_align_items": "center"})
    price = container([
        _line("Membership", "secondary", family=SERIF, size=19, weight="600",
              spacing=2, transform="uppercase"),
        _line(props["price"], "secondary", family=SANS, size=15, weight="400",
              spacing=2, transform="uppercase"),
    ], {"content_width": "full", "flex_direction": "column",
        "flex_gap": gap(6), "flex_align_items": "center"})
    bens = props.get("benefits", [])
    # Sized against the benefits column's REAL width (~640px inside the
    # band), not the 1240 page — V11 caught 6 x 15.86% + gaps = 104%.
    bw = _tracks([1] * max(len(bens), 1), 12, container=640)[0]
    ben_cells = []
    for b in bens:
        circ = container([_ico(b["icon"], 22, C["ink_primary"])], {
            "content_width": "full", "flex_direction": "column",
            "flex_justify_content": "center", "flex_align_items": "center",
            "width": slider(58, "px"), "min_height": slider(58),
            "border_radius": box(999), "border_border": "solid",
            "border_width": box(1)},
            globals_={"border_color": color_ref(TAUPE_LT)})
        ben_cells.append(container([circ, _text(b["text"], "center", small=True)],
                                   {"content_width": "full",
                                    "flex_direction": "column",
                                    "flex_align_items": "center",
                                    "flex_gap": gap(8),
                                    "width": slider(bw, "%"),
                                    "width_tablet": slider(33.33, "%"),
                                    "width_mobile": slider(50, "%")}))
    w = _tracks([20, 18, 58], 0)
    band = _row([
        _cell([lock], w[0], borders=(0, 1, 0, 0), pad=dims(18, 20, 18, 20),
              extra={"flex_justify_content": "center"}),
        _cell([price], w[1], borders=(0, 1, 0, 0), pad=dims(18, 20, 18, 20),
              extra={"flex_justify_content": "center"}),
        _cell([_row(ben_cells, 12, align="flex-start",
                    extra={"flex_wrap": "wrap"})], w[2],
              pad=dims(18, 20, 18, 20), extra={"flex_justify_content": "center"}),
    ], 0, align="stretch")
    for c in band["elements"]:
        c["settings"]["border_width_mobile"] = dims(0, 0, 0, 0)
    framed = container([band], {"content_width": "full",
                                "flex_direction": "column",
                                "padding": dims(24, 20, 24, 20),
                                "border_border": "solid", "border_width": box(1)},
                       globals_={"border_color": color_ref(TAUPE_LT)})
    kids = []
    if props.get("title"):
        kids += [_note(props.get("note", "")), _caps(props["title"])]
    if props.get("intro"):
        kids.append(container([_text(props["intro"], "center")],
                              {"content_width": "full",
                               "flex_direction": "column",
                               "width": slider(700, "px"),
                               "width_mobile": slider(100, "%")}))
    kids.append(framed)
    if props.get("buttons"):
        kids.append(_buttons(props["buttons"]))
    return _sec(kids, props.get("bg", "deep"), anchor=props.get("anchor"),
                extra={"flex_align_items": "center"}, gap_px=22)


# ─────────────────────────────── the rest ─────────────────────────────

@block("ed.highlights")
def ed_highlights(props):
    items = props.get("items", [])
    w = _tracks([1] * len(items), 0)[0]
    cells = []
    for n, it in enumerate(items):
        cells.append(_cell([
            _note(it.get("note", "")),
            _caps(it["title"], "h3"),
            _line(it["price"], C["ink_primary"], family=SERIF, size=22,
                  weight="500"),
            _text(it["text"], "center", small=True),
            container([_btn(it["link"]["label"], it["link"]["href"],
                            outline=True, small=True)],
                      {"content_width": "full", "flex_direction": "column",
                       "flex_align_items": "center"}),
        ], w, borders=(0, 0, 0, 0 if n == 0 else 1), pad=dims(10, 26, 10, 26),
            width_t=50, extra={"flex_align_items": "center",
                               "flex_justify_content": "space-between"}))
        cells[-1]["settings"]["border_width_mobile"] = dims(0, 0, 0, 0)
    head = [_note(props.get("note", "")), _caps(props["title"]), _rule(60)]
    return _sec(head + [_row(cells, 0, align="stretch")],
                props.get("bg", "paper"), extra={"flex_align_items": "center"},
                gap_px=22)


@block("ed.steps")
def ed_steps(props):
    st = props.get("steps", [])
    w = _tracks([1] * len(st), 0)[0]
    numerals = ["I", "II", "III", "IV"]
    cells = [_cell([
        _line(numerals[n], C["ink_primary"], family=DIDONE, size=46,
              weight="400"),
        _caps(s["title"], "h3"),
        _text(s["text"], "center", small=True),
    ], w, borders=(0, 0, 0, 0 if n == 0 else 1), pad=dims(8, 30, 8, 30),
        extra={"flex_align_items": "center"}) for n, s in enumerate(st)]
    for c in cells:
        c["settings"]["border_width_mobile"] = dims(0, 0, 0, 0)
    head = [_note(props.get("note", "")), _caps(props["title"]), _rule(60)]
    kids = head + [_row(cells, 0, align="stretch")]
    if props.get("footnote"):
        kids.append(_text(props["footnote"], "center", small=True))
    if props.get("buttons"):
        kids.append(_buttons(props["buttons"]))
    return _sec(kids, props.get("bg", "deep"),
                extra={"flex_align_items": "center"}, gap_px=24)


@block("ed.faq")
def ed_faq(props):
    titles, panes = [], []
    for q in props.get("items", []):
        titles.append(repeater_item(item_title=q["q"]))
        panes.append(container([_text(q["a"], "left", small=True)],
                               {"content_width": "full",
                                "flex_direction": "column",
                                "padding": dims(0, 0, 22, 0)}))
    acc = widget("nested-accordion", {
        "items": titles, "default_state": "all_collapsed", "title_tag": "h3",
        "accordion_item_title_icon_position": "right",
        "accordion_item_title_space_between": slider(0),
        "accordion_item_title_distance_from_content": slider(0),
        "accordion_border__border": "solid",
        "accordion_border__width": dims(0, 0, 1, 0),
        "accordion_item_title_icon": icon("fas fa-plus"),
        "accordion_item_title_icon_active": icon("fas fa-minus"),
    }, globals_={
        "accordion_item_title_color": color_ref("secondary"),
        "accordion_item_title_typography_typography": typo_ref(T["h_medium"]),
        "accordion_item_title_icon_color": color_ref(C["ink_primary"]),
        "accordion_border__color": color_ref(TAUPE_LT),
    }, children=panes)
    wrap = container([acc], {"content_width": "full", "flex_direction": "column",
                             "width": slider(820, "px"),
                             "width_mobile": slider(100, "%")})
    head = [_note(props.get("note", "Questions")),
            _caps(props.get("title", "Before you book")), _rule(60)]
    return _sec(head + [wrap], props.get("bg", "paper"),
                extra={"flex_align_items": "center"}, gap_px=20)


@block("ed.contact")
def ed_contact(props):
    lines = []
    for l in props.get("details", []):
        val = (f'<a href="{l["href"]}">{l["value"]}</a>' if l.get("href")
               else l["value"])
        lines.append(container([
            _note(l["label"], "left"),
            _text(f"<p>{val}</p>", "left"),
        ], {"content_width": "full", "flex_direction": "column",
            "flex_gap": gap(2), "padding": dims(14, 0, 14, 0),
            "border_border": "solid", "border_width": dims(0, 0, 1, 0)},
            globals_={"border_color": color_ref(TAUPE_LT)}))
    left = [_caps(props["title"], "h2", "left"), _rule(60)] + \
        ([_text(props["intro"], "left")] if props.get("intro") else []) + lines
    fields = []
    for f in props.get("fields", []):
        item = {"custom_id": f["id"], "field_type": f.get("type", "text"),
                "field_label": f["label"], "placeholder": f.get("placeholder", ""),
                "required": "true" if f.get("required") else "",
                "width": str(f.get("width", 100))}
        if f.get("options"):
            item["field_options"] = "\n".join(f["options"])
        if f.get("rows"):
            item["rows"] = f["rows"]
        if f.get("acceptance_text"):
            item["acceptance_text"] = f["acceptance_text"]
        fields.append(repeater_item(**item))
    form = widget("form", {
        "form_name": props.get("form_name", "Enquiry"),
        "form_fields": fields,
        "button_text": props.get("submit", "Send"),
        "button_size": "md", "input_size": "md",
        "button_border_radius": box(0),
        "field_border_radius": box(0),
        "email_to": props.get("email", ""),
        "email_subject": props.get("subject", "New enquiry — EDIT by Edita"),
        "success_message": props.get("success", "Thank you — your message has been sent."),
    }, globals_={"button_background_color": color_ref("secondary"),
                 "button_text_color": color_ref(C["surface"]),
                 "field_text_color": color_ref("secondary"),
                 "field_border_color": color_ref(TAUPE_LT)})
    right = [_note(props.get("form_note", "Send a message"), "left"), form]
    if props.get("privacy"):
        right.append(_text(props["privacy"], "left", small=True))
    w = _tracks([42, 54], 56)
    return _sec([_row([_col(left, w[0], extra={"flex_gap": gap(12)}),
                       _col(right, w[1], extra={"flex_gap": gap(14)})],
                      56, align="flex-start")], props.get("bg", "paper"))


@block("ed.cta")
def ed_cta(props):
    kids = [_note(props.get("note", "")), _caps(props["title"]), _rule(60)]
    if props.get("text"):
        kids.append(container([_text(props["text"], "center")],
                              {"content_width": "full",
                               "flex_direction": "column",
                               "width": slider(620, "px"),
                               "width_mobile": slider(100, "%")}))
    kids.append(_buttons(props.get("buttons", [])))
    return _sec(kids, props.get("bg", "deep"),
                extra={"flex_align_items": "center"}, gap_px=18)
