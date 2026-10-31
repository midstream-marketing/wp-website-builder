"""
blocks_lakes.py - Lakes Construction, Windermere.

Matched to the client's reference, soscom.co.uk/acornbuild (index + projects),
rendered 2026-10-26. The brief: keep Acorn's layout, dark theme, project
gallery and grouped project sequences; improve with lightbox, sliders,
blending hero images, animation and tabs. So:

  * Acorn's DEVICES are reproduced: the serving topbar, black header with a
    lime Free Quote button, photo hero with heavy type and a sub-line, the
    four-point strip, eyebrow-left/prose-right intro, photo service cards
    with a bold "Explore ->" link, photo split, forest CTA band, the
    three-column black footer, and - the one the client named - projects as
    GROUPS of framed, captioned photos.
  * The five IMPROVEMENTS are built in: a cross-fading Ken Burns hero
    (container background slideshow), lightbox on every project and gallery
    photo, media-carousel sliders, nested tabs, and entrance motion from the
    compile stage (ir["motion"]) plus a slow hover zoom on card photos.
  * Acorn's cream and white grounds become five shades of SLATE, because the
    brief says "dark colour scheme" and the logo was shown on slate. Lime
    #98E40E is sampled from the logo and is the only accent.

Contact details are not typed into the templates. Every phone/email shown
carries the `lc-contact` / `lc-contact-url` dynamic tags from the
lakes-site-tools plugin, with the current value as the static fallback - so
the client's one Settings screen updates the topbar, header, footer, mobile
bar and contact page together (the brief's "one global place").

    lc.topbar  lc.header  lc.footer  lc.mobilebar
    lc.hero  lc.pagehero  lc.strip  lc.introsplit  lc.cards  lc.feature
    lc.ctaband  lc.tabs  lc.projects  lc.gallery  lc.carousel  lc.steps
    lc.included  lc.faq  lc.testimonials  lc.areas  lc.related  lc.form
    lc.contactcards  lc.map  lc.legal  lc.sitemap  lc.shortcode  lc.notice
"""
from __future__ import annotations

import re

from .core import (
    container, widget, repeater_item, slider, dims, box, media, link,
    gap, color_ref, typo_ref, icon, css, dynamic,
)
from .tokens import C, T
from .blocks import (
    block, _row, _col, _tracks, _button, _text, _faq, _hover_lift,
    KIT_CONTAINER, CARD_SHADOW_SOFT,
)

LIME = "primary"        # #98E40E - the logo's lime; fills and accents
DEEP = "secondary"      # #0B0D0F - header, footer
TEXT = "text"           # #C5CDD3
PAGE = "lcpage1"        # #12161A - page ground
SLATE = "lcslat1"       # #1A1F24 - where Acorn uses sand
RAISED = "lcrais1"      # #232A31 - cards, photo frames
FOREST = "lcfore1"      # #213727 - the CTA band, as Acorn
HEAD = "lchead1"        # #F4F6F7 - headings
LINE = C["border"]      # #2E363D
MUTED = C["muted"]      # #8C979F

PAD = dims(100, 0, 100, 0)
PAD_T = dims(72, 24, 72, 24)
PAD_M = dims(56, 18, 56, 18)
R_BTN = box(3)
R_CARD = box(4)
GUTTER = 24

GROUNDS = {"page": PAGE, "slate": SLATE, "raised": RAISED, "deep": DEEP,
           "forest": FOREST}


# ─────────────────────────────── helpers ───────────────────────────────────

def _sec(children, bg="page", pad=None, anchor=None, extra=None):
    s = {
        "content_width": "boxed",
        "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "flex_gap": gap(34),
        "padding": pad or PAD,
        "padding_tablet": PAD_T,
        "padding_mobile": PAD_M,
        "background_background": "classic",
    }
    if anchor:
        s["_element_id"] = anchor
    if extra:
        s.update(extra)
    return container(children, s, globals_={
        "background_color": color_ref(GROUNDS.get(bg, PAGE))})


def _accent(text):
    """`[[phrase]]` -> the phrase in lime. Display sizes only."""
    return re.sub(r"\[\[(.+?)\]\]",
                  r'<span style="color:var(--e-global-color-primary)">\1</span>',
                  text)


def _h(text, size="h2", token=None, align="left", color=HEAD):
    return widget("heading", {
        "title": _accent(text), "header_size": size, "align": align,
    }, globals_={"title_color": color_ref(color),
                 "typography_typography": typo_ref(token or T["h_large"])})


def _p(html, align="left", small=False, color=TEXT):
    t = _text(html, align, small=small)
    t["settings"]["__globals__"]["text_color"] = color_ref(color)
    return t


def _eyebrow(text, align="left"):
    return widget("heading", {
        "title": text, "header_size": "div", "align": align,
    }, globals_={"title_color": color_ref(LIME),
                 "typography_typography": typo_ref(T["eyebrow"])})


def _contact_dyn(field, url=False):
    return dynamic("lc-contact-url" if url else "lc-contact", field=field)


def _btn(label, href, style="lime", icon_name="", dyn_field=None):
    """Acorn's two buttons, plus a hairline variant.

        lime    lime fill, near-black label (12.46:1)
        dark    forest fill, white label
        slate   raised-slate fill, white label
        ghost   white hairline on photographs
    """
    b = _button(label, href, "primary", icon_name)
    b["settings"].update({
        "border_radius": R_BTN,
        "text_padding": dims(15, 26, 15, 26),
        "border_border": "solid", "border_width": box(1),
    })
    g = b["settings"].setdefault("__globals__", {})
    fills = {"lime": (LIME, DEEP, HEAD, DEEP), "dark": (FOREST, HEAD, LIME, DEEP),
             "slate": (RAISED, HEAD, LIME, DEEP), "ghost": (C["transparent"], HEAD, HEAD, DEEP)}
    fill, ink, hov, hov_ink = fills.get(style, fills["lime"])
    g.update({"background_color": color_ref(fill),
              "border_color": color_ref(HEAD if style == "ghost" else fill),
              "button_text_color": color_ref(ink),
              "button_background_hover_color": color_ref(hov),
              "button_hover_border_color": color_ref(hov),
              "hover_color": color_ref(hov_ink),
              "typography_typography": typo_ref(T["meta"])})
    if dyn_field:
        b["settings"]["__dynamic__"] = {
            "link": _contact_dyn(dyn_field, url=True)}
    return b


