"""
blocks_fatima.py — the Live Fatima chrome.

Header and footer for the Confraternity of Our Lady of Fatima, matched to the
Adobe XD artboard "Web 1920 – 4". Every number here is read from XD Specs Mode,
not sampled off a screenshot; the measurements are written up in
`clients/live-fatima/DESIGN-SPEC.md`.

    header.fatima    solid brown bar, image wordmark left, Lora nav, orange
                     Donate button
    footer.fatima    same brown ground, wordmark over an address column and a
                     Site link column, three legal lines beneath

Why these are their own factories rather than props on the existing chrome:

  * `header.simple` paints a WHITE bar with dark links and a phone-icon CTA.
  * `header.heritage` is the closest — a dark bar with reversed links — but it
    runs an underline pointer the comp does not have, and its nav is
    `T["meta"]`, a 13px sans. Live Fatima's nav is the SERIF face at 16px,
    which is two steps off any token in the scale.

That last point forces the one deliberate departure in this module: the nav and
the button label carry **inline typography instead of a global reference**.
Adding `Lora 16/20` and `Montserrat 15/19` to `tokens.py` would change the type
scale for every other kit, and these two values exist only because this comp
says so. Everything else — colour, spacing, structure — goes through the
tokens like any other family.

The bar is `content_width: full`, not boxed. The comp's header spans x=37 to
x=1861 of a 1920 artboard; forcing it into the 1240 kit container would centre
a narrow strip in the middle of a wide brown band and look nothing like the
design.
"""
from __future__ import annotations

from .core import (
    container, widget, repeater_item, slider, dims, box, media, link,
    gap, color_ref, typo_ref,
)
from .tokens import C, T
from .blocks import block, _row, _col, _tracks, _button


# ─────────────────────────── measured from the XD ───────────────────────────
# Header bar: Rectangle 1, 1920x160, #4A3B32 (-> `secondary`).
BAR_H = 160
# Logo: Group 36, an image 443x118 at (37,21). 160 - 118 = 42, so 21 top and
# bottom is what produces the 160 bar — the padding IS the measurement.
LOGO_W = 443
LOGO_PAD_Y = 21
# Side padding. The comp starts the logo at x=37 and ends the button at 1861.
EDGE_X = 37
# Nav: Lora Regular 16/20, #FFFFFF, a consistent 46px between every pair.
NAV_FONT = "Lora"
NAV_SIZE = 16
NAV_LINE = 20
NAV_GAP = 46
# Donate: Rectangle 4, 136x41 at (1725,61), #E04120 (-> `accent`), radius 6.
# Label "Donate" is 56x19 in Montserrat Regular 15/19 — NOT Lora like the
# links beside it, which is easy to get wrong by eye.
BTN_W, BTN_H = 136, 41
BTN_RADIUS = 6
BTN_FONT = "Montserrat"
BTN_SIZE = 15
BTN_LINE = 19
BTN_PAD_X = (BTN_W - 56) // 2   # 40
BTN_PAD_Y = (BTN_H - BTN_LINE) // 2  # 11


def _inline_type(prefix: str, family: str, size: int, line: int,
                 weight: str = "400", spacing: float = 0) -> dict:
    """Inline typography for one Elementor control group.

    Elementor only reads the individual `*_font_*` keys once the group's own
    `*_typography` switch is set to "custom"; without it the whole block is
    ignored silently and the widget falls back to the kit default.
    """
    return {
        f"{prefix}_typography": "custom",
        f"{prefix}_font_family": family,
        f"{prefix}_font_size": slider(size),
        f"{prefix}_font_weight": weight,
        # Line height in PX, matching how the comp states it. The default unit
        # for this control is em, and 20em would collapse the bar.
        f"{prefix}_line_height": slider(line),
        f"{prefix}_letter_spacing": slider(spacing),
    }


@block("header.fatima")
def header_fatima(props):
    """Brown bar, wordmark left, Lora nav right, orange Donate button."""
    logo = widget("theme-site-logo", {
        "align": "left",
        "width": slider(props.get("logo_width", LOGO_W)),
        # Left unset unless the client supplies a URL, so the widget uses Site
        # Identity rather than importing a link that may 404.
        **({"image": media(props["logo"], props.get("business", ""))}
           if props.get("logo") else {}),
    })

    nav = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"),
        "layout": "horizontal",
        "align_items": "center",
        # The comp shows no underline, rule or box on the resting or active
        # item — just the label.
        "pointer": "none",
        "menu_space_between": slider(props.get("menu_gap", NAV_GAP)),
        "toggle_align": "right",
        **_inline_type("menu_typography", NAV_FONT, NAV_SIZE, NAV_LINE),
    }, globals_={
        "color_menu_item": color_ref(C["white"]),
        "color_menu_item_hover": color_ref("accent"),
        "color_menu_item_active": color_ref("accent"),
    })

    # accent == #E04120. No icon: the comp's button is the word alone.
    cta = _button(props["cta"]["label"], props["cta"]["href"], "accent", None)
    cta["settings"]["border_radius"] = box(BTN_RADIUS)
    cta["settings"]["text_padding"] = dims(BTN_PAD_Y, BTN_PAD_X,
                                           BTN_PAD_Y, BTN_PAD_X)
    # `_button` draws a 1px border in the fill colour. Harmless but untrue to
    # the comp, which has none, and it would show if the fill is ever themed.
    cta["settings"]["border_border"] = "none"
    cta["settings"].pop("border_width", None)
    cta["settings"].update(_inline_type("typography", BTN_FONT,
                                        BTN_SIZE, BTN_LINE))

    # Logo 443, nav band ~848, button 136 across 1824 of usable width. The nav
    # column is justified to its end so the links sit against the button the
    # way the comp has them, rather than floating mid-bar.
    w_logo, w_nav, w_cta = _tracks([25, 61, 14], 24)

    return container([
        _row([
            _col([logo], w_logo, extra={"flex_justify_content": "center"}),
            _col([nav], w_nav, extra={"flex_justify_content": "center",
                                      "flex_align_items": "flex-end"}),
            _col([cta], w_cta, extra={"flex_justify_content": "center",
                                      "flex_align_items": "flex-end"}),
        ], gap_px=24, align="center")
    ], {
        "content_width": "full",
        "flex_direction": "row",
        "padding": dims(LOGO_PAD_Y, EDGE_X, LOGO_PAD_Y, EDGE_X),
        "padding_tablet": dims(16, 24, 16, 24),
        "padding_mobile": dims(12, 20, 12, 20),
        "background_background": "classic",
    }, globals_={"background_color": color_ref("secondary")})


