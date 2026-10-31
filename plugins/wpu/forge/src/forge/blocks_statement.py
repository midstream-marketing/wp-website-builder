"""
blocks_statement.py — the "statement" design family.

A heading-forward layout language: every band opens with a small eyebrow
label, then a declarative statement headline, then at most one short line of
supporting copy, then an uppercase call to action. Prose is deliberately
scarce — the reference this was derived from runs 49 headings against 4 text
blocks on its homepage, and that ratio is most of what gives it its character.

Two factories, both of which the older trade families had no equivalent for:

    hero.statement   interior page banner that carries the eyebrow + statement
                     pair, rather than a bare H1 on a photo strip
    tiles.square     square photo tiles with a label — the device that page
                     uses to present verticals served and equipment categories

Both are general-purpose and take no client-specific assumptions.
"""
from __future__ import annotations

from .core import (
    container, widget, repeater_item, slider, dims, box, media, link, icon,
    gap, color_ref, typo_ref, css,
)
from .tokens import C, T
from .blocks import (
    block, _row, _col, _section, _tracks, _track, _grid_widths, _heading,
    _text, _button, _scrim, _photo, _hover_lift,
    CARD_SHADOW, CARD_SHADOW_SOFT, SECTION_PAD, SECTION_PAD_T, SECTION_PAD_M,
    TABLET_CONTAINER,
)


def _eyebrow_chip(text, on_dark=True):
    """Small uppercase label above a statement headline.

    Bare letterspaced text rather than a filled pill: on this design language
    the eyebrow is a quiet label introducing the statement, and a filled chip
    competes with the headline it is supposed to be setting up.
    """
    return widget("heading", {
        "title": text, "header_size": "div", "align": "left",
    }, globals_={
        "title_color": color_ref(C["brand_on_dark"] if on_dark
                                 else C["ink_primary"]),
        "typography_typography": typo_ref(T["eyebrow"]),
    })


@block("hero.statement")
def hero_statement(props):
    """Interior page banner: eyebrow, statement headline, optional line + CTA.

    `hero.banner` renders a headline on a photo strip and nothing else, which
    leaves every interior page opening on a bare H1. This carries the same
    eyebrow-then-statement pair the body sections use, so the page starts in
    the design language instead of arriving at it two sections down.

    Shorter than a homepage hero by default — a visitor on a service page has
    already chosen, and a full-height banner is one scroll between them and
    the answer.
    """
    align = props.get("align", "left")
    body = []
    if props.get("eyebrow"):
        body.append(_eyebrow_chip(props["eyebrow"]))
    body.append(widget("heading", {
        "title": props["h1"], "header_size": props.get("tag", "h1"),
        "align": align,
    }, globals_={
        "title_color": color_ref(C["white"]),
        "typography_typography": typo_ref(T["hero"]),
    }))
    if props.get("intro"):
        body.append(_text(props["intro"], align=align, on_dark=True))

    ctas = []
    if props.get("cta"):
        ctas.append(_button(props["cta"]["label"], props["cta"]["href"],
                            "primary"))
    if props.get("cta2"):
        ctas.append(_button(props["cta2"]["label"], props["cta2"]["href"],
                            "ghost_dark"))
    if ctas:
        body.append(_row(ctas, 12, align="center",
                         justify="flex-start" if align == "left" else "center",
                         extra={"flex_direction_mobile": "column",
                                "flex_align_items_mobile": "stretch"}))

    inner = _col(body, extra={
        "flex_gap": gap(props.get("gap", 16)),
        "content_width": "boxed",
        "boxed_width": slider(props.get("measure", 780)),
        **({"flex_align_items": "center",
            "margin": dims(0, "auto", 0, "auto")} if align == "center" else {}),
    })

    sec = container([inner], {
        "content_width": "boxed",
        "flex_direction": "column",
        "flex_justify_content": "center",
        "min_height": slider(props.get("min_height", 420)),
        "min_height_tablet": slider(360),
        "min_height_mobile": slider(320),
        "padding": dims(88, 0, 88, 0),
        "padding_tablet": dims(72, 24, 72, 24),
        "padding_mobile": dims(56, 20, 56, 20),
        "background_background": "classic",
        "background_size": "cover",
        "background_position": "center center",
        "background_repeat": "no-repeat",
        "background_overlay_background": "classic",
        "background_overlay_opacity": slider(props.get("overlay", 0.42)),
        **({"background_image": media(props["image"]["url"],
                                      props["image"].get("alt", ""))}
           if props.get("image", {}).get("url") else {}),
    }, globals_={
        "background_color": color_ref("secondary"),
        "background_overlay_color": color_ref("secondary"),
    })
    return _scrim(sec, props.get("scrim", "left"), props.get("strength", 0.82))