def _btns(items, justify="flex-start"):
    return _row(items, 12, align="center", justify=justify, extra={
        "flex_wrap": "wrap", "flex_direction_mobile": "column",
        "flex_align_items_mobile": "stretch", "padding": dims(6, 0, 0, 0)})


def _ticks(items, columns=1, container_px=KIT_CONTAINER):
    rows = []
    for t in items:
        mark = widget("icon", {
            "selected_icon": icon("fas fa-check"), "size": slider(13),
            "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref(LIME)})
        rows.append(_row([mark, _p(t, small=True)], 12, align="flex-start",
                         extra={"flex_wrap": "nowrap",
                                "flex_direction_mobile": "row",
                                "padding": dims(5, 0, 5, 0)}))
    if columns == 1:
        return container(rows, {"content_width": "full",
                                "flex_direction": "column", "flex_gap": gap(0)})
    per = -(-len(rows) // columns)
    w = _tracks([1] * columns, 22, container=container_px * 0.9)[0]
    cols = [_col(rows[i:i + per], w, extra={"flex_gap": gap(0)})
            for i in range(0, len(rows), per)]
    return _row(cols, 22, align="flex-start", extra={"flex_wrap": "wrap"})


def _card(kids, width=None, pad=None, bg=RAISED, lift=True, extra=None):
    s = {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(12),
        "padding": pad if pad is not None else dims(26, 24, 28, 24),
        "padding_mobile": dims(22, 18, 24, 18),
        "border_radius": R_CARD,
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
        **CARD_SHADOW_SOFT,
    }
    if width:
        s.update({"width": slider(width, "%"), "width_mobile": slider(100, "%")})
    if extra:
        s.update(extra)
    el = container(kids, s, globals_={"background_color": color_ref(bg),
                                      "border_color": color_ref(LINE)})
    return _hover_lift(el, 4) if lift else el


def _img(image, height=260, radius=None, lightbox_group=None, zoom=False,
         fit="cover"):
    """Image widget. With `lightbox_group` the photo opens full screen and
    steps through every photo sharing that group. Linked to the file URL with
    the lightbox data attributes set explicitly, so it works whether or not
    the image has a Media Library ID yet."""
    radius = radius if radius is not None else R_CARD
    if not (image and image.get("url")):
        return container([], {
            "content_width": "full", "min_height": slider(height),
            "border_radius": radius, "border_border": "dashed",
            "border_width": box(1), "background_background": "classic",
        }, globals_={"background_color": color_ref(RAISED),
                     "border_color": color_ref(LINE)})
    s = {"image": media(image["url"], image.get("alt", "")),
         "image_size": "full", "width": slider(100, "%"),
         "height": slider(height), "object-fit": fit, "align": "center",
         "image_border_radius": radius}
    if lightbox_group:
        l = link(image["url"])
        l["custom_attributes"] = ("data-elementor-open-lightbox|yes,"
                                  "data-elementor-lightbox-slideshow|" + lightbox_group)
        s.update({"link_to": "custom", "link": l, "open_lightbox": "yes"})
    w = widget("image", s)
    rules = []
    if zoom:
        rules += ["selector { overflow: hidden; border-radius: inherit; }",
                  "selector img { transition: transform 1.2s cubic-bezier(.2,.6,.2,1); }",
                  "selector:hover img { transform: scale(1.06); }"]
    if lightbox_group:
        rules += ["selector a { cursor: zoom-in; }"]
    if rules:
        w["settings"]["custom_css"] = css(*rules)
    return w


def _head(props, align="left"):
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], align))
    if props.get("title"):
        kids.append(_h(props["title"], props.get("tag", "h2"), T["h_large"], align))
    if props.get("intro"):
        kids.append(container([_p(props["intro"], align)], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(props.get("intro_width", 64), "%"),
            "width_mobile": slider(100, "%"),
            "margin": (dims(0, "auto", 0, "auto") if align == "center"
                       else dims(0, 0, 0, 0))}))
    if not kids:
        return []
    return [container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(14),
        "flex_align_items": "center" if align == "center" else "flex-start"})]


def _link_line(label, href, color=HEAD):
    return widget("heading", {
        "title": label + " &rarr;", "header_size": "div", "align": "left",
        "link": link(href),
    }, globals_={"title_color": color_ref(color),
                 "typography_typography": typo_ref(T["meta"])})


def _dyn_heading(field, fallback, href_field=None, color=LIME, token=None):
    """A heading showing one contact field, read live from the plugin."""
    w = widget("heading", {"title": fallback, "header_size": "div",
                           "align": "left"},
               globals_={"title_color": color_ref(color),
                         "typography_typography": typo_ref(token or T["meta"])})
    dyn = {"title": _contact_dyn(field)}
    if href_field:
        w["settings"]["link"] = link("#")
        dyn["link"] = _contact_dyn(href_field, url=True)
    w["settings"]["__dynamic__"] = dyn
    return w


def _hairline():
    return container([], {"content_width": "full", "min_height": slider(1),
                          "background_background": "classic"},
                     globals_={"background_color": color_ref(LINE)})


# ─────────────────────────────── chrome ────────────────────────────────────

@block("lc.topbar")
def lc_topbar(props):
    left = widget("heading", {"title": props["text"], "header_size": "div",
                              "align": "left"},
                  globals_={"title_color": color_ref(TEXT),
                            "typography_typography": typo_ref(T["meta"])})
    call = widget("heading", {"title": "CALL", "header_size": "div",
                              "align": "left"},
                  globals_={"title_color": color_ref(MUTED),
                            "typography_typography": typo_ref(T["eyebrow"])})
    right = _row([call,
                  _dyn_heading("phone", props["phone"], "phone"),
                  widget("heading", {"title": "&middot;", "header_size": "div"},
                         globals_={"title_color": color_ref(MUTED)}),
                  _dyn_heading("email", props["email"], "email")],
                 10, align="center", justify="flex-end",
                 extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row",
                        "flex_justify_content_mobile": "center"})
    row = _row([left, right], 20, align="center", justify="space-between",
               extra={"flex_wrap": "nowrap", "flex_wrap_tablet": "wrap"})
    return container([row], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "padding": dims(9, 0, 9, 0), "padding_tablet": dims(9, 20, 9, 20),
        "background_background": "classic",
        "hide_mobile": "hidden-mobile",
    }, globals_={"background_color": color_ref(FOREST)})


