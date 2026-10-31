"""
blocks_vybe.py — VYBE OC Delivery, Orange County CA.

A cannabis delivery storefront built to match eight supplied mockup screens.
The client asked for "exactly like the attached mockups", so this is a match
build: palette, grounds, card anatomy and control shapes are all read off
the pixels.

    #34D1FC  electric cyan — the only accent, on every screen
    #00090E  page ground, near-black with a blue cast
    #0B1720  cards and product tiles
    #132632  form fields and steppers
    #00374C  the one cyan-tinted info panel under the hero
    #1C2D3A  hairlines

THE MOCKUP ALREADY GETS THE HARD CONTRAST CALL RIGHT. White on this cyan is
1.80:1 and fails; the mockup's Add to Cart buttons use a dark label. That
rule is kept — every cyan fill carries near-black #02090E at 11.14:1.

ONE CORRECTION TO THE MOCKUP. Its green FREE pill runs white on a mid-green
at about 3.45:1, which fails for small text. Rebuilt at #3DDC6E with a
near-black label at 11.13:1 — same device, same read, legible. Matching a
mockup does not extend to copying a contrast failure.

THE REGISTRY CONSTRAINT SHAPES THE PRODUCT GRID. loop-grid's query controls
and the WooCommerce dynamic tags are not in the registry, so a bespoke
loop-item card cannot be verified and would risk importing EMPTY — the worst
failure here, because it reads as the client's data entry rather than as a
template bug. So `vy.productgrid` renders the verified `wc-products` /
`woocommerce-archive-products` widgets, and `vy.producttile` exists to build
the mockup's tile anatomy as STATIC markup for the curated sections. The
per-product meta that only PHP can emit — THCa percentage, flavour notes,
the inline weight select — is specified as a WooCommerce hook snippet in the
README rather than guessed at here.

    vy.header       hamburger, wordmark, badged cart
    vy.hero         photographic hero, free-delivery headline
    vy.infopanel    the cyan-tinted 45-minute-window panel
    vy.reviewcard   the Google reviews card
    vy.tabs         FLOWER / VAPES / EDIBLES / ACCESSORIES pill row
    vy.sectionhead  category title with an N-products count
    vy.producttile  the mockup's tile, built statically   ← signature
    vy.productgrid  the verified Woo product widgets
    vy.stickycart   the fixed bottom cart bar
    vy.cart         cart lines, notes, totals, FREE pill
    vy.checkout     contact and delivery fieldsets
    vy.windows      the 45-minute delivery window grid
    vy.payments     the five-method radio list
    vy.confirm      order received, tick in a cyan ring
    vy.steps        numbered What Happens Next
    vy.panels       generic dark panels
    vy.faq          accordion, first answer open
    vy.prose        long-form on the dark ground
    vy.agegate      the 21+ confirmation            ← compliance
    vy.warning      the California warning statement ← compliance
    vy.footer       licence number, links, warning
    vy.pagehero     inner page header
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

CYAN = "primary"        # #34D1FC
CYAN_DEEP = "secondary"  # #12A9D4
# NOTE: "primary"/"secondary"/"accent" are global colour IDS, but the surface
# slots are NOT - they resolve through C to 'surf002'/'surf003'. Using the
# bare strings produces a V1 "dangling colors token" on every container.
PAGE = C["surface"]      # #00090E
CARD = C["surface_alt"]  # #0B1720
INK = "vybink1"         # #02090E — labels on cyan and green
FIELD = "vybfld1"       # #132632
INFO = "vybinfo"        # #00374C
GREEN = "vybgrn1"       # #3DDC6E

VY_PAD = dims(56, 0, 56, 0)
VY_PAD_T = dims(44, 20, 44, 20)
VY_PAD_M = dims(34, 16, 34, 16)
R_CARD = box(8)
R_BTN = box(8)
R_PILL = box(999)
GUTTER = 16
# The mockups are phone screens. The kit still has to work on a desktop, so
# the container is held narrow rather than letting a 2-up product grid
# stretch to 1240 and stop looking like the design.
VY_CONTAINER = 1040

SHADOW = {
    "box_shadow_box_shadow_type": "yes",
    "box_shadow_box_shadow": {"horizontal": 0, "vertical": 6, "blur": 20,
                              "spread": -6, "color": "rgba(0, 0, 0, 0.55)"},
}
SHADOW_HOVER = {
    "box_shadow_hover_box_shadow_type": "yes",
    "box_shadow_hover_box_shadow": {"horizontal": 0, "vertical": 14,
                                    "blur": 34, "spread": -10,
                                    "color": "rgba(52, 209, 252, 0.28)"},
}
SHADOW_LIFTED = {
    "box_shadow_box_shadow_type": "yes",
    "box_shadow_box_shadow": {"horizontal": 0, "vertical": 20, "blur": 50,
                              "spread": -14, "color": "rgba(0, 0, 0, 0.7)"},
}


# ───────────────────────────────── helpers ─────────────────────────────────

def _sec(children, bg="page", pad=None, anchor=None, extra=None):
    grounds = {"page": PAGE, "card": CARD, "info": INFO, "field": FIELD}
    s = {
        "content_width": "boxed",
        "boxed_width": slider(VY_CONTAINER),
        "flex_direction": "column",
        "flex_gap": gap(18),
        "padding": pad or VY_PAD,
        "padding_tablet": VY_PAD_T,
        "padding_mobile": VY_PAD_M,
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
        "flex_gap": gap(8),
        "padding": pad or dims(14, 14, 16, 14),
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


def _btn(label, href, style="cyan", icon_name=None, full=False):
    """Three buttons.

        cyan    #34D1FC fill, NEAR-BLACK label — the primary. Dark and not
                white because white on this cyan is 1.80:1, which the
                mockup itself already avoids.
        outline cyan hairline, cyan label — Continue Shopping
        ghost   hairline on the dark ground — tertiary
    """
    b = _button(label, href, "primary", icon_name or "")
    b["settings"].update({
        "border_radius": R_BTN,
        "text_padding": dims(11, 18, 11, 18),
        "__typography__": typo_ref(T["meta"]),
        "hover_animation": "grow",
        "button_box_shadow_box_shadow_type": "yes",
        "button_box_shadow_box_shadow": {
            "horizontal": 0, "vertical": 4, "blur": 14, "spread": -4,
            "color": "rgba(52, 209, 252, 0.4)"},
    })
    if full:
        b["settings"]["align"] = "justify"
    g = b["settings"].setdefault("__globals__", {})
    if style == "outline":
        b["settings"].update({"border_border": "solid", "border_width": box(1)})
        g.update({"background_color": color_ref(C["transparent"]),
                  "border_color": color_ref(CYAN),
                  "button_text_color": color_ref(CYAN),
                  "button_background_hover_color": color_ref(CYAN),
                  "button_hover_border_color": color_ref(CYAN),
                  "hover_color": color_ref(INK)})
    elif style == "ghost":
        b["settings"].update({"border_border": "solid", "border_width": box(1)})
        g.update({"background_color": color_ref(C["transparent"]),
                  "border_color": color_ref(C["border"]),
                  "button_text_color": color_ref(C["white"]),
                  "button_background_hover_color": color_ref(FIELD),
                  "button_hover_border_color": color_ref(CYAN),
                  "hover_color": color_ref(C["white"])})
    else:
        g.update({"background_color": color_ref(CYAN),
                  "border_color": color_ref(CYAN),
                  "button_text_color": color_ref(INK),
                  "button_background_hover_color": color_ref(CYAN_DEEP),
                  "button_hover_border_color": color_ref(CYAN_DEEP),
                  "hover_color": color_ref(INK)})
    return b


def _pill(text, tone=GREEN, label_tone=INK, small=True):
    return container([widget("heading", {
        "title": text, "header_size": "div", "align": "center",
        "__typography__": typo_ref(T["eyebrow"] if small else T["meta"]),
    }, globals_={"title_color": color_ref(label_tone)})], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(4, 10, 4, 10), "border_radius": box(4),
        "_flex_shrink": "0", "background_background": "classic",
    }, globals_={"background_color": color_ref(tone)})


def _stepper(value="1"):
    """The mockup's minus / value / plus pill, in the field ground."""
    def key(sym):
        return widget("heading", {
            "title": sym, "header_size": "div", "align": "center",
            "__typography__": typo_ref(T["meta"]),
        }, globals_={"title_color": color_ref(C["white"])})
    return container([_row([key("−"), key(value), key("+")], 10,
                           align="center", justify="center",
                           extra={"flex_wrap": "nowrap",
                                  "flex_direction_mobile": "row"})], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(7, 12, 7, 12), "border_radius": R_BTN,
        "border_border": "solid", "border_width": box(1),
        "_flex_shrink": "0", "background_background": "classic",
    }, globals_={"background_color": color_ref(FIELD),
                 "border_color": color_ref(C["border"])})