@block("tiles.square")
def tiles_square(props):
    """Square photo tiles with a label — verticals served, equipment covered.

    The reference uses this twice on one page, for the industries it works in
    and the equipment categories it covers. It earns its place for a reason
    the icon grid cannot match: a buyer scanning for *their* equipment or
    *their* sector finds it in one pass, and every tile is a keyword the page
    would otherwise not carry.

    Tiles are square by design (`min_height` matched to the column width is
    not expressible here, so the photo takes a fixed height and the label sits
    under it). An empty image slot renders as a tinted block rather than a
    gap, so an unfilled grid still reads as a grid.
    """
    items = props["items"]
    cols = props.get("columns", 4)
    gap_px = props.get("gap", 20)
    width, width_t = _grid_widths(cols, gap_px)
    height = props.get("height", 190)
    on_dark = props.get("bg") in ("dark", "primary")

    def tile(it):
        img = it.get("image") or {}
        if img.get("url"):
            photo = _photo(img, height, radius=10)
        else:
            photo = container([], {
                "content_width": "full",
                "min_height": slider(height),
                "border_radius": box(10),
                "background_background": "classic",
            }, globals_={"background_color": color_ref(
                C["rule_dark"] if on_dark else C["surface_alt"])})

        label = _heading(it["title"], "h3", T["h_small"],
                         align="center", on_dark=on_dark)
        inner = [photo, label]
        if it.get("text"):
            inner.append(_text(it["text"], align="center", on_dark=on_dark,
                               small=True))

        cell = container(inner, {
            "content_width": "full",
            "flex_direction": "column",
            "flex_gap": gap(10),
            "flex_align_items": "center",
        })
        # A tile that links is a link everywhere, not just on its label.
        if it.get("href"):
            cell = _hover_lift(cell)
            cell["settings"]["custom_css"] = css(
                "selector { cursor: pointer; }")
        return cell

    cells = [_col([tile(i)], width, extra={
        "width_tablet": {"unit": "%", "size": width_t, "sizes": []},
    }) for i in items]
    rows = [_row(cells[n:n + cols], gap_px, align="stretch")
            for n in range(0, len(cells), cols)]

    head = []
    if props.get("eyebrow"):
        head.append(_eyebrow_chip(props["eyebrow"], on_dark=on_dark))
    if props.get("heading"):
        head.append(_heading(props["heading"], "h2", T["h_large"],
                             align="left", on_dark=on_dark,
                             tone="brand" if not on_dark else "dark"))
    if props.get("intro"):
        head.append(_text(props["intro"], on_dark=on_dark))
    children = ([_col(head, extra={"flex_gap": gap(12),
                                   "margin": dims(0, 0, 40, 0)})]
                if head else []) + rows

    if props.get("cta"):
        children.append(_col([
            _button(props["cta"]["label"], props["cta"]["href"], "primary"),
        ], extra={"flex_align_items": "flex-start",
                  "margin": dims(36, 0, 0, 0)}))

    return _section(children, bg=props.get("bg", "white"))
