"""
blocks_dualcore.py — the DualCore Peptides design family.

Client-specific, and deliberately so. The `store.*` family in
`blocks_store*.py` follows silverstatebiolabs.com: a dark header, a dark
scrimmed hero, full-bleed dark bands and a dark five-column footer. DualCore's
client supplied a different reference — alphahealthco.com — and asked for it
to be matched, so bending the existing family with more flags would have
produced the silverstate design wearing DualCore's colours. That is exactly
the "nearest existing block" substitution the design-fidelity gate exists to
catch, and every device below is listed in `clients/dualcore-peptides/
design-spec.json` with the store block it is forbidden to fall back to.

What actually distinguishes this design, in the order the eye reads it:

    1. It is a LIGHT design. White header, white footer, pale blue-silver
       tints. Dark is a spotlight, not the ground.
    2. Every dark block is INSET and ROUNDED — page margins are visible down
       both sides of it. Nothing is edge-to-edge except the header, the hero
       tint and one photograph that bleeds off the left edge on purpose.
    3. Display headings mix weight inside a single line: light framing words,
       one bold noun. It appears on the hero, the product heading and the
       why-us heading, and it is the cheapest, most recognisable thing here.
    4. The primary action is always a filled ACCENT pill with a trailing
       arrow, in a colour that is neither the brand blue nor the ink.

Colour still comes from the client's own logo through the Global Kit — see
`intake.json`. Nothing in this file names a hex.
"""
from __future__ import annotations

from .core import (
    container, widget, repeater_item, slider, dims, box, media, link, icon,
    gap, color_ref, typo_ref, css,
)
from .tokens import C, T
from .blocks import (
    block, _row, _col, _tracks, _track, _grid_widths, _heading, _text,
    _button, _hover_lift, CARD_SHADOW, CARD_SHADOW_SOFT,
    KIT_CONTAINER, TABLET_CONTAINER,
)

# ─────────────────────────── rhythm and shape ───────────────────────────
#
# The reference runs a shorter section than the trade families (measured ~80px
# a side, against their 104) and a noticeably larger corner radius. Both are
# design decisions of this reference, so they live here rather than in the
# shared constants.

DC_PAD = dims(88, 0, 88, 0)
DC_PAD_T = dims(64, 24, 64, 24)
DC_PAD_M = dims(52, 20, 52, 20)

R_CARD = box(14)          # cards and tiles
R_PANEL = box(20)         # the big tinted panels and the inset dark blocks
R_CHIP = box(10)          # the rounded-square icon chips
R_PILL = box(999)

GUTTER = 26               # gap between cards in every grid on the site


def _dc_display(text: str) -> str:
    """Mixed-weight display heading.

    The reference's signature typographic move: one line, most of it at a
    light weight, one word bold. Copy writes it as `**word**` so the emphasis
    lives with the words rather than in the layout code, and a copy edit
    cannot silently drop it.
    """
    parts = text.split("**")
    out = []
    for n, p in enumerate(parts):
        out.append(f"<b>{p}</b>" if n % 2 else p)
    return "".join(out)


def _dc_heading(text, size="h2", token=None, align="left", on_dark=False,
                tone="ink", caps=False):
    """Display heading. `tone` picks which of the three inks it takes."""
    if on_dark:
        col = C["white"]
    elif tone == "brand":
        col = C["ink_primary"]
    else:
        col = "secondary"
    body = _dc_display(text.upper() if caps else text)
    return widget("heading", {
        "title": body, "header_size": size, "align": align,
    }, globals_={
        "title_color": color_ref(col),
        "typography_typography": typo_ref(token or T["h_large"]),
    })


def _dc_section(children, bg="white", pad=None, extra=None):
    """Standard band. Only three grounds exist on this site."""
    token = {"white": C["white"], "surface": C["surface"],
             "alt": C["surface_alt"]}.get(bg, C["white"])
    s = {
        "content_width": "boxed",
        "flex_direction": "column",
        "flex_gap": gap(44),
        "padding": pad or DC_PAD,
        "padding_tablet": DC_PAD_T,
        "padding_mobile": DC_PAD_M,
        "background_background": "classic",
    }
    if extra:
        s.update(extra)
    g = {"background_color": color_ref(token)}
    g.update(s.pop("__globals__", {}))
    return container(children, s, globals_=g)


def _dc_head(props, align="center", on_dark=False):
    """Section opener: optional small caps eyebrow, mixed-weight display
    heading, optional one-line caption.

    The reference's eyebrow is bare letterspaced caps in the brand colour, not
    a filled chip — the chip belongs to the other family and using it here is
    the difference between this page and that one.
    """
    out = []
    if props.get("eyebrow"):
        out.append(widget("heading", {
            "title": props["eyebrow"].upper(), "header_size": "div",
            "align": align,
        }, globals_={
            "title_color": color_ref(C["brand_on_dark"] if on_dark
                                     else C["ink_primary"]),
            "typography_typography": typo_ref(T["eyebrow"]),
        }))
    if props.get("heading"):
        out.append(_dc_heading(props["heading"], props.get("level", "h2"),
                               T["h_large"], align=align, on_dark=on_dark))
    if props.get("sub"):
        out.append(widget("text-editor", {
            "editor": f"<p>{props['sub']}</p>", "align": align,
        }, globals_={
            "text_color": color_ref(C["on_dark"] if on_dark else C["muted"]),
            "typography_typography": typo_ref(T["body_small"]),
        }))
    return _col(out, extra={
        "flex_gap": gap(10),
        "flex_align_items": {"center": "center", "left": "flex-start"}[align],
        "content_width": "boxed",
        "boxed_width": slider(props.get("measure", 720)),
        **({"margin": dims(0, "auto", 0, "auto")} if align == "center" else {}),
    })