@block("lc.header")
def lc_header(props):
    logo = widget("theme-site-logo", {
        "align": "left", "width": slider(props.get("logo_width", 210)),
        "width_mobile": slider(150), "image_size": "full",
        "image": media(props["logo"], "Lakes Construction"),
    })
    nav = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"),
        "layout": "horizontal", "align_items": "flex-end",
        "pointer": "underline", "animation_line": "fade",
        "submenu_icon": {"value": "fas fa-chevron-down", "library": "fa-solid"},
        "menu_space_between": slider(4),
        "padding_horizontal_menu_item": slider(11),
        "dropdown_top_distance": slider(14),
        "padding_horizontal_dropdown_item": slider(18),
        "padding_vertical_dropdown_item": slider(11),
        "toggle_align": "right", "full_width": "stretch",
    }, globals_={
        "menu_typography_typography": typo_ref(T["meta"]),
        "dropdown_typography_typography": typo_ref(T["body_small"]),
        "color_menu_item": color_ref(HEAD),
        "color_menu_item_hover": color_ref(LIME),
        "color_menu_item_active": color_ref(LIME),
        "pointer_color_menu_item_hover": color_ref(LIME),
        "pointer_color_menu_item_active": color_ref(LIME),
        "color_dropdown_item": color_ref(HEAD),
        "background_color_dropdown_item": color_ref(RAISED),
        "color_dropdown_item_hover": color_ref(DEEP),
        "background_color_dropdown_item_hover": color_ref(LIME),
        "color_dropdown_item_active": color_ref(DEEP),
        "background_color_dropdown_item_active": color_ref(LIME),
        "toggle_color": color_ref(HEAD),
    })
    phone = _row([
        widget("icon", {"selected_icon": icon("fas fa-phone"), "size": slider(13),
                        "align": "center", "view": "default"},
               globals_={"primary_color": color_ref(LIME)}),
        _dyn_heading("phone", props["phone"], "phone", color=HEAD),
    ], 8, align="center", extra={"flex_wrap": "nowrap",
                                 "flex_direction_mobile": "row"})
    cta = _btn(props.get("cta_label", "Free Quote"), props["cta_url"], "lime")
    cta["settings"]["text_padding"] = dims(12, 20, 12, 20)
    right = _row([phone, cta], 18, align="center", justify="flex-end",
                 extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})
    right["settings"]["hide_mobile"] = "hidden-mobile"
    right["settings"]["hide_tablet"] = "hidden-tablet"
    row = _row([
        _col([logo], 20, extra={"width_tablet": slider(50, "%"),
                                "width_mobile": slider(60, "%")}),
        _col([nav], 54, extra={"flex_align_items": "flex-end",
                               "width_tablet": slider(50, "%"),
                               "width_mobile": slider(40, "%")}),
        _col([right], 26, extra={"flex_align_items": "flex-end"}),
    ], 16, align="center", extra={
        "flex_wrap": "nowrap", "flex_wrap_tablet": "nowrap",
        "flex_direction_mobile": "row", "flex_wrap_mobile": "nowrap"})
    return container([row], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "padding": dims(14, 0, 14, 0), "padding_tablet": dims(12, 20, 12, 20),
        "padding_mobile": dims(10, 16, 10, 16),
        "background_background": "classic",
        "border_border": "solid", "border_width": dims(0, 0, 1, 0),
        "sticky": "top", "sticky_on": ["desktop", "tablet", "mobile"],
        "sticky_offset": 0,
    }, globals_={"background_color": color_ref(DEEP),
                 "border_color": color_ref(LINE)})


@block("lc.footer")
def lc_footer(props):
    brand = [widget("image", {
        "image": media(props["logo"], "Lakes Construction"),
        "image_size": "full", "width": slider(220), "align": "left"}),
        _p(props["blurb"], small=True)]
    cols = props.get("columns", [])
    widths = _tracks([1.3] + [1] * len(cols), GUTTER)
    body = [_col(brand, widths[0], extra={"flex_gap": gap(16),
                                          "width_tablet": slider(100, "%")})]
    for i, c in enumerate(cols):
        kids = [_h(c["title"], "h3", T["h_small"])]
        for l in c.get("links", []):
            if l.get("field"):
                kids.append(_dyn_heading(l["field"], l["label"],
                                         l.get("href_field"), color=TEXT,
                                         token=T["body_small"]))
                continue
            kids.append(widget("heading", {
                "title": l["label"], "header_size": "div", "align": "left",
                **({"link": link(l["url"])} if l.get("url") else {}),
            }, globals_={"title_color": color_ref(TEXT),
                         "typography_typography": typo_ref(T["body_small"])}))
        body.append(_col(kids, widths[i + 1], extra={
            "flex_gap": gap(7), "width_tablet": slider(47, "%")}))
    legal_links = [widget("heading", {
        "title": l["label"], "header_size": "div", "align": "left",
        "link": link(l["url"])},
        globals_={"title_color": color_ref(MUTED),
                  "typography_typography": typo_ref(T["meta"])})
        for l in props.get("legal_links", [])]
    bar = _row([
        widget("heading", {"title": props["legal"], "header_size": "div",
                           "align": "left"},
               globals_={"title_color": color_ref(MUTED),
                         "typography_typography": typo_ref(T["meta"])}),
        _row(legal_links, 18, align="center", justify="flex-end",
             extra={"flex_wrap": "wrap", "flex_direction_mobile": "row",
                    "width": slider(64, "%"), "width_mobile": slider(100, "%"),
                    "flex_justify_content_mobile": "flex-start"}),
    ], 16, align="center", justify="space-between",
        extra={"flex_wrap": "wrap", "padding": dims(22, 0, 0, 0),
               "border_border": "solid", "border_width": dims(1, 0, 0, 0)})
    bar["settings"].setdefault("__globals__", {})["border_color"] = color_ref(LINE)
    return container([
        _row(body, GUTTER, align="flex-start",
             extra={"flex_wrap": "nowrap", "flex_wrap_tablet": "wrap"}),
        bar,
    ], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column", "flex_gap": gap(40),
        "padding": dims(76, 0, 32, 0), "padding_tablet": dims(60, 24, 90, 24),
        "padding_mobile": dims(52, 18, 96, 18),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(DEEP)})


