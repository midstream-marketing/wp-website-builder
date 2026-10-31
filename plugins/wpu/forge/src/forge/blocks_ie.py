"""
blocks_ie.py — I&E Homebuilders LLC, Concord NC.

No design reference, no live site and no reachable Facebook page. The two
client inputs are the whole brief: a 13-page copy document that enumerates
every section of every page, and the logo. So THE LOGO SPECIFIES THE DESIGN.

What the logo actually says, read literally:

    1. The mark is a building — a tall navy slab with three gold bars
       stepping up to its right. Those stepped bars become the repeating
       section-head motif, in place of the single plain rule every recent
       kit has used. That is `_stepped()`, and it is the signature here.
    2. The wordmark is a SERIF, so the headings are a serif.
    3. Navy and gold, and nothing else.

THE CONTRAST ARITHMETIC DECIDES THE BUTTONS. White on the logo's gold
#D9A934 is 2.17:1 — it fails outright, and a gold button with a white label
is the obvious thing to build. Navy on that same gold is 8.18:1. So:

    #D9A934   gold fill, NAVY label                  8.18:1  ✓
    #96710C   gold used as TEXT on white             4.50:1  ✓
    #D9A934   gold as text on navy                   8.18:1  ✓
    #0A1733   navy fill, white label                17.75:1  ✓

Depth is deliberate and carried forward from blocks_econ: every card has a
resting shadow and lifts on hover, every button has a shadow and a hover
state. The fidelity gate holds it there.

    ie.topbar       phone / email / service-area strip
    ie.header       logo, nav, phone, estimate CTA
    ie.hero         photo + navy scrim, room reserved for the trust strip
    ie.trust        four-item strip that OVERLAPS the hero
    ie.sectionhead  gold caps eyebrow over the stepped bars, then the heading
    ie.about        photo beside copy, with four value cards
    ie.services     six photo service cards
    ie.why          why-choose-us cards
    ie.steps        numbered process on the navy band
    ie.offer        the pale-gold seasonal offer band
    ie.prose        sub-service intro: copy beside a photograph
    ie.checklist    "What We Offer" — ticked list in columns
    ie.processlist  "Our Process" — compact numbered list
    ie.expect       numbered cards: What Happens Next / What to Expect
    ie.area         service-area band
    ie.related      three related service links
    ie.faq          accordion, first answer open
    ie.contactcards phone / WhatsApp / email / location / hours
    ie.form         contact or appointment form on a raised card
    ie.cta          closing band
    ie.pagehero     inner page header
    ie.footer       deep navy, four columns
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

NAVY = "primary"        # #0A1733
NAVY_MID = "secondary"  # #1C3160
GOLD = "accent"         # #D9A934 — fills, and gold text on dark
GOLD_TXT = "iegld01"    # #96710C — gold as text on white
GOLD_PALE = "iegld02"   # #F7EFD8 — the offer band
DEEP = "ienvy01"        # #050E2D — logo exact, footer
TINT = "ienvy02"        # #EDF1F8

IE_PAD = dims(92, 0, 92, 0)
IE_PAD_T = dims(66, 24, 66, 24)
IE_PAD_M = dims(50, 18, 50, 18)
R_CARD = box(8)
R_BTN = box(4)          # squarer than recent kits — the logo is rectangles
GUTTER = 24

SHADOW = {
    "box_shadow_box_shadow_type": "yes",
    "box_shadow_box_shadow": {"horizontal": 0, "vertical": 8, "blur": 24,
                              "spread": -8, "color": "rgba(10, 23, 51, 0.13)"},
}
SHADOW_HOVER = {
    "box_shadow_hover_box_shadow_type": "yes",
    "box_shadow_hover_box_shadow": {"horizontal": 0, "vertical": 18,
                                    "blur": 44, "spread": -12,
                                    "color": "rgba(10, 23, 51, 0.24)"},
}
SHADOW_LIFTED = {
    "box_shadow_box_shadow_type": "yes",
    "box_shadow_box_shadow": {"horizontal": 0, "vertical": 24, "blur": 60,
                              "spread": -16, "color": "rgba(10, 23, 51, 0.28)"},
}


# ───────────────────────── the signature motif ─────────────────────────────

def _stepped(align="left", on_dark=False, scale=1.0, tone=None):
    """The logo's three stepped gold bars, rebuilt from containers.

    In the mark the bars step UP to the right of the navy slab, each one
    wider than the last. Three bars at 16/30/48 px reads as the logo at
    eyebrow scale; `scale` opens it out for the dark bands.
    """
    widths = [round(w * scale) for w in (16, 30, 48)]
    bars = [container([], {
        "content_width": "full",
        "min_height": slider(round(3 * scale)),
        "width": slider(w),
        "_flex_shrink": "0",
        "background_background": "classic",
    }, globals_={"background_color": color_ref(
        tone or (GOLD if on_dark else GOLD))}) for w in widths]
    return container(bars, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(round(3 * scale)),
        "flex_align_items": "center" if align == "center" else "flex-start",
    })


# ───────────────────────────────── helpers ─────────────────────────────────

def _sec(children, bg="white", pad=None, anchor=None, extra=None):
    grounds = {"white": C["white"], "pale": C["surface"], "navy": NAVY,
               "deep": DEEP, "tint": TINT, "gold": GOLD_PALE}
    s = {
        "content_width": "boxed",
        "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "flex_gap": gap(30),
        "padding": pad or IE_PAD,
        "padding_tablet": IE_PAD_T,
        "padding_mobile": IE_PAD_M,
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
    """White card, hairline, resting shadow, lifts on hover."""
    s = {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(10),
        "padding": pad or dims(28, 26, 30, 26),
        "padding_mobile": dims(22, 18, 24, 18),
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
        "background_color": color_ref(tone or C["white"]),
        "border_color": color_ref(C["border"])})


def _h(text, size="h2", token=None, align="left", on_dark=False, tone=None):
    return widget("heading", {
        "title": text, "header_size": size, "align": align,
        "__typography__": typo_ref(token or T["h_medium"]),
    }, globals_={"title_color": color_ref(
        tone or (C["white"] if on_dark else NAVY))})


def _eyebrow(text, align="left", on_dark=False, rule=True):
    lab = widget("heading", {
        "title": text, "header_size": "div", "align": align,
        "__typography__": typo_ref(T["eyebrow"]),
    }, globals_={"title_color": color_ref(GOLD if on_dark else GOLD_TXT)})
    if not rule:
        return lab
    return container([lab, _stepped(align, on_dark)], {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(10),
        "flex_align_items": "center" if align == "center" else "flex-start"})


def _btn(label, href, style="gold", icon_name=None):
    """Four buttons.

        gold    #D9A934 fill, NAVY label — the primary. Navy and not white
                because white on this gold is 2.17:1 and illegible.
        navy    navy fill, white label — the secondary, usually the phone
        ghost   white hairline on a dark ground or a photograph
        outline hairline on light grounds — tertiary, Learn More
    """
    b = _button(label, href, "primary", icon_name or "")
    b["settings"].update({
        "border_radius": R_BTN,
        "text_padding": dims(16, 32, 16, 32),
        "__typography__": typo_ref(T["meta"]),
        "hover_animation": "float",
        "button_box_shadow_box_shadow_type": "yes",
        "button_box_shadow_box_shadow": {
            "horizontal": 0, "vertical": 6, "blur": 18, "spread": -6,
            "color": "rgba(10, 23, 51, 0.32)"},
    })
    g = b["settings"].setdefault("__globals__", {})
    if style == "navy":
        g.update({"background_color": color_ref(NAVY),
                  "border_color": color_ref(NAVY),
                  "button_text_color": color_ref(C["white"]),
                  "button_background_hover_color": color_ref(NAVY_MID),
                  "button_hover_border_color": color_ref(NAVY_MID),
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
                              "text_padding": dims(12, 22, 12, 22)})
        g.update({"background_color": color_ref(C["transparent"]),
                  "border_color": color_ref(C["border"]),
                  "button_text_color": color_ref(NAVY),
                  "button_background_hover_color": color_ref(NAVY),
                  "button_hover_border_color": color_ref(NAVY),
                  "hover_color": color_ref(C["white"])})
    else:
        # The primary. NAVY label on gold — see the module docstring.
        g.update({"background_color": color_ref(GOLD),
                  "border_color": color_ref(GOLD),
                  "button_text_color": color_ref(NAVY),
                  "button_background_hover_color": color_ref(NAVY),
                  "button_hover_border_color": color_ref(NAVY),
                  "hover_color": color_ref(C["white"])})
    return b


def _ticks(items, on_dark=False, columns=1, container_px=KIT_CONTAINER):
    rows = []
    for t in items:
        mark = widget("icon", {
            "selected_icon": icon("fas fa-check"), "size": slider(13),
            "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref(GOLD if on_dark else GOLD_TXT)})
        rows.append(_row([mark, _text(t, "left", on_dark=on_dark, small=True)],
                         12, align="flex-start",
                         extra={"flex_wrap": "nowrap",
                                "flex_direction_mobile": "row",
                                "padding": dims(6, 0, 6, 0)}))
    if columns == 1:
        return container(rows, {"content_width": "full",
                                "flex_direction": "column", "flex_gap": gap(2)})
    per = -(-len(rows) // columns)
    w = _tracks([1] * columns, 24, container=container_px)[0]
    cols = [_col(rows[i:i + per], w, extra={"flex_gap": gap(2)})
            for i in range(0, len(rows), per)]
    return _row(cols, 24, align="flex-start", extra={"flex_wrap": "wrap"})


def _shot(image, height=280, radius=R_CARD):
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


def _numeral(n, on_dark=False, size=None):
    return widget("heading", {
        "title": str(n), "header_size": "div", "align": "left",
        "__typography__": typo_ref(size or T["h_large"]),
    }, globals_={"title_color": color_ref(GOLD if on_dark else GOLD_TXT)})


def _disc(icon_name, size=54, tone=None):
    return container([widget("icon", {
        "selected_icon": icon(icon_name), "size": slider(round(size * 0.40)),
        "align": "center", "view": "default",
    }, globals_={"primary_color": color_ref(NAVY)})], {
        "content_width": "full", "flex_direction": "column",
        "flex_justify_content": "center", "flex_align_items": "center",
        "width": slider(size), "min_height": slider(size), "_flex_shrink": "0",
        "border_radius": box(4), "background_background": "classic",
    }, globals_={"background_color": color_ref(tone or GOLD)})


def _head_stack(props, align="center", on_dark=False):
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], align, on_dark))
    if props.get("title"):
        kids.append(_h(props["title"], props.get("tag", "h2"),
                       T["h_medium"], align, on_dark))
    if props.get("standfirst"):
        kids.append(widget("heading", {
            "title": props["standfirst"], "header_size": "div", "align": align,
            "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(
            GOLD if on_dark else GOLD_TXT)}))
    if props.get("intro"):
        kids.append(container([_text(props["intro"], align, on_dark=on_dark)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(props.get("intro_width", 74), "%"),
            "width_mobile": slider(100, "%"),
            "margin": (dims(0, "auto", 0, "auto") if align == "center"
                       else dims(0, 0, 0, 0))}))
    if not kids:
        return []
    return [container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(14),
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
        fields.append(repeater_item(**item))
    return widget("form", {
        "form_name": f.get("form_name", "Enquiry"),
        "form_fields": fields,
        "submit_actions": ["email"],
        "email_to": f.get("email", ""),
        "email_subject": f.get("subject", "New website enquiry"),
        "button_text": f.get("submit", "Send"),
        "button_size": "md", "input_size": "md",
        "button_width": "100",
        "show_labels": "yes", "mark_required": "yes",
        "row_gap": slider(14), "column_gap": slider(12),
        "success_message": f.get("success", ""),
        "field_border_radius": box(4), "field_border_width": box(1),
        "button_border_radius": R_BTN,
    }, globals_={
        # On a FORM widget `button_background_color` IS the correct control.
        # It is not on a Button widget, which is why _btn uses
        # `background_color` instead.
        "button_background_color": color_ref(GOLD),
        "button_text_color": color_ref(NAVY),
        "button_background_hover_color": color_ref(NAVY),
        "button_hover_color": color_ref(C["white"]),
        "field_background_color": color_ref(C["white"]),
        "field_text_color": color_ref(C["ink_primary"]),
        "field_border_color": color_ref(C["border"]),
        "label_color": color_ref(NAVY),
        "mark_required_color": color_ref(GOLD_TXT),
    })


# ─────────────────────────────── chrome ────────────────────────────────────

@block("ie.topbar")
def ie_topbar(props):
    items = []
    for it in props.get("items", []):
        kids = []
        if it.get("icon"):
            kids.append(widget("icon", {
                "selected_icon": icon(it["icon"]), "size": slider(12),
                "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref(GOLD)}))
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
    return container([_row(items, 28, align="center", justify="center",
                           extra={"flex_wrap": "wrap"})], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "padding": dims(10, 0, 10, 0),
        "padding_mobile": dims(9, 14, 9, 14),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(DEEP)})


@block("ie.header")
def ie_header(props):
    if props.get("logo"):
        brand = widget("theme-site-logo", {
            "align": "left", "image_size": "full",
            "width": slider(props.get("logo_width", 180)),
            "image": media(props["logo"], props.get("business", ""))})
    else:
        brand = container([
            widget("heading", {
                "title": props.get("business", "I&E Homebuilders"),
                "header_size": "div", "align": "left", "link": link("/"),
                "__typography__": typo_ref(T["wordmark"]),
            }, globals_={"title_color": color_ref(NAVY)}),
            widget("heading", {
                "title": props.get("tagline", ""), "header_size": "div",
                "align": "left", "__typography__": typo_ref(T["eyebrow"]),
            }, globals_={"title_color": color_ref(GOLD_TXT)}),
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
        "color_menu_item_hover": color_ref(GOLD_TXT),
        "color_menu_item_active": color_ref(GOLD_TXT),
        "pointer_color_menu_item_hover": color_ref(GOLD),
        "pointer_color_menu_item_active": color_ref(GOLD),
        "toggle_color": color_ref(NAVY),
    })

    actions = []
    if props.get("phone_display"):
        actions.append(_btn(props["phone_display"],
                            "tel:+1" + props.get("phone", ""), "navy",
                            "fas fa-phone"))
    if props.get("cta_label"):
        actions.append(_btn(props["cta_label"],
                            props.get("cta_url", "/contact-us/"), "gold"))

    row = _row([
        _col([brand], 24, extra={"flex_justify_content": "center"}),
        _col([nav], 44, extra={"flex_justify_content": "center",
                               "flex_align_items": "center"}),
        _col([_row(actions, 10, align="center", justify="flex-end",
                   extra={"flex_wrap": "wrap"})], 32,
             extra={"flex_justify_content": "center",
                    "flex_align_items": "flex-end"}),
    ], GUTTER, align="center",
        extra={"flex_wrap": "nowrap", "flex_wrap_tablet": "wrap"})

    return container([row], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "padding": dims(16, 0, 16, 0),
        "padding_mobile": dims(12, 14, 12, 14),
        "background_background": "classic",
        "sticky": "top", "sticky_on": ["desktop", "tablet", "mobile"],
        "sticky_offset": 0,
        **SHADOW,
    }, globals_={"background_color": color_ref(C["white"])})


@block("ie.footer")
def ie_footer(props):
    brand = []
    if props.get("logo"):
        brand.append(widget("image", {
            "image": media(props["logo"], props.get("business", "Logo")),
            "image_size": "full", "width": slider(190), "align": "left"}))
    else:
        brand.append(widget("heading", {
            "title": props.get("business", ""), "header_size": "div",
            "align": "left", "__typography__": typo_ref(T["wordmark"]),
        }, globals_={"title_color": color_ref(C["white"])}))
    if props.get("blurb"):
        brand.append(_text(props["blurb"], "left", on_dark=True, small=True))
    brand.append(_stepped("left", on_dark=True, scale=1.1))
    if props.get("socials"):
        brand.append(_row([widget("icon", {
            "selected_icon": icon(s.get("icon", "fab fa-facebook-f")),
            "size": slider(15), "align": "center", "view": "default",
            "link": link(s.get("url", "#")),
        }, globals_={"primary_color": color_ref(GOLD)})
            for s in props["socials"]], 16, align="center",
            extra={"flex_wrap": "wrap", "flex_direction_mobile": "row"}))

    cols = props.get("columns", [])
    widths = _tracks([1.5] + [1] * len(cols), GUTTER)
    body = [_col(brand, widths[0], extra={"flex_gap": gap(14)})]
    for i, c in enumerate(cols):
        kids = [widget("heading", {
            "title": c.get("title", ""), "header_size": "div", "align": "left",
            "__typography__": typo_ref(T["eyebrow"]),
        }, globals_={"title_color": color_ref(GOLD)})]
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

    rule = container([], {
        "content_width": "full", "min_height": slider(1),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(NAVY_MID)})

    return container([
        _row(body, GUTTER, align="flex-start", extra={"flex_wrap": "wrap"}),
        rule,
        widget("heading", {
            "title": props.get("copyright", ""), "header_size": "div",
            "align": "center", "__typography__": typo_ref(T["body_small"]),
        }, globals_={"title_color": color_ref(C["on_dark"])}),
    ], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column", "flex_gap": gap(28),
        "padding": dims(72, 0, 32, 0),
        "padding_mobile": dims(50, 18, 28, 18),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(DEEP)})


# ─────────────────────────────── sections ──────────────────────────────────

@block("ie.hero")
def ie_hero(props):
    """Photograph under a navy scrim. The bottom padding is deliberately
    deep: the trust strip overlaps up into it."""
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], "left", on_dark=True))
    if props.get("title"):
        kids.append(_h(props["title"], props.get("tag", "h1"), T["hero"],
                       "left", on_dark=True))
    if props.get("intro"):
        kids.append(container([_text(props["intro"], "left", on_dark=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(94, "%"), "width_mobile": slider(100, "%")}))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"), "gold"))
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props.get("alt_url", "#"),
                         "ghost", "fas fa-phone"))
    if props.get("third_label"):
        btns.append(_btn(props["third_label"], props.get("third_url", "#"),
                         "ghost"))
    if btns:
        kids.append(_row(btns, 12, align="center",
                         extra={"flex_wrap": "wrap",
                                "flex_direction_mobile": "column",
                                "padding": dims(10, 0, 0, 0)}))

    col = _col(kids, props.get("width", 64), extra={"flex_gap": gap(20)})
    sec = _sec([_row([col], GUTTER, align="center")], "navy",
               pad=dims(props.get("pad_top", 110), 0,
                        props.get("pad_bottom", 156), 0),
               anchor=props.get("anchor"),
               extra={"min_height": slider(props.get("height", 580))})
    img = props.get("image")
    if img and img.get("url"):
        sec["settings"].update({
            "background_image": media(img["url"], img.get("alt", "")),
            "background_position": props.get("position", "center center"),
            "background_size": "cover", "background_repeat": "no-repeat",
            "background_overlay_background": "classic",
            "background_overlay_opacity": slider(props.get("overlay", 0.74)),
        })
        sec["settings"].setdefault("__globals__", {})[
            "background_overlay_color"] = color_ref(NAVY)
    return sec


@block("ie.trust")
def ie_trust(props):
    """Four reassurance items, pulled UP into the hero on a negative margin.

    This overlap is why the generic heroes are banned in design-spec.json:
    neither reserves the space for it.
    """
    cols = props.get("columns", 4)
    w = _tracks([1] * cols, GUTTER)[0]
    cells = []
    for it in props.get("items", []):
        cells.append(_card([
            _row([
                _disc(it.get("icon", "fas fa-check"), 46),
                widget("heading", {
                    "title": it.get("label", ""), "header_size": "div",
                    "align": "left", "__typography__": typo_ref(T["h_small"]),
                }, globals_={"title_color": color_ref(NAVY)}),
            ], 13, align="center",
                extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"}),
        ], w, pad=dims(20, 20, 20, 20)))
    strip = _row(cells, GUTTER, align="stretch", extra={"flex_wrap": "wrap"})
    pull = props.get("pull")
    if pull:
        strip["settings"].update({"margin": dims(pull, 0, 0, 0),
                                  "margin_mobile": dims(-40, 0, 0, 0)})
    return _sec([strip], props.get("bg", "white"),
                pad=dims(0, 0, 74, 0), anchor=props.get("anchor"))


@block("ie.sectionhead")
def ie_sectionhead(props):
    on_dark = _dark(props.get("bg", "white"))
    align = props.get("align", "center")
    kids = _head_stack(props, align, on_dark)
    for p in props.get("paragraphs", []):
        kids.append(container([_text(p, align, on_dark=on_dark)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(props.get("width", 78), "%"),
            "width_mobile": slider(100, "%"),
            "margin": (dims(0, "auto", 0, "auto") if align == "center"
                       else dims(0, 0, 0, 0))}))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"),
                pad=props.get("pad") and dims(*props["pad"]) or None,
                extra=({"flex_align_items": "center"}
                       if align == "center" else None))


@block("ie.about")
def ie_about(props):
    on_dark = _dark(props.get("bg", "white"))
    left = _head_stack(props, "left", on_dark)
    for p in props.get("paragraphs", []):
        left.append(_text(p, "left", on_dark=on_dark))
    if props.get("ticks"):
        left.append(_ticks(props["ticks"], on_dark))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"), "gold"))
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props.get("alt_url", "#"),
                         "outline"))
    if btns:
        left.append(_row(btns, 12, align="center",
                         extra={"flex_wrap": "wrap",
                                "padding": dims(8, 0, 0, 0)}))

    wl, wr = _tracks([1.06, 1], GUTTER)
    flip = props.get("flip")
    body = [_col(left, wl, extra={"flex_gap": gap(16)}),
            _col([_shot(props.get("image"), props.get("image_height", 440))],
                 wr, extra={"flex_justify_content": "center"})]
    if flip:
        body.reverse()
    kids = [_row(body, GUTTER, align="center", extra={"flex_wrap": "wrap"})]

    cards = props.get("cards", [])
    if cards:
        w = _tracks([1] * min(len(cards), 4), GUTTER)[0]
        kids.append(_row([_card([
            _disc(c.get("icon", "fas fa-hammer"), 48),
            widget("heading", {
                "title": c.get("title", ""), "header_size": "h3",
                "align": "left", "__typography__": typo_ref(T["h_small"]),
            }, globals_={"title_color": color_ref(NAVY)}),
            _text(c.get("text", ""), "left", small=True),
        ], w, pad=dims(24, 22, 26, 22)) for c in cards], GUTTER,
            align="stretch", extra={"flex_wrap": "wrap",
                                    "padding": dims(14, 0, 0, 0)}))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("ie.services")
def ie_services(props):
    """Six photo-led service cards. Photographs and not icons: the client's
    own document calls premium kitchen and bath remodels the specialism, and
    that is bought on pictures of finished rooms."""
    kids = _head_stack(props, props.get("align", "center"),
                       _dark(props.get("bg", "white")))
    items = props.get("items", [])
    per = props.get("columns", 3)
    w = _tracks([1] * per, GUTTER)[0]
    cells = []
    for it in items:
        body = [_shot(it.get("image"), props.get("shot", 220))]
        if it.get("label"):
            body.append(widget("heading", {
                "title": it["label"], "header_size": "div", "align": "left",
                "__typography__": typo_ref(T["eyebrow"]),
            }, globals_={"title_color": color_ref(GOLD_TXT)}))
        body.append(widget("heading", {
            "title": it.get("title", ""), "header_size": "h3", "align": "left",
            "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(NAVY)}))
        if it.get("text"):
            body.append(_text(it["text"], "left", small=True))
        if it.get("url"):
            body.append(_btn(it.get("link_label", "Learn More"), it["url"],
                             "outline"))
        cells.append(_card(body, w, pad=dims(0, 0, 26, 0), extra={
            "flex_gap": gap(12), "overflow": "hidden"}))
    # The card has no side padding so the photo runs edge to edge; the text
    # below it gets its own inset instead.
    for c in cells:
        for ch in c["elements"][1:]:
            ch.setdefault("settings", {})
            ch["settings"]["_margin"] = dims(0, 24, 0, 24)
    kids.append(_row(cells, GUTTER, align="stretch",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("ie.why")
def ie_why(props):
    on_dark = _dark(props.get("bg", "white"))
    kids = _head_stack(props, props.get("align", "center"), on_dark)
    items = props.get("items", [])
    per = props.get("columns", 3)
    w = _tracks([1] * per, GUTTER)[0]
    cells = []
    for it in items:
        cells.append(_card([
            _disc(it.get("icon", "fas fa-award"), 50),
            widget("heading", {
                "title": it.get("title", ""), "header_size": "h3",
                "align": "left", "__typography__": typo_ref(T["h_small"]),
            }, globals_={"title_color": color_ref(NAVY)}),
            _text(it.get("text", ""), "left", small=True),
        ], w, pad=dims(26, 24, 28, 24)))
    kids.append(_row(cells, GUTTER, align="stretch",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("ie.steps")
def ie_steps(props):
    """The numbered process on the navy band, with the stepped-bar motif
    carried through at larger scale."""
    bg = props.get("bg", "navy")
    on_dark = _dark(bg)
    kids = _head_stack(props, props.get("align", "center"), on_dark)
    items = props.get("items", [])
    per = props.get("columns", min(len(items), 5)) or 1
    w = _tracks([1] * per, GUTTER)[0]
    cells = []
    for n, it in enumerate(items, 1):
        cells.append(_col([
            _numeral(it.get("n", n), on_dark),
            _stepped("left", on_dark, scale=0.8),
            widget("heading", {
                "title": it.get("title", ""), "header_size": "h3",
                "align": "left", "__typography__": typo_ref(T["h_small"]),
            }, globals_={"title_color": color_ref(
                C["white"] if on_dark else NAVY)}),
            _text(it.get("text", ""), "left", on_dark=on_dark, small=True),
        ], w, extra={"flex_gap": gap(10)}))
    kids.append(_row(cells, GUTTER, align="flex-start",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, bg, anchor=props.get("anchor"))


@block("ie.offer")
def ie_offer(props):
    """The seasonal offer band. The one place gold is a GROUND.

    Dated content by design - the README flags it as the block to retire
    after the holidays, so every string here is a prop.
    """
    left = []
    if props.get("eyebrow"):
        left.append(_eyebrow(props["eyebrow"], "left"))
    if props.get("title"):
        left.append(_h(props["title"], "h2", T["h_medium"], "left"))
    for p in props.get("paragraphs", []):
        left.append(_text(p, "left"))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"), "navy"))
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props.get("alt_url", "#"),
                         "outline"))
    if btns:
        left.append(_row(btns, 12, align="center",
                         extra={"flex_wrap": "wrap",
                                "padding": dims(8, 0, 0, 0)}))
    wl, wr = _tracks([1.25, 1], GUTTER)
    body = [_col(left, wl, extra={"flex_gap": gap(14)})]
    if props.get("image"):
        body.append(_col([_shot(props["image"],
                                props.get("image_height", 300))], wr))
    return _sec([_row(body, GUTTER, align="center",
                      extra={"flex_wrap": "wrap"})],
                "gold", pad=dims(62, 0, 62, 0), anchor=props.get("anchor"))


@block("ie.prose")
def ie_prose(props):
    """The sub-service intro: heading and two paragraphs beside a photo."""
    on_dark = _dark(props.get("bg", "white"))
    left = _head_stack(props, "left", on_dark)
    for p in props.get("paragraphs", []):
        left.append(_text(p, "left", on_dark=on_dark))
    wl, wr = _tracks([1.15, 1], GUTTER)
    body = [_col(left, wl, extra={"flex_gap": gap(16)})]
    if props.get("image"):
        body.append(_col([_shot(props["image"],
                                props.get("image_height", 380))], wr,
                         extra={"flex_justify_content": "center"}))
    if props.get("flip"):
        body.reverse()
    return _sec([_row(body, GUTTER, align="center",
                      extra={"flex_wrap": "wrap"})],
                props.get("bg", "white"), anchor=props.get("anchor"))


@block("ie.checklist")
def ie_checklist(props):
    """"What We Offer" — a ticked list, two columns, on a card."""
    on_dark = _dark(props.get("bg", "white"))
    kids = _head_stack(props, props.get("align", "left"), on_dark)
    inner = _ticks(props.get("items", []), on_dark,
                   columns=props.get("columns", 2),
                   container_px=KIT_CONTAINER - 60)
    kids.append(_card([inner], pad=dims(30, 32, 32, 32), hover=False))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("ie.processlist")
def ie_processlist(props):
    """"Our Process" — a compact numbered run, horizontal on desktop."""
    on_dark = _dark(props.get("bg", "white"))
    kids = _head_stack(props, props.get("align", "left"), on_dark)
    items = props.get("items", [])
    per = props.get("columns", min(len(items), 5)) or 1
    w = _tracks([1] * per, 18)[0]
    cells = []
    for n, it in enumerate(items, 1):
        label = it if isinstance(it, str) else it.get("title", "")
        cells.append(_card([
            widget("heading", {
                "title": "%02d" % n, "header_size": "div", "align": "left",
                "__typography__": typo_ref(T["h_small"]),
            }, globals_={"title_color": color_ref(GOLD_TXT)}),
            _text(label, "left", small=True),
        ], w, pad=dims(20, 18, 22, 18)))
    kids.append(_row(cells, 18, align="stretch", extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("ie.expect")
def ie_expect(props):
    """Numbered cards — What Happens Next, What to Expect at Your
    Appointment. A numbered card reads as a sequence where a bulleted list
    reads as a pile, and both of these ARE sequences."""
    on_dark = _dark(props.get("bg", "white"))
    kids = _head_stack(props, props.get("align", "center"), on_dark)
    items = props.get("items", [])
    per = props.get("columns", min(len(items), 4)) or 1
    w = _tracks([1] * per, GUTTER)[0]
    cells = []
    for n, it in enumerate(items, 1):
        body = [_numeral(n, False, T["h_small"]), _stepped("left", False, 0.7)]
        if isinstance(it, str):
            body.append(_text(it, "left", small=True))
        else:
            if it.get("title"):
                body.append(widget("heading", {
                    "title": it["title"], "header_size": "h3", "align": "left",
                    "__typography__": typo_ref(T["h_small"]),
                }, globals_={"title_color": color_ref(NAVY)}))
            if it.get("text"):
                body.append(_text(it["text"], "left", small=True))
        cells.append(_card(body, w, pad=dims(24, 22, 26, 22),
                           extra={"flex_gap": gap(9)}))
    kids.append(_row(cells, GUTTER, align="stretch",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("ie.area")
def ie_area(props):
    kids = [_eyebrow(props.get("eyebrow", "Service Area"), "center")]
    if props.get("title"):
        kids.append(_h(props["title"], "h2", T["h_medium"], "center"))
    for p in props.get("paragraphs", []):
        kids.append(container([_text(p, "center")], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(72, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    towns = props.get("towns", [])
    if towns:
        chips = [container([widget("heading", {
            "title": t, "header_size": "div", "align": "center",
            "__typography__": typo_ref(T["meta"]),
        }, globals_={"title_color": color_ref(NAVY)})], {
            "content_width": "full", "flex_direction": "column",
            "padding": dims(10, 20, 10, 20), "border_radius": box(4),
            "border_border": "solid", "border_width": box(1),
            "background_background": "classic", **SHADOW,
        }, globals_={"background_color": color_ref(C["white"]),
                     "border_color": color_ref(C["border"])}) for t in towns]
        kids.append(_row(chips, 12, align="center", justify="center",
                         extra={"flex_wrap": "wrap"}))
    if props.get("cta_label"):
        kids.append(_row([_btn(props["cta_label"],
                               props.get("cta_url", "#"), "gold")], 12,
                         align="center", justify="center",
                         extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "pale"), anchor=props.get("anchor"),
                extra={"flex_align_items": "center"})


@block("ie.related")
def ie_related(props):
    kids = _head_stack(props, "center", False)
    items = props.get("items", [])
    w = _tracks([1] * max(len(items), 1), GUTTER)[0]
    cells = []
    for it in items:
        cells.append(_card([
            _shot(it.get("image"), 150),
            widget("heading", {
                "title": it.get("title", ""), "header_size": "h3",
                "align": "left", "__typography__": typo_ref(T["h_small"]),
            }, globals_={"title_color": color_ref(NAVY)}),
            _btn(it.get("link_label", "View Service"), it.get("url", "#"),
                 "outline"),
        ], w, pad=dims(0, 0, 22, 0), extra={"flex_gap": gap(11),
                                            "overflow": "hidden"}))
    for c in cells:
        for ch in c["elements"][1:]:
            ch.setdefault("settings", {})
            ch["settings"]["_margin"] = dims(0, 22, 0, 22)
    kids.append(_row(cells, GUTTER, align="stretch",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "pale"), anchor=props.get("anchor"))


@block("ie.faq")
def ie_faq(props):
    kids = _head_stack(props, props.get("align", "center"), False)
    kids.append(_faq(props.get("items", [])))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("ie.contactcards")
def ie_contactcards(props):
    items = props.get("items", [])
    per = props.get("columns", min(len(items), 3)) or 1
    w = _tracks([1] * per, GUTTER)[0]
    cells = []
    for it in items:
        body = [_disc(it.get("icon", "fas fa-phone"), 52),
                widget("heading", {
                    "title": it.get("label", ""), "header_size": "div",
                    "align": "left", "__typography__": typo_ref(T["eyebrow"]),
                }, globals_={"title_color": color_ref(GOLD_TXT)})]
        val = widget("heading", {
            "title": it.get("value", ""), "header_size": "h3", "align": "left",
            "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(NAVY)})
        if it.get("href"):
            val["settings"]["link"] = link(it["href"])
        body.append(val)
        if it.get("note"):
            body.append(_text(it["note"], "left", small=True))
        cells.append(_card(body, w, pad=dims(26, 24, 28, 24)))
    return _sec([_row(cells, GUTTER, align="stretch",
                      extra={"flex_wrap": "wrap"})],
                props.get("bg", "white"), anchor=props.get("anchor"))


@block("ie.form")
def ie_form(props):
    on_dark = _dark(props.get("bg", "white"))
    head = _head_stack(props, "left", on_dark)
    f = dict(props.get("form", {}))
    card = _card(head + [_form_widget(f)], pad=dims(34, 34, 36, 34),
                 lifted=True, hover=False)
    side = props.get("side")
    if not side:
        return _sec([card], props.get("bg", "pale"),
                    anchor=props.get("anchor", "form"))
    skids = []
    if side.get("title"):
        skids.append(_h(side["title"], "h2", T["h_medium"], "left", on_dark))
    for p in side.get("paragraphs", []):
        skids.append(_text(p, "left", on_dark=on_dark))
    if side.get("ticks"):
        skids.append(_ticks(side["ticks"], on_dark))
    if side.get("image"):
        skids.append(_shot(side["image"], side.get("image_height", 260)))
    wl, wr = _tracks([1, 1.1], GUTTER)
    return _sec([_row([_col(skids, wl, extra={"flex_gap": gap(16)}),
                       _col([card], wr)], GUTTER, align="flex-start",
                      extra={"flex_wrap": "wrap"})],
                props.get("bg", "pale"), anchor=props.get("anchor", "form"))


@block("ie.cta")
def ie_cta(props):
    kids = [_stepped("center", on_dark=True, scale=1.3)]
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], "center", on_dark=True,
                             rule=False))
    if props.get("title"):
        kids.append(_h(props["title"], props.get("tag", "h2"), T["h_medium"],
                       "center", on_dark=True))
    if props.get("intro"):
        kids.append(container([_text(props["intro"], "center", on_dark=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(70, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"), "gold"))
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props.get("alt_url", "#"),
                         "ghost", "fas fa-phone"))
    if btns:
        kids.append(_row(btns, 12, align="center", justify="center",
                         extra={"flex_wrap": "wrap",
                                "flex_direction_mobile": "column",
                                "padding": dims(10, 0, 0, 0)}))
    sec = _sec(kids, props.get("bg", "navy"), pad=dims(84, 0, 84, 0),
               anchor=props.get("anchor"),
               extra={"flex_align_items": "center"})
    img = props.get("image")
    if img and img.get("url"):
        sec["settings"].update({
            "background_image": media(img["url"], img.get("alt", "")),
            "background_position": "center center",
            "background_size": "cover", "background_repeat": "no-repeat",
            "background_overlay_background": "classic",
            "background_overlay_opacity": slider(props.get("overlay", 0.86)),
        })
        sec["settings"].setdefault("__globals__", {})[
            "background_overlay_color"] = color_ref(NAVY)
    return sec


@block("ie.pagehero")
def ie_pagehero(props):
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], "left", on_dark=True))
    if props.get("title"):
        kids.append(_h(props["title"], props.get("tag", "h1"), T["h_large"],
                       "left", on_dark=True))
    if props.get("standfirst"):
        kids.append(widget("heading", {
            "title": props["standfirst"], "header_size": "div", "align": "left",
            "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(GOLD)}))
    if props.get("intro"):
        kids.append(container([_text(props["intro"], "left", on_dark=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(86, "%"), "width_mobile": slider(100, "%")}))
    sec = _sec([_row([_col(kids, 72, extra={"flex_gap": gap(16)})],
                     GUTTER, align="center")],
               "navy", pad=dims(96, 0, 96, 0), anchor=props.get("anchor"),
               extra={"min_height": slider(props.get("height", 360))})
    img = props.get("image")
    if img and img.get("url"):
        sec["settings"].update({
            "background_image": media(img["url"], img.get("alt", "")),
            "background_position": "center center",
            "background_size": "cover", "background_repeat": "no-repeat",
            "background_overlay_background": "classic",
            "background_overlay_opacity": slider(props.get("overlay", 0.78)),
        })
        sec["settings"].setdefault("__globals__", {})[
            "background_overlay_color"] = color_ref(NAVY)
    return sec
