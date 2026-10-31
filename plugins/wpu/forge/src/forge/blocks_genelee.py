"""
blocks_genelee.py — Gene Lee Skin Clinic: the Club Inject panel system.

Built 2026-09-11. The client named clubinject.com as the look they like, and
it was rendered and measured before any of this was written (see
clients/gene-lee-skin-clinic/design-spec.json). Its identity is not a layout,
it is ONE device used everywhere: a large rounded tinted PANEL floating in white
space, in a narrow centred column, with centred Garamond-over-Montserrat type
and a black pill button. Everything here is that panel, in different jobs.

    gl.announce     black strip above the header
    gl.header       wordmark, centred nav, sticky black Book pill
    gl.footer       centred, minimal, white
    gl.hero         the big grey panel that opens every page
    gl.panel        the workhorse: a tinted panel of centred prose
    gl.menu         Face / Body / Wellness as three panels side by side
    gl.treatment    one treatment: prose + its expected course, stacked lines
    gl.steps        the black "Joining is simple" panel, underlined step labels
    gl.portrait     round portrait, Garamond name, small role line
    gl.pillars      three short statements in one grey panel
    gl.quotes       real patient words, Garamond italic
    gl.faq          the black FAQ card
    gl.instastrip   the one full-bleed element: the Instagram feed
    gl.contact      Club Inject's underlined serif region headings, as channels
    gl.product      Glow Rx: a wide sand panel, image beside copy
    gl.cta          black closing panel, two pills
    gl.beforeafter  built and switched OFF until consented photos exist

What the reference does NOT have, and so this family does not either: photo
heroes, eyebrow labels over every heading, icon grids, shadows, outline
buttons, uppercase. The two disliked references are mostly those things.
"""
from __future__ import annotations

from .core import (
    container, widget, repeater_item, slider, dims, box, media, link,
    gap, color_ref, typo_ref, icon,
)
from .tokens import C, T
from .blocks import block, _row, _col, _tracks, _button, _heading, _text

NARROW = 680     # Club Inject's text panels, scaled to a 1240 canvas
HERO_W = 780
WIDE = 1080      # the only grids: the Face/Body/Wellness menu, the product
R_PANEL = box(32)
PILL = box(300)  # Club Inject's own button radius, measured

GROUND = {"grey": C["surface"], "sand": C["surface_alt"],
          "dark": "secondary", "white": C["white"]}


# ───────────────────────────── primitives ─────────────────────────────

def _dk(bg):
    return bg == "dark"


def _sec(children, pad=None, extra=None, anchor=None):
    """A WHITE section that holds one floating panel. The white space between
    panels is the design, so sections never take a colour themselves."""
    s = {"content_width": "boxed", "boxed_width": slider(1240),
         "flex_direction": "column", "flex_align_items": "center",
         "flex_gap": gap(0),
         "padding": pad or dims(36, 20, 36, 20),
         "padding_mobile": dims(20, 14, 20, 14),
         "background_background": "classic"}
    if anchor:
        s["_element_id"] = anchor
    if extra:
        s.update(extra)
    return container(children, s, globals_={
        "background_color": color_ref(C["white"])})


def _panel(children, bg="grey", width=NARROW, pad=None, align="center",
           gap_px=18):
    return container(children, {
        "content_width": "full", "flex_direction": "column",
        "flex_align_items": align, "flex_gap": gap(gap_px),
        "width": slider(width, "px"), "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"),
        "padding": pad or dims(64, 56, 64, 56),
        "padding_mobile": dims(44, 22, 44, 22),
        "border_radius": R_PANEL,
        "background_background": "classic",
    }, globals_={"background_color": color_ref(GROUND.get(bg, C["surface"]))})