@block("lc.mobilebar")
def lc_mobilebar(props):
    """Phones only: Call + Free Quote pinned to the bottom of the screen."""
    call = _btn("Call", props.get("phone_href", "#"), "slate", "fas fa-phone",
                dyn_field="phone")
    quote = _btn(props.get("quote_label", "Free Quote"), props["quote_url"], "lime")
    for b in (call, quote):
        b["settings"].update({"text_padding": dims(14, 10, 14, 10),
                              "align": "justify", "border_radius": box(0)})
    bar = container([_col([call], 50, extra={"width_mobile": slider(50, "%")}),
                     _col([quote], 50, extra={"width_mobile": slider(50, "%")})], {
        "content_width": "full", "flex_direction": "row",
        "flex_direction_mobile": "row", "flex_wrap": "nowrap",
        "flex_gap": gap(0), "padding": dims(0, 0, 0, 0),
        "width": slider(100, "%"),
        "_position": "fixed", "_offset_orientation_h": "start",
        "_offset_orientation_v": "end", "_offset_x": slider(0),
        "_offset_y": slider(0), "_z_index": 9990,
        "hide_desktop": "hidden-desktop", "hide_tablet": "hidden-tablet",
        "background_background": "classic",
    }, globals_={"background_color": color_ref(DEEP)})
    return bar


# ─────────────────────────────── heroes ────────────────────────────────────

def _hero_copy(props, h1_token=None):
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"]))
    kids.append(_h(props["title"], "h1", h1_token or T["hero"]))
    if props.get("subline"):
        kids.append(_h(props["subline"], "div", T["h_small"]))
    if props.get("intro"):
        kids.append(_p(props["intro"]))
    btns = []
    if props.get("cta_label"):
        btns.append(_btn(props["cta_label"], props["cta_url"], "lime"))
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props["alt_url"], "dark"))
    if btns:
        kids.append(_btns(btns))
    return kids


@block("lc.hero")
def lc_hero(props):
    """Acorn's hero, with the photographs cross-fading under the copy.

    A container BACKGROUND slideshow rather than the Slides widget: the copy
    stays put while the images blend, which is what 'main images that blend
    or merge into each other' asks for. Slow Ken Burns, 1.6s fade, 6s dwell.
    The scrim runs at 0.62 - Acorn's is heavy too, and white 72px type over a
    lake photograph needs it."""
    col = _col(_hero_copy(props), props.get("width", 60),
               extra={"flex_gap": gap(18)})
    imgs = props["images"]
    sec = _sec([_row([col], GUTTER)], "deep",
               pad=dims(130, 0, 130, 0), anchor=props.get("anchor"),
               extra={"min_height": slider(props.get("height", 720)),
                      "min_height_mobile": slider(560),
                      "flex_justify_content": "center",
                      "padding_tablet": dims(96, 24, 96, 24),
                      "padding_mobile": dims(80, 18, 80, 18),
                      "background_background": "slideshow",
                      "background_slideshow_gallery": [
                          {"id": "", "url": i["url"]} for i in imgs],
                      "background_slideshow_loop": "yes",
                      "background_slideshow_slide_duration": 6000,
                      "background_slideshow_slide_transition": "fade",
                      "background_slideshow_transition_duration": 1600,
                      "background_slideshow_background_size": "cover",
                      "background_slideshow_background_position": "center center",
                      "background_slideshow_ken_burns": "yes",
                      "background_slideshow_ken_burns_zoom_direction": "in",
                      "background_overlay_background": "classic",
                      "background_overlay_opacity": slider(props.get("overlay", 0.62))})
    sec["settings"]["__globals__"]["background_overlay_color"] = color_ref(DEEP)
    return sec


@block("lc.pagehero")
def lc_pagehero(props):
    col = _col(_hero_copy(props), props.get("width", 64),
               extra={"flex_gap": gap(16)})
    sec = _sec([_row([col], GUTTER)], "deep",
               pad=dims(110, 0, 100, 0), anchor=props.get("anchor"),
               extra={"min_height": slider(props.get("height", 480)),
                      "flex_justify_content": "center",
                      "padding_tablet": dims(84, 24, 76, 24),
                      "padding_mobile": dims(64, 18, 60, 18)})
    imgs = props.get("images") or ([props["image"]] if props.get("image") else [])
    if len(imgs) > 1:
        sec["settings"].update({
            "background_background": "slideshow",
            "background_slideshow_gallery": [{"id": "", "url": i["url"]} for i in imgs],
            "background_slideshow_loop": "yes",
            "background_slideshow_slide_duration": 6000,
            "background_slideshow_slide_transition": "fade",
            "background_slideshow_transition_duration": 1500,
            "background_slideshow_background_size": "cover",
            "background_slideshow_ken_burns": "yes",
            "background_slideshow_ken_burns_zoom_direction": "out"})
    elif imgs:
        sec["settings"].update({
            "background_image": media(imgs[0]["url"], imgs[0].get("alt", "")),
            "background_position": props.get("position", "center center"),
            "background_size": "cover", "background_repeat": "no-repeat"})
    if imgs:
        sec["settings"].update({"background_overlay_background": "classic",
                                "background_overlay_opacity": slider(props.get("overlay", 0.66))})
        sec["settings"]["__globals__"]["background_overlay_color"] = color_ref(DEEP)
    return sec


# ─────────────────────────────── sections ──────────────────────────────────

@block("lc.strip")
def lc_strip(props):
    items = props["items"]
    w = _tracks([1] * len(items), GUTTER)[0]
    cells = [_col([_h(it["title"], "h3", T["h_small"], "center"),
                   _p(it["text"], "center", small=True, color=MUTED)], w,
                  extra={"flex_gap": gap(6), "width_tablet": slider(48, "%"),
                         "padding_mobile": dims(8, 0, 8, 0)})
             for it in items]
    return _sec([_row(cells, GUTTER, align="flex-start",
                      extra={"flex_wrap": "nowrap", "flex_wrap_tablet": "wrap"})],
                "slate", pad=dims(34, 0, 34, 0),
                extra={"padding_tablet": dims(30, 24, 30, 24),
                       "border_border": "solid", "border_width": dims(0, 0, 1, 0),
                       "__globals__": {"background_color": color_ref(SLATE),
                                       "border_color": color_ref(LINE)}})


