"""
blocks_prorevive.py — the ProRevive Construction design family (`pr.*`).

The brief: "Keep the color and branding same like their earlier website." So
the reference is the client's own live site, proreviverestoration.com, and its
devices are matched rather than replaced:

    1. A NAVY TOP BAR over a white navigation bar — big white phone number on
       the left, a caps line in the middle, social icons on the right.
    2. A PHOTO HERO under a navy wash, headline left, a RED PILL phone button,
       and a "Request A Free Estimate" form on the right with rounded white
       fields and a red pill submit.
    3. The MINT RULE EYEBROW: a short mint line, then a small caps label, over
       a centred Plus Jakarta Sans heading.
    4. The phone as a RED BUTTON everywhere, never as a line of text.
    5. "Areas We Serve" and the Google reviews set on NAVY bands.
    6. A 3 x 2 "why choose us" grid of mint line icons with short labels.
    7. White process cards with a mint icon and numbered titles on grey.

What the construction site adds, because the brief asks for it:

    * A filterable portfolio (Elementor Pro gallery, `gallery_type: multiple`)
      with a lightbox. It is built for an iPad on a kitchen table: big filter
      targets, three columns that drop to two, tap-to-enlarge.
    * Before & After as a TAP TOGGLE (core `nested-tabs`), not a drag slider.
      No plugin, works with a finger, and each state is a real image with its
      own alt text.
    * Strict labelling. Stock photography is only ever shown as INSPIRATION,
      captioned as such. Before & After and "Our Projects" take real ProRevive
      jobs only; until those exist they are visible, greppable PLACEHOLDER
      slots rather than stock photos passed off as the client's work.

Two accessibility corrections to the live site, both measured:
    * The call-button red #D9534F carries white text at 3.96:1. The buttons
      use #C6443F (4.88:1) — the same red to the eye. The original stays in
      the kit as "Restoration Red".
    * Body grey #7F7F7F is 3.9:1 on white. Body text uses #5F5F5F.
    Mint is never used for text on a light ground (1.9:1); it is a rule, an
    icon and a label on navy only — which is how the live site mostly uses it.

Colour comes from the Global Kit via intake.json. The only literals are the
hero wash and shadow colours, which Elementor exposes no global for.
"""
from __future__ import annotations

import re

from .core import (
    container, widget, repeater_item, slider, dims, box, media, link, icon,
    gap, color_ref, typo_ref, dynamic,
)
from .tokens import C, T
from .blocks import (
    block, _row, _col, _tracks, _heading, _text, _button, _faq, _hover_lift,
    KIT_CONTAINER, TABLET_CONTAINER, CARD_SHADOW_SOFT,
)

# ───────────────────────────── tokens and rhythm ─────────────────────────────

NAVY = "primary"
INK = "secondary"
MINT = "accent"
RED = "ctar016"          # extra colour, intake.json
RED_HOVER = "ctah017"    # extra colour, intake.json

PAD = dims(92, 0, 92, 0)
PAD_T = dims(70, 24, 70, 24)
PAD_M = dims(56, 20, 56, 20)

R_CARD = box(8)
R_PILL = box(40)
R_FIELD = box(24)
GUTTER = 26

# The live hero runs a navy wash over its photo. Elementor has no global for
# an overlay colour, so this is one of the two literals in the family.
HERO_WASH = "rgba(1, 36, 87, 0.66)"
PAGE_WASH = "rgba(1, 36, 87, 0.74)"

GROUNDS = {"white": C["white"], "grey": C["surface"], "alt": C["surface_alt"],
           "navy": NAVY}

# `.upper()` also uppercases HTML entities, and `&AMP;` renders literally.
_ENTITY = re.compile(r"&([A-Z]+);")


def _caps(text):
    return _ENTITY.sub(lambda m: "&" + m.group(1).lower() + ";", text.upper())


def _dark(bg):
    return bg == "navy"


def _sec(children, bg="white", pad=None, extra=None, anchor=None):
    s = {
        "content_width": "boxed",
        "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "flex_gap": gap(40),
        "padding": pad or PAD,
        "padding_tablet": PAD_T,
        "padding_mobile": PAD_M,
        "background_background": "classic",
    }
    if extra:
        s.update(extra)
    if anchor:
        s["_element_id"] = anchor
    return container(children, s, globals_={
        "background_color": color_ref(GROUNDS.get(bg, C["white"]))})


# ───────────────────────────── shared parts ─────────────────────────────

def _rule(width=56):
    """The mint line. Always mint, on every ground — the one element that
    never changes colour, which is what makes it read as the brand."""
    return container([], {
        "content_width": "full",
        "width": slider(width),
        "min_height": slider(2),
        "_flex_grow": 0,
        "background_background": "classic",
    }, globals_={"background_color": color_ref(MINT)})


def _eyebrow(text, on_dark=False, align="center"):
    """Mint line + small caps label — the live site's section opener.

    On light grounds the label is grey, because mint text on white is 1.9:1.
    On navy it is mint, as on the live site.
    """
    lab = widget("heading", {
        "title": _caps(text), "header_size": "div", "align": "left",
    }, globals_={
        "title_color": color_ref(MINT if on_dark else C["muted"]),
        "typography_typography": typo_ref(T["eyebrow"]),
    })
    return _row([_rule(), lab], 14, align="center",
                justify="center" if align == "center" else "flex-start",
                extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})


def _head(props, on_dark=False, align="center", tone="dark"):
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], on_dark, align))
    if props.get("title"):
        kids.append(_heading(props["title"], props.get("size", "h2"),
                             T["h_large"], align, on_dark=on_dark, tone=tone))
    if props.get("intro"):
        kids.append(_text(props["intro"], align, on_dark=on_dark))
    w = props.get("head_width", 80 if align == "center" else 100)
    return container(kids, {
        "content_width": "full",
        "flex_direction": "column",
        "flex_gap": gap(14),
        "width": slider(w, "%"),
        "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"),
        "_flex_align_self": "center" if align == "center" else "flex-start",
    })


def _btn(label, href, style="red", icon_cls=None):
    """Four buttons, all square-shouldered except the phone pill.

    red      the conversion button (Book, Send)          white on CTA red
    call     the phone, as on the live site: a RED PILL  white on CTA red
    navy     secondary action on light grounds           white on navy
    outline  secondary action on navy / photo grounds    white hairline
    ghost    tertiary action on light grounds            navy hairline
    """
    default_icon = {"call": "fas fa-phone-alt", "red": "fas fa-arrow-right",
                    "navy": "fas fa-arrow-right", "outline": "far fa-calendar-alt",
                    "ghost": "fas fa-arrow-right"}[style]
    b = _button(label, href, "ghost", icon_cls or default_icon)
    s, g = b["settings"], b["settings"]["__globals__"]
    if style in ("red", "call"):
        g.update({
            "button_text_color": color_ref(C["white"]),
            "background_color": color_ref(RED),
            "border_color": color_ref(RED),
            "hover_color": color_ref(C["white"]),
            "button_background_hover_color": color_ref(RED_HOVER),
            "button_hover_border_color": color_ref(RED_HOVER),
        })
    elif style == "navy":
        g.update({
            "button_text_color": color_ref(C["white"]),
            "background_color": color_ref(NAVY),
            "border_color": color_ref(NAVY),
            "hover_color": color_ref(NAVY),
            "button_background_hover_color": color_ref(MINT),
            "button_hover_border_color": color_ref(MINT),
        })
    elif style == "outline":
        g.update({
            "button_text_color": color_ref(C["white"]),
            "background_color": color_ref(C["transparent"]),
            "border_color": color_ref(C["white"]),
            "hover_color": color_ref(NAVY),
            "button_background_hover_color": color_ref(MINT),
            "button_hover_border_color": color_ref(MINT),
        })
    else:
        g.update({
            "button_text_color": color_ref(NAVY),
            "background_color": color_ref(C["transparent"]),
            "border_color": color_ref(NAVY),
            "hover_color": color_ref(C["white"]),
            "button_background_hover_color": color_ref(NAVY),
            "button_hover_border_color": color_ref(NAVY),
        })
    if style == "call":
        s["border_radius"] = R_PILL
        s["icon_align"] = "left"
        s["text_padding"] = dims(17, 34, 17, 34)
    else:
        s["border_radius"] = box(4)
        s["text_padding"] = dims(16, 30, 16, 30)
    s["border_width"] = box(2)
    return b


