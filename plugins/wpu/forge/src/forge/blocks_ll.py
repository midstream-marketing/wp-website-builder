"""
blocks_ll.py — Look Lovely LLC, Battle Creek MI.

A SYNTHESIS of three Dribbble shots the client's developer named, all three
rendered and read rather than guessed at. What they share is the brief;
where they differ, the supplied palette decides.

The palette decided more than the colours. Measured against white:

    purple  #543AB5   7.93   the ONLY text-safe brand colour
    magenta #E32998   4.17   buttons and large text
    orange  #EF512C   3.57   large text only
    lime    #DBEE16   1.29   invisible — and white on lime is 1.29 too

Lime can carry only PURPLE text (6.13). So lime exists exclusively as a flat
panel fill with purple type on it — which is reference 2's colour-block
device, arrived at from contrast arithmetic rather than from taste. That is
the single idea this family is built on.

Seven service categories against four colours means the colours ROTATE, which
is what reference 3 does with the coloured shapes behind its portraits. Each
category owns its colour across the home grid, its own page and the price
list, so the colour becomes wayfinding instead of decoration.

    ll.topbar      hours / phone / address strip
    ll.header      wordmark or logo, nav, pill CTA
    ll.hero        colour panel + photo, two-tone Fraunces display, pills
    ll.blockword   the oversized word spanning a panel and a photograph
    ll.sectionhead eyebrow + two-tone heading + intro
    ll.categories  the squircle grid: coloured shape offset behind each photo
    ll.filterpills the category pill row
    ll.split       photograph and copy, with a colour panel behind one side
    ll.pricelist   service rows as name + leader + price RANGE, by category
    ll.steps       numbered steps on the deep purple band
    ll.team        stylist cards (PLACEHOLDER content — none supplied)
    ll.gallery     deliberately uneven editorial photo grid with caps captions
    ll.statement   full-bleed closing band
    ll.faq         accordion, first answer open
    ll.bookform    appointment request with an explicit day and time window
    ll.contactcards phone / email / address / hours
    ll.map         the map pin — this salon has a real street address
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

PURPLE = "primary"         # #543AB5
DEEP = "secondary"         # #2E1F63 — the spotlight ground
MAGENTA = "accent"         # #E32998
LIME = "lllim01"           # #DBEE16 — panel fill only
ORANGE = "llorg01"         # #EF512C
T_LILAC = "llblu01"        # #EFE7FA
T_BLUSH = "llpnk01"        # #FDE8F4
T_LIME = "lllme02"         # #F4FAC4

# Which colours may carry WHITE text, and which demand purple. Lime never
# takes white: 1.29:1. This map is the guard rail for every tinted surface.
ON_TONE = {PURPLE: C["white"], DEEP: C["white"], MAGENTA: C["white"],
           ORANGE: C["white"], LIME: PURPLE,
           T_LILAC: PURPLE, T_BLUSH: PURPLE, T_LIME: PURPLE}

LL_PAD = dims(94, 0, 94, 0)
LL_PAD_T = dims(68, 24, 68, 24)
LL_PAD_M = dims(52, 18, 52, 18)
R_PILL = box(999)
R_CARD = box(18)
R_BLOB = box(28)
GUTTER = 26


# ─────────────────────────────── helpers ───────────────────────────────────

def _sec(children, bg="white", pad=None, anchor=None, extra=None):
    grounds = {"white": C["white"], "pale": C["surface"], "deep": DEEP,
               "lilac": T_LILAC, "blush": T_BLUSH, "limetint": T_LIME,
               "purple": PURPLE, "magenta": MAGENTA}
    s = {
        "content_width": "boxed",
        "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "flex_gap": gap(30),
        "padding": pad or LL_PAD,
        "padding_tablet": LL_PAD_T,
        "padding_mobile": LL_PAD_M,
        "background_background": "classic",
    }
    if anchor:
        s["_element_id"] = anchor
    if extra:
        s.update(extra)
    return container(children, s, globals_={
        "background_color": color_ref(grounds.get(bg, C["white"]))})


def _dark(bg):
    return bg in ("deep", "purple", "magenta")


def _panel(children, tone, pad=None, radius=R_CARD, extra=None, width=None):
    """A flat rectangle of brand colour with content on it. The text colour is
    taken from ON_TONE rather than chosen, which is what keeps lime legal."""
    s = {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(16),
        "padding": pad or dims(38, 34, 38, 34),
        "padding_mobile": dims(26, 20, 26, 20),
        "border_radius": radius,
        "background_background": "classic",
    }
    if width:
        s.update({"width": slider(width, "%"), "width_mobile": slider(100, "%")})
    if extra:
        s.update(extra)
    return container(children, s, globals_={"background_color": color_ref(tone)})


def _h(text, size="h2", token=None, align="left", tone=None):
    return widget("heading", {
        "title": text, "header_size": size, "align": align,
        "__typography__": typo_ref(token or T["h_medium"]),
    }, globals_={"title_color": color_ref(tone or C["ink_primary"])})


def _two_tone(lead, highlight, size="h2", token=None, align="left",
              base=None, tone=None):
    """Reference 3's two-tone heading. The REAL heading tag goes to the longer
    segment and the other is a div, so the page keeps exactly one H1."""
    base = base or C["ink_primary"]
    tone = tone or MAGENTA
    parts = [(lead, base), (highlight, tone)]
    longest = max(range(2), key=lambda i: len(parts[i][0] or ""))
    kids = []
    for i, (txt, col) in enumerate(parts):
        if not txt:
            continue
        kids.append(widget("heading", {
            "title": txt, "header_size": size if i == longest else "div",
            "align": align, "__typography__": typo_ref(token or T["h_large"]),
        }, globals_={"title_color": color_ref(col)}))
    return container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(0),
        "flex_align_items": "center" if align == "center" else "flex-start"})


def _eyebrow(text, align="left", tone=None):
    return widget("heading", {
        "title": text, "header_size": "div", "align": align,
        "__typography__": typo_ref(T["eyebrow"]),
    }, globals_={"title_color": color_ref(tone or MAGENTA)})


def _caption(text, align="left", tone=None):
    """Reference 1's tiny tracked caps label under a photograph."""
    return widget("heading", {
        "title": text, "header_size": "div", "align": align,
        "__typography__": typo_ref(T["eyebrow"]),
    }, globals_={"title_color": color_ref(tone or C["muted"])})


