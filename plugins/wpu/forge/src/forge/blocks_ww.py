"""
blocks_ww.py — Weather Warrior Roofing (San Antonio, TX).

The client's instruction is "exact similar website like https://832-roofing.com/",
so this family is a device-by-device transcription of that site, rendered at
1621px and read off its computed styles. Its accent is red #C51219 on a
near-black #151422; Weather Warrior's logo is navy #112040 with gold
#BD9A5D, so the mapping is:

    832-roofing.com                     Weather Warrior
    --------------------------------    ---------------------------------
    near-black #151422 bars and bands   near-black navy #0B1120
    red #C51219 buttons, ticks, icons   gold #BD9A5D fills, navy label
    white cards on a pale grey band     unchanged
    Poppins headings, Kumbh Sans body   unchanged - both are the client's
                                        brand-neutral choice and both are
                                        already the reference's faces

One measured adjustment. The reference puts WHITE text on its red; white on
this gold is 2.1:1 and unreadable, so a gold button carries NAVY text (8.4:1)
and the navy button carries white. Gold used as TEXT on white drops to the
darker `wwgld2` #8A6A2F. The hue never moves - only the weight of it.

Devices, in the order the reference runs them:

    ww.topbar       utility strip: phone and email, right aligned
    ww.header       dark bar, logo left, uppercase nav, one filled CTA
    ww.hero         photo + scrim, eyebrow, uppercase display, tick list,
                    two stacked buttons
    ww.featured     three white cards overlapping the hero foot, each with an
                    icon disc and a ghosted 01/02/03
    ww.about        centred section title, photo left, copy and a tick list
    ww.intro        centred heading over a centred paragraph, pale band
    ww.pills        the two filled category buttons, centred
    ww.servicegrid  four-up cards: photo, uppercase title, small button
    ww.ctapair      one centred line over two stacked buttons
    ww.process      numbered steps, four across
    ww.reviews      three review cards, stars, name, ghosted quote mark
    ww.why          dark band: heading, ticks, buttons | photo
    ww.areas        the service-area list as linked chips
    ww.faq          accordion, first answer open
    ww.formband     photo ground with a white form card over it
    ww.gallery      captioned image grid
    ww.map          the per-city map
    ww.footer       dark, four columns, social row, legal bar
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

GOLD = "accent"            # #BD9A5D, the brand gold
GOLD_LIGHT = "wwgld01"      # #F0CF8F, gold on dark grounds
GOLD_TEXT = "wwgld02"       # #8A6A2F, gold that passes as text on white
NAVY = "primary"           # #112040
INK = "secondary"          # #0B1120, the near-black navy of every dark band

WW_PAD = dims(84, 0, 84, 0)
WW_PAD_T = dims(62, 24, 62, 24)
WW_PAD_M = dims(48, 18, 48, 18)
R_BTN = box(3)             # measured: the reference's buttons are 3px
R_CARD = box(8)
R_PILL = box(50)
GUTTER = 24


# ─────────────────────────────── helpers ───────────────────────────────────

def _sec(children, bg="white", pad=None, anchor=None, extra=None):
    grounds = {"white": C["white"], "pale": C["surface"], "dark": INK,
               "navy": NAVY, "gold": GOLD}
    s = {
        "content_width": "boxed",
        "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "flex_gap": gap(28),
        "padding": pad or WW_PAD,
        "padding_tablet": WW_PAD_T,
        "padding_mobile": WW_PAD_M,
        "background_background": "classic",
    }
    if anchor:
        s["_element_id"] = anchor
    if extra:
        s.update(extra)
    return container(children, s, globals_={
        "background_color": color_ref(grounds.get(bg, C["white"]))})


def _dark(bg):
    return bg in ("dark", "navy")


def _photo_ground(sec, image, position="center center", overlay=0.62,
                  colour=INK):
    """Photo behind a section with the brand scrim over it - the reference's
    hero, its why-choose band and its form band all use this one recipe."""
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
        "background_overlay_color"] = color_ref(colour)
    return sec


def _h(text, size="h2", token=None, align="left", on_dark=False, upper=True,
       color=None):
    """Headings are UPPERCASE on the reference, in Poppins, tight."""
    return widget("heading", {
        "title": text.upper() if upper else text,
        "header_size": size, "align": align,
        "__typography__": typo_ref(token or T["h_medium"]),
    }, globals_={"title_color": color_ref(
        color or (C["white"] if on_dark else NAVY))})


def _eyebrow(text, on_dark=False, align="left"):
    return widget("heading", {
        "title": text, "header_size": "div", "align": align,
        "__typography__": typo_ref(T["eyebrow"]),
    }, globals_={"title_color": color_ref(GOLD_LIGHT if on_dark else GOLD_TEXT)})


def _btn(label, href, style="gold", icon_name=None):
    """Two fills and one outline, matching the reference's button set.

        gold     brand gold, NAVY label - the primary (their red)
        navy     navy fill, white label - the secondary
        ghost    white outline on a photo or a dark band
    """
    b = _button(label, href, "primary", icon_name or "")
    b["settings"].update({
        "border_radius": R_BTN,
        "text_padding": dims(14, 26, 14, 26),
        "__typography__": typo_ref(T["meta"]),
    })
    g = b["settings"].setdefault("__globals__", {})
    if style == "navy":
        g.update({"background_color": color_ref(NAVY),
                  "border_color": color_ref(NAVY),
                  "button_text_color": color_ref(C["white"]),
                  "button_background_hover_color": color_ref(GOLD),
                  "button_hover_border_color": color_ref(GOLD),
                  "hover_color": color_ref(NAVY)})
    elif style == "ghost":
        b["settings"].update({"border_border": "solid", "border_width": box(1)})
        g.update({"background_color": color_ref(C["transparent"]),
                  "button_text_color": color_ref(C["white"]),
                  "border_color": color_ref(C["white"]),
                  "button_background_hover_color": color_ref(C["white"]),
                  "button_hover_border_color": color_ref(C["white"]),
                  "hover_color": color_ref(NAVY)})
    else:
        g.update({"background_color": color_ref(GOLD),
                  "border_color": color_ref(GOLD),
                  "button_text_color": color_ref(NAVY),
                  "button_background_hover_color": color_ref(NAVY),
                  "button_hover_border_color": color_ref(NAVY),
                  "hover_color": color_ref(C["white"])})
    return b


def _ticks(items, on_dark=False, columns=1):
    """The reference's check list: a small accent tick, one line of text."""
    rows = []
    for t in items:
        mark = widget("icon", {
            "selected_icon": icon("fas fa-check"), "size": slider(13),
            "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref(GOLD_LIGHT if on_dark else GOLD_TEXT)})
        rows.append(_row([mark, _text(t, "left", on_dark=on_dark, small=True)],
                         11, align="flex-start",
                         extra={"flex_wrap": "nowrap",
                                "flex_direction_mobile": "row",
                                "padding": dims(5, 0, 5, 0)}))
    if columns == 1:
        return container(rows, {"content_width": "full",
                                "flex_direction": "column", "flex_gap": gap(2)})
    per = -(-len(rows) // columns)
    w = _tracks([1] * columns, 20)[0]
    cols = [_col(rows[i:i + per], w, extra={"flex_gap": gap(2)})
            for i in range(0, len(rows), per)]
    return _row(cols, 20, align="flex-start", extra={"flex_wrap": "wrap"})


def _card(kids, width=None, pad=None, extra=None, tinted=False):
    s = {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(12),
        "padding": pad or dims(26, 24, 28, 24),
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
        "background_color": color_ref(C["surface"] if tinted else C["white"]),
        "border_color": color_ref(C["border"])})


def _disc(icon_name, size=48, tone="gold"):
    return container([widget("icon", {
        "selected_icon": icon(icon_name), "size": slider(round(size * 0.42)),
        "align": "center", "view": "default",
    }, globals_={"primary_color": color_ref(
        NAVY if tone == "gold" else C["white"])})], {
        "content_width": "full", "flex_direction": "column",
        "flex_justify_content": "center", "flex_align_items": "center",
        "width": slider(size), "min_height": slider(size), "_flex_shrink": "0",
        "border_radius": box(999),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(GOLD if tone == "gold" else NAVY)})


def _shot(image, height=210, radius=R_CARD):
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


# ─────────────────────────────── chrome ────────────────────────────────────

@block("ww.topbar")
def ww_topbar(props):
    """The thin strip above the header: phone and email, right aligned."""
    items = []
    for it in props.get("items", []):
        ic = widget("icon", {
            "selected_icon": icon(it.get("icon", "fas fa-phone-alt")),
            "size": slider(13), "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref(GOLD_LIGHT)})
        b = _button(it.get("label", ""), it.get("href", "#"), "ghost", "")
        b["settings"].update({
            "border_border": "none", "border_width": box(0),
            "text_padding": dims(0, 0, 0, 0),
            "__typography__": typo_ref(T["meta"])})
        b["settings"].setdefault("__globals__", {}).update({
            "button_text_color": color_ref(C["white"]),
            "hover_color": color_ref(GOLD_LIGHT)})
        items.append(_row([ic, b], 8, align="center",
                          extra={"flex_wrap": "nowrap",
                                 "flex_direction_mobile": "row"}))
    strip = _row(items, 26, align="center", extra={
        "flex_wrap": "wrap", "flex_direction_mobile": "row",
        "flex_justify_content": "flex-end",
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "margin": dims(0, "auto", 0, "auto")})
    return container([strip], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(9, 20, 9, 20),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(NAVY)})


@block("ww.header")
def ww_header(props):
    """Dark bar: logo left, uppercase nav, one filled CTA on the right.

    Sticky, because the reference's is - and on a lead-generation site the
    call button should never scroll away.
    """
    logo = widget("theme-site-logo", {
        "align": "left", "width": slider(props.get("logo_width", 190)),
        **({"image": media(props["logo"], props.get("business", ""))}
           if props.get("logo") else {}),
    })
    nav = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"),
        "layout": "horizontal", "align_items": "center",
        "pointer": "underline", "animation_line": "fade",
        "menu_space_between": slider(props.get("menu_gap", 26)),
        "toggle_align": "right",
        "__typography__": typo_ref(T["meta"]),
    }, globals_={
        "color_menu_item": color_ref(C["white"]),
        "color_menu_item_hover": color_ref(GOLD_LIGHT),
        "color_menu_item_active": color_ref(GOLD_LIGHT),
        "pointer_color_menu_item_hover": color_ref(GOLD),
    })
    cta = _btn(props.get("cta_label", "Schedule An Appointment"),
               props.get("cta_url", "/schedule-appointment/"),
               "gold", "far fa-calendar-alt")

    w = _tracks([20, 54, 24], 20)
    bar = _row([_col([logo], w[0]),
                _col([nav], w[1], extra={"flex_justify_content": "center"}),
                _col([cta], w[2], extra={"flex_align_items": "flex-end"})],
               20, align="center", extra={
                   "content_width": "boxed",
                   "boxed_width": slider(KIT_CONTAINER),
                   "margin": dims(0, "auto", 0, "auto")})
    return container([bar], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(14, 20, 14, 20),
        "sticky": "top", "sticky_on": ["desktop", "tablet", "mobile"],
        "_z_index": 99,
        "background_background": "classic",
    }, globals_={"background_color": color_ref(INK)})