def _actions(props, on_dark=False):
    """Phone pill + the booking action, in that order. The phone first because
    it is the live site's first action on every page."""
    out = []
    if props.get("phone_display"):
        out.append(_btn(props["phone_display"], "tel:" + props.get("phone", ""),
                        "call"))
    if props.get("cta_label"):
        out.append(_btn(props["cta_label"], props.get("cta_url", "/book-an-appointment/"),
                        "outline" if on_dark else "ghost"))
    return _row(out, 14, align="center",
                extra={"flex_direction_mobile": "column",
                       "flex_align_items_mobile": "stretch"})


def _slot(label, height=320, radius=R_CARD):
    """An honest empty photo slot. Visible, greppable, and deliberate-looking:
    a stock photo in a Before & After or an 'Our Projects' slot would present
    somebody else's work as ProRevive's, so these stay empty until real
    photos exist."""
    txt = widget("heading", {
        "title": "PLACEHOLDER &mdash; " + label, "header_size": "div",
        "align": "center",
    }, globals_={"title_color": color_ref(C["muted"]),
                 "typography_typography": typo_ref(T["meta"])})
    return container([txt], {
        "content_width": "full",
        "flex_direction": "column",
        "flex_justify_content": "center",
        "flex_align_items": "center",
        "min_height": slider(height),
        "min_height_mobile": slider(round(height * 0.72)),
        "padding": dims(20, 20, 20, 20),
        "border_radius": radius,
        "border_border": "dashed",
        "border_width": box(2),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["surface_alt"]),
                 "border_color": color_ref(C["border"])})


def _photo(image, height=320, radius=R_CARD, lightbox=False):
    image = image or {}
    if not image.get("url"):
        return _slot(image.get("slot", "project photo"), height, radius)
    s = {
        "image": media(image["url"], image.get("alt", "")),
        "image_size": "large",
        "width": slider(100, "%"),
        "height": slider(height),
        "height_mobile": slider(round(height * 0.72)),
        "object-fit": "cover",
        "image_border_radius": radius,
        "align": "center",
    }
    if lightbox:
        s.update({"link_to": "file", "open_lightbox": "yes"})
    return widget("image", s)


def _tag(text, on_dark=False):
    """Small caps label under a photo — used for 'Inspiration photo'."""
    return widget("heading", {
        "title": _caps(text), "header_size": "div", "align": "left",
    }, globals_={"title_color": color_ref(MINT if on_dark else C["muted"]),
                 "typography_typography": typo_ref(T["eyebrow"])})


def _mint_icon(icon_cls, size=30):
    return widget("icon", {
        "selected_icon": icon(icon_cls), "size": slider(size),
        "align": "left", "view": "default",
    }, globals_={"primary_color": color_ref(MINT)})


def _chip(icon_cls):
    """Mint disc with a navy icon — service-card marker."""
    ic = widget("icon", {
        "selected_icon": icon(icon_cls), "size": slider(22),
        "align": "center", "view": "default",
    }, globals_={"primary_color": color_ref(NAVY)})
    return container([ic], {
        "content_width": "full",
        "flex_direction": "row",
        "flex_justify_content": "center",
        "flex_align_items": "center",
        "width": slider(54),
        "min_height": slider(54),
        "_flex_grow": 0,
        "_flex_align_self": "flex-start",
        "border_radius": box(999),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(MINT)})


def _card(kids, pad=None, bg=None):
    return container(kids, {
        "content_width": "full",
        "flex_direction": "column",
        "flex_gap": gap(12),
        "padding": pad or dims(26, 24, 28, 24),
        "border_radius": R_CARD,
        "border_border": "solid",
        "border_width": box(1),
        "background_background": "classic",
        **CARD_SHADOW_SOFT,
    }, globals_={"background_color": color_ref(bg or C["white"]),
                 "border_color": color_ref(C["border"])})


def _grid(cells, cols, gutter=GUTTER, align="stretch"):
    w = _tracks([1] * cols, gutter)
    return _row([_col([c], w[i % cols]) for i, c in enumerate(cells)],
                gutter, align=align)


def _social(items, on_dark=True, size=16):
    icons = []
    for s in items:
        icons.append(widget("icon", {
            "selected_icon": icon(s.get("icon", "fas fa-link")),
            "size": slider(size), "align": "center", "view": "default",
            "link": link(s.get("url", "#"), external=True),
        }, globals_={"primary_color": color_ref(
            C["white"] if on_dark else NAVY)}))
    return _row(icons, 16, align="center", justify="flex-end",
                extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})


def _links(items, on_dark=True, icon_cls="fas fa-map-marker-alt"):
    return widget("icon-list", {
        "icon_list": [repeater_item(
            text=i["label"], selected_icon=icon(icon_cls),
            link=link(i.get("url", ""))) for i in items],
        "space_between": slider(10),
        "icon_size": slider(13),
    }, globals_={
        "icon_color": color_ref(MINT if on_dark else NAVY),
        "text_color": color_ref(C["white"] if on_dark else INK),
        "icon_typography_typography": typo_ref("text"),
    })


# ─────────────────────────────── forms ───────────────────────────────

def _fields(fields):
    out = []
    for f in fields:
        item = {
            "custom_id": f["id"],
            "field_type": f.get("type", "text"),
            "field_label": f.get("label", ""),
            "placeholder": f.get("placeholder", ""),
            "required": "true" if f.get("required") else "",
            "width": str(f.get("width", 100)),
        }
        if f.get("options"):
            item["field_options"] = "\n".join(f["options"])
        if f.get("rows"):
            item["rows"] = f["rows"]
        if f.get("acceptance_text"):
            item["acceptance_text"] = f["acceptance_text"]
        if f.get("type") == "upload":
            item.update({"file_sizes": str(f.get("max_mb", 10)),
                         "file_types": f.get("file_types", "jpg,jpeg,png,heic"),
                         "allow_multiple_upload": "yes",
                         "max_files": str(f.get("max_files", 6))})
        if f.get("type") == "date":
            item["use_native_date"] = "yes"
        if f.get("type") == "time":
            item["use_native_time"] = "yes"
        out.append(repeater_item(**item))
    return out


def _form(form, on_dark=False):
    """The live site's form look: rounded white fields, red pill submit.

    `labels` turns on visible labels. The hero form runs placeholder-only, as
    on the live site; the booking form shows labels, because a date and a
    time field with no label are unreadable once filled in.
    """
    labels = bool(form.get("labels"))
    s = {
        "form_name": form.get("form_name", "Estimate Request"),
        "form_fields": _fields(form["fields"]),
        "submit_actions": ["email"],
        "email_to": form.get("email", ""),
        "email_subject": "New " + form.get("form_name", "enquiry")
                         + " - ProRevive Construction website",
        "button_text": form.get("submit", "Send Message"),
        "button_size": "md",
        "button_width": "100",
        "input_size": "md",
        "show_labels": "yes" if labels else "",
        "mark_required": "yes" if labels else "",
        "row_gap": slider(14),
        "column_gap": slider(14),
        "success_message": form.get("success", ""),
        "field_border_radius": R_FIELD,
        "field_border_width": box(1),
        "button_border_radius": R_PILL,
    }
    if form.get("steps"):
        s.update({"step_type": "number_text", "step_next_label": "Next",
                  "step_previous_label": "Back"})
    return widget("form", s, globals_={
        "button_background_color": color_ref(RED),
        "button_background_hover_color": color_ref(RED_HOVER),
        "button_text_color": color_ref(C["white"]),
        "field_background_color": color_ref(C["white"]),
        "field_text_color": color_ref(INK),
        "field_border_color": color_ref(C["border"]),
        "label_color": color_ref(C["white"] if on_dark else INK),
        "step_active_primary_color": color_ref(NAVY),
        "step_completed_primary_color": color_ref(MINT),
    })


# ═══════════════════════════════ header ═══════════════════════════════