def _select(label):
    """A styled stand-in for a WooCommerce variation select. The real one is
    emitted by Woo; this reproduces its look in the static tiles so the
    template matches the mockup."""
    return container([_row([
        _small(label, tone=C["muted"]),
        widget("icon", {
            "selected_icon": icon("fas fa-chevron-down"), "size": slider(10),
            "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref(C["muted"])}),
    ], 8, align="center", justify="space-between",
        extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(9, 11, 9, 11), "border_radius": box(6),
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(FIELD),
                 "border_color": color_ref(C["border"])})


def _field(placeholder, optional=False):
    """A styled stand-in for a checkout input, so the Checkout template
    matches the mockup. The live fields come from WooCommerce."""
    return container([_small(placeholder, tone=C["muted"])], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(12, 12, 12, 12), "border_radius": box(6),
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(FIELD),
                 "border_color": color_ref(C["border"])})


def _frame(height=150, label=None):
    """An empty, styled image frame. NO STOCK IS USED ANYWHERE in this kit -
    a licensed cannabis retailer showing stock imagery of product it does not
    stock is a misrepresentation, which is worse than an empty frame."""
    kids = []
    if label:
        kids.append(_small(label, "center", tone=C["muted"]))
    return container(kids, {
        "content_width": "full", "min_height": slider(height),
        "flex_direction": "column",
        "flex_justify_content": "center", "flex_align_items": "center",
        "border_radius": box(6), "border_border": "dashed",
        "border_width": box(1), "background_background": "classic",
    }, globals_={"background_color": color_ref(FIELD),
                 "border_color": color_ref(C["border"])})


def _shot(image, height=150, radius=box(6), label=None):
    if image and image.get("url"):
        return widget("image", {
            "image": media(image["url"], image.get("alt", "")),
            "image_size": "full", "width": slider(100, "%"),
            "height": slider(height), "object-fit": "cover",
            "align": "center", "image_border_radius": radius})
    return _frame(height, label)


def _head_stack(props, align="left"):
    kids = []
    if props.get("eyebrow"):
        kids.append(widget("heading", {
            "title": props["eyebrow"], "header_size": "div", "align": align,
            "__typography__": typo_ref(T["eyebrow"]),
        }, globals_={"title_color": color_ref(CYAN)}))
    if props.get("title"):
        kids.append(_h(props["title"], props.get("tag", "h2"),
                       T["h_medium"], align))
    if props.get("intro"):
        kids.append(_text(props["intro"], align, on_dark=True))
    if not kids:
        return []
    return [container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(6),
        "flex_align_items": "center" if align == "center" else "flex-start"})]


