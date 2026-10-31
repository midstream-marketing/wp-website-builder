"""
blocks_econ.py — Economy Roofing & Masonry, Dracut MA.

No visual reference: the client's live site is down and none was given. What
IS specified is the structure, by a 25-page copy document that enumerates
every section of every page, and the palette, by the brief: blue and orange.

THE ORANGE IS THREE VALUES, and the split is measured rather than chosen.
White on the brand's bright orange #F26A1B is 3.06:1 — fine for a large
display word, too weak for a button label. So:

    #D4540B   button fills, white label        4.14:1  ✓
    #B8470A   orange used as TEXT on white     5.32:1  ✓
    #F26A1B   icons, rules, accents on navy    4.40:1 on #0A2E5C

A DELIBERATE CORRECTION TO RECENT HABIT. An audit of the four kits before
this one found box-shadow used in one family out of twenty, and per-factory
detail drifting down. `CARD_SHADOW` has been sitting in blocks.py the whole
time; the tooling was there and I stopped reaching for it. Depth and hover
feedback are cheap and their absence is most of what reads as "flat". Every
card here has a resting shadow and lifts on hover; every button has a shadow
and a hover state. The fidelity gate holds it that way.

    ec.topbar       address / phone / hours strip
    ec.header       wordmark or logo, nav, phone, CTA
    ec.hero         photo + navy scrim, with room reserved underneath
    ec.bookingbar   the booking strip that OVERLAPS the hero  ← signature
    ec.trust        four-item reassurance strip
    ec.sectionhead  orange caps eyebrow over an orange rule, then the heading
    ec.about        photo beside copy, with four highlight cards
    ec.services     photo service cards
    ec.testimonials eight REAL reviews with stars
    ec.why          six why-choose-us cards
    ec.gallery      deliberately uneven project grid
    ec.steps        numbered process on the navy band
    ec.prose        the sub-service body: intro, what we do, signs you need it
    ec.related      three related service links
    ec.callout      the orange-bordered emergency note
    ec.faq          accordion, first answer open
    ec.contactcards phone / email / address / hours
    ec.form         contact or booking form on a raised card
    ec.map          the map pin — this business has a real street address
    ec.cta          closing band
    ec.pagehero     inner page header
    ec.footer       deep navy, four columns
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

NAVY = "primary"        # #0A2E5C
BLUE = "secondary"      # #12559E
ORANGE = "accent"       # #D4540B — button fills
ORG_HI = "ecorg01"      # #F26A1B — icons, rules, on navy
ORG_TXT = "ecorg02"     # #B8470A — orange as text on white
TINT = "ecblu01"        # #E8F0FA
DEEP = "ecblu02"        # #06203F

EC_PAD = dims(88, 0, 88, 0)
EC_PAD_T = dims(64, 24, 64, 24)
EC_PAD_M = dims(48, 18, 48, 18)
R_CARD = box(10)
R_BTN = box(6)
GUTTER = 24

# Depth. These are the same shape as blocks.py's CARD_SHADOW, restated here
# so the values are visible next to the design decision rather than imported
# as a mystery.
SHADOW = {
    "box_shadow_box_shadow_type": "yes",
    "box_shadow_box_shadow": {"horizontal": 0, "vertical": 8, "blur": 24,
                              "spread": -8, "color": "rgba(10, 46, 92, 0.12)"},
}
SHADOW_HOVER = {
    "box_shadow_hover_box_shadow_type": "yes",
    "box_shadow_hover_box_shadow": {"horizontal": 0, "vertical": 18,
                                    "blur": 44, "spread": -12,
                                    "color": "rgba(10, 46, 92, 0.22)"},
}
SHADOW_LIFTED = {
    "box_shadow_box_shadow_type": "yes",
    "box_shadow_box_shadow": {"horizontal": 0, "vertical": 24, "blur": 60,
                              "spread": -16, "color": "rgba(10, 46, 92, 0.26)"},
}


# ─────────────────────────────── helpers ───────────────────────────────────

def _sec(children, bg="white", pad=None, anchor=None, extra=None):
    grounds = {"white": C["white"], "pale": C["surface"], "navy": NAVY,
               "deep": DEEP, "tint": TINT}
    s = {
        "content_width": "boxed",
        "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "flex_gap": gap(28),
        "padding": pad or EC_PAD,
        "padding_tablet": EC_PAD_T,
        "padding_mobile": EC_PAD_M,
        "background_background": "classic",
    }
    if anchor:
        s["_element_id"] = anchor
    if extra:
        s.update(extra)
    return container(children, s, globals_={
        "background_color": color_ref(grounds.get(bg, C["white"]))})


def _dark(bg):
    return bg in ("navy", "deep")


def _card(kids, width=None, pad=None, tone=None, hover=True, lifted=False,
          extra=None):
    """White card with a resting shadow that deepens on hover.

    The hover state is the cheap half of what makes a grid feel built rather
    than laid out, and it costs two controls.
    """
    s = {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(10),
        "padding": pad or dims(26, 24, 28, 24),
        "padding_mobile": dims(20, 18, 22, 18),
        "border_radius": R_CARD,
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
    }
    s.update(SHADOW_LIFTED if lifted else SHADOW)
    if hover:
        s.update(SHADOW_HOVER)
    if width:
        s.update({"width": slider(width, "%"), "width_mobile": slider(100, "%")})
    if extra:
        s.update(extra)
    return container(kids, s, globals_={
        "background_color": color_ref(tone or C["white"]),
        "border_color": color_ref(C["border"])})


def _h(text, size="h2", token=None, align="left", on_dark=False, tone=None):
    return widget("heading", {
        "title": text, "header_size": size, "align": align,
        "__typography__": typo_ref(token or T["h_medium"]),
    }, globals_={"title_color": color_ref(
        tone or (C["white"] if on_dark else NAVY))})


def _rule(width=48, tone=None, align="left"):
    """The short orange rule that sits under every eyebrow."""
    bar = container([], {
        "content_width": "full", "min_height": slider(3),
        "width": slider(width), "_flex_shrink": "0",
        "border_radius": box(2),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(tone or ORG_HI)})
    return container([bar], {
        "content_width": "full", "flex_direction": "column",
        "flex_align_items": "center" if align == "center" else "flex-start"})


def _eyebrow(text, align="left", on_dark=False, rule=True):
    lab = widget("heading", {
        "title": text, "header_size": "div", "align": align,
        "__typography__": typo_ref(T["eyebrow"]),
    }, globals_={"title_color": color_ref(ORG_HI if on_dark else ORG_TXT)})
    if not rule:
        return lab
    return container([lab, _rule(48, align=align)], {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(9),
        "flex_align_items": "center" if align == "center" else "flex-start"})


def _btn(label, href, style="orange", icon_name=None):
    """Four buttons, each with depth and a hover state.

        orange  #D4540B fill, white label (4.14:1) — the primary
        blue    navy fill, white label — the secondary, usually the phone
        ghost   white hairline on a dark ground or a photograph
        outline navy hairline on light grounds — tertiary, View Details
    """
    b = _button(label, href, "primary", icon_name or "")
    b["settings"].update({
        "border_radius": R_BTN,
        "text_padding": dims(15, 30, 15, 30),
        "__typography__": typo_ref(T["meta"]),
        "hover_animation": "float",
        "button_box_shadow_box_shadow_type": "yes",
        "button_box_shadow_box_shadow": {
            "horizontal": 0, "vertical": 6, "blur": 18, "spread": -6,
            "color": "rgba(10, 46, 92, 0.30)"},
    })
    g = b["settings"].setdefault("__globals__", {})
    if style == "blue":
        g.update({"background_color": color_ref(NAVY),
                  "border_color": color_ref(NAVY),
                  "button_text_color": color_ref(C["white"]),
                  "button_background_hover_color": color_ref(BLUE),
                  "button_hover_border_color": color_ref(BLUE),
                  "hover_color": color_ref(C["white"])})
    elif style == "ghost":
        b["settings"].update({"border_border": "solid", "border_width": box(2)})
        g.update({"background_color": color_ref(C["transparent"]),
                  "border_color": color_ref(C["white"]),
                  "button_text_color": color_ref(C["white"]),
                  "button_background_hover_color": color_ref(C["white"]),
                  "button_hover_border_color": color_ref(C["white"]),
                  "hover_color": color_ref(NAVY)})
    elif style == "outline":
        b["settings"].update({"border_border": "solid", "border_width": box(1),
                              "text_padding": dims(11, 20, 11, 20)})
        g.update({"background_color": color_ref(C["transparent"]),
                  "border_color": color_ref(C["border"]),
                  "button_text_color": color_ref(NAVY),
                  "button_background_hover_color": color_ref(NAVY),
                  "button_hover_border_color": color_ref(NAVY),
                  "hover_color": color_ref(C["white"])})
    else:
        g.update({"background_color": color_ref(ORANGE),
                  "border_color": color_ref(ORANGE),
                  "button_text_color": color_ref(C["white"]),
                  "button_background_hover_color": color_ref(NAVY),
                  "button_hover_border_color": color_ref(NAVY),
                  "hover_color": color_ref(C["white"])})
    return b


def _ticks(items, on_dark=False, columns=1, container_px=KIT_CONTAINER):
    rows = []
    for t in items:
        mark = widget("icon", {
            "selected_icon": icon("fas fa-circle-check"), "size": slider(14),
            "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref(ORG_HI if on_dark else ORANGE)})
        rows.append(_row([mark, _text(t, "left", on_dark=on_dark, small=True)],
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


def _shot(image, height=260, radius=R_CARD):
    if image and image.get("url"):
        return widget("image", {
            "image": media(image["url"], image.get("alt", "")),
            "image_size": "full", "width": slider(100, "%"),
            "height": slider(height), "object-fit": "cover",
            "align": "center", "image_border_radius": radius})
    return container([], {
        "content_width": "full", "min_height": slider(height),
        "border_radius": radius, "border_border": "dashed",
        "border_width": box(1), "background_background": "classic",
    }, globals_={"background_color": color_ref(TINT),
                 "border_color": color_ref(C["border"])})


def _disc(icon_name, size=52, tone=None, on_dark=False):
    return container([widget("icon", {
        "selected_icon": icon(icon_name), "size": slider(round(size * 0.42)),
        "align": "center", "view": "default",
    }, globals_={"primary_color": color_ref(C["white"])})], {
        "content_width": "full", "flex_direction": "column",
        "flex_justify_content": "center", "flex_align_items": "center",
        "width": slider(size), "min_height": slider(size), "_flex_shrink": "0",
        "border_radius": box(999), "background_background": "classic",
    }, globals_={"background_color": color_ref(tone or ORANGE)})


def _head_stack(props, align="center", on_dark=False):
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], align, on_dark))
    if props.get("title"):
        kids.append(_h(props["title"], props.get("tag", "h2"),
                       T["h_medium"], align, on_dark))
    if props.get("intro"):
        kids.append(container([_text(props["intro"], align, on_dark=on_dark)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(props.get("intro_width", 72), "%"),
            "width_mobile": slider(100, "%"),
            "margin": (dims(0, "auto", 0, "auto") if align == "center"
                       else dims(0, 0, 0, 0))}))
    if not kids:
        return []
    return [container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(12),
        "flex_align_items": "center" if align == "center" else "flex-start"})]


def _form_widget(f, compact=False):
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
    return widget("form", {
        "form_name": f.get("form_name", "Enquiry"),
        "form_fields": fields,
        "submit_actions": ["email"],
        "email_to": f.get("email", ""),
        "email_subject": f.get("subject", "New website enquiry"),
        "button_text": f.get("submit", "Send"),
        "button_size": "md", "input_size": "md",
        "button_width": "25" if compact else "100",
        "show_labels": "" if compact else "yes",
        "mark_required": "" if compact else "yes",
        "row_gap": slider(10 if compact else 14), "column_gap": slider(10),
        "success_message": f.get("success", ""),
        "field_border_radius": box(6), "field_border_width": box(1),
        "button_border_radius": R_BTN,
    }, globals_={
        "button_background_color": color_ref(ORANGE),
        "button_text_color": color_ref(C["white"]),
        "button_background_hover_color": color_ref(NAVY),
        "button_hover_color": color_ref(C["white"]),
        "field_background_color": color_ref(C["white"]),
        "field_text_color": color_ref(C["ink_primary"]),
        "field_border_color": color_ref(C["border"]),
        "label_color": color_ref(NAVY),
        "mark_required_color": color_ref(ORANGE),
    })


# ─────────────────────────────── chrome ────────────────────────────────────

@block("ec.topbar")
def ec_topbar(props):
    items = []
    for it in props.get("items", []):
        kids = []
        if it.get("icon"):
            kids.append(widget("icon", {
                "selected_icon": icon(it["icon"]), "size": slider(12),
                "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref(ORG_HI)}))
        lab = widget("heading", {
            "title": it.get("label", ""), "header_size": "div", "align": "left",
            "__typography__": typo_ref(T["meta"]),
        }, globals_={"title_color": color_ref(C["white"])})
        if it.get("href"):
            lab["settings"]["link"] = link(it["href"])
        kids.append(lab)
        items.append(_row(kids, 8, align="center",
                          extra={"flex_wrap": "nowrap",
                                 "flex_direction_mobile": "row"}))
    return container([_row(items, 26, align="center", justify="center",
                           extra={"flex_wrap": "wrap"})], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "padding": dims(9, 0, 9, 0),
        "padding_mobile": dims(8, 14, 8, 14),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(DEEP)})


@block("ec.header")
def ec_header(props):
    if props.get("logo"):
        brand = widget("theme-site-logo", {
            "align": "left", "image_size": "full",
            "width": slider(props.get("logo_width", 190)),
            "image": media(props["logo"], props.get("business", ""))})
    else:
        brand = container([
            widget("heading", {
                "title": props.get("business", "Economy Roofing"),
                "header_size": "div", "align": "left",
                "link": link("/"),
                "__typography__": typo_ref(T["wordmark"]),
            }, globals_={"title_color": color_ref(NAVY)}),
            widget("heading", {
                "title": props.get("tagline", ""), "header_size": "div",
                "align": "left", "__typography__": typo_ref(T["eyebrow"]),
            }, globals_={"title_color": color_ref(ORG_TXT)}),
        ], {"content_width": "full", "flex_direction": "column",
            "flex_gap": gap(2)})

    nav = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"),
        "layout": "horizontal", "align_items": "center",
        "pointer": "underline", "animation_line": "fade",
        "menu_space_between": slider(props.get("nav_gap", 24)),
        "toggle_align": "right",
        "__typography__": typo_ref(T["meta"]),
    }, globals_={
        "color_menu_item": color_ref(NAVY),
        "color_menu_item_hover": color_ref(ORG_TXT),
        "color_menu_item_active": color_ref(ORG_TXT),
        "pointer_color_menu_item_hover": color_ref(ORANGE),
        "pointer_color_menu_item_active": color_ref(ORANGE),
        "toggle_color": color_ref(NAVY),
    })

    actions = []
    if props.get("phone_display"):
        actions.append(_btn(props["phone_display"],
                            "tel:+1" + props.get("phone", ""), "blue",
                            "fas fa-phone"))
    if props.get("cta_label"):
        actions.append(_btn(props["cta_label"],
                            props.get("cta_url", "/book-an-appointment/"),
                            "orange"))

    row = _row([
        _col([brand], 26, extra={"flex_justify_content": "center"}),
        _col([nav], 44, extra={"flex_justify_content": "center",
                               "flex_align_items": "center"}),
        _col([_row(actions, 10, align="center", justify="flex-end",
                   extra={"flex_wrap": "wrap"})], 26,
             extra={"flex_justify_content": "center",
                    "flex_align_items": "flex-end"}),
    ], GUTTER, align="center",
        extra={"flex_wrap": "nowrap", "flex_wrap_tablet": "wrap"})

    return container([row], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "padding": dims(14, 0, 14, 0),
        "padding_mobile": dims(12, 14, 12, 14),
        "background_background": "classic",
        "sticky": "top", "sticky_on": ["desktop", "tablet", "mobile"],
        "sticky_offset": 0,
        **SHADOW,
    }, globals_={"background_color": color_ref(C["white"])})


@block("ec.footer")
def ec_footer(props):
    brand = []
    if props.get("logo"):
        brand.append(widget("image", {
            "image": media(props["logo"], props.get("business", "Logo")),
            "image_size": "full", "width": slider(200), "align": "left"}))
    else:
        brand.append(widget("heading", {
            "title": props.get("business", ""), "header_size": "div",
            "align": "left", "__typography__": typo_ref(T["wordmark"]),
        }, globals_={"title_color": color_ref(C["white"])}))
    if props.get("blurb"):
        brand.append(_text(props["blurb"], "left", on_dark=True, small=True))
    if props.get("socials"):
        brand.append(_row([widget("icon", {
            "selected_icon": icon(s.get("icon", "fab fa-facebook-f")),
            "size": slider(15), "align": "center", "view": "default",
            "link": link(s.get("url", "#")),
        }, globals_={"primary_color": color_ref(ORG_HI)})
            for s in props["socials"]], 16, align="center",
            extra={"flex_wrap": "wrap", "flex_direction_mobile": "row"}))

    cols = props.get("columns", [])
    widths = _tracks([1.4] + [1] * len(cols), GUTTER)
    body = [_col(brand, widths[0], extra={"flex_gap": gap(14)})]
    for i, c in enumerate(cols):
        kids = [widget("heading", {
            "title": c.get("title", ""), "header_size": "div", "align": "left",
            "__typography__": typo_ref(T["eyebrow"]),
        }, globals_={"title_color": color_ref(ORG_HI)})]
        for l in c.get("links", []):
            r = []
            if l.get("icon"):
                r.append(widget("icon", {
                    "selected_icon": icon(l["icon"]), "size": slider(12),
                    "align": "center", "view": "default",
                }, globals_={"primary_color": color_ref(ORG_HI)}))
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

    rule = container([], {
        "content_width": "full", "min_height": slider(1),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(BLUE)})

    return container([
        _row(body, GUTTER, align="flex-start", extra={"flex_wrap": "wrap"}),
        rule,
        widget("heading", {
            "title": props.get("copyright", ""), "header_size": "div",
            "align": "center", "__typography__": typo_ref(T["body_small"]),
        }, globals_={"title_color": color_ref(C["on_dark"])}),
    ], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column", "flex_gap": gap(26),
        "padding": dims(68, 0, 30, 0),
        "padding_mobile": dims(48, 18, 26, 18),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(DEEP)})


# ─────────────────────────────── sections ──────────────────────────────────

@block("ec.hero")
def ec_hero(props):
    """Photo under a navy scrim. The bottom padding is deliberately deep:
    the booking bar overlaps up into it."""
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], "left", on_dark=True))
    if props.get("title"):
        kids.append(_h(props["title"], props.get("tag", "h1"), T["hero"],
                       "left", on_dark=True))
    if props.get("intro"):
        kids.append(container([_text(props["intro"], "left", on_dark=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(92, "%"), "width_mobile": slider(100, "%")}))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"),
                         "orange"))
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props.get("alt_url", "#"),
                         "ghost", "fas fa-phone"))
    if btns:
        kids.append(_row(btns, 12, align="center",
                         extra={"flex_wrap": "wrap",
                                "flex_direction_mobile": "column",
                                "padding": dims(8, 0, 0, 0)}))

    col = _col(kids, props.get("width", 62), extra={"flex_gap": gap(18)})
    sec = _sec([_row([col], GUTTER, align="center")], "navy",
               pad=dims(props.get("pad_top", 104), 0,
                        props.get("pad_bottom", 150), 0),
               anchor=props.get("anchor"),
               extra={"min_height": slider(props.get("height", 560))})
    img = props.get("image")
    if img and img.get("url"):
        sec["settings"].update({
            "background_image": media(img["url"], img.get("alt", "")),
            "background_position": props.get("position", "center center"),
            "background_size": "cover", "background_repeat": "no-repeat",
            "background_overlay_background": "classic",
            "background_overlay_opacity": slider(props.get("overlay", 0.72)),
        })
        sec["settings"].setdefault("__globals__", {})[
            "background_overlay_color"] = color_ref(NAVY)
    return sec


@block("ec.bookingbar")
def ec_bookingbar(props):
    """The booking strip, pulled UP into the hero on a negative margin.

    The client's own idea, and a good one: the first thing a visitor can do
    is book an inspection, without scrolling or hunting for a contact page.
    """
    f = dict(props.get("form", {}))
    head = []
    if props.get("title"):
        head.append(_h(props["title"], "h2", T["h_small"], "left"))
    if props.get("note"):
        head.append(_text(props["note"], "left", small=True))
    card = _card(head + [_form_widget(f, compact=True)],
                 pad=dims(26, 28, 24, 28), lifted=True, hover=False,
                 extra={"margin": dims(props.get("pull", -92), 0, 0, 0),
                        "margin_mobile": dims(-56, 0, 0, 0)})
    return _sec([card], props.get("bg", "white"),
                pad=dims(0, 0, 54, 0), anchor=props.get("anchor", "book"))


@block("ec.trust")
def ec_trust(props):
    cols = props.get("columns", 4)
    w = _tracks([1] * cols, GUTTER)[0]
    cells = []
    for it in props.get("items", []):
        cells.append(_card([
            _row([
                _disc(it.get("icon", "fas fa-circle-check"), 44),
                widget("heading", {
                    "title": it.get("label", ""), "header_size": "div",
                    "align": "left",
                    "__typography__": typo_ref(T["h_small"]),
                }, globals_={"title_color": color_ref(NAVY)}),
            ], 12, align="center",
                extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"}),
        ], w, pad=dims(18, 18, 18, 18)))
    return _sec([_row(cells, GUTTER, align="stretch",
                      extra={"flex_wrap": "wrap"})],
                props.get("bg", "white"), pad=dims(0, 0, 70, 0),
                anchor=props.get("anchor"))


@block("ec.sectionhead")
def ec_sectionhead(props):
    on_dark = _dark(props.get("bg", "white"))
    kids = _head_stack(props, props.get("align", "center"), on_dark)
    for p in props.get("paragraphs", []):
        kids.append(container([_text(p, props.get("align", "center"),
                                     on_dark=on_dark)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(props.get("width", 76), "%"),
            "width_mobile": slider(100, "%"),
            "margin": (dims(0, "auto", 0, "auto")
                       if props.get("align", "center") == "center"
                       else dims(0, 0, 0, 0))}))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"),
                extra=({"flex_align_items": "center"}
                       if props.get("align", "center") == "center" else None))


@block("ec.about")
def ec_about(props):
    on_dark = _dark(props.get("bg", "white"))
    copy = []
    if props.get("eyebrow"):
        copy.append(_eyebrow(props["eyebrow"], "left", on_dark))
    if props.get("title"):
        copy.append(_h(props["title"], "h2", T["h_medium"], "left", on_dark))
    for p in props.get("paragraphs", []):
        copy.append(_text(p, "left", on_dark=on_dark))

    highs = []
    hw = _tracks([1, 1], 16, container=KIT_CONTAINER * 0.52)[0]
    for it in props.get("highlights", []):
        highs.append(_card([
            widget("icon", {
                "selected_icon": icon(it.get("icon", "fas fa-check")),
                "size": slider(17), "align": "left", "view": "default",
            }, globals_={"primary_color": color_ref(ORANGE)}),
            widget("heading", {
                "title": it.get("title", ""), "header_size": "h3",
                "align": "left", "__typography__": typo_ref(T["h_small"]),
            }, globals_={"title_color": color_ref(NAVY)}),
            _text(it.get("text", ""), "left", small=True),
        ], hw, pad=dims(18, 18, 20, 18), tone=TINT))
    if highs:
        copy.append(_row(highs, 16, align="stretch",
                         extra={"flex_wrap": "wrap",
                                "padding": dims(6, 0, 0, 0)}))
    if props.get("cta_label"):
        copy.append(container([
            _btn(props["cta_label"], props.get("cta_url", "#"), "orange")], {
            "content_width": "full", "flex_direction": "column",
            "flex_align_items": "flex-start", "padding": dims(8, 0, 0, 0)}))

    shot = _shot(props.get("image"), props.get("image_height", 520))
    w = _tracks([1, 1.15], GUTTER + 16)
    pair = [_col([shot], w[0]), _col(copy, w[1], extra={"flex_gap": gap(14)})]
    if props.get("flip"):
        pair.reverse()
    return _sec([_row(pair, GUTTER + 16, align="center",
                      extra={"flex_wrap": "wrap"})],
                props.get("bg", "white"), anchor=props.get("anchor"))


@block("ec.services")
def ec_services(props):
    on_dark = _dark(props.get("bg", "pale"))
    kids = _head_stack(props, "center", on_dark)
    cols = props.get("columns", 3)
    w = _tracks([1] * cols, GUTTER)[0]
    cards = []
    for it in props.get("items", []):
        body = [_shot(it.get("image"), props.get("thumb_height", 190))]
        if it.get("label"):
            body.append(widget("heading", {
                "title": it["label"], "header_size": "div", "align": "left",
                "__typography__": typo_ref(T["eyebrow"]),
            }, globals_={"title_color": color_ref(ORG_TXT)}))
        body.append(_h(it.get("title", ""), "h3", T["h_small"], "left"))
        if it.get("text"):
            body.append(_text(it["text"], "left", small=True))
        if it.get("href"):
            body.append(container([
                _btn(props.get("action_label", "View Details"), it["href"],
                     "outline")], {
                "content_width": "full", "flex_direction": "column",
                "flex_align_items": "flex-start",
                "padding": dims(6, 0, 0, 0)}))
        cards.append(_card(body, w, pad=dims(14, 14, 22, 14)))
    kids.append(_row(cards, GUTTER, align="stretch",
                     extra={"flex_wrap": "wrap"}))
    if props.get("cta_label"):
        kids.append(container([
            _btn(props["cta_label"], props.get("cta_url", "/services/"),
                 "orange")], {
            "content_width": "full", "flex_direction": "column",
            "flex_align_items": "center", "padding": dims(10, 0, 0, 0)}))
    return _sec(kids, props.get("bg", "pale"), anchor=props.get("anchor"))


@block("ec.testimonials")
def ec_testimonials(props):
    on_dark = _dark(props.get("bg", "white"))
    kids = _head_stack(props, "center", on_dark)
    cols = props.get("columns", 3)
    w = _tracks([1] * cols, GUTTER)[0]
    cards = []
    for it in props.get("items", []):
        stars = widget("star-rating", {
            "rating": it.get("rating", 5), "rating_scale": "5",
            "star_style": "star_fontawesome", "align": "left",
            "unmarked_star_style": "solid", "icon_size": slider(14),
        }, globals_={"stars_color": color_ref(ORG_HI),
                     "stars_unmarked_color": color_ref(C["border"])})
        cards.append(_card([
            stars,
            _text(it.get("text", ""), "left", small=True),
            widget("heading", {
                "title": it.get("name", ""), "header_size": "div",
                "align": "left", "__typography__": typo_ref(T["meta"]),
            }, globals_={"title_color": color_ref(ORG_TXT)}),
        ], w, pad=dims(24, 22, 24, 22)))
    kids.append(_row(cards, GUTTER, align="stretch",
                     extra={"flex_wrap": "wrap"}))
    if props.get("note"):
        kids.append(_text(props["note"], "center", on_dark=on_dark, small=True))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("ec.why")
def ec_why(props):
    on_dark = _dark(props.get("bg", "pale"))
    kids = _head_stack(props, "center", on_dark)
    cols = props.get("columns", 3)
    w = _tracks([1] * cols, GUTTER)[0]
    cards = []
    for i, it in enumerate(props.get("items", [])):
        cards.append(_card([
            _disc(it.get("icon", "fas fa-shield-halved"), 52),
            _h(it.get("title", ""), "h3", T["h_small"], "left"),
            _text(it.get("text", ""), "left", small=True),
        ], w, extra={"flex_gap": gap(12)}))
    kids.append(_row(cards, GUTTER, align="stretch",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "pale"), anchor=props.get("anchor"))


@block("ec.gallery")
def ec_gallery(props):
    """Deliberately uneven: the row ratios and the tile heights both vary, so
    it reads as a portfolio rather than a contact sheet."""
    on_dark = _dark(props.get("bg", "white"))
    kids = _head_stack(props, "center", on_dark)
    items = props.get("items", [])
    rows_spec = props.get("rows") or [[1.4, 1, 1], [1, 1.4], [1, 1, 1.4]]
    idx, out = 0, []
    while idx < len(items):
        ratios = rows_spec[len(out) % len(rows_spec)]
        w = _tracks(ratios, GUTTER)
        cells = []
        for j, ww in enumerate(w):
            if idx >= len(items):
                break
            it = items[idx]; idx += 1
            h = it.get("height", 300 if ratios[j] >= 1.3 else 240)
            body = [_shot(it.get("image"), h)]
            if it.get("caption"):
                body.append(widget("heading", {
                    "title": it["caption"], "header_size": "div",
                    "align": "left", "__typography__": typo_ref(T["eyebrow"]),
                }, globals_={"title_color": color_ref(
                    ORG_HI if on_dark else C["muted"])}))
            cells.append(_col(body, ww, extra={"flex_gap": gap(8)}))
        out.append(_row(cells, GUTTER, align="flex-start",
                        extra={"flex_wrap": "wrap"}))
    kids += out
    if props.get("note"):
        kids.append(_text(props["note"], "center", on_dark=on_dark, small=True))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("ec.steps")
def ec_steps(props):
    on_dark = _dark(props.get("bg", "navy"))
    kids = _head_stack(props, "center", on_dark)
    cols = props.get("columns", 4)
    w = _tracks([1] * cols, GUTTER)[0]
    cells = []
    for i, it in enumerate(props.get("items", []), 1):
        cells.append(_col([
            widget("heading", {
                "title": "%02d" % i, "header_size": "div", "align": "left",
                "__typography__": typo_ref(T["h_large"]),
            }, globals_={"title_color": color_ref(
                ORG_HI if on_dark else ORANGE)}),
            _rule(40, ORG_HI if on_dark else ORANGE),
            _h(it.get("title", ""), "h3", T["h_small"], "left", on_dark),
            _text(it.get("text", ""), "left", on_dark=on_dark, small=True),
        ], w, extra={"flex_gap": gap(10)}))
    kids.append(_row(cells, GUTTER, align="flex-start",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "navy"), anchor=props.get("anchor"))


@block("ec.prose")
def ec_prose(props):
    """The sub-service body. One layout serves all eighteen, which is what
    the client's copy document specifies."""
    kids = []
    if props.get("intro"):
        kids.append(container([_text(props["intro"], "left")], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(86, "%"), "width_mobile": slider(100, "%")}))
    blocks = props.get("blocks", [])
    w = _tracks([1, 1], GUTTER + 14)
    pair = []
    for i, b in enumerate(blocks[:2]):
        kids_b = [_h(b.get("title", ""), "h2", T["h_small"], "left")]
        kids_b.append(_ticks(b.get("items", []),
                             container_px=KIT_CONTAINER * 0.48))
        pair.append(_col([_card(kids_b, pad=dims(26, 24, 26, 24),
                                tone=TINT if i == 1 else None)], w[i]))
    if pair:
        kids.append(_row(pair, GUTTER + 14, align="stretch",
                         extra={"flex_wrap": "wrap"}))
    if props.get("why"):
        kids.append(_card([
            _eyebrow(props.get("why_label", "Why choose us"), "left"),
            _text(props["why"], "left"),
        ], pad=dims(22, 24, 22, 24), tone=TINT, hover=False))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("ec.related")