@block("pr.header")
def pr_header(props):
    """Navy top bar over a white nav bar, as on the live site. Sticky, so the
    phone and the Book button are never more than a glance away — which on an
    iPad in a consultation is also where the navigation needs to be."""
    tel = "tel:" + props.get("phone", "")
    phone = _row([
        widget("icon", {"selected_icon": icon("fas fa-phone-alt"),
                        "size": slider(18), "align": "center", "view": "default",
                        "link": link(tel)},
               globals_={"primary_color": color_ref(C["white"])}),
        widget("heading", {"title": props.get("phone_display", ""),
                           "header_size": "div", "align": "left",
                           "link": link(tel)},
               globals_={"title_color": color_ref(C["white"]),
                         "typography_typography": typo_ref(T["h_small"])}),
    ], 10, align="center", extra={"flex_wrap": "nowrap",
                                  "flex_direction_mobile": "row"})
    line = widget("heading", {
        "title": _caps(props.get("topline", "")), "header_size": "div",
        "align": "center",
    }, globals_={"title_color": color_ref(MINT),
                 "typography_typography": typo_ref(T["eyebrow"])})

    w = _tracks([30, 40, 30], 20)
    top = container([_row([
        _col([phone], w[0]),
        _col([line], w[1], extra={"flex_align_items": "center",
                                  "hide_mobile": "hidden-mobile"}),
        _col([_social(props.get("social", []))], w[2],
             extra={"flex_align_items": "flex-end",
                    "hide_mobile": "hidden-mobile"}),
    ], 20, align="center")], {
        "content_width": "boxed",
        "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "padding": dims(9, 0, 9, 0),
        "padding_tablet": dims(9, 24, 9, 24),
        "padding_mobile": dims(8, 16, 8, 16),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(NAVY)})

    if props.get("logo"):
        logo = widget("image", {
            "image": media(props["logo"], props.get("logo_alt", "")),
            "image_size": "full",
            "width": slider(props.get("logo_width", 230)),
            "width_tablet": slider(200),
            "width_mobile": slider(168),
            "align": "left",
            "link_to": "custom",
            "link": link(props.get("home", "/")),
        })
    else:
        logo = widget("theme-site-logo", {"align": "left",
                                          "width": slider(230)})
    nav = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"),
        "layout": "horizontal",
        "align_items": "center",
        "pointer": "underline",
        "menu_space_between": slider(18),
        "toggle_align": "right",
        "submenu_icon": {"value": "fas fa-caret-down", "library": "fa-solid"},
    }, globals_={
        "color_menu_item": color_ref(NAVY),
        "color_menu_item_hover": color_ref(INK),
        "color_menu_item_active": color_ref(NAVY),
        "pointer_color_menu_item_hover": color_ref(MINT),
        "pointer_color_menu_item_active": color_ref(MINT),
        "dropdown_background_color": color_ref(C["white"]),
        "dropdown_color_menu_item": color_ref(INK),
        "toggle_color": color_ref(NAVY),
        "menu_typography_typography": typo_ref(T["meta"]),
    })
    cta = _btn(props.get("cta_label", "Book an Appointment"),
               props.get("cta_url", "/book-an-appointment/"), "red",
               "far fa-calendar-alt")

    w2 = _tracks([21, 57, 22], 20)
    main = container([_row([
        _col([logo], w2[0], extra={"width_mobile": slider(62, "%")}),
        _col([nav], w2[1], extra={"flex_align_items": "center",
                                  "width_mobile": slider(34, "%")}),
        _col([cta], w2[2], extra={"flex_align_items": "flex-end",
                                  "hide_mobile": "hidden-mobile"}),
    ], 20, align="center", extra={"flex_wrap": "nowrap",
                                  "flex_direction_mobile": "row"})], {
        "content_width": "boxed",
        "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "padding": dims(14, 0, 14, 0),
        "padding_tablet": dims(12, 24, 12, 24),
        "padding_mobile": dims(10, 16, 10, 16),
        "background_background": "classic",
        **CARD_SHADOW_SOFT,
    }, globals_={"background_color": color_ref(C["white"])})

    return container([top, main], {
        "content_width": "full",
        "flex_direction": "column",
        "flex_gap": gap(0),
        "sticky": "top",
        "sticky_on": ["desktop", "tablet", "mobile"],
        "_z_index": 99,
    })


# ═════════════════════════════════ heroes ═════════════════════════════════

def _photo_ground(s, image, wash):
    if image and image.get("url"):
        s.update({
            "background_image": media(image["url"], image.get("alt", "")),
            "background_position": "center center",
            "background_size": "cover",
            "background_overlay_background": "classic",
            "background_overlay_color": wash,
        })
        return {}
    return {"background_color": color_ref(NAVY)}


@block("pr.hero")
def pr_hero(props):
    """The live home hero: photo under a navy wash, headline left, the caps
    tagline, a red phone pill — and the estimate form on the right."""
    left = []
    if props.get("eyebrow"):
        left.append(_eyebrow(props["eyebrow"], True, "left"))
    left.append(_heading(props.get("title", ""), "h1", T["hero"], "left",
                         on_dark=True))
    if props.get("tagline"):
        left.append(widget("heading", {
            "title": _caps(props["tagline"]), "header_size": "p",
            "align": "left",
        }, globals_={"title_color": color_ref(C["white"]),
                     "typography_typography": typo_ref(T["h_small"])}))
    if props.get("intro"):
        left.append(_text(props["intro"], "left", on_dark=True))
    left.append(_actions(props, on_dark=True))

    f = props.get("form") or {}
    card = container([
        _heading(f.get("title", "Request A Free Estimate"), "h2",
                 T["h_medium"], "center", on_dark=True),
        _form(f, on_dark=True),
    ], {
        "content_width": "full",
        "flex_direction": "column",
        "flex_gap": gap(18),
        "padding": dims(30, 28, 30, 28),
        "padding_mobile": dims(24, 18, 24, 18),
        "border_radius": box(12),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["overlay"])})

    w = _tracks([56, 38], 60)
    row = _row([_col(left, w[0], extra={"flex_gap": gap(20)}),
                _col([card], w[1])], 60, align="center",
               justify="space-between")
    s = {
        "content_width": "boxed",
        "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "flex_justify_content": "center",
        "min_height": slider(680),
        "min_height_mobile": slider(0),
        "padding": dims(90, 0, 90, 0),
        "padding_tablet": dims(70, 24, 70, 24),
        "padding_mobile": dims(52, 18, 52, 18),
        "background_background": "classic",
    }
    g = _photo_ground(s, props.get("image"), HERO_WASH)
    return container([row], s, globals_=g)


@block("pr.pagehero")
def pr_pagehero(props):
    """Inner-page hero: the same wash and the same two actions, shorter."""
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], True, "left"))
    kids.append(_heading(props.get("title", ""), "h1", T["h_large"], "left",
                         on_dark=True))
    if props.get("intro"):
        kids.append(_text(props["intro"], "left", on_dark=True))
    if props.get("phone_display") or props.get("cta_label"):
        kids.append(_actions(props, on_dark=True))
    body = container(kids, {
        "content_width": "full",
        "flex_direction": "column",
        "flex_gap": gap(18),
        "width": slider(70, "%"),
        "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"),
    })
    s = {
        "content_width": "boxed",
        "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "flex_justify_content": "center",
        "min_height": slider(440),
        "min_height_mobile": slider(0),
        "padding": dims(80, 0, 80, 0),
        "padding_tablet": dims(64, 24, 64, 24),
        "padding_mobile": dims(48, 18, 48, 18),
        "background_background": "classic",
    }
    g = _photo_ground(s, props.get("image"), PAGE_WASH)
    return container([body], s, globals_=g)


# ═══════════════════════════ split / prose / lists ═══════════════════════════

@block("pr.split")
def pr_split(props):
    """Photo one side, copy the other, the phone as a red button under it —
    the live site's "We Carefully Restore Your Home" section."""
    bg = props.get("bg", "white")
    on_dark = _dark(bg)
    body = []
    if props.get("eyebrow"):
        body.append(_eyebrow(props["eyebrow"], on_dark, "left"))
    if props.get("title"):
        body.append(_heading(props["title"], props.get("size", "h2"),
                             T["h_large"], "left", on_dark=on_dark))
    for p in props.get("paragraphs", []):
        body.append(_text(p, "left", on_dark=on_dark))
    if props.get("bullets"):
        body.append(_ticks(props["bullets"], on_dark))
    if props.get("phone_display") or props.get("cta_label"):
        body.append(_actions(props, on_dark))
    img = props.get("image") or {}
    photo = [_photo(img, props.get("height", 440))]
    if img.get("caption"):
        photo.append(_tag(img["caption"], on_dark))
    w = _tracks([48, 48], 56)
    cols = [_col(photo, w[0], extra={"flex_gap": gap(10)}),
            _col(body, w[1], extra={"flex_gap": gap(16)})]
    if props.get("flip"):
        cols.reverse()
    return _sec([_row(cols, 56, align="center")], bg,
                anchor=props.get("anchor"))