def _form_widget(f):
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
        fields.append(repeater_item(**item))
    return widget("form", {
        "form_name": f.get("form_name", "Enquiry"),
        "form_fields": fields,
        "submit_actions": ["email"],
        "email_to": f.get("email", ""),
        "email_subject": f.get("subject", "New enquiry"),
        "button_text": f.get("submit", "Send"),
        "button_size": "md", "input_size": "md", "button_width": "100",
        "show_labels": "", "mark_required": "",
        "row_gap": slider(10), "column_gap": slider(10),
        "success_message": f.get("success", ""),
        "field_border_radius": box(6), "field_border_width": box(1),
        "button_border_radius": R_BTN,
    }, globals_={
        # `button_background_color` IS the right control on a FORM widget.
        "button_background_color": color_ref(CYAN),
        "button_text_color": color_ref(INK),
        "button_background_hover_color": color_ref(CYAN_DEEP),
        "button_hover_color": color_ref(INK),
        "field_background_color": color_ref(FIELD),
        "field_text_color": color_ref(C["white"]),
        "field_border_color": color_ref(C["border"]),
        "label_color": color_ref(C["white"]),
        "mark_required_color": color_ref(CYAN),
    })


# ─────────────────────────────── chrome ────────────────────────────────────

@block("vy.header")
def vy_header(props):
    """Hamburger left, type-set wordmark centre, badged cart right — the
    mockup's header on every screen."""
    toggle = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"),
        "layout": "dropdown", "align_items": "left",
        "toggle_align": "left",
        "__typography__": typo_ref(T["meta"]),
    }, globals_={
        "color_menu_item": color_ref(C["white"]),
        "color_menu_item_hover": color_ref(CYAN),
        "color_menu_item_active": color_ref(CYAN),
        "toggle_color": color_ref(C["white"]),
        "background_color_dropdown_item": color_ref(CARD),
        "color_dropdown_item": color_ref(C["white"]),
    })

    if props.get("logo"):
        brand = widget("theme-site-logo", {
            "align": "center", "image_size": "full",
            "width": slider(props.get("logo_width", 130)),
            "image": media(props["logo"], props.get("business", "VYBE"))})
    else:
        brand = container([
            widget("heading", {
                "title": props.get("business", "VYBE"), "header_size": "div",
                "align": "center", "link": link("/"),
                "__typography__": typo_ref(T["wordmark"]),
            }, globals_={"title_color": color_ref(CYAN)}),
            widget("heading", {
                "title": props.get("tagline", "OC DELIVERY"),
                "header_size": "div", "align": "center",
                "__typography__": typo_ref(T["eyebrow"]),
            }, globals_={"title_color": color_ref(C["white"])}),
        ], {"content_width": "full", "flex_direction": "column",
            "flex_gap": gap(1), "flex_align_items": "center"})

    cart = widget("woocommerce-menu-cart", {
        # `side_cart_alignment` is the control, not `open_cart_position` -
        # the latter is not registered for this widget.
        "icon": "cart-medium", "cart_type": "side-cart",
        "items_indicator": "bubble", "side_cart_alignment": "right",
    }, globals_={
        "toggle_button_icon_color": color_ref(C["white"]),
        "items_indicator_text_color": color_ref(INK),
        "items_indicator_background_color": color_ref(CYAN),
    })

    row = _row([
        _col([toggle], 20, extra={"flex_justify_content": "center"}),
        _col([brand], 60, extra={"flex_justify_content": "center",
                                 "flex_align_items": "center"}),
        _col([cart], 20, extra={"flex_justify_content": "center",
                                "flex_align_items": "flex-end"}),
    ], GUTTER, align="center", extra={"flex_wrap": "nowrap"})

    return container([row], {
        "content_width": "boxed", "boxed_width": slider(VY_CONTAINER),
        "flex_direction": "column",
        "padding": dims(12, 0, 12, 0),
        "padding_mobile": dims(10, 14, 10, 14),
        "background_background": "classic",
        "sticky": "top", "sticky_on": ["desktop", "tablet", "mobile"],
        "sticky_offset": 0,
    }, globals_={"background_color": color_ref(PAGE)})