def ec_related(props):
    kids = _head_stack(props, "center")
    cols = max(1, len(props.get("items", [])))
    w = _tracks([1] * cols, GUTTER)[0]
    cards = []
    for it in props.get("items", []):
        cards.append(_card([
            _h(it.get("title", ""), "h3", T["h_small"], "left"),
            _text(it.get("text", ""), "left", small=True),
            container([_btn("View Details", it.get("href", "#"), "outline")], {
                "content_width": "full", "flex_direction": "column",
                "flex_align_items": "flex-start",
                "padding": dims(6, 0, 0, 0)}),
        ], w))
    kids.append(_row(cards, GUTTER, align="stretch",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "pale"), anchor=props.get("anchor"))


@block("ec.callout")
def ec_callout(props):
    """The emergency note. Orange-bordered so it does not read as body copy."""
    kids = []
    if props.get("title"):
        kids.append(_h(props["title"], "h3", T["h_small"], "left"))
    if props.get("text"):
        kids.append(_text(props["text"], "left"))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"),
                         "orange", "fas fa-phone"))
    row_kids = [_disc(props.get("icon", "fas fa-triangle-exclamation"), 54)]
    row_kids.append(container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(6)}))
    body = [_row(row_kids, 16, align="center",
                 extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})]
    if btns:
        body.append(container(btns, {
            "content_width": "full", "flex_direction": "column",
            "flex_align_items": "flex-start", "padding": dims(4, 0, 0, 0)}))
    card = _card(body, pad=dims(24, 26, 24, 26), hover=False,
                 extra={"border_width": dims(1, 1, 1, 5)})
    card["settings"].setdefault("__globals__", {})["border_color"] = color_ref(ORANGE)
    return _sec([card], props.get("bg", "white"),
                pad=dims(0, 0, 60, 0), anchor=props.get("anchor"))