def _pill(label, href, on_dark=False, big=False):
    """The only button: black pill, or white pill on a dark panel."""
    b = _button(label, href, "accent", None)
    b["settings"]["border_radius"] = PILL
    b["settings"]["text_padding"] = dims(16 if big else 13, 34 if big else 28,
                                         16 if big else 13, 34 if big else 28)
    if on_dark:
        b["settings"]["__globals__"].update({
            "background_color": color_ref(C["white"]),
            "border_color": color_ref(C["white"]),
            "button_text_color": color_ref("secondary"),
            "button_background_hover_color": color_ref(C["surface_alt"]),
            "hover_color": color_ref("secondary")})
    return b


def _lead(text, on_dark=False, size=22):
    """Club Inject's large light Montserrat line ("It's all we do.", 32px/400).
    Inline, because no step in the type scale is a light sans at display
    size and adding one would re-scale every other kit."""
    return widget("heading", {
        "title": text, "header_size": "p", "align": "center",
        "typography_typography": "custom",
        "typography_font_family": "Montserrat",
        "typography_font_size": slider(size),
        "typography_font_size_mobile": slider(round(size * 0.82)),
        "typography_font_weight": "300",
        "typography_line_height": slider(1.45, "em"),
    }, globals_={"title_color": color_ref(C["white"] if on_dark else "secondary")})


def _small(text, on_dark=False, align="center"):
    return widget("heading", {"title": text, "header_size": "div",
                              "align": align},
                  globals_={"title_color": color_ref(C["on_dark"] if on_dark
                                                     else C["muted"]),
                            "typography_typography": typo_ref(T["meta"])})


def _paras(paras, on_dark=False, align="center"):
    return [_text(p, align, on_dark=on_dark) for p in paras]


def _actions(props, on_dark=False):
    out = []
    if props.get("cta"):
        out.append(_pill(props["cta"]["label"], props["cta"]["href"], on_dark))
    if props.get("cta2"):
        # The secondary action is a quiet text link, never a second button —
        # the reference has exactly one button per panel.
        b = widget("button", {
            "text": props["cta2"]["label"], "link": link(props["cta2"]["href"]),
            "text_padding": dims(8, 4, 8, 4),
            "selected_icon": icon("fas fa-arrow-right"), "icon_align": "right",
        }, globals_={"button_text_color": color_ref(C["white"] if on_dark
                                                     else "secondary"),
                     "background_color": color_ref(C["transparent"]),
                     "typography_typography": typo_ref(T["meta"])})
        out.append(b)
    if not out:
        return []
    return [_row(out, 18, align="center", justify="center",
                 extra={"flex_direction_mobile": "column",
                        "margin": dims(8, 0, 0, 0)})]


# ─────────────────────────────── chrome ───────────────────────────────

def _wordmark(name, tagline, href="/"):
    return container([
        widget("heading", {"title": name, "header_size": "div",
                           "align": "left", "link": link(href)},
               globals_={"title_color": color_ref("secondary"),
                         "typography_typography": typo_ref(T["h_medium"])}),
        widget("heading", {"title": tagline.upper(), "header_size": "div",
                           "align": "left",
                           "typography_typography": "custom",
                           "typography_font_family": "Montserrat",
                           "typography_font_size": slider(9),
                           "typography_font_weight": "500",
                           "typography_letter_spacing": slider(2.4)},
               globals_={"title_color": color_ref(C["muted"])}),
    ], {"content_width": "full", "flex_direction": "column",
        "flex_gap": gap(2)})


@block("gl.announce")
def gl_announce(props):
    return container([widget("heading", {
        "title": props["text"], "header_size": "div", "align": "center",
        "typography_typography": "custom",
        "typography_font_family": "Montserrat",
        "typography_font_size": slider(12),
        "typography_font_weight": "400",
        "typography_letter_spacing": slider(0.6),
    }, globals_={"title_color": color_ref(C["white"])})], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(9, 16, 9, 16), "background_background": "classic",
    }, globals_={"background_color": color_ref("secondary")})