def _ticks(items, on_dark=False, cols=1):
    per = max(1, -(-len(items) // cols))
    chunks = [items[i:i + per] for i in range(0, len(items), per)]
    lists = [widget("icon-list", {
        "icon_list": [repeater_item(text=t, selected_icon=icon("fas fa-check-circle"),
                                    link=link("")) for t in ch],
        "space_between": slider(12),
        "icon_size": slider(16),
    }, globals_={
        "icon_color": color_ref(MINT),
        "text_color": color_ref(C["white"] if on_dark else "text"),
        "icon_typography_typography": typo_ref("text"),
    }) for ch in chunks]
    if len(lists) == 1:
        return lists[0]
    w = _tracks([1] * len(lists), 30)
    return _row([_col([l], w[i]) for i, l in enumerate(lists)], 30,
                align="flex-start")


@block("pr.checklist")
def pr_checklist(props):
    bg = props.get("bg", "white")
    on_dark = _dark(bg)
    kids = [_head(props, on_dark, props.get("align", "left"))]
    kids.append(_ticks(props.get("items", []), on_dark, props.get("columns", 2)))
    if props.get("note"):
        kids.append(_text(props["note"], "left", on_dark=on_dark, small=True))
    return _sec(kids, bg, anchor=props.get("anchor"))


@block("pr.prose")
def pr_prose(props):
    bg = props.get("bg", "white")
    on_dark = _dark(bg)
    align = props.get("align", "left")
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], on_dark, align))
    if props.get("title"):
        kids.append(_heading(props["title"], props.get("size", "h2"),
                             T["h_large"], align, on_dark=on_dark))
    for p in props.get("paragraphs", []):
        kids.append(_text(p, align, on_dark=on_dark))
    if props.get("bullets"):
        kids.append(_ticks(props["bullets"], on_dark))
    if props.get("cta_label"):
        kids.append(_row([_btn(props["cta_label"], props.get("cta_url", "#"),
                               "outline" if on_dark else "navy")], 0,
                         justify="center" if align == "center" else "flex-start"))
    inner = container(kids, {
        "content_width": "full",
        "flex_direction": "column",
        "flex_gap": gap(16),
        "width": slider(props.get("width", 82), "%"),
        "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"),
        "_flex_align_self": "center" if align == "center" else "flex-start",
    })
    return _sec([inner], bg, anchor=props.get("anchor"))


# ═══════════════════════════════ services ═══════════════════════════════

@block("pr.services")
def pr_services(props):
    """Photo-topped service cards with a mint chip — the HD icons the brief
    asks for, attached to something a visitor can click."""
    bg = props.get("bg", "grey")
    items = props.get("items", [])

    def card(it):
        kids = []
        if it.get("image") is not None:
            kids.append(_photo(it["image"], 230, R_CARD))
            # A stock photo on a service card is illustration, and says so.
            if it.get("tag"):
                kids.append(_tag(it["tag"]))
        body = [_chip(it.get("icon", "fas fa-tools"))]
        t = _heading(it.get("title", ""), "h3", T["h_medium"], "left")
        if it.get("url"):
            t["settings"]["link"] = link(it["url"])
        body.append(t)
        if it.get("text"):
            body.append(_text(it["text"], "left", small=True))
        if it.get("url"):
            body.append(_row([_btn(it.get("link_label", "Learn More"), it["url"],
                                   "ghost")], 0))
        kids.append(container(body, {"content_width": "full",
                                     "flex_direction": "column",
                                     "flex_gap": gap(12),
                                     "padding": dims(6, 4, 4, 4)}))
        return _hover_lift(_card(kids, dims(14, 14, 22, 14)), 5)

    cells = [card(it) for it in items]
    head = [_head(props, _dark(bg))] if props.get("title") else []
    return _sec(head + [_grid(cells, props.get("columns", 3))], bg,
                anchor=props.get("anchor"))


@block("pr.why")
def pr_why(props):
    """3 x 2 grid of mint line icons with short labels — the live site's
    "Why Choose Us" section. The heading is navy there, so it is here."""
    bg = props.get("bg", "white")
    on_dark = _dark(bg)

    def cell(it):
        txt = [_heading(it.get("title", ""), "h3", T["h_small"], "left",
                        on_dark=on_dark)]
        if it.get("text"):
            txt.append(_text(it["text"], "left", on_dark=on_dark, small=True))
        return _row([
            container([_mint_icon(it.get("icon", "fas fa-check"), 34)], {
                "content_width": "full", "flex_direction": "column",
                "width": slider(46), "_flex_grow": 0}),
            container(txt, {"content_width": "full", "flex_direction": "column",
                            "flex_gap": gap(6)}),
        ], 16, align="flex-start", extra={"flex_wrap": "nowrap",
                                          "flex_direction_mobile": "row"})

    head = [_head(props, on_dark, tone="brand")] if props.get("title") else []
    return _sec(head + [_grid([cell(i) for i in props.get("items", [])],
                              props.get("columns", 3), 34, "flex-start")], bg)


@block("pr.process")
def pr_process(props):
    """White cards on grey, mint icon, numbered titles — the live site's
    restoration process, rebuilt for remodeling."""
    bg = props.get("bg", "grey")

    def card(s, i):
        return _card([_row([
            container([_mint_icon(s.get("icon", "fas fa-check"), 30)], {
                "content_width": "full", "flex_direction": "column",
                "width": slider(42), "_flex_grow": 0}),
            container([
                _heading("%d. %s" % (i + 1, s.get("title", "")), "h3",
                         T["h_small"], "left"),
                _text(s.get("text", ""), "left", small=True),
            ], {"content_width": "full", "flex_direction": "column",
                "flex_gap": gap(8)}),
        ], 16, align="flex-start", extra={"flex_wrap": "nowrap",
                                          "flex_direction_mobile": "row"})],
            dims(28, 26, 28, 26))

    head = [_head(props, _dark(bg))] if props.get("title") else []
    steps = props.get("steps", [])
    return _sec(head + [_grid([card(s, i) for i, s in enumerate(steps)],
                              props.get("columns", 2))], bg,
                anchor=props.get("anchor"))


# ═══════════════════════════ areas / reviews / trust ═══════════════════════════

@block("pr.areas")
def pr_areas(props):
    """The live site's navy "Areas We Serve" band. Cities with their own
    page are links; the rest are listed, not given thin doorway pages."""
    bg = props.get("bg", "navy")
    on_dark = _dark(bg)
    items = props.get("items", [])
    cols = props.get("columns", 4)
    per = max(1, -(-len(items) // cols))
    chunks = [items[i:i + per] for i in range(0, len(items), per)]
    w = _tracks([1] * len(chunks), 24)
    grid = _row([_col([_links(ch, on_dark)], w[i],
                      extra={"width_tablet": slider(48, "%"),
                             "width_mobile": slider(100, "%")})
                 for i, ch in enumerate(chunks)], 24, align="flex-start")
    kids = [_head(props, on_dark)] if props.get("title") else []
    kids.append(grid)
    if props.get("note"):
        kids.append(_text(props["note"], "center", on_dark=on_dark, small=True))
    return _sec(kids, bg)


@block("pr.reviews")
def pr_reviews(props):
    """Navy band with the client's real Google reviews widget in a white
    frame. Renders a shortcode and no review cards of its own — typed-in
    testimonials are how sites end up publishing reviews nobody wrote."""
    bg = props.get("bg", "navy")
    on_dark = _dark(bg)
    slot = container([widget("text-editor", {
        "editor": props.get("shortcode", ""), "align": "center",
    }, globals_={"text_color": color_ref("text"),
                 "typography_typography": typo_ref("text")})], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(28, 24, 28, 24),
        "padding_mobile": dims(18, 12, 18, 12),
        "border_radius": R_CARD,
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["white"])})
    kids = [_head(props, on_dark)] if props.get("title") else []
    kids.append(slot)
    if props.get("note"):
        kids.append(_text(props["note"], "center", on_dark=on_dark, small=True))
    return _sec(kids, bg)