def _btn(label, href, style="magenta", icon_name=None):
    """Pill buttons, as all three references use.

        magenta  the primary. White on #E32998 is 4.17 — fine for the bold
                 button label it carries.
        dark     deep purple fill, white label.
        lime     lime fill with a PURPLE label. White on lime is 1.29, so the
                 label colour is not a choice here.
        ghost    white hairline, for dark grounds and photographs.
    """
    b = _button(label, href, "primary", icon_name or "")
    b["settings"].update({
        "border_radius": R_PILL,
        "text_padding": dims(16, 34, 16, 34),
        "__typography__": typo_ref(T["meta"]),
    })
    g = b["settings"].setdefault("__globals__", {})
    if style == "dark":
        g.update({"background_color": color_ref(DEEP),
                  "border_color": color_ref(DEEP),
                  "button_text_color": color_ref(C["white"]),
                  "button_background_hover_color": color_ref(MAGENTA),
                  "button_hover_border_color": color_ref(MAGENTA),
                  "hover_color": color_ref(C["white"])})
    elif style == "lime":
        g.update({"background_color": color_ref(LIME),
                  "border_color": color_ref(LIME),
                  "button_text_color": color_ref(PURPLE),
                  "button_background_hover_color": color_ref(PURPLE),
                  "button_hover_border_color": color_ref(PURPLE),
                  "hover_color": color_ref(C["white"])})
    elif style == "ghost":
        b["settings"].update({"border_border": "solid", "border_width": box(1)})
        g.update({"background_color": color_ref(C["transparent"]),
                  "button_text_color": color_ref(C["white"]),
                  "border_color": color_ref(C["white"]),
                  "button_background_hover_color": color_ref(C["white"]),
                  "button_hover_border_color": color_ref(C["white"]),
                  "hover_color": color_ref(DEEP)})
    else:
        g.update({"background_color": color_ref(MAGENTA),
                  "border_color": color_ref(MAGENTA),
                  "button_text_color": color_ref(C["white"]),
                  "button_background_hover_color": color_ref(DEEP),
                  "button_hover_border_color": color_ref(DEEP),
                  "hover_color": color_ref(C["white"])})
    return b


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


def _blob_shot(image, tone, height=300, offset=16):
    """Reference 3's device: the photograph sits on an offset rounded shape in
    the category's colour. Built as a coloured container whose child image is
    pulled up and across by a negative margin, so the colour peeks out on two
    edges."""
    img = _shot(image, height, R_CARD)
    # `_margin` with the underscore: on a WIDGET the plain `margin` key is not
    # a control (that is the container's), and it would validate as a global
    # nobody reads. The wrapper margin is what pulls the photo off the shape.
    img["settings"]["_margin"] = dims(-offset, 0, 0, -offset)
    return container([img], {
        "content_width": "full", "flex_direction": "column",
        "border_radius": R_BLOB,
        "margin": dims(offset, 0, 0, offset),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(tone)})


def _ticks(items, on_dark=False, tone=None, columns=1,
           container_px=KIT_CONTAINER):
    rows = []
    for t in items:
        mark = widget("icon", {
            "selected_icon": icon("fas fa-check"), "size": slider(12),
            "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref(
            tone or (C["white"] if on_dark else MAGENTA))})
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