@block("lc.introsplit")
def lc_introsplit(props):
    left = [_eyebrow(props["eyebrow"])] if props.get("eyebrow") else []
    left.append(_h(props["title"], props.get("tag", "h2"), T["h_large"]))
    right = [_p(p) for p in props.get("paragraphs", [])]
    if props.get("links"):
        right.append(_p(" &middot; ".join(
            '<a href="%s"><u>%s</u></a>' % (l["url"], l["label"])
            for l in props["links"])))
    w = _tracks([0.85, 1.15], 64)
    return _sec([_row([_col(left, w[0], extra={"flex_gap": gap(14)}),
                       _col(right, w[1], extra={"flex_gap": gap(14)})],
                      64, align="flex-start")],
                props.get("bg", "page"), anchor=props.get("anchor"))


@block("lc.cards")
def lc_cards(props):
    kids = _head(props, props.get("align", "left"))
    cols = props.get("columns", 4)
    w = _tracks([1] * cols, GUTTER)[0]
    cards = []
    for it in props["items"]:
        body = [_h(it["title"], "h3", T["h_small"])]
        if it.get("text"):
            body.append(_p(it["text"], small=True))
        if it.get("href"):
            body.append(_link_line(it.get("link_label", "Explore"), it["href"]))
        inner = container(body, {"content_width": "full",
                                 "flex_direction": "column", "flex_gap": gap(10),
                                 "padding": dims(22, 20, 24, 20), "_flex_grow": 1})
        photo = _img(it.get("image"), props.get("thumb_height", 210),
                     radius=dims(4, 4, 0, 0), zoom=True)
        cards.append(_card([photo, inner], w, pad=dims(0, 0, 0, 0), extra={
            "flex_gap": gap(0), "overflow": "hidden",
            "width_tablet": slider(_tracks([1, 1], GUTTER, 720)[0], "%")}))
    kids.append(_row(cards, GUTTER, align="stretch", extra={"flex_wrap": "wrap"}))
    if props.get("footer_cta"):
        f = props["footer_cta"]
        kids.append(_btns([_btn(f["label"], f["url"], "slate")]))
    return _sec(kids, props.get("bg", "page"), anchor=props.get("anchor"))


@block("lc.feature")
def lc_feature(props):
    copy = [_eyebrow(props["eyebrow"])] if props.get("eyebrow") else []
    copy.append(_h(props["title"], "h2", T["h_large"]))
    for p in props.get("paragraphs", []):
        copy.append(_p(p))
    if props.get("ticks"):
        copy.append(_ticks(props["ticks"], props.get("tick_columns", 1),
                           KIT_CONTAINER * 0.5))
    if props.get("cta_label"):
        copy.append(_btns([_btn(props["cta_label"], props["cta_url"],
                                props.get("cta_style", "dark"))]))
    photo = _img(props.get("image"), props.get("image_height", 460),
                 lightbox_group=props.get("lightbox"))
    w = _tracks([1, 1], 56)
    pair = [_col([photo], w[0]), _col(copy, w[1], extra={"flex_gap": gap(16)})]
    if props.get("flip"):
        pair.reverse()
    return _sec([_row(pair, 56, align="center")], props.get("bg", "slate"),
                anchor=props.get("anchor"))


@block("lc.ctaband")
def lc_ctaband(props):
    copy = [_eyebrow(props["eyebrow"])] if props.get("eyebrow") else []
    copy.append(_h(props["title"], "h2", T["h_large"]))
    if props.get("text"):
        copy.append(_p(props["text"], color=HEAD))
    btns = [_btn(props.get("cta_label", "Request a Free Quote"),
                 props["cta_url"], "lime")]
    if props.get("alt_label"):
        btns.append(_btn(props["alt_label"], props["alt_url"], "ghost"))
    w = _tracks([1.5, 1], 40)
    return _sec([_row([_col(copy, w[0], extra={"flex_gap": gap(12)}),
                       _col([_btns(btns, "flex-end")], w[1],
                            extra={"flex_align_items": "flex-end",
                                   "flex_align_items_mobile": "stretch"})],
                      40, align="center")],
                "forest", pad=dims(78, 0, 78, 0), anchor=props.get("anchor"))


@block("lc.tabs")
def lc_tabs(props):
    """Nested tabs. Each panel: photo(s) on the left - a slider with lightbox
    when there is more than one - and the copy with its link on the right."""
    kids = _head(props, "left")
    panels = []
    for t in props["tabs"]:
        imgs = t.get("images", [])
        if len(imgs) > 1:
            media_el = _carousel_widget(imgs, height=420, per_view=1)
        else:
            media_el = _img(imgs[0] if imgs else None, 420,
                            lightbox_group="tab-" + t["key"])
        copy = [_h(t["title"], "h3", T["h_medium"])]
        for p in t.get("paragraphs", []):
            copy.append(_p(p))
        if t.get("ticks"):
            copy.append(_ticks(t["ticks"], 2, KIT_CONTAINER * 0.5))
        if t.get("href"):
            copy.append(_btns([_btn(t.get("link_label", "Explore"), t["href"], "lime")]))
        w = _tracks([1.05, 1], 44)
        panels.append(container([_row([_col([media_el], w[0]),
                                        _col(copy, w[1], extra={"flex_gap": gap(14)})],
                                       44, align="center")], {
            "content_width": "full", "flex_direction": "column",
            "padding": dims(34, 30, 34, 30), "padding_mobile": dims(20, 14, 22, 14)}))
    tabs = widget("nested-tabs", {
        "tabs": [repeater_item(tab_title=t["label"]) for t in props["tabs"]],
        "tabs_justify_horizontal": "start",
        "horizontal_scroll": "enable",
        "breakpoint_selector": "none",
        "tabs_title_space_between": slider(6),
        "tabs_title_spacing": slider(0),
        "tabs_title_border_radius": dims(3, 3, 0, 0),
        "tabs_title_background_color_background": "classic",
        "tabs_title_background_color_active_background": "classic",
        "box_border_border": "solid", "box_border_width": box(1),
        "box_border_radius": dims(0, 4, 4, 4),
        "box_background_color_background": "classic",
    }, globals_={
        "tabs_title_background_color_color": color_ref(RAISED),
        "tabs_title_background_color_active_color": color_ref(LIME),
        "title_text_color": color_ref(HEAD),
        "title_text_color_active": color_ref(DEEP),
        "title_text_color_hover": color_ref(LIME),
        "title_typography_typography": typo_ref(T["meta"]),
        "box_border_color": color_ref(LINE),
        "box_background_color_color": color_ref(RAISED),
    }, children=panels)
    kids.append(tabs)
    return _sec(kids, props.get("bg", "page"), anchor=props.get("anchor"))