@block("ww.footer")
def ww_footer(props):
    """Dark footer: brand column with blurb and social, then link columns,
    then the contact column with accent icons, then a centred legal bar."""
    brand = [widget("theme-site-logo", {
        "align": "left", "width": slider(170),
        **({"image": media(props["logo"], props.get("business", "Logo"))}
           if props.get("logo") else {}),
    })]
    if props.get("blurb"):
        brand.append(_text(props["blurb"], "left", on_dark=True, small=True))
    if props.get("social"):
        icons = []
        for s in props["social"]:
            icons.append(widget("icon", {
                "selected_icon": icon(s.get("icon", "fab fa-facebook-f")),
                "size": slider(15), "align": "center", "view": "default",
                "link": link(s.get("url", "#")),
            }, globals_={"primary_color": color_ref(C["white"])}))
        brand.append(_row(icons, 16, align="center",
                          extra={"flex_wrap": "wrap",
                                 "flex_direction_mobile": "row"}))

    cols = [_col(brand, _tracks([30, 22, 22, 26], 26)[0],
                 extra={"flex_gap": gap(16)})]
    widths = _tracks([30, 22, 22, 26], 26)
    for i, c in enumerate(props.get("columns", [])):
        kids = [_h(c.get("title", ""), "h3", T["eyebrow"], "left", True,
                   color=GOLD_LIGHT)]
        for ln in c.get("links", []):
            if ln.get("icon"):
                ic = widget("icon", {
                    "selected_icon": icon(ln["icon"]), "size": slider(13),
                    "align": "center", "view": "default",
                }, globals_={"primary_color": color_ref(GOLD_LIGHT)})
                if ln.get("url"):
                    b = _button(ln.get("label", ""), ln["url"], "ghost", "")
                    b["settings"].update({
                        "border_border": "none", "border_width": box(0),
                        "text_padding": dims(0, 0, 0, 0),
                        "__typography__": typo_ref(T["body_small"])})
                    b["settings"].setdefault("__globals__", {}).update({
                        "button_text_color": color_ref(C["on_dark"]),
                                    "hover_color": color_ref(GOLD_LIGHT)})
                    line = b
                else:
                    line = _text(ln.get("label", ""), "left", on_dark=True,
                                 small=True)
                kids.append(_row([ic, line], 10, align="flex-start",
                                 extra={"flex_wrap": "nowrap",
                                        "flex_direction_mobile": "row",
                                        "padding": dims(4, 0, 4, 0)}))
            else:
                b = _button(ln.get("label", ""), ln.get("url", "#"), "ghost", "")
                b["settings"].update({
                    "border_border": "none", "border_width": box(0),
                    "text_padding": dims(4, 0, 4, 0),
                    "__typography__": typo_ref(T["body_small"])})
                b["settings"].setdefault("__globals__", {}).update({
                    "button_text_color": color_ref(C["on_dark"]),
                            "hover_color": color_ref(GOLD_LIGHT)})
                kids.append(b)
        cols.append(_col(kids, widths[min(i + 1, len(widths) - 1)],
                         extra={"flex_gap": gap(4)}))

    legal = container([_text(props.get("legal", ""), "center", on_dark=True,
                             small=True)], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(18, 0, 0, 0),
        "margin": dims(28, 0, 0, 0),
        "border_border": "solid", "border_width": dims(1, 0, 0, 0),
    }, globals_={"border_color": color_ref(C["rule_dark"])})

    return container([_row(cols, 26, align="flex-start",
                           extra={"flex_wrap": "wrap"}), legal], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column", "flex_gap": gap(0),
        "padding": dims(60, 0, 34, 0),
        "padding_mobile": dims(44, 18, 28, 18),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(INK)})