@block("gl.header")
def gl_header(props):
    """Club Inject's header — wordmark left, small centred nav with an
    underline pointer — plus the brief's sticky Book pill. Elementor Pro
    sticky on every device, because most of this practice's clients book on
    a phone and the button must stay under the thumb."""
    nav = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"), "layout": "horizontal",
        "align_items": "center", "pointer": "underline",
        "menu_space_between": slider(26), "toggle_align": "right",
        "dropdown": "tablet",
    }, globals_={"color_menu_item": color_ref("secondary"),
                 "color_menu_item_hover": color_ref(C["ink_primary"]),
                 "pointer_color_menu_item_hover": color_ref("secondary"),
                 "menu_typography_typography": typo_ref(T["meta"])})
    book = _pill(props["cta"]["label"], props["cta"]["href"])
    w = _tracks([28, 58, 14], 20)
    row = _row([
        _col([_wordmark(props["name"], props["tagline"])], w[0],
             extra={"flex_justify_content": "center",
                    "width_mobile": slider(62, "%")}),
        _col([nav], w[1], extra={"flex_justify_content": "center",
                                 "flex_align_items": "center",
                                 "width_mobile": slider(14, "%")}),
        _col([book], w[2], extra={"flex_justify_content": "center",
                                  "flex_align_items": "flex-end",
                                  "width_mobile": slider(24, "%")}),
    ], 20, align="center", extra={"flex_direction_mobile": "row",
                                  "flex_wrap": "nowrap"})
    head = container([row], {
        "content_width": "boxed", "boxed_width": slider(1240),
        "flex_direction": "column",
        "padding": dims(18, 20, 18, 20), "padding_mobile": dims(12, 14, 12, 14),
        "background_background": "classic",
        "sticky": "top", "sticky_on": ["desktop", "tablet", "mobile"],
        "sticky_effects_offset": 20, "_z_index": 99,
    }, globals_={"background_color": color_ref(C["white"])})
    kids = []
    if props.get("announce"):
        kids.append(gl_announce({"text": props["announce"]}))
    kids.append(head)
    return container(kids, {"content_width": "full",
                            "flex_direction": "column", "flex_gap": gap(0)})


@block("gl.footer")
def gl_footer(props):
    """Club Inject's footer: centred, white, a few lines. Plus the three
    pillars as one quiet line, because 'Asian-owned' and 'LGBTQ+ friendly'
    are part of what the client wants on every page."""
    links = widget("icon-list", {
        "icon_list": [repeater_item(text=i["text"], link=link(i["href"]),
                                    selected_icon={"value": "", "library": ""})
                      for i in props.get("links", [])],
        "view": "inline", "space_between": slider(22),
    }, globals_={"text_color": color_ref("secondary"),
                 "icon_typography_typography": typo_ref(T["meta"])})
    contact = widget("icon-list", {
        "icon_list": [repeater_item(text=c["text"], link=link(c["href"]),
                                    selected_icon=icon(c["icon"]))
                      for c in props.get("contact", [])],
        "view": "inline", "space_between": slider(26), "icon_size": slider(14),
    }, globals_={"text_color": color_ref("secondary"),
                 "icon_color": color_ref(C["ink_primary"]),
                 "icon_typography_typography": typo_ref(T["body_small"])})
    inner = container([
        widget("heading", {"title": props["name"], "header_size": "div",
                           "align": "center"},
               globals_={"title_color": color_ref("secondary"),
                         "typography_typography": typo_ref(T["h_large"])}),
        _small(props["pillars"]),
        container([contact], {"content_width": "full",
                              "flex_direction": "column",
                              "flex_align_items": "center"}),
        container([links], {"content_width": "full",
                            "flex_direction": "column",
                            "flex_align_items": "center"}),
        _small(props["legal"]),
    ], {"content_width": "full", "flex_direction": "column",
        "flex_align_items": "center", "flex_gap": gap(18)})
    return _sec([inner], pad=dims(72, 20, 56, 20),
                extra={"border_border": "solid",
                       "border_width": dims(1, 0, 0, 0)})


