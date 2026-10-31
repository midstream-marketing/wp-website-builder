"""
blocks_ee.py — E&E Custom Renovation.

No reference site was named, so the design is anchored to the logo, which is
unusually prescriptive for a contractor mark:

  * It is PURE GREYSCALE. Measured saturation 0.00 in every colour bucket.
    So this family has no accent hue at all, and none is invented. The
    "accent" role is silver, and emphasis is carried by a brushed-chrome
    GRADIENT rather than by colour.
  * It carries two type voices — a high-contrast transitional serif (E&E) and
    a wide-tracked geometric sans (CUSTOM RENOVATION). Both are used, for the
    jobs the logo uses them for: serif for display headings, tracked sans caps
    for eyebrows and buttons.
  * Its highlights are white, so the mark washes out on light grounds
    (verified by compositing). The header and footer are therefore black
    because the logo requires it, not as a style preference.
  * It has one brand shape: the gable. Rather than redraw it, `ee.gable` uses
    the roof cropped straight out of the client's own logo file, so the motif
    on the page is literally their artwork.

The chrome gradient is the signature device and it is real, not a flat grey:
a linear sweep from #EDEFF1 to #8A9099 with a hard-ish midpoint, which is how
brushed metal reads. It appears in exactly three places — the primary button,
the hairline rules under eyebrows, and the section numerals — because chrome
everywhere is chrome nowhere.

    ee.topbar      thin black utility strip
    ee.header      black header, logo left, nav, chrome CTA
    ee.hero        photo + deep scrim, chrome eyebrow, serif display, buttons
    ee.gable       the logo's roof motif as a centred section mark
    ee.rule        a standalone chrome hairline divider
    ee.intro       eyebrow + chrome rule + serif heading + paragraphs
    ee.services    service cards: photo, silver caps label, serif title
    ee.split       photo one side, copy + ticks the other
    ee.process     numbered steps with chrome numerals
    ee.showcase    one project, large photo, caption block
    ee.statement   full-bleed dark band, one serif line, one button
    ee.faq         accordion, first answer open
    ee.detailcards small cards for contact details / service points
    ee.form        form card, chrome submit
    ee.map         embedded map
    ee.footer      black, four columns, chrome rule, legal bar
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

INK = "primary"            # #0B0B0C — the black ground
ELEV = "secondary"         # #16171A — raised black
SILVER = "accent"          # #C9CDD2 — the chrome midtone
CHROME_HI = "eechr01"      # #EDEFF1
CHROME_LO = "eechr02"      # #8A9099
SILVER_TXT = "eesil01"     # #AEB4BB — silver that passes on dark
GRAPHITE = "eegrp01"       # #24262B — cards and hairlines on dark

EE_PAD = dims(96, 0, 96, 0)
EE_PAD_T = dims(70, 24, 70, 24)
EE_PAD_M = dims(54, 18, 54, 18)
R_BTN = box(2)             # near-square: the logo's serif is architectural
R_CARD = box(4)
GUTTER = 26


# ─────────────────────────────── helpers ───────────────────────────────────

def _sec(children, bg="white", pad=None, anchor=None, extra=None):
    grounds = {"white": C["white"], "pale": C["surface"],
               "dark": INK, "elev": ELEV}
    s = {
        "content_width": "boxed",
        "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "flex_gap": gap(30),
        "padding": pad or EE_PAD,
        "padding_tablet": EE_PAD_T,
        "padding_mobile": EE_PAD_M,
        "background_background": "classic",
    }
    if anchor:
        s["_element_id"] = anchor
    if extra:
        s.update(extra)
    return container(children, s, globals_={
        "background_color": color_ref(grounds.get(bg, C["white"]))})


def _dark(bg):
    return bg in ("dark", "elev")


def _chrome(height=2, width_pct=None, angle=100):
    """The brushed-chrome hairline. A container with a real linear gradient,
    not a flat grey rule — this is the device the whole design turns on."""
    s = {
        "content_width": "full",
        "min_height": slider(height),
        "flex_direction": "column",
        "background_background": "gradient",
        "background_gradient_type": "linear",
        "background_gradient_angle": slider(angle, "deg"),
        "background_color_stop": slider(18, "%"),
        "background_color_b_stop": slider(82, "%"),
    }
    if width_pct:
        s.update({"width": slider(width_pct, "%"),
                  "width_mobile": slider(min(100, width_pct * 2), "%")})
    return container([], s, globals_={
        "background_color": color_ref(CHROME_HI),
        "background_color_b": color_ref(CHROME_LO)})


def _photo_ground(sec, image, position="center center", overlay=0.72):
    """Photograph behind a band under a deep black scrim. The scrim runs
    heavier here than on a colour-brand site (0.72 against a more usual 0.55)
    because every heading over it is a thin high-contrast serif, and thin
    serifs are the first thing a busy photograph destroys."""
    if not (image and image.get("url")):
        return sec
    sec["settings"].update({
        "background_image": media(image["url"], image.get("alt", "")),
        "background_position": position,
        "background_size": "cover",
        "background_repeat": "no-repeat",
        "background_overlay_background": "classic",
        "background_overlay_opacity": slider(overlay),
    })
    sec["settings"].setdefault("__globals__", {})[
        "background_overlay_color"] = color_ref(INK)
    return sec


def _h(text, size="h2", token=None, align="left", on_dark=False, color=None):
    """Title case, never caps. Setting a high-contrast serif in uppercase at
    display size throws away the thick/thin modulation the logo is built on."""
    return widget("heading", {
        "title": text, "header_size": size, "align": align,
        "__typography__": typo_ref(token or T["h_medium"]),
    }, globals_={"title_color": color_ref(
        color or (C["white"] if on_dark else C["ink_primary"]))})


def _eyebrow(text, on_dark=False, align="left", rule=True):
    """Wide-tracked silver caps over a short chrome rule — the logo's own
    treatment of 'CUSTOM RENOVATION', and the repeating signature here."""
    lab = widget("heading", {
        "title": text, "header_size": "div", "align": align,
        "__typography__": typo_ref(T["eyebrow"]),
    }, globals_={"title_color": color_ref(
        SILVER_TXT if on_dark else C["muted"])})
    if not rule:
        return lab
    bar = container([_chrome(2)], {
        "content_width": "full", "flex_direction": "column",
        "width": slider(54), "_flex_shrink": "0",
        "margin": (dims(0, "auto", 0, "auto") if align == "center"
                   else dims(0, 0, 0, 0))})
    return container([lab, bar], {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(10),
        "flex_align_items": "center" if align == "center" else "flex-start"})


def _btn(label, href, style="chrome", icon_name=None):
    """Three buttons, no more.

        chrome  the brushed gradient with a near-black label. 6.12:1 against
                the gradient's DARKEST stop, so it passes across the sweep.
        solid   near-black fill, white label — for light grounds.
        ghost   silver hairline outline — for dark grounds and photographs.
    """
    b = _button(label, href, "primary", icon_name or "")
    b["settings"].update({
        "border_radius": R_BTN,
        "text_padding": dims(15, 30, 15, 30),
        "__typography__": typo_ref(T["meta"]),
    })
    g = b["settings"].setdefault("__globals__", {})
    if style == "solid":
        g.update({"background_color": color_ref(INK),
                  "border_color": color_ref(INK),
                  "button_text_color": color_ref(C["white"]),
                  "button_background_hover_color": color_ref(SILVER),
                  "button_hover_border_color": color_ref(SILVER),
                  "hover_color": color_ref(INK)})
    elif style == "ghost":
        b["settings"].update({"border_border": "solid", "border_width": box(1)})
        g.update({"background_color": color_ref(C["transparent"]),
                  "button_text_color": color_ref(C["white"]),
                  "border_color": color_ref(SILVER_TXT),
                  "button_background_hover_color": color_ref(C["white"]),
                  "button_hover_border_color": color_ref(C["white"]),
                  "hover_color": color_ref(INK)})
    else:
        # The gradient lives on the button's own background controls.
        b["settings"].update({
            "background_background": "gradient",
            "background_gradient_type": "linear",
            "background_gradient_angle": slider(100, "deg"),
            "background_color_stop": slider(10, "%"),
            "background_color_b_stop": slider(92, "%"),
        })
        g.update({"background_color": color_ref(CHROME_HI),
                  "background_color_b": color_ref(CHROME_LO),
                  "button_text_color": color_ref(INK),
                  "button_background_hover_color": color_ref(C["white"]),
                  "hover_color": color_ref(INK)})
    return b


def _ticks(items, on_dark=False, columns=1, container_px=KIT_CONTAINER):
    """container_px is the width of the PARENT column. A nested two-column
    tick list sized against the full container overflows and wraps - the row
    geometry rule."""
    rows = []
    for t in items:
        mark = widget("icon", {
            "selected_icon": icon("fas fa-check"), "size": slider(12),
            "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref(
            SILVER_TXT if on_dark else C["ink_primary"])})
        rows.append(_row([mark, _text(t, "left", on_dark=on_dark, small=True)],
                         12, align="flex-start",
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


def _card(kids, width=None, pad=None, on_dark=False, extra=None):
    s = {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(12),
        "padding": pad or dims(28, 26, 30, 26),
        "padding_mobile": dims(22, 18, 24, 18),
        "border_radius": R_CARD,
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
    }
    if width:
        s.update({"width": slider(width, "%"), "width_mobile": slider(100, "%")})
    if extra:
        s.update(extra)
    return container(kids, s, globals_={
        "background_color": color_ref(GRAPHITE if on_dark else C["white"]),
        "border_color": color_ref(GRAPHITE if on_dark else C["border"])})


def _shot(image, height=240, radius=R_CARD):
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


def _numeral(n, on_dark=True):
    """A large chrome numeral. Serif, because the logo's numerals would be."""
    return widget("heading", {
        "title": "%02d" % n, "header_size": "div", "align": "left",
        "__typography__": typo_ref(T["h_large"]),
    }, globals_={"title_color": color_ref(
        GRAPHITE if on_dark else C["border"])})