def _card(kids, width=None, pad=None, tone=None, extra=None):
    s = {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(12),
        "padding": pad or dims(22, 22, 26, 22),
        "padding_mobile": dims(18, 16, 20, 16),
        "border_radius": R_CARD,
        "background_background": "classic",
    }
    if width:
        s.update({"width": slider(width, "%"), "width_mobile": slider(100, "%")})
    if extra:
        s.update(extra)
    return container(kids, s, globals_={
        "background_color": color_ref(tone or C["white"])})


def _head_stack(props, align="center", on_dark=False):
    kids = []
    base = C["white"] if on_dark else C["ink_primary"]
    acc = LIME if on_dark else MAGENTA
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], align,
                             LIME if on_dark else MAGENTA))
    if props.get("title"):
        if props.get("highlight"):
            kids.append(_two_tone(props["title"], props["highlight"], "h2",
                                  T["h_medium"], align, base, acc))
        else:
            kids.append(_h(props["title"], "h2", T["h_medium"], align, base))
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

@block("ll.topbar")
def ll_topbar(props):
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
    bar = _row(items, 26, align="center", justify="center",
               extra={"flex_wrap": "wrap"})
    return container([bar], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "padding": dims(9, 0, 9, 0),
        "padding_mobile": dims(8, 14, 8, 14),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(DEEP)})


@block("ll.wordmark")
def ll_wordmark(props):
    """The logo does not exist yet — the client is having one designed and
    only shared the palette. This renders a type-set wordmark in the brand
    serif as an explicit stand-in. Pass `logo` once the real file exists and
    it becomes an image widget with no other change."""
    if props.get("logo"):
        return widget("theme-site-logo", {
            "align": props.get("align", "left"),
            "width": slider(props.get("width", 190)), "image_size": "full",
            "image": media(props["logo"], props.get("business", ""))})
    name = widget("heading", {
        "title": props.get("business", "Look Lovely"),
        "header_size": "div", "align": props.get("align", "left"),
        "link": link(props.get("href", "/")),
        "__typography__": typo_ref(T["wordmark"]),
    }, globals_={"title_color": color_ref(
        C["white"] if props.get("on_dark") else PURPLE)})
    kids = [name]
    if props.get("tagline"):
        kids.append(widget("heading", {
            "title": props["tagline"], "header_size": "div",
            "align": props.get("align", "left"),
            "__typography__": typo_ref(T["eyebrow"]),
        }, globals_={"title_color": color_ref(
            LIME if props.get("on_dark") else MAGENTA)}))
    return container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(2),
        "flex_align_items": ("center" if props.get("align") == "center"
                             else "flex-start")})


@block("ll.header")
def ll_header(props):
    mark = ll_wordmark({"logo": props.get("logo"),
                        "business": props.get("business", "Look Lovely"),
                        "tagline": props.get("tagline"),
                        "width": props.get("logo_width", 190),
                        "href": "/", "align": "left"})
    nav = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"),
        "layout": "horizontal", "align_items": "center",
        "pointer": "underline", "animation_line": "fade",
        "menu_space_between": slider(props.get("menu_gap", 24)),
        "toggle_align": "right",
        "__typography__": typo_ref(T["meta"]),
    }, globals_={
        "color_menu_item": color_ref(C["ink_primary"]),
        "color_menu_item_hover": color_ref(MAGENTA),
        "color_menu_item_active": color_ref(MAGENTA),
        "pointer_color_menu_item_hover": color_ref(MAGENTA),
        "pointer_color_menu_item_active": color_ref(MAGENTA),
        "toggle_color": color_ref(PURPLE),
    })
    cta = _btn(props.get("cta_label", "Book an Appointment"),
               props.get("cta_url", "/book-an-appointment/"), "magenta")
    row = _row([
        _col([mark], 24, extra={"flex_justify_content": "center"}),
        _col([nav], 52, extra={"flex_justify_content": "center",
                               "flex_align_items": "center"}),
        _col([cta], 20, extra={"flex_justify_content": "center",
                               "flex_align_items": "flex-end"}),
    ], GUTTER, align="center",
        extra={"flex_wrap": "nowrap", "flex_wrap_tablet": "wrap"})
    return container([row], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "padding": dims(16, 0, 16, 0),
        "padding_mobile": dims(14, 14, 14, 14),
        "background_background": "classic",
        "sticky": "top", "sticky_on": ["desktop", "tablet", "mobile"],
        "sticky_offset": 0,
    }, globals_={"background_color": color_ref(C["white"])})


