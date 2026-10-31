"""
blocks_md.py — Medina Plumbing & Radiant Heating, Inc., Citrus Heights CA.

ONE client input: the logo. No copy document, no design reference, no
reachable site, and a Facebook page that refuses unauthenticated requests.
So the logo specifies the design, and it is unusually generous about it:

    1. The mark is a SUN — a spiral core with flame rays, filled with a
       gradient that samples at #EC6D00 → #F6AA06 → #FDE053. That ray fan
       is `_rays()`, the signature here. It is not ornament: the product IS
       radiant heat, so the mark and the subject are the same thing.
    2. The wordmark is widely LETTERSPACED ROMAN SERIF CAPS, so headings are
       a serif and eyebrows are letterspaced caps.
    3. A single orange rule separates wordmark from descriptor — that rule
       sits under every section eyebrow here, carrying the sun's gradient.
    4. The tagline sets "QUALITY WORK." in black and "RADIANT COMFORT." in
       orange. That is the contrast rule the logo already solved (below).

THE CONTRAST ARITHMETIC DECIDES THE BUTTONS AND THE EYEBROWS. White on the
logo orange #F48200 is 2.61:1 — it fails, and an orange button with a white
label is the obvious build. Black on that same orange is 7.23:1. And orange
as small text on a light ground is also 2.61:1, which is exactly why the
logo's own tagline reserves orange for display size.

    #F48200  orange fill, BLACK label                 7.23:1  ✓
    #F48200  orange as text on near-black             7.23:1  ✓
    #99672E  the one orange that clears BOTH white
             (4.85) and the warm surface (4.50)               ✓
    #111111  ink fill, white label                   18.88:1  ✓

The neutral ground is a WARM off-white with warm hairlines, not the cool
blue-grey every other kit here uses. A company selling warmth should not sit
on a cold ground, and the logo contains no blue at all.

    md.topbar        licence / phone / service-area strip
    md.header        logo, nav, phone, estimate CTA
    md.hero          photo + ink scrim, room left for the trust strip
    md.trust         four-item strip that OVERLAPS the hero
    md.sectionhead   letterspaced caps eyebrow over the ray fan
    md.about         photo beside copy, with value cards
    md.services      photo service cards
    md.compare       radiant vs forced air — the explainer
    md.why           why-choose-us cards
    md.steps         numbered install process on the dark band
    md.gallery       the honest system guide — labelled, not claimed
    md.galleryintro  the standing notice above it
    md.prose         copy beside a photograph
    md.checklist     ticked list on a card
    md.expect        numbered cards — what happens next
    md.area          service-area band with town chips
    md.faq           accordion, first answer open
    md.contactcards  phone / email / mailing / hours / licence
    md.form          enquiry or booking form on a raised card
    md.cta           closing band, gradient primary
    md.pagehero      inner page header
    md.footer        near-black, four columns
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

INK = "primary"         # #111111
INK_SOFT = "secondary"  # #3A332E
ORANGE = "accent"       # #F48200
ORG_DEEP = "mdorg01"    # #EC6D00 — gradient start
AMBER = "mdamb01"       # #F6AA06 — gradient mid
GOLD = "mdgld01"        # #FDE053 — gradient end
ORG_TXT = "mdorgt1"     # #99672E — small orange text on light grounds
DEEP = "mdink01"        # #0A0A0A — footer

MD_PAD = dims(94, 0, 94, 0)
MD_PAD_T = dims(68, 24, 68, 24)
MD_PAD_M = dims(52, 18, 52, 18)
R_CARD = box(6)
R_BTN = box(2)          # almost square — the logo's rule and letterforms are
GUTTER = 24

# Warm-tinted depth. The shadow colour is brown-black rather than blue-black
# so it sits on the warm ground without going grey.
SHADOW = {
    "box_shadow_box_shadow_type": "yes",
    "box_shadow_box_shadow": {"horizontal": 0, "vertical": 8, "blur": 24,
                              "spread": -8, "color": "rgba(42, 37, 34, 0.14)"},
}
SHADOW_HOVER = {
    "box_shadow_hover_box_shadow_type": "yes",
    "box_shadow_hover_box_shadow": {"horizontal": 0, "vertical": 18,
                                    "blur": 44, "spread": -12,
                                    "color": "rgba(42, 37, 34, 0.26)"},
}
SHADOW_LIFTED = {
    "box_shadow_box_shadow_type": "yes",
    "box_shadow_box_shadow": {"horizontal": 0, "vertical": 24, "blur": 60,
                              "spread": -16, "color": "rgba(42, 37, 34, 0.28)"},
}


# ───────────────────────── the signature motif ─────────────────────────────

def _sun_gradient(angle=135):
    """The logo's own three-stop ramp, as container settings.

    Elementor's gradient takes two stops, so the ramp is carried as
    deep-orange → pale-gold with the amber implied by the stop positions;
    sampling the mark showed amber sitting near the middle anyway.
    """
    return {
        "background_background": "gradient",
        "background_gradient_type": "linear",
        "background_gradient_angle": slider(angle, "deg"),
        "background_color_stop": slider(0, "%"),
        "background_color_b_stop": slider(100, "%"),
    }


def _rays(align="left", scale=1.0, flat=False):
    """The sun's rays, rebuilt from containers.

    Five bars whose heights rise to the middle and fall away, filled with
    the logo's gradient — a fan of light. At eyebrow scale it reads as the
    orange rule under the wordmark; opened out on a dark band it reads as
    the mark itself.
    """
    heights = [9, 16, 24, 16, 9]
    bars = []
    for h in heights:
        s = {
            "content_width": "full",
            "min_height": slider(round(h * scale)),
            "width": slider(round(5 * scale)),
            "_flex_shrink": "0",
            "border_radius": box(1),
        }
        if flat:
            s["background_background"] = "classic"
            g = {"background_color": color_ref(ORANGE)}
        else:
            s.update(_sun_gradient(0))
            g = {"background_color": color_ref(ORG_DEEP),
                 "background_color_b": color_ref(GOLD)}
        bars.append(container([], s, globals_=g))
    return container(bars, {
        "content_width": "full",
        "flex_direction": "row",
        "flex_gap": gap(round(4 * scale)),
        "flex_align_items": "flex-end",
        "flex_wrap": "nowrap",
        "flex_direction_mobile": "row",
        "flex_justify_content": "center" if align == "center" else "flex-start",
    })


# ───────────────────────────────── helpers ─────────────────────────────────

def _sec(children, bg="surface", pad=None, anchor=None, extra=None):
    grounds = {"white": C["white"], "surface": C["surface"], "ink": INK,
               "deep": DEEP}
    s = {
        "content_width": "boxed",
        "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "flex_gap": gap(30),
        "padding": pad or MD_PAD,
        "padding_tablet": MD_PAD_T,
        "padding_mobile": MD_PAD_M,
        "background_background": "classic",
    }
    if anchor:
        s["_element_id"] = anchor
    if extra:
        s.update(extra)
    return container(children, s, globals_={
        "background_color": color_ref(grounds.get(bg, C["surface"]))})


def _dark(bg):
    return bg in ("ink", "deep")


def _card(kids, width=None, pad=None, tone=None, hover=True, lifted=False,
          extra=None):
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
        tone or (C["white"] if on_dark else INK))})


def _eyebrow(text, align="left", on_dark=False, rule=True):
    """Letterspaced caps, as the wordmark is. INK on light grounds — orange
    small text on light is 2.61:1, which is the trap the logo's own tagline
    already avoids by setting its black half in black."""
    lab = widget("heading", {
        "title": text, "header_size": "div", "align": align,
        "__typography__": typo_ref(T["eyebrow"]),
    }, globals_={"title_color": color_ref(ORANGE if on_dark else INK)})
    if not rule:
        return lab
    return container([lab, _rays(align)], {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(11),
        "flex_align_items": "center" if align == "center" else "flex-start"})


def _btn(label, href, style="orange", icon_name=None):
    """Five buttons.

        gradient the sun's own ramp, BLACK label — the single most
                 important action on a page
        orange   #F48200 fill, BLACK label — the primary. Black and not
                 white because white on this orange is 2.61:1.
        ink      near-black fill, white label — the secondary, the phone
        ghost    white hairline on dark grounds and photographs
        outline  warm hairline on light grounds — tertiary
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
            "color": "rgba(42, 37, 34, 0.34)"},
    })
    g = b["settings"].setdefault("__globals__", {})
    if style == "gradient":
        b["settings"].update(_sun_gradient(120))
        g.update({"background_color": color_ref(ORG_DEEP),
                  "background_color_b": color_ref(GOLD),
                  "border_color": color_ref(ORG_DEEP),
                  "button_text_color": color_ref(INK),
                  "button_background_hover_color": color_ref(INK),
                  "button_hover_border_color": color_ref(INK),
                  "hover_color": color_ref(C["white"])})
    elif style == "ink":
        g.update({"background_color": color_ref(INK),
                  "border_color": color_ref(INK),
                  "button_text_color": color_ref(C["white"]),
                  "button_background_hover_color": color_ref(INK_SOFT),
                  "button_hover_border_color": color_ref(INK_SOFT),
                  "hover_color": color_ref(C["white"])})
    elif style == "ghost":
        b["settings"].update({"border_border": "solid", "border_width": box(2)})
        g.update({"background_color": color_ref(C["transparent"]),
                  "border_color": color_ref(C["white"]),
                  "button_text_color": color_ref(C["white"]),
                  "button_background_hover_color": color_ref(C["white"]),
                  "button_hover_border_color": color_ref(C["white"]),
                  "hover_color": color_ref(INK)})
    elif style == "outline":
        b["settings"].update({"border_border": "solid", "border_width": box(1),
                              "text_padding": dims(12, 22, 12, 22)})
        g.update({"background_color": color_ref(C["transparent"]),
                  "border_color": color_ref(C["border"]),
                  "button_text_color": color_ref(INK),
                  "button_background_hover_color": color_ref(INK),
                  "button_hover_border_color": color_ref(INK),
                  "hover_color": color_ref(C["white"])})
    else:
        g.update({"background_color": color_ref(ORANGE),
                  "border_color": color_ref(ORANGE),
                  "button_text_color": color_ref(INK),
                  "button_background_hover_color": color_ref(INK),
                  "button_hover_border_color": color_ref(INK),
                  "hover_color": color_ref(C["white"])})
    return b


