"""
blocks_plaunch.py — the PeptideLaunch devices.

Three factories, and each exists because the client's copy document asks for a
shape that no block in `blocks.py` renders. The rule for adding a module here
is that the nearest existing block is a SUBSTITUTION, not a fit:

    pl.compare   a real feature matrix — free column against premium column,
                 read ACROSS a row. Two adjacent bullet lists cannot be read
                 that way and nothing in the repo renders a table.
    pl.products  a theme card with TWO calls to action. `pricing.cards` is the
                 near-miss and renders exactly one; on a theme shop "Live
                 Demo" is how the sale is made and "Buy" is how it closes, so
                 dropping either one breaks the funnel.
    pl.roi       two conversion scenarios with their arithmetic shown side by
                 side and the difference called out. `stats.band` renders
                 counters with no comparison and no working.

Everything else on this site is composed from the generic families, which is
the point: a client module is for the devices that are genuinely this brand's,
not a private copy of the whole system.

Palette discipline, from design-spec.json: the accent is the logo's ONE filled
node out of four. It fills a button, a numeral, a tick column and a featured
card's border — never a section ground. The navy is the spotlight.
"""
from __future__ import annotations

from .core import (
    container, widget, repeater_item, slider, dims, box, link,
    gap, color_ref, typo_ref, icon,
)
from .tokens import C, T
from .blocks import (
    block, _row, _col, _tracks, _grid_widths, _button, _heading, _text,
    _eyebrow, _section, CARD_SHADOW_SOFT,
)

# One radius for this kit's cards and panels. design-spec: squarer than a
# consumer brand, rounder than a lab catalogue.
R_PL = box(14)
R_PL_TABLE = box(16)


def _pl_head(props, on_dark=False, align="left"):
    """Section opener: caps eyebrow, H2, one line of intro."""
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], on_dark=on_dark))
    if props.get("heading"):
        kids.append(_heading(props["heading"], "h2", T["h_large"], align=align,
                             on_dark=on_dark, tone="dark" if on_dark else "brand"))
    if props.get("intro"):
        kids.append(_text(props["intro"], align=align, on_dark=on_dark))
    return _col(kids, extra={"flex_gap": gap(12),
                             "margin": dims(0, 0, 34, 0)})


def _pl_mark(cell, on_alt=False):
    """One comparison cell: a tick, an em-dash, or a tick with a qualifier.

    The em-dash matters. A blank cell reads as "we forgot to fill this in";
    an explicit dash reads as "no, and we are telling you so", which is the
    voice the whole comparison is written in ("Honesty saves us both support
    tickets").
    """
    mark = cell.get("mark", "")
    kids = []
    if mark == "yes":
        kids.append(widget("icon", {
            "selected_icon": icon("fas fa-circle-check"),
            "size": slider(15), "align": "left", "view": "default",
        }, globals_={"primary_color": color_ref(C["ink_primary"])}))
    elif mark == "no":
        kids.append(widget("heading", {
            "title": "&mdash;", "header_size": "div", "align": "left",
        }, globals_={"title_color": color_ref(C["muted"]),
                     "typography_typography": typo_ref(T["body_small"])}))
    if cell.get("text"):
        kids.append(_text(cell["text"], small=True))
    if not kids:
        kids.append(_text("&mdash;", small=True))
    return kids


