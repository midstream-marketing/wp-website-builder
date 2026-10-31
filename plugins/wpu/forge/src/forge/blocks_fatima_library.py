"""
blocks_fatima_library.py — the Resources library, Become A Member and
Apostolates, matched to the client's approved HTML prototypes.

The earlier `fat.*` blocks in `blocks_fatima.py` were built from written
briefs. These are built from something stricter: three finished prototypes the
client has already seen and approved —

    become-a-member (1).slim.html          the membership page
    livefatima-resources-prototype.slim.html   the library and its 12 articles
    "Apostolates Prototype" (artifact)     the works of the Confraternity

so the devices here are not inferred, they are MEASURED off those files. Every
factory below exists because the prototypes draw a shape this family had never
rendered, and the design-fidelity rule applies: match the devices, not the
section order. Where a prototype shape could be got by bending an existing
factory, it is (four `fat.apostolates` grids carry the four families of works);
where it could not, there is a new factory and a docstring saying which
prototype line asked for it.

Two family-wide notes.

GOLD. The prototypes rule their heroes and set their eyebrows in #C9A050, a
colour the dev site's Global Kit does not carry. It is added to
`intake.json -> brand.extra_colors` as `fatgld1` (plus `fatgld2`, its light
form, for dark grounds) rather than substituted with the vermillion accent,
which in this family means "one action" and would read as a button rule. The
addition is additive — no existing token changes — so pages still drop in
beside the built ones without a seam, but the Global Kit does need re-importing
once. README section 3.

NO CSS, as everywhere in this repo: the italic serif of a pull-quote comes from
`typography_font_style` on the heading widget, the sticky contents rail from
Elementor Pro's own `sticky`, and the day chips from real containers. Nothing
here emits a stylesheet.
"""
from __future__ import annotations

import re

from .core import (
    container, widget, repeater_item, slider, dims, box, media,
    gap, color_ref, typo_ref, icon,
)
from .tokens import C, T
from .blocks import (
    block, _row, _col, _tracks, _button, _heading, _text, _faq, KIT_CONTAINER,
)
from .blocks_fatima import (
    _fat_section, _fat_button, _fat_eyebrow, _fat_head, _fat_photo,
    _inline_type, R_FAT, R_FAT_BTN, FAT_GUTTER,
)

# brand.extra_colors ids. Seven characters, which the token loader enforces.
GOLD = "fatgld1"
GOLD_LIGHT = "fatgld2"


# ─────────────────────────────── helpers ───────────────────────────────────

def _slug(text):
    """A stable anchor id for a heading, so the contents rail can reach it."""
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:48] or "section"


def _rule(width=72, on_dark=False, thickness=2):
    """The gold hairline under a hero title and above a pull-quote."""
    return container([], {
        "content_width": "full",
        "min_height": slider(thickness),
        "width": slider(width),
        "_flex_shrink": "0",
        "background_background": "classic",
    }, globals_={"background_color": color_ref(
        GOLD_LIGHT if on_dark else GOLD)})


def _serif(text, token=T["h_small"], italic=False, on_dark=False,
           align="left", size="div", color=None):
    """A Lora line. `italic` is the pull-quote voice the prototypes use for
    every quotation from Our Lady, and it comes from the typography group
    rather than an <em> so the face, size and style stay one decision."""
    settings = {"title": text, "header_size": size, "align": align,
                "__typography__": typo_ref(token)}
    if italic:
        settings.update({"typography_typography": "custom",
                         "typography_font_style": "italic"})
    col = color or (C["white"] if on_dark else "secondary")
    return widget("heading", settings,
                  globals_={"title_color": color_ref(col)})


def _photo_ground(sec, image, position="center center", overlay=0.62):
    """Paint a section with a photograph and the brown scrim over it.

    The prototypes use this for the page heroes, the "How to Use These
    Resources" band, the obligations grid and every Related Resources strip —
    always the same recipe, so it is one helper rather than four copies.
    """
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
        "background_overlay_color"] = color_ref("secondary")
    return sec


def _crumb(items, on_dark=True):
    """Resources / The Message of Fatima — the trail every article carries."""
    kids = []
    for i, it in enumerate(items or []):
        if i:
            kids.append(widget("heading", {
                "title": "/", "header_size": "div", "align": "left",
                "__typography__": typo_ref(T["meta"]),
            }, globals_={"title_color": color_ref(
                C["on_dark"] if on_dark else C["muted"])}))
        if it.get("href"):
            b = _button(it.get("label", ""), it["href"], "ghost", "")
            b["settings"].update({
                "border_border": "none", "border_width": box(0),
                "text_padding": dims(0, 0, 0, 0),
                "__typography__": typo_ref(T["meta"])})
            b["settings"].setdefault("__globals__", {}).update({
                "button_text_color": color_ref(
                    C["white"] if on_dark else "secondary"),
                "button_background_color": color_ref(C["transparent"]),
                "hover_color": color_ref(GOLD_LIGHT if on_dark else GOLD)})
            kids.append(b)
        else:
            kids.append(widget("heading", {
                "title": it.get("label", ""), "header_size": "div",
                "align": "left", "__typography__": typo_ref(T["meta"]),
            }, globals_={"title_color": color_ref(
                C["on_dark"] if on_dark else C["muted"])}))
    return _row(kids, 10, align="center", extra={
        "flex_wrap": "wrap", "flex_direction_mobile": "row"})