@block("lc.projects")
def lc_projects(props):
    """Acorn's grouped project sequences - the device the client asked to
    keep - with a lightbox that steps through each group."""
    out = []
    for g in props["groups"]:
        head = []
        head.append(_hairline())
        head += _head({"eyebrow": g.get("eyebrow"), "title": g["title"],
                       "intro": g.get("intro"), "intro_width": 70})
        w = _tracks([1, 1], 16)[0]
        cells = []
        for it in g["images"]:
            cells.append(_card([
                _img(it["image"], g.get("height", 360), radius=box(2),
                     lightbox_group="proj-" + g["key"], fit="cover"),
                widget("heading", {"title": it["caption"], "header_size": "div",
                                   "align": "left"},
                       globals_={"title_color": color_ref(HEAD),
                                 "typography_typography": typo_ref(T["meta"])}),
            ], w, pad=dims(10, 10, 14, 10), lift=False,
                extra={"flex_gap": gap(12), "width_tablet": slider(48, "%")}))
        head.append(_row(cells, 16, align="stretch", extra={"flex_wrap": "wrap"}))
        out.append(_sec(head, g.get("bg", "page"), pad=dims(40, 0, 70, 0),
                        anchor=g["key"],
                        extra={"padding_tablet": dims(34, 24, 56, 24)}))
    return container(out, {"content_width": "full", "flex_direction": "column",
                           "flex_gap": gap(0), "padding": dims(0, 0, 0, 0)})


@block("lc.gallery")
def lc_gallery(props):
    """Pro gallery: filter bar of project types, lightbox. Pro's gallery
    resolves images by Media Library ID only - the Template Kit Importer
    (1.2+) registers the kit's images and writes the IDs back."""
    kids = _head(props, "left")
    gal = widget("gallery", {
        "gallery_type": "multiple",
        "galleries": [repeater_item(
            gallery_title=g["title"],
            multiple_gallery=[{"id": "", "url": im["url"]} for im in g["images"]])
            for g in props["galleries"]],
        "show_all_galleries": "yes",
        "show_all_galleries_label": props.get("all_label", "All"),
        "gallery_layout": "masonry",
        "columns": props.get("columns", 3),
        "columns_tablet": 2, "columns_mobile": 1,
        "gap": slider(12),
        "thumbnail_image_size": "large",
        "link_to": "file", "open_lightbox": "yes",
        "image_hover_animation": "grow",
        "align_filter_bar_items": "left",
        "galleries_titles_space_between": slider(6),
        "galleries_titles_gap": slider(26),
        "image_border_radius": box(3),
    }, globals_={
        "galleries_title_color_normal": color_ref(TEXT),
        "galleries_title_color_hover": color_ref(LIME),
        "galleries_title_color_active": color_ref(LIME),
        "galleries_pointer_color_hover": color_ref(LIME),
        "galleries_pointer_color_active": color_ref(LIME),
        "galleries_titles_typography_typography": typo_ref(T["meta"]),
    })
    kids.append(gal)
    if props.get("note"):
        kids.append(_p(props["note"], small=True, color=MUTED))
    return _sec(kids, props.get("bg", "page"), anchor=props.get("anchor"))


def _carousel_widget(images, height=380, per_view=3):
    """Media carousel: arrows, dots, lightbox. Uses the image URL for both
    the slide and the lightbox link, so it needs no Media Library IDs."""
    return widget("media-carousel", {
        "skin": "carousel",
        "slides": [repeater_item(type="image",
                                 image=media(i["url"], i.get("alt", "")))
                   for i in images],
        "slides_per_view": str(per_view), "slides_per_view_tablet": "2" if per_view > 1 else "1",
        "slides_per_view_mobile": "1",
        "slides_to_scroll": "1",
        "height": slider(height), "height_mobile": slider(round(height * 0.72)),
        "image_size_size": "large",
        "image_fit": "cover",
        "space_between": slider(14),
        "show_arrows": "yes", "pagination": "bullets",
        "autoplay": "yes", "autoplay_speed": 5000, "loop": "yes",
        "pause_on_interaction": "yes", "speed": 600,
        "image_link_to_type": "",
        "slide_border_radius": box(3),
    }, globals_={"arrows_color": color_ref(HEAD),
                 "pagination_color": color_ref(LIME),
                 "pagination_color_inactive": color_ref(LINE)})


@block("lc.carousel")
def lc_carousel(props):
    kids = _head(props, "left")
    kids.append(_carousel_widget(props["images"], props.get("height", 380),
                                 props.get("per_view", 3)))
    return _sec(kids, props.get("bg", "slate"), anchor=props.get("anchor"))


@block("lc.steps")
def lc_steps(props):
    kids = _head(props, "left")
    items = props["items"]
    cols = props.get("columns", min(4, len(items)))
    w = _tracks([1] * cols, GUTTER)[0]
    cells = []
    for n, it in enumerate(items, 1):
        cells.append(_card([
            widget("heading", {"title": "%02d" % n, "header_size": "div",
                               "align": "left"},
                   globals_={"title_color": color_ref(LIME),
                             "typography_typography": typo_ref(T["h_large"])}),
            _h(it["title"], "h3", T["h_small"]),
            _p(it["text"], small=True),
        ], w, extra={"width_tablet": slider(_tracks([1, 1], GUTTER, 720)[0], "%"),
                     "border_border": "solid",
                     "border_width": dims(3, 1, 1, 1)}))
    for c in cells:
        c["settings"]["__globals__"]["border_color"] = color_ref(LINE)
    kids.append(_row(cells, GUTTER, align="stretch", extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "page"), anchor=props.get("anchor"))