def _ticks(items, on_dark=False, columns=1, container_px=KIT_CONTAINER):
    rows = []
    for t in items:
        mark = widget("icon", {
            "selected_icon": icon("fas fa-check"), "size": slider(13),
            "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref(ORANGE if on_dark
                                                else ORG_TXT)})
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
    }, globals_={"background_color": color_ref(C["surface"]),
                 "border_color": color_ref(C["border"])})


def _numeral(n, on_dark=False, size=None):
    return widget("heading", {
        "title": str(n), "header_size": "div", "align": "left",
        "__typography__": typo_ref(size or T["h_large"]),
    }, globals_={"title_color": color_ref(ORANGE if on_dark else ORG_TXT)})


def _disc(icon_name, size=54, gradient=True):
    """A square badge — the logo has no circles except the sun itself."""
    s = {
        "content_width": "full", "flex_direction": "column",
        "flex_justify_content": "center", "flex_align_items": "center",
        "width": slider(size), "min_height": slider(size),
        "_flex_shrink": "0", "border_radius": box(3),
    }
    if gradient:
        s.update(_sun_gradient(135))
        g = {"background_color": color_ref(ORG_DEEP),
             "background_color_b": color_ref(GOLD)}
    else:
        s["background_background"] = "classic"
        g = {"background_color": color_ref(ORANGE)}
    return container([widget("icon", {
        "selected_icon": icon(icon_name), "size": slider(round(size * 0.40)),
        "align": "center", "view": "default",
    }, globals_={"primary_color": color_ref(INK)})], s, globals_=g)


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
            ORANGE if on_dark else ORG_TXT)}))
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
        "row_gap": slider(14), "column_gap": slider(12),
        "success_message": f.get("success", ""),
        "field_border_radius": box(2), "field_border_width": box(1),
        "button_border_radius": R_BTN,
    }, globals_={
        # `button_background_color` IS the right control on a FORM widget.
        # It is NOT one on a Button widget, which is why _btn uses
        # `background_color` instead.
        "button_background_color": color_ref(ORANGE),
        "button_text_color": color_ref(INK),
        "button_background_hover_color": color_ref(INK),
        "button_hover_color": color_ref(C["white"]),
        "field_background_color": color_ref(C["white"]),
        "field_text_color": color_ref(C["ink_primary"]),
        "field_border_color": color_ref(C["border"]),
        "label_color": color_ref(INK),
        "mark_required_color": color_ref(ORG_TXT),
    })