def _card(kids, width=None, tinted=False, pad=None, extra=None):
    """The family card: 17px radius, hairline border, white or cream."""
    s = {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(12),
        "padding": pad or dims(28, 26, 30, 26),
        "padding_mobile": dims(24, 20, 26, 20),
        "border_radius": R_FAT,
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


def _numdisc(n, on_dark=False, size=46):
    """Brown disc, gold numeral — the step marker used on three pages."""
    return container([widget("heading", {
        "title": str(n), "header_size": "div", "align": "center",
        "__typography__": typo_ref(T["h_small"]),
    }, globals_={"title_color": color_ref(GOLD_LIGHT)})], {
        "content_width": "full", "flex_direction": "column",
        "flex_justify_content": "center", "flex_align_items": "center",
        "width": slider(size), "min_height": slider(size),
        "_flex_shrink": "0",
        "border_radius": box(999),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(
        C["white"] if on_dark else "secondary")})


# ───────────────────────────── page furniture ──────────────────────────────

@block("fat.photohero")
def fat_photohero(props):
    """Article and page hero — photograph, brown scrim, breadcrumb, gold rule.

    `fat.pagehero` paints a flat brown band. Every page in the prototypes
    instead runs a photograph of the Sanctuary or the pilgrim statue under a
    top-to-bottom scrim, with the title sitting on the bottom edge, a breadcrumb
    above it and a 72px gold rule between the title and the standfirst. That is
    the most recognisable thing about the whole set, so it is a factory rather
    than a prop on the old hero, and the old one keeps serving the pages built
    against the earlier brief.
    """
    kids = []
    if props.get("breadcrumb"):
        kids.append(_crumb(props["breadcrumb"]))
    kids.append(_heading(props.get("title", ""), "h1", T["h_large"], "left",
                         on_dark=True))
    kids.append(_rule(72, on_dark=True))
    if props.get("intro"):
        kids.append(_text(props["intro"], "left", on_dark=True))
    body = container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(16),
        "width": slider(props.get("width", 60), "%"),
        "width_tablet": slider(86, "%"), "width_mobile": slider(100, "%")})

    sec = _fat_section([body], "dark",
                       pad=dims(props.get("pad_top", 132), 0,
                                props.get("pad_bottom", 72), 0),
                       extra={"min_height": slider(props.get("height", 460)),
                              "min_height_mobile": slider(360),
                              "flex_justify_content": "flex-end"})
    return _photo_ground(sec, props.get("image"),
                         props.get("position", "center 58%"),
                         props.get("overlay", 0.58))


@block("fat.source")
def fat_source(props):
    """The attribution strip the prototypes put at the head of every article
    that is reprinted: which site it came from, and the Section 107 basis.

    It is not `fat.note` — that is a bordered reference panel for legal text at
    the FOOT of a page. This is one line on cream with a book icon, read before
    the article starts, and the client's own prototype places it there on nine
    of the twelve articles. Attribution that a reader has to hunt for is not
    attribution.
    """
    ic = widget("icon", {
        "selected_icon": icon(props.get("icon", "far fa-bookmark")),
        "size": slider(18), "align": "center", "view": "default",
    }, globals_={"primary_color": color_ref(C["muted"])})
    line = _text(props.get("text", ""), "left", small=True)
    panel = container([_row([ic, line], 14, align="flex-start", extra={
        "flex_wrap": "nowrap", "flex_direction_mobile": "row"})], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(16, 20, 16, 20),
        "border_radius": box(10),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["surface"])})
    return _fat_section([panel], props.get("bg", "white"),
                        pad=dims(40, 0, 8, 0))