@block("footer.fatima")
def footer_fatima(props):
    """Wordmark, address column, Site links, three legal lines. Brown ground.

    Type styles are the comp's own (Montserrat 18 for the columns, Bold 20 for
    the column heading, 15 for the legal block). The per-element X/Y/W/H were
    not extractable from Specs Mode in the same pass as the header — the
    footer sits 8,000px down the artboard — so the COLUMN GEOMETRY here is
    proportional rather than measured. Colour, type and content are exact.
    """
    logo = widget("theme-site-logo", {
        "align": "left",
        "width": slider(props.get("logo_width", LOGO_W)),
        **({"image": media(props["logo"], props.get("business", ""))}
           if props.get("logo") else {}),
    })

    def line(text, size=18, weight="400", href=""):
        """One white line of Montserrat, optionally linked."""
        if href:
            return widget("button", {
                "text": text,
                "link": link(href),
                "selected_icon": {"value": "", "library": ""},
                "button_type": "link",
                "text_padding": dims(0, 0, 0, 0),
                "border_border": "none",
                "background_background": "",
                **_inline_type("typography", "Montserrat", size, size + 12,
                               weight),
            }, globals_={"button_text_color": color_ref(C["white"])})
        return widget("text-editor", {
            "editor": f"<p>{text}</p>",
            "align": "left",
            **_inline_type("typography", "Montserrat", size, size + 12, weight),
        }, globals_={"text_color": color_ref(C["white"])})

    address = _col(
        [line(t) for t in props.get("address", [])],
        None, extra={"flex_gap": gap(4)})

    site_col = _col([
        # Montserrat Bold 20 — the one bold thing in the footer.
        widget("heading", {
            "title": props.get("links_title", "Site"),
            "header_size": "h4",
            "align": "left",
            **_inline_type("typography", "Montserrat", 20, 30, "700"),
        }, globals_={"title_color": color_ref(C["white"])}),
        *[line(i["text"], href=i.get("href", ""))
          for i in props.get("links", [])],
    ], None, extra={"flex_gap": gap(6)})

    legal = _col([line(t, size=15) for t in props.get("legal", [])],
                 None, extra={"flex_gap": gap(2)})

    w_addr, w_links, w_spare = _tracks([38, 30, 32], 40)
    address["settings"]["width"] = {"unit": "%", "size": w_addr, "sizes": []}
    site_col["settings"]["width"] = {"unit": "%", "size": w_links, "sizes": []}

    return container([
        logo,
        _row([address, site_col], gap_px=40, align="flex-start"),
        legal,
    ], {
        "content_width": "full",
        "flex_direction": "column",
        "flex_gap": gap(48, 48),
        "padding": dims(72, EDGE_X + 75, 56, EDGE_X + 75),
        "padding_tablet": dims(56, 32, 44, 32),
        "padding_mobile": dims(44, 20, 36, 20),
        "background_background": "classic",
    }, globals_={"background_color": color_ref("secondary")})


# ══════════════════════════════════════════════════════════════════════════
#  Content blocks — About and Ways to Give (added 2026-09-07)
# ══════════════════════════════════════════════════════════════════════════
#
# The header and footer above were measured off the XD artboard. These are
# different: they are matched to the pages ALREADY BUILT on
# livefatimadev.wpenginepowered.com, because Home and Become a Member exist
# there and the instruction is to follow that design rather than the comp.
#
# What the built pages actually do, read off the live markup:
#
#   * WHITE is the primary section ground (18 of the container backgrounds on
#     Become a Member), with cream `surface` as the alternate and the brown
#     `secondary` reserved for full-bleed bands.
#   * The vermillion `accent` (#E04120) is a BAND and a BUTTON colour, used 5
#     times on that page — it is the loudest thing in the palette and it is
#     never body text.
#   * Cards run a 17px radius; that value dominates the built CSS.
#   * Lora headings in brown or reversed white; Montserrat body.
#
# Nothing below names a hex. The dev site's Global Kit was imported from
# `clients/live-fatima/intake.json`, so these tokens resolve to exactly the
# colours already on the site — which is what makes a forge-built page drop in
# beside a hand-built one without a seam.

from .blocks import _heading, _text, KIT_CONTAINER  # noqa: E402
from .core import icon  # noqa: E402

FAT_PAD = dims(88, 0, 88, 0)
FAT_PAD_T = dims(64, 24, 64, 24)
FAT_PAD_M = dims(52, 20, 52, 20)
R_FAT = box(17)          # measured off the built pages
R_FAT_BTN = box(6)       # matches the header Donate button
FAT_GUTTER = 26


def _fat_section(children, bg="white", pad=None, extra=None, anchor=None):
    """`anchor` puts an id on the section so a jump-nav link can reach it.

    Added for the Resources page, whose brief specifies a sticky category bar.
    A link needs a real scroll target: an anchor on the SECTION, not on a
    heading inside it, so the category's own top edge is what lands under the
    sticky bar rather than the heading being hidden behind it.
    """
    grounds = {"white": C["white"], "cream": C["surface"],
               "tan": C["surface_alt"], "dark": "secondary",
               "accent": C["accent_fill"]}
    s = {
        "content_width": "boxed",
        "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "flex_gap": gap(34),
        "padding": pad or FAT_PAD,
        "padding_tablet": FAT_PAD_T,
        "padding_mobile": FAT_PAD_M,
        "background_background": "classic",
    }
    if anchor:
        s["_element_id"] = anchor
    if extra:
        s.update(extra)
    return container(children, s, globals_={
        "background_color": color_ref(grounds.get(bg, C["white"]))})


def _fat_dk(bg):
    return bg in ("dark", "accent")


def _fat_button(label, href, style="accent"):
    """The site's button: vermillion fill, 6px radius, Montserrat 15/19 — the
    same object as the header Donate button, which is the only button style
    the built pages use."""
    if style == "outline":
        b = _button(label, href, "ghost", "")
        b["settings"]["__globals__"].update({
            "button_text_color": color_ref(C["white"]),
            "border_color": color_ref(C["white"])})
    elif style == "brown":
        b = _button(label, href, "primary", "")
        b["settings"]["__globals__"].update({
            "button_background_color": color_ref("secondary"),
            "button_text_color": color_ref(C["white"])})
    else:
        b = _button(label, href, "accent", "")
        b["settings"]["__globals__"].update({
            "button_background_color": color_ref(C["accent_fill"]),
            "button_text_color": color_ref(C["on_accent"])})
    b["settings"]["border_radius"] = R_FAT_BTN
    b["settings"]["text_padding"] = dims(BTN_PAD_Y + 2, BTN_PAD_X,
                                         BTN_PAD_Y + 2, BTN_PAD_X)
    b["settings"].update(_inline_type("typography", BTN_FONT, BTN_SIZE, BTN_LINE))
    return b