def _dc_card(children, bg="white", pad=None, radius=None, border=True,
             shadow=True, extra=None):
    """The one card shape on the site: soft radius, hairline silver border,
    a shadow you have to look for."""
    s = {
        "content_width": "full",
        "flex_direction": "column",
        "flex_gap": gap(12),
        "padding": pad or dims(26, 24, 26, 24),
        "padding_mobile": dims(22, 20, 22, 20),
        "border_radius": radius or R_CARD,
        "background_background": "classic",
    }
    if shadow:
        s.update(CARD_SHADOW_SOFT)
    if border:
        s.update({"border_border": "solid", "border_width": box(1)})
    if extra:
        s.update(extra)
    g = {"background_color": color_ref(
        {"white": C["white"], "alt": C["surface_alt"], "surface": C["surface"],
         "dark": "secondary"}.get(bg, C["white"]))}
    if border:
        g["border_color"] = color_ref(C["border"])
    # container() assigns __globals__ wholesale, so a caller's own globals in
    # `extra` would be silently replaced and the symptom would be an unstyled
    # panel rather than an error. Merge; the caller wins.
    g.update(s.pop("__globals__", {}))
    return container(children, s, globals_=g)


def _dc_chip_icon(icon_cls, size=20, tone="brand", on_dark=False):
    """Rounded-square icon chip. Top-LEFT of a card in this design, never
    centred above a centred title — that is the other family's card."""
    ic = widget("icon", {
        "selected_icon": icon(icon_cls), "size": slider(size),
        "align": "center", "view": "default",
    }, globals_={"primary_color": color_ref(
        C["brand_on_dark"] if on_dark else "primary")})
    return container([ic], {
        "content_width": "full",
        "flex_direction": "row",
        "flex_justify_content": "center",
        "flex_align_items": "center",
        "width": slider(46),
        "min_height": slider(46),
        "_flex_grow": 0,
        "_flex_align_self": "flex-start",
        "border_radius": R_CHIP,
        "background_background": "classic",
    }, globals_={"background_color": color_ref(
        C["rule_dark"] if on_dark else C["surface_alt"])})


def _dc_pill(label, href, style="accent", icon_cls="fas fa-arrow-right"):
    """The site's action button: a filled pill with a trailing arrow.

    `accent` is the reference's amber CTA, recoloured to the DualCore
    highlight blue. `outline` and `soft` are the hero's paired buttons.
    """
    if style == "outline":
        b = _button(label, href, "ghost", icon_cls)
        b["settings"]["border_radius"] = R_PILL
        b["settings"]["text_padding"] = dims(15, 30, 15, 30)
        return b
    if style == "soft":
        b = _button(label, href, "ghost", icon_cls)
        b["settings"]["border_radius"] = R_PILL
        b["settings"]["text_padding"] = dims(15, 30, 15, 30)
        b["settings"]["__globals__"].update({
            "background_color": color_ref(C["surface_alt"]),
            "border_color": color_ref(C["surface_alt"]),
        })
        return b
    b = _button(label, href, "accent", icon_cls)
    b["settings"]["border_radius"] = R_PILL
    b["settings"]["text_padding"] = dims(16, 32, 16, 32)
    return b


def _dc_photo(image, height=420, radius=None, fit="cover"):
    """A photograph, or the honest empty slot in its place.

    An unfilled slot renders as a fixed-height tinted block rather than
    collapsing to nothing, so a page with no photography yet still shows where
    it goes instead of looking like a layout bug.
    """
    if image and image.get("url"):
        return widget("image", {
            "image": media(image["url"], image.get("alt", "")),
            "image_size": "full",
            "width": slider(100, "%"),
            "align": "center",
            "image_border_radius": radius or R_PANEL,
            "object-fit": fit,
        })
    return container([], {
        "content_width": "full",
        "min_height": slider(height),
        "min_height_mobile": slider(round(height * 0.62)),
        "border_radius": radius or R_PANEL,
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["surface_alt"])})


# ═══════════════════════════════ header ═══════════════════════════════

@block("dc.header")
def dc_header(props):
    """Announcement strip over a WHITE navigation bar.

    The reference's header is the first thing that tells a visitor this is not
    a stock storefront: it is light, the nav is plain text with no chips, and
    the right-hand side carries a bordered help-phone pill next to a bordered
    cart total rather than a row of icons. All three are reproduced here.
    """
    out = []
    if props.get("announcement"):
        out.append(_dc_announce(props["announcement"]))
    out.append(_dc_bar(props))
    return container(out, {"content_width": "full", "flex_direction": "column",
                           "flex_gap": gap(0)})


