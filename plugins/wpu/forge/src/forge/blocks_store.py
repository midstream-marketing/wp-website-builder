"""
blocks_store.py — shared parts of the RUO e-commerce block family.

A WooCommerce storefront is a different design system from the service-trade
families in `blocks.py`: the page furniture is a cart and a search field
rather than a phone number, the hero sells a catalogue rather than a callout,
and the compliance notice is not decoration but the thing that keeps the
payment processor attached.

Structure follows silverstatebiolabs.com, which the client approved: light
body, one dark hero, pale-blue panel cards, blue section headings, a dark
image band carrying the quality promise, a five-column dark footer. Colour
comes from the client's own logo instead — see the client `intake.json`.

The family is split by template area so a new page template is a new module
rather than another thousand lines here:

    blocks_store.py       helpers, header, footer
    blocks_store_home.py  homepage sections
    blocks_store_shop.py  product archive + single product

Factories are namespaced `store.*` and are deliberately list-shaped: every
grid takes an `items` list of any length, so most new pages are composed in
the IR from factories that already exist.
"""
from __future__ import annotations

from .core import (
    container, widget, repeater_item, slider, dims, box, media, link, icon,
    gap, color_ref, typo_ref, dynamic, css,
)
from .tokens import C, T
from .blocks import (
    block, render, _row, _col, _section, _tracks, _track, _grid_widths,
    _heading, _text, _button, _eyebrow, _scrim, _photo, _hover_lift,
    CARD_SHADOW, CARD_SHADOW_SOFT, SECTION_PAD, SECTION_PAD_T, SECTION_PAD_M,
    KIT_CONTAINER, TABLET_CONTAINER,
)

# The storefront runs a tighter vertical rhythm than the trade families. A
# shop page carries more sections than a service page, and the reference's
# measured section padding is 40px a side, so the trade families' 104px of air
# between bands reads as a different, much sleepier site.
ST_PAD = dims(84, 0, 84, 0)
ST_PAD_T = dims(64, 24, 64, 24)
ST_PAD_M = dims(48, 20, 48, 20)

R_CARD = box(10)          # reference radii cluster at 4-8px; 10 on cards
R_PANEL = box(14)
R_PILL = box(999)


def _st_section(children, bg="white", pad=None, extra=None):
    """Section wrapper on the storefront rhythm."""
    s = {"padding_tablet": ST_PAD_T, "padding_mobile": ST_PAD_M}
    if extra:
        s.update(extra)
    return _section(children, bg=bg, pad=pad or ST_PAD, extra=s)


def _st_chip(text, align="center", on_dark=False):
    """Small filled capsule label.

    Sized by its own padding rather than by a stated width: a chip that states
    a width is either too wide for a short label or clips a long one.
    """
    # White on the dark chip, not the brand blue. `brand_on_dark` clears 4.5:1
    # against the near-black section (4.58), but the chip's own fill is white
    # at 16% over that ground — an effective #35383E — where the same blue is
    # 2.87:1. A 12px uppercase label is small text, so it has to be white.
    lab = widget("heading", {
        "title": text, "header_size": "div", "align": "center",
    }, globals_={
        "title_color": color_ref(C["white"] if on_dark else C["ink_primary"]),
        "typography_typography": typo_ref(T["eyebrow"]),
    })
    return container([lab], {
        "content_width": "full",
        "flex_direction": "row",
        "flex_justify_content": "center",
        "_flex_grow": 0,
        "padding": dims(7, 16, 7, 16),
        "border_radius": R_PILL,
        "background_background": "classic",
        "_flex_align_self": {"center": "center", "left": "flex-start"}[align],
    }, globals_={
        "background_color": color_ref(C["rule_dark"] if on_dark else C["surface_alt"]),
    })