@block("lc.included")
def lc_included(props):
    copy = _head({k: props.get(k) for k in ("eyebrow", "title", "intro")} |
                 {"intro_width": 100})
    copy.append(_ticks(props["items"], 2, KIT_CONTAINER * 0.55))
    if props.get("note"):
        copy.append(_p(props["note"], small=True, color=MUTED))
    w = _tracks([1.15, 0.85], 56)
    photo = _img(props.get("image"), props.get("image_height", 440),
                 lightbox_group=props.get("lightbox"))
    return _sec([_row([_col(copy, w[0], extra={"flex_gap": gap(16)}),
                       _col([photo], w[1])], 56, align="center")],
                props.get("bg", "slate"), anchor=props.get("anchor"))


@block("lc.faq")
def lc_faq(props):
    acc = _faq(props["items"], True)
    acc["settings"]["faq_schema"] = "yes"
    # The shared _faq sets accordion_item_title_color, which is NOT a
    # nested-accordion control (Elementor 4.2.4 nested-accordion.php builds
    # them as "{normal,hover,active}_{title,icon}_color"). On a light kit the
    # dead key is harmless; on this dark kit it would leave the questions in
    # the theme's near-black on slate. So the real names are set here.
    g = acc["settings"]["__globals__"]
    for k in ("accordion_item_title_color", "accordion_item_title_icon_color"):
        g.pop(k, None)
    g.update({
        "normal_title_color": color_ref(HEAD),
        "hover_title_color": color_ref(LIME),
        "active_title_color": color_ref(LIME),
        "normal_icon_color": color_ref(LIME),
        "hover_icon_color": color_ref(LIME),
        "active_icon_color": color_ref(LIME)})
    # Item borders default to Elementor's light grey #D5D8DC through a CSS
    # variable; point it at the kit's own border token.
    acc["settings"]["custom_css"] = css(
        "selector { --n-accordion-border-color: var(--e-global-color-%s); }" % LINE)
    for panel in acc["elements"]:
        for w in panel.get("elements", []):
            if w.get("widgetType") == "text-editor":
                w["settings"]["__globals__"]["text_color"] = color_ref(TEXT)
    head = _head({k: props.get(k) for k in ("eyebrow", "title", "intro")} |
                 {"intro_width": 100})
    w = _tracks([0.8, 1.2], 56)
    return _sec([_row([_col(head, w[0]), _col([acc], w[1])], 56,
                      align="flex-start")],
                props.get("bg", "page"), anchor=props.get("anchor", "faq"))


@block("lc.testimonials")
def lc_testimonials(props):
    """The brief asks for a testimonials PLACEHOLDER. Three slots, visibly
    empty, with an instruction - never written-for-them quotes."""
    kids = _head(props, "left")
    n = props.get("slots", 3)
    w = _tracks([1] * n, GUTTER)[0]
    slots = []
    for i in range(n):
        slots.append(_card([
            widget("icon", {"selected_icon": icon("fas fa-quote-left"),
                            "size": slider(22), "align": "left", "view": "default"},
                   globals_={"primary_color": color_ref(LIME)}),
            _p(props.get("slot_text", "[Customer review to be added]"),
               small=True, color=MUTED),
            widget("heading", {"title": props.get("slot_name", "[Name, town]"),
                               "header_size": "div", "align": "left"},
                   globals_={"title_color": color_ref(MUTED),
                             "typography_typography": typo_ref(T["meta"])}),
        ], w, lift=False, extra={"border_border": "dashed",
                                 "width_tablet": slider(100, "%")}))
    kids.append(_row(slots, GUTTER, align="stretch", extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "slate"), anchor=props.get("anchor"))


@block("lc.areas")
def lc_areas(props):
    """Town tiles linking to each area page."""
    kids = _head(props, props.get("align", "left"))
    cols = props.get("columns", 4)
    w = _tracks([1] * cols, 14)[0]
    tiles = []
    for it in props["items"]:
        tiles.append(_card([
            container([
                widget("icon", {"selected_icon": icon("fas fa-location-dot"),
                                "size": slider(14), "align": "left",
                                "view": "default"},
                       globals_={"primary_color": color_ref(LIME)}),
                widget("heading", {"title": it["name"], "header_size": "h3",
                                   "align": "left", "link": link(it["href"])},
                       globals_={"title_color": color_ref(HEAD),
                                 "typography_typography": typo_ref(T["h_small"])}),
            ], {"content_width": "full", "flex_direction": "row",
                "flex_direction_mobile": "row", "flex_wrap": "nowrap",
                "flex_gap": gap(10), "flex_align_items": "center"}),
            *( [_p(it["note"], small=True, color=MUTED)] if it.get("note") else []),
        ], w, pad=dims(18, 18, 18, 18),
            extra={"width_tablet": slider(_tracks([1, 1], 14, 720)[0], "%")}))
    kids.append(_row(tiles, 14, align="stretch", extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "slate"), anchor=props.get("anchor"))


@block("lc.related")
def lc_related(props):
    kids = _head(props, "left")
    cols = props.get("columns", 3)
    w = _tracks([1] * cols, GUTTER)[0]
    cards = [_card([_h(it["title"], "h3", T["h_small"]),
                    *( [_p(it["text"], small=True)] if it.get("text") else []),
                    _link_line(it.get("link_label", "Read more"), it["href"], LIME)],
                   w, extra={"width_tablet": slider(100, "%")})
             for it in props["items"]]
    kids.append(_row(cards, GUTTER, align="stretch", extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "page"), anchor=props.get("anchor"))