# ─────────────────────────────── chrome ────────────────────────────────────

@block("md.topbar")
def md_topbar(props):
    items = []
    for it in props.get("items", []):
        kids = []
        if it.get("icon"):
            kids.append(widget("icon", {
                "selected_icon": icon(it["icon"]), "size": slider(12),
                "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref(ORANGE)}))
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


@block("md.header")
def md_header(props):
    if props.get("logo"):
        brand = widget("theme-site-logo", {
            "align": "left", "image_size": "full",
            "width": slider(props.get("logo_width", 300)),
            "width_mobile": slider(220),
            "image": media(props["logo"], props.get("business", ""))})
    else:
        brand = container([
            widget("heading", {
                "title": props.get("business", "MEDINA"),
                "header_size": "div", "align": "left", "link": link("/"),
                "__typography__": typo_ref(T["wordmark"]),
            }, globals_={"title_color": color_ref(INK)}),
            widget("heading", {
                "title": props.get("tagline", ""), "header_size": "div",
                "align": "left", "__typography__": typo_ref(T["eyebrow"]),
            }, globals_={"title_color": color_ref(ORG_TXT)}),
        ], {"content_width": "full", "flex_direction": "column",
            "flex_gap": gap(3)})

    nav = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"),
        "layout": "horizontal", "align_items": "center",
        "pointer": "underline", "animation_line": "fade",
        "menu_space_between": slider(props.get("nav_gap", 22)),
        "toggle_align": "right",
        "__typography__": typo_ref(T["meta"]),
    }, globals_={
        "color_menu_item": color_ref(INK),
        "color_menu_item_hover": color_ref(ORG_TXT),
        "color_menu_item_active": color_ref(ORG_TXT),
        "pointer_color_menu_item_hover": color_ref(ORANGE),
        "pointer_color_menu_item_active": color_ref(ORANGE),
        "toggle_color": color_ref(INK),
    })

    actions = []
    if props.get("phone_display"):
        actions.append(_btn(props["phone_display"],
                            "tel:+1" + props.get("phone", ""), "ink",
                            "fas fa-phone"))
    if props.get("cta_label"):
        actions.append(_btn(props["cta_label"],
                            props.get("cta_url", "/contact-us/"), "orange"))

    row = _row([
        _col([brand], 30, extra={"flex_justify_content": "center"}),
        _col([nav], 40, extra={"flex_justify_content": "center",
                               "flex_align_items": "center"}),
        _col([_row(actions, 10, align="center", justify="flex-end",
                   extra={"flex_wrap": "wrap"})], 30,
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


@block("md.footer")
def md_footer(props):
    brand = []
    if props.get("logo"):
        brand.append(widget("image", {
            "image": media(props["logo"], props.get("business", "Logo")),
            "image_size": "full", "width": slider(260), "align": "left"}))
    else:
        brand.append(widget("heading", {
            "title": props.get("business", ""), "header_size": "div",
            "align": "left", "__typography__": typo_ref(T["wordmark"]),
        }, globals_={"title_color": color_ref(C["white"])}))
    if props.get("blurb"):
        brand.append(_text(props["blurb"], "left", on_dark=True, small=True))
    brand.append(_rays("left", scale=1.2))
    if props.get("socials"):
        brand.append(_row([widget("icon", {
            "selected_icon": icon(s.get("icon", "fab fa-facebook-f")),
            "size": slider(15), "align": "center", "view": "default",
            "link": link(s.get("url", "#")),
        }, globals_={"primary_color": color_ref(ORANGE)})
            for s in props["socials"]], 16, align="center",
            extra={"flex_wrap": "wrap", "flex_direction_mobile": "row"}))

    cols = props.get("columns", [])
    widths = _tracks([1.5] + [1] * len(cols), GUTTER)
    body = [_col(brand, widths[0], extra={"flex_gap": gap(14)})]
    for i, c in enumerate(cols):
        kids = [widget("heading", {
            "title": c.get("title", ""), "header_size": "div", "align": "left",
            "__typography__": typo_ref(T["eyebrow"]),
        }, globals_={"title_color": color_ref(ORANGE)})]
        for l in c.get("links", []):
            r = []
            if l.get("icon"):
                r.append(widget("icon", {
                    "selected_icon": icon(l["icon"]), "size": slider(12),
                    "align": "center", "view": "default",
                }, globals_={"primary_color": color_ref(ORANGE)}))
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
    }, globals_={"background_color": color_ref(INK_SOFT)})

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

@block("md.hero")
def md_hero(props):
    """Photograph under an ink scrim. Deep bottom padding: the trust strip
    overlaps up into it."""
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
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"),
                         "gradient"))
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
    sec = _sec([_row([col], GUTTER, align="center")], "ink",
               pad=dims(props.get("pad_top", 112), 0,
                        props.get("pad_bottom", 158), 0),
               anchor=props.get("anchor"),
               extra={"min_height": slider(props.get("height", 580))})
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
            "background_overlay_color"] = color_ref(INK)
    return sec


