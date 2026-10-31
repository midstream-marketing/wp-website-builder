"""
blocks_ameri.py — the dark editorial-service design family.

Derived from ameriserve.com's interior pages, which are a distinct system from
its homepage: dark from top to bottom, prose-light, and built on four devices
the older families had no equivalent for.

    band.gradient    full-bleed two-colour glow band, used as a hero foot and
                     as a section divider — the signature device
    tiles.labeled    image tiles with the label ABOVE the image, under a
                     section heading carrying a coloured underline rule
    features.rule    columns separated by a vertical accent rule rather than
                     boxed into cards
    locator.areas    coverage block — statement beside the areas served

Plus a `pill` button style on `_button`, which is what those pages use for
every secondary action.

The family is deliberately dark-first: `bg` defaults to the brand's dark
ground everywhere, because the thing that most distinguishes these pages from
a conventional light service page is simply that they never go light.
"""
from __future__ import annotations

from .core import (
    container, widget, repeater_item, slider, dims, box, media, link, icon,
    gap, color_ref, typo_ref, css,
)
from .tokens import C, T
from .blocks import (
    block, _row, _col, _section, _tracks, _track, _grid_widths, _heading,
    _text, _button, _photo, _hover_lift,
    CARD_SHADOW_SOFT, SECTION_PAD, SECTION_PAD_T, SECTION_PAD_M,
)

AM_PAD = dims(96, 0, 96, 0)
AM_PAD_T = dims(76, 24, 76, 24)
AM_PAD_M = dims(56, 20, 56, 20)


def _am_section(children, bg="dark", pad=None, extra=None):
    """Section on this family's rhythm. Dark by default — that is the point."""
    s = {"padding_tablet": AM_PAD_T, "padding_mobile": AM_PAD_M}
    if extra:
        s.update(extra)
    return _section(children, bg=bg, pad=pad or AM_PAD, extra=s)


def _am_eyebrow(text, on_dark=True):
    """Small uppercase label. Quiet — it introduces the statement, never
    competes with it."""
    return widget("heading", {
        "title": text, "header_size": "div", "align": "left",
    }, globals_={
        "title_color": color_ref(C["brand_on_dark"] if on_dark
                                 else C["ink_primary"]),
        "typography_typography": typo_ref(T["eyebrow"]),
    })


def _rule(width_pct=100, on_dark=True):
    """The coloured underline that sits beneath a section heading.

    A gradient rather than a flat line: it is the same two-colour device the
    glow bands use, reduced to a hairline, which is what ties the page
    together visually without adding another colour.
    """
    return container([], {
        "content_width": "full",
        "min_height": slider(2),
        "width": slider(width_pct, "%"),
        "margin": dims(18, 0, 0, 0),
        "background_background": "gradient",
        "background_gradient_type": "linear",
        "background_gradient_angle": slider(90, "deg"),
        "background_color_stop": slider(0, "%"),
        "background_color_b_stop": slider(100, "%"),
    }, globals_={
        "background_color": color_ref("primary"),
        "background_color_b": color_ref("accent"),
    })


def _am_head(props, on_dark=True, rule=True):
    """Eyebrow, statement heading and an optional underline rule."""
    out = []
    if props.get("eyebrow"):
        out.append(_am_eyebrow(props["eyebrow"], on_dark))
    if props.get("heading"):
        out.append(_heading(props["heading"], props.get("level", "h2"),
                            T["h_large"], align="left", on_dark=on_dark,
                            tone="brand"))
    if rule:
        out.append(_rule(on_dark=on_dark))
    if props.get("intro"):
        out.append(_text(props["intro"], on_dark=on_dark))
    return _col(out, extra={"flex_gap": gap(12),
                            "margin": dims(0, 0, 44, 0)})