@block("fat.article")
def fat_article(props):
    """The reading column, with the contents rail beside it.

    This is the workhorse of the twelve article pages. The prototypes give
    those pages a 280px "On This Page" rail that sticks while the body scrolls,
    and a body made of typed pieces rather than one HTML blob. So the block
    takes NODES, each with a type, and renders the device the prototype draws
    for it:

        h2 / h3   heading, with an anchor id the rail links to
        p         body paragraph
        ul        bulleted list, gold marks
        quote     cream card, gold rule, italic Lora, optional citation
        dialogue  speaker label in the accent + the words in italic Lora —
                  the Simple Acts of Penance page is built almost entirely
                  from these exchanges between Our Lady and the children
        note      hairline panel for an editorial aside
        table     the Consecration feast-date table, built from containers
                  because Elementor has no table widget

    Every paragraph of text this renders is the client's own, pulled from the
    live livefatima.io page the prototype names; nothing here is written.
    """
    nodes = props.get("nodes", [])
    on_dark = False
    body = []

    for n in nodes:
        kind = n.get("type", "p")
        if kind in ("h2", "h3"):
            head = _heading(n.get("text", ""), kind,
                            T["h_medium"] if kind == "h2" else T["h_small"],
                            "left")
            body.append(container([head], {
                "content_width": "full", "flex_direction": "column",
                "padding": dims(18, 0, 0, 0),
                "_element_id": n.get("anchor") or _slug(n.get("text", ""))}))
        elif kind == "p":
            body.append(_text(n.get("text", ""), "left"))
        elif kind == "lead":
            body.append(_serif(n.get("text", ""), T["h_small"], align="left"))
        elif kind == "ul":
            rows = []
            for item in n.get("items", []):
                mark = widget("icon", {
                    "selected_icon": icon(n.get("icon", "fas fa-circle")),
                    "size": slider(7), "align": "center", "view": "default",
                }, globals_={"primary_color": color_ref(GOLD)})
                rows.append(_row([mark, _text(item, "left")], 14,
                                 align="flex-start",
                                 extra={"flex_wrap": "nowrap",
                                        "flex_direction_mobile": "row",
                                        "padding": dims(6, 0, 6, 0)}))
            body.append(container(rows, {
                "content_width": "full", "flex_direction": "column",
                "flex_gap": gap(4), "padding": dims(4, 0, 8, 0)}))
        elif kind == "quote":
            kids = [_rule(48),
                    _serif(n.get("text", ""), T["h_small"], italic=True)]
            if n.get("cite"):
                kids.append(widget("heading", {
                    "title": n["cite"], "header_size": "div", "align": "left",
                    "__typography__": typo_ref(T["meta"]),
                }, globals_={"title_color": color_ref(C["muted"])}))
            body.append(container(kids, {
                "content_width": "full", "flex_direction": "column",
                "flex_gap": gap(14),
                "padding": dims(30, 36, 32, 36),
                "padding_mobile": dims(24, 22, 26, 22),
                "border_radius": R_FAT,
                "background_background": "classic",
            }, globals_={"background_color": color_ref(C["surface"])}))
        elif kind == "dialogue":
            rows = []
            for turn in n.get("turns", []):
                who = widget("heading", {
                    "title": turn.get("who", "").upper(),
                    "header_size": "div", "align": "left",
                    "__typography__": typo_ref(T["eyebrow"]),
                }, globals_={"title_color": color_ref(C["accent_fill"])})
                said = _serif(turn.get("text", ""), T["h_small"], italic=True)
                w = _tracks([18, 78], 18)
                rows.append(_row([_col([who], w[0]), _col([said], w[1])], 18,
                                 align="flex-start"))
            body.append(container(rows, {
                "content_width": "full", "flex_direction": "column",
                "flex_gap": gap(16),
                "padding": dims(30, 34, 32, 34),
                "padding_mobile": dims(24, 20, 26, 20),
                "border_radius": R_FAT,
                "background_background": "classic",
            }, globals_={"background_color": color_ref(C["surface"])}))
        elif kind == "note":
            body.append(container([_text(n.get("text", ""), "left",
                                         small=True)], {
                "content_width": "full", "flex_direction": "column",
                "padding": dims(16, 20, 16, 20),
                "border_radius": box(10),
                "border_border": "dashed", "border_width": box(1),
                "background_background": "classic",
            }, globals_={"background_color": color_ref(C["white"]),
                         "border_color": color_ref(C["border"])}))
        elif kind == "table":
            body.append(_fat_table(n))

    reading = container(body, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(16)})

    toc = props.get("toc")
    if not toc:
        inner = container([reading], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(props.get("width", 82), "%"),
            "width_tablet": slider(100, "%"),
            "width_mobile": slider(100, "%")})
        return _fat_section([inner], props.get("bg", "white"),
                            anchor=props.get("anchor"))

    links = [widget("heading", {
        "title": props.get("toc_title", "On This Page"),
        "header_size": "div", "align": "left",
        "__typography__": typo_ref(T["h_small"]),
    }, globals_={"title_color": color_ref("secondary")})]
    for i, t in enumerate(toc):
        b = _button(t.get("label", ""), "#" + (t.get("anchor") or
                                               _slug(t.get("label", ""))),
                    "ghost", "")
        b["settings"].update({
            "border_border": "solid",
            "border_width": dims(0, 0, 0, 2),
            "border_radius": box(0),
            "text_padding": dims(9, 0, 9, 16),
            "align": "left",
            "__typography__": typo_ref(T["meta"])})
        b["settings"].setdefault("__globals__", {}).update({
            "button_text_color": color_ref(
                C["accent_fill"] if i == 0 else C["muted"]),
            "button_background_color": color_ref(C["transparent"]),
            "border_color": color_ref(
                C["accent_fill"] if i == 0 else C["border"]),
            "hover_color": color_ref("secondary")})
        links.append(b)

    rail = container(links, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(2),
        "sticky": "top", "sticky_on": ["desktop"],
        "sticky_offset": props.get("sticky_offset", 110),
    })
    w = _tracks([24, 72], 48)
    return _fat_section([_row([_col([rail], w[0]), _col([reading], w[1])],
                              48, align="flex-start")],
                        props.get("bg", "white"), anchor=props.get("anchor"))