def _st_head(props, align="center", on_dark=False):
    """Eyebrow chip + heading + subheading — the reference's section opener.

    The eyebrow is a filled pale-blue chip rather than bare letterspaced text.
    It is the one piece of section furniture the reference repeats on every
    band, and it is most of what makes the page read as that site.
    """
    out = []
    if props.get("eyebrow"):
        out.append(_st_chip(props["eyebrow"], align=align, on_dark=on_dark))
    if props.get("heading"):
        out.append(_heading(props["heading"], props.get("level", "h2"),
                            T["h_large"], align=align, on_dark=on_dark,
                            tone="brand"))
    if props.get("sub"):
        out.append(_text(props["sub"], align=align, on_dark=on_dark))
    return _col(out, extra={
        "flex_gap": gap(14),
        "flex_align_items": {"center": "center", "left": "flex-start"}[align],
        "content_width": "boxed",
        "boxed_width": slider(props.get("measure", 760)),
        **({"margin": dims(0, "auto", 0, "auto")} if align == "center" else {}),
    })


def _st_card(children, bg="white", pad=None, radius=None, border=True, extra=None):
    """The storefront's one card shape. Every tile on the site is this."""
    s = {
        "content_width": "full",
        "flex_direction": "column",
        "flex_gap": gap(14),
        "padding": pad or dims(28, 28, 28, 28),
        "padding_mobile": dims(22, 20, 22, 20),
        "border_radius": radius or R_CARD,
        "background_background": "classic",
        **CARD_SHADOW_SOFT,
    }
    if border:
        s.update({"border_border": "solid", "border_width": box(1)})
    if extra:
        s.update(extra)
    g = {"background_color": color_ref(
        {"white": C["white"], "alt": C["surface_alt"], "surface": C["surface"],
         "dark": "secondary"}.get(bg, C["white"]))}
    if border:
        g["border_color"] = color_ref(C["border"])
    # `container()` assigns __globals__ wholesale, so a caller that put one in
    # `extra` would have it silently replaced by the card's own — the failure
    # being an unstyled panel rather than an error. Merge instead, caller wins.
    g.update(s.pop("__globals__", {}))
    return container(children, s, globals_=g)


def _st_icon(icon_cls, size=22, on_dark=False, boxed=True):
    """Brand-blue icon, optionally in a pale square — the reference's tile mark."""
    ic = widget("icon", {
        "selected_icon": icon(icon_cls), "size": slider(size),
        "align": "center", "view": "default",
    }, globals_={"primary_color": color_ref(
        C["brand_on_dark"] if on_dark else "primary")})
    if not boxed:
        return ic
    return container([ic], {
        "content_width": "full",
        "flex_direction": "row",
        "flex_justify_content": "center",
        "flex_align_items": "center",
        "width": slider(44),
        "min_height": slider(44),
        "_flex_grow": 0,
        "_flex_align_self": "flex-start",
        "border_radius": box(8),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(
        C["rule_dark"] if on_dark else C["surface_alt"])})


def _st_iconcard(item, on_dark=False, bg="white"):
    """Icon + title + body. The unit of every feature grid on the site."""
    return _st_card([
        _st_icon(item.get("icon", "fas fa-circle-check"), on_dark=on_dark),
        _heading(item["title"], "h3", T["h_small"], on_dark=on_dark),
        _text(item["text"], on_dark=on_dark, small=True),
    ], bg="dark" if on_dark else bg, border=not on_dark)


# ═══════════════════════════════ header ═══════════════════════════════

@block("store.header")
def store_header(props):
    """Announcement marquee, main bar with cart and search, trust strip.

    Three stacked bars, because the brief asks each to do a different job: the
    top one rotates promotional and compliance lines, the middle one navigates
    and sells, the bottom one carries the trust claims that have to survive a
    payment-processor review.
    """
    out = []
    if props.get("announcements"):
        out.append(_store_announce(props["announcements"],
                                   speed=props.get("announce_speed", 34)))
    out.append(_store_bar(props))
    if props.get("trust"):
        out.append(_store_trust_strip(props["trust"]))
    return container(out, {"content_width": "full", "flex_direction": "column",
                           "flex_gap": gap(0)})