@block("pl.compare")
def pl_compare(props):
    """Feature matrix — the honest free-vs-premium comparison.

    Built as flex rows rather than a `table` widget because the repo's widget
    registry has no table, and because a flex row can carry a real icon and a
    qualifying phrase in the same cell ("Basic", "Per-product tabs + batch
    fields") where a text table would flatten both.

    The comparison stays THREE COLUMNS WIDE at every breakpoint, including
    mobile. That is a deliberate exception to this repo's stack-on-mobile
    default: a comparison table exists to be read across, and a stacked one is
    two lists again — the exact thing this device was written to avoid. Type
    drops to the small step and the feature column takes the slack.
    """
    cols = props.get("columns", [])
    rows = props.get("rows", [])
    ratios = [44] + [(100 - 44) / max(len(cols), 1)] * len(cols)
    w = _tracks(ratios, 18)

    def line(children_by_col, head=False, last=False):
        cells = []
        for i, kids in enumerate(children_by_col):
            featured = i > 0 and cols[i - 1].get("featured")
            cells.append(container(kids, {
                "content_width": "full", "flex_direction": "column",
                "flex_gap": gap(6),
                "width": slider(w[i], "%"),
                # Held at the desktop width on tablet AND mobile — see the
                # docstring. `_col` would stack it.
                "width_tablet": slider(w[i], "%"),
                "width_mobile": slider(w[i], "%"),
                "padding": dims(16, 18, 16, 18),
                "padding_mobile": dims(12, 10, 12, 10),
                **({"background_background": "classic"} if featured else {}),
            }, globals_=({"background_color": color_ref(C["surface"])}
                         if featured else None)))
        return container([container(cells, {
            "content_width": "full", "flex_direction": "row",
            "flex_gap": gap(18), "flex_gap_mobile": gap(8),
            "flex_align_items": "flex-start",
            "flex_wrap": "nowrap",
            # The row must not become a column on mobile.
            "flex_direction_mobile": "row",
        })], {
            "content_width": "full", "flex_direction": "column",
            "border_border": "solid",
            "border_width": dims(0, 0, 0 if last else 1, 0),
            **({"background_background": "classic"} if head else {}),
        }, globals_={"border_color": color_ref(C["border"]),
                     **({"background_color": color_ref(C["surface_alt"])}
                        if head else {})})

    header = [[_text(props.get("row_label", "Feature"), small=True)]]
    for c in cols:
        h = [_heading(c["title"], "h3", T["h_small"], align="left")]
        if c.get("note"):
            h.append(_text(c["note"], small=True))
        header.append(h)
    lines = [line(header, head=True)]

    for n, r in enumerate(rows):
        body = [[_text("<strong>" + r["feature"] + "</strong>", small=True)]]
        for i, cell in enumerate(r.get("cells", [])):
            body.append(_pl_mark(cell, on_alt=cols[i].get("featured", False)))
        lines.append(line(body, last=(n == len(rows) - 1)))

    table = container(lines, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(0),
        "border_radius": R_PL_TABLE,
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["white"]),
                 "border_color": color_ref(C["border"])})

    kids = [_pl_head(props)] if props.get("heading") else []
    kids.append(table)
    if props.get("footnote"):
        kids.append(_text(props["footnote"], small=True))
    return _section(kids, bg=props.get("bg", "white"))


@block("pl.products")
def pl_products(props):
    """Theme / product cards carrying a price and two calls to action.

    Two buttons, always in the same order: the ghost "Live Demo" first, the
    filled "Buy" second. A visitor who has not seen the theme is not going to
    buy it, so the evaluation action leads and the purchase action closes —
    and the filled button being second means the accent lands where the eye
    exits the card.

    `featured` lifts one card with the brand colour rather than a shadow,
    the same convention `pricing.cards` uses, so the two read as one system
    when they appear on sibling pages.
    """
    items = props.get("items", [])
    width, width_t = _grid_widths(min(len(items), 3) or 1, 24)
    cards = []
    for it in items:
        feat = it.get("featured", False)
        kids = []
        if it.get("badge"):
            kids.append(container([widget("heading", {
                "title": it["badge"], "header_size": "div", "align": "center",
            }, globals_={"title_color": color_ref(C["on_accent"]),
                         "typography_typography": typo_ref(T["eyebrow"])})], {
                "content_width": "full", "flex_direction": "column",
                "padding": dims(5, 13, 5, 13),
                "border_radius": box(999),
                "width": slider(45, "%"),
                "background_background": "classic",
            }, globals_={"background_color": color_ref(C["accent_fill"])}))
        kids.append(_heading(it["name"], "h3", T["h_medium"], align="left"))
        if it.get("tagline"):
            kids.append(_text(it["tagline"], small=True))
        if it.get("price"):
            kids.append(widget("heading", {
                "title": it["price"], "header_size": "div", "align": "left",
            }, globals_={"title_color": color_ref(C["ink_primary"]),
                         "typography_typography": typo_ref(T["h_small"])}))
        kids.append(widget("divider", {
            "weight": slider(1), "gap": slider(14), "look": "line",
        }, globals_={"color": color_ref(C["border"])}))
        kids.append(widget("icon-list", {
            "icon_list": [repeater_item(text=p,
                                        selected_icon=icon("fas fa-circle-check"),
                                        link=link("")) for p in it.get("points", [])],
            "space_between": slider(11), "icon_size": slider(14),
        }, globals_={"icon_color": color_ref(C["ink_primary"]),
                     "text_color": color_ref("text"),
                     "icon_typography_typography": typo_ref(T["body_small"])}))
        actions = []
        if it.get("demo"):
            actions.append(_button(it["demo"]["label"], it["demo"]["href"],
                                   "ghost", None))
        if it.get("buy"):
            actions.append(_button(it["buy"]["label"], it["buy"]["href"],
                                   "accent", None))
        if actions:
            kids.append(_row(actions, gap_px=10,
                             extra={"margin": dims(6, 0, 0, 0),
                                    "flex_direction_mobile": "row"}))
        cards.append(container(kids, {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(12),
            "width": slider(width, "%"),
            "width_tablet": slider(width_t, "%"),
            "width_mobile": slider(100, "%"),
            "padding": dims(30, 28, 32, 28),
            "border_radius": R_PL,
            "border_border": "solid",
            "border_width": box(2) if feat else box(1),
            "background_background": "classic",
            **CARD_SHADOW_SOFT,
        }, globals_={
            "background_color": color_ref(C["white"]),
            "border_color": color_ref(C["accent_fill"] if feat else C["border"]),
        }))

    kids = [_pl_head(props)] if props.get("heading") else []
    kids.append(_row(cards, gap_px=24, align="stretch"))
    if props.get("footnote"):
        kids.append(_text(props["footnote"], small=True,
                          align="center"))
    return _section(kids, bg=props.get("bg", "white"))