def _fat_eyebrow(text, on_dark=False, on_accent=False):
    col = C["on_accent"] if on_accent else (
        C["on_dark"] if on_dark else C["accent_fill"])
    return widget("heading", {
        "title": text.upper(), "header_size": "div", "align": "left",
        "__typography__": typo_ref(T["eyebrow"]),
    }, globals_={"title_color": color_ref(col)})


def _fat_head(props, on_dark=False, size="h2", width=100):
    kids = []
    if props.get("eyebrow"):
        kids.append(_fat_eyebrow(props["eyebrow"], on_dark))
    if props.get("title"):
        kids.append(_heading(props["title"], size, T["h_medium"], "left",
                             on_dark=on_dark))
    if props.get("intro"):
        kids.append(_text(props["intro"], "left", on_dark=on_dark))
    return container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(14),
        "width": slider(width, "%"),
        "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%")})


def _fat_photo(image, height=420):
    """A photograph, or an honest empty slot.

    Load-bearing on the About page. The brief Section 4 is a HARD CONSTRAINT:
    no AI-generated imagery of Our Lady of Fatima or any sacred subject. No
    licensed photography has been supplied, so every slot ships empty with a
    written sourcing brief rather than filled with something that would breach
    it — the brief asks for a sourcing plan as a deliverable, not for pictures
    invented to fill the hole.
    """
    if image and image.get("url"):
        return widget("image", {
            "image": media(image["url"], image.get("alt", "")),
            "image_size": "full", "width": slider(100, "%"),
            "align": "center", "image_border_radius": R_FAT,
            "object-fit": "cover"})
    return container([], {
        "content_width": "full",
        "min_height": slider(height),
        "min_height_mobile": slider(round(height * 0.62)),
        "border_radius": R_FAT,
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["surface"]),
                 "border_color": color_ref(C["border"])})


@block("fat.pagehero")
def fat_pagehero(props):
    """Inner-page hero. Brown band, reversed Lora H1 — the treatment the built
    pages give their titles."""
    kids = [_heading(props.get("title", ""), "h1", T["h_large"], "left",
                     on_dark=True)]
    if props.get("intro"):
        kids.append(_text(props["intro"], "left", on_dark=True))
    body = container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(16), "width": slider(76, "%"),
        "width_tablet": slider(100, "%"), "width_mobile": slider(100, "%")})
    return _fat_section([body], "dark", pad=dims(76, 0, 76, 0))


@block("fat.lead")
def fat_lead(props):
    """The mission statement, set larger than body and standing alone.

    About brief Section 5: 'lead with the mission statement'. Giving it its own
    section at display size is what makes it LEAD rather than merely come
    first.
    """
    kids = []
    if props.get("eyebrow"):
        kids.append(_fat_eyebrow(props["eyebrow"]))
    kids.append(_heading(props.get("text", ""), props.get("size", "h2"),
                         T["h_medium"], "left"))
    if props.get("sub"):
        kids.append(_text(props["sub"], "left"))
    inner = container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(18), "width": slider(84, "%"),
        "width_tablet": slider(100, "%"), "width_mobile": slider(100, "%")})
    return _fat_section([inner], props.get("bg", "cream"))


@block("fat.facts")
def fat_facts(props):
    """Founding history as scannable label/value pairs under accent rules.

    About brief Section 5: present the founding history 'in an easily scannable
    form'. Who, when, and by whose approval read in about two seconds here and
    are buried inside a paragraph anywhere else.
    """
    items = props.get("items", [])
    on_dark = _fat_dk(props.get("bg", "white"))
    w = _tracks([1] * max(len(items), 1), FAT_GUTTER)

    def fact(it, width):
        rule = container([], {
            "content_width": "full", "min_height": slider(2),
            "margin": dims(0, 0, 16, 0), "background_background": "classic",
        }, globals_={"background_color": color_ref(C["accent_fill"])})
        lab = widget("heading", {
            "title": it.get("label", "").upper(), "header_size": "div",
            "align": "left", "__typography__": typo_ref(T["eyebrow"]),
        }, globals_={"title_color": color_ref(
            C["on_dark"] if on_dark else C["muted"])})
        val = _heading(it.get("value", ""), "h3", T["h_small"], "left",
                       on_dark=on_dark)
        kids = [rule, lab, val]
        if it.get("note"):
            kids.append(_text(it["note"], "left", on_dark=on_dark, small=True))
        return _col(kids, width, extra={"flex_gap": gap(8)})

    grid = _row([fact(it, w[i % len(w)]) for i, it in enumerate(items)],
                FAT_GUTTER, align="flex-start")
    head = [_fat_head(props, on_dark)] if props.get("title") else []
    return _fat_section(head + [grid], props.get("bg", "white"))


@block("fat.checklist")
def fat_checklist(props):
    """The initiatives, set apart as a bordered card with a checkmark list.

    About brief Section 5: initiatives must be 'a distinct, visually set-apart
    list, rather than embedding them in prose'. The homepage already renders
    this content as a checkmark icon-list, so this matches that treatment and
    puts it on a cream card so the section reads as a panel rather than as more
    body copy.
    """
    items = props.get("items", [])
    cols = props.get("columns", 2)
    w = _tracks([1] * cols, 20)

    def line(t):
        ic = widget("icon", {
            "selected_icon": icon(props.get("icon", "fas fa-check")),
            "size": slider(15), "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref(C["accent_fill"])})
        return container([_row([ic, _text(t, "left", small=True)], 12,
                               align="flex-start", extra={
                                   "flex_wrap": "nowrap",
                                   "flex_direction_mobile": "row"})], {
            "content_width": "full", "flex_direction": "column",
            "padding": dims(9, 0, 9, 0)})

    per = -(-len(items) // cols) if items else 0
    chunks = [items[i:i + per] for i in range(0, len(items), per)] if per else []
    grid = _row([_col([line(x) for x in ch], w[i % cols],
                      extra={"flex_gap": gap(0)})
                 for i, ch in enumerate(chunks)], 20, align="flex-start")

    kids = []
    if props.get("card_title"):
        kids.append(_heading(props["card_title"], "h3", T["h_small"], "left"))
    kids.append(grid)
    if props.get("footnote"):
        kids.append(_text(props["footnote"], "left", small=True))

    card = container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(16),
        "padding": dims(34, 32, 36, 32),
        "padding_mobile": dims(24, 20, 26, 20),
        "border_radius": R_FAT,
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["surface"]),
                 "border_color": color_ref(C["border"])})

    head = [_fat_head(props)] if props.get("title") else []
    return _fat_section(head + [card], props.get("bg", "white"))