def _head_stack(props, on_dark, align="center"):
    """eyebrow + chrome rule + serif heading + optional intro — the section
    opener used by nearly every block below."""
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], on_dark, align))
    if props.get("title"):
        kids.append(_h(props["title"], "h2", T["h_medium"], align, on_dark))
    if props.get("intro"):
        kids.append(container([_text(props["intro"], align, on_dark=on_dark)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(74, "%"), "width_mobile": slider(100, "%"),
            "margin": (dims(0, "auto", 0, "auto") if align == "center"
                       else dims(0, 0, 0, 0))}))
    if not kids:
        return []
    return [container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(14),
        "flex_align_items": "center" if align == "center" else "flex-start"})]


# ─────────────────────────────── chrome ────────────────────────────────────

@block("ee.topbar")
def ee_topbar(props):
    """Thin black strip above the header."""
    items = []
    for it in props.get("items", []):
        kids = []
        if it.get("icon"):
            kids.append(widget("icon", {
                "selected_icon": icon(it["icon"]), "size": slider(12),
                "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref(SILVER_TXT)}))
        lab = widget("heading", {
            "title": it.get("label", ""), "header_size": "div", "align": "left",
            "__typography__": typo_ref(T["meta"]),
        }, globals_={"title_color": color_ref(SILVER_TXT)})
        if it.get("href"):
            lab["settings"]["link"] = link(it["href"])
        kids.append(lab)
        items.append(_row(kids, 8, align="center",
                          extra={"flex_wrap": "nowrap",
                                 "flex_direction_mobile": "row"}))
    bar = _row(items, 28, align="center", justify="flex-end",
               extra={"flex_wrap": "wrap",
                      "flex_justify_content_mobile": "center"})
    return container([bar], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "padding": dims(10, 0, 10, 0),
        "padding_mobile": dims(9, 16, 9, 16),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(ELEV)})


@block("ee.header")
def ee_header(props):
    """Black header. The logo's highlights are white, so it cannot sit on a
    light bar — this ground is a constraint the mark imposes."""
    logo = widget("theme-site-logo", {
        "align": "left", "width": slider(props.get("logo_width", 190)),
        "image_size": "full",
        **({"image": media(props["logo"], props.get("business", ""))}
           if props.get("logo") else {}),
    })
    nav = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"),
        "layout": "horizontal", "align_items": "center",
        "pointer": "underline", "animation_line": "fade",
        "menu_space_between": slider(props.get("menu_gap", 30)),
        "toggle_align": "right",
        "__typography__": typo_ref(T["meta"]),
    }, globals_={
        "color_menu_item": color_ref(C["white"]),
        "color_menu_item_hover": color_ref(SILVER),
        "color_menu_item_active": color_ref(SILVER),
        "pointer_color_menu_item_hover": color_ref(SILVER),
        "pointer_color_menu_item_active": color_ref(SILVER),
        "toggle_color": color_ref(C["white"]),
    })
    cta = _btn(props.get("cta_label", "Request a Consultation"),
               props.get("cta_url", "/schedule-an-appointment/"), "chrome")
    row = _row([
        _col([logo], 22, extra={"flex_justify_content": "center"}),
        _col([nav], 52, extra={"flex_justify_content": "center",
                               "flex_align_items": "center"}),
        _col([cta], 22, extra={"flex_justify_content": "center",
                               "flex_align_items": "flex-end"}),
    ], GUTTER, align="center", extra={
        "flex_wrap": "nowrap", "flex_wrap_tablet": "wrap"})
    sec = container([row], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "padding": dims(16, 0, 16, 0),
        "padding_mobile": dims(14, 16, 14, 16),
        "background_background": "classic",
        "sticky": "top", "sticky_on": ["desktop", "tablet", "mobile"],
        "sticky_offset": 0,
    }, globals_={"background_color": color_ref(INK)})
    return sec