@block("ec.faq")
def ec_faq(props):
    on_dark = _dark(props.get("bg", "white"))
    kids = _head_stack(props, "center", on_dark)
    kids.append(container([_faq(props.get("items", []), first_open=True)], {
        "content_width": "full", "flex_direction": "column",
        "width": slider(84, "%"), "width_mobile": slider(100, "%"),
        "margin": dims(0, "auto", 0, "auto")}))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("ec.contactcards")
def ec_contactcards(props):
    kids = _head_stack(props, "center")
    cols = props.get("columns", 4)
    w = _tracks([1] * cols, GUTTER)[0]
    cards = []
    for it in props.get("items", []):
        body = [_disc(it.get("icon", "fas fa-circle-info"), 50)]
        body.append(widget("heading", {
            "title": it.get("label", ""), "header_size": "div", "align": "left",
            "__typography__": typo_ref(T["eyebrow"]),
        }, globals_={"title_color": color_ref(ORG_TXT)}))
        val = widget("heading", {
            "title": it.get("value", ""), "header_size": "div", "align": "left",
            "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(NAVY)})
        if it.get("href"):
            val["settings"]["link"] = link(it["href"])
        body.append(val)
        if it.get("text"):
            body.append(_text(it["text"], "left", small=True))
        cards.append(_card(body, w))
    kids.append(_row(cards, GUTTER, align="stretch",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("ec.form")
def ec_form(props):
    on_dark = _dark(props.get("bg", "pale"))
    f = dict(props.get("form", {}))
    card_kids = []
    if props.get("title"):
        card_kids.append(_h(props["title"], "h2", T["h_medium"], "left"))
    if props.get("intro"):
        card_kids.append(_text(props["intro"], "left"))
    card_kids.append(_form_widget(f))
    card = _card(card_kids, pad=dims(34, 32, 36, 32), lifted=True, hover=False)

    side = props.get("side")
    if side:
        sk = []
        if side.get("eyebrow"):
            sk.append(_eyebrow(side["eyebrow"], "left", on_dark))
        if side.get("title"):
            sk.append(_h(side["title"], "h2", T["h_medium"], "left", on_dark))
        for p in side.get("paragraphs", []):
            sk.append(_text(p, "left", on_dark=on_dark))
        if side.get("ticks"):
            sk.append(_ticks(side["ticks"], on_dark,
                             container_px=KIT_CONTAINER * 0.45))
        w = _tracks([1, 1.2], GUTTER + 14)
        body = _row([_col(sk, w[0], extra={"flex_gap": gap(14)}),
                     _col([card], w[1])], GUTTER + 14,
                    align="flex-start", extra={"flex_wrap": "wrap"})
    else:
        body = container([card], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(props.get("outer_width", 74), "%"),
            "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")})
    return _sec([body], props.get("bg", "pale"),
                anchor=props.get("anchor", "enquire"))


@block("ec.map")
def ec_map(props):
    kids = _head_stack(props, "center")
    kids.append(widget("google_maps", {
        "address": props.get("address", ""),
        "zoom": slider(props.get("zoom", 14)),
        "height": slider(props.get("height", 420)),
    }))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("ec.cta")
def ec_cta(props):
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], "center", on_dark=True))
    if props.get("title"):
        kids.append(_h(props["title"], "h2", T["h_large"], "center",
                       on_dark=True))
    if props.get("text"):
        kids.append(container([_text(props["text"], "center", on_dark=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(66, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"),
                         "orange"))
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props.get("alt_url", "#"),
                         "ghost", "fas fa-phone"))
    if btns:
        kids.append(_row(btns, 12, align="center", justify="center",
                         extra={"flex_wrap": "wrap",
                                "flex_direction_mobile": "column",
                                "padding": dims(8, 0, 0, 0)}))
    if props.get("footnote"):
        kids.append(_text(props["footnote"], "center", on_dark=True,
                          small=True))
    sec = _sec(kids, "navy", pad=dims(84, 0, 84, 0),
               anchor=props.get("anchor"),
               extra={"flex_align_items": "center"})
    img = props.get("image")
    if img and img.get("url"):
        sec["settings"].update({
            "background_image": media(img["url"], img.get("alt", "")),
            "background_position": "center center", "background_size": "cover",
            "background_repeat": "no-repeat",
            "background_overlay_background": "classic",
            "background_overlay_opacity": slider(props.get("overlay", 0.82)),
        })
        sec["settings"].setdefault("__globals__", {})[
            "background_overlay_color"] = color_ref(NAVY)
    return sec


@block("ec.pagehero")
def ec_pagehero(props):
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], "center", on_dark=True))
    if props.get("title"):
        kids.append(_h(props["title"], props.get("tag", "h1"), T["h_large"],
                       "center", on_dark=True))
    if props.get("intro"):
        kids.append(container([_text(props["intro"], "center", on_dark=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(70, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    sec = _sec(kids, "navy", pad=dims(76, 0, 80, 0),
               anchor=props.get("anchor"),
               extra={"flex_align_items": "center"})
    img = props.get("image")
    if img and img.get("url"):
        sec["settings"].update({
            "background_image": media(img["url"], img.get("alt", "")),
            "background_position": "center center", "background_size": "cover",
            "background_repeat": "no-repeat",
            "background_overlay_background": "classic",
            "background_overlay_opacity": slider(props.get("overlay", 0.78)),
        })
        sec["settings"].setdefault("__globals__", {})[
            "background_overlay_color"] = color_ref(NAVY)
    return sec
