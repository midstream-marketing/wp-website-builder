"""
blocks_stt.py — Scottsdale Tree Trimmers, Scottsdale AZ.

A redesign of the client's existing WordPress site onto the Gardiz template,
which is the theme behind oakforgelandscapes.co.uk — the site the client
said they liked.

THREE INPUTS, ALL READ RATHER THAN GUESSED:

  1. The supplied Gardiz template kit. Its `global.json` gave the exact
     palette and type: Green #2A7D2E, Black #0B3D2C, Background #E6F1E1,
     Background light #245142, Montserrat 700/600 over Open Sans 400.
  2. oakforgelandscapes.co.uk, rendered and captured. This matters, because
     Oak Forge is NOT stock Gardiz: dark header rather than white, a
     full-bleed green hero rather than a photo card with floating chips, no
     team, no pricing, no testimonials, plus an Areas We Serve section — and
     a pill eyebrow with a small tree glyph above every single section,
     which is the most recognisable thing about it. Where the two disagree,
     Oak Forge wins.
  3. The client's own live site, for 33,186 words of content, 122
     photographs and the phone number.

THE GOVERNING CONSTRAINT IS NOT AESTHETIC. The client ranks Page 1 Position
2 and believes it is the long-form articles on their homepage doing it.
Measuring agreed: 6,517 words on the homepage, 7,757 on /tree-removal. So
`stt.article` carries that content across VERBATIM — heading text and order
preserved exactly, body HTML preserved including inline links and lists —
and it is a required device. Where design and preserved content conflict,
the content wins. The design is replaceable; a position-2 ranking is not.

TWO CONTRAST DEFECTS IN THE TEMPLATE'S OWN PALETTE, corrected here:

    #8B827D  the template's body text   3.76:1 on white   FAILS
    #716B67  used instead               5.25:1 on white   ✓
    #2A7D2E  brand green on #0B3D2C     2.37:1            FAILS
    #68AE46  used on dark bands         4.50:1            ✓

Matching a reference does not extend to copying a legibility bug.

    stt.header       dark bar, logo tile, nav, outlined pill
    stt.hero         full-bleed green scrim, ROUNDED BOTTOM corners
    stt.features     four bordered cards overlapping the hero
    stt.sectionhead  pill eyebrow + heading + copy
    stt.about        offset-block image, tick list, circular badge
    stt.services     notched numbered photo cards      ← signature
    stt.ctastrip     dark green strip, heading | rule | button
    stt.areas        map-pin town list + offset image
    stt.steps        dashed-ring numbered process nodes
    stt.gallery      the client's own photographs
    stt.posts        article cards with a date badge
    stt.contact      split copy/photo + bordered form card
    stt.contactcards phone / email / area / hours
    stt.form         standalone form on a raised card
    stt.faq          accordion, first answer open
    stt.prose        copy beside a photograph
    stt.checklist    ticked list on a card
    stt.articleintro the pill eyebrow above preserved content
    stt.article      THE PRESERVED CONTENT RENDERER    ← governing device
    stt.pagehero     inner page header
    stt.footer       near-black, logo tile, tree-glyph columns
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

DEEP = "primary"        # #0B3D2C
MID = "secondary"       # #245142
GREEN = "accent"        # #2A7D2E
GRN_TXT = "sttgrn1"     # #287C2A — small green text on the pale band
LIME = "sttlim1"        # #68AE46 — green that reads ON the dark bands
NEAR = "sttdrk1"        # #0A1A14 — header and footer
ON_DARK = "sttond1"     # #CAD5D1

ST_PAD = dims(96, 0, 96, 0)
ST_PAD_T = dims(70, 24, 70, 24)
ST_PAD_M = dims(54, 18, 54, 18)
R_CARD = box(10)
R_PILL = box(999)
GUTTER = 24
TREE = "fas fa-tree"

SHADOW = {
    "box_shadow_box_shadow_type": "yes",
    "box_shadow_box_shadow": {"horizontal": 0, "vertical": 8, "blur": 24,
                              "spread": -8, "color": "rgba(11, 61, 44, 0.14)"},
}
SHADOW_HOVER = {
    "box_shadow_hover_box_shadow_type": "yes",
    "box_shadow_hover_box_shadow": {"horizontal": 0, "vertical": 18,
                                    "blur": 44, "spread": -12,
                                    "color": "rgba(11, 61, 44, 0.26)"},
}
SHADOW_LIFTED = {
    "box_shadow_box_shadow_type": "yes",
    "box_shadow_box_shadow": {"horizontal": 0, "vertical": 24, "blur": 60,
                              "spread": -16, "color": "rgba(11, 61, 44, 0.28)"},
}


# ───────────────────────── the signature eyebrow ───────────────────────────

def _pill(text, align="left", on_dark=False):
    """The white rounded pill with a tree glyph that sits above every
    section on the reference. The single most recognisable device there."""
    kids = [
        widget("icon", {
            "selected_icon": icon(TREE), "size": slider(13),
            "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref(DEEP if not on_dark
                                                else DEEP)}),
        widget("heading", {
            "title": text, "header_size": "div", "align": "left",
            "__typography__": typo_ref(T["eyebrow"]),
        }, globals_={"title_color": color_ref(DEEP)}),
    ]
    pill = container([_row(kids, 9, align="center",
                           extra={"flex_wrap": "nowrap",
                                  "flex_direction_mobile": "row"})], {
        "content_width": "full", "flex_direction": "column",
        "width": slider(0),  # shrink-to-fit
        "padding": dims(9, 18, 9, 18),
        "border_radius": R_PILL,
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["white"]),
                 "border_color": color_ref(C["border"])})
    # width:0 with auto flex-basis is unreliable; wrap and align instead.
    pill["settings"].pop("width", None)
    return container([pill], {
        "content_width": "full", "flex_direction": "row",
        "flex_align_items": "center",
        "flex_justify_content": "center" if align == "center" else "flex-start",
    })


# ───────────────────────────────── helpers ─────────────────────────────────

def _sec(children, bg="white", pad=None, anchor=None, extra=None):
    grounds = {"white": C["white"], "pale": C["surface"], "deep": DEEP,
               "near": NEAR, "mid": MID}
    s = {
        "content_width": "boxed",
        "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "flex_gap": gap(32),
        "padding": pad or ST_PAD,
        "padding_tablet": ST_PAD_T,
        "padding_mobile": ST_PAD_M,
        "background_background": "classic",
    }
    if anchor:
        s["_element_id"] = anchor
    if extra:
        s.update(extra)
    return container(children, s, globals_={
        "background_color": color_ref(grounds.get(bg, C["white"]))})


def _dark(bg):
    return bg in ("deep", "near", "mid")


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
        tone or (C["white"] if on_dark else DEEP))})


def _btn(label, href, style="dark", icon_name=None):
    """Four buttons, all fully rounded pills — the template's shape.

        dark          near-black pill, white label, trailing arrow (primary)
        green         #2A7D2E fill, white label (5.16:1)
        outline_light white hairline on dark grounds and photographs
        outline_dark  hairline pill on light grounds
    """
    b = _button(label, href, "primary", icon_name or "")
    b["settings"].update({
        "border_radius": R_PILL,
        "text_padding": dims(16, 30, 16, 30),
        "__typography__": typo_ref(T["meta"]),
        "hover_animation": "float",
        "button_box_shadow_box_shadow_type": "yes",
        "button_box_shadow_box_shadow": {
            "horizontal": 0, "vertical": 6, "blur": 18, "spread": -6,
            "color": "rgba(11, 61, 44, 0.34)"},
    })
    g = b["settings"].setdefault("__globals__", {})
    if style == "green":
        g.update({"background_color": color_ref(GREEN),
                  "border_color": color_ref(GREEN),
                  "button_text_color": color_ref(C["white"]),
                  "button_background_hover_color": color_ref(DEEP),
                  "button_hover_border_color": color_ref(DEEP),
                  "hover_color": color_ref(C["white"])})
    elif style == "outline_light":
        b["settings"].update({"border_border": "solid", "border_width": box(2)})
        g.update({"background_color": color_ref(C["transparent"]),
                  "border_color": color_ref(C["white"]),
                  "button_text_color": color_ref(C["white"]),
                  "button_background_hover_color": color_ref(C["white"]),
                  "button_hover_border_color": color_ref(C["white"]),
                  "hover_color": color_ref(DEEP)})
    elif style == "outline_dark":
        b["settings"].update({"border_border": "solid", "border_width": box(1)})
        g.update({"background_color": color_ref(C["transparent"]),
                  "border_color": color_ref(C["border"]),
                  "button_text_color": color_ref(DEEP),
                  "button_background_hover_color": color_ref(DEEP),
                  "button_hover_border_color": color_ref(DEEP),
                  "hover_color": color_ref(C["white"])})
    else:
        g.update({"background_color": color_ref(NEAR),
                  "border_color": color_ref(NEAR),
                  "button_text_color": color_ref(C["white"]),
                  "button_background_hover_color": color_ref(GREEN),
                  "button_hover_border_color": color_ref(GREEN),
                  "hover_color": color_ref(C["white"])})
    return b


def _ticks(items, on_dark=False, columns=1, container_px=KIT_CONTAINER,
           glyph="fas fa-check"):
    rows = []
    for t in items:
        mark = widget("icon", {
            "selected_icon": icon(glyph), "size": slider(13),
            "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref(LIME if on_dark else GREEN)})
        rows.append(_row([mark, _text(t, "left", on_dark=on_dark, small=True)],
                         11, align="flex-start",
                         extra={"flex_wrap": "nowrap",
                                "flex_direction_mobile": "row",
                                "padding": dims(5, 0, 5, 0)}))
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


def _offset_image(image, inset=None, height=420, flip=False):
    """A photograph with a solid green block offset behind it, and
    optionally a second smaller image overlapping the corner. Oak Forge uses
    this on About and on Areas We Serve."""
    slab = container([], {
        "content_width": "full", "min_height": slider(height - 40),
        "width": slider(88, "%"), "border_radius": R_CARD,
        "margin": dims(26, 0, -(height - 66), 26 if not flip else 0),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(GREEN)})
    kids = [slab, _shot(image, height)]
    if inset:
        small = widget("image", {
            "image": media(inset["url"], inset.get("alt", "")),
            "image_size": "full", "width": slider(54, "%"),
            "height": slider(round(height * 0.38)), "object-fit": "cover",
            "align": "right", "image_border_radius": box(8),
            "_margin": dims(-round(height * 0.20), 0, 0, 0),
        })
        kids.append(small)
    return container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(0), "overflow": "visible"})


def _numbadge(n):
    """The dark numbered badge notched into the top-right of a service card.

    Flush to the card edge with only the inner corner rounded, which is what
    makes it read as notched into the corner rather than floated on top.
    """
    return container([widget("heading", {
        "title": "%02d" % n, "header_size": "div", "align": "center",
        "__typography__": typo_ref(T["h_small"]),
    }, globals_={"title_color": color_ref(C["white"])})], {
        "content_width": "full", "flex_direction": "column",
        "flex_justify_content": "center", "flex_align_items": "center",
        "width": slider(64), "min_height": slider(60), "_flex_shrink": "0",
        "border_radius": {"unit": "px", "top": "0", "right": "10",
                          "bottom": "10", "left": "0", "isLinked": ""},
        "background_background": "classic",
    }, globals_={"background_color": color_ref(NEAR)})


def _ring(n, icon_name, on_dark=False):
    """A numbered node with a dashed ring, from the work-process section.

    The reference draws a dashed CURVE between nodes using a background
    graphic. A curve cannot be built from containers without CSS, so the
    dashed ring carries the motif per node instead — recorded in
    design-spec.json rather than quietly dropped.
    """
    inner = container([widget("icon", {
        "selected_icon": icon(icon_name), "size": slider(26),
        "align": "center", "view": "default",
    }, globals_={"primary_color": color_ref(LIME if on_dark else GREEN)})], {
        "content_width": "full", "flex_direction": "column",
        "flex_justify_content": "center", "flex_align_items": "center",
        "width": slider(96), "min_height": slider(96), "_flex_shrink": "0",
        "border_radius": box(999),
        "border_border": "dashed", "border_width": box(2),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(
        C["transparent"] if on_dark else C["white"]),
        "border_color": color_ref(LIME if on_dark else GREEN)})
    num = container([widget("heading", {
        "title": "%02d" % n, "header_size": "div", "align": "center",
        "__typography__": typo_ref(T["meta"]),
    }, globals_={"title_color": color_ref(C["white"])})], {
        "content_width": "full", "flex_direction": "column",
        "flex_justify_content": "center", "flex_align_items": "center",
        "width": slider(38), "min_height": slider(38), "_flex_shrink": "0",
        "border_radius": box(999), "background_background": "classic",
        "margin": dims(-24, 0, 0, 58),
    }, globals_={"background_color": color_ref(GREEN)})
    return container([inner, num], {
        "content_width": "full", "flex_direction": "column",
        "flex_align_items": "center", "flex_gap": gap(0)})


def _disc(icon_name, size=56, tone=None, on_dark=False):
    return container([widget("icon", {
        "selected_icon": icon(icon_name), "size": slider(round(size * 0.40)),
        "align": "center", "view": "default",
    }, globals_={"primary_color": color_ref(
        LIME if on_dark else C["white"])})], {
        "content_width": "full", "flex_direction": "column",
        "flex_justify_content": "center", "flex_align_items": "center",
        "width": slider(size), "min_height": slider(size), "_flex_shrink": "0",
        "border_radius": box(999), "background_background": "classic",
    }, globals_={"background_color": color_ref(tone or NEAR)})


def _head_stack(props, align="center", on_dark=False):
    kids = []
    if props.get("eyebrow"):
        kids.append(_pill(props["eyebrow"], align, on_dark))
    if props.get("title"):
        kids.append(_h(props["title"], props.get("tag", "h2"),
                       T["h_medium"], align, on_dark))
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
        "flex_gap": gap(16),
        "flex_align_items": "center" if align == "center" else "flex-start"})]


def _form_widget(f, on_pale=False):
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
        "field_border_radius": box(6), "field_border_width": box(1),
        "button_border_radius": box(8),
    }, globals_={
        # `button_background_color` IS correct on a FORM widget. It is not a
        # control on a Button widget, which is why _btn uses
        # `background_color` instead.
        "button_background_color": color_ref(GREEN),
        "button_text_color": color_ref(C["white"]),
        "button_background_hover_color": color_ref(DEEP),
        "button_hover_color": color_ref(C["white"]),
        "field_background_color": color_ref(C["white"]),
        "field_text_color": color_ref(C["ink_primary"]),
        "field_border_color": color_ref(C["border"]),
        "label_color": color_ref(DEEP),
        "mark_required_color": color_ref(GREEN),
    })


# ─────────────────────────────── chrome ────────────────────────────────────

@block("stt.header")
def stt_header(props):
    """Dark bar with the logo in a tile — Oak Forge, not stock Gardiz's
    white header."""
    if props.get("logo"):
        brand = widget("theme-site-logo", {
            "align": "left", "image_size": "full",
            "width": slider(props.get("logo_width", 92)),
            "image": media(props["logo"], props.get("business", ""))})
    else:
        brand = widget("heading", {
            "title": props.get("business", "Scottsdale Tree Trimmers"),
            "header_size": "div", "align": "left", "link": link("/"),
            "__typography__": typo_ref(T["wordmark"]),
        }, globals_={"title_color": color_ref(C["white"])})

    nav = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"),
        "layout": "horizontal", "align_items": "center",
        "pointer": "underline", "animation_line": "fade",
        "menu_space_between": slider(props.get("nav_gap", 24)),
        "toggle_align": "right",
        "__typography__": typo_ref(T["meta"]),
    }, globals_={
        "color_menu_item": color_ref(C["white"]),
        "color_menu_item_hover": color_ref(LIME),
        "color_menu_item_active": color_ref(LIME),
        "pointer_color_menu_item_hover": color_ref(LIME),
        "pointer_color_menu_item_active": color_ref(LIME),
        "toggle_color": color_ref(C["white"]),
    })

    actions = []
    if props.get("phone_display"):
        actions.append(_btn(props["phone_display"],
                            "tel:+1" + props.get("phone", ""),
                            "outline_light", "fas fa-phone"))
    if props.get("cta_label"):
        actions.append(_btn(props["cta_label"],
                            props.get("cta_url", "/book-an-appointment/"),
                            "outline_light"))

    row = _row([
        _col([brand], 22, extra={"flex_justify_content": "center"}),
        _col([nav], 48, extra={"flex_justify_content": "center",
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
        "padding": dims(12, 0, 12, 0),
        "padding_mobile": dims(10, 14, 10, 14),
        "background_background": "classic",
        "sticky": "top", "sticky_on": ["desktop", "tablet", "mobile"],
        "sticky_offset": 0,
    }, globals_={"background_color": color_ref(NEAR)})


@block("stt.footer")
def stt_footer(props):
    brand = []
    if props.get("logo"):
        brand.append(widget("image", {
            "image": media(props["logo"], props.get("business", "Logo")),
            "image_size": "full", "width": slider(110), "align": "left"}))
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
            mark = widget("icon", {
                "selected_icon": icon(l.get("icon", TREE)), "size": slider(11),
                "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref(LIME)})
            lab = widget("heading", {
                "title": l.get("label", ""), "header_size": "div",
                "align": "left", "__typography__": typo_ref(T["body_small"]),
            }, globals_={"title_color": color_ref(ON_DARK)})
            if l.get("url"):
                lab["settings"]["link"] = link(l["url"])
            kids.append(_row([mark, lab], 9, align="flex-start",
                             extra={"flex_wrap": "nowrap",
                                    "flex_direction_mobile": "row",
                                    "padding": dims(4, 0, 4, 0)}))
        body.append(_col(kids, widths[i + 1], extra={"flex_gap": gap(7)}))

    rule = container([], {
        "content_width": "full", "min_height": slider(1),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(MID)})

    return container([
        _row(body, GUTTER, align="flex-start", extra={"flex_wrap": "wrap"}),
        rule,
        widget("heading", {
            "title": props.get("copyright", ""), "header_size": "div",
            "align": "center", "__typography__": typo_ref(T["body_small"]),
        }, globals_={"title_color": color_ref(ON_DARK)}),
    ], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column", "flex_gap": gap(30),
        "padding": dims(78, 0, 34, 0),
        "padding_mobile": dims(54, 18, 28, 18),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(NEAR)})


# ─────────────────────────────── sections ──────────────────────────────────

@block("stt.hero")
def stt_hero(props):
    """Full-bleed photograph under a heavy deep-green scrim, with ROUNDED
    BOTTOM CORNERS and white beneath — the Oak Forge hero, not the Gardiz
    photo-card-with-floating-chips. Deep bottom padding leaves room for the
    feature strip to overlap up into it."""
    kids = []
    if props.get("eyebrow"):
        kids.append(_pill(props["eyebrow"], "left"))
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
                         "dark"))
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props.get("alt_url", "#"),
                         "outline_light", "fas fa-phone"))
    if btns:
        kids.append(_row(btns, 12, align="center",
                         extra={"flex_wrap": "wrap",
                                "flex_direction_mobile": "column",
                                "padding": dims(12, 0, 0, 0)}))

    col = _col(kids, props.get("width", 62), extra={"flex_gap": gap(22)})
    sec = _sec([_row([col], GUTTER, align="center")], "deep",
               pad=dims(props.get("pad_top", 120), 0,
                        props.get("pad_bottom", 164), 0),
               anchor=props.get("anchor"),
               extra={"min_height": slider(props.get("height", 620)),
                      "border_radius": {"unit": "px", "top": "0",
                                        "right": "0", "bottom": "36",
                                        "left": "36", "isLinked": ""}})
    img = props.get("image")
    if img and img.get("url"):
        sec["settings"].update({
            "background_image": media(img["url"], img.get("alt", "")),
            "background_position": props.get("position", "center center"),
            "background_size": "cover", "background_repeat": "no-repeat",
            "background_overlay_background": "classic",
            "background_overlay_opacity": slider(props.get("overlay", 0.80)),
        })
        sec["settings"].setdefault("__globals__", {})[
            "background_overlay_color"] = color_ref(DEEP)
    return sec


@block("stt.features")
def stt_features(props):
    """Four bordered cards sitting across the boundary where the hero ends."""
    cols = props.get("columns", 4)
    w = _tracks([1] * cols, GUTTER)[0]
    cells = []
    for it in props.get("items", []):
        cells.append(_card([
            widget("icon", {
                "selected_icon": icon(it.get("icon", TREE)), "size": slider(34),
                "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref(GREEN)}),
            widget("heading", {
                "title": it.get("title", ""), "header_size": "h3",
                "align": "center", "__typography__": typo_ref(T["h_small"]),
            }, globals_={"title_color": color_ref(DEEP)}),
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


@block("stt.sectionhead")
def stt_sectionhead(props):
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
    if props.get("cta_label"):
        kids.append(_row([_btn(props["cta_label"],
                               props.get("cta_url", "#"), "dark")], 12,
                         align="center",
                         justify="center" if align == "center" else "flex-start",
                         extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"),
                pad=props.get("tight") and dims(70, 0, 40, 0) or None,
                extra=({"flex_align_items": "center"}
                       if align == "center" else None))


@block("stt.about")
def stt_about(props):
    on_dark = _dark(props.get("bg", "white"))
    right = _head_stack(props, "left", on_dark)
    for p in props.get("paragraphs", []):
        right.append(_text(p, "left", on_dark=on_dark))
    if props.get("ticks_title"):
        right.append(_row([
            _disc(props.get("ticks_icon", "fas fa-seedling"), 52,
                  on_dark=on_dark),
            widget("heading", {
                "title": props["ticks_title"], "header_size": "h3",
                "align": "left", "__typography__": typo_ref(T["h_small"]),
            }, globals_={"title_color": color_ref(
                C["white"] if on_dark else DEEP)}),
        ], 14, align="center",
            extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row",
                   "padding": dims(8, 0, 0, 0)}))
    if props.get("ticks"):
        right.append(_ticks(props["ticks"], on_dark,
                            columns=props.get("tick_columns", 1),
                            container_px=620))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"),
                         "dark"))
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props.get("alt_url", "#"),
                         "outline_dark", "fas fa-phone"))
    if btns:
        right.append(_row(btns, 12, align="center",
                          extra={"flex_wrap": "wrap",
                                 "padding": dims(10, 0, 0, 0)}))

    wl, wr = _tracks([1, 1.08], GUTTER)
    left = _offset_image(props.get("image"), props.get("inset"),
                         props.get("image_height", 440),
                         flip=props.get("flip", False))
    body = [_col([left], wl), _col(right, wr, extra={"flex_gap": gap(16)})]
    if props.get("flip"):
        body.reverse()
    return _sec([_row(body, GUTTER, align="center",
                      extra={"flex_wrap": "wrap"})],
                props.get("bg", "white"), anchor=props.get("anchor"))


@block("stt.services")
def stt_services(props):
    """The signature: a green line icon top-left, a dark numbered badge
    notched into the top-right corner flush with the edge, title, body, and
    a photograph filling the bottom of the card edge to edge."""
    kids = _head_stack(props, props.get("align", "center"),
                       _dark(props.get("bg", "pale")))
    per = props.get("columns", 3)
    w = _tracks([1] * per, GUTTER)[0]
    cells = []
    for n, it in enumerate(props.get("items", []), props.get("start", 1)):
        head = _row([
            widget("icon", {
                "selected_icon": icon(it.get("icon", TREE)), "size": slider(34),
                "align": "left", "view": "default",
            }, globals_={"primary_color": color_ref(GREEN)}),
            _numbadge(n),
        ], 10, align="flex-start", justify="space-between",
            extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})
        title = widget("heading", {
            "title": it.get("title", ""), "header_size": "h3", "align": "left",
            "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(DEEP)})
        body = [head, title]
        if it.get("text"):
            body.append(_text(it["text"], "left", small=True))
        if it.get("url"):
            body.append(_btn(it.get("link_label", "Read More"), it["url"],
                             "outline_dark"))
        body.append(_shot(it.get("image"), props.get("shot", 230),
                          radius=box(0)))
        card = _card(body, w, pad=dims(0, 0, 0, 0),
                     extra={"flex_gap": gap(12), "overflow": "hidden"})
        # The icon row is flush to the top-right so the badge notches into
        # the corner; everything else takes its own inset.
        head["settings"]["_margin"] = dims(0, 0, 0, 24)
        for ch in card["elements"][1:-1]:
            ch.setdefault("settings", {})
            ch["settings"]["_margin"] = dims(0, 24, 0, 24)
        cells.append(card)
    kids.append(_row(cells, GUTTER, align="stretch",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "pale"), anchor=props.get("anchor"))


@block("stt.ctastrip")
def stt_ctastrip(props):
    """Deep green strip, hairline border, heading left, vertical rule,
    outlined pill right."""
    left = widget("heading", {
        "title": props.get("title", ""), "header_size": "h2", "align": "left",
        "__typography__": typo_ref(T["h_small"]),
    }, globals_={"title_color": color_ref(C["white"])})
    rule = container([], {
        "content_width": "full", "width": slider(1), "min_height": slider(56),
        "_flex_shrink": "0", "background_background": "classic",
    }, globals_={"background_color": color_ref(LIME)})
    btn = _btn(props.get("cta_label", "Get A Quote"),
               props.get("cta_url", "#"), "outline_light")
    inner = container([_row([
        _col([left], 56, extra={"flex_justify_content": "center"}),
        _col([rule], 4, extra={"flex_align_items": "center",
                               "flex_justify_content": "center"}),
        _col([_row([btn], 10, align="center", justify="flex-end",
                   extra={"flex_wrap": "wrap"})], 40,
             extra={"flex_justify_content": "center"}),
    ], GUTTER, align="center",
        extra={"flex_wrap": "nowrap", "flex_wrap_tablet": "wrap"})], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(38, 40, 38, 40),
        "padding_mobile": dims(28, 20, 28, 20),
        "border_radius": R_CARD,
        "border_border": "solid", "border_width": box(2),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(DEEP),
                 "border_color": color_ref(GREEN)})
    return _sec([inner], props.get("bg", "pale"),
                pad=dims(0, 0, 96, 0), anchor=props.get("anchor"))


@block("stt.areas")
def stt_areas(props):
    """Town list as green map-pin rows beside an offset-block image, closing
    with the natural-language 'searching for X near me' line."""
    left = _head_stack(props, "left", False)
    for p in props.get("paragraphs", []):
        left.append(_text(p, "left"))
    towns = props.get("towns", [])
    if towns:
        left.append(_ticks(towns, False,
                           columns=props.get("tick_columns", 2),
                           container_px=620,
                           glyph="fas fa-location-dot"))
    if props.get("nearme"):
        left.append(_text(props["nearme"], "left"))
    btns = []
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props.get("alt_url", "#"),
                         "dark", "fas fa-phone"))
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"),
                         "dark"))
    if btns:
        left.append(_row(btns, 12, align="center",
                         extra={"flex_wrap": "wrap",
                                "padding": dims(10, 0, 0, 0)}))
    wl, wr = _tracks([1.05, 1], GUTTER)
    body = [_col(left, wl, extra={"flex_gap": gap(16)}),
            _col([_offset_image(props.get("image"), None,
                                props.get("image_height", 420), flip=True)],
                 wr)]
    return _sec([_row(body, GUTTER, align="center",
                      extra={"flex_wrap": "wrap"})],
                props.get("bg", "white"), anchor=props.get("anchor"))


@block("stt.steps")
def stt_steps(props):
    bg = props.get("bg", "white")
    on_dark = _dark(bg)
    kids = _head_stack(props, props.get("align", "center"), on_dark)
    items = props.get("items", [])
    per = props.get("columns", min(len(items), 4)) or 1
    w = _tracks([1] * per, GUTTER)[0]
    cells = []
    for n, it in enumerate(items, 1):
        # Alternating vertical offset keeps the rhythm of the reference's
        # curved path without needing the curve itself.
        off = 0 if n % 2 else 34
        cells.append(_col([
            _ring(n, it.get("icon", TREE), on_dark),
            widget("heading", {
                "title": it.get("title", ""), "header_size": "h3",
                "align": "center", "__typography__": typo_ref(T["h_small"]),
            }, globals_={"title_color": color_ref(
                C["white"] if on_dark else DEEP)}),
            _text(it.get("text", ""), "center", on_dark=on_dark, small=True),
        ], w, extra={"flex_gap": gap(12), "flex_align_items": "center",
                     "margin": dims(off, 0, 0, 0),
                     "margin_mobile": dims(0, 0, 0, 0)}))
    kids.append(_row(cells, GUTTER, align="flex-start",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, bg, anchor=props.get("anchor"))


@block("stt.gallery")
def stt_gallery(props):
    """The client's own photographs. No stock anywhere in this kit."""
    kids = _head_stack(props, props.get("align", "center"), False)
    items = props.get("items", [])
    per = props.get("columns", 3)
    w = _tracks([1] * per, GUTTER)[0]
    cells = []
    for it in items:
        body = [_shot(it.get("image"), it.get("height", 240), radius=box(0))]
        if it.get("title"):
            body.append(widget("heading", {
                "title": it["title"], "header_size": "h3", "align": "left",
                "__typography__": typo_ref(T["h_small"]),
            }, globals_={"title_color": color_ref(DEEP)}))
        if it.get("text"):
            body.append(_text(it["text"], "left", small=True))
        card = _card(body, w, pad=dims(0, 0, 22, 0),
                     extra={"flex_gap": gap(11), "overflow": "hidden"})
        for ch in card["elements"][1:]:
            ch.setdefault("settings", {})
            ch["settings"]["_margin"] = dims(0, 22, 0, 22)
        cells.append(card)
    kids.append(_row(cells, GUTTER, align="stretch",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("stt.posts")
def stt_posts(props):
    """Article cards with a date badge — the Gardiz 'Latest News' device,
    kept even though Oak Forge has no blog, because this client's six real
    articles are part of what the brief is protecting."""
    kids = _head_stack(props, props.get("align", "center"),
                       _dark(props.get("bg", "white")))
    per = props.get("columns", 3)
    w = _tracks([1] * per, GUTTER)[0]
    cells = []
    for it in props.get("items", []):
        body = [_shot(it.get("image"), 210, radius=box(0))]
        if it.get("date"):
            body.append(container([widget("heading", {
                "title": it["date"], "header_size": "div", "align": "center",
                "__typography__": typo_ref(T["meta"]),
            }, globals_={"title_color": color_ref(C["white"])})], {
                "content_width": "full", "flex_direction": "column",
                "padding": dims(7, 14, 7, 14), "border_radius": box(6),
                "background_background": "classic",
                "margin": dims(-22, 0, 0, 22),
            }, globals_={"background_color": color_ref(GREEN)}))
        body.append(widget("heading", {
            "title": it.get("title", ""), "header_size": "h3", "align": "left",
            "__typography__": typo_ref(T["h_small"]),
            "link": link(it.get("url", "#")),
        }, globals_={"title_color": color_ref(DEEP)}))
        if it.get("text"):
            body.append(_text(it["text"], "left", small=True))
        if it.get("url"):
            body.append(_btn("Read Article", it["url"], "outline_dark"))
        card = _card(body, w, pad=dims(0, 0, 24, 0),
                     extra={"flex_gap": gap(10), "overflow": "hidden"})
        for ch in card["elements"][2:]:
            ch.setdefault("settings", {})
            ch["settings"]["_margin"] = dims(0, 22, 0, 22)
        cells.append(card)
    kids.append(_row(cells, GUTTER, align="stretch",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("stt.contact")
def stt_contact(props):
    """Copy, phone and a photograph on the left; a bordered form card with a
    service checklist on the right."""
    left = _head_stack(props, "left", False)
    for p in props.get("paragraphs", []):
        left.append(_text(p, "left"))
    if props.get("phone_display"):
        left.append(_row([
            widget("icon", {
                "selected_icon": icon("fas fa-phone"), "size": slider(15),
                "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref(GREEN)}),
            widget("heading", {
                "title": props["phone_display"], "header_size": "div",
                "align": "left", "__typography__": typo_ref(T["h_small"]),
                "link": link(props.get("phone_href", "#")),
            }, globals_={"title_color": color_ref(DEEP)}),
        ], 11, align="center",
            extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"}))
    if props.get("ticks"):
        left.append(_ticks(props["ticks"], False))
    if props.get("image"):
        left.append(_shot(props["image"], props.get("image_height", 300)))

    f = dict(props.get("form", {}))
    card_kids = []
    if f.get("title"):
        card_kids.append(_h(f["title"], "h2", T["h_small"], "left"))
    card_kids.append(_form_widget(f))
    card = _card(card_kids, pad=dims(32, 32, 34, 32), hover=False,
                 lifted=True)
    wl, wr = _tracks([1, 1.05], GUTTER)
    return _sec([_row([_col(left, wl, extra={"flex_gap": gap(16)}),
                       _col([card], wr)], GUTTER, align="flex-start",
                      extra={"flex_wrap": "wrap"})],
                props.get("bg", "pale"), anchor=props.get("anchor", "contact"))


@block("stt.contactcards")
def stt_contactcards(props):
    items = props.get("items", [])
    per = props.get("columns", min(len(items), 4)) or 1
    w = _tracks([1] * per, GUTTER)[0]
    cells = []
    for it in items:
        body = [_disc(it.get("icon", "fas fa-phone"), 54, tone=GREEN),
                widget("heading", {
                    "title": it.get("label", ""), "header_size": "div",
                    "align": "left", "__typography__": typo_ref(T["eyebrow"]),
                }, globals_={"title_color": color_ref(GRN_TXT)})]
        val = widget("heading", {
            "title": it.get("value", ""), "header_size": "h3", "align": "left",
            "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(DEEP)})
        if it.get("href"):
            val["settings"]["link"] = link(it["href"])
        body.append(val)
        if it.get("note"):
            body.append(_text(it["note"], "left", small=True))
        cells.append(_card(body, w, pad=dims(26, 24, 28, 24)))
    return _sec([_row(cells, GUTTER, align="stretch",
                      extra={"flex_wrap": "wrap"})],
                props.get("bg", "white"), anchor=props.get("anchor"))


@block("stt.form")
def stt_form(props):
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
    if side.get("ticks"):
        skids.append(_ticks(side["ticks"], False))
    if side.get("image"):
        skids.append(_shot(side["image"], side.get("image_height", 260)))
    wl, wr = _tracks([1, 1.1], GUTTER)
    return _sec([_row([_col(skids, wl, extra={"flex_gap": gap(16)}),
                       _col([card], wr)], GUTTER, align="flex-start",
                      extra={"flex_wrap": "wrap"})],
                props.get("bg", "pale"), anchor=props.get("anchor", "form"))


@block("stt.faq")
def stt_faq(props):
    kids = _head_stack(props, props.get("align", "center"), False)
    kids.append(_faq(props.get("items", [])))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("stt.prose")
def stt_prose(props):
    on_dark = _dark(props.get("bg", "white"))
    left = _head_stack(props, "left", on_dark)
    for p in props.get("paragraphs", []):
        left.append(_text(p, "left", on_dark=on_dark))
    if props.get("ticks"):
        left.append(_ticks(props["ticks"], on_dark))
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


@block("stt.checklist")
def stt_checklist(props):
    on_dark = _dark(props.get("bg", "pale"))
    kids = _head_stack(props, props.get("align", "left"), on_dark)
    kids.append(_card([_ticks(props.get("items", []), on_dark,
                              columns=props.get("columns", 2),
                              container_px=KIT_CONTAINER - 64)],
                      pad=dims(30, 32, 32, 32), hover=False))
    return _sec(kids, props.get("bg", "pale"), anchor=props.get("anchor"))


# ──────────────────── the preserved-content renderer ───────────────────────

@block("stt.articleintro")
def stt_articleintro(props):
    """The pill eyebrow and heading that introduce the preserved content.

    Its own block so the boundary between the new designed page and the
    carried-over article content is explicit in the IR, and so the client
    can see exactly where their existing material begins.
    """
    kids = _head_stack(props, props.get("align", "center"), False)
    return _sec(kids, props.get("bg", "white"),
                pad=dims(86, 0, 10, 0), anchor=props.get("anchor", "more"),
                extra={"flex_align_items": "center"}
                if props.get("align", "center") == "center" else None)


@block("stt.article")
def stt_article(props):
    """THE GOVERNING DEVICE. Renders the client's existing page content.

    The client ranks Page 1 Position 2 and asked specifically to keep this
    material. So:

      - each source H2 becomes a real Elementor HEADING widget, with the
        text unchanged, keeping the outline Google reads intact;
      - the body of each section is passed through as RAW HTML in a
        text-editor widget, so inline links, lists, bold and the client's
        own <img> tags all survive exactly. Reflowing it to plain text
        would silently drop internal links the ranking depends on;
      - the column is held to a readable measure rather than running the
        full container width, because 6,500 words at 1240px is unreadable.

    Nothing here is rewritten, reordered or summarised.
    """
    on_dark = _dark(props.get("bg", "white"))
    kids = []
    for s in props.get("sections", []):
        if s.get("heading"):
            kids.append(widget("heading", {
                "title": s["heading"],
                "header_size": "h%d" % s.get("level", 2),
                "align": "left",
                "__typography__": typo_ref(T["h_small"]),
            }, globals_={"title_color": color_ref(
                C["white"] if on_dark else DEEP)}))
        if s.get("html"):
            kids.append(widget("text-editor", {
                "editor": s["html"], "align": "left",
            }, globals_={
                "text_color": color_ref(C["on_dark"] if on_dark else "text"),
                "typography_typography": typo_ref("text"),
            }))
    measure = container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(16),
        "width": slider(props.get("measure", 880)),
        "width_mobile": slider(100, "%"),
        "margin": dims(0, "auto", 0, "auto"),
    })
    return _sec([measure], props.get("bg", "white"),
                pad=dims(8, 0, 90, 0), anchor=props.get("anchor"))


@block("stt.pagehero")
def stt_pagehero(props):
    kids = []
    if props.get("eyebrow"):
        kids.append(_pill(props["eyebrow"], "left"))
    if props.get("title"):
        kids.append(_h(props["title"], props.get("tag", "h1"), T["h_large"],
                       "left", on_dark=True))
    if props.get("intro"):
        kids.append(container([_text(props["intro"], "left", on_dark=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(86, "%"), "width_mobile": slider(100, "%")}))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"),
                         "dark"))
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props.get("alt_url", "#"),
                         "outline_light", "fas fa-phone"))
    if btns:
        kids.append(_row(btns, 12, align="center",
                         extra={"flex_wrap": "wrap",
                                "padding": dims(8, 0, 0, 0)}))
    sec = _sec([_row([_col(kids, 70, extra={"flex_gap": gap(18)})],
                     GUTTER, align="center")],
               "deep", pad=dims(104, 0, 104, 0), anchor=props.get("anchor"),
               extra={"min_height": slider(props.get("height", 400)),
                      "border_radius": {"unit": "px", "top": "0",
                                        "right": "0", "bottom": "36",
                                        "left": "36", "isLinked": ""}})
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
            "background_overlay_color"] = color_ref(DEEP)
    return sec