def _fat_table(n):
    """A table out of containers.

    Elementor core ships no table widget and this repo does not reach for a
    third-party one, so the Consecration page's feast-date table — start of the
    33-day plan, the feast, the consecration day — is a header row plus striped
    body rows. It scrolls nowhere and stacks predictably on a phone, which a
    real <table> in a text widget does not.
    """
    head = n.get("head", [])
    rows = n.get("rows", [])
    cols = max(len(head), max((len(r) for r in rows), default=1))
    w = _tracks([1] * cols, 0)

    def cell(text, header=False, last=False):
        if header:
            el = widget("heading", {
                "title": (text or "").upper(), "header_size": "div",
                "align": "right" if last else "left",
                "__typography__": typo_ref(T["eyebrow"]),
            }, globals_={"title_color": color_ref(C["on_dark"])})
        else:
            el = widget("heading", {
                "title": text or "", "header_size": "div",
                "align": "right" if last else "left",
                "__typography__": typo_ref(T["meta"] if last else T["h_small"]),
            }, globals_={"title_color": color_ref(
                C["accent_fill"] if last else "secondary")})
        return el

    header = _row([_col([cell(h, True, i == cols - 1)], w[0],
                        extra={"padding": dims(14, 22, 14, 22)})
                   for i, h in enumerate(head)], 0, align="center",
                  extra={"flex_wrap": "nowrap"})
    header = container([header], {
        "content_width": "full", "flex_direction": "column",
        "background_background": "classic",
    }, globals_={"background_color": color_ref("secondary")})

    body = []
    for i, r in enumerate(rows):
        line = _row([_col([cell(c, False, j == cols - 1)], w[0],
                          extra={"padding": dims(13, 22, 13, 22)})
                     for j, c in enumerate(r)], 0, align="center",
                    extra={"flex_wrap": "nowrap"})
        body.append(container([line], {
            "content_width": "full", "flex_direction": "column",
            "background_background": "classic",
        }, globals_={"background_color": color_ref(
            C["surface"] if i % 2 else C["white"])}))

    return container([header] + body, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(0),
        "border_radius": R_FAT,
        "border_border": "solid", "border_width": box(1),
        "overflow": "hidden",
    }, globals_={"border_color": color_ref(C["border"])})


# ─────────────────────────── library devices ───────────────────────────────

@block("fat.numbercards")
def fat_numbercards(props):
    """Numbered cards — "How to Use These Resources", "The Devotion Consists
    of", "How to Pray the Rosary".

    Three pages of the prototype run the same shape: a brown disc with a gold
    numeral, a Lora title and one line of body, in a grid. It differs from
    `fat.steps` (the 33-day stages) because those are a reading column with a
    day range as their marker; these are a scannable grid where the ORDER is
    the only thing the number carries. Over a photograph when `image` is given,
    which is what the Resources index does.
    """
    items = props.get("items", [])
    cols = props.get("columns", 3)
    on_photo = bool(props.get("image", {}).get("url"))
    w = _tracks([1] * cols, FAT_GUTTER)[0]
    cards = []
    for i, it in enumerate(items, 1):
        kids = [_numdisc(i, on_dark=False),
                _heading(it.get("title", ""), "h3", T["h_small"], "left")]
        if it.get("text"):
            kids.append(_text(it["text"], "left", small=True))
        cards.append(_card(kids, w, tinted=False))

    grid = _row(cards, FAT_GUTTER, align="stretch", extra={"flex_wrap": "wrap"})
    head = [_fat_head(props, on_dark=on_photo)] if props.get("title") else []
    sec = _fat_section(head + [grid], "dark" if on_photo else
                       props.get("bg", "white"), anchor=props.get("anchor"))
    return _photo_ground(sec, props.get("image"),
                         props.get("position", "center 35%"),
                         props.get("overlay", 0.45))