@block("pr.insurance")
def pr_insurance(props):
    """"Insurance Companies We Work With" on navy. Names as outlined chips
    rather than the carriers' logos: the logos are the carriers' trademarks,
    and a logo wall implies a partnership a contractor rarely has."""
    chips = []
    for name in props.get("items", []):
        chips.append(container([widget("heading", {
            "title": name, "header_size": "div", "align": "center",
        }, globals_={"title_color": color_ref(C["white"]),
                     "typography_typography": typo_ref(T["meta"])})], {
            "content_width": "full", "flex_direction": "row",
            "flex_justify_content": "center",
            "width": slider(round(44 + len(name) * 8.2)),
            "_flex_grow": 0,
            "padding": dims(10, 16, 10, 16),
            "border_radius": R_PILL,
            "border_border": "solid", "border_width": box(1),
        }, globals_={"border_color": color_ref(C["rule_dark"])}))
    kids = [_head(props, True)]
    kids.append(_row(chips, 12, align="center", justify="center",
                     extra={"flex_direction_mobile": "row"}))
    if props.get("note"):
        kids.append(_text(props["note"], "center", on_dark=True, small=True))
    return _sec(kids, "navy", pad=dims(70, 0, 70, 0))


# ═══════════════════════════ portfolio ═══════════════════════════

@block("pr.trends")
def pr_trends(props):
    """Current-trend cards. Every photo is licensed stock and is captioned
    INSPIRATION PHOTO, so nobody reads it as a ProRevive job."""
    bg = props.get("bg", "white")

    def card(it):
        return _hover_lift(_card([
            _photo(it.get("image"), 250, R_CARD, lightbox=True),
            _tag(props.get("tag", "Inspiration photo")),
            _heading(it.get("title", ""), "h3", T["h_small"], "left"),
            _text(it.get("text", ""), "left", small=True),
        ], dims(12, 12, 22, 12)), 5)

    kids = [_head(props, _dark(bg))] if props.get("title") else []
    kids.append(_grid([card(i) for i in props.get("items", [])],
                      props.get("columns", 4), 22))
    if props.get("cta_label"):
        kids.append(_row([_btn(props["cta_label"], props.get("cta_url", "/gallery/"),
                               "navy", "fas fa-images")], 0, justify="center"))
    return _sec(kids, bg, anchor=props.get("anchor"))


def _toggle(before, after, labels=("Before", "After"), height=380):
    """Before / After as a two-state tap toggle (core nested-tabs).

    A drag slider needs a third-party widget and fights the page scroll on an
    iPad; two big tabs work with one finger, and each state is a real image
    with its own alt text. `breakpoint_selector: none` keeps them as tabs on
    phones instead of collapsing to an accordion.
    """
    panels = [container([_photo(img, height, R_CARD, lightbox=True)],
                        {"content_width": "full", "flex_direction": "column",
                         "padding": dims(0, 0, 0, 0)})
              for img in (before, after)]
    return widget("nested-tabs", {
        "tabs": [repeater_item(tab_title=labels[0]),
                 repeater_item(tab_title=labels[1])],
        "tabs_justify_horizontal": "stretch",
        "title_alignment": "center",
        "horizontal_scroll": "disable",
        "breakpoint_selector": "none",
        "tabs_title_space_between": slider(8),
        "tabs_title_spacing": slider(12),
        "tabs_title_border_radius": box(4),
        "tabs_title_background_color_background": "classic",
        "tabs_title_background_color_active_background": "classic",
        "box_border_radius": R_CARD,
    }, globals_={
        "title_text_color": color_ref(NAVY),
        "title_text_color_active": color_ref(C["white"]),
        "title_text_color_hover": color_ref(NAVY),
        "tabs_title_background_color_color": color_ref(C["surface_alt"]),
        "tabs_title_background_color_active_color": color_ref(NAVY),
        "title_typography_typography": typo_ref("accent"),
    }, children=panels)


@block("pr.beforeafter")
def pr_beforeafter(props):
    """Real project pairs only. See `_toggle` for why it is a tap toggle."""
    bg = props.get("bg", "grey")

    def card(it):
        kids = [_toggle(it.get("before"), it.get("after"),
                        tuple(props.get("labels", ("Before", "After"))),
                        props.get("height", 360))]
        if it.get("meta"):
            kids.append(_tag(it["meta"]))
        kids.append(_heading(it.get("title", ""), "h3", T["h_small"], "left"))
        if it.get("text"):
            kids.append(_text(it["text"], "left", small=True))
        return _card(kids, dims(14, 14, 22, 14))

    kids = [_head(props, _dark(bg))] if props.get("title") else []
    kids.append(_grid([card(i) for i in props.get("items", [])],
                      props.get("columns", 3), 22))
    if props.get("note"):
        kids.append(_text(props["note"], "center", small=True))
    return _sec(kids, bg, anchor=props.get("anchor"))