# ─────────────────────────────── page devices ──────────────────────────────

@block("ww.hero")
def ww_hero(props):
    """The opener: roof photograph, scrim from the left, eyebrow, a three-line
    uppercase display headline, the trust checklist, then two stacked buttons.

    The reference stacks its two buttons rather than sitting them side by side,
    and both are filled - the phone number first. On a roofing site the call is
    the conversion, so that order is kept.
    """
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], on_dark=True))
    kids.append(_h(props.get("title", ""), "h1", T["hero"], "left",
                   on_dark=True))
    if props.get("intro"):
        kids.append(_text(props["intro"], "left", on_dark=True))
    if props.get("ticks"):
        kids.append(_ticks(props["ticks"], on_dark=True))
    acts = []
    if props.get("phone_display"):
        acts.append(_btn(props["phone_display"],
                         "tel:" + props.get("phone", ""), "gold",
                         "fas fa-phone-alt"))
    if props.get("cta_label"):
        acts.append(_btn(props["cta_label"], props.get("cta_url", "#"),
                         "ghost", "far fa-calendar-alt"))
    if acts:
        kids.append(container(acts, {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(12), "flex_align_items": "flex-start",
            "padding": dims(8, 0, 0, 0),
            "width": slider(props.get("btn_width", 42), "%"),
            "width_tablet": slider(70, "%"), "width_mobile": slider(100, "%")}))

    body = container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(16), "width": slider(props.get("width", 56), "%"),
        "width_tablet": slider(86, "%"), "width_mobile": slider(100, "%")})

    sec = _sec([body], "dark",
               pad=dims(props.get("pad_top", 96), 0, props.get("pad_bottom", 104), 0),
               extra={"min_height": slider(props.get("height", 560)),
                      "min_height_mobile": slider(420),
                      "flex_justify_content": "center"},
               anchor=props.get("anchor"))
    return _photo_ground(sec, props.get("image"),
                         props.get("position", "center center"),
                         props.get("overlay", 0.66))