# ─────────────────────────────── panels ───────────────────────────────

@block("gl.hero")
def gl_hero(props):
    """Club Inject's hero: NO photograph. A big grey rounded panel, a Garamond
    title, a light Montserrat line, a few centred lines, one black pill, and
    one line with bold inline emphasis under it."""
    kids = []
    if props.get("eyebrow"):
        kids.append(_small(props["eyebrow"]))
    kids.append(_heading(props["h1"], "h1", T["hero"], "center"))
    if props.get("lead"):
        kids.append(_lead(props["lead"]))
    if props.get("lines"):
        kids.append(container([_lead(l, size=19) for l in props["lines"]], {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(2), "margin": dims(6, 0, 6, 0)}))
    kids += _paras(props.get("paras", []))
    kids += _actions(props)
    if props.get("note"):
        kids.append(_text(props["note"], "center", small=True))
    return _sec([_panel(kids, props.get("bg", "grey"), HERO_W,
                        pad=dims(84, 64, 84, 64), gap_px=16)],
                pad=dims(44, 20, 36, 20))


@block("gl.panel")
def gl_panel(props):
    on = _dk(props.get("bg"))
    kids = []
    if props.get("title"):
        kids.append(_heading(props["title"], props.get("size", "h2"),
                             T["h_large"], "center", on_dark=on))
    if props.get("lead"):
        kids.append(_lead(props["lead"], on, 20))
    kids += _paras(props.get("paras", []), on)
    kids += _actions(props, on)
    return _sec([_panel(kids, props.get("bg", "sand"),
                        props.get("width", NARROW))],
                anchor=props.get("anchor"))


@block("gl.menu")
def gl_menu(props):
    """Face / Body / Wellness — the brief's 'More than just skin' structure,
    built as three of the reference's panels side by side."""
    cols = props.get("columns", [])
    w = _tracks([1] * max(len(cols), 1), 20, container=WIDE)[0]
    panels = []
    for c in cols:
        on = _dk(c.get("bg"))
        items = widget("icon-list", {
            "icon_list": [repeater_item(text=i["text"], link=link(i["href"]),
                                        selected_icon={"value": "",
                                                       "library": ""})
                          for i in c.get("items", [])],
            "space_between": slider(10), "icon_align": "center",
        }, globals_={"text_color": color_ref(C["white"] if on else "secondary"),
                     "icon_typography_typography": typo_ref("text")})
        p = _panel([
            _heading(c["title"], "h3", T["h_large"], "center", on_dark=on),
            _small(c.get("tagline", ""), on),
            container([items], {"content_width": "full",
                                "flex_direction": "column",
                                "flex_align_items": "center",
                                "_flex_grow": 1}),
            _pill(c["cta"]["label"], c["cta"]["href"], on),
        ], c.get("bg", "grey"), NARROW, pad=dims(52, 30, 52, 30), gap_px=16)
        p["settings"].update({"width": slider(w, "%"),
                              "width_tablet": slider(100, "%"),
                              "flex_justify_content": "space-between"})
        panels.append(p)
    head = []
    if props.get("title"):
        head.append(_heading(props["title"], "h2", T["h_large"], "center"))
    if props.get("lead"):
        head.append(_lead(props["lead"], size=19))
    grid = container([_row(panels, 20, align="stretch")], {
        "content_width": "full", "flex_direction": "column",
        "width": slider(WIDE, "px"), "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%")})
    return _sec([container(head, {"content_width": "full",
                                  "flex_direction": "column",
                                  "flex_align_items": "center",
                                  "flex_gap": gap(10),
                                  "margin": dims(0, 0, 28, 0),
                                  "width": slider(NARROW, "px"),
                                  "width_mobile": slider(100, "%")}),
                 grid], pad=dims(52, 20, 36, 20))


