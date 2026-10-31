"""
blocks_prolific.py — Prolific Roofing LLC, Corvallis OR.

No website reference: the client's domain serves an empty WordPress install.
But this is not a design-from-nothing build either — their printed LEAFLET
is finished brand design and it is the reference, the way Metroline's brand
banner was. Read off it:

    navy #0C254A · lime #96CA30 · grey #6A6E73   (sampled from the logo)
    heavy condensed CAPS headlines
    a row of FIVE circular icon badges ALTERNATING lime and navy
    a photo strip under them
    lime check-mark credential lists
    a navy block with the phone number set very large
    a bottom bar carrying Licensed & Insured and the CCB number

THE CONTRAST ARITHMETIC DECIDES THE BUTTONS. White on the logo's lime is
1.95:1 — it fails badly, and a lime button with a white label is the
obvious thing to build. Navy on that same lime is 7.82:1.

    #96CA30  lime fill, NAVY label                 7.82:1  ✓
    #96CA30  lime as text on navy                   7.82:1  ✓
    #588301  the lime that works as text on white   4.50:1  ✓
    #6A6E73  the logo's own grey, on white          5.13:1  ✓
    #0C254A  navy fill, white label                15.23:1  ✓

TWO HONEST CONSTRAINTS, both recorded in design-spec.json rather than
quietly worked around:

  1. The hexagon badge cannot be built without clip-path, so what is
     reproduced is its BORDER STRUCTURE — navy outer, grey middle, lime
     inner — in `_nested_frame()`.
  2. The eight supplied photographs are all ONE JOB: fascia repair and
     drip-edge replacement on a single property. They cover roughly one of
     the five advertised services. So `pr.services` takes a photo only
     where one genuinely exists and renders `_panel()` otherwise. A stock
     roof or a fascia shot captioned "re-roof" would throw away the one
     real advantage this kit has.

    prf.topbar       licence / phone / area strip
    prf.header       logo, nav, phone, estimate CTA
    prf.hero         full-bleed photo under a navy scrim
    prf.features     four trust cards overlapping the hero
    prf.band         navy caps headline band with a lime sub-line
    prf.sectionhead  caps eyebrow over a lime rule, then the heading
    prf.about        photo beside copy with a lime check list
    prf.services     alternating lime/navy badges      ← signature
    prf.photostrip   the client's own job photographs
    prf.statband     nested-frame panel
    prf.credbar      nested-frame credentials badge
    prf.phoneband    the big phone number block
    prf.steps        numbered process
    prf.expect       numbered cards
    prf.prose        copy beside a photograph
    prf.checklist    ticked list on a card
    prf.contact      split copy/photo + form card
    prf.contactcards phone / email / area / hours
    prf.form         standalone form on a raised card
    prf.faq          accordion, first answer open
    prf.cta          closing band
    prf.pagehero     inner page header
    prf.footer       deepest navy, three columns
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

NAVY = "primary"        # #0C254A
GREY = "secondary"      # #6A6E73 — the logo's own grey
LIME = "accent"         # #96CA30
LIME_TXT = "prlime1"    # #588301 — lime as text on white
LIME_PALE = "prlime2"   # #EAF5D6
DEEP = "prnavy1"        # #081A36 — footer
NAVY_MID = "prnavy2"    # #15356B

PR_PAD = dims(92, 0, 92, 0)
PR_PAD_T = dims(68, 24, 68, 24)
PR_PAD_M = dims(52, 18, 52, 18)
R_CARD = box(8)
R_BTN = box(4)
GUTTER = 24

SHADOW = {
    "box_shadow_box_shadow_type": "yes",
    "box_shadow_box_shadow": {"horizontal": 0, "vertical": 8, "blur": 24,
                              "spread": -8, "color": "rgba(12, 37, 74, 0.14)"},
}
SHADOW_HOVER = {
    "box_shadow_hover_box_shadow_type": "yes",
    "box_shadow_hover_box_shadow": {"horizontal": 0, "vertical": 18,
                                    "blur": 44, "spread": -12,
                                    "color": "rgba(12, 37, 74, 0.26)"},
}
SHADOW_LIFTED = {
    "box_shadow_box_shadow_type": "yes",
    "box_shadow_box_shadow": {"horizontal": 0, "vertical": 24, "blur": 60,
                              "spread": -16, "color": "rgba(12, 37, 74, 0.28)"},
}


# ───────────────────────── the signature devices ───────────────────────────

def _badge(icon_name, tone="lime", size=66):
    """A circular icon badge. The services row ALTERNATES lime and navy
    down its length, which is the single most recognisable thing about the
    leaflet — a row of five identical badges is a different design."""
    lime = tone == "lime"
    return container([widget("icon", {
        "selected_icon": icon(icon_name), "size": slider(round(size * 0.44)),
        "align": "center", "view": "default",
    }, globals_={"primary_color": color_ref(NAVY if lime else LIME)})], {
        "content_width": "full", "flex_direction": "column",
        "flex_justify_content": "center", "flex_align_items": "center",
        "width": slider(size), "min_height": slider(size), "_flex_shrink": "0",
        "border_radius": box(999), "background_background": "classic",
    }, globals_={"background_color": color_ref(LIME if lime else NAVY)})


def _nested_frame(kids, pad=None, tone="white"):
    """The logo's hexagon is three concentric borders — navy outer, grey
    middle, lime inner. The hexagon silhouette needs clip-path and cannot
    be built here, so the BORDER STRUCTURE is what gets reproduced."""
    inner = container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(14),
        "padding": pad or dims(28, 30, 30, 30),
        "padding_mobile": dims(22, 18, 24, 18),
        "border_border": "solid", "border_width": box(2),
        "border_radius": box(4),
        "background_background": "classic",
    }, globals_={"border_color": color_ref(LIME),
                 "background_color": color_ref(
                     C["white"] if tone == "white" else NAVY)})
    mid = container([inner], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(4, 4, 4, 4),
        "border_border": "solid", "border_width": box(2),
        "border_radius": box(6),
    }, globals_={"border_color": color_ref(GREY)})
    return container([mid], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(4, 4, 4, 4),
        "border_border": "solid", "border_width": box(3),
        "border_radius": box(8),
        **SHADOW,
    }, globals_={"border_color": color_ref(NAVY)})


def _panel(icon_name, label, height=220):
    """Stands in for a photograph that does not exist.

    Three of the five advertised services have no photo among the eight the
    client supplied. This renders a deliberate branded panel rather than a
    borrowed picture — it claims nothing, and it looks intentional instead
    of looking like a broken image.
    """
    return container([
        widget("icon", {
            "selected_icon": icon(icon_name), "size": slider(46),
            "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref(LIME)}),
        widget("heading", {
            "title": label, "header_size": "div", "align": "center",
            "__typography__": typo_ref(T["eyebrow"]),
        }, globals_={"title_color": color_ref(C["on_dark"])}),
    ], {
        "content_width": "full", "flex_direction": "column",
        "flex_justify_content": "center", "flex_align_items": "center",
        "flex_gap": gap(12),
        "min_height": slider(height),
        "padding": dims(20, 20, 20, 20),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(NAVY)})


# ───────────────────────────────── helpers ─────────────────────────────────

def _sec(children, bg="white", pad=None, anchor=None, extra=None):
    grounds = {"white": C["white"], "pale": C["surface"], "navy": NAVY,
               "deep": DEEP, "lime": LIME_PALE, "mid": NAVY_MID}
    s = {
        "content_width": "boxed",
        "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "flex_gap": gap(30),
        "padding": pad or PR_PAD,
        "padding_tablet": PR_PAD_T,
        "padding_mobile": PR_PAD_M,
        "background_background": "classic",
    }
    if anchor:
        s["_element_id"] = anchor
    if extra:
        s.update(extra)
    return container(children, s, globals_={
        "background_color": color_ref(grounds.get(bg, C["white"]))})


def _dark(bg):
    return bg in ("navy", "deep", "mid")


def _card(kids, width=None, pad=None, tone=None, hover=True, lifted=False,
          extra=None):
    s = {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(12),
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


def _rule(width=54, align="left", tone=None):
    bar = container([], {
        "content_width": "full", "min_height": slider(4),
        "width": slider(width), "_flex_shrink": "0",
        "border_radius": box(2), "background_background": "classic",
    }, globals_={"background_color": color_ref(tone or LIME)})
    return container([bar], {
        "content_width": "full", "flex_direction": "column",
        "flex_align_items": "center" if align == "center" else "flex-start"})


def _eyebrow(text, align="left", on_dark=False, rule=True):
    lab = widget("heading", {
        "title": text, "header_size": "div", "align": align,
        "__typography__": typo_ref(T["eyebrow"]),
    }, globals_={"title_color": color_ref(LIME if on_dark else LIME_TXT)})
    if not rule:
        return lab
    return container([lab, _rule(54, align)], {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(10),
        "flex_align_items": "center" if align == "center" else "flex-start"})


def _btn(label, href, style="lime", icon_name=None):
    """Four buttons.

        lime    #96CA30 fill, NAVY label — the primary. Navy and not white
                because white on this lime is 1.95:1 and illegible.
        navy    navy fill, white label — the secondary, usually the phone
        ghost   white hairline on navy grounds and photographs
        outline hairline on light grounds — tertiary
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
            "color": "rgba(12, 37, 74, 0.34)"},
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
        g.update({"background_color": color_ref(LIME),
                  "border_color": color_ref(LIME),
                  "button_text_color": color_ref(NAVY),
                  "button_background_hover_color": color_ref(NAVY),
                  "button_hover_border_color": color_ref(NAVY),
                  "hover_color": color_ref(C["white"])})
    return b