@block("band.gradient")
def band_gradient(props):
    """Full-bleed two-colour glow band.

    The signature device of the reference's interior pages: a wide horizontal
    wash that sits under a hero and between sections, cool on one side and
    warm on the other, blurred so it reads as light rather than as a stripe.

    Elementor's container gradient carries only two stops, which produces a
    hard left-to-right ramp instead of two separate glows. The multi-stop
    version is written as scoped CSS — there is no control equivalent, which
    is exactly the case contract v2 permits it for. The flat two-stop gradient
    stays on the container underneath as the fallback.
    """
    a, b = props.get("from", "primary"), props.get("to", "accent")
    height = props.get("height", 150)
    blur = props.get("blur", 70)
    return container([], {
        "content_width": "full",
        "min_height": slider(height),
        "min_height_mobile": slider(round(height * 0.65)),
        "background_background": "gradient",
        "background_gradient_type": "linear",
        "background_gradient_angle": slider(90, "deg"),
        "background_color_stop": slider(0, "%"),
        "background_color_b_stop": slider(100, "%"),
        "custom_css": css(
            "selector { position: relative; overflow: hidden; "
            "background-image: none; }",
            # Two separate glows over the dark ground, rather than one ramp.
            "selector::before { content: ''; position: absolute; inset: -40%; "
            "background: radial-gradient(closest-side, var(--e-global-color-"
            + ("primary" if a == "primary" else a) + ") 0%, transparent 100%) "
            "left center / 55% 180% no-repeat, "
            "radial-gradient(closest-side, var(--e-global-color-"
            + ("accent" if b == "accent" else b) + ") 0%, transparent 100%) "
            "right center / 55% 180% no-repeat; "
            "filter: blur(" + str(blur) + "px); opacity: .85; }",
            "@media (prefers-reduced-motion: reduce) { selector::before "
            "{ filter: blur(" + str(blur) + "px); } }",
        ),
    }, globals_={
        "background_color": color_ref(a),
        "background_color_b": color_ref(b),
    })


@block("tiles.labeled")
def tiles_labeled(props):
    """Image tiles with the label ABOVE the image.

    Inverted from the usual card, and deliberately: on the reference's
    Verticals and Equipment grids the label is read first and the photograph
    confirms it, which is how someone scanning for their own sector or their
    own equipment actually uses the page. It also keeps a long grid legible
    when the images are still empty slots.
    """
    items = props["items"]
    cols = props.get("columns", 4)
    gap_px = props.get("gap", 22)
    width, width_t = _grid_widths(cols, gap_px)
    height = props.get("height", 175)
    on_dark = props.get("bg", "dark") in ("dark", "primary")

    def tile(it):
        img = it.get("image") or {}
        if img.get("url"):
            photo = _photo(img, height, radius=2)
        else:
            photo = container([], {
                "content_width": "full",
                "min_height": slider(height),
                "border_radius": box(2),
                "border_border": "solid",
                "border_width": box(1),
                "background_background": "classic",
            }, globals_={
                "background_color": color_ref(C["rule_dark"] if on_dark
                                              else C["surface_alt"]),
                "border_color": color_ref(C["rule_dark"] if on_dark
                                          else C["border"]),
            })
        label = _heading(it["title"], "h3", T["h_small"], align="left",
                         on_dark=on_dark)
        inner = [label, photo]
        if it.get("text"):
            inner.append(_text(it["text"], on_dark=on_dark, small=True))
        cell = container(inner, {
            "content_width": "full",
            "flex_direction": "column",
            "flex_gap": gap(12),
        })
        return _hover_lift(cell) if it.get("href") else cell

    cells = [_col([tile(i)], width, extra={
        "width_tablet": {"unit": "%", "size": width_t, "sizes": []},
    }) for i in items]
    rows = [_row(cells[n:n + cols], gap_px, align="flex-start")
            for n in range(0, len(cells), cols)]

    children = [_am_head(props, on_dark=on_dark)] + rows
    if props.get("cta"):
        children.append(_col([
            _button(props["cta"]["label"], props["cta"]["href"], "pill"),
        ], extra={"flex_align_items": "flex-start",
                  "margin": dims(44, 0, 0, 0)}))
    return _am_section(children, bg=props.get("bg", "dark"))