@block("gl.treatment")
def gl_treatment(props):
    """One treatment. The expected course is set as centred stacked lines with
    bold values — the way Club Inject stacks its unit prices in the hero — and
    appears ONLY where the client has published those figures."""
    on = _dk(props.get("bg"))
    kids = []
    if props.get("kicker"):
        kids.append(_small(props["kicker"], on))
    kids.append(_heading(props["name"], "h2", T["h_large"], "center", on_dark=on))
    if props.get("lead"):
        kids.append(_lead(props["lead"], on, 20))
    kids += _paras(props.get("paras", []), on)
    if props.get("course"):
        lines = "".join(f"<p>{c['label']} <strong>{c['value']}</strong></p>"
                        for c in props["course"])
        kids.append(container([
            _small(props.get("course_title", "Expected course"), on),
            _text(lines, "center", on_dark=on),
        ], {"content_width": "full", "flex_direction": "column",
            "flex_gap": gap(6), "margin": dims(6, 0, 0, 0)}))
    if props.get("good_for"):
        kids.append(_text("<strong>Often chosen for:</strong> "
                          + props["good_for"], "center", on_dark=on,
                          small=True))
    kids += _actions(props, on)
    return _sec([_panel(kids, props.get("bg", "grey"), NARROW)],
                anchor=props.get("anchor"))


@block("gl.steps")
def gl_steps(props):
    """Club Inject's 'Joining is simple!' — a black panel, each step a bold
    UNDERLINED label over one line of text, one white pill at the foot."""
    kids = [_heading(props["title"], "h2", T["h_large"], "center", on_dark=True)]
    for st in props.get("steps", []):
        kids.append(_text(f"<p><strong><u>{st['label']}</u></strong></p>"
                          f"<p>{st['text']}</p>", "center", on_dark=True))
    if props.get("note"):
        kids.append(_text(f"<strong>{props['note']}</strong>", "center",
                          on_dark=True))
    kids += _actions(props, on_dark=True)
    return _sec([_panel(kids, "dark", NARROW, gap_px=14)],
                anchor=props.get("anchor"))


@block("gl.portrait")
def gl_portrait(props):
    img = widget("image", {
        "image": media(props.get("image", {}).get("url", ""),
                       props.get("image", {}).get("alt", props["name"])),
        "image_size": "full", "width": slider(180), "height": slider(180),
        "object-fit": "cover", "align": "center",
        "image_border_radius": box(999),
    })
    kids = [img,
            _heading(props["name"], props.get("size", "h2"), T["h_medium"],
                     "center"),
            _small(props.get("role", ""))]
    kids += _paras(props.get("paras", []))
    kids += _actions(props)
    return _sec([container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_align_items": "center", "flex_gap": gap(10),
        "width": slider(NARROW, "px"), "width_mobile": slider(100, "%"),
        "padding": dims(28, 0, 28, 0)})])


@block("gl.pillars")
def gl_pillars(props):
    items = props.get("items", [])
    w = _tracks([1] * max(len(items), 1), 28, container=WIDE)[0]
    cols = [_col([_heading(i["title"], "h3", T["h_medium"], "center"),
                  _text(i["text"], "center", small=True)], w,
                 extra={"flex_gap": gap(8), "flex_align_items": "center"})
            for i in items]
    head = [_heading(props["title"], "h2", T["h_large"], "center")] \
        if props.get("title") else []
    panel = _panel(head + [_row(cols, 28, align="flex-start")],
                   props.get("bg", "grey"), WIDE, pad=dims(56, 44, 56, 44),
                   gap_px=30)
    return _sec([panel])


@block("gl.quotes")
def gl_quotes(props):
    """Real patient words, verbatim from the client's own testimonials page."""
    kids = [_heading(props["title"], "h2", T["h_large"], "center")] \
        if props.get("title") else []
    for q in props.get("items", []):
        kids.append(container([
            widget("heading", {"title": f"<em>“{q['quote']}”</em>",
                               "header_size": "div", "align": "center"},
                   globals_={"title_color": color_ref("secondary"),
                             "typography_typography": typo_ref(T["h_medium"])}),
            _small(f"— {q['name']}"),
        ], {"content_width": "full", "flex_direction": "column",
            "flex_gap": gap(10), "padding": dims(14, 0, 14, 0)}))
    kids += _actions(props)
    return _sec([_panel(kids, props.get("bg", "sand"), NARROW, gap_px=10)])