@block("vy.footer")
def vy_footer(props):
    """Carries the DCC licence number, which California requires on the
    website. The build asserts it is present."""
    kids = [container([
        widget("heading", {
            "title": props.get("business", "VYBE"), "header_size": "div",
            "align": "center", "__typography__": typo_ref(T["wordmark"]),
        }, globals_={"title_color": color_ref(CYAN)}),
        widget("heading", {
            "title": props.get("tagline", "OC DELIVERY"),
            "header_size": "div", "align": "center",
            "__typography__": typo_ref(T["eyebrow"]),
        }, globals_={"title_color": color_ref(C["white"])}),
    ], {"content_width": "full", "flex_direction": "column",
        "flex_gap": gap(2), "flex_align_items": "center"})]

    if props.get("blurb"):
        kids.append(container([_text(props["blurb"], "center",
                                     on_dark=True, small=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(80, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))

    for c in props.get("columns", []):
        links = []
        for l in c.get("links", []):
            lab = widget("heading", {
                "title": l.get("label", ""), "header_size": "div",
                "align": "center", "__typography__": typo_ref(T["body_small"]),
            }, globals_={"title_color": color_ref(C["muted"])})
            if l.get("url"):
                lab["settings"]["link"] = link(l["url"])
            links.append(lab)
        kids.append(_row(links, 18, align="center", justify="center",
                         extra={"flex_wrap": "wrap"}))

    if props.get("license"):
        kids.append(_card([
            _small(props.get("license_label", "California DCC Licence"),
                   "center", tone=CYAN),
            widget("heading", {
                "title": props["license"], "header_size": "div",
                "align": "center", "__typography__": typo_ref(T["meta"]),
            }, globals_={"title_color": color_ref(C["white"])}),
        ], pad=dims(12, 14, 14, 14), hover=False,
            extra={"flex_align_items": "center"}))

    if props.get("warning"):
        kids.append(container([_text(props["warning"], "center",
                                     on_dark=True, small=True)], {
            "content_width": "full", "flex_direction": "column",
            "padding": dims(12, 14, 12, 14), "border_radius": box(6),
            "border_border": "solid", "border_width": box(1),
        }, globals_={"border_color": color_ref(C["border"])}))

    if props.get("copyright"):
        kids.append(_small(props["copyright"], "center"))

    return container(kids, {
        "content_width": "boxed", "boxed_width": slider(VY_CONTAINER),
        "flex_direction": "column", "flex_gap": gap(16),
        "padding": dims(44, 0, 30, 0),
        "padding_mobile": dims(34, 16, 24, 16),
        "background_background": "classic",
        "flex_align_items": "center",
    }, globals_={"background_color": color_ref(PAGE)})


# ─────────────────────────────── sections ──────────────────────────────────

@block("vy.hero")
def vy_hero(props):
    kids = []
    if props.get("title"):
        kids.append(_h(props["title"], props.get("tag", "h1"), T["hero"],
                       "center"))
    if props.get("intro"):
        kids.append(container([_text(props["intro"], "center",
                                     on_dark=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(86, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"),
                         "cyan"))
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props.get("alt_url", "#"),
                         "outline"))
    if btns:
        kids.append(_row(btns, 10, align="center", justify="center",
                         extra={"flex_wrap": "wrap",
                                "padding": dims(6, 0, 0, 0)}))

    sec = _sec(kids, "page",
               pad=dims(props.get("pad_top", 52), 0,
                        props.get("pad_bottom", 52), 0),
               anchor=props.get("anchor"),
               extra={"min_height": slider(props.get("height", 300)),
                      "flex_justify_content": "center"})
    img = props.get("image")
    if img and img.get("url"):
        sec["settings"].update({
            "background_image": media(img["url"], img.get("alt", "")),
            "background_position": "center center",
            "background_size": "cover", "background_repeat": "no-repeat",
            "background_overlay_background": "classic",
            "background_overlay_opacity": slider(props.get("overlay", 0.58)),
        })
        sec["settings"].setdefault("__globals__", {})[
            "background_overlay_color"] = color_ref(PAGE)
    return sec


@block("vy.infopanel")
def vy_infopanel(props):
    """The cyan-tinted panel under the hero carrying the 45-minute window
    promise."""
    kids = [_row([
        widget("icon", {
            "selected_icon": icon(props.get("icon", "far fa-clock")),
            "size": slider(18), "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref(CYAN)}),
        _text(props.get("text", ""), "left", on_dark=True, small=True),
    ], 10, align="center",
        extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})]
    panel = container(kids, {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(12, 14, 12, 14), "border_radius": R_CARD,
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic", **SHADOW,
    }, globals_={"background_color": color_ref(INFO),
                 "border_color": color_ref(CYAN)})
    return _sec([panel], "page", pad=dims(0, 0, 12, 0),
                anchor=props.get("anchor"))


@block("vy.reviewcard")
def vy_reviewcard(props):
    """The Google reviews card. Built as a LINK to the live listing rather
    than as hardcoded numbers - a rating that drifts from the real one is
    misleading, and for a licensed retailer that is an advertising-compliance
    risk as well as a bad look."""
    stars = _row([widget("icon", {
        "selected_icon": icon("fas fa-star"), "size": slider(12),
        "align": "center", "view": "default",
    }, globals_={"primary_color": color_ref(CYAN)}) for _ in range(5)], 3,
        align="center",
        extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})

    left = container([
        widget("heading", {
            "title": props.get("title", "Google Reviews"),
            "header_size": "div", "align": "left",
            "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(C["white"])}),
        _row([stars, _small(props.get("rating", ""), tone=C["white"])], 8,
             align="center",
             extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"}),
        _small(props.get("note", "")),
    ], {"content_width": "full", "flex_direction": "column",
        "flex_gap": gap(4)})

    mark = container([widget("heading", {
        "title": "G", "header_size": "div", "align": "center",
        "__typography__": typo_ref(T["h_medium"]),
    }, globals_={"title_color": color_ref(CYAN)})], {
        "content_width": "full", "flex_direction": "column",
        "flex_justify_content": "center", "flex_align_items": "center",
        "width": slider(38), "min_height": slider(38), "_flex_shrink": "0",
        "border_radius": box(999), "background_background": "classic",
    }, globals_={"background_color": color_ref(FIELD)})

    chevron = widget("icon", {
        "selected_icon": icon("fas fa-chevron-right"), "size": slider(13),
        "align": "center", "view": "default",
        "link": link(props.get("url", "#")),
    }, globals_={"primary_color": color_ref(C["muted"])})

    card = _card([_row([mark, left, chevron], 12, align="center",
                       extra={"flex_wrap": "nowrap",
                              "flex_direction_mobile": "row"})],
                 pad=dims(12, 14, 12, 14))
    return _sec([card], "page", pad=dims(0, 0, 16, 0),
                anchor=props.get("anchor"))


@block("vy.tabs")
def vy_tabs(props):
    """FLOWER / VAPES / EDIBLES / ACCESSORIES. The active one is a cyan fill
    with a near-black label; the rest are outlined."""
    pills = []
    for it in props.get("items", []):
        active = it.get("active")
        lab = widget("heading", {
            "title": it.get("label", ""), "header_size": "div",
            "align": "center", "__typography__": typo_ref(T["eyebrow"]),
            "link": link(it.get("url", "#")),
        }, globals_={"title_color": color_ref(INK if active else C["white"])})
        pills.append(container([lab], {
            "content_width": "full", "flex_direction": "column",
            "padding": dims(8, 16, 8, 16), "border_radius": R_BTN,
            "_flex_shrink": "0",
            "border_border": "solid", "border_width": box(1),
            "background_background": "classic",
        }, globals_={
            "background_color": color_ref(CYAN if active else FIELD),
            "border_color": color_ref(CYAN if active else C["border"])}))
    return _sec([_row(pills, 8, align="center",
                      extra={"flex_wrap": "wrap"})],
                "page", pad=dims(0, 0, 14, 0), anchor=props.get("anchor"))


@block("vy.sectionhead")
def vy_sectionhead(props):
    kids = [_row([
        _h(props.get("title", ""), props.get("tag", "h2"), T["h_medium"],
           "left"),
        _small(props.get("count", ""), tone=CYAN),
    ], 10, align="baseline",
        extra={"flex_wrap": "wrap", "flex_direction_mobile": "row"})]
    for p in props.get("paragraphs", []):
        kids.append(_text(p, "left", on_dark=True, small=True))
    return _sec(kids, props.get("bg", "page"),
                pad=dims(props.get("pad_top", 8), 0, 12, 0),
                anchor=props.get("anchor"))


@block("vy.producttile")
def vy_producttile(props):
    """THE SIGNATURE TILE, built statically.

    Image with a heart floated top-right, name, a cyan type/THCa meta line, a
    muted flavour line, a full-width select, a From-price, then a row holding
    the stepper and Add to Cart.

    Static because the registry has no WooCommerce dynamic tags, so a
    bespoke loop-item carrying this anatomy cannot be verified and would risk
    importing empty. These tiles are for the curated sections; the live
    archives use `vy.productgrid`, and the README specifies the Woo hook
    snippet that puts the meta back on real product cards.
    """
    per = props.get("columns", 2)
    w = _tracks([1] * per, GUTTER, container=VY_CONTAINER)[0]
    cells = []
    for it in props.get("items", []):
        heart = widget("icon", {
            "selected_icon": icon("far fa-heart"), "size": slider(13),
            "align": "right", "view": "default",
        }, globals_={"primary_color": color_ref(C["white"])})
        shot = _shot(it.get("image"), props.get("shot", 130),
                     label=it.get("frame_label"))
        head = container([shot, container([heart], {
            "content_width": "full", "flex_direction": "column",
            "flex_align_items": "flex-end",
            "margin": dims(-28, 8, 0, 0)})], {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(0)})

        body = [head, widget("heading", {
            "title": it.get("title", ""), "header_size": "h3", "align": "left",
            "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(C["white"])})]
        if it.get("meta"):
            body.append(_small(it["meta"], tone=CYAN))
        if it.get("notes"):
            body.append(_small(it["notes"]))
        if it.get("select"):
            body.append(_select(it["select"]))
        if it.get("price"):
            body.append(widget("heading", {
                "title": it["price"], "header_size": "div", "align": "left",
                "__typography__": typo_ref(T["meta"]),
            }, globals_={"title_color": color_ref(C["white"])}))
        actions = [_stepper()]
        if it.get("cta_label"):
            actions.append(_btn(it["cta_label"], it.get("url", "#"), "cyan"))
        body.append(_row(actions, 8, align="center",
                         extra={"flex_wrap": "nowrap",
                                "flex_direction_mobile": "row"}))
        cells.append(_card(body, w, pad=dims(10, 10, 12, 10)))
    return _sec([_row(cells, GUTTER, align="stretch",
                      extra={"flex_wrap": "wrap"})],
                props.get("bg", "page"), pad=dims(0, 0, 22, 0),
                anchor=props.get("anchor"))


@block("vy.productgrid")
def vy_productgrid(props):
    """The VERIFIED Woo widgets. `wc-products` for a curated grid,
    `woocommerce-archive-products` for an archive - the latter obeys whatever
    query it renders in, so one archive template serves Flower, Vapes,
    Edibles and Accessories."""
    kids = _head_stack(props, props.get("align", "left"))
    if props.get("archive"):
        grid = widget("woocommerce-archive-products", {
            "columns": props.get("columns", 2),
            "rows": props.get("rows", 4),
            "paginate": "yes",
            "allow_order": "",
            "show_result_count": "",
        }, globals_={
            "products_title_color": color_ref(C["white"]),
            "price_color": color_ref(CYAN),
        })
    else:
        grid = widget("wc-products", {
            "columns": props.get("columns", 2),
            "rows": props.get("rows", 4),
            "paginate": "",
            "orderby": props.get("orderby", "date"),
            "order": props.get("order", "desc"),
        }, globals_={
            # wc-products has `title_color`; `products_title_color` exists
            # on woocommerce-archive-products but NOT here.
            "title_color": color_ref(C["white"]),
            "price_color": color_ref(CYAN),
        })
        if props.get("filter_by"):
            grid["settings"]["filter_by"] = props["filter_by"]
    kids.append(grid)
    return _sec(kids, props.get("bg", "page"), anchor=props.get("anchor"))


@block("vy.stickycart")
def vy_stickycart(props):
    """The fixed bottom bar on every shopping screen: badged cart icon, item
    count and running total, View Cart."""
    badge = container([widget("heading", {
        "title": props.get("count", "0"), "header_size": "div",
        "align": "center", "__typography__": typo_ref(T["eyebrow"]),
    }, globals_={"title_color": color_ref(INK)})], {
        "content_width": "full", "flex_direction": "column",
        "flex_justify_content": "center", "flex_align_items": "center",
        "width": slider(20), "min_height": slider(20), "_flex_shrink": "0",
        "border_radius": box(999), "background_background": "classic",
        "margin": dims(-10, 0, 0, -10),
    }, globals_={"background_color": color_ref(CYAN)})

    cart_icon = container([
        widget("icon", {
            "selected_icon": icon("fas fa-cart-shopping"), "size": slider(20),
            "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref(C["white"])}),
        badge,
    ], {"content_width": "full", "flex_direction": "row",
        "flex_align_items": "flex-start", "_flex_shrink": "0",
        "flex_wrap": "nowrap"})

    row = _row([
        cart_icon,
        widget("heading", {
            "title": props.get("summary", ""), "header_size": "div",
            "align": "left", "__typography__": typo_ref(T["meta"]),
        }, globals_={"title_color": color_ref(C["white"])}),
        _btn(props.get("cta_label", "View Cart"),
             props.get("cta_url", "/cart/"), "cyan"),
    ], 12, align="center", justify="space-between",
        extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})

    return container([row], {
        "content_width": "boxed", "boxed_width": slider(VY_CONTAINER),
        "flex_direction": "column",
        "padding": dims(10, 14, 10, 14),
        "border_radius": box(10),
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
        "position": "fixed", "_position": "fixed",
        "_offset_orientation_v": "end", "_offset_y": slider(10),
        "z_index": 95,
        **SHADOW_LIFTED,
    }, globals_={"background_color": color_ref(CARD),
                 "border_color": color_ref(C["border"])})


@block("vy.cart")
def vy_cart(props):
    """Cart lines, order notes, totals with the green FREE pill, and the two
    buttons. The live cart is the woocommerce-cart widget, which this wraps
    when `live` is set."""
    kids = [_row([
        _h(props.get("title", "Your Cart"), props.get("tag", "h2"),
           T["h_medium"], "left"),
        widget("icon", {
            "selected_icon": icon("fas fa-xmark"), "size": slider(16),
            "align": "right", "view": "default",
            "link": link(props.get("close_url", "/")),
        }, globals_={"primary_color": color_ref(C["white"])}),
    ], 10, align="center", justify="space-between",
        extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})]

    if props.get("live"):
        kids.append(widget("woocommerce-cart", {
            "cart_layout": "one_column", "sticky_right_column": "",
        }, globals_={
            "sections_title_color": color_ref(C["white"]),
            "order_summary_title_color": color_ref(C["white"]),
        }))
        return _sec(kids, "page", anchor=props.get("anchor", "cart"))

    for it in props.get("items", []):
        line = _row([
            _shot(it.get("image"), 52, label=None),
            container([
                widget("heading", {
                    "title": it.get("title", ""), "header_size": "div",
                    "align": "left", "__typography__": typo_ref(T["h_small"]),
                }, globals_={"title_color": color_ref(C["white"])}),
                _small(it.get("variant", "")),
                _stepper(),
            ], {"content_width": "full", "flex_direction": "column",
                "flex_gap": gap(5)}),
            container([
                widget("heading", {
                    "title": it.get("price", ""), "header_size": "div",
                    "align": "right", "__typography__": typo_ref(T["meta"]),
                }, globals_={"title_color": color_ref(C["white"])}),
                widget("icon", {
                    "selected_icon": icon("far fa-trash-can"),
                    "size": slider(13), "align": "right", "view": "default",
                }, globals_={"primary_color": color_ref(C["muted"])}),
            ], {"content_width": "full", "flex_direction": "column",
                "flex_gap": gap(8), "flex_align_items": "flex-end"}),
        ], 10, align="flex-start",
            extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})
        kids.append(_card([line], pad=dims(10, 10, 10, 10), hover=False))

    if props.get("notes_label"):
        kids.append(_small(props["notes_label"], tone=C["white"]))
        kids.append(_field(props.get("notes_placeholder", "")))

    rows = []
    for t in props.get("totals", []):
        right = (_pill(t["pill"]) if t.get("pill")
                 else widget("heading", {
                     "title": t.get("value", ""), "header_size": "div",
                     "align": "right",
                     "__typography__": typo_ref(
                         T["h_small"] if t.get("strong") else T["body_small"]),
                 }, globals_={"title_color": color_ref(C["white"])}))
        rows.append(_row([
            widget("heading", {
                "title": t.get("label", ""), "header_size": "div",
                "align": "left",
                "__typography__": typo_ref(
                    T["h_small"] if t.get("strong") else T["body_small"]),
            }, globals_={"title_color": color_ref(
                C["white"] if t.get("strong") else C["muted"])}),
            right,
        ], 10, align="center", justify="space-between",
            extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row",
                   "padding": dims(5, 0, 5, 0)}))
    if rows:
        kids.append(container(rows, {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(2), "padding": dims(8, 0, 4, 0)}))

    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "/checkout/"),
                         "cyan", full=True))
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props.get("alt_url", "/"),
                         "outline", full=True))
    for b in btns:
        kids.append(b)

    return _sec(kids, "page", anchor=props.get("anchor", "cart"))


@block("vy.checkout")
def vy_checkout(props):
    """The checkout fieldsets. `live` swaps in the real
    woocommerce-checkout-page widget; otherwise this renders the mockup's
    styled layout so the template matches."""
    kids = _head_stack(props, "left")
    if props.get("live"):
        kids.append(widget("woocommerce-checkout-page", {
            }, globals_={
            "sections_title_color": color_ref(C["white"]),
            "sections_descriptions_color": color_ref(C["white"]),
        }))
        return _sec(kids, "page", anchor=props.get("anchor", "checkout"))

    for fs in props.get("fieldsets", []):
        inner = [widget("heading", {
            "title": fs.get("title", ""), "header_size": "h3", "align": "left",
            "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(C["white"])})]
        for f in fs.get("fields", []):
            if f.get("select"):
                inner.append(_select(f["label"]))
            else:
                inner.append(_field(f["label"]))
            if f.get("note"):
                inner.append(_small(f["note"]))
        kids.append(_card(inner, pad=dims(14, 14, 16, 14), hover=False))
    return _sec(kids, "page", anchor=props.get("anchor", "checkout"))


@block("vy.windows")
def vy_windows(props):
    """The 45-minute delivery window grid. This is the STYLED LAYOUT - which
    windows are actually free on a given date is WooCommerce behaviour and is
    specified in the README."""
    kids = [widget("heading", {
        "title": props.get("title", ""), "header_size": "h3", "align": "left",
        "__typography__": typo_ref(T["h_small"]),
    }, globals_={"title_color": color_ref(C["white"])})]

    for r in props.get("radios", []):
        kids.append(_row([
            widget("icon", {
                "selected_icon": icon("far fa-circle-dot" if r.get("active")
                                      else "far fa-circle"),
                "size": slider(14), "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref(
                CYAN if r.get("active") else C["muted"])}),
            _small(r.get("label", ""), tone=C["white"]),
        ], 9, align="center",
            extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row",
                   "padding": dims(4, 0, 4, 0)}))

    if props.get("date_label"):
        kids.append(_small(props["date_label"], tone=C["white"]))
        kids.append(_select(props.get("date_value", "")))
    if props.get("windows_label"):
        kids.append(_small(props["windows_label"], tone=C["white"]))

    slots = props.get("windows", [])
    w = _tracks([1, 1], 8, container=VY_CONTAINER - 40)[0]
    cells = []
    for s in slots:
        active = s.get("active")
        cells.append(container([widget("heading", {
            "title": s.get("label", ""), "header_size": "div",
            "align": "center", "__typography__": typo_ref(T["body_small"]),
        }, globals_={"title_color": color_ref(
            INK if active else C["white"])})], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(w, "%"), "width_mobile": slider(48, "%"),
            "padding": dims(9, 8, 9, 8), "border_radius": box(6),
            "border_border": "solid", "border_width": box(1),
            "background_background": "classic",
        }, globals_={
            "background_color": color_ref(CYAN if active else FIELD),
            "border_color": color_ref(CYAN if active else C["border"])}))
    if cells:
        kids.append(_row(cells, 8, align="stretch",
                         extra={"flex_wrap": "wrap"}))

    card = _card(kids, pad=dims(14, 14, 16, 14), hover=False)
    return _sec([card], "page", pad=dims(0, 0, 14, 0),
                anchor=props.get("anchor"))


@block("vy.payments")
def vy_payments(props):
    """The five-method radio list. Styled layout only - three of the five
    exist as a gateway plugin already written for this repo."""
    kids = [widget("heading", {
        "title": props.get("title", "Payment Method"), "header_size": "h3",
        "align": "left", "__typography__": typo_ref(T["h_small"]),
    }, globals_={"title_color": color_ref(C["white"])})]
    for m in props.get("items", []):
        active = m.get("active")
        kids.append(_row([
            widget("icon", {
                "selected_icon": icon("far fa-circle-dot" if active
                                      else "far fa-circle"),
                "size": slider(14), "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref(
                CYAN if active else C["muted"])}),
            widget("icon", {
                "selected_icon": icon(m.get("icon", "fas fa-wallet")),
                "size": slider(15), "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref(CYAN)}),
            _small(m.get("label", ""), tone=C["white"]),
        ], 10, align="center",
            extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row",
                   "padding": dims(6, 0, 6, 0)}))
    if props.get("cta_label"):
        kids.append(_btn(props["cta_label"], props.get("cta_url", "#"),
                         "cyan", full=True))
    if props.get("note"):
        kids.append(_small(props["note"], "center"))
    card = _card(kids, pad=dims(14, 14, 16, 14), hover=False)
    return _sec([card], "page", anchor=props.get("anchor"))


@block("vy.confirm")
def vy_confirm(props):
    """Order received: a tick in a cyan ring, the order number, and a details
    card."""
    ring = container([widget("icon", {
        "selected_icon": icon("fas fa-check"), "size": slider(24),
        "align": "center", "view": "default",
    }, globals_={"primary_color": color_ref(INK)})], {
        "content_width": "full", "flex_direction": "column",
        "flex_justify_content": "center", "flex_align_items": "center",
        "width": slider(58), "min_height": slider(58), "_flex_shrink": "0",
        "border_radius": box(999), "background_background": "classic",
    }, globals_={"background_color": color_ref(CYAN)})

    kids = [container([ring], {
        "content_width": "full", "flex_direction": "column",
        "flex_align_items": "center"})]
    if props.get("title"):
        kids.append(_h(props["title"], "h1", T["h_large"], "center"))
    if props.get("intro"):
        kids.append(_text(props["intro"], "center", on_dark=True, small=True))
    if props.get("order"):
        kids.append(_small(props["order"], "center", tone=CYAN))

    rows = []
    for d in props.get("details", []):
        rows.append(_row([
            widget("icon", {
                "selected_icon": icon(d.get("icon", "far fa-calendar")),
                "size": slider(13), "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref(CYAN)}),
            _small(d.get("value", ""), tone=C["white"]),
        ], 10, align="center",
            extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row",
                   "padding": dims(5, 0, 5, 0)}))
    if rows:
        head = [widget("heading", {
            "title": props.get("details_title", "Order Details"),
            "header_size": "h3", "align": "left",
            "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(C["white"])})]
        kids.append(_card(head + rows, pad=dims(14, 14, 14, 14), hover=False))

    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"),
                         "cyan", full=True))
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props.get("alt_url", "/"),
                         "outline", full=True))
    kids.extend(btns)
    return _sec(kids, "page", anchor=props.get("anchor"),
                extra={"flex_align_items": "center"})


@block("vy.steps")
def vy_steps(props):
    kids = [widget("heading", {
        "title": props.get("title", ""), "header_size": "h3", "align": "left",
        "__typography__": typo_ref(T["h_small"]),
    }, globals_={"title_color": color_ref(C["white"])})]
    for n, it in enumerate(props.get("items", []), 1):
        num = container([widget("heading", {
            "title": str(n), "header_size": "div", "align": "center",
            "__typography__": typo_ref(T["eyebrow"]),
        }, globals_={"title_color": color_ref(INK)})], {
            "content_width": "full", "flex_direction": "column",
            "flex_justify_content": "center", "flex_align_items": "center",
            "width": slider(22), "min_height": slider(22),
            "_flex_shrink": "0", "border_radius": box(999),
            "background_background": "classic",
        }, globals_={"background_color": color_ref(CYAN)})
        kids.append(_row([num, _small(
            it if isinstance(it, str) else it.get("text", ""),
            tone=C["white"])], 10, align="flex-start",
            extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row",
                   "padding": dims(5, 0, 5, 0)}))
    card = _card(kids, pad=dims(14, 14, 16, 14), hover=False)
    return _sec([card], "page", anchor=props.get("anchor"))


@block("vy.panels")
def vy_panels(props):
    kids = _head_stack(props, props.get("align", "left"))
    per = props.get("columns", 2)
    w = _tracks([1] * per, GUTTER, container=VY_CONTAINER)[0]
    cells = []
    for it in props.get("items", []):
        body = []
        if it.get("icon"):
            body.append(widget("icon", {
                "selected_icon": icon(it["icon"]), "size": slider(20),
                "align": "left", "view": "default",
            }, globals_={"primary_color": color_ref(CYAN)}))
        if it.get("title"):
            body.append(widget("heading", {
                "title": it["title"], "header_size": "h3", "align": "left",
                "__typography__": typo_ref(T["h_small"]),
            }, globals_={"title_color": color_ref(C["white"])}))
        if it.get("text"):
            body.append(_small(it["text"]))
        cells.append(_card(body, w, pad=dims(14, 14, 16, 14)))
    kids.append(_row(cells, GUTTER, align="stretch",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "page"), anchor=props.get("anchor"))


@block("vy.faq")
def vy_faq(props):
    kids = _head_stack(props, props.get("align", "left"))
    kids.append(_faq(props.get("items", [])))
    return _sec(kids, "page", anchor=props.get("anchor"))


@block("vy.prose")
def vy_prose(props):
    kids = _head_stack(props, "left")
    for p in props.get("paragraphs", []):
        kids.append(_text(p, "left", on_dark=True, small=True))
    if props.get("list"):
        for li in props["list"]:
            kids.append(_row([
                widget("icon", {
                    "selected_icon": icon("fas fa-check"), "size": slider(11),
                    "align": "center", "view": "default",
                }, globals_={"primary_color": color_ref(CYAN)}),
                _small(li, tone=C["white"]),
            ], 9, align="flex-start",
                extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row",
                       "padding": dims(4, 0, 4, 0)}))
    return _sec(kids, "page", anchor=props.get("anchor"))


# ───────────────────────────── compliance ──────────────────────────────────

@block("vy.agegate")
def vy_agegate(props):
    """The 21+ confirmation. NOT in the mockups - California requires age
    verification before sales content is shown. Built as a real section so
    it exists; the README covers wiring it as an interstitial."""
    kids = [container([widget("heading", {
        "title": props.get("business", "VYBE"), "header_size": "div",
        "align": "center", "__typography__": typo_ref(T["wordmark"]),
    }, globals_={"title_color": color_ref(CYAN)})], {
        "content_width": "full", "flex_direction": "column",
        "flex_align_items": "center"})]
    if props.get("title"):
        kids.append(_h(props["title"], "h1", T["h_large"], "center"))
    if props.get("intro"):
        kids.append(container([_text(props["intro"], "center", on_dark=True,
                                     small=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(80, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    btns = []
    if props.get("yes_label"):
        btns.append(_btn(props["yes_label"], props.get("yes_url", "/"),
                         "cyan"))
    if props.get("no_label"):
        btns.append(_btn(props["no_label"], props.get("no_url", "#"),
                         "ghost"))
    if btns:
        kids.append(_row(btns, 10, align="center", justify="center",
                         extra={"flex_wrap": "wrap"}))
    if props.get("note"):
        kids.append(_small(props["note"], "center"))
    return _sec(kids, "page", pad=dims(70, 0, 70, 0),
                anchor=props.get("anchor", "age-gate"),
                extra={"flex_align_items": "center",
                       "min_height": slider(460),
                       "flex_justify_content": "center"})


@block("vy.warning")
def vy_warning(props):
    """The California warning statement, in a bordered panel so it reads as
    a legal notice rather than as marketing copy."""
    kids = []
    if props.get("title"):
        kids.append(widget("heading", {
            "title": props["title"], "header_size": "h3", "align": "left",
            "__typography__": typo_ref(T["eyebrow"]),
        }, globals_={"title_color": color_ref(CYAN)}))
    for p in props.get("paragraphs", []):
        kids.append(_small(p, tone=C["white"]))
    panel = container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(8),
        "padding": dims(14, 14, 16, 14), "border_radius": R_CARD,
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(CARD),
                 "border_color": color_ref(CYAN)})
    return _sec([panel], "page", anchor=props.get("anchor", "warning"))


@block("vy.pagehero")
def vy_pagehero(props):
    kids = []
    if props.get("eyebrow"):
        kids.append(widget("heading", {
            "title": props["eyebrow"], "header_size": "div", "align": "left",
            "__typography__": typo_ref(T["eyebrow"]),
        }, globals_={"title_color": color_ref(CYAN)}))
    if props.get("title"):
        kids.append(_h(props["title"], props.get("tag", "h1"), T["h_large"],
                       "left"))
    if props.get("intro"):
        kids.append(_text(props["intro"], "left", on_dark=True, small=True))
    return _sec(kids, "page", pad=dims(40, 0, 20, 0),
                anchor=props.get("anchor"))