@block("features.rule")
def features_rule(props):
    """Columns divided by a vertical accent rule instead of boxed in cards.

    The reference uses this for its three "what sets us apart" columns. The
    rule does the separating that a card border would, without the visual
    weight of a card — which is most of why those pages feel editorial rather
    than like a product grid.
    """
    items = props["items"]
    cols = props.get("columns", len(items))
    gap_px = props.get("gap", 34)
    width, width_t = _grid_widths(cols, gap_px)
    on_dark = props.get("bg", "dark") in ("dark", "primary")

    cells = []
    for i, it in enumerate(items):
        inner = [_heading(it["title"], "h3", T["h_medium"], align="left",
                          on_dark=on_dark)]
        if it.get("text"):
            inner.append(_text(it["text"], on_dark=on_dark, small=True))
        cells.append(_col(inner, width, extra={
            "flex_gap": gap(14),
            "padding": dims(4, 0, 4, 26),
            "border_width": dims(0, 0, 0, 2),
            "border_border": "solid",
            "width_tablet": {"unit": "%", "size": width_t, "sizes": []},
            # Alternating rule colour, so a row of three reads as one device
            # rather than three identical stripes.
            "__globals__": {"border_color": color_ref(
                "primary" if i % 2 == 0 else "accent")},
        }))

    children = [_am_head(props, on_dark=on_dark),
                _row(cells, gap_px, align="stretch")]
    if props.get("cta"):
        children.append(_col([
            _button(props["cta"]["label"], props["cta"]["href"], "pill"),
        ], extra={"flex_align_items": "flex-start",
                  "margin": dims(44, 0, 0, 0)}))
    return _am_section(children, bg=props.get("bg", "dark"))


@block("locator.areas")
def locator_areas(props):
    """Coverage block — a panel of the areas served beside the statement.

    The reference runs a ZIP-code lookup against a multi-state footprint. A
    contractor with a handful of named markets does not need a search box to
    answer the same question, so this states the coverage directly and links
    each market to its page. Same job, no plugin.
    """
    on_dark = props.get("bg", "dark") in ("dark", "primary")
    areas = props["areas"]

    chips = widget("icon-list", {
        "icon_list": [repeater_item(
            text=a["name"], link=link(a.get("href", "")),
            selected_icon=icon("fas fa-location-dot")) for a in areas],
        "space_between": slider(11),
        "icon_size": slider(13),
    }, globals_={
        "icon_color": color_ref(C["brand_on_dark"] if on_dark else "primary"),
        "text_color": color_ref(C["on_dark"] if on_dark else "text"),
        "icon_typography_typography": typo_ref("accent"),
    })

    panel = container([chips], {
        "content_width": "full",
        "flex_direction": "column",
        "padding": dims(34, 34, 34, 34),
        "padding_mobile": dims(24, 20, 24, 20),
        "border_border": "solid",
        "border_width": box(1),
        "border_radius": box(4),
        "background_background": "classic",
    }, globals_={
        # `overlay` is the dark ground at partial alpha, so over that same
        # ground it resolves to itself and the panel vanishes — measured at
        # 1.00:1 against the page. `rule_dark` is white at low alpha, which
        # lifts the panel the way the reference's cards do.
        "background_color": color_ref(C["rule_dark"] if on_dark else C["surface"]),
        "border_color": color_ref(C["rule_dark"] if on_dark else C["border"]),
    })

    right = [_am_head(props, on_dark=on_dark)]
    if props.get("note"):
        right.append(_text(props["note"], on_dark=on_dark, small=True))
    if props.get("cta"):
        right.append(_button(props["cta"]["label"], props["cta"]["href"],
                             "pill"))

    w_a, w_b = _tracks(props.get("ratios", [44, 56]), 48)
    return _am_section([_row([
        _col([panel], w_a),
        _col(right, w_b, extra={"flex_gap": gap(18)}),
    ], 48, align="center")], bg=props.get("bg", "dark"))