@block("gl.faq")
def gl_faq(props):
    """Club Inject's FAQ: a small centred serif heading, then a BLACK rounded
    card with white bold questions, chevrons and hairline dividers."""
    titles, panes = [], []
    for q in props.get("items", []):
        titles.append(repeater_item(item_title=q["q"]))
        panes.append(container([_text(q["a"], "left", on_dark=True, small=True)],
                               {"content_width": "full",
                                "flex_direction": "column",
                                "padding": dims(0, 22, 20, 22)}))
    acc = widget("nested-accordion", {
        "items": titles, "default_state": "all_collapsed", "title_tag": "h3",
        "accordion_item_title_icon_position": "right",
        "accordion_item_title_space_between": slider(0),
        "accordion_item_title_distance_from_content": slider(0),
        "accordion_background__background": "classic",
        "accordion_border__border": "solid",
        "accordion_border__width": dims(0, 0, 1, 0),
        "accordion_item_title_icon": icon("fas fa-chevron-down"),
        "accordion_item_title_icon_active": icon("fas fa-chevron-up"),
    }, globals_={
        "accordion_item_title_color": color_ref(C["white"]),
        "accordion_item_title_typography_typography": typo_ref(T["h_small"]),
        "accordion_item_title_icon_color": color_ref(C["white"]),
        "accordion_background__color": color_ref("secondary"),
        "accordion_border__color": color_ref(C["rule_dark"]),
    }, children=panes)
    card = container([acc], {
        "content_width": "full", "flex_direction": "column",
        "width": slider(NARROW, "px"), "width_mobile": slider(100, "%"),
        "padding": dims(10, 8, 10, 8), "border_radius": box(22),
        "overflow": "hidden", "background_background": "classic",
    }, globals_={"background_color": color_ref("secondary")})
    head = _heading(props.get("title", "Frequently Asked Questions"), "h2",
                    T["h_medium"], "center")
    head["settings"]["_margin"] = dims(0, 0, 24, 0)
    return _sec([head, card], pad=dims(48, 20, 48, 20),
                anchor=props.get("anchor"))


@block("gl.instastrip")
def gl_instastrip(props):
    """The reference's one full-bleed element — its photo strip — carrying the
    Instagram feed the brief asks for. The feed itself comes from a plugin
    (Smash Balloon's `[instagram-feed]` by default); until it is installed
    the shortcode renders nothing and the handle + follow pill still stand."""
    head = container([
        _heading(props["title"], "h2", T["h_large"], "center"),
        _lead(props.get("lead", ""), size=18),
        _pill(props["cta"]["label"], props["cta"]["href"]),
    ], {"content_width": "full", "flex_direction": "column",
        "flex_align_items": "center", "flex_gap": gap(14),
        "padding": dims(0, 20, 28, 20)})
    feed = widget("shortcode", {"shortcode": props.get("shortcode",
                                                       "[instagram-feed]")})
    return container([head, feed], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(56, 0, 56, 0), "background_background": "classic",
    }, globals_={"background_color": color_ref(C["white"])})


@block("gl.contact")
def gl_contact(props):
    """Club Inject lists its studios under underlined Garamond region headings.
    Here the 'regions' are the practice's channels — book, talk, where."""
    kids = []
    for g in props.get("groups", []):
        kids.append(widget("heading", {
            "title": f"<u>{g['title']}</u>", "header_size": "h2",
            "align": "center"},
            globals_={"title_color": color_ref("secondary"),
                      "typography_typography": typo_ref(T["h_medium"])}))
        lines = "".join(f"<p><strong>{l['label']}</strong> "
                        + (f"<a href=\"{l['href']}\">{l['value']}</a>"
                           if l.get("href") else l["value"]) + "</p>"
                        for l in g["lines"])
        kids.append(_text(lines, "center"))
    kids += _actions(props)
    return _sec([_panel(kids, props.get("bg", "white"), NARROW,
                        pad=dims(24, 20, 24, 20), gap_px=12)])