@block("fat.split")
def fat_split(props):
    body = []
    if props.get("eyebrow"):
        body.append(_fat_eyebrow(props["eyebrow"]))
    if props.get("title"):
        body.append(_heading(props["title"], props.get("size", "h2"),
                             T["h_medium"], "left"))
    for para in props.get("paragraphs", []):
        body.append(_text(para, "left"))
    if props.get("cta_label"):
        body.append(_fat_button(props["cta_label"],
                                props.get("cta_url", "/become-a-member/")))
    photo = _fat_photo(props.get("image"), props.get("image_height", 430))
    w = _tracks([52, 44], 54)
    cols = [_col(body, w[0], extra={"flex_gap": gap(16)}),
            _col([photo], w[1])]
    if props.get("flip"):
        cols = list(reversed(cols))
    return _fat_section([_row(cols, 54, align="center")],
                        props.get("bg", "white"))


@block("fat.prose")
def fat_prose(props):
    on_dark = _fat_dk(props.get("bg", "white"))
    kids = []
    if props.get("eyebrow"):
        kids.append(_fat_eyebrow(props["eyebrow"], on_dark))
    if props.get("title"):
        kids.append(_heading(props["title"], props.get("size", "h2"),
                             T["h_medium"], "left", on_dark=on_dark))
    for para in props.get("paragraphs", []):
        kids.append(_text(para, "left", on_dark=on_dark))
    inner = container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(14), "width": slider(props.get("width", 82), "%"),
        "width_tablet": slider(100, "%"), "width_mobile": slider(100, "%")})
    return _fat_section([inner], props.get("bg", "white"))


@block("fat.note")
def fat_note(props):
    """Reference / legal text, set apart from the narrative.

    About brief Section 5: legal and registration information must be presented
    'as reference text, set apart from the narrative'. A hairline-bordered
    panel at small size does that without hiding it — and the same block
    carries the Ways to Give legal block, which that guide requires to stay
    visible somewhere on the page.
    """
    kids = []
    if props.get("title"):
        kids.append(_heading(props["title"], "h3", T["h_small"], "left"))
    for para in props.get("paragraphs", []):
        kids.append(_text(para, "left", small=True))
    # An optional action, added for the Resources page's "Can't find what
    # you're looking for?" block. The panel stays quiet — this is a prompt,
    # not the page's conversion band, and giving it the vermillion CTA would
    # put two loud actions on one page.
    if props.get("cta_label"):
        kids.append(_fat_button(props["cta_label"],
                                props.get("cta_url", "/contact/"), "brown"))
    for r in props.get("rows", []):
        lab = widget("heading", {
            "title": r.get("label", ""), "header_size": "div",
            "align": "left", "__typography__": typo_ref(T["meta"]),
        }, globals_={"title_color": color_ref(C["muted"])})
        val = _text(r.get("value", ""), "left", small=True)
        w = _tracks([32, 64], 16)
        kids.append(container([_row([_col([lab], w[0]), _col([val], w[1])],
                                    16, align="flex-start")], {
            "content_width": "full", "flex_direction": "column",
            "padding": dims(9, 0, 9, 0),
            "border_border": "solid", "border_width": dims(0, 0, 1, 0),
        }, globals_={"border_color": color_ref(C["border"])}))
    panel = container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(10),
        "padding": dims(30, 30, 32, 30),
        "padding_mobile": dims(22, 18, 24, 18),
        "border_radius": R_FAT,
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["white"]),
                 "border_color": color_ref(C["border"])})
    return _fat_section([panel], props.get("bg", "cream"))


@block("fat.giving")
def fat_giving(props):
    """The seven ways to give, stacked.

    The guide Section 4 asks for a 'Blog Layout (No need for pictures)', so
    this is a single readable column rather than a card grid: each method is a
    numbered row with its name, its description and its own call to action,
    separated by a rule.

    Two of the seven deliberately do NOT render a filled button, because the
    guide says so: Gifts by Phone is a tel: link where the NUMBER is the call
    to action, and Gifts of Stock has no button at all — a broker contacts a
    person. Forcing a uniform button onto all seven would be tidier and would
    contradict the brief, which states that nothing may be dropped, merged or
    reworded without sign-off.
    """
    items = props.get("items", [])
    rows = []
    for i, it in enumerate(items, 1):
        num = widget("heading", {
            "title": "%02d" % i, "header_size": "div", "align": "left",
            "__typography__": typo_ref(T["h_small"]),
        }, globals_={"title_color": color_ref(C["accent_fill"])})

        body = [_heading(it.get("title", ""), "h2", T["h_small"], "left")]
        for p in it.get("paragraphs", []):
            body.append(_text(p, "left"))

        kind = it.get("cta_kind", "button")
        if kind == "button" and it.get("cta_label"):
            body.append(_fat_button(it["cta_label"], it.get("cta_url", "#")))
        elif kind == "phone" and it.get("cta_label"):
            body.append(_fat_button(it["cta_label"],
                                    "tel:" + it.get("phone", ""), "brown"))
        elif kind == "none" and it.get("cta_note"):
            body.append(_text(it["cta_note"], "left", small=True))

        w = _tracks([8, 88], 24)
        row = _row([_col([num], w[0]),
                    _col(body, w[1], extra={"flex_gap": gap(12)})],
                   24, align="flex-start")
        rows.append(container([row], {
            "content_width": "full", "flex_direction": "column",
            "padding": dims(30, 0, 34, 0),
            "border_border": "solid",
            "border_width": dims(0, 0, 1 if i < len(items) else 0, 0),
        }, globals_={"border_color": color_ref(C["border"])}))

    head = [_fat_head(props)] if props.get("title") else []
    stack = container(rows, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(0), "width": slider(88, "%"),
        "width_tablet": slider(100, "%"), "width_mobile": slider(100, "%")})
    return _fat_section(head + [stack], props.get("bg", "white"))


@block("fat.cta")
def fat_cta(props):
    """Vermillion conversion band — the loudest thing in the palette, used the
    way the built pages use it: once, at the end, with one action."""
    kids = []
    if props.get("eyebrow"):
        kids.append(_fat_eyebrow(props["eyebrow"], on_accent=True))
    kids.append(_heading(props.get("title", ""), "h2", T["h_medium"], "left",
                         on_dark=True))
    if props.get("text"):
        kids.append(_text(props["text"], "left", on_dark=True))
    body = container(kids, {"content_width": "full",
                            "flex_direction": "column", "flex_gap": gap(14)})
    actions = [_fat_button(props.get("cta_label", "Join Now"),
                           props.get("cta_url", "/become-a-member/"),
                           "brown")]
    if props.get("cta2_label"):
        actions.append(_fat_button(props["cta2_label"],
                                   props.get("cta2_url", "#"), "outline"))
    w = _tracks([58, 38], 40)
    return _fat_section([_row([_col([body], w[0]),
                               _col([_row(actions, 14, align="center")], w[1])],
                              40, align="center")],
                        "accent", pad=dims(66, 0, 66, 0))


