"""
blocks_millbranch.py — the commercial-contractor card system.

Written for Mill Branch Site Solutions after probing the two references the
client named as liked (hemssitesolutions.com, smicompanies.net). The measured
device that nothing in the library could produce:

    SMI runs its service scope as cards with a TRANSLUCENT WHITE fill
    (rgba(255,255,255,0.06)) at 12px radius, sitting on a dark navy ground,
    each card carrying an uppercase label, a condensed title and a bulleted
    list of what is included.

`list.cards` is the right *content* shape — heading over a bulleted scope list
— but it is light-ground only: no `on_dark` path, no translucent fill, no
label. Shipping it would be the nearest-block substitution the design-fidelity
gate exists to catch, so this is a factory instead.

    cards.scope     translucent scope cards on a dark ground

One deliberate rejection recorded here as well as in design-spec.json: HEMS
uses fully-rounded pill buttons (border-radius 300px). Those are not carried
over. The brief's strongest instruction is that the site must not read as
residential landscaping, and a pill CTA is the single fastest way to make a
contractor site look consumer. SMI's ~6px radius is used throughout instead.
"""
from __future__ import annotations

from .core import (
    container, widget, repeater_item, slider, dims, box, link, icon,
    gap, color_ref, typo_ref,
)
from .tokens import C, T
from .blocks import block, _row, _col, _section, _grid_widths, _text


# Measured off smicompanies.net: 12px is the dominant card radius (18 uses),
# against 8px (4) and 16px (1). Not a guess.
SCOPE_RADIUS = 12


@block("cards.scope")
def cards_scope(props):
    """Scope cards: uppercase label, condensed title, bulleted inclusions.

    Ground defaults to dark because that is where the reference puts them and
    because a commercial contractor's scope list reads as heavier and more
    capable reversed out. `bg="white"` is supported so the same component can
    be reused on an interior page without a second factory.
    """
    items = props["items"]
    cols = props.get("columns", min(3, max(1, len(items))))
    width, width_t = _grid_widths(cols, 24)

    # `overlay` is the kit's translucent-white token — the same value SMI uses
    # for its card fills. On a light ground it would vanish, so the light path
    # takes the solid surface tint instead.
    on_dark = props.get("bg", "dark") in ("dark", "secondary", "primary")
    card_fill = C["overlay"] if on_dark else C["surface_alt"]

    cards = []
    for it in items:
        inner = []

        if it.get("label"):
            # The uppercase micro-label: DM Sans 600 12px in the reference,
            # which is what T["eyebrow"] is for.
            inner.append(widget("heading", {
                "title": it["label"], "header_size": "div", "align": "left",
            }, globals_={
                "title_color": color_ref("accent"),
                "typography_typography": typo_ref(T["eyebrow"]),
            }))

        inner.append(widget("heading", {
            "title": it["title"], "header_size": props.get("tag", "h3"),
            "align": "left",
        }, globals_={
            "title_color": color_ref(C["white"] if on_dark else "secondary"),
            "typography_typography": typo_ref(T["h_medium"]),
        }))

        if it.get("text"):
            inner.append(_text(it["text"], small=True, on_dark=on_dark))

        if it.get("points"):
            inner.append(widget("icon-list", {
                "icon_list": [
                    repeater_item(text=p, selected_icon=icon("fas fa-check"),
                                  link=link(""))
                    for p in it["points"]
                ],
                "space_between": slider(9),
                "icon_size": slider(13),
            }, globals_={
                # Gold ticks on dark is the brand's own accent doing the work
                # the reference does with its green.
                "icon_color": color_ref("accent"),
                "text_color": color_ref(C["on_dark"] if on_dark else "text"),
                "icon_typography_typography": typo_ref(T["body_small"]),
            }))

        if it.get("href"):
            inner.append(widget("button", {
                "text": props.get("link_label", "View service"),
                "link": link(it["href"]),
                "selected_icon": icon("fas fa-arrow-right"),
                "icon_align": "right",
                "size": "sm",
                "text_padding": dims(12, 22, 12, 22),
                # 6px, from the SMI probe. Explicitly not a pill.
                "border_radius": box(6),
                "border_border": "solid",
                "border_width": box(1),
            }, globals_={
                "button_text_color": color_ref(C["white"] if on_dark else "secondary"),
                "background_color": color_ref(C["transparent"]),
                "border_color": color_ref(C["rule_dark"] if on_dark else C["border"]),
                "hover_color": color_ref(C["on_primary"]),
                "button_background_hover_color": color_ref("accent"),
                "button_hover_border_color": color_ref("accent"),
            }))

        cards.append(_col(inner, width, extra={
            "background_background": "classic",
            "border_radius": box(SCOPE_RADIUS),
            "border_border": "solid",
            "border_width": box(1),
            "padding": dims(30, 28, 32, 28),
            "flex_gap": gap(12),
            "width_tablet": slider(width_t, "%"),
            "__globals__": {
                "background_color": color_ref(card_fill),
                "border_color": color_ref(
                    C["rule_dark"] if on_dark else C["border"]),
            },
        }))

    head = []
    if props.get("eyebrow"):
        head.append(widget("heading", {
            "title": props["eyebrow"], "header_size": "div", "align": "left",
        }, globals_={
            "title_color": color_ref("accent"),
            "typography_typography": typo_ref(T["eyebrow"]),
        }))
    if props.get("heading"):
        head.append(widget("heading", {
            "title": props["heading"], "header_size": "h2", "align": "left",
        }, globals_={
            "title_color": color_ref(C["white"] if on_dark else "secondary"),
            "typography_typography": typo_ref(T["h_large"]),
        }))
    if props.get("intro"):
        head.append(_text(props["intro"], on_dark=on_dark))

    children = []
    if head:
        children.append(_col(head, extra={"flex_gap": gap(12),
                                          "padding": dims(0, 0, 34, 0)}))
    children.append(_row(cards, gap_px=24, align="stretch"))

    return _section(children, bg=props.get("bg", "dark"))