@block("ee.footer")
def ee_footer(props):
    brand = []
    if props.get("logo"):
        brand.append(widget("image", {
            "image": media(props["logo"], props.get("business", "Logo")),
            "image_size": "full", "width": slider(190), "align": "left"}))
    if props.get("blurb"):
        brand.append(_text(props["blurb"], "left", on_dark=True, small=True))
    if props.get("social"):
        icons = [widget("icon", {
            "selected_icon": icon(s.get("icon", "fab fa-facebook-f")),
            "size": slider(15), "align": "center", "view": "default",
            "link": link(s.get("url", "#")),
        }, globals_={"primary_color": color_ref(SILVER_TXT)})
            for s in props["social"]]
        brand.append(_row(icons, 18, align="center",
                          extra={"flex_wrap": "wrap",
                                 "flex_direction_mobile": "row"}))

    cols = props.get("columns", [])
    widths = _tracks([1.5] + [1] * len(cols), GUTTER)
    body = [_col(brand, widths[0], extra={"flex_gap": gap(18)})]
    for i, c in enumerate(cols):
        kids = [widget("heading", {
            "title": c.get("title", ""), "header_size": "div", "align": "left",
            "__typography__": typo_ref(T["eyebrow"]),
        }, globals_={"title_color": color_ref(SILVER_TXT)})]
        for l in c.get("links", []):
            row = []
            if l.get("icon"):
                row.append(widget("icon", {
                    "selected_icon": icon(l["icon"]), "size": slider(12),
                    "align": "center", "view": "default",
                }, globals_={"primary_color": color_ref(SILVER_TXT)}))
            lab = widget("heading", {
                "title": l.get("label", ""), "header_size": "div",
                "align": "left", "__typography__": typo_ref(T["body_small"]),
            }, globals_={"title_color": color_ref(C["white"])})
            if l.get("url"):
                lab["settings"]["link"] = link(l["url"])
            row.append(lab)
            kids.append(_row(row, 9, align="flex-start",
                             extra={"flex_wrap": "nowrap",
                                    "flex_direction_mobile": "row",
                                    "padding": dims(4, 0, 4, 0)}))
        body.append(_col(kids, widths[i + 1], extra={"flex_gap": gap(6)}))

    legal = widget("heading", {
        "title": props.get("legal", ""), "header_size": "div",
        "align": "center", "__typography__": typo_ref(T["body_small"]),
    }, globals_={"title_color": color_ref(SILVER_TXT)})

    return container([
        _row(body, GUTTER, align="flex-start", extra={"flex_wrap": "wrap"}),
        _chrome(1),
        legal,
    ], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column", "flex_gap": gap(30),
        "padding": dims(76, 0, 34, 0),
        "padding_mobile": dims(52, 18, 28, 18),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(INK)})