@block("split.dark")
def split_dark(props):
    """Image beside prose, dark-native.

    `about.split` and `checklist.split` both resolve their heading through
    `tone="brand"` and their body through the light `text` token, so flipping
    either to a dark ground renders near-invisible copy. Rather than teach the
    base family about dark grounds — which would touch every other client —
    this is the dark-first equivalent, and it carries the eyebrow, statement
    and rule the rest of this family uses.
    """
    on_dark = props.get("bg", "dark") in ("dark", "primary")
    img = props.get("image") or {}
    if img.get("url"):
        photo = _photo(img, props.get("image_height", 460), radius=2)
    else:
        photo = container([], {
            "content_width": "full",
            "min_height": slider(props.get("image_height", 460)),
            "border_radius": box(2),
            "border_border": "solid",
            "border_width": box(1),
            "background_background": "classic",
        }, globals_={
            "background_color": color_ref(C["overlay"] if on_dark
                                          else C["surface_alt"]),
            "border_color": color_ref(C["rule_dark"] if on_dark
                                      else C["border"]),
        })

    body = [_am_head(props, on_dark=on_dark)]
    for para in props.get("paragraphs", []):
        body.append(_text(para, on_dark=on_dark))
    if props.get("ticks"):
        body.append(widget("icon-list", {
            "icon_list": [repeater_item(
                text=t, selected_icon=icon("fas fa-check"))
                for t in props["ticks"]],
            "space_between": slider(10), "icon_size": slider(13),
        }, globals_={
            "icon_color": color_ref(C["brand_on_dark"] if on_dark
                                    else "primary"),
            "text_color": color_ref(C["on_dark"] if on_dark else "text"),
            "icon_typography_typography": typo_ref(T["body_small"]),
        }))
    if props.get("cta"):
        body.append(_button(props["cta"]["label"], props["cta"]["href"],
                            "pill"))

    w_a, w_b = _tracks(props.get("ratios", [46, 54]), 52)
    cols = [_col([photo], w_a), _col(body, w_b, extra={"flex_gap": gap(16)})]
    if props.get("reverse"):
        cols.reverse()
    return _am_section([_row(cols, 52, align="center")],
                       bg=props.get("bg", "dark"))


@block("faq.dark")
def faq_dark(props):
    """Accordion on a dark ground, with FAQ schema.

    Depth has to go somewhere on a design language this prose-light, and an
    accordion is where it belongs: the words are on the page for search, and
    collapsed by default so they do not fight the layout.
    """
    items = props["items"]
    titles, panels = [], []
    for q in items:
        titles.append(repeater_item(item_title=q["q"]))
        panels.append(container([_text(q["a"], on_dark=True, small=True)], {
            "content_width": "full",
            "flex_direction": "column",
            "padding": dims(4, 0, 20, 0),
        }))
    acc = widget("nested-accordion", {
        "items": titles,
        "default_state": "all_collapsed",
        "title_tag": "h3",
        "faq_schema": "yes" if props.get("schema", True) else "",
        "accordion_item_title_icon_position": "right",
        "accordion_item_title_space_between": slider(0),
        "accordion_item_title_distance_from_content": slider(10),
        "accordion_padding": dims(20, 4, 20, 4),
        "border_width": dims(0, 0, 1, 0),
    }, globals_={
        "accordion_item_title_color": color_ref(C["white"]),
        "accordion_item_title_typography_typography": typo_ref(T["h_small"]),
        "accordion_item_title_icon_color": color_ref(C["brand_on_dark"]),
        "border_color": color_ref(C["rule_dark"]),
    }, children=panels)

    return _am_section([_am_head(props, on_dark=True), acc],
                       bg=props.get("bg", "dark"))