@block("pr.gallery")
def pr_gallery(props):
    """Filterable inspiration gallery — Elementor Pro gallery in `multiple`
    mode: filter bar (All / Kitchens / Bathrooms / Reconstruction), justified
    grid, tap to open the lightbox and swipe through. Built for the iPad on a
    kitchen table as much as for the website."""
    bg = props.get("bg", "white")
    gal = widget("gallery", {
        "gallery_type": "multiple",
        "galleries": [repeater_item(
            gallery_title=g["title"],
            multiple_gallery=[{"id": "", "url": im["url"]}
                              for im in g.get("images", [])])
            for g in props.get("galleries", [])],
        "show_all_galleries": "yes",
        "show_all_galleries_label": props.get("all_label", "All"),
        "gallery_layout": "grid",
        "columns": props.get("columns", 3),
        "columns_tablet": 2,
        "columns_mobile": 1,
        "gap": slider(12),
        "aspect_ratio": "3:2",
        "thumbnail_image_size": "large",
        "link_to": "file",
        "open_lightbox": "yes",
        "align_filter_bar_items": "center",
        "galleries_titles_space_between": slider(8),
        "galleries_titles_gap": slider(26),
        "image_border_radius": box(6),
    }, globals_={
        "galleries_title_color_normal": color_ref(INK),
        "galleries_title_color_hover": color_ref(NAVY),
        "galleries_title_color_active": color_ref(NAVY),
        "galleries_pointer_color_hover": color_ref(MINT),
        "galleries_pointer_color_active": color_ref(MINT),
        "galleries_titles_typography_typography": typo_ref("accent"),
    })
    kids = [_head(props, _dark(bg))] if props.get("title") else []
    if props.get("note"):
        kids.append(_row([
            _mint_icon("fas fa-info-circle", 18),
            _text(props["note"], "left", small=True),
        ], 12, align="center", justify="center",
            extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"}))
    kids.append(gal)
    return _sec(kids, bg, anchor=props.get("anchor"))


@block("pr.photos")
def pr_photos(props):
    """Real job photos with captions and a lightbox — 'Our Projects'."""
    bg = props.get("bg", "grey")

    def tile(it):
        kids = [_photo(it.get("image"), props.get("height", 280), R_CARD,
                       lightbox=True)]
        if it.get("caption"):
            kids.append(_text(it["caption"], "left", small=True))
        return container(kids, {"content_width": "full",
                                "flex_direction": "column", "flex_gap": gap(10)})

    kids = [_head(props, _dark(bg))] if props.get("title") else []
    kids.append(_grid([tile(i) for i in props.get("items", [])],
                      props.get("columns", 3), 22, "flex-start"))
    if props.get("note"):
        kids.append(_text(props["note"], "center", small=True))
    return _sec(kids, bg, anchor=props.get("anchor"))


# ═══════════════════════════ portfolio / case studies ═══════════════════════════
#
# The gallery page answers "show me ideas". These two blocks answer the harder
# question a homeowner asks next — "show me one you actually finished" — which
# is a different job and needs different furniture: facts attached to photos.

def _spec(label, value, on_dark=False):
    """One measured fact: caps label over a navy figure.

    The unit of proof on this page. A photo on its own is a mood board; a photo
    with where, what, how long and what it took beside it is a reference.
    """
    lab = widget("heading", {
        "title": _caps(label), "header_size": "div", "align": "left",
    }, globals_={"title_color": color_ref(MINT if on_dark else C["muted"]),
                 "typography_typography": typo_ref(T["eyebrow"])})
    val = widget("heading", {
        "title": value, "header_size": "div", "align": "left",
    }, globals_={"title_color": color_ref(C["white"] if on_dark else NAVY),
                 "typography_typography": typo_ref(T["h_small"])})
    return container([lab, val], {
        "content_width": "full",
        "flex_direction": "column",
        "flex_gap": gap(4),
    })


def _specs(items, cols=None, on_dark=False, gutter=18,
           width=KIT_CONTAINER, width_tablet=TABLET_CONTAINER):
    """A row of facts, and the one place in this family where the measure has
    to be passed in.

    A percentage width survives nesting; the px gap between the columns does
    not. These grids sit inside a card and inside a padded panel, where the
    same 16px gap is four percent of the width rather than one, so widths
    reserved against the 1240px page overflow and the grid silently halves.
    `width` / `width_tablet` are the container the caller actually has.

    Two-up at tablet rather than the `_col` default of one: these are short
    pairs, and stacking four of them makes a ladder.
    """
    cells = [_spec(i["label"], i["value"], on_dark) for i in items]
    cols = cols or max(1, min(4, len(cells)))
    w = _tracks([1] * cols, gutter, width)
    wt = _tracks([1] * min(cols, 2), gutter, width_tablet)[0]
    return _row([_col([c], w[i % cols],
                      extra={"width_tablet": slider(wt, "%")})
                 for i, c in enumerate(cells)], gutter, align="flex-start")


def _specpanel(items, cols=None, on_dark=False):
    """The facts banded across the full width, on their own ground — the strip
    a client reads before they read anything else."""
    # 1240 less the 28px panel padding each side; 720 less the section's 24
    # and the panel's 28, each side, at tablet.
    return container([_specs(items, cols, on_dark, 18, 1184, 664)], {
        "content_width": "full",
        "flex_direction": "column",
        "padding": dims(24, 28, 26, 28),
        "border_radius": R_CARD,
        "border_border": "solid",
        "border_width": box(1),
        "background_background": "classic",
    }, globals_={
        "background_color": color_ref(C["rule_dark"] if on_dark else C["surface_alt"]),
        "border_color": color_ref(C["rule_dark"] if on_dark else C["border"])})


def _quote(text, attrib=None, on_dark=False):
    """The homeowner's own words, behind a mint rule. A left border rather than
    a card: a quote is an aside in the story, not another tile in the grid."""
    kids = [_text("<p><em>" + text + "</em></p>", "left", on_dark=on_dark)]
    if attrib:
        kids.append(_tag(attrib, on_dark))
    return container(kids, {
        "content_width": "full",
        "flex_direction": "column",
        "flex_gap": gap(8),
        "padding": dims(2, 0, 2, 22),
        "border_border": "solid",
        "border_width": dims(0, 0, 0, 4),
    }, globals_={"border_color": color_ref(MINT)})


def _tile(it, height=220, on_dark=False):
    """Photo with a caption under it — the detail shots in a case study. The
    lightbox is on, because on an iPad these are what gets tapped."""
    kids = [_photo(it.get("image"), height, R_CARD, lightbox=True)]
    if it.get("caption"):
        kids.append(_text(it["caption"], "left", on_dark=on_dark, small=True))
    return container(kids, {"content_width": "full",
                            "flex_direction": "column", "flex_gap": gap(10)})


@block("pr.projectindex")
def pr_projectindex(props):
    """The portfolio's contact sheet: one card per project, each carrying the
    facts a homeowner asks for and a link down to the full story.

    The stories are anchors on the same page, not separate posts. In a
    consultation you scroll to one and scroll back; a page load loses your
    place, and on a job-site connection it loses the room.
    """
    bg = props.get("bg", "white")
    cols = props.get("columns", 2)
    # What a card is really wide, so the spec grid inside it reserves the gap
    # against the card rather than against the page.
    inner = round(KIT_CONTAINER * _tracks([1] * cols, 26)[0] / 100) - 24
    inner_tablet = TABLET_CONTAINER - 24        # cards go full width at tablet

    def card(it):
        kids = [_photo(it.get("image"), props.get("height", 300), R_CARD)]
        if it.get("meta"):
            kids.append(_tag(it["meta"]))
        kids.append(_heading(it.get("title", ""), "h3", T["h_medium"], "left"))
        if it.get("text"):
            kids.append(_text(it["text"], "left", small=True))
        if it.get("specs"):
            kids.append(_specs(it["specs"], 2, gutter=16, width=inner,
                               width_tablet=inner_tablet))
        if it.get("link_label"):
            kids.append(_row([_btn(it["link_label"], it.get("link_url", "#"),
                                   "ghost", "fas fa-arrow-down")], 0))
        return _hover_lift(_card(kids, dims(12, 12, 26, 12)), 5)

    kids = [_head(props, _dark(bg))] if props.get("title") else []
    kids.append(_grid([card(i) for i in props.get("items", [])], cols, 26))
    if props.get("note"):
        kids.append(_text(props["note"], "center", small=True))
    return _sec(kids, bg, anchor=props.get("anchor"))


@block("pr.casestudy")
def pr_casestudy(props):
    """One project told the way it gets told at a kitchen table.

    The order is deliberate: the heading and where it was, then the numbers,
    then the Before | After beside what actually happened, then the close-ups,
    then the homeowner's own words. Somebody who only looks at the photos still
    picks up the scope; somebody who reads it gets the reasoning.

    The toggle is the same tap toggle the rest of the site uses — one finger,
    and no drag slider fighting the page scroll on an iPad.
    """
    bg = props.get("bg", "white")
    on_dark = _dark(bg)

    head = []
    if props.get("eyebrow"):
        head.append(_eyebrow(props["eyebrow"], on_dark, "left"))
    head.append(_heading(props.get("title", ""), props.get("size", "h2"),
                         T["h_large"], "left", on_dark=on_dark))
    if props.get("meta"):
        head.append(_tag(props["meta"], on_dark))
    if props.get("intro"):
        head.append(_text(props["intro"], "left", on_dark=on_dark))
    kids = [container(head, {
        "content_width": "full",
        "flex_direction": "column",
        "flex_gap": gap(12),
        "width": slider(props.get("head_width", 78), "%"),
        "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"),
    })]

    if props.get("specs"):
        kids.append(_specpanel(props["specs"], props.get("spec_columns"), on_dark))

    left = [_toggle(props.get("before"), props.get("after"),
                    tuple(props.get("labels", ("Before", "After"))),
                    props.get("height", 420))]
    if props.get("caption"):
        left.append(_tag(props["caption"], on_dark))

    right = []
    for s in props.get("sections", []):
        if s.get("title"):
            right.append(_heading(s["title"], "h3", T["h_small"], "left",
                                  on_dark=on_dark))
        if s.get("text"):
            right.append(_text(s["text"], "left", on_dark=on_dark, small=True))
    if props.get("scope"):
        right.append(_heading(props.get("scope_title", "Scope Of Work"), "h3",
                              T["h_small"], "left", on_dark=on_dark))
        right.append(_ticks(props["scope"], on_dark))

    w = _tracks([56, 44], 46)
    kids.append(_row([_col(left, w[0], extra={"flex_gap": gap(10)}),
                      _col(right, w[1], extra={"flex_gap": gap(12)})],
                     46, align="flex-start"))

    if props.get("details"):
        kids.append(_grid([_tile(d, props.get("detail_height", 220), on_dark)
                           for d in props["details"]],
                          props.get("detail_columns", 3), 18, "flex-start"))
    if props.get("quote"):
        q = props["quote"]
        kids.append(_quote(q.get("text", ""), q.get("attrib"), on_dark))
    if props.get("note"):
        kids.append(_text(props["note"], "left", on_dark=on_dark, small=True))
    return _sec(kids, bg, anchor=props.get("anchor"))


# ═══════════════════════ the Projects collection (Theme Builder) ═══════════════════════
#
# Four static project pages would have been less work today and a maintenance
# bill forever: a fifth project means a fifth template, and the client cannot
# add one without calling us. These four documents are the alternative —
# a card, a single template, a starter body and a grid — and together they
# mean a new project is a new WordPress post and nothing else.
#
#   pr.projectcard   loop-item   one card, every value bound to the post
#   pr.projectgrid   page        loop-grid that repeats that card
#   pr.projecthero   single-post the navy hero, title and photo from the post
#   pr.projectbody   single-post theme-post-content — the case study itself
#
# Content on a `page` is literal; content on a loop-item or a single template
# is `__dynamic__` or a theme widget. That boundary is the whole contract here,
# and it is why none of these four take copy props for the project itself.


def _dyn_photo(height=300, radius=R_CARD, fallback=""):
    """The post's featured image. `fallback` is what renders in the editor
    preview and in a QA screenshot before any project exists — without it the
    card looks broken in the library, which is how kits get returned."""
    return widget("image", {
        "image_size": "large",
        "width": slider(100, "%"),
        "height": slider(height),
        "height_mobile": slider(round(height * 0.72)),
        "object-fit": "cover",
        "image_border_radius": radius,
        "align": "center",
    }, dynamic_={"image": dynamic("post-featured-image", fallback=fallback)})


def _post_meta(on_dark=False):
    """Date and project type, as the live site sets meta: small, tracked, mint
    icons. The terms come from the `project_type` taxonomy."""
    return widget("post-info", {
        "icon_list": [
            repeater_item(type="terms", taxonomy="project_type",
                          show_avatar="", icon_align="left",
                          selected_icon=icon("fas fa-home")),
            repeater_item(type="date", date_format="F Y",
                          selected_icon=icon("far fa-calendar-alt")),
        ],
        "view": "inline",
        "icon_align": "left",
        "icon_size": slider(15),
        "divider": "yes",
        "divider_style": "solid",
    }, globals_={
        "text_color": color_ref(C["white"] if on_dark else C["muted"]),
        "icon_color": color_ref(MINT),
        "divider_color": color_ref(C["rule_dark"] if on_dark else C["border"]),
        "icon_typography_typography": typo_ref(T["meta"]),
    })


@block("pr.projectcard")
def pr_projectcard(props):
    """The loop item: one project card, every value bound to its post.

    This is the document the loop grid repeats, so it is deliberately the same
    card as the rest of the site's grids — photo, meta, title, a ghost action —
    and deliberately carries no literal copy at all beyond the button label.
    """
    kids = [
        _dyn_photo(props.get("height", 300), R_CARD,
                   props.get("fallback_image", "")),
        _post_meta(),
        widget("theme-post-title", {
            "header_size": "h3", "align": "left", "link": link(""),
        }, globals_={
            "post_title_color": color_ref(INK),
            "post_title_typography_typography": typo_ref(T["h_medium"]),
        }),
    ]
    if props.get("cta_label"):
        btn = _btn(props["cta_label"], "", "ghost", "fas fa-arrow-right")
        btn["settings"].pop("link", None)
        btn["settings"]["__dynamic__"] = {"link": dynamic("post-url")}
        kids.append(_row([btn], 0))
    card = _hover_lift(_card(kids, dims(12, 12, 26, 12)), 5)
    # A loop item is the whole document: no section wrapper, no ground. The
    # grid that repeats it owns the spacing.
    return card


@block("pr.projectgrid")
def pr_projectgrid(props):
    """The loop grid. `@loop:<key>` never becomes a raw post id here — the
    importer resolves it after the loop-item document exists, because the id
    it would otherwise carry is an id on our machine, not the client's.

    The grid ships with no query: Elementor's query group is not in the control
    registry, so setting a post type here would be an invented key that the
    editor silently drops. It is one dropdown in the editor after import, and
    the README's import steps say so.
    """
    bg = props.get("bg", "white")
    grid = widget("loop-grid", {
        "template_id": "@loop:" + props.get("loop", "project-card"),
        "columns": str(props.get("columns", 3)),
        "columns_tablet": "2",
        "columns_mobile": "1",
        "posts_per_page": props.get("per_page", 9),
        "column_gap": gap(26),
        "row_gap": gap(30),
        "pagination": props.get("pagination", "numbers"),
        "enable_nothing_found_message": "yes",
        "nothing_found_message_text": props.get(
            "empty", "The first projects are being photographed now."),
        "nothing_found_message_align": "center",
    }, globals_={
        "nothing_found_message_color": color_ref(C["muted"]),
        "pagination_color": color_ref(NAVY),
        "pagination_color_inactive": color_ref(C["muted"]),
    })
    kids = [_head(props, _dark(bg))] if props.get("title") else []
    kids.append(grid)
    if props.get("note"):
        kids.append(_text(props["note"], "center", small=True))
    if props.get("cta_label"):
        kids.append(_row([_btn(props["cta_label"], props.get("cta_url", "#"),
                               "navy", "fas fa-images")], 0, justify="center"))
    return _sec(kids, bg, anchor=props.get("anchor"))


@block("pr.projecthero")
def pr_projecthero(props):
    """The single template's hero: the same navy wash as every other inner
    page, with the title and the photo coming from the post instead of from
    copy. `fallback` matters — it is what the editor and the QA screenshot
    show before a real project exists."""
    kids = []
    if props.get("eyebrow"):
        kids.append(_eyebrow(props["eyebrow"], True, "left"))
    kids.append(widget("theme-post-title", {
        "header_size": "h1", "align": "left",
    }, globals_={
        "post_title_color": color_ref(C["white"]),
        "post_title_typography_typography": typo_ref(T["h_large"]),
    }))
    kids.append(_post_meta(on_dark=True))
    if props.get("intro"):
        kids.append(_text(props["intro"], "left", on_dark=True))
    if props.get("phone_display") or props.get("cta_label"):
        kids.append(_actions(props, on_dark=True))
    body = container(kids, {
        "content_width": "full",
        "flex_direction": "column",
        "flex_gap": gap(18),
        "width": slider(70, "%"),
        "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"),
    })
    s = {
        "content_width": "boxed",
        "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "flex_justify_content": "center",
        "min_height": slider(440),
        "min_height_mobile": slider(0),
        "padding": dims(80, 0, 80, 0),
        "padding_tablet": dims(64, 24, 64, 24),
        "padding_mobile": dims(48, 18, 48, 18),
        "background_background": "classic",
        "background_position": "center center",
        "background_size": "cover",
        "background_overlay_background": "classic",
        "background_overlay_color": PAGE_WASH,
    }
    return container([body], s,
                     globals_={"background_color": color_ref(NAVY)},
                     dynamic_={"background_image": dynamic(
                         "post-featured-image",
                         fallback=props.get("fallback_image", ""))})