@block("lc.form")
def lc_form(props):
    f = props["form"]
    fields = []
    for fl in f["fields"]:
        item = {"custom_id": fl["id"], "field_type": fl.get("type", "text"),
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
        "form_name": f["form_name"], "form_fields": fields,
        "submit_actions": ["email", "redirect"],
        "email_to": f.get("email", ""),
        "email_subject": f["subject"],
        "redirect_to": f.get("redirect", "/thank-you/"),
        "button_text": f["submit"], "button_size": "md", "button_width": "100",
        "input_size": "md", "show_labels": "yes", "mark_required": "yes",
        "row_gap": slider(14), "column_gap": slider(12),
        "success_message": f.get("success", ""),
        "field_border_radius": box(3), "field_border_width": box(1),
        "button_border_radius": R_BTN,
    }, globals_={
        "button_background_color": color_ref(LIME),
        "button_text_color": color_ref(DEEP),
        "button_background_hover_color": color_ref(HEAD),
        "button_hover_color": color_ref(DEEP),
        "field_background_color": color_ref(PAGE),
        "field_text_color": color_ref(HEAD),
        "field_border_color": color_ref(LINE),
        "label_color": color_ref(HEAD),
        "mark_required_color": color_ref(LIME),
    })
    card = [_h(props["title"], "h2", T["h_medium"])]
    if props.get("intro"):
        card.append(_p(props["intro"], small=True))
    card.append(form)
    if props.get("privacy_note"):
        card.append(_p(props["privacy_note"], small=True, color=MUTED))
    card_el = _card(card, lift=False, pad=dims(34, 32, 36, 32),
                    extra={"flex_gap": gap(16)})
    side = props.get("side")
    if side:
        sk = _head({k: side.get(k) for k in ("eyebrow", "title")})
        for p in side.get("paragraphs", []):
            sk.append(_p(p))
        if side.get("ticks"):
            sk.append(_ticks(side["ticks"], 1, KIT_CONTAINER * 0.4))
        if side.get("shortcode"):
            sk.append(widget("shortcode", {"shortcode": side["shortcode"]}))
        w = _tracks([0.9, 1.1], 56)
        body = _row([_col(sk, w[0], extra={"flex_gap": gap(16)}),
                     _col([card_el], w[1])], 56, align="flex-start")
    else:
        body = card_el
    return _sec([body], props.get("bg", "page"), anchor=props.get("anchor", "quote"))


@block("lc.contactcards")
def lc_contactcards(props):
    kids = _head(props, "left")
    items = props["items"]
    w = _tracks([1] * len(items), GUTTER)[0]
    cards = []
    for it in items:
        body = [widget("icon", {"selected_icon": icon(it["icon"]), "size": slider(18),
                                "align": "left", "view": "stacked", "shape": "square",
                                "icon_padding": slider(12)},
                       globals_={"primary_color": color_ref(LIME),
                                 "secondary_color": color_ref(DEEP)}),
                widget("heading", {"title": it["label"], "header_size": "div",
                                   "align": "left"},
                       globals_={"title_color": color_ref(MUTED),
                                 "typography_typography": typo_ref(T["eyebrow"])})]
        if it.get("field"):
            body.append(_dyn_heading(it["field"], it["value"], it.get("href_field"),
                                     color=HEAD, token=T["h_small"]))
        else:
            body.append(widget("heading", {"title": it["value"], "header_size": "div",
                                           "align": "left"},
                               globals_={"title_color": color_ref(HEAD),
                                         "typography_typography": typo_ref(T["h_small"])}))
        if it.get("text"):
            body.append(_p(it["text"], small=True))
        cards.append(_card(body, w, extra={
            "width_tablet": slider(_tracks([1, 1], GUTTER, 720)[0], "%")}))
    kids.append(_row(cards, GUTTER, align="stretch", extra={"flex_wrap": "wrap"}))
    return _sec(kids, props.get("bg", "slate"), anchor=props.get("anchor"))


@block("lc.map")
def lc_map(props):
    """The plugin's click-to-load map. A raw Google Maps embed sets Google's
    cookies before consent, which PECR does not allow, so the iframe only
    loads when the visitor asks for it or has accepted 'maps' cookies."""
    kids = _head(props, "left")
    kids.append(widget("shortcode", {"shortcode": props["shortcode"]}))
    return _sec(kids, props.get("bg", "page"), anchor=props.get("anchor", "map"))


@block("lc.legal")
def lc_legal(props):
    kids = []
    if props.get("lead"):
        kids.append(_p(props["lead"]))
    for s in props["sections"]:
        kids.append(_h(s["title"], "h2", T["h_medium"]))
        for p in s.get("paragraphs", []):
            kids.append(_p(p))
    if props.get("updated"):
        kids.append(_p(props["updated"], small=True, color=MUTED))
    col = container(kids, {"content_width": "full", "flex_direction": "column",
                           "flex_gap": gap(14), "width": slider(76, "%"),
                           "width_tablet": slider(100, "%"),
                           "margin": dims(0, "auto", 0, "auto")})
    return _sec([col], "page", pad=dims(60, 0, 96, 0))


@block("lc.sitemap")
def lc_sitemap(props):
    kids = _head(props, "left")
    kids.append(widget("sitemap", {
        "sitemap_items": [repeater_item(
            sitemap_type_selector="post_type",
            sitemap_source_post_type="page",
            sitemap_title=props.get("list_title", "Pages"),
            sitemap_orderby_post_type="menu_order",
            sitemap_order="asc",
            sitemap_hierarchical="yes",
            sitemap_depth="0")],
        "sitemap_columns": "1",
        "sitemap_title_tag": "h2",
    }, globals_={"sitemap_title_color": color_ref(HEAD),
                 "sitemap_list_item_color": color_ref(TEXT),
                 "sitemap_bullet_color": color_ref(LIME),
                 "sitemap_title_typography_typography": typo_ref(T["h_medium"]),
                 "sitemap_list_item_typography_typography": typo_ref(T["body_small"])}))
    return _sec(kids, "page")


@block("lc.shortcode")
def lc_shortcode(props):
    kids = _head(props, "left")
    kids.append(widget("shortcode", {"shortcode": props["shortcode"]}))
    return _sec(kids, props.get("bg", "page"), anchor=props.get("anchor"))


@block("lc.notice")
def lc_notice(props):
    """A deletable 'complete before publishing' banner on the legal pages."""
    box_ = _card([_h(props["title"], "div", T["h_small"], color=LIME),
                  _p(props["text"], small=True)], lift=False,
                 extra={"border_width": dims(0, 0, 0, 4)})
    box_["settings"]["__globals__"]["border_color"] = color_ref(LIME)
    return _sec([box_], "page", pad=dims(44, 0, 0, 0),
                extra={"padding_tablet": dims(36, 24, 0, 24),
                       "padding_mobile": dims(28, 18, 0, 18)})