@block("ll.footer")
def ll_footer(props):
    brand = [ll_wordmark({"logo": props.get("logo"),
                          "business": props.get("business", "Look Lovely"),
                          "tagline": props.get("tagline"),
                          "on_dark": True, "href": "/", "align": "left"})]
    if props.get("blurb"):
        brand.append(_text(props["blurb"], "left", on_dark=True, small=True))
    if props.get("social"):
        brand.append(_row([widget("icon", {
            "selected_icon": icon(s.get("icon", "fab fa-facebook-f")),
            "size": slider(15), "align": "center", "view": "default",
            "link": link(s.get("url", "#")),
        }, globals_={"primary_color": color_ref(LIME)})
            for s in props["social"]], 16, align="center",
            extra={"flex_wrap": "wrap", "flex_direction_mobile": "row"}))

    cols = props.get("columns", [])
    widths = _tracks([1.5] + [1] * len(cols), GUTTER)
    body = [_col(brand, widths[0], extra={"flex_gap": gap(16)})]
    for i, c in enumerate(cols):
        kids = [widget("heading", {
            "title": c.get("title", ""), "header_size": "div", "align": "left",
            "__typography__": typo_ref(T["eyebrow"]),
        }, globals_={"title_color": color_ref(LIME)})]
        for l in c.get("links", []):
            r = []
            if l.get("icon"):
                r.append(widget("icon", {
                    "selected_icon": icon(l["icon"]), "size": slider(12),
                    "align": "center", "view": "default",
                }, globals_={"primary_color": color_ref(MAGENTA)}))
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
    }, globals_={"background_color": color_ref(PURPLE)})
    legal = widget("heading", {
        "title": props.get("legal", ""), "header_size": "div",
        "align": "center", "__typography__": typo_ref(T["body_small"]),
    }, globals_={"title_color": color_ref(C["white"])})

    return container([
        _row(body, GUTTER, align="flex-start", extra={"flex_wrap": "wrap"}),
        rule, legal,
    ], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column", "flex_gap": gap(28),
        "padding": dims(72, 0, 32, 0),
        "padding_mobile": dims(50, 18, 26, 18),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(DEEP)})


# ─────────────────────────────── sections ──────────────────────────────────

@block("ll.hero")
def ll_hero(props):
    """Colour panel on one side, photograph on the other — reference 2's
    structure, with reference 3's two-tone display heading on top."""
    tone = props.get("tone", T_BLUSH)
    on = ON_TONE.get(tone, C["ink_primary"])
    acc = PURPLE if tone in (LIME, T_LIME, T_BLUSH, T_LILAC) else C["white"]
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], "left", acc))
    if props.get("title"):
        kids.append(_two_tone(props["title"], props.get("highlight", ""),
                              "h1", T["hero"], "left", on, acc))
    if props.get("intro"):
        kids.append(widget("text-editor", {
            "editor": "<p>%s</p>" % props["intro"], "align": "left",
        }, globals_={"text_color": color_ref(on)}))
    if props.get("ticks"):
        kids.append(_ticks(props["ticks"], tone=acc,
                           container_px=KIT_CONTAINER * 0.46))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"),
                         "magenta" if tone != MAGENTA else "dark"))
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props.get("alt_url", "#"), "dark"))
    if btns:
        kids.append(_row(btns, 12, align="center",
                         extra={"flex_wrap": "wrap",
                                "flex_direction_mobile": "column",
                                "padding": dims(8, 0, 0, 0)}))

    w = _tracks([1, 1], GUTTER + 10)
    panel = _panel(kids, tone, pad=dims(54, 46, 58, 46), width=None,
                   extra={"flex_justify_content": "center"})
    photo = _shot(props.get("image"), props.get("image_height", 520), R_CARD)
    pair = [_col([panel], w[0]), _col([photo], w[1])]
    if props.get("flip"):
        pair.reverse()
    return _sec([_row(pair, GUTTER + 10, align="stretch",
                      extra={"flex_wrap": "wrap"})],
                props.get("bg", "white"),
                pad=props.get("pad") or dims(48, 0, 72, 0),
                anchor=props.get("anchor"))