@block("pr.projectbody")
def pr_projectbody(props):
    """`theme-post-content` — where the case study the client builds in
    Elementor actually renders. Everything designed about a project page lives
    in the post, not in this template, which is what makes the template
    reusable across ten projects and twenty."""
    bg = props.get("bg", "white")
    inner = container([widget("theme-post-content", {"align": "left"},
                              globals_={
                                  "text_color": color_ref("text"),
                                  "content_typography_typography": typo_ref("text"),
                              })], {
        "content_width": "full",
        "flex_direction": "column",
        "width": slider(props.get("width", 100), "%"),
        "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"),
        "_flex_align_self": "center",
    })
    return _sec([inner], bg, pad=dims(64, 0, 64, 0), anchor=props.get("anchor"))


# ═══════════════════════════ faq / cta / map ═══════════════════════════

@block("pr.faq")
def pr_faq(props):
    bg = props.get("bg", "white")
    acc = _faq(props.get("items", []), props.get("first_open", True))
    acc["settings"]["faq_schema"] = "yes"
    body = container([acc], {
        "content_width": "full", "flex_direction": "column",
        "width": slider(86, "%"), "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"), "_flex_align_self": "center"})
    head = [_head(props, _dark(bg))] if props.get("title") else []
    return _sec(head + [body], bg, anchor=props.get("anchor"))


@block("pr.cta")
def pr_cta(props):
    """Navy closing band: mint eyebrow, white heading, the phone pill and the
    Book button — both conversion paths, every page."""
    left = []
    if props.get("eyebrow"):
        left.append(_eyebrow(props["eyebrow"], True, "left"))
    left.append(_heading(props.get("title", ""), "h2", T["h_large"], "left",
                         on_dark=True))
    if props.get("text"):
        left.append(_text(props["text"], "left", on_dark=True))
    w = _tracks([60, 36], 40)
    right = _actions(props, on_dark=True)
    right["settings"]["flex_justify_content"] = "flex-end"
    row = _row([_col(left, w[0], extra={"flex_gap": gap(14)}),
                _col([right], w[1])], 40, align="center")
    return _sec([row], "navy", pad=dims(76, 0, 76, 0))