@block("ww.featured")
def ww_featured(props):
    """The three cards that sit across the foot of the hero.

    Pulled up into the hero with a negative top margin, exactly as the
    reference does it, and each carries a ghosted numeral behind the copy so
    the row reads as one, two, three rather than as three unrelated boxes.
    """
    items = props.get("items", [])
    w = _tracks([1] * max(len(items), 1), GUTTER)[0]
    cards = []
    for i, it in enumerate(items, 1):
        num = widget("heading", {
            "title": "0%d" % i, "header_size": "div", "align": "left",
            "__typography__": typo_ref(T["h_large"]),
        }, globals_={"title_color": color_ref(C["border"])})
        head = _row([_disc(it.get("icon", "fas fa-shield-alt"), 46),
                     _h(it.get("title", ""), "h3", T["h_small"], "left",
                        upper=False)], 14, align="center",
                    extra={"flex_wrap": "nowrap",
                           "flex_direction_mobile": "row"})
        body = [head]
        if it.get("text"):
            body.append(_text(it["text"], "left", small=True))
        body.append(num)
        cards.append(_card(body, w, pad=dims(24, 24, 18, 24)))
    grid = _row(cards, GUTTER, align="stretch", extra={"flex_wrap": "wrap"})
    return _sec([grid], props.get("bg", "white"),
                pad=dims(0, 0, 70, 0),
                extra={"margin": dims(-74, 0, 0, 0), "_z_index": 5})