@block("gl.product")
def gl_product(props):
    """Glow Rx — the brief's 'private client product page'. The one place the
    column widens, because a product needs its picture beside its words."""
    img = widget("image", {
        "image": media(props.get("image", {}).get("url", ""),
                       props.get("image", {}).get("alt", props["name"])),
        "image_size": "full", "width": slider(100, "%"), "height": slider(440),
        "height_mobile": slider(300), "object-fit": "cover",
        "image_border_radius": box(24)})
    body = [_small(props.get("kicker", ""), align="left"),
            _heading(props["name"], "h2", T["hero"], "left"),
            widget("heading", {"title": props.get("lead", ""),
                               "header_size": "p", "align": "left",
                               "typography_typography": "custom",
                               "typography_font_family": "Montserrat",
                               "typography_font_size": slider(20),
                               "typography_font_weight": "300"},
                   globals_={"title_color": color_ref("secondary")})]
    body += _paras(props.get("paras", []), align="left")
    for d in props.get("details", []):
        body.append(_text(f"<strong>{d['label']}</strong><br>{d['value']}",
                          "left", small=True))
    if props.get("cta"):
        body.append(_pill(props["cta"]["label"], props["cta"]["href"]))
    w = _tracks([46, 50], 44, container=WIDE)
    panel = _panel([_row([_col([img], w[0]),
                          _col(body, w[1], extra={"flex_gap": gap(14),
                                                  "flex_justify_content":
                                                  "center"})],
                         44, align="center")],
                   props.get("bg", "sand"), WIDE, pad=dims(40, 40, 40, 40),
                   align="stretch")
    return _sec([panel])


@block("gl.cta")
def gl_cta(props):
    kids = [_heading(props["title"], "h2", T["h_large"], "center", on_dark=True)]
    if props.get("lead"):
        kids.append(_lead(props["lead"], True, 19))
    kids += _actions(props, on_dark=True)
    return _sec([_panel(kids, "dark", NARROW)], pad=dims(36, 20, 64, 20))


@block("gl.beforeafter")
def gl_beforeafter(props):
    """Static before/after pair with the reference's Before / After labels
    overlaid. OFF until consented photographs exist — see build_ir.py."""
    def frame(img, label, side):
        return container([
            widget("image", {"image": media(img.get("url", ""), img.get("alt", "")),
                             "image_size": "full", "width": slider(100, "%"),
                             "height": slider(380), "object-fit": "cover"}),
            widget("heading", {"title": label, "header_size": "div",
                               "_position": "absolute",
                               "_offset_orientation_h": side,
                               "_offset_x": slider(10), "_offset_x_end": slider(10),
                               "_offset_orientation_v": "end",
                               "_offset_y_end": slider(10), "_z_index": 2,
                               "_padding": dims(4, 10, 4, 10),
                               "_background_background": "classic"},
                   globals_={"title_color": color_ref(C["white"]),
                             "_background_color": color_ref(C["overlay"]),
                             "typography_typography": typo_ref(T["meta"])}),
        ], {"content_width": "full", "flex_direction": "column",
            "width": slider(50, "%"), "width_mobile": slider(50, "%")})
    pair = container([frame(props["before"], "Before", "start"),
                      frame(props["after"], "After", "end")],
                     {"content_width": "full", "flex_direction": "row",
                      "flex_direction_mobile": "row", "flex_gap": gap(2),
                      "width": slider(520, "px"),
                      "width_mobile": slider(100, "%"),
                      "overflow": "hidden"})
    return _sec([_heading(props["title"], "h2", T["h_medium"], "center"), pair])