@block("fat.downloads")
def fat_downloads(props):
    """The printables rows — Resources prototype, "Downloads & Printables".

    A download is not a resource card: there is no thumbnail to show and the
    only two things a reader needs are what the file is and what it will be
    when it opens. So the row is a rounded icon plate, a Lora title and a
    format line — "PDF · printable guide to praying the Rosary" — and the whole
    row is the link.
    """
    items = props.get("items", [])
    cols = props.get("columns", 3)
    w = _tracks([1] * cols, FAT_GUTTER)[0]
    rows = []
    for it in items:
        plate = container([widget("icon", {
            "selected_icon": icon(it.get("icon", "fas fa-download")),
            "size": slider(22), "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref("secondary")})], {
            "content_width": "full", "flex_direction": "column",
            "flex_justify_content": "center", "flex_align_items": "center",
            "width": slider(52), "min_height": slider(52),
            "_flex_shrink": "0",
            "border_radius": box(12),
            "background_background": "classic",
        }, globals_={"background_color": color_ref(C["surface"])})

        text = _col([
            _heading(it.get("title", ""), "h3", T["h_small"], "left"),
            widget("heading", {
                "title": it.get("meta", ""), "header_size": "div",
                "align": "left", "__typography__": typo_ref(T["meta"]),
            }, globals_={"title_color": color_ref(C["muted"])}),
        ], None, extra={"flex_gap": gap(4)})

        row = _row([plate, text], 20, align="center",
                   extra={"flex_wrap": "nowrap",
                          "flex_direction_mobile": "row"})
        card = _card([row], w, pad=dims(22, 26, 24, 26))
        if it.get("href"):
            card["settings"]["link"] = {"url": it["href"], "is_external": "",
                                        "nofollow": ""}
        rows.append(card)

    grid = _row(rows, FAT_GUTTER, align="stretch", extra={"flex_wrap": "wrap"})
    head = [_fat_head(props)] if props.get("title") else []
    return _fat_section(head + [grid], props.get("bg", "white"),
                        anchor=props.get("anchor"))


@block("fat.related")
def fat_related(props):
    """Related Resources — the strip that closes all twelve article pages.

    Same card as the library grid, on a photograph of the Sanctuary with the
    brown scrim over it, so a reader reaching the foot of one article is
    handed the next three rather than the footer. The prototype runs this on
    every article; leaving it off would break the one navigation path those
    pages have.
    """
    items = props.get("items", [])
    cols = props.get("columns", 3)
    w = _tracks([1] * cols, FAT_GUTTER)[0]
    cards = []
    for it in items:
        kids = [
            widget("icon", {
                "selected_icon": icon(it.get("icon", "far fa-file-alt")),
                "size": slider(26), "align": "left", "view": "default",
            }, globals_={"primary_color": color_ref(C["accent_fill"])}),
            _heading(it.get("title", ""), "h3", T["h_small"], "left"),
        ]
        if it.get("desc"):
            kids.append(_text(it["desc"], "left", small=True))
        if it.get("href"):
            b = _button(it.get("action_label", "Read"), it["href"], "ghost", "")
            b["settings"].update({
                "border_radius": R_FAT_BTN,
                "text_padding": dims(10, 20, 10, 20),
                "__typography__": typo_ref(T["meta"])})
            b["settings"].setdefault("__globals__", {}).update({
                "button_text_color": color_ref(C["accent_fill"]),
                "border_color": color_ref(C["border"]),
                "button_background_hover_color": color_ref(C["accent_fill"]),
                "hover_color": color_ref(C["on_accent"])})
            kids.append(b)
        cards.append(_card(kids, w))

    grid = _row(cards, FAT_GUTTER, align="stretch", extra={"flex_wrap": "wrap"})
    head = [_fat_head(props, on_dark=True)] if props.get("title") else []
    sec = _fat_section(head + [grid], "dark")
    return _photo_ground(sec, props.get("image"),
                         props.get("position", "center 60%"),
                         props.get("overlay", 0.55))


@block("fat.linkcards")
def fat_linkcards(props):
    """Two cross-links, one brown and one cream — "Take the Next Step".

    The prototypes close Become A Member and the Resources index with exactly
    two cards of equal weight (Consecration, Ways to Give). They are not
    `fat.cta`, which is a single full-width vermillion band with one action;
    these are a fork in the road, and the tones differ so neither reads as the
    primary.
    """
    items = props.get("items", [])
    w = _tracks([1] * max(len(items), 1), FAT_GUTTER)[0]
    cards = []
    for it in items:
        dark = it.get("tone", "cream") == "brown"
        kids = [_heading(it.get("title", ""), "h3", T["h_medium"], "left",
                         on_dark=dark)]
        if it.get("text"):
            kids.append(_text(it["text"], "left", on_dark=dark))
        if it.get("cta_label"):
            kids.append(_fat_button(it["cta_label"], it.get("cta_url", "#"),
                                    "outline" if dark else "accent"))
        card = container(kids, {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(14),
            "width": slider(w, "%"), "width_mobile": slider(100, "%"),
            "padding": dims(40, 38, 42, 38),
            "padding_mobile": dims(28, 22, 30, 22),
            "border_radius": R_FAT,
            "border_border": "solid", "border_width": box(1),
            "background_background": "classic",
        }, globals_={
            "background_color": color_ref("secondary" if dark
                                          else C["surface"]),
            "border_color": color_ref("secondary" if dark else C["border"])})
        cards.append(card)

    grid = _row(cards, FAT_GUTTER, align="stretch", extra={"flex_wrap": "wrap"})
    head = [_fat_head(props)] if props.get("title") else []
    return _fat_section(head + [grid], props.get("bg", "white"),
                        anchor=props.get("anchor"))


@block("fat.faq")
def fat_faq(props):
    """Common Questions — a short column of copy beside the accordion.

    Both prototypes use the same arrangement: a 360px column carrying the
    heading, one line and a "See all FAQs" button, with the questions stacked
    beside it. The first answer is open, which is how the prototype ships it
    and what tells a reader the rest will open too.
    """
    items = props.get("items", [])
    kids = []
    if props.get("eyebrow"):
        kids.append(_fat_eyebrow(props["eyebrow"]))
    if props.get("title"):
        kids.append(_heading(props["title"], "h2", T["h_medium"], "left"))
    if props.get("intro"):
        kids.append(_text(props["intro"], "left"))
    if props.get("cta_label"):
        kids.append(_fat_button(props["cta_label"], props.get("cta_url", "#"),
                                "brown"))
    w = _tracks([30, 66], 48)
    side = _col(kids, w[0], extra={"flex_gap": gap(16)})
    panel = _col([_faq(items, first_open=True)], w[1])
    return _fat_section([_row([side, panel], 48, align="flex-start")],
                        props.get("bg", "white"), anchor=props.get("anchor"))


@block("fat.toggle")
def fat_toggle(props):
    """The For adults / For children switch on the two examinations.

    One pill group, the current page filled brown. It is a navigation control
    between two sibling pages, not a tab widget — each page is its own
    document, so the "tab" is a link and the active state is set by whichever
    page is rendering it.
    """
    items = props.get("items", [])
    pills = []
    for it in items:
        on = bool(it.get("active"))
        b = _button(it.get("label", ""), it.get("href", "#"), "ghost", "")
        b["settings"].update({
            "border_radius": box(999),
            "text_padding": dims(12, 26, 12, 26),
            "border_border": "none", "border_width": box(0),
            "__typography__": typo_ref(T["eyebrow"])})
        b["settings"].setdefault("__globals__", {}).update({
            "button_background_color": color_ref(
                "secondary" if on else C["transparent"]),
            "button_text_color": color_ref(
                C["white"] if on else "secondary"),
            "button_background_hover_color": color_ref(C["surface_alt"]),
            "hover_color": color_ref("secondary")})
        pills.append(b)

    group = container([_row(pills, 4, align="center", extra={
        "flex_wrap": "wrap", "flex_direction_mobile": "row"})], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(4, 4, 4, 4),
        "border_radius": box(999),
        "border_border": "solid", "border_width": box(1),
        "width": slider(props.get("width", 44), "%"),
        "width_tablet": slider(70, "%"), "width_mobile": slider(100, "%"),
    }, globals_={"border_color": color_ref("secondary")})
    return _fat_section([group], props.get("bg", "white"),
                        pad=dims(40, 0, 8, 0))


@block("fat.daychips")
def fat_daychips(props):
    """The thirty-three days as numbered chips, grouped by stage.

    `fat.steps` renders the same preparation as four READING stages, and the
    Consecration page built from the earlier brief keeps that. This is the
    prototype's own device for the library version: each stage is a row, its
    title and purpose on the left, and every day in it a numbered circle that
    links to that day's readings — because a member returning on day 19 wants
    to reach day 19, not read about the third week.
    """
    stages = props.get("stages", [])
    rows = []
    for i, st in enumerate(stages):
        label = _col([
            _heading(st.get("title", ""), "h3", T["h_small"], "left"),
            _text(st.get("note", ""), "left", small=True),
        ], _tracks([26, 70], 32)[0], extra={"flex_gap": gap(4)})

        chips = []
        for d in st.get("days", []):
            b = _button(str(d.get("label", d) if isinstance(d, dict) else d),
                        (d.get("href", "#") if isinstance(d, dict) else "#"),
                        "ghost", "")
            b["settings"].update({
                "border_radius": box(999),
                "text_padding": dims(13, 13, 13, 13),
                "border_border": "solid", "border_width": box(1),
                "__typography__": typo_ref(T["meta"])})
            b["settings"].setdefault("__globals__", {}).update({
                "button_text_color": color_ref("secondary"),
                "button_background_color": color_ref(C["white"]),
                "border_color": color_ref("secondary"),
                "button_background_hover_color": color_ref("secondary"),
                "hover_color": color_ref(C["white"])})
            chips.append(b)

        chiprow = _col([_row(chips, 10, align="center",
                             extra={"flex_wrap": "wrap",
                                    "flex_direction_mobile": "row"})],
                       _tracks([26, 70], 32)[1])
        rows.append(container([_row([label, chiprow], 32, align="center")], {
            "content_width": "full", "flex_direction": "column",
            "padding": dims(20, 0, 20, 0),
            "border_border": "solid",
            "border_width": dims(1, 0, 0, 0),
        }, globals_={"border_color": color_ref(C["border"])}))

    kids = ([_fat_head(props)] if props.get("title") else []) + rows
    if props.get("footnote"):
        kids.append(_text(props["footnote"], "left"))
    return _fat_section(kids, props.get("bg", "cream"),
                        anchor=props.get("anchor"))


@block("fat.textcards")
def fat_textcards(props):
    """Plain cards carrying one statement each — the six Precepts of the
    Church on both examination pages.

    No icon, no action, no thumbnail: each card is a single Lora sentence. A
    resource card here would promise a link that does not exist.
    """
    items = props.get("items", [])
    cols = props.get("columns", 3)
    w = _tracks([1] * cols, FAT_GUTTER)[0]
    cards = []
    for it in items:
        kids = [_serif(it.get("title", ""), T["h_small"])]
        if it.get("text"):
            kids.append(_text(it["text"], "left", small=True))
        cards.append(_card(kids, w, pad=dims(26, 28, 28, 28)))
    grid = _row(cards, FAT_GUTTER, align="stretch", extra={"flex_wrap": "wrap"})
    head = [_fat_head(props)] if props.get("title") else []
    return _fat_section(head + [grid], props.get("bg", "white"),
                        anchor=props.get("anchor"))


@block("fat.rows")
def fat_rows(props):
    """Label / value rows — the six Holy Days of Obligation and their dates,
    with the optional aside panel the prototype puts beside them.

    `fat.facts` sets three or four items as columns under accent rules; this is
    a list where every row is a pair and the reader scans the right-hand
    column. Different job, different device.
    """
    lines = []
    for i, it in enumerate(props.get("items", [])):
        left = _serif(it.get("label", ""), T["h_small"])
        right = widget("heading", {
            "title": it.get("value", ""), "header_size": "div",
            "align": "right", "__typography__": typo_ref(T["meta"]),
        }, globals_={"title_color": color_ref(C["muted"])})
        lines.append(container([_row([left, right], 24, align="center", extra={
            "flex_justify_content": "space-between",
            "flex_wrap": "nowrap"})], {
            "content_width": "full", "flex_direction": "column",
            "padding": dims(14, 0, 14, 0),
            "border_border": "solid", "border_width": dims(1, 0, 0, 0),
        }, globals_={"border_color": color_ref(C["border"])}))

    listing = _col(([_heading(props["title"], "h3", T["h_small"], "left")]
                    if props.get("title") else []) + lines,
                   _tracks([58, 38], 48)[0], extra={"flex_gap": gap(0)})

    aside = props.get("aside")
    if not aside:
        return _fat_section([listing], props.get("bg", "white"))

    akids = [_heading(aside.get("title", ""), "h3", T["h_small"], "left")]
    if aside.get("text"):
        akids.append(_text(aside["text"], "left"))
    if aside.get("cta_label"):
        akids.append(_fat_button(aside["cta_label"],
                                 aside.get("cta_url", "#"), "brown"))
    panel = _col([_card(akids, None, pad=dims(32, 32, 34, 32))],
                 _tracks([58, 38], 48)[1])
    return _fat_section([_row([listing, panel], 48, align="flex-start")],
                        props.get("bg", "white"))


@block("fat.mapembed")
def fat_mapembed(props):
    """The member map.

    The prototype's own note says: "Developer: embed the existing map plugin
    from livefatima.io/map here". When the client supplies that shortcode it
    goes in the `shortcode` prop and this renders it; until then the block
    ships a bordered panel that SAYS what belongs there rather than a stock
    picture of a map, which would look finished and be a lie.
    """
    if props.get("shortcode"):
        inner = widget("shortcode", {"shortcode": props["shortcode"]})
    else:
        inner = container([
            widget("icon", {
                "selected_icon": icon("fas fa-map-marker-alt"),
                "size": slider(40), "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref("secondary")}),
            _serif(props.get("placeholder_title", "Interactive Member Map"),
                   T["h_medium"], align="center"),
            _text(props.get("placeholder_note", ""), "center", small=True),
        ], {
            "content_width": "full", "flex_direction": "column",
            "flex_justify_content": "center", "flex_align_items": "center",
            "flex_gap": gap(14),
            "min_height": slider(props.get("height", 520)),
            "min_height_mobile": slider(320),
            "padding": dims(40, 24, 40, 24),
            "border_radius": box(20),
            "border_border": "dashed", "border_width": box(1),
            "background_background": "classic",
        }, globals_={"background_color": color_ref(C["surface"]),
                     "border_color": color_ref(C["border"])})

    head = [_fat_head(props)] if props.get("title") else []
    return _fat_section(head + [inner], props.get("bg", "cream"),
                        anchor=props.get("anchor"))


@block("fat.countries")
def fat_countries(props):
    """The apostolate strip: one line naming where the Confraternity is
    active, each country marked with a vermillion dot.

    It runs under the hero on the prototype's index pages and at the foot of
    the member map. The dots pulse in the prototype's CSS; here they are
    static, because this repo ships no stylesheet — recorded as a partial on
    the device rather than faked with an animation widget.
    """
    kids = []
    if props.get("title"):
        kids.append(_serif(props["title"], T["h_small"]))
    marks = []
    for name in props.get("items", []):
        dot = container([], {
            "content_width": "full", "min_height": slider(10),
            "width": slider(10), "_flex_shrink": "0",
            "border_radius": box(999),
            "background_background": "classic",
        }, globals_={"background_color": color_ref(C["accent_fill"])})
        marks.append(_row([dot, widget("heading", {
            "title": name, "header_size": "div", "align": "left",
            "__typography__": typo_ref(T["meta"]),
        }, globals_={"title_color": color_ref("secondary")})], 10,
            align="center", extra={"flex_wrap": "nowrap",
                                   "flex_direction_mobile": "row"}))
    kids.append(_row(marks, 34, align="center",
                     extra={"flex_wrap": "wrap",
                            "flex_direction_mobile": "row"}))
    strip = container([_row(kids, 40, align="center", extra={
        "flex_wrap": "wrap", "flex_direction_mobile": "row"})], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(24, 32, 24, 32),
        "border_radius": R_FAT,
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["white"]),
                 "border_color": color_ref(C["border"])})
    return _fat_section([strip], props.get("bg", "cream"),
                        pad=dims(40, 0, 40, 0))


# ───────────────────────── Become A Member devices ─────────────────────────

@block("fat.promise")
def fat_promise(props):
    """The member's promise, on the brown card with the signature blank.

    The prototype sets it as one italic Lora sentence, centred, with a ruled
    blank where the member's name goes and a gold rule beneath. It is the
    doctrinal centre of that page — "not under the pain of any sin" — so it is
    quoted whole and never paraphrased.
    """
    text = props.get("text", "")
    kids = [_serif(text, T["h_medium"], italic=True, on_dark=True,
                   align="center", color=C["white"])]
    kids.append(container([_rule(56, on_dark=True)], {
        "content_width": "full", "flex_direction": "column",
        "flex_align_items": "center"}))
    card = container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(22), "flex_align_items": "center",
        "padding": dims(62, 72, 64, 72),
        "padding_mobile": dims(34, 22, 36, 22),
        "border_radius": R_FAT,
        "background_background": "classic",
    }, globals_={"background_color": color_ref("secondary")})
    return _fat_section([card], props.get("bg", "white"))