@block("pl.roi")
def pl_roi(props):
    """The conversion-rate argument, with the arithmetic left in.

    Two scenario cards on the navy spotlight ground, each showing the rate,
    the working, and the monthly figure it produces; then the difference as a
    single line beneath. The persuasion is entirely in seeing the two sums
    next to each other — which is why this is a device and not a paragraph
    containing five numbers.

    `footnote` is not optional in practice. These are industry-typical figures,
    not a promise, and the client's own copy note says to label them as such.
    """
    scen = props.get("scenarios", [])
    w = _tracks([1] * max(len(scen), 1), 24)
    cards = []
    for s in scen:
        feat = s.get("featured", False)
        kids = [
            widget("heading", {
                "title": s.get("label", ""), "header_size": "div",
                "align": "left",
            }, globals_={"title_color": color_ref(
                C["brand_on_dark"] if feat else C["muted"]),
                "typography_typography": typo_ref(T["eyebrow"])}),
            widget("heading", {
                "title": s.get("rate", ""), "header_size": "div", "align": "left",
            }, globals_={"title_color": color_ref(
                C["brand_on_dark"] if feat else C["on_dark"]),
                "typography_typography": typo_ref(T["h_large"])}),
        ]
        if s.get("working"):
            kids.append(_text(s["working"], on_dark=True, small=True))
        if s.get("result"):
            kids.append(_heading(s["result"], "h3", T["h_small"], align="left",
                                 on_dark=True))
        cards.append(container(kids, {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(8),
            "width": slider(w[len(cards) % len(w)], "%"),
            "width_tablet": slider(100, "%"),
            "width_mobile": slider(100, "%"),
            "padding": dims(28, 26, 30, 26),
            "border_radius": R_PL,
            "border_border": "solid",
            "border_width": box(2) if feat else box(1),
            "background_background": "classic",
        }, globals_={
            "background_color": color_ref(C["overlay"]),
            "border_color": color_ref(
                C["accent_fill"] if feat else C["rule_dark"])}))

    kids = [_pl_head(props, on_dark=True)] if props.get("heading") else []
    kids.append(_row(cards, gap_px=24, align="stretch"))

    delta = props.get("delta")
    if delta:
        kids.append(container([
            widget("heading", {
                "title": delta.get("value", ""), "header_size": "div",
                "align": "left",
            }, globals_={"title_color": color_ref(C["brand_on_dark"]),
                         "typography_typography": typo_ref(T["h_large"])}),
            _text(delta.get("text", ""), on_dark=True),
        ], {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(8),
            "margin": dims(24, 0, 0, 0),
            "padding": dims(26, 26, 28, 26),
            "border_radius": R_PL,
            "border_border": "solid",
            "border_width": dims(0, 0, 0, 4),
            "background_background": "classic",
        }, globals_={"background_color": color_ref(C["overlay"]),
                     "border_color": color_ref(C["accent_fill"])}))

    if props.get("footnote"):
        kids.append(container([_text(props["footnote"], on_dark=True,
                                     small=True)], {
            "content_width": "full", "flex_direction": "column",
            "margin": dims(18, 0, 0, 0)}))

    if props.get("cta"):
        kids.append(_button(props["cta"]["label"], props["cta"]["href"],
                            "accent"))

    return _section(kids, bg=props.get("bg", "dark"),
                    pad=dims(96, 0, 96, 0))