@block("md.trust")
def md_trust(props):
    """Four reassurance items pulled UP into the hero. This overlap is why
    the generic heroes are banned — neither reserves the space."""
    cols = props.get("columns", 4)
    w = _tracks([1] * cols, GUTTER)[0]
    cells = []
    for it in props.get("items", []):
        kids = [_row([
            _disc(it.get("icon", "fas fa-check"), 46),
            widget("heading", {
                "title": it.get("label", ""), "header_size": "div",
                "align": "left", "__typography__": typo_ref(T["h_small"]),
            }, globals_={"title_color": color_ref(INK)}),
        ], 13, align="center",
            extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})]
        if it.get("note"):
            kids.append(_text(it["note"], "left", small=True))
        cells.append(_card(kids, w, pad=dims(20, 20, 20, 20)))
    strip = _row(cells, GUTTER, align="stretch", extra={"flex_wrap": "wrap"})
    pull = props.get("pull")
    if pull:
        strip["settings"].update({"margin": dims(pull, 0, 0, 0),
                                  "margin_mobile": dims(-40, 0, 0, 0)})
    return _sec([strip], props.get("bg", "surface"),
                pad=dims(0, 0, 76, 0), anchor=props.get("anchor"))


@block("md.sectionhead")
def md_sectionhead(props):
    on_dark = _dark(props.get("bg", "surface"))
    align = props.get("align", "center")
    kids = _head_stack(props, align, on_dark)
    for p in props.get("paragraphs", []):
        kids.append(container([_text(p, align, on_dark=on_dark)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(props.get("width", 78), "%"),
            "width_mobile": slider(100, "%"),
            "margin": (dims(0, "auto", 0, "auto") if align == "center"
                       else dims(0, 0, 0, 0))}))
    return _sec(kids, props.get("bg", "surface"), anchor=props.get("anchor"),
                extra=({"flex_align_items": "center"}
                       if align == "center" else None))