@block("fat.obligations")
def fat_obligations(props):
    """The seven prayers and good works, as cards over the Sanctuary photo.

    The prototype's own words under the grid — "These are promises of love, not
    laws — made not under the pain of any sin" — are part of the device, not a
    caption: the grid states seven obligations and that line is what keeps them
    from reading as conditions of membership. So the factory carries both, and
    the closing action sits beside it.
    """
    items = props.get("items", [])
    cols = props.get("columns", 4)
    w = _tracks([1] * cols, FAT_GUTTER)[0]
    cards = []
    for it in items:
        kids = [
            widget("icon", {
                "selected_icon": icon(it.get("icon", "far fa-circle")),
                "size": slider(30), "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref(C["accent_fill"])}),
            _heading(it.get("title", ""), "h3", T["h_small"], "center"),
        ]
        if it.get("text"):
            kids.append(_text(it["text"], "center", small=True))
        cards.append(_card(kids, w, pad=dims(32, 26, 34, 26),
                           extra={"flex_align_items": "center"}))

    grid = _row(cards, FAT_GUTTER, align="stretch", extra={"flex_wrap": "wrap"})
    kids = ([_fat_head(props, on_dark=True)] if props.get("title") else []) \
        + [grid]
    if props.get("foot_text") or props.get("cta_label"):
        foot = []
        if props.get("foot_text"):
            foot.append(_serif(props["foot_text"], T["h_small"], italic=True,
                               on_dark=True, align="center", color=C["white"]))
        if props.get("cta_label"):
            foot.append(_fat_button(props["cta_label"],
                                    props.get("cta_url", "#")))
        kids.append(_row(foot, 24, align="center", extra={
            "flex_wrap": "wrap", "flex_justify_content": "center",
            "padding": dims(24, 0, 0, 0)}))

    sec = _fat_section(kids, "dark", anchor=props.get("anchor"))
    return _photo_ground(sec, props.get("image"),
                         props.get("position", "center 60%"),
                         props.get("overlay", 0.6))


@block("fat.joinform")
def fat_joinform(props):
    """The enrollment form, with what-happens-next beside it.

    Built from the prototype's own field list, in its own two fieldsets — about
    you, then your address — and it carries the promise checkbox, which is the
    whole point of the page: submitting the form IS making the member's
    promise, so that consent is an explicit, required tick and not fine print
    under the button.
    """
    f = props.get("form", {})
    fields = []
    for fl in f.get("fields", []):
        item = {
            "custom_id": fl.get("id", "field"),
            "field_type": fl.get("type", "text"),
            "field_label": fl.get("label", ""),
            "width": str(fl.get("width", 100)),
        }
        if fl.get("placeholder"):
            item["placeholder"] = fl["placeholder"]
        if fl.get("required"):
            item["required"] = "true"
        if fl.get("options"):
            item["field_options"] = chr(10).join(fl["options"])
        if fl.get("text"):
            item["field_html"] = fl["text"]
        fields.append(repeater_item(**item))

    form = widget("form", {
        "form_name": f.get("form_name", "Membership"),
        "form_fields": fields,
        "button_text": f.get("submit_label", "Join the Confraternity"),
        "button_size": "md",
        "input_size": "md",
        "button_width": "100",
        "success_message": f.get("success_message", ""),
        "email_to": f.get("email", ""),
        "email_subject": f.get("email_subject", "New membership"),
        "button_border_radius": R_FAT_BTN,
    }, globals_={
        "button_background_color": color_ref(C["accent_fill"]),
        "button_text_color": color_ref(C["on_accent"]),
        "field_text_color": color_ref("secondary")})

    panel = container([form], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(36, 36, 38, 36),
        "padding_mobile": dims(24, 20, 26, 20),
        "border_radius": R_FAT,
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["surface"]),
                 "border_color": color_ref(C["border"])})

    intro = []
    if props.get("eyebrow"):
        intro.append(_fat_eyebrow(props["eyebrow"]))
    if props.get("title"):
        intro.append(_heading(props["title"], "h2", T["h_medium"], "left"))
    if props.get("intro"):
        intro.append(_text(props["intro"], "left"))
    if props.get("next_items"):
        nx = [widget("heading", {
            "title": props.get("next_title", "What happens next").upper(),
            "header_size": "div", "align": "left",
            "__typography__": typo_ref(T["eyebrow"]),
        }, globals_={"title_color": color_ref("secondary")})]
        for line in props["next_items"]:
            mark = widget("icon", {
                "selected_icon": icon("fas fa-circle"),
                "size": slider(7), "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref(GOLD)})
            nx.append(_row([mark, _text(line, "left", small=True)], 12,
                           align="flex-start",
                           extra={"flex_wrap": "nowrap",
                                  "flex_direction_mobile": "row"}))
        intro.append(container(nx, {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(10),
            "padding": dims(24, 24, 26, 24),
            "border_radius": box(10),
            "background_background": "classic",
        }, globals_={"background_color": color_ref(C["surface"])}))
    if props.get("privacy"):
        lock = widget("icon", {
            "selected_icon": icon("fas fa-lock"),
            "size": slider(15), "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref(C["muted"])})
        intro.append(_row([lock, _text(props["privacy"], "left", small=True)],
                          10, align="center",
                          extra={"flex_wrap": "nowrap",
                                 "flex_direction_mobile": "row"}))

    w = _tracks([36, 60], 48)
    return _fat_section([_row([_col(intro, w[0], extra={"flex_gap": gap(18)}),
                               _col([panel], w[1])], 48, align="flex-start")],
                        props.get("bg", "white"), anchor=props.get("anchor"))