# ══════════════════════════════════════════════════════════════════════════
#  News / blog: single-post and archive templates (added 2026-09-07)
# ══════════════════════════════════════════════════════════════════════════
#
# Two Theme Builder documents. The site has neither right now — its old
# `Global Posts` (#1208) and `Global Archive` (#1203) are both in the trash —
# so posts currently fall back to the bare hello-elementor theme.
#
# Same design language as the rest of this family, read off the built pages:
# white as the primary ground, cream as the alternate, brown for full-bleed
# bands, vermillion for the one conversion action, Lora over Montserrat,
# 17px card radius.
#
# The category rail is built from the site's REAL taxonomy, passed in from
# the IR, not from a guessed list.


def _fat_meta_row(props):
    """Date · category · author, as one muted line under the title.

    `post-info` rather than three headings, so it stays correct when the post
    changes — a hand-written date in a heading widget is wrong the moment the
    template is reused, which is the whole point of a Theme Builder document.
    """
    items = []
    if props.get("show_date", True):
        items.append(repeater_item(
            _id="date", type="date", date_format="F j, Y",
            show_icon="", show_prefix=""))
    if props.get("show_terms", True):
        items.append(repeater_item(
            _id="terms", type="terms", taxonomy="category",
            show_icon="", show_prefix=""))
    if props.get("show_author", False):
        items.append(repeater_item(
            _id="author", type="author", show_icon="", show_prefix=""))
    return widget("post-info", {
        "icon_list": items,
        # `align` is NOT a post-info control - the validator rejects it.
        # The inline view left-aligns inside its container anyway.
        "view": "inline",
        "space_between": slider(18),
        "__typography__": typo_ref(T["meta"]),
    }, globals_={
        "text_color": color_ref(C["muted"]),
        "icon_color": color_ref(C["accent_fill"]),
    })


@block("fat.categorybar")
def fat_categorybar(props):
    """The category rail — every category on the site, as links.

    Built from the real taxonomy (passed in as `items`), so it lists exactly
    what exists rather than a plausible-looking set. Post counts are shown
    because on this site they are wildly uneven — Feast Days has 112 posts and
    News has 1 — and a reader deserves to know that before clicking.

    "All" comes first and points at the posts page, so the rail also works as
    the way back from a single category.
    """
    items = props.get("items", [])
    pills = []
    for i, it in enumerate(items):
        active = (i == 0)
        label = it.get("label", "")
        if it.get("count") is not None and props.get("show_counts", True):
            label = "%s (%s)" % (label, it["count"])
        b = _button(label, it.get("url", "#"), "ghost", "")
        b["settings"].update({
            "border_radius": box(999),
            "text_padding": dims(11, 22, 11, 22),
            "__typography__": typo_ref(T["meta"]),
        })
        g = b["settings"].setdefault("__globals__", {})
        if active:
            g.update({
                "button_background_color": color_ref(C["accent_fill"]),
                "button_text_color": color_ref(C["on_accent"]),
                "border_color": color_ref(C["accent_fill"]),
            })
        else:
            g.update({
                "button_text_color": color_ref(C["ink_on_white"]),
                "border_color": color_ref(C["border"]),
            })
        pills.append(b)

    rail = _row(pills, 10, align="center", extra={
        "flex_wrap": "wrap",
        "flex_direction_mobile": "row",
    })
    head = [_fat_head(props)] if props.get("title") else []
    return _fat_section(head + [rail], props.get("bg", "cream"))


@block("fat.archivehead")
def fat_archivehead(props):
    """Brown band carrying the dynamic archive title.

    `theme-archive-title` rather than a static heading, so one template serves
    every category, tag, author and date archive and always names the right
    one. That is the difference between an archive template and six
    near-identical pages.
    """
    kids = []
    if props.get("eyebrow"):
        kids += [_fat_eyebrow(props["eyebrow"], on_dark=True)]
    kids.append(widget("theme-archive-title", {
        "align": "left",
        "__typography__": typo_ref(T["h_large"]),
    }, globals_={"title_color": color_ref(C["white"])}))
    if props.get("intro"):
        kids.append(_text(props["intro"], "left", on_dark=True))
    body = container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(14), "width": slider(76, "%"),
        "width_tablet": slider(100, "%"), "width_mobile": slider(100, "%")})
    return _fat_section([body], "dark", pad=dims(72, 0, 72, 0))


@block("fat.archiveposts")
def fat_archiveposts(props):
    """The archive loop — the posts of whatever archive is being viewed.

    `archive-posts` (not `posts`): it inherits the current query, so a category
    archive shows that category. `posts` would need its own query and would
    show the same list on every archive, which is the usual way this gets
    built wrong.
    """
    # Control names are the ones Elementor actually observes, checked against
    # the registry rather than guessed: `thumbnail` not `show_thumbnail`, and
    # there is no `item_gap`. The validator rejects the invented ones, which
    # is exactly what it is for.
    w = widget("archive-posts", {
        "_skin": "classic",
        "columns": str(props.get("columns", 3)),
        "row_gap": slider(36),
        "thumbnail": "top",
        "thumbnail_size": "medium_large",
        "image_border_radius": R_FAT,
        "show_title": "yes",
        "title_tag": "h3",
        "show_excerpt": "yes",
        "excerpt_length": props.get("excerpt_length", 22),
        "show_read_more": "yes",
        "read_more_text": props.get("read_more", "Read more"),
        "meta_data": ["date", "terms"],
        "meta_separator": "  ·  ",
        "pagination_type": "numbers_and_prev_next",
        "pagination_prev_label": "Previous",
        "pagination_next_label": "Next",
        "pagination_align": "center",
        "nothing_found_message": props.get(
            "empty", "There are no posts in this section yet."),
    }, globals_={
        "title_color": color_ref(C["ink_on_white"]),
        "meta_color": color_ref(C["muted"]),
        "excerpt_color": color_ref("text"),
        "read_more_color": color_ref(C["accent_fill"]),
        "pagination_color": color_ref(C["muted"]),
        "pagination_active_color": color_ref(C["accent_fill"]),
    })
    head = [_fat_head(props)] if props.get("title") else []
    return _fat_section(head + [w], props.get("bg", "white"))