@block("md.about")
def md_about(props):
    on_dark = _dark(props.get("bg", "surface"))
    left = _head_stack(props, "left", on_dark)
    for p in props.get("paragraphs", []):
        left.append(_text(p, "left", on_dark=on_dark))
    if props.get("ticks"):
        left.append(_ticks(props["ticks"], on_dark))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"),
                         "orange"))
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props.get("alt_url", "#"),
                         "outline"))
    if btns:
        left.append(_row(btns, 12, align="center",
                         extra={"flex_wrap": "wrap",
                                "padding": dims(8, 0, 0, 0)}))

    wl, wr = _tracks([1.06, 1], GUTTER)
    body = [_col(left, wl, extra={"flex_gap": gap(16)}),
            _col([_shot(props.get("image"), props.get("image_height", 440))],
                 wr, extra={"flex_justify_content": "center"})]
    if props.get("flip"):
        body.reverse()
    kids = [_row(body, GUTTER, align="center", extra={"flex_wrap": "wrap"})]

    cards = props.get("cards", [])
    if cards:
        w = _tracks([1] * min(len(cards), 4), GUTTER)[0]
        kids.append(_row([_card([
            _disc(c.get("icon", "fas fa-fire"), 48),
            widget("heading", {
                "title": c.get("title", ""), "header_size": "h3",
                "align": "left", "__typography__": typo_ref(T["h_small"]),
            }, globals_={"title_color": color_ref(INK)}),
            _text(c.get("text", ""), "left", small=True),
        ], w, pad=dims(24, 22, 26, 22)) for c in cards], GUTTER,
            align="stretch", extra={"flex_wrap": "wrap",
                                    "padding": dims(14, 0, 0, 0)}))
    return _sec(kids, props.get("bg", "surface"), anchor=props.get("anchor"))