# ─────────────────────────────── sections ──────────────────────────────────

@block("ee.hero")
def ee_hero(props):
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], True, "left"))
    if props.get("title"):
        kids.append(_h(props["title"], "h1", T["hero"], "left", True))
    if props.get("intro"):
        kids.append(_text(props["intro"], "left", on_dark=True))
    col_w = props.get("width", 58)
    if props.get("ticks"):
        kids.append(_ticks(props["ticks"], True,
                           2 if len(props["ticks"]) > 3 else 1,
                           container_px=KIT_CONTAINER * col_w / 100))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"), "chrome"))
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props.get("alt_url", "#"), "ghost"))
    if btns:
        kids.append(_row(btns, 14, align="center",
                         extra={"flex_wrap": "wrap",
                                "flex_direction_mobile": "column",
                                "padding": dims(8, 0, 0, 0)}))
    col = _col(kids, col_w, extra={"flex_gap": gap(20)})
    sec = _sec([_row([col], GUTTER, align="center")], "dark",
               pad=dims(props.get("pad_top", 112), 0,
                        props.get("pad_bottom", 118), 0),
               anchor=props.get("anchor"),
               extra={"min_height": slider(props.get("height", 600))})
    return _photo_ground(sec, props.get("image"),
                         props.get("position", "center center"),
                         props.get("overlay", 0.72))