def _store_announce(messages, speed=34):
    """Scrolling compliance/promo strip.

    Scoped CSS rather than a widget: Elementor has no marquee control, and the
    alternative — a third-party ticker — would put a plugin dependency into
    the header, the one template that must import cleanly on a bare Pro + Woo
    install.

    The list is duplicated end to end and translated by exactly -50%, which is
    what makes the loop seamless; translating a single copy snaps back to a
    blank strip at the end of every cycle. `prefers-reduced-motion` stops the
    animation rather than hiding the text, so the compliance line is still
    readable for anyone who has asked the OS for less movement.
    """
    sep = "&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;"
    run = sep.join(messages)
    inner = widget("text-editor", {
        "editor": "<p>" + run + sep + run + "</p>", "align": "left",
    }, globals_={
        "text_color": color_ref(C["on_primary"]),
        "typography_typography": typo_ref(T["meta"]),
    })
    return container([inner], {
        "content_width": "full",
        "flex_direction": "row",
        "padding": dims(8, 0, 8, 0),
        "background_background": "classic",
        "custom_css": css(
            "selector { overflow: hidden; }",
            "selector p { white-space: nowrap; margin: 0; "
            "animation: forge-store-marquee " + str(speed) + "s linear infinite; }",
            "selector:hover p { animation-play-state: paused; }",
            "@keyframes forge-store-marquee { from { transform: translateX(0); } "
            "to { transform: translateX(-50%); } }",
            "@media (prefers-reduced-motion: reduce) { selector p { animation: none; } }",
        ),
    }, globals_={"background_color": color_ref("primary")})