@block("md.services")
def md_services(props):
    """Photo-led service cards. Radiant heating is invisible once it is in,
    so the photographs do the explaining that an icon cannot."""
    kids = _head_stack(props, props.get("align", "center"),
                       _dark(props.get("bg", "surface")))
    per = props.get("columns", 3)
    w = _tracks([1] * per, GUTTER)[0]
    cells = []
    for it in props.get("items", []):
        body = [_shot(it.get("image"), props.get("shot", 220))]
        if it.get("label"):
            body.append(widget("heading", {
                "title": it["label"], "header_size": "div", "align": "left",
                "__typography__": typo_ref(T["eyebrow"]),
            }, globals_={"title_color": color_ref(ORG_TXT)}))
        body.append(widget("heading", {
            "title": it.get("title", ""), "header_size": "h3", "align": "left",
            "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(INK)}))
        if it.get("text"):
            body.append(_text(it["text"], "left", small=True))
        if it.get("url"):
            body.append(_btn(it.get("link_label", "Learn More"), it["url"],
                             "outline"))
        cells.append(_card(body, w, pad=dims(0, 0, 26, 0),
                           extra={"flex_gap": gap(12), "overflow": "hidden"}))
    # No side padding on the card so the photo runs edge to edge; the text
    # below it takes its own inset.
    for c in cells:
        for ch in c["elements"][1:]:
            ch.setdefault("settings", {})
            ch["settings"]["_margin"] = dims(0, 24, 0, 24)
    kids.append(_row(cells, GUTTER, align="stretch",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "surface"), anchor=props.get("anchor"))


@block("md.compare")
def md_compare(props):
    """Radiant versus forced air, side by side. Most people landing here do
    not know what hydronic heating is, and no amount of selling works until
    that is fixed."""
    on_dark = _dark(props.get("bg", "white"))
    kids = _head_stack(props, "center", on_dark)
    cols = props.get("columns_data", [])
    w = _tracks([1] * max(len(cols), 1), GUTTER)[0]
    cells = []
    for i, c in enumerate(cols):
        head = [widget("heading", {
            "title": c.get("title", ""), "header_size": "h3", "align": "left",
            "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(INK)})]
        if c.get("note"):
            head.append(_text(c["note"], "left", small=True))
        rows = []
        for p in c.get("points", []):
            mark = widget("icon", {
                "selected_icon": icon(c.get("icon", "fas fa-check")),
                "size": slider(13), "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref(
                ORG_TXT if i == 0 else C["muted"])})
            rows.append(_row([mark, _text(p, "left", small=True)], 11,
                             align="flex-start",
                             extra={"flex_wrap": "nowrap",
                                    "flex_direction_mobile": "row",
                                    "padding": dims(5, 0, 5, 0)}))
        cells.append(_card(head + rows, w, pad=dims(28, 26, 30, 26),
                           extra={"flex_gap": gap(8)}))
    kids.append(_row(cells, GUTTER, align="stretch",
                     extra={"flex_wrap": "wrap"}))
    if props.get("footnote"):
        kids.append(container([_text(props["footnote"], "center",
                                     on_dark=on_dark, small=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(80, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"),
                extra={"flex_align_items": "center"})


@block("md.why")
def md_why(props):
    on_dark = _dark(props.get("bg", "surface"))
    kids = _head_stack(props, props.get("align", "center"), on_dark)
    per = props.get("columns", 3)
    w = _tracks([1] * per, GUTTER)[0]
    cells = []
    for it in props.get("items", []):
        cells.append(_card([
            _disc(it.get("icon", "fas fa-award"), 50),
            widget("heading", {
                "title": it.get("title", ""), "header_size": "h3",
                "align": "left", "__typography__": typo_ref(T["h_small"]),
            }, globals_={"title_color": color_ref(INK)}),
            _text(it.get("text", ""), "left", small=True),
        ], w, pad=dims(26, 24, 28, 24)))
    kids.append(_row(cells, GUTTER, align="stretch",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "surface"), anchor=props.get("anchor"))


@block("md.steps")
def md_steps(props):
    bg = props.get("bg", "ink")
    on_dark = _dark(bg)
    kids = _head_stack(props, props.get("align", "center"), on_dark)
    items = props.get("items", [])
    per = props.get("columns", min(len(items), 5)) or 1
    w = _tracks([1] * per, GUTTER)[0]
    cells = []
    for n, it in enumerate(items, 1):
        cells.append(_col([
            _numeral(it.get("n", n), on_dark),
            _rays("left", scale=0.85),
            widget("heading", {
                "title": it.get("title", ""), "header_size": "h3",
                "align": "left", "__typography__": typo_ref(T["h_small"]),
            }, globals_={"title_color": color_ref(
                C["white"] if on_dark else INK)}),
            _text(it.get("text", ""), "left", on_dark=on_dark, small=True),
        ], w, extra={"flex_gap": gap(10)}))
    kids.append(_row(cells, GUTTER, align="flex-start",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, bg, anchor=props.get("anchor"))


@block("md.galleryintro")
def md_galleryintro(props):
    """The standing notice above the gallery.

    The client asked for a Gallery page and has supplied no photographs, so
    the page says exactly what it is showing. This block exists so that
    disclosure is structural rather than a line somebody can quietly delete.
    """
    kids = _head_stack(props, "center", False)
    if props.get("notice"):
        kids.append(_card([
            _row([
                widget("icon", {
                    "selected_icon": icon("fas fa-circle-info"),
                    "size": slider(16), "align": "center", "view": "default",
                }, globals_={"primary_color": color_ref(ORG_TXT)}),
                _text(props["notice"], "left", small=True),
            ], 12, align="flex-start",
                extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"}),
        ], pad=dims(18, 22, 20, 22), hover=False,
            # Elementor stores dimension values as STRINGS, including in a
            # hand-built unlinked box like this one.
            extra={"border_width": {"unit": "px", "top": "1", "right": "1",
                                    "bottom": "1", "left": "4",
                                    "isLinked": ""}},
        ))
        kids[-1]["settings"].setdefault("__globals__", {})[
            "border_color"] = color_ref(ORANGE)
    return _sec(kids, props.get("bg", "surface"),
                pad=dims(84, 0, 20, 0), anchor=props.get("anchor"),
                extra={"flex_align_items": "center"})


@block("md.gallery")
def md_gallery(props):
    """The system guide. Each tile names the SYSTEM TYPE, not a job.

    Deliberately not captioned as the client's own work — none of these
    photographs are. The data shape takes real project photos with no
    rebuild: swap the image and rewrite the caption.
    """
    kids = _head_stack(props, props.get("align", "center"), False)
    items = props.get("items", [])
    per = props.get("columns", 3)
    w = _tracks([1] * per, GUTTER)[0]
    cells = []
    for it in items:
        body = [_shot(it.get("image"), it.get("height", 240))]
        if it.get("label"):
            body.append(widget("heading", {
                "title": it["label"], "header_size": "div", "align": "left",
                "__typography__": typo_ref(T["eyebrow"]),
            }, globals_={"title_color": color_ref(ORG_TXT)}))
        body.append(widget("heading", {
            "title": it.get("title", ""), "header_size": "h3", "align": "left",
            "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(INK)}))
        if it.get("text"):
            body.append(_text(it["text"], "left", small=True))
        cells.append(_card(body, w, pad=dims(0, 0, 24, 0),
                           extra={"flex_gap": gap(11), "overflow": "hidden"}))
    for c in cells:
        for ch in c["elements"][1:]:
            ch.setdefault("settings", {})
            ch["settings"]["_margin"] = dims(0, 22, 0, 22)
    kids.append(_row(cells, GUTTER, align="stretch",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "surface"), anchor=props.get("anchor"),
                pad=props.get("pad_top") and dims(20, 0, 94, 0) or None)


@block("md.prose")
def md_prose(props):
    on_dark = _dark(props.get("bg", "white"))
    left = _head_stack(props, "left", on_dark)
    for p in props.get("paragraphs", []):
        left.append(_text(p, "left", on_dark=on_dark))
    if props.get("ticks"):
        left.append(_ticks(props["ticks"], on_dark))
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


@block("md.checklist")
def md_checklist(props):
    on_dark = _dark(props.get("bg", "surface"))
    kids = _head_stack(props, props.get("align", "left"), on_dark)
    inner = _ticks(props.get("items", []), on_dark,
                   columns=props.get("columns", 2),
                   container_px=KIT_CONTAINER - 60)
    kids.append(_card([inner], pad=dims(30, 32, 32, 32), hover=False))
    return _sec(kids, props.get("bg", "surface"), anchor=props.get("anchor"))


@block("md.expect")
def md_expect(props):
    on_dark = _dark(props.get("bg", "white"))
    kids = _head_stack(props, props.get("align", "center"), on_dark)
    items = props.get("items", [])
    per = props.get("columns", min(len(items), 4)) or 1
    w = _tracks([1] * per, GUTTER)[0]
    cells = []
    for n, it in enumerate(items, 1):
        body = [_numeral(n, False, T["h_small"]), _rays("left", scale=0.7)]
        if isinstance(it, str):
            body.append(_text(it, "left", small=True))
        else:
            if it.get("title"):
                body.append(widget("heading", {
                    "title": it["title"], "header_size": "h3", "align": "left",
                    "__typography__": typo_ref(T["h_small"]),
                }, globals_={"title_color": color_ref(INK)}))
            if it.get("text"):
                body.append(_text(it["text"], "left", small=True))
        cells.append(_card(body, w, pad=dims(24, 22, 26, 22),
                           extra={"flex_gap": gap(9)}))
    kids.append(_row(cells, GUTTER, align="stretch",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("md.area")
def md_area(props):
    kids = [_eyebrow(props.get("eyebrow", "Service Area"), "center")]
    if props.get("title"):
        kids.append(_h(props["title"], "h2", T["h_medium"], "center"))
    for p in props.get("paragraphs", []):
        kids.append(container([_text(p, "center")], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(74, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    towns = props.get("towns", [])
    if towns:
        chips = [container([widget("heading", {
            "title": t, "header_size": "div", "align": "center",
            "__typography__": typo_ref(T["meta"]),
        }, globals_={"title_color": color_ref(INK)})], {
            "content_width": "full", "flex_direction": "column",
            "padding": dims(10, 20, 10, 20), "border_radius": box(2),
            "border_border": "solid", "border_width": box(1),
            "background_background": "classic", **SHADOW,
        }, globals_={"background_color": color_ref(C["white"]),
                     "border_color": color_ref(C["border"])}) for t in towns]
        kids.append(_row(chips, 12, align="center", justify="center",
                         extra={"flex_wrap": "wrap"}))
    if props.get("cta_label"):
        kids.append(_row([_btn(props["cta_label"],
                               props.get("cta_url", "#"), "orange")], 12,
                         align="center", justify="center",
                         extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "surface"), anchor=props.get("anchor"),
                extra={"flex_align_items": "center"})


@block("md.faq")
def md_faq(props):
    kids = _head_stack(props, props.get("align", "center"), False)
    kids.append(_faq(props.get("items", [])))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("md.contactcards")
def md_contactcards(props):
    items = props.get("items", [])
    per = props.get("columns", min(len(items), 3)) or 1
    w = _tracks([1] * per, GUTTER)[0]
    cells = []
    for it in items:
        body = [_disc(it.get("icon", "fas fa-phone"), 52),
                widget("heading", {
                    "title": it.get("label", ""), "header_size": "div",
                    "align": "left", "__typography__": typo_ref(T["eyebrow"]),
                }, globals_={"title_color": color_ref(ORG_TXT)})]
        val = widget("heading", {
            "title": it.get("value", ""), "header_size": "h3", "align": "left",
            "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(INK)})
        if it.get("href"):
            val["settings"]["link"] = link(it["href"])
        body.append(val)
        if it.get("note"):
            body.append(_text(it["note"], "left", small=True))
        cells.append(_card(body, w, pad=dims(26, 24, 28, 24)))
    return _sec([_row(cells, GUTTER, align="stretch",
                      extra={"flex_wrap": "wrap"})],
                props.get("bg", "white"), anchor=props.get("anchor"))


@block("md.form")
def md_form(props):
    on_dark = _dark(props.get("bg", "surface"))
    head = _head_stack(props, "left", on_dark)
    f = dict(props.get("form", {}))
    card = _card(head + [_form_widget(f)], pad=dims(34, 34, 36, 34),
                 lifted=True, hover=False)
    side = props.get("side")
    if not side:
        return _sec([card], props.get("bg", "surface"),
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
                props.get("bg", "surface"), anchor=props.get("anchor", "form"))


@block("md.cta")
def md_cta(props):
    kids = [_rays("center", scale=1.4)]
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], "center", on_dark=True,
                             rule=False))
    if props.get("title"):
        kids.append(_h(props["title"], props.get("tag", "h2"), T["h_medium"],
                       "center", on_dark=True))
    if props.get("intro"):
        kids.append(container([_text(props["intro"], "center", on_dark=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(72, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"),
                         "gradient"))
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props.get("alt_url", "#"),
                         "ghost", "fas fa-phone"))
    if btns:
        kids.append(_row(btns, 12, align="center", justify="center",
                         extra={"flex_wrap": "wrap",
                                "flex_direction_mobile": "column",
                                "padding": dims(10, 0, 0, 0)}))
    sec = _sec(kids, props.get("bg", "ink"), pad=dims(86, 0, 86, 0),
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
            "background_overlay_color"] = color_ref(INK)
    return sec


@block("md.pagehero")
def md_pagehero(props):
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
        }, globals_={"title_color": color_ref(ORANGE)}))
    if props.get("intro"):
        kids.append(container([_text(props["intro"], "left", on_dark=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(86, "%"), "width_mobile": slider(100, "%")}))
    sec = _sec([_row([_col(kids, 72, extra={"flex_gap": gap(16)})],
                     GUTTER, align="center")],
               "ink", pad=dims(96, 0, 96, 0), anchor=props.get("anchor"),
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
            "background_overlay_color"] = color_ref(INK)
    return sec