def _dc_announce(text):
    """Brand-fill strip, centred caps, an arrow glyph either side.

    Static rather than scrolling: this line carries a discount code, and a
    code that slides out of the viewport before it can be read is worse than
    no code. The other family marquees its strip because it rotates several
    compliance lines; this one carries exactly one.
    """
    arrow = lambda cls: widget("icon", {
        "selected_icon": icon(cls), "size": slider(11), "align": "center",
        "view": "default",
    }, globals_={"primary_color": color_ref(C["on_primary"])})
    label = widget("heading", {
        "title": text.upper(), "header_size": "div", "align": "center",
    }, globals_={
        "title_color": color_ref(C["on_primary"]),
        "typography_typography": typo_ref(T["meta"]),
    })
    return container([
        _row([arrow("fas fa-angle-right"), label, arrow("fas fa-angle-left")],
             10, align="center", justify="center",
             extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"}),
    ], {
        "content_width": "boxed",
        "flex_direction": "row",
        "flex_justify_content": "center",
        "padding": dims(9, 20, 9, 20),
        "background_background": "classic",
    }, globals_={"background_color": color_ref("primary")})


def _dc_help_pill(props):
    """'Need Help?  (000) 000-0000' in a bordered capsule.

    The reference puts the phone number in the header rather than only in the
    footer, which is a deliberate reassurance device for a vertical where
    buyers want to know a human exists before they pay.
    """
    inner = [
        widget("heading", {
            "title": props.get("help_label", "Need Help?"),
            "header_size": "div", "align": "left",
        }, globals_={
            "title_color": color_ref(C["muted"]),
            "typography_typography": typo_ref(T["meta"]),
        }),
        widget("icon", {
            "selected_icon": icon("fas fa-phone"), "size": slider(12),
            "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref("primary")}),
        widget("heading", {
            "title": f'<a href="tel:{props.get("phone_href", "")}">'
                     f'{props.get("phone", "")}</a>',
            "header_size": "div", "align": "left",
        }, globals_={
            "title_color": color_ref(C["ink_primary"]),
            "typography_typography": typo_ref("accent"),
        }),
    ]
    return container([_row(inner, 8, align="center", justify="center",
                           extra={"flex_wrap": "nowrap",
                                  "flex_direction_mobile": "row"})], {
        "content_width": "full",
        "flex_direction": "row",
        "flex_justify_content": "center",
        "flex_align_items": "center",
        "_flex_grow": 0,
        "padding": dims(9, 18, 9, 18),
        "border_radius": R_PILL,
        "border_border": "solid",
        "border_width": box(1),
        "hide_mobile": "hidden-mobile",
        "background_background": "classic",
    }, globals_={
        "background_color": color_ref(C["white"]),
        "border_color": color_ref(C["border"]),
    })


def _dc_bar(props):
    logo = widget("theme-site-logo", {
        "align": "left", "width": slider(props.get("logo_width", 176)),
        **({"image": media(props["logo"], props.get("business", ""))}
           if props.get("logo") else {}),
    })

    nav = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"),
        "layout": "horizontal",
        "align_items": "left",
        "pointer": "underline",
        "menu_space_between": slider(props.get("nav_gap", 26)),
        "toggle_align": "right",
        "submenu_icon": {"value": "fas fa-caret-down", "library": "fa-solid"},
        "dropdown_border_radius": box(12),
        "padding_horizontal_dropdown_item": slider(18),
        "padding_vertical_dropdown_item": slider(11),
    }, globals_={
        "color_menu_item": color_ref("secondary"),
        "color_menu_item_hover": color_ref(C["ink_primary"]),
        "color_menu_item_active": color_ref(C["ink_primary"]),
        "pointer_color_menu_item_hover": color_ref("primary"),
        "pointer_color_menu_item_active": color_ref("primary"),
        "menu_typography_typography": typo_ref("accent"),
        "color_dropdown_item": color_ref("text"),
        "color_dropdown_item_hover": color_ref(C["ink_primary"]),
        "background_color_dropdown_item": color_ref(C["white"]),
        "background_color_dropdown_item_hover": color_ref(C["surface_alt"]),
        "dropdown_typography_typography": typo_ref(T["body_small"]),
    })

    # Icon only, as in the reference — an open search field in a light header
    # competes with the nav for the same horizontal space and wins, which is
    # why the reference collapses it to a glyph.
    search = widget("button", {
        "text": "",
        "link": link(props.get("search_href", "/?s=&post_type=product")),
        "selected_icon": icon("fas fa-magnifying-glass"),
        "icon_align": "left",
        "text_padding": dims(11, 12, 11, 12),
        "border_radius": R_PILL,
        "border_border": "none",
        "border_width": box(0),
    }, globals_={
        "button_text_color": color_ref("secondary"),
        "background_color": color_ref(C["transparent"]),
        "hover_color": color_ref(C["ink_primary"]),
        "button_background_hover_color": color_ref(C["surface_alt"]),
    })

    cart = container([widget("woocommerce-menu-cart", {
        "cart_type": "mini-cart",
        "icon": "cart-medium",
        "items_indicator": "bubble",
        "toggle_icon_size": slider(18),
        "toggle_button_padding": dims(0, 0, 0, 0),
        "toggle_button_border_radius": box(0),
        "show_subtotal": "yes",
        "show_divider": "yes",
        "show_remove_icon": "yes",
        "view_cart_button_show": "yes",
        "checkout_button_show": "yes",
    }, globals_={
        "toggle_button_text_color": color_ref("secondary"),
        "toggle_button_icon_color": color_ref("secondary"),
        "toggle_button_hover_icon_color": color_ref(C["ink_primary"]),
        "items_indicator_background_color": color_ref("primary"),
        "items_indicator_text_color": color_ref(C["on_primary"]),
        "subtotal_color": color_ref("secondary"),
    })], {
        "content_width": "full",
        "flex_direction": "row",
        "flex_justify_content": "center",
        "flex_align_items": "center",
        "_flex_grow": 0,
        "padding": dims(9, 16, 9, 16),
        "border_radius": R_PILL,
        "border_border": "solid",
        "border_width": box(1),
        "background_background": "classic",
    }, globals_={
        "background_color": color_ref(C["white"]),
        "border_color": color_ref(C["border"]),
    })

    w_logo, w_nav, w_util = _tracks(props.get("bar_ratios", [19, 43, 38]), 18)

    return container([
        _row([
            _col([logo], w_logo, extra={"flex_justify_content": "center"}),
            _col([nav], w_nav, extra={"flex_justify_content": "center"}),
            _col([_row([search, _dc_help_pill(props), cart], 10, align="center",
                       justify="flex-end",
                       extra={"flex_wrap": "nowrap",
                              "flex_direction_mobile": "row"})],
                 w_util, extra={"flex_justify_content": "center"}),
        ], gap_px=18, align="center"),
    ], {
        "content_width": "boxed",
        "flex_direction": "row",
        "padding": dims(14, 0, 14, 0),
        "padding_mobile": dims(12, 18, 12, 18),
        "border_width": dims(0, 0, 1, 0),
        "border_border": "solid",
        "background_background": "classic",
    }, globals_={
        "background_color": color_ref(C["white"]),
        "border_color": color_ref(C["border"]),
    })


# ════════════════════════════════ hero ════════════════════════════════

@block("dc.hero")
def dc_hero(props):
    """Light gradient hero: mixed-weight H1 and paired pills on the left,
    product vials floating on the right, statistics along the bottom.

    Three things make it this hero rather than a generic split hero, and all
    three are load-bearing:

    * the ground is a pale vertical gradient, not a photograph with a scrim;
    * the vials are foreground objects, absolutely positioned, overlapping
      each other and overhanging the section's bottom edge;
    * the statistics sit INSIDE the hero under the buttons, so the first
      screen carries the three claims the whole store rests on.
    """
    left = [
        widget("heading", {
            "title": _dc_display(props["heading"]), "header_size": "h1",
            "align": "left",
        }, globals_={
            "title_color": color_ref("secondary"),
            "typography_typography": typo_ref(T["hero"]),
        }),
    ]
    if props.get("text"):
        left.append(widget("text-editor", {
            "editor": f"<p>{props['text']}</p>", "align": "left",
        }, globals_={
            "text_color": color_ref("text"),
            "typography_typography": typo_ref("text"),
        }))

    ctas = []
    if props.get("cta"):
        ctas.append(_dc_pill(props["cta"]["label"], props["cta"]["href"],
                             "outline", icon_cls=None))
    if props.get("cta2"):
        ctas.append(_dc_pill(props["cta2"]["label"], props["cta2"]["href"],
                             "soft", icon_cls=None))
    if ctas:
        left.append(_row(ctas, 12, align="center",
                         extra={"flex_direction_mobile": "column",
                                "flex_align_items_mobile": "stretch",
                                "margin": dims(6, 0, 0, 0)}))

    if props.get("stats"):
        left.append(_dc_stats(props["stats"]))

    media_col = _dc_hero_media(props.get("images", []),
                              height=props.get("media_height", 470))

    w_copy, w_media = _tracks(props.get("ratios", [54, 46]), 32)

    return container([
        _row([
            _col(left, w_copy, extra={"flex_gap": gap(20),
                                      "flex_justify_content": "center"}),
            _col([media_col], w_media,
                 extra={"flex_justify_content": "center"}),
        ], gap_px=32, align="center"),
    ], {
        "content_width": "boxed",
        "flex_direction": "column",
        "flex_justify_content": "center",
        "padding": dims(72, 0, 84, 0),
        "padding_tablet": dims(60, 24, 64, 24),
        "padding_mobile": dims(44, 20, 48, 20),
        "overflow": "hidden",
        "background_background": "gradient",
        "background_gradient_type": "linear",
        "background_gradient_angle": slider(180, "deg"),
        "background_color_stop": slider(0, "%"),
        "background_color_b_stop": slider(100, "%"),
    }, globals_={
        "background_color": color_ref(C["surface_alt"]),
        "background_color_b": color_ref(C["white"]),
    })


def _dc_stats(items):
    """Big figure over a small caption, three across.

    The figure takes the display token rather than a heading token: at body
    size these read as a footnote, and the point of the device is that the
    number is the loudest thing under the fold line.
    """
    w = _track(len(items), 20)
    cells = []
    for i in items:
        cells.append(_col([
            widget("heading", {
                "title": i["value"], "header_size": "div", "align": "left",
            }, globals_={
                "title_color": color_ref(C["ink_primary"]),
                "typography_typography": typo_ref(T["h_medium"]),
            }),
            widget("text-editor", {
                "editor": f"<p>{i['label']}</p>", "align": "left",
            }, globals_={
                "text_color": color_ref(C["muted"]),
                "typography_typography": typo_ref(T["meta"]),
            }),
        ], w, extra={"flex_gap": gap(2),
                     "width_tablet": slider(100, "%")}))
    return container([_row(cells, 20, align="flex-start")], {
        "content_width": "full",
        "flex_direction": "column",
        "padding": dims(22, 0, 0, 0),
        "margin": dims(10, 0, 0, 0),
        "border_width": dims(1, 0, 0, 0),
        "border_border": "solid",
    }, globals_={"border_color": color_ref(C["border"])})


def _dc_hero_media(images, height=470):
    """Two vials, overlapping, absolutely positioned inside a sized frame.

    Absolute positioning is the only way to get one object in front of and
    below another without a wrapper image, and every control used here is a
    real container control — `_position`, `_offset_x`/`_offset_y`, their
    orientations and `_z_index`. The frame keeps its own height so the hero
    does not collapse when the slots are still empty.
    """
    frame_children = []
    plan = [
        # (width %, x offset %, y offset %, z, from-right, from-bottom)
        {"w": 52, "x": 2, "y": 6, "z": 2, "hz": "start", "vt": "start"},
        {"w": 60, "x": 0, "y": 0, "z": 1, "hz": "end", "vt": "end"},
    ]
    for n, spec in enumerate(plan):
        img = images[n] if n < len(images) else None
        node = _dc_photo(img, height=round(height * 0.82), radius=R_PANEL,
                         fit="contain")
        frame_children.append(container([node], {
            "content_width": "full",
            "flex_direction": "column",
            "width": slider(spec["w"], "%"),
            "_position": "absolute",
            "_offset_orientation_h": spec["hz"],
            "_offset_orientation_v": spec["vt"],
            "_offset_x": slider(spec["x"], "%"),
            "_offset_y": slider(spec["y"], "%"),
            "_z_index": spec["z"],
        }))

    return container(frame_children, {
        "content_width": "full",
        "flex_direction": "column",
        "min_height": slider(height),
        "min_height_tablet": slider(round(height * 0.8)),
        "min_height_mobile": slider(round(height * 0.66)),
    })


# ══════════════════════════ overlapping strip ══════════════════════════

@block("dc.featurestrip")
def dc_featurestrip(props):
    """Four white cards straddling the boundary between two sections.

    The negative top margin is the whole device. Without it these are the
    first row of the next band and the page reads as a stack of rectangles;
    with it they tie the hero to what follows, which is the single cheapest
    move in the reference and one of the most recognisable.
    """
    items = props["items"]
    cols = props.get("columns", len(items))
    w, w_t = _grid_widths(cols, GUTTER)

    cards = []
    for i in items:
        cards.append(_col([_hover_lift(_dc_card([
            widget("icon", {
                "selected_icon": icon(i.get("icon", "fas fa-circle-check")),
                "size": slider(26), "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref("primary")}),
            _heading(i["title"], "h3", T["h_small"], align="center"),
            *([widget("text-editor", {
                "editor": f"<p>{i['text']}</p>", "align": "center",
            }, globals_={
                "text_color": color_ref(C["muted"]),
                "typography_typography": typo_ref(T["meta"]),
            })] if i.get("text") else []),
        ], pad=dims(26, 20, 26, 20), extra={
            "flex_gap": gap(10),
            "flex_align_items": "center",
            "min_height": slider(props.get("min_height", 168)),
            "flex_justify_content": "center",
            **CARD_SHADOW,
        }))], w, extra={"width_tablet": slider(w_t, "%")}))

    return _dc_section([_row(cards, GUTTER, align="stretch")],
                       bg=props.get("bg", "white"),
                       pad=dims(0, 0, 0, 0), extra={
        "flex_gap": gap(0),
        "margin": dims(props.get("lift", -58), 0, 0, 0),
        "margin_tablet": dims(-40, 0, 0, 0),
        "margin_mobile": dims(-28, 0, 0, 0),
        "z_index": 5,
        "background_background": "",
        "padding_tablet": dims(0, 24, 0, 24),
        "padding_mobile": dims(0, 20, 0, 20),
    })


# ═══════════════════ bleed-left photo + card accordion ═══════════════════

@block("dc.research")
def dc_research(props):
    """A photograph running off the left page edge, against an accordion of
    white cards inside a tinted panel.

    Two separate devices that only work together. The bleed is what stops the
    page feeling boxed; the accordion-of-cards is what stops the panel reading
    as an FAQ. Each accordion item keeps a leading check icon and a plus/minus
    expander, which is how the reference signals "these open" without a
    caption telling you so.
    """
    items = props["items"]
    titles, panels = [], []
    for it in items:
        titles.append(repeater_item(item_title=it["title"]))
        panels.append(container([
            widget("text-editor", {
                "editor": f"<p>{it['text']}</p>", "align": "left",
            }, globals_={
                "text_color": color_ref(C["muted"]),
                "typography_typography": typo_ref(T["body_small"]),
            }),
        ], {
            "content_width": "full",
            "flex_direction": "column",
            "padding": dims(0, 8, 4, 8),
        }))

    acc = widget("nested-accordion", {
        "items": titles,
        "default_state": "expanded",
        "title_tag": "h3",
        "accordion_item_title_icon_position": "right",
        "accordion_item_title_icon": icon("fas fa-plus"),
        "accordion_item_title_icon_active": icon("fas fa-minus"),
        "accordion_item_title_space_between": slider(12),
        "accordion_item_title_distance_from_content": slider(8),
        "accordion_border_radius": R_CARD,
        "accordion_padding": dims(18, 20, 18, 20),
        "content_padding": dims(0, 20, 16, 20),
        "icon_size": slider(13),
        "icon_spacing": slider(12),
        "accordion_background__background": "classic",
        "content_background_background": "classic",
        "accordion_border__border": "solid",
        "accordion_border__width": box(1),
    }, globals_={
        "accordion_background__color": color_ref(C["white"]),
        "content_background_color": color_ref(C["white"]),
        "accordion_border__color": color_ref(C["border"]),
        "accordion_item_title_color": color_ref("secondary"),
        "accordion_item_title_typography_typography": typo_ref(T["h_small"]),
        "accordion_item_title_icon_color": color_ref(C["ink_primary"]),
    }, children=panels)

    panel_children = []
    if props.get("eyebrow") or props.get("heading"):
        panel_children.append(_dc_head(props, align=props.get("align", "center")))
    panel_children.append(container([acc], {
        "content_width": "full",
        "flex_direction": "column",
        "padding": dims(18, 18, 18, 18),
        "padding_mobile": dims(14, 14, 14, 14),
        "border_radius": R_PANEL,
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["surface_alt"])}))

    photo = _dc_photo(props.get("image"), height=props.get("image_height", 430),
                      radius=dims(0, R_PANEL["top"], R_PANEL["top"], 0))

    w_img, w_body = _tracks(props.get("ratios", [42, 58]), 40, 1440)

    return container([
        _row([
            _col([photo], w_img, extra={"flex_justify_content": "center"}),
            _col(panel_children, w_body, extra={
                "flex_gap": gap(24),
                "padding": dims(0, 100, 0, 44),
                "padding_tablet": dims(0, 24, 0, 24),
                "padding_mobile": dims(0, 20, 0, 20),
            }),
        ], gap_px=40, align="center"),
    ], {
        # Full width, not boxed: the photograph has to reach the viewport edge
        # or the bleed does not exist. The copy column re-establishes the page
        # margin with its own padding.
        "content_width": "full",
        "flex_direction": "column",
        "padding": dims(76, 0, 76, 0),
        "padding_tablet": dims(58, 0, 58, 0),
        "padding_mobile": dims(44, 0, 44, 0),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(
        {"white": C["white"], "surface": C["surface"],
         "alt": C["surface_alt"]}.get(props.get("bg", "white"), C["white"]))})


# ═════════════════════════ product grid + pill ═════════════════════════

@block("dc.products")
def dc_products(props):
    """Centred mixed-weight heading, a WooCommerce grid, and one accent pill.

    The grid is the verified `wc-products` widget rather than a hand-built
    loop-item card. The registry carries no WooCommerce dynamic tags and
    loop-grid's query controls were never mined, so a bespoke card cannot be
    checked before shipping and imports EMPTY when it is wrong — which reads
    to the client as their own data-entry problem rather than as a template
    bug. The reference's per-card variation dropdown, quantity stepper and
    View Details button are therefore delivered as a documented WooCommerce
    setting plus one snippet, and that decision is recorded in design-spec.json
    rather than quietly dropped.
    """
    grid = widget("wc-products", {
        "columns": str(props.get("columns", 3)),
        "posts_per_page": str(props.get("count", 6)),
        **({"filter_by": props["filter_by"]} if props.get("filter_by") else {}),
        **({"orderby": props["orderby"]} if props.get("orderby") else {}),
    })

    body = [_dc_head(props, align="center"), grid]
    if props.get("cta"):
        body.append(_row([_dc_pill(props["cta"]["label"], props["cta"]["href"])],
                         0, align="center", justify="center",
                         extra={"flex_direction_mobile": "row"}))
    return _dc_section(body, bg=props.get("bg", "white"),
                       extra={"flex_gap": gap(36)})


# ══════════════════════════ inset dark band ══════════════════════════

@block("dc.band")
def dc_band(props):
    """Near-black rounded block, inset inside the page container.

    The reference never runs a dark band edge to edge. Every one of them is a
    card with the page margin visible either side and a 20px radius, and that
    geometry is the second-most identifying thing on the page after the
    mixed-weight display type. `flip` puts the photograph on the left, which
    is how the same component serves both the testing band and the closing
    assistance band without becoming two components.
    """
    copy_children = [
        _dc_heading(props["heading"], props.get("level", "h2"),
                    T["h_large"], on_dark=True,
                    caps=props.get("caps", True)),
    ]
    if props.get("text"):
        copy_children.append(widget("text-editor", {
            "editor": f"<p>{props['text']}</p>", "align": "left",
        }, globals_={
            "text_color": color_ref(C["on_dark"]),
            "typography_typography": typo_ref(T["body_small"]),
        }))
    if props.get("points"):
        copy_children.append(widget("icon-list", {
            "icon_list": [repeater_item(
                text=t, selected_icon=icon("fas fa-circle-check"),
                link=link("")) for t in props["points"]],
            "space_between": slider(10),
            "icon_size": slider(14),
        }, globals_={
            "icon_color": color_ref(C["brand_on_dark"]),
            "text_color": color_ref(C["on_dark"]),
            "icon_typography_typography": typo_ref(T["body_small"]),
        }))
    if props.get("cta"):
        copy_children.append(_row(
            [_dc_pill(props["cta"]["label"], props["cta"]["href"])],
            0, align="center", justify="flex-start",
            extra={"margin": dims(8, 0, 0, 0),
                   "flex_direction_mobile": "row"}))

    copy_col_extra = {
        "flex_gap": gap(16),
        "flex_justify_content": "center",
        "padding": dims(52, 44, 52, 48),
        "padding_tablet": dims(40, 30, 40, 30),
        "padding_mobile": dims(32, 22, 32, 22),
    }
    photo = _dc_photo(props.get("image"), height=props.get("image_height", 300),
                      radius=box(0), fit="cover")
    photo_col_extra = {"flex_justify_content": "center",
                       "min_height": slider(props.get("image_height", 300))}

    w_copy, w_img = _tracks(props.get("ratios", [55, 45]), 0)
    copy_col = _col(copy_children, w_copy, extra=copy_col_extra)
    photo_col = _col([photo], w_img, extra=photo_col_extra)
    cols = [photo_col, copy_col] if props.get("flip") else [copy_col, photo_col]

    panel = container([_row(cols, 0, align="stretch",
                            extra={"flex_wrap": "nowrap",
                                   "flex_wrap_tablet": "wrap"})], {
        "content_width": "full",
        "flex_direction": "column",
        "border_radius": R_PANEL,
        "overflow": "hidden",
        "background_background": "classic",
        **CARD_SHADOW,
    }, globals_={"background_color": color_ref("secondary")})

    return _dc_section([panel], bg=props.get("bg", "white"),
                       pad=props.get("pad") or dims(28, 0, 28, 0),
                       extra={"flex_gap": gap(0),
                              "padding_tablet": dims(24, 24, 24, 24),
                              "padding_mobile": dims(20, 20, 20, 20)})


# ═══════════════════ one tinted panel, N icon columns ═══════════════════

@block("dc.panelgrid")
def dc_panelgrid(props):
    """Three icon columns inside ONE tinted rounded panel.

    Not three cards. The reference groups them in a single panel with no
    dividers and no borders, so the band reads as one statement rather than as
    a feature grid — which is precisely the substitution `store.features`
    would have made here.
    """
    items = props["items"]
    cols = props.get("columns", len(items))
    w = _track(cols, 34)
    cells = []
    for i in items:
        cells.append(_col([
            _dc_chip_icon(i.get("icon", "fas fa-circle-check")),
            _heading(i["title"], "h3", T["h_small"]),
            widget("text-editor", {
                "editor": f"<p>{i['text']}</p>", "align": "left",
            }, globals_={
                "text_color": color_ref(C["muted"]),
                "typography_typography": typo_ref(T["body_small"]),
            }),
        ], w, extra={"flex_gap": gap(12),
                     "width_tablet": slider(100, "%")}))

    panel = container([_row(cells, 34, align="flex-start")], {
        "content_width": "full",
        "flex_direction": "column",
        "padding": dims(44, 40, 44, 40),
        "padding_tablet": dims(36, 30, 36, 30),
        "padding_mobile": dims(28, 22, 28, 22),
        "border_radius": R_PANEL,
        "background_background": "classic",
    }, globals_={"background_color": color_ref(
        C["surface_alt"] if props.get("tint", "alt") == "alt" else C["surface"])})

    body = []
    if props.get("heading"):
        body.append(_dc_head(props, align=props.get("align", "center")))
    body.append(panel)
    return _dc_section(body, bg=props.get("bg", "white"),
                       extra={"flex_gap": gap(36)})


# ═══════════════════════════ checklist cards ═══════════════════════════

@block("dc.checkcards")
def dc_checkcards(props):
    """White bordered cards: icon chip, title, paragraph, short tick list.

    The tick list is the part that matters. The reference uses these cards
    where a claim needs its evidence attached to it, and a card with the
    paragraph but not the list is a different, weaker component.
    """
    items = props["items"]
    cols = props.get("columns", len(items))
    w, w_t = _grid_widths(cols, GUTTER)

    cards = []
    for i in items:
        inner = [
            _dc_chip_icon(i.get("icon", "fas fa-flask")),
            _heading(i["title"], "h3", T["h_small"]),
        ]
        if i.get("text"):
            inner.append(widget("text-editor", {
                "editor": f"<p>{i['text']}</p>", "align": "left",
            }, globals_={
                "text_color": color_ref(C["muted"]),
                "typography_typography": typo_ref(T["body_small"]),
            }))
        if i.get("points"):
            inner.append(widget("icon-list", {
                "icon_list": [repeater_item(
                    text=t, selected_icon=icon("fas fa-circle-check"),
                    link=link("")) for t in i["points"]],
                "space_between": slider(9),
                "icon_size": slider(13),
            }, globals_={
                "icon_color": color_ref("primary"),
                "text_color": color_ref("text"),
                "icon_typography_typography": typo_ref(T["meta"]),
            }))
        cards.append(_col([_hover_lift(_dc_card(
            inner, bg=i.get("bg", props.get("card_bg", "white")),
            pad=dims(30, 28, 30, 28),
            extra={"flex_gap": gap(14), "min_height": slider(
                props.get("min_height", 300))}))],
            w, extra={"width_tablet": slider(w_t, "%")}))

    body = []
    if props.get("heading"):
        body.append(_dc_head(props, align=props.get("align", "center")))
    body.append(_row(cards, GUTTER, align="stretch"))
    return _dc_section(body, bg=props.get("bg", "white"),
                       extra={"flex_gap": gap(36)})


# ══════════════════════════════ page hero ══════════════════════════════

@block("dc.pagehero")
def dc_pagehero(props):
    """Inner-page hero on the pale tint.

    Deliberately short and light. The other family's page hero is a dark
    scrimmed banner; twenty pages of that would undo the reference everywhere
    except the homepage, which is the failure mode this whole family exists to
    avoid.
    """
    children = [_dc_head({
        "eyebrow": props.get("eyebrow"),
        "heading": props["heading"],
        "sub": props.get("sub"),
        "level": "h1",
        "measure": props.get("measure", 800),
    }, align=props.get("align", "center"))]

    ctas = []
    if props.get("cta"):
        ctas.append(_dc_pill(props["cta"]["label"], props["cta"]["href"]))
    if props.get("cta2"):
        ctas.append(_dc_pill(props["cta2"]["label"], props["cta2"]["href"],
                             "outline", icon_cls=None))
    if ctas:
        children.append(_row(ctas, 12, align="center",
                             justify=props.get("align", "center"),
                             extra={"flex_direction_mobile": "column",
                                    "flex_align_items_mobile": "stretch"}))

    return container(children, {
        "content_width": "boxed",
        "flex_direction": "column",
        "flex_gap": gap(22),
        "flex_align_items": "center",
        "padding": dims(72, 0, 72, 0),
        "padding_tablet": dims(56, 24, 56, 24),
        "padding_mobile": dims(44, 20, 44, 20),
        "background_background": "gradient",
        "background_gradient_type": "linear",
        "background_gradient_angle": slider(180, "deg"),
        "background_color_stop": slider(0, "%"),
        "background_color_b_stop": slider(100, "%"),
    }, globals_={
        "background_color": color_ref(C["surface_alt"]),
        "background_color_b": color_ref(C["white"]),
    })


# ══════════════════════════════ footer ══════════════════════════════

@block("dc.footer")
def dc_footer(props):
    """Light footer: brand column, link columns, the legal block, the hours
    panel, and a single centred copyright line.

    The legal block is not decoration. In this vertical the disclaimer is the
    text a payment processor's reviewer reads first, so it is set as real
    typeset prose at the full page width rather than squeezed into a column,
    and it is carried verbatim from the client's own wording wherever the
    client has supplied it.
    """
    groups = props.get("groups", [])
    brand_ratio = props.get("brand_ratio", 27)
    ratios = ([brand_ratio] + [(100 - brand_ratio) / len(groups)] * len(groups)
              if groups else [100])
    widths = _tracks(ratios, 28)

    logo = (widget("image", {
        "image": media(props["logo"], props.get("business", "")),
        "width": slider(props.get("logo_width", 180)), "align": "left"})
        if props.get("logo") else
        widget("theme-site-logo", {
            "align": "left", "width": slider(props.get("logo_width", 180))}))

    brand_col = [logo]
    if props.get("blurb"):
        brand_col.append(widget("text-editor", {
            "editor": f"<p>{props['blurb']}</p>", "align": "left",
        }, globals_={
            "text_color": color_ref(C["muted"]),
            "typography_typography": typo_ref(T["body_small"]),
        }))
    if props.get("socials"):
        brand_col.append(widget("social-icons", {
            "social_icon_list": [
                repeater_item(social_icon=icon("fab fa-" + s["network"]),
                              link=link(s["url"], external=True))
                for s in props["socials"]],
            "align": "left", "icon_size": slider(15), "shape": "circle",
            "icon_spacing": slider(9), "icon_color": "custom",
        }, globals_={
            "icon_primary_color": color_ref(C["surface_alt"]),
            "icon_secondary_color": color_ref("secondary"),
            "icon_primary_color_hover": color_ref("primary"),
        }))

    cols = [_col(brand_col, widths[0], extra={"flex_gap": gap(16)})]
    for grp, w in zip(groups, widths[1:]):
        cols.append(_col([
            widget("heading", {
                "title": grp["title"], "header_size": "h4", "align": "left",
            }, globals_={
                "title_color": color_ref(C["ink_primary"]),
                "typography_typography": typo_ref(T["h_small"]),
            }),
            widget("icon-list", {
                "icon_list": [repeater_item(
                    text=i["text"], link=link(i.get("href", "")),
                    selected_icon={"value": "", "library": ""})
                    for i in grp["items"]],
                "space_between": slider(9),
            }, globals_={
                "text_color": color_ref(C["muted"]),
                "icon_typography_typography": typo_ref(T["body_small"]),
            }),
        ], w, extra={"flex_gap": gap(14)}))

    out = [_row(cols, 28, align="flex-start")]

    if props.get("legal"):
        out.append(_dc_legal(props["legal"]))
    if props.get("contact_panel"):
        out.append(_dc_hours_panel(props["contact_panel"]))

    out.append(widget("divider", {
        "weight": slider(1), "gap": slider(6), "style": "solid",
    }, globals_={"color": color_ref(C["border"])}))
    if props.get("copyright"):
        out.append(widget("text-editor", {
            "editor": f"<p>{props['copyright']}</p>", "align": "center",
        }, globals_={
            "text_color": color_ref(C["muted"]),
            "typography_typography": typo_ref(T["meta"]),
        }))

    return container(out, {
        "content_width": "boxed",
        "flex_direction": "column",
        "flex_gap": gap(30),
        "padding": dims(70, 0, 28, 0),
        "padding_tablet": dims(58, 24, 24, 24),
        "padding_mobile": dims(46, 20, 22, 20),
        "border_width": dims(1, 0, 0, 0),
        "border_border": "solid",
        "background_background": "classic",
    }, globals_={
        "background_color": color_ref(C["white"]),
        "border_color": color_ref(C["border"]),
    })


def _dc_legal(paragraphs):
    """The small-print block. Each entry is {label, text}; the label is run in
    bold at the head of its own paragraph, as the reference sets it."""
    html = "".join(
        f"<p><strong>{p['label']}</strong> {p['text']}</p>" if p.get("label")
        else f"<p>{p['text']}</p>" for p in paragraphs)
    return container([widget("text-editor", {
        "editor": html, "align": "left",
    }, globals_={
        "text_color": color_ref(C["muted"]),
        "typography_typography": typo_ref(T["meta"]),
    })], {
        "content_width": "full",
        "flex_direction": "column",
        "padding": dims(22, 0, 4, 0),
        "border_width": dims(1, 0, 0, 0),
        "border_border": "solid",
    }, globals_={"border_color": color_ref(C["border"])})


def _dc_hours_panel(p):
    """Tinted panel: contact call-to-action, the weekday hours table, and one
    action on the right.

    The hours are a repeater-free two-column list rather than a table widget,
    because a table widget is third-party in every kit mined and the contract
    is core + Pro only.
    """
    left = _col([
        _row([
            widget("icon", {
                "selected_icon": icon("fas fa-phone"), "size": slider(13),
                "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref("primary")}),
            widget("heading", {
                "title": p.get("phone_label", ""), "header_size": "div",
                "align": "left",
            }, globals_={
                "title_color": color_ref(C["ink_primary"]),
                "typography_typography": typo_ref("accent"),
            }),
        ], 8, align="center", extra={"flex_wrap": "nowrap",
                                     "flex_direction_mobile": "row"}),
        _dc_heading(p["heading"], "h3", T["h_medium"]),
        *([widget("text-editor", {
            "editor": f"<p>{p['sub']}</p>", "align": "left",
        }, globals_={
            "text_color": color_ref(C["muted"]),
            "typography_typography": typo_ref(T["meta"]),
        })] if p.get("sub") else []),
    ], 38, extra={"flex_gap": gap(8), "flex_justify_content": "center"})

    rows = []
    for r in p.get("hours", []):
        rows.append(_row([
            _col([widget("text-editor", {
                "editor": f"<p>{r['day']}</p>", "align": "left",
            }, globals_={
                "text_color": color_ref("text"),
                "typography_typography": typo_ref(T["meta"]),
            })], 52),
            _col([widget("text-editor", {
                "editor": f"<p>{r['time']}</p>", "align": "right",
            }, globals_={
                "text_color": color_ref(C["muted"]),
                "typography_typography": typo_ref(T["meta"]),
            })], 44),
        ], 8, align="center", extra={"flex_wrap": "nowrap",
                                     "flex_direction_mobile": "row"}))
    middle = _col(rows, 36, extra={"flex_gap": gap(4)})

    right = _col([_dc_pill(p["cta"]["label"], p["cta"]["href"], "outline",
                           icon_cls="fas fa-envelope")]
                 if p.get("cta") else [], 20,
                 extra={"flex_justify_content": "center",
                        "flex_align_items": "flex-end"})

    return container([_row([left, middle, right], 30, align="center")], {
        "content_width": "full",
        "flex_direction": "column",
        "padding": dims(30, 34, 30, 34),
        "padding_mobile": dims(24, 20, 24, 20),
        "border_radius": R_PANEL,
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["surface_alt"])})


# ═══════════════════════════ media / copy split ═══════════════════════════

@block("dc.split")
def dc_split(props):
    """Photograph beside prose — the workhorse of every inner page.

    Added after the fidelity gate caught `store.split` leaking into About,
    We Test, the COA Library and Reviews. The ban in design-spec.json is
    global on purpose: a block that is merely discouraged gets used, and the
    other family's split carries its own radii, its own eyebrow chip and its
    own heading tone, so four pages of it would drift back toward the design
    this family exists to replace.

    Same prop shape as the block it displaces, so swapping it in was a
    one-word change per call site rather than a rewrite.
    """
    photo = _dc_photo(props.get("image"),
                      height=props.get("image_height", 430), radius=R_PANEL)

    body = [_dc_head({
        "eyebrow": props.get("eyebrow"),
        "heading": props["heading"],
        "sub": props.get("sub"),
        "measure": props.get("measure", 620),
    }, align="left")]

    for para in props.get("paras", []):
        body.append(widget("text-editor", {
            "editor": f"<p>{para}</p>", "align": "left",
        }, globals_={
            "text_color": color_ref("text"),
            "typography_typography": typo_ref(T["body_small"]),
        }))

    if props.get("ticks"):
        body.append(widget("icon-list", {
            "icon_list": [repeater_item(
                text=t, selected_icon=icon("fas fa-circle-check"),
                link=link("")) for t in props["ticks"]],
            "space_between": slider(10),
            "icon_size": slider(14),
        }, globals_={
            "icon_color": color_ref("primary"),
            "text_color": color_ref("text"),
            "icon_typography_typography": typo_ref(T["body_small"]),
        }))

    if props.get("cta"):
        body.append(_row([_dc_pill(props["cta"]["label"], props["cta"]["href"])],
                         0, align="center", justify="flex-start",
                         extra={"margin": dims(6, 0, 0, 0),
                                "flex_direction_mobile": "row"}))

    w_a, w_b = _tracks(props.get("ratios", [46, 54]), 44)
    cols = [_col([photo], w_a, extra={"flex_justify_content": "center"}),
            _col(body, w_b, extra={"flex_gap": gap(16),
                                   "flex_justify_content": "center"})]
    if props.get("flip"):
        cols.reverse()

    return _dc_section([_row(cols, 44, align="center")],
                       bg=props.get("bg", "white"),
                       extra={"flex_gap": gap(0)})