@block("fat.singlehead")
def fat_singlehead(props):
    """Single-post header: brown band, dynamic title, meta line.

    The featured image sits BELOW the band rather than behind the title. Many
    of these posts are saints' feast days whose images are devotional artwork,
    and scrimming a dark overlay across a holy image to make white type legible
    is the wrong treatment for this site.
    """
    kids = []
    if props.get("eyebrow"):
        kids.append(_fat_eyebrow(props["eyebrow"], on_dark=True))
    kids.append(widget("theme-post-title", {
        "align": "left",
        "__typography__": typo_ref(T["h_large"]),
    }, globals_={"title_color": color_ref(C["white"])}))
    meta = _fat_meta_row(props)
    meta["settings"]["__globals__"] = {
        "text_color": color_ref(C["on_dark"]),
        "icon_color": color_ref(C["brand_on_dark"]),
    }
    kids.append(meta)
    body = container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(16), "width": slider(80, "%"),
        "width_tablet": slider(100, "%"), "width_mobile": slider(100, "%")})
    return _fat_section([body], "dark", pad=dims(72, 0, 72, 0))


@block("fat.singlebody")
def fat_singlebody(props):
    """Featured image, then the post content, in a readable measure.

    Width is capped at 74% rather than full: 185 of these posts are long-form
    devotional prose, and a 1240px line length is unreadable. This is the one
    place in the family where the container is deliberately narrower than the
    grid.
    """
    kids = []
    if props.get("show_image", True):
        kids.append(widget("theme-post-featured-image", {
            "image_size": "large",
            "align": "center",
            "image_border_radius": R_FAT,
        }))
    kids.append(widget("theme-post-content", {
        "__typography__": typo_ref("text"),
    }, globals_={"text_color": color_ref("text")}))

    if props.get("show_share", True):
        kids.append(container([], {
            "content_width": "full", "min_height": slider(1),
            "margin": dims(34, 0, 26, 0), "background_background": "classic",
        }, globals_={"background_color": color_ref(C["border"])}))
        kids.append(widget("share-buttons", {
            "share_buttons": [
                repeater_item(_id="fb", button="facebook"),
                repeater_item(_id="x", button="x-twitter"),
                repeater_item(_id="em", button="email"),
                repeater_item(_id="pr", button="print"),
            ],
            "view": "icon-text",
            "shape": "rounded",
            "columns": "4",
            "alignment": "left",
            "share_buttons_size": slider(22),
        }))

    inner = container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(26), "width": slider(props.get("width", 74), "%"),
        "width_tablet": slider(100, "%"), "width_mobile": slider(100, "%")})
    return _fat_section([inner], props.get("bg", "white"))


@block("fat.singlenav")
def fat_singlenav(props):
    """Previous / next post, then a strip of recent posts.

    `post-navigation` keeps a reader inside the archive instead of dead-ending
    on the last paragraph, which is where most of the traffic on a devotional
    site actually goes next.
    """
    nav = widget("post-navigation", {
        "show_label": "yes",
        "prev_label": props.get("prev_label", "Previous"),
        "next_label": props.get("next_label", "Next"),
        "show_title": "yes",
        "show_borders": "yes",
        "__typography__": typo_ref(T["meta"]),
    }, globals_={
        "label_color": color_ref(C["muted"]),
        "title_color": color_ref(C["ink_on_white"]),
        "borders_color": color_ref(C["border"]),
    })

    # A "recent posts" strip deliberately is NOT emitted here.
    #
    # Elementor's `posts` widget would be the right tool, but this build's
    # registry has not mined its display controls (only `_skin`, `columns`,
    # `pagination_*`), so every setting that makes it useful - how many posts,
    # thumbnails, excerpt off - fails validation. Shipping it with defaults
    # would put a 10-post paginated blog roll at the foot of every article.
    #
    # Prev/next plus the category rail above is a complete way onward, so the
    # template is honest rather than padded. Adding a Related Posts widget by
    # hand in Elementor afterwards is a two-minute job and is noted in the
    # README.
    return _fat_section([nav], props.get("bg", "cream"))


# ══════════════════════════════════════════════════════════════════════════
#  Consecration page (added 2026-09-08)
# ══════════════════════════════════════════════════════════════════════════
#
# One new device. Everything else on that page is built from the blocks the
# About and Ways to Give pages already established, so the new page reads as
# part of the same site rather than as a visitor.


@block("fat.steps")
def fat_steps(props):
    """The Thirty-Three Day preparation, as four numbered stages.

    Deliberately NOT `fat.giving`, which numbers its rows 01…07 — these stages
    already carry their own numbering ("Part I") and, more importantly, the
    thing a reader scans for here is the DAY RANGE: where am I in the
    thirty-three days. So the marker column is the range itself, set in the
    accent, with the part number as its eyebrow.

    Same anatomy as `fat.giving` otherwise — a single readable column with a
    hairline rule between stages — because the brief for this family asks for a
    blog-style reading layout, and a four-card grid would compress the longest
    of the four paragraphs into a scroll box.
    """
    items = props.get("items", [])
    rows = []
    for i, it in enumerate(items, 1):
        marker = [
            widget("heading", {
                "title": it.get("part", "Part %d" % i).upper(),
                "header_size": "div", "align": "left",
                "__typography__": typo_ref(T["eyebrow"]),
            }, globals_={"title_color": color_ref(C["muted"])}),
            _heading(it.get("days", ""), "h3", T["h_small"], "left"),
        ]
        body = [_heading(it.get("title", ""), "h3", T["h_small"], "left")]
        for p in it.get("paragraphs", []):
            body.append(_text(p, "left"))
        if it.get("prayers"):
            body.append(_text(it["prayers"], "left", small=True))

        w = _tracks([22, 74], 28)
        row = _row([_col(marker, w[0], extra={"flex_gap": gap(6)}),
                    _col(body, w[1], extra={"flex_gap": gap(12)})],
                   28, align="flex-start")
        rows.append(container([row], {
            "content_width": "full", "flex_direction": "column",
            "padding": dims(30, 0, 34, 0),
            "border_border": "solid",
            "border_width": dims(0, 0, 1 if i < len(items) else 0, 0),
        }, globals_={"border_color": color_ref(C["border"])}))

    head = [_fat_head(props)] if props.get("title") else []
    stack = container(rows, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(0), "width": slider(88, "%"),
        "width_tablet": slider(100, "%"), "width_mobile": slider(100, "%")})
    return _fat_section(head + [stack], props.get("bg", "white"))