def _checks(items, on_dark=False, columns=1, container_px=KIT_CONTAINER):
    """The leaflet's lime check-mark credential list."""
    rows = []
    for t in items:
        mark = container([widget("icon", {
            "selected_icon": icon("fas fa-check"), "size": slider(11),
            "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref(NAVY)})], {
            "content_width": "full", "flex_direction": "column",
            "flex_justify_content": "center", "flex_align_items": "center",
            "width": slider(22), "min_height": slider(22),
            "_flex_shrink": "0", "border_radius": box(999),
            "background_background": "classic",
        }, globals_={"background_color": color_ref(LIME)})
        rows.append(_row([mark, _text(t, "left", on_dark=on_dark, small=True)],
                         11, align="center",
                         extra={"flex_wrap": "nowrap",
                                "flex_direction_mobile": "row",
                                "padding": dims(6, 0, 6, 0)}))
    if columns == 1:
        return container(rows, {"content_width": "full",
                                "flex_direction": "column", "flex_gap": gap(2)})
    per = -(-len(rows) // columns)
    w = _tracks([1] * columns, 22, container=container_px)[0]
    cols = [_col(rows[i:i + per], w, extra={"flex_gap": gap(2)})
            for i in range(0, len(rows), per)]
    return _row(cols, 22, align="flex-start", extra={"flex_wrap": "wrap"})


def _shot(image, height=300, radius=R_CARD):
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
    }, globals_={"background_color": color_ref(C["surface"]),
                 "border_color": color_ref(C["border"])})


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
        }, globals_={"title_color": color_ref(LIME if on_dark else LIME_TXT)}))
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
        "email_subject": f.get("subject", "New website enquiry"),
        "button_text": f.get("submit", "Send"),
        "button_size": "md", "input_size": "md",
        "button_width": "100",
        "show_labels": "yes", "mark_required": "yes",
        "row_gap": slider(13), "column_gap": slider(12),
        "success_message": f.get("success", ""),
        "field_border_radius": box(4), "field_border_width": box(1),
        "button_border_radius": R_BTN,
    }, globals_={
        # `button_background_color` IS the right control on a FORM widget.
        # It is not one on a Button widget — hence _btn uses background_color.
        "button_background_color": color_ref(LIME),
        "button_text_color": color_ref(NAVY),
        "button_background_hover_color": color_ref(NAVY),
        "button_hover_color": color_ref(C["white"]),
        "field_background_color": color_ref(C["white"]),
        "field_text_color": color_ref(C["ink_primary"]),
        "field_border_color": color_ref(C["border"]),
        "label_color": color_ref(NAVY),
        "mark_required_color": color_ref(LIME_TXT),
    })