@block("ee.gable")
def ee_gable(props):
    """The roof motif, cropped from the client's own logo file rather than
    redrawn, used as a centred section mark above a heading."""
    img = props.get("image")
    kids = []
    if img and img.get("url"):
        kids.append(widget("image", {
            "image": media(img["url"], img.get("alt", "")),
            "image_size": "full", "align": "center",
            "width": slider(props.get("width", 120))}))
    kids += _head_stack(props, _dark(props.get("bg", "white")), "center")
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"),
                extra={"flex_align_items": "center"})


@block("ee.rule")
def ee_rule(props):
    """A standalone chrome divider on its own band."""
    return _sec([_chrome(props.get("height", 1),
                         props.get("width", 100))],
                props.get("bg", "white"),
                pad=dims(0, 0, 0, 0))


@block("ee.intro")
def ee_intro(props):
    on_dark = _dark(props.get("bg", "pale"))
    kids = _head_stack({k: props.get(k) for k in ("eyebrow", "title")},
                       on_dark, props.get("align", "center"))
    for p in props.get("paragraphs", []):
        kids.append(container([_text(p, props.get("align", "center"),
                                     on_dark=on_dark)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(props.get("width", 76), "%"),
            "width_mobile": slider(100, "%"),
            "margin": (dims(0, "auto", 0, "auto")
                       if props.get("align", "center") == "center"
                       else dims(0, 0, 0, 0))}))
    return _sec(kids, props.get("bg", "pale"), anchor=props.get("anchor"),
                extra={"flex_align_items": "center"
                       if props.get("align", "center") == "center" else None}
                if props.get("align", "center") == "center" else None)