@block("pr.map")
def pr_map(props):
    """Map centred on the service area. No street address is published by
    the client, and a guessed pin on a contractor's page is worse than an
    honest regional view; one field in intake.json re-centres it."""
    bg = props.get("bg", "white")
    m = widget("google_maps", {
        "address": props.get("address", "Tacoma, WA"),
        "zoom": slider(props.get("zoom", 9)),
        "height": slider(props.get("height", 420)),
        "height_mobile": slider(320),
    })
    frame = container([m], {
        "content_width": "full", "flex_direction": "column",
        "border_radius": R_CARD, "overflow": "hidden",
        "border_border": "solid", "border_width": box(1),
    }, globals_={"border_color": color_ref(C["border"])})
    head = [_head(props, _dark(bg))] if props.get("title") else []
    return _sec(head + [frame], bg, anchor=props.get("anchor"))


# ═══════════════════════════ contact / booking ═══════════════════════════

def _details(items):
    return widget("icon-list", {
        "icon_list": [repeater_item(
            text=d["text"], selected_icon=icon(d.get("icon", "fas fa-info-circle")),
            link=link(d.get("href", ""))) for d in items],
        "space_between": slider(14),
        "icon_size": slider(18),
    }, globals_={"icon_color": color_ref(NAVY),
                 "text_color": color_ref(INK),
                 "icon_typography_typography": typo_ref("text")})


def _form_card(f):
    kids = []
    if f.get("title"):
        kids.append(_heading(f["title"], "h2", T["h_medium"], "left"))
    if f.get("intro"):
        kids.append(_text(f["intro"], "left", small=True))
    kids.append(_form(f))
    return container(kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(16),
        "padding": dims(34, 32, 34, 32),
        "padding_mobile": dims(24, 18, 24, 18),
        "border_radius": box(12),
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
        **CARD_SHADOW_SOFT,
    }, globals_={"background_color": color_ref(C["white"]),
                 "border_color": color_ref(C["border"])})


@block("pr.contact")
def pr_contact(props):
    bg = props.get("bg", "grey")
    info = [_head(dict(props, head_width=100), False, "left")]
    info.append(_details(props.get("details", [])))
    if props.get("phone_display") or props.get("cta_label"):
        info.append(_actions(props))
    w = _tracks([42, 54], 44)
    return _sec([_row([_col(info, w[0], extra={"flex_gap": gap(20)}),
                       _col([_form_card(props.get("form", {}))], w[1])],
                      44, align="flex-start")], bg, anchor=props.get("anchor"))


@block("pr.booking")
def pr_booking(props):
    """Book an Appointment: a stepped form (project, then you, then a time)
    beside what happens next. Steps keep each screen short enough to fill in
    on a phone, and the date and time fields use the device's own picker."""
    bg = props.get("bg", "grey")
    aside = []
    if props.get("aside_title"):
        aside.append(_heading(props["aside_title"], "h2", T["h_medium"], "left"))
    for i, st in enumerate(props.get("next", [])):
        aside.append(_row([
            container([widget("heading", {
                "title": str(i + 1), "header_size": "div", "align": "center",
            }, globals_={"title_color": color_ref(NAVY),
                         "typography_typography": typo_ref(T["h_small"])})], {
                "content_width": "full", "flex_direction": "row",
                "flex_justify_content": "center", "flex_align_items": "center",
                "width": slider(38), "min_height": slider(38), "_flex_grow": 0,
                "border_radius": box(999), "background_background": "classic",
            }, globals_={"background_color": color_ref(MINT)}),
            container([_heading(st.get("title", ""), "h3", T["h_small"], "left"),
                       _text(st.get("text", ""), "left", small=True)],
                      {"content_width": "full", "flex_direction": "column",
                       "flex_gap": gap(4)}),
        ], 14, align="flex-start", extra={"flex_wrap": "nowrap",
                                          "flex_direction_mobile": "row"}))
    if props.get("details"):
        aside.append(_details(props["details"]))
    if props.get("phone_display"):
        aside.append(_actions({"phone_display": props["phone_display"],
                               "phone": props.get("phone", "")}))
    w = _tracks([58, 38], 44)
    return _sec([_row([_col([_form_card(props.get("form", {}))], w[0]),
                       _col(aside, w[1], extra={"flex_gap": gap(18)})],
                      44, align="flex-start")], bg, anchor=props.get("anchor"))


# ═══════════════════════════ footer / sticky bar ═══════════════════════════

@block("pr.footer")
def pr_footer(props):
    white = C["white"]
    brand = []
    if props.get("logo"):
        brand.append(widget("image", {
            "image": media(props["logo"], props.get("logo_alt", "")),
            "image_size": "full", "width": slider(230), "align": "left"}))
    if props.get("blurb"):
        brand.append(_text(props["blurb"], "left", on_dark=True, small=True))
    if props.get("social"):
        s = _social(props["social"])
        s["settings"]["flex_justify_content"] = "flex-start"
        brand.append(s)

    def title(t):
        return widget("heading", {"title": _caps(t), "header_size": "div",
                                  "align": "left"},
                      globals_={"title_color": color_ref(MINT),
                                "typography_typography": typo_ref(T["eyebrow"])})

    w = _tracks([32, 20, 20, 24], 30)
    cols = [_col(brand, w[0], extra={"flex_gap": gap(18)})]
    for i, grp in enumerate(props.get("columns", [])[:2], start=1):
        cols.append(_col([title(grp["title"]),
                          _links(grp.get("links", []), True, "fas fa-angle-right")],
                         w[i], extra={"flex_gap": gap(14)}))
    contact = [title(props.get("contact_title", "Contact"))]
    items = []
    if props.get("phone_display"):
        items.append({"label": props["phone_display"],
                      "url": "tel:" + props.get("phone", "")})
    if props.get("email"):
        items.append({"label": props["email"], "url": "mailto:" + props["email"]})
    if props.get("location"):
        items.append({"label": props["location"], "url": ""})
    contact.append(widget("icon-list", {
        "icon_list": [repeater_item(text=it["label"], selected_icon=icon(ic),
                                    link=link(it["url"]))
                      for it, ic in zip(items, ["fas fa-phone-alt", "fas fa-envelope",
                                                "fas fa-map-marker-alt"])],
        "space_between": slider(12), "icon_size": slider(15),
    }, globals_={"icon_color": color_ref(MINT), "text_color": color_ref(white),
                 "icon_typography_typography": typo_ref("text")}))
    if props.get("cta_label"):
        contact.append(_btn(props["cta_label"], props.get("cta_url", "#"), "red",
                            "far fa-calendar-alt"))
    cols.append(_col(contact, w[3], extra={"flex_gap": gap(14)}))

    rule = container([], {"content_width": "full", "min_height": slider(1),
                          "margin": dims(38, 0, 22, 0),
                          "background_background": "classic"},
                     globals_={"background_color": color_ref(C["rule_dark"])})
    return _sec([_row(cols, 30, align="flex-start"), rule,
                 _text(props.get("legal", ""), "left", on_dark=True, small=True)],
                "navy", pad=dims(72, 0, 36, 0))


@block("pr.stickybar")
def pr_stickybar(props):
    """Phone + Book, pinned to the bottom of phones only."""
    call = _btn(props.get("call_label", "Call"), "tel:" + props.get("phone", ""),
                "call")
    book = _btn(props.get("cta_label", "Book"), props.get("cta_url",
                                                          "/book-an-appointment/"),
                "outline", "far fa-calendar-alt")
    return container([_row([call, book], 10, align="center", justify="center",
                           extra={"flex_wrap": "nowrap",
                                  "flex_direction_mobile": "row"})], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(10, 12, 10, 12),
        "background_background": "classic",
        "hide_desktop": "hidden-desktop",
        "hide_tablet": "hidden-tablet",
        "_position": "fixed",
        "_offset_orientation_v": "end",
        "_offset_y_end": slider(0),
        "_offset_x": slider(0),
        "width": slider(100, "%"),
        "_z_index": 998,
    }, globals_={"background_color": color_ref(NAVY)})