def _store_bar(props):
    """Logo, primary nav, search, account, cart."""
    logo = widget("theme-site-logo", {
        "align": "left", "width": slider(props.get("logo_width", 190)),
        **({"image": media(props["logo"], props.get("business", ""))}
           if props.get("logo") else {}),
    })

    nav = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"),
        "layout": "horizontal",
        "align_items": "center",
        "pointer": "underline",
        "menu_space_between": slider(props.get("nav_gap", 20)),
        "toggle_align": "right",
        "submenu_icon": {"value": "fas fa-caret-down", "library": "fa-solid"},
        "dropdown_border_radius": box(10),
        "padding_horizontal_dropdown_item": slider(18),
        "padding_vertical_dropdown_item": slider(11),
    }, globals_={
        "color_menu_item": color_ref(C["on_dark"]),
        "color_menu_item_hover": color_ref(C["white"]),
        "color_menu_item_active": color_ref(C["white"]),
        "pointer_color_menu_item_hover": color_ref(C["brand_on_dark"]),
        "pointer_color_menu_item_active": color_ref(C["brand_on_dark"]),
        "menu_typography_typography": typo_ref("accent"),
        "color_dropdown_item": color_ref("text"),
        "color_dropdown_item_hover": color_ref(C["ink_primary"]),
        "background_color_dropdown_item": color_ref(C["white"]),
        "background_color_dropdown_item_hover": color_ref(C["surface_alt"]),
        "dropdown_typography_typography": typo_ref(T["body_small"]),
    })

    search = widget("search-form", {
        "skin": "classic",
        "placeholder": props.get("search_placeholder", "Search for products..."),
        "button_type": "icon",
        "icon": "search",
        "size": slider(42),
        "icon_size": slider(15),
        "border_radius": box(8),
        "button_width": slider(46),
    }, globals_={
        "input_text_color": color_ref(C["white"]),
        "input_background_color": color_ref(C["rule_dark"]),
        "input_border_color": color_ref(C["rule_dark"]),
        "input_border_color_focus": color_ref(C["brand_on_dark"]),
        "button_background_color": color_ref("primary"),
        "button_text_color": color_ref(C["on_primary"]),
        "input_typography_typography": typo_ref(T["body_small"]),
    })

    account = widget("button", {
        "text": "",
        "link": link(props.get("account_href", "/my-account/")),
        "selected_icon": icon("far fa-user"),
        "icon_align": "left",
        "text_padding": dims(11, 13, 11, 13),
        "border_radius": box(8),
        "border_border": "solid",
        "border_width": box(1),
    }, globals_={
        "button_text_color": color_ref(C["on_dark"]),
        "background_color": color_ref(C["transparent"]),
        "border_color": color_ref(C["rule_dark"]),
        "hover_color": color_ref(C["white"]),
        "button_background_hover_color": color_ref("primary"),
        "button_hover_border_color": color_ref("primary"),
    })

    # `mini-cart` gives the slide-out panel. The alternative, `button`, links
    # straight to /cart/ and loses the add-to-cart feedback that stops a
    # shopper wondering whether the click registered.
    cart = widget("woocommerce-menu-cart", {
        "cart_type": "mini-cart",
        "icon": "cart-medium",
        "items_indicator": "bubble",
        "toggle_icon_size": slider(20),
        "toggle_button_padding": dims(9, 11, 9, 11),
        "toggle_button_border_radius": box(8),
        "show_subtotal": "",
        "show_divider": "yes",
        "show_remove_icon": "yes",
        "view_cart_button_show": "yes",
        "checkout_button_show": "yes",
    }, globals_={
        "toggle_button_text_color": color_ref(C["on_dark"]),
        "toggle_button_icon_color": color_ref(C["on_dark"]),
        "toggle_button_hover_icon_color": color_ref(C["white"]),
        "items_indicator_background_color": color_ref("primary"),
        "items_indicator_text_color": color_ref(C["on_primary"]),
        "subtotal_color": color_ref("secondary"),
    })

    w_logo, w_nav, w_util = _tracks(props.get("bar_ratios", [20, 48, 32]), 20)

    return container([
        _row([
            _col([logo], w_logo, extra={"flex_justify_content": "center"}),
            _col([nav], w_nav, extra={"flex_justify_content": "center"}),
            _col([_row([search, account, cart], 10, align="center",
                       justify="flex-end",
                       extra={"flex_direction_mobile": "row",
                              "flex_wrap": "nowrap"})],
                 w_util, extra={"flex_justify_content": "center"}),
        ], gap_px=20, align="center"),
    ], {
        "content_width": "boxed",
        "flex_direction": "row",
        "padding": dims(14, 0, 14, 0),
        "padding_mobile": dims(12, 18, 12, 18),
        "background_background": "classic",
    }, globals_={"background_color": color_ref("secondary")})


def _store_trust_strip(items):
    """The claims under the nav.

    Hidden on mobile: four of them wrap to three lines on a phone and push the
    catalogue below the fold, and they are repeated in the hero trust row
    anyway.
    """
    lst = widget("icon-list", {
        "icon_list": [repeater_item(
            text=i["text"],
            selected_icon=icon(i.get("icon", "fas fa-circle-check")))
            for i in items],
        "view": "inline",
        "space_between": slider(30),
        "icon_size": slider(13),
    }, globals_={
        "icon_color": color_ref("primary"),
        "text_color": color_ref("text"),
        "icon_typography_typography": typo_ref(T["meta"]),
    })
    return container([lst], {
        "content_width": "boxed",
        "flex_direction": "row",
        "flex_justify_content": "center",
        "padding": dims(10, 0, 10, 0),
        "border_width": dims(0, 0, 1, 0),
        "border_border": "solid",
        "hide_mobile": "hidden-mobile",
        "background_background": "classic",
    }, globals_={
        "background_color": color_ref(C["surface"]),
        "border_color": color_ref(C["border"]),
    })


# ═══════════════════════════════ footer ═══════════════════════════════