# ══════════════════════════════════════════════════════════════════════════
#  Resources and Apostolates (added 2026-09-09)
# ══════════════════════════════════════════════════════════════════════════
#
# Both pages arrived as full design briefs written for a mockup designer, so
# unlike the earlier pages in this family the DEVICES are specified rather than
# inferred. Five new factories, each because the brief names a shape this
# family has never rendered:
#
#   fat.jumpnav       sticky category bar with anchor links   (Resources 4.4)
#   fat.featured      the larger "Start Here" card            (Resources 4.3)
#   fat.resourcecards the resource card grid + badges         (Resources 5)
#   fat.signup        the newsletter capture block            (Resources 4.11)
#   fat.apostolates   13 ministry cards, 3-up, tinted         (Apostolates 4)
#
# The Apostolates brief states outright that "there is no existing card or grid
# component anywhere on the site" and that the result "must feel native to the
# rest of the site, not bolted on". So both grids are built from this family's
# own vocabulary — 17px radius, hairline #D9CFC2 border, Lora titles over
# Montserrat body, vermillion reserved for one action — rather than from a
# generic card block wearing the palette.


def _fat_badge(text, y=12):
    """Format pill sitting ON the thumbnail, per Resources brief 5.2.

    Absolutely positioned rather than stacked above the title, because the
    brief puts it "in the top corner of the thumbnail" and that placement is
    what lets a scanning reader tell a PDF from an article without reading
    anything. Legal controls, no CSS: `_position` + offsets + z-index.
    """
    return container([widget("heading", {
        "title": text.upper(), "header_size": "div", "align": "center",
        "__typography__": typo_ref(T["eyebrow"]),
    }, globals_={"title_color": color_ref(C["on_accent"])})], {
        "content_width": "full", "flex_direction": "column",
        "flex_justify_content": "center",
        "padding": dims(5, 12, 5, 12),
        "border_radius": box(999),
        "width": slider(34, "%"),
        "_position": "absolute",
        "_offset_orientation_h": "start", "_offset_x": slider(12),
        "_offset_orientation_v": "start", "_offset_y": slider(y),
        "_z_index": 3,
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["accent_fill"])})


def _fat_thumb(item, height=172):
    """16:9 thumbnail area. Never blank — Resources brief 5.1.

    "If no photo exists for an item, use a simple single-color line icon
    centered on a soft cream background (never leave this area blank)." No
    photography has been supplied, so every card in this build takes the icon
    path; dropping an image URL into the copy file switches it per item with
    no other change.
    """
    if item.get("image", {}).get("url"):
        inner = widget("image", {
            "image": media(item["image"]["url"], item["image"].get("alt", "")),
            "image_size": "full", "width": slider(100, "%"),
            "height": slider(height), "object-fit": "cover",
            "object-position": "center center", "align": "center"})
    else:
        inner = widget("icon", {
            "selected_icon": icon(item.get("icon", "far fa-file-alt")),
            "size": slider(34), "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref(C["ink_primary"])})

    kids = [inner]
    if item.get("format"):
        kids.append(_fat_badge(item["format"]))
    return container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_justify_content": "center", "flex_align_items": "center",
        "min_height": slider(height),
        "overflow": "hidden",
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["surface"])})


@block("fat.jumpnav")
def fat_jumpnav(props):
    """Sticky category bar — Resources brief 4.4.

    Elementor Pro's own sticky, not a scroll script: `sticky: top` plus
    `sticky_offset` clearing the 90-110px header the brief reserves. The bar
    is full-width so it spans the viewport when it sticks, while its inner row
    stays on the kit's 1240 measure.

    NOT built, and said plainly rather than faked: the brief also asks for the
    active category to highlight as the visitor scrolls. That is a scroll
    observer, i.e. JavaScript, and this repo's contract is core + Pro controls
    only. The links work; the active state does not exist. See README.
    """
    items = props.get("items", [])
    links = []
    for it in items:
        b = _button(it.get("label", ""), it.get("href", "#"), "ghost", "")
        b["settings"].update({
            "border_radius": box(999),
            "text_padding": dims(9, 18, 9, 18),
            "border_border": "none", "border_width": box(0),
            "__typography__": typo_ref(T["meta"]),
        })
        b["settings"].setdefault("__globals__", {}).update({
            "button_text_color": color_ref(C["ink_on_white"]),
            "button_background_hover_color": color_ref(C["surface_alt"]),
            "hover_color": color_ref("secondary"),
        })
        links.append(b)

    rail = _row(links, 6, align="center", extra={
        "flex_wrap": "wrap", "flex_direction_mobile": "row",
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "margin": dims(0, "auto", 0, "auto")})

    return container([rail], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(10, 20, 10, 20),
        "border_border": "solid", "border_width": dims(0, 0, 1, 0),
        "background_background": "classic",
        "sticky": "top",
        "sticky_on": ["desktop", "tablet"],
        "sticky_offset": props.get("offset", 0),
        "_z_index": 90,
    }, globals_={"background_color": color_ref(C["white"]),
                 "border_color": color_ref(C["border"])})


@block("fat.featured")
def fat_featured(props):
    """The "Start Here" block — Resources brief 4.3.

    "A single, visually distinct card or banner (larger than the standard
    resource card) pointing a first-time visitor to the single best entry
    point." Distinct here is a cream ground, a vermillion rule down the leading
    edge and display-size type — not a different shape. On a devotional library
    the one thing that must not happen is the entry point looking like a
    promotion.
    """
    kids = []
    if props.get("eyebrow"):
        kids.append(_fat_eyebrow(props["eyebrow"]))
    kids.append(_heading(props.get("title", ""), "h2", T["h_medium"], "left"))
    if props.get("text"):
        kids.append(_text(props["text"], "left"))
    if props.get("meta"):
        kids.append(_text(props["meta"], "left", small=True))
    if props.get("cta_label"):
        kids.append(_fat_button(props["cta_label"], props.get("cta_url", "#")))
    body = _col(kids, None, extra={"flex_gap": gap(14)})

    card = container([body], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(38, 40, 40, 40),
        "padding_mobile": dims(26, 22, 28, 22),
        "border_radius": R_FAT,
        "border_border": "solid",
        "border_width": dims(1, 1, 1, 5),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["surface"]),
                 "border_color": color_ref(C["accent_fill"])})

    head = [_fat_head(props)] if props.get("heading") else []
    return _fat_section(head + [card], props.get("bg", "white"),
                        anchor=props.get("anchor"))


