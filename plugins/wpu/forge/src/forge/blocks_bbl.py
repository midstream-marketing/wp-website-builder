"""
blocks_bbl.py — Black Bear Labs (research peptides, WooCommerce).

The client's reference is a MOBILE APP mockup and the deliverable is a
responsive WooCommerce site, so this family is a translation. The visual
language transfers unchanged — none of it was app-specific:

    pure black ground, near-black cards with a warm hairline
    one gold used two ways: #C49850 fills, #E8CC90 text on dark
    a metallic gold GRADIENT for the primary button, black label
    DM Serif Display for the brand voice, Manrope for the product voice

Measured, because it settles the button: black on the gold gradient is
6.55:1 at the gradient's DARKEST stop; white on that gold is 2.39:1 and
fails. Every gold button here carries a black label, which is also what the
mockup does.

THE ONE PLACE THIS DOES NOT MATCH THE MOCKUP EXACTLY, and why:

The mockup's product card is bespoke — render left, name, gold dose, grey
category, "TAP TO OPEN". A custom `loop-item` card cannot be verified here,
because the WooCommerce dynamic tags are not in the registry, and the failure
mode is a grid that imports EMPTY. On a client's shop that reads as their own
data entry rather than as a template bug, which is the worst way to fail. So
the grid is the verified `wc-products` / `woocommerce-archive-products`
widget, and the two meta lines come from a companion mu-plugin hooking
`woocommerce_after_shop_loop_item_title`. Layout from the template, meta from
the hook — see blocks noted `_delivery` in design-spec.json.

    bbl.header      logo tile + stacked serif wordmark + nav + cart button
    bbl.tabbar      the app's bottom tab bar, mobile only
    bbl.footer      black, columns, compliance, legal
    bbl.hero        brand lockup, oversized display, gold compliance line
    bbl.section     eyebrow + serif heading + paragraphs
    bbl.pills       the filter pill row
    bbl.products    a wc-products grid (featured / new / by category)
    bbl.archive     the shop archive grid
    bbl.cards       near-black feature cards
    bbl.split       product render beside copy
    bbl.steps       numbered process on cards
    bbl.faq         accordion, first answer open
    bbl.compliance  the RESEARCH USE ONLY band — required on every page
    bbl.agegate     the age gate, built as the styling spec for the plugin
    bbl.form        contact form on a card
    bbl.ctaband     closing CTA
    bbl.product     single product: images, title, price, add to cart
    bbl.producttabs description / additional information tabs
    bbl.related     related products
    bbl.cart        the cart page
    bbl.checkout    the checkout page
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

GOLD = "primary"          # #C49850 — fills
GOLD_TXT = "accent"       # #E8CC90 — gold text on dark
GD_HI = "bblgdhi"         # #C8A05C
GD_LO = "bblgdlo"         # #B48844
CARD = "bblcard"          # #0C0C10
CARD2 = "bblcrd2"         # #141418
LINE = "bblline"          # #2A2420 — DECORATIVE hairline only (1.37:1)
BLACK = "surface"         # #000000
INK = "secondary"         # #0C0C10

BBL_PAD = dims(92, 0, 92, 0)
BBL_PAD_T = dims(66, 24, 66, 24)
BBL_PAD_M = dims(50, 18, 50, 18)
R_CARD = box(16)
R_BTN = box(10)
R_PILL = box(999)
GUTTER = 22


# ─────────────────────────────── helpers ───────────────────────────────────

def _sec(children, bg="black", pad=None, anchor=None, extra=None):
    grounds = {"black": C["surface"], "card": CARD, "card2": CARD2}
    s = {
        "content_width": "boxed",
        "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "flex_gap": gap(28),
        "padding": pad or BBL_PAD,
        "padding_tablet": BBL_PAD_T,
        "padding_mobile": BBL_PAD_M,
        "background_background": "classic",
    }
    if anchor:
        s["_element_id"] = anchor
    if extra:
        s.update(extra)
    return container(children, s, globals_={
        "background_color": color_ref(grounds.get(bg, C["surface"]))})


def _card(kids, width=None, pad=None, raised=False, extra=None):
    """Near-black card, 16px radius, warm hairline, no shadow."""
    s = {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(12),
        "padding": pad or dims(26, 24, 28, 24),
        "padding_mobile": dims(20, 16, 22, 16),
        "border_radius": R_CARD,
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
    }
    if width:
        s.update({"width": slider(width, "%"), "width_mobile": slider(100, "%")})
    if extra:
        s.update(extra)
    return container(kids, s, globals_={
        "background_color": color_ref(CARD2 if raised else CARD),
        "border_color": color_ref(LINE)})


def _h(text, size="h2", token=None, align="left", tone=None):
    """Serif: the brand voice."""
    return widget("heading", {
        "title": text, "header_size": size, "align": align,
        "__typography__": typo_ref(token or T["h_medium"]),
    }, globals_={"title_color": color_ref(tone or C["white"])})


def _display(text, size="h1", token=None, align="left", tone=None):
    """Heavy sans: the product voice. Uses the caps display token."""
    return widget("heading", {
        "title": text, "header_size": size, "align": align,
        "__typography__": typo_ref(token or T["caps_hero"]),
    }, globals_={"title_color": color_ref(tone or C["white"])})


def _eyebrow(text, align="left", tone=None):
    return widget("heading", {
        "title": text, "header_size": "div", "align": align,
        "__typography__": typo_ref(T["eyebrow"]),
    }, globals_={"title_color": color_ref(tone or GOLD_TXT)})


def _gold(text, align="left", token=None, tone=None):
    return widget("heading", {
        "title": text, "header_size": "div", "align": align,
        "__typography__": typo_ref(token or T["caps_sub"]),
    }, globals_={"title_color": color_ref(tone or GOLD_TXT)})


def _btn(label, href, style="gold", icon_name=None):
    """Three buttons.

        gold     the metallic gradient with a BLACK label. 6.55:1 at the
                 gradient's darkest stop; white would be 2.39:1 and fail.
        outline  gold hairline, gold label, transparent fill — the mockup's
                 unselected filter pill.
        ghost    muted hairline, for tertiary actions only.
    """
    b = _button(label, href, "primary", icon_name or "")
    b["settings"].update({
        "border_radius": R_BTN,
        "text_padding": dims(16, 32, 16, 32),
        "__typography__": typo_ref(T["meta"]),
    })
    g = b["settings"].setdefault("__globals__", {})
    if style == "outline":
        b["settings"].update({"border_border": "solid", "border_width": box(1)})
        g.update({"background_color": color_ref(C["transparent"]),
                  "border_color": color_ref(GOLD),
                  "button_text_color": color_ref(GOLD_TXT),
                  "button_background_hover_color": color_ref(GOLD),
                  "button_hover_border_color": color_ref(GOLD),
                  "hover_color": color_ref(C["surface"])})
    elif style == "ghost":
        b["settings"].update({"border_border": "solid", "border_width": box(1)})
        g.update({"background_color": color_ref(C["transparent"]),
                  "border_color": color_ref(LINE),
                  "button_text_color": color_ref(C["white"]),
                  "button_background_hover_color": color_ref(CARD2),
                  "button_hover_border_color": color_ref(GOLD),
                  "hover_color": color_ref(C["white"])})
    else:
        # The gradient lives on the button's own background group.
        b["settings"].update({
            "background_background": "gradient",
            "background_gradient_type": "linear",
            "background_gradient_angle": slider(100, "deg"),
            "background_color_stop": slider(0, "%"),
            "background_color_b_stop": slider(100, "%"),
            "border_border": "none", "border_width": box(0),
        })
        g.update({"background_color": color_ref(GD_HI),
                  "background_color_b": color_ref(GD_LO),
                  "button_text_color": color_ref(C["surface"]),
                  "button_background_hover_color": color_ref(GOLD_TXT),
                  "hover_color": color_ref(C["surface"])})
    return b


def _ticks(items, columns=1, container_px=KIT_CONTAINER, tone=None):
    rows = []
    for t in items:
        mark = widget("icon", {
            "selected_icon": icon("fas fa-check"), "size": slider(12),
            "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref(tone or GOLD_TXT)})
        rows.append(_row([mark, _text(t, "left", on_dark=True, small=True)],
                         11, align="flex-start",
                         extra={"flex_wrap": "nowrap",
                                "flex_direction_mobile": "row",
                                "padding": dims(5, 0, 5, 0)}))
    if columns == 1:
        return container(rows, {"content_width": "full",
                                "flex_direction": "column", "flex_gap": gap(2)})
    per = -(-len(rows) // columns)
    w = _tracks([1] * columns, 20, container=container_px)[0]
    cols = [_col(rows[i:i + per], w, extra={"flex_gap": gap(2)})
            for i in range(0, len(rows), per)]
    return _row(cols, 20, align="flex-start", extra={"flex_wrap": "wrap"})


def _shot(image, height=300, radius=R_CARD, fit="cover"):
    if image and image.get("url"):
        return widget("image", {
            "image": media(image["url"], image.get("alt", "")),
            "image_size": "full", "width": slider(100, "%"),
            "height": slider(height), "object-fit": fit,
            "align": "center", "image_border_radius": radius})
    return container([], {
        "content_width": "full", "min_height": slider(height),
        "border_radius": radius, "border_border": "dashed",
        "border_width": box(1), "background_background": "classic",
    }, globals_={"background_color": color_ref(CARD),
                 "border_color": color_ref(LINE)})


def _head_stack(props, align="center"):
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], align))
    if props.get("title"):
        # Exactly one H1 per page. Every page that is not the home page
        # carries it on its section head, so each head can be promoted.
        tag = "h1" if props.get("h1") else "h2"
        tok = T["h_large"] if props.get("h1") else T["h_medium"]
        kids.append(_h(props["title"], tag, tok, align))
    if props.get("intro"):
        kids.append(container([_text(props["intro"], align, on_dark=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(props.get("intro_width", 74), "%"),
            "width_mobile": slider(100, "%"),
            "margin": (dims(0, "auto", 0, "auto") if align == "center"
                       else dims(0, 0, 0, 0))}))
    if not kids:
        return []
    return [container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(12),
        "flex_align_items": "center" if align == "center" else "flex-start"})]


# ─────────────────────────────── chrome ────────────────────────────────────

@block("bbl.header")
def bbl_header(props):
    """Logo tile, then the two-line brand block, nav, and a bordered cart."""
    brand_kids = []
    if props.get("logo"):
        brand_kids.append(widget("image", {
            "image": media(props["logo"], props.get("business", "")),
            "image_size": "full", "align": "left",
            "width": slider(props.get("logo_width", 64)),
            "image_border_radius": box(8),
            "link": link(props.get("home", "/"))}))
    words = [widget("heading", {
        "title": props.get("business", "Black Bear Labs"),
        "header_size": "div", "align": "left",
        "link": link(props.get("home", "/")),
        "__typography__": typo_ref(T["wordmark"]),
    }, globals_={"title_color": color_ref(C["white"])})]
    if props.get("sub"):
        words.append(widget("heading", {
            "title": props["sub"], "header_size": "div", "align": "left",
            "__typography__": typo_ref(T["eyebrow"]),
        }, globals_={"title_color": color_ref(GOLD_TXT)}))
    brand_kids.append(container(words, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(1)}))
    brand = _row(brand_kids, 12, align="center",
                 extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})

    nav = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"),
        "layout": "horizontal", "align_items": "center",
        "pointer": "underline", "animation_line": "fade",
        "menu_space_between": slider(props.get("nav_gap", 26)),
        "toggle_align": "right",
        "__typography__": typo_ref(T["meta"]),
    }, globals_={
        "color_menu_item": color_ref(C["white"]),
        "color_menu_item_hover": color_ref(GOLD_TXT),
        "color_menu_item_active": color_ref(GOLD_TXT),
        "pointer_color_menu_item_hover": color_ref(GOLD),
        "pointer_color_menu_item_active": color_ref(GOLD),
        "toggle_color": color_ref(GOLD_TXT),
    })

    cart = widget("woocommerce-menu-cart", {
        "cart_type": "mini-cart",
        "icon": "cart-medium",
        "items_indicator": "bubble",
        "toggle_button_padding": dims(8, 10, 8, 10),
    }, globals_={
        "toggle_button_icon_color": color_ref(GOLD_TXT),
        "toggle_button_border_color": color_ref(GOLD),
        "toggle_button_text_color": color_ref(C["white"]),
        "toggle_button_hover_icon_color": color_ref(C["surface"]),
        "toggle_button_hover_background_color": color_ref(GOLD),
        "items_indicator_background_color": color_ref(GOLD),
        "items_indicator_text_color": color_ref(C["surface"]),
    })
    # The mockup's cart is an outlined rounded square. The widget exposes a
    # border colour, width and radius but no border TYPE, so the outline is
    # drawn by the container around it - verified controls, same result.
    cart = container([cart], {
        "content_width": "full", "flex_direction": "column",
        "flex_align_items": "center", "flex_justify_content": "center",
        "border_radius": box(10),
        "border_border": "solid", "border_width": box(1),
        "padding": dims(2, 4, 2, 4),
        "_flex_shrink": "0",
    }, globals_={"border_color": color_ref(GOLD)})

    row = _row([
        _col([brand], 34, extra={"flex_justify_content": "center"}),
        _col([nav], 46, extra={"flex_justify_content": "center",
                               "flex_align_items": "center"}),
        _col([cart], 16, extra={"flex_justify_content": "center",
                                "flex_align_items": "flex-end"}),
    ], GUTTER, align="center",
        extra={"flex_wrap": "nowrap", "flex_wrap_tablet": "wrap"})

    return container([row], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "padding": dims(14, 0, 14, 0),
        "padding_mobile": dims(12, 14, 12, 14),
        "background_background": "classic",
        "border_border": "solid", "border_width": dims(0, 0, 1, 0),
        "sticky": "top", "sticky_on": ["desktop", "tablet", "mobile"],
        "sticky_offset": 0,
    }, globals_={"background_color": color_ref(C["surface"]),
                 "border_color": color_ref(LINE)})


@block("bbl.tabbar")
def bbl_tabbar(props):
    """The mockup's bottom tab bar, kept for MOBILE ONLY.

    It is the most recognisable thing in the client's design and it is a good
    mobile commerce pattern in its own right, so it survives the translation
    rather than being thrown away with the rest of the native chrome. Hidden
    on desktop and tablet, where the sticky header already does this job.
    """
    cells = []
    items = props.get("items", [])
    w = _tracks([1] * max(1, len(items)), 0)[0]
    for it in items:
        active = bool(it.get("active"))
        tone = GOLD_TXT if active else C["muted"]
        cells.append(_col([
            widget("icon", {
                "selected_icon": icon(it.get("icon", "fas fa-circle")),
                "size": slider(17), "align": "center", "view": "default",
                "link": link(it.get("href", "#")),
            }, globals_={"primary_color": color_ref(tone)}),
            widget("heading", {
                "title": it.get("label", ""), "header_size": "div",
                "align": "center", "link": link(it.get("href", "#")),
                "__typography__": typo_ref(T["eyebrow"]),
            }, globals_={"title_color": color_ref(tone)}),
        ], w, extra={"flex_gap": gap(4),
                     "flex_align_items": "center",
                     "flex_justify_content": "center"}))

    return container([_row(cells, 0, align="center",
                           extra={"flex_wrap": "nowrap",
                                  "flex_direction_mobile": "row"})], {
        "content_width": "full",
        "flex_direction": "column",
        "padding": dims(10, 10, 12, 10),
        "background_background": "classic",
        "border_border": "solid", "border_width": dims(1, 0, 0, 0),
        "sticky": "bottom", "sticky_on": ["mobile"],
        "sticky_offset": 0,
        "hide_desktop": "hidden-desktop",
        "hide_tablet": "hidden-tablet",
    }, globals_={"background_color": color_ref(CARD),
                 "border_color": color_ref(LINE)})


@block("bbl.footer")
def bbl_footer(props):
    brand = []
    if props.get("logo"):
        brand.append(widget("image", {
            "image": media(props["logo"], props.get("business", "Logo")),
            "image_size": "full", "width": slider(props.get("logo_width", 210)),
            "align": "left", "image_border_radius": box(10)}))
    if props.get("blurb"):
        brand.append(_text(props["blurb"], "left", on_dark=True, small=True))
    if props.get("socials"):
        brand.append(_row([widget("icon", {
            "selected_icon": icon(s.get("icon", "fab fa-instagram")),
            "size": slider(15), "align": "center", "view": "default",
            "link": link(s.get("url", "#")),
        }, globals_={"primary_color": color_ref(GOLD_TXT)})
            for s in props["socials"]], 16, align="center",
            extra={"flex_wrap": "wrap", "flex_direction_mobile": "row"}))

    cols = props.get("columns", [])
    widths = _tracks([1.5] + [1] * len(cols), GUTTER)
    body = [_col(brand, widths[0], extra={"flex_gap": gap(14)})]
    for i, c in enumerate(cols):
        kids = [_eyebrow(c.get("title", ""), "left")]
        for l in c.get("links", []):
            r = []
            if l.get("icon"):
                r.append(widget("icon", {
                    "selected_icon": icon(l["icon"]), "size": slider(12),
                    "align": "center", "view": "default",
                }, globals_={"primary_color": color_ref(GOLD)}))
            lab = widget("heading", {
                "title": l.get("label", ""), "header_size": "div",
                "align": "left", "__typography__": typo_ref(T["body_small"]),
            }, globals_={"title_color": color_ref(C["white"])})
            if l.get("url"):
                lab["settings"]["link"] = link(l["url"])
            r.append(lab)
            kids.append(_row(r, 9, align="flex-start",
                             extra={"flex_wrap": "nowrap",
                                    "flex_direction_mobile": "row",
                                    "padding": dims(4, 0, 4, 0)}))
        body.append(_col(kids, widths[i + 1], extra={"flex_gap": gap(6)}))

    kids = [_row(body, GUTTER, align="flex-start", extra={"flex_wrap": "wrap"})]
    if props.get("disclaimer"):
        kids.append(_card([_text(props["disclaimer"], "left", on_dark=True,
                                 small=True)], pad=dims(18, 18, 18, 18)))
    if props.get("copyright"):
        kids.append(widget("heading", {
            "title": props["copyright"], "header_size": "div",
            "align": "center", "__typography__": typo_ref(T["body_small"]),
        }, globals_={"title_color": color_ref(C["muted"])}))

    return container(kids, {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column", "flex_gap": gap(26),
        "padding": dims(70, 0, 90, 0),
        "padding_mobile": dims(48, 18, 96, 18),
        "background_background": "classic",
        "border_border": "solid", "border_width": dims(1, 0, 0, 0),
    }, globals_={"background_color": color_ref(C["surface"]),
                 "border_color": color_ref(LINE)})


# ─────────────────────────────── sections ──────────────────────────────────

@block("bbl.hero")
def bbl_hero(props):
    """Brand lockup, oversized display word, gold compliance line, one line
    of instruction, buttons. The mockup's home screen, verbatim in structure."""
    kids = []
    if props.get("image"):
        kids.append(widget("image", {
            "image": media(props["image"]["url"], props["image"].get("alt", "")),
            "image_size": "full", "align": "center",
            "width": slider(props.get("image_width", 54), "%"),
            "image_border_radius": R_CARD,
            "image_border_border": "solid",
            "image_border_width": box(1),
        }, globals_={"image_border_color": color_ref(LINE)}))
    if props.get("display"):
        kids.append(_display(props["display"], "h1", T["caps_hero"], "center"))
    if props.get("compliance"):
        kids.append(_gold(props["compliance"], "center", T["caps_sub"]))
    if props.get("intro"):
        kids.append(container([_text(props["intro"], "center", on_dark=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(66, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"), "gold"))
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props.get("alt_url", "#"),
                         "outline"))
    if btns:
        kids.append(_row(btns, 12, align="center", justify="center",
                         extra={"flex_wrap": "wrap",
                                "flex_direction_mobile": "column",
                                "padding": dims(6, 0, 0, 0)}))
    return _sec(kids, "black",
                pad=props.get("pad") or dims(56, 0, 72, 0),
                anchor=props.get("anchor"),
                extra={"flex_align_items": "center"})


@block("bbl.section")
def bbl_section(props):
    kids = _head_stack(props, props.get("align", "center"))
    for p in props.get("paragraphs", []):
        kids.append(container([_text(p, props.get("align", "center"),
                                     on_dark=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(props.get("width", 76), "%"),
            "width_mobile": slider(100, "%"),
            "margin": (dims(0, "auto", 0, "auto")
                       if props.get("align", "center") == "center"
                       else dims(0, 0, 0, 0))}))
    if props.get("ticks"):
        kids.append(_ticks(props["ticks"], props.get("tick_columns", 2)))
    return _sec(kids, props.get("bg", "black"), anchor=props.get("anchor"),
                extra=({"flex_align_items": "center"}
                       if props.get("align", "center") == "center" else None))


@block("bbl.pills")
def bbl_pills(props):
    pills = []
    for it in props.get("items", []):
        b = _btn(it.get("label", ""), it.get("href", "#"),
                 "gold" if it.get("active") else "outline")
        b["settings"].update({"border_radius": R_PILL,
                              "text_padding": dims(12, 26, 12, 26)})
        pills.append(b)
    return _sec([_row(pills, 10, align="center", justify="center",
                      extra={"flex_wrap": "wrap"})],
                props.get("bg", "black"),
                pad=dims(0, 0, 26, 0), anchor=props.get("anchor"))


@block("bbl.products")
def bbl_products(props):
    """A verified wc-products grid. The gold dose line and grey category line
    on each card are added by the companion mu-plugin, not by this widget —
    see the module docstring."""
    kids = _head_stack(props, "center")
    grid = widget("wc-products", {
        "columns": str(props.get("columns", 3)),
        "posts_per_page": str(props.get("limit", 6)),
        "filter_by": props.get("filter_by", "all"),
        "orderby": props.get("orderby", "date"),
        "order": props.get("order", "desc"),
        "show_onsale_flash": props.get("show_sale", ""),
        "image_border_radius": R_CARD,
        "button_border_radius": R_BTN,
    }, globals_={
        "title_color": color_ref(C["white"]),
        "price_color": color_ref(GOLD_TXT),
        "button_background_color": color_ref(GOLD),
        "button_text_color": color_ref(C["surface"]),
    })
    kids.append(grid)
    if props.get("cta_label"):
        kids.append(container([
            _btn(props["cta_label"], props.get("cta_url", "/shop/"), "outline")
        ], {"content_width": "full", "flex_direction": "column",
            "flex_align_items": "center", "padding": dims(10, 0, 0, 0)}))
    return _sec(kids, props.get("bg", "black"), anchor=props.get("anchor"))


@block("bbl.archivehead")
def bbl_archivehead(props):
    """The shop H1, taken from the archive itself.

    This one template serves /shop/ and every product category and tag, so a
    static heading would label every category page with the same words. The
    archive title widget renders the real one.
    """
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], "center"))
    kids.append(widget("theme-archive-title", {
        "header_size": "h1", "align": "center",
        "__typography__": typo_ref(T["h_large"]),
    }, globals_={"title_color": color_ref(C["white"])}))
    if props.get("intro"):
        kids.append(container([_text(props["intro"], "center", on_dark=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(74, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    return _sec(kids, props.get("bg", "black"),
                pad=dims(52, 0, 26, 0), anchor=props.get("anchor"),
                extra={"flex_align_items": "center"})


@block("bbl.archive")
def bbl_archive(props):
    """The shop grid. woocommerce-archive-products obeys whatever archive
    query it is rendered in, so this one template serves /shop/ and every
    product category and tag."""
    kids = _head_stack(props, "center")
    kids.append(widget("woocommerce-archive-products", {
        "columns": str(props.get("columns", 3)),
        "rows": str(props.get("rows", 4)),
        "allow_order": props.get("allow_order", "yes"),
        "show_result_count": props.get("show_count", "yes"),
        "nothing_found_message": props.get(
            "empty_message",
            "No peptides match that filter yet. Clear the filter or browse "
            "the full catalogue."),
        "image_border_radius": R_CARD,
        "button_border_radius": R_BTN,
    }, globals_={
        "products_title_color": color_ref(C["white"]),
        "title_color": color_ref(C["white"]),
        "price_color": color_ref(GOLD_TXT),
    }))
    return _sec(kids, props.get("bg", "black"), anchor=props.get("anchor"))


@block("bbl.cards")
def bbl_cards(props):
    kids = _head_stack(props, "center")
    cols = props.get("columns", 3)
    w = _tracks([1] * cols, GUTTER)[0]
    cards = []
    for it in props.get("items", []):
        body = []
        if it.get("icon"):
            body.append(container([widget("icon", {
                "selected_icon": icon(it["icon"]), "size": slider(19),
                "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref(GOLD_TXT)})], {
                "content_width": "full", "flex_direction": "column",
                "flex_justify_content": "center",
                "flex_align_items": "center",
                "width": slider(44), "min_height": slider(44),
                "_flex_shrink": "0", "border_radius": box(999),
                "border_border": "solid", "border_width": box(1),
                "background_background": "classic",
            }, globals_={"background_color": color_ref(C["surface"]),
                         "border_color": color_ref(LINE)}))
        body.append(_h(it.get("title", ""), "h3", T["h_small"], "left"))
        if it.get("text"):
            body.append(_text(it["text"], "left", on_dark=True, small=True))
        if it.get("note"):
            body.append(_gold(it["note"], "left", T["eyebrow"]))
        cards.append(_card(body, w, raised=props.get("raised", False)))
    kids.append(_row(cards, GUTTER, align="stretch",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "black"), anchor=props.get("anchor"))


@block("bbl.split")
def bbl_split(props):
    copy = []
    if props.get("eyebrow"):
        copy.append(_eyebrow(props["eyebrow"], "left"))
    if props.get("title"):
        copy.append(_h(props["title"], "h2", T["h_medium"], "left"))
    for p in props.get("paragraphs", []):
        copy.append(_text(p, "left", on_dark=True))
    if props.get("list_title"):
        copy.append(_gold(props["list_title"], "left", T["eyebrow"]))
    if props.get("ticks"):
        copy.append(_ticks(props["ticks"], props.get("tick_columns", 1),
                           container_px=KIT_CONTAINER * 0.5))
    if props.get("footnote"):
        copy.append(_text(props["footnote"], "left", on_dark=True, small=True))
    if props.get("cta_label"):
        copy.append(container([
            _btn(props["cta_label"], props.get("cta_url", "#"), "gold")], {
            "content_width": "full", "flex_direction": "column",
            "flex_align_items": "flex-start", "padding": dims(8, 0, 0, 0)}))

    shot = _shot(props.get("image"), props.get("image_height", 440),
                 fit=props.get("fit", "contain"))
    if props.get("framed", True):
        shot = _card([shot], pad=dims(20, 20, 20, 20))
    w = _tracks([1, 1.15], GUTTER + 14)
    pair = [_col([shot], w[0]), _col(copy, w[1], extra={"flex_gap": gap(14)})]
    if props.get("flip"):
        pair.reverse()
    return _sec([_row(pair, GUTTER + 14, align="center",
                      extra={"flex_wrap": "wrap"})],
                props.get("bg", "black"), anchor=props.get("anchor"))


@block("bbl.steps")
def bbl_steps(props):
    kids = _head_stack(props, "center")
    cols = props.get("columns", 4)
    w = _tracks([1] * cols, GUTTER)[0]
    cells = []
    for i, it in enumerate(props.get("items", []), 1):
        cells.append(_card([
            _gold("%02d" % i, "left", T["h_small"]),
            _h(it.get("title", ""), "h3", T["h_small"], "left"),
            _text(it.get("text", ""), "left", on_dark=True, small=True),
        ], w, extra={"flex_gap": gap(8)}))
    kids.append(_row(cells, GUTTER, align="stretch",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "black"), anchor=props.get("anchor"))


@block("bbl.faq")
def bbl_faq(props):
    kids = _head_stack(props, "center")
    kids.append(container([_faq(props.get("items", []), first_open=True)], {
        "content_width": "full", "flex_direction": "column",
        "width": slider(84, "%"), "width_mobile": slider(100, "%"),
        "margin": dims(0, "auto", 0, "auto")}))
    return _sec(kids, props.get("bg", "black"), anchor=props.get("anchor"))


@block("bbl.compliance")
def bbl_compliance(props):
    """RESEARCH USE ONLY. Required on every page — it is the one element that
    must survive any later edit, which is why it is its own block rather than
    a line of footer text."""
    kids = [_gold(props.get("headline",
                            "RESEARCH USE ONLY. NOT FOR HUMAN CONSUMPTION."),
                  "center", T["caps_sub"])]
    if props.get("body"):
        kids.append(container([_text(props["body"], "center", on_dark=True,
                                     small=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(78, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    if props.get("cta_label"):
        kids.append(container([
            _btn(props["cta_label"], props.get("cta_url", "#"), "outline")], {
            "content_width": "full", "flex_direction": "column",
            "flex_align_items": "center", "padding": dims(6, 0, 0, 0)}))
    panel = _card(kids, pad=dims(26, 26, 28, 26),
                  extra={"flex_align_items": "center"})
    return _sec([panel], props.get("bg", "black"),
                pad=props.get("pad") or dims(34, 0, 34, 0),
                anchor=props.get("anchor"))


@block("bbl.agegate")
def bbl_agegate(props):
    """The age gate, built as a TEMPLATE so the client can see it and so the
    styling is documented. The live gate is served by the age-gate plugin;
    this is the spec that plugin should be styled to."""
    kids = [_eyebrow(props.get("eyebrow", "Black Bear Labs"), "center")]
    if props.get("title"):
        kids.append(_h(props["title"], "h1", T["h_large"], "center"))
    if props.get("compliance"):
        kids.append(_gold(props["compliance"], "center", T["caps_sub"]))
    if props.get("body"):
        kids.append(_text(props["body"], "center", on_dark=True))
    b = _btn(props.get("cta_label", "I CONFIRM - ENTER SITE"),
             props.get("cta_url", "/"), "gold")
    b["settings"]["button_width"] = "100"
    kids.append(b)
    if props.get("decline"):
        kids.append(_text(props["decline"], "center", on_dark=True, small=True))
    panel = container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(16),
        "padding": dims(40, 34, 42, 34),
        "padding_mobile": dims(28, 20, 30, 20),
        "border_radius": R_CARD,
        "border_border": "solid", "border_width": box(1),
        "width": slider(46, "%"), "width_tablet": slider(72, "%"),
        "width_mobile": slider(100, "%"),
        "margin": dims(0, "auto", 0, "auto"),
        "flex_align_items": "center",
        "background_background": "classic",
    }, globals_={"background_color": color_ref(CARD),
                 "border_color": color_ref(GOLD)})
    return _sec([panel], "black", pad=dims(110, 0, 110, 0),
                anchor=props.get("anchor"),
                extra={"flex_align_items": "center"})


@block("bbl.form")
def bbl_form(props):
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
        "form_name": f.get("form_name", "Enquiry"),
        "form_fields": fields,
        "submit_actions": ["email"],
        "email_to": f.get("email", ""),
        "email_subject": f.get("subject", "New website enquiry"),
        "button_text": f.get("submit", "Send"),
        "button_size": "md", "button_width": "100", "input_size": "md",
        "show_labels": "yes", "mark_required": "yes",
        "row_gap": slider(14), "column_gap": slider(12),
        "success_message": f.get("success", ""),
        "field_border_radius": box(8), "field_border_width": box(1),
        "button_border_radius": R_BTN,
    }, globals_={
        "button_background_color": color_ref(GOLD),
        "button_text_color": color_ref(C["surface"]),
        "button_background_hover_color": color_ref(GOLD_TXT),
        "button_hover_color": color_ref(C["surface"]),
        "field_background_color": color_ref(C["surface"]),
        "field_text_color": color_ref(C["white"]),
        "field_border_color": color_ref(LINE),
        "label_color": color_ref(GOLD_TXT),
        "mark_required_color": color_ref(GOLD),
    })

    card_kids = []
    if props.get("title"):
        card_kids.append(_h(props["title"], "h2", T["h_medium"], "left"))
    if props.get("intro"):
        card_kids.append(_text(props["intro"], "left", on_dark=True))
    card_kids.append(form)
    card = _card(card_kids, pad=dims(34, 32, 36, 32))

    side = props.get("side")
    if side:
        sk = []
        if side.get("eyebrow"):
            sk.append(_eyebrow(side["eyebrow"], "left"))
        if side.get("title"):
            sk.append(_h(side["title"], "h2", T["h_medium"], "left"))
        for p in side.get("paragraphs", []):
            sk.append(_text(p, "left", on_dark=True))
        if side.get("ticks"):
            sk.append(_ticks(side["ticks"],
                             container_px=KIT_CONTAINER * 0.45))
        w = _tracks([1, 1.2], GUTTER + 14)
        body = _row([_col(sk, w[0], extra={"flex_gap": gap(14)}),
                     _col([card], w[1])], GUTTER + 14,
                    align="flex-start", extra={"flex_wrap": "wrap"})
    else:
        body = container([card], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(props.get("outer_width", 72), "%"),
            "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")})
    return _sec([body], props.get("bg", "black"),
                anchor=props.get("anchor", "enquire"))


@block("bbl.ctaband")
def bbl_ctaband(props):
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], "center"))
    if props.get("title"):
        kids.append(_h(props["title"], "h2", T["h_large"], "center"))
    if props.get("text"):
        kids.append(container([_text(props["text"], "center", on_dark=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(66, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"), "gold"))
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props.get("alt_url", "#"),
                         "outline"))
    if btns:
        kids.append(_row(btns, 12, align="center", justify="center",
                         extra={"flex_wrap": "wrap",
                                "flex_direction_mobile": "column",
                                "padding": dims(6, 0, 0, 0)}))
    panel = _card(kids, pad=dims(48, 34, 50, 34), raised=True,
                  extra={"flex_align_items": "center"})
    return _sec([panel], props.get("bg", "black"), anchor=props.get("anchor"))


# ──────────────────────────── WooCommerce ────────────────────────────────

@block("bbl.product")
def bbl_product(props):
    """Single product: gallery one side, the Woo detail widgets the other."""
    gallery = widget("woocommerce-product-images", {
        "image_border_radius": R_CARD,
    })
    detail = [
        widget("woocommerce-breadcrumb", {
            "__typography__": typo_ref(T["body_small"]),
        }, globals_={"text_color": color_ref(C["muted"]),
                     "link_color": color_ref(GOLD_TXT)}),
        widget("woocommerce-product-title", {
            "header_size": "h1",
            "__typography__": typo_ref(T["h_medium"]),
        }, globals_={"title_color": color_ref(C["white"])}),
        widget("woocommerce-product-price", {
            "__typography__": typo_ref(T["h_small"]),
        }, globals_={"price_color": color_ref(GOLD_TXT)}),
        widget("woocommerce-product-short-description", {
            "__typography__": typo_ref(T["body_small"]),
        }, globals_={"text_color": color_ref(C["on_dark"])}),
        widget("woocommerce-product-stock", {
            "__typography__": typo_ref(T["meta"]),
        }, globals_={"in_stock_color": color_ref(GOLD_TXT)}),
        widget("woocommerce-product-add-to-cart", {
            "button_border_radius": R_BTN,
            "quantity_border_radius": box(8),
            "quantity_border_border": "solid",
            "quantity_border_width": box(1),
        }, globals_={
            "button_bg_color": color_ref(GOLD),
            "button_text_color": color_ref(C["surface"]),
            "button_bg_color_hover": color_ref(GOLD_TXT),
            "button_text_color_hover": color_ref(C["surface"]),
            "quantity_bg_color": color_ref(C["surface"]),
            "quantity_border_color": color_ref(LINE),
        }),
        widget("woocommerce-product-meta", {
            "__typography__": typo_ref(T["body_small"]),
        }, globals_={"text_color": color_ref(C["muted"]),
                     "link_color": color_ref(GOLD_TXT)}),
    ]
    if props.get("assurances"):
        detail.append(_card([_ticks(props["assurances"])],
                            pad=dims(18, 18, 18, 18)))
    if props.get("notice"):
        detail.append(_card([_gold(props["notice"], "left", T["eyebrow"])],
                            pad=dims(14, 16, 14, 16)))

    w = _tracks(props.get("ratios", [1, 1]), GUTTER + 14)
    return _sec([_row([
        _col([_card([gallery], pad=dims(18, 18, 18, 18))], w[0]),
        _col(detail, w[1], extra={"flex_gap": gap(14)}),
    ], GUTTER + 14, align="flex-start", extra={"flex_wrap": "wrap"})],
        props.get("bg", "black"),
        pad=dims(44, 0, 56, 0), anchor=props.get("anchor"))


@block("bbl.producttabs")
def bbl_producttabs(props):
    return _sec([widget("woocommerce-product-data-tabs", {
        "__typography__": typo_ref(T["body_small"]),
    }, globals_={
        "tabs_title_normal_color": color_ref(C["muted"]),
        "tabs_title_active_color": color_ref(GOLD_TXT),
        "tab_content_color": color_ref(C["on_dark"]),
    })], props.get("bg", "black"), pad=dims(10, 0, 56, 0),
        anchor=props.get("anchor"))


@block("bbl.related")
def bbl_related(props):
    return _sec([widget("woocommerce-product-related", {
        "columns": str(props.get("columns", 4)),
        "posts_per_page": str(props.get("limit", 4)),
        "orderby": props.get("orderby", "rand"),
        "image_border_radius": R_CARD,
    }, globals_={
        "heading_color": color_ref(C["white"]),
        "title_color": color_ref(C["white"]),
        "price_color": color_ref(GOLD_TXT),
        "button_background_color": color_ref(GOLD),
        "button_text_color": color_ref(C["surface"]),
    })], props.get("bg", "black"), anchor=props.get("anchor"))


@block("bbl.cart")
def bbl_cart(props):
    kids = _head_stack(props, "center")
    kids.append(widget("woocommerce-cart", {
        "sections_title_typography_typography": "custom",
        "checkout_button_border_radius": R_BTN,
        "checkout_button_normal_background_background": "gradient",
        "checkout_button_normal_background_gradient_type": "linear",
        "checkout_button_normal_background_gradient_angle": slider(100, "deg"),
        "checkout_button_normal_background_color_stop": slider(0, "%"),
        "checkout_button_normal_background_color_b_stop": slider(100, "%"),
    }, globals_={
        "sections_title_color": color_ref(C["white"]),
        "checkout_button_normal_background_color": color_ref(GD_HI),
        "checkout_button_normal_background_color_b": color_ref(GD_LO),
        "checkout_button_normal_text_color": color_ref(C["surface"]),
        "checkout_button_hover_background_color": color_ref(GOLD_TXT),
        "checkout_button_hover_text_color": color_ref(C["surface"]),
    }))
    return _sec(kids, props.get("bg", "black"),
                pad=dims(44, 0, 64, 0), anchor=props.get("anchor"))


@block("bbl.checkout")
def bbl_checkout(props):
    kids = _head_stack(props, "center")
    kids.append(widget("woocommerce-checkout-page", {
        "purchase_button_border_radius": R_BTN,
        "purchase_button_normal_background_background": "gradient",
        "purchase_button_normal_background_gradient_type": "linear",
        "purchase_button_normal_background_gradient_angle": slider(100, "deg"),
        "purchase_button_normal_background_color_stop": slider(0, "%"),
        "purchase_button_normal_background_color_b_stop": slider(100, "%"),
    }, globals_={
        "sections_title_color": color_ref(C["white"]),
        "forms_label_color": color_ref(GOLD_TXT),
        "purchase_button_normal_background_color": color_ref(GD_HI),
        "purchase_button_normal_background_color_b": color_ref(GD_LO),
        "purchase_button_normal_text_color": color_ref(C["surface"]),
        "purchase_button_hover_background_color": color_ref(GOLD_TXT),
        "purchase_button_hover_text_color": color_ref(C["surface"]),
    }))
    return _sec(kids, props.get("bg", "black"),
                pad=dims(44, 0, 64, 0), anchor=props.get("anchor"))