@block("store.footer")
def store_footer(props):
    """Dark five-column footer, trust/payment badges, disclaimer, copyright.

    The RUO disclaimer strip sits above the copyright and below a hairline,
    because it is a legal notice rather than navigation — the brief asks for
    it verbatim and in the same words everywhere it appears.
    """
    groups = props.get("groups", [])
    brand_ratio = props.get("brand_ratio", 26)
    ratios = [brand_ratio] + [(100 - brand_ratio) / len(groups)] * len(groups) \
        if groups else [100]
    widths = _tracks(ratios, 28)

    logo = (widget("image", {
        "image": media(props["logo"], props.get("business", "")),
        "width": slider(props.get("logo_width", 180)), "align": "left"})
        if props.get("logo") else
        widget("theme-site-logo", {"align": "left",
                                   "width": slider(props.get("logo_width", 180))}))

    brand_col = [logo]
    if props.get("blurb"):
        brand_col.append(_text(props["blurb"], on_dark=True, small=True))
    if props.get("socials"):
        brand_col.append(widget("social-icons", {
            "social_icon_list": [
                repeater_item(social_icon=icon("fab fa-" + s["network"]),
                              link=link(s["url"], external=True))
                for s in props["socials"]],
            "align": "left", "icon_size": slider(15), "shape": "circle",
            "icon_spacing": slider(9),
            "icon_color": "custom",
        }, globals_={
            "icon_primary_color": color_ref(C["rule_dark"]),
            "icon_secondary_color": color_ref(C["white"]),
            "icon_primary_color_hover": color_ref("primary"),
        }))

    cols = [_col(brand_col, widths[0], extra={"flex_gap": gap(16)})]
    for grp, w in zip(groups, widths[1:]):
        cols.append(_col([
            _heading(grp["title"], "h4", T["h_small"], on_dark=True),
            widget("icon-list", {
                "icon_list": [repeater_item(
                    text=i["text"], link=link(i.get("href", "")),
                    selected_icon={"value": "", "library": ""})
                    for i in grp["items"]],
                "space_between": slider(8),
            }, globals_={
                "text_color": color_ref(C["on_dark"]),
                "icon_typography_typography": typo_ref(T["body_small"]),
            }),
        ], w, extra={"flex_gap": gap(13)}))

    out = [_row(cols, 28, align="flex-start")]

    badges = []
    if props.get("badges"):
        badges.append(widget("icon-list", {
            "icon_list": [repeater_item(
                text=b["text"],
                selected_icon=icon(b.get("icon", "fas fa-shield-halved")))
                for b in props["badges"]],
            "view": "inline", "space_between": slider(22), "icon_size": slider(13),
        }, globals_={
            "icon_color": color_ref(C["brand_on_dark"]),
            "text_color": color_ref(C["on_dark"]),
            "icon_typography_typography": typo_ref(T["meta"]),
        }))
    if props.get("payments"):
        badges.append(_text(
            props.get("payments_label", "") + " " +
            "&nbsp;&nbsp;".join(props["payments"]),
            align="right", on_dark=True, small=True))
    if badges:
        out.append(_st_rule())
        out.append(_row(badges, 24, align="center",
                        justify="space-between" if len(badges) > 1 else "center"))

    out.append(_st_rule())
    if props.get("disclaimer"):
        out.append(_text(props["disclaimer"], align="center", on_dark=True,
                         small=True))
    if props.get("copyright"):
        out.append(_text(props["copyright"], align="center", on_dark=True,
                         small=True))

    return _section(out, bg="dark", pad=dims(72, 0, 34, 0), extra={
        "flex_gap": gap(22),
        "padding_tablet": dims(60, 24, 30, 24),
        "padding_mobile": dims(48, 20, 26, 20),
    })


def _st_rule():
    """Hairline on a dark ground. The light footer's border token is invisible
    here, so dividers inside dark panels use the dedicated dark rule token."""
    return widget("divider", {
        "weight": slider(1), "gap": slider(4), "style": "solid",
    }, globals_={"color": color_ref(C["rule_dark"])})