# ─────────────────────────────── chrome ────────────────────────────────────

@block("prf.topbar")
def prf_topbar(props):
    items = []
    for it in props.get("items", []):
        kids = []
        if it.get("icon"):
            kids.append(widget("icon", {
                "selected_icon": icon(it["icon"]), "size": slider(12),
                "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref(LIME)}))
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


@block("prf.header")
def prf_header(props):
    if props.get("logo"):
        brand = widget("theme-site-logo", {
            "align": "left", "image_size": "full",
            "width": slider(props.get("logo_width", 110)),
            "width_mobile": slider(84),
            "image": media(props["logo"], props.get("business", ""))})
    else:
        brand = widget("heading", {
            "title": props.get("business", "Prolific Roofing"),
            "header_size": "div", "align": "left", "link": link("/"),
            "__typography__": typo_ref(T["wordmark"]),
        }, globals_={"title_color": color_ref(NAVY)})

    nav = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"),
        "layout": "horizontal", "align_items": "center",
        "pointer": "underline", "animation_line": "fade",
        "menu_space_between": slider(props.get("nav_gap", 24)),
        "toggle_align": "right",
        "__typography__": typo_ref(T["meta"]),
    }, globals_={
        "color_menu_item": color_ref(NAVY),
        "color_menu_item_hover": color_ref(LIME_TXT),
        "color_menu_item_active": color_ref(LIME_TXT),
        "pointer_color_menu_item_hover": color_ref(LIME),
        "pointer_color_menu_item_active": color_ref(LIME),
        "toggle_color": color_ref(NAVY),
    })

    actions = []
    if props.get("phone_display"):
        actions.append(_btn(props["phone_display"],
                            "tel:+1" + props.get("phone", ""), "navy",
                            "fas fa-phone"))
    if props.get("cta_label"):
        actions.append(_btn(props["cta_label"],
                            props.get("cta_url", "/schedule-an-appointment/"),
                            "lime"))

    row = _row([
        _col([brand], 20, extra={"flex_justify_content": "center"}),
        _col([nav], 48, extra={"flex_justify_content": "center",
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
        "padding": dims(12, 0, 12, 0),
        "padding_mobile": dims(10, 14, 10, 14),
        "background_background": "classic",
        "sticky": "top", "sticky_on": ["desktop", "tablet", "mobile"],
        "sticky_offset": 0,
        **SHADOW,
    }, globals_={"background_color": color_ref(C["white"])})


@block("prf.footer")
def prf_footer(props):
    brand = []
    if props.get("logo"):
        brand.append(widget("image", {
            "image": media(props["logo"], props.get("business", "Logo")),
            "image_size": "full", "width": slider(130), "align": "left"}))
    if props.get("blurb"):
        brand.append(_text(props["blurb"], "left", on_dark=True, small=True))
    if props.get("strapline_image"):
        brand.append(widget("image", {
            "image": media(props["strapline_image"],
                           props.get("strapline_alt", "")),
            "image_size": "full", "width": slider(230), "align": "left"}))
    if props.get("socials"):
        brand.append(_row([widget("icon", {
            "selected_icon": icon(s.get("icon", "fab fa-facebook-f")),
            "size": slider(15), "align": "center", "view": "default",
            "link": link(s.get("url", "#")),
        }, globals_={"primary_color": color_ref(LIME)})
            for s in props["socials"]], 16, align="center",
            extra={"flex_wrap": "wrap", "flex_direction_mobile": "row"}))

    cols = props.get("columns", [])
    widths = _tracks([1.5] + [1] * len(cols), GUTTER)
    body = [_col(brand, widths[0], extra={"flex_gap": gap(16)})]
    for i, c in enumerate(cols):
        kids = [widget("heading", {
            "title": c.get("title", ""), "header_size": "div", "align": "left",
            "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(C["white"])})]
        for l in c.get("links", []):
            r = []
            if l.get("icon"):
                r.append(widget("icon", {
                    "selected_icon": icon(l["icon"]), "size": slider(12),
                    "align": "center", "view": "default",
                }, globals_={"primary_color": color_ref(LIME)}))
            lab = widget("heading", {
                "title": l.get("label", ""), "header_size": "div",
                "align": "left", "__typography__": typo_ref(T["body_small"]),
            }, globals_={"title_color": color_ref(C["on_dark"])})
            if l.get("url"):
                lab["settings"]["link"] = link(l["url"])
            r.append(lab)
            kids.append(_row(r, 9, align="flex-start",
                             extra={"flex_wrap": "nowrap",
                                    "flex_direction_mobile": "row",
                                    "padding": dims(4, 0, 4, 0)}))
        body.append(_col(kids, widths[i + 1], extra={"flex_gap": gap(7)}))

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
        "padding": dims(74, 0, 32, 0),
        "padding_mobile": dims(52, 18, 28, 18),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(DEEP)})


# ─────────────────────────────── sections ──────────────────────────────────

@block("prf.hero")
def prf_hero(props):
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], "left", on_dark=True))
    if props.get("title"):
        kids.append(_h(props["title"], props.get("tag", "h1"), T["hero"],
                       "left", on_dark=True))
    if props.get("standfirst"):
        kids.append(widget("heading", {
            "title": props["standfirst"], "header_size": "div", "align": "left",
            "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(LIME)}))
    if props.get("intro"):
        kids.append(container([_text(props["intro"], "left", on_dark=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(92, "%"), "width_mobile": slider(100, "%")}))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"), "lime"))
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props.get("alt_url", "#"),
                         "ghost", "fas fa-phone"))
    if btns:
        kids.append(_row(btns, 12, align="center",
                         extra={"flex_wrap": "wrap",
                                "flex_direction_mobile": "column",
                                "padding": dims(12, 0, 0, 0)}))

    col = _col(kids, props.get("width", 62), extra={"flex_gap": gap(20)})
    sec = _sec([_row([col], GUTTER, align="center")], "navy",
               pad=dims(props.get("pad_top", 116), 0,
                        props.get("pad_bottom", 160), 0),
               anchor=props.get("anchor"),
               extra={"min_height": slider(props.get("height", 600))})
    img = props.get("image")
    if img and img.get("url"):
        sec["settings"].update({
            "background_image": media(img["url"], img.get("alt", "")),
            "background_position": props.get("position", "center center"),
            "background_size": "cover", "background_repeat": "no-repeat",
            "background_overlay_background": "classic",
            "background_overlay_opacity": slider(props.get("overlay", 0.78)),
        })
        sec["settings"].setdefault("__globals__", {})[
            "background_overlay_color"] = color_ref(NAVY)
    return sec


@block("prf.features")
def prf_features(props):
    """Four trust cards, badges alternating lime and navy as the leaflet
    does, overlapping the foot of the hero."""
    cols = props.get("columns", 4)
    w = _tracks([1] * cols, GUTTER)[0]
    cells = []
    for n, it in enumerate(props.get("items", [])):
        cells.append(_card([
            _badge(it.get("icon", "fas fa-check"),
                   "lime" if n % 2 == 0 else "navy", 60),
            widget("heading", {
                "title": it.get("title", ""), "header_size": "h3",
                "align": "center", "__typography__": typo_ref(T["h_small"]),
            }, globals_={"title_color": color_ref(NAVY)}),
            _text(it.get("text", ""), "center", small=True),
        ], w, pad=dims(30, 22, 32, 22),
            extra={"flex_align_items": "center"}))
    strip = _row(cells, GUTTER, align="stretch", extra={"flex_wrap": "wrap"})
    pull = props.get("pull")
    if pull:
        strip["settings"].update({"margin": dims(pull, 0, 0, 0),
                                  "margin_mobile": dims(-40, 0, 0, 0)})
    return _sec([strip], props.get("bg", "white"),
                pad=dims(0, 0, 80, 0), anchor=props.get("anchor"))


@block("prf.band")
def prf_band(props):
    """The leaflet's navy caps banner with a lime sub-line."""
    kids = [widget("heading", {
        "title": props.get("title", ""), "header_size": props.get("tag", "h2"),
        "align": "center", "__typography__": typo_ref(T["h_large"]),
    }, globals_={"title_color": color_ref(C["white"])})]
    if props.get("subtitle"):
        kids.append(widget("heading", {
            "title": props["subtitle"], "header_size": "div",
            "align": "center", "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(LIME)}))
    if props.get("intro"):
        kids.append(container([_text(props["intro"], "center", on_dark=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(74, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"), "lime"))
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props.get("alt_url", "#"),
                         "ghost", "fas fa-phone"))
    if btns:
        kids.append(_row(btns, 12, align="center", justify="center",
                         extra={"flex_wrap": "wrap",
                                "flex_direction_mobile": "column",
                                "padding": dims(8, 0, 0, 0)}))
    return _sec(kids, props.get("bg", "navy"), pad=dims(62, 0, 62, 0),
                anchor=props.get("anchor"),
                extra={"flex_align_items": "center"})


@block("prf.sectionhead")
def prf_sectionhead(props):
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
                pad=props.get("tight") and dims(70, 0, 36, 0) or None,
                extra=({"flex_align_items": "center"}
                       if align == "center" else None))


@block("prf.about")
def prf_about(props):
    on_dark = _dark(props.get("bg", "white"))
    right = _head_stack(props, "left", on_dark)
    for p in props.get("paragraphs", []):
        right.append(_text(p, "left", on_dark=on_dark))
    if props.get("checks"):
        right.append(_checks(props["checks"], on_dark,
                             columns=props.get("check_columns", 1),
                             container_px=620))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"), "lime"))
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props.get("alt_url", "#"),
                         "outline", "fas fa-phone"))
    if btns:
        right.append(_row(btns, 12, align="center",
                          extra={"flex_wrap": "wrap",
                                 "padding": dims(10, 0, 0, 0)}))
    wl, wr = _tracks([1, 1.06], GUTTER)
    body = [_col([_shot(props.get("image"), props.get("image_height", 430))],
                 wl),
            _col(right, wr, extra={"flex_gap": gap(16)})]
    if props.get("flip"):
        body.reverse()
    return _sec([_row(body, GUTTER, align="center",
                      extra={"flex_wrap": "wrap"})],
                props.get("bg", "white"), anchor=props.get("anchor"))


@block("prf.services")
def prf_services(props):
    """THE SIGNATURE. Circular icon badges ALTERNATING lime and navy down
    the row, as the leaflet does.

    A card takes a photograph only where one genuinely shows that service.
    The client's eight photographs are all one fascia and drip-edge job, so
    the other services get `_panel()` — a deliberate branded block, not a
    borrowed picture and not a stock roof.
    """
    kids = _head_stack(props, props.get("align", "center"),
                       _dark(props.get("bg", "white")))
    per = props.get("columns", 3)
    w = _tracks([1] * per, GUTTER)[0]
    cells = []
    for n, it in enumerate(props.get("items", [])):
        body = [_badge(it.get("icon", "fas fa-house"),
                       "lime" if n % 2 == 0 else "navy", 66)]
        body.append(widget("heading", {
            "title": it.get("title", ""), "header_size": "h3", "align": "left",
            "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(NAVY)}))
        if it.get("text"):
            body.append(_text(it["text"], "left", small=True))
        if it.get("url"):
            body.append(_btn(it.get("link_label", "Learn More"), it["url"],
                             "outline"))
        shot = (_shot(it["image"], props.get("shot", 220), radius=box(0))
                if it.get("image")
                else _panel(it.get("icon", "fas fa-house"),
                            it.get("panel_label", it.get("title", "")),
                            props.get("shot", 220)))
        body.append(shot)
        card = _card(body, w, pad=dims(28, 0, 0, 0),
                     extra={"flex_gap": gap(12), "overflow": "hidden"})
        for ch in card["elements"][:-1]:
            ch.setdefault("settings", {})
            ch["settings"]["_margin"] = dims(0, 26, 0, 26)
        cells.append(card)
    kids.append(_row(cells, GUTTER, align="stretch",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("prf.photostrip")
def prf_photostrip(props):
    """The leaflet's photo strip, carrying the client's own job photographs
    and captioned as what they actually are."""
    kids = _head_stack(props, props.get("align", "center"), False)
    items = props.get("items", [])
    per = props.get("columns", min(len(items), 4)) or 1
    w = _tracks([1] * per, 16)[0]
    cells = []
    for it in items:
        body = [_shot(it.get("image"), it.get("height", 210), radius=box(0))]
        if it.get("caption"):
            body.append(_text(it["caption"], "left", small=True))
        card = _card(body, w, pad=dims(0, 0, 18, 0),
                     extra={"flex_gap": gap(10), "overflow": "hidden"})
        for ch in card["elements"][1:]:
            ch.setdefault("settings", {})
            ch["settings"]["_margin"] = dims(0, 18, 0, 18)
        cells.append(card)
    kids.append(_row(cells, 16, align="stretch", extra={"flex_wrap": "wrap"}))
    if props.get("note"):
        kids.append(container([_text(props["note"], "center", small=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(76, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    return _sec(kids, props.get("bg", "pale"), anchor=props.get("anchor"))


@block("prf.statband")
def prf_statband(props):
    """A nested-frame panel — the logo's border structure at section scale."""
    items = props.get("items", [])
    per = max(len(items), 1)
    w = _tracks([1] * per, GUTTER, container=KIT_CONTAINER - 90)[0]
    cells = []
    for it in items:
        cells.append(_col([
            widget("heading", {
                "title": it.get("value", ""), "header_size": "div",
                "align": "center", "__typography__": typo_ref(T["h_large"]),
            }, globals_={"title_color": color_ref(NAVY)}),
            _rule(40, "center"),
            widget("heading", {
                "title": it.get("label", ""), "header_size": "div",
                "align": "center", "__typography__": typo_ref(T["eyebrow"]),
            }, globals_={"title_color": color_ref(GREY)}),
        ], w, extra={"flex_gap": gap(10), "flex_align_items": "center"}))
    frame = _nested_frame([_row(cells, GUTTER, align="flex-start",
                                extra={"flex_wrap": "wrap"})],
                          pad=dims(34, 30, 36, 30))
    return _sec([frame], props.get("bg", "white"),
                pad=dims(0, 0, 90, 0), anchor=props.get("anchor"))


@block("prf.credbar")
def prf_credbar(props):
    """Licensed & Insured, the CCB number and the service area, in the
    logo's nested frame. Oregon requires the CCB number on advertising,
    websites included, so this is compliance as much as design."""
    items = []
    for it in props.get("items", []):
        items.append(_row([
            _badge(it.get("icon", "fas fa-shield-halved"),
                   it.get("tone", "lime"), 52),
            container([
                widget("heading", {
                    "title": it.get("label", ""), "header_size": "div",
                    "align": "left", "__typography__": typo_ref(T["eyebrow"]),
                }, globals_={"title_color": color_ref(LIME_TXT)}),
                widget("heading", {
                    "title": it.get("value", ""), "header_size": "div",
                    "align": "left", "__typography__": typo_ref(T["h_small"]),
                }, globals_={"title_color": color_ref(NAVY)}),
            ], {"content_width": "full", "flex_direction": "column",
                "flex_gap": gap(3)}),
        ], 13, align="center",
            extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"}))
    per = max(len(items), 1)
    w = _tracks([1] * per, GUTTER, container=KIT_CONTAINER - 90)[0]
    cols = [_col([i], w) for i in items]
    frame = _nested_frame([_row(cols, GUTTER, align="center",
                                extra={"flex_wrap": "wrap"})],
                          pad=dims(26, 28, 28, 28))
    return _sec([frame], props.get("bg", "white"),
                pad=props.get("pad") and dims(*props["pad"])
                or dims(0, 0, 86, 0),
                anchor=props.get("anchor"))


@block("prf.phoneband")
def prf_phoneband(props):
    """The leaflet's bottom third: the phone number set very large on navy,
    beside a column of lime check marks."""
    left = []
    if props.get("eyebrow"):
        left.append(_eyebrow(props["eyebrow"], "left", on_dark=True))
    if props.get("title"):
        left.append(_h(props["title"], "h2", T["h_medium"], "left",
                       on_dark=True))
    phone = widget("heading", {
        "title": props.get("phone_display", ""), "header_size": "div",
        "align": "left", "__typography__": typo_ref(T["hero"]),
        "link": link(props.get("phone_href", "#")),
    }, globals_={"title_color": color_ref(LIME)})
    left.append(phone)
    if props.get("note"):
        left.append(_text(props["note"], "left", on_dark=True))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"), "lime"))
    if btns:
        left.append(_row(btns, 12, align="center",
                         extra={"flex_wrap": "wrap",
                                "padding": dims(8, 0, 0, 0)}))
    wl, wr = _tracks([1.15, 1], GUTTER)
    right = []
    if props.get("checks"):
        right.append(_checks(props["checks"], True))
    return _sec([_row([_col(left, wl, extra={"flex_gap": gap(16)}),
                       _col(right, wr, extra={"flex_gap": gap(8),
                                              "flex_justify_content":
                                                  "center"})],
                      GUTTER, align="center", extra={"flex_wrap": "wrap"})],
                props.get("bg", "navy"), pad=dims(74, 0, 74, 0),
                anchor=props.get("anchor"))


@block("prf.steps")
def prf_steps(props):
    bg = props.get("bg", "white")
    on_dark = _dark(bg)
    kids = _head_stack(props, props.get("align", "center"), on_dark)
    items = props.get("items", [])
    per = props.get("columns", min(len(items), 4)) or 1
    w = _tracks([1] * per, GUTTER)[0]
    cells = []
    for n, it in enumerate(items, 1):
        cells.append(_col([
            _badge(it.get("icon", "fas fa-check"),
                   "lime" if n % 2 else "navy", 64),
            widget("heading", {
                "title": "%02d" % n, "header_size": "div", "align": "center",
                "__typography__": typo_ref(T["eyebrow"]),
            }, globals_={"title_color": color_ref(
                LIME if on_dark else LIME_TXT)}),
            widget("heading", {
                "title": it.get("title", ""), "header_size": "h3",
                "align": "center", "__typography__": typo_ref(T["h_small"]),
            }, globals_={"title_color": color_ref(
                C["white"] if on_dark else NAVY)}),
            _text(it.get("text", ""), "center", on_dark=on_dark, small=True),
        ], w, extra={"flex_gap": gap(10), "flex_align_items": "center"}))
    kids.append(_row(cells, GUTTER, align="flex-start",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, bg, anchor=props.get("anchor"))


@block("prf.expect")
def prf_expect(props):
    on_dark = _dark(props.get("bg", "white"))
    kids = _head_stack(props, props.get("align", "center"), on_dark)
    items = props.get("items", [])
    per = props.get("columns", min(len(items), 4)) or 1
    w = _tracks([1] * per, GUTTER)[0]
    cells = []
    for n, it in enumerate(items, 1):
        body = [_badge(it.get("icon", "fas fa-check"),
                       "lime" if n % 2 else "navy", 58)]
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
        cells.append(_card(body, w, pad=dims(26, 24, 28, 24),
                           extra={"flex_gap": gap(10)}))
    kids.append(_row(cells, GUTTER, align="stretch",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("prf.prose")
def prf_prose(props):
    on_dark = _dark(props.get("bg", "white"))
    left = _head_stack(props, "left", on_dark)
    for p in props.get("paragraphs", []):
        left.append(_text(p, "left", on_dark=on_dark))
    if props.get("checks"):
        left.append(_checks(props["checks"], on_dark))
    wl, wr = _tracks([1.12, 1], GUTTER)
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


@block("prf.checklist")
def prf_checklist(props):
    on_dark = _dark(props.get("bg", "pale"))
    kids = _head_stack(props, props.get("align", "left"), on_dark)
    kids.append(_card([_checks(props.get("items", []), on_dark,
                               columns=props.get("columns", 2),
                               container_px=KIT_CONTAINER - 64)],
                      pad=dims(30, 32, 32, 32), hover=False))
    return _sec(kids, props.get("bg", "pale"), anchor=props.get("anchor"))


@block("prf.contact")
def prf_contact(props):
    left = _head_stack(props, "left", False)
    for p in props.get("paragraphs", []):
        left.append(_text(p, "left"))
    if props.get("phone_display"):
        left.append(_row([
            _badge("fas fa-phone", "lime", 48),
            widget("heading", {
                "title": props["phone_display"], "header_size": "div",
                "align": "left", "__typography__": typo_ref(T["h_medium"]),
                "link": link(props.get("phone_href", "#")),
            }, globals_={"title_color": color_ref(NAVY)}),
        ], 13, align="center",
            extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"}))
    if props.get("checks"):
        left.append(_checks(props["checks"], False))
    if props.get("image"):
        left.append(_shot(props["image"], props.get("image_height", 290)))

    f = dict(props.get("form", {}))
    card_kids = []
    if f.get("title"):
        card_kids.append(_h(f["title"], "h2", T["h_small"], "left"))
    card_kids.append(_form_widget(f))
    card = _card(card_kids, pad=dims(32, 32, 34, 32), hover=False, lifted=True)
    wl, wr = _tracks([1, 1.05], GUTTER)
    return _sec([_row([_col(left, wl, extra={"flex_gap": gap(16)}),
                       _col([card], wr)], GUTTER, align="flex-start",
                      extra={"flex_wrap": "wrap"})],
                props.get("bg", "pale"), anchor=props.get("anchor", "contact"))


@block("prf.contactcards")
def prf_contactcards(props):
    items = props.get("items", [])
    per = props.get("columns", min(len(items), 4)) or 1
    w = _tracks([1] * per, GUTTER)[0]
    cells = []
    for n, it in enumerate(items):
        body = [_badge(it.get("icon", "fas fa-phone"),
                       "lime" if n % 2 == 0 else "navy", 56),
                widget("heading", {
                    "title": it.get("label", ""), "header_size": "div",
                    "align": "left", "__typography__": typo_ref(T["eyebrow"]),
                }, globals_={"title_color": color_ref(LIME_TXT)})]
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


@block("prf.form")
def prf_form(props):
    f = dict(props.get("form", {}))
    head = _head_stack(props, "left", False)
    card = _card(head + [_form_widget(f)], pad=dims(34, 34, 36, 34),
                 lifted=True, hover=False)
    side = props.get("side")
    if not side:
        return _sec([card], props.get("bg", "pale"),
                    anchor=props.get("anchor", "form"))
    skids = []
    if side.get("title"):
        skids.append(_h(side["title"], "h2", T["h_medium"], "left"))
    for p in side.get("paragraphs", []):
        skids.append(_text(p, "left"))
    if side.get("checks"):
        skids.append(_checks(side["checks"], False))
    if side.get("image"):
        skids.append(_shot(side["image"], side.get("image_height", 260)))
    wl, wr = _tracks([1, 1.1], GUTTER)
    return _sec([_row([_col(skids, wl, extra={"flex_gap": gap(16)}),
                       _col([card], wr)], GUTTER, align="flex-start",
                      extra={"flex_wrap": "wrap"})],
                props.get("bg", "pale"), anchor=props.get("anchor", "form"))


@block("prf.faq")
def prf_faq(props):
    kids = _head_stack(props, props.get("align", "center"), False)
    kids.append(_faq(props.get("items", [])))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("prf.cta")
def prf_cta(props):
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], "center", on_dark=True))
    if props.get("title"):
        kids.append(_h(props["title"], props.get("tag", "h2"), T["h_large"],
                       "center", on_dark=True))
    if props.get("subtitle"):
        kids.append(widget("heading", {
            "title": props["subtitle"], "header_size": "div",
            "align": "center", "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(LIME)}))
    if props.get("intro"):
        kids.append(container([_text(props["intro"], "center", on_dark=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(72, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"), "lime"))
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
            "background_overlay_opacity": slider(props.get("overlay", 0.88)),
        })
        sec["settings"].setdefault("__globals__", {})[
            "background_overlay_color"] = color_ref(NAVY)
    return sec


@block("prf.pagehero")
def prf_pagehero(props):
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
        }, globals_={"title_color": color_ref(LIME)}))
    if props.get("intro"):
        kids.append(container([_text(props["intro"], "left", on_dark=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(86, "%"), "width_mobile": slider(100, "%")}))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"), "lime"))
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props.get("alt_url", "#"),
                         "ghost", "fas fa-phone"))
    if btns:
        kids.append(_row(btns, 12, align="center",
                         extra={"flex_wrap": "wrap",
                                "padding": dims(8, 0, 0, 0)}))
    sec = _sec([_row([_col(kids, 70, extra={"flex_gap": gap(16)})],
                     GUTTER, align="center")],
               "navy", pad=dims(100, 0, 100, 0), anchor=props.get("anchor"),
               extra={"min_height": slider(props.get("height", 380))})
    img = props.get("image")
    if img and img.get("url"):
        sec["settings"].update({
            "background_image": media(img["url"], img.get("alt", "")),
            "background_position": "center center",
            "background_size": "cover", "background_repeat": "no-repeat",
            "background_overlay_background": "classic",
            "background_overlay_opacity": slider(props.get("overlay", 0.82)),
        })
        sec["settings"].setdefault("__globals__", {})[
            "background_overlay_color"] = color_ref(NAVY)
    return sec