@block("ww.intro")
def ww_intro(props):
    """Centred uppercase heading over a centred paragraph, on the pale band."""
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], _dark(props.get("bg", "pale")),
                             "center"))
    kids.append(_h(props.get("title", ""), props.get("size", "h2"),
                   T["h_medium"], "center", _dark(props.get("bg", "pale"))))
    for p in props.get("paragraphs", []):
        kids.append(container([_text(p, "center",
                                     _dark(props.get("bg", "pale")))], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(props.get("width", 74), "%"),
            "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    return _sec(kids, props.get("bg", "pale"), anchor=props.get("anchor"))


@block("ww.about")
def ww_about(props):
    """Centred section title, then photo on one side and copy with a tick
    list on the other - the reference's About block."""
    body = []
    if props.get("subtitle"):
        body.append(_h(props["subtitle"], "h3", T["h_small"], "left"))
    for p in props.get("paragraphs", []):
        body.append(_text(p, "left"))
    if props.get("list_title"):
        body.append(_h(props["list_title"], "h3", T["h_small"], "left"))
    if props.get("ticks"):
        body.append(_ticks(props["ticks"]))
    if props.get("footnote"):
        body.append(_text(props["footnote"], "left"))
    if props.get("cta_label"):
        body.append(_btn(props["cta_label"], props.get("cta_url", "#"), "gold"))

    w = _tracks([44, 52], 46)
    cols = [_col([_shot(props.get("image"), props.get("image_height", 420))], w[0]),
            _col(body, w[1], extra={"flex_gap": gap(14)})]
    if props.get("flip"):
        cols.reverse()
    head = []
    if props.get("title"):
        head.append(_h(props["title"], "h2", T["h_medium"], "center"))
    return _sec(head + [_row(cols, 46, align="center")],
                props.get("bg", "white"), anchor=props.get("anchor"))


@block("ww.pills")
def ww_pills(props):
    """The pair of filled category buttons the reference centres above its
    service grids."""
    pills = [_btn(p.get("label", ""), p.get("href", "#"),
                  "gold" if i == 0 else "navy")
             for i, p in enumerate(props.get("items", []))]
    return _sec([_row(pills, 14, align="center", extra={
        "flex_wrap": "wrap", "flex_direction_mobile": "row",
        "flex_justify_content": "center"})],
        props.get("bg", "pale"), pad=dims(56, 0, 10, 0))


@block("ww.servicegrid")
def ww_servicegrid(props):
    """Four-up service cards: photograph, uppercase title, one small button.

    The card is the reference's, including the inset photo and the centred
    button under a centred title. Titles get a floor so a two-line name does
    not shorten the cards beside it.
    """
    items = props.get("items", [])
    cols = props.get("columns", 4)
    w = _tracks([1] * cols, GUTTER)[0]
    cards = []
    for it in items:
        kids = [_shot(it.get("image"), props.get("thumb_height", 170)),
                container([_h(it.get("title", ""), "h3", T["h_small"],
                              "center")], {
                    "content_width": "full", "flex_direction": "column",
                    "flex_justify_content": "center",
                    "min_height": slider(props.get("title_height", 52))})]
        if it.get("text"):
            kids.append(_text(it["text"], "center", small=True))
        b = _btn(props.get("action_label", "Know More"), it.get("href", "#"),
                 "gold")
        b["settings"]["text_padding"] = dims(10, 20, 10, 20)
        kids.append(container([b], {
            "content_width": "full", "flex_direction": "column",
            "flex_align_items": "center"}))
        cards.append(_card(kids, w, pad=dims(14, 14, 20, 14)))
    grid = _row(cards, GUTTER, align="stretch", extra={"flex_wrap": "wrap"})
    head = []
    if props.get("title"):
        head.append(_h(props["title"], "h2", T["h_medium"], "center"))
    if props.get("intro"):
        head.append(container([_text(props["intro"], "center")], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(76, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    return _sec(head + [grid], props.get("bg", "pale"),
                anchor=props.get("anchor"))


@block("ww.ctapair")
def ww_ctapair(props):
    """One centred line over the two stacked buttons - the reference closes
    most of its sections this way."""
    kids = []
    if props.get("title"):
        kids.append(_h(props["title"], "h2", T["h_medium"], "center",
                       _dark(props.get("bg", "pale"))))
    if props.get("text"):
        kids.append(container([_text(props["text"], "center",
                                     _dark(props.get("bg", "pale")))], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(72, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    acts = []
    if props.get("phone_display"):
        acts.append(_btn(props["phone_display"], "tel:" + props.get("phone", ""),
                         "gold", "fas fa-phone-alt"))
    if props.get("cta_label"):
        acts.append(_btn(props["cta_label"], props.get("cta_url", "#"),
                         "navy" if not _dark(props.get("bg", "pale")) else "ghost",
                         "far fa-calendar-alt"))
    kids.append(container(acts, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(12), "flex_align_items": "center",
        "width": slider(30, "%"), "width_tablet": slider(56, "%"),
        "width_mobile": slider(100, "%"),
        "margin": dims(6, "auto", 0, "auto")}))
    return _sec(kids, props.get("bg", "pale"), anchor=props.get("anchor"))


@block("ww.process")
def ww_process(props):
    """The four-step process, numbered across."""
    items = props.get("items", [])
    cols = props.get("columns", 4)
    w = _tracks([1] * cols, GUTTER)[0]
    cards = []
    for i, it in enumerate(items, 1):
        badge = container([widget("heading", {
            "title": "%02d" % i, "header_size": "div", "align": "center",
            "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(NAVY)})], {
            "content_width": "full", "flex_direction": "column",
            "flex_justify_content": "center", "flex_align_items": "center",
            "width": slider(46), "min_height": slider(46), "_flex_shrink": "0",
            "border_radius": box(999), "background_background": "classic",
        }, globals_={"background_color": color_ref(GOLD)})
        kids = [badge, _h(it.get("title", ""), "h3", T["h_small"], "left",
                          upper=False)]
        if it.get("text"):
            kids.append(_text(it["text"], "left", small=True))
        cards.append(_card(kids, w))
    head = []
    if props.get("title"):
        head.append(_h(props["title"], "h2", T["h_medium"], "center"))
    if props.get("intro"):
        head.append(container([_text(props["intro"], "center")], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(72, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    return _sec(head + [_row(cards, GUTTER, align="stretch",
                             extra={"flex_wrap": "wrap"})],
                props.get("bg", "white"), anchor=props.get("anchor"))


@block("ww.reviews")
def ww_reviews(props):
    """Three review cards: gold stars, the quote, the name in the accent, and
    a ghosted quote mark in the corner."""
    items = props.get("items", [])
    cols = props.get("columns", 3)
    w = _tracks([1] * cols, GUTTER)[0]
    cards = []
    for it in items:
        stars = widget("star-rating", {
            "rating": it.get("rating", 5), "rating_scale": "5", "star_style": "star_fontawesome",
            "align": "left", "unmarked_star_style": "solid",
            "icon_size": slider(14),
        }, globals_={"stars_color": color_ref(GOLD),
                     "stars_unmarked_color": color_ref(C["border"])})
        quote = widget("icon", {
            "selected_icon": icon("fas fa-quote-right"), "size": slider(26),
            "align": "right", "view": "default",
        }, globals_={"primary_color": color_ref(C["surface"])})
        cards.append(_card([
            stars,
            _text(it.get("text", ""), "left", small=True),
            _h(it.get("name", ""), "h3", T["h_small"], "left", upper=False,
               color=GOLD_TEXT),
            quote,
        ], w, pad=dims(24, 24, 20, 24)))
    head = []
    if props.get("title"):
        head.append(_h(props["title"], "h2", T["h_medium"], "center"))
    if props.get("intro"):
        head.append(container([_text(props["intro"], "center")], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(76, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    return _sec(head + [_row(cards, GUTTER, align="stretch",
                             extra={"flex_wrap": "wrap"})],
                props.get("bg", "white"), anchor=props.get("anchor"))


@block("ww.why")
def ww_why(props):
    """The dark band: heading and tick list on one side, photo on the other,
    two stacked buttons under the list."""
    body = [_h(props.get("title", ""), "h2", T["h_medium"], "left",
               on_dark=True)]
    if props.get("intro"):
        body.append(_text(props["intro"], "left", on_dark=True))
    if props.get("ticks"):
        body.append(_ticks(props["ticks"], on_dark=True))
    acts = []
    if props.get("phone_display"):
        acts.append(_btn(props["phone_display"], "tel:" + props.get("phone", ""),
                         "gold", "fas fa-phone-alt"))
    if props.get("cta_label"):
        acts.append(_btn(props["cta_label"], props.get("cta_url", "#"),
                         "ghost", "far fa-calendar-alt"))
    if acts:
        body.append(container(acts, {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(12), "flex_align_items": "flex-start",
            "width": slider(58, "%"), "width_mobile": slider(100, "%"),
            "padding": dims(6, 0, 0, 0)}))

    w = _tracks([48, 48], 44)
    cols = [_col(body, w[0], extra={"flex_gap": gap(14)}),
            _col([_shot(props.get("image"), props.get("image_height", 360))], w[1])]
    if props.get("flip"):
        cols.reverse()
    return _sec([_row(cols, 44, align="center")], "dark",
                anchor=props.get("anchor"))


@block("ww.areas")
def ww_areas(props):
    """The service-area list. Every town is a link to its own page, which is
    the entire point of a local-SEO area section."""
    chips = []
    for a in props.get("items", []):
        label = a.get("label", a) if isinstance(a, dict) else a
        href = a.get("href", "") if isinstance(a, dict) else ""
        if href:
            b = _button(label, href, "ghost", "")
            b["settings"].update({
                "border_radius": R_PILL,
                "text_padding": dims(9, 18, 9, 18),
                "border_border": "solid", "border_width": box(1),
                "__typography__": typo_ref(T["meta"])})
            b["settings"].setdefault("__globals__", {}).update({
                "button_text_color": color_ref(NAVY),
                "background_color": color_ref(C["white"]),
                "border_color": color_ref(C["border"]),
                "button_background_hover_color": color_ref(NAVY),
                "button_hover_border_color": color_ref(NAVY),
                "hover_color": color_ref(C["white"])})
            chips.append(b)
        else:
            chips.append(_text(label, "left", small=True))
    grid = _row(chips, 10, align="center", extra={
        "flex_wrap": "wrap", "flex_direction_mobile": "row",
        "flex_justify_content": "center"})
    head = []
    if props.get("title"):
        head.append(_h(props["title"], "h2", T["h_medium"], "center"))
    if props.get("intro"):
        head.append(container([_text(props["intro"], "center")], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(76, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    return _sec(head + [grid], props.get("bg", "pale"),
                anchor=props.get("anchor"))


@block("ww.faq")
def ww_faq(props):
    """Accordion, first answer open."""
    kids = []
    if props.get("title"):
        kids.append(_h(props["title"], "h2", T["h_medium"], "center"))
    if props.get("intro"):
        kids.append(container([_text(props["intro"], "center")], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(72, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    inner = container([_faq(props.get("items", []), first_open=True)], {
        "content_width": "full", "flex_direction": "column",
        "width": slider(84, "%"), "width_mobile": slider(100, "%"),
        "margin": dims(0, "auto", 0, "auto")})
    return _sec(kids + [inner], props.get("bg", "white"),
                anchor=props.get("anchor"))


@block("ww.formband")
def ww_formband(props):
    """A photograph with the quote form floating over it on a white card -
    the reference's closing conversion block."""
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
        "form_name": f.get("form_name", "Quote Request"),
        "form_fields": fields,
        "submit_actions": ["email"],
        "email_to": f.get("email", ""),
        "email_subject": f.get("subject", "New website enquiry"),
        "button_text": f.get("submit", "Submit"),
        "button_size": "md", "button_width": "100", "input_size": "md",
        "show_labels": "yes", "mark_required": "yes",
        "row_gap": slider(14), "column_gap": slider(12),
        "success_message": f.get("success", ""),
        "field_border_radius": box(3), "field_border_width": box(1),
        "button_border_radius": R_BTN,
    }, globals_={
        "button_background_color": color_ref(GOLD),
        "button_text_color": color_ref(NAVY),
        "button_background_hover_color": color_ref(NAVY),
        "button_hover_color": color_ref(C["white"]),
        "field_background_color": color_ref(C["white"]),
        "field_text_color": color_ref(NAVY),
        "field_border_color": color_ref(C["border"]),
        "label_color": color_ref(NAVY),
        "mark_required_color": color_ref(GOLD_TEXT),
    })

    card = container([
        _h(props.get("title", ""), "h2", T["h_medium"], "center", upper=False),
        form,
    ], {
        "content_width": "full", "flex_direction": "column", "flex_gap": gap(18),
        "padding": dims(32, 32, 34, 32),
        "padding_mobile": dims(22, 18, 24, 18),
        "border_radius": R_CARD,
        "width": slider(props.get("card_width", 52), "%"),
        "width_tablet": slider(80, "%"), "width_mobile": slider(100, "%"),
        "margin": dims(0, "auto", 0, "auto"),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["white"])})

    sec = _sec([card], "dark", pad=dims(74, 0, 74, 0),
               anchor=props.get("anchor", "quote"))
    return _photo_ground(sec, props.get("image"),
                         props.get("position", "center center"),
                         props.get("overlay", 0.55))


@block("ww.gallery")
def ww_gallery(props):
    """Captioned project grid, grouped by the categories the client listed."""
    kids = []
    if props.get("title"):
        kids.append(_h(props["title"], "h2", T["h_medium"], "center"))
    if props.get("intro"):
        kids.append(container([_text(props["intro"], "center")], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(74, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    cols = props.get("columns", 3)
    w = _tracks([1] * cols, GUTTER)[0]
    cards = []
    for it in props.get("items", []):
        body = [_shot(it.get("image"), props.get("thumb_height", 230))]
        body.append(_h(it.get("title", ""), "h3", T["h_small"], "left",
                       upper=False))
        if it.get("text"):
            body.append(_text(it["text"], "left", small=True))
        cards.append(_card(body, w, pad=dims(14, 14, 20, 14)))
    kids.append(_row(cards, GUTTER, align="stretch",
                     extra={"flex_wrap": "wrap"}))
    if props.get("note"):
        kids.append(_text(props["note"], "center", small=True))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("ww.map")
def ww_map(props):
    """The per-city map the location template asks for.

    Elementor's own Google Maps widget, addressed to the city - no API key
    needed for the basic embed, and the client can retype the address in the
    editor without touching code.
    """
    kids = []
    if props.get("title"):
        kids.append(_h(props["title"], "h2", T["h_medium"], "center"))
    if props.get("intro"):
        kids.append(container([_text(props["intro"], "center")], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(74, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    kids.append(widget("google_maps", {
        "address": props.get("address", "San Antonio, TX"),
        "zoom": slider(props.get("zoom", 11)),
        "height": slider(props.get("height", 380)),
    }))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))