@block("ll.blockword")
def ll_blockword(props):
    """Reference 2's signature: an oversized word spanning a colour panel and
    a photograph. Elementor cannot split one glyph run across two grounds, so
    it is built as two halves of the phrase sitting flush against the seam —
    the same read, reproduced with the tools that exist."""
    tone = props.get("tone", LIME)
    on = ON_TONE.get(tone, PURPLE)
    left = _panel([
        widget("heading", {
            "title": props.get("word_a", ""), "header_size": "div",
            "align": "right", "__typography__": typo_ref(T["caps_hero"]),
        }, globals_={"title_color": color_ref(on)}),
    ], tone, pad=dims(56, 26, 56, 40),
        extra={"flex_justify_content": "center",
               "flex_align_items": "flex-end"})
    right_kids = [widget("heading", {
        "title": props.get("word_b", ""), "header_size": "div", "align": "left",
        "__typography__": typo_ref(T["caps_hero"]),
    }, globals_={"title_color": color_ref(C["white"])})]
    photo = container(right_kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_justify_content": "center",
        "padding": dims(56, 40, 56, 26),
        "border_radius": R_CARD,
        "background_background": "classic",
        "background_size": "cover", "background_position": "center center",
        "background_repeat": "no-repeat",
        "background_overlay_background": "classic",
        "background_overlay_opacity": slider(props.get("overlay", 0.34)),
    }, globals_={"background_color": color_ref(DEEP)})
    img = props.get("image")
    if img and img.get("url"):
        photo["settings"]["background_image"] = media(img["url"],
                                                      img.get("alt", ""))
        photo["settings"].setdefault("__globals__", {})[
            "background_overlay_color"] = color_ref(DEEP)
    w = _tracks([1, 1], 0)
    seam = _row([_col([left], w[0]), _col([photo], w[1])], 0,
                align="stretch", extra={"flex_wrap": "wrap"})
    kids = [seam]
    if props.get("caption"):
        kids.append(container([_text(props["caption"], "center")], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(72, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("ll.sectionhead")
def ll_sectionhead(props):
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


@block("ll.categories")
def ll_categories(props):
    """The squircle grid. Each category photograph sits on an offset rounded
    shape in that category's own colour."""
    on_dark = _dark(props.get("bg", "white"))
    kids = _head_stack(props, "center", on_dark)
    cols = props.get("columns", 3)
    w = _tracks([1] * cols, GUTTER + 8)[0]
    cards = []
    for it in props.get("items", []):
        tone = it.get("tone", MAGENTA)
        body = [_blob_shot(it.get("image"), tone,
                           props.get("thumb_height", 260))]
        body.append(_caption(it.get("label", ""), "left", tone))
        body.append(_h(it.get("title", ""), "h3", T["h_small"], "left",
                       C["white"] if on_dark else C["ink_primary"]))
        if it.get("text"):
            body.append(_text(it["text"], "left", on_dark=on_dark, small=True))
        if it.get("price"):
            body.append(widget("heading", {
                "title": it["price"], "header_size": "div", "align": "left",
                "__typography__": typo_ref(T["meta"]),
            }, globals_={"title_color": color_ref(
                LIME if on_dark else PURPLE)}))
        if it.get("href"):
            b = _btn(props.get("action_label", "View Treatments"), it["href"],
                     "ghost" if on_dark else "dark")
            b["settings"]["text_padding"] = dims(12, 24, 12, 24)
            body.append(container([b], {
                "content_width": "full", "flex_direction": "column",
                "flex_align_items": "flex-start",
                "padding": dims(6, 0, 0, 0)}))
        cards.append(_col(body, w, extra={"flex_gap": gap(10)}))
    kids.append(_row(cards, GUTTER + 8, align="flex-start",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("ll.filterpills")
def ll_filterpills(props):
    pills = []
    for it in props.get("items", []):
        active = it.get("active")
        b = _btn(it.get("label", ""), it.get("href", "#"),
                 "magenta" if active else "ghostlight")
        if not active:
            g = b["settings"].setdefault("__globals__", {})
            b["settings"].update({"border_border": "solid",
                                  "border_width": box(1)})
            g.update({"background_color": color_ref(C["white"]),
                      "button_text_color": color_ref(PURPLE),
                      "border_color": color_ref(C["border"]),
                      "button_background_hover_color": color_ref(PURPLE),
                      "button_hover_border_color": color_ref(PURPLE),
                      "hover_color": color_ref(C["white"])})
        b["settings"]["text_padding"] = dims(12, 24, 12, 24)
        pills.append(b)
    return _sec([_row(pills, 10, align="center", justify="center",
                      extra={"flex_wrap": "wrap"})],
                props.get("bg", "pale"),
                pad=dims(30, 0, 30, 0), anchor=props.get("anchor"))


@block("ll.split")
def ll_split(props):
    on_dark = _dark(props.get("bg", "white"))
    base = C["white"] if on_dark else C["ink_primary"]
    acc = LIME if on_dark else MAGENTA
    copy = []
    if props.get("eyebrow"):
        copy.append(_eyebrow(props["eyebrow"], "left", acc))
    if props.get("title"):
        if props.get("highlight"):
            copy.append(_two_tone(props["title"], props["highlight"], "h2",
                                  T["h_medium"], "left", base, acc))
        else:
            copy.append(_h(props["title"], "h2", T["h_medium"], "left", base))
    for p in props.get("paragraphs", []):
        copy.append(_text(p, "left", on_dark=on_dark))
    if props.get("list_title"):
        copy.append(_h(props["list_title"], "h3", T["h_small"], "left", base))
    if props.get("ticks"):
        copy.append(_ticks(props["ticks"], on_dark, acc,
                           props.get("tick_columns", 1),
                           container_px=KIT_CONTAINER * 0.48))
    if props.get("footnote"):
        copy.append(_text(props["footnote"], "left", on_dark=on_dark,
                          small=True))
    if props.get("cta_label"):
        copy.append(container([
            _btn(props["cta_label"], props.get("cta_url", "#"),
                 "ghost" if on_dark else "magenta")], {
            "content_width": "full", "flex_direction": "column",
            "flex_align_items": "flex-start", "padding": dims(8, 0, 0, 0)}))

    tone = props.get("tone")
    shot = (_blob_shot(props.get("image"), tone, props.get("image_height", 460))
            if tone else _shot(props.get("image"), props.get("image_height", 460)))
    w = _tracks([1, 1], GUTTER + 14)
    pair = [_col([shot], w[0]), _col(copy, w[1], extra={"flex_gap": gap(16)})]
    if props.get("flip"):
        pair.reverse()
    kids = _head_stack({"title": props.get("section_title")}, "center", on_dark)
    kids.append(_row(pair, GUTTER + 14, align="center",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("ll.pricelist")
def ll_pricelist(props):
    """Service rows as name + price RANGE, grouped by category, the group
    marked in that category's colour. Ranges stay ranges."""
    on_dark = _dark(props.get("bg", "white"))
    kids = _head_stack(props, "center", on_dark)
    groups = props.get("groups", [])
    cols = props.get("columns", 2)
    w = _tracks([1] * cols, GUTTER + 8)[0]
    cells = []
    for grp in groups:
        tone = grp.get("tone", MAGENTA)
        head = [_caption(grp.get("label", "Category"), "left", tone),
                _h(grp.get("title", ""), "h3", T["h_small"], "left",
                   C["white"] if on_dark else C["ink_primary"])]
        rows = []
        for it in grp.get("items", []):
            name = widget("heading", {
                "title": it.get("name", ""), "header_size": "div",
                "align": "left", "__typography__": typo_ref(T["body_small"]),
            }, globals_={"title_color": color_ref(
                C["white"] if on_dark else C["ink_primary"])})
            price = widget("heading", {
                "title": it.get("price", ""), "header_size": "div",
                "align": "right", "__typography__": typo_ref(T["meta"]),
            }, globals_={"title_color": color_ref(
                LIME if on_dark else PURPLE)})
            rows.append(_row([
                _col([name], 64), _col([price], 32,
                                       extra={"flex_align_items": "flex-end"}),
            ], 8, align="center",
                extra={"flex_wrap": "nowrap",
                       "flex_direction_mobile": "row",
                       "padding": dims(9, 0, 9, 0),
                       "border_border": "solid",
                       "border_width": dims(0, 0, 1, 0),
                       "__globals__": {"border_color": color_ref(
                           PURPLE if on_dark else C["border"])}}))
        if grp.get("href"):
            b = _btn(props.get("action_label", "Book This"), grp["href"],
                     "ghost" if on_dark else "lime")
            b["settings"]["text_padding"] = dims(11, 22, 11, 22)
            rows.append(container([b], {
                "content_width": "full", "flex_direction": "column",
                "flex_align_items": "flex-start",
                "padding": dims(14, 0, 0, 0)}))
        cells.append(_card(head + rows, w,
                           pad=dims(26, 26, 24, 26),
                           tone=(None if on_dark else C["white"]),
                           extra={"flex_gap": gap(4)}))
    kids.append(_row(cells, GUTTER + 8, align="flex-start",
                     extra={"flex_wrap": "wrap"}))
    if props.get("note"):
        kids.append(container([_text(props["note"], "center",
                                     on_dark=on_dark, small=True)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(80, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    return _sec(kids, props.get("bg", "pale"), anchor=props.get("anchor"))


@block("ll.steps")
def ll_steps(props):
    on_dark = _dark(props.get("bg", "deep"))
    kids = _head_stack(props, "center", on_dark)
    cols = props.get("columns", 4)
    w = _tracks([1] * cols, GUTTER)[0]
    cells = []
    for i, it in enumerate(props.get("items", []), 1):
        num = container([widget("heading", {
            "title": "%02d" % i, "header_size": "div", "align": "center",
            "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(PURPLE)})], {
            "content_width": "full", "flex_direction": "column",
            "flex_justify_content": "center", "flex_align_items": "center",
            "width": slider(52), "min_height": slider(52),
            "_flex_shrink": "0", "border_radius": box(999),
            "background_background": "classic",
        }, globals_={"background_color": color_ref(LIME)})
        cells.append(_col([
            num,
            _h(it.get("title", ""), "h3", T["h_small"], "left",
               C["white"] if on_dark else C["ink_primary"]),
            _text(it.get("text", ""), "left", on_dark=on_dark, small=True),
        ], w, extra={"flex_gap": gap(12)}))
    kids.append(_row(cells, GUTTER, align="flex-start",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "deep"), anchor=props.get("anchor"))


@block("ll.team")
def ll_team(props):
    on_dark = _dark(props.get("bg", "white"))
    kids = _head_stack(props, "center", on_dark)
    cols = props.get("columns", 4)
    w = _tracks([1] * cols, GUTTER)[0]
    cards = []
    for i, it in enumerate(props.get("items", [])):
        tone = it.get("tone", (MAGENTA, PURPLE, ORANGE, LIME)[i % 4])
        cards.append(_col([
            _blob_shot(it.get("image"), tone, props.get("thumb_height", 260)),
            _h(it.get("name", ""), "h3", T["h_small"], "left",
               C["white"] if on_dark else C["ink_primary"]),
            _caption(it.get("role", ""), "left", tone),
            _text(it.get("bio", ""), "left", on_dark=on_dark, small=True),
        ], w, extra={"flex_gap": gap(8)}))
    kids.append(_row(cards, GUTTER, align="flex-start",
                     extra={"flex_wrap": "wrap"}))
    if props.get("note"):
        kids.append(_text(props["note"], "center", on_dark=on_dark, small=True))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("ll.gallery")
def ll_gallery(props):
    """Deliberately uneven — reference 1's gallery is a scatter, not a tile
    grid, so the column ratios and the image heights both vary."""
    on_dark = _dark(props.get("bg", "white"))
    kids = _head_stack(props, "center", on_dark)
    items = props.get("items", [])
    rows_spec = props.get("rows") or [[1.3, 1], [1, 1.3]]
    idx = 0
    out = []
    while idx < len(items):
        ratios = rows_spec[(len(out)) % len(rows_spec)]
        w = _tracks(ratios, GUTTER)
        cells = []
        for j, ww in enumerate(w):
            if idx >= len(items):
                break
            it = items[idx]; idx += 1
            h = it.get("height", 330 if ratios[j] >= 1.2 else 270)
            body = [_shot(it.get("image"), h, R_CARD)]
            if it.get("caption"):
                body.append(_caption(it["caption"], "left",
                                     it.get("tone", C["muted"])))
            cells.append(_col(body, ww, extra={"flex_gap": gap(8)}))
        out.append(_row(cells, GUTTER, align="flex-start",
                        extra={"flex_wrap": "wrap"}))
    kids += out
    if props.get("note"):
        kids.append(_text(props["note"], "center", on_dark=on_dark, small=True))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("ll.statement")
def ll_statement(props):
    tone = props.get("tone", DEEP)
    on = ON_TONE.get(tone, C["white"])
    acc = LIME if tone in (DEEP, PURPLE, MAGENTA) else PURPLE
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], "center", acc))
    if props.get("title"):
        kids.append(_two_tone(props["title"], props.get("highlight", ""),
                              "h2", T["h_large"], "center", on, acc))
    if props.get("text"):
        kids.append(container([widget("text-editor", {
            "editor": "<p>%s</p>" % props["text"], "align": "center",
        }, globals_={"text_color": color_ref(on)})], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(68, "%"), "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")}))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props.get("cta_url", "#"),
                         "lime" if tone in (DEEP, PURPLE) else "dark"))
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props.get("alt_url", "#"),
                         "ghost" if tone in (DEEP, PURPLE, MAGENTA) else "dark"))
    if btns:
        kids.append(_row(btns, 12, align="center", justify="center",
                         extra={"flex_wrap": "wrap",
                                "flex_direction_mobile": "column",
                                "padding": dims(8, 0, 0, 0)}))
    bg = {DEEP: "deep", PURPLE: "purple", MAGENTA: "magenta",
          T_LILAC: "lilac", T_BLUSH: "blush", T_LIME: "limetint"}.get(tone, "deep")
    return _sec(kids, bg, pad=dims(86, 0, 86, 0),
                anchor=props.get("anchor"),
                extra={"flex_align_items": "center"})


@block("ll.faq")
def ll_faq(props):
    on_dark = _dark(props.get("bg", "white"))
    kids = _head_stack(props, "center", on_dark)
    kids.append(container([_faq(props.get("items", []), first_open=True)], {
        "content_width": "full", "flex_direction": "column",
        "width": slider(84, "%"), "width_mobile": slider(100, "%"),
        "margin": dims(0, "auto", 0, "auto")}))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("ll.contactcards")
def ll_contactcards(props):
    on_dark = _dark(props.get("bg", "white"))
    kids = _head_stack(props, "center", on_dark)
    cols = props.get("columns", 4)
    w = _tracks([1] * cols, GUTTER)[0]
    tints = [T_BLUSH, T_LILAC, T_LIME, T_BLUSH]
    cards = []
    for i, it in enumerate(props.get("items", [])):
        tint = it.get("tone", tints[i % len(tints)])
        body = []
        if it.get("icon"):
            body.append(widget("icon", {
                "selected_icon": icon(it["icon"]), "size": slider(20),
                "align": "left", "view": "default",
            }, globals_={"primary_color": color_ref(MAGENTA)}))
        body.append(_caption(it.get("label", ""), "left", PURPLE))
        val = widget("heading", {
            "title": it.get("value", ""), "header_size": "div", "align": "left",
            "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(C["ink_primary"])})
        if it.get("href"):
            val["settings"]["link"] = link(it["href"])
        body.append(val)
        if it.get("text"):
            body.append(_text(it["text"], "left", small=True))
        cards.append(_card(body, w, tone=tint))
    kids.append(_row(cards, GUTTER, align="stretch",
                     extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))


@block("ll.bookform")
def ll_bookform(props):
    """The appointment request. Day and time window are explicit choices, as
    reference 3's slot picker is — but these are real form fields that email
    the salon, which is what the client agreed to. No availability, no
    payment: both were deliberately out of scope."""
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
        "form_name": f.get("form_name", "Appointment Request"),
        "form_fields": fields,
        "submit_actions": ["email"],
        "email_to": f.get("email", ""),
        "email_subject": f.get("subject", "New appointment request"),
        "button_text": f.get("submit", "Request My Appointment"),
        "button_size": "md", "button_width": "100", "input_size": "md",
        "show_labels": "yes", "mark_required": "yes",
        "row_gap": slider(14), "column_gap": slider(12),
        "success_message": f.get("success", ""),
        "field_border_radius": box(10), "field_border_width": box(1),
        "button_border_radius": R_PILL,
    }, globals_={
        "button_background_color": color_ref(MAGENTA),
        "button_text_color": color_ref(C["white"]),
        "button_background_hover_color": color_ref(DEEP),
        "button_hover_color": color_ref(C["white"]),
        "field_background_color": color_ref(C["white"]),
        "field_text_color": color_ref(C["ink_primary"]),
        "field_border_color": color_ref(C["border"]),
        "label_color": color_ref(PURPLE),
        "mark_required_color": color_ref(MAGENTA),
    })

    card_kids = []
    if props.get("title"):
        card_kids.append(_h(props["title"], "h2", T["h_medium"], "left"))
    if props.get("intro"):
        card_kids.append(_text(props["intro"], "left"))
    card_kids.append(form)
    card = container(card_kids, {
        "content_width": "full", "flex_direction": "column", "flex_gap": gap(18),
        "padding": dims(38, 36, 40, 36),
        "padding_mobile": dims(24, 18, 26, 18),
        "border_radius": R_CARD,
        "width": slider(props.get("card_width", 100), "%"),
        "width_mobile": slider(100, "%"),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["white"])})

    side = props.get("side")
    if side:
        sk = []
        if side.get("eyebrow"):
            sk.append(_eyebrow(side["eyebrow"], "left",
                               LIME if on_dark else MAGENTA))
        if side.get("title"):
            sk.append(_h(side["title"], "h2", T["h_medium"], "left",
                         C["white"] if on_dark else C["ink_primary"]))
        for p in side.get("paragraphs", []):
            sk.append(_text(p, "left", on_dark=on_dark))
        if side.get("ticks"):
            sk.append(_ticks(side["ticks"], on_dark,
                             LIME if on_dark else MAGENTA,
                             container_px=KIT_CONTAINER * 0.45))
        w = _tracks([1, 1.2], GUTTER + 14)
        body = _row([_col(sk, w[0], extra={"flex_gap": gap(16)}),
                     _col([card], w[1])], GUTTER + 14,
                    align="flex-start", extra={"flex_wrap": "wrap"})
    else:
        body = container([card], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(props.get("outer_width", 74), "%"),
            "width_mobile": slider(100, "%"),
            "margin": dims(0, "auto", 0, "auto")})
    return _sec([body], props.get("bg", "pale"),
                anchor=props.get("anchor", "book"))


@block("ll.map")
def ll_map(props):
    on_dark = _dark(props.get("bg", "white"))
    kids = _head_stack(props, "center", on_dark)
    kids.append(widget("google_maps", {
        "address": props.get("address", ""),
        "zoom": slider(props.get("zoom", 14)),
        "height": slider(props.get("height", 420)),
    }))
    return _sec(kids, props.get("bg", "white"), anchor=props.get("anchor"))