@block("fat.resourcecards")
def fat_resourcecards(props):
    """One category of the resource library — Resources brief 4.5-4.9 and 5.

    Every resource uses the SAME card whatever its category, which is the
    brief's own rule and the reason a visitor can tell an article from a PDF at
    a glance. Fields, top to bottom: thumbnail, format badge, title, one-line
    description, metadata, one action.

    Two states the brief calls out explicitly, both built here:

      * EMPTY DESCRIPTION - the description slot keeps its height when the text
        is missing, so the grid stays aligned rather than that card shrinking.
      * LONG TITLE - the title slot also has a floor, so a two-line title on
        one card does not leave every card beside it short.

    Those two are why the card body is built from fixed-height slots rather
    than a plain stack, and they are the reason this is a new factory rather
    than a reuse of `fat.checklist`.
    """
    items = props.get("items", [])
    cols = props.get("columns", 3)
    w = _tracks([1] * cols, FAT_GUTTER)[0]
    cards = []
    for it in items:
        body = [
            container([_heading(it.get("title", ""), "h3", T["h_small"],
                                "left")], {
                "content_width": "full", "flex_direction": "column",
                "min_height": slider(props.get("title_height", 62))}),
            container([_text(it["desc"], "left", small=True)]
                      if it.get("desc") else [], {
                "content_width": "full", "flex_direction": "column",
                "min_height": slider(props.get("desc_height", 46))}),
        ]
        if it.get("meta"):
            body.append(widget("heading", {
                "title": it["meta"], "header_size": "div", "align": "left",
                "__typography__": typo_ref(T["meta"]),
            }, globals_={"title_color": color_ref(C["muted"])}))
        if it.get("action_label"):
            b = _button(it["action_label"], it.get("href", "#"), "ghost", "")
            b["settings"].update({
                "border_radius": R_FAT_BTN,
                "text_padding": dims(11, 22, 11, 22),
                "__typography__": typo_ref(T["meta"])})
            b["settings"].setdefault("__globals__", {}).update({
                "button_text_color": color_ref(C["ink_on_white"]),
                "border_color": color_ref(C["border"]),
                "button_background_hover_color": color_ref(C["accent_fill"]),
                "button_hover_border_color": color_ref(C["accent_fill"]),
                "hover_color": color_ref(C["on_accent"])})
            body.append(b)

        cards.append(container([
            _fat_thumb(it, props.get("thumb_height", 172)),
            container(body, {
                "content_width": "full", "flex_direction": "column",
                "flex_gap": gap(10),
                "padding": dims(22, 24, 26, 24)}),
        ], {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(0),
            "width": slider(w, "%"),
            "width_mobile": slider(100, "%"),
            "border_radius": R_FAT,
            "border_border": "solid", "border_width": box(1),
            "overflow": "hidden",
            "background_background": "classic",
        }, globals_={"background_color": color_ref(C["white"]),
                     "border_color": color_ref(C["border"])}))

    grid = _row(cards, FAT_GUTTER, align="stretch", extra={"flex_wrap": "wrap"})
    head = [_fat_head(props)] if props.get("title") else []
    return _fat_section(head + [grid], props.get("bg", "white"),
                        anchor=props.get("anchor"))


@block("fat.apostolates")
def fat_apostolates(props):
    """The thirteen ministries — Apostolates brief 4.

    "A responsive grid of cards - 3 columns on desktop, 1 column on mobile -
    each with a simple icon or small image, the apostolate title, and a 1-line
    description", plus: "Add light visual variety (subtle borders, alternating
    backgrounds, etc.) so 13 items don't feel monotonous."

    The variety is per-card grounds alternating white and cream. In a 3-up grid
    an alternating index produces a checkerboard rather than stripes, which is
    what stops thirteen equal cards reading as a wall — and it costs one global
    colour reference per card, no CSS.

    Icons take the vermillion and are line-weight, per the brief's "simple,
    line-based... to feel liturgical rather than flat-corporate". They are
    deliberately not the solid faces used elsewhere in this kit.
    """
    items = props.get("items", [])
    cols = props.get("columns", 3)
    w = _tracks([1] * cols, FAT_GUTTER)[0]
    cards = []
    for i, it in enumerate(items):
        tinted = (i % 2 == 1)
        cards.append(container([
            widget("icon", {
                "selected_icon": icon(it.get("icon", "far fa-circle")),
                "size": slider(26), "align": "left", "view": "default",
            }, globals_={"primary_color": color_ref(C["accent_fill"])}),
            _heading(it.get("title", ""), "h3", T["h_small"], "left"),
            _text(it.get("text", ""), "left", small=True),
        ], {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(12),
            "width": slider(w, "%"),
            "width_mobile": slider(100, "%"),
            "padding": dims(28, 26, 30, 26),
            "padding_mobile": dims(24, 20, 26, 20),
            "border_radius": R_FAT,
            "border_border": "solid", "border_width": box(1),
            "background_background": "classic",
        }, globals_={
            "background_color": color_ref(C["surface"] if tinted else C["white"]),
            "border_color": color_ref(C["border"])}))

    grid = _row(cards, FAT_GUTTER, align="stretch", extra={"flex_wrap": "wrap"})
    head = [_fat_head(props)] if props.get("title") else []
    return _fat_section(head + [grid], props.get("bg", "white"))


@block("fat.signup")
def fat_signup(props):
    """Newsletter capture — Resources brief 4.11.

    "Reuse the organization's existing name/email signup pattern." Two fields
    and one button, on the cream ground, at the foot of the page — a reader who
    has worked through the library is the likeliest subscriber there is. No
    incentive copy and no urgency device: the brief bans exactly that register.
    """
    fields = [
        repeater_item(custom_id="name", field_type="text", field_label="Name",
                      placeholder="Your name", required="true", width="50"),
        repeater_item(custom_id="email", field_type="email",
                      field_label="Email", placeholder="Email address",
                      required="true", width="50"),
    ]
    form = widget("form", {
        "form_name": props.get("form_name", "Newsletter"),
        "form_fields": fields,
        "button_text": props.get("submit_label", "Subscribe"),
        "button_size": "sm",
        "input_size": "md",
        "success_message": props.get(
            "success_message", "Thank you - you are subscribed."),
        "email_to": props.get("email", ""),
        "email_subject": props.get("email_subject", "Newsletter signup"),
        "button_border_radius": R_FAT_BTN,
    }, globals_={
        "button_background_color": color_ref(C["accent_fill"]),
        "button_text_color": color_ref(C["on_accent"]),
        "field_text_color": color_ref("secondary"),
    })

    kids = []
    if props.get("eyebrow"):
        kids.append(_fat_eyebrow(props["eyebrow"]))
    if props.get("title"):
        kids.append(_heading(props["title"], "h2", T["h_medium"], "left"))
    if props.get("text"):
        kids.append(_text(props["text"], "left"))
    tw = _tracks([46, 50], 40)
    copy = _col(kids, tw[0], extra={"flex_gap": gap(12)})
    field = _col([form], tw[1], extra={"flex_justify_content": "center"})
    return _fat_section([_row([copy, field], 40, align="center")],
                        props.get("bg", "cream"))