@block("ee.services")
def ee_services(props):
    on_dark = _dark(props.get("bg", "white"))
    kids = _head_stack(props, on_dark, "center")
    cols = props.get("columns", 3)
    w = _tracks([1] * cols, GUTTER)[0]
    cards = []
    for it in props.get("items", []):
        body = [_shot(it.get("image"), props.get("thumb_height", 220))]
        if it.get("label"):
            body.append(widget("heading", {
                "title": it["label"], "header_size": "div", "align": "left",
                "__typography__": typo_ref(T["eyebrow"]),
            }, globals_={"title_color": color_ref(
                SILVER_TXT if on_dark else C["muted"])}))
        body.append(_h(it.get("title", ""), "h3", T["h_small"], "left", on_dark))
        if it.get("text"):
            body.append(_text(it["text"], "left", on_dark=on_dark, small=True))
        if it.get("href"):
            b = _btn(props.get("action_label", "Learn More"), it["href"],
                     "ghost" if on_dark else "solid")
            b["settings"]["text_padding"] = dims(11, 20, 11, 20)
            body.append(container([b], {
                "content_width": "full", "flex_direction": "column",
                "flex_align_items": "flex-start",
                "padding": dims(6, 0, 0, 0)}))
        cards.append(_card(body, w, pad=dims(14, 14, 24, 14), on_dark=on_dark))
    kids.append(_row(cards, GUTTER, align="stretch",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("ee.split")
def ee_split(props):
    on_dark = _dark(props.get("bg", "white"))
    copy = []
    if props.get("eyebrow"):
        copy.append(_eyebrow(props["eyebrow"], on_dark, "left"))
    if props.get("title"):
        copy.append(_h(props["title"], "h2", T["h_medium"], "left", on_dark))
    for p in props.get("paragraphs", []):
        copy.append(_text(p, "left", on_dark=on_dark))
    if props.get("list_title"):
        copy.append(_h(props["list_title"], "h3", T["h_small"], "left", on_dark))
    if props.get("ticks"):
        copy.append(_ticks(props["ticks"], on_dark,
                           props.get("tick_columns", 1)))
    if props.get("footnote"):
        copy.append(_text(props["footnote"], "left", on_dark=on_dark, small=True))
    if props.get("cta_label"):
        copy.append(container([
            _btn(props["cta_label"], props.get("cta_url", "#"),
                 "ghost" if on_dark else "chrome")], {
            "content_width": "full", "flex_direction": "column",
            "flex_align_items": "flex-start", "padding": dims(8, 0, 0, 0)}))

    shot = _shot(props.get("image"), props.get("image_height", 460))
    w = _tracks([1, 1], GUTTER + 14)
    pair = [_col([shot], w[0]), _col(copy, w[1], extra={"flex_gap": gap(16)})]
    if props.get("flip"):
        pair.reverse()
    kids = _head_stack({"title": props.get("section_title")}, on_dark, "center")
    kids.append(_row(pair, GUTTER + 14, align="center",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("ee.process")
def ee_process(props):
    on_dark = _dark(props.get("bg", "dark"))
    kids = _head_stack(props, on_dark, "center")
    cols = props.get("columns", 4)
    w = _tracks([1] * cols, GUTTER)[0]
    cells = []
    for i, it in enumerate(props.get("items", []), 1):
        cells.append(_col([
            _numeral(i, on_dark),
            _chrome(2, 100),
            _h(it.get("title", ""), "h3", T["h_small"], "left", on_dark),
            _text(it.get("text", ""), "left", on_dark=on_dark, small=True),
        ], w, extra={"flex_gap": gap(12)}))
    kids.append(_row(cells, GUTTER, align="flex-start",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "dark"), anchor=props.get("anchor"))


@block("ee.showcase")
def ee_showcase(props):
    """One project, shown large. Built for the single real photograph the
    client supplied — a grid of one stock photo pretending to be a portfolio
    is the thing this block exists to avoid."""
    on_dark = _dark(props.get("bg", "elev"))
    kids = _head_stack(props, on_dark, "center")
    kids.append(_shot(props.get("image"), props.get("image_height", 520)))
    meta = []
    if props.get("caption_title"):
        meta.append(_h(props["caption_title"], "h3", T["h_small"], "left",
                       on_dark))
    if props.get("caption"):
        meta.append(_text(props["caption"], "left", on_dark=on_dark, small=True))
    facts = []
    split = _tracks([1.1, 1], GUTTER + 10)
    fact_px = KIT_CONTAINER * split[1] / 100
    for f in props.get("facts", []):
        facts.append(_col([
            widget("heading", {
                "title": f.get("label", ""), "header_size": "div",
                "align": "left", "__typography__": typo_ref(T["eyebrow"]),
            }, globals_={"title_color": color_ref(
                SILVER_TXT if on_dark else C["muted"])}),
            _text(f.get("value", ""), "left", on_dark=on_dark, small=True),
        ], _tracks([1] * max(1, len(props.get("facts", []))), GUTTER,
                   container=fact_px)[0],
            extra={"flex_gap": gap(4)}))
    if meta or facts:
        w = split
        kids.append(_row([
            _col(meta, w[0], extra={"flex_gap": gap(10)}),
            _col([_row(facts, GUTTER, align="flex-start",
                       extra={"flex_wrap": "wrap"})] if facts else [], w[1]),
        ], GUTTER + 10, align="flex-start", extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "elev"), anchor=props.get("anchor"))


@block("ee.statement")
def ee_statement(props):
    """A full-bleed dark band carrying one serif line and one button. The
    design's full stop."""
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], True, "center"))
    if props.get("title"):
        kids.append(_h(props["title"], "h2", T["h_large"], "center", True))
    if props.get("text"):
        kids.append(container([_text(props["text"], "center", on_dark=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(66, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"), "chrome"))
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props.get("alt_url", "#"), "ghost"))
    if btns:
        kids.append(_row(btns, 14, align="center", justify="center",
                         extra={"flex_wrap": "wrap",
                                "flex_direction_mobile": "column",
                                "padding": dims(8, 0, 0, 0)}))
    sec = _sec(kids, "dark", pad=dims(96, 0, 96, 0),
               anchor=props.get("anchor"),
               extra={"flex_align_items": "center"})
    return _photo_ground(sec, props.get("image"),
                         props.get("position", "center center"),
                         props.get("overlay", 0.78))


@block("ee.faq")
def ee_faq(props):
    on_dark = _dark(props.get("bg", "white"))
    kids = _head_stack(props, on_dark, "center")
    kids.append(container([_faq(props.get("items", []), first_open=True)], {
        "content_width": "full", "flex_direction": "column",
        "width": slider(84, "%"), "width_mobile": slider(100, "%"),
        "margin": dims(0, "auto", 0, "auto")}))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("ee.detailcards")
def ee_detailcards(props):
    on_dark = _dark(props.get("bg", "white"))
    kids = _head_stack(props, on_dark, "center")
    cols = props.get("columns", 4)
    w = _tracks([1] * cols, GUTTER)[0]
    cards = []
    for it in props.get("items", []):
        body = []
        if it.get("icon"):
            body.append(widget("icon", {
                "selected_icon": icon(it["icon"]), "size": slider(20),
                "align": "left", "view": "default",
            }, globals_={"primary_color": color_ref(
                SILVER_TXT if on_dark else C["ink_primary"])}))
        body.append(widget("heading", {
            "title": it.get("label", ""), "header_size": "div", "align": "left",
            "__typography__": typo_ref(T["eyebrow"]),
        }, globals_={"title_color": color_ref(
            SILVER_TXT if on_dark else C["muted"])}))
        val = widget("heading", {
            "title": it.get("value", ""), "header_size": "div", "align": "left",
            "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(
            C["white"] if on_dark else C["ink_primary"])})
        if it.get("href"):
            val["settings"]["link"] = link(it["href"])
        body.append(val)
        if it.get("text"):
            body.append(_text(it["text"], "left", on_dark=on_dark, small=True))
        cards.append(_card(body, w, on_dark=on_dark))
    kids.append(_row(cards, GUTTER, align="stretch",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("ee.form")
def ee_form(props):
    f = props.get("form", {})
    on_dark = _dark(props.get("bg", "pale"))
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
        "button_text": f.get("submit", "Submit"),
        "button_size": "md", "button_width": "100", "input_size": "md",
        "show_labels": "yes", "mark_required": "yes",
        "row_gap": slider(14), "column_gap": slider(12),
        "success_message": f.get("success", ""),
        "field_border_radius": box(2), "field_border_width": box(1),
        "button_border_radius": R_BTN,
    }, globals_={
        "button_background_color": color_ref(INK),
        "button_text_color": color_ref(C["white"]),
        "button_background_hover_color": color_ref(SILVER),
        "button_hover_color": color_ref(INK),
        "field_background_color": color_ref(C["white"]),
        "field_text_color": color_ref(C["ink_primary"]),
        "field_border_color": color_ref(C["border"]),
        "label_color": color_ref(C["ink_primary"]),
        "mark_required_color": color_ref(C["muted"]),
    })

    card = container([
        _h(props.get("title", ""), "h2", T["h_medium"], "left"),
        *( [_text(props["intro"], "left")] if props.get("intro") else [] ),
        _chrome(2, 70),
        form,
    ], {
        "content_width": "full", "flex_direction": "column", "flex_gap": gap(18),
        "padding": dims(38, 36, 40, 36),
        "padding_mobile": dims(24, 18, 26, 18),
        "border_radius": R_CARD,
        "border_border": "solid", "border_width": box(1),
        "width": slider(props.get("card_width", 100), "%"),
        "width_mobile": slider(100, "%"),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["white"]),
                 "border_color": color_ref(C["border"])})

    side = props.get("side")
    if side:
        sk = []
        if side.get("eyebrow"):
            sk.append(_eyebrow(side["eyebrow"], on_dark, "left"))
        if side.get("title"):
            sk.append(_h(side["title"], "h2", T["h_medium"], "left", on_dark))
        for p in side.get("paragraphs", []):
            sk.append(_text(p, "left", on_dark=on_dark))
        if side.get("ticks"):
            sk.append(_ticks(side["ticks"], on_dark))
        w = _tracks([1, 1.15], GUTTER + 14)
        body = _row([_col(sk, w[0], extra={"flex_gap": gap(16)}),
                     _col([card], w[1])], GUTTER + 14,
                    align="flex-start", extra={"flex_wrap": "wrap"})
    else:
        body = container([card], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(props.get("outer_width", 72), "%"),
            "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")})

    return _sec([body], props.get("bg", "pale"),
                anchor=props.get("anchor", "enquire"))


@block("ee.map")
def ee_map(props):
    on_dark = _dark(props.get("bg", "white"))
    kids = _head_stack(props, on_dark, "center")
    kids.append(widget("google_maps", {
        "address": props.get("address", ""),
        "zoom": slider(props.get("zoom", 11)),
        "height": slider(props.get("height", 400)),
    }))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))
